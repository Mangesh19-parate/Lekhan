"""Portal Sheet Generator for Maharashtra IGR / SARATHI Portals (PRD FR-16, Features F-063, Goal G6).

Generates structured party and property data text directly from document snapshots,
enabling copy-paste entry into government registration portals without manual re-typing.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.generation.pipeline import GeneratedDocumentRecord
from app.lang_packs.english import number_to_words_en
from app.lang_packs.marathi import number_to_words_mr
from app.portal.models import (
    PortalDataSheet,
    PortalFinancial,
    PortalParty,
    PortalProperty,
)


class PortalSheetGenerator:
    """Produces assistive portal data sheets from document snapshots."""

    def generate_sheet(self, doc: GeneratedDocumentRecord) -> PortalDataSheet:
        snapshot = doc.data_snapshot or {}

        # 1. Parse Parties
        parties: list[PortalParty] = []
        for role, default_label in [
            ("vendors", "Party 1 (Executant / लिहून देणार)"),
            ("sellers", "Party 1 (Executant / लिहून देणार)"),
            ("prospective_sellers", "Party 1 (Executant / लिहून देणार)"),
            ("principals", "Party 1 (Principal / लिहून देणार)"),
            ("purchasers", "Party 2 (Claimant / लिहून घेणार)"),
            ("prospective_purchasers", "Party 2 (Claimant / लिहून घेणार)"),
            ("attorneys", "Party 2 (Attorney / कुलमुखत्यार)"),
        ]:
            party_list = snapshot.get(role)
            if isinstance(party_list, list):
                for p in party_list:
                    if isinstance(p, dict):
                        name_raw = p.get("full_name") or p.get("name") or ""
                        parties.append(
                            PortalParty(
                                role=default_label,
                                name_mr=str(name_raw),
                                name_en=str(name_raw),
                                age=int(p.get("age", 0)) if p.get("age") else None,
                                pan_masked=p.get("pan"),
                                aadhaar_last4=str(p.get("aadhaar_last4", ""))
                                if p.get("aadhaar_last4")
                                else None,
                                address=str(p.get("address", "")),
                                mobile=p.get("mobile"),
                            )
                        )

        # 2. Parse Property Details
        prop_data = snapshot.get("property_details") or snapshot.get("property") or {}
        boundaries_data = prop_data.get("boundaries") or snapshot.get("boundaries") or {}

        mouza = str(prop_data.get("mouza", snapshot.get("property.mouza", "Nagpur")))
        khasra = str(
            prop_data.get("khasra_no")
            or prop_data.get("gat_khasra_no")
            or prop_data.get("city_survey_no")
            or snapshot.get("property.khasra_no", "")
        )
        unit_no = str(
            prop_data.get("plot_no")
            or prop_data.get("flat_no")
            or prop_data.get("shop_no")
            or snapshot.get("property.flat_no", "")
        )
        floor = prop_data.get("floor_no") or snapshot.get("property.floor_no")
        bld = (
            prop_data.get("building_name")
            or prop_data.get("layout_name")
            or snapshot.get("property.building_name")
        )

        area_str = str(
            prop_data.get("area_sqm")
            or prop_data.get("carpet_area_sqm")
            or prop_data.get("area_hectare_r")
            or ""
        )

        portal_prop = PortalProperty(
            category=str(snapshot.get("property_type", "plot / residential")),
            mouza=mouza,
            khasra_survey_cts=khasra,
            unit_or_plot_no=unit_no,
            floor_no=str(floor) if floor else None,
            building_name=str(bld) if bld else None,
            area_metric=area_str,
            boundaries={str(k): str(v) for k, v in boundaries_data.items()}
            if isinstance(boundaries_data, dict)
            else {},
        )

        # 3. Parse Financial Consideration
        fin = snapshot.get("financial_terms") or snapshot.get("financial") or {}
        tot_val = (
            fin.get("total_consideration")
            or fin.get("total_price")
            or snapshot.get("financial.total_consideration")
            or 0
        )
        try:
            total_dec = Decimal(str(tot_val))
            total_int = int(total_dec)
        except (InvalidOperation, ValueError, TypeError) as err:
            logger.debug("Failed to parse consideration %r for portal summary: %s", tot_val, err)
            total_int = 0

        words_mr = number_to_words_mr(total_int, currency=True) if total_int > 0 else "रुपये शून्य फक्त"
        words_en = (
            number_to_words_en(total_int, currency=True) if total_int > 0 else "Rupees Zero Only"
        )

        portal_fin = PortalFinancial(
            total_consideration=f"{total_int:,}",
            amount_in_words_mr=words_mr,
            amount_in_words_en=words_en,
            earnest_amount=str(fin.get("advance_paid") or fin.get("earnest_amount") or ""),
            balance_amount=str(fin.get("balance_amount") or fin.get("balance_due") or ""),
            payment_mode=str(fin.get("payment_mode", "RTGS / Electronic Transfer")),
        )

        # 4. Generate Formatted Copy-Paste Plain Text Block
        copy_text = self._build_plain_text_summary(
            doc_no=doc.doc_no,
            parties=parties,
            prop=portal_prop,
            fin=portal_fin,
            execution_date=str(snapshot.get("execution_date", "")),
        )

        return PortalDataSheet(
            document_id=doc.id,
            doc_no=doc.doc_no,
            document_type=doc.language,
            parties=parties,
            property=portal_prop,
            financial=portal_fin,
            copy_paste_text=copy_text,
        )

    def _build_plain_text_summary(
        self,
        doc_no: str,
        parties: list[PortalParty],
        prop: PortalProperty,
        fin: PortalFinancial,
        execution_date: str,
    ) -> str:
        lines: list[str] = [
            "================================================================================",
            "   MAHARASHTRA SUB-REGISTRAR REGISTRATION PORTAL DATA ENTRY SHEET (IGR PDE)",
            f"   Lekhan Document No: {doc_no} | Execution Date: {execution_date}",
            "================================================================================",
            "",
            "[1] PARTIES SUMMARY (पक्षकारांचा तपशील)",
            "--------------------------------------------------------------------------------",
        ]

        for i, p in enumerate(parties, 1):
            lines.extend(
                [
                    f"Party #{i} - {p.role}:",
                    f"  Full Name:       {p.name_mr}",
                    f"  Age:             {p.age or 'N/A'}",
                    f"  PAN:             {p.pan_masked or 'N/A'}",
                    f"  Aadhaar Last 4:  {p.aadhaar_last4 or 'N/A'}",
                    f"  Address:         {p.address}",
                    "",
                ]
            )

        lines.extend(
            [
                "[2] PROPERTY PARTICULARS (मिळकतीचा तपशील)",
                "--------------------------------------------------------------------------------",
                f"  District / Taluka:        {prop.district} / {prop.taluka}",
                f"  Mouza / Village:          {prop.mouza}",
                f"  Gat / Survey / Khasra No: {prop.khasra_survey_cts}",
                f"  Unit / Plot / Flat No:    {prop.unit_or_plot_no}",
                f"  Building / Layout Name:   {prop.building_name or 'N/A'}",
                f"  Floor:                    {prop.floor_no or 'Ground'}",
                f"  Area (Metric):            {prop.area_metric}",
            ]
        )

        if prop.boundaries:
            lines.append("  Four Boundaries (चतुःसीमा):")
            for direction, boundary in prop.boundaries.items():
                lines.append(f"    - {direction.capitalize()}: {boundary}")

        lines.extend(
            [
                "",
                "[3] FINANCIAL CONSIDERATION (मोबदला व देय रक्कम)",
                "--------------------------------------------------------------------------------",
                f"  Total Consideration (Rs.):  {fin.total_consideration}/-",
                f"  Amount in Words (Marathi):  {fin.amount_in_words_mr}",
                f"  Amount in Words (English):  {fin.amount_in_words_en}",
                f"  Earnest / Advance Paid:     Rs. {fin.earnest_amount}/-",
                f"  Balance Consideration:      Rs. {fin.balance_amount}/-",
                f"  Payment Mode / Details:     {fin.payment_mode}",
                "================================================================================",
            ]
        )

        return "\n".join(lines)


portal_sheet_generator = PortalSheetGenerator()
