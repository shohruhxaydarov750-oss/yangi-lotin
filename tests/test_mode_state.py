from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from yangi_lotin.mode_state import ModeSelection, ModeSnapshot
from yangi_lotin.tray import WindowsTrayIcon


class ModeSelectionTests(unittest.TestCase):
    def test_reverse_mode_is_exclusive_and_tray_restores_it(self) -> None:
        selection = ModeSelection()
        self.assertEqual(
            selection.toggle_mode("latin_to_cyrillic"),
            ModeSnapshot(False, False, True),
        )
        self.assertEqual(selection.toggle_all(), ModeSnapshot(False, False))
        self.assertEqual(selection.toggle_all(), ModeSnapshot(False, False, True))
        self.assertEqual(
            selection.toggle_mode("old_latin"), ModeSnapshot(False, True)
        )
        with self.assertRaises(ValueError):
            selection.set_modes(True, False, True)

    def test_independent_switches_and_one_click_restore(self) -> None:
        selection = ModeSelection()
        self.assertEqual(selection.toggle_mode("old_latin"), ModeSnapshot(True, False))
        self.assertEqual(selection.toggle_all(), ModeSnapshot(False, False))
        self.assertEqual(selection.toggle_all(), ModeSnapshot(True, False))
        self.assertEqual(selection.toggle_mode("cyrillic"), ModeSnapshot(False, False))
        self.assertEqual(selection.toggle_all(), ModeSnapshot(True, False))

    def test_switching_one_mode_does_not_enable_the_other(self) -> None:
        selection = ModeSelection(False, False, ModeSnapshot(False, True))
        self.assertEqual(selection.toggle_mode("cyrillic"), ModeSnapshot(True, False))
        self.assertEqual(selection.last_nonempty, ModeSnapshot(True, False))
        with self.assertRaises(ValueError):
            selection.toggle_mode("unknown")

    def test_off_state_and_previous_choice_survive_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "YangiLotin" / "settings.json"
            selection = ModeSelection()
            selection.toggle_mode("cyrillic")
            selection.toggle_all()
            selection.save(path)
            restored = ModeSelection.load(path)
            self.assertEqual(restored.current, ModeSnapshot(False, False))
            self.assertEqual(restored.toggle_all(), ModeSnapshot(False, True))
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_reverse_choice_survives_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            selection = ModeSelection()
            selection.toggle_mode("latin_to_cyrillic")
            selection.toggle_all()
            selection.save(path)
            self.assertIn('"version": 2', path.read_text(encoding="utf-8"))
            restored = ModeSelection.load(path)
            self.assertEqual(restored.current, ModeSnapshot(False, False))
            self.assertEqual(restored.toggle_all(), ModeSnapshot(False, False, True))

    def test_v1_settings_migrate_without_reenabling_paused_modes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(
                '{"version":1,"cyrillic":false,"old_latin":false,'
                '"last_cyrillic":false,"last_old_latin":true}',
                encoding="utf-8",
            )
            restored = ModeSelection.load(path)
            self.assertEqual(restored.current, ModeSnapshot(False, False))
            self.assertEqual(restored.toggle_all(), ModeSnapshot(False, True))

    def test_damaged_settings_use_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            self.assertEqual(ModeSelection.load(path).current, ModeSnapshot(True, True))
            for content in (
                "{", '{"version":1,"cyrillic":"false"}',
                '{"version":[]}', "[]",
            ):
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    self.assertEqual(
                        ModeSelection.load(path).current,
                        ModeSnapshot(True, True),
                    )


class TrayModeStateTests(unittest.TestCase):
    def test_reverse_mode_counts_as_active_and_excludes_forward(self) -> None:
        tray = WindowsTrayIcon(
            active=True,
            on_toggle=lambda _active: None,
            on_open=lambda: None,
            on_exit=lambda: None,
            cyrillic_enabled=False,
            old_latin_enabled=False,
            latin_to_cyrillic_enabled=True,
        )
        self.assertTrue(tray.active)
        tray.set_modes(False, False)
        self.assertFalse(tray.active)
        tray.set_modes(False, False, True)
        self.assertTrue(tray.active)
        with self.assertRaises(ValueError):
            tray.set_modes(True, False, True)


if __name__ == "__main__":
    unittest.main()
