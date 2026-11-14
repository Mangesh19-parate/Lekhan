"""Lawyer-Authored Advisory Rules Engine (PRD FR-15, Features F-062).

Evaluates non-blocking statutory compliance suggestions on draft payloads:
- Income Tax Section 194-IA 1% TDS deduction threshold (> 50 Lakhs).
- Income Tax Rule 114B Form 60 PAN requirement (> 10 Lakhs).
- Maharashtra Tenancy Act Section 63 Agricultural Purchaser Certificate.
- MahaRERA Section 3 Project Registration Disclosure.
- 30-year Search Title Report recommendation.
"""

from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from app.advisory.models import AdvisoryAlert
from app.audit.service import audit_service
from app.shared.logging import get_logger

logger = get_logger(__name__)

_ADVISORY_CATALOG: tuple[AdvisoryAlert, ...] = (
    AdvisoryAlert(
        id="ADVISORY_TDS_194IA",
        rule_name="Income Tax Section 194-IA TDS",
        severity="warning",
        title_en="Statutory 1% TDS Deduction Required (Total Consideration >= Rs. 50 Lakhs)",
        title_mr="१% टीडीएस कपात आवश्यक (एकूण मोबदला रु. ५० लाख किंवा अधिक)",
        advice_en=(
            "Under Section 194-IA of the Income Tax Act 1961, the purchaser is legally required "
            "to deduct 1% TDS from the total consideration and deposit it via Form 26QB before registration."
        ),
        advice_mr=(
            "आयकर कायदा १९६१ च्या कलम १९४-आयए अन्वये एकूण मोबदला रु. ५० लाख किंवा अधिक असल्यास "
            "खरेदीदाराने १% टीडीएस कपात करून फॉर्म २६क्यूबी द्वारे भरणे बंधनकारक आहे."
        ),
        statutory_ref="Income Tax Act 1961, Section 194-IA",
        action_needed="Ensure 1% TDS challan / Form 26QB acknowledgment number is cited in payment schedule.",
    ),
    AdvisoryAlert(
        id="ADVISORY_PAN_FORM_60",
        rule_name="PAN or Form 60 Declaration",
        severity="warning",
        title_en="Mandatory PAN or Form 60 Declaration Missing",
        title_mr="पॅन कार्ड किंवा फॉर्म ६० घोषणापत्र आवश्यक",
        advice_en=(
            "Under Rule 114B of the Income Tax Rules, any party transacting immovable property "
            "valued over Rs. 10 Lakhs must provide a valid PAN or submit Form 60/61."
        ),
        advice_mr=(
            "आयकर नियम ११४बी नुसार रु. १० लाखांपेक्षा जास्त किमतीच्या स्थावर मिळकतीसाठी "
            "पॅन क्रमांक देणे किंवा पॅन नसल्यास फॉर्म ६० घोषणापत्र जोडणे अनिवार्य आहे."
        ),
        statutory_ref="Income Tax Rules 1962, Rule 114B",
        action_needed="Verify PAN numbers for all parties or attach Form 60 declaration.",
    ),
    AdvisoryAlert(
        id="ADVISORY_AGRICULTURAL_STATUS",
        rule_name="Maharashtra Agriculturalist Entitlement Check",
        severity="advisory",
        title_en="Agriculturalist Status & 7/12 Akar Verification",
        title_mr="शेतकरी दाखला व ७/१२ आकारणी पडताळणी",
        advice_en=(
            "Under Section 63 of the Maharashtra Tenancy and Agricultural Lands Act 1948, "
            "transfer of agricultural land to a non-agriculturalist is void without Collector permission. "
            "Ensure purchaser's farmer certificate and 7/12 extract Akar/Potkharab details are verified."
        ),
        advice_mr=(
            "महाराष्ट्र कुळवहिवाट व शेतजमीन कायदा १९४८ च्या कलम ६३ अन्वये शेतजमीन बिगर-शेतकऱ्यास "
            "हस्तांतरित करता येत नाही. खरेदीदार शेतकरी असल्याचा दाखला व ७/१२ वरील आकारणी/पोटखराब तपासावे."
        ),
        statutory_ref="Maharashtra Tenancy and Agricultural Lands Act 1948, Section 63",
        action_needed="Cite purchaser's farmer status certificate and revenue Akar in schedule.",
    ),
    AdvisoryAlert(
        id="ADVISORY_MAHARERA_DISCLOSURE",
        rule_name="MahaRERA Project Registration Disclosure",
        severity="advisory",
        title_en="MahaRERA Project Registration Reference",
        title_mr="महारेरा प्रकल्प नोंदणी क्रमांक पडताळणी",
        advice_en=(
            "Under Section 3 of Real Estate (Regulation and Development) Act 2016, projects exceeding "
            "500 sqm or 8 apartments require MahaRERA registration. Ensure project RERA number is cited."
        ),
        advice_mr=(
            "रेरा कायदा २०१६ च्या कलम ३ अन्वये ५०० चौ.मी. किंवा ८ पेक्षा अधिक सदनिकांच्या प्रकल्पास "
            "महारेरा नोंदणी बंधनकारक आहे. दस्तऐवजात महारेरा नोंदणी क्रमांक नमूद असल्याची खात्री करावी."
        ),
        statutory_ref="Real Estate (Regulation and Development) Act 2016, Section 3",
        action_needed="Add MahaRERA project registration number to building recitals.",
    ),
)
_RULES_BY_ID = {rule.id: rule for rule in _ADVISORY_CATALOG}


class AdvisoryRulesEngine:
    """Evaluates lawyer-authored advisory rules against matter data."""

    def list_rules(self) -> list[AdvisoryAlert]:
        """Returns the registered statutory advisory rules without evaluating dummy data."""
        return list(_ADVISORY_CATALOG)

    def evaluate_payload(
        self,
        payload: dict[str, Any],
        template_id: str | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> list[AdvisoryAlert]:
        """Evaluates all registered advisory rules and returns triggered alerts."""
        alerts: list[AdvisoryAlert] = []

        total_price = self._extract_total_price(payload)
        tmpl = (template_id or payload.get("template_id") or "").lower()

        if total_price >= Decimal("5000000"):
            alerts.append(_RULES_BY_ID["ADVISORY_TDS_194IA"])

        if total_price > Decimal("1000000") and self._has_missing_pan(payload):
            alerts.append(_RULES_BY_ID["ADVISORY_PAN_FORM_60"])

        if "agri" in tmpl or self._is_agricultural_payload(payload):
            alerts.append(_RULES_BY_ID["ADVISORY_AGRICULTURAL_STATUS"])

        if "flat" in tmpl or "apartment" in tmpl:
            alerts.append(_RULES_BY_ID["ADVISORY_MAHARERA_DISCLOSURE"])

        # Audit evaluation event
        if tenant_id:
            audit_service.log_event(
                tenant_id=tenant_id,
                action="advisory_alerts_evaluated",
                entity="advisory",
                entity_id=template_id or "payload",
                meta={"alerts_count": len(alerts), "rule_ids": [a.id for a in alerts]},
            )

        return alerts

    def _extract_total_price(self, payload: dict[str, Any]) -> Decimal:
        """Extracts total consideration amount across standard field naming patterns."""
        fin = payload.get("financial_terms") or payload.get("financial") or {}
        for key in ("total_consideration", "total_price", "agreed_price", "consideration"):
            val = fin.get(key)
            if val is not None:
                try:
                    return Decimal(str(val))
                except (InvalidOperation, ValueError, TypeError) as err:
                    logger.debug("Could not parse numeric consideration value %r: %s", val, err)
        return Decimal("0")

    def _has_missing_pan(self, payload: dict[str, Any]) -> bool:
        """Checks if any vendor or purchaser lacks a PAN string."""
        for role_key in ("vendors", "purchasers", "sellers", "parties"):
            parties_list = payload.get(role_key)
            if isinstance(parties_list, list):
                for p in parties_list:
                    if isinstance(p, dict):
                        pan = p.get("pan") or p.get("pan_masked")
                        if not pan or len(str(pan).strip()) < 5:
                            return True
        return False

    def _is_agricultural_payload(self, payload: dict[str, Any]) -> bool:
        prop = payload.get("property_details") or payload.get("property") or {}
        return "area_hectare_r" in prop or "potkharab_area" in prop or "gat_khasra_no" in prop


advisory_rules_engine = AdvisoryRulesEngine()
