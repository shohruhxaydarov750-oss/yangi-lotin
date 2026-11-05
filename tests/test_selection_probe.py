"""Selection probes must distinguish Chrome completion from a plain caret."""

import unittest

from yangi_lotin.selection_probe import SelectionStatus, _inspect_selection


class _Range:
    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end

    def CompareEndpoints(self, endpoint: int, other: "_Range", other_endpoint: int) -> int:
        left = self.start if endpoint == 0 else self.end
        right = other.start if other_endpoint == 0 else other.end
        return (left > right) - (left < right)

    def GetText(self, _length: int) -> str:
        raise AssertionError("The probe must never read text")


class _Ranges:
    def __init__(self, *ranges: _Range) -> None:
        self.values = ranges
        self.Length = len(ranges)

    def GetElement(self, index: int) -> _Range:
        return self.values[index]


class _Pattern:
    def __init__(self, document_end: int, *selected: _Range) -> None:
        self.DocumentRange = _Range(0, document_end)
        self.ranges = _Ranges(*selected)

    def GetSelection(self) -> _Ranges:
        return self.ranges

    def QueryInterface(self, _interface: object) -> "_Pattern":
        return self


class _Focused:
    CurrentIsPassword = False
    CurrentControlType = 50004

    def __init__(self, pattern: _Pattern) -> None:
        self.pattern = pattern

    def GetCurrentPattern(self, _id: int) -> _Pattern:
        return self.pattern


class _Automation:
    def __init__(self, focused: _Focused) -> None:
        self.focused = focused

    def GetFocusedElement(self) -> _Focused:
        return self.focused


class _UIA:
    UIA_EditControlTypeId = 50004
    UIA_TextPatternId = 10014
    IUIAutomationTextPattern = object()
    TextPatternRangeEndpoint_Start = 0
    TextPatternRangeEndpoint_End = 1


class SelectionProbeTests(unittest.TestCase):
    def test_omnibox_completion_ends_at_document_end(self) -> None:
        cases = (
            (_Pattern(8, _Range(2, 8)), SelectionStatus.SUFFIX),
            (_Pattern(8, _Range(2, 2)), SelectionStatus.CARET),
            (_Pattern(8), SelectionStatus.UNAVAILABLE),
            (_Pattern(8, _Range(2, 5)), SelectionStatus.OTHER_SELECTION),
        )
        for pattern, expected in cases:
            with self.subTest(expected=expected):
                self.assertIs(
                    _inspect_selection(_Automation(_Focused(pattern)), _UIA),
                    expected,
                )

    def test_password_and_unsupported_controls_are_not_inspected(self) -> None:
        password = _Focused(_Pattern(8, _Range(2, 8)))
        password.CurrentIsPassword = True
        self.assertIs(
            _inspect_selection(_Automation(password), _UIA),
            SelectionStatus.UNAVAILABLE,
        )
        document = _Focused(_Pattern(8, _Range(2, 8)))
        document.CurrentControlType = 50030
        self.assertIs(
            _inspect_selection(_Automation(document), _UIA),
            SelectionStatus.UNAVAILABLE,
        )


if __name__ == "__main__":
    unittest.main()
