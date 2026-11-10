"""Regional conveyancing language packs for Lekhan."""

from app.lang_packs.base import LanguagePack
from app.lang_packs.english import (
    EnglishLanguagePack,
    format_currency_indian_en,
    number_to_words_en,
    words_to_number_en,
)
from app.lang_packs.marathi import (
    MarathiLanguagePack,
    format_currency_indian_mr,
    format_date_mr,
    get_honorific_mr,
    join_party_names_mr,
    number_to_words_mr,
    to_devanagari_digits,
    to_western_digits,
    words_to_number_mr,
)
from app.lang_packs.registry import get_language_pack, get_template_filters

__all__ = [
    "EnglishLanguagePack",
    "LanguagePack",
    "MarathiLanguagePack",
    "format_currency_indian_en",
    "format_currency_indian_mr",
    "format_date_mr",
    "get_honorific_mr",
    "get_language_pack",
    "get_template_filters",
    "join_party_names_mr",
    "number_to_words_en",
    "number_to_words_mr",
    "to_devanagari_digits",
    "to_western_digits",
    "words_to_number_en",
    "words_to_number_mr",
]
