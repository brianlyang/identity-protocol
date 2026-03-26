#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
LAUNCHER_RUNTIME_ADMISSIBILITY_PROFILE = "launcher_outer_surface"
LAUNCHER_RUNTIME_ADMISSIBILITY_ENV_CATALOG_MISMATCH_MODE = "observe"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_reasons(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    reasons: list[str] = []
    for value in values:
        token = _clean_text(value)
        if token and token not in reasons:
            reasons.append(token)
    return reasons


def _fallback_runtime_mode_guard_payload(
    *,
    catalog_path: Path,
    identity_id: str,
    structural_reason: str,
    raw_stdout: str = "",
    raw_stderr: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "runtime_mode_guard_status": STATUS_FAIL_REQUIRED,
        "error_code": "IP-ENV-002",
        "identity_id": _clean_text(identity_id),
        "catalog_path": str(catalog_path.resolve()),
        "binding_class": structural_reason,
        "stale_reasons": [structural_reason],
    }
    if _clean_text(raw_stdout):
        payload["raw_stdout"] = raw_stdout
    if _clean_text(raw_stderr):
        payload["raw_stderr"] = raw_stderr
    return payload


def run_launcher_runtime_mode_guard(
    *,
    identity_id: str,
    catalog_path: Path,
    protocol_home: Path,
    operation: str,
) -> tuple[int, dict[str, Any]]:
    repo_catalog_path = (protocol_home / "identity" / "catalog" / "identities.yaml").resolve()
    cmd = [
        sys.executable,
        str((protocol_home / "scripts" / "validate_identity_runtime_mode_guard.py").resolve()),
        "--identity-id",
        _clean_text(identity_id),
        "--catalog",
        str(catalog_path.resolve()),
        "--repo-catalog",
        str(repo_catalog_path),
        "--expect-mode",
        "auto",
        "--operation",
        _clean_text(operation) or "inspection",
        "--admissibility-profile",
        LAUNCHER_RUNTIME_ADMISSIBILITY_PROFILE,
        "--env-catalog-mismatch-mode",
        LAUNCHER_RUNTIME_ADMISSIBILITY_ENV_CATALOG_MISMATCH_MODE,
        "--json-only",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(protocol_home.resolve()),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = _clean_text(proc.stdout)
    if not stdout:
        return 1, _fallback_runtime_mode_guard_payload(
            catalog_path=catalog_path,
            identity_id=identity_id,
            structural_reason="runtime_mode_guard_payload_missing",
            raw_stdout=str(proc.stdout or ""),
            raw_stderr=str(proc.stderr or ""),
        )
    try:
        decoded = json.loads(stdout)
    except Exception:
        return 1, _fallback_runtime_mode_guard_payload(
            catalog_path=catalog_path,
            identity_id=identity_id,
            structural_reason="runtime_mode_guard_payload_unparseable",
            raw_stdout=str(proc.stdout or ""),
            raw_stderr=str(proc.stderr or ""),
        )
    if not isinstance(decoded, dict):
        return 1, _fallback_runtime_mode_guard_payload(
            catalog_path=catalog_path,
            identity_id=identity_id,
            structural_reason="runtime_mode_guard_payload_not_object",
            raw_stdout=str(proc.stdout or ""),
            raw_stderr=str(proc.stderr or ""),
        )
    return proc.returncode, decoded


def build_launcher_runtime_admissibility_projection(
    *,
    identity_id: str,
    catalog_path: Path,
    protocol_home: Path,
    operation: str,
) -> dict[str, Any]:
    guard_rc, guard_payload = run_launcher_runtime_mode_guard(
        identity_id=identity_id,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
        operation=operation,
    )
    guard_status = _clean_text(guard_payload.get("runtime_mode_guard_status")).upper() or STATUS_FAIL_REQUIRED
    error_code = _clean_text(guard_payload.get("error_code"))
    binding_class = _clean_text(guard_payload.get("binding_class"))
    runtime_stale_reasons = _clean_reasons(guard_payload.get("stale_reasons"))

    projection_stale_reasons: list[str] = []
    if guard_status not in {STATUS_PASS_REQUIRED, STATUS_FAIL_REQUIRED}:
        projection_stale_reasons.append("runtime_mode_guard_status_missing")
    if guard_status == STATUS_FAIL_REQUIRED and not (binding_class or error_code):
        projection_stale_reasons.append("runtime_mode_guard_failure_reason_missing")

    admissibility_status = (
        STATUS_PASS_REQUIRED
        if guard_rc == 0 and guard_status == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED
    )
    admissibility_reason = (
        "runtime_catalog_admitted"
        if admissibility_status == STATUS_PASS_REQUIRED
        else (binding_class or error_code or "runtime_mode_guard_blocked")
    )
    projection_status = STATUS_PASS_REQUIRED if not projection_stale_reasons else STATUS_FAIL_REQUIRED

    return {
        "launcher_runtime_admissibility_projection_status": projection_status,
        "launcher_runtime_admissibility_status": admissibility_status,
        "launcher_runtime_admissibility_reason": admissibility_reason,
        "launcher_runtime_admissibility_operation": _clean_text(operation) or "inspection",
        "launcher_runtime_admissibility_profile": LAUNCHER_RUNTIME_ADMISSIBILITY_PROFILE,
        "launcher_runtime_admissibility_env_catalog_mismatch_mode": (
            LAUNCHER_RUNTIME_ADMISSIBILITY_ENV_CATALOG_MISMATCH_MODE
        ),
        "runtime_mode_guard_status": guard_status,
        "runtime_mode_guard_error_code": error_code,
        "runtime_mode_guard_binding_class": binding_class,
        "runtime_mode_guard_rc": int(guard_rc),
        "runtime_mode_guard_stale_reasons": runtime_stale_reasons,
        "owner_boundary_note": (
            "derived outer-surface projection only; runtime-mode guard remains the semantic owner "
            "for admissibility truth and launcher surfaces must not relabel mismatch semantics"
        ),
        "stale_reasons": projection_stale_reasons,
        "runtime_mode_guard_payload": guard_payload,
    }
