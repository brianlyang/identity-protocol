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
    should_seed_default_correlation_keys,
)
from response_stamp_common import resolve_layer_intent
from tool_vendor_governance_common import contract_required, load_json, load_yaml, resolve_pack_and_task, resolve_report_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_UNKNOWN_IN_CONCLUSION = "IP-SRC-001"
ERR_REQUIRED_TRACE_MISSING = "IP-SRC-002"
ERR_SOURCE_METADATA_INCOMPLETE = "IP-SRC-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}

REQ_CONTRACT_KEYS = (
    "required",
    "feedback_batch_path_pattern",
    "allowed_trust_tiers",
    "conclusion_required_tiers",
    "enforcement_validator",
)
DEFAULT_ALLOWED_TIERS = ("official", "primary", "secondary", "unknown")
DEFAULT_CONCLUSION_REQUIRED_TIERS = ("official", "primary")

URL_RE = re.compile(r"https?://[^\s)\]>]+", flags=re.IGNORECASE)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "external_source_trust_chain_contract_v1",
        "external_source_trust_chain_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c

    umbrella = task.get("semantic_isolation_and_source_trust_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("external_source_trust_chain_contract_v1")
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


def _feedback_artifacts_present(pack_path: Path) -> bool:
    root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if not root.exists():
        return False
    return any(p.is_file() for p in root.rglob("*"))


def _select_correlated_feedback_batch(pack_path: Path, correlated_refs: list[str]) -> Path | None:
    if not correlated_refs:
        return None
    root = (pack_path / "runtime" / "protocol-feedback").resolve()
    candidates: list[Path] = []
    for rel in correlated_refs:
        token = str(rel or "").strip().replace("\\", "/")
        if not token:
            continue
        p = (root / token).resolve()
        if p.is_file() and p.name.startswith("FEEDBACK_BATCH_"):
            candidates.append(p)
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.stat().st_mtime)
    return candidates[-1]


def _extract_first(text: str, pattern: str) -> str:
    m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else ""


def _normalize_tier(v: Any) -> str:
    return str(v or "").strip().lower()


def _normalize_scope(v: Any) -> str:
    s = str(v or "").strip().lower()
    if s in {"conclusion", "final", "closure", "conclusion_layer"}:
        return "conclusion"
    if s in {"candidate", "lead", "exploration", "candidate_lead"}:
        return "candidate"
    return s or "unknown"


def _to_rows_from_json(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates: list[tuple[str, Any]] = []
    for key in (
        "external_sources",
        "source_rows",
        "sources",
        "evidence_sources",
        "references",
        "citations",
    ):
        val = doc.get(key)
        if isinstance(val, list):
            candidates.append((key, val))

    for key, arr in candidates:
        for idx, item in enumerate(arr):
            if not isinstance(item, dict):
                continue
            tier = _normalize_tier(item.get("trust_tier") or item.get("tier"))
            scope = _normalize_scope(item.get("scope") or item.get("statement_scope") or item.get("section"))
            ref = str(item.get("ref") or item.get("url") or item.get("source") or "").strip()
            note = str(item.get("downgrade_note") or item.get("note") or "").strip()
            follow = str(item.get("follow_up") or item.get("follow_up_action") or "").strip()
            rows.append(
                {
                    "origin": f"json:{key}[{idx}]",
                    "tier": tier,
                    "scope": scope,
                    "ref": ref,
                    "downgrade_note": note,
                    "follow_up_action": follow,
                }
            )
    return rows


def _to_rows_from_text(raw: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(raw.splitlines(), start=1):
        l = line.strip()
        if not l:
            continue
        low = l.lower()
        if not any(x in low for x in ("trust_tier", "source_tier", "tier=", "tier:", "official", "primary", "secondary", "unknown")):
            continue

        tier = _extract_first(l, r"(?:trust_tier|source_tier|tier)\s*[:=]\s*([a-zA-Z_]+)")
        if not tier:
            for cand in ("official", "primary", "secondary", "unknown"):
                if re.search(rf"\b{cand}\b", low):
                    tier = cand
                    break
        scope = _extract_first(l, r"(?:scope|section|statement_scope)\s*[:=]\s*([a-zA-Z_]+)")
        if not scope:
            if "conclusion" in low or "final" in low or "closure" in low:
                scope = "conclusion"
            elif "candidate" in low or "lead" in low:
                scope = "candidate"

        urls = URL_RE.findall(l)
        ref = urls[0] if urls else ""
        note = ""
        follow = ""
        if "downgrade" in low or "unverified" in low or "tentative" in low:
            note = l
        if "follow-up" in low or "follow up" in low or "retrieve" in low or "official" in low:
            follow = l

        rows.append(
            {
                "origin": f"line:{idx}",
                "tier": _normalize_tier(tier),
                "scope": _normalize_scope(scope),
                "ref": ref,
                "downgrade_note": note,
                "follow_up_action": follow,
            }
        )
    return rows


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    out: list[dict[str, Any]] = []
    for r in rows:
        key = (
            str(r.get("tier", "")),
            str(r.get("scope", "")),
            str(r.get("ref", "")),
            str(r.get("origin", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate external source trust-chain contract for conclusion-layer evidence.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--feedback-batch", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--correlation-key", action="append", default=[])
    ap.add_argument("--activity-window-hours", type=float, default=72.0)
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
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

    if _is_fixture_identity(catalog_path, args.identity_id):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "resolved_pack_path": str(pack_path),
            "operation": args.operation,
            "required_contract": False,
            "auto_required_signal": False,
            "external_source_trust_chain_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "feedback_batch_path": "",
            "allowed_trust_tiers": list(DEFAULT_ALLOWED_TIERS),
            "conclusion_required_tiers": list(DEFAULT_CONCLUSION_REQUIRED_TIERS),
            "source_row_count": 0,
            "conclusion_source_count": 0,
            "candidate_source_count": 0,
            "unknown_in_conclusion_refs": [],
            "missing_tier_refs": [],
            "missing_trace_refs": [],
            "unknown_candidate_without_downgrade": [],
            "stale_reasons": ["fixture_profile_scope"],
        }
        _emit(payload, json_only=args.json_only)
        return 0

    contract = _select_contract(task)
    required_declared = contract_required(contract) if contract else False
    layer_intent = resolve_layer_intent(
        explicit_work_layer=str(args.expected_work_layer or "").strip(),
        explicit_source_layer=str(args.expected_source_layer or "").strip(),
        intent_text=str(args.layer_intent_text or "").strip(),
        default_work_layer="instance",
        default_source_layer="project",
    )
    run_id = str(args.run_id or "").strip()
    explicit_corr_keys = list(args.correlation_key or [])
    default_seeded = should_seed_default_correlation_keys(
        operation=args.operation,
        run_id=run_id,
        explicit_keys=explicit_corr_keys,
    )
    default_corr = discover_default_correlation_keys(pack_path)
    correlation_keys = build_correlation_keys(
        default_keys=(default_corr.get("correlation_keys", []) if default_seeded else []),
        run_id=run_id,
        explicit_keys=explicit_corr_keys,
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
        "intent_confidence_resolver": layer_intent.get("intent_confidence"),
        "fallback_reason": str(layer_intent.get("fallback_reason", "")),
        "default_correlation_seeded": default_seeded,
        "default_correlation_run_id": str(default_corr.get("latest_run_id", "")),
        "default_correlation_report": str(default_corr.get("latest_report_path", "")),
        "correlation_keys": correlation_keys,
        "external_source_trust_chain_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "feedback_batch_path": "",
        "allowed_trust_tiers": list(DEFAULT_ALLOWED_TIERS),
        "conclusion_required_tiers": list(DEFAULT_CONCLUSION_REQUIRED_TIERS),
        "source_row_count": 0,
        "conclusion_source_count": 0,
        "candidate_source_count": 0,
        "unknown_in_conclusion_refs": [],
        "missing_tier_refs": [],
        "missing_trace_refs": [],
        "unknown_candidate_without_downgrade": [],
        "stale_reasons": [],
    }

    if not required:
        if auto_required_candidate and bool(activity.get("requiredization_historical_activity_detected", False)):
            payload["stale_reasons"] = ["contract_not_required_due_lane_scope_history_only_activity"]
        else:
            payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if (
        args.operation in INSPECTION_OPERATIONS
        and not bool(payload.get("requiredization_current_round_linked", False))
        and not str(args.feedback_batch or "").strip()
    ):
        payload["external_source_trust_chain_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["error_code"] = ""
        payload["stale_reasons"] = ["required_contract_not_applicable_no_current_round_evidence_source"]
        _emit(payload, json_only=args.json_only)
        return 0

    missing_contract = [k for k in REQ_CONTRACT_KEYS if k not in contract]
    if contract and missing_contract:
        payload["external_source_trust_chain_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SOURCE_METADATA_INCOMPLETE
        payload["stale_reasons"] = [f"contract_missing_fields:{','.join(missing_contract)}"]
        _emit(payload, json_only=args.json_only)
        return 1

    allowed_tiers = contract.get("allowed_trust_tiers")
    if not isinstance(allowed_tiers, list) or not allowed_tiers:
        allowed_tiers = list(DEFAULT_ALLOWED_TIERS)
    allowed_tier_set = {str(x).strip().lower() for x in allowed_tiers if str(x).strip()}

    conclusion_required_tiers = contract.get("conclusion_required_tiers")
    if not isinstance(conclusion_required_tiers, list) or not conclusion_required_tiers:
        conclusion_required_tiers = list(DEFAULT_CONCLUSION_REQUIRED_TIERS)
    conclusion_required_set = {str(x).strip().lower() for x in conclusion_required_tiers if str(x).strip()}

    payload["allowed_trust_tiers"] = sorted(allowed_tier_set)
    payload["conclusion_required_tiers"] = sorted(conclusion_required_set)

    batch_path: Path | None = None
    if args.feedback_batch.strip():
        p = Path(args.feedback_batch).expanduser().resolve()
        if p.exists():
            batch_path = p
    else:
        batch_path = _select_correlated_feedback_batch(pack_path, list(activity.get("activity_correlated_refs", [])))
        pattern = str(contract.get("feedback_batch_path_pattern", "")).strip()
        if not pattern:
            pattern = "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md"
        if batch_path is None:
            batch_path = resolve_report_path(report="", pattern=pattern, pack_root=pack_path)

    if batch_path is None:
        payload["error_code"] = ERR_SOURCE_METADATA_INCOMPLETE
        payload["stale_reasons"] = ["feedback_batch_not_found"]
        if args.operation in INSPECTION_OPERATIONS:
            payload["external_source_trust_chain_status"] = STATUS_SKIPPED_NOT_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 0
        payload["external_source_trust_chain_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    raw = batch_path.read_text(encoding="utf-8", errors="ignore")
    parsed: dict[str, Any] = {}
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            parsed = obj
    except Exception:
        parsed = {}

    rows = _to_rows_from_json(parsed)
    rows.extend(_to_rows_from_text(raw))
    rows = _dedupe_rows(rows)

    payload["feedback_batch_path"] = str(batch_path)
    payload["source_row_count"] = len(rows)

    unknown_in_conclusion_refs: list[str] = []
    missing_tier_refs: list[str] = []
    missing_trace_refs: list[str] = []
    unknown_candidate_without_downgrade: list[str] = []

    conclusion_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []

    for row in rows:
        tier = _normalize_tier(row.get("tier"))
        scope = _normalize_scope(row.get("scope"))
        ref = str(row.get("ref") or row.get("origin") or "").strip() or str(row.get("origin", ""))

        if scope == "conclusion":
            conclusion_rows.append(row)
        elif scope == "candidate":
            candidate_rows.append(row)

        if not tier:
            missing_tier_refs.append(ref)
            continue
        if tier not in allowed_tier_set:
            missing_tier_refs.append(ref)
            continue

        if scope == "conclusion" and tier == "unknown":
            unknown_in_conclusion_refs.append(ref)

        if scope == "candidate" and tier == "unknown":
            note = str(row.get("downgrade_note") or "").strip()
            follow = str(row.get("follow_up_action") or "").strip()
            low_line = " ".join([note, follow]).lower()
            has_downgrade = bool(note) or any(x in low_line for x in ("downgrade", "unverified", "tentative"))
            has_follow = bool(follow) or any(x in low_line for x in ("follow-up", "follow up", "retrieve", "official", "primary"))
            if not (has_downgrade and has_follow):
                unknown_candidate_without_downgrade.append(ref)

    payload["conclusion_source_count"] = len(conclusion_rows)
    payload["candidate_source_count"] = len(candidate_rows)

    # conclusion statements must have official/primary trace when conclusion rows exist
    if conclusion_rows:
        has_required_trace = any(_normalize_tier(r.get("tier")) in conclusion_required_set for r in conclusion_rows)
        if not has_required_trace:
            for r in conclusion_rows:
                ref = str(r.get("ref") or r.get("origin") or "").strip() or str(r.get("origin", ""))
                missing_trace_refs.append(ref)

    stale_reasons: list[str] = []
    error_code = ""

    if missing_tier_refs:
        stale_reasons.append("source_tier_missing_or_invalid")
        error_code = ERR_SOURCE_METADATA_INCOMPLETE

    if unknown_in_conclusion_refs:
        stale_reasons.append("unknown_source_tier_in_conclusion")
        error_code = ERR_UNKNOWN_IN_CONCLUSION

    if missing_trace_refs:
        stale_reasons.append("official_primary_trace_missing_for_conclusion")
        if not error_code:
            error_code = ERR_REQUIRED_TRACE_MISSING

    if unknown_candidate_without_downgrade:
        stale_reasons.append("unknown_candidate_missing_downgrade_or_followup")
        if not error_code:
            error_code = ERR_SOURCE_METADATA_INCOMPLETE

    payload["unknown_in_conclusion_refs"] = sorted(set(unknown_in_conclusion_refs))
    payload["missing_tier_refs"] = sorted(set(missing_tier_refs))
    payload["missing_trace_refs"] = sorted(set(missing_trace_refs))
    payload["unknown_candidate_without_downgrade"] = sorted(set(unknown_candidate_without_downgrade))

    if stale_reasons:
        payload["external_source_trust_chain_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_SOURCE_METADATA_INCOMPLETE
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["external_source_trust_chain_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
