"""Wave 1 Hindi Templates Generator for Lekhan.

Generates Hindi variants for each of the 8 Wave 1 deed types:
1. sale_deed_plot_hi
2. agreement_to_sell_plot_hi
3. sale_deed_flat_hi
4. agreement_to_sell_flat_hi
5. general_poa_hi
6. sale_deed_shop_hi
7. sale_deed_agricultural_hi
8. release_deed_hi

Features:
- Schema v1 compliant manifest.json (status: draft, language: hi)
- OpenXML template.docx formatted with US Legal paper size, centered PAGE footer field, Noto Sans Devanagari font
- Complete validation with ManifestCompiler and DocxLinter
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.shared import Inches, Pt

from app.templates.compiler import ManifestCompiler
from app.templates.lint import DocxLinter

TEMPLATES_LIB_DIR = Path(__file__).resolve().parent.parent / "templates-library"


WAVE_1_HINDI_SPECS: list[dict[str, Any]] = [
    # 1. sale_deed_plot_hi
    {
        "source_id": "sale_deed_plot_mr",
        "target_id": "sale_deed_plot_hi",
        "name_hi": "विक्रय विलेख (भूखंड / प्लॉट)",
        "name_en": "Sale Deed (Plot in NIT/NMC Layout)",
        "party_labels": {
            "sellers": {"label_hi": "विक्रेता (प्रथम पक्षकार)", "label_en": "Seller(s)"},
            "purchasers": {"label_hi": "क्रेता (द्वितीय पक्षकार)", "label_en": "Purchaser(s)"},
        },
        "paragraphs": [
            ("॥ विक्रय विलेख (भूखंड / प्लॉट) ॥", True, True, 14),
            ("दस्तावेज़ पंजीयन दिनांक: {{ execution_date }}, नागपुर", False, True, 11),
            ("प्रारूप दस्तावेज़ (पंजीयन से पूर्व अधिवक्ता द्वारा सत्यापन आवश्यक)", False, True, 10),
            ("१. विक्रयकर्ता (प्रथम पक्षकार):", True, False, 12),
            ("{{ sellers_block }}", False, False, 11),
            ("२. क्रेता (द्वितीय पक्षकार):", True, False, 12),
            ("{{ purchasers_block }}", False, False, 11),
            ("३. संपत्ति का विवरण (Property Schedule):", True, False, 12),
            (
                "इस विक्रय विलेख द्वारा अंतरित की जाने वाली संपत्ति जिला नागपुर, उप-जिला व तहसील नागपुर स्थित मौजे {{ property_mouza }}, "
                "खसरा क्र. {{ property_khasra_no }}, नगर भूमापन शीट क्र. {{ property_sheet_no }}, स्थित नागपुर सुधार प्रन्यास / महापालिका स्वीकृत "
                "लेआउट {{ property_layout_name }} स्थित भूखंड क्र. {{ property_plot_no }}, जिसका कुल क्षेत्रफल {{ property_area_sqm }} वर्ग मीटर "
                "(समतुल्य {{ property_area_sqft }} वर्ग फुट) है।",
                False,
                False,
                11,
            ),
            ("४. संपत्ति की चतुर्सीमा (Four Boundaries):", True, False, 12),
            ("पूर्व दिशा में: {{ boundary_east }}", False, False, 11),
            ("पश्चिम दिशा में: {{ boundary_west }}", False, False, 11),
            ("उत्तर दिशा में: {{ boundary_north }}", False, False, 11),
            ("दक्षिण दिशा में: {{ boundary_south }}", False, False, 11),
            ("५. प्रतिफल एवं भुगतान का विवरण (Consideration & Payment):", True, False, 12),
            (
                "उक्त भूखंड विक्रय का कुल प्रतिफल उभय पक्षों की आपसी सहमति से रु. {{ total_consideration }}/- (शब्दों में {{ total_consideration_words }}) "
                "तय किया गया है, जिसका भुगतान निम्नानुसार किया गया है:",
                False,
                False,
                11,
            ),
            ("क) बयाना राशि रु. {{ earnest_advance }}/- (शब्दों में {{ earnest_advance_words }}) विक्रेता को पूर्व में प्राप्त हो चुकी है।", False, False, 11),
            ("ख) शेष अंतिम राशि रु. {{ balance_amount }}/- (शब्दों में {{ balance_amount_words }}) आज विलेख निष्पादन के समय अदा की गई।", False, False, 11),
            ("{{ payment_details_clause }}", False, False, 11),
            ("६. कब्जा सुपुर्दगी एवं निर्विवाद स्वामित्व वारंटी:", True, False, 12),
            (
                "उक्त भूखंड का भौतिक, शांतिपूर्ण एवं विधिक कब्जा विक्रेता द्वारा क्रेता को आज प्रत्यक्ष रूप से सुपुर्द कर दिया गया है। "
                "विक्रेता वचन देता है कि उक्त संपत्ति सभी प्रकार के भार, बंधक, ग्रहणाधिकार, विधिक विवाद अथवा कुर्की से पूर्णतः मुक्त एवं स्वच्छ स्वत्व युक्त है।",
                False,
                False,
                11,
            ),
            ("७. साक्षीदार (Witnesses):", True, False, 12),
            ("१) {{ witness_1 }}", False, False, 11),
            ("२) {{ witness_2 }}", False, False, 11),
            ("हस्ताक्षर विक्रेता (प्रथम पक्षकार): ______________________", True, False, 11),
            ("हस्ताक्षर क्रेता (द्वितीय पक्षकार): ______________________", True, False, 11),
        ],
    },
    # 2. agreement_to_sell_plot_hi
    {
        "source_id": "agreement_to_sell_plot_mr",
        "target_id": "agreement_to_sell_plot_hi",
        "name_hi": "बयाना इकरारनामा / विक्रय अनुबंध (भूखंड)",
        "name_en": "Agreement to Sell (Plot)",
        "party_labels": {
            "prospective_sellers": {"label_hi": "प्रस्तावित विक्रेता", "label_en": "Prospective Seller(s)"},
            "prospective_purchasers": {"label_hi": "प्रस्तावित क्रेता", "label_en": "Prospective Purchaser(s)"},
        },
        "paragraphs": [
            ("॥ बयाना इकरारनामा / विक्रय अनुबंध (भूखंड) ॥", True, True, 14),
            ("दस्तावेज़ निष्पादन दिनांक: {{ execution_date }}", False, True, 11),
            ("प्रारूप दस्तावेज़ (अधिवक्ता द्वारा सत्यापन आवश्यक)", False, True, 10),
            ("प्रस्तावित विक्रेता (प्रथम पक्षकार):", True, False, 12),
            ("{{ prospective_sellers }}", False, False, 11),
            ("प्रस्तावित क्रेता (द्वितीय पक्षकार):", True, False, 12),
            ("{{ prospective_purchasers }}", False, False, 11),
            ("संपत्ति का विवरण (Property Schedule):", True, False, 12),
            (
                "मौजे {{ property.mouza }}, खसरा क्र. {{ property.khasra_no }}, भूखंड क्र. {{ property.plot_no }}, "
                "क्षेत्रफल {{ property.area_sqm }} वर्ग मीटर (समतुल्य {{ property.area_sqft }} वर्ग फुट)।",
                False,
                False,
                11,
            ),
            ("प्रतिफल एवं भुगतान की शर्तें:", True, False, 12),
            (
                "उक्त भूखंड का कुल प्रतिफल रु. {{ financial.total_consideration }} तय हुआ है, जिसमें से बयाना राशि रु. {{ financial.earnest_amount }} "
                "प्राप्त हुई है। शेष राशि रु. {{ financial.balance_due }} देय रहेगी।",
                False,
                False,
                11,
            ),
            ("उक्त व्यवहार का अंतिम विक्रय विलेख {{ terms.months_to_complete }} माह के भीतर निष्पादित किया जाना तय पाया गया है।", False, False, 11),
            ("साक्षीदार (Witnesses):", True, False, 12),
            ("{{ witnesses }}", False, False, 11),
        ],
    },
    # 3. sale_deed_flat_hi
    {
        "source_id": "sale_deed_flat_mr",
        "target_id": "sale_deed_flat_hi",
        "name_hi": "विक्रय विलेख (सदनिका / आवासीय फ्लैट)",
        "name_en": "Sale Deed (Residential Flat / Apartment)",
        "party_labels": {
            "sellers": {"label_hi": "विक्रेता", "label_en": "Seller(s)"},
            "purchasers": {"label_hi": "क्रेता", "label_en": "Purchaser(s)"},
        },
        "paragraphs": [
            ("॥ विक्रय विलेख (सदनिका / फ्लैट) ॥", True, True, 14),
            ("दस्तावेज़ निष्पादन दिनांक: {{ execution_date }}", False, True, 11),
            ("विक्रेता (प्रथम पक्षकार):", True, False, 12),
            ("{{ sellers }}", False, False, 11),
            ("क्रेता (द्वितीय पक्षकार):", True, False, 12),
            ("{{ purchasers }}", False, False, 11),
            ("सदनिका का विवरण (Property Schedule):", True, False, 12),
            (
                "सदनिका क्र. {{ property.flat_no }}, तल क्र. {{ property.floor_no }}, भवन {{ property.building_name }}, "
                "मौजे {{ property.mouza }}, खसरा क्र. {{ property.khasra_no }}, नगर भूमापन शीट क्र. {{ property.sheet_no }}, "
                "कारपेट क्षेत्रफल {{ property.carpet_area_sqm }} वर्ग मीटर (समतुल्य {{ property.carpet_area_sqft }} वर्ग फुट), "
                "साथ में पार्किंग स्थल क्र. {{ property.parking_no }}।",
                False,
                False,
                11,
            ),
            ("चतुर्सीमा (Boundaries):", True, False, 12),
            (
                "पूर्व: {{ boundaries.east }}, पश्चिम: {{ boundaries.west }}, उत्तर: {{ boundaries.north }}, दक्षिण: {{ boundaries.south }}।",
                False,
                False,
                11,
            ),
            ("प्रतिफल एवं देय राशि:", True, False, 12),
            (
                "उक्त सदनिका का कुल प्रतिफल रु. {{ financial.total_consideration }} तय हुआ है, जिसमें से बयाना राशि रु. {{ financial.earnest_advance }} "
                "प्राप्त हो चुकी है। शेष प्रतिफल राशि रु. {{ financial.balance_amount }} देय रहेगी।",
                False,
                False,
                11,
            ),
            ("साक्षीदार (Witnesses):", True, False, 12),
            ("{{ witnesses }}", False, False, 11),
        ],
    },
    # 4. agreement_to_sell_flat_hi
    {
        "source_id": "agreement_to_sell_flat_mr",
        "target_id": "agreement_to_sell_flat_hi",
        "name_hi": "सदनिका / फ्लैट विक्रय अनुबंध व बयाना रसीद",
        "name_en": "Agreement to Sell (Flat / Apartment)",
        "party_labels": {
            "prospective_sellers": {"label_hi": "प्रस्तावित विक्रेता", "label_en": "Prospective Seller(s)"},
            "prospective_purchasers": {"label_hi": "प्रस्तावित क्रेता", "label_en": "Prospective Purchaser(s)"},
        },
        "paragraphs": [
            ("॥ सदनिका / फ्लैट विक्रय अनुबंध व बयाना रसीद ॥", True, True, 14),
            ("यह विक्रय अनुबंध आज दिनांक {{ execution_date }} को निम्नांकित पक्षकारों के मध्य निष्पादित हुआ:", False, True, 11),
            ("१. बयाना स्वीकारकर्ता / प्रस्तावित विक्रेता:", True, False, 12),
            ("{{ prospective_sellers }}", False, False, 11),
            ("२. बयाना प्रदाता / प्रस्तावित क्रेता:", True, False, 12),
            ("{{ prospective_purchasers }}", False, False, 11),
            ("सदनिका का विवरण (Property Schedule):", True, False, 12),
            (
                "भवन {{ property.building_name }}, मौजे {{ property.mouza }}, खसरा क्र. {{ property.khasra_no }} स्थित "
                "तल क्र. {{ property.floor_no }}, फ्लैट क्र. {{ property.flat_no }}, जिसका कारपेट क्षेत्रफल {{ property.carpet_area_sqm }} वर्ग मीटर "
                "(समतुल्य {{ property.carpet_area_sqft }} वर्ग फुट) है।",
                False,
                False,
                11,
            ),
            ("प्रतिफल एवं अवधि की शर्तें:", True, False, 12),
            (
                "उक्त फ्लैट का कुल मान्य प्रतिफल रुपये {{ financial.total_consideration }} तय हुआ है तथा आज बयाना राशि रुपये {{ financial.earnest_amount }} प्राप्त हुई। "
                "शेष राशि रुपये {{ financial.balance_due }} अंतिम विलेख के समय देय रहेगी।",
                False,
                False,
                11,
            ),
            ("उभय पक्षों की सहमति से अंतिम विक्रय विलेख {{ terms.months_to_complete }} माह के भीतर निष्पादित व पंजीकृत किया जाएगा।", False, False, 11),
            ("साक्षीदार (Witnesses):", True, False, 12),
            ("{{ witnesses }}", False, False, 11),
        ],
    },
    # 5. general_poa_hi
    {
        "source_id": "general_poa_mr",
        "target_id": "general_poa_hi",
        "name_hi": "सामान्य मुख्तारनामा (जनरल पावर ऑफ अटॉर्नी)",
        "name_en": "General Power of Attorney (GPA)",
        "party_labels": {
            "principals": {"label_hi": "मुख्तारकर्ता (Principal)", "label_en": "Principal(s)"},
            "attorneys": {"label_hi": "मुख्तारआम (Attorney)", "label_en": "Attorney(s)"},
        },
        "paragraphs": [
            ("॥ सामान्य मुख्तारनामा (General Power of Attorney) ॥", True, True, 14),
            ("दस्तावेज़ निष्पादन दिनांक: {{ execution_date }}", False, True, 11),
            ("मुख्तारनामा निष्पादक (Principals):", True, False, 12),
            ("{{ principals }}", False, False, 11),
            ("नियुक्त मुख्तारआम (Attorneys):", True, False, 12),
            ("{{ attorneys }}", False, False, 11),
            ("संपत्ति का विवरण (Property Schedule):", True, False, 12),
            (
                "संपत्ति का विवरण: {{ property.description }}, मौजे {{ property.mouza }}, खसरा क्र. {{ property.khasra_no }}।",
                False,
                False,
                11,
            ),
            ("प्रदत्त अधिकारों की अनुसूची (Powers Granted):", True, False, 12),
            ("१. संपत्ति विक्रय व अंतरण अधिकार: {{ powers.can_sell }}", False, False, 11),
            ("२. बंधक एवं ऋण अधिकार: {{ powers.can_mortgage }}", False, False, 11),
            ("३. न्यायालय एवं विधिक प्राधिकरण में उपस्थिति: {{ powers.can_appear_court }}", False, False, 11),
            (
                "मुख्तारकर्ता यह अभिपुष्टि करता है कि मुख्तारआम द्वारा उक्त अधिकारों के तहत विधिक रूप से किया गया प्रत्येक कार्य मुख्तारकर्ता द्वारा स्वयं किया गया माना जाएगा।",
                False,
                False,
                11,
            ),
            ("साक्षीदार (Witnesses):", True, False, 12),
            ("{{ witnesses }}", False, False, 11),
        ],
    },
    # 6. sale_deed_shop_hi
    {
        "source_id": "sale_deed_shop_mr",
        "target_id": "sale_deed_shop_hi",
        "name_hi": "विक्रय विलेख (व्यावसायिक दुकान / यूनिट)",
        "name_en": "Sale Deed (Commercial Shop / Unit)",
        "party_labels": {
            "sellers": {"label_hi": "विक्रेता", "label_en": "Seller(s)"},
            "purchasers": {"label_hi": "क्रेता", "label_en": "Purchaser(s)"},
        },
        "paragraphs": [
            ("॥ विक्रय विलेख (व्यावसायिक दुकान / गाला) ॥", True, True, 14),
            ("दस्तावेज़ निष्पादन दिनांक: {{ execution_date }}", False, True, 11),
            ("विक्रेता (प्रथम पक्षकार):", True, False, 12),
            ("{{ sellers }}", False, False, 11),
            ("क्रेता (द्वितीय पक्षकार):", True, False, 12),
            ("{{ purchasers }}", False, False, 11),
            ("व्यावसायिक दुकान का विवरण (Shop Schedule):", True, False, 12),
            (
                "दुकान क्र. {{ property.shop_no }}, तल {{ property.floor_no }}, व्यावसायिक संकुल {{ property.complex_name }}, "
                "मौजे {{ property.mouza }}, खसरा क्र. {{ property.khasra_no }}, नगर भूमापन शीट क्र. {{ property.sheet_no }}, "
                "निर्मित क्षेत्रफल {{ property.builtup_area_sqm }} वर्ग मीटर, दर्शनी भाग {{ property.frontage_ft }} फुट।",
                False,
                False,
                11,
            ),
            ("चतुर्सीमा (Boundaries):", True, False, 12),
            (
                "पूर्व: {{ boundaries.east }}, पश्चिम: {{ boundaries.west }}, उत्तर: {{ boundaries.north }}, दक्षिण: {{ boundaries.south }}।",
                False,
                False,
                11,
            ),
            ("प्रतिफल एवं भुगतान की शर्तें:", True, False, 12),
            (
                "उक्त दुकान का कुल प्रतिफल रु. {{ financial.total_consideration }} तय हुआ है, जिसमें से बयाना रु. {{ financial.earnest_advance }} प्राप्त हुआ "
                "तथा शेष प्रतिफल राशि अंतिम निष्पादन पर देय रहेगी।",
                False,
                False,
                11,
            ),
            ("साक्षीदार (Witnesses):", True, False, 12),
            ("{{ witnesses }}", False, False, 11),
        ],
    },
    # 7. sale_deed_agricultural_hi
    {
        "source_id": "sale_deed_agricultural_mr",
        "target_id": "sale_deed_agricultural_hi",
        "name_hi": "विक्रय विलेख (कृषि भूमि / शेतजमीन)",
        "name_en": "Sale Deed (Agricultural Land)",
        "party_labels": {
            "sellers": {"label_hi": "विक्रेता (कृषक)", "label_en": "Seller(s)"},
            "purchasers": {"label_hi": "क्रेता (कृषक)", "label_en": "Purchaser(s)"},
        },
        "paragraphs": [
            ("॥ विक्रय विलेख (कृषि भूमि / शेतजमीन) ॥", True, True, 14),
            ("यह कृषि भूमि विक्रय विलेख आज दिनांक {{ execution_date }} को निष्पादित किया गया:", False, True, 11),
            ("१. विक्रेता (कृषक पक्षकार):", True, False, 12),
            ("{{ sellers }}", False, False, 11),
            ("२. क्रेता (कृषक पक्षकार):", True, False, 12),
            ("{{ purchasers }}", False, False, 11),
            ("कृषि भूमि का विवरण (Agricultural Schedule):", True, False, 12),
            (
                "मौजे {{ property.mouza }}, गट / खसरा क्र. {{ property.gat_khasra_no }}, कुल क्षेत्रफल {{ property.area_hectare_r }} (हेक्टर-आर), "
                "पोटखराब क्षेत्र {{ property.potkharab_area }}, आकारणी रुपये {{ property.assessment_tax }}, भूमि का प्रकार {{ property.irrigation_type }}।",
                False,
                False,
                11,
            ),
            ("चतुर्सीमा (Boundaries):", True, False, 12),
            (
                "पूर्व: {{ boundaries.east }}, पश्चिम: {{ boundaries.west }}, उत्तर: {{ boundaries.north }}, दक्षिण: {{ boundaries.south }}।",
                False,
                False,
                11,
            ),
            ("प्रतिफल एवं जल-रास्ता अधिकार:", True, False, 12),
            (
                "उक्त कृषि भूमि का कुल प्रतिफल रु. {{ financial.total_consideration }} तय हुआ है, जिसमें से बयाना रु. {{ financial.earnest_advance }} प्राप्त हुआ "
                "तथा शेष राशि विलेख पंजीयन पर देय रहेगी। साथ ही खेत में जाने का रास्ता एवं पानी की नाली का अधिकार क्रेता को सौंपा गया।",
                False,
                False,
                11,
            ),
            ("साक्षीदार (Witnesses):", True, False, 12),
            ("{{ witnesses }}", False, False, 11),
        ],
    },
    # 8. release_deed_hi
    {
        "source_id": "release_deed_mr",
        "target_id": "release_deed_hi",
        "name_hi": "हक त्याग विलेख (रिलीज़ डीड)",
        "name_en": "Deed of Release / Relinquishment of Undivided Share",
        "party_labels": {
            "releasors": {"label_hi": "हक त्यागकर्ता", "label_en": "Releasor(s)"},
            "releasees": {"label_hi": "हक ग्राहिता", "label_en": "Releasee(s)"},
        },
        "paragraphs": [
            ("॥ हक त्याग विलेख ॥", True, True, 14),
            ("(DEED OF RELEASE / RELINQUISHMENT OF UNDIVIDED SHARE)", False, True, 11),
            ("दस्तावेज़ पंजीयन दिनांक: {{ execution_date }}, नागपुर", False, True, 11),
            ("[सूचना: यह संगणक-जनित प्रारूप दस्तावेज़ है। अंतिम पंजीयन से पूर्व विधिक अधिवक्ता द्वारा सत्यापन आवश्यक है।]", False, True, 10),
            ("॥ हक त्यागकर्ता (RELEASOR / सह-हिस्सेदार) ॥", True, False, 12),
            ("{{ releasors_block }}", False, False, 11),
            ("(जिन्हें इस विलेख में आगे 'हक त्यागकर्ता' कहा गया है।)", False, False, 10),
            ("॥ हक स्वीकारकर्ता (RELEASEE / सह-हिस्सेदार) ॥", True, False, 12),
            ("{{ releasees_block }}", False, False, 11),
            ("(जिन्हें इस विलेख में आगे 'हक स्वीकारकर्ता' कहा गया है।)", False, False, 10),
            ("॥ हक त्याग विलेख की पृष्ठभूमि ॥", True, False, 12),
            (
                "चूंकि, नीचे अनुसूची में वर्णित संपत्ति मौजे {{ property.mouza }}, खसरा क्र. {{ property.khasra_no }}, "
                "प्लॉट क्र. {{ property.plot_no }}, कुल क्षेत्रफल {{ property.area_sqm }} वर्ग मीटर संयुक्त पारिवारिक संपत्ति है, "
                "जिसमें हक त्यागकर्ता का {{ property.relinquished_share }} अविभाज्य विधिक हिस्सा है;",
                False,
                False,
                11,
            ),
            (
                "और चूंकि, हक त्यागकर्ता ने पारिवारिक सौहार्द एवं नैसर्गिक प्रेमवश स्वेच्छा से अपना संपूर्ण हिस्सा बिना किसी प्रतिफल के "
                "हक स्वीकारकर्ता के पक्ष में सदैव के लिए छोड़ने का निर्णय लिया है;",
                False,
                False,
                11,
            ),
            ("॥ हक त्याग के नियम एवं शर्तें ॥", True, False, 12),
            (
                "१. हक त्यागकर्ता यह घोषित करते हैं कि उन्होंने बिना किसी प्रतिफल की अपेक्षा के, उक्त संपत्ति में अपना संपूर्ण विधिक अधिकार, "
                "स्वामित्व एवं कब्जा हक स्वीकारकर्ता के हित में स्वेच्छा से त्याग दिया है।",
                False,
                False,
                11,
            ),
            (
                "२. आज के पश्चात हक त्यागकर्ता अथवा उनके विधिक उत्तराधिकारियों का उक्त संपत्ति पर कोई अधिकार नहीं रहेगा और हक स्वीकारकर्ता ही "
                "एकमात्र पूर्ण स्वामी होंगे।",
                False,
                False,
                11,
            ),
            ("३. हक त्यागकर्ता प्रमाणित करते हैं कि उक्त संपत्ति पर कोई बंधक, भार, विधिक विवाद अथवा कुर्की नहीं है तथा संपत्ति पूर्णतः भारमुक्त है।", False, False, 11),
            ("४. स्थानीय राजस्व अभिलेखों में हक स्वीकारकर्ता का नाम एकमात्र स्वामी के रूप में दर्ज करने हेतु हक त्यागकर्ता की पूर्ण सहमति है।", False, False, 11),
            ("॥ संपत्ति का विवरण (PROPERTY SCHEDULE) ॥", True, False, 12),
            ("मौजे: {{ property.mouza }}, खसरा क्र.: {{ property.khasra_no }}, प्लॉट क्र.: {{ property.plot_no }}", False, False, 11),
            ("कुल क्षेत्रफल: {{ property.area_sqm }} वर्ग मीटर, त्यागा गया हिस्सा: {{ property.relinquished_share }}", False, False, 11),
            ("चतुर्सीमा (Boundaries):", True, False, 12),
            ("पूर्व: {{ boundaries.east }}", False, False, 11),
            ("पश्चिम: {{ boundaries.west }}", False, False, 11),
            ("उत्तर: {{ boundaries.north }}", False, False, 11),
            ("दक्षिण: {{ boundaries.south }}", False, False, 11),
            ("साक्षीदार (Witnesses):", True, False, 12),
            ("१) {{ witness_1 }}", False, False, 11),
            ("२) {{ witness_2 }}", False, False, 11),
            ("हक त्यागकर्ता के हस्ताक्षर: ________________________", True, False, 11),
            ("हक स्वीकारकर्ता के हस्ताक्षर: ________________________", True, False, 11),
        ],
    },
]


def build_hindi_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    """Builds valid Hindi Schema v1 manifest matching source manifest structure."""
    source_dir = TEMPLATES_LIB_DIR / spec["source_id"]
    source_manifest = json.loads((source_dir / "manifest.json").read_text(encoding="utf-8"))

    manifest = dict(source_manifest)
    manifest["template_id"] = spec["target_id"]
    manifest["language"] = "hi"
    manifest["status"] = "draft"
    manifest["version"] = 1
    manifest["name_mr"] = spec["name_hi"]  # Devanagari title
    manifest["name_en"] = spec["name_en"]

    # Update party labels
    if "parties" in manifest and "party_labels" in spec:
        for p_key, p_val in manifest["parties"].items():
            if p_key in spec["party_labels"]:
                p_val["label_mr"] = spec["party_labels"][p_key]["label_hi"]
                p_val["label_en"] = spec["party_labels"][p_key]["label_en"]

    return manifest


def build_hindi_docx(spec: dict[str, Any]) -> bytes:
    """Builds OpenXML DOCX template adhering to Legal size and centered PAGE footer field."""
    doc = docx.Document()
    sec = doc.sections[0]
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(14.0)
    sec.top_margin = Inches(1.0)
    sec.bottom_margin = Inches(1.0)
    sec.left_margin = Inches(1.0)
    sec.right_margin = Inches(1.0)

    # Footer setup with Centered PAGE / NUMPAGES
    f_p = sec.footer.paragraphs[0]
    f_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    f_p.add_run("पृष्ठ ")
    fld1 = parse_xml(
        '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:instr="PAGE"/>'
    )
    f_p._p.append(fld1)
    f_p.add_run(" / ")
    fld2 = parse_xml(
        '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:instr="NUMPAGES"/>'
    )
    f_p._p.append(fld2)

    for r in f_p.runs:
        r.font.name = "Noto Sans Devanagari"
        r.font.size = Pt(10)

    # Add paragraphs from spec
    for text, bold, center, size_pt in spec["paragraphs"]:
        p = doc.add_paragraph()
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = bold
        run.font.name = "Noto Sans Devanagari"
        run.font.size = Pt(size_pt)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generate_all_wave_1_hindi_templates() -> None:
    """Generates and validates all Wave 1 Hindi templates."""
    compiler = ManifestCompiler()
    linter = DocxLinter()

    print(f"Generating {len(WAVE_1_HINDI_SPECS)} Wave 1 Hindi templates...")

    for spec in WAVE_1_HINDI_SPECS:
        target_dir = TEMPLATES_LIB_DIR / spec["target_id"]
        target_dir.mkdir(parents=True, exist_ok=True)

        manifest = build_hindi_manifest(spec)
        docx_bytes = build_hindi_docx(spec)

        manifest_path = target_dir / "manifest.json"
        docx_path = target_dir / "template.docx"

        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        docx_path.write_bytes(docx_bytes)

        # Validation
        compiled = compiler.compile(manifest)
        assert compiled.template_id == spec["target_id"]

        report = linter.lint(docx_bytes, manifest=manifest)
        if not report.can_approve or len(report.errors) > 0 or len(report.leftover_data) > 0:
            print(f"FAILED {spec['target_id']}: errors={report.errors}, leftover={report.leftover_data}")
            sys.exit(1)

        print(f"  ✓ {spec['target_id']} created and passed lint (0 errors, 0 leftover data)")

    print(f"\nAll {len(WAVE_1_HINDI_SPECS)} Wave 1 Hindi templates successfully generated and approved!")


if __name__ == "__main__":
    generate_all_wave_1_hindi_templates()
