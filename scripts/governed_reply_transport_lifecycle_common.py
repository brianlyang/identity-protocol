#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from protocol_infra_contract import (
    HOST_VISIBLE_POST_CHECK_RECOVERY_ARTIFACT_CHANNEL,
    HOST_VISIBLE_POST_CHECK_RECOVERY_MATERIALIZATION_REASON,
    HOST_VISIBLE_POST_CHECK_RECOVERY_REPLY_TRANSPORT_REF,
)
from runtime_temp_path_common import runtime_temp_file

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

GOVERNED_REPLY_TRANSPORT_PHASE_UNRESOLVED = "unresolved"
GOVERNED_REPLY_TRANSPORT_PHASE_SOURCE_MATERIALIZED = "source_materialized"
GOVERNED_REPLY_TRANSPORT_PHASE_CURRENT_SURFACE_ATTESTED = "current_surface_attested"
GOVERNED_REPLY_TRANSPORT_PHASE_LIVE_RECEIPT_BOUND = "live_receipt_bound"
GOVERNED_REPLY_TRANSPORT_PHASE_FINAL_RELAY_BOUND = "final_relay_bound"
REPLY_TRANSPORT_RESOLUTION_MODE_EXISTING_FILE = "existing_file"
REPLY_TRANSPORT_RESOLUTION_MODE_EXISTING_FILE_MISSING = "existing_file_missing"
REPLY_TRANSPORT_RESOLUTION_MODE_MATERIALIZE_RUNTIME_SENTINEL = "materialize_runtime_sentinel"


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _parse_json_payload(raw: str) -> dict[str, Any]:
    text = _normalize_text(raw)
    if not text:
        return {}
    for line in reversed(text.splitlines()):
        row = _normalize_text(line)
        if not row:
            continue
        try:
            payload = json.loads(row)
        except Exception:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def reply_transport_ref_is_runtime_materialization_token(raw_ref: Any) -> bool:
    token = _normalize_text(raw_ref)
    return token.startswith("runtime:")


def reply_transport_binding_issue_is_pre_live(issue: Any) -> bool:
    token = _normalize_text(issue)
    if not token:
        return False
    return token == "reply_transport_live_receipts_missing" or token.startswith(
        (
            "reply_transport_live_receipt_missing:",
            "reply_transport_live_receipt_stale:",
        )
    )


def reply_transport_binding_is_projection_eligible(
    *,
    reason: Any = "",
    issues: list[Any] | tuple[Any, ...] | None = None,
) -> bool:
    normalized_issues = [_normalize_text(item) for item in (issues or []) if _normalize_text(item)]
    if not normalized_issues:
        token = _normalize_text(reason)
        normalized_issues = [token] if token else []
    if not normalized_issues:
        return False
    return all(reply_transport_binding_issue_is_pre_live(item) for item in normalized_issues)


def derive_governed_reply_transport_lifecycle(
    *,
    reply_transport_ref: Any,
    current_surface_transport_attestation_status: Any,
    reply_transport_binding_status: Any,
    final_channel_relay_status: Any = "",
    reply_transport_source_status: Any = "",
) -> dict[str, str]:
    ref = _normalize_text(reply_transport_ref)
    current_surface_status = _normalize_text(current_surface_transport_attestation_status).upper()
    live_binding_status = _normalize_text(reply_transport_binding_status).upper()
    final_relay = _normalize_text(final_channel_relay_status).upper()
    source_status = _normalize_text(reply_transport_source_status).upper()

    phase = GOVERNED_REPLY_TRANSPORT_PHASE_UNRESOLVED
    reason = "reply_transport_ref_missing"
    if ref:
        phase = GOVERNED_REPLY_TRANSPORT_PHASE_SOURCE_MATERIALIZED
        reason = "reply_transport_ref_resolved"
    if source_status == STATUS_FAIL_REQUIRED:
        phase = GOVERNED_REPLY_TRANSPORT_PHASE_UNRESOLVED
        reason = "reply_transport_source_resolution_not_pass"
    elif current_surface_status == STATUS_PASS_REQUIRED:
        phase = GOVERNED_REPLY_TRANSPORT_PHASE_CURRENT_SURFACE_ATTESTED
        reason = "current_surface_transport_attested"
    if live_binding_status == STATUS_PASS_REQUIRED:
        phase = GOVERNED_REPLY_TRANSPORT_PHASE_LIVE_RECEIPT_BOUND
        reason = "reply_transport_live_receipts_bound"
    if final_relay == STATUS_PASS_REQUIRED:
        phase = GOVERNED_REPLY_TRANSPORT_PHASE_FINAL_RELAY_BOUND
        reason = "final_channel_relay_bound"
    return {
        "governed_reply_transport_lifecycle_phase": phase,
        "governed_reply_transport_lifecycle_status": (
            STATUS_PASS_REQUIRED if phase != GOVERNED_REPLY_TRANSPORT_PHASE_UNRESOLVED else STATUS_FAIL_REQUIRED
        ),
        "governed_reply_transport_lifecycle_reason": reason,
    }


def _default_materialized_body(
    *,
    requested_ref: str,
    operation: str,
    run_id: str,
    materialization_reason: str,
) -> str:
    lines = [
        "[Protocol Recovery Artifact] governed reply transport source materialized by protocol control plane.",
        f"materialization_reason={_normalize_text(materialization_reason) or HOST_VISIBLE_POST_CHECK_RECOVERY_MATERIALIZATION_REASON}",
        f"requested_ref={_normalize_text(requested_ref) or HOST_VISIBLE_POST_CHECK_RECOVERY_REPLY_TRANSPORT_REF}",
        f"operation={_normalize_text(operation) or 'validate'}",
    ]
    run_token = _normalize_text(run_id)
    if run_token:
        lines.append(f"run_id={run_token}")
    return "\n".join(lines)


def _render_native_chat_surface(
    *,
    repo_root: Path,
    catalog_path: Path,
    repo_catalog_path: Path,
    identity_id: str,
    actor_id: str,
    session_id: str,
) -> tuple[int, dict[str, Any]]:
    cmd = [
        sys.executable,
        str((repo_root / "scripts" / "render_identity_response_stamp.py").resolve()),
        "--identity-id",
        _normalize_text(identity_id),
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--actor-id",
        _normalize_text(actor_id),
        "--surface",
        "native-chat",
        "--native-chat-machine-profile",
        "mini",
        "--work-layer",
        "instance",
        "--source-layer",
        "project",
        "--json-only",
    ]
    if _normalize_text(session_id):
        cmd.extend(["--session-id", _normalize_text(session_id)])
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_root))
    return proc.returncode, _parse_json_payload(proc.stdout)


def materialize_governed_reply_transport_artifact(
    *,
    repo_root: Path,
    catalog_path: Path,
    repo_catalog_path: Path,
    identity_id: str,
    actor_id: str,
    session_id: str = "",
    operation: str = "",
    run_id: str = "",
    requested_ref: str = "",
    artifact_channel: str = "",
    artifact_stem: str = "",
    materialization_reason: str = "",
    body_text: str = "",
) -> dict[str, Any]:
    channel = _normalize_text(artifact_channel) or HOST_VISIBLE_POST_CHECK_RECOVERY_ARTIFACT_CHANNEL
    stem = _normalize_text(artifact_stem) or f"{channel}-{_normalize_text(identity_id) or 'identity'}"
    output_path = runtime_temp_file(
        channel=channel,
        operation=_normalize_text(operation) or "validate",
        identity_id=_normalize_text(identity_id),
        run_token=_normalize_text(run_id),
        stem=stem,
        ext="txt",
    ).resolve()

    rc, render_payload = _render_native_chat_surface(
        repo_root=repo_root,
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
        identity_id=identity_id,
        actor_id=actor_id,
        session_id=session_id,
    )
    identity_line = _normalize_text(render_payload.get("native_chat_identity_line", ""))
    machine_line = _normalize_text(render_payload.get("native_chat_machine_verification_line", ""))
    reasons: list[str] = []
    if rc != 0:
        reasons.append("native_chat_surface_render_failed")
    if not identity_line.startswith("Identity-Context:"):
        reasons.append("native_chat_identity_line_missing")
    if not machine_line.startswith("Machine-Verification:"):
        reasons.append("native_chat_machine_verification_line_missing")
    if reasons:
        return {
            "reply_transport_source_status": STATUS_FAIL_REQUIRED,
            "reply_transport_requested_ref": _normalize_text(requested_ref),
            "reply_transport_effective_ref": "",
            "reply_transport_resolution_mode": REPLY_TRANSPORT_RESOLUTION_MODE_MATERIALIZE_RUNTIME_SENTINEL,
            "reply_transport_source_materialized": False,
            "reply_transport_source_exists": False,
            "reply_transport_source_artifact_kind": "",
            "reply_transport_source_path": "",
            "reply_transport_source_render_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-HDSTAMP-003",
            "stale_reasons": reasons,
        }

    body = _normalize_text(body_text) or _default_materialized_body(
        requested_ref=requested_ref,
        operation=operation,
        run_id=run_id,
        materialization_reason=materialization_reason,
    )
    content = "\n".join(line for line in (identity_line, machine_line, body) if line).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return {
        "reply_transport_source_status": STATUS_PASS_REQUIRED,
        "reply_transport_requested_ref": _normalize_text(requested_ref),
        "reply_transport_effective_ref": str(output_path),
        "reply_transport_resolution_mode": REPLY_TRANSPORT_RESOLUTION_MODE_MATERIALIZE_RUNTIME_SENTINEL,
        "reply_transport_source_materialized": True,
        "reply_transport_source_exists": True,
        "reply_transport_source_artifact_kind": "plain_text_final_answer",
        "reply_transport_source_path": str(output_path),
        "reply_transport_source_render_status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
    }


def resolve_governed_reply_transport_artifact(
    *,
    repo_root: Path,
    catalog_path: Path,
    repo_catalog_path: Path,
    identity_id: str,
    actor_id: str,
    session_id: str = "",
    operation: str = "",
    run_id: str = "",
    reply_transport_ref: str = "",
    default_runtime_ref: str = HOST_VISIBLE_POST_CHECK_RECOVERY_REPLY_TRANSPORT_REF,
    artifact_channel: str = "",
    artifact_stem: str = "",
    materialization_reason: str = "",
    body_text: str = "",
) -> dict[str, Any]:
    requested_ref = _normalize_text(reply_transport_ref) or _normalize_text(default_runtime_ref)
    if reply_transport_ref and not reply_transport_ref_is_runtime_materialization_token(reply_transport_ref):
        candidate = Path(reply_transport_ref).expanduser()
        if candidate.exists() and candidate.is_file():
            resolved = str(candidate.resolve())
            return {
                "reply_transport_source_status": STATUS_PASS_REQUIRED,
                "reply_transport_requested_ref": requested_ref,
                "reply_transport_effective_ref": resolved,
                "reply_transport_resolution_mode": REPLY_TRANSPORT_RESOLUTION_MODE_EXISTING_FILE,
                "reply_transport_source_materialized": False,
                "reply_transport_source_exists": True,
                "reply_transport_source_artifact_kind": "plain_text_final_answer",
                "reply_transport_source_path": resolved,
                "reply_transport_source_render_status": STATUS_PASS_REQUIRED,
                "error_code": "",
                "stale_reasons": [],
            }
        return {
            "reply_transport_source_status": STATUS_FAIL_REQUIRED,
            "reply_transport_requested_ref": requested_ref,
            "reply_transport_effective_ref": "",
            "reply_transport_resolution_mode": REPLY_TRANSPORT_RESOLUTION_MODE_EXISTING_FILE_MISSING,
            "reply_transport_source_materialized": False,
            "reply_transport_source_exists": False,
            "reply_transport_source_artifact_kind": "",
            "reply_transport_source_path": "",
            "reply_transport_source_render_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-HDSTAMP-003",
            "stale_reasons": [f"reply_transport_ref_unresolved:{requested_ref}"],
        }

    return materialize_governed_reply_transport_artifact(
        repo_root=repo_root,
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
        identity_id=identity_id,
        actor_id=actor_id,
        session_id=session_id,
        operation=operation,
        run_id=run_id,
        requested_ref=requested_ref,
        artifact_channel=artifact_channel,
        artifact_stem=artifact_stem,
        materialization_reason=materialization_reason,
        body_text=body_text,
    )
