"""Spike generation engine for Marathi Plot Sale Deed.

Renders approved template, computes derived fields, enforces Decimal currency math,
and validates that no unrendered template tags remain in the output document.
"""

from __future__ import annotations

import io
import re
import zipfile
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

from pydantic import BaseModel, Field

from app.lang_packs.marathi import (
    get_honorific_mr,
    number_to_words_mr,
)
from app.units.area import sqm_to_sqft


class PartyInput(BaseModel):
    """Party facts for sellers or purchasers."""

    full_name: str = Field(..., description="Full legal name")
    gender: str = Field("male", description="male | female | other")
    marital_status: str | None = None
    age: int = Field(..., ge=18, le=120)
    occupation: str = Field("व्यवसाय", description="Occupation")
    address: str = Field(..., description="Full residential address")
    pan: str = Field(..., description="Synthetic PAN for testing")


class PropertyInput(BaseModel):
    """Property facts for NIT/NMC layout plot."""

    mouza: str = Field("सोनेगाव", description="Mouza name")
    khasra_no: str = Field("45/2", description="Khasra / Survey number")
    plot_no: str = Field("12", description="Plot number")
    layout_name: str = Field("शिवकृपा लेआउट", description="Layout name")
    sheet_no: str = Field("14", description="City Survey / Sheet number")
    area_sqm: Decimal = Field(..., gt=0, description="Area in Square Meters")


class BoundariesInput(BaseModel):
    """Four directions boundaries."""

    east: str = Field("रस्ता", description="East boundary")
    west: str = Field("भूखंड क्र. 13", description="West boundary")
    north: str = Field("मोकळी जागा", description="North boundary")
    south: str = Field("भूखंड क्र. 11", description="South boundary")


class InstalmentInput(BaseModel):
    """Payment instalment details."""

    amount: Decimal = Field(..., gt=0)
    mode: str = Field("cheque", description="cheque | rtgs | cash")
    ref_no: str = Field("CHQ123456", description="Cheque or UTR reference")
    bank_name: str = Field("स्टेट बँक ऑफ इंडिया", description="Bank name")
    date_str: str = Field("09/11/2026", description="Payment date")


class FinancialInput(BaseModel):
    """Consideration and payment details."""

    total_consideration: Decimal = Field(..., gt=0)
    earnest_advance: Decimal = Field(..., ge=0)
    instalments: list[InstalmentInput] = Field(default_factory=list)


class PlotSaleDeedInput(BaseModel):
    """Complete input schema for Marathi Plot Sale Deed spike."""

    execution_date: str = Field("०९ नोव्हेंबर २०२६")
    sellers: list[PartyInput] = Field(..., min_length=1, max_length=4)
    purchasers: list[PartyInput] = Field(..., min_length=1, max_length=4)
    property_details: PropertyInput
    boundaries: BoundariesInput
    financial: FinancialInput
    witness_1: str = Field("१) श्री. विजय एकनाथ जोशी, रा. नागपूर")
    witness_2: str = Field("२) श्री. सचिन मनोहर देशमुख, रा. नागपूर")


class SpikeGenerationError(Exception):
    """Raised when document generation fails or verification gate rejects output."""


def generate_plot_sale_deed_docx(
    data: PlotSaleDeedInput,
    template_path: Path | None = None,
) -> bytes:
    """Renders the Marathi Plot Sale Deed template into a complete DOCX file.

    Computes derived fields (amount in words, area conversions, party blocks),
    substitutes XML tags, and executes the verification gate.
    """
    if template_path is None:
        template_path = (
            Path(__file__).parent.parent.parent.parent
            / "templates-library"
            / "sale_deed_plot_mr"
            / "template.docx"
        )

    if not template_path.exists():
        raise SpikeGenerationError(f"Approved template not found at {template_path}")

    # 1. Compute Derived Fields
    balance_amount = data.financial.total_consideration - data.financial.earnest_advance
    if balance_amount < 0:
        raise SpikeGenerationError("Earnest advance cannot exceed total consideration.")

    area_sqft = sqm_to_sqft(data.property_details.area_sqm)

    total_words = number_to_words_mr(data.financial.total_consideration, currency=True)
    advance_words = number_to_words_mr(data.financial.earnest_advance, currency=True)
    balance_words = number_to_words_mr(balance_amount, currency=True)

    # 2. Format Repeating Parties Block
    sellers_lines: list[str] = []
    for idx, s in enumerate(data.sellers, start=1):
        honorific = get_honorific_mr(s.gender, s.marital_status)
        prefix = f"({idx}) " if len(data.sellers) > 1 else ""
        sellers_lines.append(
            f"{prefix}{honorific} {s.full_name}, वय वर्षे: {s.age}, धंदा: {s.occupation}, "
            f"रा.: {s.address}, पॅन: {s.pan}"
        )
    sellers_block = "\n".join(sellers_lines)

    purchasers_lines: list[str] = []
    for idx, p in enumerate(data.purchasers, start=1):
        honorific = get_honorific_mr(p.gender, p.marital_status)
        prefix = f"({idx}) " if len(data.purchasers) > 1 else ""
        purchasers_lines.append(
            f"{prefix}{honorific} {p.full_name}, वय वर्षे: {p.age}, धंदा: {p.occupation}, "
            f"रा.: {p.address}, पॅन: {p.pan}"
        )
    purchasers_block = "\n".join(purchasers_lines)

    # 3. Format Payment Details
    if data.financial.instalments:
        pay_lines = ["देयकाचा तपशील:"]
        for inst in data.financial.instalments:
            pay_lines.append(
                f"• रक्कम रु. {inst.amount}/- ({inst.mode.upper()}) क्र. {inst.ref_no}, "
                f"बँक: {inst.bank_name}, दिनांक: {inst.date_str}"
            )
        payment_details_clause = "\n".join(pay_lines)
    else:
        payment_details_clause = "उर्वरित रक्कम धनादेश / RTGS द्वारे अदा करण्यात आली आहे."

    # 4. Context Dictionary for XML Replacement
    replacements: dict[str, str] = {
        "{{ execution_date }}": escape(data.execution_date),
        "{{ sellers_block }}": escape(sellers_block),
        "{{ purchasers_block }}": escape(purchasers_block),
        "{{ property_mouza }}": escape(data.property_details.mouza),
        "{{ property_khasra_no }}": escape(data.property_details.khasra_no),
        "{{ property_plot_no }}": escape(data.property_details.plot_no),
        "{{ property_layout_name }}": escape(data.property_details.layout_name),
        "{{ property_sheet_no }}": escape(data.property_details.sheet_no),
        "{{ property_area_sqm }}": escape(str(data.property_details.area_sqm)),
        "{{ property_area_sqft }}": escape(str(area_sqft)),
        "{{ boundary_east }}": escape(data.boundaries.east),
        "{{ boundary_west }}": escape(data.boundaries.west),
        "{{ boundary_north }}": escape(data.boundaries.north),
        "{{ boundary_south }}": escape(data.boundaries.south),
        "{{ total_consideration }}": escape(f"{data.financial.total_consideration:,.2f}"),
        "{{ total_consideration_words }}": escape(total_words),
        "{{ earnest_advance }}": escape(f"{data.financial.earnest_advance:,.2f}"),
        "{{ earnest_advance_words }}": escape(advance_words),
        "{{ balance_amount }}": escape(f"{balance_amount:,.2f}"),
        "{{ balance_amount_words }}": escape(balance_words),
        "{{ payment_details_clause }}": escape(payment_details_clause),
        "{{ witness_1 }}": escape(data.witness_1),
        "{{ witness_2 }}": escape(data.witness_2),
    }

    # 5. Open template ZIP and substitute document.xml
    in_buf = io.BytesIO(template_path.read_bytes())
    out_buf = io.BytesIO()

    with zipfile.ZipFile(in_buf, "r") as zin, zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            if item.filename == "word/document.xml":
                doc_xml = content.decode("utf-8")
                for placeholder, val in replacements.items():
                    # Handle multi-line replacements by converting newline to Word break
                    xml_val = val.replace("\n", '<w:br/>')
                    doc_xml = doc_xml.replace(placeholder, xml_val)

                # 6. Verification Gate: Assert NO leftover tags {{ or {%
                unrendered_tags = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", doc_xml)
                if unrendered_tags:
                    raise SpikeGenerationError(
                        f"Verification Gate Failed: Unrendered template tags remain in output: {unrendered_tags}"
                    )

                content = doc_xml.encode("utf-8")

            zout.writestr(item, content)

    return out_buf.getvalue()

