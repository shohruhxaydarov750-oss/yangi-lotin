from __future__ import annotations

import unittest

from yangi_lotin import TUTUQ, count_convertible, transliterate


class NewAlphabetLettersTests(unittest.TestCase):
    def test_typical_uzbek_words(self) -> None:
        cases = {
            "Ўзбекистон": "Özbekiston",
            "Қўнғироқ": "Qönğiroq",
            "Ғалла": "Ğalla",
            "Шаҳар": "Şahar",
            "Чирчиқ": "Çirçiq",
            "чўл": "çöl",
            "тоғ": "toğ",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)

    def test_all_direct_letters(self) -> None:
        source = "абвгджзийклмнопрстуфхчшыэўқғҳ"
        expected = "abvgdjziyklmnoprstufxçşieöqğh"
        self.assertEqual(transliterate(source), expected)


class ContextualETests(unittest.TestCase):
    def test_word_initial_and_after_vowel(self) -> None:
        cases = {
            "ер": "yer",
            "Ер": "Yer",
            "поезд": "poyezd",
            "Европа": "Yevropa",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)

    def test_after_consonant(self) -> None:
        cases = {"келди": "keldi", "театр": "teatr", "Йемен": "Yemen"}
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)


class IotatedVowelTests(unittest.TestCase):
    def test_yo_yu_ya(self) -> None:
        cases = {
            "ёш": "yoş",
            "юрак": "yurak",
            "яхши": "yaxşi",
            "дунё": "dunyo",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)


class TSeTests(unittest.TestCase):
    def test_positional_rules(self) -> None:
        cases = {
            "цирк": "sirk",
            "Цемент": "Sement",
            "концерт": "konsert",
            "акция": "aksiya",
            "абзац": "abzas",
            "лицей": "litsey",
            "милиция": "militsiya",
            "конституция": "konstitutsiya",
            "доцент": "dotsent",
            "пицца": "pitssa",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)

    def test_documented_lexical_exceptions(self) -> None:
        cases = {
            "ацетон": "aseton",
            "ацетилен": "asetilen",
            "телецентр": "telesentr",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)


class SignsTests(unittest.TestCase):
    def test_tutuq_is_preserved(self) -> None:
        cases = {
            "маъно": f"ma{TUTUQ}no",
            "санъат": f"san{TUTUQ}at",
            "шеър": f"şe{TUTUQ}r",
            "қалъа": f"qal{TUTUQ}a",
            "масъул": f"mas{TUTUQ}ul",
            "маъюс": f"ma{TUTUQ}yus",
            "эълон": f"e{TUTUQ}lon",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)

    def test_hard_sign_after_o_with_breve_is_not_duplicated(self) -> None:
        cases = {"мўъжиза": "möjiza", "мўътадил": "mötadil", "мўъмин": "mömin"}
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)

    def test_international_hard_sign_loans(self) -> None:
        cases = {
            "объект": "obyekt",
            "субъект": "subyekt",
            "подъезд": "podyezd",
            "инъекция": "inyeksiya",
            "адъютант": "adyutant",
            "конъюнктура": "konyunktura",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)

    def test_soft_sign(self) -> None:
        cases = {
            "альбом": "albom",
            "июнь": "iyun",
            "рельс": "rels",
            "компьютер": "kompyuter",
            "пьеса": "pyesa",
            "почтальон": "poçtalyon",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)


class CapitalisationTests(unittest.TestCase):
    def test_title_and_all_caps(self) -> None:
        cases = {
            "Ёш": "Yoş",
            "ЁШ": "YOŞ",
            "ЕЧИМ": "YEÇIM",
            "Юлдуз": "Yulduz",
            "ЮЛДУЗ": "YULDUZ",
            "МИЛИЦИЯ": "MILITSIYA",
            "АБЗАЦ": "ABZAS",
            "МАЪНО": f"MA{TUTUQ}NO",
            "Щука": "Şuka",
            "ЩУКА": "ŞUKA",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate(source), expected)

    def test_mixed_case_is_deterministic(self) -> None:
        self.assertEqual(transliterate("ЁшЛАР"), "YoşLAR")


class PreservationTests(unittest.TestCase):
    def test_paragraphs_punctuation_digits_and_emoji(self) -> None:
        source = "Салом, дунё! 2026 😊\r\n\r\nЯнги сатр."
        expected = "Salom, dunyo! 2026 😊\r\n\r\nYangi satr."
        self.assertEqual(transliterate(source), expected)

    def test_existing_latin_is_not_converted(self) -> None:
        source = "Sh Ch O‘ G‘ ş ç ö ğ — Özbekiston"
        self.assertEqual(transliterate(source), source)

    def test_mixed_script_keeps_non_cyrillic_content(self) -> None:
        self.assertEqual(transliterate("ID-7: Ўзбекистон / API"), "ID-7: Özbekiston / API")

    def test_decomposed_unicode_is_normalised(self) -> None:
        self.assertEqual(transliterate("У\u0306збекистон"), "Özbekiston")
        self.assertEqual(transliterate("Е\u0308ш"), "Yoş")

    def test_empty_string(self) -> None:
        self.assertEqual(transliterate(""), "")

    def test_non_string_rejected(self) -> None:
        with self.assertRaises(TypeError):
            transliterate(None)  # type: ignore[arg-type]

    def test_count_convertible(self) -> None:
        self.assertEqual(count_convertible("ABC Ўз!"), 2)


if __name__ == "__main__":
    unittest.main()
