from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from repair_contract_backfill_status_profile_common import (
    CURRENT_RUN_PROJECTION_ENFORCEMENT_BLOCKING as ENFORCEMENT_BLOCKING,
    STATUS_PROFILE_STRICT_FULL,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _run_json_command(*, cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, dict[str, Any], str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd.resolve()),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = str(proc.stdout or "")
    stderr = str(proc.stderr or "")
    payload: dict[str, Any] = {}
    if stdout.strip():
        try:
            decoded = json.loads(stdout)
            if isinstance(decoded, dict):
                payload = decoded
        except Exception:
            payload = {}
    return proc.returncode, payload, stdout, stderr


def seed_invalid_active_execution_report(*, report_path: Path) -> str:
    report_path = report_path.expanduser().resolve()
    report_path.write_text('{"invalid_json":', encoding="utf-8")
    return str(report_path)


def validate_strict_profile_probe_payload(
    *,
    payload: dict[str, Any],
    expected_identity_id: str,
    expected_report_path: Path,
) -> dict[str, Any]:
    expected_identity_id = str(expected_identity_id).strip()
    expected_report = str(expected_report_path.expanduser().resolve())
    if str(payload.get("identity_id", "")).strip() != expected_identity_id:
        raise RuntimeError("strict_profile_identity_id_mismatch")
    if str(payload.get("contract_backfill_status", "")).strip() != STATUS_FAIL_REQUIRED:
        raise RuntimeError("strict_profile_did_not_fail_close")
    if str(payload.get("status_profile", "")).strip() != STATUS_PROFILE_STRICT_FULL:
        raise RuntimeError("strict_profile_label_missing")
    if str(payload.get("current_run_projection_enforcement_mode", "")).strip() != ENFORCEMENT_BLOCKING:
        raise RuntimeError("strict_profile_enforcement_mode_not_blocking")
    observation = payload.get("current_run_projection_observation_failures") or []
    if observation not in ([],):
        raise RuntimeError("strict_profile_observation_failures_not_empty")
    blocking = payload.get("current_run_projection_blocking_failures") or []
    if not any(
        item in blocking
        for item in ("current_run_terminal_truth_projection_failed", "current_run_weak_live_projection_failed")
    ):
        raise RuntimeError("strict_profile_blocking_failure_missing")
    terminal_truth = payload.get("current_run_terminal_truth_projection_backfill") or {}
    report_selected = str(terminal_truth.get("report_selected_path", "")).strip()
    if report_selected != expected_report:
        raise RuntimeError("strict_profile_report_selected_path_mismatch")
    return {
        "strict_profile_status": STATUS_FAIL_REQUIRED,
        "status_profile": STATUS_PROFILE_STRICT_FULL,
        "current_run_projection_enforcement_mode": ENFORCEMENT_BLOCKING,
        "current_run_projection_blocking_failures": blocking,
        "current_run_projection_observation_failures": observation,
        "report_selected_path": report_selected,
    }


def run_repair_contract_backfill_strict_profile_probe(
    *,
    repo_root: Path,
    workspace_root: Path,
    catalog_arg: str,
    identity_id: str,
    report_path: Path,
    codex_home: Path,
) -> dict[str, Any]:
    repo_root = repo_root.expanduser().resolve()
    workspace_root = workspace_root.expanduser().resolve()
    report_path = Path(seed_invalid_active_execution_report(report_path=report_path))
    env = os.environ.copy()
    env.pop("IDENTITY_HOME", None)
    env.pop("IDENTITY_CATALOG", None)
    env.pop("IDENTITY_PROTOCOL_HOME", None)
    env["IDENTITY_PROTOCOL_HOME"] = str(repo_root)
    env["CODEX_HOME"] = str(codex_home.expanduser().resolve())
    cmd = [
        sys.executable,
        str((repo_root / "scripts" / "repair_contract_backfill.py").resolve()),
        "--catalog",
        str(catalog_arg),
        "--identity-id",
        str(identity_id).strip(),
        "--json-only",
    ]
    rc, payload, stdout, stderr = _run_json_command(cmd=cmd, cwd=workspace_root, env=env)
    if rc == 0:
        raise RuntimeError("strict_profile_probe_unexpected_success")
    projection = validate_strict_profile_probe_payload(
        payload=payload,
        expected_identity_id=str(identity_id).strip(),
        expected_report_path=report_path,
    )
    return {
        "status": STATUS_PASS_REQUIRED,
        "seeded_report_path": str(report_path),
        "strict_profile_probe": projection,
        "strict_profile_payload": payload,
        "repair_contract_backfill_rc": rc,
        "stdout_captured": bool(stdout.strip()),
        "stderr_captured": bool(stderr.strip()),
    }
