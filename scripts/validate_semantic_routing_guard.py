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
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task, resolve_report_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MISSING_CLASSIFICATION = "IP-SEM-001"
ERR_MIXED_WITHOUT_SPLIT = "IP-SEM-002"
ERR_NAMESPACE_VIOLATION = "IP-SEM-003"
ERR_DOMAIN_WHITELIST = "IP-SEM-004"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}

REQ_CONTRACT_KEYS = (
    "required",
    "feedback_batch_path_pattern",
    "required_fields",
    "enforcement_validator",
)
DEFAULT_REQUIRED_FIELDS = ("intent_domain", "intent_confidence", "classifier_reason")
DEFAULT_DOMAIN_ENUM = ("protocol_vendor", "business_partner", "mixed", "unknown")


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


def _extract_first(text: str, pattern: str) -> str:
    m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else ""


def _extract_fields(feedback_path: Path) -> tuple[dict[str, Any], str]:
    raw = feedback_path.read_text(encoding="utf-8", errors="ignore")
    parsed: dict[str, Any] = {}
    try:
        doc = json.loads(raw)
        if isinstance(doc, dict):
            parsed = doc
    except Exception:
        parsed = {}

    fields: dict[str, Any] = {
        "intent_domain": str(parsed.get("intent_domain", "")).strip(),
        "intent_confidence": parsed.get("intent_confidence"),
        "classifier_reason": str(parsed.get("classifier_reason", "")).strip(),
    }
    if not fields["intent_domain"]:
        fields["intent_domain"] = _extract_first(raw, r"\bintent_domain\b\s*[:=]\s*([a-zA-Z_]+)")
    if fields["intent_confidence"] is None or str(fields["intent_confidence"]).strip() == "":
        conf = _extract_first(raw, r"\bintent_confidence\b\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)")
        fields["intent_confidence"] = conf
    if not fields["classifier_reason"]:
        fields["classifier_reason"] = _extract_first(raw, r"\bclassifier_reason\b\s*[:=]\s*(.+)$")

    return fields, raw


def _split_evidence_present(text: str, parsed_fields: dict[str, Any]) -> bool:
    low = text.lower()
    if "protocol-vendor-intel/" in low and "business-partner-intel/" in low:
        return True
    split_marker = any(x in low for x in ("split+tag", "split and tag", "split-tagged", "manual review handoff"))
    if split_marker and ("protocol_vendor" in low or "business_partner" in low):
        return True
    refs = parsed_fields.get("split_outputs")
    if isinstance(refs, list):
        joined = " ".join(str(x).lower() for x in refs)
        if "protocol-vendor-intel/" in joined and "business-partner-intel/" in joined:
            return True
    return False


def _legacy_namespace_refs(text: str) -> list[str]:
    refs: list[str] = []
    for m in re.finditer(r"`([^`]+)`", text):
        token = m.group(1).strip()
        low = token.lower()
        if "vendor-intel/" in low and "protocol-vendor-intel/" not in low and "business-partner-intel/" not in low:
            refs.append(token)
    for m in re.finditer(r"(?im)^\s*[-*0-9.]+\s+([^\s].+)$", text):
        token = m.group(1).strip()
        low = token.lower()
        if "vendor-intel/" in low and "protocol-vendor-intel/" not in low and "business-partner-intel/" not in low:
            refs.append(token)
    return sorted(set(refs))


def _to_float(v: Any) -> float | None:
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate semantic routing guard contract for protocol feedback batches.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--feedback-batch", default="")
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
        feedback_root=(pack_path / "runtime" / "protocol-feedback"),
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
        "semantic_routing_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "feedback_batch_path": "",
        "intent_domain": "",
        "intent_confidence": None,
        "classifier_reason": "",
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

    missing_contract = [k for k in REQ_CONTRACT_KEYS if k not in contract]
    if missing_contract:
        payload["semantic_routing_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MISSING_CLASSIFICATION
        payload["stale_reasons"] = [f"contract_missing_fields:{','.join(missing_contract)}"]
        _emit(payload, json_only=args.json_only)
        return 1

    batch_path: Path | None = None
    if args.feedback_batch.strip():
        p = Path(args.feedback_batch).expanduser().resolve()
        if p.exists():
            batch_path = p
    else:
        pattern = str(contract.get("feedback_batch_path_pattern", "")).strip()
        if not pattern:
            pattern = "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md"
        batch_path = resolve_report_path(report="", pattern=pattern, pack_root=pack_path)

    if batch_path is None:
        payload["error_code"] = ERR_MISSING_CLASSIFICATION
        payload["stale_reasons"] = ["feedback_batch_not_found"]
        if args.operation in INSPECTION_OPERATIONS:
            payload["semantic_routing_status"] = STATUS_SKIPPED_NOT_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 0
        payload["semantic_routing_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    payload["feedback_batch_path"] = str(batch_path)
    fields, raw = _extract_fields(batch_path)
    intent_domain = str(fields.get("intent_domain", "")).strip().lower()
    conf = _to_float(fields.get("intent_confidence"))
    classifier_reason = str(fields.get("classifier_reason", "")).strip()
    payload["intent_domain"] = intent_domain
    payload["intent_confidence"] = conf
    payload["classifier_reason"] = classifier_reason

    required_fields = contract.get("required_fields")
    if not isinstance(required_fields, list) or not required_fields:
        required_fields = list(DEFAULT_REQUIRED_FIELDS)
    domain_enum = contract.get("domain_enum")
    if not isinstance(domain_enum, list) or not domain_enum:
        domain_enum = list(DEFAULT_DOMAIN_ENUM)
    domain_enum_set = {str(x).strip().lower() for x in domain_enum if str(x).strip()}

    stale_reasons: list[str] = []
    error_code = ""
    if "intent_domain" in required_fields and not intent_domain:
        stale_reasons.append("intent_domain_missing")
        error_code = ERR_MISSING_CLASSIFICATION
    if "intent_confidence" in required_fields and conf is None:
        stale_reasons.append("intent_confidence_missing")
        error_code = ERR_MISSING_CLASSIFICATION
    elif conf is not None and not (0.0 <= conf <= 1.0):
        stale_reasons.append("intent_confidence_out_of_range")
        error_code = ERR_MISSING_CLASSIFICATION
    if "classifier_reason" in required_fields and not classifier_reason:
        stale_reasons.append("classifier_reason_missing")
        error_code = ERR_MISSING_CLASSIFICATION

    if intent_domain and intent_domain not in domain_enum_set:
        stale_reasons.append("intent_domain_not_in_whitelist")
        error_code = ERR_DOMAIN_WHITELIST

    if intent_domain == "mixed" and not _split_evidence_present(raw, fields):
        stale_reasons.append("mixed_domain_without_split_evidence")
        error_code = ERR_MIXED_WITHOUT_SPLIT

    if intent_domain == "unknown":
        rr = classifier_reason.lower()
        if not any(x in rr for x in ("clarify", "disambiguat", "split", "tag", "manual review")):
            stale_reasons.append("unknown_domain_without_clarification_strategy")
            error_code = ERR_MIXED_WITHOUT_SPLIT

    legacy_refs = _legacy_namespace_refs(raw)
    payload["legacy_namespace_refs"] = legacy_refs
    if legacy_refs:
        stale_reasons.append("legacy_vendor_namespace_reference_detected")
        if not error_code:
            error_code = ERR_NAMESPACE_VIOLATION

    if stale_reasons:
        payload["semantic_routing_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_MISSING_CLASSIFICATION
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["semantic_routing_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
