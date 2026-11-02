"""Windows notification-area icon with one-click live-mode toggle."""

from __future__ import annotations

import ctypes
import math
import os
import threading
import time
from ctypes import wintypes
from typing import Callable


WINDOWS = os.name == "nt"

if WINDOWS:
    LRESULT = ctypes.c_ssize_t
    WPARAM = ctypes.c_size_t
    LPARAM = ctypes.c_ssize_t
    HICON = ctypes.c_void_p
    HINSTANCE = ctypes.c_void_p
    HBITMAP = ctypes.c_void_p
    HBRUSH = ctypes.c_void_p
    HCURSOR = ctypes.c_void_p
    HMENU = ctypes.c_void_p
    HDC = ctypes.c_void_p

    WM_NULL = 0x0000
    WM_DESTROY = 0x0002
    WM_CLOSE = 0x0010
    WM_CONTEXTMENU = 0x007B
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONUP = 0x0205
    WM_APP = 0x8000
    WM_TRAY = WM_APP + 1
    WM_UPDATE = WM_APP + 2

    NIN_SELECT = 0x0400
    NIN_KEYSELECT = 0x0401

    NIM_ADD = 0x00000000
    NIM_MODIFY = 0x00000001
    NIM_DELETE = 0x00000002
    NIM_SETVERSION = 0x00000004
    NOTIFYICON_VERSION_4 = 4

    NIF_MESSAGE = 0x00000001
    NIF_ICON = 0x00000002
    NIF_TIP = 0x00000004
    NIF_SHOWTIP = 0x00000080

    MF_STRING = 0x00000000
    MF_CHECKED = 0x00000008
    MF_SEPARATOR = 0x00000800
    TPM_RIGHTBUTTON = 0x0002
    TPM_RETURNCMD = 0x0100
    TPM_NONOTIFY = 0x0080

    WS_POPUP = 0x80000000
    WS_EX_TOOLWINDOW = 0x00000080

    DIB_RGB_COLORS = 0
    BI_RGB = 0

    MENU_TOGGLE = 1001
    MENU_OPEN = 1002
    MENU_EXIT = 1003
    MENU_CYRILLIC = 1004
    MENU_OLD_LATIN = 1005
    MENU_LATIN_TO_CYRILLIC = 1006

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    class NOTIFYICONDATAW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("hWnd", wintypes.HWND),
            ("uID", wintypes.UINT),
            ("uFlags", wintypes.UINT),
            ("uCallbackMessage", wintypes.UINT),
            ("hIcon", HICON),
            ("szTip", wintypes.WCHAR * 128),
            ("dwState", wintypes.DWORD),
            ("dwStateMask", wintypes.DWORD),
            ("szInfo", wintypes.WCHAR * 256),
            ("uVersion", wintypes.UINT),
            ("szInfoTitle", wintypes.WCHAR * 64),
            ("dwInfoFlags", wintypes.DWORD),
            ("guidItem", GUID),
            ("hBalloonIcon", HICON),
        ]

    WNDPROC = ctypes.WINFUNCTYPE(
        LRESULT,
        wintypes.HWND,
        wintypes.UINT,
        WPARAM,
        LPARAM,
    )

    class WNDCLASSEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", HINSTANCE),
            ("hIcon", HICON),
            ("hCursor", HCURSOR),
            ("hbrBackground", HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
            ("hIconSm", HICON),
        ]

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class RGBQUAD(ctypes.Structure):
        _fields_ = [
            ("rgbBlue", ctypes.c_ubyte),
            ("rgbGreen", ctypes.c_ubyte),
            ("rgbRed", ctypes.c_ubyte),
            ("rgbReserved", ctypes.c_ubyte),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BITMAPINFOHEADER),
            ("bmiColors", RGBQUAD * 1),
        ]

    class ICONINFO(ctypes.Structure):
        _fields_ = [
            ("fIcon", wintypes.BOOL),
            ("xHotspot", wintypes.DWORD),
            ("yHotspot", wintypes.DWORD),
            ("hbmMask", HBITMAP),
            ("hbmColor", HBITMAP),
        ]

    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

    shell32.Shell_NotifyIconW.argtypes = [
        wintypes.DWORD,
        ctypes.POINTER(NOTIFYICONDATAW),
    ]
    shell32.Shell_NotifyIconW.restype = wintypes.BOOL

    user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
    user32.RegisterClassExW.restype = wintypes.ATOM
    user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, HINSTANCE]
    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.HWND,
        HMENU,
        HINSTANCE,
        ctypes.c_void_p,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.DefWindowProcW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        WPARAM,
        LPARAM,
    ]
    user32.DefWindowProcW.restype = LRESULT
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.GetMessageW.argtypes = [
        ctypes.POINTER(wintypes.MSG),
        wintypes.HWND,
        wintypes.UINT,
        wintypes.UINT,
    ]
    user32.GetMessageW.restype = ctypes.c_int
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.PostMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        WPARAM,
        LPARAM,
    ]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterWindowMessageW.restype = wintypes.UINT
    user32.CreatePopupMenu.restype = HMENU
    user32.AppendMenuW.argtypes = [
        HMENU,
        wintypes.UINT,
        ctypes.c_size_t,
        wintypes.LPCWSTR,
    ]
    user32.TrackPopupMenu.argtypes = [
        HMENU,
        wintypes.UINT,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.HWND,
        ctypes.c_void_p,
    ]
    user32.TrackPopupMenu.restype = wintypes.UINT
    user32.DestroyMenu.argtypes = [HMENU]
    user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.CreateIconIndirect.argtypes = [ctypes.POINTER(ICONINFO)]
    user32.CreateIconIndirect.restype = HICON
    user32.DestroyIcon.argtypes = [HICON]

    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = HINSTANCE

    gdi32.CreateDIBSection.argtypes = [
        HDC,
        ctypes.POINTER(BITMAPINFO),
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    gdi32.CreateDIBSection.restype = HBITMAP
    gdi32.CreateBitmap.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.c_void_p,
    ]
    gdi32.CreateBitmap.restype = HBITMAP
    gdi32.DeleteObject.argtypes = [ctypes.c_void_p]


class WindowsTrayIcon:
    """Own a tray icon and Win32 message loop on a dedicated thread."""

    def __init__(
        self,
        active: bool,
        on_toggle: Callable[[bool], None],
        on_open: Callable[[], None],
        on_exit: Callable[[], None],
        *,
        cyrillic_enabled: bool | None = None,
        old_latin_enabled: bool | None = None,
        latin_to_cyrillic_enabled: bool = False,
        on_mode_toggle: Callable[[str], None] | None = None,
    ) -> None:
        if latin_to_cyrillic_enabled and (
            (cyrillic_enabled is not None and bool(cyrillic_enabled))
            or (old_latin_enabled is not None and bool(old_latin_enabled))
        ):
            raise ValueError("Opposite conversion directions cannot be active together")
        self._cyrillic_enabled = (
            bool(active and not latin_to_cyrillic_enabled)
            if cyrillic_enabled is None else bool(cyrillic_enabled)
        )
        self._old_latin_enabled = (
            bool(active and not latin_to_cyrillic_enabled)
            if old_latin_enabled is None else bool(old_latin_enabled)
        )
        self._latin_to_cyrillic_enabled = bool(latin_to_cyrillic_enabled)
        self._active = (
            self._cyrillic_enabled
            or self._old_latin_enabled
            or self._latin_to_cyrillic_enabled
        )
        self._on_toggle = on_toggle
        self._on_mode_toggle = on_mode_toggle
        self._on_open = on_open
        self._on_exit = on_exit
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._startup_error: BaseException | None = None
        self._hwnd = 0
        self._module = None
        self._wnd_proc = None
        self._class_name = f"YangiLotinTrayWindow_{os.getpid()}"
        self._taskbar_created = 0
        self._icon_on = None
        self._icon_off = None
        self._icon_added = False
        self._last_toggle_at = 0.0

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def active(self) -> bool:
        with self._lock:
            return self._active

    @property
    def icon_added(self) -> bool:
        """Whether Windows currently has a visible notification-area icon."""

        return bool(self._icon_added)

    def start(self, timeout: float = 4.0) -> None:
        if not WINDOWS:
            raise OSError("The tray icon is available only on Windows")
        if self.running:
            return

        self._ready.clear()
        self._startup_error = None
        self._thread = threading.Thread(
            target=self._thread_main,
            name="YangiLotinTray",
            daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(timeout):
            raise TimeoutError("Tray icon did not start in time")
        if self._startup_error is not None:
            raise RuntimeError("Tray icon could not start") from self._startup_error

    def set_active(self, active: bool) -> None:
        """Compatibility helper for callers with a single shared mode."""

        self.set_modes(active, active, False)

    def set_modes(
        self,
        cyrillic: bool,
        old_latin: bool,
        latin_to_cyrillic: bool = False,
    ) -> None:
        """Update checked menu items and the effective icon state."""

        if latin_to_cyrillic and (cyrillic or old_latin):
            raise ValueError("Opposite conversion directions cannot be active together")

        with self._lock:
            self._cyrillic_enabled = bool(cyrillic)
            self._old_latin_enabled = bool(old_latin)
            self._latin_to_cyrillic_enabled = bool(latin_to_cyrillic)
            self._active = (
                self._cyrillic_enabled
                or self._old_latin_enabled
                or self._latin_to_cyrillic_enabled
            )
        if self._hwnd:
            user32.PostMessageW(self._hwnd, WM_UPDATE, 0, 0)

    def stop(self, timeout: float = 4.0) -> None:
        thread = self._thread
        if not thread:
            return
        if self._hwnd:
            user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
        if thread is not threading.current_thread():
            thread.join(timeout)
        # Do not lose track of a still-running message loop; start() must not
        # create a duplicate tray icon after a rare shutdown timeout.
        if not thread.is_alive():
            self._thread = None

    def _thread_main(self) -> None:
        try:
            self._module = kernel32.GetModuleHandleW(None)
            self._icon_on = self._create_state_icon(True)
            self._icon_off = self._create_state_icon(False)
            self._taskbar_created = int(
                user32.RegisterWindowMessageW("TaskbarCreated")
            )
            self._wnd_proc = WNDPROC(self._window_proc)

            window_class = WNDCLASSEXW(
                cbSize=ctypes.sizeof(WNDCLASSEXW),
                style=0,
                lpfnWndProc=self._wnd_proc,
                cbClsExtra=0,
                cbWndExtra=0,
                hInstance=self._module,
                hIcon=self._icon_on,
                hCursor=None,
                hbrBackground=None,
                lpszMenuName=None,
                lpszClassName=self._class_name,
                hIconSm=self._icon_on,
            )
            if not user32.RegisterClassExW(ctypes.byref(window_class)):
                raise ctypes.WinError(ctypes.get_last_error())

            self._hwnd = int(
                user32.CreateWindowExW(
                    WS_EX_TOOLWINDOW,
                    self._class_name,
                    "YangiLotinTray",
                    WS_POPUP,
                    0,
                    0,
                    0,
                    0,
                    None,
                    None,
                    self._module,
                    None,
                )
                or 0
            )
            if not self._hwnd:
                raise ctypes.WinError(ctypes.get_last_error())

            self._add_icon()
            self._ready.set()

            message = wintypes.MSG()
            while True:
                result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result == 0:
                    break
                if result == -1:
                    raise ctypes.WinError(ctypes.get_last_error())
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
        except BaseException as error:
            self._startup_error = error
            self._ready.set()
        finally:
            self._delete_icon()
            if self._hwnd:
                user32.DestroyWindow(self._hwnd)
            self._hwnd = 0
            if self._module:
                user32.UnregisterClassW(self._class_name, self._module)
            if self._icon_on:
                user32.DestroyIcon(self._icon_on)
            if self._icon_off:
                user32.DestroyIcon(self._icon_off)
            self._icon_on = None
            self._icon_off = None

    def _window_proc(
        self,
        hwnd: int,
        message: int,
        w_param: int,
        l_param: int,
    ) -> int:
        try:
            if self._taskbar_created and message == self._taskbar_created:
                self._icon_added = False
                self._add_icon()
                return 0

            if message == WM_TRAY:
                event = int(l_param) & 0xFFFF
                if event in {NIN_SELECT, NIN_KEYSELECT, WM_LBUTTONUP}:
                    self._toggle_from_tray()
                    return 0
                if event in {WM_CONTEXTMENU, WM_RBUTTONUP}:
                    self._show_menu()
                    return 0

            if message == WM_UPDATE:
                self._modify_icon()
                return 0

            if message == WM_CLOSE:
                user32.DestroyWindow(hwnd)
                return 0

            if message == WM_DESTROY:
                self._delete_icon()
                self._hwnd = 0
                user32.PostQuitMessage(0)
                return 0
        except BaseException:
            return int(user32.DefWindowProcW(hwnd, message, w_param, l_param))

        return int(user32.DefWindowProcW(hwnd, message, w_param, l_param))

    def _toggle_from_tray(self) -> None:
        now = time.monotonic()
        if now - self._last_toggle_at < 0.25:
            return
        self._last_toggle_at = now
        with self._lock:
            desired_active = not self._active
        # The GUI owns the remembered pair of modes.  It will apply the
        # requested state and call set_modes(), so the icon and menu cannot
        # briefly disagree about which conversions are enabled.
        self._on_toggle(desired_active)

    def _show_menu(self) -> None:
        menu = user32.CreatePopupMenu()
        if not menu:
            return
        try:
            with self._lock:
                active = self._active
                cyrillic = self._cyrillic_enabled
                old_latin = self._old_latin_enabled
                latin_to_cyrillic = self._latin_to_cyrillic_enabled
            toggle_label = (
                "Real-time rejimni öçiriş"
                if active
                else "Real-time rejimni yoqiş"
            )
            user32.AppendMenuW(menu, MF_STRING, MENU_TOGGLE, toggle_label)
            if self._on_mode_toggle is not None:
                user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
                user32.AppendMenuW(
                    menu,
                    MF_STRING | (MF_CHECKED if cyrillic else 0),
                    MENU_CYRILLIC,
                    "Kirill → yangi lotin",
                )
                user32.AppendMenuW(
                    menu,
                    MF_STRING | (MF_CHECKED if old_latin else 0),
                    MENU_OLD_LATIN,
                    "Eski lotin → yangi lotin",
                )
                user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
                user32.AppendMenuW(
                    menu,
                    MF_STRING | (MF_CHECKED if latin_to_cyrillic else 0),
                    MENU_LATIN_TO_CYRILLIC,
                    "Lotin → kirill",
                )
            user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
            user32.AppendMenuW(menu, MF_STRING, MENU_OPEN, "Oynani oçiş")
            user32.AppendMenuW(menu, MF_STRING, MENU_EXIT, "Çiqiş")

            point = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(point))
            user32.SetForegroundWindow(self._hwnd)
            command = int(
                user32.TrackPopupMenu(
                    menu,
                    TPM_RIGHTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY,
                    point.x,
                    point.y,
                    0,
                    self._hwnd,
                    None,
                )
            )
            user32.PostMessageW(self._hwnd, WM_NULL, 0, 0)
            if command == MENU_TOGGLE:
                self._toggle_from_tray()
            elif command == MENU_CYRILLIC and self._on_mode_toggle is not None:
                self._on_mode_toggle("cyrillic")
            elif command == MENU_OLD_LATIN and self._on_mode_toggle is not None:
                self._on_mode_toggle("old_latin")
            elif command == MENU_LATIN_TO_CYRILLIC and self._on_mode_toggle is not None:
                self._on_mode_toggle("latin_to_cyrillic")
            elif command == MENU_OPEN:
                self._on_open()
            elif command == MENU_EXIT:
                self._on_exit()
        finally:
            user32.DestroyMenu(menu)

    def _notification_data(self) -> NOTIFYICONDATAW:
        with self._lock:
            active = self._active
            cyrillic = self._cyrillic_enabled
            old_latin = self._old_latin_enabled
            latin_to_cyrillic = self._latin_to_cyrillic_enabled
        data = NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        data.hWnd = self._hwnd
        data.uID = 1
        data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP | NIF_SHOWTIP
        data.uCallbackMessage = WM_TRAY
        data.hIcon = self._icon_on if active else self._icon_off
        enabled_modes = ", ".join(
            label
            for selected, label in (
                (cyrillic, "kirill"),
                (old_latin, "eski lotin"),
                (latin_to_cyrillic, "lotin → kirill"),
            )
            if selected
        )
        data.szTip = (
            f"Yangi Lotin — YOQILGAN: {enabled_modes}"
            if active
            else "Yangi Lotin — ÖÇIRILGAN"
        )
        data.uVersion = NOTIFYICON_VERSION_4
        return data

    def _add_icon(self) -> None:
        if not self._hwnd:
            return
        data = self._notification_data()
        if shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(data)):
            self._icon_added = True
            shell32.Shell_NotifyIconW(NIM_SETVERSION, ctypes.byref(data))

    def _modify_icon(self) -> None:
        if not self._icon_added:
            self._add_icon()
            return
        data = self._notification_data()
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(data))

    def _delete_icon(self) -> None:
        if not self._icon_added or not self._hwnd:
            return
        data = self._notification_data()
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(data))
        self._icon_added = False

    @staticmethod
    def _line_distance(
        x: float,
        y: float,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> float:
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(x - x1, y - y1)
        position = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        position = max(0.0, min(1.0, position))
        nearest_x = x1 + position * dx
        nearest_y = y1 + position * dy
        return math.hypot(x - nearest_x, y - nearest_y)

    def _create_state_icon(self, active: bool) -> int:
        width = 32
        height = 32
        pixels = bytearray(width * height * 4)
        base = (36, 107, 254) if active else (100, 116, 139)

        for y in range(height):
            for x in range(width):
                dx = x + 0.5 - width / 2
                dy = y + 0.5 - height / 2
                inside = dx * dx + dy * dy <= 14 * 14
                white = False
                if active:
                    white = (
                        self._line_distance(x, y, 8, 16, 13, 21) <= 1.6
                        or self._line_distance(x, y, 13, 21, 24, 10) <= 1.6
                    )
                else:
                    white = 9 <= x <= 23 and 14 <= y <= 17

                offset = (y * width + x) * 4
                if white and inside:
                    red, green, blue, alpha = 255, 255, 255, 255
                elif inside:
                    red, green, blue = base
                    alpha = 255
                else:
                    red, green, blue, alpha = 0, 0, 0, 0
                pixels[offset : offset + 4] = bytes((blue, green, red, alpha))

        bitmap_info = BITMAPINFO()
        bitmap_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bitmap_info.bmiHeader.biWidth = width
        bitmap_info.bmiHeader.biHeight = -height
        bitmap_info.bmiHeader.biPlanes = 1
        bitmap_info.bmiHeader.biBitCount = 32
        bitmap_info.bmiHeader.biCompression = BI_RGB
        bitmap_info.bmiHeader.biSizeImage = len(pixels)

        bits = ctypes.c_void_p()
        color_bitmap = gdi32.CreateDIBSection(
            None,
            ctypes.byref(bitmap_info),
            DIB_RGB_COLORS,
            ctypes.byref(bits),
            None,
            0,
        )
        if not color_bitmap or not bits:
            raise ctypes.WinError(ctypes.get_last_error())
        ctypes.memmove(bits, bytes(pixels), len(pixels))

        mask_data = (ctypes.c_ubyte * 128)()
        mask_bitmap = gdi32.CreateBitmap(
            width,
            height,
            1,
            1,
            ctypes.byref(mask_data),
        )
        if not mask_bitmap:
            gdi32.DeleteObject(color_bitmap)
            raise ctypes.WinError(ctypes.get_last_error())

        icon_info = ICONINFO(
            fIcon=True,
            xHotspot=0,
            yHotspot=0,
            hbmMask=mask_bitmap,
            hbmColor=color_bitmap,
        )
        icon = user32.CreateIconIndirect(ctypes.byref(icon_info))
        gdi32.DeleteObject(mask_bitmap)
        gdi32.DeleteObject(color_bitmap)
        if not icon:
            raise ctypes.WinError(ctypes.get_last_error())
        return int(icon)


__all__ = ["WindowsTrayIcon"]
