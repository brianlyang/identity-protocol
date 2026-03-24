#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strict_live_evidence_resolution_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    clean_string,
    resolve_active_execution_context,
)

DEFAULT_FEEDBACK_RUN_ID_FIELD = "run_id"
DEFAULT_FEEDBACK_REPLAY_STATUS_FIELD = "replay_status"
DEFAULT_FEEDBACK_REF_FIELDS: tuple[str, ...] = (
    "decision_trace_ref",
    "artifacts",
)


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _parse_ts(ts: str) -> datetime | None:
    token = clean_string(ts)
    if not token:
        return None
    try:
        return datetime.fromisoformat(token.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _glob_paths(pattern: str, *, pack_root: Path) -> list[Path]:
    raw = clean_string(pattern)
    if not raw:
        return []
    candidate = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ("*", "?", "["))
    if candidate.is_absolute():
        if has_magic:
            return sorted(Path(item).resolve() for item in glob.glob(str(candidate)))
        return [candidate.resolve()] if candidate.exists() else []

    local_prefix = f"identity/runtime/local/{pack_root.name}/"
    mapped_raw = raw
    if raw.startswith(local_prefix):
        mapped_raw = f"runtime/{raw[len(local_prefix):]}"
    elif raw.startswith("identity/runtime/"):
        mapped_raw = f"runtime/{raw[len('identity/runtime/'):]}"

    preferred = sorted(pack_root.glob(mapped_raw))
    if preferred:
        return preferred
    if mapped_raw != raw:
        fallback = sorted(Path(".").glob(mapped_raw))
        if fallback:
            return fallback
    return sorted(Path(".").glob(raw))


def _identity_scoped_logs(paths: list[Path], identity_id: str) -> list[Path]:
    if not paths:
        return []
    scoped: list[Path] = []
    token_dash = clean_string(identity_id)
    token_us = token_dash.replace("-", "_")
    for path in paths:
        name = path.name
        if token_dash in name or token_us in name:
            scoped.append(path)
            continue
        row = _load_json(path)
        if clean_string(row.get("identity_id")) == token_dash:
            scoped.append(path)
    return scoped or paths


def resolve_identity_feedback_logs(
    *,
    pack_root: Path,
    pattern: str,
    identity_id: str,
) -> list[Path]:
    return _identity_scoped_logs(_glob_paths(pattern, pack_root=pack_root), identity_id)


def select_latest_identity_feedback_log(
    *,
    pack_root: Path,
    pattern: str,
    identity_id: str,
) -> Path | None:
    logs = resolve_identity_feedback_logs(
        pack_root=pack_root,
        pattern=pattern,
        identity_id=identity_id,
    )
    if not logs:
        return None
    return max(logs, key=lambda path: path.stat().st_mtime)


def _resolve_existing_path(raw: Any, *, pack_root: Path) -> Path | None:
    token = clean_string(raw)
    if not token:
        return None
    if len(token) > 1024:
        return None
    if "/" not in token and "\\" not in token and not token.endswith((".json", ".jsonl", ".md")):
        return None
    candidate = Path(token).expanduser()
    if not candidate.is_absolute():
        candidate = (pack_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        return candidate if candidate.exists() else None
    except OSError:
        return None


def _collect_path_candidates(node: Any, *, pack_root: Path, sink: list[Path]) -> None:
    if isinstance(node, dict):
        if "path" in node:
            candidate = _resolve_existing_path(node.get("path"), pack_root=pack_root)
            if candidate is not None and candidate not in sink:
                sink.append(candidate)
        for value in node.values():
            _collect_path_candidates(value, pack_root=pack_root, sink=sink)
        return
    if isinstance(node, list):
        for item in node:
            _collect_path_candidates(item, pack_root=pack_root, sink=sink)
        return
    candidate = _resolve_existing_path(node, pack_root=pack_root)
    if candidate is not None and candidate not in sink:
        sink.append(candidate)


def _doc_references_path(node: Any, target_path: Path) -> bool:
    target = target_path.expanduser().resolve().as_posix()
    if isinstance(node, dict):
        return any(_doc_references_path(value, target_path) for value in node.values())
    if isinstance(node, list):
        return any(_doc_references_path(item, target_path) for item in node)
    token = clean_string(node)
    if not token:
        return False
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        try:
            return candidate.resolve().as_posix() == target
        except Exception:
            return False
    return token == target


def _select_joined_receipt(
    *,
    active_context: dict[str, Any],
    candidates: list[Path],
) -> tuple[str, str]:
    active_report_path = clean_string(active_context.get("report_path"))
    active_report = Path(active_report_path).expanduser().resolve() if active_report_path else None
    active_report_doc = active_context.get("report_doc") if isinstance(active_context.get("report_doc"), dict) else {}

    for candidate in candidates:
        if active_report is not None and candidate.resolve() == active_report:
            return str(candidate.resolve()), STATUS_PASS_REQUIRED
        if active_report_doc and _doc_references_path(active_report_doc, candidate):
            return str(candidate.resolve()), STATUS_PASS_REQUIRED

    if candidates:
        return str(candidates[0].resolve()), STATUS_FAIL_REQUIRED
    return "", STATUS_FAIL_REQUIRED


def derive_feedback_current_run_binding_projection(
    *,
    pack_root: Path,
    identity_id: str,
    contract_doc: dict[str, Any] | None,
) -> dict[str, Any]:
    contract = contract_doc if isinstance(contract_doc, dict) else {}
    active_context = resolve_active_execution_context(pack_root)
    stale_reasons: list[str] = []

    latest_log = None
    feedback_pattern = clean_string(contract.get("feedback_log_path_pattern"))
    if feedback_pattern:
        latest_log = select_latest_identity_feedback_log(
            pack_root=pack_root,
            pattern=feedback_pattern,
            identity_id=identity_id,
        )
    latest_doc = _load_json(latest_log)

    if not clean_string(active_context.get("pointer_path")):
        stale_reasons.append("active_execution_pointer_missing")
    current_run_id = clean_string(active_context.get("run_id"))
    if not current_run_id:
        stale_reasons.append("current_run_id_missing")

    latest_feedback_log = str(latest_log.resolve()) if isinstance(latest_log, Path) and latest_log.exists() else ""
    evidence_origin = "live_log" if latest_feedback_log else "missing"
    if not latest_feedback_log:
        stale_reasons.append("latest_feedback_log_missing")

    max_age_days = int(contract.get("max_log_age_days") or 0)
    latest_feedback_log_age_days = None
    report_freshness_status = STATUS_FAIL_REQUIRED
    latest_ts = _parse_ts(clean_string(latest_doc.get("timestamp")))
    if latest_ts is not None and max_age_days > 0:
        age_seconds = max(0.0, datetime.now(timezone.utc).timestamp() - latest_ts.timestamp())
        latest_feedback_log_age_days = round(age_seconds / 86400.0, 2)
        if age_seconds <= max_age_days * 86400:
            report_freshness_status = STATUS_PASS_REQUIRED
        else:
            stale_reasons.append("latest_feedback_log_not_fresh_enough")
    elif latest_feedback_log:
        stale_reasons.append("latest_feedback_timestamp_missing_or_invalid")

    run_id_field = clean_string(contract.get("feedback_run_id_field")) or DEFAULT_FEEDBACK_RUN_ID_FIELD
    feedback_run_id = clean_string(latest_doc.get(run_id_field))
    latest_feedback_run_id_match_status = (
        STATUS_PASS_REQUIRED if current_run_id and feedback_run_id and feedback_run_id == current_run_id else STATUS_FAIL_REQUIRED
    )
    if latest_feedback_log and not feedback_run_id:
        stale_reasons.append("latest_feedback_run_id_missing")
    elif current_run_id and feedback_run_id and feedback_run_id != current_run_id:
        stale_reasons.append("latest_feedback_run_id_mismatch")

    ref_fields = [
        clean_string(item)
        for item in (contract.get("feedback_operational_prompt_ref_candidates") or [])
        if clean_string(item)
    ] or list(DEFAULT_FEEDBACK_REF_FIELDS)
    receipt_candidates: list[Path] = []
    for field in ref_fields:
        if field in latest_doc:
            _collect_path_candidates(latest_doc.get(field), pack_root=pack_root, sink=receipt_candidates)
    operational_prompt_receipt_ref, operational_prompt_run_join_status = _select_joined_receipt(
        active_context=active_context,
        candidates=receipt_candidates,
    )
    if latest_feedback_log and not operational_prompt_receipt_ref:
        stale_reasons.append("operational_prompt_receipt_ref_missing")
    elif latest_feedback_log and operational_prompt_run_join_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("operational_prompt_receipt_not_joined_to_current_run")

    replay_field = clean_string(contract.get("feedback_replay_status_field")) or DEFAULT_FEEDBACK_REPLAY_STATUS_FIELD
    replay_status = clean_string(latest_doc.get(replay_field)).upper()
    if latest_feedback_log and replay_status != "PASS":
        stale_reasons.append("latest_feedback_replay_status_not_pass")

    preflight_reentry_receipt_ref = clean_string(active_context.get("pointer_path"))
    if not preflight_reentry_receipt_ref:
        stale_reasons.append("preflight_reentry_receipt_ref_missing")

    latest_feedback_same_run_binding_status = (
        STATUS_PASS_REQUIRED
        if latest_feedback_run_id_match_status == STATUS_PASS_REQUIRED
        and operational_prompt_run_join_status == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED
    )
    loopback_live_binding_status = (
        STATUS_PASS_REQUIRED
        if latest_feedback_same_run_binding_status == STATUS_PASS_REQUIRED
        and replay_status == "PASS"
        and preflight_reentry_receipt_ref
        else STATUS_FAIL_REQUIRED
    )

    return {
        "required_run_id": current_run_id,
        "current_run_pointer": clean_string(active_context.get("pointer_path")),
        "current_run_report_path": clean_string(active_context.get("report_path")),
        "latest_feedback_log": latest_feedback_log,
        "latest_feedback_log_age_days": latest_feedback_log_age_days,
        "report_freshness_status": report_freshness_status,
        "latest_feedback_run_id": feedback_run_id,
        "latest_feedback_run_id_match_status": latest_feedback_run_id_match_status,
        "latest_feedback_same_run_binding_status": latest_feedback_same_run_binding_status,
        "operational_prompt_receipt_ref": operational_prompt_receipt_ref,
        "operational_prompt_run_join_status": operational_prompt_run_join_status,
        "feedback_run_id": feedback_run_id,
        "preflight_reentry_receipt_ref": preflight_reentry_receipt_ref,
        "loopback_live_binding_status": loopback_live_binding_status,
        "feedback_replay_status": replay_status,
        "evidence_origin": evidence_origin,
        "stale_reasons": sorted(set(stale_reasons)),
    }
