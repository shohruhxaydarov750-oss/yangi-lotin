"""System-wide, real-time Uzbek script conversion for Windows.

The Win32 hook adapter keeps only the unfinished current word in memory. It
does not log, persist, or transmit keystrokes. The pure LiveComposer is kept
separate so contextual transliteration remains thoroughly testable.
"""

from __future__ import annotations

import ctypes
import os
import threading
import unicodedata
from collections.abc import Callable
from ctypes import wintypes
from dataclasses import dataclass

from .reverse import latin_to_cyrillic
from .transliterator import (
    is_live_source_character,
    modernize_old_latin,
    to_new_latin,
    transliterate,
)


@dataclass(frozen=True)
class EditPlan:
    """Minimal edit required to replace the previously rendered token."""

    backspaces: int
    insert: str


class LiveComposer:
    """Incrementally render one source token with contextual corrections."""

    def __init__(
        self,
        max_token_length: int = 128,
        renderer: Callable[[str], str] = transliterate,
    ) -> None:
        self.max_token_length = max_token_length
        self._renderer = renderer
        self.source_token = ""
        self.rendered_token = ""

    @property
    def has_token(self) -> bool:
        return bool(self.source_token)

    @staticmethod
    def _edit_between(previous: str, current: str) -> EditPlan:
        prefix_length = 0
        limit = min(len(previous), len(current))
        while prefix_length < limit and previous[prefix_length] == current[prefix_length]:
            prefix_length += 1
        return EditPlan(
            backspaces=len(previous) - prefix_length,
            insert=current[prefix_length:],
        )

    def feed(self, character: str) -> EditPlan:
        if len(character) != 1:
            raise ValueError("feed() accepts exactly one character")

        if len(self.source_token) >= self.max_token_length:
            # Extremely long uninterrupted tokens are committed. Keeping a
            # bounded token makes the low-level callback predictably fast.
            self.reset()

        previous = self.rendered_token
        self.source_token += character
        self.rendered_token = self._renderer(self.source_token)
        return self._edit_between(previous, self.rendered_token)

    def backspace(self) -> EditPlan:
        if not self.source_token:
            return EditPlan(0, "")

        previous = self.rendered_token
        self.source_token = self.source_token[:-1]
        self.rendered_token = self._renderer(self.source_token)
        return self._edit_between(previous, self.rendered_token)

    def reset(self) -> None:
        self.source_token = ""
        self.rendered_token = ""


class KeyboardCaseTracker:
    """Track Caps Lock presses without relying on another thread's key state."""

    def __init__(self, caps_on: bool = False) -> None:
        self.caps_on = bool(caps_on)
        self._caps_down = False
        self._shift_keys_down: set[int] = set()

    def observe_caps(self, pressed: bool) -> None:
        if pressed and not self._caps_down:
            self.caps_on = not self.caps_on
        self._caps_down = pressed

    def observe_shift(self, key: int, pressed: bool) -> None:
        if pressed:
            self._shift_keys_down.add(key)
        else:
            self._shift_keys_down.discard(key)

    @property
    def shift_down(self) -> bool:
        return bool(self._shift_keys_down)


WINDOWS = os.name == "nt"

if WINDOWS:
    LRESULT = ctypes.c_ssize_t
    ULONG_PTR = ctypes.c_size_t
    HHOOK = ctypes.c_void_p
    HINSTANCE = ctypes.c_void_p

    WH_KEYBOARD_LL = 13
    WH_MOUSE_LL = 14
    HC_ACTION = 0

    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    WM_SYSKEYDOWN = 0x0104
    WM_SYSKEYUP = 0x0105
    WM_QUIT = 0x0012

    WM_LBUTTONDOWN = 0x0201
    WM_RBUTTONDOWN = 0x0204
    WM_MBUTTONDOWN = 0x0207
    WM_MOUSEWHEEL = 0x020A
    WM_XBUTTONDOWN = 0x020B
    WM_MOUSEHWHEEL = 0x020E

    VK_BACK = 0x08
    VK_SHIFT = 0x10
    VK_LSHIFT = 0xA0
    VK_RSHIFT = 0xA1
    VK_CONTROL = 0x11
    VK_MENU = 0x12
    VK_CAPITAL = 0x14
    VK_PACKET = 0xE7
    VK_LWIN = 0x5B
    VK_RWIN = 0x5C

    GWL_STYLE = -16
    ES_PASSWORD = 0x0020

    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    INPUT_KEYBOARD = 1
    PM_NOREMOVE = 0x0000

    INJECTION_MARKER = 0x594C4154

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class MSLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("pt", wintypes.POINT),
            ("mouseData", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND),
            ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND),
            ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND),
            ("hwndCaret", wintypes.HWND),
            ("rcCaret", wintypes.RECT),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class INPUTUNION(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("mi", MOUSEINPUT),
            ("hi", HARDWAREINPUT),
        ]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("union",)
        _fields_ = [("type", wintypes.DWORD), ("union", INPUTUNION)]

    HOOKPROC = ctypes.WINFUNCTYPE(
        LRESULT,
        ctypes.c_int,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.SetWindowsHookExW.argtypes = [
        ctypes.c_int,
        HOOKPROC,
        HINSTANCE,
        wintypes.DWORD,
    ]
    user32.SetWindowsHookExW.restype = HHOOK
    user32.CallNextHookEx.argtypes = [
        HHOOK,
        ctypes.c_int,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.CallNextHookEx.restype = LRESULT
    user32.UnhookWindowsHookEx.argtypes = [HHOOK]
    user32.UnhookWindowsHookEx.restype = wintypes.BOOL
    user32.GetMessageW.argtypes = [
        ctypes.POINTER(wintypes.MSG),
        wintypes.HWND,
        wintypes.UINT,
        wintypes.UINT,
    ]
    user32.GetMessageW.restype = ctypes.c_int
    user32.PeekMessageW.argtypes = [
        ctypes.POINTER(wintypes.MSG),
        wintypes.HWND,
        wintypes.UINT,
        wintypes.UINT,
        wintypes.UINT,
    ]
    user32.PeekMessageW.restype = wintypes.BOOL
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.PostThreadMessageW.argtypes = [
        wintypes.DWORD,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.PostThreadMessageW.restype = wintypes.BOOL
    user32.SendInput.argtypes = [
        wintypes.UINT,
        ctypes.POINTER(INPUT),
        ctypes.c_int,
    ]
    user32.SendInput.restype = wintypes.UINT
    user32.GetKeyState.argtypes = [ctypes.c_int]
    user32.GetKeyState.restype = ctypes.c_short
    user32.ToUnicodeEx.argtypes = [
        wintypes.UINT,
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_ubyte),
        wintypes.LPWSTR,
        ctypes.c_int,
        wintypes.UINT,
        ctypes.c_void_p,
    ]
    user32.ToUnicodeEx.restype = ctypes.c_int
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    user32.GetKeyboardLayout.restype = ctypes.c_void_p
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short

    user32.GetGUIThreadInfo.argtypes = [
        wintypes.DWORD,
        ctypes.POINTER(GUITHREADINFO),
    ]
    user32.GetGUIThreadInfo.restype = wintypes.BOOL

    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int

    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t

    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = HINSTANCE
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD


class LiveKeyboardTransliterator:
    """Windows hook that replaces typed text according to the selected direction."""

    def __init__(self, enabled: bool = True) -> None:
        self._cyrillic_enabled = bool(enabled)
        self._old_latin_enabled = bool(enabled)
        self._latin_to_cyrillic_enabled = False
        self._lock = threading.RLock()
        self._composer = LiveComposer(renderer=to_new_latin)
        self._case_tracker = KeyboardCaseTracker()
        self._foreground_hwnd = 0
        self._suppressed_keys: set[tuple[int, int]] = set()
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._keyboard_hook = None
        self._mouse_hook = None
        self._keyboard_proc = None
        self._mouse_proc = None
        self._ready = threading.Event()
        self._startup_error: BaseException | None = None
        self._injecting = False

    @property
    def enabled(self) -> bool:
        with self._lock:
            return (
                self._cyrillic_enabled
                or self._old_latin_enabled
                or self._latin_to_cyrillic_enabled
            )

    @property
    def modes(self) -> tuple[bool, bool, bool]:
        with self._lock:
            return (
                self._cyrillic_enabled,
                self._old_latin_enabled,
                self._latin_to_cyrillic_enabled,
            )

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def set_enabled(self, enabled: bool) -> None:
        self.set_modes(enabled, enabled)

    def set_modes(
        self,
        cyrillic: bool,
        old_latin: bool,
        latin_to_cyrillic_enabled: bool = False,
    ) -> None:
        if latin_to_cyrillic_enabled and (cyrillic or old_latin):
            raise ValueError("Opposite conversion directions cannot run together")
        with self._lock:
            self._cyrillic_enabled = bool(cyrillic)
            self._old_latin_enabled = bool(old_latin)
            self._latin_to_cyrillic_enabled = bool(latin_to_cyrillic_enabled)
            if self._latin_to_cyrillic_enabled:
                renderer = latin_to_cyrillic
            elif self._cyrillic_enabled and self._old_latin_enabled:
                renderer = to_new_latin
            elif self._old_latin_enabled:
                renderer = modernize_old_latin
            else:
                renderer = transliterate
            self._composer = LiveComposer(renderer=renderer)
            self._reset_locked()

    def toggle(self) -> bool:
        enabled = not self.enabled
        self.set_enabled(enabled)
        return enabled

    def start(self, timeout: float = 4.0) -> None:
        if not WINDOWS:
            raise OSError("Real-time mode is available only on Windows")
        if self.running:
            return

        self._ready.clear()
        self._startup_error = None
        self._thread = threading.Thread(
            target=self._hook_thread,
            name="YangiLotinKeyboardHook",
            daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(timeout):
            raise TimeoutError("Windows keyboard hook did not start in time")
        if self._startup_error is not None:
            raise RuntimeError("Windows keyboard hook could not start") from self._startup_error

    def stop(self, timeout: float = 4.0) -> None:
        self.set_enabled(False)
        thread = self._thread
        if not thread:
            return
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if thread is not threading.current_thread():
            thread.join(timeout)
        # Keep the reference when a blocked Windows callback has not exited
        # yet. That prevents start() from creating a second global hook.
        if not thread.is_alive():
            self._thread = None

    def _reset_locked(self) -> None:
        self._composer.reset()
        self._foreground_hwnd = 0
        self._suppressed_keys.clear()

    def _reset(self) -> None:
        with self._lock:
            self._reset_locked()

    def _hook_thread(self) -> None:
        try:
            self._thread_id = int(kernel32.GetCurrentThreadId())
            message = wintypes.MSG()
            user32.PeekMessageW(ctypes.byref(message), None, 0, 0, PM_NOREMOVE)

            with self._lock:
                self._case_tracker = KeyboardCaseTracker(
                    bool(user32.GetKeyState(VK_CAPITAL) & 1)
                )

            self._keyboard_proc = HOOKPROC(self._keyboard_callback)
            self._mouse_proc = HOOKPROC(self._mouse_callback)
            module = kernel32.GetModuleHandleW(None)
            self._keyboard_hook = user32.SetWindowsHookExW(
                WH_KEYBOARD_LL,
                self._keyboard_proc,
                module,
                0,
            )
            if not self._keyboard_hook:
                raise ctypes.WinError(ctypes.get_last_error())

            self._mouse_hook = user32.SetWindowsHookExW(
                WH_MOUSE_LL,
                self._mouse_proc,
                module,
                0,
            )
            if not self._mouse_hook:
                raise ctypes.WinError(ctypes.get_last_error())

            self._ready.set()
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
            if self._mouse_hook:
                user32.UnhookWindowsHookEx(self._mouse_hook)
            if self._keyboard_hook:
                user32.UnhookWindowsHookEx(self._keyboard_hook)
            self._mouse_hook = None
            self._keyboard_hook = None
            self._thread_id = 0
            self._reset()

    def _mouse_callback(self, n_code: int, w_param: int, l_param: int) -> int:
        try:
            if n_code == HC_ACTION and int(w_param) in {
                WM_LBUTTONDOWN,
                WM_RBUTTONDOWN,
                WM_MBUTTONDOWN,
                WM_XBUTTONDOWN,
                WM_MOUSEWHEEL,
                WM_MOUSEHWHEEL,
            }:
                self._reset()
        except BaseException:
            self._reset()
        return int(user32.CallNextHookEx(self._mouse_hook, n_code, w_param, l_param))

    def _keyboard_callback(self, n_code: int, w_param: int, l_param: int) -> int:
        try:
            if n_code != HC_ACTION:
                return int(
                    user32.CallNextHookEx(
                        self._keyboard_hook,
                        n_code,
                        w_param,
                        l_param,
                    )
                )

            event = int(w_param)
            data = ctypes.cast(
                l_param,
                ctypes.POINTER(KBDLLHOOKSTRUCT),
            ).contents

            # Our own SendInput events are tagged. Other injected input is
            # allowed so accessibility keyboards still work.
            if int(data.dwExtraInfo) == INJECTION_MARKER or self._injecting:
                return int(
                    user32.CallNextHookEx(
                        self._keyboard_hook,
                        n_code,
                        w_param,
                        l_param,
                    )
                )

            key_id = (int(data.vkCode), int(data.scanCode))
            if event in {WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP}:
                with self._lock:
                    pressed = event in {WM_KEYDOWN, WM_SYSKEYDOWN}
                    if key_id[0] == VK_CAPITAL:
                        self._case_tracker.observe_caps(pressed)
                    elif key_id[0] in {VK_SHIFT, VK_LSHIFT, VK_RSHIFT}:
                        self._case_tracker.observe_shift(key_id[0], pressed)
            if event in {WM_KEYUP, WM_SYSKEYUP}:
                with self._lock:
                    if key_id in self._suppressed_keys:
                        self._suppressed_keys.discard(key_id)
                        return 1
                return int(
                    user32.CallNextHookEx(
                        self._keyboard_hook,
                        n_code,
                        w_param,
                        l_param,
                    )
                )

            if event not in {WM_KEYDOWN, WM_SYSKEYDOWN}:
                return int(
                    user32.CallNextHookEx(
                        self._keyboard_hook,
                        n_code,
                        w_param,
                        l_param,
                    )
                )

            with self._lock:
                if not (
                    self._cyrillic_enabled
                    or self._old_latin_enabled
                    or self._latin_to_cyrillic_enabled
                ):
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )

                hwnd, belongs_to_this_process = self._foreground_window_info()
                if belongs_to_this_process:
                    self._reset_locked()
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )
                if hwnd != self._foreground_hwnd:
                    self._composer.reset()
                    self._foreground_hwnd = hwnd

                if self._focused_password_field(hwnd):
                    self._composer.reset()
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )

                vk_code = int(data.vkCode)
                if vk_code in {VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN}:
                    self._composer.reset()
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )

                if self._disallowed_modifier_down():
                    self._composer.reset()
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )

                if vk_code == VK_BACK:
                    if not self._composer.has_token:
                        return int(
                            user32.CallNextHookEx(
                                self._keyboard_hook,
                                n_code,
                                w_param,
                                l_param,
                            )
                        )
                    plan = self._composer.backspace()
                    sent, expected = self._inject_edit(plan)
                    if sent == expected:
                        self._suppressed_keys.add(key_id)
                        return 1
                    self._composer.reset()
                    if sent:
                        self._suppressed_keys.add(key_id)
                        return 1
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )

                if vk_code in {VK_SHIFT, VK_LSHIFT, VK_RSHIFT, VK_CAPITAL}:
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )

                character = self._decode_character(data, hwnd)
                if character:
                    character = unicodedata.normalize("NFC", character)
                if not character or not is_live_source_character(
                    character,
                    self._cyrillic_enabled,
                    self._old_latin_enabled,
                    self._latin_to_cyrillic_enabled,
                ):
                    self._composer.reset()
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )

                if len(character) != 1:
                    self._composer.reset()
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )

                plan = self._composer.feed(character)
                # A leading s/c/o/g can be replaced by sh/ch/o'/g'. Send
                # that first letter through the same input stream as its
                # later replacement. Passing the physical first key through
                # can let a browser process it after our injected Backspace.
                pair_prefix = (
                    self._old_latin_enabled
                    and character.casefold() in {"s", "c", "o", "g"}
                )
                if plan == EditPlan(0, character) and not pair_prefix:
                    return int(
                        user32.CallNextHookEx(
                            self._keyboard_hook,
                            n_code,
                            w_param,
                            l_param,
                        )
                    )
                sent, expected = self._inject_edit(plan)
                if sent == expected:
                    self._suppressed_keys.add(key_id)
                    return 1

                self._composer.reset()
                if sent:
                    self._suppressed_keys.add(key_id)
                    return 1
        except BaseException:
            self._reset()

        return int(
            user32.CallNextHookEx(
                self._keyboard_hook,
                n_code,
                w_param,
                l_param,
            )
        )

    def _foreground_window_info(self) -> tuple[int, bool]:
        hwnd = int(user32.GetForegroundWindow() or 0)
        process_id = wintypes.DWORD()
        if hwnd:
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        return hwnd, process_id.value == os.getpid()

    def _disallowed_modifier_down(self) -> bool:
        return any(
            user32.GetAsyncKeyState(vk_code) & 0x8000
            for vk_code in (VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN)
        )

    @staticmethod
    def _focused_password_field(hwnd: int) -> bool:
        """Leave native Windows password edits untouched, without reading text.

        Custom web and app controls may not expose the native Edit style, so
        the visible tray pause remains necessary for those fields.
        """

        process_id = wintypes.DWORD()
        thread_id = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if not thread_id:
            return False
        info = GUITHREADINFO()
        info.cbSize = ctypes.sizeof(GUITHREADINFO)
        if not user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)):
            return False
        focus = info.hwndFocus
        if not focus:
            return False
        class_name = ctypes.create_unicode_buffer(64)
        if not user32.GetClassNameW(focus, class_name, len(class_name)):
            return False
        kind = class_name.value.casefold()
        if kind != "edit" and not kind.startswith("richedit"):
            return False
        return bool(user32.GetWindowLongPtrW(focus, GWL_STYLE) & ES_PASSWORD)

    def _decode_character(self, data: KBDLLHOOKSTRUCT, hwnd: int) -> str:
        if int(data.vkCode) == VK_PACKET:
            # KEYEVENTF_UNICODE delivers a UTF-16 unit in the scan-code field.
            # This covers letters from Unicode keyboards and input methods.
            unit = int(data.scanCode)
            return chr(unit) if 0 < unit <= 0xFFFF and not 0xD800 <= unit <= 0xDFFF else ""

        # GetKeyboardState reads the *hook thread's* message history. That can
        # lag behind the foreground app and mistake lowercase for uppercase.
        # Supply a fresh state for this event instead.
        keyboard_state = (ctypes.c_ubyte * 256)()
        keyboard_state[int(data.vkCode)] |= 0x80
        if self._case_tracker.shift_down or user32.GetAsyncKeyState(VK_SHIFT) & 0x8000:
            keyboard_state[VK_SHIFT] |= 0x80
        if self._case_tracker.caps_on:
            keyboard_state[VK_CAPITAL] |= 1

        process_id = wintypes.DWORD()
        thread_id = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        layout = user32.GetKeyboardLayout(thread_id)
        buffer = ctypes.create_unicode_buffer(8)
        count = user32.ToUnicodeEx(
            int(data.vkCode),
            int(data.scanCode),
            keyboard_state,
            buffer,
            len(buffer),
            4,
            layout,
        )
        if count != 1:
            return ""
        return buffer[0]

    @staticmethod
    def _keyboard_input(vk_code: int, scan_code: int, flags: int) -> INPUT:
        return INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=vk_code,
                wScan=scan_code,
                dwFlags=flags,
                time=0,
                dwExtraInfo=INJECTION_MARKER,
            ),
        )

    def _inject_edit(self, plan: EditPlan) -> tuple[int, int]:
        inputs: list[INPUT] = []
        for _ in range(plan.backspaces):
            inputs.append(self._keyboard_input(VK_BACK, 0, 0))
            inputs.append(self._keyboard_input(VK_BACK, 0, KEYEVENTF_KEYUP))

        utf16 = plan.insert.encode("utf-16-le", errors="surrogatepass")
        for offset in range(0, len(utf16), 2):
            unit = int.from_bytes(utf16[offset : offset + 2], "little")
            inputs.append(self._keyboard_input(0, unit, KEYEVENTF_UNICODE))
            inputs.append(
                self._keyboard_input(
                    0,
                    unit,
                    KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                )
            )

        if not inputs:
            return 0, 0

        array_type = INPUT * len(inputs)
        input_array = array_type(*inputs)
        self._injecting = True
        try:
            sent = int(
                user32.SendInput(
                    len(inputs),
                    input_array,
                    ctypes.sizeof(INPUT),
                )
            )
        finally:
            self._injecting = False
        return sent, len(inputs)


__all__ = [
    "EditPlan", "LiveComposer", "KeyboardCaseTracker", "LiveKeyboardTransliterator"
]
