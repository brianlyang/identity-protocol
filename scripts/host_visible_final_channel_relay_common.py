#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from final_emit_contract_common import STATUS_FAIL_REQUIRED, STATUS_PASS_REQUIRED
from protocol_infra_contract import (
    HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_RECEIPT_DIR,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_RECEIPT_PREFIX,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE,
)

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = SCRIPT_DIR.parent

FINAL_CHANNEL_RELAY_METADATA_FIELDS: tuple[str, ...] = (
    "agent_relay_final_answer_receipt_path",
    "agent_relay_final_answer_status",
    "agent_relay_final_answer_relay_mode",
    "agent_relay_final_answer_delivery_authority",
    "agent_relay_final_answer_source_artifact",
    "agent_relay_final_answer_question_tag",
)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _sanitize_token(value: Any, *, fallback: str) -> str:
    raw = _normalize_text(value)
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in raw).strip("._")
    return safe or fallback


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


def build_host_visible_final_channel_question_tag(*, run_id: Any, reply_transport_ref: Any) -> str:
    run_token = _sanitize_token(run_id, fallback="run")
    reply_name = Path(_normalize_text(reply_transport_ref) or "reply.txt").name
    reply_token = _sanitize_token(reply_name, fallback="reply")
    return f"host_visible_final::{run_token}::{reply_token}"


def build_host_visible_final_channel_receipt_path(
    *,
    pack_path: Path,
    run_id: Any,
    now_token: Any,
) -> Path:
    run_token = _sanitize_token(run_id, fallback="run")
    ts_token = _sanitize_token(now_token, fallback="ts")
    filename = f"{HOST_VISIBLE_FINAL_CHANNEL_RELAY_RECEIPT_PREFIX}-{ts_token}-{run_token}.json"
    return (pack_path / HOST_VISIBLE_FINAL_CHANNEL_RELAY_RECEIPT_DIR / filename).resolve()


def build_host_visible_final_channel_relay_receipt(
    *,
    repo_root: Path,
    pack_path: Path,
    identity_id: str,
    run_id: str,
    reply_transport_ref: str,
    now_token: str,
) -> tuple[int, dict[str, Any]]:
    reply_ref = _normalize_text(reply_transport_ref)
    if not reply_ref:
        return 1, {
            "build_status": STATUS_FAIL_REQUIRED,
            "agent_relay_final_answer_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-RELAY-001",
            "stale_reasons": ["reply_transport_ref_missing"],
        }
    source_artifact_path = Path(reply_ref).expanduser().resolve()
    try:
        source_snapshot_ts = datetime.fromtimestamp(
            source_artifact_path.stat().st_mtime,
            tz=timezone.utc,
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        source_snapshot_ts = ""
    question_tag = build_host_visible_final_channel_question_tag(
        run_id=run_id,
        reply_transport_ref=reply_ref,
    )
    receipt_path = build_host_visible_final_channel_receipt_path(
        pack_path=pack_path,
        run_id=run_id,
        now_token=now_token,
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    validation_output_path = receipt_path.with_name(receipt_path.stem + ".validation.json")
    completed = subprocess.run(
        [
            str(sys.executable or "python3"),
            str((repo_root / "scripts" / "build_agent_relay_final_answer.py").resolve()),
            "--mode",
            HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE,
            "--target-identity-id",
            _normalize_text(identity_id),
            "--question-tag",
            question_tag,
            "--source-artifact",
            str(source_artifact_path),
            "--source-snapshot-ts",
            source_snapshot_ts,
            "--output",
            str(receipt_path),
            "--validate",
            "--validation-output",
            str(validation_output_path),
            "--json-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = _parse_json_payload(completed.stdout)
    if not payload:
        payload = {
            "build_status": STATUS_FAIL_REQUIRED,
            "agent_relay_final_answer_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-RELAY-001",
            "stale_reasons": ["builder_stdout_not_json"],
            "builder_stderr": _normalize_text(completed.stderr),
        }
    if not _normalize_text(payload.get("receipt_path", "")):
        payload["receipt_path"] = str(receipt_path)
    if not _normalize_text(payload.get("question_tag", "")):
        payload["question_tag"] = question_tag
    if not _normalize_text(payload.get("source_artifact", "")):
        payload["source_artifact"] = str(source_artifact_path)
    if not _normalize_text(payload.get("relay_mode", "")):
        payload["relay_mode"] = HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE
    if not _normalize_text(payload.get("delivery_authority", "")):
        payload["delivery_authority"] = HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY
    return completed.returncode, payload


def project_host_visible_final_channel_relay_fields(payload: dict[str, Any]) -> dict[str, Any]:
    doc = payload if isinstance(payload, dict) else {}
    relay_status = _normalize_text(doc.get("agent_relay_final_answer_status", "")) or _normalize_text(
        doc.get("build_status", "")
    )
    return {
        "agent_relay_final_answer_receipt_path": _normalize_text(doc.get("receipt_path", "")),
        "agent_relay_final_answer_status": relay_status,
        "agent_relay_final_answer_relay_mode": _normalize_text(doc.get("relay_mode", "")),
        "agent_relay_final_answer_delivery_authority": _normalize_text(doc.get("delivery_authority", "")),
        "agent_relay_final_answer_source_artifact": _normalize_text(doc.get("source_artifact", "")),
        "agent_relay_final_answer_question_tag": _normalize_text(doc.get("question_tag", "")),
    }


def inspect_host_visible_final_channel_relay(
    *,
    receipt_doc: dict[str, Any],
    repo_root: Path,
    expected_identity_id: str = "",
    expected_source_artifact: str = "",
) -> dict[str, Any]:
    doc = receipt_doc if isinstance(receipt_doc, dict) else {}
    relay_fields = {
        field: _normalize_text(doc.get(field, ""))
        for field in FINAL_CHANNEL_RELAY_METADATA_FIELDS
    }
    result: dict[str, Any] = {
        "required": True,
        "status": STATUS_FAIL_REQUIRED,
        "reason": "relay_receipt_path_missing",
        "error_code": "",
        "receipt_path": relay_fields["agent_relay_final_answer_receipt_path"],
        "receipt_exists": False,
        "relay_mode": relay_fields["agent_relay_final_answer_relay_mode"],
        "delivery_authority": relay_fields["agent_relay_final_answer_delivery_authority"],
        "question_tag": relay_fields["agent_relay_final_answer_question_tag"],
        "source_artifact": relay_fields["agent_relay_final_answer_source_artifact"],
        "validation_status": STATUS_FAIL_REQUIRED,
        "validation_error_code": "",
        "validation_stale_reasons": [],
        "target_identity_id": "",
    }
    issues: list[str] = []

    for field, value in relay_fields.items():
        if not value:
            issues.append(f"{field}_missing")
    if relay_fields["agent_relay_final_answer_status"] != STATUS_PASS_REQUIRED:
        issues.append("relay_status_not_pass")
    if relay_fields["agent_relay_final_answer_relay_mode"] != HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE:
        issues.append(
            "relay_mode_invalid:"
            f"{relay_fields['agent_relay_final_answer_relay_mode'] or 'missing'}"
        )
    if relay_fields["agent_relay_final_answer_delivery_authority"] != HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY:
        issues.append(
            "delivery_authority_invalid:"
            f"{relay_fields['agent_relay_final_answer_delivery_authority'] or 'missing'}"
        )
    expected_source = _normalize_text(expected_source_artifact)
    if expected_source and relay_fields["agent_relay_final_answer_source_artifact"] != expected_source:
        issues.append("source_artifact_mismatch")

    receipt_path_text = relay_fields["agent_relay_final_answer_receipt_path"]
    if receipt_path_text:
        receipt_path = Path(receipt_path_text).expanduser().resolve()
        result["receipt_exists"] = receipt_path.exists()
        if not receipt_path.exists():
            issues.append("relay_receipt_missing")
        else:
            completed = subprocess.run(
                [
                    str(sys.executable or "python3"),
                    str((repo_root / "scripts" / "validate_agent_relay_final_answer.py").resolve()),
                    "--receipt",
                    str(receipt_path),
                    "--json-only",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            validation_payload = _parse_json_payload(completed.stdout)
            validation_status = _normalize_text(validation_payload.get("agent_relay_final_answer_status", ""))
            result["validation_status"] = validation_status or STATUS_FAIL_REQUIRED
            result["validation_error_code"] = _normalize_text(validation_payload.get("error_code", ""))
            result["validation_stale_reasons"] = [
                _normalize_text(item)
                for item in (validation_payload.get("stale_reasons") or [])
                if _normalize_text(item)
            ]
            result["target_identity_id"] = _normalize_text(validation_payload.get("target_identity_id", ""))
            if completed.returncode != 0 or validation_status != STATUS_PASS_REQUIRED:
                issues.append("relay_receipt_validation_not_pass")
            if _normalize_text(validation_payload.get("relay_surface", "")) != HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE:
                issues.append("relay_surface_invalid")
            if _normalize_text(validation_payload.get("relay_mode", "")) != HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE:
                issues.append("validator_relay_mode_invalid")
            if _normalize_text(validation_payload.get("delivery_authority", "")) != HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY:
                issues.append("validator_delivery_authority_invalid")
            validator_source_artifact = _normalize_text(validation_payload.get("source_artifact", ""))
            if expected_source and validator_source_artifact != expected_source:
                issues.append("validator_source_artifact_mismatch")
            expected_identity = _normalize_text(expected_identity_id)
            if expected_identity and _normalize_text(validation_payload.get("target_identity_id", "")) not in {
                "",
                expected_identity,
            }:
                issues.append("validator_target_identity_mismatch")

    if issues:
        result["reason"] = issues[0]
        result["issues"] = issues
        return result

    result["status"] = STATUS_PASS_REQUIRED
    result["reason"] = "exact_relay_validated"
    result["issues"] = []
    return result
