"""Language pack registry and Jinja sandbox filter provider.

Supports statutory Marathi and English conveyancing language packs.
"""

from __future__ import annotations

from typing import Any, Callable

from app.lang_packs.base import LanguagePack
from app.lang_packs.english import EnglishLanguagePack
from app.lang_packs.marathi import MarathiLanguagePack

_REGISTRY: dict[str, LanguagePack] = {
    "mr": MarathiLanguagePack(),
    "en": EnglishLanguagePack(),
}


def get_language_pack(code: str = "mr") -> LanguagePack:
    """Retrieves language pack by ISO 639-1 code ('mr' or 'en')."""
    pack = _REGISTRY.get(code.lower().strip())
    if not pack:
        raise ValueError(
            f"Unsupported language code '{code}'. Supported: {sorted(_REGISTRY.keys())}"
        )
    return pack


def get_template_filters(language_code: str = "mr") -> dict[str, Callable[..., Any]]:
    """Returns whitelisted filters for sandboxed Jinja / docxtpl rendering."""
    pack = get_language_pack(language_code)

    return {
        "words": lambda val: pack.number_to_words(val, currency=False),
        "words_currency": lambda val: pack.number_to_words(val, currency=True),
        "date_fmt": lambda val: pack.format_date(val),
        "curr_fmt": lambda val: pack.format_currency(val),
        "join_names": lambda val: pack.join_names(val),
        "to_digits": lambda val: pack.to_digits(str(val)),
        "to_western": lambda val: pack.to_western_digits(str(val)),
    }
