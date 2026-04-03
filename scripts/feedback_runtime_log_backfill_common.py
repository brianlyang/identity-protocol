#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strict_live_evidence_resolution_common import clean_string, resolve_active_execution_context


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_feedback_runtime_log_payload(
    *,
    pack_root: Path,
    identity_id: str,
    task_doc: dict[str, Any],
    log_path: Path,
    source_label: str,
) -> dict[str, Any]:
    active_context = resolve_active_execution_context(pack_root)
    task_id = clean_string(task_doc.get("task_id")) or f"{identity_id}_bootstrap"
    active_run_id = clean_string(active_context.get("run_id"))
    active_report_path = clean_string(active_context.get("report_path"))
    active_pointer_path = clean_string(active_context.get("pointer_path"))
    prompt_contract_path = (pack_root / "runtime" / "state" / "prompt_contract.json").resolve()
    prompt_contract_ref = str(prompt_contract_path) if prompt_contract_path.exists() else ""

    artifact_refs: list[str] = []
    for ref in (
        active_report_path,
        prompt_contract_ref,
        active_pointer_path,
        str(log_path.resolve()),
    ):
        token = clean_string(ref)
        if token and token not in artifact_refs:
            artifact_refs.append(token)

    current_run_joined = bool(active_run_id and active_report_path)
    run_id = active_run_id or f"{source_label}-{identity_id}"
    binding_mode = "current_run_joined" if current_run_joined else "synthetic_refresh"
    decision_trace_ref = active_report_path or f"{source_label}_runtime_feedback_refresh"
    context_signature = (
        f"{source_label}-current-run-refresh"
        if current_run_joined
        else f"{source_label}-refresh"
    )

    return {
        "feedback_id": f"feedback-{identity_id}-{source_label}",
        "identity_id": identity_id,
        "task_id": task_id,
        "run_id": run_id,
        "timestamp": _utc_now_iso(),
        "context_signature": context_signature,
        "outcome": "PASS",
        "failure_type": "none",
        "decision_trace_ref": decision_trace_ref,
        "artifacts": artifact_refs,
        "rulebook_delta": {
            "positive": 0,
            "negative": 0,
        },
        "replay_status": "PASS",
        "active_execution_report_ref": active_report_path,
        "active_execution_pointer_ref": active_pointer_path,
        "operational_prompt_ref": prompt_contract_ref or active_report_path,
        "current_run_binding_mode": binding_mode,
    }
