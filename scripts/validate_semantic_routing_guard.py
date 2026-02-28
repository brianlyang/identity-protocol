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


def _feedback_artifacts_present(pack_path: Path) -> bool:
    root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if not root.exists():
        return False
    for sub in ("outbox-to-protocol", "vendor-intel", "protocol-vendor-intel", "business-partner-intel"):
        d = (root / sub).resolve()
        if d.exists() and any(p.is_file() for p in d.rglob("*")):
            return True
    return any(p.is_file() for p in root.rglob("*"))


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
    if not contract and _feedback_artifacts_present(pack_path):
        required = True
        auto_required_signal = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
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
