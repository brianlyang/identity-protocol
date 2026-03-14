#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actor_session_common import load_actor_binding, resolve_actor_id
from gateway_wrapper_enforcement import run_gateway_wrapped_command as _run_gateway_wrapped_command
from protocol_infra_contract import (
    CANONICAL_FINAL_EMIT_SCRIPT,
    CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
)
from response_stamp_common import DEFAULT_WORK_LAYER, resolve_layer_intent
from resolve_identity_context import resolve_identity
from runtime_temp_path_common import named_temp_root, runtime_temp_file

PROTOCOL_ROOT = Path(__file__).resolve().parent.parent
LOCK_PROTOCOL_PREFIX = "SESSION_LANE_LOCK_PROTOCOL_"
LOCK_EXIT_PREFIX = "SESSION_LANE_LOCK_EXIT_"
IP_ERROR_CODE_RE = re.compile(r"\b(IP-[A-Z0-9-]+)\b")
FINAL_EMIT_SCRIPT = CANONICAL_FINAL_EMIT_SCRIPT
REQUIRED_GATE_BUNDLE_SCRIPT = CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT
SESSION_ID_FALLBACK = ""

M2M_VALIDATOR_NAMES: set[str] = {
    "actor_session_binding",
    "actor_session_multibinding_concurrency",
    "no_implicit_switch",
    "cross_actor_isolation",
    "response_stamp_validation",
    "reply_identity_context_first_line",
    "send_time_reply_gate",
    "headstamp_recurrence_closure",
    "execution_reply_identity_coherence",
    "required_gate_tuple_parity",
    "execution_target_tuple_isolation",
}
BUNDLE_GATE_VALIDATOR_NAMES: set[str] = {
    "required_gate_bundle_runner",
    "required_gate_bundle_runner_shadow",
}
CAPABILITY_VALIDATOR_NAMES: set[str] = {
    "capability_activation",
    "prompt_bootstrap_capability",
    "prompt_capability_matrix",
    "prompt_kernel_executable_coupling",
}
RELEASE_ENV_VALIDATOR_NAMES: set[str] = {
    "release_plane_cloud_evidence",
    "run_id_report_selection",
    "outlet_regression_matrix",
}
BASELINE_VALIDATOR_NAMES: set[str] = {
    "session_refresh_status",
    "execution_report_freshness",
    "protocol_baseline_freshness",
    "protocol_version_alignment",
}
PROTOCOL_FEEDBACK_OBS_VALIDATOR_NAMES: set[str] = {
    "protocol_feedback_sidecar",
    "protocol_feedback_reply_channel",
    "protocol_feedback_bootstrap_ready",
}
DOWNSINK_PATH_GOVERNANCE_VALIDATOR_NAMES: set[str] = {
    "downsink_path_immutability",
    "downsink_path_write_guard",
    "downsink_path_literal_lock",
}
VALIDATOR_ERROR_CODE_KEYS: tuple[str, ...] = (
    "error_code",
    "sidecar_error_code",
    "capability_activation_error_code",
    "pin_error_code",
    "baseline_error_code",
    "freshness_error_code",
    "normalization_error_code",
    "semantic_convergence_error_code",
)
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
TUPLE_CONTEXT_PRIMARY_MARKERS: set[str] = {
    "entry_receipt_operation_mismatch",
    "entry_receipt_run_id_mismatch",
    "entry_receipt_actor_id_mismatch",
    "entry_receipt_session_id_mismatch",
}
TUPLE_CONTEXT_ALLOWED_MARKERS: set[str] = {
    *TUPLE_CONTEXT_PRIMARY_MARKERS,
    "entry_receipt_bundle_status_not_pass",
}


def _run(cmd: list[str], *, cwd: Path | None = None) -> tuple[int, str, str]:
    run_cmd = list(cmd)
    run_cwd = cwd.resolve() if isinstance(cwd, Path) else PROTOCOL_ROOT
    if "--session-id" not in run_cmd and SESSION_ID_FALLBACK:
        script = str(run_cmd[1]).strip() if len(run_cmd) >= 2 else ""
        if script in {REQUIRED_GATE_BUNDLE_SCRIPT, FINAL_EMIT_SCRIPT}:
            run_cmd.extend(["--session-id", SESSION_ID_FALLBACK])
    rc, out, err = _run_gateway_wrapped_command(
        cmd=run_cmd,
        protocol_root=PROTOCOL_ROOT,
        passthrough_cwd=run_cwd,
    )
    return rc, (out or "").strip(), (err or "").strip()


def _extract_error_code_from_validator(entry: dict[str, Any]) -> str:
    payload = _parse_json_payload(str(entry.get("out", ""))) or {}
    for key in VALIDATOR_ERROR_CODE_KEYS:
        token = str(payload.get(key, "")).strip()
        if token:
            return token
    for blob_key in ("out", "err"):
        blob = str(entry.get(blob_key, "") or "")
        m = IP_ERROR_CODE_RE.search(blob)
        if m:
            return str(m.group(1) or "").strip()
    return ""


def _is_m2m_error_code(error_code: str) -> bool:
    token = str(error_code or "").strip().upper()
    if not token:
        return False
    return (
        token.startswith("IP-ASB-")
        or token.startswith("IP-ACTOR-")
        or token.startswith("IP-FE-")
        or token.startswith("IP-HDSTAMP-")
    )


def _is_m2m_failure_row(*, validator_name: str, error_code: str) -> bool:
    if validator_name in BUNDLE_GATE_VALIDATOR_NAMES and not _is_m2m_error_code(error_code):
        return False
    return validator_name in M2M_VALIDATOR_NAMES or _is_m2m_error_code(error_code)


def _classify_m2m_projection(
    *,
    validators: dict[str, Any],
    instance_status: str,
    repo_status: str,
    release_status: str,
) -> dict[str, Any]:
    failed: list[dict[str, str]] = []
    for name, raw in (validators or {}).items():
        entry = raw if isinstance(raw, dict) else {}
        if bool(entry.get("ok", False)):
            continue
        error_code = _extract_error_code_from_validator(entry)
        failed.append(
            {
                "validator": str(name),
                "error_code": error_code,
            }
        )

    m2m_failed = [
        row
        for row in failed
        if _is_m2m_failure_row(
            validator_name=str(row.get("validator", "")),
            error_code=str(row.get("error_code", "")),
        )
    ]
    non_m2m_failed = [row for row in failed if row not in m2m_failed]

    non_m2m_scope: list[str] = []
    if any(
        row["validator"] in CAPABILITY_VALIDATOR_NAMES or str(row.get("error_code", "")).upper().startswith("IP-CAP-")
        for row in non_m2m_failed
    ):
        non_m2m_scope.append("instance_capability")
    if any(row["validator"] in RELEASE_ENV_VALIDATOR_NAMES for row in non_m2m_failed):
        non_m2m_scope.append("release_env")
    if any(
        row["validator"] in BASELINE_VALIDATOR_NAMES or str(row.get("error_code", "")).upper().startswith("IP-PBL-")
        for row in non_m2m_failed
    ):
        non_m2m_scope.append("baseline_refresh")
    if any(row["validator"] in PROTOCOL_FEEDBACK_OBS_VALIDATOR_NAMES for row in non_m2m_failed):
        non_m2m_scope.append("protocol_feedback_observability")
    if any(row["validator"] in DOWNSINK_PATH_GOVERNANCE_VALIDATOR_NAMES for row in non_m2m_failed):
        non_m2m_scope.append("downsink_path_immutability")
    if repo_status != "CLOSED":
        non_m2m_scope.append("repo_plane")
    if release_status != "CLOSED":
        non_m2m_scope.append("release_plane")
    if instance_status != "CLOSED" and non_m2m_failed and "instance_plane" not in non_m2m_scope:
        non_m2m_scope.append("instance_plane")
    if non_m2m_failed and not non_m2m_scope:
        non_m2m_scope.append("other")

    return {
        "m2m_binding_closure_status": "PASS" if not m2m_failed else "FAIL",
        "m2m_failure_scope": "protocol_m2m" if m2m_failed else "",
        "m2m_failed_validator_count": len(m2m_failed),
        "m2m_failed_validators": m2m_failed,
        "m2m_failure_reasons": [
            f"{row['validator']}:{row.get('error_code') or 'UNKNOWN'}"
            for row in m2m_failed
        ],
        "non_m2m_failed_validator_count": len(non_m2m_failed),
        "non_m2m_failed_validators": non_m2m_failed,
        "non_m2m_failure_scope": sorted(set(non_m2m_scope)),
        "non_m2m_failure_reasons": [
            f"{row['validator']}:{row.get('error_code') or 'UNKNOWN'}"
            for row in non_m2m_failed
        ],
        "failed_validator_count_total": len(failed),
    }


def _is_tuple_context_only_stale_reasons(stale_reasons: list[str]) -> bool:
    tokens = [str(x).strip() for x in stale_reasons if str(x).strip()]
    if not tokens:
        return False
    primary_detected = False
    for token in tokens:
        if token in TUPLE_CONTEXT_PRIMARY_MARKERS:
            primary_detected = True
            continue
        if token in TUPLE_CONTEXT_ALLOWED_MARKERS:
            continue
        if token.startswith("entry_receipt_required_fields_missing:"):
            primary_detected = True
            continue
        return False
    return primary_detected


def _classify_tuple_context_projection(*, validators: dict[str, Any]) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    tuple_rows: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    for name, raw in (validators or {}).items():
        entry = raw if isinstance(raw, dict) else {}
        payload = _parse_json_payload(str(entry.get("out", ""))) or {}
        if isinstance(payload, dict):
            tuple_rows.append((str(name), entry, payload))

    coverage_entry = (validators or {}).get("required_contract_coverage")
    coverage_payload = _parse_json_payload(
        str((coverage_entry or {}).get("out", "")) if isinstance(coverage_entry, dict) else ""
    ) or {}
    for contract_row in (coverage_payload.get("contracts") or []):
        if not isinstance(contract_row, dict):
            continue
        if str(contract_row.get("name", "")).strip() != "protocol_unique_entry_gate":
            continue
        tail_payload = _parse_json_payload(str(contract_row.get("validator_tail", ""))) or {}
        if not isinstance(tail_payload, dict):
            continue
        tuple_rows.append(
            (
                "protocol_unique_entry_gate:coverage",
                {
                    "rc": 0
                    if str(contract_row.get("validator_status", "")).strip().upper() == STATUS_PASS_REQUIRED
                    else 1,
                    "ok": str(contract_row.get("validator_status", "")).strip().upper() == STATUS_PASS_REQUIRED,
                    "out": json.dumps(tail_payload, ensure_ascii=False),
                    "err": "",
                    "error_code": str(tail_payload.get("error_code", "")).strip()
                    or str(contract_row.get("reason_code", "")).strip(),
                },
                tail_payload,
            )
        )

    for name, entry, payload in tuple_rows:
        tuple_only = bool(payload.get("protocol_unique_entry_receipt_tuple_context_only_failure", False))
        if not tuple_only:
            tuple_status = str(
                payload.get("protocol_unique_entry_receipt_tuple_context_status", "")
            ).strip().upper()
            stale_reasons = [
                str(x).strip()
                for x in (payload.get("stale_reasons") or [])
                if str(x).strip()
            ]
            if tuple_status == STATUS_FAIL_REQUIRED and _is_tuple_context_only_stale_reasons(stale_reasons):
                tuple_only = True
        if not tuple_only:
            continue
        mismatch_fields = [
            str(x).strip()
            for x in (payload.get("protocol_unique_entry_receipt_tuple_context_mismatch_fields") or [])
            if str(x).strip()
        ]
        matches.append(
            {
                "validator": str(name),
                "error_code": _extract_error_code_from_validator(entry),
                "mismatch_fields": sorted(set(mismatch_fields)),
            }
        )
    return {
        "tuple_context_status": STATUS_PASS_REQUIRED if not matches else STATUS_FAIL_REQUIRED,
        "tuple_context_only_failure": bool(matches),
        "tuple_context_only_failure_count": len(matches),
        "tuple_context_only_failure_validators": matches,
    }


def _build_governance_closure_axes(
    *,
    instance_status: str,
    repo_status: str,
    release_status: str,
    m2m_projection: dict[str, Any],
    tuple_context_projection: dict[str, Any],
) -> dict[str, Any]:
    normalized_instance = str(instance_status or "").strip().upper()
    normalized_repo = str(repo_status or "").strip().upper()
    normalized_release = str(release_status or "").strip().upper()
    m2m_status = str(m2m_projection.get("m2m_binding_closure_status", "")).strip().upper()
    infra_pass = normalized_repo == "CLOSED" and m2m_status == "PASS"
    runtime_pass = normalized_instance == "CLOSED"
    release_pass = normalized_release == "CLOSED"
    tuple_context_status = str(tuple_context_projection.get("tuple_context_status", "")).strip().upper()
    tuple_context_pass = tuple_context_status != STATUS_FAIL_REQUIRED
    reasons: list[str] = []
    if normalized_repo != "CLOSED":
        reasons.append(f"repo_plane_not_closed:{normalized_repo or 'UNKNOWN'}")
    if m2m_status != "PASS":
        reasons.append(f"m2m_binding_not_pass:{m2m_status or 'UNKNOWN'}")
    if normalized_instance != "CLOSED":
        reasons.append(f"instance_plane_not_closed:{normalized_instance or 'UNKNOWN'}")
    if normalized_release != "CLOSED":
        reasons.append(f"release_plane_not_closed:{normalized_release or 'UNKNOWN'}")
    if not tuple_context_pass:
        tuple_validators = [
            str(row.get("validator", "")).strip()
            for row in (tuple_context_projection.get("tuple_context_only_failure_validators") or [])
            if str(row.get("validator", "")).strip()
        ]
        reason = "tuple_context_only_failure_detected"
        if tuple_validators:
            reason += ":" + ",".join(sorted(set(tuple_validators)))
        reasons.append(reason)
    return {
        "infrastructure_closure_status": STATUS_PASS_REQUIRED if infra_pass else STATUS_FAIL_REQUIRED,
        "runtime_readiness_status": STATUS_PASS_REQUIRED if runtime_pass else STATUS_FAIL_REQUIRED,
        "release_readiness_status": STATUS_PASS_REQUIRED if release_pass else STATUS_FAIL_REQUIRED,
        "tuple_context_consistency_status": STATUS_PASS_REQUIRED if tuple_context_pass else STATUS_FAIL_REQUIRED,
        "decision_mode": "FULL_GO" if (infra_pass and runtime_pass and release_pass) else "CONDITIONAL_GO",
        "conditional_reasons": reasons,
    }


def _tracked_worktree_state() -> tuple[bool, list[str], str]:
    rc, out, err = _run(["git", "status", "--porcelain"])
    if rc != 0:
        return False, [], (err or out or "git_status_failed")
    rows = [ln for ln in out.splitlines() if ln.strip()]
    tracked_dirty = [ln for ln in rows if not ln.startswith("??")]
    return len(tracked_dirty) == 0, tracked_dirty[:20], ""


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _resolve_applied_gate_set(*, layer_intent_text: str, expected_work_layer: str, expected_source_layer: str) -> str:
    resolved = resolve_layer_intent(
        explicit_work_layer=str(expected_work_layer or "").strip(),
        explicit_source_layer=str(expected_source_layer or "").strip(),
        intent_text=str(layer_intent_text or "").strip(),
        default_work_layer=DEFAULT_WORK_LAYER,
        default_source_layer="project",
    )
    work_layer = str(resolved.get("resolved_work_layer", DEFAULT_WORK_LAYER)).strip().lower() or DEFAULT_WORK_LAYER
    if work_layer == "protocol":
        return "protocol_required_checks"
    if work_layer == "instance":
        return "instance_required_checks"
    return "dual_unroutable"


def _load_json(path: str) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"json file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


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


def _safe_json_file(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _latest_lane_receipt(*, outbox_dir: Path, prefix: str, identity_id: str) -> Path | None:
    if not outbox_dir.exists():
        return None
    rows = sorted(outbox_dir.glob(f"{prefix}*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in rows:
        doc = _safe_json_file(p)
        rid = str(doc.get("identity_id", "")).strip()
        if rid and rid != identity_id:
            continue
        return p.resolve()
    return None


def _detect_session_lane_lock(
    *,
    catalog_path: Path,
    identity_id: str,
    actor_id: str,
    session_id: str,
    resolved_pack_path: Path | None,
) -> str:
    try:
        binding = load_actor_binding(
            catalog_path,
            actor_id,
            identity_id=identity_id,
            session_id=session_id,
        )
    except Exception:
        binding = {}
    for key in ("session_lane_lock", "lane_lock", "work_layer_lock"):
        token = str(binding.get(key, "")).strip().lower()
        if token in {"protocol", "instance"}:
            return token

    if resolved_pack_path is None:
        return ""
    outbox_dir = (resolved_pack_path / "runtime" / "protocol-feedback" / "outbox-to-protocol").resolve()
    lock_protocol = _latest_lane_receipt(outbox_dir=outbox_dir, prefix=LOCK_PROTOCOL_PREFIX, identity_id=identity_id)
    lock_exit = _latest_lane_receipt(outbox_dir=outbox_dir, prefix=LOCK_EXIT_PREFIX, identity_id=identity_id)
    if lock_protocol is None:
        return ""
    protocol_mtime = lock_protocol.stat().st_mtime
    exit_mtime = lock_exit.stat().st_mtime if lock_exit is not None else -1.0
    if exit_mtime > protocol_mtime:
        return ""
    return "protocol"


def _latest_report(identity_id: str, identity_home: str = "", preferred_pack: str = "") -> Path | None:
    roots: list[Path] = []
    if preferred_pack.strip():
        pack = Path(preferred_pack).expanduser().resolve()
        roots.append(pack / "runtime" / "reports")
        roots.append(pack / "runtime")
    roots.extend(
        [
            named_temp_root("identity-upgrade-reports"),
            named_temp_root("identity-runtime"),
        ]
    )
    if identity_home.strip():
        roots.append(Path(identity_home).expanduser().resolve())
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        candidates.extend(root.glob(f"**/identity-upgrade-exec-{identity_id}-*.json"))
    filtered = [p for p in candidates if not p.name.endswith("-patch-plan.json")]
    if not filtered:
        return None
    filtered.sort(key=lambda p: p.stat().st_mtime)
    return filtered[-1]


def _release_plane_status(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if args.checks_json:
        checks_doc = _load_json(args.checks_json)
        raw = checks_doc.get("required_checks_set", [])
        if isinstance(raw, list):
            checks = [x for x in raw if isinstance(x, dict)]

    if not args.required_gates_run_id:
        detail = {
            "conditions": {
                "target_branch_explicit": bool(args.target_branch),
                "release_head_sha_explicit": bool(args.release_head_sha),
                "required_gates_run_id_accessible": False,
                "run_head_matches_release_head": False,
                "required_checks_all_success": False,
                "workflow_file_sha_matches": False,
            },
            "required_checks_set": checks,
        }
        return "NOT_STARTED", detail

    cond = {
        "target_branch_explicit": bool(args.target_branch),
        "release_head_sha_explicit": bool(args.release_head_sha),
        "required_gates_run_id_accessible": bool(args.required_gates_run_id and args.run_url),
        "run_head_matches_release_head": args.run_head_sha == args.release_head_sha and bool(args.run_head_sha),
        "required_checks_all_success": bool(checks) and all(str(x.get("status", "")).lower() == "success" for x in checks),
        "workflow_file_sha_matches": args.run_workflow_file_sha == args.workflow_file_sha and bool(args.workflow_file_sha),
    }
    return ("CLOSED" if all(cond.values()) else "BLOCKED"), {"conditions": cond, "required_checks_set": checks}


def _repo_plane_status(args: argparse.Namespace, resolved: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    workspace_clean, workspace_dirty_entries, workspace_status_error = _tracked_worktree_state()
    checks: dict[str, Any] = {
        "catalog_explicit": bool(args.catalog and Path(args.catalog).exists()),
        "resolved_scope_known": str(resolved.get("resolved_scope", "")).upper() != "UNKNOWN",
        "conflict_detected": bool(resolved.get("conflict_detected", False)),
        "workspace_clean": workspace_clean,
        "workspace_dirty_entries": workspace_dirty_entries,
        "workspace_status_error": workspace_status_error,
    }
    if args.with_docs_contract:
        rc, out, err = _run(["python3", "scripts/docs_command_contract_check.py"])
        checks["docs_command_contract"] = {
            "rc": rc,
            "ok": rc == 0,
            "stdout_tail": out.splitlines()[-1] if out else "",
            "stderr_tail": err.splitlines()[-1] if err else "",
        }
    status = "CLOSED"
    if checks["conflict_detected"]:
        status = "BLOCKED"
    if not checks["catalog_explicit"] or not checks["resolved_scope_known"]:
        status = "BLOCKED"
    if not checks["workspace_clean"] or checks["workspace_status_error"]:
        status = "BLOCKED"
    if args.with_docs_contract and not checks["docs_command_contract"]["ok"]:
        status = "BLOCKED"
    return status, checks


def _instance_plane_status(
    args: argparse.Namespace,
    report_path: Path | None,
    resolved: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    if report_path is None:
        return "NOT_STARTED", {"reason": "execution_report_not_found"}

    data = _load_json(str(report_path))
    ew = data.get("experience_writeback") or {}
    mandatory = all(
        k in data
        for k in (
            "permission_state",
            "writeback_status",
            "next_action",
            "skills_used",
            "mcp_tools_used",
            "tool_calls_used",
            "capability_activation_status",
            "capability_activation_error_code",
        )
    ) and isinstance(ew, dict) and (
        "status" in ew and "error_code" in ew
    )
    wb = str(data.get("writeback_status", "")).strip()
    ps = str(data.get("permission_state", "")).strip()
    all_ok = _bool(data.get("all_ok", False))
    err_code = str((ew.get("error_code", "") or data.get("permission_error_code", ""))).strip()
    next_action = str(data.get("next_action", "")).strip()
    report_run_id = str(data.get("run_id", "")).strip()
    current_round_anchor_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cap_status = str(data.get("capability_activation_status", "")).strip().upper()
    cap_error = str(data.get("capability_activation_error_code", "")).strip()
    hard_boundary = err_code.startswith("IP-PATH-") or err_code.startswith("IP-PERM-")

    validators: dict[str, Any] = {}
    layer_intent_text = str(getattr(args, "layer_intent_text", "") or "").strip()
    expected_work_layer = str(getattr(args, "expected_work_layer", "") or "").strip().lower()
    expected_source_layer = str(getattr(args, "expected_source_layer", "") or "").strip().lower()
    actor_id = resolve_actor_id(str(getattr(args, "actor_id", "") or "").strip())
    resolved_ctx = resolved or {}
    resolved_source_hint = str(resolved_ctx.get("source_layer", "") or "").strip().lower()
    effective_source_layer = expected_source_layer or (
        resolved_source_hint if resolved_source_hint in {"project", "global"} else "project"
    )
    resolved_pack_token = str(resolved_ctx.get("resolved_pack_path") or resolved_ctx.get("pack_path") or "").strip()
    resolved_pack_path: Path | None = None
    if resolved_pack_token:
        try:
            resolved_pack_path = Path(resolved_pack_token).expanduser().resolve()
        except Exception:
            resolved_pack_path = None
    lane_lock_hint = _detect_session_lane_lock(
        catalog_path=Path(args.catalog).expanduser().resolve(),
        identity_id=args.identity_id,
        actor_id=actor_id,
        session_id=str(getattr(args, "session_id", "") or "").strip(),
        resolved_pack_path=resolved_pack_path,
    )
    effective_work_layer = expected_work_layer
    if not effective_work_layer:
        inferred = resolve_layer_intent(
            explicit_work_layer="",
            explicit_source_layer=effective_source_layer,
            intent_text=layer_intent_text,
            default_work_layer=DEFAULT_WORK_LAYER,
            default_source_layer=effective_source_layer,
        )
        effective_work_layer = (
            str(inferred.get("resolved_work_layer", DEFAULT_WORK_LAYER)).strip().lower() or DEFAULT_WORK_LAYER
        )
    if not expected_work_layer and lane_lock_hint in {"protocol", "instance"}:
        effective_work_layer = lane_lock_hint
    if effective_work_layer not in {"protocol", "instance", "dual"}:
        effective_work_layer = DEFAULT_WORK_LAYER

    lane_applied_gate_set = _resolve_applied_gate_set(
        layer_intent_text=layer_intent_text,
        expected_work_layer=effective_work_layer,
        expected_source_layer=effective_source_layer,
    )
    # Always validate tuple and writeback linkage to keep evidence machine-checkable.
    rc_tuple, out_tuple, err_tuple = _run(
        ["python3", "scripts/validate_identity_binding_tuple.py", "--identity-id", args.identity_id, "--report", str(report_path)]
    )
    validators["binding_tuple"] = {"rc": rc_tuple, "ok": rc_tuple == 0, "out": out_tuple, "err": err_tuple}

    rc_wb, out_wb, err_wb = _run(
        [
            "python3",
            "scripts/validate_identity_experience_writeback.py",
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--local-catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--execution-report",
            str(report_path),
        ]
    )
    validators["experience_writeback"] = {"rc": rc_wb, "ok": rc_wb == 0, "out": out_wb, "err": err_wb}

    perm_cmd = ["python3", "scripts/validate_identity_permission_state.py", "--identity-id", args.identity_id, "--report", str(report_path), "--ci"]
    if all_ok and wb == "WRITTEN" and ps == "WRITEBACK_WRITTEN":
        perm_cmd.append("--require-written")
    rc_perm, out_perm, err_perm = _run(perm_cmd)
    validators["permission_state"] = {"rc": rc_perm, "ok": rc_perm == 0, "out": out_perm, "err": err_perm}

    rc_session, out_session, err_session = _run(
        [
            "python3",
            "scripts/validate_identity_session_pointer_consistency.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--actor-id",
            actor_id,
            "--session-id",
            str(getattr(args, "session_id", "") or "").strip(),
        ]
    )
    validators["session_pointer"] = {
        "rc": rc_session,
        "ok": rc_session == 0,
        "out": out_session,
        "err": err_session,
    }

    rc_home_align, out_home_align, err_home_align = _run(
        [
            "python3",
            "scripts/validate_identity_home_catalog_alignment.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-home",
            str(Path(args.catalog).expanduser().resolve().parent),
            "--json-only",
        ]
    )
    home_align_payload = _parse_json_payload(out_home_align) or {}
    validators["identity_home_catalog_alignment"] = {
        "rc": rc_home_align,
        "ok": rc_home_align == 0,
        "out": out_home_align,
        "err": err_home_align,
    }
    home_align_status = str(home_align_payload.get("path_governance_status", "")).strip().upper()
    if rc_home_align != 0 or home_align_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fixture_boundary, out_fixture_boundary, err_fixture_boundary = _run(
        [
            "python3",
            "scripts/validate_fixture_runtime_boundary.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fixture_boundary_payload = _parse_json_payload(out_fixture_boundary) or {}
    validators["fixture_runtime_boundary"] = {
        "rc": rc_fixture_boundary,
        "ok": rc_fixture_boundary == 0,
        "out": out_fixture_boundary,
        "err": err_fixture_boundary,
    }
    fixture_boundary_status = str(fixture_boundary_payload.get("path_governance_status", "")).strip().upper()
    if rc_fixture_boundary != 0 or fixture_boundary_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_actor_binding, out_actor_binding, err_actor_binding = _run(
        [
            "python3",
            "scripts/validate_actor_session_binding.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--actor-id",
            actor_id,
            "--session-id",
            str(getattr(args, "session_id", "") or "").strip(),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    actor_binding_payload = _parse_json_payload(out_actor_binding) or {}
    validators["actor_session_binding"] = {
        "rc": rc_actor_binding,
        "ok": rc_actor_binding == 0,
        "out": out_actor_binding,
        "err": err_actor_binding,
    }
    actor_binding_status = str(actor_binding_payload.get("actor_binding_status", "")).strip().upper()
    if rc_actor_binding != 0 or actor_binding_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_actor_mb, out_actor_mb, err_actor_mb = _run(
        [
            "python3",
            "scripts/validate_actor_session_multibinding_concurrency.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--actor-id",
            actor_id,
            "--session-id",
            str(getattr(args, "session_id", "") or "").strip(),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    actor_mb_payload = _parse_json_payload(out_actor_mb) or {}
    validators["actor_session_multibinding_concurrency"] = {
        "rc": rc_actor_mb,
        "ok": rc_actor_mb == 0,
        "out": out_actor_mb,
        "err": err_actor_mb,
    }
    actor_mb_status = str(actor_mb_payload.get("actor_session_multibinding_status", "")).strip().upper()
    if rc_actor_mb != 0 or actor_mb_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_no_implicit, out_no_implicit, err_no_implicit = _run(
        [
            "python3",
            "scripts/validate_no_implicit_switch.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    no_implicit_payload = _parse_json_payload(out_no_implicit) or {}
    validators["no_implicit_switch"] = {
        "rc": rc_no_implicit,
        "ok": rc_no_implicit == 0,
        "out": out_no_implicit,
        "err": err_no_implicit,
    }
    no_implicit_status = str(no_implicit_payload.get("implicit_switch_status", "")).strip().upper()
    if rc_no_implicit != 0 or no_implicit_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_cross_actor, out_cross_actor, err_cross_actor = _run(
        [
            "python3",
            "scripts/validate_cross_actor_isolation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    cross_actor_payload = _parse_json_payload(out_cross_actor) or {}
    validators["cross_actor_isolation"] = {
        "rc": rc_cross_actor,
        "ok": rc_cross_actor == 0,
        "out": out_cross_actor,
        "err": err_cross_actor,
    }
    cross_actor_status = str(cross_actor_payload.get("cross_actor_isolation_status", "")).strip().upper()
    if rc_cross_actor != 0 or cross_actor_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_refresh, out_refresh, err_refresh = _run(
        [
            "python3",
            "scripts/validate_identity_session_refresh_status.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--actor-id",
            actor_id,
            "--operation",
            "three-plane",
            "--baseline-policy",
            "warn",
            "--json-only",
        ]
    )
    refresh_payload = _parse_json_payload(out_refresh) or {}
    validators["session_refresh_status"] = {
        "rc": rc_refresh,
        "ok": rc_refresh == 0,
        "out": out_refresh,
        "err": err_refresh,
    }
    refresh_status = str(refresh_payload.get("session_refresh_status", "")).strip().upper()
    if rc_refresh != 0 or refresh_status == "FAIL_REQUIRED":
        hard_boundary = True

    stamp_artifact = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="three-plane",
            identity_id=args.identity_id,
            stem=f"identity-response-stamp-three-plane-{args.identity_id}",
            ext="json",
        )
    )
    stamp_blocker_receipt = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="three-plane",
            identity_id=args.identity_id,
            stem=f"identity-stamp-blocker-receipt-three-plane-{args.identity_id}",
            ext="json",
        )
    )
    reply_first_line_blocker_receipt = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="three-plane",
            identity_id=args.identity_id,
            stem=f"identity-reply-first-line-blocker-receipt-three-plane-{args.identity_id}",
            ext="json",
        )
    )
    send_time_reply_file = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="three-plane",
            identity_id=args.identity_id,
            stem=f"identity-send-time-reply-three-plane-{args.identity_id}",
            ext="txt",
        )
    )
    send_time_reply_gate_blocker_receipt = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="three-plane",
            identity_id=args.identity_id,
            stem=f"identity-send-time-reply-gate-blocker-receipt-three-plane-{args.identity_id}",
            ext="json",
        )
    )
    execution_reply_coherence_blocker_receipt = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="three-plane",
            identity_id=args.identity_id,
            stem=f"identity-execution-reply-coherence-blocker-receipt-three-plane-{args.identity_id}",
            ext="json",
        )
    )
    bundle_run_token = (
        str(args.required_gates_run_id or "").strip()
        or str(report_run_id or "").strip()
        or f"three-plane-{args.identity_id}"
    )
    required_gate_bundle_receipt = str(
        runtime_temp_file(
            channel="required-gate-bundle",
            operation="three-plane",
            identity_id=args.identity_id,
            run_token=bundle_run_token,
            stem=f"required-gate-bundle-three-plane-{args.identity_id}-{bundle_run_token}",
            ext="json",
        )
    )
    required_gate_bundle_receipt_shadow = str(
        runtime_temp_file(
            channel="required-gate-bundle",
            operation="scan",
            identity_id=args.identity_id,
            run_token=f"{bundle_run_token}-scan-probe",
            stem=f"required-gate-bundle-three-plane-scan-probe-{args.identity_id}-{bundle_run_token}",
            ext="json",
        )
    )
    vibe_pack_out_root = str(named_temp_root("vibe-coding-feeding-packs"))
    capability_fit_out_root = str(named_temp_root("capability-fit-matrices"))

    render_cmd = [
        "python3",
        "scripts/render_identity_response_stamp.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--actor-id",
        actor_id,
        "--session-id",
        str(getattr(args, "session_id", "") or "").strip(),
        "--view",
        "external",
        "--disclosure-level",
        "standard",
        "--out",
        stamp_artifact,
        "--json-only",
    ]
    if layer_intent_text:
        render_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        render_cmd.extend(["--work-layer", effective_work_layer])
    if effective_source_layer:
        render_cmd.extend(["--source-layer", effective_source_layer])
    rc_stamp_render, out_stamp_render, err_stamp_render = _run(render_cmd)
    stamp_render_payload = _parse_json_payload(out_stamp_render) or {}
    validators["response_stamp_render"] = {
        "rc": rc_stamp_render,
        "ok": rc_stamp_render == 0,
        "out": out_stamp_render,
        "err": err_stamp_render,
    }

    rc_stamp, out_stamp, err_stamp = _run(
        [
            "python3",
            "scripts/validate_identity_response_stamp.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--actor-id",
            actor_id,
            "--session-id",
            str(getattr(args, "session_id", "") or "").strip(),
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-user-visible-gate",
            "--operation",
            "three-plane",
            "--blocker-receipt-out",
            stamp_blocker_receipt,
            "--json-only",
        ]
    )
    stamp_payload = _parse_json_payload(out_stamp) or {}
    validators["response_stamp_validation"] = {
        "rc": rc_stamp,
        "ok": rc_stamp == 0,
        "out": out_stamp,
        "err": err_stamp,
    }

    rc_receipt, out_receipt, err_receipt = _run(
        [
            "python3",
            "scripts/validate_identity_response_stamp_blocker_receipt.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--force-check",
            "--receipt",
            stamp_blocker_receipt,
            "--json-only",
        ]
    )
    receipt_payload = _parse_json_payload(out_receipt) or {}
    validators["response_stamp_blocker_receipt"] = {
        "rc": rc_receipt,
        "ok": rc_receipt == 0,
        "out": out_receipt,
        "err": err_receipt,
    }
    if rc_stamp != 0 or rc_receipt != 0:
        hard_boundary = True

    reply_first_line_cmd = [
        "python3",
        "scripts/validate_reply_identity_context_first_line.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--stamp-json",
        stamp_artifact,
        "--force-check",
        "--enforce-first-line-gate",
        "--operation",
        "three-plane",
        "--actor-id",
        actor_id,
        "--session-id",
        str(getattr(args, "session_id", "") or "").strip(),
        "--blocker-receipt-out",
        reply_first_line_blocker_receipt,
        "--json-only",
    ]
    if layer_intent_text:
        reply_first_line_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        reply_first_line_cmd.extend(["--expected-work-layer", effective_work_layer])
    if effective_source_layer:
        reply_first_line_cmd.extend(["--expected-source-layer", effective_source_layer])
    rc_reply_first_line, out_reply_first_line, err_reply_first_line = _run(reply_first_line_cmd)
    reply_first_line_payload = _parse_json_payload(out_reply_first_line) or {}
    validators["reply_identity_context_first_line"] = {
        "rc": rc_reply_first_line,
        "ok": rc_reply_first_line == 0,
        "out": out_reply_first_line,
        "err": err_reply_first_line,
    }
    reply_first_line_status = str(reply_first_line_payload.get("reply_first_line_status", "")).strip().upper()
    if rc_reply_first_line != 0 or reply_first_line_status == "FAIL_REQUIRED":
        hard_boundary = True

    layer_intent_cmd = [
        "python3",
        "scripts/validate_layer_intent_resolution.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--stamp-json",
        stamp_artifact,
        "--force-check",
        "--enforce-layer-intent-gate",
        "--operation",
        "three-plane",
        "--json-only",
    ]
    if layer_intent_text:
        layer_intent_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        layer_intent_cmd.extend(["--expected-work-layer", effective_work_layer])
    if effective_source_layer:
        layer_intent_cmd.extend(["--expected-source-layer", effective_source_layer])
    rc_layer_intent, out_layer_intent, err_layer_intent = _run(layer_intent_cmd)
    layer_intent_payload = _parse_json_payload(out_layer_intent) or {}
    validators["layer_intent_resolution"] = {
        "rc": rc_layer_intent,
        "ok": rc_layer_intent == 0,
        "out": out_layer_intent,
        "err": err_layer_intent,
    }
    layer_intent_status = str(layer_intent_payload.get("layer_intent_resolution_status", "")).strip().upper()
    if rc_layer_intent != 0 or layer_intent_status == "FAIL_REQUIRED":
        hard_boundary = True

    compose_send_time_cmd = [
        "python3",
        "scripts/final_emit_governed.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--body-text",
        "THREE_PLANE_SEND_TIME_REPLY_BODY",
        "--out-reply-file",
        send_time_reply_file,
        "--blocker-receipt-out",
        send_time_reply_gate_blocker_receipt,
        "--outlet-channel-id",
        "final_emit_governed",
        "--actor-id",
        actor_id,
        "--session-id",
        str(getattr(args, "session_id", "") or "").strip(),
        "--json-only",
    ]
    if layer_intent_text:
        compose_send_time_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        compose_send_time_cmd.extend(["--work-layer", effective_work_layer])
    if effective_source_layer:
        compose_send_time_cmd.extend(["--source-layer", effective_source_layer])
    rc_compose_send_time, out_compose_send_time, err_compose_send_time = _run(compose_send_time_cmd)
    compose_send_time_payload = _parse_json_payload(out_compose_send_time) or {}
    validators["compose_governed_reply_preflight"] = {
        "rc": rc_compose_send_time,
        "ok": rc_compose_send_time == 0,
        "out": out_compose_send_time,
        "err": err_compose_send_time,
    }
    compose_send_time_status = str(compose_send_time_payload.get("send_time_gate_status", "")).strip().upper()
    if rc_compose_send_time != 0 or compose_send_time_status == "FAIL_REQUIRED":
        hard_boundary = True

    send_time_cmd = [
        "python3",
        "scripts/validate_send_time_reply_gate.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--reply-file",
        send_time_reply_file,
        "--force-check",
        "--enforce-send-time-gate",
        "--reply-outlet-guard-applied",
        "--outlet-channel-id",
        "final_emit_governed",
        "--reply-transport-ref",
        send_time_reply_file,
        "--operation",
        "three-plane",
        "--blocker-receipt-out",
        send_time_reply_gate_blocker_receipt,
        "--actor-id",
        actor_id,
        "--session-id",
        str(getattr(args, "session_id", "") or "").strip(),
        "--json-only",
    ]
    if layer_intent_text:
        send_time_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        send_time_cmd.extend(["--expected-work-layer", effective_work_layer])
    if effective_source_layer:
        send_time_cmd.extend(["--expected-source-layer", effective_source_layer])
    rc_send_time_gate, out_send_time_gate, err_send_time_gate = _run(send_time_cmd)
    send_time_gate_payload = _parse_json_payload(out_send_time_gate) or {}
    validators["send_time_reply_gate"] = {
        "rc": rc_send_time_gate,
        "ok": rc_send_time_gate == 0,
        "out": out_send_time_gate,
        "err": err_send_time_gate,
    }
    send_time_gate_status = str(send_time_gate_payload.get("send_time_gate_status", "")).strip().upper()
    if rc_send_time_gate != 0 or send_time_gate_status == "FAIL_REQUIRED":
        hard_boundary = True

    headstamp_recurrence_cmd = [
        "python3",
        "scripts/validate_headstamp_recurrence_closure.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--operation",
        "three-plane",
        "--actor-id",
        actor_id,
        "--session-id",
        str(getattr(args, "session_id", "") or "").strip(),
        "--json-only",
    ]
    rc_headstamp, out_headstamp, err_headstamp = _run(headstamp_recurrence_cmd)
    headstamp_payload = _parse_json_payload(out_headstamp) or {}
    validators["headstamp_recurrence_closure"] = {
        "rc": rc_headstamp,
        "ok": rc_headstamp == 0,
        "out": out_headstamp,
        "err": err_headstamp,
    }
    headstamp_status = str(headstamp_payload.get("headstamp_recurrence_closure_status", "")).strip().upper()
    if rc_headstamp != 0 or headstamp_status == "FAIL_REQUIRED":
        hard_boundary = True

    reply_coherence_cmd = [
        "python3",
        "scripts/validate_execution_reply_identity_coherence.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--stamp-json",
        stamp_artifact,
        "--force-check",
        "--enforce-coherence-gate",
        "--operation",
        "three-plane",
        "--actor-id",
        actor_id,
        "--session-id",
        str(getattr(args, "session_id", "") or "").strip(),
        "--blocker-receipt-out",
        execution_reply_coherence_blocker_receipt,
        "--json-only",
    ]
    if layer_intent_text:
        reply_coherence_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        reply_coherence_cmd.extend(["--expected-work-layer", effective_work_layer])
    if effective_source_layer:
        reply_coherence_cmd.extend(["--expected-source-layer", effective_source_layer])
    rc_reply_coherence, out_reply_coherence, err_reply_coherence = _run(reply_coherence_cmd)
    reply_coherence_payload = _parse_json_payload(out_reply_coherence) or {}
    validators["execution_reply_identity_coherence"] = {
        "rc": rc_reply_coherence,
        "ok": rc_reply_coherence == 0,
        "out": out_reply_coherence,
        "err": err_reply_coherence,
    }
    reply_coherence_status = str(reply_coherence_payload.get("coherence_status", "")).strip().upper()
    if rc_reply_coherence != 0 or reply_coherence_status in {"FAIL_REQUIRED", "WARN_NON_BLOCKING"}:
        hard_boundary = True

    rc_prompt, out_prompt, err_prompt = _run(
        [
            "python3",
            "scripts/validate_identity_prompt_activation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--report",
            str(report_path),
        ]
    )
    validators["prompt_activation"] = {"rc": rc_prompt, "ok": rc_prompt == 0, "out": out_prompt, "err": err_prompt}

    rc_prompt_lc, out_prompt_lc, err_prompt_lc = _run(
        [
            "python3",
            "scripts/validate_identity_prompt_lifecycle.py",
            "--identity-id",
            args.identity_id,
            "--report",
            str(report_path),
        ]
    )
    validators["prompt_lifecycle"] = {
        "rc": rc_prompt_lc,
        "ok": rc_prompt_lc == 0,
        "out": out_prompt_lc,
        "err": err_prompt_lc,
    }

    cap_cmd = [
        "python3",
        "scripts/validate_identity_capability_activation.py",
        "--identity-id",
        args.identity_id,
        "--report",
        str(report_path),
    ]
    if all_ok and wb == "WRITTEN" and ps == "WRITEBACK_WRITTEN":
        cap_cmd.append("--require-activated")
    rc_cap, out_cap, err_cap = _run(cap_cmd)
    validators["capability_activation"] = {
        "rc": rc_cap,
        "ok": rc_cap == 0,
        "out": out_cap,
        "err": err_cap,
    }

    rc_dc, out_dc, err_dc = _run(
        [
            "python3",
            "scripts/validate_identity_dialogue_content.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
        ]
    )
    validators["dialogue_content"] = {"rc": rc_dc, "ok": rc_dc == 0, "out": out_dc, "err": err_dc}

    rc_dcv, out_dcv, err_dcv = _run(
        [
            "python3",
            "scripts/validate_identity_dialogue_cross_validation.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
        ]
    )
    validators["dialogue_cross_validation"] = {
        "rc": rc_dcv,
        "ok": rc_dcv == 0,
        "out": out_dcv,
        "err": err_dcv,
    }

    rc_drs, out_drs, err_drs = _run(
        [
            "python3",
            "scripts/validate_identity_dialogue_result_support.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
        ]
    )
    validators["dialogue_result_support"] = {"rc": rc_drs, "ok": rc_drs == 0, "out": out_drs, "err": err_drs}

    rc_cov, out_cov, err_cov = _run(
        [
            "python3",
            "scripts/validate_required_contract_coverage.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--actor-id",
            args.actor_id,
            "--session-id",
            str(getattr(args, "session_id", "") or "").strip(),
            "--json-only",
        ]
    )
    coverage_payload = _parse_json_payload(out_cov) or {}
    validators["required_contract_coverage"] = {
        "rc": rc_cov,
        "ok": rc_cov == 0,
        "out": out_cov,
        "err": err_cov,
    }

    rc_unlock_formula, out_unlock_formula, err_unlock_formula = _run(
        [
            "python3",
            "scripts/validate_unlock_formula.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    unlock_formula_payload = _parse_json_payload(out_unlock_formula) or {}
    validators["unlock_formula_automation"] = {
        "rc": rc_unlock_formula,
        "ok": rc_unlock_formula == 0,
        "out": out_unlock_formula,
        "err": err_unlock_formula,
    }
    unlock_formula_status = str(unlock_formula_payload.get("unlock_formula_status", "")).strip().upper()
    if rc_unlock_formula != 0 or unlock_formula_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_release_cloud, out_release_cloud, err_release_cloud = _run(
        [
            "python3",
            "scripts/validate_release_plane_cloud_evidence.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--target-branch",
            str(args.target_branch or ""),
            "--release-head-sha",
            str(args.release_head_sha or ""),
            "--required-gates-run-id",
            str(args.required_gates_run_id or ""),
            "--run-url",
            str(args.run_url or ""),
            "--workflow-file-sha",
            str(args.workflow_file_sha or ""),
            "--run-head-sha",
            str(args.run_head_sha or ""),
            "--run-workflow-file-sha",
            str(args.run_workflow_file_sha or ""),
            "--checks-json",
            str(args.checks_json or ""),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    release_cloud_payload = _parse_json_payload(out_release_cloud) or {}
    validators["release_plane_cloud_evidence"] = {
        "rc": rc_release_cloud,
        "ok": rc_release_cloud == 0,
        "out": out_release_cloud,
        "err": err_release_cloud,
    }
    release_cloud_status = str(release_cloud_payload.get("release_plane_cloud_evidence_status", "")).strip().upper()
    if rc_release_cloud != 0 or release_cloud_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_cross_cwd, out_cross_cwd, err_cross_cwd = _run(
        [
            "python3",
            "scripts/validate_cross_cwd_absolute_input.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            str(Path(args.repo_catalog).resolve()),
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    cross_cwd_payload = _parse_json_payload(out_cross_cwd) or {}
    validators["cross_cwd_absolute_input"] = {
        "rc": rc_cross_cwd,
        "ok": rc_cross_cwd == 0,
        "out": out_cross_cwd,
        "err": err_cross_cwd,
    }
    cross_cwd_status = str(cross_cwd_payload.get("cross_cwd_absolute_input_status", "")).strip().upper()
    if rc_cross_cwd != 0 or cross_cwd_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_run_selector, out_run_selector, err_run_selector = _run(
        [
            "python3",
            "scripts/validate_run_id_report_selection.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            str(args.required_gates_run_id or ""),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    run_selector_payload = _parse_json_payload(out_run_selector) or {}
    validators["run_id_report_selection"] = {
        "rc": rc_run_selector,
        "ok": rc_run_selector == 0,
        "out": out_run_selector,
        "err": err_run_selector,
    }
    run_selector_status = str(run_selector_payload.get("run_id_report_selection_status", "")).strip().upper()
    if rc_run_selector != 0 or run_selector_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_phase_bootstrap, out_phase_bootstrap, err_phase_bootstrap = _run(
        [
            "python3",
            "scripts/validate_phase_bootstrap_before_strict.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    phase_bootstrap_payload = _parse_json_payload(out_phase_bootstrap) or {}
    validators["phase_bootstrap_before_strict"] = {
        "rc": rc_phase_bootstrap,
        "ok": rc_phase_bootstrap == 0,
        "out": out_phase_bootstrap,
        "err": err_phase_bootstrap,
    }
    phase_bootstrap_status = str(phase_bootstrap_payload.get("phase_bootstrap_before_strict_status", "")).strip().upper()
    if rc_phase_bootstrap != 0 or phase_bootstrap_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_tmp_collision, out_tmp_collision, err_tmp_collision = _run(
        [
            "python3",
            "scripts/validate_tmp_collision_safety.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            str(args.required_gates_run_id or ""),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    tmp_collision_payload = _parse_json_payload(out_tmp_collision) or {}
    validators["tmp_collision_safety"] = {
        "rc": rc_tmp_collision,
        "ok": rc_tmp_collision == 0,
        "out": out_tmp_collision,
        "err": err_tmp_collision,
    }
    tmp_collision_status = str(tmp_collision_payload.get("tmp_collision_safety_status", "")).strip().upper()
    if rc_tmp_collision != 0 or tmp_collision_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fresh_rotation, out_fresh_rotation, err_fresh_rotation = _run(
        [
            "python3",
            "scripts/validate_handoff_collab_freshness_rotation.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fresh_rotation_payload = _parse_json_payload(out_fresh_rotation) or {}
    validators["handoff_collab_freshness_rotation"] = {
        "rc": rc_fresh_rotation,
        "ok": rc_fresh_rotation == 0,
        "out": out_fresh_rotation,
        "err": err_fresh_rotation,
    }
    fresh_rotation_status = str(fresh_rotation_payload.get("handoff_collab_freshness_rotation_status", "")).strip().upper()
    if rc_fresh_rotation != 0 or fresh_rotation_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_atomic_emit, out_atomic_emit, err_atomic_emit = _run(
        [
            "python3",
            "scripts/validate_protocol_feedback_atomic_emit.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    atomic_emit_payload = _parse_json_payload(out_atomic_emit) or {}
    validators["protocol_feedback_atomic_emit"] = {
        "rc": rc_atomic_emit,
        "ok": rc_atomic_emit == 0,
        "out": out_atomic_emit,
        "err": err_atomic_emit,
    }
    atomic_emit_status = str(atomic_emit_payload.get("protocol_feedback_atomic_emit_status", "")).strip().upper()
    if rc_atomic_emit != 0 or atomic_emit_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_cap_boundary, out_cap_boundary, err_cap_boundary = _run(
        [
            "python3",
            "scripts/validate_capability_boundary_classification.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    cap_boundary_payload = _parse_json_payload(out_cap_boundary) or {}
    validators["capability_boundary_classification"] = {
        "rc": rc_cap_boundary,
        "ok": rc_cap_boundary == 0,
        "out": out_cap_boundary,
        "err": err_cap_boundary,
    }
    cap_boundary_status = str(cap_boundary_payload.get("capability_boundary_status", "")).strip().upper()
    if rc_cap_boundary != 0 or cap_boundary_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_promotion_pipeline, out_promotion_pipeline, err_promotion_pipeline = _run(
        [
            "python3",
            "scripts/validate_promotion_pipeline.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    promotion_pipeline_payload = _parse_json_payload(out_promotion_pipeline) or {}
    validators["promotion_evidence_pipeline"] = {
        "rc": rc_promotion_pipeline,
        "ok": rc_promotion_pipeline == 0,
        "out": out_promotion_pipeline,
        "err": err_promotion_pipeline,
    }
    promotion_pipeline_status = str(promotion_pipeline_payload.get("promotion_pipeline_status", "")).strip().upper()
    if rc_promotion_pipeline != 0 or promotion_pipeline_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_outlet_matrix, out_outlet_matrix, err_outlet_matrix = _run(
        [
            "python3",
            "scripts/validate_outlet_matrix.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    outlet_matrix_payload = _parse_json_payload(out_outlet_matrix) or {}
    validators["outlet_regression_matrix"] = {
        "rc": rc_outlet_matrix,
        "ok": rc_outlet_matrix == 0,
        "out": out_outlet_matrix,
        "err": err_outlet_matrix,
    }
    outlet_matrix_status = str(outlet_matrix_payload.get("outlet_matrix_status", "")).strip().upper()
    if rc_outlet_matrix != 0 or outlet_matrix_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_sidecar_cwd, out_sidecar_cwd, err_sidecar_cwd = _run(
        [
            "python3",
            "scripts/validate_sidecar_cwd_parity.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    sidecar_cwd_payload = _parse_json_payload(out_sidecar_cwd) or {}
    validators["sidecar_cwd_parity"] = {
        "rc": rc_sidecar_cwd,
        "ok": rc_sidecar_cwd == 0,
        "out": out_sidecar_cwd,
        "err": err_sidecar_cwd,
    }
    sidecar_cwd_status = str(sidecar_cwd_payload.get("sidecar_cwd_parity_status", "")).strip().upper()
    if rc_sidecar_cwd != 0 or sidecar_cwd_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_docs_bridge, out_docs_bridge, err_docs_bridge = _run(
        [
            "python3",
            "scripts/validate_docs_bridge_consistency.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    docs_bridge_payload = _parse_json_payload(out_docs_bridge) or {}
    validators["docs_bridge_consistency"] = {
        "rc": rc_docs_bridge,
        "ok": rc_docs_bridge == 0,
        "out": out_docs_bridge,
        "err": err_docs_bridge,
    }
    docs_bridge_status = str(docs_bridge_payload.get("bridge_consistency_status", "")).strip().upper()
    if rc_docs_bridge != 0 or docs_bridge_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_mapping_coverage, out_mapping_coverage, err_mapping_coverage = _run(
        [
            "python3",
            "scripts/validate_contract_mapping_coverage.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    mapping_coverage_payload = _parse_json_payload(out_mapping_coverage) or {}
    validators["contract_mapping_coverage"] = {
        "rc": rc_mapping_coverage,
        "ok": rc_mapping_coverage == 0,
        "out": out_mapping_coverage,
        "err": err_mapping_coverage,
    }
    mapping_coverage_status = str(mapping_coverage_payload.get("contract_mapping_coverage_status", "")).strip().upper()
    if rc_mapping_coverage != 0 or mapping_coverage_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_prompt_bootstrap, out_prompt_bootstrap, err_prompt_bootstrap = _run(
        [
            "python3",
            "scripts/validate_prompt_bootstrap_capability.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    prompt_bootstrap_payload = _parse_json_payload(out_prompt_bootstrap) or {}
    validators["prompt_bootstrap_capability"] = {
        "rc": rc_prompt_bootstrap,
        "ok": rc_prompt_bootstrap == 0,
        "out": out_prompt_bootstrap,
        "err": err_prompt_bootstrap,
    }
    prompt_bootstrap_status = str(prompt_bootstrap_payload.get("prompt_bootstrap_contract_status", "")).strip().upper()
    if rc_prompt_bootstrap != 0 or prompt_bootstrap_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_prompt_matrix, out_prompt_matrix, err_prompt_matrix = _run(
        [
            "python3",
            "scripts/validate_prompt_capability_matrix.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    prompt_matrix_payload = _parse_json_payload(out_prompt_matrix) or {}
    validators["prompt_capability_matrix"] = {
        "rc": rc_prompt_matrix,
        "ok": rc_prompt_matrix == 0,
        "out": out_prompt_matrix,
        "err": err_prompt_matrix,
    }
    prompt_matrix_status = str(prompt_matrix_payload.get("prompt_capability_matrix_status", "")).strip().upper()
    if rc_prompt_matrix != 0 or prompt_matrix_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_interference, out_interference, err_interference = _run(
        [
            "python3",
            "scripts/validate_refresh_strict_business_interference.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    interference_payload = _parse_json_payload(out_interference) or {}
    validators["refresh_strict_business_interference"] = {
        "rc": rc_interference,
        "ok": rc_interference == 0,
        "out": out_interference,
        "err": err_interference,
    }
    interference_status = str(interference_payload.get("refresh_strict_business_interference_status", "")).strip().upper()
    if rc_interference != 0 or interference_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_kernel_ssot, out_kernel_ssot, err_kernel_ssot = _run(
        [
            "python3",
            "scripts/validate_kernel_ssot_source.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    kernel_ssot_payload = _parse_json_payload(out_kernel_ssot) or {}
    validators["kernel_ssot_source"] = {
        "rc": rc_kernel_ssot,
        "ok": rc_kernel_ssot == 0,
        "out": out_kernel_ssot,
        "err": err_kernel_ssot,
    }
    kernel_ssot_status = str(kernel_ssot_payload.get("kernel_ssot_source_status", "")).strip().upper()
    if rc_kernel_ssot != 0 or kernel_ssot_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_prompt_derivation, out_prompt_derivation, err_prompt_derivation = _run(
        [
            "python3",
            "scripts/validate_prompt_derivation_conformance.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    prompt_derivation_payload = _parse_json_payload(out_prompt_derivation) or {}
    validators["prompt_derivation_conformance"] = {
        "rc": rc_prompt_derivation,
        "ok": rc_prompt_derivation == 0,
        "out": out_prompt_derivation,
        "err": err_prompt_derivation,
    }
    prompt_derivation_status = str(prompt_derivation_payload.get("prompt_derivation_conformance_status", "")).strip().upper()
    if rc_prompt_derivation != 0 or prompt_derivation_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_semantic_convergence, out_semantic_convergence, err_semantic_convergence = _run(
        [
            "python3",
            "scripts/validate_semantic_convergence.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    semantic_convergence_payload = _parse_json_payload(out_semantic_convergence) or {}
    validators["semantic_convergence"] = {
        "rc": rc_semantic_convergence,
        "ok": rc_semantic_convergence == 0,
        "out": out_semantic_convergence,
        "err": err_semantic_convergence,
    }
    semantic_convergence_status = str(semantic_convergence_payload.get("semantic_convergence_status", "")).strip().upper()
    if rc_semantic_convergence != 0 or semantic_convergence_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_prompt_coupling, out_prompt_coupling, err_prompt_coupling = _run(
        [
            "python3",
            "scripts/validate_prompt_kernel_executable_coupling.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--actor-id",
            args.actor_id,
            "--session-id",
            args.session_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    prompt_coupling_payload = _parse_json_payload(out_prompt_coupling) or {}
    validators["prompt_kernel_executable_coupling"] = {
        "rc": rc_prompt_coupling,
        "ok": rc_prompt_coupling == 0,
        "out": out_prompt_coupling,
        "err": err_prompt_coupling,
    }
    prompt_coupling_status = str(prompt_coupling_payload.get("prompt_kernel_executable_coupling_status", "")).strip().upper()
    if rc_prompt_coupling != 0 or prompt_coupling_status == "FAIL_REQUIRED":
        hard_boundary = True

    bundle_send_time_gate_status = compose_send_time_status or "UNKNOWN"
    bundle_outlet_bypass_detected = "true" if bool(compose_send_time_payload.get("outlet_bypass_detected", False)) else "false"
    bundle_final_emit_contract_status = str(compose_send_time_payload.get("final_emit_contract_status", "")).strip().upper()
    bundle_final_emit_policy_mode = str(compose_send_time_payload.get("final_emit_policy_mode", "")).strip()
    bundle_final_emit_schema_status = str(compose_send_time_payload.get("final_emit_schema_status", "")).strip().upper()
    bundle_resolved_work_layer = str(
        effective_work_layer
        or layer_intent_payload.get("resolved_work_layer")
        or compose_send_time_payload.get("work_layer")
        or stamp_payload.get("work_layer")
        or ""
    ).strip().lower()
    bundle_resolved_source_layer = str(
        effective_source_layer
        or layer_intent_payload.get("resolved_source_layer")
        or compose_send_time_payload.get("source_layer")
        or stamp_payload.get("source_layer")
        or ""
    ).strip().lower()
    bundle_lock_state = str(
        reply_first_line_payload.get("context_lock_state")
        or compose_send_time_payload.get("context_lock_state")
        or stamp_payload.get("lock_state")
        or "LOCK_MATCH"
    ).strip()
    rc_required_bundle, out_required_bundle, err_required_bundle = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--surface-label",
            "three_plane",
            "--operation",
            "three-plane",
            "--out",
            required_gate_bundle_receipt,
            "--json-only",
        ]
    )
    required_bundle_payload = _parse_json_payload(out_required_bundle) or {}
    validators["required_gate_bundle_runner"] = {
        "rc": rc_required_bundle,
        "ok": rc_required_bundle == 0,
        "out": out_required_bundle,
        "err": err_required_bundle,
    }
    required_bundle_status = str(required_bundle_payload.get("bundle_status", "")).strip().upper()
    if rc_required_bundle != 0 or required_bundle_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_required_bundle_shadow, out_required_bundle_shadow, err_required_bundle_shadow = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--surface-label",
            "three_plane_scan_probe",
            "--operation",
            "scan",
            "--out",
            required_gate_bundle_receipt_shadow,
            "--json-only",
        ]
    )
    required_bundle_shadow_payload = _parse_json_payload(out_required_bundle_shadow) or {}
    validators["required_gate_bundle_runner_shadow"] = {
        "rc": rc_required_bundle_shadow,
        "ok": rc_required_bundle_shadow == 0,
        "out": out_required_bundle_shadow,
        "err": err_required_bundle_shadow,
    }
    required_bundle_shadow_status = str(required_bundle_shadow_payload.get("bundle_status", "")).strip().upper()
    if rc_required_bundle_shadow != 0 or required_bundle_shadow_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_recurrence, out_recurrence, err_recurrence = _run(
        [
            "python3",
            "scripts/validate_required_gate_recurrence_escalator.py",
            "--identity-id",
            args.identity_id,
            "--surface",
            "three_plane",
            "--operation",
            "three-plane",
            "--receipt",
            required_gate_bundle_receipt,
            "--enforce-blocking",
            "--json-only",
        ]
    )
    recurrence_payload = _parse_json_payload(out_recurrence) or {}
    validators["required_gate_recurrence_escalator"] = {
        "rc": rc_recurrence,
        "ok": rc_recurrence == 0,
        "out": out_recurrence,
        "err": err_recurrence,
    }
    recurrence_status = str(recurrence_payload.get("required_gate_recurrence_status", "")).strip().upper()
    if rc_recurrence != 0 or recurrence_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_tuple_parity, out_tuple_parity, err_tuple_parity = _run(
        [
            "python3",
            "scripts/validate_required_gate_tuple_parity.py",
            "--receipt",
            required_gate_bundle_receipt,
            "--receipt",
            required_gate_bundle_receipt_shadow,
            "--require-distinct-operations",
            "--json-only",
        ]
    )
    tuple_parity_payload = _parse_json_payload(out_tuple_parity) or {}
    validators["required_gate_tuple_parity"] = {
        "rc": rc_tuple_parity,
        "ok": rc_tuple_parity == 0,
        "out": out_tuple_parity,
        "err": err_tuple_parity,
    }
    tuple_parity_status = str(tuple_parity_payload.get("required_gate_tuple_parity_status", "")).strip().upper()
    if rc_tuple_parity != 0 or tuple_parity_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_cross_verify, out_cross_verify, err_cross_verify = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "cross_verification_tracks",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--report-selected-path",
            str(report_path),
            "--json-only",
        ]
    )
    cross_verify_payload = _parse_json_payload(out_cross_verify) or {}
    validators["cross_verification_tracks"] = {
        "rc": rc_cross_verify,
        "ok": rc_cross_verify == 0,
        "out": out_cross_verify,
        "err": err_cross_verify,
    }
    cross_verify_status = str(cross_verify_payload.get("cross_verification_tracks_status", "")).strip().upper()
    if rc_cross_verify != 0 or cross_verify_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_intake_quorum, out_intake_quorum, err_intake_quorum = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "intake_evidence_quorum",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--report-selected-path",
            str(report_path),
            "--json-only",
        ]
    )
    intake_quorum_payload = _parse_json_payload(out_intake_quorum) or {}
    validators["intake_evidence_quorum"] = {
        "rc": rc_intake_quorum,
        "ok": rc_intake_quorum == 0,
        "out": out_intake_quorum,
        "err": err_intake_quorum,
    }
    intake_quorum_status = str(intake_quorum_payload.get("intake_evidence_quorum_status", "")).strip().upper()
    if rc_intake_quorum != 0 or intake_quorum_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_route_pin, out_route_pin, err_route_pin = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "route_version_pinning",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    route_pin_payload = _parse_json_payload(out_route_pin) or {}
    validators["route_version_pinning"] = {
        "rc": rc_route_pin,
        "ok": rc_route_pin == 0,
        "out": out_route_pin,
        "err": err_route_pin,
    }
    route_pin_status = str(route_pin_payload.get("pin_status", "")).strip().upper()
    if rc_route_pin != 0 or route_pin_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fallback_norm, out_fallback_norm, err_fallback_norm = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "fallback_taxonomy_normalization",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fallback_norm_payload = _parse_json_payload(out_fallback_norm) or {}
    validators["fallback_taxonomy_normalization"] = {
        "rc": rc_fallback_norm,
        "ok": rc_fallback_norm == 0,
        "out": out_fallback_norm,
        "err": err_fallback_norm,
    }
    fallback_norm_status = str(fallback_norm_payload.get("fallback_taxonomy_normalization_status", "")).strip().upper()
    if rc_fallback_norm != 0 or fallback_norm_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_dedup_mono, out_dedup_mono, err_dedup_mono = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "dedup_monotonicity",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    dedup_mono_payload = _parse_json_payload(out_dedup_mono) or {}
    validators["dedup_monotonicity"] = {
        "rc": rc_dedup_mono,
        "ok": rc_dedup_mono == 0,
        "out": out_dedup_mono,
        "err": err_dedup_mono,
    }
    dedup_mono_status = str(dedup_mono_payload.get("monotonicity_status", "")).strip().upper()
    if rc_dedup_mono != 0 or dedup_mono_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_xwf_schema, out_xwf_schema, err_xwf_schema = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "cross_workflow_schema",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    xwf_schema_payload = _parse_json_payload(out_xwf_schema) or {}
    validators["cross_workflow_schema"] = {
        "rc": rc_xwf_schema,
        "ok": rc_xwf_schema == 0,
        "out": out_xwf_schema,
        "err": err_xwf_schema,
    }
    xwf_schema_status = str(xwf_schema_payload.get("cross_workflow_schema_status", "")).strip().upper()
    if rc_xwf_schema != 0 or xwf_schema_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_skill_path, out_skill_path, err_skill_path = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "skill_path_integrity",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    skill_path_payload = _parse_json_payload(out_skill_path) or {}
    validators["skill_path_integrity"] = {
        "rc": rc_skill_path,
        "ok": rc_skill_path == 0,
        "out": out_skill_path,
        "err": err_skill_path,
    }
    skill_path_status = str(skill_path_payload.get("path_integrity_status", "")).strip().upper()
    if rc_skill_path != 0 or skill_path_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_exec_target_tuple, out_exec_target_tuple, err_exec_target_tuple = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "execution_target_tuple_isolation",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    exec_target_tuple_payload = _parse_json_payload(out_exec_target_tuple) or {}
    validators["execution_target_tuple_isolation"] = {
        "rc": rc_exec_target_tuple,
        "ok": rc_exec_target_tuple == 0,
        "out": out_exec_target_tuple,
        "err": err_exec_target_tuple,
    }
    exec_target_tuple_status = str(
        exec_target_tuple_payload.get("execution_target_tuple_isolation_status", "")
    ).strip().upper()
    if rc_exec_target_tuple != 0 or exec_target_tuple_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_multimodal_plugin, out_multimodal_plugin, err_multimodal_plugin = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "multimodal_plugin_enforcement",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--report-selected-path",
            str(report_path),
            "--json-only",
        ]
    )
    multimodal_plugin_payload = _parse_json_payload(out_multimodal_plugin) or {}
    validators["multimodal_plugin_enforcement"] = {
        "rc": rc_multimodal_plugin,
        "ok": rc_multimodal_plugin == 0,
        "out": out_multimodal_plugin,
        "err": err_multimodal_plugin,
    }
    multimodal_plugin_status = str(
        multimodal_plugin_payload.get("multimodal_plugin_enforcement_status", "")
    ).strip().upper()
    if rc_multimodal_plugin != 0 or multimodal_plugin_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_reasoning_plugin, out_reasoning_plugin, err_reasoning_plugin = _run(
        [
            "python3",
            "scripts/required_gate_bundle_runner.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--run-id",
            bundle_run_token,
            "--send-time-gate-status",
            bundle_send_time_gate_status,
            "--outlet-bypass-detected",
            bundle_outlet_bypass_detected,
            "--final-emit-contract-status",
            bundle_final_emit_contract_status,
            "--final-emit-policy-mode",
            bundle_final_emit_policy_mode,
            "--final-emit-schema-status",
            bundle_final_emit_schema_status,
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            bundle_resolved_work_layer,
            "--resolved-source-layer",
            bundle_resolved_source_layer,
            "--lock-state",
            bundle_lock_state,
            "--target-name",
            "reasoning_loop_failclose_enforcement",
            "--surface-label",
            "three_plane_target_probe",
            "--operation",
            "three-plane",
            "--report-selected-path",
            str(report_path),
            "--json-only",
        ]
    )
    reasoning_plugin_payload = _parse_json_payload(out_reasoning_plugin) or {}
    validators["reasoning_loop_failclose_enforcement"] = {
        "rc": rc_reasoning_plugin,
        "ok": rc_reasoning_plugin == 0,
        "out": out_reasoning_plugin,
        "err": err_reasoning_plugin,
    }
    reasoning_plugin_status = str(
        reasoning_plugin_payload.get("reasoning_loop_failclose_status", "")
    ).strip().upper()
    if rc_reasoning_plugin != 0 or reasoning_plugin_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_replay_archive, out_replay_archive, err_replay_archive = _run(
        [
            "python3",
            "scripts/validate_replay_archive_contract.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    replay_archive_payload = _parse_json_payload(out_replay_archive) or {}
    validators["replay_archive_contract"] = {
        "rc": rc_replay_archive,
        "ok": rc_replay_archive == 0,
        "out": out_replay_archive,
        "err": err_replay_archive,
    }
    replay_archive_status = str(replay_archive_payload.get("replay_archive_contract_status", "")).strip().upper()
    if rc_replay_archive != 0 or replay_archive_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_herm, out_herm, err_herm = _run(
        [
            "python3",
            "scripts/validate_e2e_hermetic_runtime_import.py",
            "--operation",
            "three-plane",
            "--pythonpath-bootstrap-mode",
            "internal_bootstrap",
            "--json-only",
        ]
    )
    herm_payload = _parse_json_payload(out_herm) or {}
    validators["e2e_hermetic_runtime_import"] = {
        "rc": rc_herm,
        "ok": rc_herm == 0,
        "out": out_herm,
        "err": err_herm,
    }
    herm_status = str(herm_payload.get("e2e_hermetic_runtime_status", "")).strip().upper()
    if rc_herm != 0 or herm_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_semantic, out_semantic, err_semantic = _run(
        [
            "python3",
            "scripts/validate_semantic_routing_guard.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    semantic_payload = _parse_json_payload(out_semantic) or {}
    validators["semantic_routing_guard"] = {
        "rc": rc_semantic,
        "ok": rc_semantic == 0,
        "out": out_semantic,
        "err": err_semantic,
    }
    semantic_status = str(semantic_payload.get("semantic_routing_status", "")).strip().upper()
    if rc_semantic != 0 or semantic_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_split, out_split, err_split = _run(
        [
            "python3",
            "scripts/validate_instance_protocol_split_receipt.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    split_payload = _parse_json_payload(out_split) or {}
    validators["instance_protocol_split_receipt"] = {
        "rc": rc_split,
        "ok": rc_split == 0,
        "out": out_split,
        "err": err_split,
    }
    split_status = str(split_payload.get("instance_protocol_split_status", "")).strip().upper()
    if rc_split != 0 or split_status == "FAIL_REQUIRED":
        hard_boundary = True

    lane_cmd = [
        "python3",
        "scripts/validate_work_layer_gate_set_routing.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--applied-gate-set",
        lane_applied_gate_set,
        "--force-check",
        "--json-only",
    ]
    if layer_intent_text:
        lane_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        lane_cmd.extend(["--expected-work-layer", effective_work_layer])
    if effective_source_layer:
        lane_cmd.extend(["--source-layer", effective_source_layer])
    rc_lane, out_lane, err_lane = _run(lane_cmd)
    lane_payload = _parse_json_payload(out_lane) or {}
    validators["work_layer_gate_set_routing"] = {
        "rc": rc_lane,
        "ok": rc_lane == 0,
        "out": out_lane,
        "err": err_lane,
    }
    lane_status = str(lane_payload.get("work_layer_gate_set_routing_status", "")).strip().upper()
    if rc_lane != 0 or lane_status == "FAIL_REQUIRED":
        hard_boundary = True

    reply_channel_cmd = [
        "python3",
        "scripts/validate_protocol_feedback_reply_channel.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--force-check",
        "--json-only",
    ]
    rc_reply_channel, out_reply_channel, err_reply_channel = _run(reply_channel_cmd)
    reply_channel_payload = _parse_json_payload(out_reply_channel) or {}
    validators["protocol_feedback_reply_channel"] = {
        "rc": rc_reply_channel,
        "ok": rc_reply_channel == 0,
        "out": out_reply_channel,
        "err": err_reply_channel,
    }
    reply_channel_status = str(reply_channel_payload.get("protocol_feedback_reply_channel_status", "")).strip().upper()
    if rc_reply_channel != 0 or reply_channel_status == "FAIL_REQUIRED":
        hard_boundary = True

    bootstrap_cmd = [
        "python3",
        "scripts/validate_protocol_feedback_bootstrap_ready.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--force-check",
        "--json-only",
    ]
    if layer_intent_text:
        bootstrap_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        bootstrap_cmd.extend(["--expected-work-layer", effective_work_layer])
    if effective_source_layer:
        bootstrap_cmd.extend(["--source-layer", effective_source_layer])
    rc_bootstrap, out_bootstrap, err_bootstrap = _run(bootstrap_cmd)
    bootstrap_payload = _parse_json_payload(out_bootstrap) or {}
    validators["protocol_feedback_bootstrap_ready"] = {
        "rc": rc_bootstrap,
        "ok": rc_bootstrap == 0,
        "out": out_bootstrap,
        "err": err_bootstrap,
    }
    bootstrap_status = str(bootstrap_payload.get("protocol_feedback_bootstrap_status", "")).strip().upper()
    if rc_bootstrap != 0 or bootstrap_status == "FAIL_REQUIRED":
        hard_boundary = True

    candidate_cmd = [
        "python3",
        "scripts/validate_protocol_entry_candidate_bridge.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--force-check",
        "--json-only",
    ]
    if layer_intent_text:
        candidate_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        candidate_cmd.extend(["--expected-work-layer", effective_work_layer])
    if effective_source_layer:
        candidate_cmd.extend(["--source-layer", effective_source_layer])
    rc_candidate, out_candidate, err_candidate = _run(candidate_cmd)
    candidate_payload = _parse_json_payload(out_candidate) or {}
    validators["protocol_entry_candidate_bridge"] = {
        "rc": rc_candidate,
        "ok": rc_candidate == 0,
        "out": out_candidate,
        "err": err_candidate,
    }
    candidate_status = str(candidate_payload.get("protocol_entry_candidate_status", "")).strip().upper()
    if rc_candidate != 0 or candidate_status == "FAIL_REQUIRED":
        hard_boundary = True

    inquiry_cmd = [
        "python3",
        "scripts/validate_protocol_inquiry_followup_chain.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--force-check",
        "--json-only",
    ]
    if layer_intent_text:
        inquiry_cmd.extend(["--layer-intent-text", layer_intent_text])
    if effective_work_layer:
        inquiry_cmd.extend(["--expected-work-layer", effective_work_layer])
    if effective_source_layer:
        inquiry_cmd.extend(["--source-layer", effective_source_layer])
    rc_inquiry, out_inquiry, err_inquiry = _run(inquiry_cmd)
    inquiry_payload = _parse_json_payload(out_inquiry) or {}
    validators["protocol_inquiry_followup_chain"] = {
        "rc": rc_inquiry,
        "ok": rc_inquiry == 0,
        "out": out_inquiry,
        "err": err_inquiry,
    }
    inquiry_status = str(inquiry_payload.get("protocol_inquiry_followup_chain_status", "")).strip().upper()
    if rc_inquiry != 0 or inquiry_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_semantic_iso, out_semantic_iso, err_semantic_iso = _run(
        [
            "python3",
            "scripts/validate_protocol_vendor_semantic_isolation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    semantic_iso_payload = _parse_json_payload(out_semantic_iso) or {}
    validators["protocol_vendor_semantic_isolation"] = {
        "rc": rc_semantic_iso,
        "ok": rc_semantic_iso == 0,
        "out": out_semantic_iso,
        "err": err_semantic_iso,
    }
    semantic_iso_status = str(semantic_iso_payload.get("protocol_vendor_semantic_isolation_status", "")).strip().upper()
    if rc_semantic_iso != 0 or semantic_iso_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_source_trust, out_source_trust, err_source_trust = _run(
        [
            "python3",
            "scripts/validate_external_source_trust_chain.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    source_trust_payload = _parse_json_payload(out_source_trust) or {}
    validators["external_source_trust_chain"] = {
        "rc": rc_source_trust,
        "ok": rc_source_trust == 0,
        "out": out_source_trust,
        "err": err_source_trust,
    }
    source_trust_status = str(source_trust_payload.get("external_source_trust_chain_status", "")).strip().upper()
    if rc_source_trust != 0 or source_trust_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_sanitization, out_sanitization, err_sanitization = _run(
        [
            "python3",
            "scripts/validate_protocol_data_sanitization_boundary.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    sanitization_payload = _parse_json_payload(out_sanitization) or {}
    validators["protocol_data_sanitization_boundary"] = {
        "rc": rc_sanitization,
        "ok": rc_sanitization == 0,
        "out": out_sanitization,
        "err": err_sanitization,
    }
    sanitization_status = (
        str(sanitization_payload.get("protocol_data_sanitization_boundary_status", "")).strip().upper()
    )
    if rc_sanitization != 0 or sanitization_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_opt_trigger, out_opt_trigger, err_opt_trigger = _run(
        [
            "python3",
            "scripts/trigger_platform_optimization_discovery.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    opt_trigger_payload = _parse_json_payload(out_opt_trigger) or {}
    validators["platform_optimization_discovery_trigger"] = {
        "rc": rc_opt_trigger,
        "ok": rc_opt_trigger == 0,
        "out": out_opt_trigger,
        "err": err_opt_trigger,
    }

    rc_dreq, out_dreq, err_dreq = _run(
        [
            "python3",
            "scripts/validate_discovery_requiredization.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    dreq_payload = _parse_json_payload(out_dreq) or {}
    validators["discovery_requiredization"] = {
        "rc": rc_dreq,
        "ok": rc_dreq == 0,
        "out": out_dreq,
        "err": err_dreq,
    }
    dreq_status = str(dreq_payload.get("discovery_requiredization_status", "")).strip().upper()
    if rc_dreq != 0 or dreq_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_vibe_pack, out_vibe_pack, err_vibe_pack = _run(
        [
            "python3",
            "scripts/build_vibe_coding_feeding_pack.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--out-root",
            vibe_pack_out_root,
            "--json-only",
        ]
    )
    vibe_pack_payload = _parse_json_payload(out_vibe_pack) or {}
    validators["vibe_coding_feeding_pack"] = {
        "rc": rc_vibe_pack,
        "ok": rc_vibe_pack == 0,
        "out": out_vibe_pack,
        "err": err_vibe_pack,
    }

    rc_cap_fit, out_cap_fit, err_cap_fit = _run(
        [
            "python3",
            "scripts/validate_identity_capability_fit_optimization.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    cap_fit_payload = _parse_json_payload(out_cap_fit) or {}
    validators["capability_fit_optimization"] = {
        "rc": rc_cap_fit,
        "ok": rc_cap_fit == 0,
        "out": out_cap_fit,
        "err": err_cap_fit,
    }
    cap_fit_status = str(cap_fit_payload.get("capability_fit_optimization_status", "")).strip().upper()
    if rc_cap_fit != 0 or cap_fit_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_compose, out_compose, err_compose = _run(
        [
            "python3",
            "scripts/validate_capability_composition_before_discovery.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    compose_payload = _parse_json_payload(out_compose) or {}
    validators["capability_composition_before_discovery"] = {
        "rc": rc_compose,
        "ok": rc_compose == 0,
        "out": out_compose,
        "err": err_compose,
    }
    compose_status = str(compose_payload.get("compose_before_discovery_status", "")).strip().upper()
    if rc_compose != 0 or compose_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fit_fresh, out_fit_fresh, err_fit_fresh = _run(
        [
            "python3",
            "scripts/validate_capability_fit_review_freshness.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fit_fresh_payload = _parse_json_payload(out_fit_fresh) or {}
    validators["capability_fit_review_freshness"] = {
        "rc": rc_fit_fresh,
        "ok": rc_fit_fresh == 0,
        "out": out_fit_fresh,
        "err": err_fit_fresh,
    }
    fit_fresh_status = str(fit_fresh_payload.get("capability_fit_review_freshness_status", "")).strip().upper()
    if rc_fit_fresh != 0 or fit_fresh_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fit_roundtable, out_fit_roundtable, err_fit_roundtable = _run(
        [
            "python3",
            "scripts/validate_capability_fit_roundtable_evidence.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fit_roundtable_payload = _parse_json_payload(out_fit_roundtable) or {}
    validators["capability_fit_roundtable_evidence"] = {
        "rc": rc_fit_roundtable,
        "ok": rc_fit_roundtable == 0,
        "out": out_fit_roundtable,
        "err": err_fit_roundtable,
    }
    fit_roundtable_status = str(fit_roundtable_payload.get("capability_fit_roundtable_status", "")).strip().upper()
    if rc_fit_roundtable != 0 or fit_roundtable_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fit_trigger, out_fit_trigger, err_fit_trigger = _run(
        [
            "python3",
            "scripts/trigger_capability_fit_review.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fit_trigger_payload = _parse_json_payload(out_fit_trigger) or {}
    validators["capability_fit_review_trigger"] = {
        "rc": rc_fit_trigger,
        "ok": rc_fit_trigger == 0,
        "out": out_fit_trigger,
        "err": err_fit_trigger,
    }

    rc_fit_builder, out_fit_builder, err_fit_builder = _run(
        [
            "python3",
            "scripts/build_capability_fit_matrix.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--out-root",
            capability_fit_out_root,
            "--json-only",
        ]
    )
    fit_builder_payload = _parse_json_payload(out_fit_builder) or {}
    validators["capability_fit_matrix_builder"] = {
        "rc": rc_fit_builder,
        "ok": rc_fit_builder == 0,
        "out": out_fit_builder,
        "err": err_fit_builder,
    }

    rc_namespace, out_namespace, err_namespace = _run(
        [
            "python3",
            "scripts/validate_vendor_namespace_separation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    namespace_payload = _parse_json_payload(out_namespace) or {}
    validators["vendor_namespace_separation"] = {
        "rc": rc_namespace,
        "ok": rc_namespace == 0,
        "out": out_namespace,
        "err": err_namespace,
    }
    namespace_status = str(namespace_payload.get("vendor_namespace_status", "")).strip().upper()
    if rc_namespace != 0 or namespace_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_writeback, out_writeback, err_writeback = _run(
        [
            "python3",
            "scripts/validate_writeback_continuity.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--report",
            str(report_path),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    writeback_payload = _parse_json_payload(out_writeback) or {}
    validators["writeback_continuity"] = {
        "rc": rc_writeback,
        "ok": rc_writeback == 0,
        "out": out_writeback,
        "err": err_writeback,
    }
    writeback_status = str(writeback_payload.get("writeback_continuity_status", "")).strip().upper()
    if rc_writeback != 0 or writeback_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_post_exec, out_post_exec, err_post_exec = _run(
        [
            "python3",
            "scripts/validate_post_execution_mandatory.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--report",
            str(report_path),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    post_exec_payload = _parse_json_payload(out_post_exec) or {}
    validators["post_execution_mandatory"] = {
        "rc": rc_post_exec,
        "ok": rc_post_exec == 0,
        "out": out_post_exec,
        "err": err_post_exec,
    }
    post_exec_status = str(post_exec_payload.get("post_execution_mandatory_status", "")).strip().upper()
    if rc_post_exec != 0 or post_exec_status == "FAIL_REQUIRED":
        hard_boundary = True

    sidecar_cmd = [
        "python3",
        "scripts/validate_protocol_feedback_sidecar_contract.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--report",
        str(report_path),
        "--current-round-anchor-utc",
        current_round_anchor_utc,
        "--operation",
        "three-plane",
        "--json-only",
    ]
    if report_run_id:
        sidecar_cmd.extend(["--run-id", report_run_id])
    rc_sidecar, out_sidecar, err_sidecar = _run(sidecar_cmd)
    sidecar_payload = _parse_json_payload(out_sidecar) or {}
    validators["protocol_feedback_sidecar"] = {
        "rc": rc_sidecar,
        "ok": rc_sidecar == 0,
        "out": out_sidecar,
        "err": err_sidecar,
    }
    sidecar_status = str(sidecar_payload.get("sidecar_contract_status", "")).strip().upper()
    if rc_sidecar != 0 or sidecar_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_base_boundary, out_base_boundary, err_base_boundary = _run(
        [
            "python3",
            "scripts/validate_instance_base_repo_write_boundary.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--report",
            str(report_path),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    base_boundary_payload = _parse_json_payload(out_base_boundary) or {}
    validators["instance_base_repo_write_boundary"] = {
        "rc": rc_base_boundary,
        "ok": rc_base_boundary == 0,
        "out": out_base_boundary,
        "err": err_base_boundary,
    }
    base_boundary_status = str(base_boundary_payload.get("base_repo_write_boundary_status", "")).strip().upper()
    if rc_base_boundary != 0 or base_boundary_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_archival, out_archival, err_archival = _run(
        [
            "python3",
            "scripts/validate_protocol_feedback_ssot_archival.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    archival_payload = _parse_json_payload(out_archival) or {}
    validators["protocol_feedback_ssot_archival"] = {
        "rc": rc_archival,
        "ok": rc_archival == 0,
        "out": out_archival,
        "err": err_archival,
    }
    archival_status = str(archival_payload.get("feedback_ssot_archival_status", "")).strip().upper()
    if rc_archival != 0 or archival_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_downsink_immutability, out_downsink_immutability, err_downsink_immutability = _run(
        [
            "python3",
            "scripts/validate_protocol_downsink_path_immutability.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    downsink_immutability_payload = _parse_json_payload(out_downsink_immutability) or {}
    validators["downsink_path_immutability"] = {
        "rc": rc_downsink_immutability,
        "ok": rc_downsink_immutability == 0,
        "out": out_downsink_immutability,
        "err": err_downsink_immutability,
    }
    downsink_immutability_status = str(
        downsink_immutability_payload.get("protocol_downsink_path_immutability_status", "")
    ).strip().upper()
    if rc_downsink_immutability != 0 or downsink_immutability_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_downsink_write_guard, out_downsink_write_guard, err_downsink_write_guard = _run(
        [
            "python3",
            "scripts/validate_protocol_downsink_path_write_guard.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    downsink_write_guard_payload = _parse_json_payload(out_downsink_write_guard) or {}
    validators["downsink_path_write_guard"] = {
        "rc": rc_downsink_write_guard,
        "ok": rc_downsink_write_guard == 0,
        "out": out_downsink_write_guard,
        "err": err_downsink_write_guard,
    }
    downsink_write_guard_status = str(
        downsink_write_guard_payload.get("protocol_downsink_path_write_guard_status", "")
    ).strip().upper()
    if rc_downsink_write_guard != 0 or downsink_write_guard_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_downsink_literal_lock, out_downsink_literal_lock, err_downsink_literal_lock = _run(
        [
            "python3",
            "scripts/validate_protocol_downsink_path_literal_lock.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    downsink_literal_lock_payload = _parse_json_payload(out_downsink_literal_lock) or {}
    validators["downsink_path_literal_lock"] = {
        "rc": rc_downsink_literal_lock,
        "ok": rc_downsink_literal_lock == 0,
        "out": out_downsink_literal_lock,
        "err": err_downsink_literal_lock,
    }
    downsink_literal_lock_status = str(
        downsink_literal_lock_payload.get("protocol_downsink_path_literal_lock_status", "")
    ).strip().upper()
    if rc_downsink_literal_lock != 0 or downsink_literal_lock_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fresh, out_fresh, err_fresh = _run(
        [
            "python3",
            "scripts/validate_execution_report_freshness.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--report",
            str(report_path),
            "--execution-report-policy",
            "strict",
            "--json-only",
        ]
    )
    freshness_payload = _parse_json_payload(out_fresh) or {}
    validators["execution_report_freshness"] = {
        "rc": rc_fresh,
        "ok": rc_fresh == 0,
        "out": out_fresh,
        "err": err_fresh,
    }

    rc_baseline, out_baseline, err_baseline = _run(
        [
            "python3",
            "scripts/validate_identity_protocol_baseline_freshness.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--execution-report",
            str(report_path),
            "--baseline-policy",
            "warn",
            "--json-only",
        ]
    )
    baseline_payload = _parse_json_payload(out_baseline) or {}
    validators["protocol_baseline_freshness"] = {
        "rc": rc_baseline,
        "ok": rc_baseline == 0,
        "out": out_baseline,
        "err": err_baseline,
    }

    rc_align, out_align, err_align = _run(
        [
            "python3",
            "scripts/validate_identity_protocol_version_alignment.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--execution-report",
            str(report_path),
            "--operation",
            "three-plane",
            "--alignment-policy",
            "warn",
            "--json-only",
        ]
    )
    align_payload = _parse_json_payload(out_align) or {}
    validators["protocol_version_alignment"] = {
        "rc": rc_align,
        "ok": rc_align == 0,
        "out": out_align,
        "err": err_align,
    }
    align_status = str(align_payload.get("protocol_version_alignment_status", "")).strip().upper()
    if rc_align != 0 or align_status == "FAIL_REQUIRED":
        hard_boundary = True

    detail = {
        "report_path": str(report_path),
        "all_ok": all_ok,
        "writeback_status": wb,
        "permission_state": ps,
        "effective_expected_work_layer": effective_work_layer,
        "effective_expected_source_layer": effective_source_layer,
        "detected_session_lane_lock": lane_lock_hint,
        "capability_activation_status": cap_status,
        "capability_activation_error_code": cap_error,
        "next_action": next_action,
        "error_code": err_code,
        "mandatory_fields_complete": bool(mandatory),
        "hard_boundary": hard_boundary,
        "prompt_runtime_state_externalization": {
            "prompt_policy_hash": data.get("prompt_policy_hash", ""),
            "runtime_state_artifact_path": data.get("runtime_state_artifact_path", ""),
            "runtime_state_artifact_hash": data.get("runtime_state_artifact_hash", ""),
            "prompt_runtime_state_binding_status": data.get("prompt_runtime_state_binding_status", ""),
            "prompt_runtime_state_externalization_status": data.get("prompt_runtime_state_externalization_status", ""),
            "prompt_runtime_state_externalization_error_code": data.get("prompt_runtime_state_externalization_error_code", ""),
        },
        "required_contract_coverage": {
            "required_contract_total": coverage_payload.get("required_contract_total"),
            "required_contract_passed": coverage_payload.get("required_contract_passed"),
            "required_contract_coverage_rate": coverage_payload.get("required_contract_coverage_rate"),
            "discovery_required_total": coverage_payload.get("discovery_required_total"),
            "discovery_required_passed": coverage_payload.get("discovery_required_passed"),
            "discovery_required_coverage_rate": coverage_payload.get("discovery_required_coverage_rate"),
            "discovery_required_gate_failed": coverage_payload.get("discovery_required_gate_failed"),
            "skipped_contract_count": coverage_payload.get("skipped_contract_count"),
            "failed_required_contract_count": coverage_payload.get("failed_required_contract_count"),
            "failed_optional_contract_count": coverage_payload.get("failed_optional_contract_count"),
        },
        "unlock_formula_automation": {
            "unlock_formula_status": unlock_formula_payload.get("unlock_formula_status"),
            "error_code": unlock_formula_payload.get("error_code", ""),
            "required_contract": unlock_formula_payload.get("required_contract"),
            "auto_required_signal": unlock_formula_payload.get("auto_required_signal"),
            "unlock_allowed": unlock_formula_payload.get("unlock_allowed"),
            "decision_gates": unlock_formula_payload.get("decision_gates", {}),
            "p0_total": unlock_formula_payload.get("p0_total"),
            "p0_done": unlock_formula_payload.get("p0_done"),
            "p0_not_done_refs": unlock_formula_payload.get("p0_not_done_refs", []),
            "audit_signoff_status": unlock_formula_payload.get("audit_signoff_status", ""),
            "env_blockers": unlock_formula_payload.get("env_blockers", []),
            "protocol_blockers": unlock_formula_payload.get("protocol_blockers", []),
            "formula_input_digest": unlock_formula_payload.get("formula_input_digest", ""),
            "stale_reasons": unlock_formula_payload.get("stale_reasons", []),
            "evidence_ref": unlock_formula_payload.get("evidence_ref", ""),
        },
        "release_plane_cloud_evidence": {
            "release_plane_cloud_evidence_status": release_cloud_payload.get("release_plane_cloud_evidence_status"),
            "error_code": release_cloud_payload.get("error_code", ""),
            "required_contract": release_cloud_payload.get("required_contract"),
            "auto_required_signal": release_cloud_payload.get("auto_required_signal"),
            "release_plane_status": release_cloud_payload.get("release_plane_status", ""),
            "conditions": release_cloud_payload.get("conditions", {}),
            "target_branch": release_cloud_payload.get("target_branch", ""),
            "release_head_sha": release_cloud_payload.get("release_head_sha", ""),
            "required_gates_run_id": release_cloud_payload.get("required_gates_run_id", ""),
            "stale_reasons": release_cloud_payload.get("stale_reasons", []),
            "evidence_ref": release_cloud_payload.get("evidence_ref", ""),
        },
        "cross_cwd_absolute_input": {
            "cross_cwd_absolute_input_status": cross_cwd_payload.get("cross_cwd_absolute_input_status"),
            "error_code": cross_cwd_payload.get("error_code", ""),
            "required_contract": cross_cwd_payload.get("required_contract"),
            "auto_required_signal": cross_cwd_payload.get("auto_required_signal"),
            "repo_catalog_input": cross_cwd_payload.get("repo_catalog_input", ""),
            "repo_catalog_is_absolute": cross_cwd_payload.get("repo_catalog_is_absolute"),
            "repo_cwd_resolved_repo_catalog": cross_cwd_payload.get("repo_cwd_resolved_repo_catalog", ""),
            "tmp_cwd_resolved_repo_catalog": cross_cwd_payload.get("tmp_cwd_resolved_repo_catalog", ""),
            "cwd_parity_status": cross_cwd_payload.get("cwd_parity_status", ""),
            "stale_reasons": cross_cwd_payload.get("stale_reasons", []),
            "evidence_ref": cross_cwd_payload.get("evidence_ref", ""),
        },
        "run_id_report_selection": {
            "run_id_report_selection_status": run_selector_payload.get("run_id_report_selection_status"),
            "error_code": run_selector_payload.get("error_code", ""),
            "required_contract": run_selector_payload.get("required_contract"),
            "auto_required_signal": run_selector_payload.get("auto_required_signal"),
            "run_id": run_selector_payload.get("run_id", ""),
            "selection_strategy": run_selector_payload.get("selection_strategy", ""),
            "report_selected_path": run_selector_payload.get("report_selected_path", ""),
            "candidate_count": run_selector_payload.get("candidate_count"),
            "stale_reasons": run_selector_payload.get("stale_reasons", []),
            "evidence_ref": run_selector_payload.get("evidence_ref", ""),
        },
        "phase_bootstrap_before_strict": {
            "phase_bootstrap_before_strict_status": phase_bootstrap_payload.get("phase_bootstrap_before_strict_status"),
            "error_code": phase_bootstrap_payload.get("error_code", ""),
            "required_contract": phase_bootstrap_payload.get("required_contract"),
            "auto_required_signal": phase_bootstrap_payload.get("auto_required_signal"),
            "phase_a_refresh_applied": phase_bootstrap_payload.get("phase_a_refresh_applied"),
            "phase_b_strict_revalidate_status": phase_bootstrap_payload.get("phase_b_strict_revalidate_status", ""),
            "phase_trace_status": phase_bootstrap_payload.get("phase_trace_status", ""),
            "stale_reasons": phase_bootstrap_payload.get("stale_reasons", []),
            "evidence_ref": phase_bootstrap_payload.get("evidence_ref", ""),
        },
        "tmp_collision_safety": {
            "tmp_collision_safety_status": tmp_collision_payload.get("tmp_collision_safety_status"),
            "error_code": tmp_collision_payload.get("error_code", ""),
            "required_contract": tmp_collision_payload.get("required_contract"),
            "auto_required_signal": tmp_collision_payload.get("auto_required_signal"),
            "tmp_root": tmp_collision_payload.get("tmp_root", ""),
            "collision_count": tmp_collision_payload.get("collision_count"),
            "unique_path_count": tmp_collision_payload.get("unique_path_count"),
            "generated_paths": tmp_collision_payload.get("generated_paths", []),
            "stale_reasons": tmp_collision_payload.get("stale_reasons", []),
            "evidence_ref": tmp_collision_payload.get("evidence_ref", ""),
        },
        "handoff_collab_freshness_rotation": {
            "handoff_collab_freshness_rotation_status": fresh_rotation_payload.get("handoff_collab_freshness_rotation_status"),
            "error_code": fresh_rotation_payload.get("error_code", ""),
            "required_contract": fresh_rotation_payload.get("required_contract"),
            "auto_required_signal": fresh_rotation_payload.get("auto_required_signal"),
            "rotation_applied": fresh_rotation_payload.get("rotation_applied"),
            "freshness_age_days": fresh_rotation_payload.get("freshness_age_days"),
            "freshness_status": fresh_rotation_payload.get("freshness_status", ""),
            "rotation_receipt_ref": fresh_rotation_payload.get("rotation_receipt_ref", ""),
            "stale_reasons": fresh_rotation_payload.get("stale_reasons", []),
            "evidence_ref": fresh_rotation_payload.get("evidence_ref", ""),
        },
        "protocol_feedback_atomic_emit": {
            "protocol_feedback_atomic_emit_status": atomic_emit_payload.get("protocol_feedback_atomic_emit_status"),
            "error_code": atomic_emit_payload.get("error_code", ""),
            "required_contract": atomic_emit_payload.get("required_contract"),
            "auto_required_signal": atomic_emit_payload.get("auto_required_signal"),
            "transaction_id": atomic_emit_payload.get("transaction_id", ""),
            "batch_ref": atomic_emit_payload.get("batch_ref", ""),
            "index_ref": atomic_emit_payload.get("index_ref", ""),
            "receipt_ref": atomic_emit_payload.get("receipt_ref", ""),
            "stale_reasons": atomic_emit_payload.get("stale_reasons", []),
            "evidence_ref": atomic_emit_payload.get("evidence_ref", ""),
        },
        "capability_boundary_classification": {
            "capability_boundary_status": cap_boundary_payload.get("capability_boundary_status"),
            "error_code": cap_boundary_payload.get("error_code", ""),
            "required_contract": cap_boundary_payload.get("required_contract"),
            "auto_required_signal": cap_boundary_payload.get("auto_required_signal"),
            "boundary_classification": cap_boundary_payload.get("boundary_classification", ""),
            "classification_source": cap_boundary_payload.get("classification_source", ""),
            "capability_activation_status": cap_boundary_payload.get("capability_activation_status", ""),
            "capability_activation_error_code": cap_boundary_payload.get("capability_activation_error_code", ""),
            "stale_reasons": cap_boundary_payload.get("stale_reasons", []),
            "evidence_ref": cap_boundary_payload.get("evidence_ref", ""),
        },
        "promotion_evidence_pipeline": {
            "promotion_pipeline_status": promotion_pipeline_payload.get("promotion_pipeline_status"),
            "error_code": promotion_pipeline_payload.get("error_code", ""),
            "required_contract": promotion_pipeline_payload.get("required_contract"),
            "auto_required_signal": promotion_pipeline_payload.get("auto_required_signal"),
            "decision_hash": promotion_pipeline_payload.get("decision_hash", ""),
            "input_hash": promotion_pipeline_payload.get("input_hash", ""),
            "reviewer_role": promotion_pipeline_payload.get("reviewer_role", ""),
            "reviewer_signature_ref": promotion_pipeline_payload.get("reviewer_signature_ref", ""),
            "evidence_bundle_refs": promotion_pipeline_payload.get("evidence_bundle_refs", []),
            "receipt_path": promotion_pipeline_payload.get("receipt_path", ""),
            "stale_reasons": promotion_pipeline_payload.get("stale_reasons", []),
            "evidence_ref": promotion_pipeline_payload.get("evidence_ref", ""),
        },
        "outlet_regression_matrix": {
            "outlet_matrix_status": outlet_matrix_payload.get("outlet_matrix_status"),
            "error_code": outlet_matrix_payload.get("error_code", ""),
            "required_contract": outlet_matrix_payload.get("required_contract"),
            "auto_required_signal": outlet_matrix_payload.get("auto_required_signal"),
            "matrix_positive_status": outlet_matrix_payload.get("matrix_positive_status", ""),
            "matrix_negative_status": outlet_matrix_payload.get("matrix_negative_status", ""),
            "cross_cwd_parity_status": outlet_matrix_payload.get("cross_cwd_parity_status", ""),
            "send_time_gate_status": outlet_matrix_payload.get("send_time_gate_status", ""),
            "governed_outlet_enforced": outlet_matrix_payload.get("governed_outlet_enforced"),
            "outlet_channel_id": outlet_matrix_payload.get("outlet_channel_id", ""),
            "outlet_bypass_detected": outlet_matrix_payload.get("outlet_bypass_detected"),
            "stale_reasons": outlet_matrix_payload.get("stale_reasons", []),
            "evidence_ref": outlet_matrix_payload.get("evidence_ref", ""),
        },
        "sidecar_cwd_parity": {
            "sidecar_cwd_parity_status": sidecar_cwd_payload.get("sidecar_cwd_parity_status"),
            "cwd_parity_status": sidecar_cwd_payload.get("cwd_parity_status", ""),
            "error_code": sidecar_cwd_payload.get("error_code", ""),
            "required_contract": sidecar_cwd_payload.get("required_contract"),
            "auto_required_signal": sidecar_cwd_payload.get("auto_required_signal"),
            "passthrough_digest": sidecar_cwd_payload.get("passthrough_digest", ""),
            "root_digest": sidecar_cwd_payload.get("root_digest", ""),
            "temp_digest": sidecar_cwd_payload.get("temp_digest", ""),
            "sidecar_contract_status": sidecar_cwd_payload.get("sidecar_contract_status", ""),
            "sidecar_error_code": sidecar_cwd_payload.get("sidecar_error_code", ""),
            "stale_reasons": sidecar_cwd_payload.get("stale_reasons", []),
            "evidence_ref": sidecar_cwd_payload.get("evidence_ref", ""),
        },
        "docs_bridge_consistency": {
            "bridge_consistency_status": docs_bridge_payload.get("bridge_consistency_status"),
            "error_code": docs_bridge_payload.get("error_code", ""),
            "required_contract": docs_bridge_payload.get("required_contract"),
            "auto_required_signal": docs_bridge_payload.get("auto_required_signal"),
            "contradiction_pairs": docs_bridge_payload.get("contradiction_pairs", []),
            "governance_anchor_refs": docs_bridge_payload.get("governance_anchor_refs", []),
            "review_anchor_refs": docs_bridge_payload.get("review_anchor_refs", []),
            "stale_reasons": docs_bridge_payload.get("stale_reasons", []),
            "evidence_ref": docs_bridge_payload.get("evidence_ref", ""),
        },
        "contract_mapping_coverage": {
            "contract_mapping_coverage_status": mapping_coverage_payload.get("contract_mapping_coverage_status"),
            "error_code": mapping_coverage_payload.get("error_code", ""),
            "required_contract": mapping_coverage_payload.get("required_contract"),
            "auto_required_signal": mapping_coverage_payload.get("auto_required_signal"),
            "total_requirements": mapping_coverage_payload.get("total_requirements"),
            "p0_total": mapping_coverage_payload.get("p0_total"),
            "mapped_total": mapping_coverage_payload.get("mapped_total"),
            "p0_mapped": mapping_coverage_payload.get("p0_mapped"),
            "coverage_rate": mapping_coverage_payload.get("coverage_rate"),
            "p0_coverage_rate": mapping_coverage_payload.get("p0_coverage_rate"),
            "orphan_count": mapping_coverage_payload.get("orphan_count"),
            "unmapped_p0_requirements": mapping_coverage_payload.get("unmapped_p0_requirements", []),
            "stale_reasons": mapping_coverage_payload.get("stale_reasons", []),
            "evidence_ref": mapping_coverage_payload.get("evidence_ref", ""),
        },
        "prompt_bootstrap_capability": {
            "prompt_bootstrap_contract_status": prompt_bootstrap_payload.get("prompt_bootstrap_contract_status"),
            "error_code": prompt_bootstrap_payload.get("error_code", ""),
            "required_contract": prompt_bootstrap_payload.get("required_contract"),
            "auto_required_signal": prompt_bootstrap_payload.get("auto_required_signal"),
            "capability_driver_required_total": prompt_bootstrap_payload.get("capability_driver_required_total"),
            "capability_driver_present_total": prompt_bootstrap_payload.get("capability_driver_present_total"),
            "capability_driver_coverage_rate": prompt_bootstrap_payload.get("capability_driver_coverage_rate"),
            "missing_capability_drivers": prompt_bootstrap_payload.get("missing_capability_drivers", []),
            "stale_reasons": prompt_bootstrap_payload.get("stale_reasons", []),
            "evidence_ref": prompt_bootstrap_payload.get("evidence_ref", ""),
        },
        "prompt_capability_matrix": {
            "prompt_capability_matrix_status": prompt_matrix_payload.get("prompt_capability_matrix_status"),
            "error_code": prompt_matrix_payload.get("error_code", ""),
            "required_contract": prompt_matrix_payload.get("required_contract"),
            "auto_required_signal": prompt_matrix_payload.get("auto_required_signal"),
            "capability_driver_required_total": prompt_matrix_payload.get("capability_driver_required_total"),
            "capability_driver_present_total": prompt_matrix_payload.get("capability_driver_present_total"),
            "capability_driver_coverage_rate": prompt_matrix_payload.get("capability_driver_coverage_rate"),
            "missing_capability_drivers": prompt_matrix_payload.get("missing_capability_drivers", []),
            "stale_reasons": prompt_matrix_payload.get("stale_reasons", []),
            "evidence_ref": prompt_matrix_payload.get("evidence_ref", ""),
        },
        "refresh_strict_business_interference": {
            "refresh_strict_business_interference_status": interference_payload.get("refresh_strict_business_interference_status"),
            "error_code": interference_payload.get("error_code", ""),
            "required_contract": interference_payload.get("required_contract"),
            "auto_required_signal": interference_payload.get("auto_required_signal"),
            "refresh_receipt_ref": interference_payload.get("refresh_receipt_ref", ""),
            "strict_receipt_ref": interference_payload.get("strict_receipt_ref", ""),
            "refresh_status": interference_payload.get("refresh_status", ""),
            "strict_status": interference_payload.get("strict_status", ""),
            "interference_row_count_refresh": interference_payload.get("interference_row_count_refresh"),
            "interference_row_count_strict": interference_payload.get("interference_row_count_strict"),
            "stale_reasons": interference_payload.get("stale_reasons", []),
            "evidence_ref": interference_payload.get("evidence_ref", ""),
        },
        "kernel_ssot_source": {
            "kernel_ssot_source_status": kernel_ssot_payload.get("kernel_ssot_source_status"),
            "error_code": kernel_ssot_payload.get("error_code", ""),
            "required_contract": kernel_ssot_payload.get("required_contract"),
            "auto_required_signal": kernel_ssot_payload.get("auto_required_signal"),
            "canonical_source_paths": kernel_ssot_payload.get("canonical_source_paths", []),
            "missing_source_paths": kernel_ssot_payload.get("missing_source_paths", []),
            "ssot_validator_rc": kernel_ssot_payload.get("ssot_validator_rc"),
            "stale_reasons": kernel_ssot_payload.get("stale_reasons", []),
            "evidence_ref": kernel_ssot_payload.get("evidence_ref", ""),
        },
        "prompt_derivation_conformance": {
            "prompt_derivation_conformance_status": prompt_derivation_payload.get("prompt_derivation_conformance_status"),
            "error_code": prompt_derivation_payload.get("error_code", ""),
            "required_contract": prompt_derivation_payload.get("required_contract"),
            "auto_required_signal": prompt_derivation_payload.get("auto_required_signal"),
            "kernel_contract_version": prompt_derivation_payload.get("kernel_contract_version", ""),
            "kernel_contract_digest": prompt_derivation_payload.get("kernel_contract_digest", ""),
            "derived_from_contract_ids": prompt_derivation_payload.get("derived_from_contract_ids", []),
            "overlay_digest": prompt_derivation_payload.get("overlay_digest", ""),
            "stale_reasons": prompt_derivation_payload.get("stale_reasons", []),
            "evidence_ref": prompt_derivation_payload.get("evidence_ref", ""),
        },
        "semantic_convergence": {
            "semantic_convergence_status": semantic_convergence_payload.get("semantic_convergence_status"),
            "semantic_convergence_error_code": semantic_convergence_payload.get("semantic_convergence_error_code", ""),
            "required_contract": semantic_convergence_payload.get("required_contract"),
            "auto_required_signal": semantic_convergence_payload.get("auto_required_signal"),
            "lineage_ref": semantic_convergence_payload.get("lineage_ref", ""),
            "mismatch_count": semantic_convergence_payload.get("mismatch_count"),
            "mismatch_fields": semantic_convergence_payload.get("mismatch_fields", []),
            "stale_reasons": semantic_convergence_payload.get("stale_reasons", []),
            "evidence_ref": semantic_convergence_payload.get("evidence_ref", ""),
        },
        "prompt_kernel_executable_coupling": {
            "prompt_kernel_executable_coupling_status": prompt_coupling_payload.get("prompt_kernel_executable_coupling_status"),
            "error_code": prompt_coupling_payload.get("error_code", ""),
            "required_contract": prompt_coupling_payload.get("required_contract"),
            "auto_required_signal": prompt_coupling_payload.get("auto_required_signal"),
            "kernel_contract_ref": prompt_coupling_payload.get("kernel_contract_ref", ""),
            "validator_ref": prompt_coupling_payload.get("validator_ref", ""),
            "actor_context_explicit": prompt_coupling_payload.get("actor_context_explicit"),
            "routing_validator_rc": prompt_coupling_payload.get("routing_validator_rc"),
            "stale_reasons": prompt_coupling_payload.get("stale_reasons", []),
            "evidence_ref": prompt_coupling_payload.get("evidence_ref", ""),
        },
        "required_gate_bundle_runner": {
            "required_gate_bundle_runner_status": required_bundle_payload.get("bundle_status"),
            "error_code": required_bundle_payload.get("error_code", ""),
            "bundle_contract_id": required_bundle_payload.get("bundle_contract_id", ""),
            "bundle_key": required_bundle_payload.get("bundle_key", ""),
            "surface_label": required_bundle_payload.get("surface_label", ""),
            "identity_id": required_bundle_payload.get("identity_id", ""),
            "actor_id": required_bundle_payload.get("actor_id", ""),
            "resolved_work_layer": required_bundle_payload.get("resolved_work_layer", ""),
            "resolved_source_layer": required_bundle_payload.get("resolved_source_layer", ""),
            "lock_state": required_bundle_payload.get("lock_state", ""),
            "required_contract": required_bundle_payload.get("required_contract"),
            "failed_required_contract_count": required_bundle_payload.get("failed_required_contract_count"),
            "row_contract_error_count": required_bundle_payload.get("row_contract_error_count"),
            "run_id_binding": required_bundle_payload.get("run_id_binding", ""),
            "report_selected_path": required_bundle_payload.get("report_selected_path", ""),
            "send_time_gate_status": required_bundle_payload.get("send_time_gate_status", ""),
            "outlet_bypass_detected": required_bundle_payload.get("outlet_bypass_detected"),
            "final_emit_contract_status": required_bundle_payload.get("final_emit_contract_status", ""),
            "final_emit_policy_mode": required_bundle_payload.get("final_emit_policy_mode", ""),
            "final_emit_schema_status": required_bundle_payload.get("final_emit_schema_status", ""),
            "mapping_errors": required_bundle_payload.get("mapping_errors", []),
            "missing_targets": required_bundle_payload.get("missing_targets", []),
            "contract_mapping": required_bundle_payload.get("contract_mapping", ""),
            "result_rows": required_bundle_payload.get("results", []),
        },
        "required_gate_bundle_runner_shadow": {
            "required_gate_bundle_runner_shadow_status": required_bundle_shadow_payload.get("bundle_status"),
            "error_code": required_bundle_shadow_payload.get("error_code", ""),
            "surface_label": required_bundle_shadow_payload.get("surface_label", ""),
            "identity_id": required_bundle_shadow_payload.get("identity_id", ""),
            "actor_id": required_bundle_shadow_payload.get("actor_id", ""),
            "resolved_work_layer": required_bundle_shadow_payload.get("resolved_work_layer", ""),
            "resolved_source_layer": required_bundle_shadow_payload.get("resolved_source_layer", ""),
            "lock_state": required_bundle_shadow_payload.get("lock_state", ""),
            "required_contract": required_bundle_shadow_payload.get("required_contract"),
            "failed_required_contract_count": required_bundle_shadow_payload.get("failed_required_contract_count"),
            "row_contract_error_count": required_bundle_shadow_payload.get("row_contract_error_count"),
            "run_id_binding": required_bundle_shadow_payload.get("run_id_binding", ""),
            "report_selected_path": required_bundle_shadow_payload.get("report_selected_path", ""),
            "send_time_gate_status": required_bundle_shadow_payload.get("send_time_gate_status", ""),
            "outlet_bypass_detected": required_bundle_shadow_payload.get("outlet_bypass_detected"),
            "final_emit_contract_status": required_bundle_shadow_payload.get("final_emit_contract_status", ""),
            "final_emit_policy_mode": required_bundle_shadow_payload.get("final_emit_policy_mode", ""),
            "final_emit_schema_status": required_bundle_shadow_payload.get("final_emit_schema_status", ""),
            "mapping_errors": required_bundle_shadow_payload.get("mapping_errors", []),
            "missing_targets": required_bundle_shadow_payload.get("missing_targets", []),
            "contract_mapping": required_bundle_shadow_payload.get("contract_mapping", ""),
            "result_rows": required_bundle_shadow_payload.get("results", []),
        },
        "required_gate_recurrence_escalator": {
            "required_gate_recurrence_status": recurrence_payload.get("required_gate_recurrence_status"),
            "error_code": recurrence_payload.get("error_code", ""),
            "escalation_level": recurrence_payload.get("escalation_level", ""),
            "surface": recurrence_payload.get("surface", ""),
            "operation": recurrence_payload.get("operation", ""),
            "receipt_path": recurrence_payload.get("receipt_path", ""),
            "state_path": recurrence_payload.get("state_path", ""),
            "new_event_count": recurrence_payload.get("new_event_count"),
            "tracked_event_count": recurrence_payload.get("tracked_event_count"),
            "l1_error_families": recurrence_payload.get("l1_error_families", []),
            "l2_error_families": recurrence_payload.get("l2_error_families", []),
            "l3_error_families": recurrence_payload.get("l3_error_families", []),
            "family_metrics": recurrence_payload.get("family_metrics", []),
            "stale_reasons": recurrence_payload.get("stale_reasons", []),
        },
        "required_gate_tuple_parity": {
            "required_gate_tuple_parity_status": tuple_parity_payload.get("required_gate_tuple_parity_status"),
            "error_code": tuple_parity_payload.get("error_code", ""),
            "tuple_fields": tuple_parity_payload.get("tuple_fields", []),
            "core_tuple_fields": tuple_parity_payload.get("core_tuple_fields", []),
            "conditional_tuple_fields": tuple_parity_payload.get("conditional_tuple_fields", []),
            "receipts_checked": tuple_parity_payload.get("receipts_checked", []),
            "surface_labels_checked": tuple_parity_payload.get("surface_labels_checked", []),
            "min_receipts": tuple_parity_payload.get("min_receipts"),
            "require_distinct_surface_labels": tuple_parity_payload.get("require_distinct_surface_labels"),
            "require_distinct_operations": tuple_parity_payload.get("require_distinct_operations"),
            "operations_checked": tuple_parity_payload.get("operations_checked", []),
            "missing_operations": tuple_parity_payload.get("missing_operations", []),
            "duplicate_operations": tuple_parity_payload.get("duplicate_operations", {}),
            "parity_contract_reasons": tuple_parity_payload.get("parity_contract_reasons", []),
            "missing_surface_labels": tuple_parity_payload.get("missing_surface_labels", []),
            "duplicate_surface_labels": tuple_parity_payload.get("duplicate_surface_labels", {}),
            "load_errors": tuple_parity_payload.get("load_errors", []),
            "missing_fields": tuple_parity_payload.get("missing_fields", {}),
            "mismatches": tuple_parity_payload.get("mismatches", {}),
            "stale_reasons": tuple_parity_payload.get("stale_reasons", []),
        },
        "cross_verification_tracks": {
            "cross_verification_tracks_status": cross_verify_payload.get("cross_verification_tracks_status"),
            "error_code": cross_verify_payload.get("error_code", ""),
            "required_contract": cross_verify_payload.get("required_contract"),
            "auto_required_signal": cross_verify_payload.get("auto_required_signal"),
            "cross_verification_bundle_id": cross_verify_payload.get("cross_verification_bundle_id", ""),
            "source_url_set": cross_verify_payload.get("source_url_set", []),
            "reference_timestamp_utc": cross_verify_payload.get("reference_timestamp_utc", ""),
            "conflict_reconciliation_note": cross_verify_payload.get("conflict_reconciliation_note", ""),
            "missing_tracks": cross_verify_payload.get("missing_tracks", []),
            "missing_metadata_fields": cross_verify_payload.get("missing_metadata_fields", []),
            "stale_reasons": cross_verify_payload.get("stale_reasons", []),
            "evidence_ref": cross_verify_payload.get("evidence_ref", ""),
        },
        "intake_evidence_quorum": {
            "intake_evidence_quorum_status": intake_quorum_payload.get("intake_evidence_quorum_status"),
            "error_code": intake_quorum_payload.get("error_code", ""),
            "required_contract": intake_quorum_payload.get("required_contract"),
            "auto_required_signal": intake_quorum_payload.get("auto_required_signal"),
            "cross_verification_bundle_id": intake_quorum_payload.get("cross_verification_bundle_id", ""),
            "source_url_set": intake_quorum_payload.get("source_url_set", []),
            "reference_timestamp_utc": intake_quorum_payload.get("reference_timestamp_utc", ""),
            "conflict_reconciliation_note": intake_quorum_payload.get("conflict_reconciliation_note", ""),
            "missing_tracks": intake_quorum_payload.get("missing_tracks", []),
            "missing_metadata_fields": intake_quorum_payload.get("missing_metadata_fields", []),
            "stale_reasons": intake_quorum_payload.get("stale_reasons", []),
            "evidence_ref": intake_quorum_payload.get("evidence_ref", ""),
        },
        "route_version_pinning": {
            "pin_status": route_pin_payload.get("pin_status"),
            "pin_error_code": route_pin_payload.get("pin_error_code", ""),
            "required_contract": route_pin_payload.get("required_contract"),
            "auto_required_signal": route_pin_payload.get("auto_required_signal"),
            "route_endpoint": route_pin_payload.get("route_endpoint", ""),
            "workflow_id": route_pin_payload.get("workflow_id", ""),
            "workflow_publish_version": route_pin_payload.get("workflow_publish_version", ""),
            "pin_proof_ref": route_pin_payload.get("pin_proof_ref", ""),
            "expected_route_endpoint": route_pin_payload.get("expected_route_endpoint", ""),
            "expected_workflow_id": route_pin_payload.get("expected_workflow_id", ""),
            "expected_workflow_publish_version": route_pin_payload.get("expected_workflow_publish_version", ""),
            "mismatch_fields": route_pin_payload.get("mismatch_fields", []),
            "receipt_path": route_pin_payload.get("receipt_path", ""),
            "stale_reasons": route_pin_payload.get("stale_reasons", []),
            "evidence_ref": route_pin_payload.get("evidence_ref", ""),
        },
        "fallback_taxonomy_normalization": {
            "fallback_taxonomy_normalization_status": fallback_norm_payload.get("fallback_taxonomy_normalization_status"),
            "normalization_error_code": fallback_norm_payload.get("normalization_error_code", ""),
            "required_contract": fallback_norm_payload.get("required_contract"),
            "auto_required_signal": fallback_norm_payload.get("auto_required_signal"),
            "taxonomy_version": fallback_norm_payload.get("taxonomy_version", ""),
            "fallback_reason_row_count": fallback_norm_payload.get("fallback_reason_row_count"),
            "fallback_reason_rows": fallback_norm_payload.get("fallback_reason_rows", []),
            "unmapped_fallback_reasons": fallback_norm_payload.get("unmapped_fallback_reasons", []),
            "blocker_taxonomy_namespace_preserved": fallback_norm_payload.get("blocker_taxonomy_namespace_preserved"),
            "stale_reasons": fallback_norm_payload.get("stale_reasons", []),
            "evidence_ref": fallback_norm_payload.get("evidence_ref", ""),
        },
        "dedup_monotonicity": {
            "monotonicity_status": dedup_mono_payload.get("monotonicity_status"),
            "error_code": dedup_mono_payload.get("error_code", ""),
            "required_contract": dedup_mono_payload.get("required_contract"),
            "auto_required_signal": dedup_mono_payload.get("auto_required_signal"),
            "run_id": dedup_mono_payload.get("run_id", ""),
            "parallel_claims_requested": dedup_mono_payload.get("parallel_claims_requested"),
            "claim_rows_total": dedup_mono_payload.get("claim_rows_total"),
            "grouped_run_count": dedup_mono_payload.get("grouped_run_count"),
            "candidate_count": dedup_mono_payload.get("candidate_count"),
            "earliest_claim_ts": dedup_mono_payload.get("earliest_claim_ts", ""),
            "stable_tiebreaker": dedup_mono_payload.get("stable_tiebreaker", ""),
            "winner_id": dedup_mono_payload.get("winner_id", ""),
            "winner_reason": dedup_mono_payload.get("winner_reason", ""),
            "tie_candidate_count": dedup_mono_payload.get("tie_candidate_count"),
            "claims_path": dedup_mono_payload.get("claims_path", ""),
            "stale_reasons": dedup_mono_payload.get("stale_reasons", []),
            "evidence_ref": dedup_mono_payload.get("evidence_ref", ""),
        },
        "cross_workflow_schema": {
            "cross_workflow_schema_status": xwf_schema_payload.get("cross_workflow_schema_status"),
            "error_code": xwf_schema_payload.get("error_code", ""),
            "required_contract": xwf_schema_payload.get("required_contract"),
            "auto_required_signal": xwf_schema_payload.get("auto_required_signal"),
            "run_id": xwf_schema_payload.get("run_id", ""),
            "route_action": xwf_schema_payload.get("route_action", ""),
            "quality_meta_state": xwf_schema_payload.get("quality_meta_state", ""),
            "dedup_state": xwf_schema_payload.get("dedup_state", ""),
            "evidence_hash": xwf_schema_payload.get("evidence_hash", ""),
            "schema_version": xwf_schema_payload.get("schema_version", ""),
            "hash_consistency_status": xwf_schema_payload.get("hash_consistency_status", ""),
            "stale_reasons": xwf_schema_payload.get("stale_reasons", []),
            "evidence_ref": xwf_schema_payload.get("evidence_ref", ""),
        },
        "skill_path_integrity": {
            "path_integrity_status": skill_path_payload.get("path_integrity_status"),
            "path_integrity_error_code": skill_path_payload.get("path_integrity_error_code", ""),
            "required_contract": skill_path_payload.get("required_contract"),
            "auto_required_signal": skill_path_payload.get("auto_required_signal"),
            "layout_mode": skill_path_payload.get("layout_mode", ""),
            "active_repo_root": skill_path_payload.get("active_repo_root", ""),
            "active_runtime_root": skill_path_payload.get("active_runtime_root", ""),
            "required_skills": skill_path_payload.get("required_skills", []),
            "missing_skill_paths": skill_path_payload.get("missing_skill_paths", []),
            "out_of_layout_skill_paths": skill_path_payload.get("out_of_layout_skill_paths", []),
            "allowed_skill_roots": skill_path_payload.get("allowed_skill_roots", []),
            "skill_path_rows": skill_path_payload.get("skill_path_rows", []),
            "stale_reasons": skill_path_payload.get("stale_reasons", []),
            "evidence_ref": skill_path_payload.get("evidence_ref", ""),
        },
        "execution_target_tuple_isolation": {
            "execution_target_tuple_isolation_status": exec_target_tuple_payload.get("execution_target_tuple_isolation_status"),
            "error_code": exec_target_tuple_payload.get("error_code", ""),
            "required_contract": exec_target_tuple_payload.get("required_contract"),
            "auto_required_signal": exec_target_tuple_payload.get("auto_required_signal"),
            "execution_target_kind": exec_target_tuple_payload.get("execution_target_kind", ""),
            "execution_target_key": exec_target_tuple_payload.get("execution_target_key", ""),
            "execution_target_ref": exec_target_tuple_payload.get("execution_target_ref", ""),
            "route_conflict_status": exec_target_tuple_payload.get("route_conflict_status", ""),
            "route_conflict_error_code": exec_target_tuple_payload.get("route_conflict_error_code", ""),
            "conflict_key_mode": exec_target_tuple_payload.get("conflict_key_mode", ""),
            "override_non_bypass_status": exec_target_tuple_payload.get("override_non_bypass_status", ""),
            "process_call_support_status": exec_target_tuple_payload.get("process_call_support_status", ""),
            "tuple_fields_present": exec_target_tuple_payload.get("tuple_fields_present", []),
            "tuple_fields_missing": exec_target_tuple_payload.get("tuple_fields_missing", []),
            "stale_reasons": exec_target_tuple_payload.get("stale_reasons", []),
            "evidence_ref": exec_target_tuple_payload.get("evidence_ref", ""),
        },
        "multimodal_plugin_enforcement": {
            "multimodal_plugin_enforcement_status": multimodal_plugin_payload.get("multimodal_plugin_enforcement_status"),
            "multimodal_runtime_evidence_status": multimodal_plugin_payload.get("multimodal_runtime_evidence_status"),
            "multimodal_preflight_status": multimodal_plugin_payload.get("multimodal_preflight_status", ""),
            "error_code": multimodal_plugin_payload.get("error_code", ""),
            "required_contract": multimodal_plugin_payload.get("required_contract"),
            "auto_required_signal": multimodal_plugin_payload.get("auto_required_signal"),
            "plugin_registry_status": multimodal_plugin_payload.get("plugin_registry_status", ""),
            "plugin_naming_status": multimodal_plugin_payload.get("plugin_naming_status", ""),
            "plugin_schema_status": multimodal_plugin_payload.get("plugin_schema_status", ""),
            "plugin_threshold_status": multimodal_plugin_payload.get("plugin_threshold_status", ""),
            "plugin_path_status": multimodal_plugin_payload.get("plugin_path_status", ""),
            "plugin_copy_policy_status": multimodal_plugin_payload.get("plugin_copy_policy_status", ""),
            "provider_config_status": multimodal_plugin_payload.get("provider_config_status", ""),
            "provider_profile_id": multimodal_plugin_payload.get("provider_profile_id", ""),
            "plugin_contract_owner": multimodal_plugin_payload.get("plugin_contract_owner", ""),
            "plugin_resolution_mode": multimodal_plugin_payload.get("plugin_resolution_mode", ""),
            "report_selected_path": multimodal_plugin_payload.get("report_selected_path", ""),
            "runtime_report_path": multimodal_plugin_payload.get("runtime_report_path", ""),
            "runtime_report_run_id": multimodal_plugin_payload.get("runtime_report_run_id", ""),
            "multimodal_calls": multimodal_plugin_payload.get("multimodal_calls"),
            "multimodal_resolved": multimodal_plugin_payload.get("multimodal_resolved"),
            "multimodal_unresolved": multimodal_plugin_payload.get("multimodal_unresolved"),
            "multimodal_errors": multimodal_plugin_payload.get("multimodal_errors"),
            "multimodal_retry_calls": multimodal_plugin_payload.get("multimodal_retry_calls"),
            "runtime_gate_mode": multimodal_plugin_payload.get("runtime_gate_mode", ""),
            "runtime_gate_required_confidence": multimodal_plugin_payload.get("runtime_gate_required_confidence"),
            "multimodal_runtime_evidence_refs": multimodal_plugin_payload.get("multimodal_runtime_evidence_refs", []),
            "forbidden_copy_refs": multimodal_plugin_payload.get("forbidden_copy_refs", []),
            "stale_reasons": multimodal_plugin_payload.get("stale_reasons", []),
            "evidence_ref": multimodal_plugin_payload.get("evidence_ref", ""),
        },
        "reasoning_loop_failclose_enforcement": {
            "reasoning_loop_failclose_status": reasoning_plugin_payload.get("reasoning_loop_failclose_status"),
            "reasoning_runtime_evidence_status": reasoning_plugin_payload.get("reasoning_runtime_evidence_status"),
            "reasoning_attempt_trace_status": reasoning_plugin_payload.get("reasoning_attempt_trace_status"),
            "no_target_done_block_status": reasoning_plugin_payload.get("no_target_done_block_status"),
            "terminal_attempt_index": reasoning_plugin_payload.get("terminal_attempt_index"),
            "terminal_attempt_target_reached": reasoning_plugin_payload.get("terminal_attempt_target_reached"),
            "terminal_attempt_no_target_reached": reasoning_plugin_payload.get("terminal_attempt_no_target_reached"),
            "no_target_completion_mode": reasoning_plugin_payload.get("no_target_completion_mode", ""),
            "done_requires_terminal_target_reached": reasoning_plugin_payload.get("done_requires_terminal_target_reached"),
            "reasoning_next_action_status": reasoning_plugin_payload.get("reasoning_next_action_status"),
            "reasoning_escalation_status": reasoning_plugin_payload.get("reasoning_escalation_status"),
            "escalation_requirement_mode": reasoning_plugin_payload.get("escalation_requirement_mode", ""),
            "escalation_signal_accept_nonempty_ref": reasoning_plugin_payload.get("escalation_signal_accept_nonempty_ref"),
            "escalation_signal_nonempty_fields": reasoning_plugin_payload.get("escalation_signal_nonempty_fields", []),
            "strict_run_id_binding": reasoning_plugin_payload.get("strict_run_id_binding"),
            "runtime_report_selection_mode": reasoning_plugin_payload.get("runtime_report_selection_mode", ""),
            "reasoning_four_track_status": reasoning_plugin_payload.get("reasoning_four_track_status"),
            "external_source_freshness_status": reasoning_plugin_payload.get("external_source_freshness_status"),
            "reasoning_enforcement_level": reasoning_plugin_payload.get("reasoning_enforcement_level", ""),
            "plugin_registry_status": reasoning_plugin_payload.get("plugin_registry_status", ""),
            "runtime_report_path": reasoning_plugin_payload.get("runtime_report_path", ""),
            "runtime_report_run_id": reasoning_plugin_payload.get("runtime_report_run_id", ""),
            "runtime_report_source": reasoning_plugin_payload.get("runtime_report_source", ""),
            "report_selected_path": reasoning_plugin_payload.get("report_selected_path", ""),
            "reasoning_attempt_count": reasoning_plugin_payload.get("reasoning_attempt_count"),
            "reasoning_failed_attempt_count": reasoning_plugin_payload.get("reasoning_failed_attempt_count"),
            "no_target_reached_detected": reasoning_plugin_payload.get("no_target_reached_detected"),
            "reasoning_runtime_evidence_refs": reasoning_plugin_payload.get("reasoning_runtime_evidence_refs", []),
            "error_code": reasoning_plugin_payload.get("error_code", ""),
            "required_contract": reasoning_plugin_payload.get("required_contract"),
            "auto_required_signal": reasoning_plugin_payload.get("auto_required_signal"),
            "stale_reasons": reasoning_plugin_payload.get("stale_reasons", []),
            "evidence_ref": reasoning_plugin_payload.get("evidence_ref", ""),
        },
        "replay_archive_contract": {
            "replay_archive_contract_status": replay_archive_payload.get("replay_archive_contract_status"),
            "error_code": replay_archive_payload.get("error_code", ""),
            "replay_case_total": replay_archive_payload.get("replay_case_total"),
            "replay_case_passed": replay_archive_payload.get("replay_case_passed"),
            "replay_case_failed": replay_archive_payload.get("replay_case_failed"),
            "stale_reasons": replay_archive_payload.get("stale_reasons", []),
            "evidence_ref": replay_archive_payload.get("evidence_ref", ""),
            "out_path": replay_archive_payload.get("out_path", ""),
        },
        "e2e_hermetic_runtime_import": {
            "e2e_hermetic_runtime_status": herm_payload.get("e2e_hermetic_runtime_status"),
            "pythonpath_bootstrap_mode": herm_payload.get("pythonpath_bootstrap_mode", ""),
            "import_preflight_status": herm_payload.get("import_preflight_status", ""),
            "import_preflight_error_code": herm_payload.get("import_preflight_error_code", ""),
            "missing_modules": herm_payload.get("missing_modules", []),
            "stale_reasons": herm_payload.get("stale_reasons", []),
        },
        "semantic_routing_guard": {
            "semantic_routing_status": semantic_payload.get("semantic_routing_status"),
            "error_code": semantic_payload.get("error_code", ""),
            "required_contract": semantic_payload.get("required_contract"),
            "auto_required_signal": semantic_payload.get("auto_required_signal"),
            "feedback_batch_path": semantic_payload.get("feedback_batch_path"),
            "intent_domain": semantic_payload.get("intent_domain"),
            "intent_confidence": semantic_payload.get("intent_confidence"),
            "classifier_reason": semantic_payload.get("classifier_reason", ""),
            "legacy_namespace_refs": semantic_payload.get("legacy_namespace_refs", []),
            "stale_reasons": semantic_payload.get("stale_reasons", []),
        },
        "instance_protocol_split_receipt": {
            "instance_protocol_split_status": split_payload.get("instance_protocol_split_status"),
            "error_code": split_payload.get("error_code", ""),
            "required_contract": split_payload.get("required_contract"),
            "auto_required_signal": split_payload.get("auto_required_signal"),
            "receipt_path": split_payload.get("receipt_path", ""),
            "split_notice": split_payload.get("split_notice", ""),
            "feedback_triggered": split_payload.get("feedback_triggered"),
            "trigger_conditions": split_payload.get("trigger_conditions", {}),
            "instance_actions_ref": split_payload.get("instance_actions_ref", ""),
            "protocol_actions_ref": split_payload.get("protocol_actions_ref", ""),
            "evidence_index_ref": split_payload.get("evidence_index_ref", ""),
            "stale_reasons": split_payload.get("stale_reasons", []),
        },
        "work_layer_gate_set_routing": {
            "work_layer_gate_set_routing_status": lane_payload.get("work_layer_gate_set_routing_status"),
            "error_code": lane_payload.get("error_code", ""),
            "work_layer": lane_payload.get("work_layer", ""),
            "source_layer": lane_payload.get("source_layer", ""),
            "applied_gate_set": lane_payload.get("applied_gate_set", ""),
            "protocol_context_detected": lane_payload.get("protocol_context_detected"),
            "protocol_context_reasons": lane_payload.get("protocol_context_reasons", []),
            "session_lane_lock": lane_payload.get("session_lane_lock", ""),
            "session_lane_lock_source": lane_payload.get("session_lane_lock_source", ""),
            "session_lane_lock_receipt": lane_payload.get("session_lane_lock_receipt", ""),
            "session_lane_lock_exit_receipt": lane_payload.get("session_lane_lock_exit_receipt", ""),
            "lane_resolution_decision": lane_payload.get("lane_resolution_decision", ""),
            "lane_resolution_blocked": lane_payload.get("lane_resolution_blocked"),
            "lane_resolution_error_code": lane_payload.get("lane_resolution_error_code", ""),
            "lane_transition_reason": lane_payload.get("lane_transition_reason", ""),
            "protocol_feedback_triggered": lane_payload.get("protocol_feedback_triggered"),
            "protocol_feedback_paths": lane_payload.get("protocol_feedback_paths", []),
            "pending_receipt_path": lane_payload.get("pending_receipt_path", ""),
            "lane_lock_receipt_path": lane_payload.get("lane_lock_receipt_path", ""),
            "protocol_relevant_diff_detected": lane_payload.get("protocol_relevant_diff_detected"),
            "protocol_relevant_files": lane_payload.get("protocol_relevant_files", []),
            "stale_reasons": lane_payload.get("stale_reasons", []),
        },
        "protocol_feedback_reply_channel": {
            "protocol_feedback_reply_channel_status": reply_channel_payload.get("protocol_feedback_reply_channel_status"),
            "error_code": reply_channel_payload.get("error_code", ""),
            "required_contract": reply_channel_payload.get("required_contract"),
            "auto_required_signal": reply_channel_payload.get("auto_required_signal"),
            "primary_channel_root": reply_channel_payload.get("primary_channel_root", ""),
            "protocol_feedback_activity_detected": reply_channel_payload.get("protocol_feedback_activity_detected"),
            "protocol_feedback_activity_refs": reply_channel_payload.get("protocol_feedback_activity_refs", []),
            "non_standard_primary_refs": reply_channel_payload.get("non_standard_primary_refs", []),
            "mirror_reference_refs": reply_channel_payload.get("mirror_reference_refs", []),
            "split_receipt_requiredized": reply_channel_payload.get("split_receipt_requiredized"),
            "split_receipt_status": reply_channel_payload.get("split_receipt_status", ""),
            "split_receipt_error_code": reply_channel_payload.get("split_receipt_error_code", ""),
            "stale_reasons": reply_channel_payload.get("stale_reasons", []),
        },
        "protocol_feedback_bootstrap_ready": {
            "protocol_feedback_bootstrap_status": bootstrap_payload.get("protocol_feedback_bootstrap_status"),
            "protocol_feedback_bootstrap_mode": bootstrap_payload.get("protocol_feedback_bootstrap_mode", ""),
            "error_code": bootstrap_payload.get("error_code", ""),
            "required_contract": bootstrap_payload.get("required_contract"),
            "auto_required_signal": bootstrap_payload.get("auto_required_signal"),
            "resolved_work_layer": bootstrap_payload.get("resolved_work_layer", ""),
            "protocol_triggered": bootstrap_payload.get("protocol_triggered"),
            "protocol_lane_selected": bootstrap_payload.get("protocol_lane_selected"),
            "bootstrap_created_paths": bootstrap_payload.get("bootstrap_created_paths", []),
            "bootstrap_receipt_path": bootstrap_payload.get("bootstrap_receipt_path", ""),
            "feedback_root": bootstrap_payload.get("feedback_root", ""),
            "missing_required_dirs": bootstrap_payload.get("missing_required_dirs", []),
            "stale_reasons": bootstrap_payload.get("stale_reasons", []),
        },
        "protocol_entry_candidate_bridge": {
            "protocol_entry_candidate_status": candidate_payload.get("protocol_entry_candidate_status"),
            "protocol_entry_decision": candidate_payload.get("protocol_entry_decision", ""),
            "candidate_reason": candidate_payload.get("candidate_reason", ""),
            "candidate_confidence": candidate_payload.get("candidate_confidence"),
            "clarification_required": candidate_payload.get("clarification_required"),
            "clarification_questions": candidate_payload.get("clarification_questions", []),
            "candidate_seed_outbox_ref": candidate_payload.get("candidate_seed_outbox_ref", ""),
            "candidate_seed_index_ref": candidate_payload.get("candidate_seed_index_ref", ""),
            "candidate_receipt_path": candidate_payload.get("candidate_receipt_path", ""),
            "candidate_seed_path": candidate_payload.get("candidate_seed_path", ""),
            "candidate_promotion_status": candidate_payload.get("candidate_promotion_status", ""),
            "error_code": candidate_payload.get("error_code", ""),
            "stale_reasons": candidate_payload.get("stale_reasons", []),
        },
        "protocol_inquiry_followup_chain": {
            "protocol_inquiry_followup_chain_status": inquiry_payload.get("protocol_inquiry_followup_chain_status"),
            "candidate_decision": inquiry_payload.get("candidate_decision", ""),
            "candidate_status": inquiry_payload.get("candidate_status", ""),
            "inquiry_state": inquiry_payload.get("inquiry_state", ""),
            "followup_question_set": inquiry_payload.get("followup_question_set", []),
            "signal_origin": inquiry_payload.get("signal_origin", ""),
            "sanitization_paraphrase_ref": inquiry_payload.get("sanitization_paraphrase_ref", ""),
            "protocol_feedback_seed_ref": inquiry_payload.get("protocol_feedback_seed_ref", ""),
            "protocol_feedback_index_ref": inquiry_payload.get("protocol_feedback_index_ref", ""),
            "followup_round_count": inquiry_payload.get("followup_round_count"),
            "max_followup_rounds": inquiry_payload.get("max_followup_rounds"),
            "latest_evidence_age_hours": inquiry_payload.get("latest_evidence_age_hours"),
            "evidence_ttl_hours": inquiry_payload.get("evidence_ttl_hours"),
            "inquiry_requiredization_triggered": inquiry_payload.get("inquiry_requiredization_triggered"),
            "inquiry_requiredization_receipt_path": inquiry_payload.get("inquiry_requiredization_receipt_path", ""),
            "error_code": inquiry_payload.get("error_code", ""),
            "stale_reasons": inquiry_payload.get("stale_reasons", []),
        },
        "protocol_vendor_semantic_isolation": {
            "protocol_vendor_semantic_isolation_status": semantic_iso_payload.get("protocol_vendor_semantic_isolation_status"),
            "error_code": semantic_iso_payload.get("error_code", ""),
            "required_contract": semantic_iso_payload.get("required_contract"),
            "auto_required_signal": semantic_iso_payload.get("auto_required_signal"),
            "feedback_batch_path": semantic_iso_payload.get("feedback_batch_path"),
            "intent_domain": semantic_iso_payload.get("intent_domain"),
            "intent_confidence": semantic_iso_payload.get("intent_confidence"),
            "intent_domain_before": semantic_iso_payload.get("intent_domain_before"),
            "intent_domain_after": semantic_iso_payload.get("intent_domain_after"),
            "switch_receipt_required": semantic_iso_payload.get("switch_receipt_required"),
            "switch_receipt_present": semantic_iso_payload.get("switch_receipt_present"),
            "switch_receipt_fields": semantic_iso_payload.get("switch_receipt_fields", {}),
            "protocol_vendor_refs": semantic_iso_payload.get("protocol_vendor_refs", []),
            "business_partner_refs": semantic_iso_payload.get("business_partner_refs", []),
            "stale_reasons": semantic_iso_payload.get("stale_reasons", []),
        },
        "external_source_trust_chain": {
            "external_source_trust_chain_status": source_trust_payload.get("external_source_trust_chain_status"),
            "error_code": source_trust_payload.get("error_code", ""),
            "required_contract": source_trust_payload.get("required_contract"),
            "auto_required_signal": source_trust_payload.get("auto_required_signal"),
            "feedback_batch_path": source_trust_payload.get("feedback_batch_path"),
            "allowed_trust_tiers": source_trust_payload.get("allowed_trust_tiers", []),
            "conclusion_required_tiers": source_trust_payload.get("conclusion_required_tiers", []),
            "source_row_count": source_trust_payload.get("source_row_count"),
            "conclusion_source_count": source_trust_payload.get("conclusion_source_count"),
            "candidate_source_count": source_trust_payload.get("candidate_source_count"),
            "unknown_in_conclusion_refs": source_trust_payload.get("unknown_in_conclusion_refs", []),
            "missing_tier_refs": source_trust_payload.get("missing_tier_refs", []),
            "missing_trace_refs": source_trust_payload.get("missing_trace_refs", []),
            "unknown_candidate_without_downgrade": source_trust_payload.get("unknown_candidate_without_downgrade", []),
            "stale_reasons": source_trust_payload.get("stale_reasons", []),
        },
        "protocol_data_sanitization_boundary": {
            "protocol_data_sanitization_boundary_status": sanitization_payload.get(
                "protocol_data_sanitization_boundary_status"
            ),
            "error_code": sanitization_payload.get("error_code", ""),
            "required_contract": sanitization_payload.get("required_contract"),
            "auto_required_signal": sanitization_payload.get("auto_required_signal"),
            "feedback_batch_path": sanitization_payload.get("feedback_batch_path"),
            "forbidden_key_hits": sanitization_payload.get("forbidden_key_hits", []),
            "sensitive_pattern_hits": sanitization_payload.get("sensitive_pattern_hits", []),
            "violation_count": sanitization_payload.get("violation_count"),
            "stale_reasons": sanitization_payload.get("stale_reasons", []),
        },
        "platform_optimization_discovery_trigger": {
            "platform_optimization_discovery_status": opt_trigger_payload.get("platform_optimization_discovery_status"),
            "error_code": opt_trigger_payload.get("error_code", ""),
            "required_contract": opt_trigger_payload.get("required_contract"),
            "auto_required_signal": opt_trigger_payload.get("auto_required_signal"),
            "triggered": opt_trigger_payload.get("triggered", False),
            "trigger_reason": opt_trigger_payload.get("trigger_reason", ""),
            "discovery_scope": opt_trigger_payload.get("discovery_scope", ""),
            "official_doc_retrieval_set": opt_trigger_payload.get("official_doc_retrieval_set", []),
            "cross_validation_summary": opt_trigger_payload.get("cross_validation_summary", {}),
            "upgrade_proposal_ref": opt_trigger_payload.get("upgrade_proposal_ref", ""),
            "feedback_batches": opt_trigger_payload.get("feedback_batches", []),
            "stale_reasons": opt_trigger_payload.get("stale_reasons", []),
        },
        "discovery_requiredization": {
            "discovery_requiredization_status": dreq_payload.get("discovery_requiredization_status"),
            "error_code": dreq_payload.get("error_code", ""),
            "required_contract": dreq_payload.get("required_contract"),
            "required_contract_declared": dreq_payload.get("required_contract_declared"),
            "auto_required_signal": dreq_payload.get("auto_required_signal"),
            "requiredization_triggered": dreq_payload.get("requiredization_triggered"),
            "trigger_classes": dreq_payload.get("trigger_classes", []),
            "window_rounds": dreq_payload.get("window_rounds"),
            "feedback_batches": dreq_payload.get("feedback_batches", []),
            "trigger_condition_flags": dreq_payload.get("trigger_condition_flags", {}),
            "discovery_contract_required_state": dreq_payload.get("discovery_contract_required_state", {}),
            "requiredized_all_discovery_contracts": dreq_payload.get("requiredized_all_discovery_contracts"),
            "requiredization_receipt_path": dreq_payload.get("requiredization_receipt_path", ""),
            "requiredization_receipt_linked": dreq_payload.get("requiredization_receipt_linked"),
            "evidence_index_path": dreq_payload.get("evidence_index_path", ""),
            "ci_required_validators_missing": dreq_payload.get("ci_required_validators_missing", []),
            "discovery_required_total": dreq_payload.get("discovery_required_total"),
            "discovery_required_passed": dreq_payload.get("discovery_required_passed"),
            "discovery_required_coverage_rate": dreq_payload.get("discovery_required_coverage_rate"),
            "stale_reasons": dreq_payload.get("stale_reasons", []),
        },
        "vibe_coding_feeding_pack": {
            "vibe_coding_feeding_pack_status": vibe_pack_payload.get("vibe_coding_feeding_pack_status"),
            "error_code": vibe_pack_payload.get("error_code", ""),
            "required_contract": vibe_pack_payload.get("required_contract"),
            "auto_required_signal": vibe_pack_payload.get("auto_required_signal"),
            "pack_root": vibe_pack_payload.get("pack_root", ""),
            "pack_id": vibe_pack_payload.get("pack_id", ""),
            "pack_files": vibe_pack_payload.get("pack_files", []),
            "feedback_batch_path": vibe_pack_payload.get("feedback_batch_path", ""),
            "feedback_batch_sha256": vibe_pack_payload.get("feedback_batch_sha256", ""),
            "evidence_index_path": vibe_pack_payload.get("evidence_index_path", ""),
            "evidence_index_linked": vibe_pack_payload.get("evidence_index_linked", False),
            "deterministic_manifest_sha256": vibe_pack_payload.get("deterministic_manifest_sha256", ""),
            "sanitization_check_passed": vibe_pack_payload.get("sanitization_check_passed", True),
            "stale_reasons": vibe_pack_payload.get("stale_reasons", []),
        },
        "capability_fit_optimization": {
            "capability_fit_optimization_status": cap_fit_payload.get("capability_fit_optimization_status"),
            "error_code": cap_fit_payload.get("error_code", ""),
            "required_contract": cap_fit_payload.get("required_contract"),
            "fit_matrix_path": cap_fit_payload.get("fit_matrix_path", ""),
            "matrix_candidate_count": cap_fit_payload.get("matrix_candidate_count"),
            "selected_candidate_count": cap_fit_payload.get("selected_candidate_count"),
            "selected_candidate_ids": cap_fit_payload.get("selected_candidate_ids", []),
            "missing_required_fields": cap_fit_payload.get("missing_required_fields", []),
            "selected_missing_fields": cap_fit_payload.get("selected_missing_fields", []),
            "next_review_at": cap_fit_payload.get("next_review_at", ""),
            "review_interval_days": cap_fit_payload.get("review_interval_days"),
            "review_freshness_status": cap_fit_payload.get("review_freshness_status", ""),
            "stale_reasons": cap_fit_payload.get("stale_reasons", []),
        },
        "capability_composition_before_discovery": {
            "compose_before_discovery_status": compose_payload.get("compose_before_discovery_status"),
            "error_code": compose_payload.get("error_code", ""),
            "required_contract": compose_payload.get("required_contract"),
            "fit_matrix_path": compose_payload.get("fit_matrix_path", ""),
            "existing_composition_candidate_count": compose_payload.get("existing_composition_candidate_count"),
            "selected_candidate_type": compose_payload.get("selected_candidate_type", ""),
            "decision_basis": compose_payload.get("decision_basis", ""),
            "stale_reasons": compose_payload.get("stale_reasons", []),
        },
        "capability_fit_review_freshness": {
            "capability_fit_review_freshness_status": fit_fresh_payload.get("capability_fit_review_freshness_status"),
            "error_code": fit_fresh_payload.get("error_code", ""),
            "required_contract": fit_fresh_payload.get("required_contract"),
            "fit_matrix_path": fit_fresh_payload.get("fit_matrix_path", ""),
            "selected_candidate_id": fit_fresh_payload.get("selected_candidate_id", ""),
            "selected_candidate_type": fit_fresh_payload.get("selected_candidate_type", ""),
            "next_review_at": fit_fresh_payload.get("next_review_at", ""),
            "review_interval_days": fit_fresh_payload.get("review_interval_days"),
            "review_freshness_status": fit_fresh_payload.get("review_freshness_status", ""),
            "overdue_by_days": fit_fresh_payload.get("overdue_by_days"),
            "stale_reasons": fit_fresh_payload.get("stale_reasons", []),
        },
        "capability_fit_roundtable_evidence": {
            "capability_fit_roundtable_status": fit_roundtable_payload.get("capability_fit_roundtable_status"),
            "error_code": fit_roundtable_payload.get("error_code", ""),
            "required_contract": fit_roundtable_payload.get("required_contract"),
            "fit_matrix_path": fit_roundtable_payload.get("fit_matrix_path", ""),
            "roundtable_evidence_path": fit_roundtable_payload.get("roundtable_evidence_path", ""),
            "selected_candidate_id": fit_roundtable_payload.get("selected_candidate_id", ""),
            "selected_candidate_type": fit_roundtable_payload.get("selected_candidate_type", ""),
            "roundtable_required": fit_roundtable_payload.get("roundtable_required", False),
            "facts_count": fit_roundtable_payload.get("facts_count"),
            "inferences_count": fit_roundtable_payload.get("inferences_count"),
            "selected_fact_refs": fit_roundtable_payload.get("selected_fact_refs", []),
            "stale_reasons": fit_roundtable_payload.get("stale_reasons", []),
        },
        "capability_fit_review_trigger": {
            "capability_fit_review_trigger_status": fit_trigger_payload.get("capability_fit_review_trigger_status"),
            "error_code": fit_trigger_payload.get("error_code", ""),
            "required_contract": fit_trigger_payload.get("required_contract"),
            "triggered": fit_trigger_payload.get("triggered", False),
            "trigger_reason": fit_trigger_payload.get("trigger_reason", ""),
            "fit_matrix_path": fit_trigger_payload.get("fit_matrix_path", ""),
            "selected_candidate_id": fit_trigger_payload.get("selected_candidate_id", ""),
            "selected_candidate_type": fit_trigger_payload.get("selected_candidate_type", ""),
            "review_freshness_status": fit_trigger_payload.get("review_freshness_status", ""),
            "roundtable_required": fit_trigger_payload.get("roundtable_required", False),
            "roundtable_evidence_path": fit_trigger_payload.get("roundtable_evidence_path", ""),
            "stale_reasons": fit_trigger_payload.get("stale_reasons", []),
        },
        "capability_fit_matrix_builder": {
            "capability_fit_matrix_builder_status": fit_builder_payload.get("capability_fit_matrix_builder_status"),
            "error_code": fit_builder_payload.get("error_code", ""),
            "required_contract": fit_builder_payload.get("required_contract"),
            "matrix_path": fit_builder_payload.get("matrix_path", ""),
            "matrix_candidate_count": fit_builder_payload.get("matrix_candidate_count"),
            "selected_candidate_count": fit_builder_payload.get("selected_candidate_count"),
            "selected_candidate_id": fit_builder_payload.get("selected_candidate_id", ""),
            "selected_candidate_type": fit_builder_payload.get("selected_candidate_type", ""),
            "inventory_snapshot_path": fit_builder_payload.get("inventory_snapshot_path", ""),
            "external_candidate_source_path": fit_builder_payload.get("external_candidate_source_path", ""),
            "stale_reasons": fit_builder_payload.get("stale_reasons", []),
        },
        "vendor_namespace_separation": {
            "vendor_namespace_status": namespace_payload.get("vendor_namespace_status"),
            "error_code": namespace_payload.get("error_code", ""),
            "required_contract": namespace_payload.get("required_contract"),
            "auto_required_signal": namespace_payload.get("auto_required_signal"),
            "feedback_root": namespace_payload.get("feedback_root"),
            "protocol_vendor_file_count": namespace_payload.get("protocol_vendor_file_count"),
            "business_partner_file_count": namespace_payload.get("business_partner_file_count"),
            "legacy_vendor_file_count": namespace_payload.get("legacy_vendor_file_count"),
            "legacy_namespace_refs": namespace_payload.get("legacy_namespace_refs", []),
            "stale_reasons": namespace_payload.get("stale_reasons", []),
        },
        "writeback_continuity": {
            "writeback_continuity_status": writeback_payload.get("writeback_continuity_status"),
            "error_code": writeback_payload.get("error_code", ""),
            "required_contract": writeback_payload.get("required_contract"),
            "report_selected_path": writeback_payload.get("report_selected_path"),
            "writeback_mode": writeback_payload.get("writeback_mode"),
            "writeback_status": writeback_payload.get("writeback_status"),
            "upgrade_required": writeback_payload.get("upgrade_required"),
            "all_ok": writeback_payload.get("all_ok"),
            "degrade_reason": writeback_payload.get("degrade_reason", ""),
            "risk_level": writeback_payload.get("risk_level", ""),
            "next_recovery_action": writeback_payload.get("next_recovery_action", ""),
            "stale_reasons": writeback_payload.get("stale_reasons", []),
        },
        "post_execution_mandatory": {
            "post_execution_mandatory_status": post_exec_payload.get("post_execution_mandatory_status"),
            "error_code": post_exec_payload.get("error_code", ""),
            "required_contract": post_exec_payload.get("required_contract"),
            "report_selected_path": post_exec_payload.get("report_selected_path"),
            "missing_fields": post_exec_payload.get("missing_fields", []),
            "writeback_mode": post_exec_payload.get("writeback_mode", ""),
            "writeback_status": post_exec_payload.get("writeback_status", ""),
            "next_action": post_exec_payload.get("next_action", ""),
            "next_recovery_action": post_exec_payload.get("next_recovery_action", ""),
            "stale_reasons": post_exec_payload.get("stale_reasons", []),
        },
        "protocol_feedback_sidecar": {
            "sidecar_contract_status": sidecar_payload.get("sidecar_contract_status"),
            "sidecar_error_code": sidecar_payload.get("sidecar_error_code", ""),
            "required_contract": sidecar_payload.get("required_contract"),
            "auto_required_signal": sidecar_payload.get("auto_required_signal"),
            "requiredization_scope_decision": sidecar_payload.get("requiredization_scope_decision", ""),
            "requiredization_scope_reason": sidecar_payload.get("requiredization_scope_reason", ""),
            "requiredization_current_round_linked": sidecar_payload.get("requiredization_current_round_linked"),
            "current_round_anchor_utc": sidecar_payload.get("current_round_anchor_utc", ""),
            "activity_correlation_status": sidecar_payload.get("activity_correlation_status", ""),
            "activity_correlation_key": sidecar_payload.get("activity_correlation_key", ""),
            "activity_unscoped_count": sidecar_payload.get("activity_unscoped_count"),
            "activity_ignored_missing_correlation_key_refs": sidecar_payload.get(
                "activity_ignored_missing_correlation_key_refs", []
            ),
            "activity_ignored_missing_anchor_refs": sidecar_payload.get("activity_ignored_missing_anchor_refs", []),
            "activity_ignored_pre_round_refs": sidecar_payload.get("activity_ignored_pre_round_refs", []),
            "enforce_blocking": sidecar_payload.get("enforce_blocking"),
            "escalation_required": sidecar_payload.get("escalation_required"),
            "escalation_decision": sidecar_payload.get("escalation_decision"),
            "observability_escalation_required": sidecar_payload.get("observability_escalation_required"),
            "observability_alert_level": sidecar_payload.get("observability_alert_level", ""),
            "observability_escalation_reason": sidecar_payload.get("observability_escalation_reason", ""),
            "blocking_error_codes": sidecar_payload.get("blocking_error_codes", []),
            "p0_violations": sidecar_payload.get("p0_violations", []),
            "track_a": sidecar_payload.get("track_a", {}),
            "track_b": sidecar_payload.get("track_b", {}),
            "stale_reasons": sidecar_payload.get("stale_reasons", []),
        },
        "instance_base_repo_write_boundary": {
            "base_repo_write_boundary_status": base_boundary_payload.get("base_repo_write_boundary_status"),
            "error_code": base_boundary_payload.get("error_code", ""),
            "required_contract": base_boundary_payload.get("required_contract"),
            "auto_required_signal": base_boundary_payload.get("auto_required_signal"),
            "report_selected_path": base_boundary_payload.get("report_selected_path", ""),
            "source_mode": base_boundary_payload.get("source_mode", ""),
            "allowlist_prefixes": base_boundary_payload.get("allowlist_prefixes", []),
            "denylist_prefixes": base_boundary_payload.get("denylist_prefixes", []),
            "repo_relative_candidates": base_boundary_payload.get("repo_relative_candidates", []),
            "allowed_paths": base_boundary_payload.get("allowed_paths", []),
            "blocked_paths": base_boundary_payload.get("blocked_paths", []),
            "explicit_deny_hits": base_boundary_payload.get("explicit_deny_hits", []),
            "override_receipt_path": base_boundary_payload.get("override_receipt_path", ""),
            "override_applied": base_boundary_payload.get("override_applied"),
            "stale_reasons": base_boundary_payload.get("stale_reasons", []),
        },
        "protocol_feedback_ssot_archival": {
            "feedback_ssot_archival_status": archival_payload.get("feedback_ssot_archival_status"),
            "error_code": archival_payload.get("error_code", ""),
            "required_contract": archival_payload.get("required_contract"),
            "auto_required_signal": archival_payload.get("auto_required_signal"),
            "feedback_root": archival_payload.get("feedback_root", ""),
            "outbox_dir": archival_payload.get("outbox_dir", ""),
            "evidence_index_path": archival_payload.get("evidence_index_path", ""),
            "batch_file_count": archival_payload.get("batch_file_count"),
            "batch_files": archival_payload.get("batch_files", []),
            "index_linked_batches": archival_payload.get("index_linked_batches", []),
            "index_unlinked_batches": archival_payload.get("index_unlinked_batches", []),
            "mirror_candidate_refs": archival_payload.get("mirror_candidate_refs", []),
            "stale_reasons": archival_payload.get("stale_reasons", []),
        },
        "downsink_path_immutability": {
            "protocol_downsink_path_immutability_status": downsink_immutability_payload.get(
                "protocol_downsink_path_immutability_status"
            ),
            "error_code": downsink_immutability_payload.get("error_code", ""),
            "required_contract": downsink_immutability_payload.get("required_contract"),
            "auto_required_signal": downsink_immutability_payload.get("auto_required_signal"),
            "contract_key": downsink_immutability_payload.get("contract_key", ""),
            "runtime_mirror_contract_path": downsink_immutability_payload.get("runtime_mirror_contract_path", ""),
            "required_domains": downsink_immutability_payload.get("required_domains", []),
            "stale_reasons": downsink_immutability_payload.get("stale_reasons", []),
        },
        "downsink_path_write_guard": {
            "protocol_downsink_path_write_guard_status": downsink_write_guard_payload.get(
                "protocol_downsink_path_write_guard_status"
            ),
            "error_code": downsink_write_guard_payload.get("error_code", ""),
            "required_contract": downsink_write_guard_payload.get("required_contract"),
            "auto_required_signal": downsink_write_guard_payload.get("auto_required_signal"),
            "checked_candidate_count": downsink_write_guard_payload.get("checked_candidate_count"),
            "checked_candidates": downsink_write_guard_payload.get("checked_candidates", []),
            "registry_rule_count": downsink_write_guard_payload.get("registry_rule_count"),
            "stale_reasons": downsink_write_guard_payload.get("stale_reasons", []),
        },
        "downsink_path_literal_lock": {
            "protocol_downsink_path_literal_lock_status": downsink_literal_lock_payload.get(
                "protocol_downsink_path_literal_lock_status"
            ),
            "error_code": downsink_literal_lock_payload.get("error_code", ""),
            "required_contract": downsink_literal_lock_payload.get("required_contract"),
            "auto_required_signal": downsink_literal_lock_payload.get("auto_required_signal"),
            "scan_file_count": downsink_literal_lock_payload.get("scan_file_count"),
            "scan_files": downsink_literal_lock_payload.get("scan_files", []),
            "scan_globs": downsink_literal_lock_payload.get("scan_globs", []),
            "registry_rule_count": downsink_literal_lock_payload.get("registry_rule_count"),
            "stale_reasons": downsink_literal_lock_payload.get("stale_reasons", []),
        },
        "identity_home_catalog_alignment": {
            "path_governance_status": home_align_payload.get("path_governance_status"),
            "path_error_codes": home_align_payload.get("path_error_codes", []),
            "identity_home": home_align_payload.get("identity_home"),
            "identity_home_expected": home_align_payload.get("identity_home_expected"),
            "identity_home_source": home_align_payload.get("identity_home_source"),
            "stale_reasons": home_align_payload.get("stale_reasons", []),
        },
        "fixture_runtime_boundary": {
            "path_governance_status": fixture_boundary_payload.get("path_governance_status"),
            "path_error_codes": fixture_boundary_payload.get("path_error_codes", []),
            "operation": fixture_boundary_payload.get("operation"),
            "allow_fixture_runtime": fixture_boundary_payload.get("allow_fixture_runtime"),
            "fixture_audit_receipt": fixture_boundary_payload.get("fixture_audit_receipt"),
            "stale_reasons": fixture_boundary_payload.get("stale_reasons", []),
        },
        "actor_session_binding": {
            "actor_binding_status": actor_binding_payload.get("actor_binding_status"),
            "error_code": actor_binding_payload.get("error_code", ""),
            "actor_id": actor_binding_payload.get("actor_id", ""),
            "actor_session_path": actor_binding_payload.get("actor_session_path", ""),
            "bound_identity_id": actor_binding_payload.get("bound_identity_id", ""),
            "catalog_identity_status": actor_binding_payload.get("catalog_identity_status", ""),
            "stale_reasons": actor_binding_payload.get("stale_reasons", []),
        },
        "actor_session_multibinding_concurrency": {
            "actor_session_multibinding_status": actor_mb_payload.get("actor_session_multibinding_status"),
            "error_code": actor_mb_payload.get("error_code", ""),
            "binding_key_mode": actor_mb_payload.get("binding_key_mode", ""),
            "session_entry_count": actor_mb_payload.get("session_entry_count"),
            "cas_checked": actor_mb_payload.get("cas_checked"),
            "cas_conflict_detected": actor_mb_payload.get("cas_conflict_detected"),
            "non_activation_mutation_detected": actor_mb_payload.get("non_activation_mutation_detected"),
            "rebind_receipt_status": actor_mb_payload.get("rebind_receipt_status", ""),
            "dropped_peer_session_count": actor_mb_payload.get("dropped_peer_session_count"),
            "stale_reasons": actor_mb_payload.get("stale_reasons", []),
        },
        "no_implicit_switch": {
            "implicit_switch_status": no_implicit_payload.get("implicit_switch_status"),
            "error_code": no_implicit_payload.get("error_code", ""),
            "switch_report_path": no_implicit_payload.get("switch_report_path", ""),
            "switch_id": no_implicit_payload.get("switch_id", ""),
            "actor_id": no_implicit_payload.get("actor_id", ""),
            "run_id": no_implicit_payload.get("run_id", ""),
            "cross_actor_demotion_detected": no_implicit_payload.get("cross_actor_demotion_detected"),
            "stale_reasons": no_implicit_payload.get("stale_reasons", []),
        },
        "cross_actor_isolation": {
            "cross_actor_isolation_status": cross_actor_payload.get("cross_actor_isolation_status"),
            "error_code": cross_actor_payload.get("error_code", ""),
            "actor_binding_count": cross_actor_payload.get("actor_binding_count"),
            "active_identities": cross_actor_payload.get("active_identities", []),
            "stale_reasons": cross_actor_payload.get("stale_reasons", []),
        },
        "session_refresh_status": {
            "session_refresh_status": refresh_payload.get("session_refresh_status"),
            "error_code": refresh_payload.get("error_code", ""),
            "actor_id": refresh_payload.get("actor_id", ""),
            "lease_status": refresh_payload.get("lease_status", ""),
            "pointer_consistency": refresh_payload.get("pointer_consistency", ""),
            "risk_flags": refresh_payload.get("risk_flags", []),
            "next_action": refresh_payload.get("next_action", ""),
            "baseline_status": refresh_payload.get("baseline_status", ""),
            "baseline_error_code": refresh_payload.get("baseline_error_code", ""),
            "report_protocol_commit_sha": refresh_payload.get("report_protocol_commit_sha", ""),
            "protocol_head_sha_at_run_start": refresh_payload.get("protocol_head_sha_at_run_start", ""),
            "baseline_reference_mode": refresh_payload.get("baseline_reference_mode", ""),
            "current_protocol_head_sha": refresh_payload.get("current_protocol_head_sha", ""),
            "head_drift_detected": refresh_payload.get("head_drift_detected", False),
            "lag_commits": refresh_payload.get("lag_commits"),
            "report_selected_path": refresh_payload.get("report_selected_path", ""),
            "stale_reasons": refresh_payload.get("stale_reasons", []),
        },
        "response_identity_stamp": {
            "render_status": "PASS" if rc_stamp_render == 0 else "FAIL",
            "stamp_status": stamp_payload.get("stamp_status"),
            "stamp_error_code": stamp_payload.get("error_code"),
            "blocker_receipt_status": receipt_payload.get("receipt_status"),
            "blocker_receipt_path": stamp_payload.get("blocker_receipt_path", ""),
            "reply_sample_count": stamp_payload.get("reply_sample_count", 0),
            "reply_stamp_missing_count": stamp_payload.get("reply_stamp_missing_count", 0),
            "reply_stamp_missing_refs": stamp_payload.get("reply_stamp_missing_refs", []),
            "reply_first_line_status": reply_first_line_payload.get("reply_first_line_status"),
            "reply_first_line_error_code": reply_first_line_payload.get("error_code", ""),
            "reply_first_line_missing_count": reply_first_line_payload.get("reply_first_line_missing_count", 0),
            "reply_first_line_missing_refs": reply_first_line_payload.get("reply_first_line_missing_refs", []),
            "reply_first_line_blocker_receipt_path": reply_first_line_payload.get("blocker_receipt_path", ""),
            "layer_intent_resolution_status": layer_intent_payload.get("layer_intent_resolution_status", ""),
            "layer_intent_error_code": layer_intent_payload.get("error_code", ""),
            "resolved_work_layer": layer_intent_payload.get("resolved_work_layer", ""),
            "resolved_source_layer": layer_intent_payload.get("resolved_source_layer", ""),
            "layer_intent_confidence": layer_intent_payload.get("intent_confidence"),
            "layer_intent_source": layer_intent_payload.get("intent_source", ""),
            "layer_intent_fallback_reason": layer_intent_payload.get("fallback_reason", ""),
            "send_time_gate_status": send_time_gate_payload.get("send_time_gate_status"),
            "send_time_gate_error_code": send_time_gate_payload.get("error_code", ""),
            "governed_outlet_enforced": send_time_gate_payload.get("governed_outlet_enforced", False),
            "outlet_channel_id": send_time_gate_payload.get("outlet_channel_id", ""),
            "final_emit_channel_id": send_time_gate_payload.get("final_emit_channel_id", ""),
            "final_emit_policy_mode": send_time_gate_payload.get("final_emit_policy_mode", ""),
            "final_emit_schema_id": send_time_gate_payload.get("final_emit_schema_id", ""),
            "final_emit_schema_status": send_time_gate_payload.get("final_emit_schema_status", ""),
            "final_emit_contract_status": send_time_gate_payload.get("final_emit_contract_status", ""),
            "outlet_preflight_receipt": send_time_gate_payload.get("outlet_preflight_receipt", ""),
            "outlet_bypass_detected": send_time_gate_payload.get("outlet_bypass_detected", False),
            "send_time_reply_evidence_mode": send_time_gate_payload.get("reply_evidence_mode", ""),
            "send_time_reply_evidence_ref": send_time_gate_payload.get("reply_evidence_ref", ""),
            "send_time_reply_sample_count": send_time_gate_payload.get("reply_sample_count", 0),
            "send_time_reply_missing_count": send_time_gate_payload.get("reply_first_line_missing_count", 0),
            "send_time_reply_missing_refs": send_time_gate_payload.get("reply_first_line_missing_refs", []),
            "send_time_blocker_receipt_path": send_time_gate_payload.get("blocker_receipt_path", ""),
            "reply_coherence_status": reply_coherence_payload.get("coherence_status"),
            "reply_coherence_error_code": reply_coherence_payload.get("error_code", ""),
            "reply_coherence_decision": reply_coherence_payload.get("coherence_decision", ""),
            "reply_coherence_mismatch_fields": reply_coherence_payload.get("mismatch_fields", []),
            "reply_coherence_command_catalog_ref": reply_coherence_payload.get("command_catalog_ref", ""),
            "reply_coherence_resolved_catalog_ref": reply_coherence_payload.get("resolved_catalog_ref", ""),
            "reply_coherence_catalog_ref": reply_coherence_payload.get("reply_catalog_ref", ""),
            "reply_coherence_blocker_receipt_path": reply_coherence_payload.get("blocker_receipt_path", ""),
            "external_stamp": stamp_render_payload.get("external_stamp"),
            "stale_reasons": stamp_payload.get("stale_reasons", []),
            "first_line_stale_reasons": reply_first_line_payload.get("stale_reasons", []),
            "layer_intent_stale_reasons": layer_intent_payload.get("stale_reasons", []),
            "send_time_stale_reasons": send_time_gate_payload.get("stale_reasons", []),
            "coherence_stale_reasons": reply_coherence_payload.get("stale_reasons", []),
        },
        "execution_report_freshness": {
            "freshness_status": freshness_payload.get("freshness_status"),
            "freshness_error_code": freshness_payload.get("freshness_error_code"),
            "report_selected_path": freshness_payload.get("report_selected_path"),
            "stale_reasons": freshness_payload.get("stale_reasons", []),
            "checks": freshness_payload.get("checks", {}),
        },
        "protocol_baseline_freshness": {
            "baseline_status": baseline_payload.get("baseline_status"),
            "baseline_error_code": baseline_payload.get("baseline_error_code"),
            "report_selected_path": baseline_payload.get("report_selected_path"),
            "report_protocol_root": baseline_payload.get("report_protocol_root"),
            "report_protocol_commit_sha": baseline_payload.get("report_protocol_commit_sha"),
            "protocol_head_sha_at_run_start": baseline_payload.get("protocol_head_sha_at_run_start"),
            "baseline_reference_mode": baseline_payload.get("baseline_reference_mode"),
            "current_protocol_head_sha": baseline_payload.get("current_protocol_head_sha"),
            "head_drift_detected": baseline_payload.get("head_drift_detected", False),
            "lag_commits": baseline_payload.get("lag_commits"),
            "stale_reasons": baseline_payload.get("stale_reasons", []),
        },
        "protocol_version_alignment": {
            "protocol_version_alignment_status": align_payload.get("protocol_version_alignment_status"),
            "error_code": align_payload.get("error_code", ""),
            "operation": align_payload.get("operation"),
            "alignment_policy": align_payload.get("alignment_policy"),
            "report_selected_path": align_payload.get("report_selected_path"),
            "tuple_checks": align_payload.get("tuple_checks", {}),
            "stale_reasons": align_payload.get("stale_reasons", []),
        },
        "validators": validators,
    }

    validators_all_ok = all(v.get("ok", False) for v in validators.values())
    capability_strict_ok = cap_status in {"ACTIVATED", "NOT_REQUIRED"}
    if all_ok and wb == "WRITTEN" and ps == "WRITEBACK_WRITTEN" and mandatory and validators_all_ok and capability_strict_ok:
        return "CLOSED", detail
    if hard_boundary:
        return "BLOCKED", detail
    if mandatory and next_action and validators_all_ok:
        return "IN_PROGRESS", detail
    return "BLOCKED", detail


def _git_current_branch() -> str:
    rc, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0:
        return out.strip()
    return ""


def _git_head_sha() -> str:
    rc, out, _ = _run(["git", "rev-parse", "HEAD"])
    if rc == 0:
        return out.strip()
    return ""


def main() -> int:
    global SESSION_ID_FALLBACK
    ap = argparse.ArgumentParser(description="Emit unified three-plane status for identity governance.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default=os.environ.get("IDENTITY_CATALOG", ""))
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="", help="optional explicit scope arbitration: REPO/USER/ADMIN/SYSTEM")
    ap.add_argument("--execution-report", default="")
    ap.add_argument("--with-docs-contract", action="store_true", help="run repo-plane docs contract checker")
    ap.add_argument("--target-branch", default="")
    ap.add_argument("--release-head-sha", default="")
    ap.add_argument("--required-gates-run-id", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--workflow-file-sha", default="")
    ap.add_argument("--run-head-sha", default="")
    ap.add_argument("--run-workflow-file-sha", default="")
    ap.add_argument("--checks-json", default="")
    ap.add_argument("--layer-intent-text", default="", help="optional natural-language layer intent passed to stamp render/reply gates")
    ap.add_argument("--expected-work-layer", default="", help="optional expected work_layer override for strict reply gates")
    ap.add_argument("--expected-source-layer", default="", help="optional expected source_layer override for strict reply gates")
    ap.add_argument(
        "--actor-id",
        default="",
        help=(
            "explicit actor id for strict governed-outlet/headstamp recurrence closure checks. "
            "required for strict three-plane execution (no implicit fallback)."
        ),
    )
    ap.add_argument(
        "--session-id",
        default="",
        help="explicit actor session id for strict three-plane execution (e.g., run:<run_id>)",
    )
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if not args.catalog:
        print("[FAIL] --catalog is required (or export IDENTITY_CATALOG first).")
        return 2
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_arg = Path(args.repo_catalog).expanduser()
    if repo_catalog_arg.is_absolute():
        repo_catalog_path = repo_catalog_arg.resolve()
    else:
        repo_catalog_path = (PROTOCOL_ROOT / repo_catalog_arg).resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(
            "[FAIL] IP-CWD-004 repo catalog not found under protocol-root deterministic resolution: "
            f"{repo_catalog_path} (hint: pass explicit --repo-catalog <absolute-path>)"
        )
        return 2
    args.repo_catalog = str(repo_catalog_path)
    actor_id_input = str(args.actor_id or "").strip()
    if not actor_id_input:
        print(
            "[FAIL] IP-ACTOR-ENTRY-001 explicit --actor-id is required for strict three-plane execution "
            f"(identity_id={args.identity_id})"
        )
        return 1
    args.actor_id = actor_id_input
    session_id_input = str(args.session_id or "").strip()
    if not session_id_input:
        print(
            "[FAIL] IP-ASB-SESSION-ENTRY-001 explicit --session-id is required for strict three-plane execution "
            f"(identity_id={args.identity_id}, actor_id={actor_id_input})"
        )
        return 1
    args.session_id = session_id_input
    SESSION_ID_FALLBACK = session_id_input

    mode_guard_cmd = [
        "python3",
        "scripts/validate_identity_runtime_mode_guard.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--expect-mode",
        "auto",
        "--operation",
        "three-plane",
    ]
    if str(args.scope or "").strip():
        mode_guard_cmd.extend(["--scope", str(args.scope).strip()])
    rc_mode_guard, out_mode_guard, err_mode_guard = _run(mode_guard_cmd)
    if rc_mode_guard != 0:
        print("[FAIL] runtime mode guard preflight blocked three-plane execution")
        if out_mode_guard:
            print(out_mode_guard)
        if err_mode_guard:
            print(err_mode_guard)
        return rc_mode_guard or 2

    try:
        resolved = resolve_identity(
            args.identity_id,
            repo_catalog_path,
            catalog_path,
            preferred_scope=str(args.scope or ""),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity context: {exc}")
        return 2

    if not args.target_branch:
        args.target_branch = _git_current_branch()
    if not args.release_head_sha:
        args.release_head_sha = _git_head_sha()

    preferred_pack = str(resolved.get("resolved_pack_path") or resolved.get("pack_path") or "")
    report_path = Path(args.execution_report).expanduser().resolve() if args.execution_report else _latest_report(
        args.identity_id,
        os.environ.get("IDENTITY_HOME", ""),
        preferred_pack,
    )
    instance_status, instance_detail = _instance_plane_status(args, report_path, resolved)
    repo_status, repo_detail = _repo_plane_status(args, resolved)
    release_status, release_detail = _release_plane_status(args)

    payload = {
        "target_branch": args.target_branch,
        "release_head_sha": args.release_head_sha,
        "required_gates_run_id": args.required_gates_run_id,
        "run_url": args.run_url,
        "workflow_file_sha": args.workflow_file_sha,
        "required_checks_set": release_detail.get("required_checks_set", []),
        "instance_plane_status": instance_status,
        "repo_plane_status": repo_status,
        "release_plane_status": release_status,
        "identity_context": {
            "identity_id": args.identity_id,
            "source_layer": resolved.get("source_layer"),
            "catalog_path": resolved.get("catalog_path"),
            "pack_path": resolved.get("pack_path"),
            "resolved_scope": resolved.get("resolved_scope"),
            "resolved_pack_path": resolved.get("resolved_pack_path"),
            "conflict_detected": resolved.get("conflict_detected"),
        },
        "instance_plane_detail": instance_detail,
        "repo_plane_detail": repo_detail,
        "release_plane_detail": release_detail,
    }
    m2m_projection = _classify_m2m_projection(
        validators=instance_detail.get("validators", {}) if isinstance(instance_detail, dict) else {},
        instance_status=instance_status,
        repo_status=repo_status,
        release_status=release_status,
    )
    tuple_context_projection = _classify_tuple_context_projection(
        validators=instance_detail.get("validators", {}) if isinstance(instance_detail, dict) else {},
    )
    payload["m2m_projection"] = m2m_projection
    payload["tuple_context_projection"] = tuple_context_projection
    if isinstance(instance_detail, dict):
        instance_detail["m2m_projection"] = m2m_projection
        instance_detail["tuple_context_projection"] = tuple_context_projection
    payload["governance_closure_axes"] = _build_governance_closure_axes(
        instance_status=instance_status,
        repo_status=repo_status,
        release_status=release_status,
        m2m_projection=m2m_projection,
        tuple_context_projection=tuple_context_projection,
    )

    overall = "Conditional Go"
    if instance_status == "CLOSED" and repo_status == "CLOSED" and release_status == "CLOSED":
        overall = "Full Go"
    payload["overall_release_decision"] = overall
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] wrote: {out}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"overall_release_decision={overall}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
