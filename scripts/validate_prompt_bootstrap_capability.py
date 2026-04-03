#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from prompt_live_driver_binding_common import (
    derive_prompt_live_driver_binding_projection,
    merge_prompt_live_driver_binding_contract_defaults,
)
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_DRIVER_MISSING = "IP-PBOOT-001"
ERR_PROMPT_MISSING = "IP-PBOOT-002"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}
DEFAULT_DRIVERS = (
    "scripts/validate_identity_tool_installation.py",
    "scripts/validate_identity_vendor_api_discovery.py",
    "scripts/validate_identity_vendor_api_solution.py",
)


def _clean_string(value: Any) -> str:
    return str(value or "").strip()


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "prompt_bootstrap_capability_contract_v1",
        "prompt_bootstrap_capability_contract",
        "rq_014_prompt_bootstrap_capability_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _required_drivers(contract: dict[str, Any]) -> list[str]:
    rows = contract.get("required_capability_drivers")
    if isinstance(rows, list):
        vals = [str(x).strip() for x in rows if str(x).strip()]
        if vals:
            return vals
    return [str(x) for x in DEFAULT_DRIVERS]


def _collect_configured_validators(task: dict[str, Any]) -> list[str]:
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
    # Preserve first-seen order while removing duplicates.
    return list(dict.fromkeys(rows))


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate prompt bootstrap capability contract (RQ-014).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
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

    contract = merge_prompt_live_driver_binding_contract_defaults(_select_contract(task))
    required = contract_required(contract)
    if args.force_required:
        required = True
    fixture_identity = _is_fixture_identity(catalog_path, args.identity_id)
    if fixture_identity:
        required = False

    prompt_path = (pack_path / "IDENTITY_PROMPT.md").resolve()
    prompt_text = prompt_path.read_text(encoding="utf-8", errors="ignore") if prompt_path.exists() else ""
    required_drivers = _required_drivers(contract)
    configured_validators = _collect_configured_validators(task)

    present: list[str] = []
    missing: list[str] = []
    for driver in required_drivers:
        if driver in configured_validators or Path(driver).name in prompt_text:
            present.append(driver)
        else:
            missing.append(driver)

    total = len(required_drivers)
    passed = len(present)
    coverage = round((passed / total) * 100.0, 2) if total > 0 else 100.0

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "prompt_path": str(prompt_path),
        "operation": args.operation,
        "fixture_identity": fixture_identity,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": prompt_path.exists(),
        "requiredization_current_round_linked": False,
        "prompt_bootstrap_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "capability_driver_required_total": total,
        "capability_driver_present_total": passed,
        "capability_driver_coverage_rate": coverage,
        "missing_capability_drivers": missing,
        "required_capability_drivers": required_drivers,
        "evidence_ref": str(prompt_path) if prompt_path.exists() else "",
        "driver_receipt_refs": [],
        "driver_run_id": "",
        "driver_projection_digest": "",
        "current_run_driver_binding_status": STATUS_SKIPPED_NOT_REQUIRED if not required else STATUS_FAIL_REQUIRED,
        "current_run_report_path": "",
        "prompt_runtime_state_path": "",
        "evidence_origin": "missing",
        "stale_reasons": [],
    }

    if required:
        live_projection = derive_prompt_live_driver_binding_projection(
            pack_root=pack_path,
            contract_doc=contract,
            prompt_path=prompt_path,
        )
        payload.update(live_projection)

    if not required:
        payload["stale_reasons"] = ["fixture_profile_scope"] if fixture_identity else ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not prompt_path.exists():
        payload["prompt_bootstrap_contract_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PROMPT_MISSING
        payload["stale_reasons"] = ["identity_prompt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if missing:
        payload["prompt_bootstrap_contract_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_DRIVER_MISSING
        payload["stale_reasons"] = ["capability_driver_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["prompt_bootstrap_contract_status"] = STATUS_PASS_REQUIRED
    payload["requiredization_current_round_linked"] = (
        _clean_string(payload.get("current_run_driver_binding_status")).upper() == STATUS_PASS_REQUIRED
    )
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
