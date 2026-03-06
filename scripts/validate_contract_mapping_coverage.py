#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MAPPING_FILE_MISSING = "IP-MAP-001"
ERR_GOVERNANCE_PARSE = "IP-MAP-002"
ERR_COVERAGE_BELOW_TARGET = "IP-MAP-003"
ERR_ORPHAN_ROWS = "IP-MAP-004"

RQ_ROW_RE = re.compile(r"^\|\s*(ASB16-RQ-\d{3})\s*\|")


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


def _extract_governance_rows(governance_text: str) -> tuple[dict[str, str], list[str]]:
    section_start = governance_text.find("## 5) Requirement Mapping")
    section_end = governance_text.find("## 6)", section_start + 1)
    if section_start < 0:
        return {}, []
    if section_end < 0:
        section = governance_text[section_start:]
    else:
        section = governance_text[section_start:section_end]
    priorities: dict[str, str] = {}
    ordered: list[str] = []
    for line in section.splitlines():
        if not line.strip().startswith("| ASB16-RQ-"):
            continue
        cols = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(cols) < 4:
            continue
        rq = cols[0]
        priority = cols[3].upper()
        priorities[rq] = priority
        ordered.append(rq)
    return priorities, ordered


def _load_mapping_rows(mapping_path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    raw = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return {}, []
    rows: dict[str, dict[str, Any]] = {}
    orphan_keys: list[str] = []
    for key, value in raw.items():
        if key == "_meta":
            continue
        if not isinstance(value, dict):
            continue
        rq = str(value.get("requirement_id", "")).strip()
        if not rq:
            orphan_keys.append(str(key))
            continue
        rows[rq] = value
    return rows, sorted(orphan_keys)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate kernel contract mapping coverage contract (RQ-026).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--governance-doc", default="docs/governance/identity-actor-session-binding-governance-v1.6.0.md")
    ap.add_argument("--mapping-file", default="identity/protocol/mappings/contract-binding.v1.6.yaml")
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
        "governance_doc_path": str(Path(args.governance_doc).expanduser().resolve()),
        "mapping_file_path": str(Path(args.mapping_file).expanduser().resolve()),
        "total_requirements": 0,
        "p0_total": 0,
        "mapped_total": 0,
        "p0_mapped": 0,
        "coverage_rate": 0.0,
        "p0_coverage_rate": 0.0,
        "unmapped_requirements": [],
        "unmapped_p0_requirements": [],
        "orphan_count": 0,
        "orphan_rows": [],
        "stale_reasons": [],
        "evidence_ref": str(Path(args.mapping_file).expanduser().resolve()),
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    governance_path = Path(args.governance_doc).expanduser().resolve()
    mapping_path = Path(args.mapping_file).expanduser().resolve()
    if not governance_path.exists() or not mapping_path.exists():
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MAPPING_FILE_MISSING
        reasons = []
        if not governance_path.exists():
            reasons.append("governance_doc_missing")
        if not mapping_path.exists():
            reasons.append("mapping_file_missing")
        payload["stale_reasons"] = reasons
        _emit(payload, json_only=args.json_only)
        return 1

    governance_text = governance_path.read_text(encoding="utf-8", errors="ignore")
    priorities, ordered = _extract_governance_rows(governance_text)
    if not ordered:
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_GOVERNANCE_PARSE
        payload["stale_reasons"] = ["governance_requirement_table_parse_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    mapping_rows, orphan_rows = _load_mapping_rows(mapping_path)
    mapped_ids = set(mapping_rows.keys())
    total_requirements = len(ordered)
    p0_ids = [rq for rq in ordered if priorities.get(rq, "") == "P0"]
    p0_total = len(p0_ids)
    mapped_total = len([rq for rq in ordered if rq in mapped_ids])
    p0_mapped = len([rq for rq in p0_ids if rq in mapped_ids])
    unmapped = [rq for rq in ordered if rq not in mapped_ids]
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
    payload["unmapped_requirements"] = unmapped
    payload["unmapped_p0_requirements"] = unmapped_p0
    payload["orphan_count"] = len(orphan_rows)
    payload["orphan_rows"] = orphan_rows

    if orphan_rows:
        payload["contract_mapping_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ORPHAN_ROWS
        payload["stale_reasons"] = ["mapping_orphan_rows_detected"]
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
