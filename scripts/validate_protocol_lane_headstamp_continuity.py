#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from actor_session_common import load_actor_binding
from protocol_infra_contract import HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY
from response_stamp_common import parse_identity_context_stamp, resolve_layer_intent
from tool_vendor_governance_common import (
    contract_required,
    latest_identity_upgrade_report,
    load_json,
    load_yaml,
    resolve_pack_and_task,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_ROUTE_NOT_CONFIGURED = "IP-LANE-ROUTE-001"
ERR_PROTOCOL_REQUEST_DOWNGRADED = "IP-LANE-ACT-002"
ERR_LANE_RECEIPT_MISSING = "IP-LANE-ACT-003"
ERR_HEADSTAMP_MISSING_OR_MALFORMED = "IP-HDSTAMP-001"
ERR_HEADSTAMP_ACTOR_BINDING_MISMATCH = "IP-HDSTAMP-002"
ERR_HEADSTAMP_RECEIPT_MISSING = "IP-HDSTAMP-003"

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

PRIMARY_CONTRACT_KEYS = (
    "protocol_lane_activation_headstamp_contract_v1",
    "protocol_lane_activation_headstamp_contract",
)
HOST_VISIBLE_CONTRACT_KEYS = (
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    "protocol_host_visible_surface_registry_contract_v1",
    "protocol_host_visible_surface_registry_contract",
)
HOST_VISIBLE_RECEIPT_PATTERN_DEFAULT = "runtime/reports/host-visible-surface/host-visible-surface-*.json"
HOST_VISIBLE_RUNTIME_RECEIPT_MAX_AGE_SECONDS = 300


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in PRIMARY_CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    # legacy compatibility: accept any contract key that denotes protocol-lane + headstamp continuity.
    for key, node in task.items():
        if not isinstance(node, dict):
            continue
        key_norm = str(key or "").strip().lower()
        if "protocol_lane" in key_norm and "headstamp" in key_norm and "contract" in key_norm:
            return node
    return {}


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog = load_yaml(catalog_path)
    except Exception:
        return False
    identities = catalog.get("identities") or []
    row = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _load_optional_json(path_raw: str) -> tuple[dict[str, Any], str]:
    token = str(path_raw or "").strip()
    if not token:
        return {}, ""
    p = Path(token).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return {}, str(p)
    try:
        node = load_json(p)
    except Exception:
        return {}, str(p)
    return node, str(p)


def _norm_lane(value: Any) -> str:
    token = str(value or "").strip().lower()
    if token in {"protocol", "instance", "dual"}:
        return token
    return ""


def _nonempty(*values: Any) -> str:
    for value in values:
        token = str(value or "").strip()
        if token:
            return token
    return ""


def _resolve_runtime_path(base_path: Path, raw: str) -> Path:
    token = str(raw or "").strip()
    if not token:
        return Path("")
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_path / candidate).resolve()


def _select_host_visible_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in HOST_VISIBLE_CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _load_live_host_visible_receipt(
    *,
    pack_path: Path,
    task: dict[str, Any],
    identity_id: str,
    actor_id: str,
    session_id: str,
    run_id: str,
) -> tuple[dict[str, Any], str, int]:
    contract = _select_host_visible_contract(task)
    if not isinstance(contract, dict):
        return {}, "", -1
    pattern_raw = str(contract.get("runtime_receipt_pattern", "")).strip() or HOST_VISIBLE_RECEIPT_PATTERN_DEFAULT
    glob_path = _resolve_runtime_path(pack_path, pattern_raw)
    if not str(glob_path).strip():
        return {}, "", -1
    try:
        max_age_seconds = int(contract.get("runtime_receipt_max_age_seconds", HOST_VISIBLE_RUNTIME_RECEIPT_MAX_AGE_SECONDS))
    except Exception:
        max_age_seconds = HOST_VISIBLE_RUNTIME_RECEIPT_MAX_AGE_SECONDS
    now_epoch = int(time.time())
    candidates = sorted(glob_path.parent.glob(glob_path.name), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            doc = load_json(path)
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        receipt_identity = str(doc.get("identity_id", "")).strip()
        receipt_actor = str(doc.get("actor_id", "")).strip()
        receipt_session = str(doc.get("session_id", "")).strip()
        receipt_run_id = str(doc.get("run_id", "")).strip()
        if receipt_identity and receipt_identity != identity_id:
            continue
        if actor_id and receipt_actor and receipt_actor != actor_id:
            continue
        if session_id and receipt_session and receipt_session != session_id:
            continue
        if run_id and receipt_run_id and receipt_run_id != run_id:
            continue
        try:
            age_seconds = max(0, int(now_epoch - int(path.stat().st_mtime)))
        except Exception:
            age_seconds = -1
        if max_age_seconds > 0 and age_seconds >= 0 and age_seconds > max_age_seconds:
            continue
        return doc, str(path.resolve()), age_seconds
    return {}, "", -1


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-lane activation and headstamp continuity contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="", help="optional identity-upgrade report json")
    ap.add_argument("--stamp-json", default="", help="optional render_identity_response_stamp artifact json")
    ap.add_argument("--stamp-line", default="", help="optional direct external stamp line")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
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
    required_contract = contract_required(contract)
    auto_required_signal = args.operation in STRICT_OPERATIONS
    enforce_required = bool(required_contract)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "auto_required_signal": auto_required_signal,
        "protocol_lane_headstamp_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_lane_activation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "lane_activation_error_code": "",
        "headstamp_continuity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "headstamp_error_code": "",
        "error_code": "",
        "requested_lane": "",
        "previous_lane": "",
        "resolved_lane": "",
        "route_source_ref": "",
        "lane_activation_evidence_ref": "",
        "protocol_request_detected": False,
        "headstamp_present": False,
        "headstamp_has_layer_context": False,
        "headstamp_identity_id": "",
        "headstamp_actor_id": "",
        "actor_binding_identity_id": "",
        "report_ref": "",
        "stamp_ref": "",
        "headstamp_live_receipt_ref": "",
        "headstamp_live_receipt_age_seconds": -1,
        "headstamp_live_receipt_fallback_applied": False,
        "headstamp_live_receipt_binding_status": STATUS_SKIPPED_NOT_REQUIRED,
        "headstamp_report_fallback_applied": False,
        "headstamp_report_binding_status": STATUS_SKIPPED_NOT_REQUIRED,
        "stale_reasons": [],
        "evidence_ref": "",
    }

    if _is_fixture_identity(catalog_path, args.identity_id):
        payload["stale_reasons"] = ["fixture_profile_scope"]
        _emit(payload, json_only=args.json_only)
        return 0

    report_doc: dict[str, Any] = {}
    report_ref = ""
    if str(args.report or "").strip():
        report_doc, report_ref = _load_optional_json(args.report)
    if not report_doc:
        latest = latest_identity_upgrade_report(args.identity_id, pack_path)
        if latest and latest.exists():
            report_doc, report_ref = _load_optional_json(str(latest))

    stamp_doc: dict[str, Any] = {}
    stamp_ref = ""
    if str(args.stamp_json or "").strip():
        stamp_doc, stamp_ref = _load_optional_json(args.stamp_json)

    stamp_line = _nonempty(
        args.stamp_line,
        stamp_doc.get("external_stamp") if isinstance(stamp_doc, dict) else "",
        report_doc.get("external_stamp") if isinstance(report_doc, dict) else "",
    )
    parsed_stamp = parse_identity_context_stamp(stamp_line) if stamp_line else {}
    live_receipt_doc: dict[str, Any] = {}
    live_receipt_ref = ""
    live_receipt_age_seconds = -1
    if not stamp_line:
        live_receipt_doc, live_receipt_ref, live_receipt_age_seconds = _load_live_host_visible_receipt(
            pack_path=pack_path,
            task=task,
            identity_id=args.identity_id,
            actor_id=str(args.actor_id or "").strip(),
            session_id=str(args.session_id or "").strip(),
            run_id=str(args.run_id or "").strip(),
        )
        payload["headstamp_live_receipt_ref"] = live_receipt_ref
        payload["headstamp_live_receipt_age_seconds"] = live_receipt_age_seconds

    explicit_expected_work = _norm_lane(args.expected_work_layer)
    intent = resolve_layer_intent(
        explicit_work_layer=explicit_expected_work,
        explicit_source_layer=str(args.expected_source_layer or "").strip(),
        intent_text=str(args.layer_intent_text or "").strip(),
        default_work_layer="instance",
        default_source_layer="project",
    )
    requested_lane = _norm_lane(explicit_expected_work or intent.get("resolved_work_layer") or "")
    protocol_request_detected = requested_lane == "protocol" or bool(intent.get("protocol_triggered", False))

    if not enforce_required and (protocol_request_detected or bool(stamp_line)):
        enforce_required = True

    resolved_lane = _norm_lane(
        _nonempty(
            parsed_stamp.get("work_layer"),
            report_doc.get("work_layer"),
            report_doc.get("resolved_work_layer"),
            requested_lane,
            "instance",
        )
    )
    previous_lane = _norm_lane(_nonempty(report_doc.get("previous_lane"), report_doc.get("lane_previous"), ""))
    route_source_ref = _nonempty(
        report_doc.get("route_source_ref"),
        report_doc.get("lane_resolution_decision"),
        report_doc.get("lane_resolution_source"),
        report_doc.get("lane_transition_reason"),
        stamp_doc.get("intent_source"),
        stamp_doc.get("layer_intent_resolution_status"),
    )
    if not route_source_ref and live_receipt_ref:
        route_source_ref = "host_visible_live_receipt_fallback"

    payload["requested_lane"] = requested_lane or "instance"
    payload["resolved_lane"] = resolved_lane or "instance"
    payload["previous_lane"] = previous_lane
    payload["route_source_ref"] = route_source_ref
    payload["lane_activation_evidence_ref"] = report_ref or stamp_ref or live_receipt_ref
    payload["protocol_request_detected"] = protocol_request_detected
    payload["evidence_ref"] = report_ref or stamp_ref or live_receipt_ref or str(task_path)
    payload["report_ref"] = report_ref
    payload["stamp_ref"] = stamp_ref

    if not enforce_required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    lane_status = STATUS_PASS_REQUIRED
    lane_error_code = ""
    lane_reasons: list[str] = []

    if protocol_request_detected and resolved_lane != "protocol":
        lane_status = STATUS_FAIL_REQUIRED
        lane_error_code = ERR_PROTOCOL_REQUEST_DOWNGRADED
        lane_reasons.append("protocol_request_downgraded")
    elif protocol_request_detected and not route_source_ref:
        lane_status = STATUS_FAIL_REQUIRED
        lane_error_code = ERR_ROUTE_NOT_CONFIGURED
        lane_reasons.append("protocol_route_source_missing")
    elif protocol_request_detected and not (report_ref or stamp_ref or live_receipt_ref):
        lane_status = STATUS_FAIL_REQUIRED
        lane_error_code = ERR_LANE_RECEIPT_MISSING
        lane_reasons.append("lane_activation_receipt_missing")

    head_status = STATUS_PASS_REQUIRED
    head_error_code = ""
    head_reasons: list[str] = []

    live_receipt_headstamp_ok = False
    report_headstamp_ok = False
    if not stamp_line and isinstance(live_receipt_doc, dict) and live_receipt_doc:
        receipt_headstamp_status = str(live_receipt_doc.get("headstamp_first_line_status", "")).strip().upper()
        receipt_send_time_status = str(live_receipt_doc.get("send_time_gate_status", "")).strip().upper()
        if receipt_headstamp_status == STATUS_PASS_REQUIRED and receipt_send_time_status in {
            STATUS_PASS_REQUIRED,
            "NOT_APPLICABLE",
        }:
            live_receipt_headstamp_ok = True
            payload["headstamp_live_receipt_fallback_applied"] = True
            payload["headstamp_live_receipt_binding_status"] = STATUS_PASS_REQUIRED
            payload["headstamp_present"] = True
            payload["headstamp_has_layer_context"] = True
            payload["headstamp_identity_id"] = str(live_receipt_doc.get("identity_id", "")).strip() or args.identity_id
            payload["headstamp_actor_id"] = str(live_receipt_doc.get("actor_id", "")).strip()
        else:
            payload["headstamp_live_receipt_binding_status"] = STATUS_FAIL_REQUIRED
            if receipt_headstamp_status != STATUS_PASS_REQUIRED:
                head_reasons.append("headstamp_live_receipt_status_not_pass")
            if receipt_send_time_status not in {STATUS_PASS_REQUIRED, "NOT_APPLICABLE"}:
                head_reasons.append("headstamp_live_receipt_send_time_status_not_pass")
    if not stamp_line and not live_receipt_headstamp_ok and isinstance(report_doc, dict) and report_doc:
        report_headstamp_status = str(report_doc.get("headstamp_first_line_status", "")).strip().upper()
        report_send_time_status = str(report_doc.get("send_time_gate_status", "")).strip().upper()
        report_reply_binding_status = str(report_doc.get("reply_transport_binding_status", "")).strip().upper()
        report_pre_mutation_status = str(report_doc.get("pre_mutation_projection_status", "")).strip().upper()
        report_final_emit_contract_status = str(report_doc.get("final_emit_contract_status", "")).strip().upper()
        report_final_emit_schema_status = str(report_doc.get("final_emit_schema_status", "")).strip().upper()
        report_outlet_bypass_detected = bool(report_doc.get("outlet_bypass_detected", False))
        if (
            report_headstamp_status == STATUS_PASS_REQUIRED
            and report_send_time_status == STATUS_PASS_REQUIRED
            and report_reply_binding_status == STATUS_PASS_REQUIRED
            and report_pre_mutation_status == STATUS_PASS_REQUIRED
            and report_final_emit_contract_status == STATUS_PASS_REQUIRED
            and report_final_emit_schema_status == STATUS_PASS_REQUIRED
            and not report_outlet_bypass_detected
        ):
            report_headstamp_ok = True
            payload["headstamp_report_fallback_applied"] = True
            payload["headstamp_report_binding_status"] = STATUS_PASS_REQUIRED
            payload["headstamp_present"] = True
            payload["headstamp_has_layer_context"] = bool(
                _nonempty(
                    report_doc.get("work_layer"),
                    report_doc.get("resolved_work_layer"),
                    args.expected_work_layer,
                )
                and _nonempty(
                    report_doc.get("source_layer"),
                    report_doc.get("resolved_source_layer"),
                    args.expected_source_layer,
                )
            )
            payload["headstamp_identity_id"] = args.identity_id
            payload["headstamp_actor_id"] = _nonempty(args.actor_id, report_doc.get("actor_id"))
        else:
            payload["headstamp_report_binding_status"] = STATUS_FAIL_REQUIRED
            if report_headstamp_status != STATUS_PASS_REQUIRED:
                head_reasons.append("headstamp_report_status_not_pass")
            if report_send_time_status != STATUS_PASS_REQUIRED:
                head_reasons.append("headstamp_report_send_time_status_not_pass")
            if report_reply_binding_status != STATUS_PASS_REQUIRED:
                head_reasons.append("headstamp_report_reply_binding_status_not_pass")
            if report_pre_mutation_status != STATUS_PASS_REQUIRED:
                head_reasons.append("headstamp_report_pre_mutation_projection_not_pass")
            if report_final_emit_contract_status != STATUS_PASS_REQUIRED:
                head_reasons.append("headstamp_report_final_emit_contract_status_not_pass")
            if report_final_emit_schema_status != STATUS_PASS_REQUIRED:
                head_reasons.append("headstamp_report_final_emit_schema_status_not_pass")
            if report_outlet_bypass_detected:
                head_reasons.append("headstamp_report_outlet_bypass_detected")
    if not stamp_line and not live_receipt_headstamp_ok:
        if report_headstamp_ok:
            pass
        else:
            head_status = STATUS_FAIL_REQUIRED
            head_error_code = ERR_HEADSTAMP_RECEIPT_MISSING
            if "headstamp_receipt_missing" not in head_reasons:
                head_reasons.append("headstamp_receipt_missing")
    elif live_receipt_headstamp_ok:
        if payload["headstamp_identity_id"] and payload["headstamp_identity_id"] != args.identity_id:
            head_status = STATUS_FAIL_REQUIRED
            head_error_code = ERR_HEADSTAMP_ACTOR_BINDING_MISMATCH
            head_reasons.append("headstamp_identity_mismatch")
        else:
            actor_id_effective = _nonempty(args.actor_id, payload["headstamp_actor_id"])
            if actor_id_effective:
                binding = load_actor_binding(
                    catalog_path,
                    actor_id_effective,
                    identity_id=args.identity_id,
                    session_id=str(args.session_id or "").strip(),
                )
                binding_identity = str(binding.get("identity_id", "")).strip()
                payload["actor_binding_identity_id"] = binding_identity
                if binding_identity and binding_identity != args.identity_id:
                    head_status = STATUS_FAIL_REQUIRED
                    head_error_code = ERR_HEADSTAMP_ACTOR_BINDING_MISMATCH
                    head_reasons.append("actor_binding_identity_mismatch")
    elif report_headstamp_ok:
        actor_id_effective = _nonempty(args.actor_id, payload["headstamp_actor_id"])
        if actor_id_effective:
            binding = load_actor_binding(
                catalog_path,
                actor_id_effective,
                identity_id=args.identity_id,
                session_id=str(args.session_id or "").strip(),
            )
            binding_identity = str(binding.get("identity_id", "")).strip()
            payload["actor_binding_identity_id"] = binding_identity
            if binding_identity and binding_identity != args.identity_id:
                head_status = STATUS_FAIL_REQUIRED
                head_error_code = ERR_HEADSTAMP_ACTOR_BINDING_MISMATCH
                head_reasons.append("actor_binding_identity_mismatch")
    elif not parsed_stamp or not parsed_stamp.get("_has_layer_context"):
        head_status = STATUS_FAIL_REQUIRED
        head_error_code = ERR_HEADSTAMP_MISSING_OR_MALFORMED
        head_reasons.append("headstamp_missing_or_malformed")
    else:
        payload["headstamp_present"] = True
        payload["headstamp_has_layer_context"] = bool(parsed_stamp.get("_has_layer_context", False))
        payload["headstamp_identity_id"] = str(parsed_stamp.get("identity_id", "")).strip()
        payload["headstamp_actor_id"] = str(parsed_stamp.get("actor_id", "")).strip()

        if payload["headstamp_identity_id"] and payload["headstamp_identity_id"] != args.identity_id:
            head_status = STATUS_FAIL_REQUIRED
            head_error_code = ERR_HEADSTAMP_ACTOR_BINDING_MISMATCH
            head_reasons.append("headstamp_identity_mismatch")
        else:
            actor_id_effective = _nonempty(args.actor_id, payload["headstamp_actor_id"])
            if actor_id_effective:
                binding = load_actor_binding(
                    catalog_path,
                    actor_id_effective,
                    identity_id=args.identity_id,
                )
                binding_identity = str(binding.get("identity_id", "")).strip()
                payload["actor_binding_identity_id"] = binding_identity
                if binding_identity and binding_identity != args.identity_id:
                    head_status = STATUS_FAIL_REQUIRED
                    head_error_code = ERR_HEADSTAMP_ACTOR_BINDING_MISMATCH
                    head_reasons.append("actor_binding_identity_mismatch")

    stale = [*lane_reasons, *head_reasons]
    overall_fail = lane_status == STATUS_FAIL_REQUIRED or head_status == STATUS_FAIL_REQUIRED
    payload["protocol_lane_activation_status"] = lane_status
    payload["lane_activation_error_code"] = lane_error_code
    payload["headstamp_continuity_status"] = head_status
    payload["headstamp_error_code"] = head_error_code
    payload["protocol_lane_headstamp_status"] = STATUS_FAIL_REQUIRED if overall_fail else STATUS_PASS_REQUIRED
    payload["error_code"] = lane_error_code or head_error_code
    payload["stale_reasons"] = stale
    _emit(payload, json_only=args.json_only)
    return 1 if overall_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
