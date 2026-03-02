#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from protocol_feedback_lane_common import (
    build_correlation_keys,
    collect_protocol_feedback_activity,
    decide_requiredization_scope,
    discover_default_correlation_keys,
)
from response_stamp_common import resolve_layer_intent
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MISSING_CLASSIFICATION = "IP-SEM-001"
ERR_MIXED_WITHOUT_SPLIT = "IP-SEM-002"
ERR_NAMESPACE_VIOLATION = "IP-SEM-003"
ERR_DOMAIN_WHITELIST = "IP-SEM-004"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "semantic_routing_guard_contract_v1",
        "semantic_routing_guard_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _collect_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted([p for p in root.rglob("*") if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)


def _outbox_legacy_refs(outbox_dir: Path) -> list[str]:
    if not outbox_dir.exists():
        return []
    refs: list[str] = []
    for p in sorted(outbox_dir.glob("FEEDBACK_BATCH_*")):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r"`([^`]+)`", text):
            token = m.group(1).strip()
            low = token.lower()
            if "vendor-intel/" in low and "protocol-vendor-intel/" not in low and "business-partner-intel/" not in low:
                refs.append(f"{p}:{token}")
    return sorted(set(refs))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol feedback vendor namespace separation contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--feedback-root", default="")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--correlation-key", action="append", default=[])
    ap.add_argument("--activity-window-hours", type=float, default=72.0)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
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
    required_declared = contract_required(contract) if contract else False
    feedback_root = Path(args.feedback_root).expanduser().resolve() if args.feedback_root.strip() else (
        pack_path / "runtime" / "protocol-feedback"
    ).resolve()
    layer_intent = resolve_layer_intent(
        explicit_work_layer=str(args.expected_work_layer or "").strip(),
        explicit_source_layer=str(args.expected_source_layer or "").strip(),
        intent_text=str(args.layer_intent_text or "").strip(),
        default_work_layer="instance",
        default_source_layer="auto",
    )
    default_corr = discover_default_correlation_keys(pack_path)
    correlation_keys = build_correlation_keys(
        default_keys=default_corr.get("correlation_keys", []),
        run_id=str(args.run_id or "").strip(),
        explicit_keys=list(args.correlation_key or []),
    )
    activity = collect_protocol_feedback_activity(
        feedback_root=feedback_root,
        correlation_keys=correlation_keys,
        activity_window_hours=float(args.activity_window_hours or 72.0),
    )
    auto_required_candidate = (not required_declared) and bool(activity.get("protocol_feedback_activity_detected", False))
    required_scope = decide_requiredization_scope(
        required_declared=required_declared,
        auto_required_candidate=auto_required_candidate,
        resolved_work_layer=str(layer_intent.get("resolved_work_layer", "instance")),
        protocol_triggered=bool(layer_intent.get("protocol_triggered", False)),
        current_round_linked=bool(activity.get("requiredization_current_round_linked", False)),
    )
    required = bool(required_scope.get("required_contract", False))
    auto_required_signal = bool(required_scope.get("auto_required_signal", False))
    protocol_vendor_root = (feedback_root / "protocol-vendor-intel").resolve()
    business_partner_root = (feedback_root / "business-partner-intel").resolve()
    legacy_vendor_root = (feedback_root / "vendor-intel").resolve()
    outbox_root = (feedback_root / "outbox-to-protocol").resolve()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "required_contract_declared": required_declared,
        "auto_required_signal": auto_required_signal,
        "requiredization_scope_decision": str(required_scope.get("requiredization_scope_decision", "")),
        "requiredization_scope_reason": str(required_scope.get("requiredization_scope_reason", "")),
        "requiredization_current_round_linked": bool(activity.get("requiredization_current_round_linked", False)),
        "requiredization_historical_activity_detected": bool(activity.get("requiredization_historical_activity_detected", False)),
        "activity_correlation_status": str(activity.get("activity_correlation_status", "")),
        "activity_correlation_key": str(activity.get("activity_correlation_key", "")),
        "activity_window_hours": float(activity.get("activity_window_hours", args.activity_window_hours)),
        "activity_correlated_refs": list(activity.get("activity_correlated_refs", [])),
        "activity_unscoped_refs": list(activity.get("activity_unscoped_refs", [])),
        "activity_ignored_stale_refs": list(activity.get("activity_ignored_stale_refs", [])),
        "protocol_feedback_activity_detected": bool(activity.get("protocol_feedback_activity_detected", False)),
        "protocol_feedback_activity_refs": list(activity.get("protocol_feedback_activity_refs", [])),
        "resolved_work_layer": str(layer_intent.get("resolved_work_layer", "")),
        "resolved_source_layer": str(layer_intent.get("resolved_source_layer", "")),
        "protocol_triggered": bool(layer_intent.get("protocol_triggered", False)),
        "protocol_trigger_reasons": list(layer_intent.get("protocol_trigger_reasons") or []),
        "intent_source": str(layer_intent.get("intent_source", "")),
        "intent_confidence": layer_intent.get("intent_confidence"),
        "fallback_reason": str(layer_intent.get("fallback_reason", "")),
        "default_correlation_run_id": str(default_corr.get("latest_run_id", "")),
        "default_correlation_report": str(default_corr.get("latest_report_path", "")),
        "correlation_keys": correlation_keys,
        "feedback_root": str(feedback_root),
        "protocol_vendor_root": str(protocol_vendor_root),
        "business_partner_root": str(business_partner_root),
        "legacy_vendor_root": str(legacy_vendor_root),
        "vendor_namespace_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "protocol_vendor_file_count": 0,
        "business_partner_file_count": 0,
        "legacy_vendor_file_count": 0,
        "legacy_namespace_refs": [],
        "stale_reasons": [],
    }

    if not required:
        if auto_required_candidate and bool(activity.get("requiredization_historical_activity_detected", False)):
            payload["stale_reasons"] = ["contract_not_required_due_lane_scope_history_only_activity"]
        else:
            payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not feedback_root.exists():
        payload["error_code"] = ERR_MISSING_CLASSIFICATION
        payload["stale_reasons"] = ["feedback_root_not_found"]
        if args.operation in INSPECTION_OPERATIONS:
            payload["vendor_namespace_status"] = STATUS_SKIPPED_NOT_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 0
        payload["vendor_namespace_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    protocol_files = _collect_files(protocol_vendor_root)
    business_files = _collect_files(business_partner_root)
    legacy_files = _collect_files(legacy_vendor_root)
    outbox_legacy = _outbox_legacy_refs(outbox_root)

    payload["protocol_vendor_file_count"] = len(protocol_files)
    payload["business_partner_file_count"] = len(business_files)
    payload["legacy_vendor_file_count"] = len(legacy_files)
    payload["legacy_namespace_refs"] = outbox_legacy

    stale_reasons: list[str] = []
    error_code = ""

    require_split = bool(contract.get("require_split_namespaces", True))
    if require_split and len(protocol_files) == 0 and len(business_files) == 0:
        stale_reasons.append("split_namespace_outputs_missing")
        error_code = ERR_DOMAIN_WHITELIST

    if legacy_files:
        stale_reasons.append("legacy_vendor_namespace_has_files")
        error_code = ERR_NAMESPACE_VIOLATION

    if outbox_legacy:
        stale_reasons.append("outbox_references_legacy_vendor_namespace")
        if not error_code:
            error_code = ERR_NAMESPACE_VIOLATION

    if stale_reasons:
        payload["vendor_namespace_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_NAMESPACE_VIOLATION
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["vendor_namespace_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
