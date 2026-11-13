"""Convert Uzbek Cyrillic and Latin scripts."""

from .reverse import count_latin_to_cyrillic, latin_to_cyrillic
from .transliterator import (
    APOSTROPHE_VARIANTS,
    TUTUQ,
    count_all_conversions,
    count_convertible,
    count_old_latin_replacements,
    modernize_old_latin,
    to_new_latin,
    transliterate,
)

__all__ = [
    "count_latin_to_cyrillic",
    "latin_to_cyrillic",
    "APOSTROPHE_VARIANTS",
    "TUTUQ",
    "count_all_conversions",
    "count_convertible",
    "count_old_latin_replacements",
    "modernize_old_latin",
    "to_new_latin",
    "transliterate",
]
__version__ = "1.6.6"
