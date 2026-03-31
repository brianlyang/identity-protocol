#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from repo_root_resolution_common import resolve_protocol_repo_root

REGISTRY_SCHEMA_VERSION = "control_plane_lane_registry.v1"
RECEIPT_SCHEMA_VERSION = "control_plane_receipt.v1"
DEFAULT_CURRENT_REGISTRY_REL = "identity/protocol/mappings/control-plane-lane-registry.current.yaml"
DEFAULT_VERSIONED_REGISTRY_REL = "identity/protocol/mappings/control-plane-lane-registry.v1.yaml"
ACTIVE_LANE_ID = "identity_control_plane_bootstrap_mvp"
ACTIVE_CONTRACT_ID = "identity_control_plane_bootstrap_mvp"

REQUIRED_ROLE_BINDINGS: dict[str, str] = {
    "architect": "base-repo-architect",
    "executor": "base-repo-closure-orchestrator",
    "auditor": "base-repo-audit-expert-v3",
    "office": "office-ops-expert",
}

ALLOWED_EXECUTION_MODES = frozenset({"split_roles", "autonomous_reinforcement", "bootstrap_stream"})
ALLOWED_STATUSES = frozenset(
    {
        "pending_architect",
        "architect_ready",
        "preflight_passed",
        "closure_running",
        "closure_done",
        "audit_ready",
        "audit_passed",
        "office_ready",
        "accepted",
        "fail_closed",
        "hold",
    }
)
ALLOWED_POST_COMMIT_ACCEPTANCE_MODES = frozenset({"async_read_only_audit", "sync_audit_gate", "none"})
ALLOWED_WARN_PRESERVATION_POLICIES = frozenset({"forbid_warn", "preserve_non_blocking_warn", "allow_warn"})
ALLOWED_ENTRY_SURFACES = frozenset({"root", "middle", "consumer"})
ALLOWED_EXPECTED_RESULTS = frozenset({"PASS_REQUIRED", "PASS", "WARN_PRESERVED"})
ALLOWED_REWRITE_MARKERS = frozenset(
    {
        "owner_truth_overwrite",
        "root_semantic_redefinition",
        "whole_lane_reopen",
    }
)
SCOPE_LOCK_ALLOWED_NEXT_ACTIONS = (
    "mutate_fixed_write_set",
    "run_validator",
    "run_probe",
    "stage_fixed_write_set",
    "make_isolated_commit",
    "ingest_structured_receipt",
)
STREAM_GUARD_FORBIDDEN_ACTIONS = frozenset(
    {
        "reread",
        "recap",
        "re-anchor",
        "whole-family-reinspection",
        "upstream-law-rewrite",
        "issue-043-truth-writeback",
    }
)

CONTROL_PLANE_MVP_FIXED_WRITE_SET: list[str] = [
    "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md",
    "identity/protocol/mappings/control-plane-lane-registry.current.yaml",
    "identity/protocol/mappings/control-plane-lane-registry.v1.yaml",
    "scripts/control_plane_lane_registry_common.py",
    "scripts/control_plane_lane_preflight.py",
    "scripts/control_plane_lane_render.py",
    "scripts/control_plane_lane_ingest.py",
    "scripts/control_plane_lane_next.py",
    "scripts/control_plane_lane_stream_guard.py",
    "scripts/validate_identity_control_plane_bootstrap_mvp.py",
    "scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh",
]

ISSUE_043_INPUT_SURFACES: list[str] = [
    "docs/governance/identity-non-owner-machine-law-reinforcement-admission-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-non-owner-machine-law-reinforcement-admission.md",
    "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
    "docs/workbook/protocol-issue-register-v1.6.md",
]
ISSUE_043_CONSUMED_FIELDS: list[str] = [
    "accepted_upstream_law_ref",
    "issue_id",
    "contract_id",
    "law_ref",
    "reinforcement_entry_surface",
    "reinforcement_scope_status",
    "whole_lane_completion_target",
    "whole_lane_completion_status",
    "non_owner_reinforcement_status",
    "cross_layer_completion_admission_status",
    "canonical_owner_truth_preservation_status",
    "root_semantic_redefinition_status",
    "stale_reasons",
]
ISSUE_043_UPSTREAM_LAW_REF: dict[str, Any] = {
    "issue_id": "ISSUE-043",
    "accepted_commit": "fb7b5301626cb5d83504e9e94fe0e2cb9f787b7c",
    "contract_id": "non_owner_machine_law_reinforcement_admission_contract_v1",
    "law_ref": "machine_law_reinforcement_may_be_admitted_from_root_middle_or_consumer_surfaces_without_redefining_accepted_root_law",
    "consumed_fields": ISSUE_043_CONSUMED_FIELDS,
    "input_surfaces": ISSUE_043_INPUT_SURFACES,
}


@dataclass(frozen=True)
class RegistryBundle:
    repo_root: Path
    current_path: Path
    versioned_path: Path
    current_doc: dict[str, Any]
    registry_doc: dict[str, Any]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    token = _text(value).lower()
    return token in {"1", "true", "yes", "on"}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _path_token(value: Any, repo_root: Path) -> str:
    token = _text(value)
    if not token:
        return ""
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(repo_root.resolve()).as_posix()
        except Exception:
            return candidate.as_posix()
    return Path(token).as_posix()


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = [_text(item) for item in value]
    else:
        items = [_text(value)]
    return _dedupe([item for item in items if item])


def _path_list(value: Any, repo_root: Path) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = [_path_token(item, repo_root) for item in value]
    else:
        items = [_path_token(value, repo_root)]
    return _dedupe([item for item in items if item])


def _load_yaml(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"yaml root must be mapping: {path}")
    return doc


def _dump_yaml(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")


def resolve_repo_root(repo_root: str = "") -> Path:
    return resolve_protocol_repo_root(repo_root, start=Path.cwd())


def _resolve_current_path(repo_root: Path, current_registry: str = "") -> Path:
    token = _text(current_registry)
    if not token:
        return (repo_root / DEFAULT_CURRENT_REGISTRY_REL).resolve()
    path = Path(token).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (repo_root / token).resolve()


def _resolve_versioned_path(repo_root: Path, current_path: Path, active_file: str) -> Path:
    token = _text(active_file)
    if not token:
        raise ValueError("active_file_missing")
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    relative_to_current = (current_path.parent / token).resolve()
    if relative_to_current.exists():
        return relative_to_current
    return (repo_root / token).resolve()


def load_registry_bundle(*, repo_root: str = "", current_registry: str = "") -> RegistryBundle:
    resolved_repo_root = resolve_repo_root(repo_root)
    current_path = _resolve_current_path(resolved_repo_root, current_registry)
    current_doc = _load_yaml(current_path)
    versioned_path = _resolve_versioned_path(resolved_repo_root, current_path, _text(current_doc.get("active_file")))
    registry_doc = _load_yaml(versioned_path)
    return RegistryBundle(
        repo_root=resolved_repo_root,
        current_path=current_path,
        versioned_path=versioned_path,
        current_doc=current_doc,
        registry_doc=registry_doc,
    )


def normalize_role_bindings(bindings: Any) -> dict[str, str]:
    if not isinstance(bindings, dict):
        bindings = {}
    normalized = {role: _text(bindings.get(role) or REQUIRED_ROLE_BINDINGS[role]) for role in REQUIRED_ROLE_BINDINGS}
    missing = [role for role, identity_id in normalized.items() if not identity_id]
    if missing:
        raise ValueError(f"missing_role_bindings:{','.join(missing)}")
    return normalized


def normalize_upstream_law_ref(value: Any, repo_root: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    return {
        "issue_id": _text(value.get("issue_id")),
        "accepted_commit": _text(value.get("accepted_commit")),
        "contract_id": _text(value.get("contract_id")),
        "law_ref": _text(value.get("law_ref")),
        "consumed_fields": _string_list(value.get("consumed_fields")),
        "input_surfaces": _path_list(value.get("input_surfaces"), repo_root),
    }


def normalize_lane(lane_doc: dict[str, Any], *, repo_root: Path, registry_role_bindings: dict[str, str]) -> dict[str, Any]:
    lane_role_bindings = normalize_role_bindings(lane_doc.get("role_bindings") or registry_role_bindings)
    execution_mode = _text(lane_doc.get("execution_mode"))
    status = _text(lane_doc.get("status"))
    writer_role = _text(lane_doc.get("writer_role"))
    next_role = _text(lane_doc.get("next_role"))
    if execution_mode not in ALLOWED_EXECUTION_MODES:
        raise ValueError(f"invalid_execution_mode:{execution_mode}")
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"invalid_status:{status}")
    if writer_role not in lane_role_bindings:
        raise ValueError(f"invalid_writer_role:{writer_role}")
    if next_role and next_role not in lane_role_bindings:
        raise ValueError(f"invalid_next_role:{next_role}")
    allowed_entry_surfaces = _string_list(lane_doc.get("allowed_entry_surfaces"))
    if not allowed_entry_surfaces or any(surface not in ALLOWED_ENTRY_SURFACES for surface in allowed_entry_surfaces):
        raise ValueError(f"invalid_allowed_entry_surfaces:{allowed_entry_surfaces}")
    forbidden_rewrite_markers = _string_list(lane_doc.get("forbidden_rewrite_markers"))
    if not forbidden_rewrite_markers or any(marker not in ALLOWED_REWRITE_MARKERS for marker in forbidden_rewrite_markers):
        raise ValueError(f"invalid_forbidden_rewrite_markers:{forbidden_rewrite_markers}")
    validator_expected_status = _text(lane_doc.get("validator_expected_status"))
    probe_expected_status = _text(lane_doc.get("probe_expected_status"))
    if validator_expected_status not in ALLOWED_EXPECTED_RESULTS:
        raise ValueError(f"invalid_validator_expected_status:{validator_expected_status}")
    if probe_expected_status not in ALLOWED_EXPECTED_RESULTS:
        raise ValueError(f"invalid_probe_expected_status:{probe_expected_status}")
    expected_terminal_status = _text(lane_doc.get("expected_terminal_status"))
    if expected_terminal_status not in ALLOWED_STATUSES:
        raise ValueError(f"invalid_expected_terminal_status:{expected_terminal_status}")
    warn_preservation_policy = _text(lane_doc.get("warn_preservation_policy"))
    if warn_preservation_policy not in ALLOWED_WARN_PRESERVATION_POLICIES:
        raise ValueError(f"invalid_warn_preservation_policy:{warn_preservation_policy}")
    post_commit_acceptance_mode = _text(lane_doc.get("post_commit_acceptance_mode"))
    if post_commit_acceptance_mode not in ALLOWED_POST_COMMIT_ACCEPTANCE_MODES:
        raise ValueError(f"invalid_post_commit_acceptance_mode:{post_commit_acceptance_mode}")
    read_only_roles = _string_list(lane_doc.get("read_only_roles"))
    if any(role not in lane_role_bindings for role in read_only_roles):
        raise ValueError(f"invalid_read_only_roles:{read_only_roles}")
    return {
        "lane_id": _text(lane_doc.get("lane_id")),
        "classification": _text(lane_doc.get("classification")),
        "status": status,
        "active": _bool(lane_doc.get("active")),
        "execution_mode": execution_mode,
        "writer_role": writer_role,
        "read_only_roles": read_only_roles,
        "role_bindings": lane_role_bindings,
        "exact_fixed_write_set": _path_list(lane_doc.get("exact_fixed_write_set"), repo_root),
        "read_only_input_surfaces": _path_list(lane_doc.get("read_only_input_surfaces"), repo_root),
        "validator_command": _text(lane_doc.get("validator_command")),
        "probe_command": _text(lane_doc.get("probe_command")),
        "validator_expected_status": validator_expected_status,
        "probe_expected_status": probe_expected_status,
        "expected_terminal_status": expected_terminal_status,
        "warn_preservation_policy": warn_preservation_policy,
        "admitted_delta_only": _text(lane_doc.get("admitted_delta_only")),
        "fail_close_token": _text(lane_doc.get("fail_close_token")),
        "blocker_id": _text(lane_doc.get("blocker_id")),
        "next_role": next_role or writer_role,
        "accepted_upstream_law_ref": normalize_upstream_law_ref(lane_doc.get("accepted_upstream_law_ref"), repo_root),
        "allowed_entry_surfaces": allowed_entry_surfaces,
        "handoff_required": _bool(lane_doc.get("handoff_required")),
        "post_commit_acceptance_mode": post_commit_acceptance_mode,
        "forbidden_rewrite_markers": forbidden_rewrite_markers,
        "receipt_schema_version": _text(lane_doc.get("receipt_schema_version")) or RECEIPT_SCHEMA_VERSION,
    }


def normalize_registry_doc(doc: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    role_bindings = normalize_role_bindings(doc.get("role_bindings"))
    lanes = [normalize_lane(lane_doc, repo_root=repo_root, registry_role_bindings=role_bindings) for lane_doc in doc.get("lanes", [])]
    active_lane_id = _text(doc.get("active_lane_id"))
    if not active_lane_id:
        active_lanes = [lane["lane_id"] for lane in lanes if lane["active"]]
        active_lane_id = active_lanes[0] if len(active_lanes) == 1 else ""
    return {
        "schema_version": _text(doc.get("schema_version")),
        "contract_id": _text(doc.get("contract_id")),
        "classification": _text(doc.get("classification")),
        "receipt_schema_version": _text(doc.get("receipt_schema_version")) or RECEIPT_SCHEMA_VERSION,
        "active_lane_id": active_lane_id,
        "role_bindings": role_bindings,
        "lanes": lanes,
    }


def get_lane(registry_doc: dict[str, Any], lane_id: str = "") -> dict[str, Any]:
    resolved_lane_id = _text(lane_id) or _text(registry_doc.get("active_lane_id"))
    for lane in registry_doc.get("lanes", []):
        if _text(lane.get("lane_id")) == resolved_lane_id:
            return copy.deepcopy(lane)
    raise KeyError(f"lane_not_found:{resolved_lane_id}")


def replace_lane(registry_doc: dict[str, Any], updated_lane: dict[str, Any]) -> dict[str, Any]:
    lane_id = _text(updated_lane.get("lane_id"))
    cloned = copy.deepcopy(registry_doc)
    new_lanes: list[dict[str, Any]] = []
    replaced = False
    for lane in cloned.get("lanes", []):
        if _text(lane.get("lane_id")) == lane_id:
            new_lanes.append(copy.deepcopy(updated_lane))
            replaced = True
        else:
            new_lanes.append(copy.deepcopy(lane))
    if not replaced:
        raise KeyError(f"lane_not_found:{lane_id}")
    cloned["lanes"] = new_lanes
    return cloned


def write_registry_doc(bundle: RegistryBundle, registry_doc: dict[str, Any]) -> None:
    _dump_yaml(bundle.versioned_path, registry_doc)


def normalized_receipt_template() -> dict[str, Any]:
    return {
        "receipt_schema_version": RECEIPT_SCHEMA_VERSION,
        "validator_result": {"status": "", "details": []},
        "probe_result": {"status": "", "details": []},
        "staged_paths": [],
        "commit_id": "",
        "blocker_receipt": None,
        "fail_close_token": "",
        "warnings": [],
        "observed_actions": [],
        "normalized_receipt": {},
    }


def normalize_receipt(value: Any, *, repo_root: Path) -> dict[str, Any]:
    template = normalized_receipt_template()
    if isinstance(value, str):
        parsed = json.loads(value)
    elif isinstance(value, dict):
        parsed = value
    else:
        parsed = {}
    validator_result = parsed.get("validator_result") if isinstance(parsed.get("validator_result"), dict) else {}
    probe_result = parsed.get("probe_result") if isinstance(parsed.get("probe_result"), dict) else {}
    blocker_receipt = parsed.get("blocker_receipt")
    if blocker_receipt is not None and not isinstance(blocker_receipt, dict):
        blocker_receipt = {"reason": _text(blocker_receipt)}
    normalized = {
        "receipt_schema_version": _text(parsed.get("receipt_schema_version")) or RECEIPT_SCHEMA_VERSION,
        "validator_result": {
            "status": _text(validator_result.get("status")),
            "details": _string_list(validator_result.get("details")),
        },
        "probe_result": {
            "status": _text(probe_result.get("status")),
            "details": _string_list(probe_result.get("details")),
        },
        "staged_paths": _path_list(parsed.get("staged_paths"), repo_root),
        "commit_id": _text(parsed.get("commit_id")),
        "blocker_receipt": blocker_receipt,
        "fail_close_token": _text(parsed.get("fail_close_token")),
        "warnings": _string_list(parsed.get("warnings")),
        "observed_actions": _string_list(parsed.get("observed_actions")),
    }
    normalized["normalized_receipt"] = {
        "receipt_schema_version": normalized["receipt_schema_version"],
        "validator_result": normalized["validator_result"],
        "probe_result": normalized["probe_result"],
        "staged_paths": normalized["staged_paths"],
        "commit_id": normalized["commit_id"],
        "blocker_receipt": normalized["blocker_receipt"],
        "fail_close_token": normalized["fail_close_token"],
        "warnings": normalized["warnings"],
        "observed_actions": normalized["observed_actions"],
    }
    template.update(normalized)
    return template


def status_matches(expected: str, actual: str) -> bool:
    if expected == "PASS_REQUIRED":
        return actual == "PASS_REQUIRED"
    if expected == "PASS":
        return actual == "PASS"
    if expected == "WARN_PRESERVED":
        return actual in {"PASS_REQUIRED", "PASS", "WARN_PRESERVED"}
    return False


def warnings_allowed(lane: dict[str, Any], receipt: dict[str, Any]) -> bool:
    warnings = receipt.get("warnings") or []
    if not warnings:
        return True
    return _text(lane.get("warn_preservation_policy")) in {"preserve_non_blocking_warn", "allow_warn"}


def route_next_role(lane: dict[str, Any], status: str | None = None) -> dict[str, Any]:
    current_status = _text(status) or _text(lane.get("status"))
    role: str | None = None
    suggested_next_status = current_status
    if current_status == "pending_architect":
        role = "architect"
        suggested_next_status = "architect_ready"
    elif current_status == "architect_ready":
        role = _text(lane.get("writer_role"))
        suggested_next_status = "preflight_passed"
    elif current_status in {"preflight_passed", "closure_running"}:
        role = _text(lane.get("writer_role"))
        suggested_next_status = "closure_done"
    elif current_status == "closure_done":
        if _text(lane.get("post_commit_acceptance_mode")) == "none":
            role = "office"
            suggested_next_status = "accepted"
        else:
            role = "auditor"
            suggested_next_status = "audit_ready"
    elif current_status == "audit_ready":
        role = "auditor"
        suggested_next_status = "audit_passed"
    elif current_status == "audit_passed":
        role = "office"
        suggested_next_status = "office_ready"
    elif current_status == "office_ready":
        role = "office"
        suggested_next_status = "accepted"
    identity_id = lane.get("role_bindings", {}).get(role) if role else None
    return {
        "role": role,
        "identity_id": identity_id,
        "suggested_next_status": suggested_next_status,
    }


def stream_guard_result(
    lane: dict[str, Any],
    receipt: dict[str, Any],
    *,
    require_exact: bool = False,
    scope_locked: bool = True,
) -> dict[str, Any]:
    failures: list[str] = []
    fixed_write_set = lane.get("exact_fixed_write_set", [])
    staged_paths = receipt.get("staged_paths", [])
    read_only_surfaces = set(lane.get("read_only_input_surfaces", []))
    read_only_surfaces.update((lane.get("accepted_upstream_law_ref") or {}).get("input_surfaces", []))
    if scope_locked:
        forbidden_hits = [action for action in receipt.get("observed_actions", []) if action in STREAM_GUARD_FORBIDDEN_ACTIONS]
        if forbidden_hits:
            failures.append(f"forbidden_actions_after_scope_lock:{','.join(forbidden_hits)}")
    if any(path not in fixed_write_set for path in staged_paths):
        failures.append("staged_paths_escape_fixed_write_set")
    if any(path in read_only_surfaces for path in staged_paths):
        failures.append("read_only_surface_write_attempt")
    if require_exact and staged_paths and set(staged_paths) != set(fixed_write_set):
        failures.append("staged_paths_not_exact_fixed_write_set")
    return {
        "status": "FAIL_REQUIRED" if failures else "PASS_REQUIRED",
        "scope_lock_status": "LOCKED" if scope_locked else "UNLOCKED",
        "failure_tokens": failures,
        "normalized_receipt": receipt.get("normalized_receipt") or normalized_receipt_template()["normalized_receipt"],
    }


def classify_receipt_outcome(lane: dict[str, Any], receipt: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    current_status = _text(lane.get("status"))
    if receipt.get("fail_close_token"):
        return "fail_closed", ["fail_close_token_present"]
    if receipt.get("blocker_receipt"):
        return "hold", ["blocker_receipt_present"]
    if current_status in {"closure_done", "audit_ready"}:
        if receipt.get("commit_id"):
            reasons.append("audit_receipt_must_not_include_commit_id")
        if not receipt.get("validator_result", {}).get("status"):
            reasons.append("audit_receipt_missing_validator_status")
        if reasons:
            return "fail_closed", reasons
        return "audit_passed", []
    if current_status in {"audit_passed", "office_ready"}:
        return _text(lane.get("expected_terminal_status")), []
    if not status_matches(_text(lane.get("validator_expected_status")), _text(receipt.get("validator_result", {}).get("status"))):
        reasons.append("validator_status_mismatch")
    if not status_matches(_text(lane.get("probe_expected_status")), _text(receipt.get("probe_result", {}).get("status"))):
        reasons.append("probe_status_mismatch")
    if not warnings_allowed(lane, receipt):
        reasons.append("warnings_not_admitted")
    if receipt.get("commit_id"):
        if set(receipt.get("staged_paths", [])) != set(lane.get("exact_fixed_write_set", [])):
            reasons.append("commit_requires_exact_fixed_write_set")
        return ("fail_closed", reasons) if reasons else ("closure_done", [])
    if receipt.get("staged_paths") and any(path not in lane.get("exact_fixed_write_set", []) for path in receipt.get("staged_paths", [])):
        reasons.append("staged_paths_escape_fixed_write_set")
    return ("fail_closed", reasons) if reasons else ("closure_running", [])


def load_json_file(path: str) -> dict[str, Any]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"json root must be object: {path}")
    return doc


def emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))
        return
    print(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
