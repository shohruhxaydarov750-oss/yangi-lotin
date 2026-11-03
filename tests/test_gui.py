from __future__ import annotations

import unittest
from unittest import mock
import tkinter as tk

from yangi_lotin.gui import ConverterApp, Palette
from yangi_lotin.mode_state import ModeSelection, ModeSnapshot


class ManualConverterStateTests(unittest.TestCase):
    def test_manual_target_follows_last_selected_direction_on_open(self) -> None:
        for selection, expected in (
            (ModeSelection(True, True), "new_latin"),
            (ModeSelection(True, False), "new_latin"),
            (ModeSelection(False, True), "new_latin"),
            (
                ModeSelection(False, False, latin_to_cyrillic=True),
                "cyrillic",
            ),
            (
                ModeSelection(
                    False,
                    False,
                    last_nonempty=ModeSnapshot(False, False, True),
                ),
                "cyrillic",
            ),
        ):
            with self.subTest(selection=selection.current, expected=expected):
                app = ConverterApp.__new__(ConverterApp)
                app._modes = selection
                self.assertEqual(app._initial_manual_target(), expected)

    def test_manual_targets_accept_both_forms_of_their_input_script(self) -> None:
        app = ConverterApp.__new__(ConverterApp)
        app.input_text = mock.Mock()
        app._set_output = mock.Mock()
        app._set_status = mock.Mock()

        app.manual_target = "new_latin"
        app.input_text.get.return_value = "салом shahar o'zbek"
        app.convert()
        app._set_output.assert_called_with("salom şahar özbek")

        app.manual_target = "cyrillic"
        app.input_text.get.return_value = "salom şahar"
        app.convert()
        app._set_output.assert_called_with("салом шаҳар")

    def test_changing_target_reconverts_existing_text(self) -> None:
        app = ConverterApp.__new__(ConverterApp)
        app.manual_target = "new_latin"
        app.input_text = mock.Mock()
        app.input_text.get.return_value = "salom"
        app._update_manual_target_ui = mock.Mock()
        app._invalidate_output = mock.Mock()
        app.convert = mock.Mock()

        app._select_manual_target("cyrillic")

        self.assertEqual(app.manual_target, "cyrillic")
        app._update_manual_target_ui.assert_called_once_with()
        app._invalidate_output.assert_called_once_with()
        app.convert.assert_called_once_with()
        app.input_text.focus_set.assert_called_once_with()

    def test_ctrl_v_is_bound_before_text_default_and_pastes_once(self) -> None:
        app = ConverterApp.__new__(ConverterApp)
        app.root = mock.Mock()
        app.input_text = mock.Mock()
        app.output_text = mock.Mock()
        app.paste = mock.Mock()
        app.convert = mock.Mock()
        app.copy = mock.Mock()
        app.clear = mock.Mock()

        app._bind_shortcuts()

        input_paste = next(
            call.args[1]
            for call in app.input_text.bind.call_args_list
            if call.args[0] == "<Control-v>"
        )
        self.assertEqual(input_paste(mock.Mock()), "break")
        app.paste.assert_called_once_with()
        self.assertIn(
            "<Control-v>",
            [call.args[0] for call in app.root.bind_all.call_args_list],
        )

    def test_paste_inserts_into_input_and_immediately_converts(self) -> None:
        app = ConverterApp.__new__(ConverterApp)
        app.root = mock.Mock()
        app.root.clipboard_get.return_value = "shahar"
        app.input_text = mock.Mock()
        app.input_text.index.side_effect = tk.TclError("no selection")
        app.input_text.get.return_value = "shahar"
        app._input_modified = mock.Mock()
        app.convert = mock.Mock()

        app.paste()

        app.input_text.insert.assert_called_once_with("insert", "shahar")
        app._input_modified.assert_called_once_with(None)
        app.convert.assert_called_once_with()
        app.input_text.focus_set.assert_called_once_with()

    def test_enter_converts_and_shift_enter_inserts_line_break(self) -> None:
        app = ConverterApp.__new__(ConverterApp)
        app.root = mock.Mock()
        app.input_text = mock.Mock()
        app.output_text = mock.Mock()
        app.paste = mock.Mock()
        app.convert = mock.Mock()
        app.copy = mock.Mock()
        app.clear = mock.Mock()

        app._bind_shortcuts()

        enter = next(
            call.args[1]
            for call in app.input_text.bind.call_args_list
            if call.args[0] == "<Return>"
        )
        self.assertEqual(enter(mock.Mock()), "break")
        app.convert.assert_called_once_with()
        self.assertEqual(app._insert_paragraph_break(mock.Mock()), "break")
        app.input_text.insert.assert_called_once_with("insert", "\n")

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
