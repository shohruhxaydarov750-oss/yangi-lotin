"""Polished, dependency-free Tkinter interface for the converter."""

from __future__ import annotations

import ctypes
import queue
import sys
import tkinter as tk
from functools import lru_cache
from pathlib import Path
from tkinter import ttk

from . import autostart
from .live_mode import LiveKeyboardTransliterator
from .mode_state import ModeSelection, ModeSnapshot
from .reverse import count_latin_to_cyrillic, latin_to_cyrillic
from .tray import WindowsTrayIcon
from .transliterator import (
    count_all_conversions,
    count_convertible,
    count_old_latin_replacements,
    modernize_old_latin,
    to_new_latin,
    transliterate,
)


class Palette:
    BACKGROUND = "#F3F5F9"
    SURFACE = "#FFFFFF"
    BORDER = "#DCE1EA"
    TEXT = "#172033"
    MUTED = "#687386"
    FAINT = "#9AA4B2"
    PRIMARY = "#246BFE"
    PRIMARY_HOVER = "#1857D6"
    PRIMARY_PRESSED = "#1248B6"
    PRIMARY_SOFT = "#EAF1FF"
    SUCCESS = "#18875C"
    WARNING = "#B26A00"
    SELECTION = "#CFE0FF"
    LIVE_ON_BACKGROUND = "#E8F7F0"
    LIVE_ON = "#147A55"
    LIVE_OFF_BACKGROUND = "#EDF0F4"
    LIVE_OFF = "#687386"


def _enable_windows_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Uzbek.YangiLotin.Desktop.1"
        )
    except (AttributeError, OSError):
        pass


_OPEN_EVENT_NAME = "Local\\YangiLotin.OpenWindow.v1"


def _acquire_single_instance(show_existing: bool = True) -> tuple[int, int] | None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateEventW.argtypes = [
        ctypes.c_void_p, ctypes.c_bool, ctypes.c_bool, ctypes.c_wchar_p
    ]
    kernel32.CreateEventW.restype = ctypes.c_void_p
    kernel32.OpenEventW.argtypes = [ctypes.c_uint, ctypes.c_bool, ctypes.c_wchar_p]
    kernel32.OpenEventW.restype = ctypes.c_void_p
    kernel32.SetEvent.argtypes = [ctypes.c_void_p]
    kernel32.SetEvent.restype = ctypes.c_bool
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    user32.MessageBoxW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_uint,
    ]

    ctypes.set_last_error(0)
    handle = kernel32.CreateMutexW(None, False, "Local\\YangiLotin.RealTime.v1")
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    already_running = ctypes.get_last_error() == 183
    if already_running:
        if show_existing:
            open_event = kernel32.OpenEventW(0x0002, False, _OPEN_EVENT_NAME)
            if open_event:
                try:
                    kernel32.SetEvent(open_event)
                finally:
                    kernel32.CloseHandle(open_event)
            else:
                # An older copy may not support the open-window request.
                user32.MessageBoxW(
                    None,
                    "Yangi Lotin allaqaçon tray'da işlab turibdi.",
                    "Yangi Lotin",
                    0x00000040,
                )
        kernel32.CloseHandle(handle)
        return None
    open_event = kernel32.CreateEventW(None, False, False, _OPEN_EVENT_NAME)
    if not open_event:
        error = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise ctypes.WinError(error)
    return int(handle), int(open_event)


def _release_single_instance(handles: tuple[int, int]) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle(ctypes.c_void_p(handles[1]))
    kernel32.CloseHandle(ctypes.c_void_p(handles[0]))


@lru_cache(maxsize=1)
def _wait_for_open_request():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    kernel32.WaitForSingleObject.restype = ctypes.c_uint
    return kernel32.WaitForSingleObject


def _open_window_requested(handle: int) -> bool:
    return _wait_for_open_request()(ctypes.c_void_p(handle), 0) == 0


class ConverterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._status_timer: str | None = None
        self._persistent_status: tuple[str, str] | None = None
        self._placeholder_visible = False
        self._closing = False
        self._service_events: queue.SimpleQueue[tuple[str, object]] = queue.SimpleQueue()
        self._live_keyboard: LiveKeyboardTransliterator | None = None
        self._tray: WindowsTrayIcon | None = None
        self._hook_failure_reported = False
        self._open_event = 0
        self._modes = ModeSelection.load()

        self.root.title("Yangi Lotin — kirill va lotin o‘girgich")
        self.root.minsize(760, 640)
        self.root.configure(background=Palette.BACKGROUND)
        self.root.option_add("*tearOff", False)

        self._set_window_icon()
        self._configure_styles()
        self._build_layout()
        self._bind_shortcuts()
        self._centre_window(1040, 830)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self._start_background_services()
        self.root.after(75, self._drain_service_events)

        self.input_text.focus_set()
        self._refresh_placeholder()

    def _set_window_icon(self) -> None:
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        icon_file = base / "packaging" / "YangiLotin.ico"
        if sys.platform == "win32" and icon_file.is_file():
            try:
                self.root.iconbitmap(default=str(icon_file))
                return
            except tk.TclError:
                pass

        # Keep a simple fallback if the source is copied without the icon.
        icon = tk.PhotoImage(width=32, height=32)
        icon.put(Palette.PRIMARY, to=(0, 0, 32, 32))
        icon.put("#FFFFFF", to=(6, 7, 10, 25))
        icon.put("#FFFFFF", to=(10, 7, 18, 11))
        icon.put("#FFFFFF", to=(10, 15, 17, 19))
        icon.put("#FFFFFF", to=(17, 11, 21, 25))
        icon.put("#8FE3CF", to=(23, 7, 27, 25))
        self.root.iconphoto(True, icon)
        self._window_icon = icon

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Accent.TButton",
            background=Palette.PRIMARY,
            foreground="#FFFFFF",
            bordercolor=Palette.PRIMARY,
            lightcolor=Palette.PRIMARY,
            darkcolor=Palette.PRIMARY,
            padding=(18, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Accent.TButton",
            background=[("pressed", Palette.PRIMARY_PRESSED), ("active", Palette.PRIMARY_HOVER)],
            bordercolor=[("pressed", Palette.PRIMARY_PRESSED), ("active", Palette.PRIMARY_HOVER)],
            lightcolor=[("pressed", Palette.PRIMARY_PRESSED), ("active", Palette.PRIMARY_HOVER)],
            darkcolor=[("pressed", Palette.PRIMARY_PRESSED), ("active", Palette.PRIMARY_HOVER)],
        )

        style.configure(
            "Secondary.TButton",
            background=Palette.SURFACE,
            foreground=Palette.TEXT,
            bordercolor=Palette.BORDER,
            lightcolor=Palette.SURFACE,
            darkcolor=Palette.SURFACE,
            padding=(16, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Secondary.TButton",
            background=[("pressed", "#E7EAF0"), ("active", "#F0F2F6")],
            bordercolor=[("active", "#BFC7D3")],
        )

        style.configure(
            "Quiet.TButton",
            background=Palette.BACKGROUND,
            foreground=Palette.MUTED,
            bordercolor=Palette.BACKGROUND,
            lightcolor=Palette.BACKGROUND,
            darkcolor=Palette.BACKGROUND,
            padding=(12, 10),
            font=("Segoe UI", 10),
        )
        style.map(
            "Quiet.TButton",
            foreground=[("active", Palette.TEXT)],
            background=[("active", "#E8EBF1"), ("pressed", "#DEE3EB")],
            bordercolor=[("active", "#E8EBF1"), ("pressed", "#DEE3EB")],
        )

        style.configure(
            "Editor.Vertical.TScrollbar",
            background="#D8DDE6",
            troughcolor=Palette.SURFACE,
            bordercolor=Palette.SURFACE,
            arrowcolor=Palette.MUTED,
            width=12,
        )

    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        header = tk.Frame(self.root, background=Palette.SURFACE, padx=28, pady=20)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        logo = tk.Canvas(
            header,
            width=60,
            height=60,
            background=Palette.SURFACE,
            highlightthickness=0,
        )
        logo.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 16))
        logo.create_oval(2, 2, 58, 58, fill=Palette.PRIMARY, outline="")
        logo.create_text(
            30,
            30,
            text="А↔Ö",
            fill="#FFFFFF",
            font=("Segoe UI Semibold", 13),
        )

        tk.Label(
            header,
            text="Kirill va lotin yozuvini o‘girish",
            background=Palette.SURFACE,
            foreground=Palette.TEXT,
            font=("Segoe UI Semibold", 22),
            anchor="w",
        ).grid(row=0, column=1, sticky="sw")
        tk.Label(
            header,
            text="Yozayotganda avtomatik yoki oynada qo‘lda o‘giring",
            background=Palette.SURFACE,
            foreground=Palette.MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=1, column=1, sticky="nw", pady=(3, 0))

        self.live_pill = tk.Button(
            header,
            text="REAL-TIME:  TAYYORLANMOQDA…",
            command=self.toggle_live_mode,
            background=Palette.LIVE_OFF_BACKGROUND,
            foreground=Palette.LIVE_OFF,
            activebackground=Palette.LIVE_OFF_BACKGROUND,
            activeforeground=Palette.LIVE_OFF,
            font=("Segoe UI Semibold", 8),
            padx=12,
            pady=7,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.live_pill.grid(row=0, column=2, rowspan=2, sticky="e", padx=(18, 0))

        modes = tk.Frame(self.root, background=Palette.SURFACE, padx=28, pady=12)
        modes.grid(row=1, column=0, sticky="ew")
        modes.grid_columnconfigure(2, weight=1)

        tk.Label(
            modes,
            text="AVTOMATIK REJIMLAR",
            background=Palette.SURFACE,
            foreground=Palette.MUTED,
            font=("Segoe UI Semibold", 9),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.cyrillic_toggle = self._make_mode_button(
            modes, "cyrillic", 0
        )
        self.old_latin_toggle = self._make_mode_button(
            modes, "old_latin", 1
        )
        tk.Label(
            modes,
            text="Har birini alohida yoqing yoki öçiring",
            background=Palette.SURFACE,
            foreground=Palette.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=1, column=2, sticky="e")

        self.reverse_toggle = tk.Button(
            modes,
            command=lambda: self.toggle_conversion_mode("latin_to_cyrillic"),
            font=("Segoe UI Semibold", 9),
            padx=14,
            pady=8,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.reverse_toggle.grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(9, 0)
        )
        tk.Label(
            modes,
            text="Eski va yangi lotindan kirillga",
            background=Palette.SURFACE,
            foreground=Palette.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=2, column=2, sticky="e", pady=(9, 0))

        self.startup_toggle = tk.Button(
            modes,
            command=self.toggle_startup,
            font=("Segoe UI Semibold", 9),
            padx=14,
            pady=7,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.startup_toggle.grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(10, 0)
        )
        tk.Label(
            modes,
            text="Windows'ga kirganda tray'da özi işga tüşadi",
            background=Palette.SURFACE,
            foreground=Palette.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=3, column=2, sticky="e", pady=(10, 0))

        body = tk.Frame(self.root, background=Palette.BACKGROUND, padx=28, pady=22)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1, uniform="editor")
        body.grid_columnconfigure(1, weight=1, uniform="editor")
        body.grid_rowconfigure(1, weight=1)

        source_bar = tk.Frame(body, background=Palette.BACKGROUND)
        source_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        tk.Label(
            source_bar,
            text="Qo‘lda manba:",
            background=Palette.BACKGROUND,
            foreground=Palette.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=0, column=0, padx=(0, 8))
        self.manual_source = tk.StringVar(value=self._initial_manual_source())
        self.manual_selector = ttk.Combobox(
            source_bar,
            textvariable=self.manual_source,
            values=("Ikkalasi", "Kirill", "Eski lotin", "Lotin → kirill"),
            state="readonly",
            width=16,
            font=("Segoe UI", 9),
        )
        self.manual_selector.grid(row=0, column=1)
        self.manual_selector.bind(
            "<<ComboboxSelected>>", lambda _event: self._invalidate_output()
        )

        input_card, input_inner = self._make_card(body, 0)
        output_card, output_inner = self._make_card(body, 1)
        input_card.grid(padx=(0, 9))
        output_card.grid(padx=(9, 0))

        self.input_count = self._make_card_header(
            input_inner,
            "MANBA MATN",
        )
        self.output_count = self._make_card_header(output_inner, "NATIJA")

        input_editor = tk.Frame(input_inner, background=Palette.SURFACE)
        input_editor.grid(row=1, column=0, sticky="nsew", padx=18, pady=(2, 18))
        input_editor.grid_columnconfigure(0, weight=1)
        input_editor.grid_rowconfigure(0, weight=1)

        output_editor = tk.Frame(output_inner, background=Palette.SURFACE)
        output_editor.grid(row=1, column=0, sticky="nsew", padx=18, pady=(2, 18))
        output_editor.grid_columnconfigure(0, weight=1)
        output_editor.grid_rowconfigure(0, weight=1)

        self.input_text = self._make_text_widget(input_editor)
        self.output_text = self._make_text_widget(output_editor, output=True)

        self.placeholder = tk.Label(
            input_editor,
            text="Kirill yoki lotin matnini kiriting…",
            background=Palette.SURFACE,
            foreground=Palette.FAINT,
            font=("Segoe UI", 12),
            cursor="xterm",
        )
        self.placeholder.bind("<Button-1>", self._focus_from_placeholder)

        actions = tk.Frame(self.root, background=Palette.BACKGROUND, padx=28)
        actions.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        actions.grid_columnconfigure(2, weight=1)

        ttk.Button(
            actions,
            text="Qöyiş",
            command=self.paste,
            style="Secondary.TButton",
        ).grid(row=0, column=0, padx=(0, 9))
        ttk.Button(
            actions,
            text="Ögiriş",
            command=self.convert,
            style="Accent.TButton",
        ).grid(row=0, column=1)
        ttk.Button(
            actions,
            text="Nusxalaş",
            command=self.copy,
            style="Secondary.TButton",
        ).grid(row=0, column=3, padx=(0, 9))
        ttk.Button(
            actions,
            text="Tozala",
            command=self.clear,
            style="Quiet.TButton",
        ).grid(row=0, column=4)

        footer = tk.Frame(self.root, background=Palette.SURFACE, padx=28, pady=11)
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        self.status = tk.Label(
            footer,
            text="Tayyor",
            background=Palette.SURFACE,
            foreground=Palette.SUCCESS,
            font=("Segoe UI Semibold", 9),
            anchor="w",
        )
        self.status.grid(row=0, column=0, sticky="w")

        tk.Label(
            footer,
            text="Tray ikonka — real-time ON/OFF   ·   Ctrl+Enter — ögiriş   ·   Ctrl+Shift+C — nusxalaş   ·   Ctrl+L — tozala",
            background=Palette.SURFACE,
            foreground=Palette.MUTED,
            font=("Segoe UI", 8),
        ).grid(row=0, column=1, sticky="e")

        self.input_text.bind("<<Modified>>", self._input_modified)
        self.input_text.bind("<KeyPress>", self._hide_placeholder, add="+")
        self.input_text.bind("<FocusOut>", lambda _event: self._refresh_placeholder())

        self._build_context_menus()
        self._update_startup_ui()

    def _make_mode_button(self, parent: tk.Frame, name: str, column: int) -> tk.Button:
        button = tk.Button(
            parent,
            command=lambda: self.toggle_conversion_mode(name),
            font=("Segoe UI Semibold", 9),
            padx=14,
            pady=8,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
        )
        button.grid(row=1, column=column, sticky="w", padx=(0, 9))
        return button

    def _update_startup_ui(self) -> None:
        try:
            enabled = autostart.is_enabled()
        except OSError:
            enabled = False
        self.startup_toggle.configure(
            text=f"WINDOWS BILAN BOSHLASH  ·  {'ON' if enabled else 'OFF'}",
            background=Palette.LIVE_ON_BACKGROUND if enabled else Palette.LIVE_OFF_BACKGROUND,
            foreground=Palette.LIVE_ON if enabled else Palette.LIVE_OFF,
            activebackground="#D9F1E6" if enabled else "#E1E5EB",
            activeforeground=Palette.LIVE_ON if enabled else Palette.LIVE_OFF,
        )

    def toggle_startup(self) -> None:
        try:
            if autostart.is_enabled():
                autostart.disable()
                message = "Windows bilan işga tüşiriş öçirildi"
            else:
                autostart.enable()
                message = "Windows bilan işga tüşiriş yoqildi"
            self._update_startup_ui()
            self._set_status(message)
        except (OSError, ValueError, autostart.AutostartConflictError):
            self._set_status("Windows bilan işga tüşirişni sozlab bölmadi", Palette.WARNING)

    def _make_card(self, parent: tk.Widget, column: int) -> tuple[tk.Frame, tk.Frame]:
        border = tk.Frame(parent, background=Palette.BORDER, padx=1, pady=1)
        border.grid(row=1, column=column, sticky="nsew")
        border.grid_columnconfigure(0, weight=1)
        border.grid_rowconfigure(0, weight=1)

        inner = tk.Frame(border, background=Palette.SURFACE)
        inner.grid(row=0, column=0, sticky="nsew")
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_rowconfigure(1, weight=1)
        return border, inner

    def _make_card_header(self, parent: tk.Widget, title: str) -> tk.Label:
        header = tk.Frame(parent, background=Palette.SURFACE, padx=18, pady=15)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text=title,
            background=Palette.SURFACE,
            foreground=Palette.MUTED,
            font=("Segoe UI Semibold", 9),
        ).grid(row=0, column=0, sticky="w")
        counter = tk.Label(
            header,
            text="0 belgi · 0 söz",
            background=Palette.SURFACE,
            foreground=Palette.FAINT,
            font=("Segoe UI", 8),
        )
        counter.grid(row=0, column=1, sticky="e")
        return counter

    def _make_text_widget(self, parent: tk.Frame, output: bool = False) -> tk.Text:
        scrollbar = ttk.Scrollbar(
            parent,
            orient="vertical",
            style="Editor.Vertical.TScrollbar",
        )
        scrollbar.grid(row=0, column=1, sticky="ns")

        text = tk.Text(
            parent,
            wrap="word",
            undo=not output,
            maxundo=-1,
            autoseparators=True,
            borderwidth=0,
            highlightthickness=0,
            background=Palette.SURFACE,
            foreground=Palette.TEXT,
            insertbackground=Palette.PRIMARY,
            selectbackground=Palette.SELECTION,
            selectforeground=Palette.TEXT,
            font=("Segoe UI", 12),
            padx=4,
            pady=4,
            spacing1=2,
            spacing3=2,
            yscrollcommand=scrollbar.set,
        )
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.configure(command=text.yview)

        if output:
            text.configure(state="disabled", cursor="arrow", takefocus=True)
        return text

    def _build_context_menus(self) -> None:
        input_menu = tk.Menu(self.root)
        input_menu.add_command(label="Kesib ol", command=lambda: self.input_text.event_generate("<<Cut>>"))
        input_menu.add_command(label="Nusxala", command=lambda: self.input_text.event_generate("<<Copy>>"))
        input_menu.add_command(label="Qöy", command=self.paste)
        input_menu.add_separator()
        input_menu.add_command(label="Barchasini tanla", command=lambda: self._select_all(self.input_text))

        output_menu = tk.Menu(self.root)
        output_menu.add_command(label="Nusxala", command=self.copy)
        output_menu.add_separator()
        output_menu.add_command(label="Barchasini tanla", command=lambda: self._select_all(self.output_text))

        self.input_text.bind("<Button-3>", lambda event: self._show_menu(input_menu, event))
        self.output_text.bind("<Button-3>", lambda event: self._show_menu(output_menu, event))

    @staticmethod
    def _show_menu(menu: tk.Menu, event: tk.Event) -> str:
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    @staticmethod
    def _select_all(widget: tk.Text) -> str:
        widget.tag_add("sel", "1.0", "end-1c")
        widget.mark_set("insert", "1.0")
        widget.see("insert")
        return "break"

    def _bind_shortcuts(self) -> None:
        convert_shortcut = self._shortcut(self.convert)
        self.root.bind_all("<Control-Return>", convert_shortcut)
        # A Text widget's default key binding would insert a newline before
        # the bind_all handler runs.  The widget-level binding runs first and
        # returns "break", so Ctrl+Enter converts without changing the input.
        self.input_text.bind("<Control-Return>", convert_shortcut)
        self.output_text.bind("<Control-Return>", convert_shortcut)
        self.root.bind_all("<Control-Shift-V>", self._shortcut(self.paste))
        self.root.bind_all("<Control-Shift-v>", self._shortcut(self.paste))
        self.root.bind_all("<Control-Shift-C>", self._shortcut(self.copy))
        self.root.bind_all("<Control-Shift-c>", self._shortcut(self.copy))
        self.root.bind_all("<Control-l>", self._shortcut(self.clear))
        self.root.bind_all("<Control-L>", self._shortcut(self.clear))

    @staticmethod
    def _shortcut(action):
        def handler(_event: tk.Event) -> str:
            action()
            return "break"

        return handler

    def _centre_window(self, width: int, height: int) -> None:
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(width, max(760, screen_width - 16))
        height = min(height, max(640, screen_height - 70))
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2 - 20)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _focus_from_placeholder(self, _event: tk.Event) -> str:
        self._hide_placeholder()
        self.input_text.focus_set()
        return "break"

    def _hide_placeholder(self, _event: tk.Event | None = None) -> None:
        if self._placeholder_visible:
            self.placeholder.place_forget()
            self._placeholder_visible = False

    def _refresh_placeholder(self) -> None:
        if not self.input_text.get("1.0", "end-1c"):
            self.placeholder.place(x=8, y=8)
            self._placeholder_visible = True
        else:
            self._hide_placeholder()

    def _input_modified(self, _event: tk.Event) -> None:
        if not self.input_text.edit_modified():
            return
        self.input_text.edit_modified(False)
        text = self.input_text.get("1.0", "end-1c")
        self.input_count.configure(text=self._count_label(text))
        self._invalidate_output()
        self._refresh_placeholder()

    def _initial_manual_source(self) -> str:
        current = self._modes.current
        selected = current if current.any_enabled else self._modes.last_nonempty
        if selected.latin_to_cyrillic:
            return "Lotin → kirill"
        if selected.cyrillic and selected.old_latin:
            return "Ikkalasi"
        return "Kirill" if selected.cyrillic else "Eski lotin"

    def _invalidate_output(self) -> None:
        # Copy must never return a result for older input or another source mode.
        if self.output_text.get("1.0", "end-1c"):
            self._set_output("")

    @staticmethod
    def _count_label(text: str) -> str:
        words = len(text.split()) if text else 0
        return f"{len(text)} belgi · {words} söz"

    def _set_output(self, text: str) -> None:
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")
        self.output_count.configure(text=self._count_label(text))

    def _set_status(
        self,
        message: str,
        colour: str = Palette.SUCCESS,
        *,
        persistent: bool = False,
    ) -> None:
        if self._status_timer is not None:
            self.root.after_cancel(self._status_timer)
            self._status_timer = None
        if persistent:
            self._persistent_status = (message, colour)
        self.status.configure(text=message, foreground=colour)
        if message != "Tayyor" and not persistent:
            self._status_timer = self.root.after(3200, self._reset_status)

    def _reset_status(self) -> None:
        self._status_timer = None
        message, colour = self._persistent_status or ("Tayyor", Palette.SUCCESS)
        self.status.configure(text=message, foreground=colour)

    def _start_background_services(self) -> None:
        live_started = False
        current = self._modes.current
        try:
            self._live_keyboard = LiveKeyboardTransliterator(enabled=False)
            self._live_keyboard.set_modes(
                current.cyrillic, current.old_latin, current.latin_to_cyrillic
            )
            self._live_keyboard.start()
            live_started = True
        except Exception:
            self._live_keyboard = None
            self._set_status(
                "Real-time klaviatura rejimi işga tüşmadi",
                Palette.WARNING,
                persistent=True,
            )

        try:
            self._tray = WindowsTrayIcon(
                active=live_started and current.any_enabled,
                on_toggle=lambda active: self._service_events.put(("toggle", active)),
                on_mode_toggle=lambda name: self._service_events.put(("mode", name)),
                on_open=lambda: self._service_events.put(("open", None)),
                on_exit=lambda: self._service_events.put(("exit", None)),
                cyrillic_enabled=live_started and current.cyrillic,
                old_latin_enabled=live_started and current.old_latin,
                latin_to_cyrillic_enabled=live_started and current.latin_to_cyrillic,
            )
            self._tray.start()
            if not self._tray.icon_added:
                self._set_status(
                    "Tray ikonka hali tayyor emas",
                    Palette.WARNING,
                    persistent=True,
                )
        except Exception:
            self._tray = None
            self._set_status(
                "Tray ikonka işga tüşmadi",
                Palette.WARNING,
                persistent=True,
            )

        self._update_live_ui()

    def _drain_service_events(self) -> None:
        if self._closing:
            return
        if self._open_event and _open_window_requested(self._open_event):
            self.show_window()
        while True:
            try:
                event, value = self._service_events.get_nowait()
            except queue.Empty:
                break

            if event == "toggle":
                self.toggle_live_mode()
            elif event == "mode":
                self.toggle_conversion_mode(str(value))
            elif event == "open":
                self.show_window()
            elif event == "exit":
                self.shutdown()
                return

        if (
            self._live_keyboard is not None
            and not self._live_keyboard.running
            and not self._hook_failure_reported
        ):
            self._hook_failure_reported = True
            if self._tray is not None:
                self._tray.set_modes(False, False, False)
            self._update_live_ui()
            self._set_status(
                "Real-time xizmat töxtadi — dasturni qayta oçing",
                Palette.WARNING,
                persistent=True,
            )

        self.root.after(75, self._drain_service_events)

    def _update_live_ui(self) -> None:
        running = bool(self._live_keyboard and self._live_keyboard.running)
        current = self._modes.current
        active = running and current.any_enabled
        if active:
            self.live_pill.configure(
                text="AVTOMATIK:  YOQILGAN",
                background=Palette.LIVE_ON_BACKGROUND,
                foreground=Palette.LIVE_ON,
                activebackground="#D9F1E6",
                activeforeground=Palette.LIVE_ON,
                state="normal",
            )
        else:
            self.live_pill.configure(
                text="AVTOMATIK:  ÖÇIRILGAN" if running else "AVTOMATIK:  XATO",
                background=Palette.LIVE_OFF_BACKGROUND,
                foreground=Palette.LIVE_OFF,
                activebackground="#E1E5EB",
                activeforeground=Palette.LIVE_OFF,
                state="normal" if running else "disabled",
            )

        for button, enabled, title in (
            (self.cyrillic_toggle, current.cyrillic, "KIRILL → YANGI LOTIN"),
            (self.old_latin_toggle, current.old_latin, "ESKI LOTIN → YANGI LOTIN"),
            (self.reverse_toggle, current.latin_to_cyrillic, "LOTIN → KIRILL"),
        ):
            on = running and enabled
            button.configure(
                text=f"{title}  ·  {'ON' if on else 'OFF'}",
                background=Palette.LIVE_ON_BACKGROUND if on else Palette.LIVE_OFF_BACKGROUND,
                foreground=Palette.LIVE_ON if on else Palette.LIVE_OFF,
                activebackground="#D9F1E6" if on else "#E1E5EB",
                activeforeground=Palette.LIVE_ON if on else Palette.LIVE_OFF,
                state="normal" if running else "disabled",
            )

    def _apply_modes(self, snapshot: ModeSnapshot) -> bool:
        if self._live_keyboard is not None and self._live_keyboard.running:
            self._live_keyboard.set_modes(
                snapshot.cyrillic, snapshot.old_latin, snapshot.latin_to_cyrillic
            )
        if self._tray is not None:
            self._tray.set_modes(
                snapshot.cyrillic if self._live_keyboard and self._live_keyboard.running else False,
                snapshot.old_latin if self._live_keyboard and self._live_keyboard.running else False,
                snapshot.latin_to_cyrillic if self._live_keyboard and self._live_keyboard.running else False,
            )
        self._update_live_ui()
        try:
            self._modes.save()
        except OSError:
            self._set_status("Rejim tanlovi saqlanmadi", Palette.WARNING)
            return False
        return True

    def toggle_live_mode(self) -> None:
        if self._live_keyboard is None or not self._live_keyboard.running:
            self._set_status("Avtomatik xizmat ishga tushmagan", Palette.WARNING)
            return
        snapshot = self._modes.toggle_all()
        if not self._apply_modes(snapshot):
            return
        self._set_status(
            "Avtomatik ögiriş yoqildi" if snapshot.any_enabled else "Avtomatik ögiriş öçirildi",
            Palette.SUCCESS if snapshot.any_enabled else Palette.WARNING,
        )

    def toggle_conversion_mode(self, name: str) -> None:
        if self._live_keyboard is None or not self._live_keyboard.running:
            self._set_status("Avtomatik xizmat ishga tushmagan", Palette.WARNING)
            return
        if name not in {"cyrillic", "old_latin", "latin_to_cyrillic"}:
            return
        snapshot = self._modes.toggle_mode(name)
        if not self._apply_modes(snapshot):
            return
        label = {
            "cyrillic": "Kirill → yangi lotin",
            "old_latin": "Eski lotin → yangi lotin",
            "latin_to_cyrillic": "Lotin → kirill",
        }[name]
        enabled = getattr(snapshot, name)
        self._set_status(
            f"{label} rejimi {'yoqildi' if enabled else 'öçirildi'}",
            Palette.SUCCESS if enabled else Palette.WARNING,
        )

    def hide_to_tray(self) -> None:
        if self._tray is None or not self._tray.running:
            self.shutdown()
            return
        if not self._tray.icon_added:
            self._set_status("Tray ikonka tayyor bölmagunça oyna oçiq qoladi", Palette.WARNING)
            return
        self.root.withdraw()

    def show_window(self) -> None:
        if self._closing:
            return
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.after(50, self.root.focus_force)

    def shutdown(self) -> None:
        if self._closing:
            return
        self._closing = True
        if self._status_timer is not None:
            try:
                self.root.after_cancel(self._status_timer)
            except tk.TclError:
                pass
            self._status_timer = None
        if self._live_keyboard is not None:
            self._live_keyboard.stop()
        if self._tray is not None:
            self._tray.stop()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def paste(self) -> None:
        try:
            clipboard_text = self.root.clipboard_get()
        except tk.TclError:
            self._set_status("Almaşuv buferida matn yöq", Palette.WARNING)
            return

        try:
            first = self.input_text.index("sel.first")
            last = self.input_text.index("sel.last")
            self.input_text.delete(first, last)
        except tk.TclError:
            pass

        self.input_text.insert("insert", clipboard_text)
        self.input_text.focus_set()
        self._set_status("Matn qöyildi")

    def convert(self) -> None:
        source = self.input_text.get("1.0", "end-1c")
        if not source:
            self._set_status(
                "Avval kirill yoki lotin matn kiriting",
                Palette.WARNING,
            )
            self.input_text.focus_set()
            return

        manual_source = self.manual_source.get()
        if manual_source == "Kirill":
            result = transliterate(source)
            converted = count_convertible(source)
        elif manual_source == "Eski lotin":
            result = modernize_old_latin(source)
            converted = count_old_latin_replacements(source)
        elif manual_source == "Lotin → kirill":
            result = latin_to_cyrillic(source)
            converted = count_latin_to_cyrillic(source)
        else:
            result = to_new_latin(source)
            converted = count_all_conversions(source)
        self._set_output(result)
        if converted:
            self._set_status(f"{converted} ta harf yoki birikma ögirildi")
        else:
            self._set_status("Ögiriladigan harf yoki birikma topilmadi", Palette.WARNING)

    def copy(self) -> None:
        result = self.output_text.get("1.0", "end-1c")
        if not result:
            self._set_status("Nusxalaş uçun natija yöq", Palette.WARNING)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(result)
        self.root.update_idletasks()
        self._set_status("Natija nusxalandi")

    def clear(self) -> None:
        self.input_text.delete("1.0", "end")
        self._set_output("")
        self.input_text.focus_set()
        self._refresh_placeholder()
        self._set_status("Maydonlar tozalandi")


def main() -> None:
    _enable_windows_dpi_awareness()
    start_in_tray = "--tray" in sys.argv[1:]
    instance = _acquire_single_instance(show_existing=not start_in_tray)
    if instance is None:
        return
    root = tk.Tk()
    if start_in_tray:
        root.withdraw()
    app: ConverterApp | None = None
    try:
        app = ConverterApp(root)
        app._open_event = instance[1]
        if not start_in_tray:
            try:
                if autostart.refresh_if_enabled():
                    app._update_startup_ui()
            except OSError:
                app._set_status("Windows bilan işga tüşiş nusxasi yangilanmadi", Palette.WARNING)
        if start_in_tray and not (
            app._tray is not None
            and app._tray.running
            and app._tray.icon_added
            and app._live_keyboard is not None
            and app._live_keyboard.running
        ):
            app.show_window()
        root.mainloop()
    finally:
        if app is not None:
            app.shutdown()
        else:
            root.destroy()
        _release_single_instance(instance)


if __name__ == "__main__":
    main()
