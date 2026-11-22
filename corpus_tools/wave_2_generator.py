"""Generator for Wave 2 Templates (28 Document Types, 56 Templates).

Creates templates-library/<id>/ with:
1. manifest.json (Schema v1, status: draft, version: 1)
2. template.docx (US Legal paper size, centered PAGE footer, Noto Sans Devanagari / Calibri, clean tags)
3. Clause library reuse (from app.templates.clauses)
4. Full validation pass with DocxLinter and ManifestCompiler
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
from docx.shared import Inches, Pt, RGBColor

from app.templates.clauses import get_clause
from app.templates.compiler import ManifestCompiler
from app.templates.lint import DocxLinter

TEMPLATES_LIB_DIR = Path(__file__).resolve().parent.parent / "templates-library"

TEMPLATES_SPEC: list[dict[str, Any]] = [
    # 1. gift_deed
    {
        "id": "gift_deed",
        "doc_type": "gift_deed",
        "prop_type": "plot",
        "name_mr": "दानपत्र (बक्षीसपत्र)",
        "name_en": "Gift Deed (Immoveable Property)",
        "parties": {
            "donors": {"role": "donor", "label_mr": "दान देणारे (दाता)", "label_en": "Donor(s)"},
            "donees": {"role": "donee", "label_mr": "दान घेणारे (ग्रहिता)", "label_en": "Donee(s)"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. दात्याने नैसर्गिक प्रेम व जिव्हाळ्यापोटी सदर मिळकत ग्रहितेस विना मोबदला स्वेच्छेने दान दिली आहे.",
            "२. ग्रहितेने सदर दान आज रोजी आनंदाने व प्रत्यक्ष कब्जासह स्वीकारले आहे.",
            "३. सदर मिळकत सर्व प्रकारच्या बोजा व वादापासून मुक्त असल्याबाबत दात्याने पूर्ण हमी दिली आहे.",
        ],
        "terms_en": [
            "1. The Donor, out of natural love and affection, hereby transfers and conveys the Schedule Property to the Donee by way of gift without monetary consideration.",
            "2. The Donee has accepted the gift along with physical possession of the Schedule Property on this date.",
            "3. The Donor warrants that the Schedule Property is free from all encumbrances, charges, and litigations.",
        ],
    },
    # 2. exchange_deed
    {
        "id": "exchange_deed",
        "doc_type": "exchange_deed",
        "prop_type": "plot",
        "name_mr": "अदलाबदल पत्र (मिळकत अदलाबदल दस्त)",
        "name_en": "Deed of Exchange (Immoveable Property)",
        "parties": {
            "first_parties": {"role": "first_party", "label_mr": "प्रथम पक्षकार", "label_en": "Party of First Part"},
            "second_parties": {"role": "second_party", "label_mr": "द्वितीय पक्षकार", "label_en": "Party of Second Part"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. उभय पक्षांनी आपापसातील सहमतीने परिशिष्ट 'अ' मधील मिळकत आणि परिशिष्ट 'ब' मधील मिळकत यांची कायदेशीर अदलाबदल केली आहे.",
            "२. आज रोजी उभय पक्षांनी आपापल्या मिळकतींचा प्रत्यक्ष व शांततामय ताबा एकमेकांस सुपूर्द केला आहे.",
            "३. दोन्ही मिळकतींवर कोणतेही कर्ज किंवा बोजा नसल्याची खात्री उभय पक्षांनी दिली आहे.",
        ],
        "terms_en": [
            "1. The parties hereto have mutually agreed to exchange the property described in Schedule 'A' with the property described in Schedule 'B'.",
            "2. Both parties have delivered and exchanged physical and vacant possession of their respective properties.",
            "3. Both parties warrant that their respective properties are clear, marketable, and free from encumbrances.",
        ],
    },
    # 3. transfer_deed
    {
        "id": "transfer_deed",
        "doc_type": "transfer_deed",
        "prop_type": "plot",
        "name_mr": "हस्तांतरण पत्र (मालकी हक्क व ताबा हस्तांतरण)",
        "name_en": "Deed of Transfer (Ownership and Rights Conveyance)",
        "parties": {
            "transferors": {"role": "transferor", "label_mr": "हस्तांतरक", "label_en": "Transferor(s)"},
            "transferees": {"role": "transferee", "label_mr": "हस्तांतरिती", "label_en": "Transferee(s)"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. हस्तांतरक यांनी सदर मिळकतीवरील आपले सर्व कायदेशीर हक्क, मालकी व हितसंबंध हस्तांतरिती यांच्या नावे हस्तांतरित केले आहेत.",
            "२. हस्तांतरण मोबदल्याची संपूर्ण रक्कम हस्तांतरक यांना रीतसर प्राप्त झाली असून कोणतीही बाकी राहिलेली नाही.",
            "३. आजपासून सदर मिळकतीचे संपूर्ण मालक हस्तांतरिती राहतील.",
        ],
        "terms_en": [
            "1. The Transferor hereby conveys and transfers all legal ownership rights, title, and interest in the property to the Transferee.",
            "2. The Transferor acknowledges receipt of the agreed consideration in full and final settlement.",
            "3. The Transferee shall henceforth hold and enjoy the property as absolute owner.",
        ],
    },
    # 4. house_sale_deed
    {
        "id": "house_sale_deed",
        "doc_type": "sale_deed",
        "prop_type": "residential",
        "name_mr": "घर / इमारत खरेदीखत",
        "name_en": "Deed of Absolute Sale (Residential House / Bungalow)",
        "parties": {
            "sellers": {"role": "seller", "label_mr": "विक्रेता", "label_en": "Seller(s) / Vendor(s)"},
            "purchasers": {"role": "purchaser", "label_mr": "खरेदीदार", "label_en": "Purchaser(s)"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. विक्रेत्याने सदर निवासी इमारत व जागेचा संपूर्ण मालकी हक्क खरेदीदारास कायमस्वरूपी विकला आहे.",
            "२. खरेदीदाराने मान्य केलेला संपूर्ण खरेदी मोबदला विक्रेत्यास रीतसर प्रदान केला आहे.",
            "३. इमारतीचा प्रत्यक्ष व शांततामय ताबा आज रोजी खरेदीदारास दिला आहे.",
        ],
        "terms_en": [
            "1. The Vendor hereby conveys, transfers, and sells the absolute ownership of the residential house structure and land to the Purchaser.",
            "2. The Purchaser has paid the full and final consideration to the Vendor.",
            "3. The physical, vacant, and peaceful possession of the house has been handed over to the Purchaser.",
        ],
    },
    # 5. family_partition
    {
        "id": "family_partition",
        "doc_type": "family_partition",
        "prop_type": "agricultural",
        "name_mr": "कौटुंबिक वाटणीपत्र (सहहिस्सेदार वाटप दस्त)",
        "name_en": "Deed of Family Partition (Coparcenary Property)",
        "parties": {
            "first_sharers": {"role": "coparcener_1", "label_mr": "प्रथम वाटणीदार", "label_en": "First Coparcener"},
            "second_sharers": {"role": "coparcener_2", "label_mr": "द्वितीय वाटणीदार", "label_en": "Second Coparcener"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. उभय पक्षकारांनी कौटुंबिक सौख्यासाठी सामायिक वडिलोपार्जित मिळकतीची आपापसातील संमतीने स्वतंत्र वाटणी केली आहे.",
            "२. वाटणीनुसार प्रत्येक पक्षकाराने आपापल्या हिश्श्याचा ताबा स्वतंत्रपणे घेतला असून भविष्यात कोणाचीही हरकत असणार नाही.",
            "३. सर्व सहहिस्सेदारांनी या वाटणीस पूर्ण मान्यता दिली आहे.",
        ],
        "terms_en": [
            "1. The parties, being co-owners and legal heirs, have mutually partitioned their joint ancestral property for peace and harmony.",
            "2. Each party has taken exclusive possession of their allocated share and shall enjoy the same independently.",
            "3. The partition is final, binding, and irrevocable on all parties and their successors.",
        ],
    },
    # 6. family_settlement
    {
        "id": "family_settlement",
        "doc_type": "family_settlement",
        "prop_type": "residential",
        "name_mr": "कौटुंबिक समजोता पत्र (आपसातील समझोता करार)",
        "name_en": "Family Settlement Agreement (Dispute Resolution)",
        "parties": {
            "first_parties": {"role": "first_party", "label_mr": "प्रथम पक्षकार", "label_en": "Party of First Part"},
            "second_parties": {"role": "second_party", "label_mr": "द्वितीय पक्षकार", "label_en": "Party of Second Part"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. कौटुंबिक वाद मिटवून शांतता राखण्यासाठी उभय पक्षांनी आपापसातील ज्येष्ठ नातेवाईकांच्या मध्यस्थीने हा समझोता केला आहे.",
            "२. समझोत्यानुसार सर्व पक्षकारांनी आपल्या दाव्यांची अंतिम तडजोड केली असून न्यायालयात प्रलंबित वाद मागे घेण्याचे मान्य केले आहे.",
            "३. हा समजोता सर्व कुटुंबियांवर बंधनकारक राहील.",
        ],
        "terms_en": [
            "1. To preserve family harmony and settle all internal disputes, the parties enter into this comprehensive settlement agreement.",
            "2. All conflicting claims stand fully compromised and parties agree to withdraw any pending litigation.",
            "3. This family arrangement is permanent, binding, and enforceable.",
        ],
    },
    # 7. will
    {
        "id": "will",
        "doc_type": "will",
        "prop_type": "residential",
        "name_mr": "मृत्युपत्र (इच्छापत्र)",
        "name_en": "Last Will and Testament",
        "parties": {
            "testators": {"role": "testator", "label_mr": "इच्छापत्र / मृत्युपत्र करणारे (चाचणीकार)", "label_en": "Testator(s)"},
            "beneficiaries": {"role": "beneficiary", "label_mr": "वारसदार / लाभार्थी", "label_en": "Beneficiary(ies)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": False,
        "terms_mr": [
            "१. मी पूर्ण शुद्धीत, उत्तम शारीरिक व मानसिक स्वास्थ्यात, कोणाच्याही दबावाशिवाय हे माझे शेवटचे मृत्युपत्र करत आहे.",
            "२. यापूर्वी मी केलेले कोणतेही मृत्युपत्र किंवा इच्छापत्र असल्यास ते याद्वारे पूर्णपणे रद्दबातल ठरवितो.",
            "३. माझ्या मृत्यूनंतर माझ्या खालील सर्व स्थावर व जंगम मिळकतींची मालकी नमूद लाभार्थ्यांकडे जावी.",
        ],
        "terms_en": [
            "1. I am making this Last Will and Testament in sound state of mind and health, free from any coercion or undue influence.",
            "2. I hereby revoke all former wills, codicils, and testamentary dispositions made by me.",
            "3. Upon my demise, all my immoveable and moveable assets shall bequeath absolutely to the named beneficiaries.",
        ],
    },
    # 8. property_distribution_agreement
    {
        "id": "property_distribution_agreement",
        "doc_type": "property_distribution_agreement",
        "prop_type": "plot",
        "name_mr": "मिळकत वाटप करारनामा",
        "name_en": "Property Distribution Agreement (Co-owners)",
        "parties": {
            "first_sharers": {"role": "co_owner_1", "label_mr": "प्रथम सहमालक", "label_en": "First Co-owner"},
            "second_sharers": {"role": "co_owner_2", "label_mr": "द्वितीय सहमालक", "label_en": "Second Co-owner"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. सहमालकांनी मिळकतीचे सुलभ व्यवस्थापन व वापरासाठी वाटप करार केला आहे.",
            "२. करारानुसार वाटून दिलेल्या भागावर संबंधित सहमालकाचा स्वतंत्र वहिवाट हक्क राहील.",
            "३. महसूल व कर दायित्व वाटणीनुसार स्वतंत्रपणे अदा केले जाईल.",
        ],
        "terms_en": [
            "1. The co-owners execute this agreement to organize and distribute joint properties for efficient management.",
            "2. Each party shall have exclusive right to possess and utilize their distributed portion.",
            "3. Municipal taxes and revenue dues shall be borne individually as allocated.",
        ],
    },
    # 9. possession_letter
    {
        "id": "possession_letter",
        "doc_type": "possession_letter",
        "prop_type": "flat",
        "name_mr": "ताबा पत्र (प्रत्यक्ष ताबा सुपूर्द पत्र)",
        "name_en": "Possession Letter (Physical Handover of Unit)",
        "parties": {
            "deliverers": {"role": "deliverer", "label_mr": "ताबा देणारे (हस्तांतरक)", "label_en": "Possession Deliverer(s)"},
            "recipients": {"role": "recipient", "label_mr": "ताबा घेणारे (स्वीकारणारे)", "label_en": "Possession Recipient(s)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": False,
        "terms_mr": [
            "१. नोंदणीकृत खरेदी / हस्तांतरण दस्तानुसार नमूद मिळकतीचा प्रत्यक्ष, रिक्त व शांततामय ताबा आज रोजी देण्यात आला आहे.",
            "२. ताबा घेणाऱ्यांनी मिळकतीची पाहणी करून समाधान व्यक्त केले असून चाव्या स्वीकारल्या आहेत.",
            "३. आजपासून मिळकतीचे सर्व देखरेख व महसूल दायित्व ताबा घेणाऱ्यांवर राहील.",
        ],
        "terms_en": [
            "1. Pursuant to the registered deed, physical, vacant, and peaceful possession of the premises is delivered today.",
            "2. The recipient confirms satisfactory inspection of the premises and accepts the keys.",
            "3. Maintenance charges and outgoings from this date forward shall be the recipient's responsibility.",
        ],
    },
    # 10. possession_receipt
    {
        "id": "possession_receipt",
        "doc_type": "possession_receipt",
        "prop_type": "flat",
        "name_mr": "ताबा पावती (कब्जा पोचपावती)",
        "name_en": "Possession Receipt (Acknowledgment of Delivery)",
        "parties": {
            "recipients": {"role": "recipient", "label_mr": "ताबा स्वीकारणारे", "label_en": "Possession Acknowledger(s)"},
            "deliverers": {"role": "deliverer", "label_mr": "ताबा देणारे", "label_en": "Possession Handover Party"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": False,
        "terms_mr": [
            "१. मी/आम्ही याद्वारे पावती देतो की, नमूद मिळकतीचा प्रत्यक्ष ताबा मला/आम्हाला बिनतक्रार प्राप्त झाला आहे.",
            "२. मिळकतीत कोणतीही उणीव शिल्लक नसून सर्व चाव्या व ताबा रीतसर मिळाला आहे.",
            "३. या पावतीवर साक्षीदारांसमक्ष स्वाक्षरी केली आहे.",
        ],
        "terms_en": [
            "1. The undersigned hereby acknowledges receipt of physical and peaceful possession of the described property.",
            "2. The condition of the premises is verified and all keys have been formally received without objection.",
            "3. Signed and acknowledged in the presence of attesting witnesses.",
        ],
    },
    # 11. property_handover
    {
        "id": "property_handover",
        "doc_type": "property_handover",
        "prop_type": "commercial_unit",
        "name_mr": "मिळकत सुपूर्द पत्र (जागा हस्तांतरण व ताबा)",
        "name_en": "Property Handover Memorandum",
        "parties": {
            "handover_parties": {"role": "handover_party", "label_mr": "सुपूर्द करणारे", "label_en": "Handover Party"},
            "takeover_parties": {"role": "takeover_party", "label_mr": "स्वीकारणारे", "label_en": "Takeover Party"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": False,
        "terms_mr": [
            "१. कराराच्या अटींनुसार नमूद जागेचे हस्तांतरण व सुपूर्दीकरण आज पूर्ण करण्यात आले आहे.",
            "२. जागेतील सर्व फिक्स्चर, फिटिंग्ज व उपकरणांची संयुक्त तपासणी पूर्ण झाली आहे.",
            "३. आजच्या तारखेपासून सर्व सुरक्षा व व्यवस्थापन दायित्व स्वीकारणाऱ्या पक्षाकडे असेल.",
        ],
        "terms_en": [
            "1. In terms of the underlying agreement, formal handover of the premises is completed on this date.",
            "2. All fixtures, fittings, and infrastructure have been jointly verified and accepted.",
            "3. Security and custodial responsibility vest in the takeover party from this handover date.",
        ],
    },
    # 12. rights_transfer
    {
        "id": "rights_transfer",
        "doc_type": "rights_transfer",
        "prop_type": "flat",
        "name_mr": "हक्क हस्तांतरण पत्र (करार व वाटप हक्क अभिहस्तांतरण)",
        "name_en": "Assignment and Transfer of Rights Deed",
        "parties": {
            "assignors": {"role": "assignor", "label_mr": "हक्क अभिहस्तांतरक", "label_en": "Assignor(s)"},
            "assignees": {"role": "assignee", "label_mr": "हक्क अभिहस्तांतरिती", "label_en": "Assignee(s)"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. अभिहस्तांतरक यांनी नमूद मिळकतीमधील आपले सर्व वाटप हक्क, विकास हक्क व हितसंबंध अभिहस्तांतरिती यांच्या लाभात हस्तांतरित केले आहेत.",
            "२. संपूर्ण हस्तांतरण मोबदला प्राप्त झाल्याची कबुली अभिहस्तांतरक देत आहेत.",
            "३. संबंधित संस्था / प्राधिकरणाकडे नाव नोंदणीसाठी अभिहस्तांतरक संपूर्ण सहकार्य करतील.",
        ],
        "terms_en": [
            "1. The Assignor assigns and transfers all allotment rights, beneficial interest, and title to the Assignee.",
            "2. Full agreed consideration has been acknowledged as received by the Assignor.",
            "3. The Assignor undertakes to execute all requisite forms for mutation with relevant authorities.",
        ],
    },
    # 13. property_rights_declaration
    {
        "id": "property_rights_declaration",
        "doc_type": "property_rights_declaration",
        "prop_type": "plot",
        "name_mr": "मिळकत हक्क घोषणापत्र (प्रतिज्ञापत्र / जाहीरनामा)",
        "name_en": "Declaration of Property Rights and Title",
        "parties": {
            "declarants": {"role": "declarant", "label_mr": "घोषणा करणारे (प्रतिज्ञाकर्ते)", "label_en": "Declarant(s)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. मी याद्वारे सत्यप्रतिज्ञेवर जाहीर करतो की, खालील परिशिष्टातील मिळकतीचा मी एकमेव कायदेशीर व प्रत्यक्ष ताबेदार मालक आहे.",
            "२. सदर मिळकतीवर कोणाचाही इतर हक्क, बोजा अथवा वाद नाही.",
            "३. हे घोषणापत्र मी स्वखुशीने व शुद्धीत संबंधित शासकीय नोंदींसाठी करत आहे.",
        ],
        "terms_en": [
            "1. The Declarant solemnly affirms being the sole and lawful owner in exclusive possession of the Schedule Property.",
            "2. There are no subsisting charges, disputes, or adverse claims of any third party.",
            "3. This declaration is executed voluntarily to establish title on public record.",
        ],
    },
    # 14. general_agreement
    {
        "id": "general_agreement",
        "doc_type": "general_agreement",
        "prop_type": "general",
        "name_mr": "सर्वसाधारण करारनामा",
        "name_en": "General Agreement / Memorandum of Understanding",
        "parties": {
            "first_parties": {"role": "first_party", "label_mr": "प्रथम पक्षकार", "label_en": "First Party"},
            "second_parties": {"role": "second_party", "label_mr": "द्वितीय पक्षकार", "label_en": "Second Party"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": False,
        "has_boundaries": False,
        "terms_mr": [
            "१. उभय पक्षांनी परस्पर सहमतीने आणि कायदेशीर मोबदल्याच्या आधारावर या करारातील अटी मान्य केल्या आहेत.",
            "२. करारातील शर्तींचे उल्लंघन झाल्यास नुकसानग्रस्त पक्षास कायदेशीर नुकसानभरपाई मागण्याचा अधिकार राहील.",
            "३. कराराची मुदत व पूर्तता उभय पक्षांवर बंधनकारक राहील.",
        ],
        "terms_en": [
            "1. The parties enter into this agreement upon mutual covenants and valid lawful consideration.",
            "2. Any breach of terms entitles the non-defaulting party to claim damages and specific performance.",
            "3. The covenants herein shall be strictly binding on both parties and their successors.",
        ],
    },
    # 15. leave_and_licence
    {
        "id": "leave_and_licence",
        "doc_type": "leave_and_licence",
        "prop_type": "residential",
        "name_mr": "लिव्ह अँड लायसन्स करार (भाडेतत्वावर वापर परवाना)",
        "name_en": "Leave and Licence Agreement (Residential)",
        "parties": {
            "licensors": {"role": "licensor", "label_mr": "परवाना देणारे (लायसन्सर)", "label_en": "Licensor(s)"},
            "licensees": {"role": "licensee", "label_mr": "परवाना घेणारे (लायसन्सदार)", "label_en": "Licensee(s)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": False,
        "terms_mr": [
            "१. परवाना देणारे यांनी केवळ तात्पुरत्या निवासी वापरासाठी नमूद जागेचा वापर परवाना ११ महिन्यांसाठी दिला आहे.",
            "२. परवाना घेणारे मासिक परवाना शुल्क नियमितपणे अदा करतील आणि अनामत रक्कम परत करण्यायोग्य राहील.",
            "३. या कराराने कोणत्याही प्रकारचे भाडेकरू हक्क किंवा मालकी हक्क निर्माण होत नाहीत.",
        ],
        "terms_en": [
            "1. The Licensor grants temporary permissive licence to use the premises for residential purpose for 11 months.",
            "2. The Licensee shall pay monthly licence compensation and deposit a refundable security deposit.",
            "3. This agreement creates only a permissive licence and no tenancy or sub-tenancy rights whatsoever.",
        ],
    },
    # 16. rent_residential
    {
        "id": "rent_residential",
        "doc_type": "rent_residential",
        "prop_type": "residential",
        "name_mr": "निवासी भाडेकरारनामा",
        "name_en": "Residential Tenancy Agreement",
        "parties": {
            "landlords": {"role": "landlord", "label_mr": "घरमालक", "label_en": "Landlord(s)"},
            "tenants": {"role": "tenant", "label_mr": "भाडेकरू", "label_en": "Tenant(s)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": False,
        "terms_mr": [
            "१. घरमालकाने नमूद निवासी सदनिका/घर भाडेकरूस मासिक भाड्याने राहण्यासाठी दिले आहे.",
            "२. वीज बिल व पाणीपट्टी भाडेकरू स्वतःच्या खर्चाने नियमित भरतील.",
            "३. भाडेकरू जागेचा वापर केवळ कुटुंबाच्या निवासी कारणासाठीच करतील.",
        ],
        "terms_en": [
            "1. The Landlord lets out the residential premise to the Tenant on agreed monthly rental.",
            "2. Utility charges including electricity and water consumption shall be borne directly by the Tenant.",
            "3. The premises shall be used exclusively for peaceful residential family purposes.",
        ],
    },
    # 17. rent_shop
    {
        "id": "rent_shop",
        "doc_type": "rent_shop",
        "prop_type": "shop",
        "name_mr": "दुकान भाडेकरारनामा (व्यावसायिक गाळा भाडेकरार)",
        "name_en": "Commercial Shop Tenancy Agreement",
        "parties": {
            "landlords": {"role": "landlord", "label_mr": "दुकान मालक", "label_en": "Landlord(s) / Shop Owner(s)"},
            "tenants": {"role": "tenant", "label_mr": "भाडेकरू (दुकानदार)", "label_en": "Tenant(s) / Shopkeeper"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. मालकाने नमूद व्यावसायिक दुकान गाळा भाडेकरूस कायदेशीर व्यवसायासाठी भाड्याने दिला आहे.",
            "२. भाडेकरू स्थानिक प्राधिकरणाचे सर्व नियम व शॉप ॲक्ट परवाना अटींचे पालन करतील.",
            "३. दुकानात कोणताही अनधिकृत फेरबदल अथवा उप-भाडेकरू ठेवण्यास सक्त मनाई आहे.",
        ],
        "terms_en": [
            "1. The Landlord lets out the commercial shop unit to the Tenant for lawful business activity.",
            "2. The Tenant shall comply with all Municipal Shop & Establishment regulations and trade permits.",
            "3. Sub-letting or unauthorized structural modifications are strictly prohibited.",
        ],
    },
    # 18. rent_commercial
    {
        "id": "rent_commercial",
        "doc_type": "rent_commercial",
        "prop_type": "commercial_unit",
        "name_mr": "व्यावसायिक जागा भाडेपट्टा करार",
        "name_en": "Commercial Premises Lease Agreement",
        "parties": {
            "lessors": {"role": "lessor", "label_mr": "भाडेपट्टा देणारे (जागा मालक)", "label_en": "Lessor(s)"},
            "lessees": {"role": "lessee", "label_mr": "भाडेपट्टा घेणारे (कंपनी / संस्था)", "label_en": "Lessee(s)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. जागा मालकाने व्यावसायिक संकुलातील नमूद जागा कार्यालयासाठी भाडेपट्ट्याने दिली आहे.",
            "२. जीएसटी व इतर लागू कर नियमानुसार अदा केले जातील.",
            "३. भाडेपट्टा समाप्तीनंतर जागा मूळ सुस्थितीत मालकास सुपूर्द केली जाईल.",
        ],
        "terms_en": [
            "1. The Lessor leases the commercial premises for corporate office and business operations.",
            "2. Applicable GST and statutory levies shall be paid over and above base rent.",
            "3. Upon lease expiry, vacant possession shall be restored in original tenantable condition.",
        ],
    },
    # 19. flat_leave_licence
    {
        "id": "flat_leave_licence",
        "doc_type": "leave_and_licence",
        "prop_type": "flat",
        "name_mr": "सदनिका लिव्ह अँड लायसन्स करार (अपार्टमेंट परवाना)",
        "name_en": "Apartment Leave and Licence Agreement",
        "parties": {
            "licensors": {"role": "licensor", "label_mr": "परवाना देणारे (सदनिका मालक)", "label_en": "Licensor(s)"},
            "licensees": {"role": "licensee", "label_mr": "परवाना घेणारे (वापरकर्ते)", "label_en": "Licensee(s)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": False,
        "terms_mr": [
            "१. सोसायटीतील नमूद निवासी सदनिकेचा तात्पुरता वापर परवाना देण्यात आला आहे.",
            "२. परवानाधारक सहकारी गृहनिर्माण संस्थेच्या सर्व उपविधी व नियमांचे काटेकोर पालन करतील.",
            "३. मासिक मेंटेनन्स व सोसायटी चार्जेस करारातील ठरल्यानुसार अदा केले जातील.",
        ],
        "terms_en": [
            "1. Temporary licence is granted for residential use of the designated society apartment.",
            "2. The Licensee shall adhere strictly to Co-operative Housing Society bye-laws.",
            "3. Society maintenance charges shall be defrayed in accordance with agreed covenants.",
        ],
    },
    # 20. agri_lease
    {
        "id": "agri_lease",
        "doc_type": "agri_lease",
        "prop_type": "agricultural",
        "name_mr": "शेतजमीन खंडपत्र करार (कौलिक करार)",
        "name_en": "Agricultural Land Lease Deed (Khandpatra)",
        "parties": {
            "land_owners": {"role": "land_owner", "label_mr": "जमीन मालक (शेतमालक)", "label_en": "Agricultural Landowner(s)"},
            "cultivators": {"role": "cultivator", "label_mr": "खंडकरी / वहिवाटदार शेतकरी", "label_en": "Cultivator / Tenant Farmer"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. शेतमालकाने नमूद शेतजमीन ठराविक वार्षिक खंडावर हंगामी शेती लागवडीसाठी दिली आहे.",
            "२. खंडकरी शेतजमिनीतील विहीर, पाणी व वहिवाट रस्त्याचा योग्य वापर करतील.",
            "३. शेती हंगामाच्या अखेरीस वार्षिक खंड रक्कम रीतसर अदा केली जाईल.",
        ],
        "terms_en": [
            "1. The landowner leases the agricultural land on annual lease rent for seasonal cultivation.",
            "2. The cultivator is granted irrigation and cart-track easement rights for agricultural activity.",
            "3. Annual agricultural lease rent shall be discharged at the close of every harvest cycle.",
        ],
    },
    # 21. mortgage_deed
    {
        "id": "mortgage_deed",
        "doc_type": "mortgage_deed",
        "prop_type": "plot",
        "name_mr": "गहाणखत (कर्ज सुरक्षिततेसाठी मिळकत गहाण)",
        "name_en": "Deed of Mortgage (Immoveable Property)",
        "parties": {
            "mortgagors": {"role": "mortgagor", "label_mr": "गहाण देणारे (कर्जदार)", "label_en": "Mortgagor(s) / Borrower(s)"},
            "mortgagees": {"role": "mortgagee", "label_mr": "गहाण घेणारे (सावकार / बँक)", "label_en": "Mortgagee(s) / Lender(s)"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. गहाण देणाऱ्यांनी मंजूर कर्जाच्या परतफेडीची हमी म्हणून नमूद मिळकत गहाण ठेवली आहे.",
            "२. कर्जाची मुद्दल व व्याजाची पूर्ण परतफेड झाल्यानंतर मिळकत गहाणमुक्त करून दिली जाईल.",
            "३. परतफेडीत कसूर झाल्यास गहाण घेणाऱ्यांस कायदेशीर कारवाई करून कर्ज वसूल करण्याचा अधिकार राहील.",
        ],
        "terms_en": [
            "1. The Mortgagor mortgages the Schedule Property as security for repayment of the loan advance.",
            "2. Upon complete repayment of principal and interest, the property shall be redeemed and reconveyed.",
            "3. In the event of default, the Mortgagee shall be entitled to exercise legal enforcement rights.",
        ],
    },
    # 22. mortgage_agreement
    {
        "id": "mortgage_agreement",
        "doc_type": "mortgage_deed",
        "prop_type": "plot",
        "name_mr": "गहाण करारनामा (कर्ज व गहाण शर्ती करार)",
        "name_en": "Mortgage Agreement and Loan Covenant",
        "parties": {
            "mortgagors": {"role": "mortgagor", "label_mr": "गहाण देणारे", "label_en": "Mortgagor(s)"},
            "mortgagees": {"role": "mortgagee", "label_mr": "गहाण घेणारे", "label_en": "Mortgagee(s)"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. कर्ज परतफेडीचे हप्ते, व्याजदर व मुदत या करारानुसार ठरविण्यात आली आहे.",
            "२. गहाण मिळकतीची सुरक्षितता टिकवून ठेवण्याचे दायित्व गहाण देणाऱ्यांवर राहील.",
            "३. अटींचे पालन होईपर्यंत मिळकतीवर प्रथम बोजा राहील.",
        ],
        "terms_en": [
            "1. The repayment instalments, interest rate, and schedule are agreed under this covenant.",
            "2. The Mortgagor undertakes to maintain the mortgage security in good condition and clear of prior charges.",
            "3. The Mortgagee shall hold a first charge on the security asset pending full satisfaction.",
        ],
    },
    # 23. simple_mortgage
    {
        "id": "simple_mortgage",
        "doc_type": "mortgage_deed",
        "prop_type": "plot",
        "name_mr": "साधे गहाणखत (विना ताबा गहाण)",
        "name_en": "Deed of Simple Mortgage (Without Possession)",
        "parties": {
            "mortgagors": {"role": "mortgagor", "label_mr": "साधे गहाण देणारे", "label_en": "Mortgagor(s)"},
            "mortgagees": {"role": "mortgagee", "label_mr": "साधे गहाण घेणारे", "label_en": "Mortgagee(s)"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. मिळकतीचा प्रत्यक्ष ताबा गहाण देणाऱ्यांकडेच राहील; केवळ कर्ज सुरक्षिततेसाठी साधे गहाण केले आहे.",
            "२. कर्ज परतफेडीत कसूर झाल्यास मिळकत विकून येणाऱ्या रकमेतून कर्ज वसूल करण्याचा अधिकार गहाण घेणाऱ्यांस राहील.",
            "३. संपूर्ण परतफेडीनंतर गहाणाचा बोजा कायदेशीरपणे रद्द केला जाईल.",
        ],
        "terms_en": [
            "1. Possession remains with the Mortgagor; the mortgage binds the Mortgagor personally to repay the debt.",
            "2. In default of repayment, the Mortgagee retains the statutory right to cause the mortgaged property to be sold.",
            "3. Upon full discharge, the simple mortgage charge shall be formally cancelled.",
        ],
    },
    # 24. usufructuary_mortgage
    {
        "id": "usufructuary_mortgage",
        "doc_type": "mortgage_deed",
        "prop_type": "agricultural",
        "name_mr": "भोगगहाणखत (ताबा व उत्पन्नासह गहाण)",
        "name_en": "Deed of Usufructuary Mortgage (With Possession)",
        "parties": {
            "mortgagors": {"role": "mortgagor", "label_mr": "भोगगहाण देणारे", "label_en": "Mortgagor(s)"},
            "mortgagees": {"role": "mortgagee", "label_mr": "भोगगहाण घेणारे", "label_en": "Mortgagee(s)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. गहाण देणाऱ्यांनी मिळकतीचा प्रत्यक्ष ताबा गहाण घेणाऱ्यांस सुपूर्द केला आहे.",
            "२. मिळकतीपासून मिळणारे भाडे, पीक अथवा उत्पन्न कर्जाचे व्याज व मुद्दलापोटी जमा करून घेण्याचा अधिकार गहाण घेणाऱ्यांस राहील.",
            "३. कर्जाची पूर्ण फेड झाल्यानंतर मिळकतीचा ताबा मूळ मालकास परत दिला जाईल.",
        ],
        "terms_en": [
            "1. The Mortgagor delivers physical possession of the mortgaged asset to the Mortgagee.",
            "2. The Mortgagee is authorized to receive rents, agricultural produce, and profits in lieu of interest and principal.",
            "3. Upon full liquidation of the mortgage debt from usufruct, vacant possession shall be restored.",
        ],
    },
    # 25. memorandum_of_deposit_of_title_deeds
    {
        "id": "memorandum_of_deposit_of_title_deeds",
        "doc_type": "mortgage_deed",
        "prop_type": "plot",
        "name_mr": "दस्तऐवज ठेव स्मरणपत्र (समभावी गहाण / MODTD)",
        "name_en": "Memorandum of Deposit of Title Deeds (Equitable Mortgage)",
        "parties": {
            "borrowers": {"role": "borrower", "label_mr": "कर्जदार / दस्त ठेव देणारे", "label_en": "Borrower(s) / Depositor(s)"},
            "lenders": {"role": "lender", "label_mr": "बँक / कर्ज संस्था (दस्त स्वीकारणारे)", "label_en": "Lender Bank / Financial Institution"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. कर्जदाराने मंजूर कर्जाच्या सुरक्षिततेसाठी मूळ मालकी दस्तांची साखळी बँकेकडे स्वेच्छेने जमा केली आहे.",
            "२. या दस्त ठेवीने मिळकतीवर कायदेशीर समभावी गहाण (Equitable Mortgage) निर्माण झाले आहे.",
            "३. कर्ज खात्याची पूर्ण पूर्तता झाल्यानंतर सर्व मूळ कागदपत्रे कर्जदारास परत केली जातील.",
        ],
        "terms_en": [
            "1. The Borrower has deposited original title deeds and chain documents with the Lender as mortgage security.",
            "2. The deposit constitutes a valid equitable mortgage under Section 58(f) of the Transfer of Property Act.",
            "3. Upon full repayment of the facility, all original title instruments shall be returned.",
        ],
    },
    # 26. loan_security_document
    {
        "id": "loan_security_document",
        "doc_type": "loan_security_document",
        "prop_type": "general",
        "name_mr": "कर्ज सुरक्षा व हमी दस्तऐवज",
        "name_en": "Loan Security and Personal Guarantee Document",
        "parties": {
            "borrowers": {"role": "borrower", "label_mr": "मुख्य कर्जदार", "label_en": "Borrower(s)"},
            "guarantors": {"role": "guarantor", "label_mr": "जामीनदार (हमीदार)", "label_en": "Guarantor(s)"},
            "lenders": {"role": "lender", "label_mr": "कर्जदाते / वित्तीय संस्था", "label_en": "Lender(s)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": False,
        "has_boundaries": False,
        "terms_mr": [
            "१. मुख्य कर्जदार व जामीनदार यांनी मंजूर कर्जाच्या परतफेडीची संयुक्त व स्वतंत्र हमी दिली आहे.",
            "२. परतफेडीत कसूर झाल्यास जामीनदाराच्या वैयक्तिक मालमत्तेतूनही वसुली करण्याचा अधिकार कर्जदात्यास राहील.",
            "३. ही हमी अटळ व अखंड स्वरूपाची राहील.",
        ],
        "terms_en": [
            "1. The Borrower and Guarantor guarantee prompt repayment of the loan on joint and several liability basis.",
            "2. In default of repayment, the Lender is entitled to proceed against the assets of the Guarantor.",
            "3. This guarantee shall be continuing and irrevocable until full discharge of the debt.",
        ],
    },
    # 27. special_poa
    {
        "id": "special_poa",
        "doc_type": "special_poa",
        "prop_type": "plot",
        "name_mr": "विशेष कुलमुखत्यारपत्र (विशिष्ट कामासाठी मुखत्यार)",
        "name_en": "Special Power of Attorney (Designated Registration & Acts)",
        "parties": {
            "principals": {"role": "principal", "label_mr": "मुखत्यार देणारे (मुख्य मालक)", "label_en": "Principal(s)"},
            "attorneys": {"role": "attorney", "label_mr": "विशेष मुखत्यार", "label_en": "Special Attorney(s)"},
        },
        "clause_ids": ["witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. मुख्य मालकाने नमूद मिळकतीच्या दस्तऐवज नोंदणी व संबंधित उप-निबंधक कार्यालयात हजर राहण्यासाठी विशेष मुखत्यार नेमले आहे.",
            "२. विशेष मुखत्यारास केवळ नमूद विशिष्ट कामापुरतेच अधिकार असून मिळकत विकण्याचा किंवा बोजा करण्याचा अधिकार नाही.",
            "३. मुखत्याराने केलेल्या सर्व अधिकृत कृत्यांस मुख्य मालक मान्यता देत आहेत.",
        ],
        "terms_en": [
            "1. The Principal appoints the Special Attorney strictly for presentation and admission of deed registration before the Sub-Registrar.",
            "2. The Special Attorney has no power of alienation, sale, or encumbrance over the property.",
            "3. The Principal ratifies and confirms all lawful acts performed under this special authority.",
        ],
    },
    # 28. irrevocable_poa
    {
        "id": "irrevocable_poa",
        "doc_type": "special_poa",
        "prop_type": "plot",
        "name_mr": "अपरिवर्तनीय कुलमुखत्यारपत्र (हितसंबंधयुक्त कुलमुखत्यार)",
        "name_en": "Irrevocable Power of Attorney (Coupled with Interest)",
        "parties": {
            "principals": {"role": "principal", "label_mr": "अधिकार देणारे (मुख्य मालक)", "label_en": "Principal(s)"},
            "attorneys": {"role": "attorney", "label_mr": "अधिकार घेणारे (कुलमुखत्यार)", "label_en": "Irrevocable Attorney(s)"},
        },
        "clause_ids": ["title_warranty", "witness_attestation"],
        "has_property": True,
        "has_boundaries": True,
        "terms_mr": [
            "१. सदर कुलमुखत्यारपत्र हे कायदेशीर मोबदला व हितसंबंधासह (Interest) दिलेले असल्याने ते भारतीय करार कायदा कलम २०२ अन्वये अपरिवर्तनीय राहील.",
            "२. कुलमुखत्यारास मिळकतीचा विकास, विक्री, करार व नोंदणी करण्याचे संपूर्ण व अबाधित अधिकार प्रदान केले आहेत.",
            "३. मुख्य मालक किंवा त्यांच्या वारसांना हे मुखत्यारपत्र एकतर्फी रद्द करण्याचा कोणताही अधिकार राहणार नाही.",
        ],
        "terms_en": [
            "1. This Power of Attorney is coupled with valuable consideration and interest, and is irrevocable under Section 202 of the Indian Contract Act.",
            "2. The Attorney is invested with plenary authority to develop, convey, alienate, and register instruments in respect of the property.",
            "3. The Principal or legal heirs shall have no power or right to revoke this authority unilaterally.",
        ],
    },
]


def build_manifest(spec: dict[str, Any], lang: str) -> dict[str, Any]:
    """Constructs Schema v1 compliant manifest dictionary."""
    template_id = f"{spec['id']}_{lang}"
    is_mr = lang == "mr"

    # Parties setup
    parties_cfg: dict[str, Any] = {}
    for p_key, p_info in spec["parties"].items():
        parties_cfg[p_key] = {
            "role": p_info["role"],
            "min_parties": 1,
            "max_parties": 4,
            "label_en": p_info["label_en"],
            "label_mr": p_info["label_mr"],
        }

    # Repeaters setup: witnesses is standard
    repeaters_cfg: dict[str, Any] = {
        "witnesses": {
            "name": "witnesses",
            "min": 2,
            "max": 2,
            "label_en": "Attesting Witnesses",
            "label_mr": "साक्षीदार",
        }
    }

    # Fields setup
    fields_cfg: dict[str, Any] = {
        "execution_date": {
            "name": "execution_date",
            "type": "string",
            "label_en": "Execution Date",
            "label_mr": "दस्त नोंदणी दिनांक",
            "required": True,
        }
    }

    sections_cfg: list[dict[str, Any]] = []

    if spec.get("has_property"):
        fields_cfg["property.mouza"] = {
            "name": "property.mouza",
            "type": "string",
            "label_en": "Mouza / Village",
            "label_mr": "मौजे",
            "required": True,
        }
        fields_cfg["property.khasra_no"] = {
            "name": "property.khasra_no",
            "type": "string",
            "label_en": "Khasra / Survey No.",
            "label_mr": "खसरा / सर्व्हे क्र.",
            "required": True,
        }
        fields_cfg["property.area_sqm"] = {
            "name": "property.area_sqm",
            "type": "decimal",
            "label_en": "Area (Sq. Metres)",
            "label_mr": "क्षेत्रफळ (चौ.मी.)",
            "required": True,
        }
        sections_cfg.append(
            {
                "id": "property_schedule",
                "title_en": "Property Schedule",
                "title_mr": "मिळकतीचे वर्णन",
                "field_names": ["property.mouza", "property.khasra_no", "property.area_sqm"],
            }
        )

    if spec.get("has_boundaries"):
        fields_cfg["boundaries.east"] = {
            "name": "boundaries.east",
            "type": "string",
            "label_en": "East Boundary",
            "label_mr": "पूर्व",
            "required": True,
        }
        fields_cfg["boundaries.west"] = {
            "name": "boundaries.west",
            "type": "string",
            "label_en": "West Boundary",
            "label_mr": "पश्चिम",
            "required": True,
        }
        fields_cfg["boundaries.north"] = {
            "name": "boundaries.north",
            "type": "string",
            "label_en": "North Boundary",
            "label_mr": "उत्तर",
            "required": True,
        }
        fields_cfg["boundaries.south"] = {
            "name": "boundaries.south",
            "type": "string",
            "label_en": "South Boundary",
            "label_mr": "दक्षिण",
            "required": True,
        }
        sections_cfg.append(
            {
                "id": "boundaries",
                "title_en": "Boundaries",
                "title_mr": "चतुःसीमा",
                "field_names": [
                    "boundaries.east",
                    "boundaries.west",
                    "boundaries.north",
                    "boundaries.south",
                ],
            }
        )

    if not sections_cfg:
        sections_cfg.append(
            {
                "id": "agreement_terms",
                "title_en": "Agreement Terms",
                "title_mr": "कराराच्या अटी व तपशील",
                "field_names": ["execution_date"],
            }
        )

    manifest: dict[str, Any] = {
        "manifest_schema": 1,
        "template_id": template_id,
        "name_en": f"{spec['name_en']}",
        "name_mr": f"{spec['name_mr']}",
        "version": 1,
        "status": "draft",
        "document_type": spec["doc_type"],
        "property_type": spec["prop_type"],
        "language": lang,
        "page_size": "legal",
        "digits_setting": "western",
        "retention_class": "matter_lifecycle",
        "parties": parties_cfg,
        "repeaters": repeaters_cfg,
        "sections": sections_cfg,
        "fields": fields_cfg,
        "clauses": spec["clause_ids"],
    }

    return manifest


def build_docx(spec: dict[str, Any], lang: str) -> bytes:
    """Builds OpenXML DOCX template adhering to OpenXML and linter standards."""
    is_mr = lang == "mr"
    doc = docx.Document()

    # Section & Legal Paper Size (8.5 x 14 in = 12240 x 20160 dxa)
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
    if is_mr:
        f_p.add_run("पान क्र. ")
        fld1 = parse_xml(
            '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:instr="PAGE"/>'
        )
        f_p._p.append(fld1)
        f_p.add_run(" / ")
        fld2 = parse_xml(
            '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:instr="NUMPAGES"/>'
        )
        f_p._p.append(fld2)
        font_name = "Noto Sans Devanagari"
    else:
        f_p.add_run("Page ")
        fld1 = parse_xml(
            '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:instr="PAGE"/>'
        )
        f_p._p.append(fld1)
        f_p.add_run(" of ")
        fld2 = parse_xml(
            '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:instr="NUMPAGES"/>'
        )
        f_p._p.append(fld2)
        font_name = "Calibri"

    for r in f_p.runs:
        r.font.name = font_name
        r.font.size = Pt(10)

    # Helper for adding paragraphs with font
    def add_p(text: str, bold: bool = False, center: bool = False, size_pt: int = 12) -> None:
        p = doc.add_paragraph()
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = bold
        run.font.name = font_name
        run.font.size = Pt(size_pt)

    # 1. Title
    title = f"॥ {spec['name_mr']} ॥" if is_mr else f"DEED OF {spec['name_en'].upper()}"
    add_p(title, bold=True, center=True, size_pt=14)

    subtitle = f"({spec['name_en']})" if is_mr else f"({spec['name_mr']})"
    add_p(subtitle, bold=False, center=True, size_pt=11)

    # 2. Execution Date
    date_str = (
        "दस्त नोंदणी दिनांक: {{ execution_date }}"
        if is_mr
        else "Date of Execution: {{ execution_date }}"
    )
    add_p(date_str, bold=False, center=True, size_pt=11)

    # 3. Statutory Computer-Generated Disclaimer
    disclaimer = (
        "[सूचना: हा संगणक-व्युत्पन्न मसुदा असून केवळ सुलभ संपादन व संदर्भासाठी आहे. अंतिम नोंदणीपूर्वी संबंधित वकिलांकडून तपासणी आवश्यक आहे.]"
        if is_mr
        else "[NOTICE: This is a computer-generated draft provided solely for reference and editing. Verification by an advocate is required prior to final registration.]"
    )
    add_p(disclaimer, bold=False, center=True, size_pt=9)

    doc.add_paragraph()  # spacer

    # 4. Parties Blocks
    for p_key, p_info in spec["parties"].items():
        header_text = (
            f"॥ {p_info['label_mr']} ॥"
            if is_mr
            else f"PARTY OF THE ROLE: {p_info['label_en'].upper()}"
        )
        add_p(header_text, bold=True, size_pt=12)

        # Single Jinja tag matching party repeater
        tag_text = f"{{{{ {p_key}_block }}}}"
        add_p(tag_text, bold=False, size_pt=11)

        note_text = (
            f'(ज्यांचा उल्लेख या दस्तात पुढे "{p_info["label_mr"]}" असा करण्यात आला आहे.)'
            if is_mr
            else f'(hereinafter referred to as the "{p_info["label_en"]}" which expression shall include legal heirs and assigns.)'
        )
        add_p(note_text, bold=False, size_pt=10)
        doc.add_paragraph()

    # 5. Background / Recital
    recital_header = "॥ पार्श्वभूमी व कारण ॥" if is_mr else "WHEREAS / RECITALS:"
    add_p(recital_header, bold=True, size_pt=12)

    if spec.get("has_property"):
        if is_mr:
            p_desc = "ज्याअर्थी, खालील परिशिष्टात नमूद मिळकत मौजे {{ property.mouza }}, खसरा क्र. {{ property.khasra_no }}, क्षेत्रफळ {{ property.area_sqm }} चौ.मी. ही मिळकत निष्कलंक व निर्वेध मालकीची आहे."
        else:
            p_desc = "WHEREAS, the property described in the Schedule below situated at Mouza {{ property.mouza }}, bearing Khasra No. {{ property.khasra_no }}, admeasuring {{ property.area_sqm }} Sq. Metres is held with clear and marketable title."
        add_p(p_desc, size_pt=11)
    else:
        gen_recital = (
            "ज्याअर्थी, उभय पक्षांनी परस्पर संमतीने हा कायदेशीर करार करण्याचे ठरविले आहे."
            if is_mr
            else "WHEREAS, the parties have mutually agreed to enter into this legal instrument on the terms set forth below."
        )
        add_p(gen_recital, size_pt=11)

    doc.add_paragraph()

    # 6. Terms & Covenants
    terms_header = "॥ नियम व शर्ती ॥" if is_mr else "TERMS AND COVENANTS:"
    add_p(terms_header, bold=True, size_pt=12)
    terms_list = spec["terms_mr"] if is_mr else spec["terms_en"]
    for t_item in terms_list:
        add_p(t_item, size_pt=11)

    # 7. Clause Library Integration
    for cid in spec["clause_ids"]:
        cb = get_clause(cid)
        if cb:
            c_header = f"॥ {cb.name_mr} ॥" if is_mr else f"COVENANT: {cb.name_en.upper()}"
            add_p(c_header, bold=True, size_pt=11)
            c_text = cb.text_mr if is_mr else cb.text_en
            # If clause has placeholders, substitute with generic placeholders
            if cb.placeholders:
                for ph in cb.placeholders:
                    c_text = c_text.replace(f"{{{ph}}}", f"[-- {ph.upper()} --]")
            add_p(c_text, size_pt=11)

    # 8. Property Schedule
    if spec.get("has_property"):
        doc.add_paragraph()
        sched_header = "॥ मिळकतीचे परिशिष्ट (शेड्युल) ॥" if is_mr else "SCHEDULE OF THE PROPERTY:"
        add_p(sched_header, bold=True, size_pt=12)
        if is_mr:
            sched_body = "सर्व ती स्थावर मिळकत मौजे {{ property.mouza }}, खसरा क्र. {{ property.khasra_no }}, क्षेत्रफळ {{ property.area_sqm }} चौ.मी. नागपूर."
        else:
            sched_body = "All that piece and parcel of immoveable property situated at Mouza {{ property.mouza }}, Khasra No. {{ property.khasra_no }}, Area {{ property.area_sqm }} Sq. Metres, Nagpur."
        add_p(sched_body, size_pt=11)

    # 9. Boundaries
    if spec.get("has_boundaries"):
        doc.add_paragraph()
        b_header = "॥ चतुःसीमा ॥" if is_mr else "BOUNDARIES:"
        add_p(b_header, bold=True, size_pt=12)
        if is_mr:
            add_p("पूर्व: {{ boundaries.east }}", size_pt=11)
            add_p("पश्चिम: {{ boundaries.west }}", size_pt=11)
            add_p("उत्तर: {{ boundaries.north }}", size_pt=11)
            add_p("दक्षिण: {{ boundaries.south }}", size_pt=11)
        else:
            add_p("East: {{ boundaries.east }}", size_pt=11)
            add_p("West: {{ boundaries.west }}", size_pt=11)
            add_p("North: {{ boundaries.north }}", size_pt=11)
            add_p("South: {{ boundaries.south }}", size_pt=11)

    # 10. Attestation and Signatures
    doc.add_paragraph()
    sig_header = "॥ स्वाक्षरी व साक्षांकन ॥" if is_mr else "IN WITNESS WHEREOF / EXECUTION:"
    add_p(sig_header, bold=True, size_pt=12)

    for p_key, p_info in spec["parties"].items():
        role_label = p_info["label_mr"] if is_mr else p_info["label_en"]
        add_p(f"स्वाक्षरी {role_label}: ____________________", bold=True, size_pt=11)

    doc.add_paragraph()
    wit_header = "साक्षीदार (Witnesses):" if is_mr else "Attesting Witnesses:"
    add_p(wit_header, bold=True, size_pt=11)
    add_p("१. नाव: ____________________ पत्ता: ____________________ स्वाक्षरी: ____________", size_pt=10)
    add_p("२. नाव: ____________________ पत्ता: ____________________ स्वाक्षरी: ____________", size_pt=10)

    stream = io.BytesIO()
    doc.save(stream)
    return stream.getvalue()


def generate_all_wave_2() -> None:
    """Generates all 56 Wave 2 templates and asserts 100% lint compliance."""
    compiler = ManifestCompiler()
    linter = DocxLinter()

    total_created = 0
    passed_lint = 0

    print(f"Starting Wave 2 template generation for {len(TEMPLATES_SPEC)} document types...")

    for spec in TEMPLATES_SPEC:
        for lang in ("mr", "en"):
            tmpl_id = f"{spec['id']}_{lang}"
            target_dir = TEMPLATES_LIB_DIR / tmpl_id
            target_dir.mkdir(parents=True, exist_ok=True)

            manifest_path = target_dir / "manifest.json"
            docx_path = target_dir / "template.docx"

            # 1. Build manifest
            manifest_dict = build_manifest(spec, lang)
            manifest_json_bytes = json.dumps(manifest_dict, indent=2, ensure_ascii=False).encode("utf-8")
            manifest_path.write_bytes(manifest_json_bytes)

            # 2. Build DOCX
            docx_bytes = build_docx(spec, lang)
            docx_path.write_bytes(docx_bytes)

            # 3. Validate
            compiled = compiler.compile(manifest_dict)
            assert compiled.template_id == tmpl_id

            report = linter.lint(docx_bytes, manifest=manifest_dict)
            if not report.can_approve or len(report.errors) > 0 or len(report.leftover_data) > 0:
                print(f"FAILED LINT for {tmpl_id}:")
                print(f"  Errors: {report.errors}")
                print(f"  Leftover: {report.leftover_data}")
                raise RuntimeError(f"Lint failed for {tmpl_id}")

            total_created += 1
            passed_lint += 1
            print(f"  [OK] {tmpl_id:45} (Manifest: compiled, Lint: 0 errors, 0 leftover PII)")

    print(f"\nSuccessfully generated and verified {total_created} templates ({passed_lint}/{total_created} passed lint)!")


if __name__ == "__main__":
    generate_all_wave_2()
