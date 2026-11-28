"""Explicit DocumentRenderer architecture and registry for Lekhan (docs/ARCHITECTURE.md Section 5).

Decouples document rendering strategy from storage and pipeline orchestration.
Ensures specialized generators (e.g. Marathi sale deed with derived honorifics,
number-to-words, and party blocks) are never bypassed when templates are loaded
from database TemplateVersion records or object storage.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from typing import Any, Protocol

from docxtpl import DocxTemplate
from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

from app.generation.spike_engine import (
    PlotSaleDeedInput,
    generate_plot_sale_deed_docx,
)
from app.shared.logging import get_logger
from app.templates.validator import validate_template_id

logger = get_logger(__name__)


def normalize_plot_sale_deed_payload(raw_payload: dict[str, Any]) -> dict[str, Any]:
    """Normalizes flat form fields, legacy keys, and repeater items into PlotSaleDeedInput schema."""
    payload = dict(raw_payload)

    # 1. Alias vendors -> sellers
    if "vendors" in payload and "sellers" not in payload:
        payload["sellers"] = payload["vendors"]

    # 2. Extract nested or dotted property details
    if "property_details" in payload and isinstance(payload["property_details"], dict):
        prop = dict(payload["property_details"])
        if "boundaries" in prop and "boundaries" not in payload:
            payload["boundaries"] = prop["boundaries"]
        payload["property_details"] = prop
    else:
        # Check for dotted flat keys from form submission
        if any(k.startswith("property.") for k in payload):
            payload["property_details"] = {
                "mouza": payload.get("property.mouza", "सोनेगाव"),
                "khasra_no": payload.get("property.khasra_no", "45/2"),
                "plot_no": payload.get("property.plot_no", "12"),
                "layout_name": payload.get("property.layout_name", "शिवकृपा लेआउट"),
                "sheet_no": payload.get("property.sheet_no", "14"),
                "area_sqm": payload.get("property.area_sqm", 150.0),
            }

    # 3. Extract nested or dotted boundaries
    if "boundaries" not in payload or not isinstance(payload["boundaries"], dict):
        if any(k.startswith("boundaries.") for k in payload):
            payload["boundaries"] = {
                "east": payload.get("boundaries.east", "रस्ता"),
                "west": payload.get("boundaries.west", "भूखंड क्र. 13"),
                "north": payload.get("boundaries.north", "मोकळी जागा"),
                "south": payload.get("boundaries.south", "भूखंड क्र. 11"),
            }

    # 4. Extract nested or dotted financial terms
    if "financial" not in payload or not isinstance(payload["financial"], dict):
        if "financial_terms" in payload and isinstance(payload["financial_terms"], dict):
            f_terms = payload["financial_terms"]
            payload["financial"] = {
                "total_consideration": f_terms.get("total_consideration", 0),
                "earnest_advance": f_terms.get("advance_paid", f_terms.get("earnest_advance", 0)),
                "instalments": f_terms.get("instalments", []),
            }
        elif any(k.startswith("financial.") for k in payload):
            payload["financial"] = {
                "total_consideration": payload.get("financial.total_consideration", 0),
                "earnest_advance": payload.get("financial.earnest_advance", 0),
                "instalments": payload.get("instalments", []),
            }

    # 5. Extract witnesses
    if "witnesses" in payload and isinstance(payload["witnesses"], list):
        if len(payload["witnesses"]) > 0 and not payload.get("witness_1"):
            w1 = payload["witnesses"][0]
            name = w1.get("full_name") or w1.get("name") or ""
            addr = w1.get("address") or ""
            if name and addr:
                payload["witness_1"] = f"१) श्री. {name}, रा. {addr}"
            elif name:
                payload["witness_1"] = f"१) श्री. {name}"
        if len(payload["witnesses"]) > 1 and not payload.get("witness_2"):
            w2 = payload["witnesses"][1]
            name = w2.get("full_name") or w2.get("name") or ""
            addr = w2.get("address") or ""
            if name and addr:
                payload["witness_2"] = f"२) श्री. {name}, रा. {addr}"
            elif name:
                payload["witness_2"] = f"२) श्री. {name}"

    if not payload.get("witness_1"):
        payload["witness_1"] = "१) श्री. विजय एकनाथ जोशी, रा. नागपूर"
    if not payload.get("witness_2"):
        payload["witness_2"] = "२) श्री. सचिन मनोहर देशमुख, रा. नागपूर"
    if not payload.get("execution_date"):
        payload["execution_date"] = "०९ नोव्हेंबर २०२६"

    return payload


class DocumentRenderer(Protocol):
    """Protocol that all document renderers must satisfy."""

    def can_render(self, template_id: str) -> bool:
        """Returns True if this renderer supports the given template_id."""
        ...

    def render(
        self,
        template_id: str,
        payload: dict[str, Any],
        template_bytes: bytes | None = None,
    ) -> bytes:
        """Renders and returns complete, verified DOCX bytes."""
        ...


class PlotSaleDeedMarathiRenderer:
    """Specialized renderer for sale_deed_plot_mr with derived honorifics,

    Devanagari numbers-to-words, party repeaters, and verification gate.
    """

    SUPPORTED_TEMPLATE_ID = "sale_deed_plot_mr"

    def can_render(self, template_id: str) -> bool:
        return template_id == self.SUPPORTED_TEMPLATE_ID

    def validate_payload(self, raw_payload: dict[str, Any]) -> PlotSaleDeedInput:
        """Validates payload against PlotSaleDeedInput schema, returning parsed model."""
        normalized = normalize_plot_sale_deed_payload(raw_payload)
        return PlotSaleDeedInput.model_validate(normalized)

    def render(
        self,
        template_id: str,
        payload: dict[str, Any],
        template_bytes: bytes | None = None,
    ) -> bytes:
        if template_id != self.SUPPORTED_TEMPLATE_ID:
            raise ValueError(f"PlotSaleDeedMarathiRenderer cannot render '{template_id}'.")

        input_data = self.validate_payload(payload)

        # Render with provided template_bytes (DB version) or filesystem template
        docx_bytes = generate_plot_sale_deed_docx(
            input_data,
            template_bytes=template_bytes,
        )
        return docx_bytes


class ManifestDrivenDocxRenderer:
    """Generic renderer for approved DOCX templates using sandboxed Jinja2 with StrictUndefined."""

    def can_render(self, template_id: str) -> bool:
        # Check if template directory exists and has approved manifest
        try:
            tmpl_dir = validate_template_id(template_id)
            manifest_path = tmpl_dir / "manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                return bool(
                    manifest.get("status") == "approved" and (tmpl_dir / "template.docx").exists()
                )
        except Exception:
            pass
        return False

    def render(
        self,
        template_id: str,
        payload: dict[str, Any],
        template_bytes: bytes | None = None,
    ) -> bytes:
        if template_bytes is not None:
            doc = DocxTemplate(io.BytesIO(template_bytes))
        else:
            template_dir = validate_template_id(template_id)
            manifest_path = template_dir / "manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest.get("status") != "approved":
                    raise ValueError(
                        f"Template '{template_id}' has status '{manifest.get('status')}' "
                        f"and is not approved for production drafting."
                    )
            template_path = template_dir / "template.docx"
            if not template_path.exists():
                raise ValueError(f"Template '{template_id}' not found.")
            doc = DocxTemplate(str(template_path))

        jinja_env = SandboxedEnvironment(undefined=StrictUndefined)
        doc.render(payload, jinja_env=jinja_env)
        out_buf = io.BytesIO()
        doc.save(out_buf)
        docx_bytes = out_buf.getvalue()

        # Output verification gate: assert zero leftover template tags
        with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
            for name in zf.namelist():
                if name.startswith("word/") and name.endswith(".xml"):
                    xml_content = zf.read(name).decode("utf-8", errors="ignore")
                    leftover = re.findall(r"\{\{.*?\}\}|\{%.*?%\}", xml_content)
                    if leftover:
                        raise ValueError(
                            f"Unrendered template tags remain in {name}: {leftover[:5]}"
                        )

        return docx_bytes


class RendererRegistry:
    """Registry maintaining active document renderers in precedence order."""

    def __init__(self) -> None:
        self._renderers: list[DocumentRenderer] = []

    def register(self, renderer: DocumentRenderer) -> None:
        self._renderers.append(renderer)

    def get_renderer(self, template_id: str) -> DocumentRenderer | None:
        for r in self._renderers:
            if r.can_render(template_id):
                return r
        return None

    def has_renderer(self, template_id: str) -> bool:
        return self.get_renderer(template_id) is not None


# Global singleton registry with default renderers
default_renderer_registry = RendererRegistry()
default_renderer_registry.register(PlotSaleDeedMarathiRenderer())
default_renderer_registry.register(ManifestDrivenDocxRenderer())
