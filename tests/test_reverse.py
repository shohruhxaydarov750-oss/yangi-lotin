from __future__ import annotations

import unittest

from yangi_lotin.live_mode import LiveComposer
from yangi_lotin.reverse import (
    count_latin_to_cyrillic,
    is_latin_source_character,
    latin_to_cyrillic,
)


class LatinToCyrillicTests(unittest.TestCase):
    def test_direct_letters(self) -> None:
        pairs = {
            "a": "а", "b": "б", "d": "д", "f": "ф", "g": "г",
            "h": "ҳ", "i": "и", "j": "ж", "k": "к", "l": "л",
            "m": "м", "n": "н", "o": "о", "p": "п", "q": "қ",
            "r": "р", "s": "с", "t": "т", "u": "у", "v": "в",
            "x": "х", "y": "й", "z": "з", "ö": "ў", "ğ": "ғ",
            "ş": "ш", "ç": "ч",
        }
        for source, expected in pairs.items():
            with self.subTest(source=source):
                self.assertEqual(latin_to_cyrillic(source), expected)
                self.assertEqual(latin_to_cyrillic(source.upper()), expected.upper())

    def test_old_and_new_alphabet_words(self) -> None:
        cases = {
            "shahar": "шаҳар",
            "chiroyli": "чиройли",
            "o'zbek": "ўзбек",
            "g'alaba": "ғалаба",
            "şahar": "шаҳар",
            "çöl": "чўл",
            "özbekiston": "ўзбекистон",
            "qönğiroq": "қўнғироқ",
            "yoş": "ёш",
            "yurak": "юрак",
            "yaxşi": "яхши",
            "yöl": "йўл",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(latin_to_cyrillic(source), expected)

    def test_case_and_contextual_e(self) -> None:
        cases = {
            "Şahar": "Шаҳар",
            "CHIROYLI": "ЧИРОЙЛИ",
            "ÖZBEKISTON": "ЎЗБЕКИСТОН",
            "YOŞLAR": "ЁШЛАР",
            "YEÇIM": "ЕЧИМ",
            "Yer": "Ер",
            "ekin": "экин",
            "Eʼlon": "Эълон",
            "kel": "кел",
            "teatr": "театр",
            "poyezd": "поезд",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(latin_to_cyrillic(source), expected)

    def test_tutuq_and_quotes(self) -> None:
        cases = {
            "maʼno": "маъно",
            "san'at": "санъат",
            "e’lon": "эълон",
            "qalʻa": "қалъа",
            "'salom'": "'салом'",
            "'go'": "'го'",
            "‘o’": "‘о’",
            "“o‘zbek”": "“ўзбек”",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(latin_to_cyrillic(source), expected)

    def test_common_ambiguous_loan_spellings(self) -> None:
        cases = {
            "sirk": "цирк",
            "Sement": "Цемент",
            "konsert": "концерт",
            "aksiya": "акция",
            "abzas": "абзац",
            "litsey": "литсей",
            "militsiya": "милитсия",
            "konstitutsiya": "конститутсия",
            "pitssa": "питсса",
            "aseton": "ацетон",
            "obyekt": "объект",
            "kompyuter": "компьютер",
            "iyun": "июнь",
            "iyunda": "июнда",
            "iyul": "июль",
            "iyulda": "июлда",
            "sentyabr": "сентябрь",
            "sentyabrda": "сентябрда",
            "poçtalyon": "почтальон",
            "möjiza": "мўъжиза",
            "sirkda": "циркда",
            "sirka": "сирка",
            "sirkali": "сиркали",
            "Konsertlar": "Концертлар",
            "obyektga": "объектга",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(latin_to_cyrillic(source), expected)

    def test_ts_stays_two_letters(self) -> None:
        for source, expected in {
            "ts": "тс", "Ts": "Тс", "tS": "тС", "TS": "ТС",
            "matn": "матн", "at+s": "ат+с",
        }.items():
            with self.subTest(source=source):
                self.assertEqual(latin_to_cyrillic(source), expected)

    def test_preserves_non_latin_and_formatting(self) -> None:
        source = "Salom, dunyo! 2026 😊\r\n\r\nСалом / w c."
        expected = "Салом, дунё! 2026 😊\r\n\r\nСалом / w c."
        self.assertEqual(latin_to_cyrillic(source), expected)

    def test_counts_and_live_gate(self) -> None:
        self.assertEqual(count_latin_to_cyrillic("sh ch o' g'"), 4)
        self.assertEqual(count_latin_to_cyrillic("ma'no"), 5)
        self.assertEqual(count_latin_to_cyrillic("w c 7"), 0)
        for character in "AbzSHchöÖğĞşŞçÇ'`´‘’ʻʼ":
            with self.subTest(character=character):
                self.assertTrue(is_latin_source_character(character))
        for character in " 7-😊ш":
            with self.subTest(character=character):
                self.assertFalse(is_latin_source_character(character))

    def test_live_prefix_and_backspace_follow_reverse_output(self) -> None:
        for word in ("salom", "shahar", "o'zbek", "yaxşi", "sirkda", "obyektga", "ts"):
            with self.subTest(word=word):
                composer = LiveComposer(renderer=latin_to_cyrillic)
                visible = ""
                for index, character in enumerate(word, start=1):
                    edit = composer.feed(character)
                    visible = visible[:-edit.backspaces] if edit.backspaces else visible
                    visible += edit.insert
                    self.assertEqual(visible, latin_to_cyrillic(word[:index]))
                while composer.has_token:
                    edit = composer.backspace()
                    visible = visible[:-edit.backspaces] if edit.backspaces else visible
                    visible += edit.insert
                    self.assertEqual(visible, latin_to_cyrillic(composer.source_token))

    def test_non_string_rejected(self) -> None:
        with self.assertRaises(TypeError):
            latin_to_cyrillic(None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            count_latin_to_cyrillic(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
