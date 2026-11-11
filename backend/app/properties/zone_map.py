"""Nagpur Urban Zone-Map and City Survey Sheet Lookup Service (F-064).

Provides authoritative Mouza (village) to City Survey Sheet index mapping
for Nagpur Municipal Corporation (NMC) and Nagpur Improvement Trust (NIT).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

NAGPUR_MOUZA_SHEET_INDEX: dict[str, dict[str, Any]] = {
    "sonegaon": {
        "mouza_en": "Sonegaon",
        "mouza_mr": "सोनेगाव",
        "zone_no": 1,
        "zone_name_en": "Laxmi Nagar Zone",
        "zone_name_mr": "लक्ष्मी नगर झोन",
        "sheets": ["12", "13", "14", "15", "16"],
        "taluka": "Nagpur (Urban)",
        "district": "Nagpur",
    },
    "dharampeth": {
        "mouza_en": "Dharampeth",
        "mouza_mr": "धरमपेठ",
        "zone_no": 2,
        "zone_name_en": "Dharampeth Zone",
        "zone_name_mr": "धरमपेठ झोन",
        "sheets": ["3", "4", "7", "8", "11"],
        "taluka": "Nagpur (Urban)",
        "district": "Nagpur",
    },
    "khamla": {
        "mouza_en": "Khamla",
        "mouza_mr": "खामला",
        "zone_no": 1,
        "zone_name_en": "Laxmi Nagar Zone",
        "zone_name_mr": "लक्ष्मी नगर झोन",
        "sheets": ["21", "22", "23", "25"],
        "taluka": "Nagpur (Urban)",
        "district": "Nagpur",
    },
    "sitabuldi": {
        "mouza_en": "Sitabuldi",
        "mouza_mr": "सीताबर्डी",
        "zone_no": 2,
        "zone_name_en": "Dharampeth Zone",
        "zone_name_mr": "धरमपेठ झोन",
        "sheets": ["1", "2", "5", "6"],
        "taluka": "Nagpur (Urban)",
        "district": "Nagpur",
    },
    "manewada": {
        "mouza_en": "Manewada",
        "mouza_mr": "मानेवाडा",
        "zone_no": 4,
        "zone_name_en": "Hanuman Nagar Zone",
        "zone_name_mr": "हनुमान नगर झोन",
        "sheets": ["30", "31", "32", "33"],
        "taluka": "Nagpur (Urban)",
        "district": "Nagpur",
    },
    "parsodi": {
        "mouza_en": "Parsodi",
        "mouza_mr": "पारसोडी",
        "zone_no": 1,
        "zone_name_en": "Laxmi Nagar Zone",
        "zone_name_mr": "लक्ष्मी नगर झोन",
        "sheets": ["9", "10"],
        "taluka": "Nagpur (Urban)",
        "district": "Nagpur",
    },
}


class ZoneSheetLookupResult(BaseModel):
    mouza_en: str
    mouza_mr: str
    zone_no: int
    zone_name: str
    available_sheets: list[str]
    is_valid_sheet: bool | None = None


def lookup_nagpur_sheet(mouza: str, sheet_no: str | None = None) -> ZoneSheetLookupResult | None:
    """Look up zone and city survey sheets for a given Nagpur Mouza."""
    clean_mouza = mouza.strip().lower()
    # Normalize Marathi or English mouza match
    matched_entry = None
    for key, data in NAGPUR_MOUZA_SHEET_INDEX.items():
        if (
            key in clean_mouza
            or data["mouza_en"].lower() in clean_mouza
            or data["mouza_mr"] in mouza
        ):
            matched_entry = data
            break

    if not matched_entry:
        return None

    is_valid = None
    if sheet_no:
        clean_sheet = sheet_no.strip()
        is_valid = clean_sheet in matched_entry["sheets"]

    return ZoneSheetLookupResult(
        mouza_en=matched_entry["mouza_en"],
        mouza_mr=matched_entry["mouza_mr"],
        zone_no=matched_entry["zone_no"],
        zone_name=matched_entry["zone_name_mr"],
        available_sheets=matched_entry["sheets"],
        is_valid_sheet=is_valid,
    )
