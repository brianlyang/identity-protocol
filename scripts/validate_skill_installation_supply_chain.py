#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CONTRACT_MISSING = "IP-SSUP-001"
ERR_DRIVER_MISSING = "IP-SSUP-002"
ERR_SKILL_PATH_INTEGRITY = "IP-SSUP-003"

STRICT_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "scan",
    "three-plane",
    "inspection",
    "mutation",
}

CONTRACT_KEYS = (
    "skill_installation_supply_chain_contract_v1",
    "skill_installation_supply_chain_contract",
    "rq_039_skill_installation_supply_chain_contract_v1",
)

DEFAULT_DEPENDENT_CONTRACT_KEYS = (
    "tool_installation_contract",
    "vendor_api_discovery_contract",
    "vendor_api_solution_contract",
    "skill_path_integrity_contract_v1",
)
DEFAULT_DRIVER_VALIDATORS = (
    "scripts/validate_identity_tool_installation.py",
    "scripts/validate_identity_vendor_api_discovery.py",
    "scripts/validate_identity_vendor_api_solution.py",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog_doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    rows = catalog_doc.get("identities")
    if not isinstance(rows, list):
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("id", "")).strip() != identity_id:
            continue
        profile = str(row.get("profile", "")).strip().lower()
        runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
        return profile == "fixture" or runtime_mode == "demo_only"
    return False


def _collect_validator_ids(task: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    candidate_lists = [
        task.get("required_validators"),
        (task.get("ci_enforcement_contract") or {}).get("required_validators"),
        ((task.get("identity_update_lifecycle_contract") or {}).get("validation_contract") or {}).get("required_checks"),
    ]
    for source in candidate_lists:
        if not isinstance(source, list):
            continue
        for item in source:
            token = str(item).strip()
            if token:
                rows.append(token)
    return list(dict.fromkeys(rows))


def _run_skill_path_integrity(*, catalog: Path, identity_id: str, operation: str) -> tuple[int, dict[str, Any], str]:
    cmd = [
        "python3",
        "scripts/validate_skill_path_integrity.py",
        "--catalog",
        str(catalog),
        "--identity-id",
        identity_id,
        "--operation",
        operation,
        "--json-only",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    raw = (proc.stdout or "").strip()
    payload: dict[str, Any] = {}
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                payload = data
        except Exception:
            payload = {}
    tail = ""
    if raw:
        tail = raw.splitlines()[-1]
    elif (proc.stderr or "").strip():
        tail = (proc.stderr or "").strip().splitlines()[-1]
    return proc.returncode, payload, tail


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate skill installation supply-chain contract (RQ-039).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
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

    fixture_identity = _is_fixture_identity(catalog_path, args.identity_id)
    if fixture_identity:
        required = False

    dependent_contract_keys = contract.get("dependent_contract_keys")
    if isinstance(dependent_contract_keys, list):
        dependent_keys = [str(x).strip() for x in dependent_contract_keys if str(x).strip()]
    else:
        dependent_keys = [str(x) for x in DEFAULT_DEPENDENT_CONTRACT_KEYS]

    required_driver_validators = contract.get("required_capability_drivers")
    if isinstance(required_driver_validators, list):
        driver_validators = [str(x).strip() for x in required_driver_validators if str(x).strip()]
    else:
        driver_validators = [str(x) for x in DEFAULT_DRIVER_VALIDATORS]

    configured_validators = _collect_validator_ids(task)
    missing_dependent_contracts = [
        key for key in dependent_keys if not isinstance(task.get(key), dict)
    ]
    missing_driver_validators = [
        vid for vid in driver_validators if vid not in configured_validators
    ]

    rc_skill, skill_payload, skill_tail = _run_skill_path_integrity(
        catalog=catalog_path,
        identity_id=args.identity_id,
        operation=args.operation,
    )
    skill_status = str(skill_payload.get("path_integrity_status", "")).strip().upper()
    skill_required_skills = list(skill_payload.get("required_skills") or []) if isinstance(skill_payload.get("required_skills"), list) else []

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "fixture_identity": fixture_identity,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": True,
        "requiredization_current_round_linked": bool(skill_required_skills),
        "skill_installation_supply_chain_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "dependent_contract_keys": dependent_keys,
        "missing_dependent_contract_keys": missing_dependent_contracts,
        "required_capability_drivers": driver_validators,
        "missing_capability_drivers": missing_driver_validators,
        "configured_validator_count": len(configured_validators),
        "skill_path_integrity": {
            "status": skill_status,
            "rc": rc_skill,
            "tail": skill_tail,
            "required_skill_count": len(skill_required_skills),
            "stale_reasons": list(skill_payload.get("stale_reasons") or []) if isinstance(skill_payload.get("stale_reasons"), list) else [],
        },
        "evidence_ref": str(task_path),
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["fixture_profile_scope"] if fixture_identity else ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if missing_dependent_contracts:
        payload["skill_installation_supply_chain_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_MISSING
        payload["stale_reasons"] = ["dependent_contract_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if missing_driver_validators:
        payload["skill_installation_supply_chain_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_DRIVER_MISSING
        payload["stale_reasons"] = ["capability_driver_validator_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if rc_skill != 0 or skill_status != STATUS_PASS_REQUIRED:
        payload["skill_installation_supply_chain_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SKILL_PATH_INTEGRITY
        payload["stale_reasons"] = ["skill_path_integrity_not_pass_required"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["skill_installation_supply_chain_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
