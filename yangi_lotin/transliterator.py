"""Deterministic Uzbek Cyrillic/old Latin -> updated Uzbek Latin conversion.

The target alphabet uses Ö/Ğ/Ş/Ç as enacted by O'RQ-1184 (2026); the law
is scheduled to take effect on 22 April 2027. ``transliterate`` remains
Cyrillic-only for API compatibility; ``to_new_latin`` also modernises the
four legacy Latin letter forms. Unrecognised characters are preserved.
"""

from __future__ import annotations

import unicodedata

TUTUQ = "\u02bc"  # MODIFIER LETTER APOSTROPHE, the retained tutuq sign.

# Old Uzbek Latin keyboards and documents use several visually similar
# apostrophes for O‘/G‘.  All are accepted after O/G, but unmatched marks are
# deliberately preserved exactly as typed.
APOSTROPHE_VARIANTS = frozenset("'`´‘’ʻʼ")
_ASCII_LATIN = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
)
_NEW_LATIN_SPECIALS = frozenset("öÖğĞşŞçÇ")
_QUOTE_OPENERS = {
    "'": frozenset("'"),
    "’": frozenset("'‘’"),
}

_DIRECT_MAP = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "ё": "yo",
    "ж": "j",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "x",
    "ч": "ç",
    "ш": "ş",
    "щ": "ş",
    "ы": "i",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "ў": "ö",
    "қ": "q",
    "ғ": "ğ",
    "ҳ": "h",
}

_CYRILLIC_VOWELS = frozenset("аеёиоуўыэюя")
_PLAIN_VOWELS_AFTER_SOFT_SIGN = frozenset("аиоуўыэ")

# In these established international/Russian loans, ъ separates an iotated
# vowel but is not written as a tutuq sign in Uzbek Latin.  Patterns are used
# rather than whole words so ordinary Uzbek suffixes keep working.
_DROPPED_HARD_SIGN_PATTERNS = (
    "объект",
    "объём",
    "объем",
    "субъект",
    "подъезд",
    "разъезд",
    "съезд",
    "адъют",
    "конъюнкт",
    "инъек",
)

# The normal ц rule is positional.  A few lexical/morpheme-boundary spellings
# cannot be inferred from neighbours, so the small, documented exceptions
# below force s at the listed zero-based position.
_FORCE_S_PATTERNS = {
    "ацетон": frozenset({1}),
    "ацетилен": frozenset({1}),
    "телецентр": frozenset({4}),
}

_CONVERTIBLE = frozenset(_DIRECT_MAP) | frozenset({"е", "ц", "ъ", "ь"})


def _is_cyrillic_letter(character: str) -> bool:
    """Return True for alphabetic characters in the Cyrillic Unicode blocks."""

    if not character.isalpha():
        return False
    codepoint = ord(character)
    return (
        0x0400 <= codepoint <= 0x052F
        or 0x1C80 <= codepoint <= 0x1C8F
        or 0x2DE0 <= codepoint <= 0x2DFF
        or 0xA640 <= codepoint <= 0xA69F
    )


def _apply_case(fragment: str, source: str, token_is_all_caps: bool) -> str:
    if not fragment or not source.isupper():
        return fragment
    if token_is_all_caps:
        return fragment.upper()
    return fragment[0].upper() + fragment[1:]


def _pattern_covers_index(token: str, pattern: str, index: int, marker: str) -> bool:
    marker_offset = pattern.index(marker)
    start = token.find(pattern)
    while start != -1:
        if start + marker_offset == index:
            return True
        start = token.find(pattern, start + 1)
    return False


def _drop_hard_sign(token: str, index: int) -> bool:
    # The old Latin spellings mo'jiza/mo'tadil used the mark as part of O'.
    # With the self-contained letter Ö, the following Cyrillic ъ is not a
    # separate tutuq sign.
    if index > 0 and token[index - 1] == "ў":
        return True
    return any(
        _pattern_covers_index(token, pattern, index, "ъ")
        for pattern in _DROPPED_HARD_SIGN_PATTERNS
    )


def _force_s_for_tse(token: str, index: int) -> bool:
    for pattern, positions in _FORCE_S_PATTERNS.items():
        start = token.find(pattern)
        while start != -1:
            if index - start in positions:
                return True
            start = token.find(pattern, start + 1)
    return False


def _fragment_for(token: str, index: int) -> str:
    character = token[index]

    if character in _DIRECT_MAP:
        return _DIRECT_MAP[character]

    if character == "е":
        if index == 0:
            return "ye"
        previous = token[index - 1]
        return "ye" if previous in _CYRILLIC_VOWELS or previous in "ъь" else "e"

    if character == "ц":
        if _force_s_for_tse(token, index):
            return "s"
        # Uzbek spelling writes ts only medially after a vowel.  This gives
        # litsey/militsiya/pitssa, but sirk/konsert/aksiya/abzas.
        if 0 < index < len(token) - 1 and token[index - 1] in _CYRILLIC_VOWELS:
            return "ts"
        return "s"

    if character == "ъ":
        return "" if _drop_hard_sign(token, index) else TUTUQ

    if character == "ь":
        if index + 1 < len(token) and token[index + 1] in _PLAIN_VOWELS_AFTER_SOFT_SIGN:
            return "y"
        return ""

    # Unknown Cyrillic letters are outside the converter's documented Uzbek
    # scope.  Preserving them is safer than deleting or guessing.
    return character


def _transliterate_token(token: str) -> str:
    lowered = token.lower()
    cased_letters = [char for char in token if char.isupper() or char.islower()]
    token_is_all_caps = bool(cased_letters) and all(char.isupper() for char in cased_letters)

    converted: list[str] = []
    for index, source in enumerate(token):
        fragment = _fragment_for(lowered, index)
        converted.append(_apply_case(fragment, source, token_is_all_caps))
    return "".join(converted)


def transliterate(text: str) -> str:
    """Convert Uzbek Cyrillic text to the updated Latin alphabet.

    NFC normalisation lets decomposed Unicode input such as у + breve behave
    like ў.  Paragraphs, whitespace, punctuation, emoji, digits and existing
    Latin text are otherwise preserved in their original order.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = unicodedata.normalize("NFC", text)
    result: list[str] = []
    index = 0

    while index < len(text):
        if not _is_cyrillic_letter(text[index]):
            result.append(text[index])
            index += 1
            continue

        end = index + 1
        while end < len(text) and _is_cyrillic_letter(text[end]):
            end += 1
        result.append(_transliterate_token(text[index:end]))
        index = end

    return unicodedata.normalize("NFC", "".join(result))


def count_convertible(text: str) -> int:
    """Count source letters that this converter knows how to transliterate."""

    normalised = unicodedata.normalize("NFC", text)
    return sum(character.lower() in _CONVERTIBLE for character in normalised)


def _is_paired_closing_quote(text: str, letter_index: int) -> bool:
    """Keep a quote after a quoted word's final o/g as punctuation.

    Without this check, ``'go'`` loses its closing quote because ``o'``
    looks like the old Uzbek letter.  An actual letter inside quotes still
    works as ``'o''`` -> ``'ö'``.
    """

    closing_index = letter_index + 1
    closing = text[closing_index]
    openers = _QUOTE_OPENERS.get(closing)
    if openers is None:
        return False
    if closing_index + 1 < len(text) and (
        text[closing_index + 1] in _ASCII_LATIN
        or text[closing_index + 1] in _NEW_LATIN_SPECIALS
        or text[closing_index + 1] in APOSTROPHE_VARIANTS
    ):
        return False

    start = letter_index
    while start > 0 and (
        text[start - 1] in _ASCII_LATIN
        or text[start - 1] in _NEW_LATIN_SPECIALS
    ):
        start -= 1
    return start > 0 and text[start - 1] in openers


def modernize_old_latin(text: str) -> str:
    """Convert legacy Uzbek Latin digraphs to Ö/Ğ/Ş/Ç.

    Supported forms are sh, ch, o + apostrophe and g + apostrophe.  The scan
    is intentionally narrow: ng/yo/ya/yu, punctuation, unmatched apostrophes,
    existing new-Latin letters and all other content remain unchanged.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = unicodedata.normalize("NFC", text)
    converted: list[str] = []
    index = 0

    while index < len(text):
        first = text[index]
        if index + 1 < len(text):
            second = text[index + 1]
            lowered = first.lower()

            if lowered in {"s", "c"} and second.lower() == "h":
                replacement = "ş" if lowered == "s" else "ç"
                if first.isupper() or second.isupper():
                    replacement = replacement.upper()
                converted.append(replacement)
                index += 2
                continue

            if (
                lowered in {"o", "g"}
                and second in APOSTROPHE_VARIANTS
                and not _is_paired_closing_quote(text, index)
            ):
                replacement = "ö" if lowered == "o" else "ğ"
                if first.isupper():
                    replacement = replacement.upper()
                converted.append(replacement)
                index += 2
                continue

        converted.append(first)
        index += 1

    return unicodedata.normalize("NFC", "".join(converted))


def count_old_latin_replacements(text: str) -> int:
    """Count legacy two-character Latin forms that would be modernised."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = unicodedata.normalize("NFC", text)
    count = 0
    index = 0
    while index + 1 < len(text):
        first = text[index]
        second = text[index + 1]
        lowered = first.lower()
        is_digraph = lowered in {"s", "c"} and second.lower() == "h"
        is_apostrophe_letter = (
            lowered in {"o", "g"} and second in APOSTROPHE_VARIANTS
            and not _is_paired_closing_quote(text, index)
        )
        if is_digraph or is_apostrophe_letter:
            count += 1
            index += 2
        else:
            index += 1
    return count


def to_new_latin(text: str) -> str:
    """Convert both Uzbek Cyrillic and legacy Latin input to new Latin.

    Legacy Latin is modernised *before* Cyrillic transliteration.  This
    ordering is important: Cyrillic ``сҳ`` becomes the two sounds ``sh`` and
    must not be reinterpreted as the single legacy digraph ``sh``.
    """

    return transliterate(modernize_old_latin(text))


def count_all_conversions(text: str) -> int:
    """Count Cyrillic source letters plus old-Latin pairs to be converted."""

    return count_convertible(text) + count_old_latin_replacements(text)


def is_live_source_character(
    character: str,
    cyrillic_enabled: bool = True,
    old_latin_enabled: bool = True,
    latin_to_cyrillic_enabled: bool = False,
) -> bool:
    """Return whether one typed character can belong to a live source word."""

    if not isinstance(character, str) or len(character) != 1:
        return False
    character = unicodedata.normalize("NFC", character)
    if len(character) != 1:
        return False
    return (
        (cyrillic_enabled and count_convertible(character) == 1)
        or (
            (old_latin_enabled or latin_to_cyrillic_enabled)
            and (
                character in _ASCII_LATIN
                or character in _NEW_LATIN_SPECIALS
                or character in APOSTROPHE_VARIANTS
            )
        )
    )
