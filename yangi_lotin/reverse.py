"""Uzbek Latin (legacy or updated) to Cyrillic, with explicit ambiguities.

Both Latin spellings use the same output direction.  This is a spelling
transliterator, not a dictionary or a perfect inverse: Latin omits some
Cyrillic distinctions, especially ъ/ь and positional ц.  A small table of
common established loan spellings covers cases that the letters cannot infer.
"""

from __future__ import annotations

import unicodedata

from .transliterator import APOSTROPHE_VARIANTS, modernize_old_latin


_ASCII_LATIN = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_NEW_LATIN = frozenset("öÖğĞşŞçÇ")
_LETTER_MAP = {
    "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф",
    "g": "г", "h": "ҳ", "i": "и", "j": "ж", "k": "к",
    "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
    "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у",
    "v": "в", "x": "х", "y": "й", "z": "з",
    "ö": "ў", "ğ": "ғ", "ş": "ш", "ç": "ч",
}
_Y_VOWEL_MAP = {"a": "я", "e": "е", "o": "ё", "u": "ю"}

# These common stems have lost a Cyrillic sign or a positional ц in Latin.
# Keeping the replacement through a suffix also prevents live typing from
# first showing цирк and then reverting to сиркд as "sirkda" is completed.
# The rest of the converter follows the letter rules.
_WORD_STEM_OVERRIDES = {
    # "sirka" (vinegar) is not derived from "sirk" (circus).
    "sirka": "сирка",
    "sirk": "цирк",
    "sement": "цемент",
    "konsert": "концерт",
    "aksiya": "акция",
    "abzas": "абзац",
    "aseton": "ацетон",
    "asetilen": "ацетилен",
    "telesentr": "телецентр",
    "pitssa": "пицца",
    "obyekt": "объект",
    "subyekt": "субъект",
    "podyezd": "подъезд",
    "inyeksiya": "инъекция",
    "adyutant": "адъютант",
    "konyunktura": "конъюнктура",
    "albom": "альбом",
    "iyun": "июнь",
    "iyul": "июль",
    "rels": "рельс",
    "kompyuter": "компьютер",
    "pyesa": "пьеса",
    "poçtalyon": "почтальон",
    "sentyabr": "сентябрь",
    "möjiza": "мўъжиза",
    "mötadil": "мўътадил",
    "mömin": "мўъмин",
}


def _is_latin_letter(character: str) -> bool:
    return character in _ASCII_LATIN or character in _NEW_LATIN


def is_latin_source_character(character: str) -> bool:
    """Whether a typed character can continue a Latin source token."""

    if not isinstance(character, str) or len(character) != 1:
        return False
    character = unicodedata.normalize("NFC", character)
    return len(character) == 1 and (
        _is_latin_letter(character) or character in APOSTROPHE_VARIANTS
    )


def _case(fragment: str, source: str) -> str:
    return fragment.upper() if any(letter.isupper() for letter in source) else fragment


def _stem_override(token: str) -> tuple[str, int] | None:
    for stem in sorted(_WORD_STEM_OVERRIDES, key=len, reverse=True):
        if not token.lower().startswith(stem):
            continue
        source = token[:len(stem)]
        target = _WORD_STEM_OVERRIDES[stem]
        # Month names end in ь on their own, but Uzbek suffixes attach to
        # the stem without it: июнь -> июнда, июль -> июлда.
        if len(token) > len(stem) and stem in {"iyun", "iyul", "sentyabr"}:
            target = target[:-1]
        if source.isupper():
            return target.upper(), len(stem)
        if source.islower():
            return target, len(stem)
        if source[0].isupper() and source[1:].islower():
            return target[0].upper() + target[1:], len(stem)
    return None


def _convert_token(token: str) -> tuple[str, int]:
    exception = _stem_override(token)
    if exception is not None:
        replacement, index = exception
        converted: list[str] = [replacement]
        count = sum(_is_latin_letter(char) for char in token[:index])
    else:
        converted = []
        count = 0
        index = 0
    while index < len(token):
        first = token[index]
        second = token[index + 1] if index + 1 < len(token) else ""
        lower = first.lower()

        if lower == "y" and second.lower() in _Y_VOWEL_MAP:
            converted.append(_case(_Y_VOWEL_MAP[second.lower()], first + second))
            count += 1
            index += 2
            continue

        if lower == "t" and second.lower() == "s":
            converted.append(_case("ц", first + second))
            count += 1
            index += 2
            continue

        if first in APOSTROPHE_VARIANTS:
            # Internal tutuq becomes ъ. Quotation marks around a word stay
            # punctuation; o'/g' have already become ö/ğ.
            internal = (
                index > 0
                and index + 1 < len(token)
                and _is_latin_letter(token[index - 1])
                and _is_latin_letter(token[index + 1])
            )
            converted.append("ъ" if internal else first)
            count += int(internal)
            index += 1
            continue

        if lower in _LETTER_MAP:
            # Latin e starts a word as э. The explicit ye digraph above is е.
            fragment = "э" if lower == "e" and index == 0 else _LETTER_MAP[lower]
            converted.append(_case(fragment, first))
            count += 1
        else:
            converted.append(first)
        index += 1

    return "".join(converted), count


def _convert(text: str) -> tuple[str, int]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = modernize_old_latin(unicodedata.normalize("NFC", text))
    result: list[str] = []
    count = 0
    index = 0
    while index < len(text):
        if not _is_latin_letter(text[index]):
            result.append(text[index])
            index += 1
            continue

        end = index + 1
        while end < len(text) and is_latin_source_character(text[end]):
            end += 1
        fragment, converted = _convert_token(text[index:end])
        result.append(fragment)
        count += converted
        index = end

    return unicodedata.normalize("NFC", "".join(result)), count


def latin_to_cyrillic(text: str) -> str:
    """Convert old/new Uzbek Latin to Cyrillic, preserving other content."""

    return _convert(text)[0]


def count_latin_to_cyrillic(text: str) -> int:
    """Count source Latin letters or tutuq signs handled by this converter."""

    return _convert(text)[1]


__all__ = [
    "latin_to_cyrillic", "count_latin_to_cyrillic", "is_latin_source_character"
]
