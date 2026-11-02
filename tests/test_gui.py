from __future__ import annotations

import unittest
from unittest import mock

from yangi_lotin.gui import ConverterApp, Palette
from yangi_lotin.mode_state import ModeSelection, ModeSnapshot


class ManualConverterStateTests(unittest.TestCase):
    def test_manual_source_follows_last_selected_direction_on_open(self) -> None:
        for selection, expected in (
            (ModeSelection(True, True), "Ikkalasi"),
            (ModeSelection(True, False), "Kirill"),
            (ModeSelection(False, True), "Eski lotin"),
            (
                ModeSelection(False, False, latin_to_cyrillic=True),
                "Lotin → kirill",
            ),
            (
                ModeSelection(
                    False,
                    False,
                    last_nonempty=ModeSnapshot(False, False, True),
                ),
                "Lotin → kirill",
            ),
        ):
            with self.subTest(selection=selection.current, expected=expected):
                app = ConverterApp.__new__(ConverterApp)
                app._modes = selection
                self.assertEqual(app._initial_manual_source(), expected)

    def test_edit_clears_stale_output_before_it_can_be_copied(self) -> None:
        app = ConverterApp.__new__(ConverterApp)
        app.input_text = mock.Mock()
        app.input_text.edit_modified.return_value = True
        app.input_text.get.return_value = "new text"
        app.input_count = mock.Mock()
        app.output_text = mock.Mock()
        app.output_text.get.return_value = "old result"
        app._set_output = mock.Mock()
        app._refresh_placeholder = mock.Mock()

        app._input_modified(None)

        app._set_output.assert_called_once_with("")
        app.input_count.configure.assert_called_once_with(text="8 belgi · 2 söz")

    def test_background_failure_remains_visible_after_transient_status(self) -> None:
        app = ConverterApp.__new__(ConverterApp)
        app.root = mock.Mock()
        app.root.after.return_value = "timer"
        app.status = mock.Mock()
        app._status_timer = None
        app._persistent_status = None

        app._set_status("Tray ikonka işga tüşmadi", Palette.WARNING, persistent=True)
        app._set_status("Matn qöyildi")
        app._reset_status()

        self.assertEqual(
            app.status.configure.call_args,
            mock.call(text="Tray ikonka işga tüşmadi", foreground=Palette.WARNING),
        )


if __name__ == "__main__":
    unittest.main()
