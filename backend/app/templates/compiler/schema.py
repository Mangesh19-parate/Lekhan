"""Manifest Schema v1 for Lekhan Legal Document Templates.

Declarative specification defining:
- Metadata, document/property classification, language, page size
- Party roles and repeaters (witnesses, instalments, schedule items)
- Form sections and input fields with types and visibility rules
- Derived fields computed at runtime in dependency order
- Declarative condition expressions and cross-field validation rules
- Retention policy and digit rendering preferences
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

FieldType = Literal[
    "string",
    "decimal",
    "integer",
    "boolean",
    "date",
    "enum",
    "text",
]

DocumentType = Literal[
    "sale_deed",
    "agreement_to_sell",
    "general_poa",
    "special_poa",
    "gift_deed",
    "lease_deed",
    "release_deed",
    "mortgage_deed",
    "will",
    "rectification_deed",
]

PropertyType = Literal[
    "plot",
    "flat",
    "shop",
    "agricultural",
    "na",
    "row_house",
    "commercial_unit",
    "office",
]

LanguageCode = Literal["mr", "en", "hi"]
PageSize = Literal["legal", "a4"]
DigitsSetting = Literal["western", "devanagari"]
RetentionClass = Literal["permanent", "statutory_12yr", "matter_lifecycle", "ephemeral"]
TemplateStatus = Literal["draft", "in_review", "approved", "deprecated", "archived"]


class PartyRoleDef(BaseModel):
    """Configuration for a legal party role (e.g. seller, purchaser, POA)."""

    role: str
    min_parties: int = 1
    max_parties: int = 4
    label_en: str = ""
    label_mr: str = ""
    description: str | None = None


class FieldDef(BaseModel):
    """Declaration of an input form field."""

    name: str
    type: FieldType = "string"
    label_en: str = ""
    label_mr: str = ""
    required: bool = True
    default: Any | None = None
    enum_values: list[str] | None = None
    visible_when: str | None = None
    help_text_en: str | None = None
    help_text_mr: str | None = None


class RepeaterDef(BaseModel):
    """Dynamic repeating structure (instalments, witnesses, boundaries)."""

    name: str = ""
    min: int = 0
    max: int = 10
    label_en: str | None = None
    label_mr: str | None = None
    fields: dict[str, FieldDef] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _normalize_repeater_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_fields = data.get("fields")
            if isinstance(raw_fields, list):
                norm: dict[str, Any] = {}
                for item in raw_fields:
                    if isinstance(item, str):
                        norm[item] = {"name": item, "label_en": item, "label_mr": item}
                    elif isinstance(item, dict) and "name" in item:
                        norm[item["name"]] = item
                data["fields"] = norm
        return data


class SectionDef(BaseModel):
    """Form section grouping for UI presentation."""

    id: str
    title_en: str
    title_mr: str
    field_names: list[str] = Field(default_factory=list)
    visible_when: str | None = None


class DerivedFieldDef(BaseModel):
    """Computed field evaluated at runtime in topological DAG order."""

    name: str
    type: FieldType = "decimal"
    expression: str
    label_en: str | None = None
    label_mr: str | None = None
    description: str | None = None


class ConditionDef(BaseModel):
    """Reusable named condition expression."""

    id: str
    expression: str
    description: str | None = None


class ValidationDef(BaseModel):
    """Cross-field assertion rule.

    'condition' expression must evaluate to True for the document to be valid.
    """

    id: str
    condition: str
    message_en: str
    message_mr: str
    severity: Literal["error", "warning"] = "error"


class ManifestSchemaV1(BaseModel):
    """Manifest Schema v1 root model."""

    manifest_schema: Literal[1] = 1
    template_id: str = "template"
    name_en: str = ""
    name_mr: str = ""
    version: int = 1
    status: TemplateStatus = "draft"
    document_type: str = "general"
    property_type: str = "general"
    language: LanguageCode = "mr"
    page_size: PageSize = "legal"
    digits_setting: DigitsSetting = "western"
    retention_class: RetentionClass = "matter_lifecycle"

    parties: dict[str, PartyRoleDef] = Field(default_factory=dict)
    repeaters: dict[str, RepeaterDef] = Field(default_factory=dict)
    sections: list[SectionDef] = Field(default_factory=list)
    fields: dict[str, FieldDef] = Field(default_factory=dict)
    derived_fields: dict[str, DerivedFieldDef] = Field(default_factory=dict)
    conditions: dict[str, ConditionDef] = Field(default_factory=dict)
    validations: list[ValidationDef] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_manifest(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Normalize fields: list -> dict
        raw_fields = data.get("fields")
        if isinstance(raw_fields, list):
            norm_fields: dict[str, Any] = {}
            for item in raw_fields:
                if isinstance(item, str):
                    norm_fields[item] = {"name": item, "label_en": item, "label_mr": item}
                elif isinstance(item, dict) and "name" in item:
                    norm_fields[item["name"]] = item
            data["fields"] = norm_fields

        # Normalize repeaters: inject name from key if missing
        raw_repeaters = data.get("repeaters")
        if isinstance(raw_repeaters, dict):
            for key, val in raw_repeaters.items():
                if isinstance(val, dict) and not val.get("name"):
                    val["name"] = key

        # Normalize derived_fields: list -> dict if passed as list
        raw_derived = data.get("derived_fields")
        if isinstance(raw_derived, list):
            norm_derived: dict[str, Any] = {}
            for item in raw_derived:
                if isinstance(item, dict) and "name" in item:
                    norm_derived[item["name"]] = item
            data["derived_fields"] = norm_derived

        return data
