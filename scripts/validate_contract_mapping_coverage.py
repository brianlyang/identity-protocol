#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

from contract_binding_mapping_common import is_stream_version
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MAPPING_FILE_MISSING = "IP-MAP-001"
ERR_GOVERNANCE_PARSE = "IP-MAP-002"
ERR_COVERAGE_BELOW_TARGET = "IP-MAP-003"
ERR_ORPHAN_ROWS = "IP-MAP-004"
ERR_MAPPING_DUPLICATE_REQUIREMENT_ID = "IP-MAP-005"

REQUIREMENT_ID_TOKEN_RE = re.compile(r"\b([A-Z0-9][A-Z0-9_-]*-RQ-\d{3})\b", re.IGNORECASE)
PRIORITY_TOKEN_RE = re.compile(r"^P\d+$", re.IGNORECASE)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "contract_mapping_projection_contract_v1",
        "contract_mapping_projection_contract",
        "rq_026_kernel_contract_mapping_projection_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _extract_requirement_rows_from_text(doc_text: str) -> tuple[dict[str, str], list[str]]:
    priorities: dict[str, str] = {}
    ordered: list[str] = []
    seen: set[str] = set()

    for raw_line in doc_text.splitlines():
        line = str(raw_line or "").strip()
        if not line.startswith("|"):
            continue
        cols = [part.strip() for part in line.strip().strip("|").split("|")]
        if not cols:
            continue
        rq_match = REQUIREMENT_ID_TOKEN_RE.search(cols[0])
        if not rq_match:
            continue
        requirement_id = rq_match.group(1).upper()
        if requirement_id not in seen:
            ordered.append(requirement_id)
            seen.add(requirement_id)

        priority = ""
        for col in cols[1:]:
            token = str(col or "").strip().upper()
            if PRIORITY_TOKEN_RE.fullmatch(token):
                priority = token
                break
        if priority:
            priorities[requirement_id] = priority

    for match in REQUIREMENT_ID_TOKEN_RE.finditer(doc_text):
        requirement_id = match.group(1).upper()
        if requirement_id not in seen:
            ordered.append(requirement_id)
            seen.add(requirement_id)

    return priorities, ordered


def _requirement_namespace(requirement_id: str) -> str:
    token = str(requirement_id or "").strip().upper()
    if "-RQ-" not in token:
        return ""
    return token.split("-RQ-", 1)[0].strip()


def _load_mapping_rows(mapping_path: Path) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    raw = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return {}, [], []
    rows: dict[str, dict[str, Any]] = {}
    orphan_keys: list[str] = []
    duplicate_requirement_ids: list[str] = []
    for key, value in raw.items():
        if key == "_meta":
            continue
        if not isinstance(value, dict):
            continue
        rq = str(value.get("requirement_id", "")).strip().upper()
        if not rq:
            orphan_keys.append(str(key))
            continue
        if rq in rows:
            duplicate_requirement_ids.append(rq)
        rows[rq] = value
    return rows, sorted(orphan_keys), sorted(set(duplicate_requirement_ids))


def _resolve_current_yaml_alias(configured_path: Path) -> tuple[Path, str, str]:
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    current_doc = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    if not isinstance(current_doc, dict):
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    repo_root = Path(__file__).resolve().parents[1]
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _resolve_governance_docs(
    *,
    repo_root: Path,
    explicit_governance_doc: str,
    stream_doc_registry_entry: str,
) -> tuple[list[Path], Path, str, str, str, list[str]]:
    errors: list[str] = []

    explicit_path = str(explicit_governance_doc or "").strip()
    if explicit_path:
        doc_path = Path(explicit_path).expanduser().resolve()
        if not doc_path.exists() or not doc_path.is_file():
            return [], doc_path, "", "", "", [f"governance_doc_missing:{doc_path}"]
        return [doc_path], doc_path, "", "", "", []

    registry_entry_path = Path(stream_doc_registry_entry).expanduser().resolve()
    registry_path, registry_active_file, registry_alias_error = _resolve_current_yaml_alias(registry_entry_path)
    if registry_alias_error:
        return [], registry_entry_path, "", registry_active_file, registry_alias_error, [
            f"stream_doc_registry_alias_error:{registry_alias_error}:{registry_active_file}"
        ]
    if not registry_path.exists() or not registry_path.is_file():
        return [], registry_path, "", registry_active_file, "", [f"stream_doc_registry_missing:{registry_path}"]

    doc = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        return [], registry_path, str(registry_path), registry_active_file, "", [
            f"stream_doc_registry_invalid_root:{registry_path}"
        ]

    rows = doc.get("stream_docs")
    if not isinstance(rows, list) or not rows:
        return [], registry_path, str(registry_path), registry_active_file, "", [
            "stream_doc_registry_stream_docs_invalid"
        ]

    docs: list[Path] = []
    seen_docs: set[Path] = set()
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"stream_doc_registry_row_invalid:{idx}")
            continue
        stream_version = str(row.get("stream_version", "")).strip()
        if not stream_version:
            errors.append(f"stream_doc_registry_stream_version_missing:{idx}")
        elif not is_stream_version(stream_version):
            errors.append(f"stream_doc_registry_stream_version_invalid:{stream_version}")
        for field in ("governance_doc", "review_doc"):
            rel_doc = str(row.get(field, "")).strip()
            if not rel_doc:
                errors.append(f"stream_doc_registry_missing_{field}:{stream_version or f'row_{idx}'}")
                continue
            abs_doc = (repo_root / rel_doc).resolve()
            if not abs_doc.exists() or not abs_doc.is_file():
                errors.append(f"stream_doc_registry_doc_missing:{rel_doc}")
                continue
            if abs_doc in seen_docs:
                continue
            docs.append(abs_doc)
            seen_docs.add(abs_doc)

    static_rows = doc.get("mandatory_static_docs")
    if not isinstance(static_rows, list) or not static_rows:
        errors.append("stream_doc_registry_mandatory_static_docs_invalid")
    else:
        for rel_doc in static_rows:
            rel_doc_token = str(rel_doc or "").strip()
            if not rel_doc_token:
                continue
            if not (
                rel_doc_token.startswith("docs/governance/")
                or rel_doc_token.startswith("docs/review/")
            ):
                continue
            abs_doc = (repo_root / rel_doc_token).resolve()
            if not abs_doc.exists() or not abs_doc.is_file():
                errors.append(f"stream_doc_registry_doc_missing:{rel_doc_token}")
                continue
            if abs_doc in seen_docs:
                continue
            docs.append(abs_doc)
            seen_docs.add(abs_doc)

    return docs, registry_entry_path, str(registry_path), registry_active_file, registry_alias_error, errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate kernel contract mapping coverage contract (RQ-026).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--governance-doc",
        default="",
        help="optional explicit governance doc override; when empty resolves from stream-doc-registry.current.yaml",
    )
    ap.add_argument(
        "--stream-doc-registry",
        default="identity/protocol/mappings/stream-doc-registry.current.yaml",
        help="stream registry current alias used when --governance-doc is omitted",
    )
    ap.add_argument("--mapping-file", default="identity/protocol/mappings/contract-binding.current.yaml")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required = contract_required(contract)
    if args.force_required:
        required = True

    mapping_entry_path = Path(args.mapping_file).expanduser().resolve()
    mapping_path, mapping_active_file, mapping_alias_error = _resolve_current_yaml_alias(mapping_entry_path)

    repo_root = Path(__file__).resolve().parents[1]
    docs_to_scan, stream_registry_entry_path, stream_registry_path, stream_registry_active_file, stream_registry_alias_error, stream_registry_errors = _resolve_governance_docs(
        repo_root=repo_root,
        explicit_governance_doc=str(args.governance_doc or ""),
        stream_doc_registry_entry=str(args.stream_doc_registry or ""),
    )

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in {"update", "readiness", "e2e", "ci", "validate"}),
        "producer_readiness": False,
        "requiredization_current_round_linked": bool(required),
        "contract_mapping_coverage_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "governance_doc_path": str(Path(args.governance_doc).expanduser().resolve()) if str(args.governance_doc).strip() else "",
        "stream_doc_registry_entry_path": str(stream_registry_entry_path),
        "stream_doc_registry_path": str(stream_registry_path),
        "stream_doc_registry_active_file": stream_registry_active_file,
        "stream_doc_registry_alias_error": stream_registry_alias_error,
        "scanned_governance_docs": [str(p) for p in docs_to_scan],
        "mapping_file_entry_path": str(mapping_entry_path),
        "mapping_file_path": str(mapping_path),
        "mapping_file_active_file": mapping_active_file,
        "mapping_file_alias_error": mapping_alias_error,
        "total_requirements": 0,
        "p0_total": 0,
        "mapped_total": 0,
        "p0_mapped": 0,
        "coverage_rate": 0.0,
        "p0_coverage_rate": 0.0,
        "priority_fallback_all_required": False,
        "unmapped_requirements": [],
        "unmapped_p0_requirements": [],
        "orphan_count": 0,
        "orphan_rows": [],
        "duplicate_requirement_ids": [],
        "stale_reasons": [],
        "evidence_ref": str(mapping_path),
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if mapping_alias_error:
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MAPPING_FILE_MISSING
        payload["stale_reasons"] = [f"mapping_file_alias_error:{mapping_alias_error}:{mapping_active_file}"]
        _emit(payload, json_only=args.json_only)
        return 1

    if stream_registry_errors:
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_GOVERNANCE_PARSE
        payload["stale_reasons"] = stream_registry_errors
        _emit(payload, json_only=args.json_only)
        return 1

    if not mapping_path.exists() or not mapping_path.is_file():
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MAPPING_FILE_MISSING
        payload["stale_reasons"] = [f"mapping_file_missing:{mapping_path}"]
        _emit(payload, json_only=args.json_only)
        return 1

    mapping_rows, orphan_rows, duplicate_requirement_ids = _load_mapping_rows(mapping_path)
    mapped_ids = set(mapping_rows.keys())
    mapped_namespaces = sorted(
        {
            ns
            for ns in (_requirement_namespace(requirement_id) for requirement_id in mapped_ids)
            if ns
        }
    )

    priorities: dict[str, str] = {}
    ordered_requirements: list[str] = []
    seen_requirement_ids: set[str] = set()
    for doc_path in docs_to_scan:
        text = doc_path.read_text(encoding="utf-8", errors="ignore")
        doc_priorities, doc_ordered = _extract_requirement_rows_from_text(text)
        for requirement_id, priority in doc_priorities.items():
            rid = requirement_id.upper()
            if mapped_namespaces and _requirement_namespace(rid) not in mapped_namespaces:
                continue
            priorities[rid] = priority.upper()
        for requirement_id in doc_ordered:
            rid = requirement_id.upper()
            if mapped_namespaces and _requirement_namespace(rid) not in mapped_namespaces:
                continue
            if rid in seen_requirement_ids:
                continue
            ordered_requirements.append(rid)
            seen_requirement_ids.add(rid)

    if not ordered_requirements:
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_GOVERNANCE_PARSE
        payload["stale_reasons"] = ["governance_requirement_table_parse_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    total_requirements = len(ordered_requirements)
    p0_ids = [rq for rq in ordered_requirements if priorities.get(rq, "") == "P0"]
    priority_fallback_all_required = False
    if not p0_ids and ordered_requirements:
        p0_ids = list(ordered_requirements)
        priority_fallback_all_required = True

    p0_total = len(p0_ids)
    mapped_total = len([rq for rq in ordered_requirements if rq in mapped_ids])
    p0_mapped = len([rq for rq in p0_ids if rq in mapped_ids])
    unmapped = [rq for rq in ordered_requirements if rq not in mapped_ids]
    unmapped_p0 = [rq for rq in p0_ids if rq not in mapped_ids]

    coverage_rate = round((mapped_total / total_requirements) * 100.0, 2) if total_requirements else 0.0
    p0_coverage_rate = round((p0_mapped / p0_total) * 100.0, 2) if p0_total else 0.0

    payload["producer_readiness"] = True
    payload["total_requirements"] = total_requirements
    payload["p0_total"] = p0_total
    payload["mapped_total"] = mapped_total
    payload["p0_mapped"] = p0_mapped
    payload["coverage_rate"] = coverage_rate
    payload["p0_coverage_rate"] = p0_coverage_rate
    payload["priority_fallback_all_required"] = priority_fallback_all_required
    payload["unmapped_requirements"] = unmapped
    payload["unmapped_p0_requirements"] = unmapped_p0
    payload["orphan_count"] = len(orphan_rows)
    payload["orphan_rows"] = orphan_rows
    payload["duplicate_requirement_ids"] = duplicate_requirement_ids

    if orphan_rows:
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ORPHAN_ROWS
        payload["stale_reasons"] = ["mapping_orphan_rows_detected"]
        _emit(payload, json_only=args.json_only)
        return 1

    if duplicate_requirement_ids:
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MAPPING_DUPLICATE_REQUIREMENT_ID
        payload["stale_reasons"] = ["mapping_duplicate_requirement_id_detected"]
        _emit(payload, json_only=args.json_only)
        return 1

    if p0_coverage_rate < 100.0:
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_COVERAGE_BELOW_TARGET
        payload["stale_reasons"] = ["p0_mapping_coverage_below_100"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["contract_mapping_coverage_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
