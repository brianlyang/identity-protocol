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

ERR_BUSINESS_LEAK = "IP-DSN-001"
ERR_SENSITIVE_CONSTANT = "IP-DSN-002"

INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}

REQ_CONTRACT_KEYS = (
    "required",
    "feedback_batch_path_pattern",
    "enforcement_validator",
)

# Generic governance-focused leak patterns (protocol-layer must stay business-neutral).
DEFAULT_FORBIDDEN_KEY_PATTERNS = (
    r"(^|[._])(customer|tenant|client|account)(_id|_name|_profile)?$",
    r"(^|[._])(business|platform|domain)(_scenario|_sample|_keyword|_threshold|_policy)$",
    r"(^|[._])(order|product|sku|shop|store|merchant)(_id|_name|_sample)?$",
)

DEFAULT_SENSITIVE_PATTERNS = (
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",  # email
    r"\b(?:\+?\d[\d\-\s]{8,}\d)\b",  # phone-like number
    r"\bAKIA[0-9A-Z]{16}\b",  # AWS-like key
    r"\bsk-[A-Za-z0-9]{20,}\b",  # model/api token style
    r'(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|secret)\b\s*[:=]\s*["\']?[A-Za-z0-9_\-]{8,}',
)

EXEMPT_DOMAIN_TERMS = {
    "business_partner",
    "protocol_vendor",
    "intent_domain",
    "intent_domain_before",
    "intent_domain_after",
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_data_sanitization_boundary_v1",
        "protocol_data_sanitization_boundary_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c

    umbrella = task.get("semantic_isolation_and_source_trust_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("protocol_data_sanitization_boundary_v1")
        if isinstance(nested, dict):
            return nested
    return {}


def _feedback_artifacts_present(pack_path: Path) -> bool:
    root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if not root.exists():
        return False
    return any(p.is_file() for p in root.rglob("*"))


def _walk_json(obj: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k)
            cur = f"{path}.{key}"
            rows.append((path, key, v))
            rows.extend(_walk_json(v, cur))
    elif isinstance(obj, list):
        for idx, v in enumerate(obj):
            rows.extend(_walk_json(v, f"{path}[{idx}]"))
    return rows


def _normalize_patterns(raw: Any, defaults: tuple[str, ...]) -> list[re.Pattern[str]]:
    items: list[str] = []
    if isinstance(raw, list) and raw:
        for x in raw:
            token = str(x).strip()
            if token:
                items.append(token)
    else:
        items = list(defaults)
    out: list[re.Pattern[str]] = []
    for pat in items:
        try:
            out.append(re.compile(pat, flags=re.IGNORECASE))
        except Exception:
            continue
    return out


def _stringify(v: Any) -> str:
    if isinstance(v, str):
        return v
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        return str(v)


def _contains_exempt_term(text: str) -> bool:
    low = text.lower()
    return any(term in low for term in EXEMPT_DOMAIN_TERMS)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol data sanitization boundary for closure payloads.")
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
        "protocol_data_sanitization_boundary_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "feedback_batch_path": "",
        "forbidden_key_hits": [],
        "sensitive_pattern_hits": [],
        "violation_count": 0,
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    missing_contract = [k for k in REQ_CONTRACT_KEYS if k not in contract]
    if contract and missing_contract:
        payload["protocol_data_sanitization_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_BUSINESS_LEAK
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
        payload["error_code"] = ERR_BUSINESS_LEAK
        payload["stale_reasons"] = ["feedback_batch_not_found"]
        if args.operation in INSPECTION_OPERATIONS:
            payload["protocol_data_sanitization_boundary_status"] = STATUS_SKIPPED_NOT_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 0
        payload["protocol_data_sanitization_boundary_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    payload["feedback_batch_path"] = str(batch_path)
    raw = batch_path.read_text(encoding="utf-8", errors="ignore")

    parsed: dict[str, Any] = {}
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            parsed = obj
    except Exception:
        parsed = {}

    key_patterns = _normalize_patterns(contract.get("forbidden_key_patterns"), DEFAULT_FORBIDDEN_KEY_PATTERNS)
    sensitive_patterns = _normalize_patterns(contract.get("sensitive_value_patterns"), DEFAULT_SENSITIVE_PATTERNS)

    forbidden_key_hits: list[dict[str, Any]] = []
    sensitive_hits: list[dict[str, Any]] = []

    if parsed:
        for ppath, key, val in _walk_json(parsed):
            k_low = key.lower()
            if k_low in EXEMPT_DOMAIN_TERMS:
                continue
            # key-level business leakage
            for pat in key_patterns:
                if pat.search(key):
                    sval = _stringify(val)
                    if sval.strip() and not _contains_exempt_term(sval):
                        forbidden_key_hits.append(
                            {
                                "path": f"{ppath}.{key}",
                                "key": key,
                                "value_preview": sval[:120],
                                "pattern": pat.pattern,
                            }
                        )
                    break

            sval = _stringify(val)
            if not sval.strip():
                continue
            # sensitive constants leak
            for pat in sensitive_patterns:
                if pat.search(sval):
                    sensitive_hits.append(
                        {
                            "path": f"{ppath}.{key}",
                            "key": key,
                            "value_preview": sval[:120],
                            "pattern": pat.pattern,
                        }
                    )
                    break

    # text-level scan as fallback (for markdown/plain batches)
    lines = raw.splitlines()
    for idx, line in enumerate(lines, start=1):
        l = line.strip()
        if not l:
            continue
        if _contains_exempt_term(l):
            continue
        for pat in sensitive_patterns:
            if pat.search(l):
                sensitive_hits.append(
                    {
                        "path": f"line:{idx}",
                        "key": "",
                        "value_preview": l[:120],
                        "pattern": pat.pattern,
                    }
                )
                break

    # deterministic de-dup and cap output size
    def _dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, str, str]] = set()
        out: list[dict[str, Any]] = []
        for it in items:
            sig = (str(it.get("path", "")), str(it.get("pattern", "")), str(it.get("value_preview", "")))
            if sig in seen:
                continue
            seen.add(sig)
            out.append(it)
        return out

    forbidden_key_hits = _dedupe(forbidden_key_hits)
    sensitive_hits = _dedupe(sensitive_hits)

    stale_reasons: list[str] = []
    error_code = ""
    if forbidden_key_hits:
        stale_reasons.append("business_or_tenant_key_leak_detected")
        error_code = ERR_BUSINESS_LEAK
    if sensitive_hits:
        stale_reasons.append("sensitive_constant_detected")
        if not error_code:
            error_code = ERR_SENSITIVE_CONSTANT

    payload["forbidden_key_hits"] = forbidden_key_hits[:30]
    payload["sensitive_pattern_hits"] = sensitive_hits[:30]
    payload["violation_count"] = len(forbidden_key_hits) + len(sensitive_hits)

    if stale_reasons:
        payload["protocol_data_sanitization_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_BUSINESS_LEAK
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["protocol_data_sanitization_boundary_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
