"""Inspect only the focused text selection, without reading its contents.

Chromium's address bar selects an inline completion after the text the user
typed. A global keyboard hook cannot infer that selection from key events.
UI Automation runs on a separate MTA thread because a provider can be slow;
the hook waits for a small, fixed budget and leaves the physical key alone if
the answer is unavailable.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from enum import Enum


class SelectionStatus(Enum):
    CARET = "caret"
    SUFFIX = "suffix"
    OTHER_SELECTION = "other_selection"
    UNAVAILABLE = "unavailable"


@dataclass
class _Request:
    done: threading.Event = field(default_factory=threading.Event)
    result: SelectionStatus = SelectionStatus.UNAVAILABLE


def _inspect_selection(automation: object, uia: object) -> SelectionStatus:
    """Return the selection shape, never the selected or document text."""

    try:
        focused = automation.GetFocusedElement()
        if focused is None or focused.CurrentIsPassword:
            return SelectionStatus.UNAVAILABLE
        if focused.CurrentControlType != uia.UIA_EditControlTypeId:
            return SelectionStatus.UNAVAILABLE
        unknown = focused.GetCurrentPattern(uia.UIA_TextPatternId)
        pattern = unknown.QueryInterface(uia.IUIAutomationTextPattern)
        ranges = pattern.GetSelection()
        if ranges is None:
            return SelectionStatus.UNAVAILABLE
        if ranges.Length == 0:
            return SelectionStatus.UNAVAILABLE
        if ranges.Length != 1:
            return SelectionStatus.OTHER_SELECTION
        selected = ranges.GetElement(0)
        start = uia.TextPatternRangeEndpoint_Start
        end = uia.TextPatternRangeEndpoint_End
        span = selected.CompareEndpoints(start, selected, end)
        if span == 0:
            return SelectionStatus.CARET
        if span > 0:
            return SelectionStatus.UNAVAILABLE
        document = pattern.DocumentRange
        if selected.CompareEndpoints(end, document, end) == 0:
            return SelectionStatus.SUFFIX
        return SelectionStatus.OTHER_SELECTION
    except Exception:
        return SelectionStatus.UNAVAILABLE


class SelectionProbe:
    """Bounded request/response bridge to a persistent COM MTA worker."""

    def __init__(self) -> None:
        self._requests: queue.Queue[_Request] = queue.Queue(maxsize=1)
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._available = False
        self.startup_error: BaseException | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._ready.clear()
        self._available = False
        self.startup_error = None
        self._thread = threading.Thread(
            target=self._run,
            name="YangiLotinSelectionProbe",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=0.2)
        if thread is not None and not thread.is_alive():
            self._thread = None

    def wait_ready(self, timeout: float = 5.0) -> bool:
        """Check COM initialization without inspecting any application text."""

        return self._ready.wait(timeout) and self._available

    def query(self, timeout: float = 0.08) -> SelectionStatus:
        if not self._ready.is_set() or not self._available:
            return SelectionStatus.UNAVAILABLE
        request = _Request()
        try:
            self._requests.put_nowait(request)
        except queue.Full:
            return SelectionStatus.UNAVAILABLE
        if not request.done.wait(timeout):
            return SelectionStatus.UNAVAILABLE
        return request.result

    def _run(self) -> None:
        initialized = False
        automation = None
        try:
            import sys

            first_import = "comtypes" not in sys.modules
            # comtypes initializes the importing thread at import time.
            # Its default is STA; UI Automation clients need an MTA worker.
            sys.coinit_flags = 0
            import comtypes
            from comtypes.client import CreateObject, GetModule

            if not first_import:
                comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
            initialized = True
            GetModule("UIAutomationCore.dll")
            from comtypes.gen import UIAutomationClient as uia

            automation = CreateObject(uia.CUIAutomation, interface=uia.IUIAutomation)
            self._available = True
            self._ready.set()
            while not self._stop.is_set():
                try:
                    request = self._requests.get(timeout=0.1)
                except queue.Empty:
                    continue
                request.result = _inspect_selection(automation, uia)
                request.done.set()
        except Exception as error:
            self.startup_error = error
            self._available = False
            self._ready.set()
        finally:
            if initialized:
                # Release COM pointers on their owning thread, before COM
                # itself is uninitialized. Releasing later can crash Python.
                automation = None
                comtypes.CoUninitialize()


__all__ = ["SelectionProbe", "SelectionStatus"]
