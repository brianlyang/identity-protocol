#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQ_KEYS = [
    "required",
    "preserve_existing_default",
    "on_conflict",
    "idempotent_reinstall_allowed",
    "same_signature_action",
    "allow_replace_only_with_backup",
    "rollback_reference_required",
    "install_report_required",
    "dry_run_required",
    "install_report_path_pattern",
]


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p
    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate install safety contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate install safety for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    task = _load_json(task_path)
    gates = task.get("gates") or {}
    if gates.get("install_safety_gate") != "required":
        print("[FAIL] gates.install_safety_gate must be required")
        return 1
    print("[OK] gates.install_safety_gate=required")

    c = task.get("install_safety_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing install_safety_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        print(f"[FAIL] install_safety_contract missing fields: {missing}")
        return 1

    rc = 0
    if c.get("required") is not True:
        print("[FAIL] install_safety_contract.required must be true")
        rc = 1
    if c.get("preserve_existing_default") is not True:
        print("[FAIL] install_safety_contract.preserve_existing_default must be true")
        rc = 1
    if str(c.get("on_conflict", "")).strip() != "abort_and_explain":
        print("[FAIL] install_safety_contract.on_conflict must be 'abort_and_explain'")
        rc = 1
    if c.get("idempotent_reinstall_allowed") is not True:
        print("[FAIL] install_safety_contract.idempotent_reinstall_allowed must be true")
        rc = 1
    if str(c.get("same_signature_action", "")).strip() != "no_op_with_report":
        print("[FAIL] install_safety_contract.same_signature_action must be 'no_op_with_report'")
        rc = 1
    if c.get("allow_replace_only_with_backup") is not True:
        print("[FAIL] install_safety_contract.allow_replace_only_with_backup must be true")
        rc = 1
    if c.get("rollback_reference_required") is not True:
        print("[FAIL] install_safety_contract.rollback_reference_required must be true")
        rc = 1
    if c.get("install_report_required") is not True:
        print("[FAIL] install_safety_contract.install_report_required must be true")
        rc = 1
    if c.get("dry_run_required") is not True:
        print("[FAIL] install_safety_contract.dry_run_required must be true")
        rc = 1

    pattern = str(c.get("install_report_path_pattern") or "").strip()
    if not pattern:
        print("[FAIL] install_safety_contract.install_report_path_pattern missing")
        return 1

    report_path = Path(args.report) if args.report else None
    if not report_path or not report_path.exists():
        reports = sorted(Path(".").glob(pattern))
        if reports:
            report_path = reports[-1]
    if not report_path or not report_path.exists():
        print(f"[FAIL] install report not found by pattern: {pattern}")
        return 1

    report = _load_json(report_path)
    required_report_fields = [
        "report_id",
        "identity_id",
        "generated_at",
        "operation",
        "conflict_type",
        "action",
        "preserved_paths",
    ]
    miss_report = [k for k in required_report_fields if k not in report]
    if miss_report:
        print(f"[FAIL] install report missing fields: {miss_report}")
        rc = 1
    if str(report.get("identity_id", "")).strip() != args.identity_id:
        print("[FAIL] install report identity_id mismatch")
        rc = 1

    conflict_type = str(report.get("conflict_type", "")).strip()
    action = str(report.get("action", "")).strip()
    if conflict_type == "same_signature":
        if action != "no_op_with_report":
            print("[FAIL] same_signature conflict must use action=no_op_with_report")
            rc = 1
    elif conflict_type == "destructive_replace":
        if not report.get("backup_ref") or not report.get("rollback_ref"):
            print("[FAIL] destructive_replace requires backup_ref and rollback_ref")
            rc = 1
        if action != "guarded_apply":
            print("[FAIL] destructive_replace requires action=guarded_apply with backup/rollback")
            rc = 1
    elif conflict_type == "compatible_upgrade":
        if action != "abort_and_explain":
            print("[FAIL] compatible_upgrade must use action=abort_and_explain per install_safety_contract")
            rc = 1
    elif conflict_type == "fresh_install":
        if action != "guarded_apply":
            print("[FAIL] fresh_install must use action=guarded_apply")
            rc = 1
    else:
        print(f"[FAIL] conflict_type not supported: {conflict_type}")
        rc = 1

    if rc:
        return 1
    print(f"[OK] install report validated: {report_path}")
    print("Install safety contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
