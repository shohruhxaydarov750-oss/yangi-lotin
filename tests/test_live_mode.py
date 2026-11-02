from __future__ import annotations

import random
import os
import unittest

from yangi_lotin.live_mode import (
    EditPlan,
    KeyboardCaseTracker,
    LiveComposer,
    LiveKeyboardTransliterator,
)
from yangi_lotin.transliterator import (
    modernize_old_latin,
    to_new_latin,
    transliterate,
)
from yangi_lotin.reverse import latin_to_cyrillic


def apply_edit(visible: str, plan: EditPlan) -> str:
    if plan.backspaces > len(visible):
        raise AssertionError("edit removes more text than is visible")
    if plan.backspaces:
        visible = visible[: -plan.backspaces]
    return visible + plan.insert


class LiveComposerTests(unittest.TestCase):
    WORDS = (
        "Ўзбекистон",
        "Қўнғироқ",
        "Ғалла",
        "Шаҳар",
        "Чирчиқ",
        "ер",
        "Европа",
        "поезд",
        "ёш",
        "ЁШ",
        "цирк",
        "концерт",
        "акция",
        "абзац",
        "лицей",
        "милиция",
        "пицца",
        "маъно",
        "мўъжиза",
        "объект",
        "компьютер",
        "почтальон",
    )

    def test_every_prefix_matches_full_engine(self) -> None:
        for word in self.WORDS:
            with self.subTest(word=word):
                composer = LiveComposer()
                visible = ""
                for index, character in enumerate(word, start=1):
                    visible = apply_edit(visible, composer.feed(character))
                    self.assertEqual(visible, transliterate(word[:index]))

    def test_backspace_removes_one_source_character(self) -> None:
        for word in self.WORDS:
            with self.subTest(word=word):
                composer = LiveComposer()
                visible = ""
                for character in word:
                    visible = apply_edit(visible, composer.feed(character))
                for remaining in range(len(word) - 1, -1, -1):
                    visible = apply_edit(visible, composer.backspace())
                    self.assertEqual(visible, transliterate(word[:remaining]))
                self.assertFalse(composer.has_token)

    def test_future_context_rewrites_only_changed_tail(self) -> None:
        composer = LiveComposer()
        visible = apply_edit("", composer.feed("Ё"))
        self.assertEqual(visible, "YO")
        plan = composer.feed("ш")
        self.assertEqual(plan, EditPlan(backspaces=1, insert="oş"))
        self.assertEqual(apply_edit(visible, plan), "Yoş")

        composer.reset()
        visible = ""
        for character in "лиц":
            visible = apply_edit(visible, composer.feed(character))
        self.assertEqual(visible, "lis")
        visible = apply_edit(visible, composer.feed("е"))
        self.assertEqual(visible, "litse")

    def test_reset_prevents_state_leakage(self) -> None:
        composer = LiveComposer()
        for character in "поезд":
            composer.feed(character)
        composer.reset()
        self.assertEqual(composer.source_token, "")
        self.assertEqual(composer.rendered_token, "")
        self.assertEqual(composer.feed("е"), EditPlan(0, "ye"))

    def test_randomized_prefix_and_backspace_property(self) -> None:
        randomizer = random.Random(20261029)
        alphabet = "абвгдеёжзийклмнопрстуфхцчшъыьэюяўқғҳ"
        for _ in range(2000):
            length = randomizer.randint(1, 32)
            source = "".join(randomizer.choice(alphabet) for _ in range(length))
            composer = LiveComposer()
            visible = ""
            for index, character in enumerate(source, start=1):
                visible = apply_edit(visible, composer.feed(character))
                self.assertEqual(visible, transliterate(source[:index]))
            for remaining in range(length - 1, -1, -1):
                visible = apply_edit(visible, composer.backspace())
                self.assertEqual(visible, transliterate(source[:remaining]))


class OldLatinLiveComposerTests(unittest.TestCase):
    WORDS = (
        "shahar",
        "chiroyli",
        "o'zbekiston",
        "g'alaba",
        "o'quvchi",
        "g'isht",
        "SHOVQIN",
        "CHIROYLI",
        "O'G'IL",
        "ShChO'G'",
    )

    @staticmethod
    def make_composer() -> LiveComposer:
        return LiveComposer(renderer=to_new_latin)

    def test_every_prefix_and_backspace_matches_combined_engine(self) -> None:
        for word in self.WORDS:
            with self.subTest(word=word):
                composer = self.make_composer()
                visible = ""
                for index, character in enumerate(word, start=1):
                    visible = apply_edit(visible, composer.feed(character))
                    self.assertEqual(visible, to_new_latin(word[:index]))
                for remaining in range(len(word) - 1, -1, -1):
                    visible = apply_edit(visible, composer.backspace())
                    self.assertEqual(visible, to_new_latin(word[:remaining]))

    def test_completed_pairs_rewrite_the_visible_tail(self) -> None:
        composer = self.make_composer()
        self.assertEqual(composer.feed("s"), EditPlan(0, "s"))
        self.assertEqual(composer.feed("h"), EditPlan(1, "ş"))
        self.assertEqual(composer.backspace(), EditPlan(1, "s"))

        composer.reset()
        self.assertEqual(composer.feed("g"), EditPlan(0, "g"))
        self.assertEqual(composer.feed("'"), EditPlan(1, "ğ"))
        self.assertEqual(composer.backspace(), EditPlan(1, "g"))

    def test_lowercase_pairs_stay_lowercase_in_each_render_mode(self) -> None:
        for source, expected in (
            ("sh", "ş"), ("ch", "ç"), ("o'", "ö"), ("g'", "ğ")
        ):
            with self.subTest(source=source):
                composer = LiveComposer(renderer=modernize_old_latin)
                visible = ""
                for character in source:
                    visible = apply_edit(visible, composer.feed(character))
                self.assertEqual(visible, expected)

    def test_randomized_prefix_and_backspace_property(self) -> None:
        randomizer = random.Random(20261031)
        alphabet = "abcdefghijklmnopqrstuvwxyzSHCOG'‘’ʻʼ`´"
        for _ in range(2000):
            length = randomizer.randint(1, 32)
            source = "".join(randomizer.choice(alphabet) for _ in range(length))
            composer = self.make_composer()
            visible = ""
            for index, character in enumerate(source, start=1):
                visible = apply_edit(visible, composer.feed(character))
                self.assertEqual(visible, to_new_latin(source[:index]))
            for remaining in range(length - 1, -1, -1):
                visible = apply_edit(visible, composer.backspace())
                self.assertEqual(visible, to_new_latin(source[:remaining]))


class ModeAndCaseTests(unittest.TestCase):
    def test_caps_lock_tracking_ignores_key_repeat(self) -> None:
        tracker = KeyboardCaseTracker(caps_on=False)
        tracker.observe_caps(True)
        self.assertTrue(tracker.caps_on)
        tracker.observe_caps(True)
        self.assertTrue(tracker.caps_on)
        tracker.observe_caps(False)
        tracker.observe_caps(True)
        self.assertFalse(tracker.caps_on)

    def test_shift_tracking_keeps_a_digraph_across_shift_presses(self) -> None:
        tracker = KeyboardCaseTracker()
        tracker.observe_shift(0xA0, True)
        self.assertTrue(tracker.shift_down)
        tracker.observe_shift(0xA0, False)
        self.assertFalse(tracker.shift_down)
        tracker.observe_shift(0xA1, True)
        self.assertTrue(tracker.shift_down)
        tracker.observe_shift(0xA1, False)
        self.assertFalse(tracker.shift_down)

    def test_live_service_selects_independent_renderers(self) -> None:
        service = LiveKeyboardTransliterator(enabled=False)
        service.set_modes(True, False)
        self.assertEqual(service.modes, (True, False, False))
        self.assertEqual(service._composer._renderer("ш sh"), "ş sh")
        service.set_modes(False, True)
        self.assertEqual(service.modes, (False, True, False))
        self.assertEqual(service._composer._renderer("ш sh"), "ш ş")
        service.set_modes(True, True)
        self.assertEqual(service._composer._renderer("ш sh"), "ş ş")
        service.set_modes(False, False, True)
        self.assertEqual(service.modes, (False, False, True))
        self.assertEqual(service._composer._renderer("ш sh"), "ш ш")
        with self.assertRaises(ValueError):
            service.set_modes(True, False, True)
        service.set_modes(False, False)
        self.assertFalse(service.enabled)
        self.assertFalse(service._composer.has_token)

    @unittest.skipUnless(os.name == "nt", "Windows keyboard packet")
    def test_unicode_packet_decodes_special_latin_character(self) -> None:
        from yangi_lotin.live_mode import KBDLLHOOKSTRUCT, VK_PACKET

        service = LiveKeyboardTransliterator(enabled=False)
        event = KBDLLHOOKSTRUCT(vkCode=VK_PACKET, scanCode=ord("ş"))
        self.assertEqual(service._decode_character(event, 0), "ş")

    @unittest.skipUnless(os.name == "nt", "Windows native Edit controls")
    def test_native_password_edit_is_left_untouched(self) -> None:
        import ctypes
        from ctypes import wintypes

        from yangi_lotin.live_mode import ES_PASSWORD, user32

        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
            wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, wintypes.HWND, wintypes.HMENU,
            wintypes.HINSTANCE, ctypes.c_void_p,
        ]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.SetFocus.argtypes = [wintypes.HWND]
        user32.DestroyWindow.argtypes = [wintypes.HWND]

        windows = []
        try:
            for style in (0x00CF0000 | ES_PASSWORD, 0x00CF0000):
                hwnd = user32.CreateWindowExW(
                    0, "Edit", "", style, 0, 0, 100, 20,
                    None, None, None, None,
                )
                self.assertTrue(hwnd)
                windows.append(hwnd)
            user32.SetFocus(windows[0])
            self.assertTrue(
                LiveKeyboardTransliterator._focused_password_field(windows[0])
            )
            user32.SetFocus(windows[1])
            self.assertFalse(
                LiveKeyboardTransliterator._focused_password_field(windows[1])
            )
        finally:
            for hwnd in windows:
                user32.DestroyWindow(hwnd)


class ReverseLiveComposerTests(unittest.TestCase):
    def test_prefixes_and_backspaces_for_old_and_new_latin(self) -> None:
        for word in (
            "salom", "shahar", "chiroyli", "o'zbek", "g'alla",
            "şahar", "çiroyli", "özbek", "ğalla", "yoz", "yer",
            "maʼno", "SH", "Sh",
        ):
            with self.subTest(word=word):
                composer = LiveComposer(renderer=latin_to_cyrillic)
                visible = ""
                for index, character in enumerate(word, start=1):
                    visible = apply_edit(visible, composer.feed(character))
                    self.assertEqual(visible, latin_to_cyrillic(word[:index]))
                for remaining in range(len(word) - 1, -1, -1):
                    visible = apply_edit(visible, composer.backspace())
                    self.assertEqual(visible, latin_to_cyrillic(word[:remaining]))


if __name__ == "__main__":
    unittest.main()
