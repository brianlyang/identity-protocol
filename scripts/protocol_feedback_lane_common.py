#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


def _safe_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def discover_default_correlation_keys(pack_root: Path) -> dict[str, Any]:
    reports_dir = (pack_root / "runtime" / "reports").resolve()
    report_files = sorted(reports_dir.glob("identity-upgrade-exec-*.json"), key=lambda p: p.stat().st_mtime) if reports_dir.exists() else []
    latest = report_files[-1] if report_files else None
    keys: set[str] = set()
    latest_run_id = ""
    if latest and latest.exists():
        doc = _safe_json(latest)
        latest_run_id = str(doc.get("run_id", "")).strip()
        if latest_run_id:
            keys.add(latest_run_id)
            keys.add(f"run_id={latest_run_id}")
            keys.add(f"run_id\": \"{latest_run_id}")
        keys.add(latest.name)
        keys.add(latest.stem)
    return {
        "latest_report_path": str(latest) if latest else "",
        "latest_run_id": latest_run_id,
        "correlation_keys": sorted({k for k in keys if str(k).strip()}),
    }


def build_correlation_keys(
    *,
    default_keys: Iterable[str] | None = None,
    run_id: str = "",
    explicit_keys: Iterable[str] | None = None,
) -> list[str]:
    out: set[str] = set()
    for raw in (default_keys or []):
        token = str(raw or "").strip()
        if token:
            out.add(token)
    rid = str(run_id or "").strip()
    if rid:
        out.add(rid)
        out.add(f"run_id={rid}")
        out.add(f"run_id\": \"{rid}")
    for raw in (explicit_keys or []):
        token = str(raw or "").strip()
        if token:
            out.add(token)
    return sorted(out)


def collect_protocol_feedback_activity(
    *,
    feedback_root: Path,
    correlation_keys: Iterable[str] | None = None,
    activity_window_hours: float = 72.0,
) -> dict[str, Any]:
    root = feedback_root.resolve()
    if not root.exists():
        return {
            "feedback_root": str(root),
            "activity_window_hours": activity_window_hours,
            "protocol_feedback_activity_detected": False,
            "protocol_feedback_activity_refs": [],
            "activity_correlated_refs": [],
            "activity_unscoped_refs": [],
            "activity_ignored_stale_refs": [],
            "activity_correlation_status": "NO_ACTIVITY",
            "activity_correlation_key": "",
            "requiredization_current_round_linked": False,
            "requiredization_historical_activity_detected": False,
            "correlation_keys": [],
        }

    keys = [str(x).strip() for x in (correlation_keys or []) if str(x).strip()]
    keys_lower = [x.lower() for x in keys]
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max(0.0, float(activity_window_hours)))

    activity_refs: list[str] = []
    correlated_refs: list[str] = []
    unscoped_refs: list[str] = []
    ignored_stale_refs: list[str] = []
    first_hit_key = ""

    for sub in ("outbox-to-protocol", "evidence-index", "upgrade-proposals"):
        d = (root / sub).resolve()
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file():
                continue
            try:
                rel = p.relative_to(root).as_posix()
            except Exception:
                rel = str(p)

            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            except Exception:
                mtime = now
            in_window = mtime >= cutoff

            text = ""
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
            low = f"{rel}\n{text}".lower()

            matched = [k for k in keys_lower if k and k in low]
            if matched:
                if not first_hit_key:
                    first_hit_key = matched[0]
                activity_refs.append(rel)
                correlated_refs.append(rel)
                continue

            if in_window:
                activity_refs.append(rel)
                unscoped_refs.append(rel)
            else:
                ignored_stale_refs.append(rel)

    detected = bool(activity_refs)
    linked = bool(correlated_refs)
    if not detected:
        status = "NO_ACTIVITY"
    elif linked:
        status = "CORRELATED_CURRENT_ROUND"
    else:
        status = "ACTIVITY_UNSCOPED"

    return {
        "feedback_root": str(root),
        "activity_window_hours": activity_window_hours,
        "protocol_feedback_activity_detected": detected,
        "protocol_feedback_activity_refs": activity_refs,
        "activity_correlated_refs": correlated_refs,
        "activity_unscoped_refs": unscoped_refs,
        "activity_ignored_stale_refs": ignored_stale_refs,
        "activity_correlation_status": status,
        "activity_correlation_key": first_hit_key,
        "requiredization_current_round_linked": linked,
        "requiredization_historical_activity_detected": bool(detected and not linked),
        "correlation_keys": keys,
    }


def decide_requiredization_scope(
    *,
    required_declared: bool,
    auto_required_candidate: bool,
    resolved_work_layer: str,
    protocol_triggered: bool,
    current_round_linked: bool,
) -> dict[str, Any]:
    if required_declared:
        return {
            "required_contract": True,
            "auto_required_signal": False,
            "requiredization_scope_decision": "DECLARED_REQUIRED",
            "requiredization_scope_reason": "contract_required_declared",
        }

    if not auto_required_candidate:
        return {
            "required_contract": False,
            "auto_required_signal": False,
            "requiredization_scope_decision": "NO_AUTO_REQUIRED_ACTIVITY",
            "requiredization_scope_reason": "auto_required_candidate_not_met",
        }

    reasons: list[str] = []
    if str(resolved_work_layer or "").strip().lower() == "protocol":
        reasons.append("resolved_work_layer_protocol")
    if bool(protocol_triggered):
        reasons.append("protocol_triggered_current_round")
    if bool(current_round_linked):
        reasons.append("current_round_linked")

    if reasons:
        return {
            "required_contract": True,
            "auto_required_signal": True,
            "requiredization_scope_decision": "AUTO_REQUIRED_SCOPED",
            "requiredization_scope_reason": "|".join(reasons),
        }

    return {
        "required_contract": False,
        "auto_required_signal": False,
        "requiredization_scope_decision": "AUTO_REQUIRED_BLOCKED",
        "requiredization_scope_reason": "history_only_without_current_round_linkage",
    }

