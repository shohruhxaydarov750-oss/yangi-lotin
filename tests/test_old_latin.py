from __future__ import annotations

import unittest

from yangi_lotin.transliterator import (
    APOSTROPHE_VARIANTS,
    count_all_conversions,
    count_old_latin_replacements,
    is_live_source_character,
    modernize_old_latin,
    to_new_latin,
    transliterate,
)


class OldLatinMappingTests(unittest.TestCase):
    def test_typical_words(self) -> None:
        cases = {
            "shahar": "şahar",
            "chiroyli": "çiroyli",
            "o'zbekiston": "özbekiston",
            "g'alaba": "ğalaba",
            "o'quvchi": "öquvçi",
            "g'isht": "ğişt",
            "SHOVQIN": "ŞOVQIN",
            "CHIROYLI": "ÇIROYLI",
            "O'G'IL": "ÖĞIL",
            "Sh Ch sH cH": "Ş Ç Ş Ç",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(modernize_old_latin(source), expected)

    def test_all_supported_apostrophes(self) -> None:
        for apostrophe in APOSTROPHE_VARIANTS:
            with self.subTest(apostrophe=repr(apostrophe)):
                source = f"o{apostrophe} g{apostrophe} O{apostrophe} G{apostrophe}"
                self.assertEqual(modernize_old_latin(source), "ö ğ Ö Ğ")

    def test_unmatched_content_is_preserved(self) -> None:
        cases = (
            "ng yo ya yu",
            "ma'no san'at qat'iy",
            "'salom' — 2026 😊",
            "Ş Ç Ö Ğ ş ç ö ğ",
            "URL/API/file_name",
        )
        for source in cases:
            with self.subTest(source=source):
                self.assertEqual(modernize_old_latin(source), source)

    def test_closing_quotes_are_not_old_latin_letters(self) -> None:
        cases = {
            "'go'": "'go'",
            "'o'": "'o'",
            "‘go’": "‘go’",
            "‘o’": "‘o’",
            "'o''": "'ö'",
            "‘oʼ’": "‘ö’",
            "o'": "ö",
            "o'zbek": "özbek",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(modernize_old_latin(source), expected)
        self.assertEqual(count_old_latin_replacements("'go' ‘o’"), 0)

    def test_mixed_scripts_and_no_chain_regression(self) -> None:
        self.assertEqual(
            to_new_latin("Шаҳар va shahar"),
            "Şahar va şahar",
        )
        # Cyrillic с + ҳ are two sounds.  Their generated "sh" must not be
        # reinterpreted as the old-Latin single-letter digraph.
        self.assertEqual(to_new_latin("сҳ"), "sh")

    def test_cyrillic_only_api_remains_compatible(self) -> None:
        source = "Sh Ch O' G'"
        self.assertEqual(transliterate(source), source)

    def test_counts_and_live_character_gate(self) -> None:
        source = "sh ch o' g' Ш"
        self.assertEqual(count_old_latin_replacements(source), 4)
        self.assertEqual(count_all_conversions(source), 5)
        for character in "AbzSHchöÖğĞşŞçÇ'`´‘’ʻʼЎ":
            with self.subTest(character=character):
                self.assertTrue(is_live_source_character(character))
        for character in " 7-😊":
            with self.subTest(character=character):
                self.assertFalse(is_live_source_character(character))
        self.assertTrue(is_live_source_character("ш", True, False))
        self.assertFalse(is_live_source_character("s", True, False))
        self.assertTrue(is_live_source_character("s", False, True))
        self.assertFalse(is_live_source_character("ш", False, True))
        self.assertFalse(is_live_source_character("s", False, False))
        self.assertTrue(is_live_source_character("ş", False, False, True))
        self.assertTrue(is_live_source_character("s", False, False, True))
        self.assertFalse(is_live_source_character("ш", False, False, True))

    def test_non_string_rejected(self) -> None:
        with self.assertRaises(TypeError):
            modernize_old_latin(None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            count_old_latin_replacements(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
