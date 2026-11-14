"""Tag extraction and manifest alignment verification for DOCX templates.

Verifies:
1. Undefined tags: Tags present in DOCX that are not declared in the manifest (blocks approval).
2. Unused fields: Fields declared in the manifest that are never used in the DOCX (warning).
"""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any
from xml.etree import ElementTree as ET

from app.templates.lint.models import LintFinding, LintSeverity

W_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# Regex for {{ expr }} and {% statement %}
VAR_TAG_REGEX = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")
BLOCK_TAG_REGEX = re.compile(r"\{%\s*([^%]+?)\s*%\}")

STANDARD_BUILTINS = frozenset(
    {
        "loop",
        "loop.index",
        "loop.index0",
        "loop.first",
        "loop.last",
        "loop.length",
        "true",
        "false",
        "none",
    }
)


def extract_docx_tags(docx_bytes: bytes) -> tuple[set[str], dict[str, list[tuple[str, int]]]]:
    """Extracts all variable identifiers and expressions from DOCX XML parts.

    Returns:
        (set_of_variables, locations_map)
    """
    found_vars: set[str] = set()
    locations: dict[str, list[tuple[str, int]]] = {}

    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
        for info in zf.infolist():
            if info.filename.startswith("word/") and (
                info.filename == "word/document.xml"
                or "header" in info.filename
                or "footer" in info.filename
            ):
                content = zf.read(info.filename)
                try:
                    root = ET.fromstring(content)
                    for p_idx, p in enumerate(root.iter(f"{{{W_NAMESPACE}}}p")):
                        text = "".join(t.text or "" for t in p.iter(f"{{{W_NAMESPACE}}}t"))

                        # 1. Variable tags: {{ expression }}
                        for match in VAR_TAG_REGEX.finditer(text):
                            expr = match.group(1).strip()
                            # Extract base variable identifiers (ignoring filters like | filter_name)
                            base_expr = expr.split("|")[0].strip()
                            # Tokenize to get identifier
                            for token in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_\.]*\b", base_expr):
                                if token.lower() not in STANDARD_BUILTINS:
                                    found_vars.add(token)
                                    locations.setdefault(token, []).append((info.filename, p_idx))

                        # 2. Block tags: {% for x in collection %} or {% if condition %}
                        for match in BLOCK_TAG_REGEX.finditer(text):
                            stmt = match.group(1).strip()
                            # Extract collection in 'for x in collection'
                            for_match = re.search(
                                r"\bfor\s+\w+\s+in\s+([a-zA-Z_][a-zA-Z0-9_\.]*)", stmt
                            )
                            if for_match:
                                coll = for_match.group(1).strip()
                                found_vars.add(coll)
                                locations.setdefault(coll, []).append((info.filename, p_idx))

                            # Extract condition variables in 'if condition'
                            if stmt.startswith("if ") or stmt.startswith("elif "):
                                for token in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_\.]*\b", stmt):
                                    if token not in ("if", "elif", "and", "or", "not", "in", "is"):
                                        found_vars.add(token)
                                        locations.setdefault(token, []).append(
                                            (info.filename, p_idx)
                                        )

                except (ET.ParseError, UnicodeDecodeError, KeyError):
                    continue

    return found_vars, locations


def check_tag_alignment(docx_bytes: bytes, manifest: dict[str, Any]) -> list[LintFinding]:
    """Compares document tags against manifest declarations.

    Emits:
        - UNDEFINED_TAG (Error) for tags missing from manifest.
        - UNUSED_FIELD (Warning) for manifest fields not used in document.
    """
    findings: list[LintFinding] = []
    found_tags, locations = extract_docx_tags(docx_bytes)

    # Collect all declared manifest fields
    declared_fields: set[str] = set()

    # Fields
    raw_fields = manifest.get("fields", {})
    if isinstance(raw_fields, list):
        declared_fields.update(raw_fields)
    elif isinstance(raw_fields, dict):
        declared_fields.update(raw_fields.keys())

    # Derived fields
    raw_derived = manifest.get("derived_fields", {})
    if isinstance(raw_derived, list):
        for item in raw_derived:
            if isinstance(item, dict) and "name" in item:
                declared_fields.add(item["name"])
    elif isinstance(raw_derived, dict):
        declared_fields.update(raw_derived.keys())

    # Repeaters & party roles
    repeaters = manifest.get("repeaters", {})
    if isinstance(repeaters, dict):
        declared_fields.update(repeaters.keys())

    parties = manifest.get("parties", {})
    if isinstance(parties, dict):
        declared_fields.update(parties.keys())

    # Standard context variables
    standard_context = {
        "execution_date",
        "matter_id",
        "document_id",
        "tenant_id",
        "today",
    }
    declared_fields.update(standard_context)

    def _is_tag_declared(tag: str) -> bool:
        if tag in declared_fields:
            return True
        root_part = tag.split(".")[0].split("[")[0]
        if root_part in declared_fields:
            return True
        normalized = tag.replace("_", ".")
        if normalized in declared_fields:
            return True
        for prefix in ("property_", "financial_", "terms_"):
            if tag.startswith(prefix):
                candidate = prefix[:-1] + "." + tag[len(prefix) :]
                if candidate in declared_fields:
                    return True
        if tag.startswith("boundary_"):
            dir_name = tag.split("boundary_", 1)[1]
            if f"boundaries.{dir_name}" in declared_fields:
                return True
        clean_tag = tag[:-6] if tag.endswith("_words") else tag
        if clean_tag in declared_fields or clean_tag.replace("_", ".") in declared_fields:
            return True
        if f"financial.{clean_tag}" in declared_fields:
            return True
        if tag.endswith("_block"):
            role = tag[:-6]
            if role in parties:
                return True
        if tag.startswith("witness_") and "witnesses" in repeaters:
            return True
        if tag.endswith("_clause"):
            return True
        for df in declared_fields:
            if df.endswith(f".{clean_tag}"):
                return True
        return False

    def _is_field_used(field_name: str) -> bool:
        if any(tag == field_name or tag.startswith(f"{field_name}.") for tag in found_tags):
            return True
        flat = field_name.replace(".", "_")
        if flat in found_tags or f"{flat}_words" in found_tags:
            return True
        suffix = field_name.split(".")[-1]
        if suffix in found_tags or f"{suffix}_words" in found_tags:
            return True
        if field_name.startswith("boundaries."):
            dir_name = field_name.split("boundaries.", 1)[1]
            if f"boundary_{dir_name}" in found_tags:
                return True
        if field_name in parties and (
            f"{field_name}_block" in found_tags or field_name in found_tags
        ):
            return True
        if field_name == "witnesses" and any(t.startswith("witness_") for t in found_tags):
            return True
        if field_name == "instalments" and any(t.endswith("_clause") for t in found_tags):
            return True
        return False

    # 1. Check for Undefined Tags (in DOCX but not manifest)
    for tag in sorted(found_tags):
        if not _is_tag_declared(tag):
            locs = locations.get(tag, [("word/document.xml", 0)])
            part, p_idx = locs[0]
            findings.append(
                LintFinding(
                    code="UNDEFINED_TAG",
                    severity=LintSeverity.ERROR,
                    message=f"Undefined tag '{{{{ {tag} }}}}' in template is not declared in manifest.",
                    part=part,
                    paragraph_idx=p_idx,
                    meta={"tag": tag},
                )
            )

    # 2. Check for Unused Manifest Fields (in manifest but not DOCX)
    for field_name in sorted(declared_fields):
        # Exclude standard context variables and derived fields from mandatory usage
        if field_name in standard_context:
            continue

        if not _is_field_used(field_name):
            findings.append(
                LintFinding(
                    code="UNUSED_FIELD",
                    severity=LintSeverity.WARNING,
                    message=f"Declared manifest field '{field_name}' is not referenced anywhere in the DOCX.",
                    part="manifest",
                    meta={"field": field_name},
                )
            )

    return findings
