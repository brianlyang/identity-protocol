#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from repo_root_resolution_common import resolve_repo_root
from typing import Any

import yaml

from contract_binding_mapping_common import (
    collect_requirement_rows,
    is_requirement_id,
    is_requirement_key,
    is_stream_version,
)
from registry_alias_control_plane_common import STREAM_DOC_REGISTRY_CURRENT, resolve_current_yaml_alias

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
WRAPPER_OPTIONAL_METADATA = {"wrapper_only_optional", "wrapper_compatibility_optional"}
WRAPPER_CONTEXT_RE = re.compile(
    r"\b(wrapper|alias|compatibility|compatibility-only|optional|delegate|delegated|delegating)\b",
    flags=re.IGNORECASE,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


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


def _parse_validator_entry(raw: str) -> tuple[str, str]:
    token = str(raw or "").strip()
    if not token:
        return "", ""
    if "::" not in token:
        return token, ""
    script_part, metadata = token.split("::", 1)
    return script_part.strip(), metadata.strip()


def _parse_script_from_validator_id(raw: str) -> str:
    return _parse_validator_entry(raw)[0]


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
            stream_version = str(row.get("stream_version", "")).strip()
            if not stream_version:
                errors.append("stream_doc_registry_stream_version_missing")
            elif not is_stream_version(stream_version):
                errors.append(f"stream_doc_registry_stream_version_invalid:{stream_version}")
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


def _derive_versioned_alias(script_path: str, *, repo_root: Path) -> str:
    token = str(script_path or "").strip()
    if not token.startswith("scripts/"):
        return ""
    alias_candidates = [
        token.replace("scripts/validate_", "scripts/validate_v16_", 1),
        token.replace("scripts/normalize_", "scripts/normalize_v16_", 1),
    ]
    for candidate in alias_candidates:
        if candidate == token:
            continue
        if (repo_root / candidate).resolve().exists():
            return candidate
    return ""


def _derive_canonical_from_versioned(script_path: str, *, repo_root: Path) -> str:
    token = str(script_path or "").strip()
    if not token.startswith("scripts/"):
        return ""
    candidates = [
        token.replace("scripts/validate_v16_", "scripts/validate_", 1),
        token.replace("scripts/normalize_v16_", "scripts/normalize_", 1),
    ]
    for candidate in candidates:
        if candidate == token:
            continue
        if (repo_root / candidate).resolve().exists():
            return candidate
    return ""


def _collect_doc_wrapper_alias_pairs(
    *,
    repo_root: Path,
    validator_ids: list[str],
) -> list[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    canonical_scripts: list[str] = []
    for raw_validator in validator_ids:
        script_path, metadata = _parse_validator_entry(raw_validator)
        if not script_path:
            continue
        if metadata in WRAPPER_OPTIONAL_METADATA:
            canonical = _derive_canonical_from_versioned(script_path, repo_root=repo_root)
            if canonical:
                pairs.add((script_path, canonical))
            continue
        canonical_scripts.append(script_path)
    for canonical in canonical_scripts:
        alias = _derive_versioned_alias(canonical, repo_root=repo_root)
        if alias:
            pairs.add((alias, canonical))
    return sorted(pairs)


def _scan_doc_for_legacy_wrapper_usage(
    *,
    doc_path: Path,
    alias_pairs: list[tuple[str, str]],
    requirement_key: str,
    field_name: str,
    violations: list[dict[str, Any]],
) -> None:
    if not alias_pairs:
        return
    for line_no, raw_line in enumerate(doc_path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        for legacy_script, canonical_script in alias_pairs:
            if legacy_script not in line:
                continue
            if WRAPPER_CONTEXT_RE.search(line):
                continue
            _append_violation(
                violations,
                requirement_key=requirement_key,
                field=field_name,
                reason="doc_executable_role_mismatch_legacy_wrapper_used_as_canonical",
                reference_path=str(doc_path),
                line=line_no,
                legacy_script=legacy_script,
                canonical_script=canonical_script,
                snippet=line,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate contract-binding reference integrity across docs/scripts.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--contract-mapping", default="identity/protocol/mappings/contract-binding.current.yaml")
    parser.add_argument(
        "--stream-doc-registry",
        default=STREAM_DOC_REGISTRY_CURRENT,
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    mapping_entry_path = (repo_root / str(args.contract_mapping)).resolve()
    mapping_path, mapping_active_file, mapping_alias_error = resolve_current_yaml_alias(
        repo_root, str(args.contract_mapping)
    )
    stream_doc_registry_entry_path = (repo_root / str(args.stream_doc_registry)).resolve()
    stream_doc_registry_path, stream_doc_registry_active_file, stream_doc_registry_alias_error = resolve_current_yaml_alias(
        repo_root, str(args.stream_doc_registry)
    )

    stale_reasons: list[str] = []
    violations: list[dict[str, Any]] = []
    if mapping_alias_error:
        stale_reasons.append(
            f"contract_mapping_alias_resolution_failed:{mapping_entry_path}:{mapping_alias_error}:{mapping_active_file}"
        )
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

    rows = collect_requirement_rows(mapping_doc)

    heading_cache: dict[Path, set[str]] = {}
    for requirement_key in sorted(rows.keys()):
        row = rows[requirement_key]

        if not is_requirement_key(requirement_key):
            _append_violation(
                violations,
                requirement_key=requirement_key,
                field="requirement_key",
                reason="invalid_requirement_key_format",
            )

        requirement_id = str(row.get("requirement_id", "")).strip()
        if not requirement_id or not is_requirement_id(requirement_id):
            _append_violation(
                violations,
                requirement_key=requirement_key,
                field="requirement_id",
                reason="invalid_requirement_id_format",
                requirement_id=requirement_id,
            )

        validator_ids = _as_str_list(row.get("validator_ids"))
        doc_wrapper_alias_pairs = _collect_doc_wrapper_alias_pairs(
            repo_root=repo_root,
            validator_ids=validator_ids,
        )
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
                elif field_name in STREAM_ANCHOR_FIELDS:
                    _scan_doc_for_legacy_wrapper_usage(
                        doc_path=resolved,
                        alias_pairs=doc_wrapper_alias_pairs,
                        requirement_key=requirement_key,
                        field_name=field_name,
                        violations=violations,
                    )

    status = STATUS_PASS_REQUIRED
    error_code = ""
    if stale_reasons or violations:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_POLICY

    payload = {
        "contract_binding_reference_integrity_status": status,
        "error_code": error_code,
        "contract_mapping_entry": str(mapping_entry_path),
        "contract_mapping": str(mapping_path),
        "contract_mapping_active_file": mapping_active_file,
        "contract_mapping_alias_error": mapping_alias_error,
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
