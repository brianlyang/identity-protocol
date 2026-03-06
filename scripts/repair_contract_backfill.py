#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from create_identity_pack import _ensure_intake_p1_contracts
from tool_vendor_governance_common import load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


REQUIRED_INTAKE_KEYS = (
    "multi_track_cross_verification_contract_v1",
    "intake_evidence_quorum_contract_v1",
    "fallback_taxonomy_normalization_contract_v1",
    "dedup_monotonic_winner_contract_v1",
    "cross_workflow_evidence_schema_contract_v1",
    "skill_path_integrity_contract_v1",
    "route_workflow_version_pinning_contract_v1",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _legacy_path_drift_fields(task: dict[str, Any], identity_id: str) -> list[str]:
    legacy_prefix = f"identity/runtime/local/{identity_id}/reports/"
    out: list[str] = []
    mapping = {
        "dedup_monotonic_winner_contract_v1.claims_path_pattern": ("dedup_monotonic_winner_contract_v1", "claims_path_pattern"),
        "cross_workflow_evidence_schema_contract_v1.evidence_path_pattern": ("cross_workflow_evidence_schema_contract_v1", "evidence_path_pattern"),
        "route_workflow_version_pinning_contract_v1.proof_receipt_path_pattern": ("route_workflow_version_pinning_contract_v1", "proof_receipt_path_pattern"),
    }
    for field_ref, (contract_key, path_key) in mapping.items():
        node = task.get(contract_key)
        if not isinstance(node, dict):
            continue
        value = str(node.get(path_key, "")).strip()
        if value.startswith(legacy_prefix):
            out.append(field_ref)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill intake contract set into CURRENT_TASK.json.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--apply", action="store_true", help="persist updates to CURRENT_TASK.json")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog, args.identity_id)
        task_doc = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    before = json.loads(json.dumps(task_doc))
    missing_before = [k for k in REQUIRED_INTAKE_KEYS if not isinstance(task_doc.get(k), dict)]
    legacy_drift_before = _legacy_path_drift_fields(task_doc, args.identity_id)

    updated = _ensure_intake_p1_contracts(task_doc, args.identity_id)
    missing_after = [k for k in REQUIRED_INTAKE_KEYS if not isinstance(updated.get(k), dict)]
    legacy_drift_after = _legacy_path_drift_fields(updated, args.identity_id)

    changed = before != updated
    applied = False
    if changed and args.apply:
        task_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        applied = True

    if missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-CBKF-001"
        stale_reasons = ["required_contract_keys_missing_after_backfill"]
    elif legacy_drift_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-CBKF-002"
        stale_reasons = ["legacy_contract_path_drift_after_backfill"]
    elif changed:
        status = STATUS_PASS_REQUIRED if applied else STATUS_SKIPPED_NOT_REQUIRED
        error_code = ""
        stale_reasons = [] if applied else ["dry_run_only"]
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""
        stale_reasons = ["already_backfilled"] if not applied else []

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog),
        "pack_path": str(pack_path),
        "task_path": str(task_path),
        "contract_backfill_status": status,
        "error_code": error_code,
        "changed": changed,
        "applied": applied,
        "missing_contract_keys_before": missing_before,
        "missing_contract_keys_after": missing_after,
        "legacy_path_drift_fields_before": legacy_drift_before,
        "legacy_path_drift_fields_after": legacy_drift_after,
        "required_contract_keys": list(REQUIRED_INTAKE_KEYS),
        "stale_reasons": stale_reasons,
        "evidence_ref": str(task_path),
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED} else 1


if __name__ == "__main__":
    raise SystemExit(main())

