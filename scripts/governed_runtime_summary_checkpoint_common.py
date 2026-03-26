#!/usr/bin/env python3
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SUMMARY_LIFECYCLE_IN_PROGRESS = "IN_PROGRESS"
SUMMARY_LIFECYCLE_FINALIZED = "FINALIZED"
SUMMARY_CHECKPOINT_KIND_CHECKPOINT = "checkpoint"
SUMMARY_CHECKPOINT_KIND_FINAL = "final"


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        token = _clean_str(value)
        if token and token not in out:
            out.append(token)
    return out


def utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def apply_governed_runtime_summary_checkpoint(
    summary: dict[str, Any],
    *,
    phase: str,
    current_check_name: str = "",
    current_check_state: str = "idle",
    phase_step_index: int | None = None,
    phase_step_total: int | None = None,
    last_completed_check_name: str = "",
    lifecycle_status: str = SUMMARY_LIFECYCLE_IN_PROGRESS,
    checkpoint_kind: str = SUMMARY_CHECKPOINT_KIND_CHECKPOINT,
) -> dict[str, Any]:
    command_execution = summary.get("command_execution") or {}
    progress = summary.setdefault("summary_progress", {})
    checkpoint_sequence = _safe_int(progress.get("checkpoint_sequence")) + 1
    checkpoint_written_utc = utc_now_iso_z()

    if phase_step_index is not None:
        progress["phase_step_index"] = int(phase_step_index)
    if phase_step_total is not None:
        progress["phase_step_total"] = int(phase_step_total)

    progress["phase"] = _clean_str(phase) or "unknown"
    progress["current_check_name"] = _clean_str(current_check_name)
    progress["current_check_state"] = _clean_str(current_check_state) or "idle"
    if last_completed_check_name:
        progress["last_completed_check_name"] = _clean_str(last_completed_check_name)
    elif command_execution.get("last_completed_script"):
        progress["last_completed_check_name"] = _clean_str(command_execution.get("last_completed_script"))
    progress["executed_command_count"] = _safe_int(command_execution.get("executed_command_count"))
    progress["failed_command_count"] = _safe_int(command_execution.get("failed_command_count"))
    progress["first_failed_check_name"] = _clean_str(command_execution.get("first_failed_script"))
    progress["failed_check_names"] = _clean_list(command_execution.get("failed_scripts"))
    progress["checkpoint_sequence"] = checkpoint_sequence
    progress["checkpoint_written_utc"] = checkpoint_written_utc

    summary["summary_lifecycle_status"] = _clean_str(lifecycle_status) or SUMMARY_LIFECYCLE_IN_PROGRESS
    summary["summary_checkpoint_kind"] = _clean_str(checkpoint_kind) or SUMMARY_CHECKPOINT_KIND_CHECKPOINT
    summary["summary_checkpoint_written_utc"] = checkpoint_written_utc
    return progress


def write_governed_runtime_summary_checkpoint(summary_out: str, payload: dict[str, Any]) -> str:
    target = Path(summary_out).expanduser()
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()
    else:
        target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot = deepcopy(payload)
    snapshot["summary_out"] = str(target)
    target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(target)


def _resolve_doc_path(path_text: str) -> Path | None:
    token = _clean_str(path_text)
    if not token:
        return None
    target = Path(token).expanduser()
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()
    else:
        target = target.resolve()
    return target


def load_governed_runtime_summary_doc(path_text: str) -> dict[str, Any]:
    target = _resolve_doc_path(path_text)
    if target is None:
        return {}
    try:
        doc = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def capture_governed_runtime_summary_resume_source(
    path_text: str,
    *,
    summary_out: str = "",
) -> dict[str, Any]:
    resume_target = _resolve_doc_path(path_text)
    summary_target = _resolve_doc_path(summary_out)
    resume_doc = load_governed_runtime_summary_doc(str(resume_target)) if resume_target is not None else {}
    same_path_as_summary_out = bool(
        resume_target is not None and summary_target is not None and resume_target == summary_target
    )
    return {
        "resume_from_summary": str(resume_target) if resume_target is not None else "",
        "summary_out": str(summary_target) if summary_target is not None else "",
        "resume_doc": deepcopy(resume_doc),
        "resume_capture_mode": "stable_prewrite_snapshot" if resume_target is not None else "absent",
        "same_path_as_summary_out": same_path_as_summary_out,
    }


def derive_governed_runtime_summary_resume_projection(
    available_check_names: list[str],
    summary_doc: dict[str, Any],
    *,
    resumable_phase: str = "command_sequence",
) -> dict[str, Any]:
    phase = _clean_str((summary_doc.get("summary_progress") or {}).get("phase"))
    lifecycle_status = _clean_str(summary_doc.get("summary_lifecycle_status"))
    current_check_name = _clean_str((summary_doc.get("summary_progress") or {}).get("current_check_name"))
    current_check_state = _clean_str((summary_doc.get("summary_progress") or {}).get("current_check_state"))
    last_completed_check_name = _clean_str((summary_doc.get("summary_progress") or {}).get("last_completed_check_name"))
    name_to_index = {name: idx for idx, name in enumerate(available_check_names)}

    projection: dict[str, Any] = {
        "resume_projection_status": "SKIPPED_NOT_REQUIRED",
        "resume_reason": "",
        "summary_lifecycle_status": lifecycle_status,
        "summary_phase": phase,
        "current_check_name": current_check_name,
        "current_check_state": current_check_state,
        "last_completed_check_name": last_completed_check_name,
        "resume_start_index": 0,
        "resume_start_check_name": "",
        "resume_skipped_check_count": 0,
        "resume_skipped_check_names": [],
    }

    if lifecycle_status == SUMMARY_LIFECYCLE_FINALIZED:
        projection["resume_reason"] = "summary_already_finalized"
        return projection
    if phase != _clean_str(resumable_phase):
        projection["resume_reason"] = "summary_phase_not_resumable"
        return projection

    start_index = 0
    if current_check_name and current_check_state.lower() == "running" and current_check_name in name_to_index:
        start_index = name_to_index[current_check_name]
        projection["resume_reason"] = "resume_from_running_check"
    elif last_completed_check_name and last_completed_check_name in name_to_index:
        start_index = name_to_index[last_completed_check_name] + 1
        projection["resume_reason"] = "resume_after_last_completed_check"
    else:
        projection["resume_reason"] = "checkpoint_check_names_not_in_current_sequence"
        return projection

    if start_index >= len(available_check_names):
        projection["resume_projection_status"] = "PASS_REQUIRED"
        projection["resume_reason"] = "sequence_already_exhausted"
        projection["resume_start_index"] = len(available_check_names)
        projection["resume_skipped_check_count"] = len(available_check_names)
        projection["resume_skipped_check_names"] = list(available_check_names)
        return projection

    projection["resume_projection_status"] = "PASS_REQUIRED"
    projection["resume_start_index"] = start_index
    projection["resume_start_check_name"] = available_check_names[start_index]
    projection["resume_skipped_check_count"] = start_index
    projection["resume_skipped_check_names"] = list(available_check_names[:start_index])
    return projection
