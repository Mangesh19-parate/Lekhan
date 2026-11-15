"""Unit and inverse-parser property tests for Marathi and English language packs."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.auth import get_current_actor
from app.identity.policy import Actor
from app.lang_packs import (
    EnglishLanguagePack,
    MarathiLanguagePack,
    format_currency_indian_en,
    format_currency_indian_mr,
    format_date_mr,
    get_honorific_mr,
    get_language_pack,
    get_template_filters,
    join_party_names_mr,
    number_to_words_en,
    number_to_words_mr,
    to_devanagari_digits,
    to_western_digits,
    words_to_number_en,
    words_to_number_mr,
)
from app.lang_packs.hindi import number_to_words_hi
from app.main import app
from app.shared.errors import InvalidAmountError

SAMPLE_AMOUNTS = [
    Decimal("0"),
    Decimal("1"),
    Decimal("5"),
    Decimal("15"),
    Decimal("25"),
    Decimal("42"),
    Decimal("99"),
    Decimal("100"),
    Decimal("105"),
    Decimal("350"),
    Decimal("1000"),
    Decimal("1234"),
    Decimal("15000"),
    Decimal("99999"),
    Decimal("100000"),  # 1 Lakh
    Decimal("525000"),  # 5.25 Lakh
    Decimal("1550000"),  # 15.5 Lakh
    Decimal("2500000"),  # 25 Lakh
    Decimal("9999999"),
    Decimal("10000000"),  # 1 Crore
    Decimal("25000000"),  # 2.5 Crore
    Decimal("12345678"),
    Decimal("1550000.50"),  # With paise
    Decimal("25000.75"),
]


# ---------------------------------------------------------------------------
# 1. Marathi Round-Trip Inverse-Parser Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("amount", SAMPLE_AMOUNTS)
def test_marathi_roundtrip_inverse_parser(amount: Decimal) -> None:
    """Verifies that words_to_number_mr(number_to_words_mr(N)) == N (exact Decimal oracle)."""
    words = number_to_words_mr(amount, currency=True)
    parsed = words_to_number_mr(words)
    expected = amount.quantize(Decimal("0.01"))
    assert parsed == expected, f"Marathi roundtrip failed for {amount}: '{words}' -> {parsed}"


def test_marathi_specific_phrasings() -> None:
    """Verifies standard Marathi conveyancing number phrasings."""
    assert number_to_words_mr(0) == "शून्य रुपये फक्त"
    assert number_to_words_mr(100, currency=False) == "शंभर"
    assert number_to_words_mr(105, currency=False) == "एकशे पाच"
    assert number_to_words_mr(1550000) == "पंधरा लाख पन्नास हजार रुपये फक्त"
    assert number_to_words_mr(Decimal("1250000.50")) == "बारा लाख पन्नास हजार रुपये आणि पन्नास पैसे फक्त"


# ---------------------------------------------------------------------------
# 2. English Round-Trip Inverse-Parser Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("amount", SAMPLE_AMOUNTS)
def test_english_roundtrip_inverse_parser(amount: Decimal) -> None:
    """Verifies that words_to_number_en(number_to_words_en(N)) == N (exact Decimal oracle)."""
    words = number_to_words_en(amount, currency=True)
    parsed = words_to_number_en(words)
    expected = amount.quantize(Decimal("0.01"))
    assert parsed == expected, f"English roundtrip failed for {amount}: '{words}' -> {parsed}"


def test_english_specific_phrasings() -> None:
    """Verifies Indian legal numbering words in English."""
    assert number_to_words_en(0) == "Rupees Zero Only"
    assert number_to_words_en(1550000) == "Rupees Fifteen Lakh Fifty Thousand Only"
    assert (
        number_to_words_en(Decimal("1250000.50"))
        == "Rupees Twelve Lakh Fifty Thousand and Fifty Paise Only"
    )


# ---------------------------------------------------------------------------
# 3. Currency Formatters (Indian Number Grouping)
# ---------------------------------------------------------------------------


def test_indian_currency_grouping_en() -> None:
    """Verifies Indian digit grouping in English conveyancing."""
    assert format_currency_indian_en(1310000) == "Rs. 13,10,000/-"
    assert format_currency_indian_en(10000000) == "Rs. 1,00,00,000/-"
    assert format_currency_indian_en(Decimal("2500000.50")) == "Rs. 25,00,000.50/-"


def test_indian_currency_grouping_mr() -> None:
    """Verifies Indian digit grouping in Marathi conveyancing."""
    assert format_currency_indian_mr(1310000) == "रु. 13,10,000/-"
    assert format_currency_indian_mr(1310000, devanagari=True) == "रु. १३,१०,०००/-"


# ---------------------------------------------------------------------------
# 4. Devanagari Digits Transliteration
# ---------------------------------------------------------------------------


def test_digit_transliteration() -> None:
    """Verifies Western <-> Devanagari digit converters."""
    assert to_devanagari_digits("13,10,000") == "१३,१०,०००"
    assert to_western_digits("१३,१०,०००") == "13,10,000"
    assert to_western_digits("०१२३४५६७८९") == "0123456789"


# ---------------------------------------------------------------------------
# 5. Honorifics, Dates, and Name Joining
# ---------------------------------------------------------------------------


def test_marathi_honorifics_and_names() -> None:
    """Verifies Marathi statutory honorifics and name lists."""
    assert get_honorific_mr("male") == "श्री."
    assert get_honorific_mr("female", "married") == "सौ."
    assert get_honorific_mr("female", "unmarried") == "कु."

    assert join_party_names_mr(["सचिन"]) == "सचिन"
    assert join_party_names_mr(["सचिन", "विजय"]) == "सचिन व विजय"
    assert join_party_names_mr(["सचिन", "विजय", "अनिल"]) == "सचिन, विजय व अनिल"

    test_date = date(2026, 11, 9)
    assert format_date_mr(test_date) == "9 नोव्हेंबर 2026"
    assert format_date_mr(test_date, devanagari=True) == "९ नोव्हेंबर २०२६"


def test_english_honorifics_and_names() -> None:
    """Verifies English statutory honorifics and name lists."""
    en_pack = EnglishLanguagePack()
    assert en_pack.honorific("male") == "Mr."
    assert en_pack.honorific("female", "married") == "Mrs."
    assert en_pack.honorific("female", "unmarried") == "Ms."

    assert en_pack.join_names(["Sachin"]) == "Sachin"
    assert en_pack.join_names(["Sachin", "Vijay"]) == "Sachin and Vijay"
    assert en_pack.join_names(["Sachin", "Vijay", "Anil"]) == "Sachin, Vijay and Anil"

    test_date = date(2026, 11, 9)
    assert en_pack.format_date(test_date) == "9th November 2026"


# ---------------------------------------------------------------------------
# 6. Language Registry and Jinja Template Filters
# ---------------------------------------------------------------------------


def test_language_pack_registry() -> None:
    """Verifies registry lookup and Jinja filter generator."""
    mr = get_language_pack("mr")
    assert isinstance(mr, MarathiLanguagePack)

    en = get_language_pack("en")
    assert isinstance(en, EnglishLanguagePack)

    with pytest.raises(ValueError):
        get_language_pack("invalid_code")

    filters = get_template_filters("mr")
    assert "words" in filters
    assert "words_currency" in filters
    assert "curr_fmt" in filters
    assert filters["words"](100) == "शंभर"


# ---------------------------------------------------------------------------
# 7. Validation Bounds and Helper Endpoint Security Tests
# ---------------------------------------------------------------------------


def test_amount_to_words_endpoint_requires_auth_and_validates_bounds() -> None:
    """Verifies that /api/v1/helpers/amount-to-words requires auth and rejects invalid amounts with 422."""
    client = TestClient(app, raise_server_exceptions=False)

    # 1. Unauthenticated request -> 401 Unauthorized
    res_unauth = client.get("/api/v1/helpers/amount-to-words?amount=1000")
    assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED

    # Authenticated setup
    test_actor = Actor(
        user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000001"),
        tenant_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000002"),
        role="drafter",
    )
    app.dependency_overrides[get_current_actor] = lambda: test_actor

    try:
        # 2. Valid amount with paise -> 200 OK
        res_ok = client.get("/api/v1/helpers/amount-to-words?amount=1250000.50")
        assert res_ok.status_code == status.HTTP_200_OK
        data = res_ok.json()
        assert data["amount"] == "1250000.50"
        assert "बारा लाख पन्नास हजार रुपये आणि पन्नास पैसे फक्त" in data["words_mr"]

        # 3. Negative amount -> 422 Unprocessable Entity
        res_neg = client.get("/api/v1/helpers/amount-to-words?amount=-500")
        assert res_neg.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "negative" in res_neg.json()["detail"].lower()

        # 4. Non-finite amount (NaN / Infinity) -> 422 Unprocessable Entity
        res_nan = client.get("/api/v1/helpers/amount-to-words?amount=NaN")
        assert res_nan.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        res_inf = client.get("/api/v1/helpers/amount-to-words?amount=Infinity")
        assert res_inf.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 5. Over 10**15 bound -> 422 Unprocessable Entity
        res_over = client.get("/api/v1/helpers/amount-to-words?amount=1000000000000001")
        assert res_over.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "exceeds maximum" in res_over.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_language_packs_reject_float_and_invalid_bounds() -> None:
    """Verifies that number_to_words_mr, number_to_words_hi, and number_to_words_en reject invalid inputs."""
    # 1. Float rejection in Hindi (float removed)
    with pytest.raises(InvalidAmountError) as exc_hi_float:
        number_to_words_hi(100.50)  # type: ignore[arg-type]
    assert exc_hi_float.value.status_code == 422

    # Decimal accepted in Hindi
    assert "रुपये" in number_to_words_hi(Decimal("100.50"))

    # 2. Negative rejection
    with pytest.raises(InvalidAmountError) as exc_mr_neg:
        number_to_words_mr(-50)
    assert exc_mr_neg.value.status_code == 422

    with pytest.raises(InvalidAmountError) as exc_en_neg:
        number_to_words_en(Decimal("-0.05"))
    assert exc_en_neg.value.status_code == 422

    # 3. Non-finite rejection
    with pytest.raises(InvalidAmountError) as exc_mr_nan:
        number_to_words_mr(Decimal("NaN"))
    assert exc_mr_nan.value.status_code == 422

    # 4. Bound > 10**15 rejection
    with pytest.raises(InvalidAmountError) as exc_en_bound:
        number_to_words_en(Decimal("1000000000000000.01"))
    assert exc_en_bound.value.status_code == 422
