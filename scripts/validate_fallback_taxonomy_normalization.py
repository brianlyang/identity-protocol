#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from response_stamp_common import FALLBACK_TAXONOMY_VERSION, normalize_fallback_taxonomy_class
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

ERR_UNMAPPED_REASON = "IP-FBTAX-001"
ERR_REASON_SOURCE_MISSING = "IP-FBTAX-002"
ERR_NAMESPACE_CONFLICT = "IP-FBTAX-003"

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

OBSERVATION_OPERATIONS = {
    "scan",
    "three-plane",
    "inspection",
    "validate",
}

CANONICAL_BLOCKER_TYPES = {
    "auth_login_required",
    "anti_automation_challenge_required",
    "session_reauthentication_required",
    "manual_verification_required",
}
LEGACY_BLOCKER_ALIAS_MAP = {
    "login_required": "auth_login_required",
    "captcha_required": "anti_automation_challenge_required",
    "session_expired": "session_reauthentication_required",
}

REPORT_REASON_KEYS = {"fallback_reason", "fallback_reason_raw", "layer_intent_fallback_reason"}
RAW_REASON_LINE_RE = re.compile(
    r"(?:fallback_reason_raw|fallback_reason|layer_intent_fallback_reason)\s*[:=]\s*([^\n,;]+)",
    flags=re.IGNORECASE,
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "fallback_taxonomy_normalization_contract_v1",
        "fallback_taxonomy_normalization_contract",
        "rq_022_fallback_taxonomy_normalization_contract_v1",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    umbrella = task.get("layer_intent_resolution_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("fallback_taxonomy_normalization_contract_v1")
        if isinstance(nested, dict):
            return nested
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


def _collect_reasons_from_obj(node: Any, out: list[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            lk = str(k).strip().lower()
            if lk in REPORT_REASON_KEYS:
                if isinstance(v, str) and v.strip():
                    out.append(v.strip())
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and item.strip():
                            out.append(item.strip())
            _collect_reasons_from_obj(v, out)
        return
    if isinstance(node, list):
        for item in node:
            _collect_reasons_from_obj(item, out)


def _collect_reasons_from_raw(raw: str) -> list[str]:
    rows: list[str] = []
    for m in RAW_REASON_LINE_RE.finditer(str(raw or "")):
        token = m.group(1).strip().strip("\"'").strip()
        if token:
            rows.append(token)
    return rows


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        t = str(v).strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _normalize_blocker_types(raw_blockers: list[Any]) -> list[str]:
    out: list[str] = []
    for b in raw_blockers:
        token = str(b or "").strip().lower()
        if not token:
            continue
        token = LEGACY_BLOCKER_ALIAS_MAP.get(token, token)
        out.append(token)
    return _dedupe_keep_order(out)


def _resolve_report_path(pack_path: Path, identity_id: str, explicit_report: str) -> Path | None:
    if explicit_report.strip():
        p = Path(explicit_report).expanduser().resolve()
        return p if p.exists() and p.is_file() else None
    latest = latest_identity_upgrade_report(identity_id, pack_path)
    if latest and latest.exists():
        return latest.resolve()
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate v1.6 fallback taxonomy normalization (RQ-022).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--fallback-reason", action="append", default=[])
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

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "run_profile": "observation" if args.operation in OBSERVATION_OPERATIONS else "enforcement",
        "required_contract": False,
        "auto_required_signal": False,
        "producer_readiness": False,
        "requiredization_current_round_linked": False,
        "no_fallback_event_in_current_run": False,
        "fallback_taxonomy_normalization_status": STATUS_SKIPPED_NOT_REQUIRED,
        "normalization_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "normalization_error_code": "",
        "taxonomy_version": FALLBACK_TAXONOMY_VERSION,
        "report_path": "",
        "evidence_ref": "",
        "fallback_reason_row_count": 0,
        "fallback_reason_rows": [],
        "unmapped_fallback_reasons": [],
        "fallback_reason_raw": "",
        "fallback_taxonomy_class": "",
        "blocker_taxonomy_namespace_preserved": True,
        "blocker_taxonomy_types": [],
        "stale_reasons": [],
    }

    if _is_fixture_identity(catalog_path, args.identity_id):
        payload["stale_reasons"] = ["fixture_profile_scope"]
        _emit(payload, json_only=args.json_only)
        return 0

    contract = _select_contract(task)
    required = contract_required(contract) if contract else False
    auto_required = False

    report_path = _resolve_report_path(pack_path, args.identity_id, args.report)
    explicit_current_round_linked = bool(args.fallback_reason or args.report.strip())
    if explicit_current_round_linked:
        required = True
        auto_required = True
    elif args.operation in STRICT_OPERATIONS:
        # keep strict ops signal auditable without auto-failing when there is no sample evidence.
        auto_required = False

    payload["required_contract"] = required
    payload["auto_required_signal"] = auto_required
    payload["requiredization_current_round_linked"] = explicit_current_round_linked

    reasons: list[str] = [str(x).strip() for x in (args.fallback_reason or []) if str(x).strip()]
    raw_report = ""

    if report_path is not None:
        payload["report_path"] = str(report_path)
        payload["evidence_ref"] = str(report_path)
        raw_report = report_path.read_text(encoding="utf-8", errors="ignore")
        try:
            doc = json.loads(raw_report)
            _collect_reasons_from_obj(doc, reasons)
        except Exception:
            pass
        reasons.extend(_collect_reasons_from_raw(raw_report))

    reasons = _dedupe_keep_order(reasons)
    payload["fallback_reason_row_count"] = len(reasons)
    payload["producer_readiness"] = bool(reasons)

    blocker_contract = task.get("blocker_taxonomy_contract") or {}
    blocker_types_raw = blocker_contract.get("required_blocker_types") if isinstance(blocker_contract, dict) else []
    blocker_types = _normalize_blocker_types(blocker_types_raw if isinstance(blocker_types_raw, list) else [])
    payload["blocker_taxonomy_types"] = blocker_types

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if report_path is not None and not payload["requiredization_current_round_linked"]:
        payload["producer_readiness"] = True
        payload["fallback_taxonomy_normalization_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["normalization_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["required_contract_not_applicable_no_current_round_evidence_source"]
        _emit(payload, json_only=args.json_only)
        return 0
    if report_path is None and not payload["requiredization_current_round_linked"] and args.operation in STRICT_OPERATIONS:
        payload["fallback_taxonomy_normalization_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["normalization_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["required_contract_not_applicable_no_current_round_evidence_source"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not reasons:
        if args.operation in OBSERVATION_OPERATIONS and not args.fallback_reason:
            payload["fallback_taxonomy_normalization_status"] = STATUS_SKIPPED_NOT_REQUIRED
            payload["normalization_status"] = STATUS_SKIPPED_NOT_REQUIRED
            payload["no_fallback_event_in_current_run"] = True
            payload["stale_reasons"] = ["no_fallback_event_in_current_run"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["fallback_taxonomy_normalization_status"] = STATUS_FAIL_REQUIRED
        payload["normalization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REASON_SOURCE_MISSING
        payload["normalization_error_code"] = ERR_REASON_SOURCE_MISSING
        payload["stale_reasons"] = ["fallback_reason_source_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    rows: list[dict[str, str]] = []
    unmapped: list[str] = []
    raw_overlap_blocker: list[str] = []
    for raw in reasons:
        klass = normalize_fallback_taxonomy_class(raw)
        if not klass:
            unmapped.append(raw)
        if raw.strip().lower() in CANONICAL_BLOCKER_TYPES or raw.strip().lower() in blocker_types:
            raw_overlap_blocker.append(raw)
        rows.append(
            {
                "fallback_reason_raw": raw,
                "fallback_taxonomy_class": klass,
            }
        )

    payload["fallback_reason_rows"] = rows
    if rows:
        payload["fallback_reason_raw"] = rows[0]["fallback_reason_raw"]
        payload["fallback_taxonomy_class"] = rows[0]["fallback_taxonomy_class"]
    payload["unmapped_fallback_reasons"] = _dedupe_keep_order(unmapped)

    stale_reasons: list[str] = []
    error_code = ""

    if raw_overlap_blocker:
        stale_reasons.append("fallback_reason_overlaps_blocker_taxonomy")
        error_code = ERR_NAMESPACE_CONFLICT
        payload["blocker_taxonomy_namespace_preserved"] = False

    if unmapped:
        stale_reasons.append("unmapped_fallback_reason")
        if not error_code:
            error_code = ERR_UNMAPPED_REASON

    if stale_reasons:
        payload["fallback_taxonomy_normalization_status"] = STATUS_FAIL_REQUIRED
        payload["normalization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code
        payload["normalization_error_code"] = error_code
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["fallback_taxonomy_normalization_status"] = STATUS_PASS_REQUIRED
    payload["normalization_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["normalization_error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
