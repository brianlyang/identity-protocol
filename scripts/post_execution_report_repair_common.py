#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from capability_activation_projection_common import (
    CAPABILITY_ACTIVATION_REPORT_REQUIRED_FIELDS,
    build_capability_activation_report_projection,
)
from terminal_truth_cleanliness_common import project_terminal_truth_fields
from tool_vendor_governance_common import resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"
DEFAULT_OPERATION = "readiness"
CANONICAL_EXECUTION_CLOSEOUT_PREFIX = "identity-upgrade-exec-"
POST_EXECUTION_TERMINAL_TRUTH_OBSERVATION_FIELDS: tuple[str, ...] = (
    "execution_closure_status",
    "terminal_truth_cleanliness_status",
    "terminal_truth_class",
    "terminal_state_machine_status",
    "terminal_state_class",
    "negative_feedback_class",
    "negative_feedback_terminal_veto_status",
    "loopback_required",
    "next_state_after_veto",
    "publishable",
    "canonical_result_eligible",
    "dirty_signals",
    "terminal_truth_blockers",
    "placeholder_result_fields",
    "contradiction_fields",
    "confidence_blocker_fields",
)

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _clean_status_value(value: Any) -> str:
    return str(value or "").strip().upper()


def _clean_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for item in value:
        token = str(item or "").strip()
        if token:
            cleaned.append(token)
    return cleaned


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _canonical_execution_closeout_surface(path: Path | None = None, *, run_id: str = "") -> bool:
    path_match = False
    if isinstance(path, Path):
        name = path.name
        path_match = (
            name.startswith(CANONICAL_EXECUTION_CLOSEOUT_PREFIX)
            and name.endswith(".json")
            and not name.endswith("-patch-plan.json")
        )
    run_match = str(run_id or "").strip().startswith(CANONICAL_EXECUTION_CLOSEOUT_PREFIX)
    return path_match or run_match


def classify_post_execution_report_surface(
    *,
    report_doc: dict[str, Any],
    report_path: Path | None = None,
) -> dict[str, Any]:
    run_id = str((report_doc or {}).get("run_id", "")).strip()
    resolved_path = None
    if isinstance(report_path, Path):
        try:
            resolved_path = report_path.expanduser().resolve()
        except Exception:
            resolved_path = report_path
    canonical_path_match = False
    if isinstance(resolved_path, Path):
        name = resolved_path.name
        canonical_path_match = (
            name.startswith(CANONICAL_EXECUTION_CLOSEOUT_PREFIX)
            and name.endswith(".json")
            and not name.endswith("-patch-plan.json")
        )
    canonical_run_id_match = run_id.startswith(CANONICAL_EXECUTION_CLOSEOUT_PREFIX)
    closeout_shape_fields = [
        field
        for field in (
            "permission_state",
            "writeback_status",
            "writeback_mode",
            "next_action",
            "final_emit_channel_id",
        )
        if field in (report_doc or {})
    ]
    applicable = canonical_path_match or canonical_run_id_match
    if applicable:
        applicability_reason = (
            "canonical_execution_closeout_path"
            if canonical_path_match
            else "canonical_execution_closeout_run_id"
        )
        status = STATUS_PASS_REQUIRED
        report_surface_class = "canonical_execution_closeout"
    else:
        if closeout_shape_fields:
            applicability_reason = "closeout_shape_without_canonical_family_binding"
        elif resolved_path is not None:
            applicability_reason = "non_closeout_runtime_report_surface"
        elif run_id:
            applicability_reason = "non_closeout_runtime_run_id"
        else:
            applicability_reason = "report_surface_missing_canonical_execution_closeout_identity"
        status = STATUS_SKIPPED_NOT_REQUIRED
        report_surface_class = "non_closeout_runtime_surface"
    return {
        "status": status,
        "applicable": applicable,
        "report_surface_class": report_surface_class,
        "applicability_reason": applicability_reason,
        "source_report_path": str(resolved_path) if resolved_path is not None else "",
        "source_report_name": str(resolved_path.name) if resolved_path is not None else "",
        "source_run_id": run_id,
        "canonical_path_match": canonical_path_match,
        "canonical_run_id_match": canonical_run_id_match,
        "closeout_shape_fields_present": closeout_shape_fields,
    }


def _normalize_runtime_provenance(
    *,
    report_doc: dict[str, Any],
    catalog_path: Path,
    identity_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = dict(report_doc or {})
    changed_fields: list[str] = []
    try:
        resolved_pack_path, _ = resolve_pack_and_task(catalog_path, identity_id)
    except Exception as exc:
        return normalized, {
            "status": STATUS_FAIL_REQUIRED,
            "error": f"runtime_provenance_resolution_failed:{type(exc).__name__}",
            "changed_fields": [],
            "expected_catalog_path": str(catalog_path.resolve()),
            "expected_pack_path": "",
        }

    expected_catalog_path = str(catalog_path.resolve())
    expected_pack_path = str(resolved_pack_path.resolve())
    for key, expected in (
        ("identity_id", str(identity_id or "").strip()),
        ("catalog_path", expected_catalog_path),
        ("resolved_pack_path", expected_pack_path),
    ):
        current = str(normalized.get(key, "")).strip()
        if current != expected:
            normalized[key] = expected
            changed_fields.append(key)

    return normalized, {
        "status": STATUS_PASS_REQUIRED,
        "error": "",
        "changed_fields": changed_fields,
        "expected_catalog_path": expected_catalog_path,
        "expected_pack_path": expected_pack_path,
    }


def _run_json_validator(cmd: list[str]) -> tuple[int, dict[str, Any], str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    payload = _parse_json_payload(proc.stdout or "") or {}
    return proc.returncode, payload, proc.stdout or "", proc.stderr or ""


def _run_report_validator(
    *,
    validator_script: str,
    status_field: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    identity_id: str,
    report_path: Path,
    operation: str,
) -> dict[str, Any]:
    cmd = [
        "python3",
        str((SCRIPT_DIR / validator_script).resolve()),
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--identity-id",
        identity_id,
        "--report",
        str(report_path),
        "--operation",
        operation,
        "--json-only",
    ]
    rc, payload, stdout, stderr = _run_json_validator(cmd)
    status = str(payload.get(status_field, "")).strip().upper()
    if not status:
        status = STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    return {
        "cmd": cmd,
        "rc": rc,
        "status": status,
        "payload": payload,
        "stdout_tail": (stdout or "")[-400:],
        "stderr_tail": (stderr or "")[-400:],
    }


def _resolve_capability_activation_projection(
    *,
    catalog_path: Path,
    repo_catalog_path: Path,
    identity_id: str,
    work_layer: str = "",
    source_layer: str = "",
) -> dict[str, Any]:
    cmd = [
        "python3",
        str((SCRIPT_DIR / "validate_identity_capability_activation.py").resolve()),
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--identity-id",
        identity_id,
    ]
    if str(work_layer or "").strip():
        cmd.extend(["--work-layer", str(work_layer).strip()])
    if str(source_layer or "").strip():
        cmd.extend(["--source-layer", str(source_layer).strip()])
    rc, payload, stdout, stderr = _run_json_validator(cmd)
    projection = build_capability_activation_report_projection(payload) if payload else {}
    status = str(payload.get("capability_activation_status", "")).strip().upper()
    stale_reasons: list[str] = []
    if rc != 0:
        stale_reasons.append("capability_activation_validator_failed")
    if not payload:
        stale_reasons.append("capability_activation_payload_missing")
    return {
        "cmd": cmd,
        "rc": rc,
        "payload": payload,
        "projection": projection,
        "status": status,
        "stdout_tail": (stdout or "")[-400:],
        "stderr_tail": (stderr or "")[-400:],
        "stale_reasons": stale_reasons,
    }


def _project_and_validate_terminal_truth(
    *,
    report_doc: dict[str, Any],
    post_execution_status: str,
    writeback_continuity_status: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    identity_id: str,
    operation: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    projected = project_terminal_truth_fields(
        report_doc,
        post_execution_status=post_execution_status,
        writeback_continuity_status=writeback_continuity_status,
    )
    with tempfile.NamedTemporaryFile(
        prefix=f"postexec-terminal-truth-{identity_id}-",
        suffix=".json",
        delete=False,
    ) as tmp:
        tmp_path = Path(tmp.name).resolve()
    try:
        _write_json(tmp_path, projected)
        validator_result = _run_report_validator(
            validator_script="validate_terminal_truth_cleanliness.py",
            status_field="identity_terminal_truth_cleanliness_status",
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            identity_id=identity_id,
            report_path=tmp_path,
            operation=operation,
        )
        return projected, validator_result
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def build_post_execution_terminal_truth_observation_projection(
    report_doc: dict[str, Any] | None,
) -> dict[str, Any]:
    source = report_doc if isinstance(report_doc, dict) else {}
    return {
        "execution_closure_status": _clean_status_value(source.get("execution_closure_status"))
        or STATUS_UNKNOWN,
        "terminal_truth_cleanliness_status": _clean_status_value(
            source.get("terminal_truth_cleanliness_status")
        )
        or STATUS_UNKNOWN,
        "terminal_truth_class": str(source.get("terminal_truth_class", "") or "").strip(),
        "terminal_state_machine_status": _clean_status_value(
            source.get("terminal_state_machine_status")
        )
        or STATUS_UNKNOWN,
        "terminal_state_class": str(source.get("terminal_state_class", "") or "").strip(),
        "negative_feedback_class": str(source.get("negative_feedback_class", "") or "").strip(),
        "negative_feedback_terminal_veto_status": _clean_status_value(
            source.get("negative_feedback_terminal_veto_status")
        )
        or STATUS_UNKNOWN,
        "loopback_required": bool(source.get("loopback_required", False)),
        "next_state_after_veto": str(source.get("next_state_after_veto", "") or "").strip(),
        "publishable": bool(source.get("publishable", False)),
        "canonical_result_eligible": bool(source.get("canonical_result_eligible", False)),
        "dirty_signals": _clean_string_list(source.get("dirty_signals")),
        "terminal_truth_blockers": _clean_string_list(source.get("terminal_truth_blockers")),
        "placeholder_result_fields": _clean_string_list(
            source.get("placeholder_result_fields")
        ),
        "contradiction_fields": _clean_string_list(source.get("contradiction_fields")),
        "confidence_blocker_fields": _clean_string_list(
            source.get("confidence_blocker_fields")
        ),
    }


def enrich_post_execution_report(
    *,
    report_doc: dict[str, Any],
    report_path: Path | None = None,
    catalog_path: Path,
    repo_catalog_path: Path,
    identity_id: str,
    operation: str = DEFAULT_OPERATION,
    work_layer: str = "",
    source_layer: str = "",
) -> dict[str, Any]:
    report_before = dict(report_doc or {})
    report_after = dict(report_before)
    projection_applicability = classify_post_execution_report_surface(
        report_doc=report_before,
        report_path=report_path,
    )

    capability_missing_before = [
        field for field in CAPABILITY_ACTIVATION_REPORT_REQUIRED_FIELDS if field not in report_before
    ]
    if projection_applicability.get("applicable") is not True:
        return {
            "report_after": report_after,
            "report_changed": False,
            "changed_keys": [],
            "projection_applicability": projection_applicability,
            "runtime_provenance_normalization": {
                "status": STATUS_SKIPPED_NOT_REQUIRED,
                "error": "",
                "changed_fields": [],
                "expected_catalog_path": str(catalog_path.resolve()),
                "expected_pack_path": "",
            },
            "capability_activation_projection": {
                "status": STATUS_SKIPPED_NOT_REQUIRED,
                "skip_reason": projection_applicability.get("applicability_reason", ""),
                "payload": {},
                "projection": {},
                "stale_reasons": [],
            },
            "capability_activation_missing_fields_before": capability_missing_before,
            "capability_activation_missing_fields_after": list(capability_missing_before),
            "post_execution_validation": {
                "status": STATUS_SKIPPED_NOT_REQUIRED,
                "skip_reason": projection_applicability.get("applicability_reason", ""),
            },
            "writeback_continuity_validation": {
                "status": STATUS_SKIPPED_NOT_REQUIRED,
                "skip_reason": projection_applicability.get("applicability_reason", ""),
            },
            "experience_writeback_validation": {
                "status": STATUS_SKIPPED_NOT_REQUIRED,
                "skip_reason": projection_applicability.get("applicability_reason", ""),
            },
            "terminal_truth_validation": {
                "status": STATUS_SKIPPED_NOT_REQUIRED,
                "skip_reason": projection_applicability.get("applicability_reason", ""),
            },
            "stale_reasons": [],
        }
    report_after, runtime_provenance_normalization = _normalize_runtime_provenance(
        report_doc=report_after,
        catalog_path=catalog_path,
        identity_id=identity_id,
    )
    capability_result = _resolve_capability_activation_projection(
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
        identity_id=identity_id,
        work_layer=work_layer,
        source_layer=source_layer,
    )
    capability_projection = capability_result.get("projection") or {}
    if isinstance(capability_projection, dict):
        report_after.update(capability_projection)
    capability_missing_after = [
        field for field in CAPABILITY_ACTIVATION_REPORT_REQUIRED_FIELDS if field not in report_after
    ]

    with tempfile.NamedTemporaryFile(
        prefix=f"postexec-enrichment-{identity_id}-",
        suffix=".json",
        delete=False,
    ) as tmp:
        temp_report_path = Path(tmp.name).resolve()
    try:
        _write_json(temp_report_path, report_after)
        post_execution_result = _run_report_validator(
            validator_script="validate_post_execution_mandatory.py",
            status_field="post_execution_mandatory_status",
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            identity_id=identity_id,
            report_path=temp_report_path,
            operation=operation,
        )
        writeback_result = _run_report_validator(
            validator_script="validate_writeback_continuity.py",
            status_field="writeback_continuity_status",
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            identity_id=identity_id,
            report_path=temp_report_path,
            operation=operation,
        )
        experience_writeback_result = _run_report_validator(
            validator_script="validate_identity_experience_writeback.py",
            status_field="experience_writeback_validation_status",
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            identity_id=identity_id,
            report_path=temp_report_path,
            operation=operation,
        )
    finally:
        try:
            temp_report_path.unlink(missing_ok=True)
        except Exception:
            pass

    terminal_truth_projected, terminal_truth_result = _project_and_validate_terminal_truth(
        report_doc=report_after,
        post_execution_status=str(post_execution_result.get("status", "")),
        writeback_continuity_status=str(writeback_result.get("status", "")),
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
        identity_id=identity_id,
        operation=operation,
    )
    report_after = terminal_truth_projected
    terminal_truth_observation_projection = build_post_execution_terminal_truth_observation_projection(
        report_after
    )

    blocking_stale_reasons: list[str] = []
    observation_stale_reasons: list[str] = []
    blocking_stale_reasons.extend(list(capability_result.get("stale_reasons") or []))
    if capability_missing_after:
        blocking_stale_reasons.append("capability_activation_report_fields_unresolved")
    if str(runtime_provenance_normalization.get("status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        blocking_stale_reasons.append("runtime_provenance_normalization_failed")
    if str(post_execution_result.get("status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        blocking_stale_reasons.append("post_execution_validator_not_green_after_projection")
    if str(writeback_result.get("status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        blocking_stale_reasons.append("writeback_continuity_not_green_after_projection")
    experience_writeback_status = str(experience_writeback_result.get("status", "")).strip().upper()
    if experience_writeback_status not in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED}:
        blocking_stale_reasons.append("experience_writeback_not_green_after_projection")
    if str(terminal_truth_result.get("status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        observation_stale_reasons.append("terminal_truth_validator_not_green_after_projection")

    changed_keys = sorted(
        key
        for key in set(report_before.keys()) | set(report_after.keys())
        if report_before.get(key) != report_after.get(key)
    )

    return {
        "report_after": report_after,
        "report_changed": bool(changed_keys),
        "changed_keys": changed_keys,
        "projection_applicability": projection_applicability,
        "runtime_provenance_normalization": runtime_provenance_normalization,
        "capability_activation_projection": capability_result,
        "capability_activation_missing_fields_before": capability_missing_before,
        "capability_activation_missing_fields_after": capability_missing_after,
        "post_execution_validation": post_execution_result,
        "writeback_continuity_validation": writeback_result,
        "experience_writeback_validation": experience_writeback_result,
        "terminal_truth_validation": terminal_truth_result,
        "terminal_truth_observation_projection": terminal_truth_observation_projection,
        "repair_projection_status": STATUS_PASS_REQUIRED if not blocking_stale_reasons else STATUS_FAIL_REQUIRED,
        "stale_reasons": sorted(
            set(str(reason).strip() for reason in blocking_stale_reasons if str(reason).strip())
        ),
        "observation_stale_reasons": sorted(
            set(str(reason).strip() for reason in observation_stale_reasons if str(reason).strip())
        ),
    }
