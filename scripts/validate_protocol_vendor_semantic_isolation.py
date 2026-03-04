#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task, resolve_report_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CONTRACT_FIELDS = "IP-SEM-001"
ERR_FEEDBACK_BATCH_MISSING = "IP-SEM-001"
ERR_CROSS_DOMAIN_WITHOUT_SWITCH = "IP-SEM-005"
ERR_MIXED_DOMAIN_SPLIT_MISSING = "IP-SEM-002"
ERR_SWITCH_RECEIPT_INVALID = "IP-SEM-005"
ERR_DOMAIN_INVALID = "IP-SEM-004"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}

REQ_CONTRACT_KEYS = (
    "required",
    "feedback_batch_path_pattern",
    "switch_receipt_required",
    "enforcement_validator",
)
DEFAULT_DOMAIN_ENUM = ("protocol_vendor", "business_partner", "mixed", "unknown")
REQUIRED_SWITCH_FIELDS = ("trigger_text", "intent_domain_before", "intent_domain_after", "intent_confidence")


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_vendor_semantic_isolation_contract_v1",
        "protocol_vendor_semantic_isolation_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c

    umbrella = task.get("semantic_isolation_and_source_trust_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("protocol_vendor_semantic_isolation_contract_v1")
        if isinstance(nested, dict):
            return nested
    return {}


def _feedback_artifacts_present(pack_path: Path) -> bool:
    root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if not root.exists():
        return False
    for sub in ("outbox-to-protocol", "protocol-vendor-intel", "business-partner-intel"):
        d = (root / sub).resolve()
        if d.exists() and any(p.is_file() for p in d.rglob("*")):
            return True
    return any(p.is_file() for p in root.rglob("*"))


def _extract_first(text: str, pattern: str) -> str:
    m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else ""


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _collect_refs(raw: str, namespace: str) -> list[str]:
    refs: list[str] = []
    ns = namespace.lower()
    for m in re.finditer(r"`([^`]+)`", raw):
        token = m.group(1).strip()
        if ns in token.lower():
            refs.append(token)
    for m in re.finditer(r"(?im)^[\s\-*0-9.]+([^\n]+)$", raw):
        token = m.group(1).strip()
        if ns in token.lower():
            refs.append(token)
    return sorted(set(refs))


def _extract_payload(feedback_path: Path) -> tuple[dict[str, Any], str]:
    raw = feedback_path.read_text(encoding="utf-8", errors="ignore")
    parsed: dict[str, Any] = {}
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            parsed = obj
    except Exception:
        parsed = {}

    domain_switch: dict[str, Any] = {}
    maybe_switch = parsed.get("domain_switch_receipt")
    if isinstance(maybe_switch, dict):
        domain_switch = maybe_switch

    intent_domain = str(parsed.get("intent_domain", "")).strip().lower()
    if not intent_domain:
        intent_domain = _extract_first(raw, r"\bintent_domain\b\s*[:=]\s*([a-zA-Z_]+)").lower()

    trigger_text = str(domain_switch.get("trigger_text") or parsed.get("trigger_text") or "").strip()
    if not trigger_text:
        trigger_text = _extract_first(raw, r"\btrigger_text\b\s*[:=]\s*(.+)$")

    before = str(domain_switch.get("intent_domain_before") or parsed.get("intent_domain_before") or "").strip().lower()
    if not before:
        before = _extract_first(raw, r"\bintent_domain_before\b\s*[:=]\s*([a-zA-Z_]+)").lower()

    after = str(domain_switch.get("intent_domain_after") or parsed.get("intent_domain_after") or "").strip().lower()
    if not after:
        after = _extract_first(raw, r"\bintent_domain_after\b\s*[:=]\s*([a-zA-Z_]+)").lower()

    confidence_raw = domain_switch.get("intent_confidence")
    if confidence_raw is None:
        confidence_raw = parsed.get("intent_confidence")
    if confidence_raw is None:
        confidence_raw = _extract_first(raw, r"\bintent_confidence\b\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)")
    confidence = _to_float(confidence_raw)

    approved_by = str(domain_switch.get("approved_by") or parsed.get("approved_by") or "").strip()
    if not approved_by:
        approved_by = _extract_first(raw, r"\bapproved_by\b\s*[:=]\s*(.+)$")

    payload = {
        "intent_domain": intent_domain,
        "switch_receipt": {
            "trigger_text": trigger_text,
            "intent_domain_before": before,
            "intent_domain_after": after,
            "intent_confidence": confidence,
            "approved_by": approved_by,
        },
        "parsed": parsed,
    }
    return payload, raw


def _contains_manual_override(raw: str) -> bool:
    low = raw.lower()
    return any(token in low for token in ("manual override", "explicit override", "override receipt", "manual approval"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-vendor semantic isolation contract for conclusion-layer feedback.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--feedback-batch", default="")
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
    required = contract_required(contract) if contract else False
    auto_required_signal = False
    if not required and _feedback_artifacts_present(pack_path):
        required = True
        auto_required_signal = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "protocol_vendor_semantic_isolation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "feedback_batch_path": "",
        "intent_domain": "",
        "intent_confidence": None,
        "intent_domain_before": "",
        "intent_domain_after": "",
        "switch_receipt_required": True,
        "switch_receipt_present": False,
        "switch_receipt_fields": {},
        "protocol_vendor_refs": [],
        "business_partner_refs": [],
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    missing_contract = [k for k in REQ_CONTRACT_KEYS if k not in contract]
    if contract and missing_contract:
        payload["protocol_vendor_semantic_isolation_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_FIELDS
        payload["stale_reasons"] = [f"contract_missing_fields:{','.join(missing_contract)}"]
        _emit(payload, json_only=args.json_only)
        return 1

    switch_receipt_required = bool(contract.get("switch_receipt_required", True))
    payload["switch_receipt_required"] = switch_receipt_required

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
        payload["error_code"] = ERR_FEEDBACK_BATCH_MISSING
        payload["stale_reasons"] = ["feedback_batch_not_found"]
        if args.operation in INSPECTION_OPERATIONS:
            payload["protocol_vendor_semantic_isolation_status"] = STATUS_SKIPPED_NOT_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 0
        payload["protocol_vendor_semantic_isolation_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    parsed_payload, raw = _extract_payload(batch_path)
    intent_domain = str(parsed_payload.get("intent_domain", "")).strip().lower()
    receipt = parsed_payload.get("switch_receipt", {}) if isinstance(parsed_payload.get("switch_receipt"), dict) else {}

    protocol_vendor_refs = _collect_refs(raw, "protocol-vendor-intel/")
    business_partner_refs = _collect_refs(raw, "business-partner-intel/")

    payload["feedback_batch_path"] = str(batch_path)
    payload["intent_domain"] = intent_domain
    payload["intent_confidence"] = receipt.get("intent_confidence")
    payload["intent_domain_before"] = str(receipt.get("intent_domain_before", ""))
    payload["intent_domain_after"] = str(receipt.get("intent_domain_after", ""))
    payload["switch_receipt_fields"] = receipt
    payload["protocol_vendor_refs"] = protocol_vendor_refs
    payload["business_partner_refs"] = business_partner_refs

    domain_enum = contract.get("domain_enum")
    if not isinstance(domain_enum, list) or not domain_enum:
        domain_enum = list(DEFAULT_DOMAIN_ENUM)
    domain_enum_set = {str(x).strip().lower() for x in domain_enum if str(x).strip()}

    stale_reasons: list[str] = []
    error_code = ""

    if intent_domain and intent_domain not in domain_enum_set:
        stale_reasons.append("intent_domain_not_in_whitelist")
        error_code = ERR_DOMAIN_INVALID

    missing_receipt_fields = [k for k in REQUIRED_SWITCH_FIELDS if not str(receipt.get(k, "")).strip()]
    if receipt.get("intent_confidence") is None:
        if "intent_confidence" not in missing_receipt_fields:
            missing_receipt_fields.append("intent_confidence")
    conf = receipt.get("intent_confidence")
    if conf is not None and isinstance(conf, (int, float)) and not (0.0 <= float(conf) <= 1.0):
        stale_reasons.append("intent_confidence_out_of_range")
        error_code = ERR_SWITCH_RECEIPT_INVALID

    switch_receipt_present = len(missing_receipt_fields) == 0
    payload["switch_receipt_present"] = switch_receipt_present

    if _contains_manual_override(raw) and not str(receipt.get("approved_by", "")).strip():
        stale_reasons.append("manual_override_without_approved_by")
        if not error_code:
            error_code = ERR_SWITCH_RECEIPT_INVALID

    has_protocol = len(protocol_vendor_refs) > 0
    has_business = len(business_partner_refs) > 0

    cross_domain_without_switch = False
    if intent_domain == "protocol_vendor" and has_business:
        if switch_receipt_required and not switch_receipt_present:
            cross_domain_without_switch = True
    elif intent_domain == "business_partner" and has_protocol:
        if switch_receipt_required and not switch_receipt_present:
            cross_domain_without_switch = True
    elif has_protocol and has_business and intent_domain not in {"mixed", "unknown"}:
        if switch_receipt_required and not switch_receipt_present:
            cross_domain_without_switch = True

    if cross_domain_without_switch:
        stale_reasons.append("cross_domain_behavior_without_switch_receipt")
        error_code = ERR_CROSS_DOMAIN_WITHOUT_SWITCH

    if intent_domain == "mixed":
        if not (has_protocol and has_business):
            stale_reasons.append("mixed_domain_without_split_outputs")
            error_code = ERR_MIXED_DOMAIN_SPLIT_MISSING
        if switch_receipt_required and not switch_receipt_present:
            stale_reasons.append("mixed_domain_without_switch_receipt")
            if not error_code:
                error_code = ERR_MIXED_DOMAIN_SPLIT_MISSING

    if switch_receipt_required and not switch_receipt_present and (has_protocol and has_business):
        if "cross_domain_behavior_without_switch_receipt" not in stale_reasons:
            stale_reasons.append("cross_domain_behavior_without_switch_receipt")
        if not error_code:
            error_code = ERR_CROSS_DOMAIN_WITHOUT_SWITCH

    if switch_receipt_required and (has_protocol or has_business):
        before = str(receipt.get("intent_domain_before", "")).strip().lower()
        after = str(receipt.get("intent_domain_after", "")).strip().lower()
        if switch_receipt_present and before and after and before == after:
            stale_reasons.append("switch_receipt_before_after_identical")
            if not error_code:
                error_code = ERR_SWITCH_RECEIPT_INVALID
        if switch_receipt_required and not switch_receipt_present and missing_receipt_fields and (intent_domain == "mixed"):
            stale_reasons.append(f"switch_receipt_missing_fields:{','.join(sorted(set(missing_receipt_fields)))}")
            if not error_code:
                error_code = ERR_SWITCH_RECEIPT_INVALID

    if stale_reasons:
        payload["protocol_vendor_semantic_isolation_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_CROSS_DOMAIN_WITHOUT_SWITCH
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["protocol_vendor_semantic_isolation_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
