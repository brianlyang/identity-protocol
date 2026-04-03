#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "control_plane_lane_registry.v1"
CURRENT_SCHEMA_VERSION = "control_plane_lane_registry.current.v1"
OWNER_BINDING_SCHEMA_VERSION = "control_plane_owner_binding.v1"
OWNER_BINDING_CURRENT_SCHEMA_VERSION = "control_plane_owner_binding.current.v1"
OWNER_BINDING_TRUTH_CLASS = "owner_binding_overlay"
OWNER_BINDING_SCOPE = "repo_local"
OWNER_BINDING_RUNTIME_EVIDENCE_SURFACE = True
OWNER_BINDING_RUNTIME_EVIDENCE_CLASS = "concrete_identity_binding"
OWNER_BINDING_CANONICAL_REENTRY_POLICY = "fail_close"
OWNER_BINDING_POLICY = "receipt_scoped_runtime_evidence_only"
OWNER_BINDING_ACTIVE_PROFILE_ID = "control_plane_runtime_evidence_policy"
CONTRACT_ID = "control_plane_role_binding_overlay_hardening"
CLASSIFICATION = "existing_surface_alignment"
ACTIVE_LANE_ID = CONTRACT_ID
RECEIPT_SCHEMA_VERSION = "control_plane_receipt.v1"
FAIL_CLOSE_TOKEN = "control_plane_role_binding_overlay_hardening_not_machine_authoritative"
ADMITTED_DELTA_ONLY = [
    "canonical_role_law_owner_binding_overlay_split_only",
    "owner_binding_overlay_current_and_versioned_surface_only",
    "route_next_role_semantics_identity_resolution_split_only",
    "historical_control_plane_lane_compatibility_probe_only",
    "canonical_registry_deconcretizes_role_bindings_only",
    "no_reopen_of_control_plane_protocol_feedback_instance_state_runner_hardening",
]
VALIDATOR_COMMAND = "TMPDIR=$PWD/.tmp python3 scripts/validate_control_plane_role_binding_overlay_hardening.py --json-only"
PROBE_COMMAND = "TMPDIR=$PWD/.tmp bash scripts/ci/run_control_plane_role_binding_overlay_hardening_probes_ci.sh"
VALIDATOR_EXPECTED_STATUS = "PASS_REQUIRED"
PROBE_EXPECTED_STATUS = "PASS"
EXPECTED_TERMINAL_STATUS = "closure_done"
DEFAULT_CURRENT_REGISTRY_REL = Path("identity/protocol/mappings/control-plane-lane-registry.current.yaml")
DEFAULT_VERSIONED_REGISTRY_REL = Path("identity/protocol/mappings/control-plane-lane-registry.v1.yaml")
DEFAULT_OWNER_BINDING_CURRENT_REL = Path("identity/protocol/mappings/control-plane-owner-binding.current.yaml")
DEFAULT_OWNER_BINDING_VERSIONED_REL = Path("identity/protocol/mappings/control-plane-owner-binding.v1.yaml")
REGISTRATION_BOOTSTRAP_LANE_ID = "control_plane_lane_registration_transaction_bootstrap"
REGISTRATION_TRANSACTION_LANE_ID = "control_plane_lane_registration_transaction_only"
REGISTERED_TARGET_LANE_ID = "control_plane_protocol_feedback_instance_state_runner_hardening"
EXPECTED_FIXED_WRITE_SET = [
    "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md",
    "identity/protocol/mappings/control-plane-lane-registry.current.yaml",
    "identity/protocol/mappings/control-plane-lane-registry.v1.yaml",
    "identity/protocol/mappings/control-plane-owner-binding.current.yaml",
    "identity/protocol/mappings/control-plane-owner-binding.v1.yaml",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-post-closure-handoff-projection-drift.md",
    "scripts/control_plane_lane_registry_common.py",
    "scripts/control_plane_lane_render.py",
    "scripts/control_plane_lane_next.py",
    "scripts/control_plane_lane_ingest.py",
    "scripts/control_plane_lane_stream_guard.py",
    "scripts/validate_identity_control_plane_bootstrap_mvp.py",
    "scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh",
    "scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py",
    "scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh",
    "scripts/validate_control_plane_role_binding_overlay_hardening.py",
    "scripts/ci/run_control_plane_role_binding_overlay_hardening_probes_ci.sh",
]
REQUIRED_OWNER_BINDING_ROLES = (
    "architect",
    "executor",
    "auditor",
    "office",
)
EXPECTED_ALLOWED_ACTIONS = [
    "run_validator",
    "run_probe",
    "stage_and_commit",
    "emit_blocker_receipt",
    "emit_fail_close_token",
]
RUNTIME_ALLOWED_LITERAL_EXCEPTION_SURFACES = [
    "runtime_evidence_surfaces",
    "actor_session_store",
    "runtime_reports",
    "ci_probe_fixtures",
    "docs_examples",
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
HELPER_LITERAL_LOCK_IN_SURFACES = [
    "scripts/control_plane_lane_registry_common.py",
    "scripts/validate_identity_control_plane_bootstrap_mvp.py",
    "scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py",
    "scripts/validate_control_plane_role_binding_overlay_hardening.py",
    "scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh",
    "scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh",
    "scripts/ci/run_control_plane_role_binding_overlay_hardening_probes_ci.sh",
]
FORBIDDEN_HOST_PATH_PATTERN = re.compile(r"/Users/[^/\s]+(?:/[^\s]*)?")
PROHIBITED_RUNTIME_LITERAL_PATTERNS = {
    "concrete_run_token": re.compile(r"run:[A-Za-z0-9._:-]+"),
    "concrete_actor_id": re.compile(r"assistant:[A-Za-z0-9._-]+"),
}
HELPER_LITERAL_LOCK_IN_PATTERNS = {
    "concrete_role_binding_mapping_reentry": re.compile(r"\brole_to_identity_bindings\b"),
    "identity_resolver_reentry": re.compile(r"\bresolve_role_identity\s*\("),
    "identity_projection_get_reentry": re.compile(r"\.get\((['\"])identity_id\1\)"),
    "identity_projection_index_reentry": re.compile(r"\[(['\"])identity_id\1\]"),
    "render_overlay_key_reentry": re.compile(r"\[(['\"])owner_binding_overlay\1\]"),
    "overlay_exception_surface_reentry": re.compile(r"^\s*-\s*owner_binding_overlay\s*$", re.MULTILINE),
    "concrete_identity_literal_reentry": re.compile(r"\bbase-repo-[A-Za-z0-9._-]+\b"),
}


@dataclass(frozen=True)
class RegistryBundle:
    repo_root: Path
    current_registry: Path
    versioned_registry: Path
    current_doc: dict[str, Any]
    registry_doc: dict[str, Any]
    owner_binding_current: Path
    owner_binding_versioned: Path
    owner_binding_current_doc: dict[str, Any]
    owner_binding_doc: dict[str, Any]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def display_path(path: Path, root: Path | None = None) -> str:
    base = root or repo_root()
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


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


def _resolve_path_reference(base_file: Path, raw_ref: str | None, root: Path) -> Path:
    raw = str(raw_ref or "").strip()
    if not raw:
        raise ValueError(f"missing path reference relative to {base_file}")
    ref = Path(raw)
    if ref.is_absolute():
        return ref.resolve()
    base_candidate = (base_file.parent / ref).resolve()
    if base_candidate.exists():
        return base_candidate
    return (root / ref).resolve()


def _resolve_active_yaml(
    entry_path: Path,
    entry_doc: dict[str, Any],
    default_active_rel: Path,
    root: Path,
) -> tuple[Path, str, dict[str, Any]]:
    active_file = str(entry_doc.get("active_file", default_active_rel.as_posix()))
    active_path = _resolve_path_reference(entry_path, active_file, root)
    if not active_path.exists():
        raise FileNotFoundError(f"active yaml file does not resolve from {entry_path}: {active_file}")
    return active_path, active_file, load_yaml(active_path)


def resolve_registry_bundle(registry_current_override: str | None = None) -> RegistryBundle:
    root = repo_root()
    current_registry = (
        Path(registry_current_override).resolve()
        if registry_current_override
        else (root / DEFAULT_CURRENT_REGISTRY_REL).resolve()
    )
    current_doc = load_yaml(current_registry)
    versioned_registry, _active_file, registry_doc = _resolve_active_yaml(
        current_registry,
        current_doc,
        DEFAULT_VERSIONED_REGISTRY_REL,
        root,
    )
    owner_binding_ref = str(
        current_doc.get("owner_binding_file")
        or registry_doc.get("owner_binding_file")
        or DEFAULT_OWNER_BINDING_CURRENT_REL.as_posix()
    )
    owner_binding_current = _resolve_path_reference(current_registry, owner_binding_ref, root)
    if not owner_binding_current.exists():
        raise FileNotFoundError(
            f"owner binding current file does not resolve from {current_registry}: {owner_binding_ref}"
        )
    owner_binding_current_doc = load_yaml(owner_binding_current)
    owner_binding_versioned, _owner_active_file, owner_binding_doc = _resolve_active_yaml(
        owner_binding_current,
        owner_binding_current_doc,
        DEFAULT_OWNER_BINDING_VERSIONED_REL,
        root,
    )
    return RegistryBundle(
        repo_root=root,
        current_registry=current_registry,
        versioned_registry=versioned_registry,
        current_doc=current_doc,
        registry_doc=registry_doc,
        owner_binding_current=owner_binding_current,
        owner_binding_versioned=owner_binding_versioned,
        owner_binding_current_doc=owner_binding_current_doc,
        owner_binding_doc=owner_binding_doc,
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


def ensure_control_plane_execution_context(bundle: RegistryBundle) -> tuple[bool, dict[str, Any]]:
    cwd_ok = Path.cwd().resolve() == bundle.repo_root.resolve()
    git_top = git_top_level(bundle.repo_root)
    git_top_ok = git_top == bundle.repo_root.resolve()
    detail = {
        "cwd": str(Path.cwd().resolve()),
        "repo_root": str(bundle.repo_root.resolve()),
        "cwd_matches_repo_root": cwd_ok,
        "git_top_level": str(git_top),
        "git_top_matches_repo_root": git_top_ok,
    }
    return cwd_ok and git_top_ok, detail


def ensure_registration_transaction_execution_context(bundle: RegistryBundle) -> tuple[bool, dict[str, Any]]:
    return ensure_control_plane_execution_context(bundle)


def route_next_role_semantics(lane: dict[str, Any], *, status_override: str | None = None) -> dict[str, Any]:
    status = status_override or lane.get("status", "architect_ready")
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
        role = str(lane.get("next_role", "executor"))
        suggested = status
    return {
        "role": role,
        "suggested_next_status": suggested,
    }


def owner_binding_policy_issues(
    doc: Any,
    *,
    require_active_file: bool = False,
    require_required_roles: bool = False,
    require_runtime_roots: bool = False,
) -> list[str]:
    if not isinstance(doc, dict):
        return ["owner_binding_doc_not_mapping"]
    issues: list[str] = []
    expected_pairs = {
        "truth_class": OWNER_BINDING_TRUTH_CLASS,
        "scope": OWNER_BINDING_SCOPE,
        "portable": False,
        "runtime_evidence_surface": OWNER_BINDING_RUNTIME_EVIDENCE_SURFACE,
        "runtime_evidence_class": OWNER_BINDING_RUNTIME_EVIDENCE_CLASS,
        "canonical_reentry_policy": OWNER_BINDING_CANONICAL_REENTRY_POLICY,
        "binding_policy": OWNER_BINDING_POLICY,
        "active_binding_id": OWNER_BINDING_ACTIVE_PROFILE_ID,
    }
    for field_name, expected_value in expected_pairs.items():
        if doc.get(field_name) != expected_value:
            issues.append(f"{field_name}_mismatch")
    if require_active_file and not str(doc.get("active_file") or "").strip():
        issues.append("missing_active_file")
    if require_required_roles:
        if list(doc.get("required_roles") or []) != list(REQUIRED_OWNER_BINDING_ROLES):
            issues.append("required_roles_mismatch")
    if require_runtime_roots:
        roots = doc.get("admitted_runtime_evidence_roots")
        if not isinstance(roots, list) or not roots or any(
            not isinstance(item, str) or not item.strip() for item in roots
        ):
            issues.append("admitted_runtime_evidence_roots_invalid")
    if "role_to_identity_bindings" in doc:
        issues.append("concrete_role_bindings_reentered")
    return issues


def check_helper_literal_lock_in(
    paths: list[Path],
    *,
    root: Path | None = None,
) -> list[str]:
    hits: list[str] = []
    base = root or repo_root()
    for path in paths:
        if path.name == "control_plane_lane_registry_common.py":
            continue
        text = path.read_text(encoding="utf-8")
        for token, pattern in HELPER_LITERAL_LOCK_IN_PATTERNS.items():
            if pattern.search(text):
                hits.append(f"{token}:{display_path(path, base)}")
    return hits


def binding_surface_projection(bundle: RegistryBundle) -> dict[str, Any]:
    return {
        "resolution_status": "DEFERRED_TO_RUNTIME_EVIDENCE",
        "truth_class": bundle.owner_binding_current_doc.get("truth_class"),
        "scope": bundle.owner_binding_current_doc.get("scope"),
        "portable": bundle.owner_binding_current_doc.get("portable"),
        "binding_policy": bundle.owner_binding_current_doc.get("binding_policy"),
        "runtime_evidence_surface": bundle.owner_binding_current_doc.get("runtime_evidence_surface"),
        "runtime_evidence_class": bundle.owner_binding_current_doc.get("runtime_evidence_class"),
        "canonical_reentry_policy": bundle.owner_binding_current_doc.get("canonical_reentry_policy"),
        "current_file": display_path(bundle.owner_binding_current, bundle.repo_root),
        "versioned_file": display_path(bundle.owner_binding_versioned, bundle.repo_root),
        "active_binding_id": bundle.owner_binding_current_doc.get("active_binding_id"),
        "required_roles": list(bundle.owner_binding_doc.get("required_roles") or []),
        "admitted_runtime_evidence_roots": list(
            bundle.owner_binding_doc.get("admitted_runtime_evidence_roots") or []
        ),
    }


def route_next_role(
    lane: dict[str, Any],
    *,
    bundle: RegistryBundle | None = None,
    status_override: str | None = None,
) -> dict[str, Any]:
    semantics = route_next_role_semantics(lane, status_override=status_override)
    resolved_bundle = bundle or resolve_registry_bundle()
    return {
        **semantics,
        "binding_surface": binding_surface_projection(resolved_bundle),
    }


def check_forbidden_runtime_literals(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    root = repo_root()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for token, pattern in PROHIBITED_RUNTIME_LITERAL_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{token}:{display_path(path, root)}")
    return failures


def commit_not_materialized_token_for_lane(lane_id: str) -> str:
    if lane_id in {REGISTRATION_BOOTSTRAP_LANE_ID, REGISTRATION_TRANSACTION_LANE_ID}:
        return "registration_transaction_commit_not_materialized"
    if lane_id == REGISTERED_TARGET_LANE_ID:
        return "protocol_feedback_instance_state_runner_hardening_commit_not_materialized"
    if lane_id == ACTIVE_LANE_ID:
        return "role_binding_overlay_hardening_commit_not_materialized"
    return f"{lane_id}_commit_not_materialized"


def validate_receipt(
    receipt: dict[str, Any],
    *,
    lane: dict[str, Any],
    require_exact: bool,
    repo_root_path: Path,
) -> list[str]:
    failures: list[str] = []
    if receipt.get("receipt_schema_version") != RECEIPT_SCHEMA_VERSION:
        failures.append("receipt_schema_version_mismatch")
    expected_staged_paths = list(lane.get("exact_fixed_write_set") or EXPECTED_FIXED_WRITE_SET)
    staged_paths = receipt.get("staged_paths")
    if staged_paths != expected_staged_paths:
        failures.append("staged_paths_not_exact_fixed_write_set")
    if require_exact and staged_paths != expected_staged_paths:
        failures.append("staged_paths_escape_fixed_write_set")
    validator_status = ((receipt.get("validator_result") or {}).get("status"))
    if validator_status != str(lane.get("validator_expected_status") or VALIDATOR_EXPECTED_STATUS):
        failures.append("validator_status_not_exact")
    probe_status = ((receipt.get("probe_result") or {}).get("status"))
    if probe_status != str(lane.get("probe_expected_status") or PROBE_EXPECTED_STATUS):
        failures.append("probe_status_not_exact")
    observed_actions = receipt.get("observed_actions") or []
    allowed_actions = list(lane.get("scope_lock_allowed_actions") or EXPECTED_ALLOWED_ACTIONS)
    if any(action not in allowed_actions for action in observed_actions):
        failures.append("forbidden_actions_after_scope_lock")
    commit_id = receipt.get("commit_id")
    if not commit_id or not commit_resolves(str(commit_id), cwd=repo_root_path):
        failures.append(commit_not_materialized_token_for_lane(str(lane.get("lane_id") or ACTIVE_LANE_ID)))
    return failures


def canonical_package_paths(
    root: Path | None = None,
    *,
    lane: dict[str, Any] | None = None,
) -> list[Path]:
    base = root or repo_root()
    rels = list((lane or {}).get("exact_fixed_write_set") or EXPECTED_FIXED_WRITE_SET)
    return [(base / rel).resolve() for rel in rels]
