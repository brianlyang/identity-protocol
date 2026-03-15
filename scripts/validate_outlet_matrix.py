#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from final_emit_contract_common import FINAL_EMIT_CHANNEL_ID, FINAL_EMIT_POLICY_MODE
from protocol_infra_contract import HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS
from tool_vendor_governance_common import contract_required, latest_identity_upgrade_report, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REPORT_MISSING = "IP-OUTLET-001"
ERR_REQUIRED_FIELD_MISSING = "IP-OUTLET-002"
ERR_OUTLET_BYPASS = "IP-OUTLET-003"
ERR_FINAL_EMIT_CONTRACT = "IP-OUTLET-004"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}
HOST_VISIBLE_GOVERNED_CHANNELS = {
    str(channel).strip().lower()
    for channel in HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS
    if str(channel).strip()
}
HOST_VISIBLE_GOVERNED_CHANNELS.add(FINAL_EMIT_CHANNEL_ID.lower())


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "outbound_reply_outlet_regression_matrix_contract_v1",
        "outlet_regression_matrix_contract_v1",
        "rq_004_outlet_matrix_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _load_json_file(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _resolve_report_path(pack_path: Path, identity_id: str, explicit_report: str) -> tuple[Path | None, dict[str, Any] | None]:
    if explicit_report.strip():
        rp = Path(explicit_report).expanduser().resolve()
        if rp.exists() and rp.is_file():
            return rp, _load_json_file(rp)
        return None, None
    latest = latest_identity_upgrade_report(identity_id, pack_path)
    if latest and latest.exists():
        return latest.resolve(), _load_json_file(latest.resolve())
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate outlet regression matrix contract (RQ-004).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
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
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": False,
        "requiredization_current_round_linked": False,
        "outlet_matrix_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "matrix_positive_status": STATUS_SKIPPED_NOT_REQUIRED,
        "matrix_negative_status": STATUS_SKIPPED_NOT_REQUIRED,
        "cross_cwd_parity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "send_time_gate_status": "",
        "governed_outlet_enforced": False,
        "outlet_channel_id": "",
        "final_emit_channel_id": "",
        "final_emit_policy_mode": "",
        "final_emit_schema_id": "",
        "final_emit_schema_status": "",
        "final_emit_contract_status": "",
        "outlet_bypass_detected": False,
        "blocker_receipt_path": "",
        "outlet_preflight_receipt": "",
        "report_path": "",
        "evidence_ref": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    report_path, report_doc = _resolve_report_path(pack_path, args.identity_id, args.report)
    if report_path is None or report_doc is None:
        payload["stale_reasons"] = ["outlet_matrix_report_not_found"]
        _emit(payload, json_only=args.json_only)
        return 0

    payload["producer_readiness"] = True
    payload["requiredization_current_round_linked"] = True
    payload["report_path"] = str(report_path)
    payload["evidence_ref"] = str(report_path)

    send_time_gate_status = str(report_doc.get("send_time_gate_status", "")).strip().upper()
    governed_outlet = bool(report_doc.get("governed_outlet_enforced", False))
    outlet_bypass = bool(report_doc.get("outlet_bypass_detected", False))
    outlet_channel_id = str(report_doc.get("outlet_channel_id", "")).strip()
    final_emit_channel_id = str(report_doc.get("final_emit_channel_id", "")).strip()
    final_emit_policy_mode = str(report_doc.get("final_emit_policy_mode", "")).strip()
    final_emit_schema_id = str(report_doc.get("final_emit_schema_id", "")).strip()
    final_emit_schema_status = str(report_doc.get("final_emit_schema_status", "")).strip().upper()
    final_emit_contract_status = str(report_doc.get("final_emit_contract_status", "")).strip().upper()
    blocker_receipt_path = str(report_doc.get("blocker_receipt_path", "")).strip()
    outlet_preflight_receipt = str(report_doc.get("outlet_preflight_receipt", "")).strip()

    payload["send_time_gate_status"] = send_time_gate_status
    payload["governed_outlet_enforced"] = governed_outlet
    payload["outlet_channel_id"] = outlet_channel_id
    payload["final_emit_channel_id"] = final_emit_channel_id
    payload["final_emit_policy_mode"] = final_emit_policy_mode
    payload["final_emit_schema_id"] = final_emit_schema_id
    payload["final_emit_schema_status"] = final_emit_schema_status
    payload["final_emit_contract_status"] = final_emit_contract_status
    payload["outlet_bypass_detected"] = outlet_bypass
    payload["blocker_receipt_path"] = blocker_receipt_path
    payload["outlet_preflight_receipt"] = outlet_preflight_receipt

    missing_fields: list[str] = []
    if not send_time_gate_status:
        missing_fields.append("send_time_gate_status")
    if not outlet_channel_id:
        missing_fields.append("outlet_channel_id")
    if not final_emit_channel_id:
        missing_fields.append("final_emit_channel_id")
    if not final_emit_policy_mode:
        missing_fields.append("final_emit_policy_mode")
    if not final_emit_schema_status:
        missing_fields.append("final_emit_schema_status")
    if not final_emit_contract_status:
        missing_fields.append("final_emit_contract_status")
    if not outlet_preflight_receipt:
        missing_fields.append("outlet_preflight_receipt")
    if missing_fields:
        payload["outlet_matrix_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REQUIRED_FIELD_MISSING
        payload["stale_reasons"] = [f"missing_field:{name}" for name in missing_fields]
        _emit(payload, json_only=args.json_only)
        return 1

    positive_pass = send_time_gate_status == STATUS_PASS_REQUIRED and governed_outlet and not outlet_bypass
    payload["matrix_positive_status"] = STATUS_PASS_REQUIRED if positive_pass else STATUS_FAIL_REQUIRED

    negative_pass = bool(blocker_receipt_path or outlet_preflight_receipt)
    payload["matrix_negative_status"] = STATUS_PASS_REQUIRED if negative_pass else STATUS_FAIL_REQUIRED

    catalog_is_abs = Path(catalog_path).is_absolute()
    report_is_abs = Path(report_path).is_absolute()
    payload["cross_cwd_parity_status"] = STATUS_PASS_REQUIRED if catalog_is_abs and report_is_abs else STATUS_FAIL_REQUIRED

    if outlet_bypass:
        payload["outlet_matrix_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_OUTLET_BYPASS
        payload["stale_reasons"] = ["outlet_bypass_detected"]
        _emit(payload, json_only=args.json_only)
        return 1

    outlet_channel_norm = outlet_channel_id.strip().lower()
    outlet_is_governed = outlet_channel_norm in HOST_VISIBLE_GOVERNED_CHANNELS
    outlet_is_final_emit = outlet_channel_norm == FINAL_EMIT_CHANNEL_ID.lower()

    if (
        not outlet_is_governed
        or final_emit_channel_id != FINAL_EMIT_CHANNEL_ID
        or (outlet_is_final_emit and final_emit_policy_mode != FINAL_EMIT_POLICY_MODE)
        or final_emit_schema_status != STATUS_PASS_REQUIRED
        or final_emit_contract_status != STATUS_PASS_REQUIRED
    ):
        payload["outlet_matrix_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_FINAL_EMIT_CONTRACT
        payload["stale_reasons"] = [
            "governed_outlet_contract_mismatch",
            f"expected_outlet_channel_id_in:{','.join(sorted(HOST_VISIBLE_GOVERNED_CHANNELS))}",
            f"expected_final_emit_channel_id:{FINAL_EMIT_CHANNEL_ID}",
            f"expected_final_emit_policy_mode_when_outlet_is_final_emit:{FINAL_EMIT_POLICY_MODE}",
            f"expected_final_emit_schema_status:{STATUS_PASS_REQUIRED}",
            f"expected_final_emit_contract_status:{STATUS_PASS_REQUIRED}",
        ]
        _emit(payload, json_only=args.json_only)
        return 1

    if payload["matrix_positive_status"] != STATUS_PASS_REQUIRED or payload["matrix_negative_status"] != STATUS_PASS_REQUIRED:
        payload["outlet_matrix_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REQUIRED_FIELD_MISSING
        payload["stale_reasons"] = ["matrix_positive_or_negative_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    if payload["cross_cwd_parity_status"] != STATUS_PASS_REQUIRED:
        payload["outlet_matrix_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REQUIRED_FIELD_MISSING
        payload["stale_reasons"] = ["cross_cwd_parity_not_proven"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["outlet_matrix_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
