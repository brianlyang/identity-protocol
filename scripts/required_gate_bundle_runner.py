#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import hashlib
import hmac
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from protocol_infra_contract import (
    CTX_TOOL_TIMEOUT_ERROR_CODE,
    CTX_TOOL_TIMEOUT_MARKER,
    CTX_TOOL_TIMEOUT_REASON_PREFIX,
    GATEWAY_WRAPPER_SUBPROCESS_TIMEOUT_SECONDS_DEFAULT,
    PRIVILEGE_ESCALATION_ERROR_CODE,
    PRIVILEGE_ESCALATION_REASON_PREFIX,
    PRIVILEGE_ESCALATION_REMEDIATION_HINT,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS,
)
from tool_vendor_governance_common import derive_active_repo_root, load_json, resolve_pack_and_task

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    psutil = None

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_FAIL_OPTIONAL = "FAIL_OPTIONAL"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"

BUNDLE_CONTRACT_ID = "hotfix_p0_007_ucg_control_plane_freeze_contract_v1"
BUNDLE_KEY = "required_gate_bundle_runner"
DEFAULT_HOST_WRAPPER_SURFACE_LABEL = "host_ingress_wrapper"
DEFAULT_REQUIRED_WRAPPER_DISPATCH_TOKEN = "instance_wrapper_ingress_v1"
HOST_GATEWAY_CONTRACT_KEYS: tuple[str, ...] = (
    "protocol_host_unique_channel_contract_v1",
    "protocol_gateway_wrapper_contract_v1",
    "protocol_gateway_contract_v1",
)
DEFAULT_GATE_PROFILE_FILE = "identity/protocol/mappings/layer-targeted-gate-profile.current.yaml"
DEFAULT_GATE_PROFILE_NAME = "strict_full"
DEFAULT_PLUGIN_GOVERNANCE_FILE = "identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml"
STRICT_NO_TRIM_OPERATIONS_DEFAULT: tuple[str, ...] = (
    "activate",
    "update",
    "mutation",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "three-plane",
)
LIGHT_NO_TRIM_OPERATIONS_DEFAULT: tuple[str, ...] = (
    "inspection",
    "scan",
)

# Order is deterministic for replay and log comparison.
BUNDLE_REQUIREMENT_ORDER: tuple[str, ...] = (
    "asb16-rq-001",
    "asb16-rq-002",
    "asb16-rq-003",
    "asb16-rq-004",
    "asb16-rq-005",
    "asb16-rq-006",
    "asb16-rq-007",
    "asb16-rq-008",
    "asb16-rq-009",
    "asb16-rq-010",
    "asb16-rq-011",
    "asb16-rq-012",
    "asb16-rq-013",
    "asb16-rq-014",
    "asb16-rq-015",
    "asb16-rq-016",
    "asb16-rq-023",
    "asb16-rq-024",
    "asb16-rq-025",
    "asb16-rq-026",
    "asb16-rq-027",
    "asb16-rq-028",
    "asb16-rq-029",
    "asb16-rq-031",
    "asb16-rq-032",
    "asb16-rq-017",
    "asb16-rq-030",
    "asb16-rq-021",
    "asb16-rq-022",
    "asb16-rq-018",
    "asb16-rq-019",
    "asb16-rq-020",
    "asb16-rq-033",
    "asb16-rq-034",
    "asb16-rq-035",
    "asb16-rq-036",
    "asb16-rq-037",
    "asb16-rq-038",
    "asb16-rq-039",
    "asb16-rq-040",
    "asb16-rq-041",
)

TARGET_NAME_BY_REQUIREMENT: dict[str, str] = {
    "asb16-rq-001": "unlock_formula",
    "asb16-rq-002": "capability_boundary_classification",
    "asb16-rq-003": "promotion_pipeline",
    "asb16-rq-004": "outlet_matrix",
    "asb16-rq-005": "sidecar_cwd_invariance",
    "asb16-rq-006": "release_plane_cloud_evidence",
    "asb16-rq-007": "cross_cwd_absolute_input",
    "asb16-rq-008": "docs_bridge_consistency",
    "asb16-rq-009": "run_id_report_selection",
    "asb16-rq-010": "phase_bootstrap_before_strict",
    "asb16-rq-011": "tmp_collision_safety",
    "asb16-rq-012": "handoff_collab_freshness_rotation",
    "asb16-rq-013": "protocol_feedback_atomic_emit",
    "asb16-rq-014": "prompt_bootstrap_capability",
    "asb16-rq-015": "prompt_capability_matrix",
    "asb16-rq-016": "refresh_strict_business_interference",
    "asb16-rq-023": "discovery_requiredization_activation",
    "asb16-rq-024": "discovery_requiredization_coverage",
    "asb16-rq-025": "kernel_canonical_source",
    "asb16-rq-026": "kernel_contract_mapping_projection",
    "asb16-rq-027": "prompt_derivation_conformance",
    "asb16-rq-028": "instance_write_boundary_lock",
    "asb16-rq-029": "semantic_convergence",
    "asb16-rq-031": "prompt_import_executable_coupling",
    "asb16-rq-032": "headstamp_pre_send_hard_gate",
    "asb16-rq-017": "cross_verification_tracks",
    "asb16-rq-030": "intake_evidence_quorum",
    "asb16-rq-021": "route_version_pinning",
    "asb16-rq-022": "fallback_taxonomy_normalization",
    "asb16-rq-018": "dedup_monotonicity",
    "asb16-rq-019": "cross_workflow_schema",
    "asb16-rq-020": "skill_path_integrity",
    "asb16-rq-033": "execution_target_tuple_isolation",
    "asb16-rq-034": "multimodal_plugin_enforcement",
    "asb16-rq-035": "reasoning_loop_failclose_enforcement",
    "asb16-rq-036": "downsink_path_immutability",
    "asb16-rq-037": "downsink_path_write_guard",
    "asb16-rq-038": "downsink_path_literal_lock",
    "asb16-rq-039": "skill_installation_supply_chain",
    "asb16-rq-040": "skill_frontmatter",
    "asb16-rq-041": "skill_sync_drift_guard",
}
REQUIREMENT_BY_TARGET: dict[str, str] = {v: k for k, v in TARGET_NAME_BY_REQUIREMENT.items()}

STATUS_FIELD_BY_TARGET: dict[str, str] = {
    "unlock_formula": "unlock_formula_status",
    "capability_boundary_classification": "capability_boundary_status",
    "promotion_pipeline": "promotion_pipeline_status",
    "outlet_matrix": "outlet_matrix_status",
    "sidecar_cwd_invariance": "sidecar_cwd_parity_status",
    "release_plane_cloud_evidence": "release_plane_cloud_evidence_status",
    "cross_cwd_absolute_input": "cross_cwd_absolute_input_status",
    "docs_bridge_consistency": "bridge_consistency_status",
    "run_id_report_selection": "run_id_report_selection_status",
    "phase_bootstrap_before_strict": "phase_bootstrap_before_strict_status",
    "tmp_collision_safety": "tmp_collision_safety_status",
    "handoff_collab_freshness_rotation": "handoff_collab_freshness_rotation_status",
    "protocol_feedback_atomic_emit": "protocol_feedback_atomic_emit_status",
    "prompt_bootstrap_capability": "prompt_bootstrap_contract_status",
    "prompt_capability_matrix": "prompt_capability_matrix_status",
    "refresh_strict_business_interference": "refresh_strict_business_interference_status",
    "discovery_requiredization_activation": "discovery_requiredization_status",
    "discovery_requiredization_coverage": "discovery_requiredization_status",
    "kernel_canonical_source": "kernel_ssot_source_status",
    "kernel_contract_mapping_projection": "contract_mapping_coverage_status",
    "prompt_derivation_conformance": "prompt_derivation_conformance_status",
    "instance_write_boundary_lock": "base_repo_write_boundary_status",
    "semantic_convergence": "semantic_convergence_status",
    "prompt_import_executable_coupling": "prompt_kernel_executable_coupling_status",
    "headstamp_pre_send_hard_gate": "send_time_gate_status",
    "cross_verification_tracks": "cross_verification_tracks_status",
    "intake_evidence_quorum": "intake_evidence_quorum_status",
    "route_version_pinning": "pin_status",
    "fallback_taxonomy_normalization": "fallback_taxonomy_normalization_status",
    "dedup_monotonicity": "monotonicity_status",
    "cross_workflow_schema": "cross_workflow_schema_status",
    "skill_path_integrity": "path_integrity_status",
    "execution_target_tuple_isolation": "execution_target_tuple_isolation_status",
    "multimodal_plugin_enforcement": "multimodal_plugin_enforcement_status",
    "reasoning_loop_failclose_enforcement": "reasoning_loop_failclose_status",
    "downsink_path_immutability": "protocol_downsink_path_immutability_status",
    "downsink_path_write_guard": "protocol_downsink_path_write_guard_status",
    "downsink_path_literal_lock": "protocol_downsink_path_literal_lock_status",
    "skill_installation_supply_chain": "skill_installation_supply_chain_status",
    "skill_frontmatter": "skill_frontmatter_status",
    "skill_sync_drift_guard": "skill_sync_drift_guard_status",
}

ERROR_FIELD_CANDIDATES: tuple[str, ...] = (
    "error_code",
    "pin_error_code",
    "normalization_error_code",
    "path_integrity_error_code",
    "route_conflict_error_code",
)

TRUTHY_VALUES: tuple[str, ...] = ("1", "true", "yes", "y", "on")
FALSY_VALUES: tuple[str, ...] = ("0", "false", "no", "n", "off", "")
HEADSTAMP_EVIDENCE_REQUIRED_OPERATIONS: tuple[str, ...] = (
    "activate",
    "update",
    "mutation",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "three-plane",
)
RUNTIME_PROOF_REQUIRED_OPERATIONS: tuple[str, ...] = (
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "three-plane",
    "mutation",
)
MM_RUNTIME_REQUIRED_FIELDS: tuple[str, ...] = (
    "multimodal_runtime_evidence_status",
    "multimodal_preflight_status",
    "runtime_report_path",
    "runtime_report_run_id",
    "multimodal_calls",
    "multimodal_resolved",
    "multimodal_unresolved",
    "multimodal_errors",
    "multimodal_retry_calls",
    "runtime_gate_mode",
    "runtime_gate_required_confidence",
)
RL_RUNTIME_REQUIRED_FIELDS: tuple[str, ...] = (
    "reasoning_runtime_evidence_status",
    "reasoning_enforcement_level",
    "reasoning_attempt_trace_status",
    "no_target_done_block_status",
    "reasoning_next_action_status",
    "reasoning_escalation_status",
    "runtime_report_path",
    "runtime_report_run_id",
    "reasoning_attempt_count",
    "reasoning_runtime_evidence_refs",
)
STRICT_SKIP_BLOCKING_POLICIES: set[str] = {
    "fail_close",
    "strict_no_skip",
    "forbid_skip",
}
DEFAULT_STRICT_SKIP_POLICY = "fail_close"
DEFAULT_STRICT_SKIP_ALLOWED_REASONS: tuple[str, ...] = (
    "fixture_profile_scope",
    "contract_not_required",
    "scan_probe_profile_filtered_not_required",
)
PRE_EXECUTION_CURRENT_ROUND_SKIP_ALLOWED_REASONS: tuple[str, ...] = (
    "required_contract_not_applicable_current_round_unmaterialized",
    "required_contract_not_applicable_current_round_unlinked",
    "required_contract_not_applicable_no_current_round_evidence_source",
    "required_contract_not_applicable_missing_release_evidence",
    "no_promotion_event_in_current_run",
)
PRE_EXECUTION_CURRENT_ROUND_SKIP_OPERATIONS: set[str] = {"update", "validate"}
MONOTONIC_POLICY_DEFAULT_TARGET = "__strict_skip_defaults__"
STRICT_SKIP_RUNTIME_STATUS_FIELD_BY_TARGET: dict[str, str] = {
    "multimodal_plugin_enforcement": "multimodal_runtime_evidence_status",
    "reasoning_loop_failclose_enforcement": "reasoning_runtime_evidence_status",
}
ERR_ENTRY_CONTRACT = "IP-GATE-ENTRY-001"
ERR_ENTRY_REQUIRED = "IP-GATE-ENTRY-002"
ERR_ENTRY_REQUIRED_EVIDENCE_GAP = "IP-GATE-ENTRY-008"
REQUIRED_EVIDENCE_GAP_TOKEN = "required_contract_not_applicable_no_current_round_evidence_source"
STRICT_SKIP_NOT_ALLOWED_PREFIX = "strict_skip_not_allowed:"
ENTRY_RECEIPT_STATE_FILE = "required_gate_bundle_entry.latest.json"
ENTRY_RECEIPT_HISTORY_DIR = "required-gate-bundle-entry"
WRAPPER_PROOF_MAX_AGE_SECONDS_DEFAULT = 300
WRAPPER_PROOF_NONCE_STATE_FILE = "required_gate_wrapper_nonce_state.json"
DEFAULT_TIMEOUT_ENV = "IDENTITY_PROTOCOL_GATEWAY_CMD_TIMEOUT_SECONDS"


@dataclass(frozen=True)
class ValidatorSpec:
    requirement_key: str
    target_name: str
    script_path: str
    fixed_args: tuple[str, ...] = ()


@dataclass(frozen=True)
class GateProfileSelection:
    profile_name: str
    profile_mode: str
    requirement_keys: tuple[str, ...]
    strict_no_trim_operations: tuple[str, ...]


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        token = str(item or "").strip()
        if token:
            out.append(token)
    return out


def _as_lower_str_set(value: Any) -> set[str]:
    out: set[str] = set()
    if not isinstance(value, list):
        return out
    for item in value:
        token = str(item or "").strip().lower()
        if token:
            out.add(token)
    return out


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _atomic_write_text(path: Path, content: str) -> None:
    target = path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + f".tmp-{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)


def _resolve_subprocess_timeout_seconds() -> int:
    env_token = str(os.environ.get(DEFAULT_TIMEOUT_ENV, "")).strip()
    fallback = int(GATEWAY_WRAPPER_SUBPROCESS_TIMEOUT_SECONDS_DEFAULT)
    parsed = _safe_int(env_token, default=fallback)
    if parsed <= 0:
        return fallback
    return parsed


def _build_timeout_payload(*, cmd: list[str], timeout_seconds: int) -> dict[str, Any]:
    script = str(cmd[1] if len(cmd) >= 2 else "unknown_command").strip() or "unknown_command"
    reason = (
        f"{CTX_TOOL_TIMEOUT_MARKER}:{CTX_TOOL_TIMEOUT_REASON_PREFIX}:"
        f"required_gate_bundle_runner:{script}:timeout_seconds={int(timeout_seconds)}"
    )
    return {
        "bundle_status": STATUS_FAIL_REQUIRED,
        "error_code": CTX_TOOL_TIMEOUT_ERROR_CODE,
        "context_timeout_guard_status": STATUS_FAIL_REQUIRED,
        "context_timeout_marker": CTX_TOOL_TIMEOUT_MARKER,
        "timeout_seconds": int(timeout_seconds),
        "stale_reasons": [reason],
    }


def _is_privilege_escalation_error(exc: Exception) -> bool:
    if isinstance(exc, PermissionError):
        return True
    if isinstance(exc, OSError) and getattr(exc, "errno", None) in {
        errno.EACCES,
        errno.EPERM,
        errno.EROFS,
    }:
        return True
    return False


def _format_privilege_escalation_reason(*, path: Path, scope: str, exc: Exception) -> str:
    safe_scope = str(scope or "").strip() or "unknown_scope"
    safe_path = str(path.expanduser().resolve())
    safe_exc = type(exc).__name__
    return (
        f"{PRIVILEGE_ESCALATION_REASON_PREFIX}:{safe_scope}:path={safe_path}:error={safe_exc}:"
        f"hint={PRIVILEGE_ESCALATION_REMEDIATION_HINT}:error_code={PRIVILEGE_ESCALATION_ERROR_CODE}"
    )


def _resolve_pack_relative_path(pack_path: Path, raw_path: str, default_rel: str = "") -> Path:
    token = str(raw_path or "").strip() or str(default_rel or "").strip()
    if not token:
        return Path("")
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    if token.startswith("identity/runtime/"):
        return (pack_path / "runtime" / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (pack_path / token).resolve()
    return (pack_path / token).resolve()


def _consume_wrapper_nonce(
    *,
    catalog_path: str,
    identity_id: str,
    nonce: str,
    issued_at_epoch: int,
    max_age_seconds: int,
) -> tuple[bool, str]:
    try:
        pack_path, _task_path = resolve_pack_and_task(
            Path(catalog_path).expanduser().resolve(),
            identity_id,
        )
    except Exception as exc:
        return False, f"wrapper_dispatch_proof_nonce_pack_resolve_failed:{exc}"

    now_epoch = int(datetime.now(timezone.utc).timestamp())
    state_path = (pack_path / "runtime" / "state" / WRAPPER_PROOF_NONCE_STATE_FILE).resolve()
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            return False, _format_privilege_escalation_reason(
                path=state_path.parent,
                scope="wrapper_dispatch_proof_nonce_state_dir_write",
                exc=exc,
            )
        return False, f"wrapper_dispatch_proof_nonce_state_dir_write_failed:{exc}"
    state_doc: dict[str, Any] = {"used": {}}
    if state_path.exists():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                state_doc = loaded
        except Exception as exc:
            if _is_privilege_escalation_error(exc):
                return False, _format_privilege_escalation_reason(
                    path=state_path,
                    scope="wrapper_dispatch_proof_nonce_state_read",
                    exc=exc,
                )
            state_doc = {"used": {}}
    used = state_doc.get("used")
    if not isinstance(used, dict):
        used = {}

    ttl = max(int(max_age_seconds or 0), 1) * 4
    stale = [
        key
        for key, value in used.items()
        if now_epoch - _safe_int(value, default=0) > ttl
    ]
    for key in stale:
        used.pop(key, None)

    nonce_key = str(nonce or "").strip()
    if nonce_key in used:
        return False, "wrapper_dispatch_proof_nonce_replay_detected"

    used[nonce_key] = int(issued_at_epoch)
    state_doc["used"] = used
    try:
        _atomic_write_text(
            state_path,
            json.dumps(state_doc, ensure_ascii=False, indent=2) + "\n",
        )
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            return False, _format_privilege_escalation_reason(
                path=state_path,
                scope="wrapper_dispatch_proof_nonce_state_write",
                exc=exc,
            )
        return False, f"wrapper_dispatch_proof_nonce_state_write_failed:{exc}"
    return True, ""


def _validate_wrapper_dispatch_proof(
    *,
    proof_json: str,
    proof_signature: str,
    dispatch_secret: str,
    catalog_path: str,
    identity_id: str,
    operation: str,
    run_id_binding: str,
    actor_id: str,
    session_id: str,
    resolved_work_layer: str,
    resolved_source_layer: str,
    surface_label: str,
    max_age_seconds: int,
) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    details: dict[str, Any] = {
        "wrapper_dispatch_proof_nonce": "",
        "wrapper_dispatch_proof_issued_at_epoch": 0,
        "wrapper_dispatch_proof_sha256": "",
    }
    if not str(proof_json or "").strip():
        return False, ["wrapper_dispatch_proof_missing"], details
    if not str(proof_signature or "").strip():
        return False, ["wrapper_dispatch_proof_signature_missing"], details
    if not str(dispatch_secret or "").strip():
        return False, ["wrapper_dispatch_proof_secret_missing"], details

    try:
        doc = json.loads(str(proof_json).strip())
    except Exception:
        return False, ["wrapper_dispatch_proof_invalid_json"], details
    if not isinstance(doc, dict):
        return False, ["wrapper_dispatch_proof_payload_not_object"], details

    required_fields = (
        "schema_version",
        "identity_id",
        "operation",
        "run_id",
        "actor_id",
        "session_id",
        "work_layer",
        "source_layer",
        "surface_label",
        "issued_at_epoch",
        "nonce",
    )
    missing = [field for field in required_fields if field not in doc]
    if missing:
        return False, ["wrapper_dispatch_proof_fields_missing:" + ",".join(sorted(missing))], details

    details["wrapper_dispatch_proof_nonce"] = str(doc.get("nonce", "")).strip()
    details["wrapper_dispatch_proof_issued_at_epoch"] = _safe_int(doc.get("issued_at_epoch"), default=0)
    canonical = _canonical_json(doc)
    details["wrapper_dispatch_proof_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    expected_signature = hmac.new(
        str(dispatch_secret).encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(str(proof_signature).strip(), expected_signature):
        errors.append("wrapper_dispatch_proof_signature_invalid")

    if str(doc.get("schema_version", "")).strip() != "v1":
        errors.append("wrapper_dispatch_proof_schema_version_invalid")
    if str(doc.get("identity_id", "")).strip() != str(identity_id or "").strip():
        errors.append("wrapper_dispatch_proof_identity_mismatch")
    if str(doc.get("operation", "")).strip().lower() != str(operation or "").strip().lower():
        errors.append("wrapper_dispatch_proof_operation_mismatch")
    if str(doc.get("run_id", "")).strip() != str(run_id_binding or "").strip():
        errors.append("wrapper_dispatch_proof_run_id_mismatch")
    if str(doc.get("actor_id", "")).strip() != str(actor_id or "").strip():
        errors.append("wrapper_dispatch_proof_actor_id_mismatch")
    if str(doc.get("session_id", "")).strip() != str(session_id or "").strip():
        errors.append("wrapper_dispatch_proof_session_id_mismatch")
    if str(doc.get("work_layer", "")).strip().lower() != str(resolved_work_layer or "").strip().lower():
        errors.append("wrapper_dispatch_proof_work_layer_mismatch")
    if str(doc.get("source_layer", "")).strip().lower() != str(resolved_source_layer or "").strip().lower():
        errors.append("wrapper_dispatch_proof_source_layer_mismatch")
    if str(doc.get("surface_label", "")).strip() != str(surface_label or "").strip():
        errors.append("wrapper_dispatch_proof_surface_label_mismatch")

    issued_at_epoch = _safe_int(doc.get("issued_at_epoch"), default=0)
    now_epoch = int(datetime.now(timezone.utc).timestamp())
    max_age = max(_safe_int(max_age_seconds, default=WRAPPER_PROOF_MAX_AGE_SECONDS_DEFAULT), 1)
    if issued_at_epoch <= 0:
        errors.append("wrapper_dispatch_proof_issued_at_invalid")
    else:
        if issued_at_epoch > now_epoch + 30:
            errors.append("wrapper_dispatch_proof_issued_at_in_future")
        if now_epoch - issued_at_epoch > max_age:
            errors.append("wrapper_dispatch_proof_expired")

    nonce = str(doc.get("nonce", "")).strip()
    if len(nonce) < 16:
        errors.append("wrapper_dispatch_proof_nonce_too_short")
    if not errors:
        consumed, consume_error = _consume_wrapper_nonce(
            catalog_path=catalog_path,
            identity_id=identity_id,
            nonce=nonce,
            issued_at_epoch=issued_at_epoch,
            max_age_seconds=max_age,
        )
        if not consumed:
            errors.append(str(consume_error or "wrapper_dispatch_proof_nonce_consume_failed"))

    return len(errors) == 0, errors, details


def _read_process_commandline(pid: int) -> str:
    if pid <= 0:
        return ""
    if psutil is not None:
        try:
            proc = psutil.Process(pid)
            tokens = [str(tok or "").strip() for tok in (proc.cmdline() or [])]
            rendered = " ".join(token for token in tokens if token).strip()
            if rendered:
                return rendered
        except Exception:
            pass
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if proc_cmdline.exists():
        try:
            raw = proc_cmdline.read_bytes()
            tokens = [chunk.decode("utf-8", errors="ignore").strip() for chunk in raw.split(b"\x00")]
            return " ".join(token for token in tokens if token).strip()
        except Exception:
            pass
    try:
        proc = subprocess.run(
            ["ps", "-o", "command=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return str(proc.stdout or "").strip()


def _validate_wrapper_parent_attestation(
    *,
    expected_wrapper_path: str,
) -> tuple[bool, list[str], dict[str, Any]]:
    def _resolve_cli_path_token(token: str) -> str:
        raw = str(token or "").strip()
        if not raw:
            return ""
        if "/" not in raw and "\\" not in raw:
            return ""
        try:
            return str(Path(raw).expanduser().resolve())
        except Exception:
            return ""

    def _parent_command_matches_expected_wrapper(parent_cmdline: str, expected_path: Path) -> bool:
        line = str(parent_cmdline or "").strip()
        if not line:
            return False
        try:
            tokens = shlex.split(line)
        except Exception:
            tokens = line.split()
        if not tokens:
            return False

        expected = str(expected_path)

        direct_exec_path = _resolve_cli_path_token(tokens[0])
        if direct_exec_path and direct_exec_path == expected:
            return True

        exe_name = Path(tokens[0]).name.lower()
        if "python" not in exe_name:
            return False

        first_script_token = ""
        for tok in tokens[1:]:
            token = str(tok or "").strip()
            if not token:
                continue
            if token in {"-m", "-c"}:
                return False
            if token.startswith("-"):
                continue
            first_script_token = token
            break
        if not first_script_token:
            return False
        script_path = _resolve_cli_path_token(first_script_token)
        return bool(script_path and script_path == expected)

    errors: list[str] = []
    expected_path = Path(str(expected_wrapper_path or "").strip()).expanduser().resolve()
    parent_pid = int(os.getppid())
    parent_cmdline = _read_process_commandline(parent_pid)
    env_wrapper_path = str(os.environ.get("IDENTITY_PROTOCOL_INGRESS_WRAPPER_PATH", "")).strip()
    details: dict[str, Any] = {
        "wrapper_parent_attestation_ppid": parent_pid,
        "wrapper_parent_attestation_expected_path": str(expected_path) if str(expected_wrapper_path or "").strip() else "",
        "wrapper_parent_attestation_command_sha256": (
            hashlib.sha256(parent_cmdline.encode("utf-8")).hexdigest() if parent_cmdline else ""
        ),
        "wrapper_parent_attestation_env_path": env_wrapper_path,
    }
    if not str(expected_wrapper_path or "").strip():
        errors.append("wrapper_parent_attestation_expected_path_missing")
    if not env_wrapper_path:
        errors.append("wrapper_parent_attestation_env_path_missing")
    else:
        env_path = Path(env_wrapper_path).expanduser().resolve()
        if env_path != expected_path:
            errors.append("wrapper_parent_attestation_env_path_mismatch")
    if not parent_cmdline:
        errors.append("wrapper_parent_attestation_parent_command_missing")
    elif not _parent_command_matches_expected_wrapper(parent_cmdline, expected_path):
        errors.append("wrapper_parent_attestation_parent_command_mismatch")
    return len(errors) == 0, errors, details


def _resolve_host_gateway_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in HOST_GATEWAY_CONTRACT_KEYS:
        raw = task.get(key)
        if isinstance(raw, dict):
            return raw
    for key, raw in task.items():
        if not isinstance(raw, dict):
            continue
        token = str(key or "").strip().lower()
        if "gateway" in token and "contract" in token:
            return raw
    return {}


def _resolve_wrapper_enforcement_policy(
    *,
    catalog_path: str,
    identity_id: str,
) -> tuple[dict[str, Any], list[str]]:
    policy: dict[str, Any] = {
        "required_surface_label": DEFAULT_HOST_WRAPPER_SURFACE_LABEL,
        "required_dispatch_token": DEFAULT_REQUIRED_WRAPPER_DISPATCH_TOKEN,
        "required_wrapper_surface_status": STATUS_PASS_REQUIRED,
        "required_wrapper_dispatch_status": STATUS_PASS_REQUIRED,
        "expected_ingress_wrapper_path": "",
        "host_dispatch_mode": "wrapper_only",
        "strict_operations": list(STRICT_NO_TRIM_OPERATIONS_DEFAULT),
        "light_operations": list(LIGHT_NO_TRIM_OPERATIONS_DEFAULT),
        "allow_upgrade_only": True,
        "proof_required": True,
        "proof_max_age_seconds": WRAPPER_PROOF_MAX_AGE_SECONDS_DEFAULT,
        "proof_signer_mode": "",
        "proof_signer_secret_env": "",
        "proof_signing_key_path": "",
        "proof_signing_secret": "",
    }
    errors: list[str] = []
    try:
        pack_path, task_path = resolve_pack_and_task(
            Path(catalog_path).expanduser().resolve(),
            identity_id,
        )
        task = load_json(task_path)
    except Exception as exc:
        return policy, [f"host_gateway_contract_resolve_failed:{exc}"]

    policy["expected_ingress_wrapper_path"] = str(
        _resolve_pack_relative_path(
            pack_path,
            "",
            default_rel="runtime/gate/protocol_ingress_wrapper.py",
        )
    )

    host_gateway_contract = _resolve_host_gateway_contract(task if isinstance(task, dict) else {})
    if not isinstance(host_gateway_contract, dict) or not host_gateway_contract:
        return policy, ["host_gateway_contract_missing"]

    host_dispatch_mode = str(host_gateway_contract.get("host_dispatch_mode", "")).strip().lower()
    if host_dispatch_mode:
        policy["host_dispatch_mode"] = host_dispatch_mode
    else:
        errors.append("host_gateway_contract_dispatch_mode_missing")

    dispatch_token = str(host_gateway_contract.get("ingress_wrapper_dispatch_token", "")).strip()
    if dispatch_token:
        policy["required_dispatch_token"] = dispatch_token
    else:
        errors.append("host_gateway_contract_ingress_dispatch_token_missing")

    ingress_wrapper_raw = str(host_gateway_contract.get("ingress_wrapper_path", "")).strip()
    resolved_ingress_wrapper_path = _resolve_pack_relative_path(
        pack_path,
        ingress_wrapper_raw,
        default_rel="runtime/gate/protocol_ingress_wrapper.py",
    )
    if resolved_ingress_wrapper_path:
        policy["expected_ingress_wrapper_path"] = str(resolved_ingress_wrapper_path)
    if not str(policy.get("expected_ingress_wrapper_path", "")).strip():
        errors.append("host_gateway_contract_ingress_wrapper_path_missing")

    entry_policy = host_gateway_contract.get("entry_receipt_policy")
    if not isinstance(entry_policy, dict):
        errors.append("host_gateway_contract_entry_receipt_policy_missing")
    else:
        required_surface_label = str(entry_policy.get("required_surface_label", "")).strip()
        if required_surface_label:
            policy["required_surface_label"] = required_surface_label
        else:
            errors.append("host_gateway_contract_required_surface_label_missing")

        required_wrapper_surface_status = str(entry_policy.get("required_wrapper_surface_status", "")).strip().upper()
        if required_wrapper_surface_status:
            policy["required_wrapper_surface_status"] = required_wrapper_surface_status
        else:
            errors.append("host_gateway_contract_required_wrapper_surface_status_missing")

        required_wrapper_dispatch_status = str(
            entry_policy.get("required_wrapper_dispatch_token_status", "")
        ).strip().upper()
        if required_wrapper_dispatch_status:
            policy["required_wrapper_dispatch_status"] = required_wrapper_dispatch_status
        else:
            errors.append("host_gateway_contract_required_wrapper_dispatch_status_missing")

    operation_profile_policy = host_gateway_contract.get("operation_profile_policy")
    if not isinstance(operation_profile_policy, dict):
        errors.append("host_gateway_contract_operation_profile_policy_missing")
    else:
        strict_operations = _as_lower_str_set(operation_profile_policy.get("strict_operations"))
        light_operations = _as_lower_str_set(operation_profile_policy.get("light_operations"))
        allow_upgrade_only = bool(operation_profile_policy.get("allow_upgrade_only", True))
        if strict_operations:
            policy["strict_operations"] = sorted(strict_operations)
        else:
            errors.append("host_gateway_contract_operation_profile_strict_operations_missing")
        if light_operations:
            policy["light_operations"] = sorted(light_operations)
        else:
            errors.append("host_gateway_contract_operation_profile_light_operations_missing")
        policy["allow_upgrade_only"] = allow_upgrade_only

    ingress_proof_policy = host_gateway_contract.get("ingress_proof_policy")
    if isinstance(ingress_proof_policy, dict):
        proof_required = bool(ingress_proof_policy.get("required", True))
        proof_max_age_seconds = _safe_int(
            ingress_proof_policy.get("max_age_seconds"),
            default=WRAPPER_PROOF_MAX_AGE_SECONDS_DEFAULT,
        )
        policy["proof_required"] = proof_required
        policy["proof_max_age_seconds"] = max(proof_max_age_seconds, 1)
        signer_mode = str(ingress_proof_policy.get("signer_mode", "")).strip().lower()
        proof_signing_key_path = str(ingress_proof_policy.get("signing_key_path", "")).strip()
        if not signer_mode:
            signer_mode = "runtime_file_secret" if proof_signing_key_path else ""
        policy["proof_signer_mode"] = signer_mode

        if signer_mode == "runtime_env_secret":
            signer_secret_env = str(ingress_proof_policy.get("signer_secret_env", "")).strip()
            bootstrap_from_key = bool(
                ingress_proof_policy.get("bootstrap_env_secret_from_signing_key_path", True)
            )
            policy["proof_signer_secret_env"] = signer_secret_env
            if not signer_secret_env:
                errors.append("host_gateway_contract_ingress_proof_signer_secret_env_missing")
            else:
                secret = str(os.environ.get(signer_secret_env, "")).strip()
                if not secret and bootstrap_from_key and proof_signing_key_path:
                    key_path = Path(proof_signing_key_path).expanduser()
                    if not key_path.is_absolute():
                        if proof_signing_key_path.startswith("identity/runtime/"):
                            key_path = (pack_path / "runtime" / proof_signing_key_path[len("identity/runtime/") :]).resolve()
                        elif proof_signing_key_path.startswith("runtime/"):
                            key_path = (pack_path / proof_signing_key_path).resolve()
                        else:
                            key_path = (pack_path / proof_signing_key_path).resolve()
                    policy["proof_signing_key_path"] = str(key_path)
                    if key_path.exists():
                        secret = key_path.read_text(encoding="utf-8", errors="ignore").strip()
                        if secret:
                            os.environ[signer_secret_env] = secret
                if secret:
                    policy["proof_signing_secret"] = secret
                else:
                    errors.append("host_gateway_contract_ingress_proof_signer_secret_env_unset")
        elif signer_mode in {"runtime_file_secret", ""}:
            if proof_signing_key_path:
                key_path = Path(proof_signing_key_path).expanduser()
                if not key_path.is_absolute():
                    if proof_signing_key_path.startswith("identity/runtime/"):
                        key_path = (pack_path / "runtime" / proof_signing_key_path[len("identity/runtime/") :]).resolve()
                    elif proof_signing_key_path.startswith("runtime/"):
                        key_path = (pack_path / proof_signing_key_path).resolve()
                    else:
                        key_path = (pack_path / proof_signing_key_path).resolve()
                policy["proof_signing_key_path"] = str(key_path)
                if key_path.exists():
                    secret = key_path.read_text(encoding="utf-8", errors="ignore").strip()
                    if secret:
                        policy["proof_signing_secret"] = secret
                    else:
                        errors.append("host_gateway_contract_ingress_proof_signing_key_empty")
                else:
                    errors.append("host_gateway_contract_ingress_proof_signing_key_missing")
            else:
                errors.append("host_gateway_contract_ingress_proof_signing_key_path_missing")
        else:
            errors.append("host_gateway_contract_ingress_proof_signer_mode_unsupported")

    if not str(policy.get("required_dispatch_token", "")).strip():
        errors.append("host_gateway_contract_required_dispatch_token_empty")

    if not str(policy.get("required_surface_label", "")).strip():
        errors.append("host_gateway_contract_required_surface_label_empty")

    return policy, errors


def _operation_requires_wrapper_provenance(
    *,
    operation: str,
    host_dispatch_mode: str,
    wrapper_policy: dict[str, Any],
) -> bool:
    if str(host_dispatch_mode or "").strip().lower() != "wrapper_only":
        return False
    op = str(operation or "").strip().lower()
    strict_operations = _as_lower_str_set(wrapper_policy.get("strict_operations"))
    light_operations = _as_lower_str_set(wrapper_policy.get("light_operations"))
    allow_upgrade_only = bool(wrapper_policy.get("allow_upgrade_only", True))

    if op and (op in strict_operations or op in light_operations):
        return True
    if op and allow_upgrade_only:
        # Unknown operations under wrapper_only are treated as strict by default.
        return True
    # Empty operation token is invalid input and must not bypass wrapper provenance.
    if not op:
        return True
    return False


def _resolve_default_contract_mapping(repo_root: Path) -> Path:
    mapping_dir = repo_root / "identity" / "protocol" / "mappings"
    current_file = mapping_dir / "contract-binding.current.yaml"
    if current_file.exists():
        return current_file
    candidates = sorted(mapping_dir.glob("contract-binding.v*.yaml"))
    if candidates:
        return candidates[-1]
    fallback = mapping_dir / "contract-binding.yaml"
    return fallback


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    try:
        current_doc = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return configured_path, "", "current_file_parse_failed"
    if not isinstance(current_doc, dict):
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _pick_primary_status_field(row: dict[str, Any]) -> str:
    report_fields = _as_str_list(row.get("report_field_refs"))
    if not report_fields:
        return ""
    for field in report_fields:
        if field.endswith("_status"):
            return field
    return report_fields[0]


def _load_monotonic_policy_by_target(
    *,
    repo_root: Path,
    governance_file: str = DEFAULT_PLUGIN_GOVERNANCE_FILE,
) -> tuple[dict[str, dict[str, Any]], Path, list[str]]:
    errors: list[str] = []
    policy_by_target: dict[str, dict[str, Any]] = {}
    governance_entry_path = (repo_root / str(governance_file or DEFAULT_PLUGIN_GOVERNANCE_FILE)).resolve()
    governance_path = governance_entry_path

    if governance_entry_path.name.endswith(".current.yaml"):
        governance_path, _active_file, alias_error = _resolve_current_yaml_alias(
            repo_root,
            str(governance_file or DEFAULT_PLUGIN_GOVERNANCE_FILE),
        )
        if alias_error:
            errors.append(f"plugin_governance_alias_error:{governance_entry_path}:{alias_error}")
            return policy_by_target, governance_path, errors
    if not governance_path.exists() or not governance_path.is_file():
        errors.append(f"plugin_governance_file_missing:{governance_path}")
        return policy_by_target, governance_path, errors

    try:
        governance_doc = yaml.safe_load(governance_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"plugin_governance_parse_failed:{governance_path}:{exc}")
        return policy_by_target, governance_path, errors
    if not isinstance(governance_doc, dict):
        errors.append(f"plugin_governance_invalid_root:{governance_path}")
        return policy_by_target, governance_path, errors

    profiles = governance_doc.get("plugin_failclose_profiles")
    if not isinstance(profiles, list):
        errors.append(f"plugin_governance_profiles_missing_or_invalid:{governance_path}")
        return policy_by_target, governance_path, errors

    strict_skip_defaults = governance_doc.get("strict_skip_defaults")
    if not isinstance(strict_skip_defaults, dict):
        strict_skip_defaults = {}
    default_strict_skip_policy = (
        str(strict_skip_defaults.get("strict_skip_policy", DEFAULT_STRICT_SKIP_POLICY)).strip().lower()
        or DEFAULT_STRICT_SKIP_POLICY
    )
    default_strict_skip_allowed_reasons = _as_str_list(
        strict_skip_defaults.get("strict_skip_allowed_reasons", DEFAULT_STRICT_SKIP_ALLOWED_REASONS)
    )
    policy_by_target[MONOTONIC_POLICY_DEFAULT_TARGET] = {
        "strict_skip_policy": default_strict_skip_policy,
        "strict_skip_allowed_reasons": set(default_strict_skip_allowed_reasons),
        "minimum_enforcement_level": "",
        "allow_self_upgrade": False,
        "allow_downgrade": False,
        "strict_skip_default_applied": True,
    }

    for row in profiles:
        if not isinstance(row, dict):
            continue
        target_name = str(row.get("target_name", "")).strip()
        if not target_name:
            continue
        monotonic = row.get("monotonic_policy")
        if not isinstance(monotonic, dict):
            monotonic = {}
        strict_skip_allowed_reasons = _as_str_list(monotonic.get("strict_skip_allowed_reasons"))
        strict_skip_policy = str(monotonic.get("strict_skip_policy", "")).strip().lower() or default_strict_skip_policy
        if strict_skip_allowed_reasons:
            effective_skip_allowed_reasons = set(strict_skip_allowed_reasons)
            strict_skip_default_applied = False
        else:
            effective_skip_allowed_reasons = set(default_strict_skip_allowed_reasons)
            strict_skip_default_applied = True
        policy_by_target[target_name] = {
            "strict_skip_policy": strict_skip_policy,
            "strict_skip_allowed_reasons": effective_skip_allowed_reasons,
            "minimum_enforcement_level": str(monotonic.get("minimum_enforcement_level", "")).strip().upper(),
            "allow_self_upgrade": _parse_bool_token(monotonic.get("allow_self_upgrade", False)),
            "allow_downgrade": _parse_bool_token(monotonic.get("allow_downgrade", False)),
            "strict_skip_default_applied": strict_skip_default_applied,
        }
    return policy_by_target, governance_path, errors


def _build_effective_requirement_maps(
    *,
    repo_root: Path,
    mapping_path: Path,
) -> tuple[tuple[str, ...], dict[str, str], dict[str, str], list[str]]:
    errors: list[str] = []
    requirement_order = list(BUNDLE_REQUIREMENT_ORDER)
    target_name_by_requirement = dict(TARGET_NAME_BY_REQUIREMENT)
    status_field_by_target = dict(STATUS_FIELD_BY_TARGET)

    try:
        mapping_doc = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"contract_mapping_parse_failed:{mapping_path}:{exc}")
        mapping_doc = {}
    if not isinstance(mapping_doc, dict):
        errors.append(f"contract_mapping_invalid_root:{mapping_path}")
        mapping_doc = {}

    registry_entry = "identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml"
    registry_path, _registry_active_file, registry_alias_error = _resolve_current_yaml_alias(repo_root, registry_entry)
    if registry_alias_error:
        errors.append(f"plugin_registry_alias_error:{registry_entry}:{registry_alias_error}")
        return tuple(requirement_order), target_name_by_requirement, status_field_by_target, errors
    if not registry_path.exists() or not registry_path.is_file():
        errors.append(f"plugin_registry_missing:{registry_path}")
        return tuple(requirement_order), target_name_by_requirement, status_field_by_target, errors

    try:
        registry_doc = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"plugin_registry_parse_failed:{registry_path}:{exc}")
        return tuple(requirement_order), target_name_by_requirement, status_field_by_target, errors

    plugins = registry_doc.get("plugins") if isinstance(registry_doc, dict) else None
    if not isinstance(plugins, list):
        errors.append(f"plugin_registry_plugins_missing_or_invalid:{registry_path}")
        return tuple(requirement_order), target_name_by_requirement, status_field_by_target, errors

    for row in plugins:
        if not isinstance(row, dict):
            continue
        gate_mode = str(row.get("gate_mode", "")).strip().lower()
        if gate_mode != "fail_close_strict":
            continue
        requirement_key = str(row.get("requirement_key", "")).strip()
        target_name = str(row.get("bundle_target_name", "")).strip()
        if not requirement_key or not target_name:
            errors.append(f"plugin_registry_tuple_missing:{row.get('plugin_id','')}")
            continue
        target_name_by_requirement[requirement_key] = target_name
        if requirement_key not in requirement_order:
            requirement_order.append(requirement_key)

        if target_name in status_field_by_target:
            continue
        mapping_row = mapping_doc.get(requirement_key)
        if not isinstance(mapping_row, dict):
            errors.append(f"contract_mapping_row_missing_for_plugin_requirement:{requirement_key}")
            continue
        status_field = _pick_primary_status_field(mapping_row)
        if not status_field:
            errors.append(f"status_field_unresolved_for_plugin_requirement:{requirement_key}")
            continue
        status_field_by_target[target_name] = status_field

    return tuple(requirement_order), target_name_by_requirement, status_field_by_target, errors


def _parse_validator_entry(raw_entry: str) -> tuple[str, tuple[str, ...]]:
    # Example raw entries:
    # - scripts/validate_v16_intake_evidence_core.py::mode=intake_contract
    # - scripts/validate_v16_cross_verification_tracks.py::wrapper_only_optional
    raw = str(raw_entry or "").strip()
    if not raw:
        return "", ()
    if "::" not in raw:
        return raw, ()
    script_part, suffix = raw.split("::", 1)
    suffix = suffix.strip()
    if not suffix:
        return script_part.strip(), ()
    if suffix.startswith("mode="):
        mode_value = suffix.split("=", 1)[1].strip()
        if mode_value:
            return script_part.strip(), ("--mode", mode_value)
    # wrapper/optional annotations are metadata only and do not map to CLI flags.
    return script_part.strip(), ()


def _select_validator_spec(
    requirement_key: str,
    row: dict[str, Any],
    *,
    target_name_by_requirement: dict[str, str],
) -> ValidatorSpec | None:
    target_name = target_name_by_requirement.get(requirement_key, requirement_key)
    validator_ids = list(row.get("validator_ids") or [])
    parsed: list[tuple[str, tuple[str, ...]]] = [
        _parse_validator_entry(entry) for entry in validator_ids if str(entry or "").strip()
    ]
    if not parsed:
        return None

    # Prefer validate_* scripts for gate execution (emit/normalize helpers are non-gating helpers).
    preferred: tuple[str, tuple[str, ...]] | None = None
    for script_path, fixed_args in parsed:
        base = Path(script_path).name
        if base.startswith("validate_"):
            preferred = (script_path, fixed_args)
            break
    if preferred is None:
        preferred = parsed[0]
    return ValidatorSpec(
        requirement_key=requirement_key,
        target_name=target_name,
        script_path=preferred[0],
        fixed_args=preferred[1],
    )


def _load_validator_specs(
    mapping_path: Path,
    requirement_keys: tuple[str, ...],
    *,
    target_name_by_requirement: dict[str, str],
) -> tuple[list[ValidatorSpec], list[str]]:
    if not mapping_path.exists():
        return [], [f"contract_mapping_missing:{mapping_path}"]

    data = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    errors: list[str] = []
    specs: list[ValidatorSpec] = []
    for requirement_key in requirement_keys:
        row = data.get(requirement_key)
        if not isinstance(row, dict):
            errors.append(f"mapping_row_missing:{requirement_key}")
            continue
        spec = _select_validator_spec(
            requirement_key,
            row,
            target_name_by_requirement=target_name_by_requirement,
        )
        if spec is None:
            errors.append(f"validator_ids_missing:{requirement_key}")
            continue
        specs.append(spec)
    return specs, errors


def _load_gate_profile_selection(
    *,
    repo_root: Path,
    profile_file: str,
    profile_name: str,
    operation: str,
    resolved_work_layer: str,
    default_requirement_order: tuple[str, ...],
    known_requirement_keys: set[str],
) -> tuple[GateProfileSelection | None, Path, list[str]]:
    errors: list[str] = []
    profile_entry_path = (repo_root / str(profile_file or DEFAULT_GATE_PROFILE_FILE)).resolve()
    profile_path = profile_entry_path
    profile_alias_error = ""
    if profile_entry_path.name.endswith(".current.yaml"):
        profile_path, _active_file, profile_alias_error = _resolve_current_yaml_alias(
            repo_root, str(profile_file or DEFAULT_GATE_PROFILE_FILE)
        )
        if profile_alias_error:
            errors.append(f"gate_profile_alias_error:{profile_entry_path}:{profile_alias_error}")
            return None, profile_path, errors
    elif not profile_path.exists():
        errors.append(f"gate_profile_file_missing:{profile_path}")
        return None, profile_path, errors

    try:
        doc = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"gate_profile_parse_failed:{profile_path}:{exc}")
        return None, profile_path, errors
    if not isinstance(doc, dict):
        errors.append(f"gate_profile_invalid_root:{profile_path}")
        return None, profile_path, errors

    profiles = doc.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        errors.append(f"gate_profile_profiles_missing_or_invalid:{profile_path}")
        return None, profile_path, errors

    selected_name = (
        str(profile_name or "").strip()
        or str(doc.get("default_profile", "")).strip()
        or DEFAULT_GATE_PROFILE_NAME
    )
    selected = profiles.get(selected_name)
    if not isinstance(selected, dict):
        errors.append(f"gate_profile_not_found:{selected_name}")
        return None, profile_path, errors

    mode = str(selected.get("mode", "")).strip().lower() or "full"
    if mode not in {"full", "targeted"}:
        errors.append(f"gate_profile_invalid_mode:{selected_name}:{mode}")
        return None, profile_path, errors

    strict_no_trim_operations = tuple(
        _as_str_list(doc.get("strict_no_trim_operations")) or list(STRICT_NO_TRIM_OPERATIONS_DEFAULT)
    )
    normalized_operation = str(operation or "").strip().lower()
    allow_strict_operations = set(_as_str_list(selected.get("allow_strict_operations")))
    if (
        mode != "full"
        and normalized_operation in set(strict_no_trim_operations)
        and normalized_operation not in allow_strict_operations
    ):
        errors.append(f"gate_profile_forbidden_for_strict_operation:{selected_name}:{normalized_operation}")

    allowed_operations = _as_str_list(selected.get("allowed_operations"))
    if not allowed_operations:
        allowed_operations = ["*"] if mode == "full" else []
    if not allowed_operations:
        errors.append(f"gate_profile_allowed_operations_missing:{selected_name}")
    elif "*" not in allowed_operations and normalized_operation not in set(allowed_operations):
        errors.append(f"gate_profile_operation_not_allowed:{selected_name}:{normalized_operation}")

    require_layers = set(_as_str_list(selected.get("require_work_layers")))
    normalized_work_layer = str(resolved_work_layer or "").strip().lower()
    if require_layers and normalized_work_layer and normalized_work_layer not in require_layers:
        errors.append(f"gate_profile_work_layer_not_allowed:{selected_name}:{normalized_work_layer}")

    if mode == "full":
        requirement_keys = tuple(default_requirement_order)
    else:
        requested = _as_str_list(selected.get("requirement_keys"))
        if not requested:
            errors.append(f"gate_profile_requirement_keys_missing:{selected_name}")
            requirement_keys = ()
        else:
            unknown = [key for key in requested if key not in known_requirement_keys]
            if unknown:
                errors.append(f"gate_profile_unknown_requirement_keys:{selected_name}:{','.join(unknown)}")
            requirement_keys = tuple(key for key in requested if key in known_requirement_keys)
            if not requirement_keys:
                errors.append(f"gate_profile_requirement_keys_empty:{selected_name}")

    operation_overrides = selected.get("operation_requirement_overrides")
    if isinstance(operation_overrides, dict):
        override_node = operation_overrides.get(normalized_operation)
        if not isinstance(override_node, dict):
            override_node = operation_overrides.get("*")
        if isinstance(override_node, dict):
            include_keys = _as_str_list(override_node.get("include_requirement_keys"))
            exclude_keys = _as_str_list(override_node.get("exclude_requirement_keys"))
            unknown_include = sorted({key for key in include_keys if key not in known_requirement_keys})
            unknown_exclude = sorted({key for key in exclude_keys if key not in known_requirement_keys})
            if unknown_include:
                errors.append(
                    f"gate_profile_unknown_override_include_keys:{selected_name}:{normalized_operation}:{','.join(unknown_include)}"
                )
            if unknown_exclude:
                errors.append(
                    f"gate_profile_unknown_override_exclude_keys:{selected_name}:{normalized_operation}:{','.join(unknown_exclude)}"
                )
            include_keys = [key for key in include_keys if key in known_requirement_keys]
            exclude_keys_set = {key for key in exclude_keys if key in known_requirement_keys}
            if include_keys:
                requirement_keys = tuple(key for key in include_keys if key not in exclude_keys_set)
            elif exclude_keys_set:
                requirement_keys = tuple(key for key in requirement_keys if key not in exclude_keys_set)
            if not requirement_keys:
                errors.append(f"gate_profile_requirement_keys_empty_after_override:{selected_name}:{normalized_operation}")

    selection = GateProfileSelection(
        profile_name=selected_name,
        profile_mode=mode,
        requirement_keys=requirement_keys,
        strict_no_trim_operations=strict_no_trim_operations,
    )
    return selection, profile_path, errors


def _run(cmd: list[str], *, cwd: Path | None = None) -> tuple[int, str, str]:
    timeout_seconds = _resolve_subprocess_timeout_seconds()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else None,
            timeout=timeout_seconds,
        )
        return int(proc.returncode), proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        payload = _build_timeout_payload(cmd=cmd, timeout_seconds=timeout_seconds)
        out = json.dumps(payload, ensure_ascii=False)
        return 124, out, str(exc)


_SCRIPT_FLAG_SCAN_CACHE: dict[tuple[str, str], bool] = {}


def _script_accepts_flag(script_path: str, *, flag: str, repo_root: Path) -> bool:
    key = (str(script_path or "").strip(), str(flag or "").strip())
    if not key[0] or not key[1]:
        return False
    cached = _SCRIPT_FLAG_SCAN_CACHE.get(key)
    if cached is not None:
        return cached
    path = _resolve_input_path(repo_root, key[0])
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        _SCRIPT_FLAG_SCAN_CACHE[key] = False
        return False
    accepted = key[1] in text
    _SCRIPT_FLAG_SCAN_CACHE[key] = accepted
    return accepted


def _parse_payload(stdout_text: str) -> dict[str, Any]:
    text = (stdout_text or "").strip()
    if not text:
        return {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in reversed(lines):
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return {}


def _extract_error_code(payload: dict[str, Any], stderr_text: str) -> str:
    for key in ERROR_FIELD_CANDIDATES:
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    err = str(stderr_text or "").strip()
    if "IP-" in err:
        # keep tail concise for replay readability
        tail = err.splitlines()[-1] if err.splitlines() else err
        return tail.strip()
    return ""


def _classify_status(
    *,
    target_name: str,
    rc: int,
    payload: dict[str, Any],
    status_field_by_target: dict[str, str],
) -> tuple[str, str]:
    status_field = status_field_by_target[target_name]
    status_value = str(payload.get(status_field, "")).strip().upper()
    if status_value in {
        STATUS_PASS_REQUIRED,
        STATUS_SKIPPED_NOT_REQUIRED,
        STATUS_FAIL_REQUIRED,
    }:
        return status_value, status_field
    if status_value == STATUS_FAIL_OPTIONAL:
        return STATUS_FAIL_REQUIRED, status_field

    if rc != 0:
        return STATUS_FAIL_REQUIRED, status_field
    if status_field not in payload:
        return STATUS_FAIL_REQUIRED, status_field
    required_contract = bool(payload.get("required_contract", False))
    return (STATUS_PASS_REQUIRED if required_contract else STATUS_SKIPPED_NOT_REQUIRED), status_field


def _validate_row_payload_contract(
    *,
    payload: dict[str, Any],
    status_field: str,
    target_name: str,
    operation: str,
    required_contract: bool,
) -> list[str]:
    issues: list[str] = []
    if not isinstance(payload, dict) or not payload:
        issues.append("payload_missing_or_not_object")
        return issues
    if status_field not in payload:
        issues.append("status_field_missing")
    if "required_contract" not in payload:
        issues.append("required_contract_missing")
    op = str(operation or "").strip().lower()
    if (
        target_name == "multimodal_plugin_enforcement"
        and required_contract
        and op in RUNTIME_PROOF_REQUIRED_OPERATIONS
    ):
        for field in MM_RUNTIME_REQUIRED_FIELDS:
            if field not in payload:
                issues.append(f"mm_runtime_field_missing:{field}")
    if (
        target_name == "reasoning_loop_failclose_enforcement"
        and required_contract
        and op in RUNTIME_PROOF_REQUIRED_OPERATIONS
    ):
        for field in RL_RUNTIME_REQUIRED_FIELDS:
            if field not in payload:
                issues.append(f"rl_runtime_field_missing:{field}")
    return issues


def _write_payload_out(out_path: str, payload: dict[str, Any]) -> None:
    target = Path(out_path).expanduser().resolve()
    _atomic_write_text(target, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _persist_unique_entry_receipt(
    *,
    catalog_path: str,
    identity_id: str,
    operation: str,
    run_id_binding: str,
    actor_id: str,
    session_id: str,
    surface_label: str,
    payload: dict[str, Any],
) -> tuple[str, str, str]:
    try:
        pack_path, _task_path = resolve_pack_and_task(
            Path(catalog_path).expanduser().resolve(),
            identity_id,
        )
    except Exception as exc:
        return "", "", f"resolve_pack_failed:{exc}"

    ts = _utc_now_iso()
    operation_token = str(operation or "").strip().lower() or "unknown"
    run_token = str(run_id_binding or "").strip() or f"ts-{int(datetime.now(timezone.utc).timestamp())}"
    state_dir = (pack_path / "runtime" / "state").resolve()
    history_dir = (pack_path / "runtime" / "reports" / ENTRY_RECEIPT_HISTORY_DIR).resolve()
    latest_path = (state_dir / ENTRY_RECEIPT_STATE_FILE).resolve()
    operation_path = (state_dir / f"required_gate_bundle_entry.{operation_token}.json").resolve()
    history_path = (
        history_dir / f"required-gate-bundle-entry-{identity_id}-{operation_token}-{run_token}.json"
    ).resolve()

    receipt = {
        "receipt_version": "v1",
        "receipt_id": f"{BUNDLE_KEY}:{identity_id}:{operation_token}:{run_token}",
        "created_at_utc": ts,
        "bundle_contract_id": BUNDLE_CONTRACT_ID,
        "bundle_key": BUNDLE_KEY,
        "identity_id": str(identity_id),
        "catalog_path": str(Path(catalog_path).expanduser().resolve()),
        "operation": operation_token,
        "surface_label": str(surface_label or "").strip(),
        "wrapper_dispatch_required": bool(payload.get("wrapper_dispatch_required", False)),
        "wrapper_surface_status": str(payload.get("wrapper_surface_status", "")).strip(),
        "wrapper_dispatch_token_status": str(payload.get("wrapper_dispatch_token_status", "")).strip(),
        "wrapper_dispatch_proof_required": bool(payload.get("wrapper_dispatch_proof_required", False)),
        "wrapper_dispatch_proof_status": str(payload.get("wrapper_dispatch_proof_status", "")).strip(),
        "wrapper_dispatch_proof_nonce": str(payload.get("wrapper_dispatch_proof_nonce", "")).strip(),
        "wrapper_dispatch_proof_issued_at_epoch": int(
            _safe_int(payload.get("wrapper_dispatch_proof_issued_at_epoch"), default=0)
        ),
        "wrapper_dispatch_proof_sha256": str(payload.get("wrapper_dispatch_proof_sha256", "")).strip(),
        "wrapper_parent_attestation_required": bool(payload.get("wrapper_parent_attestation_required", False)),
        "wrapper_parent_attestation_status": str(payload.get("wrapper_parent_attestation_status", "")).strip(),
        "wrapper_parent_attestation_ppid": int(
            _safe_int(payload.get("wrapper_parent_attestation_ppid"), default=0)
        ),
        "wrapper_parent_attestation_expected_path": str(
            payload.get("wrapper_parent_attestation_expected_path", "")
        ).strip(),
        "wrapper_parent_attestation_command_sha256": str(
            payload.get("wrapper_parent_attestation_command_sha256", "")
        ).strip(),
        "wrapper_dispatch_token_expected": str(payload.get("wrapper_dispatch_token_expected", "")).strip(),
        "run_id_binding": str(run_id_binding or "").strip(),
        "actor_id": str(actor_id or "").strip(),
        "session_id": str(session_id or "").strip(),
        "report_selected_path": str(payload.get("report_selected_path", "")).strip(),
        "bundle_status": str(payload.get("bundle_status", "")).strip(),
        "error_code": str(payload.get("error_code", "")).strip(),
        "required_contract": bool(payload.get("required_contract", False)),
        "failed_required_contract_count": int(payload.get("failed_required_contract_count", 0) or 0),
        "row_contract_error_count": int(payload.get("row_contract_error_count", 0) or 0),
        "gate_profile": str(payload.get("gate_profile", "")).strip(),
        "gate_profile_mode": str(payload.get("gate_profile_mode", "")).strip(),
        "mapping_errors": list(payload.get("mapping_errors") or []),
        "selector_policy_id": UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID,
        "selector_precedence": list(UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE),
        "selector_source_fields": list(UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS),
    }
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        history_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            return "", "", _format_privilege_escalation_reason(
                path=state_dir if not state_dir.exists() else history_dir,
                scope="required_gate_bundle_entry_state_dir_write",
                exc=exc,
            )
        return "", "", f"persist_state_dir_failed:{exc}"

    for target_path in (latest_path, operation_path, history_path):
        try:
            _write_payload_out(str(target_path), receipt)
        except Exception as exc:
            if _is_privilege_escalation_error(exc):
                return "", "", _format_privilege_escalation_reason(
                    path=target_path,
                    scope="required_gate_bundle_entry_receipt_write",
                    exc=exc,
                )
            return "", "", f"persist_failed:{target_path}:{exc}"

    return str(latest_path), str(history_path), ""


def _parse_bool_token(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    text = str(raw or "").strip().lower()
    if text in TRUTHY_VALUES:
        return True
    if text in FALSY_VALUES:
        return False
    return False


def _derive_parity_operation_scope(*, operation: str, surface_label: str) -> str:
    op = str(operation or "").strip().lower()
    label = str(surface_label or "").strip().lower()
    if op in {"scan", "inspection"} and label.endswith("_scan_probe"):
        return "scan_probe"
    if op:
        return f"operation:{op}"
    if label:
        return f"surface:{label}"
    return "default"


def _derive_required_contract_reason(
    *,
    required_contract: bool,
    operation: str,
    surface_label: str,
) -> str:
    if bool(required_contract):
        return "required_contract_detected"
    op = str(operation or "").strip().lower()
    label = str(surface_label or "").strip().lower()
    if op in {"scan", "inspection"} and label.endswith("_scan_probe"):
        return "scan_probe_optional_not_required"
    return "no_required_contract_detected"


def _row_has_required_current_round_evidence_gap(row: dict[str, Any]) -> bool:
    stale_reasons = {
        str(token).strip()
        for token in (row.get("stale_reasons") or [])
        if str(token).strip()
    }
    issue_tokens = {
        str(token).strip()
        for token in (row.get("payload_contract_issues") or [])
        if str(token).strip()
    }
    if REQUIRED_EVIDENCE_GAP_TOKEN in stale_reasons:
        return True
    for token in issue_tokens:
        if not token.startswith(STRICT_SKIP_NOT_ALLOWED_PREFIX):
            continue
        _, _, reason_csv = token.partition(":")
        reason_set = {item.strip() for item in reason_csv.split(",") if item.strip()}
        if REQUIRED_EVIDENCE_GAP_TOKEN in reason_set:
            return True
    return False


def _normalize_headstamp_projection_status(raw: str) -> tuple[str, bool]:
    token = str(raw or "").strip().upper()
    if token in {STATUS_PASS_REQUIRED, STATUS_FAIL_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED, STATUS_WARN_NON_BLOCKING}:
        required_contract = token in {STATUS_PASS_REQUIRED, STATUS_FAIL_REQUIRED, STATUS_WARN_NON_BLOCKING}
        return token, required_contract
    if token in {"NOT_APPLICABLE", "PASS_NOT_APPLICABLE"}:
        return STATUS_SKIPPED_NOT_REQUIRED, False
    if token:
        return STATUS_FAIL_REQUIRED, True
    return STATUS_SKIPPED_NOT_REQUIRED, False


def _build_headstamp_projection_payload(
    *,
    send_time_gate_status: str,
    operation: str,
    evidence_ref: str,
) -> dict[str, Any]:
    status, required_contract = _normalize_headstamp_projection_status(send_time_gate_status)
    normalized = str(send_time_gate_status or "").strip().upper()
    payload: dict[str, Any] = {
        "required_contract": required_contract,
        "send_time_gate_status": status,
        "reply_first_line_status": status,
        "error_code": "",
        "evidence_ref": str(evidence_ref or "").strip(),
        "stale_reasons": ["headstamp_projection_from_bundle_signal"],
        "auto_required_signal": False,
    }
    if normalized and normalized not in {
        STATUS_PASS_REQUIRED,
        STATUS_FAIL_REQUIRED,
        STATUS_SKIPPED_NOT_REQUIRED,
        STATUS_WARN_NON_BLOCKING,
        "NOT_APPLICABLE",
        "PASS_NOT_APPLICABLE",
    }:
        payload["send_time_gate_status"] = STATUS_FAIL_REQUIRED
        payload["reply_first_line_status"] = STATUS_FAIL_REQUIRED
        payload["required_contract"] = True
        payload["error_code"] = ERR_ENTRY_CONTRACT
        payload["stale_reasons"] = [f"invalid_send_time_gate_status_token:{normalized}"]
        return payload

    if status == STATUS_FAIL_REQUIRED and not str(payload.get("error_code", "")).strip():
        # Canonical headstamp family when upstream status is explicit fail but no detailed code is provided.
        payload["error_code"] = "IP-HDSTAMP-003"
    if status == STATUS_WARN_NON_BLOCKING:
        payload["stale_reasons"].append("headstamp_warn_non_blocking_projection")
    if status == STATUS_SKIPPED_NOT_REQUIRED:
        payload["stale_reasons"].append("headstamp_pre_send_gate_not_applicable_for_surface")
    op = str(operation or "").strip().lower()
    if status == STATUS_SKIPPED_NOT_REQUIRED and op in HEADSTAMP_EVIDENCE_REQUIRED_OPERATIONS:
        payload["stale_reasons"].append("strict_operation_without_reply_evidence_projection")
    return payload


def _resolve_input_path(repo_root: Path, raw_path: str) -> Path:
    value = str(raw_path or "").strip()
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()


def _resolve_skill_path_active_repo_root_binding(
    *,
    catalog_path: str,
    identity_id: str,
    active_repo_root_arg: str,
    repo_root: Path,
) -> tuple[str, str, str]:
    explicit = str(active_repo_root_arg or "").strip()
    if explicit:
        return str(Path(explicit).expanduser().resolve()), "cli_explicit", ""
    try:
        pack_path, _task_path = resolve_pack_and_task(
            Path(catalog_path).expanduser().resolve(),
            identity_id,
        )
        resolved_root, resolved_source = derive_active_repo_root(
            catalog_path=Path(catalog_path).expanduser().resolve(),
            pack_path=pack_path,
            cwd=repo_root,
        )
        return str(resolved_root), str(resolved_source), ""
    except Exception as exc:
        fallback_root = repo_root.parent.resolve()
        return str(fallback_root), "bundle_repo_root_fallback", f"skill_path_active_repo_root_resolve_failed:{exc}"


def _file_contains_token(path: Path, token: str, *, max_chars: int = 400_000) -> bool:
    target = str(token or "").strip()
    if not target:
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return target in text[:max_chars]


def _extract_bundle_id_from_text(raw: str) -> str:
    patterns = (
        r"cross_verification_bundle_id\s*[:=]\s*([^\s,;]+)",
        r"bundle_id\s*[:=]\s*([^\s,;]+)",
        r"evidence_bundle_id\s*[:=]\s*([^\s,;]+)",
    )
    for pat in patterns:
        m = re.search(pat, raw, flags=re.IGNORECASE)
        if m:
            return str(m.group(1) or "").strip()
    return ""


def _resolve_cross_verification_bundle_context(
    *,
    pack_path: Path,
    run_id: str,
) -> tuple[str, str, str]:
    feedback_root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if not feedback_root.exists():
        return "", "", "cross_verification_bundle_feedback_root_missing"

    patterns = (
        "outbox-to-protocol/*cross*verification*.*",
        "outbox-to-protocol/*xverify*.*",
        "outbox-to-protocol/FEEDBACK_BATCH_*.md",
        "**/*cross*verification*.*",
        "**/*intake*evidence*.*",
        "**/*quorum*.*",
    )
    seen: set[str] = set()
    candidates: list[Path] = []
    for pattern in patterns:
        for hit in feedback_root.glob(pattern):
            if not hit.is_file():
                continue
            resolved = hit.resolve()
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(resolved)
    if not candidates:
        return "", "", "cross_verification_bundle_candidates_missing"

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    selected = candidates[0]
    run_token = str(run_id or "").strip()
    if run_token:
        filtered = [
            p for p in candidates if run_token in p.name or _file_contains_token(p, run_token)
        ]
        if filtered:
            selected = filtered[0]

    bundle_id = selected.stem
    try:
        raw = selected.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        raw = ""
    extracted = _extract_bundle_id_from_text(raw)
    if extracted:
        bundle_id = extracted
    return str(selected), str(bundle_id or "").strip(), "bundle_runtime_feedback_latest"


def _is_strict_no_trim_operation(operation: str) -> bool:
    return str(operation or "").strip().lower() in set(STRICT_NO_TRIM_OPERATIONS_DEFAULT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run required gate bundle from mapping single-source registry.")
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--identity-id", required=True)
    parser.add_argument("--operation", default="validate")
    parser.add_argument("--repo-catalog", default="")
    parser.add_argument("--active-repo-root", default="")
    parser.add_argument("--contract-mapping", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--report-selected-path", default="")
    parser.add_argument("--session-id", default="")
    parser.add_argument("--send-time-gate-status", default="")
    parser.add_argument("--reply-text", default="")
    parser.add_argument("--reply-file", default="")
    parser.add_argument("--reply-log", default="")
    parser.add_argument("--reply-transport-ref", default="")
    parser.add_argument("--reply-outlet-guard-applied", action="store_true")
    parser.add_argument(
        "--outlet-bypass-detected",
        nargs="?",
        const="true",
        default="",
        help="explicit outlet bypass flag (true/false). bare flag implies true.",
    )
    parser.add_argument("--surface-label", default="")
    parser.add_argument(
        "--wrapper-dispatch-token",
        default="",
        help="required wrapper dispatch token for host_ingress_wrapper strict operations",
    )
    parser.add_argument("--wrapper-proof-json", default="", help="signed dynamic wrapper proof payload (json)")
    parser.add_argument("--wrapper-proof-signature", default="", help="HMAC signature for wrapper proof payload")
    parser.add_argument("--target-name", default="", help="optional single target probe via bundle registry lineage")
    parser.add_argument("--gate-profile", default="", help="optional gate profile key for requirement selection")
    parser.add_argument(
        "--gate-profile-file",
        default=DEFAULT_GATE_PROFILE_FILE,
        help="gate profile mapping yaml for layer-targeted gate selection",
    )
    parser.add_argument("--out", default="", help="optional path to persist JSON receipt")
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--actor-id", default="")
    parser.add_argument("--resolved-work-layer", default="")
    parser.add_argument("--resolved-source-layer", default="")
    parser.add_argument("--lock-state", default="")
    parser.add_argument("--final-emit-contract-status", default="")
    parser.add_argument("--final-emit-policy-mode", default="")
    parser.add_argument("--final-emit-schema-status", default="")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    repo_catalog_path = (
        Path(str(args.repo_catalog or "")).expanduser().resolve()
        if str(args.repo_catalog or "").strip()
        else (repo_root / "identity" / "catalog" / "identities.yaml").resolve()
    )
    mapping_path = Path(args.contract_mapping).expanduser().resolve() if str(args.contract_mapping or "").strip() else _resolve_default_contract_mapping(repo_root)
    mapping_alias_error = ""
    if mapping_path.name.endswith(".current.yaml"):
        resolved_mapping_path, _active_mapping_file, mapping_alias_error = _resolve_current_yaml_alias(
            repo_root, str(mapping_path)
        )
        if not mapping_alias_error:
            mapping_path = resolved_mapping_path
    (
        effective_requirement_order,
        effective_target_name_by_requirement,
        effective_status_field_by_target,
        effective_wiring_errors,
    ) = _build_effective_requirement_maps(repo_root=repo_root, mapping_path=mapping_path)
    monotonic_policy_by_target, monotonic_policy_file, monotonic_policy_errors = _load_monotonic_policy_by_target(
        repo_root=repo_root
    )
    effective_requirement_by_target = {
        target: requirement
        for requirement, target in effective_target_name_by_requirement.items()
    }
    known_requirement_keys = set(effective_target_name_by_requirement.keys())
    target_name = str(args.target_name or "").strip()
    gate_profile = str(args.gate_profile or "").strip() or DEFAULT_GATE_PROFILE_NAME
    gate_profile_file = str(args.gate_profile_file or "").strip() or DEFAULT_GATE_PROFILE_FILE
    operation = str(args.operation or "").strip()
    operation_normalized = operation.lower()
    gate_profile_entry_file = _resolve_input_path(repo_root, gate_profile_file)
    canonical_gate_profile_entry_file = (repo_root / DEFAULT_GATE_PROFILE_FILE).resolve()
    gate_profile_selection, gate_profile_resolved_file, gate_profile_errors = _load_gate_profile_selection(
        repo_root=repo_root,
        profile_file=gate_profile_file,
        profile_name=gate_profile,
        operation=operation,
        resolved_work_layer=str(args.resolved_work_layer or "").strip(),
        default_requirement_order=effective_requirement_order,
        known_requirement_keys=known_requirement_keys,
    )
    requirement_keys = (
        gate_profile_selection.requirement_keys
        if isinstance(gate_profile_selection, GateProfileSelection)
        else effective_requirement_order
    )
    mapping_errors: list[str] = []
    if mapping_alias_error:
        mapping_errors.append(f"contract_mapping_alias_resolution_failed:{mapping_alias_error}")
    mapping_errors.extend(effective_wiring_errors)
    mapping_errors.extend(gate_profile_errors)
    mapping_errors.extend(monotonic_policy_errors)
    if _is_strict_no_trim_operation(operation_normalized) and gate_profile_entry_file != canonical_gate_profile_entry_file:
        mapping_errors.append(
            "gate_profile_file_non_canonical_for_strict_operation:"
            f"{gate_profile_file}:expected={DEFAULT_GATE_PROFILE_FILE}"
        )
    if target_name:
        target_key = effective_requirement_by_target.get(target_name, "")
        if not target_key:
            mapping_errors.append(f"unknown_target_name:{target_name}")
            requirement_keys = ()
        else:
            if (
                isinstance(gate_profile_selection, GateProfileSelection)
                and gate_profile_selection.profile_mode != "full"
                and target_key not in set(gate_profile_selection.requirement_keys)
            ):
                requirement_keys = ()
            else:
                requirement_keys = (target_key,)

    specs, spec_errors = _load_validator_specs(
        mapping_path,
        requirement_keys,
        target_name_by_requirement=effective_target_name_by_requirement,
    )
    mapping_errors.extend(spec_errors)
    result_rows: list[dict[str, Any]] = []
    failure_count = 0
    row_contract_error_count = 0
    surface_label = str(args.surface_label or "").strip() or str(args.operation or "").strip().replace("-", "_") or "unknown_surface"
    wrapper_dispatch_token = str(args.wrapper_dispatch_token or "").strip()
    wrapper_proof_json = str(args.wrapper_proof_json or "").strip()
    wrapper_proof_signature = str(args.wrapper_proof_signature or "").strip()
    run_id_binding = str(args.run_id or "").strip()
    report_selected_path = str(args.report_selected_path or "").strip()
    actor_id = str(args.actor_id or "").strip()
    session_id = str(args.session_id or "").strip()
    send_time_gate_status = str(args.send_time_gate_status or "").strip()
    reply_text = str(args.reply_text or "").strip()
    reply_file = str(args.reply_file or "").strip()
    reply_log = str(args.reply_log or "").strip()
    reply_transport_ref = str(args.reply_transport_ref or "").strip()
    explicit_reply_guard = bool(args.reply_outlet_guard_applied)
    outlet_bypass_detected = _parse_bool_token(args.outlet_bypass_detected)
    reply_outlet_guard_applied = explicit_reply_guard or (not outlet_bypass_detected)

    if mapping_errors:
        failure_count += len(mapping_errors)
    if not run_id_binding:
        mapping_errors.append("run_id_binding_missing")
        failure_count += 1

    cross_verification_bundle_path = ""
    cross_verification_bundle_id = ""
    cross_verification_bundle_source = ""
    cross_verification_bundle_error = ""
    try:
        pack_path_for_bundle, _task_path = resolve_pack_and_task(
            Path(args.catalog).expanduser().resolve(),
            str(args.identity_id),
        )
        (
            cross_verification_bundle_path,
            cross_verification_bundle_id,
            cross_verification_bundle_source,
        ) = _resolve_cross_verification_bundle_context(
            pack_path=pack_path_for_bundle,
            run_id=run_id_binding,
        )
    except Exception as exc:
        cross_verification_bundle_error = f"cross_verification_bundle_context_resolve_failed:{exc}"
    if cross_verification_bundle_error:
        mapping_errors.append(cross_verification_bundle_error)
        failure_count += 1

    wrapper_policy, wrapper_policy_errors = _resolve_wrapper_enforcement_policy(
        catalog_path=str(args.catalog),
        identity_id=str(args.identity_id),
    )
    mapping_errors.extend(wrapper_policy_errors)
    if wrapper_policy_errors:
        failure_count += len(wrapper_policy_errors)

    (
        skill_path_active_repo_root,
        skill_path_active_repo_root_source,
        skill_path_active_repo_root_error,
    ) = _resolve_skill_path_active_repo_root_binding(
        catalog_path=str(args.catalog),
        identity_id=str(args.identity_id),
        active_repo_root_arg=str(args.active_repo_root or ""),
        repo_root=repo_root,
    )
    if skill_path_active_repo_root_error:
        mapping_errors.append(skill_path_active_repo_root_error)
        failure_count += 1

    strict_operation = _is_strict_no_trim_operation(operation_normalized)
    wrapper_required_surface_label = str(
        wrapper_policy.get("required_surface_label", DEFAULT_HOST_WRAPPER_SURFACE_LABEL)
    ).strip()
    wrapper_required_dispatch_token = str(
        wrapper_policy.get("required_dispatch_token", DEFAULT_REQUIRED_WRAPPER_DISPATCH_TOKEN)
    ).strip()
    wrapper_proof_required = bool(wrapper_policy.get("proof_required", True))
    wrapper_proof_max_age_seconds = max(
        _safe_int(wrapper_policy.get("proof_max_age_seconds"), default=WRAPPER_PROOF_MAX_AGE_SECONDS_DEFAULT),
        1,
    )
    host_dispatch_mode = str(wrapper_policy.get("host_dispatch_mode", "wrapper_only")).strip().lower()
    wrapper_surface_required = _operation_requires_wrapper_provenance(
        operation=operation_normalized,
        host_dispatch_mode=host_dispatch_mode,
        wrapper_policy=wrapper_policy,
    )
    wrapper_dispatch_required = wrapper_surface_required
    wrapper_surface_ok = (not wrapper_surface_required) or surface_label == wrapper_required_surface_label
    wrapper_surface_status = (
        STATUS_SKIPPED_NOT_REQUIRED
        if not wrapper_surface_required
        else (STATUS_PASS_REQUIRED if wrapper_surface_ok else STATUS_FAIL_REQUIRED)
    )
    if wrapper_surface_required and not wrapper_surface_ok:
        mapping_errors.append(
            "wrapper_surface_not_configured_wrapper:"
            f"{surface_label}:expected={wrapper_required_surface_label}"
        )
        failure_count += 1
    wrapper_dispatch_ok = (
        not wrapper_dispatch_required
        or wrapper_dispatch_token == wrapper_required_dispatch_token
    )
    wrapper_dispatch_token_status = (
        STATUS_SKIPPED_NOT_REQUIRED
        if not wrapper_dispatch_required
        else (STATUS_PASS_REQUIRED if wrapper_dispatch_ok else STATUS_FAIL_REQUIRED)
    )
    if wrapper_dispatch_required and not wrapper_required_dispatch_token:
        mapping_errors.append("wrapper_dispatch_token_expected_missing_from_contract")
        failure_count += 1
    if wrapper_dispatch_required and not wrapper_dispatch_ok:
        mapping_errors.append("wrapper_dispatch_token_missing_or_invalid")
        failure_count += 1
    wrapper_dispatch_proof_status = STATUS_SKIPPED_NOT_REQUIRED
    wrapper_dispatch_proof_nonce = ""
    wrapper_dispatch_proof_issued_at_epoch = 0
    wrapper_dispatch_proof_sha256 = ""
    wrapper_dispatch_proof_required = bool(wrapper_dispatch_required and wrapper_proof_required)
    wrapper_parent_attestation_required = bool(wrapper_dispatch_required)
    wrapper_parent_attestation_status = STATUS_SKIPPED_NOT_REQUIRED
    wrapper_parent_attestation_ppid = int(os.getppid())
    wrapper_parent_attestation_expected_path = str(
        wrapper_policy.get("expected_ingress_wrapper_path", "")
    ).strip()
    wrapper_parent_attestation_command_sha256 = ""
    if wrapper_dispatch_proof_required:
        proof_ok, proof_errors, proof_details = _validate_wrapper_dispatch_proof(
            proof_json=wrapper_proof_json,
            proof_signature=wrapper_proof_signature,
            dispatch_secret=str(wrapper_policy.get("proof_signing_secret", "")).strip(),
            catalog_path=str(args.catalog),
            identity_id=str(args.identity_id),
            operation=operation_normalized,
            run_id_binding=run_id_binding,
            actor_id=actor_id,
            session_id=session_id,
            resolved_work_layer=str(args.resolved_work_layer or "").strip(),
            resolved_source_layer=str(args.resolved_source_layer or "").strip(),
            surface_label=surface_label,
            max_age_seconds=wrapper_proof_max_age_seconds,
        )
        wrapper_dispatch_proof_nonce = str(proof_details.get("wrapper_dispatch_proof_nonce", "")).strip()
        wrapper_dispatch_proof_issued_at_epoch = _safe_int(
            proof_details.get("wrapper_dispatch_proof_issued_at_epoch"),
            default=0,
        )
        wrapper_dispatch_proof_sha256 = str(proof_details.get("wrapper_dispatch_proof_sha256", "")).strip()
        wrapper_dispatch_proof_status = STATUS_PASS_REQUIRED if proof_ok else STATUS_FAIL_REQUIRED
        if not proof_ok:
            mapping_errors.extend(proof_errors)
            failure_count += len(proof_errors)
    if wrapper_parent_attestation_required:
        (
            wrapper_parent_ok,
            wrapper_parent_errors,
            wrapper_parent_details,
        ) = _validate_wrapper_parent_attestation(
            expected_wrapper_path=wrapper_parent_attestation_expected_path,
        )
        wrapper_parent_attestation_ppid = _safe_int(
            wrapper_parent_details.get("wrapper_parent_attestation_ppid"),
            default=wrapper_parent_attestation_ppid,
        )
        wrapper_parent_attestation_command_sha256 = str(
            wrapper_parent_details.get("wrapper_parent_attestation_command_sha256", "")
        ).strip()
        wrapper_parent_attestation_status = (
            STATUS_PASS_REQUIRED if wrapper_parent_ok else STATUS_FAIL_REQUIRED
        )
        if not wrapper_parent_ok:
            mapping_errors.extend(wrapper_parent_errors)
            failure_count += len(wrapper_parent_errors)

    for spec in specs:
        validator_path = Path(spec.script_path)
        if not validator_path.is_absolute():
            validator_path = (repo_root / validator_path).resolve()
        cmd = [
            sys.executable,
            str(validator_path),
            "--catalog",
            str(args.catalog),
            "--identity-id",
            str(args.identity_id),
            "--operation",
            str(args.operation),
            "--json-only",
        ]
        cmd.extend(spec.fixed_args)
        if (
            repo_catalog_path.exists()
            and _script_accepts_flag(spec.script_path, flag="--repo-catalog", repo_root=repo_root)
        ):
            cmd.extend(["--repo-catalog", str(repo_catalog_path)])
        if spec.target_name == "prompt_import_executable_coupling":
            if actor_id:
                cmd.extend(["--actor-id", actor_id])
            if session_id:
                cmd.extend(["--session-id", session_id])
        if spec.target_name == "headstamp_pre_send_hard_gate":
            if actor_id:
                cmd.extend(["--actor-id", actor_id])
            if session_id:
                cmd.extend(["--session-id", session_id])
            if reply_text:
                cmd.extend(["--reply-text", reply_text])
            if reply_file:
                cmd.extend(["--reply-file", reply_file])
            if reply_log:
                cmd.extend(["--reply-log", reply_log])
            if reply_transport_ref:
                cmd.extend(["--reply-transport-ref", reply_transport_ref])
            if reply_outlet_guard_applied:
                cmd.append("--reply-outlet-guard-applied")
            if str(args.final_emit_policy_mode or "").strip():
                cmd.extend(["--final-emit-policy-mode", str(args.final_emit_policy_mode).strip()])
            if str(args.final_emit_schema_status or "").strip():
                cmd.extend(["--final-emit-schema-status", str(args.final_emit_schema_status).strip()])

        if spec.target_name == "skill_path_integrity":
            cmd.extend(["--active-repo-root", skill_path_active_repo_root])

        if spec.target_name in {
            "multimodal_plugin_enforcement",
            "run_id_report_selection",
        }:
            cmd.extend(["--run-id", run_id_binding])
            if report_selected_path:
                if spec.target_name == "run_id_report_selection":
                    cmd.extend(["--report", report_selected_path])
                else:
                    cmd.extend(["--report-selected-path", report_selected_path])
        if spec.target_name == "reasoning_loop_failclose_enforcement":
            if run_id_binding and report_selected_path:
                cmd.extend(["--run-id", run_id_binding])
            if report_selected_path:
                cmd.extend(["--report-selected-path", report_selected_path])
        if spec.target_name in {"cross_verification_tracks", "intake_evidence_quorum"}:
            if cross_verification_bundle_path:
                cmd.extend(["--bundle", cross_verification_bundle_path])
            if cross_verification_bundle_id:
                cmd.extend(["--bundle-id", cross_verification_bundle_id])

        # RQ-032: if no concrete reply evidence is provided, project the upstream
        # gate signal instead of forcing a synthetic re-validation pass.
        if spec.target_name == "headstamp_pre_send_hard_gate" and not any([reply_text, reply_file, reply_log]):
            payload = _build_headstamp_projection_payload(
                send_time_gate_status=send_time_gate_status,
                operation=str(args.operation),
                evidence_ref=reply_transport_ref,
            )
            rc = 0 if str(payload.get("send_time_gate_status", "")).strip().upper() != STATUS_FAIL_REQUIRED else 1
            err = ""
        else:
            rc, out, err = _run(cmd, cwd=repo_root)
            payload = _parse_payload(out)
        status_value, status_field = _classify_status(
            target_name=spec.target_name,
            rc=rc,
            payload=payload,
            status_field_by_target=effective_status_field_by_target,
        )
        required_contract = bool(payload.get("required_contract", False))
        payload_contract_issues = _validate_row_payload_contract(
            payload=payload,
            status_field=status_field,
            target_name=spec.target_name,
            operation=str(args.operation),
            required_contract=required_contract,
        )
        if rc != 0:
            payload_contract_issues.append("validator_rc_nonzero")
        if payload_contract_issues:
            status_value = STATUS_FAIL_REQUIRED

        default_monotonic_policy = monotonic_policy_by_target.get(MONOTONIC_POLICY_DEFAULT_TARGET, {})
        monotonic_policy = monotonic_policy_by_target.get(spec.target_name, default_monotonic_policy)
        strict_skip_policy = str(monotonic_policy.get("strict_skip_policy", "")).strip().lower()
        strict_skip_allowed_reasons = {
            str(token).strip()
            for token in (monotonic_policy.get("strict_skip_allowed_reasons") or set())
            if str(token).strip()
        }
        if operation_normalized in PRE_EXECUTION_CURRENT_ROUND_SKIP_OPERATIONS:
            strict_skip_allowed_reasons.update(PRE_EXECUTION_CURRENT_ROUND_SKIP_ALLOWED_REASONS)
        runtime_status_field = STRICT_SKIP_RUNTIME_STATUS_FIELD_BY_TARGET.get(spec.target_name, "")
        runtime_status_value = str(payload.get(runtime_status_field, "")).strip().upper()
        row_status_skipped = status_value == STATUS_SKIPPED_NOT_REQUIRED
        runtime_status_skipped = bool(runtime_status_field) and runtime_status_value == STATUS_SKIPPED_NOT_REQUIRED
        if (
            required_contract
            and _is_strict_no_trim_operation(operation_normalized)
            and strict_skip_policy in STRICT_SKIP_BLOCKING_POLICIES
            and (row_status_skipped or runtime_status_skipped)
        ):
            stale_reason_tokens = {
                str(token).strip()
                for token in (payload.get("stale_reasons") or [])
                if str(token).strip()
            }
            if not stale_reason_tokens:
                payload_contract_issues.append("strict_skip_not_allowed:missing_stale_reason")
            else:
                disallowed_reasons = sorted(stale_reason_tokens - strict_skip_allowed_reasons)
                if disallowed_reasons:
                    payload_contract_issues.append(
                        "strict_skip_not_allowed:" + ",".join(disallowed_reasons)
                    )
        if payload_contract_issues:
            status_value = STATUS_FAIL_REQUIRED
            row_contract_error_count += 1
        error_code = _extract_error_code(payload, err)
        if payload_contract_issues and not error_code:
            error_code = ERR_ENTRY_REQUIRED

        if status_value == STATUS_FAIL_REQUIRED:
            failure_count += 1
        elif status_value == STATUS_FAIL_OPTIONAL and required_contract:
            failure_count += 1

        result_rows.append(
            {
                "requirement_key": spec.requirement_key,
                "target_name": spec.target_name,
                "validator": spec.script_path,
                "fixed_args": list(spec.fixed_args),
                "validator_rc": rc,
                "status_field": status_field,
                "status": status_value,
                "error_code": error_code,
                "required_contract": required_contract,
                "auto_required_signal": bool(payload.get("auto_required_signal", False)),
                "surface_label": surface_label,
                "stale_reasons": list(payload.get("stale_reasons") or []),
                "evidence_ref": str(payload.get("evidence_ref", "")).strip(),
                "cross_verification_bundle_path": (
                    cross_verification_bundle_path
                    if spec.target_name in {"cross_verification_tracks", "intake_evidence_quorum"}
                    else ""
                ),
                "cross_verification_bundle_id": (
                    cross_verification_bundle_id
                    if spec.target_name in {"cross_verification_tracks", "intake_evidence_quorum"}
                    else ""
                ),
                "cross_verification_bundle_source": (
                    cross_verification_bundle_source
                    if spec.target_name in {"cross_verification_tracks", "intake_evidence_quorum"}
                    else ""
                ),
                "payload_contract_issues": payload_contract_issues,
                "monotonic_policy": {
                    "strict_skip_policy": strict_skip_policy,
                    "strict_skip_allowed_reasons": sorted(strict_skip_allowed_reasons),
                    "runtime_status_field": runtime_status_field,
                    "runtime_status_value": runtime_status_value,
                    "row_status_value": status_value,
                    "row_status_skipped": row_status_skipped,
                    "runtime_status_skipped": runtime_status_skipped,
                    "strict_skip_default_applied": bool(monotonic_policy.get("strict_skip_default_applied", False)),
                },
                "payload": payload,
                "stderr_tail": (err.splitlines()[-1] if err else ""),
            }
        )

    missing_targets = [
        effective_target_name_by_requirement[key]
        for key in requirement_keys
        if effective_target_name_by_requirement.get(key) not in {row.get("target_name") for row in result_rows}
    ]
    if missing_targets:
        failure_count += len(missing_targets)

    required_contract_any = any(bool(row.get("required_contract", False)) for row in result_rows)
    failed_required_rows = [
        row for row in result_rows if str(row.get("status", "")).upper() == STATUS_FAIL_REQUIRED
    ]
    failed_required_contract_count = len(failed_required_rows)
    failed_required_requirement_keys = [
        str(row.get("requirement_key", "")).strip()
        for row in failed_required_rows
        if str(row.get("requirement_key", "")).strip()
    ]
    failed_required_target_names = [
        str(row.get("target_name", "")).strip()
        for row in failed_required_rows
        if str(row.get("target_name", "")).strip()
    ]
    required_current_round_evidence_gap_rows = [
        row for row in failed_required_rows if _row_has_required_current_round_evidence_gap(row)
    ]
    required_current_round_evidence_gap_keys = [
        str(row.get("requirement_key", "")).strip()
        for row in required_current_round_evidence_gap_rows
        if str(row.get("requirement_key", "")).strip()
    ]
    required_current_round_evidence_gap_targets = [
        str(row.get("target_name", "")).strip()
        for row in required_current_round_evidence_gap_rows
        if str(row.get("target_name", "")).strip()
    ]

    if mapping_errors or missing_targets:
        bundle_status = STATUS_FAIL_REQUIRED
        error_code = ERR_ENTRY_CONTRACT
    elif required_current_round_evidence_gap_rows:
        bundle_status = STATUS_FAIL_REQUIRED
        error_code = ERR_ENTRY_REQUIRED_EVIDENCE_GAP
    elif row_contract_error_count > 0:
        bundle_status = STATUS_FAIL_REQUIRED
        error_code = ERR_ENTRY_CONTRACT
    elif failed_required_contract_count > 0:
        bundle_status = STATUS_FAIL_REQUIRED
        error_code = ERR_ENTRY_REQUIRED
    else:
        bundle_status = STATUS_PASS_REQUIRED
        error_code = ""

    parity_operation_scope = _derive_parity_operation_scope(
        operation=str(args.operation or "").strip(),
        surface_label=surface_label,
    )
    required_contract_reason = _derive_required_contract_reason(
        required_contract=required_contract_any,
        operation=str(args.operation or "").strip(),
        surface_label=surface_label,
    )

    payload: dict[str, Any] = {
        "bundle_contract_id": BUNDLE_CONTRACT_ID,
        "bundle_key": BUNDLE_KEY,
        "bundle_status": bundle_status,
        "error_code": error_code,
        "identity_id": str(args.identity_id),
        "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        "operation": str(args.operation),
        "contract_mapping": str(mapping_path),
        "gate_profile": gate_profile,
        "gate_profile_mode": (
            gate_profile_selection.profile_mode
            if isinstance(gate_profile_selection, GateProfileSelection)
            else ""
        ),
        "gate_profile_file": gate_profile_file,
        "gate_profile_entry_file": str(gate_profile_entry_file),
        "gate_profile_resolved_file": str(gate_profile_resolved_file),
        "canonical_gate_profile_entry_file": str(canonical_gate_profile_entry_file),
        "gate_profile_requirement_count": len(requirement_keys),
        "gate_profile_requirement_keys": list(requirement_keys),
        "monotonic_policy_file": str(monotonic_policy_file),
        "mapping_errors": mapping_errors,
        "missing_targets": missing_targets,
        "results": result_rows,
        "surface_label": surface_label,
        "skill_path_active_repo_root": skill_path_active_repo_root,
        "skill_path_active_repo_root_source": skill_path_active_repo_root_source,
        "wrapper_surface_required_label": wrapper_required_surface_label,
        "wrapper_required_surface_status": str(
            wrapper_policy.get("required_wrapper_surface_status", STATUS_PASS_REQUIRED)
        ).strip().upper(),
        "wrapper_required_dispatch_status": str(
            wrapper_policy.get("required_wrapper_dispatch_status", STATUS_PASS_REQUIRED)
        ).strip().upper(),
        "wrapper_expected_ingress_wrapper_path": str(
            wrapper_policy.get("expected_ingress_wrapper_path", "")
        ).strip(),
        "wrapper_host_dispatch_mode": host_dispatch_mode,
        "wrapper_policy_strict_operations": sorted(
            _as_lower_str_set(wrapper_policy.get("strict_operations"))
        ),
        "wrapper_policy_light_operations": sorted(
            _as_lower_str_set(wrapper_policy.get("light_operations"))
        ),
        "wrapper_policy_allow_upgrade_only": bool(wrapper_policy.get("allow_upgrade_only", True)),
        "wrapper_proof_signer_mode": str(wrapper_policy.get("proof_signer_mode", "")).strip(),
        "wrapper_proof_signer_secret_env": str(wrapper_policy.get("proof_signer_secret_env", "")).strip(),
        "wrapper_proof_signing_key_path": str(wrapper_policy.get("proof_signing_key_path", "")).strip(),
        "wrapper_dispatch_required": wrapper_dispatch_required,
        "wrapper_surface_status": wrapper_surface_status,
        "wrapper_dispatch_token_status": wrapper_dispatch_token_status,
        "wrapper_dispatch_token_expected": wrapper_required_dispatch_token,
        "wrapper_dispatch_proof_required": wrapper_dispatch_proof_required,
        "wrapper_dispatch_proof_status": wrapper_dispatch_proof_status,
        "wrapper_dispatch_proof_nonce": wrapper_dispatch_proof_nonce,
        "wrapper_dispatch_proof_issued_at_epoch": wrapper_dispatch_proof_issued_at_epoch,
        "wrapper_dispatch_proof_sha256": wrapper_dispatch_proof_sha256,
        "wrapper_parent_attestation_required": wrapper_parent_attestation_required,
        "wrapper_parent_attestation_status": wrapper_parent_attestation_status,
        "wrapper_parent_attestation_ppid": wrapper_parent_attestation_ppid,
        "wrapper_parent_attestation_expected_path": wrapper_parent_attestation_expected_path,
        "wrapper_parent_attestation_command_sha256": wrapper_parent_attestation_command_sha256,
        "run_id_binding": run_id_binding,
        "session_id": session_id,
        "report_selected_path": report_selected_path,
        "cross_verification_bundle_path": cross_verification_bundle_path,
        "cross_verification_bundle_id": cross_verification_bundle_id,
        "cross_verification_bundle_source": cross_verification_bundle_source,
        "cross_verification_bundle_error": cross_verification_bundle_error,
        "actor_id": str(args.actor_id or "").strip(),
        "resolved_work_layer": str(args.resolved_work_layer or "").strip(),
        "resolved_source_layer": str(args.resolved_source_layer or "").strip(),
        "lock_state": str(args.lock_state or "").strip(),
        "required_contract": required_contract_any,
        "required_contract_reason": required_contract_reason,
        "failed_required_contract_count": failed_required_contract_count,
        "failed_required_requirement_keys": failed_required_requirement_keys,
        "failed_required_target_names": failed_required_target_names,
        "required_current_round_evidence_gap_count": len(required_current_round_evidence_gap_rows),
        "required_current_round_evidence_gap_requirement_keys": required_current_round_evidence_gap_keys,
        "required_current_round_evidence_gap_target_names": required_current_round_evidence_gap_targets,
        "required_current_round_evidence_gap_detected": bool(required_current_round_evidence_gap_rows),
        "parity_operation_scope": parity_operation_scope,
        "send_time_gate_status": str(args.send_time_gate_status or "").strip().upper(),
        "outlet_bypass_detected": _parse_bool_token(args.outlet_bypass_detected),
        "final_emit_contract_status": str(args.final_emit_contract_status or "").strip().upper(),
        "final_emit_policy_mode": str(args.final_emit_policy_mode or "").strip(),
        "final_emit_schema_status": str(args.final_emit_schema_status or "").strip().upper(),
        "row_contract_error_count": row_contract_error_count,
        "protocol_unique_entry_receipt_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_unique_entry_receipt_path": "",
        "protocol_unique_entry_receipt_history_path": "",
    }

    receipt_path = ""
    receipt_history_path = ""
    receipt_error = ""
    receipt_required = (
        _is_strict_no_trim_operation(operation_normalized)
        or wrapper_surface_required
    )
    if receipt_required:
        receipt_path, receipt_history_path, receipt_error = _persist_unique_entry_receipt(
            catalog_path=str(args.catalog),
            identity_id=str(args.identity_id),
            operation=str(args.operation),
            run_id_binding=run_id_binding,
            actor_id=str(args.actor_id or "").strip(),
            session_id=session_id,
            surface_label=surface_label,
            payload=payload,
        )
        if receipt_error:
            payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_path"] = ""
            payload["protocol_unique_entry_receipt_history_path"] = ""
            entry_issue = f"entry_receipt_persist_failed:{receipt_error}"
            if entry_issue not in mapping_errors:
                mapping_errors.append(entry_issue)
            payload["mapping_errors"] = mapping_errors
            payload["bundle_status"] = STATUS_FAIL_REQUIRED
            if PRIVILEGE_ESCALATION_ERROR_CODE in str(receipt_error):
                payload["error_code"] = PRIVILEGE_ESCALATION_ERROR_CODE
            else:
                payload["error_code"] = ERR_ENTRY_REQUIRED
            bundle_status = STATUS_FAIL_REQUIRED
            if PRIVILEGE_ESCALATION_ERROR_CODE in str(receipt_error):
                error_code = PRIVILEGE_ESCALATION_ERROR_CODE
            else:
                error_code = ERR_ENTRY_REQUIRED
        else:
            if str(payload.get("bundle_status", "")).strip().upper() == STATUS_PASS_REQUIRED:
                payload["protocol_unique_entry_receipt_status"] = STATUS_PASS_REQUIRED
            else:
                payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_path"] = receipt_path
            payload["protocol_unique_entry_receipt_history_path"] = receipt_history_path

    if target_name:
        if not result_rows and not mapping_errors:
            target_status_field = effective_status_field_by_target.get(target_name, "status")
            target_payload = {
                target_status_field: STATUS_SKIPPED_NOT_REQUIRED,
                "required_contract": False,
                "auto_required_signal": False,
                "error_code": "",
                "stale_reasons": ["target_excluded_by_gate_profile"],
                "bundle_contract_id": BUNDLE_CONTRACT_ID,
                "bundle_key": BUNDLE_KEY,
                "bundle_target_name": target_name,
                "surface_label": surface_label,
                "run_id_binding": run_id_binding,
                "report_selected_path": report_selected_path,
                "gate_profile": gate_profile,
                "gate_profile_mode": (
                    gate_profile_selection.profile_mode
                    if isinstance(gate_profile_selection, GateProfileSelection)
                    else ""
                ),
                "gate_profile_file": gate_profile_file,
                "gate_profile_entry_file": str(gate_profile_entry_file),
                "gate_profile_resolved_file": str(gate_profile_resolved_file),
                "canonical_gate_profile_entry_file": str(canonical_gate_profile_entry_file),
                "gate_profile_requirement_count": len(requirement_keys),
                "gate_profile_requirement_keys": list(requirement_keys),
                "actor_id": str(args.actor_id or "").strip(),
                "resolved_work_layer": str(args.resolved_work_layer or "").strip(),
                "resolved_source_layer": str(args.resolved_source_layer or "").strip(),
                "lock_state": str(args.lock_state or "").strip(),
                "parity_operation_scope": parity_operation_scope,
                "required_contract_reason": "scan_probe_profile_filtered_not_required",
                "send_time_gate_status": str(args.send_time_gate_status or "").strip().upper(),
                "outlet_bypass_detected": _parse_bool_token(args.outlet_bypass_detected),
                "final_emit_contract_status": str(args.final_emit_contract_status or "").strip().upper(),
                "final_emit_policy_mode": str(args.final_emit_policy_mode or "").strip(),
                "final_emit_schema_status": str(args.final_emit_schema_status or "").strip().upper(),
                "protocol_unique_entry_receipt_status": payload.get("protocol_unique_entry_receipt_status", ""),
                "protocol_unique_entry_receipt_path": payload.get("protocol_unique_entry_receipt_path", ""),
                "protocol_unique_entry_receipt_history_path": payload.get(
                    "protocol_unique_entry_receipt_history_path", ""
                ),
            }
            if str(args.out or "").strip():
                _write_payload_out(str(args.out), target_payload)
            if args.json_only:
                print(json.dumps(target_payload, ensure_ascii=False))
            else:
                print(json.dumps(target_payload, ensure_ascii=False, indent=2))
            return 0

        target_row = next((row for row in result_rows if row.get("target_name") == target_name), None)
        if not target_row:
            stale_reasons = ["bundle_target_missing"]
            if mapping_errors:
                stale_reasons = ["bundle_entry_contract_failed"] + [f"mapping_error:{x}" for x in mapping_errors]
            target_status_field = effective_status_field_by_target.get(target_name, "status")
            target_payload = {
                target_status_field: STATUS_FAIL_REQUIRED,
                "error_code": ERR_ENTRY_CONTRACT,
                "stale_reasons": stale_reasons,
                "bundle_contract_id": BUNDLE_CONTRACT_ID,
                "bundle_key": BUNDLE_KEY,
                "bundle_target_name": target_name,
                "mapping_errors": mapping_errors,
                "gate_profile": gate_profile,
                "gate_profile_mode": (
                    gate_profile_selection.profile_mode
                    if isinstance(gate_profile_selection, GateProfileSelection)
                    else ""
                ),
                "gate_profile_file": gate_profile_file,
                "gate_profile_entry_file": str(gate_profile_entry_file),
                "gate_profile_resolved_file": str(gate_profile_resolved_file),
                "canonical_gate_profile_entry_file": str(canonical_gate_profile_entry_file),
                "gate_profile_requirement_count": len(requirement_keys),
                "gate_profile_requirement_keys": list(requirement_keys),
                "actor_id": str(args.actor_id or "").strip(),
                "resolved_work_layer": str(args.resolved_work_layer or "").strip(),
                "resolved_source_layer": str(args.resolved_source_layer or "").strip(),
                "lock_state": str(args.lock_state or "").strip(),
                "protocol_unique_entry_receipt_status": payload.get("protocol_unique_entry_receipt_status", ""),
                "protocol_unique_entry_receipt_path": payload.get("protocol_unique_entry_receipt_path", ""),
                "protocol_unique_entry_receipt_history_path": payload.get(
                    "protocol_unique_entry_receipt_history_path", ""
                ),
            }
            if args.json_only:
                print(json.dumps(target_payload, ensure_ascii=False))
            else:
                print(json.dumps(target_payload, ensure_ascii=False, indent=2))
            return 1

        target_payload = dict(
            target_row.get("payload") if isinstance(target_row.get("payload"), dict) else {}
        )
        target_status_field = effective_status_field_by_target[target_name]
        target_payload.setdefault(target_status_field, target_row.get("status", STATUS_FAIL_REQUIRED))
        target_payload.setdefault("required_contract", bool(target_row.get("required_contract", False)))
        target_payload.setdefault("auto_required_signal", bool(target_row.get("auto_required_signal", False)))
        target_payload.setdefault("stale_reasons", list(target_row.get("stale_reasons") or []))
        target_payload.setdefault("evidence_ref", str(target_row.get("evidence_ref", "")))
        if not str(target_payload.get("error_code", "")).strip() and str(target_row.get("error_code", "")).strip():
            target_payload["error_code"] = target_row.get("error_code", "")
        target_payload.setdefault("bundle_contract_id", BUNDLE_CONTRACT_ID)
        target_payload.setdefault("bundle_key", BUNDLE_KEY)
        target_payload.setdefault("bundle_target_name", target_name)
        target_payload.setdefault("gate_profile", gate_profile)
        target_payload.setdefault(
            "gate_profile_mode",
            gate_profile_selection.profile_mode
            if isinstance(gate_profile_selection, GateProfileSelection)
            else "",
        )
        target_payload.setdefault("gate_profile_file", gate_profile_file)
        target_payload.setdefault("gate_profile_entry_file", str(gate_profile_entry_file))
        target_payload.setdefault("gate_profile_resolved_file", str(gate_profile_resolved_file))
        target_payload.setdefault("canonical_gate_profile_entry_file", str(canonical_gate_profile_entry_file))
        target_payload.setdefault("gate_profile_requirement_count", len(requirement_keys))
        target_payload.setdefault("gate_profile_requirement_keys", list(requirement_keys))
        target_payload.setdefault("surface_label", surface_label)
        target_payload.setdefault("run_id_binding", run_id_binding)
        target_payload.setdefault("report_selected_path", report_selected_path)
        target_payload.setdefault("actor_id", str(args.actor_id or "").strip())
        target_payload.setdefault("resolved_work_layer", str(args.resolved_work_layer or "").strip())
        target_payload.setdefault("resolved_source_layer", str(args.resolved_source_layer or "").strip())
        target_payload.setdefault("lock_state", str(args.lock_state or "").strip())
        target_payload.setdefault("parity_operation_scope", parity_operation_scope)
        target_payload.setdefault(
            "required_contract_reason",
            _derive_required_contract_reason(
                required_contract=bool(target_payload.get("required_contract", False)),
                operation=str(args.operation or "").strip(),
                surface_label=surface_label,
            ),
        )
        target_payload.setdefault("send_time_gate_status", str(args.send_time_gate_status or "").strip().upper())
        target_payload.setdefault("outlet_bypass_detected", _parse_bool_token(args.outlet_bypass_detected))
        target_payload.setdefault("final_emit_contract_status", str(args.final_emit_contract_status or "").strip().upper())
        target_payload.setdefault("final_emit_policy_mode", str(args.final_emit_policy_mode or "").strip())
        target_payload.setdefault("final_emit_schema_status", str(args.final_emit_schema_status or "").strip().upper())
        target_payload.setdefault("protocol_unique_entry_receipt_status", payload.get("protocol_unique_entry_receipt_status", ""))
        target_payload.setdefault("protocol_unique_entry_receipt_path", payload.get("protocol_unique_entry_receipt_path", ""))
        target_payload.setdefault(
            "protocol_unique_entry_receipt_history_path",
            payload.get("protocol_unique_entry_receipt_history_path", ""),
        )
        if bundle_status == STATUS_FAIL_REQUIRED:
            target_payload[target_status_field] = STATUS_FAIL_REQUIRED
            if not str(target_payload.get("error_code", "")).strip():
                target_payload["error_code"] = error_code or ERR_ENTRY_CONTRACT
            stale = list(target_payload.get("stale_reasons") or [])
            if "bundle_entry_contract_failed" not in stale:
                stale.append("bundle_entry_contract_failed")
            target_payload["stale_reasons"] = stale
        if str(args.out or "").strip():
            _write_payload_out(str(args.out), target_payload)
        if args.json_only:
            print(json.dumps(target_payload, ensure_ascii=False))
        else:
            print(json.dumps(target_payload, ensure_ascii=False, indent=2))
        return 1 if str(target_payload.get(target_status_field, "")).upper() == STATUS_FAIL_REQUIRED else 0

    if str(args.out or "").strip():
        _write_payload_out(str(args.out), payload)
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[BUNDLE] {BUNDLE_KEY} status={bundle_status} failed_required_contract_count={failed_required_contract_count} "
            f"mapping_errors={len(mapping_errors)} missing_targets={len(missing_targets)}"
        )
        for row in result_rows:
            print(
                f"[BUNDLE] {row['target_name']}: status={row['status']} rc={row['validator_rc']} "
                f"required_contract={row['required_contract']} error_code={row['error_code'] or '-'}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 1 if bundle_status == STATUS_FAIL_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
