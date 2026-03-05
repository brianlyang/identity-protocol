#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ERR_SEND_TIME_GATE = "IP-ASB-STAMP-SESSION-001"
ERR_SYNTHETIC_EVIDENCE = "IP-ASB-STAMP-SESSION-002"
ERR_OUTLET_GUARD_MISSING = "IP-ASB-STAMP-SESSION-003"
ERR_NON_GOVERNED_OUTLET = "IP-ASB-STAMP-SESSION-004"
ERR_RUNTIME_BINDING_MISMATCH = "IP-ASB-STAMP-SESSION-005"
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STRICT_SEND_TIME_OPERATIONS = {"activate", "update", "mutation", "readiness", "e2e", "validate", "send-time"}


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _parse_json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        doc = json.loads(text)
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def _read_stamp_payload(stamp_json_path: Path) -> dict[str, Any]:
    doc = _parse_json_payload(stamp_json_path.read_text(encoding="utf-8"))
    return doc if isinstance(doc, dict) else {}


def _read_stamp_line(stamp_json_path: Path) -> str:
    doc = _read_stamp_payload(stamp_json_path)
    return str(doc.get("external_stamp", "")).strip()


def _reply_text_from_args(args: argparse.Namespace) -> tuple[str, str]:
    """
    Returns (reply_text, evidence_mode).
    """
    if str(args.reply_text or "").strip():
        return str(args.reply_text).strip(), "reply_text"

    if str(args.reply_file or "").strip():
        p = Path(str(args.reply_file)).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"reply file not found: {p}")
        return p.read_text(encoding="utf-8", errors="ignore"), "reply_file"

    if str(args.reply_log or "").strip():
        p = Path(str(args.reply_log)).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"reply log not found: {p}")
        # pass-through mode; validator will parse the log directly.
        return "", "reply_log"

    if str(args.stamp_json or "").strip():
        p = Path(str(args.stamp_json)).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"stamp json not found: {p}")
        stamp_line = _read_stamp_line(p)
        if not stamp_line:
            return "", "stamp_json"
        business_line = str(args.business_line or "").strip() or "SEND_TIME_GATE_PROBE_BODY"
        return f"{stamp_line}\n{business_line}\n", "stamp_json_composed_reply"

    return "", "missing"


def _is_strict_send_time_context(operation: str, enforce_send_time_gate: bool) -> bool:
    op = str(operation or "").strip().lower()
    return bool(enforce_send_time_gate) or op in STRICT_SEND_TIME_OPERATIONS


def _reply_transport_ref(args: argparse.Namespace, evidence_mode: str) -> str:
    explicit = str(args.reply_transport_ref or "").strip()
    if explicit:
        return explicit
    if evidence_mode == "reply_file":
        return str(Path(str(args.reply_file or "")).expanduser().resolve())
    if evidence_mode == "reply_log":
        return str(Path(str(args.reply_log or "")).expanduser().resolve())
    if evidence_mode == "reply_text":
        return "inline:reply_text"
    if evidence_mode in {"stamp_json", "stamp_json_composed_reply"}:
        return str(Path(str(args.stamp_json or "")).expanduser().resolve())
    return "unresolved"


def _is_governed_outlet(channel_id: str) -> bool:
    cid = str(channel_id or "").strip().lower()
    if not cid:
        return False
    return cid.startswith("governed_") or cid.startswith("governed-") or cid in {"governed", "governedoutlet"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Unified send-time gate for governed user-visible reply channel. "
            "Fails closed on missing first-line Identity-Context and emits blocker receipt."
        )
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--reply-text", default="")
    ap.add_argument("--reply-file", default="")
    ap.add_argument("--reply-log", default="")
    ap.add_argument("--stamp-json", default="", help="optional fallback to compose send-time reply from external_stamp")
    ap.add_argument("--reply-transport-ref", default="")
    ap.add_argument(
        "--outlet-channel-id",
        default="governed_adapter_v1",
        help="logical reply outlet channel id; strict operations require governed_* channel",
    )
    ap.add_argument("--reply-outlet-guard-applied", action="store_true")
    ap.add_argument("--business-line", default="SEND_TIME_GATE_PROBE_BODY")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--enforce-send-time-gate", action="store_true")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument(
        "--operation",
        choices=[
            "activate",
            "update",
            "mutation",
            "readiness",
            "e2e",
            "ci",
            "validate",
            "scan",
            "three-plane",
            "inspection",
            "send-time",
        ],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if catalog_path.exists() and _is_fixture_identity(catalog_path, args.identity_id):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": False,
            "send_time_gate_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "reply_first_line_status": STATUS_SKIPPED_NOT_REQUIRED,
            "reply_evidence_mode": "fixture_skip",
            "reply_transport_ref": "",
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": False,
            "outlet_channel_id": str(args.outlet_channel_id or "").strip() or "governed_adapter_v1",
            "outlet_preflight_receipt": "",
            "outlet_bypass_detected": False,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 0,
            "reply_first_line_missing_refs": [],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "fixture_profile_scope",
            "fallback_reason": "fixture_profile_scope",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": ["fixture_profile_scope"],
            "upstream_validator_rc": 0,
        }
        _emit(payload, json_only=args.json_only)
        return 0

    try:
        reply_text, evidence_mode = _reply_text_from_args(args)
    except Exception as exc:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
            "operation": args.operation,
            "send_time_gate_status": STATUS_FAIL_REQUIRED if args.enforce_send_time_gate else STATUS_WARN_NON_BLOCKING,
            "error_code": ERR_SEND_TIME_GATE,
            "reply_evidence_mode": "invalid_input",
            "reply_transport_ref": "invalid_input",
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["input:missing_or_invalid"],
            "blocker_receipt_path": "",
            "stale_reasons": [f"send_time_input_invalid:{exc}"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    strict_context = _is_strict_send_time_context(args.operation, args.enforce_send_time_gate)
    reply_transport_ref = _reply_transport_ref(args, evidence_mode)
    outlet_channel_id = str(args.outlet_channel_id or "").strip() or "governed_adapter_v1"
    governed_outlet = _is_governed_outlet(outlet_channel_id)
    strict_outlet_enforced = strict_context and governed_outlet and bool(args.reply_outlet_guard_applied)
    preflight_receipt_ref = str(Path(args.blocker_receipt_out).expanduser().resolve()) if str(args.blocker_receipt_out or "").strip() else ""

    if strict_context and not governed_outlet:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_NON_GOVERNED_OUTLET,
            "reply_first_line_status": STATUS_FAIL_REQUIRED,
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": strict_outlet_enforced,
            "outlet_channel_id": outlet_channel_id,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["non_governed_outlet_channel"],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "strict_send_time_guard",
            "fallback_reason": "non_governed_outlet_channel",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": ["strict_send_time_non_governed_outlet_forbidden"],
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    if strict_context and evidence_mode in {"reply_text", "stamp_json", "stamp_json_composed_reply", "missing"}:
        synthetic_reason = (
            "strict_send_time_inline_reply_text_forbidden"
            if evidence_mode == "reply_text"
            else "strict_send_time_synthetic_evidence_forbidden"
        )
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_SYNTHETIC_EVIDENCE,
            "reply_first_line_status": STATUS_FAIL_REQUIRED,
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": strict_outlet_enforced,
            "outlet_channel_id": outlet_channel_id,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["strict_evidence_source_not_live"],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "strict_send_time_guard",
            "fallback_reason": "synthetic_reply_evidence_forbidden",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": [synthetic_reason],
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1
    if strict_context and not bool(args.reply_outlet_guard_applied):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_OUTLET_GUARD_MISSING,
            "reply_first_line_status": STATUS_FAIL_REQUIRED,
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": False,
            "governed_outlet_enforced": False,
            "outlet_channel_id": outlet_channel_id,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["reply_outlet_guard_not_applied"],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "strict_send_time_guard",
            "fallback_reason": "reply_outlet_guard_missing",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": ["strict_send_time_outlet_guard_missing"],
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    expected_work_layer = str(args.expected_work_layer or "").strip()
    expected_source_layer = str(args.expected_source_layer or "").strip()
    layer_intent_text = str(args.layer_intent_text or "").strip()
    stamp_payload: dict[str, Any] = {}
    if str(args.stamp_json or "").strip():
        stamp_path = Path(str(args.stamp_json)).expanduser().resolve()
        if stamp_path.exists():
            stamp_payload = _read_stamp_payload(stamp_path)
    if not expected_work_layer:
        expected_work_layer = str(stamp_payload.get("resolved_work_layer", "")).strip() or str(
            stamp_payload.get("work_layer", "")
        ).strip()
    if not expected_source_layer:
        expected_source_layer = str(stamp_payload.get("resolved_source_layer", "")).strip() or str(
            stamp_payload.get("source_layer", "")
        ).strip()
    if not layer_intent_text:
        layer_intent_text = str(stamp_payload.get("layer_intent_text", "")).strip()

    op_for_validator = "validate" if args.operation == "send-time" else args.operation
    cmd = [
        sys.executable,
        "scripts/validate_reply_identity_context_first_line.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        op_for_validator,
        "--json-only",
    ]
    if str(args.actor_id or "").strip():
        cmd.extend(["--actor-id", str(args.actor_id).strip()])
    if args.force_check:
        cmd.append("--force-check")
    if args.enforce_send_time_gate:
        cmd.append("--enforce-first-line-gate")
    if str(args.blocker_receipt_out or "").strip():
        cmd.extend(["--blocker-receipt-out", str(args.blocker_receipt_out).strip()])
    if expected_work_layer:
        cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        cmd.extend(["--expected-source-layer", expected_source_layer])
    if layer_intent_text:
        cmd.extend(["--layer-intent-text", layer_intent_text])
    if evidence_mode == "reply_log":
        cmd.extend(["--reply-log", str(args.reply_log).strip()])
    elif reply_text:
        cmd.extend(["--reply-text", reply_text])

    p = subprocess.run(cmd, capture_output=True, text=True)
    validator_payload = _parse_json_payload(p.stdout)

    first_line_status = str(validator_payload.get("reply_first_line_status", "")).strip() or (
        STATUS_PASS_REQUIRED if p.returncode == 0 else STATUS_FAIL_REQUIRED
    )
    error_code = str(validator_payload.get("error_code", "")).strip()
    if p.returncode != 0 and not error_code:
        error_code = ERR_SEND_TIME_GATE

    send_time_status = first_line_status
    if send_time_status not in {
        STATUS_PASS_REQUIRED,
        STATUS_FAIL_REQUIRED,
        STATUS_SKIPPED_NOT_REQUIRED,
        STATUS_WARN_NON_BLOCKING,
    }:
        send_time_status = STATUS_PASS_REQUIRED if p.returncode == 0 else STATUS_FAIL_REQUIRED

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        "operation": args.operation,
        "validator_operation": op_for_validator,
        "send_time_gate_enforced": bool(args.enforce_send_time_gate),
        "required_contract": bool(validator_payload.get("required_contract", False)),
        "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
        "governed_outlet_enforced": strict_outlet_enforced,
        "outlet_channel_id": outlet_channel_id,
        "outlet_preflight_receipt": preflight_receipt_ref,
        "outlet_bypass_detected": bool(
            (strict_context and not governed_outlet)
            or (strict_context and not bool(args.reply_outlet_guard_applied))
            or str(error_code).strip() == ERR_NON_GOVERNED_OUTLET
        ),
        "expected_work_layer": expected_work_layer,
        "expected_source_layer": expected_source_layer,
        "layer_intent_text": layer_intent_text,
        "send_time_gate_status": send_time_status,
        "error_code": error_code,
        "reply_first_line_status": first_line_status,
        "reply_evidence_mode": evidence_mode,
        "reply_transport_ref": reply_transport_ref,
        "reply_evidence_ref": validator_payload.get("reply_evidence_ref", ""),
        "reply_sample_count": validator_payload.get("reply_sample_count", 0),
        "reply_first_line_missing_count": validator_payload.get("reply_first_line_missing_count", 0),
        "reply_first_line_missing_refs": validator_payload.get("reply_first_line_missing_refs", []),
        "expected_identity_id": validator_payload.get("expected_identity_id", ""),
        "reply_first_line_work_layer": validator_payload.get("reply_first_line_work_layer", ""),
        "reply_first_line_source_layer": validator_payload.get("reply_first_line_source_layer", ""),
        "expected_source_layer_input": validator_payload.get("expected_source_layer_input", ""),
        "expected_source_layer_effective": validator_payload.get("expected_source_layer_effective", ""),
        "expected_source_layer_validation_status": validator_payload.get("expected_source_layer_validation_status", ""),
        "expected_source_layer_validation_error_code": validator_payload.get("expected_source_layer_validation_error_code", ""),
        "source_layer_downgrade_applied": validator_payload.get("source_layer_downgrade_applied", False),
        "layer_intent_resolution_status": validator_payload.get("layer_intent_resolution_status", ""),
        "resolved_work_layer": validator_payload.get("resolved_work_layer", ""),
        "resolved_source_layer": validator_payload.get("resolved_source_layer", ""),
        "intent_confidence": validator_payload.get("intent_confidence"),
        "intent_source": validator_payload.get("intent_source", ""),
        "fallback_reason": validator_payload.get("fallback_reason", ""),
        "protocol_triggered": bool(validator_payload.get("protocol_triggered", False)),
        "protocol_trigger_reasons": validator_payload.get("protocol_trigger_reasons", []),
        "protocol_trigger_confidence": validator_payload.get("protocol_trigger_confidence", 0.0),
        "blocker_receipt_path": validator_payload.get("blocker_receipt_path", ""),
        "stale_reasons": validator_payload.get("stale_reasons", []),
        "upstream_validator_rc": p.returncode,
    }
    if str(error_code).strip() == ERR_RUNTIME_BINDING_MISMATCH:
        payload["outlet_bypass_detected"] = True
    if "blocker_receipt" in validator_payload:
        payload["blocker_receipt"] = validator_payload.get("blocker_receipt")

    _emit(payload, json_only=args.json_only)
    return 1 if p.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
