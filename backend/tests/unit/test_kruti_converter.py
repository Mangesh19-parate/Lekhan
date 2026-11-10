"""Unit tests for Kruti Dev to Unicode converter and Latin detector."""

from app.lang_packs.encodings.kruti import (
    KrutiConverter,
    RunSegment,
    merge_adjacent_runs,
)


def test_is_kruti_font() -> None:
    """Verifies Kruti font detection."""
    assert KrutiConverter.is_kruti_font("Kruti Dev 010") is True
    assert KrutiConverter.is_kruti_font("DevLys 010") is True
    assert KrutiConverter.is_kruti_font("kdm010") is True
    assert KrutiConverter.is_kruti_font("Times New Roman") is False
    assert KrutiConverter.is_kruti_font("Arial") is False
    assert KrutiConverter.is_kruti_font("Noto Sans Devanagari") is False
    assert KrutiConverter.is_kruti_font(None) is False


def test_basic_consonant_and_vowel_mapping() -> None:
    """Verifies standard single and multi-character glyph conversion."""
    # 'v' -> 'अ', 'vk' -> 'आ', 'd' -> 'क'
    assert KrutiConverter.convert_string("v") == "अ"
    assert KrutiConverter.convert_string("vk") == "आ"
    assert KrutiConverter.convert_string("d") == "क"
    assert KrutiConverter.convert_string("x") == "ग"
    assert KrutiConverter.convert_string("u") == "न"


def test_marathi_retroflex_l() -> None:
    """Verifies Marathi-specific retroflex L 'ळ' mapped from 'G'."""
    assert KrutiConverter.convert_string("G") == "ळ"
    # 'ldG' -> 'सकळ'
    assert KrutiConverter.convert_string("ldG") == "सकळ"
    # 'feGdr' -> 'मिळकत'
    assert KrutiConverter.convert_string("feGdr") == "मिळकत"


def test_pre_base_i_reordering() -> None:
    """Verifies pre-base short 'i' matra 'f' moves after the base consonant."""
    # 'fd' -> 'कि'
    assert KrutiConverter.convert_string("fd") == "कि"
    # 'fLFkfr' -> 'स्थिति' (with half consonant L and two-char Fk)
    converted = KrutiConverter.convert_string("fLFkfr")
    assert "ि" in converted
    assert converted.startswith("स्थि")


def test_post_base_reph_reordering() -> None:
    """Verifies post-base reph 'Z' moves before the base consonant as 'र्'."""
    # 'dZ' -> 'र्क'
    assert KrutiConverter.convert_string("dZ") == "र्क"
    # 'loZ' -> 'सर्व'
    assert KrutiConverter.convert_string("loZ") == "सर्व"


def test_latin_typed_in_kruti_detector() -> None:
    """Verifies detection of Latin PAN, phone/Aadhaar numbers, and keywords."""
    text_with_pan = "विक्रेता PAN ABCDE1234F मोबाईल 9876543210"
    warnings = KrutiConverter.detect_latin_in_kruti(text_with_pan)

    pattern_types = [w.pattern_type for w in warnings]
    snippets = [w.text for w in warnings]

    assert "PAN" in pattern_types
    assert "ABCDE1234F" in snippets
    assert "10_12_DIGIT_ID" in pattern_types
    assert "9876543210" in snippets


def test_merge_adjacent_runs() -> None:
    """Verifies that adjacent runs sharing identical font and style are merged."""
    runs = [
        RunSegment(text="foØ", font_name="Kruti Dev 010", bold=False, italic=False, size_pt=12.0, is_kruti=True),
        RunSegment(text="srk", font_name="Kruti Dev 010", bold=False, italic=False, size_pt=12.0, is_kruti=True),
        RunSegment(text=" (Seller)", font_name="Times New Roman", bold=False, italic=False, size_pt=12.0, is_kruti=False),
    ]

    merged = merge_adjacent_runs(runs)

    assert len(merged) == 2
    assert merged[0].text == "foØsrk"  # Successfully joined across Word split run!
    assert merged[0].is_kruti is True
    assert merged[1].text == " (Seller)"
    assert merged[1].is_kruti is False

