"""Golden-file test for Week 3 Marathi Plot Sale Deed Spike.

Validates:
1. End-to-end generation from synthetic input.
2. Complete absence of unrendered '{{' or '{%' tags.
3. Proper formatting of Marathi numbers in words.
4. OpenXML compliance: Legal paper size (12240x20160 dxa) and PAGE footer field.
"""

import io
import zipfile
from decimal import Decimal
from pathlib import Path

from app.generation.spike_engine import (
    BoundariesInput,
    FinancialInput,
    InstalmentInput,
    PartyInput,
    PlotSaleDeedInput,
    PropertyInput,
    generate_plot_sale_deed_docx,
)


def test_marathi_plot_sale_deed_spike_generation(tmp_path: Path) -> None:
    """Verifies that the spike generates a valid Legal-sized Marathi DOCX."""
    payload = PlotSaleDeedInput(
        execution_date="०९ नोव्हेंबर २०२६",
        sellers=[
            PartyInput(
                full_name="रमेश विठ्ठलराव पाटील",
                gender="male",
                age=45,
                occupation="नोकरी",
                address="प्लॉट क्र. २२, त्रिमूर्ती नगर, नागपूर",
                pan="ABCDE1234F",
            )
        ],
        purchasers=[
            PartyInput(
                full_name="सुनीता गजानन जोशी",
                gender="female",
                age=42,
                occupation="घरकाम",
                address="फ्लॅट क्र. ४०२, गोकुळ हाइट्स, सोनेगाव, नागपूर",
                pan="XYZPQ9876K",
            )
        ],
        property_details=PropertyInput(
            mouza="सोनेगाव",
            khasra_no="४५/२",
            plot_no="१२",
            layout_name="शिवकृपा लेआउट",
            sheet_no="१४",
            area_sqm=Decimal("150.00"),
        ),
        boundaries=BoundariesInput(
            east="९.०० मी. रुंद रस्ता",
            west="भूखंड क्र. १३",
            north="लेआउट खुली जागा",
            south="भूखंड क्र. ११",
        ),
        financial=FinancialInput(
            total_consideration=Decimal("1550000.00"),
            earnest_advance=Decimal("200000.00"),
            instalments=[
                InstalmentInput(
                    amount=Decimal("1350000.00"),
                    mode="rtgs",
                    ref_no="RTGS123456789",
                    bank_name="स्टेट बँक ऑफ इंडिया",
                    date_str="०९/११/२०२६",
                )
            ],
        ),
        witness_1="१) श्री. विजय एकनाथ जोशी, रा. नागपूर",
        witness_2="२) श्री. सचिन मनोहर देशमुख, रा. नागपूर",
    )

    docx_bytes = generate_plot_sale_deed_docx(payload)
    assert len(docx_bytes) > 1000

    # Save to tmp_path or work/ for manual inspection in Word
    out_file = tmp_path / "spike_plot_sale_deed.docx"
    out_file.write_bytes(docx_bytes)
    assert out_file.exists()

    # Inspect DOCX ZIP contents
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as z:
        # 1. Verify document.xml content
        doc_xml = z.read("word/document.xml").decode("utf-8")

        # Zero unrendered tags
        assert "{{" not in doc_xml
        assert "}}" not in doc_xml
        assert "{%" not in doc_xml

        # Check critical Marathi text substitutions
        assert "खरेदीखत (भूखंड)" in doc_xml
        assert "सोनेगाव" in doc_xml
        assert "शिवकृपा लेआउट" in doc_xml
        assert "रमेश विठ्ठलराव पाटील" in doc_xml
        assert "सुनीता गजानन जोशी" in doc_xml
        assert "पंधरा लाख पन्नास हजार रुपये फक्त" in doc_xml
        assert "दोन लाख रुपये फक्त" in doc_xml
        assert "तेरा लाख पन्नास हजार रुपये फक्त" in doc_xml

        # Legal page size: 12240 x 20160 dxa
        assert 'w:w="12240"' in doc_xml
        assert 'w:h="20160"' in doc_xml

        # 2. Verify footer1.xml contains automatic PAGE field
        footer_xml = z.read("word/footer1.xml").decode("utf-8")
        assert 'w:instr="PAGE"' in footer_xml
        assert 'w:instr="NUMPAGES"' in footer_xml
