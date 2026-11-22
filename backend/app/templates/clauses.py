"""Clause Library (F-029): Reusable, lawyer-approved legal clause blocks.

Standard blocks:
- Instalment payment schedules
- Bank housing loan covenants
- Section 194-IA TDS deduction
- Vendor title warranty & indemnity
- Attesting witness declarations
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClauseBlock(BaseModel):
    clause_id: str
    name_en: str
    name_mr: str
    category: str
    text_mr: str
    text_en: str
    placeholders: list[str] = Field(default_factory=list)


CLAUSE_LIBRARY: dict[str, ClauseBlock] = {
    "tds_194ia": ClauseBlock(
        clause_id="tds_194ia",
        name_en="Income Tax Section 194-IA TDS Deduction",
        name_mr="प्राप्तिकर कायदा कलम १९४-आयए अंतर्गत टीडीएस वजावट",
        category="tax_statutory",
        text_mr=(
            "सदर मिळकतीचा एकूण मोबदला रुपये ५०,००,०००/- पेक्षा जास्त असल्याने, "
            "भारतीय प्राप्तिकर कायदा, १९६१ च्या कलम १९४-आयए मधील तरतुदींनुसार खरेदीदार यांनी एकूण मोबदल्याच्या १% "
            "रक्कम म्हणजेच रुपये {tds_amount}/- टीडीएस (TDS) म्हणून वजा करून ती शासकीय तिजोरीत जमा केली आहे "
            "व त्याचे फॉर्म क्र. 16B चे प्रमाणपत्र विक्रेते यांना सुपूर्द करण्याचे मान्य केले आहे."
        ),
        text_en=(
            "Since the total consideration of the said property exceeds Rs. 50,00,000/-, as per the statutory provisions "
            "of Section 194-IA of the Income Tax Act, 1961, the Purchaser has deducted 1% TDS amounting to Rs. {tds_amount}/- "
            "and deposited the same into the government treasury, and agrees to furnish Form 16B certificate to the Vendor."
        ),
        placeholders=["tds_amount"],
    ),
    "bank_housing_loan": ClauseBlock(
        clause_id="bank_housing_loan",
        name_en="Bank Housing Loan & Direct Disbursement Covenant",
        name_mr="बँक गृहकर्ज व थेट धनादेश वाटप करार",
        category="payment_terms",
        text_mr=(
            "सदर खरेदी व्यवहारासाठी खरेदीदार यांनी {bank_name} कडून गृहकर्ज मंजूर करून घेतले असून, "
            "मंजूर कर्जापैकी शिल्लक मोबदल्याची रक्कम रुपये {loan_disbursement_amount}/- ही सदर बँकेकडून थेट "
            "विक्रेते यांच्या नावे बँकर्स चेक / आरटीजीएस द्वारे दस्त नोंदणी वेळी सुपूर्द करण्यात येईल."
        ),
        text_en=(
            "For the purchase of the said property, the Purchaser has obtained a sanctioned housing loan from {bank_name}, "
            "and the balance consideration amounting to Rs. {loan_disbursement_amount}/- shall be disbursed directly to the Vendor "
            "via Banker's Cheque / RTGS at the time of deed registration."
        ),
        placeholders=["bank_name", "loan_disbursement_amount"],
    ),
    "title_warranty": ClauseBlock(
        clause_id="title_warranty",
        name_en="Clear & Marketable Title Warranty and Indemnity",
        name_mr="निर्दोष, बिनबोजा व निर्वेध मालकी हक्काची हमी",
        category="title_covenant",
        text_mr=(
            "विक्रेते याद्वारे खरेदीदार यांना अशी खात्री देतात की, सदर मिळकत ही सर्व प्रकारच्या कर्जबोजा, गहाण, जप्ती, "
            "कोर्ट वाद, शासकीय देणे अथवा इतर कोणत्याही बोजापासून पूर्णपणे मुक्त, निर्वेध व स्वच्छ असून, विक्रेते यांना ती विकण्याचा "
            "संपूर्ण व कायदेशीर अधिकार आहे. भविष्यात कोणताही वाद उद्भवल्यास विक्रेते खरेदीदारास पूर्णपणे नुकसानभरपाई देण्यास बांधील राहतील."
        ),
        text_en=(
            "The Vendor hereby warrants and assures the Purchaser that the said property is entirely free from all encumbrances, "
            "mortgages, attachments, court litigations, government dues or charges of any nature whatsoever, and the Vendor possesses "
            "full right and authority to convey the same. The Vendor agrees to indemnify the Purchaser against any adverse claims."
        ),
        placeholders=[],
    ),
    "witness_attestation": ClauseBlock(
        clause_id="witness_attestation",
        name_en="Attesting Witnesses Formal Declaration",
        name_mr="साक्षीदारांचे औपचारिक साक्षांकन विधान",
        category="attestation",
        text_mr=(
            "आम्ही खालील सही करणारे साक्षीदार प्रमाणित करतो की, उभय पक्षांनी आमचे समक्ष वरील दस्तऐवजातील सर्व मजकूर नीट वाचून, "
            "समजून घेऊन, पूर्ण शुद्धीत व कोणाच्याही दबावाशिवाय स्वतःच्या संमतीने स्वाक्षरी केली आहे."
        ),
        text_en=(
            "We the undersigned attesting witnesses hereby certify that both parties have signed this deed in our presence after "
            "reading and understanding the entire contents thereof, in sound state of mind and without any undue influence or coercion."
        ),
        placeholders=[],
    ),
}


def get_clause(clause_id: str) -> ClauseBlock | None:
    """Retrieve clause block by ID."""
    return CLAUSE_LIBRARY.get(clause_id)


def list_available_clauses() -> list[ClauseBlock]:
    """Returns all lawyer-approved reusable clauses."""
    return list(CLAUSE_LIBRARY.values())
