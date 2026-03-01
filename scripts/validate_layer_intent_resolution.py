#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from response_stamp_common import (
    ALLOWED_SOURCE_LAYERS,
    ALLOWED_WORK_LAYERS,
    parse_identity_context_stamp,
    resolve_layer_intent,
    resolve_stamp_context,
)
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_LAYER_INTENT = "IP-ASB-STAMP-SESSION-001"
STRICT_OPERATIONS = {"activate", "update", "mutation", "readiness", "e2e", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "layer_intent_resolution_contract_v1",
        "layer_intent_resolution_contract",
        "reply_identity_context_first_line_contract_v1",
        "identity_response_stamp_contract",
        "response_stamp_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _normalize_layer_value(value: str, *, allowed: set[str], fallback: str) -> str:
    token = str(value or "").strip().lower()
    if token in allowed:
        return token
    fb = str(fallback or "").strip().lower()
    return fb if fb in allowed else next(iter(sorted(allowed)))


def _run_regression_samples(default_source_layer: str) -> dict[str, Any]:
    samples = [
        {
            "sample_id": "instance_intent",
            "intent_text": "business execution runtime deliver",
            "expect_work_layer": "instance",
            "expect_protocol_triggered": False,
        },
        {
            "sample_id": "protocol_intent",
            "intent_text": "protocol governance required gate fail IP-LAYER-TEST-001 fix wiring",
            "expect_work_layer": "protocol",
            "expect_protocol_triggered": True,
        },
        {
            "sample_id": "ambiguous_intent",
            "intent_text": "business runtime with protocol governance context",
            "expect_work_layer": "instance",
            "expect_protocol_triggered": False,
        },
    ]
    rows: list[dict[str, Any]] = []
    failed_ids: list[str] = []
    for sample in samples:
        resolved = resolve_layer_intent(
            intent_text=str(sample.get("intent_text", "")),
            default_work_layer="instance",
            default_source_layer=default_source_layer,
        )
        actual_work = str(resolved.get("resolved_work_layer", "")).strip().lower()
        actual_trigger = bool(resolved.get("protocol_triggered", False))
        passed = (
            actual_work == str(sample.get("expect_work_layer", "")).strip().lower()
            and actual_trigger == bool(sample.get("expect_protocol_triggered", False))
        )
        row = {
            "sample_id": sample["sample_id"],
            "expect_work_layer": sample["expect_work_layer"],
            "actual_work_layer": actual_work,
            "expect_protocol_triggered": bool(sample["expect_protocol_triggered"]),
            "actual_protocol_triggered": actual_trigger,
            "pass": passed,
        }
        rows.append(row)
        if not passed:
            failed_ids.append(sample["sample_id"])
    return {
        "status": STATUS_PASS_REQUIRED if not failed_ids else STATUS_FAIL_REQUIRED,
        "failed_sample_ids": failed_ids,
        "samples": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate automatic layer-intent resolution for Identity-Context reply stamp.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--work-layer", default="", help="explicit work-layer override for resolver seed")
    ap.add_argument("--source-layer", default="", help="explicit source-layer override for resolver seed")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--stamp-line", default="")
    ap.add_argument("--stamp-json", default="")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--enforce-layer-intent-gate", action="store_true")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "mutation", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        _, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required_contract = bool(args.force_check or args.enforce_layer_intent_gate or contract_required(contract))
    if not required_contract:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "required_contract": False,
            "layer_intent_resolution_status": STATUS_SKIPPED_NOT_REQUIRED,
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "",
            "fallback_reason": "contract_not_required",
            "error_code": "",
            "stale_reasons": ["contract_not_required"],
        }
        _emit(payload, json_only=args.json_only)
        return 0

    try:
        ctx = resolve_stamp_context(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            actor_id=args.actor_id,
            explicit_catalog=bool(str(args.catalog or "").strip()),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve stamp context: {exc}")
        return 1

    stamp_doc: dict[str, Any] = {}
    stamp_line = str(args.stamp_line or "").strip()
    if str(args.stamp_json or "").strip():
        p = Path(args.stamp_json).expanduser().resolve()
        if not p.exists():
            print(f"[FAIL] stamp json not found: {p}")
            return 1
        try:
            raw_doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[FAIL] invalid stamp json: {p} ({exc})")
            return 1
        if isinstance(raw_doc, dict):
            stamp_doc = raw_doc
        if not stamp_line:
            stamp_line = str(stamp_doc.get("external_stamp", "")).strip()

    resolver_work = str(args.work_layer or "").strip() or str(stamp_doc.get("resolved_work_layer", "")).strip()
    resolver_source = str(args.source_layer or "").strip() or str(stamp_doc.get("resolved_source_layer", "")).strip()
    resolver_intent_text = str(args.layer_intent_text or "").strip() or str(stamp_doc.get("layer_intent_text", "")).strip()

    intent = resolve_layer_intent(
        explicit_work_layer=resolver_work,
        explicit_source_layer=resolver_source,
        intent_text=resolver_intent_text,
        default_work_layer="instance",
        default_source_layer=ctx.source_domain,
    )
    resolved_work_layer = _normalize_layer_value(
        str(intent.get("resolved_work_layer", "")).strip(),
        allowed=set(ALLOWED_WORK_LAYERS),
        fallback="instance",
    )
    resolved_source_layer = _normalize_layer_value(
        str(intent.get("resolved_source_layer", "")).strip(),
        allowed=set(ALLOWED_SOURCE_LAYERS),
        fallback=ctx.source_domain if ctx.source_domain in ALLOWED_SOURCE_LAYERS else "auto",
    )

    expected_work_layer = _normalize_layer_value(
        str(args.expected_work_layer or "").strip() or resolved_work_layer,
        allowed=set(ALLOWED_WORK_LAYERS),
        fallback=resolved_work_layer,
    )
    expected_source_layer = _normalize_layer_value(
        str(args.expected_source_layer or "").strip() or resolved_source_layer,
        allowed=set(ALLOWED_SOURCE_LAYERS),
        fallback=resolved_source_layer,
    )

    parsed = parse_identity_context_stamp(stamp_line) if stamp_line else {}
    parsed_work_layer = str(parsed.get("work_layer", "")).strip() if parsed else ""
    parsed_source_layer = str(parsed.get("source_layer", "")).strip() if parsed else ""
    layer_context_present = bool(parsed.get("_has_layer_context", False)) if parsed else False

    stale_reasons: list[str] = []
    error_code = ""
    strict_operation = args.operation in STRICT_OPERATIONS

    protocol_triggered = bool(intent.get("protocol_triggered", False))
    protocol_trigger_reasons = list(intent.get("protocol_trigger_reasons") or [])

    if strict_operation and args.enforce_layer_intent_gate:
        if not stamp_line:
            stale_reasons.append("layer_intent_stamp_missing")
            error_code = ERR_LAYER_INTENT
        elif not layer_context_present:
            stale_reasons.append("layer_context_tail_missing")
            error_code = ERR_LAYER_INTENT

    if resolved_work_layer == "protocol" and not protocol_triggered:
        stale_reasons.append("protocol_layer_without_trigger")
        if strict_operation and not error_code:
            error_code = ERR_LAYER_INTENT

    if stamp_line and layer_context_present and not error_code:
        if parsed_work_layer not in ALLOWED_WORK_LAYERS:
            stale_reasons.append("parsed_work_layer_invalid")
            if strict_operation:
                error_code = ERR_LAYER_INTENT
        elif parsed_work_layer != expected_work_layer:
            stale_reasons.append("work_layer_mismatch")
            if strict_operation:
                error_code = ERR_LAYER_INTENT
        if parsed_source_layer not in ALLOWED_SOURCE_LAYERS:
            stale_reasons.append("parsed_source_layer_invalid")
            if strict_operation and not error_code:
                error_code = ERR_LAYER_INTENT
        elif parsed_source_layer != expected_source_layer:
            stale_reasons.append("source_layer_mismatch")
            if strict_operation and not error_code:
                error_code = ERR_LAYER_INTENT

    # keep source/source_layer coherence in strict operations.
    parsed_source = str(parsed.get("source", "")).strip() if parsed else ""
    if stamp_line and strict_operation and parsed_source and parsed_source_layer and parsed_source != parsed_source_layer and not error_code:
        stale_reasons.append("source_and_source_layer_mismatch")
        error_code = ERR_LAYER_INTENT

    regression = _run_regression_samples(resolved_source_layer)
    regression_status = str(regression.get("status", STATUS_FAIL_REQUIRED))
    regression_failed_ids = list(regression.get("failed_sample_ids") or [])
    if regression_failed_ids:
        stale_reasons.append("layer_intent_regression_failed:" + ",".join(regression_failed_ids))
        if strict_operation and args.enforce_layer_intent_gate and not error_code:
            error_code = ERR_LAYER_INTENT

    if not stale_reasons and str(intent.get("intent_source", "")).strip() == "default_fallback":
        fallback_reason = str(intent.get("fallback_reason", "")).strip()
        if fallback_reason:
            stale_reasons.append(f"fallback:{fallback_reason}")

    strict_fail = bool(error_code) and strict_operation
    warn_non_blocking = bool(error_code) and not strict_operation
    if strict_fail:
        status = STATUS_FAIL_REQUIRED
    elif warn_non_blocking:
        status = STATUS_WARN_NON_BLOCKING
    else:
        status = STATUS_PASS_REQUIRED

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "strict_operation": strict_operation,
        "layer_intent_resolution_status": status,
        "resolved_work_layer": resolved_work_layer,
        "resolved_source_layer": resolved_source_layer,
        "expected_work_layer": expected_work_layer,
        "expected_source_layer": expected_source_layer,
        "intent_confidence": intent.get("intent_confidence", 0.0),
        "intent_source": intent.get("intent_source", "default_fallback"),
        "fallback_reason": intent.get("fallback_reason", ""),
        "protocol_triggered": protocol_triggered,
        "protocol_trigger_reasons": protocol_trigger_reasons,
        "protocol_trigger_confidence": float(intent.get("protocol_trigger_confidence", 0.0) or 0.0),
        "strict_threshold": intent.get("strict_threshold"),
        "regression_sample_status": regression_status,
        "regression_failed_sample_ids": regression_failed_ids,
        "regression_samples": regression.get("samples", []),
        "resolver_intent_text": resolver_intent_text,
        "layer_context_present": layer_context_present,
        "parsed_work_layer": parsed_work_layer,
        "parsed_source_layer": parsed_source_layer,
        "parsed_source": parsed_source,
        "error_code": error_code,
        "stale_reasons": stale_reasons,
    }

    _emit(payload, json_only=args.json_only)
    return 1 if strict_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
