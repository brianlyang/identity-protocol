#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_TUPLE_MISSING = "IP-XTARGET-001"
ERR_CONFLICT_KEY_LEGACY = "IP-XTARGET-002"
ERR_OVERRIDE_BYPASS = "IP-XTARGET-003"
ERR_PROCESS_CALL_MISSING = "IP-XTARGET-004"

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

OBSERVATION_OPERATIONS = {"scan", "three-plane", "inspection", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "execution_target_tuple_isolation_contract_v1",
        "execution_target_tuple_isolation_contract",
        "rq_033_execution_target_tuple_isolation_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(tok in text for tok in tokens)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate execution-target tuple isolation contract (RQ-033).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--runtime-bridge-root", default="")
    ap.add_argument(
        "--operation",
        choices=[
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
        ],
        default="validate",
    )
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
    required = contract_required(contract) if contract else False
    runtime_bridge_root_raw = str(args.runtime_bridge_root or "").strip() or str(
        contract.get("runtime_bridge_root", "")
    ).strip() or str(os.getenv("IDENTITY_RUNTIME_BRIDGE_ROOT", "")).strip()
    auto_required = bool(runtime_bridge_root_raw)
    if auto_required:
        required = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "run_profile": "observation" if args.operation in OBSERVATION_OPERATIONS else "enforcement",
        "required_contract": required,
        "auto_required_signal": auto_required,
        "producer_readiness": False,
        "requiredization_current_round_linked": bool(required and (auto_required or args.operation in STRICT_OPERATIONS)),
        "execution_target_tuple_isolation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "runtime_bridge_root": runtime_bridge_root_raw,
        "execution_target_kind": "",
        "execution_target_key": "",
        "execution_target_ref": "",
        "route_conflict_status": "",
        "route_conflict_error_code": "",
        "tuple_fields_present": [],
        "tuple_fields_missing": [],
        "conflict_key_mode": "unknown",
        "override_non_bypass_status": "unknown",
        "process_call_support_status": "unknown",
        "stale_reasons": [],
        "evidence_ref": "",
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not runtime_bridge_root_raw:
        payload["execution_target_tuple_isolation_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TUPLE_MISSING
        payload["stale_reasons"] = ["runtime_bridge_root_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    runtime_bridge_root = Path(runtime_bridge_root_raw).expanduser().resolve()
    main_path = runtime_bridge_root / "src" / "feiqiao_guard" / "main.py"
    router_path = runtime_bridge_root / "src" / "feiqiao_guard" / "identity_router.py"
    models_path = runtime_bridge_root / "src" / "feiqiao_guard" / "models.py"

    missing_files = [str(p) for p in (main_path, router_path, models_path) if not p.exists()]
    if missing_files:
        payload["execution_target_tuple_isolation_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TUPLE_MISSING
        payload["stale_reasons"] = ["runtime_bridge_files_missing"]
        payload["tuple_fields_missing"] = missing_files
        payload["evidence_ref"] = str(runtime_bridge_root)
        _emit(payload, json_only=args.json_only)
        return 1

    main_text = main_path.read_text(encoding="utf-8", errors="ignore")
    router_text = router_path.read_text(encoding="utf-8", errors="ignore")
    models_text = models_path.read_text(encoding="utf-8", errors="ignore")

    payload["evidence_ref"] = f"{main_path};{router_path};{models_path}"

    tuple_presence: dict[str, bool] = {
        "models.execution_target_kind": "execution_target_kind" in models_text,
        "models.execution_target_key": "execution_target_key" in models_text,
        "router.execution_target_kind": "execution_target_kind" in router_text,
        "router.execution_target_key": "execution_target_key" in router_text,
        "main.execution_target_kind": _contains_any(main_text, ("execution_target_kind", "target_kind")),
        "main.execution_target_key": _contains_any(main_text, ("execution_target_key", "target_key")),
    }
    present = sorted([k for k, v in tuple_presence.items() if v])
    missing = sorted([k for k, v in tuple_presence.items() if not v])
    payload["tuple_fields_present"] = present
    payload["tuple_fields_missing"] = missing

    stale_reasons: list[str] = []
    error_code = ""

    if missing:
        stale_reasons.append("execution_target_tuple_fields_missing")
        error_code = error_code or ERR_TUPLE_MISSING

    if tuple_presence["router.execution_target_kind"] and tuple_presence["router.execution_target_key"]:
        payload["conflict_key_mode"] = "execution_target_tuple"
        payload["route_conflict_status"] = STATUS_PASS_REQUIRED
    else:
        payload["conflict_key_mode"] = "legacy_session_codex_only"
        payload["route_conflict_status"] = STATUS_FAIL_REQUIRED
        payload["route_conflict_error_code"] = ERR_CONFLICT_KEY_LEGACY
        stale_reasons.append("conflict_key_not_tuple_based")
        error_code = error_code or ERR_CONFLICT_KEY_LEGACY

    override_guard_present = (
        "route_issue(" in main_text
        and "chat_inbound_blocked_route_issue" in main_text
        and "status_code=409" in main_text
    )
    if override_guard_present:
        payload["override_non_bypass_status"] = STATUS_PASS_REQUIRED
    else:
        payload["override_non_bypass_status"] = STATUS_FAIL_REQUIRED
        stale_reasons.append("override_bypass_guard_missing")
        error_code = error_code or ERR_OVERRIDE_BYPASS

    requires_session_or_codex = (
        "identity_or_session_or_codex_home_required" in main_text
        or "session_or_codex_home_required" in main_text
    )
    process_call_markers = _contains_any(
        main_text + "\n" + models_text,
        ("process_call", "invocation_lane_id", "execution_target_kind"),
    )
    if (not requires_session_or_codex) and process_call_markers:
        payload["process_call_support_status"] = STATUS_PASS_REQUIRED
    else:
        payload["process_call_support_status"] = STATUS_FAIL_REQUIRED
        stale_reasons.append("process_call_target_without_codex_home_not_supported")
        error_code = error_code or ERR_PROCESS_CALL_MISSING

    payload["producer_readiness"] = True

    if stale_reasons:
        payload["execution_target_tuple_isolation_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code
        payload["stale_reasons"] = sorted(dict.fromkeys(stale_reasons))
        _emit(payload, json_only=args.json_only)
        return 1

    payload["execution_target_tuple_isolation_status"] = STATUS_PASS_REQUIRED
    payload["route_conflict_error_code"] = ""
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
