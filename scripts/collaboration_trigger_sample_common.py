from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_SAMPLE_IDENTITY_ID = "sample-identity"
DEFAULT_SAMPLE_TASK_ID = "sample-task"
DEFAULT_SAMPLE_NOTIFY_CHANNEL = "ops-notification-router"
DEFAULT_SAMPLE_DETECTED_AT = "2026-02-21T15:15:00Z"
DEFAULT_SAMPLE_NOTIFIED_AT = DEFAULT_SAMPLE_DETECTED_AT

POSITIVE_SAMPLE_RELATIVE_PATH = Path("positive/collab-login-required-pass.json")
NEGATIVE_SAMPLE_RELATIVE_PATH = Path("negative/collab-delay-fail.json")


def _base_payload(
    *,
    identity_id: str,
    task_id: str,
    event_id: str,
    blocker_type: str,
    dedupe_key: str,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "identity_id": identity_id,
        "task_id": task_id,
        "blocker_type": blocker_type,
        "source": "sample_fixture",
        "detected_at": DEFAULT_SAMPLE_DETECTED_AT,
        "requires_human_collab": True,
        "next_action": "notify operator",
        "notified_at": DEFAULT_SAMPLE_NOTIFIED_AT,
        "notify_channel": DEFAULT_SAMPLE_NOTIFY_CHANNEL,
        "dedupe_key": dedupe_key,
    }


def collaboration_trigger_sample_payloads(
    *,
    identity_id: str = DEFAULT_SAMPLE_IDENTITY_ID,
    task_id: str = DEFAULT_SAMPLE_TASK_ID,
) -> dict[Path, dict[str, Any]]:
    identity_token = str(identity_id or DEFAULT_SAMPLE_IDENTITY_ID).strip() or DEFAULT_SAMPLE_IDENTITY_ID
    task_token = str(task_id or DEFAULT_SAMPLE_TASK_ID).strip() or DEFAULT_SAMPLE_TASK_ID

    positive = _base_payload(
        identity_id=identity_token,
        task_id=task_token,
        event_id=f"{identity_token}-collab-positive-001",
        blocker_type="auth_login_required",
        dedupe_key=f"{identity_token}-auth-login-required",
    )
    positive["state_change_bypass_dedupe"] = True
    positive["chat_receipt"] = {
        "emitted": True,
        "event_id": positive["event_id"],
        "blocker_type": positive["blocker_type"],
        "notified_at": positive["notified_at"],
        "channel": positive["notify_channel"],
        "dedupe_key": positive["dedupe_key"],
        "status": "SENT",
    }

    negative = _base_payload(
        identity_id=identity_token,
        task_id=task_token,
        event_id=f"{identity_token}-collab-negative-001",
        blocker_type="auth_login_required",
        dedupe_key=f"{identity_token}-auth-login-required-delayed",
    )
    negative["state_change_bypass_dedupe"] = False
    negative["chat_receipt"] = {
        "emitted": False,
        "event_id": negative["event_id"],
        "blocker_type": negative["blocker_type"],
        "notified_at": negative["notified_at"],
        "channel": negative["notify_channel"],
        "dedupe_key": negative["dedupe_key"],
        "status": "PENDING",
    }

    return {
        POSITIVE_SAMPLE_RELATIVE_PATH: positive,
        NEGATIVE_SAMPLE_RELATIVE_PATH: negative,
    }


def materialize_collaboration_trigger_samples(
    root: Path,
    *,
    identity_id: str = DEFAULT_SAMPLE_IDENTITY_ID,
    task_id: str = DEFAULT_SAMPLE_TASK_ID,
    apply: bool = True,
) -> dict[str, Any]:
    sample_root = Path(root).expanduser().resolve()
    changed_files: list[str] = []
    written_files: list[str] = []
    missing_before: list[str] = []
    file_rows: list[dict[str, Any]] = []

    for rel_path, payload in collaboration_trigger_sample_payloads(
        identity_id=identity_id,
        task_id=task_id,
    ).items():
        dst = (sample_root / rel_path).resolve()
        expected_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        existed_before = dst.exists()
        before_text = dst.read_text(encoding="utf-8", errors="ignore") if existed_before else ""
        changed = before_text != expected_text
        if not existed_before:
            missing_before.append(str(rel_path))
        if changed:
            changed_files.append(str(dst))
        if apply and changed:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(expected_text, encoding="utf-8")
            written_files.append(str(dst))
        file_rows.append(
            {
                "relative_path": str(rel_path),
                "path": str(dst),
                "existed_before": existed_before,
                "changed": changed,
                "applied": apply and changed,
            }
        )

    return {
        "sample_root": str(sample_root),
        "identity_id": identity_id,
        "task_id": task_id,
        "changed": bool(changed_files),
        "applied": bool(written_files),
        "changed_files": changed_files,
        "written_files": written_files,
        "missing_before": missing_before,
        "files": file_rows,
    }
