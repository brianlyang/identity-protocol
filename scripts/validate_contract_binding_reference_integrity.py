#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_POLICY = "IP-CP-INV-001"

REFERENCE_FIELDS: tuple[str, ...] = (
    "governance_anchor",
    "review_anchor",
    "kernel_source_path",
)
STREAM_ANCHOR_FIELDS: tuple[str, ...] = (
    "governance_anchor",
    "review_anchor",
)
ALLOWED_GATE_SURFACES: set[str] = {
    "creator",
    "readiness",
    "e2e",
    "full-scan",
    "three-plane",
    "ci",
}
STREAM_FIELD_PREFIX: dict[str, str] = {
    "governance_anchor": "docs/governance/",
    "review_anchor": "docs/review/",
}
RQ_KEY_RE = re.compile(r"^asb16-rq-\d{3}$")
RQ_ID_RE = re.compile(r"^ASB16-RQ-\d{3}$")


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    current_doc = _load_yaml(configured_path)
    if not current_doc:
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        token = str(item or "").strip()
        if token:
            out.append(token)
    return out


def _append_violation(violations: list[dict[str, Any]], *, requirement_key: str, field: str, reason: str, **extra: Any) -> None:
    row = {
        "requirement_key": requirement_key,
        "field": field,
        "reason": reason,
    }
    row.update(extra)
    violations.append(row)


def _parse_script_from_validator_id(raw: str) -> str:
    token = str(raw or "").strip()
    if not token:
        return ""
    return token.split("::", 1)[0].strip()


def _slugify_heading(text: str) -> str:
    token = str(text or "").strip().lower()
    token = token.replace("`", "").replace("*", "")
    token = "".join(ch for ch in token if ch.isalnum() or ch in {"-", " ", "_"})
    token = token.replace(" ", "-")
    return token.strip("-")


def _markdown_heading_slugs(path: Path) -> set[str]:
    slugs: set[str] = set()
    base_counts: dict[str, int] = {}
    in_code_block = False
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if not stripped.startswith("#"):
            continue
        heading = stripped.lstrip("#").strip()
        if not heading:
            continue
        base = _slugify_heading(heading)
        if not base:
            continue
        index = base_counts.get(base, 0)
        if index == 0:
            slugs.add(base)
        else:
            slugs.add(f"{base}-{index}")
        base_counts[base] = index + 1
    return slugs


def _split_ref(ref: str) -> tuple[str, str]:
    token = str(ref or "").strip()
    if "#" not in token:
        return token, ""
    path, fragment = token.split("#", 1)
    return path.strip(), fragment.strip().lower()


def _load_stream_allowed_docs(registry_path: Path) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    allowed: set[str] = set()
    if not registry_path.exists():
        errors.append(f"stream_doc_registry_missing:{registry_path}")
        return allowed, errors
    try:
        doc = _load_yaml(registry_path)
    except Exception as exc:
        errors.append(f"stream_doc_registry_parse_failed:{registry_path}:{exc}")
        return allowed, errors

    stream_rows = doc.get("stream_docs")
    if not isinstance(stream_rows, list) or not stream_rows:
        errors.append("stream_doc_registry_stream_docs_invalid")
    else:
        for row in stream_rows:
            if not isinstance(row, dict):
                errors.append("stream_doc_registry_row_not_object")
                continue
            for field in ("governance_doc", "review_doc"):
                value = str(row.get(field, "")).strip()
                if value:
                    allowed.add(value)
                else:
                    errors.append(f"stream_doc_registry_field_missing:{field}")

    mandatory_static_docs = doc.get("mandatory_static_docs")
    if not isinstance(mandatory_static_docs, list) or not mandatory_static_docs:
        errors.append("stream_doc_registry_mandatory_static_docs_invalid")
    else:
        for row in mandatory_static_docs:
            token = str(row or "").strip()
            if token:
                allowed.add(token)
    return allowed, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate contract-binding reference integrity across docs/scripts.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--contract-mapping", default="identity/protocol/mappings/contract-binding.v1.6.yaml")
    parser.add_argument(
        "--stream-doc-registry",
        default="identity/protocol/mappings/stream-doc-registry.current.yaml",
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    mapping_path = (repo_root / str(args.contract_mapping)).resolve()
    stream_doc_registry_entry_path = (repo_root / str(args.stream_doc_registry)).resolve()
    stream_doc_registry_path, stream_doc_registry_active_file, stream_doc_registry_alias_error = _resolve_current_yaml_alias(
        repo_root, str(args.stream_doc_registry)
    )

    stale_reasons: list[str] = []
    violations: list[dict[str, Any]] = []
    if stream_doc_registry_alias_error:
        stale_reasons.append(
            f"stream_doc_registry_alias_resolution_failed:{stream_doc_registry_entry_path}:{stream_doc_registry_alias_error}:{stream_doc_registry_active_file}"
        )
    stream_allowed_docs, stream_registry_errors = _load_stream_allowed_docs(stream_doc_registry_path)
    stale_reasons.extend(stream_registry_errors)

    if not mapping_path.exists():
        stale_reasons.append(f"contract_mapping_missing:{mapping_path}")
        mapping_doc: dict[str, Any] = {}
    else:
        try:
            mapping_doc = _load_yaml(mapping_path)
        except Exception as exc:
            stale_reasons.append(f"contract_mapping_parse_failed:{mapping_path}:{exc}")
            mapping_doc = {}

    rows = {
        key: value
        for key, value in mapping_doc.items()
        if isinstance(key, str) and key.startswith("asb16-rq-") and isinstance(value, dict)
    }

    heading_cache: dict[Path, set[str]] = {}
    for requirement_key in sorted(rows.keys()):
        row = rows[requirement_key]

        if not RQ_KEY_RE.match(requirement_key):
            _append_violation(
                violations,
                requirement_key=requirement_key,
                field="requirement_key",
                reason="invalid_requirement_key_format",
            )

        requirement_id = str(row.get("requirement_id", "")).strip()
        if not requirement_id or not RQ_ID_RE.match(requirement_id):
            _append_violation(
                violations,
                requirement_key=requirement_key,
                field="requirement_id",
                reason="invalid_requirement_id_format",
                requirement_id=requirement_id,
            )

        validator_ids = _as_str_list(row.get("validator_ids"))
        if not validator_ids:
            _append_violation(
                violations,
                requirement_key=requirement_key,
                field="validator_ids",
                reason="validator_ids_missing_or_empty",
            )
        else:
            for raw_validator in validator_ids:
                script_path = _parse_script_from_validator_id(raw_validator)
                if not script_path:
                    _append_violation(
                        violations,
                        requirement_key=requirement_key,
                        field="validator_ids",
                        reason="validator_id_parse_failed",
                        validator_id=raw_validator,
                    )
                    continue
                if script_path.startswith("scripts/"):
                    resolved_script = (repo_root / script_path).resolve()
                    if not resolved_script.exists():
                        _append_violation(
                            violations,
                            requirement_key=requirement_key,
                            field="validator_ids",
                            reason="validator_script_missing",
                            script_path=script_path,
                        )

        gate_surfaces = _as_str_list(row.get("gate_surfaces"))
        if not gate_surfaces:
            _append_violation(
                violations,
                requirement_key=requirement_key,
                field="gate_surfaces",
                reason="gate_surfaces_missing_or_empty",
            )
        else:
            unknown_surfaces = sorted(s for s in gate_surfaces if s not in ALLOWED_GATE_SURFACES)
            if unknown_surfaces:
                _append_violation(
                    violations,
                    requirement_key=requirement_key,
                    field="gate_surfaces",
                    reason="gate_surfaces_unknown_tokens",
                    unknown_surfaces=unknown_surfaces,
                )

        for field_name in REFERENCE_FIELDS:
            ref = str(row.get(field_name, "")).strip()
            if not ref:
                _append_violation(
                    violations,
                    requirement_key=requirement_key,
                    field=field_name,
                    reason="reference_missing",
                )
                continue
            rel_path, anchor = _split_ref(ref)
            if not rel_path:
                _append_violation(
                    violations,
                    requirement_key=requirement_key,
                    field=field_name,
                    reason="reference_path_missing",
                    reference=ref,
                )
                continue

            if field_name in STREAM_ANCHOR_FIELDS:
                required_prefix = STREAM_FIELD_PREFIX.get(field_name, "")
                if required_prefix and not rel_path.startswith(required_prefix):
                    _append_violation(
                        violations,
                        requirement_key=requirement_key,
                        field=field_name,
                        reason="reference_path_prefix_mismatch",
                        reference=ref,
                        required_prefix=required_prefix,
                        reference_path=rel_path,
                    )
                if not anchor:
                    _append_violation(
                        violations,
                        requirement_key=requirement_key,
                        field=field_name,
                        reason="reference_anchor_required_for_stream_field",
                        reference=ref,
                        reference_path=rel_path,
                    )
                if stream_allowed_docs and rel_path not in stream_allowed_docs:
                    _append_violation(
                        violations,
                        requirement_key=requirement_key,
                        field=field_name,
                        reason="reference_doc_not_registered_in_stream_registry",
                        reference=ref,
                        reference_path=rel_path,
                        stream_doc_registry=str(stream_doc_registry_path),
                    )

            resolved = (repo_root / rel_path).resolve()
            if not resolved.exists():
                _append_violation(
                    violations,
                    requirement_key=requirement_key,
                    field=field_name,
                    reason="reference_file_missing",
                    reference=ref,
                    reference_path=rel_path,
                )
                continue

            if anchor and resolved.suffix.lower() == ".md":
                if resolved not in heading_cache:
                    heading_cache[resolved] = _markdown_heading_slugs(resolved)
                if anchor not in heading_cache[resolved]:
                    _append_violation(
                        violations,
                        requirement_key=requirement_key,
                        field=field_name,
                        reason="reference_anchor_missing",
                        reference=ref,
                        anchor=anchor,
                        reference_path=rel_path,
                    )

    status = STATUS_PASS_REQUIRED
    error_code = ""
    if stale_reasons or violations:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_POLICY

    payload = {
        "contract_binding_reference_integrity_status": status,
        "error_code": error_code,
        "contract_mapping": str(mapping_path),
        "stream_doc_registry_entry": str(stream_doc_registry_entry_path),
        "stream_doc_registry": str(stream_doc_registry_path),
        "stream_doc_registry_active_file": stream_doc_registry_active_file,
        "stream_doc_registry_alias_error": stream_doc_registry_alias_error,
        "stream_doc_registry_parse_ok": len(stream_registry_errors) == 0,
        "stream_allowed_doc_count": len(stream_allowed_docs),
        "requirement_row_count": len(rows),
        "reference_fields": list(REFERENCE_FIELDS),
        "stream_anchor_fields": list(STREAM_ANCHOR_FIELDS),
        "allowed_gate_surfaces": sorted(ALLOWED_GATE_SURFACES),
        "violation_count": len(violations),
        "violations": violations,
        "stale_reasons": stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[CONTRACT-BINDING-REF] status={status} "
            f"rows={len(rows)} violations={len(violations)} stale={len(stale_reasons)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
