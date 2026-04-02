#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "control_plane_lane_registry.v1"
CURRENT_SCHEMA_VERSION = "control_plane_lane_registry.current.v1"
CONTRACT_ID = "control_plane_protocol_feedback_instance_state_runner_hardening"
CLASSIFICATION = "existing_surface_alignment"
ACTIVE_LANE_ID = CONTRACT_ID
RECEIPT_SCHEMA_VERSION = "control_plane_receipt.v1"
FAIL_CLOSE_TOKEN = "control_plane_protocol_feedback_instance_state_runner_hardening_execution_contract_not_machine_authoritative"
ADMITTED_DELTA_ONLY = [
    "protocol_feedback_instance_state_runner_contract_only",
    "protocol_feedback_validator_probe_surface_reuse_only",
    "protocol_feedback_live_closure_state_admissibility_only",
    "stage_equality_target_redefined_to_machine_authoritative_necessity_subset_only",
    "no_absolute_host_path_literals_in_target_executable_surfaces",
    "no_reopen_of_control_plane_lane_registration_transaction_only",
]
VALIDATOR_COMMAND = "TMPDIR=$PWD/.tmp python3 scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py --json-only"
PROBE_COMMAND = "TMPDIR=$PWD/.tmp bash scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh"
VALIDATOR_EXPECTED_STATUS = "PASS_REQUIRED"
PROBE_EXPECTED_STATUS = "PASS"
EXPECTED_TERMINAL_STATUS = "closure_done"
DEFAULT_CURRENT_REGISTRY_REL = Path("identity/protocol/mappings/control-plane-lane-registry.current.yaml")
DEFAULT_VERSIONED_REGISTRY_REL = Path("identity/protocol/mappings/control-plane-lane-registry.v1.yaml")
EXPECTED_FIXED_WRITE_SET = [
    "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md",
    "identity/protocol/mappings/control-plane-lane-registry.v1.yaml",
    "scripts/control_plane_lane_registry_common.py",
    "scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py",
    "scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh",
]
EXPECTED_ROLE_BINDINGS = {
    "architect": "base-repo-architect",
    "executor": "base-repo-closure-orchestrator",
    "auditor": "base-repo-audit-expert-v3",
    "office": "office-ops-expert",
}
EXPECTED_ALLOWED_ACTIONS = [
    "run_validator",
    "run_probe",
    "stage_and_commit",
    "emit_blocker_receipt",
    "emit_fail_close_token",
]
EXPECTED_EXECUTABLE_SURFACES = [
    "scripts/validate_protocol_feedback_bootstrap_ready.py",
    "scripts/validate_protocol_feedback_inbox_channel.py",
    "scripts/validate_protocol_feedback_reply_channel.py",
    "scripts/validate_protocol_feedback_sidecar_contract.py",
    "scripts/validate_protocol_feedback_ssot_archival.py",
    "scripts/validate_sidecar_cwd_parity.py",
    "scripts/validate_identity_state_consistency.py",
    "scripts/protocol_feedback_lane_common.py",
    "scripts/protocol_feedback_contract_common.py",
    "scripts/ci/run_protocol_feedback_sidecar_contract_probes_ci.sh",
    "scripts/ci/run_protocol_feedback_ssot_archival_probes_ci.sh",
    "scripts/ci/run_sidecar_cwd_parity_probes_ci.sh",
]
FORBIDDEN_HOST_PATH_LITERAL = "/Users/yangxi"
PROHIBITED_RUNTIME_LITERAL_PATTERNS = {
    "concrete_run_token": re.compile(r"run:[A-Za-z0-9._:-]+"),
    "concrete_actor_id": re.compile(r"assistant:[A-Za-z0-9._-]+"),
}


@dataclass(frozen=True)
class RegistryBundle:
    repo_root: Path
    current_registry: Path
    versioned_registry: Path
    current_doc: dict[str, Any]
    registry_doc: dict[str, Any]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def emit(payload: dict[str, Any], *, json_only: bool = False) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml document at {path} is not a mapping")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    path.write_text(text, encoding="utf-8")


def resolve_registry_bundle(registry_current_override: str | None = None) -> RegistryBundle:
    root = repo_root()
    current_registry = (Path(registry_current_override).resolve() if registry_current_override else (root / DEFAULT_CURRENT_REGISTRY_REL).resolve())
    current_doc = load_yaml(current_registry)
    active_file = str(current_doc.get("active_file", DEFAULT_VERSIONED_REGISTRY_REL.as_posix()))
    active_path = Path(active_file)
    candidates = []
    if active_path.is_absolute():
        candidates.append(active_path)
    else:
        candidates.append((current_registry.parent / active_path).resolve())
        candidates.append((root / active_path).resolve())
    versioned_registry = next((candidate for candidate in candidates if candidate.exists()), None)
    if versioned_registry is None:
        raise FileNotFoundError(f"active registry file does not resolve from {current_registry}: {active_file}")
    registry_doc = load_yaml(versioned_registry)
    return RegistryBundle(
        repo_root=root,
        current_registry=current_registry,
        versioned_registry=versioned_registry,
        current_doc=current_doc,
        registry_doc=registry_doc,
    )


def get_lane(registry_doc: dict[str, Any], lane_id: str = ACTIVE_LANE_ID) -> dict[str, Any]:
    for lane in registry_doc.get("lanes", []):
        if lane.get("lane_id") == lane_id:
            return lane
    raise KeyError(f"lane not found: {lane_id}")


def git_stdout(args: list[str], *, cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def git_top_level(root: Path) -> Path:
    return Path(git_stdout(["git", "rev-parse", "--show-toplevel"], cwd=root)).resolve()


def commit_resolves(commit_id: str, *, cwd: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit_id}^{{commit}}"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def ensure_registration_transaction_execution_context(bundle: RegistryBundle) -> tuple[bool, dict[str, Any]]:
    cwd_ok = Path.cwd().resolve() == bundle.repo_root.resolve()
    git_top_ok = git_top_level(bundle.repo_root) == bundle.repo_root.resolve()
    detail = {
        "cwd": str(Path.cwd().resolve()),
        "repo_root": str(bundle.repo_root.resolve()),
        "cwd_matches_repo_root": cwd_ok,
        "git_top_level": str(git_top_level(bundle.repo_root)),
        "git_top_matches_repo_root": git_top_ok,
    }
    return cwd_ok and git_top_ok, detail


def route_next_role(lane: dict[str, Any], *, status_override: str | None = None) -> dict[str, Any]:
    status = status_override or lane.get("status", "architect_ready")
    role_bindings = lane.get("role_bindings") or EXPECTED_ROLE_BINDINGS
    if status in {"architect_ready", "preflight_passed", "closure_running"}:
        role = "executor"
        suggested = "closure_running"
    elif status == "closure_done":
        role = "auditor"
        suggested = "audit_ready"
    elif status in {"accepted", "hold"}:
        role = "office"
        suggested = "hold"
    else:
        role = lane.get("next_role", "executor")
        suggested = status
    return {
        "role": role,
        "identity_id": role_bindings[role],
        "suggested_next_status": suggested,
    }


def check_forbidden_runtime_literals(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for token, pattern in PROHIBITED_RUNTIME_LITERAL_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{token}:{path.relative_to(repo_root()).as_posix()}")
    return failures


def validate_receipt(
    receipt: dict[str, Any],
    *,
    require_exact: bool,
    repo_root_path: Path,
) -> list[str]:
    failures: list[str] = []
    if receipt.get("receipt_schema_version") != RECEIPT_SCHEMA_VERSION:
        failures.append("receipt_schema_version_mismatch")
    staged_paths = receipt.get("staged_paths")
    if staged_paths != EXPECTED_FIXED_WRITE_SET:
        failures.append("staged_paths_not_exact_fixed_write_set")
    if require_exact and staged_paths != EXPECTED_FIXED_WRITE_SET:
        failures.append("staged_paths_escape_fixed_write_set")
    validator_status = ((receipt.get("validator_result") or {}).get("status"))
    if validator_status != VALIDATOR_EXPECTED_STATUS:
        failures.append("validator_status_not_exact")
    probe_status = ((receipt.get("probe_result") or {}).get("status"))
    if probe_status != PROBE_EXPECTED_STATUS:
        failures.append("probe_status_not_exact")
    observed_actions = receipt.get("observed_actions") or []
    if any(action not in EXPECTED_ALLOWED_ACTIONS for action in observed_actions):
        failures.append("forbidden_actions_after_scope_lock")
    commit_id = receipt.get("commit_id")
    if not commit_id or not commit_resolves(str(commit_id), cwd=repo_root_path):
        failures.append("protocol_feedback_instance_state_runner_hardening_commit_not_materialized")
    return failures


def canonical_package_paths(root: Path | None = None) -> list[Path]:
    base = root or repo_root()
    return [(base / rel).resolve() for rel in EXPECTED_FIXED_WRITE_SET]
