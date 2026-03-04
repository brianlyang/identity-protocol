#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import (
    contract_required,
    load_json,
    nonempty,
    resolve_pack_and_task,
    resolve_report_path,
)


REQ_CONTRACT_KEYS = (
    "required",
    "report_path_pattern",
    "required_report_fields",
    "enforcement_validator",
)

DEFAULT_REQUIRED_FIELDS = (
    "vendor_name",
    "vendor_surface_name",
    "official_reference_url",
    "machine_readable_contract_ref",
    "contract_kind",
    "auth_discovery_ref",
    "versioning_policy_ref",
    "rate_limit_policy_ref",
    "capability_probe_command_ref",
    "attach_readiness_decision",
    "fallback_vendor_or_route_ref",
)


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    c = task.get("vendor_api_discovery_contract")
    return c if isinstance(c, dict) else {}


def _extract_candidates(report: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("vendor_api_candidates", "candidate_matrix", "candidates"):
        rows = report.get(key)
        if isinstance(rows, list):
            return [x for x in rows if isinstance(x, dict)]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate vendor/API discovery closure contract.")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    try:
        pack_path, task_path = resolve_pack_and_task(Path(args.catalog).expanduser().resolve(), args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    if not contract_required(contract):
        print(f"[OK] vendor/api discovery contract not required for identity={args.identity_id}; skipped")
        return 0

    missing_contract = [k for k in REQ_CONTRACT_KEYS if k not in contract]
    if missing_contract:
        print(f"[FAIL] IP-VAP-001 vendor/api discovery contract missing fields: {missing_contract}")
        return 1

    report_path = resolve_report_path(
        report=args.report,
        pattern=str(contract.get("report_path_pattern", "")),
        pack_root=pack_path,
    )
    if report_path is None:
        print("[FAIL] IP-VAP-002 vendor/api discovery report not found")
        return 1

    try:
        report = load_json(report_path)
    except Exception as exc:
        print(f"[FAIL] IP-VAP-002 invalid report json: {report_path} ({exc})")
        return 1

    required_fields = contract.get("required_report_fields")
    if not isinstance(required_fields, list) or not required_fields:
        required_fields = list(DEFAULT_REQUIRED_FIELDS)

    missing_report = [k for k in required_fields if k not in report]
    if missing_report:
        print(f"[FAIL] IP-VAP-003 discovery report missing required fields: {missing_report}")
        return 1

    readiness = str(report.get("attach_readiness_decision", "")).strip().lower()
    if readiness not in {"ready", "defer", "blocked"}:
        print(f"[FAIL] IP-VAP-004 attach_readiness_decision invalid: {readiness}")
        return 1

    candidates = _extract_candidates(report)
    if candidates:
        selected_rows = [x for x in candidates if str(x.get("decision", "")).strip().lower() == "selected"]
        if readiness == "ready" and not selected_rows:
            print("[FAIL] IP-VAP-005 readiness=ready requires at least one selected candidate")
            return 1
        for idx, row in enumerate(selected_rows, start=1):
            miss = [
                key
                for key in ("source_url", "source_kind", "trust_tier", "provenance_or_signature_ref")
                if not nonempty(row.get(key))
            ]
            if miss:
                print(f"[FAIL] IP-VAP-006 selected candidate[{idx}] missing trust/provenance fields: {miss}")
                return 1
            trust_tier = str(row.get("trust_tier", "")).strip().upper()
            if trust_tier == "T2" and not nonempty(report.get("approval_receipt_ref")):
                print("[FAIL] IP-VAP-007 T2 discovery source requires approval_receipt_ref")
                return 1

    print(f"[OK] vendor/api discovery closure validated: {report_path}")
    print("validate_identity_vendor_api_discovery PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

