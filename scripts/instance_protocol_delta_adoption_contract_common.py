#!/usr/bin/env python3
"""Shared constants for instance protocol delta adoption validation."""

from __future__ import annotations

from pathlib import Path

ISSUE_ID = "ISSUE-044"
LANE_ID = "instance_protocol_delta_adoption_contract_v1"
ABSORBED_LAW_ID = "scope_locked_mutation_phase_runtime_enforcement_contract_v1"
ABSORBED_PROTOCOL_DELTA_COMMIT = "f616889"
ABSORBED_PROTOCOL_DELTA_SUBJECT = (
    "scope locked mutation phase runtime enforcement adopted into consumer-facing "
    "instance protocol delta adoption surfaces"
)
GOVERNANCE_DOC = (
    "docs/governance/identity-instance-protocol-delta-adoption-governance-v1.6.x.md"
)
REVIEW_DOC = (
    "docs/review/"
    "protocol-remediation-audit-ledger-v1.6.x-instance-protocol-delta-adoption.md"
)
STATE_PATH = ".identity/instance_protocol_delta_adoption_state.json"
FALLBACK_PATH = ".identity/fallback-notes/instance_protocol_delta_adoption.md"
POLICY_PATH = ".identity/policy/instance_protocol_delta_adoption.md"
FIXED_WRITE_SET = (
    GOVERNANCE_DOC,
    REVIEW_DOC,
    "scripts/instance_protocol_delta_adoption_contract_common.py",
    "scripts/validate_instance_protocol_delta_adoption.py",
    "scripts/ci/run_instance_protocol_delta_adoption_probes_ci.sh",
)
CAPABILITY_FAMILIES = (
    "instance_protocol_delta_adoption",
    "scope_locked_mutation_phase_runtime_enforcement",
)
RELEVANT_PROTOCOL_DELTA_LAWS = (ABSORBED_LAW_ID,)
ADOPTED_PROTOCOL_DELTA_LAWS = (ABSORBED_LAW_ID,)
REQUIRED_MACHINE_FIELDS = (
    "protocol_current_head",
    "protocol_current_head_short",
    "protocol_current_head_subject",
    "last_seen_protocol_commit",
    "last_adopted_protocol_commit",
    "capability_family_count",
    "capability_families",
    "relevant_protocol_delta_laws",
    "adopted_protocol_delta_laws",
    "scanned_commit_count",
    "relevant_unadopted_commit_count",
    "relevant_unadopted_commits",
    "protocol_delta_adoption_status",
    "protocol_delta_adoption_mode",
    "protocol_delta_state_written",
    "protocol_root",
    "policy_path",
    "fallback_path",
    "state_path",
    "stale_reasons",
)
FAIL_CLOSE_REASON_FAMILY = (
    "relevant_protocol_delta_pending_adoption",
    "protocol_authority_resolution_failed",
    "protocol_owner_surface_not_ready",
    "instance_local_adoption_markers_missing",
    f"relevant_unadopted_protocol_commits:{ABSORBED_LAW_ID}",
    f"runtime_guard_law_not_adopted:{ABSORBED_LAW_ID}",
)
SUCCESS_MODE = "continuous_protocol_delta_adoption_ready"
FAIL_MODE = "relevant_protocol_delta_pending_adoption"
PASS_STATUS = "PASS_REQUIRED"
FAIL_STATUS = "FAIL_REQUIRED"


def repo_root_from_script(script_path: Path) -> Path:
    return script_path.resolve().parents[1]
