#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from response_stamp_common import resolve_layer_intent
from tool_vendor_governance_common import (
    contract_required,
    load_json,
    resolve_pack_and_task,
    resolve_report_path,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_FAIL_OPTIONAL = "FAIL_OPTIONAL"

REASON_PASS = "IP-COV-000"
REASON_SKIPPED = "IP-COV-001"
REASON_FAIL = "IP-COV-999"
REASON_LANE_REQUIRED = "IP-COV-LANE-001"
REASON_REQUIRED_SUBCHECK_SKIPPED = "IP-COV-UE-001"
REASON_REQUIRED_STATUS_SKIPPED = "IP-COV-REQ-001"
REASON_REQUIRED_NO_CURRENT_ROUND_EVIDENCE = "IP-COV-REQ-002"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}
SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent

ERR_RE = re.compile(r"\b(IP-[A-Z0-9-]+)\b")
DISCOVERY_TARGET_NAMES = {
    "tool_installation",
    "vendor_api_discovery",
    "vendor_api_solution",
}
STATUS_FIELD_BY_SCRIPT = {
    "scripts/validate_unlock_formula.py": "unlock_formula_status",
    "scripts/validate_release_plane_cloud_evidence.py": "release_plane_cloud_evidence_status",
    "scripts/validate_cross_cwd_absolute_input.py": "cross_cwd_absolute_input_status",
    "scripts/validate_run_id_report_selection.py": "run_id_report_selection_status",
    "scripts/validate_phase_bootstrap_before_strict.py": "phase_bootstrap_before_strict_status",
    "scripts/validate_tmp_collision_safety.py": "tmp_collision_safety_status",
    "scripts/validate_handoff_collab_freshness_rotation.py": "handoff_collab_freshness_rotation_status",
    "scripts/validate_protocol_feedback_atomic_emit.py": "protocol_feedback_atomic_emit_status",
    "scripts/validate_capability_boundary_classification.py": "capability_boundary_status",
    "scripts/validate_promotion_pipeline.py": "promotion_pipeline_status",
    "scripts/validate_outlet_matrix.py": "outlet_matrix_status",
    "scripts/validate_sidecar_cwd_parity.py": "sidecar_cwd_parity_status",
    "scripts/validate_docs_bridge_consistency.py": "bridge_consistency_status",
    "scripts/validate_contract_mapping_coverage.py": "contract_mapping_coverage_status",
    "scripts/validate_prompt_bootstrap_capability.py": "prompt_bootstrap_contract_status",
    "scripts/validate_prompt_capability_matrix.py": "prompt_capability_matrix_status",
    "scripts/validate_refresh_strict_business_interference.py": "refresh_strict_business_interference_status",
    "scripts/validate_kernel_ssot_source.py": "kernel_ssot_source_status",
    "scripts/validate_prompt_derivation_conformance.py": "prompt_derivation_conformance_status",
    "scripts/validate_semantic_convergence.py": "semantic_convergence_status",
    "scripts/validate_prompt_kernel_executable_coupling.py": "prompt_kernel_executable_coupling_status",
    "scripts/validate_semantic_routing_guard.py": "semantic_routing_status",
    "scripts/validate_instance_protocol_split_receipt.py": "instance_protocol_split_status",
    "scripts/validate_vendor_namespace_separation.py": "vendor_namespace_status",
    "scripts/validate_protocol_feedback_sidecar_contract.py": "sidecar_contract_status",
    "scripts/validate_v16_cross_verification_tracks.py": "cross_verification_tracks_status",
    "scripts/validate_v16_intake_evidence_quorum.py": "intake_evidence_quorum_status",
    "scripts/validate_route_version_pinning.py": "pin_status",
    "scripts/validate_fallback_taxonomy_normalization.py": "fallback_taxonomy_normalization_status",
    "scripts/validate_dedup_monotonicity.py": "monotonicity_status",
    "scripts/validate_v16_cross_workflow_schema.py": "cross_workflow_schema_status",
    "scripts/validate_v16_skill_path_integrity.py": "path_integrity_status",
    "scripts/validate_gated_switch_guard.py": "gated_switch_guard_status",
    "scripts/validate_protocol_lane_headstamp_continuity.py": "protocol_lane_headstamp_status",
    "scripts/validate_host_transport_wiring_attestation.py": "host_transport_wiring_attestation_status",
    "scripts/validate_execution_target_tuple_isolation.py": "execution_target_tuple_isolation_status",
    "scripts/validate_protocol_unique_entry_gate.py": "protocol_unique_entry_gate_status",
    "scripts/validate_protocol_downsink_path_immutability.py": "protocol_downsink_path_immutability_status",
    "scripts/validate_protocol_downsink_path_write_guard.py": "protocol_downsink_path_write_guard_status",
    "scripts/validate_protocol_downsink_path_literal_lock.py": "protocol_downsink_path_literal_lock_status",
    "scripts/validate_skill_installation_supply_chain.py": "skill_installation_supply_chain_status",
    "scripts/validate_skill_frontmatter.py": "skill_frontmatter_status",
    "scripts/validate_skill_sync_drift_guard.py": "skill_sync_drift_guard_status",
}
PROTOCOL_GOVERNANCE_TARGET_NAMES = {
    "release_plane_cloud_evidence",
    "cross_cwd_absolute_input",
    "run_id_report_selection",
    "phase_bootstrap_before_strict",
    "tmp_collision_safety",
    "handoff_collab_freshness_rotation",
    "protocol_feedback_atomic_emit",
    "capability_boundary_classification",
    "promotion_evidence_pipeline",
    "outlet_regression_matrix",
    "sidecar_cwd_parity",
    "docs_bridge_consistency",
    "contract_mapping_coverage",
    "prompt_bootstrap_capability",
    "prompt_capability_matrix",
    "refresh_strict_business_interference",
    "kernel_ssot_source",
    "prompt_derivation_conformance",
    "semantic_convergence",
    "prompt_kernel_executable_coupling",
    "semantic_routing_guard",
    "instance_protocol_split_receipt",
    "vendor_namespace_separation",
    "protocol_feedback_sidecar",
    "execution_target_tuple_isolation",
    "cross_verification_tracks",
    "intake_evidence_quorum",
    "route_version_pinning",
    "fallback_taxonomy_normalization",
    "dedup_monotonicity",
    "cross_workflow_schema",
    "skill_path_integrity",
    "protocol_unique_entry_gate",
    "protocol_lane_headstamp_continuity",
    "host_transport_wiring_attestation",
    "downsink_path_immutability",
    "downsink_path_write_guard",
    "downsink_path_literal_lock",
    "skill_installation_supply_chain",
    "skill_frontmatter",
    "skill_sync_drift_guard",
}

INSTANCE_STRICT_REQUIRED_FLOOR_TARGET_NAMES = {
    "unlock_formula_automation",
    "run_id_report_selection",
    "phase_bootstrap_before_strict",
    "tmp_collision_safety",
    "prompt_bootstrap_capability",
    "prompt_capability_matrix",
    "kernel_ssot_source",
    "prompt_derivation_conformance",
    "prompt_kernel_executable_coupling",
    "tool_installation",
    "vendor_api_discovery",
    "vendor_api_solution",
    "gated_switch_guard",
    "protocol_lane_headstamp_continuity",
    "host_transport_wiring_attestation",
    "protocol_unique_entry_gate",
    "downsink_path_immutability",
    "downsink_path_write_guard",
    "downsink_path_literal_lock",
    "skill_installation_supply_chain",
    "skill_frontmatter",
    "skill_sync_drift_guard",
}

FORCE_REQUIRED_CAPABLE_VALIDATOR_SCRIPTS = {
    "scripts/validate_unlock_formula.py",
    "scripts/validate_release_plane_cloud_evidence.py",
    "scripts/validate_cross_cwd_absolute_input.py",
    "scripts/validate_run_id_report_selection.py",
    "scripts/validate_phase_bootstrap_before_strict.py",
    "scripts/validate_tmp_collision_safety.py",
    "scripts/validate_handoff_collab_freshness_rotation.py",
    "scripts/validate_protocol_feedback_atomic_emit.py",
    "scripts/validate_capability_boundary_classification.py",
    "scripts/validate_promotion_pipeline.py",
    "scripts/validate_outlet_matrix.py",
    "scripts/validate_sidecar_cwd_parity.py",
    "scripts/validate_docs_bridge_consistency.py",
    "scripts/validate_contract_mapping_coverage.py",
    "scripts/validate_prompt_bootstrap_capability.py",
    "scripts/validate_prompt_capability_matrix.py",
    "scripts/validate_refresh_strict_business_interference.py",
    "scripts/validate_kernel_ssot_source.py",
    "scripts/validate_prompt_derivation_conformance.py",
    "scripts/validate_semantic_convergence.py",
    "scripts/validate_prompt_kernel_executable_coupling.py",
    "scripts/validate_protocol_unique_entry_gate.py",
    "scripts/validate_protocol_downsink_path_immutability.py",
    "scripts/validate_protocol_downsink_path_write_guard.py",
    "scripts/validate_protocol_downsink_path_literal_lock.py",
    "scripts/validate_skill_installation_supply_chain.py",
    "scripts/validate_skill_frontmatter.py",
    "scripts/validate_skill_sync_drift_guard.py",
}


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    if not isinstance(doc, dict):
        return False
    rows = [row for row in (doc.get("identities") or []) if isinstance(row, dict)]
    identity = str(identity_id or "").strip()
    target = next((row for row in rows if str(row.get("id", "")).strip() == identity), None)
    if not isinstance(target, dict):
        return False
    profile = str(target.get("profile", "")).strip().lower()
    runtime_mode = str(target.get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _resolve_repo_path(path_like: str) -> Path:
    candidate = Path(str(path_like)).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (REPO_ROOT / candidate).resolve()


@dataclass
class ContractTarget:
    name: str
    contract_keys: tuple[str, ...]
    validator_script: str
    validator_args: tuple[str, ...] = ()


TARGETS = (
    ContractTarget(
        name="unlock_formula_automation",
        contract_keys=(
            "release_unlock_formula_automation_contract_v1",
            "release_unlock_formula_automation_contract",
            "rq_001_unlock_formula_contract_v1",
        ),
        validator_script="scripts/validate_unlock_formula.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="release_plane_cloud_evidence",
        contract_keys=(
            "release_plane_cloud_evidence_contract_v1",
            "release_plane_cloud_evidence_contract",
            "rq_006_release_plane_cloud_evidence_contract_v1",
        ),
        validator_script="scripts/validate_release_plane_cloud_evidence.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="cross_cwd_absolute_input",
        contract_keys=(
            "cross_cwd_absolute_input_contract_v1",
            "cross_cwd_absolute_input_contract",
            "rq_007_cross_cwd_absolute_input_contract_v1",
        ),
        validator_script="scripts/validate_cross_cwd_absolute_input.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="run_id_report_selection",
        contract_keys=(
            "run_id_report_selection_contract_v1",
            "run_id_report_selection_contract",
            "rq_009_run_id_anchored_report_selection_contract_v1",
        ),
        validator_script="scripts/validate_run_id_report_selection.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="phase_bootstrap_before_strict",
        contract_keys=(
            "phase_bootstrap_before_strict_contract_v1",
            "phase_bootstrap_before_strict_contract",
            "rq_010_phase_a_bootstrap_before_strict_contract_v1",
        ),
        validator_script="scripts/validate_phase_bootstrap_before_strict.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="tmp_collision_safety",
        contract_keys=(
            "tmp_collision_safe_allocator_contract_v1",
            "tmp_collision_safe_allocator_contract",
            "rq_011_tmp_collision_safe_allocator_contract_v1",
        ),
        validator_script="scripts/validate_tmp_collision_safety.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="handoff_collab_freshness_rotation",
        contract_keys=(
            "handoff_collab_freshness_autorotation_contract_v1",
            "handoff_collab_freshness_autorotation_contract",
            "rq_012_handoff_collab_freshness_autorotation_contract_v1",
        ),
        validator_script="scripts/validate_handoff_collab_freshness_rotation.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="protocol_feedback_atomic_emit",
        contract_keys=(
            "protocol_feedback_atomic_emit_contract_v1",
            "protocol_feedback_atomic_emit_contract",
            "rq_013_protocol_feedback_atomic_emit_contract_v1",
        ),
        validator_script="scripts/validate_protocol_feedback_atomic_emit.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="capability_boundary_classification",
        contract_keys=(
            "capability_activation_boundary_contract_v2",
            "capability_activation_boundary_contract",
            "rq_002_capability_boundary_contract_v1",
        ),
        validator_script="scripts/validate_capability_boundary_classification.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="promotion_evidence_pipeline",
        contract_keys=(
            "status_promotion_evidence_contract_v1",
            "status_promotion_evidence_contract",
            "rq_003_promotion_evidence_pipeline_contract_v1",
        ),
        validator_script="scripts/validate_promotion_pipeline.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="outlet_regression_matrix",
        contract_keys=(
            "outbound_reply_outlet_regression_matrix_contract_v1",
            "outbound_reply_outlet_regression_matrix_contract",
            "rq_004_outlet_matrix_contract_v1",
        ),
        validator_script="scripts/validate_outlet_matrix.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="sidecar_cwd_parity",
        contract_keys=(
            "sidecar_cwd_invariance_contract_v1",
            "sidecar_cwd_invariance_contract",
            "rq_005_sidecar_cwd_invariance_contract_v1",
        ),
        validator_script="scripts/validate_sidecar_cwd_parity.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="docs_bridge_consistency",
        contract_keys=(
            "docs_bridge_consistency_contract_v1",
            "docs_bridge_consistency_contract",
            "rq_008_docs_bridge_consistency_contract_v1",
        ),
        validator_script="scripts/validate_docs_bridge_consistency.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="contract_mapping_coverage",
        contract_keys=(
            "contract_mapping_projection_contract_v1",
            "contract_mapping_projection_contract",
            "rq_026_kernel_contract_mapping_projection_contract_v1",
        ),
        validator_script="scripts/validate_contract_mapping_coverage.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="prompt_bootstrap_capability",
        contract_keys=(
            "prompt_bootstrap_capability_contract_v1",
            "prompt_bootstrap_capability_contract",
            "rq_014_prompt_bootstrap_capability_contract_v1",
        ),
        validator_script="scripts/validate_prompt_bootstrap_capability.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="prompt_capability_matrix",
        contract_keys=(
            "prompt_capability_matrix_fail_closed_contract_v1",
            "prompt_capability_matrix_fail_closed_contract",
            "rq_015_prompt_capability_matrix_fail_closed_contract_v1",
        ),
        validator_script="scripts/validate_prompt_capability_matrix.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="refresh_strict_business_interference",
        contract_keys=(
            "refresh_strict_business_interference_matrix_contract_v1",
            "refresh_strict_business_interference_matrix_contract",
            "rq_016_refresh_strict_business_interference_matrix_contract_v1",
        ),
        validator_script="scripts/validate_refresh_strict_business_interference.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="kernel_ssot_source",
        contract_keys=(
            "kernel_canonical_source_contract_v1",
            "kernel_canonical_source_contract",
            "rq_025_kernel_canonical_source_contract_v1",
        ),
        validator_script="scripts/validate_kernel_ssot_source.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="prompt_derivation_conformance",
        contract_keys=(
            "derived_prompt_conformance_contract_v1",
            "derived_prompt_conformance_contract",
            "rq_027_derived_prompt_conformance_contract_v1",
        ),
        validator_script="scripts/validate_prompt_derivation_conformance.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="semantic_convergence",
        contract_keys=(
            "semantic_single_source_convergence_contract_v1",
            "semantic_single_source_convergence_contract",
            "rq_029_semantic_single_source_convergence_contract_v1",
        ),
        validator_script="scripts/validate_semantic_convergence.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="tool_installation",
        contract_keys=("tool_installation_contract",),
        validator_script="scripts/validate_identity_tool_installation.py",
    ),
    ContractTarget(
        name="vendor_api_discovery",
        contract_keys=("vendor_api_discovery_contract",),
        validator_script="scripts/validate_identity_vendor_api_discovery.py",
    ),
    ContractTarget(
        name="vendor_api_solution",
        contract_keys=("vendor_api_solution_contract",),
        validator_script="scripts/validate_identity_vendor_api_solution.py",
    ),
    ContractTarget(
        name="semantic_routing_guard",
        contract_keys=("semantic_routing_guard_contract_v1", "semantic_routing_guard_contract"),
        validator_script="scripts/validate_semantic_routing_guard.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="instance_protocol_split_receipt",
        contract_keys=("instance_protocol_split_receipt_contract_v1", "instance_protocol_split_receipt_contract"),
        validator_script="scripts/validate_instance_protocol_split_receipt.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="vendor_namespace_separation",
        contract_keys=("semantic_routing_guard_contract_v1", "semantic_routing_guard_contract"),
        validator_script="scripts/validate_vendor_namespace_separation.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="protocol_feedback_sidecar",
        contract_keys=("protocol_feedback_sidecar_contract_v1", "protocol_feedback_sidecar_contract"),
        validator_script="scripts/validate_protocol_feedback_sidecar_contract.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="cross_verification_tracks",
        contract_keys=(
            "multi_track_cross_verification_contract_v1",
            "multi_track_cross_verification_contract",
            "cross_verification_tracks_contract_v1",
            "cross_verification_tracks_contract",
            "rq_017_multi_track_cross_verification_contract_v1",
        ),
        validator_script="scripts/validate_v16_cross_verification_tracks.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="intake_evidence_quorum",
        contract_keys=(
            "intake_evidence_quorum_contract_v1",
            "intake_evidence_quorum_contract",
            "rq_030_intake_evidence_quorum_contract_v1",
        ),
        validator_script="scripts/validate_v16_intake_evidence_quorum.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="route_version_pinning",
        contract_keys=(
            "route_workflow_version_pinning_contract_v1",
            "route_workflow_version_pinning_contract",
            "rq_021_route_workflow_version_pinning_contract_v1",
        ),
        validator_script="scripts/validate_route_version_pinning.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="fallback_taxonomy_normalization",
        contract_keys=(
            "fallback_taxonomy_normalization_contract_v1",
            "fallback_taxonomy_normalization_contract",
            "rq_022_fallback_taxonomy_normalization_contract_v1",
        ),
        validator_script="scripts/validate_fallback_taxonomy_normalization.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="dedup_monotonicity",
        contract_keys=(
            "dedup_monotonic_winner_contract_v1",
            "dedup_monotonic_winner_contract",
            "rq_018_dedup_monotonic_winner_contract_v1",
        ),
        validator_script="scripts/validate_dedup_monotonicity.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="cross_workflow_schema",
        contract_keys=(
            "cross_workflow_evidence_schema_contract_v1",
            "cross_workflow_evidence_schema_contract",
            "rq_019_cross_workflow_evidence_schema_contract_v1",
        ),
        validator_script="scripts/validate_v16_cross_workflow_schema.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="skill_path_integrity",
        contract_keys=(
            "skill_path_integrity_contract_v1",
            "skill_path_integrity_contract",
            "rq_020_skill_path_integrity_contract_v1",
        ),
        validator_script="scripts/validate_v16_skill_path_integrity.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="skill_installation_supply_chain",
        contract_keys=(
            "skill_installation_supply_chain_contract_v1",
            "skill_installation_supply_chain_contract",
            "rq_039_skill_installation_supply_chain_contract_v1",
        ),
        validator_script="scripts/validate_skill_installation_supply_chain.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="skill_frontmatter",
        contract_keys=(
            "skill_frontmatter_contract_v1",
            "skill_frontmatter_contract",
            "rq_040_skill_frontmatter_contract_v1",
        ),
        validator_script="scripts/validate_skill_frontmatter.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="skill_sync_drift_guard",
        contract_keys=(
            "skill_sync_drift_guard_contract_v1",
            "skill_sync_drift_guard_contract",
            "rq_041_skill_sync_drift_guard_contract_v1",
        ),
        validator_script="scripts/validate_skill_sync_drift_guard.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="gated_switch_guard",
        contract_keys=(
            "gated_switch_guard_contract_v1",
            "gated_switch_guard_contract",
        ),
        validator_script="scripts/validate_gated_switch_guard.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="prompt_kernel_executable_coupling",
        contract_keys=(
            "prompt_import_executable_coupling_contract_v1",
            "prompt_import_executable_coupling_contract",
            "rq_031_prompt_import_executable_coupling_contract_v1",
        ),
        validator_script="scripts/validate_prompt_kernel_executable_coupling.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="protocol_lane_headstamp_continuity",
        contract_keys=(
            "protocol_lane_activation_headstamp_contract_v1",
            "protocol_lane_activation_headstamp_contract",
        ),
        validator_script="scripts/validate_protocol_lane_headstamp_continuity.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="host_transport_wiring_attestation",
        contract_keys=(
            "host_visible_surface_registry_contract_v1",
            "host_visible_surface_registry_contract",
        ),
        validator_script="scripts/validate_host_transport_wiring_attestation.py",
        validator_args=("--require-live-receipts", "--json-only"),
    ),
    ContractTarget(
        name="execution_target_tuple_isolation",
        contract_keys=(
            "execution_target_tuple_isolation_contract_v1",
            "execution_target_tuple_isolation_contract",
            "rq_033_execution_target_tuple_isolation_contract_v1",
        ),
        validator_script="scripts/validate_execution_target_tuple_isolation.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="protocol_unique_entry_gate",
        contract_keys=(
            "protocol_unique_entry_gate_contract_v1",
            "protocol_unique_entry_gate_contract",
            "rq_036_protocol_unique_entry_gate_contract_v1",
        ),
        validator_script="scripts/validate_protocol_unique_entry_gate.py",
        validator_args=("--force-check", "--json-only"),
    ),
    ContractTarget(
        name="downsink_path_immutability",
        contract_keys=(
            "protocol_downsink_path_immutability_contract_v1",
            "protocol_downsink_path_immutability_contract",
            "rq_036_downsink_path_immutability_contract_v1",
        ),
        validator_script="scripts/validate_protocol_downsink_path_immutability.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="downsink_path_write_guard",
        contract_keys=(
            "protocol_downsink_path_immutability_contract_v1",
            "protocol_downsink_path_immutability_contract",
            "rq_037_downsink_path_write_guard_contract_v1",
        ),
        validator_script="scripts/validate_protocol_downsink_path_write_guard.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="downsink_path_literal_lock",
        contract_keys=(
            "protocol_downsink_path_immutability_contract_v1",
            "protocol_downsink_path_immutability_contract",
            "rq_038_downsink_path_literal_lock_contract_v1",
        ),
        validator_script="scripts/validate_protocol_downsink_path_literal_lock.py",
        validator_args=("--json-only",),
    ),
)


def _resolve_contract_for_target(task: dict[str, Any], target: ContractTarget) -> tuple[dict[str, Any], str]:
    for key in target.contract_keys:
        raw = task.get(key)
        if isinstance(raw, dict):
            return raw, key

    if target.name == "gated_switch_guard":
        for key, raw in task.items():
            if not isinstance(raw, dict):
                continue
            token = str(key or "").strip().lower()
            if "gated_switch" in token and "contract" in token:
                return raw, str(key)
    if target.name == "protocol_lane_headstamp_continuity":
        for key, raw in task.items():
            if not isinstance(raw, dict):
                continue
            token = str(key or "").strip().lower()
            if "protocol_lane" in token and "headstamp" in token and "contract" in token:
                return raw, str(key)
    if target.name == "execution_target_tuple_isolation":
        for key, raw in task.items():
            if not isinstance(raw, dict):
                continue
            token = str(key or "").strip().lower()
            if "execution_target_tuple" in token and "contract" in token:
                return raw, str(key)
    if target.name == "protocol_unique_entry_gate":
        for key, raw in task.items():
            if not isinstance(raw, dict):
                continue
            token = str(key or "").strip().lower()
            if "unique_entry" in token and "contract" in token:
                return raw, str(key)
    if target.name in {"downsink_path_immutability", "downsink_path_write_guard", "downsink_path_literal_lock"}:
        for key, raw in task.items():
            if not isinstance(raw, dict):
                continue
            token = str(key or "").strip().lower()
            if "downsink" in token and "path" in token and "contract" in token:
                return raw, str(key)
    return {}, target.contract_keys[0]


def _extract_reason(out: str, err: str, default_reason: str) -> str:
    text = f"{out}\n{err}".strip()
    m = ERR_RE.search(text)
    if m:
        return m.group(1)
    return default_reason


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else None
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _classify_from_payload(
    *,
    script: str,
    payload: dict[str, Any],
    required: bool,
    fallback_rc: int,
) -> tuple[str, str]:
    status_key = STATUS_FIELD_BY_SCRIPT.get(script, "")
    validator_status = str(payload.get(status_key, "")).strip().upper() if status_key else ""
    if required and validator_status == STATUS_SKIPPED_NOT_REQUIRED:
        stale_reasons = payload.get("stale_reasons")
        stale_tokens = (
            [str(item).strip() for item in stale_reasons if str(item).strip()]
            if isinstance(stale_reasons, list)
            else []
        )
        if "required_contract_not_applicable_no_current_round_evidence_source" in stale_tokens:
            return STATUS_FAIL_REQUIRED, REASON_REQUIRED_NO_CURRENT_ROUND_EVIDENCE
        return STATUS_FAIL_REQUIRED, REASON_REQUIRED_STATUS_SKIPPED
    if (
        script == "scripts/validate_protocol_unique_entry_gate.py"
        and required
        and validator_status == STATUS_PASS_REQUIRED
    ):
        receipt_required = bool(payload.get("protocol_unique_entry_receipt_required", False))
        receipt_status = str(payload.get("protocol_unique_entry_receipt_status", "")).strip().upper()
        if receipt_required and receipt_status == STATUS_SKIPPED_NOT_REQUIRED:
            return STATUS_FAIL_REQUIRED, REASON_REQUIRED_SUBCHECK_SKIPPED
    if not validator_status:
        return _classify(required, fallback_rc)
    if validator_status == STATUS_PASS_REQUIRED:
        if required:
            return STATUS_PASS_REQUIRED, REASON_PASS
        return STATUS_SKIPPED_NOT_REQUIRED, REASON_SKIPPED
    if validator_status == STATUS_SKIPPED_NOT_REQUIRED:
        return STATUS_SKIPPED_NOT_REQUIRED, REASON_SKIPPED
    if validator_status == STATUS_FAIL_REQUIRED:
        return (STATUS_FAIL_REQUIRED if required else STATUS_FAIL_OPTIONAL), REASON_FAIL
    if validator_status == "WARN_NON_BLOCKING":
        return (STATUS_FAIL_REQUIRED if required else STATUS_FAIL_OPTIONAL), REASON_FAIL
    return _classify(required, fallback_rc)


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
    catalog: str,
    identity_id: str,
    run_id: str,
) -> tuple[str, str]:
    try:
        pack_path, _task_path = resolve_pack_and_task(Path(catalog).expanduser().resolve(), identity_id)
    except Exception:
        return "", ""
    feedback_root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if not feedback_root.exists():
        return "", ""

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
        return "", ""

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    selected = candidates[0]
    run_token = str(run_id or "").strip()
    if run_token:
        filtered = [p for p in candidates if run_token in p.name or _file_contains_token(p, run_token)]
        if filtered:
            selected = filtered[0]
    bundle_id = selected.stem
    try:
        raw = selected.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        raw = ""
    parsed_bundle_id = _extract_bundle_id_from_text(raw)
    if parsed_bundle_id:
        bundle_id = parsed_bundle_id
    return str(selected), str(bundle_id or "").strip()


def _run_validator(
    script: str,
    catalog: str,
    identity_id: str,
    *,
    repo_catalog: str,
    actor_id: str,
    session_id: str,
    operation: str,
    expected_work_layer: str,
    expected_source_layer: str,
    layer_intent_text: str,
    run_id: str,
    report_selected_path: str,
    force_required: bool,
    extra_args: tuple[str, ...],
) -> tuple[int, str, str]:
    script_path = _resolve_repo_path(script)
    repo_catalog_path = _resolve_repo_path(repo_catalog)
    cmd = ["python3", str(script_path), "--catalog", catalog, "--identity-id", identity_id]
    if script in {
        "scripts/validate_unlock_formula.py",
        "scripts/validate_release_plane_cloud_evidence.py",
        "scripts/validate_cross_cwd_absolute_input.py",
        "scripts/validate_run_id_report_selection.py",
        "scripts/validate_phase_bootstrap_before_strict.py",
        "scripts/validate_tmp_collision_safety.py",
        "scripts/validate_handoff_collab_freshness_rotation.py",
        "scripts/validate_protocol_feedback_atomic_emit.py",
        "scripts/validate_capability_boundary_classification.py",
        "scripts/validate_promotion_pipeline.py",
        "scripts/validate_outlet_matrix.py",
        "scripts/validate_sidecar_cwd_parity.py",
        "scripts/validate_docs_bridge_consistency.py",
        "scripts/validate_contract_mapping_coverage.py",
        "scripts/validate_prompt_bootstrap_capability.py",
        "scripts/validate_prompt_capability_matrix.py",
        "scripts/validate_refresh_strict_business_interference.py",
        "scripts/validate_kernel_ssot_source.py",
        "scripts/validate_prompt_derivation_conformance.py",
        "scripts/validate_semantic_convergence.py",
        "scripts/validate_prompt_kernel_executable_coupling.py",
        "scripts/validate_semantic_routing_guard.py",
        "scripts/validate_vendor_namespace_separation.py",
        "scripts/validate_v16_cross_verification_tracks.py",
        "scripts/validate_v16_intake_evidence_quorum.py",
        "scripts/validate_route_version_pinning.py",
        "scripts/validate_fallback_taxonomy_normalization.py",
        "scripts/validate_dedup_monotonicity.py",
        "scripts/validate_v16_cross_workflow_schema.py",
        "scripts/validate_v16_skill_path_integrity.py",
        "scripts/validate_gated_switch_guard.py",
        "scripts/validate_protocol_lane_headstamp_continuity.py",
        "scripts/validate_execution_target_tuple_isolation.py",
        "scripts/validate_protocol_unique_entry_gate.py",
        "scripts/validate_protocol_downsink_path_immutability.py",
        "scripts/validate_protocol_downsink_path_write_guard.py",
        "scripts/validate_protocol_downsink_path_literal_lock.py",
    }:
        cmd += ["--operation", operation]
    if script in {
        "scripts/validate_protocol_lane_headstamp_continuity.py",
        "scripts/validate_protocol_unique_entry_gate.py",
    }:
        if actor_id:
            cmd += ["--actor-id", actor_id]
        if session_id:
            cmd += ["--session-id", session_id]
        if run_id:
            cmd += ["--run-id", run_id]
    if script == "scripts/validate_host_transport_wiring_attestation.py":
        effective_run_id = str(run_id or "").strip()
        if not effective_run_id:
            session_token = str(session_id or "").strip()
            if session_token.startswith("run:") and len(session_token) > 4:
                effective_run_id = session_token.split(":", 1)[1].strip()
        if actor_id:
            cmd += ["--require-actor-id", actor_id]
        if session_id:
            cmd += ["--require-session-id", session_id]
        if effective_run_id:
            cmd += ["--require-run-id", effective_run_id]
    if script == "scripts/validate_protocol_lane_headstamp_continuity.py":
        if expected_work_layer:
            cmd += ["--expected-work-layer", expected_work_layer]
        if expected_source_layer:
            cmd += ["--expected-source-layer", expected_source_layer]
        if layer_intent_text:
            cmd += ["--layer-intent-text", layer_intent_text]
    if script == "scripts/validate_instance_protocol_split_receipt.py":
        cmd += ["--operation", operation, "--repo-catalog", str(repo_catalog_path)]
    if script == "scripts/validate_protocol_feedback_sidecar_contract.py":
        cmd += ["--repo-catalog", str(repo_catalog_path), "--operation", operation]
    if script == "scripts/validate_cross_cwd_absolute_input.py":
        cmd += ["--repo-catalog", str(repo_catalog_path)]
    if script == "scripts/validate_prompt_kernel_executable_coupling.py":
        cmd += ["--repo-catalog", str(repo_catalog_path)]
        if actor_id:
            cmd += ["--actor-id", actor_id]
        if session_id:
            cmd += ["--session-id", session_id]
        if expected_work_layer:
            cmd += ["--expected-work-layer", expected_work_layer]
        if expected_source_layer:
            cmd += ["--source-layer", expected_source_layer]
    if script in {
        "scripts/validate_semantic_routing_guard.py",
        "scripts/validate_instance_protocol_split_receipt.py",
        "scripts/validate_vendor_namespace_separation.py",
        "scripts/validate_protocol_feedback_sidecar_contract.py",
    }:
        if expected_work_layer:
            cmd += ["--expected-work-layer", expected_work_layer]
        if expected_source_layer:
            cmd += ["--expected-source-layer", expected_source_layer]
        if layer_intent_text:
            cmd += ["--layer-intent-text", layer_intent_text]
    if script == "scripts/validate_run_id_report_selection.py":
        if run_id:
            cmd += ["--run-id", run_id]
        if str(report_selected_path or "").strip():
            cmd += ["--report", str(report_selected_path).strip()]
    if script == "scripts/validate_outlet_matrix.py" and str(report_selected_path or "").strip():
        cmd += ["--report", str(report_selected_path).strip()]
    if script in {
        "scripts/validate_v16_cross_verification_tracks.py",
        "scripts/validate_v16_intake_evidence_quorum.py",
    }:
        bundle_path, bundle_id = _resolve_cross_verification_bundle_context(
            catalog=catalog,
            identity_id=identity_id,
            run_id=run_id,
        )
        if bundle_path:
            cmd += ["--bundle", bundle_path]
        if bundle_id:
            cmd += ["--bundle-id", bundle_id]
    if force_required and script in FORCE_REQUIRED_CAPABLE_VALIDATOR_SCRIPTS:
        cmd += ["--force-required"]
    cmd += list(extra_args)
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _classify(required: bool, rc: int) -> tuple[str, str]:
    if rc == 0 and required:
        return STATUS_PASS_REQUIRED, REASON_PASS
    if rc == 0 and not required:
        return STATUS_SKIPPED_NOT_REQUIRED, REASON_SKIPPED
    if rc != 0 and required:
        return STATUS_FAIL_REQUIRED, REASON_FAIL
    return STATUS_FAIL_OPTIONAL, REASON_FAIL


def _coverage_rate(passed: int, total: int) -> float:
    if total <= 0:
        return 0.0
    raw = (passed / total) * 100.0
    bounded = max(0.0, min(100.0, raw))
    return round(bounded, 2)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Validate required-contract coverage semantics for tool/vendor closures "
            "(PASS_REQUIRED / SKIPPED_NOT_REQUIRED / FAIL_REQUIRED)."
        )
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--min-required-contract-coverage",
        type=float,
        default=-1.0,
        help="optional minimum required-contract coverage rate (0-100). default disabled",
    )
    ap.add_argument(
        "--min-discovery-required-coverage",
        type=float,
        default=-1.0,
        help=(
            "optional minimum required-contract coverage rate (0-100) for discovery subset "
            "(tool_installation/vendor_api_discovery/vendor_api_solution). default disabled"
        ),
    )
    ap.add_argument(
        "--json-only",
        action="store_true",
        help="emit payload JSON only",
    )
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--report-selected-path", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
        help="operation context passed to operation-aware validators",
    )
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity runtime task: {exc}")
        return 2

    rows: list[dict[str, Any]] = []
    required_total = 0
    required_passed = 0
    skipped_count = 0
    skipped_lane_excluded_count = 0
    skipped_actionable_count = 0
    failed_required = 0
    failed_optional = 0
    discovery_required_total = 0
    discovery_required_passed = 0
    protocol_targets_included: list[str] = []
    protocol_targets_blocking: list[str] = []
    strict_instance_floor_promoted: list[str] = []
    strict_instance_floor_blocking: list[str] = []
    strict_instance_floor_missing: list[str] = []
    prompt_lane_lock_influence_targets: list[str] = []
    skipped_lane_excluded_targets: list[str] = []
    skipped_actionable_targets: list[str] = []
    failed_optional_targets: list[str] = []

    layer_intent = resolve_layer_intent(
        explicit_work_layer=str(args.expected_work_layer or "").strip(),
        explicit_source_layer=str(args.expected_source_layer or "").strip(),
        intent_text=str(args.layer_intent_text or "").strip(),
        default_work_layer="instance",
        default_source_layer="project",
    )
    fixture_identity = _is_fixture_identity(catalog_path, args.identity_id)
    fixture_ci_floor_exempt = args.operation == "ci" and fixture_identity
    coverage_lane = str(layer_intent.get("resolved_work_layer", "instance")).strip().lower() or "instance"
    if coverage_lane not in {"protocol", "instance", "dual"}:
        coverage_lane = "instance"
    if coverage_lane == "protocol":
        coverage_target_set = "protocol_targets"
    elif coverage_lane == "dual":
        coverage_target_set = "shared_targets"
    else:
        coverage_target_set = "instance_targets"

    strict_operation = args.operation in STRICT_OPERATIONS
    strict_instance_floor_enabled = strict_operation and coverage_lane == "instance" and not fixture_ci_floor_exempt

    for target in TARGETS:
        contract, contract_key_used = _resolve_contract_for_target(task, target)
        required = contract_required(contract)
        lane_floor_target = (
            strict_instance_floor_enabled and target.name in INSTANCE_STRICT_REQUIRED_FLOOR_TARGET_NAMES
        )
        force_required = bool(
            lane_floor_target and target.validator_script in FORCE_REQUIRED_CAPABLE_VALIDATOR_SCRIPTS
        )

        report_pattern = str(contract.get("report_path_pattern", "")).strip()
        evidence = resolve_report_path(report="", pattern=report_pattern, pack_root=pack_path) if report_pattern else None
        evidence_ref = str(evidence) if evidence else ""

        rc, out, err = _run_validator(
            target.validator_script,
            str(catalog_path),
            args.identity_id,
            repo_catalog=args.repo_catalog,
            actor_id=str(args.actor_id or "").strip(),
            session_id=str(args.session_id or "").strip(),
            operation=args.operation,
            expected_work_layer=str(args.expected_work_layer or "").strip(),
            expected_source_layer=str(args.expected_source_layer or "").strip(),
            layer_intent_text=str(args.layer_intent_text or "").strip(),
            run_id=str(args.run_id or "").strip(),
            report_selected_path=str(args.report_selected_path or "").strip(),
            force_required=force_required,
            extra_args=target.validator_args,
        )
        payload = _parse_json_payload(out) if target.validator_args else None
        required_effective = required
        lane_target_included = True
        requiredization_current_round_linked = False
        if isinstance(payload, dict):
            payload_required = payload.get("required_contract")
            if isinstance(payload_required, bool):
                required_effective = required_effective or payload_required
            requiredization_current_round_linked = bool(payload.get("requiredization_current_round_linked", False))
            if not requiredization_current_round_linked and str(payload.get("activity_correlation_status", "")).strip().upper() == "CORRELATED_CURRENT_ROUND":
                requiredization_current_round_linked = True

        if lane_floor_target and not required_effective:
            strict_instance_floor_promoted.append(target.name)
            required_effective = True

        if (
            target.name in PROTOCOL_GOVERNANCE_TARGET_NAMES
            and coverage_lane == "instance"
            and not requiredization_current_round_linked
            and not lane_floor_target
        ):
            required_effective = False
            lane_target_included = False
        if target.name in PROTOCOL_GOVERNANCE_TARGET_NAMES and required_effective:
            protocol_targets_included.append(target.name)
        required_total += 1 if required_effective else 0

        if isinstance(payload, dict):
            validator_status, reason_code = _classify_from_payload(
                script=target.validator_script,
                payload=payload,
                required=required_effective,
                fallback_rc=rc,
            )
            if reason_code == REASON_FAIL:
                payload_reason = str(payload.get("error_code") or payload.get("sidecar_error_code") or "").strip()
                reason_code = payload_reason or _extract_reason(out, err, reason_code)
        else:
            validator_status, reason_code = _classify(required_effective, rc)
            if reason_code == REASON_FAIL:
                reason_code = _extract_reason(out, err, reason_code)

        prompt_routing_work_layer = ""
        prompt_routing_intent_source = ""
        prompt_routing_protocol_context_reasons: list[str] = []
        prompt_lane_lock_influence_observed = False
        if target.name == "prompt_kernel_executable_coupling" and isinstance(payload, dict):
            routing_detail = _parse_json_payload(str(payload.get("routing_validator_tail", "")) or "")
            if routing_detail:
                prompt_routing_work_layer = str(routing_detail.get("work_layer", "")).strip().lower()
                prompt_routing_intent_source = str(routing_detail.get("intent_source", "")).strip()
                raw_reasons = routing_detail.get("protocol_context_reasons")
                if isinstance(raw_reasons, list):
                    prompt_routing_protocol_context_reasons = [str(x).strip() for x in raw_reasons if str(x).strip()]
                prompt_lane_lock_influence_observed = "session_lane_lock_protocol" in prompt_routing_protocol_context_reasons
                if prompt_lane_lock_influence_observed:
                    prompt_lane_lock_influence_targets.append(target.name)

        if lane_floor_target and validator_status == STATUS_SKIPPED_NOT_REQUIRED:
            validator_status = STATUS_FAIL_REQUIRED
            reason_code = REASON_LANE_REQUIRED
            strict_instance_floor_missing.append(target.name)

        if validator_status == STATUS_PASS_REQUIRED:
            required_passed += 1
        elif validator_status == STATUS_SKIPPED_NOT_REQUIRED:
            skipped_count += 1
            if not lane_target_included:
                skipped_lane_excluded_count += 1
                skipped_lane_excluded_targets.append(target.name)
            else:
                skipped_actionable_count += 1
                skipped_actionable_targets.append(target.name)
        elif validator_status == STATUS_FAIL_REQUIRED:
            failed_required += 1
            if target.name in PROTOCOL_GOVERNANCE_TARGET_NAMES and required_effective:
                protocol_targets_blocking.append(target.name)
            if lane_floor_target:
                strict_instance_floor_blocking.append(target.name)
        elif validator_status == STATUS_FAIL_OPTIONAL:
            failed_optional += 1
            failed_optional_targets.append(target.name)

        if target.name in DISCOVERY_TARGET_NAMES and required_effective:
            discovery_required_total += 1
            if validator_status == STATUS_PASS_REQUIRED:
                discovery_required_passed += 1

        rows.append(
            {
                "name": target.name,
                "contract_key": contract_key_used,
                "validator": target.validator_script,
                "validator_status": validator_status,
                "required_contract_declared": required,
                "required_contract": required_effective,
                "coverage_lane": coverage_lane,
                "coverage_target_set": coverage_target_set,
                "lane_target_included": lane_target_included,
                "lane_required_floor_target": lane_floor_target,
                "validator_force_required": force_required,
                "prompt_routing_work_layer": prompt_routing_work_layer,
                "prompt_routing_intent_source": prompt_routing_intent_source,
                "prompt_routing_protocol_context_reasons": prompt_routing_protocol_context_reasons,
                "prompt_lane_lock_influence_observed": prompt_lane_lock_influence_observed,
                "requiredization_current_round_linked": requiredization_current_round_linked,
                "auto_required_signal": (payload.get("auto_required_signal") if isinstance(payload, dict) else False),
                "reason_code": reason_code,
                "evidence_ref": evidence_ref,
                "validator_rc": rc,
                "operation": args.operation,
                "validator_tail": (out.splitlines()[-1] if out else (err.splitlines()[-1] if err else "")),
            }
        )

    coverage_rate = _coverage_rate(required_passed, required_total)
    discovery_coverage_rate = _coverage_rate(discovery_required_passed, discovery_required_total)
    coverage_counter_overflow = required_passed > required_total
    discovery_counter_overflow = discovery_required_passed > discovery_required_total
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_path),
        "operation": args.operation,
        "fixture_identity": fixture_identity,
        "strict_instance_floor_fixture_ci_exempt": fixture_ci_floor_exempt,
        "coverage_lane": coverage_lane,
        "coverage_target_set": coverage_target_set,
        "resolved_work_layer": str(layer_intent.get("resolved_work_layer", "")),
        "resolved_source_layer": str(layer_intent.get("resolved_source_layer", "")),
        "intent_source": str(layer_intent.get("intent_source", "")),
        "intent_confidence": layer_intent.get("intent_confidence"),
        "fallback_reason": str(layer_intent.get("fallback_reason", "")),
        "protocol_triggered": bool(layer_intent.get("protocol_triggered", False)),
        "protocol_trigger_reasons": list(layer_intent.get("protocol_trigger_reasons") or []),
        "coverage_protocol_targets_included": sorted(set(protocol_targets_included)),
        "coverage_protocol_targets_blocking": sorted(set(protocol_targets_blocking)),
        "strict_instance_floor_enabled": strict_instance_floor_enabled,
        "strict_instance_floor_targets": (
            sorted(INSTANCE_STRICT_REQUIRED_FLOOR_TARGET_NAMES) if strict_instance_floor_enabled else []
        ),
        "strict_instance_floor_promoted": sorted(set(strict_instance_floor_promoted)),
        "strict_instance_floor_missing": sorted(set(strict_instance_floor_missing)),
        "strict_instance_floor_blocking": sorted(set(strict_instance_floor_blocking)),
        "prompt_lane_lock_influence_count": len(sorted(set(prompt_lane_lock_influence_targets))),
        "prompt_lane_lock_influence_targets": sorted(set(prompt_lane_lock_influence_targets)),
        "contracts": rows,
        "required_contract_total": required_total,
        "required_contract_passed": required_passed,
        "required_contract_coverage_rate": coverage_rate,
        "discovery_required_total": discovery_required_total,
        "discovery_required_passed": discovery_required_passed,
        "discovery_required_coverage_rate": discovery_coverage_rate,
        "skipped_contract_count": skipped_count,
        "skipped_lane_excluded_contract_count": skipped_lane_excluded_count,
        "skipped_actionable_contract_count": skipped_actionable_count,
        "skipped_lane_excluded_contracts": sorted(set(skipped_lane_excluded_targets)),
        "skipped_actionable_contracts": sorted(set(skipped_actionable_targets)),
        "failed_required_contract_count": failed_required,
        "failed_optional_contract_count": failed_optional,
        "failed_optional_contracts": sorted(set(failed_optional_targets)),
        "coverage_counter_overflow": coverage_counter_overflow,
        "discovery_counter_overflow": discovery_counter_overflow,
    }

    min_cov = args.min_required_contract_coverage
    coverage_gate_enabled = min_cov >= 0.0
    coverage_gate_failed = coverage_gate_enabled and coverage_rate < min_cov
    if coverage_gate_enabled:
        payload["min_required_contract_coverage"] = min_cov
        payload["coverage_gate_failed"] = coverage_gate_failed

    min_discovery_cov = args.min_discovery_required_coverage
    discovery_gate_enabled = min_discovery_cov >= 0.0
    discovery_gate_failed = (
        discovery_gate_enabled
        and discovery_required_total > 0
        and discovery_coverage_rate < min_discovery_cov
    )
    if discovery_gate_enabled:
        payload["min_discovery_required_coverage"] = min_discovery_cov
        payload["discovery_required_gate_failed"] = discovery_gate_failed

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for row in rows:
            print(
                f"[COVERAGE] {row['name']}: status={row['validator_status']} "
                f"required={row['required_contract']} reason={row['reason_code']} "
                f"evidence_ref={row['evidence_ref'] or '-'}"
            )
        print(
            "[COVERAGE] summary: "
            f"required_contract_total={required_total} "
            f"required_contract_passed={required_passed} "
            f"required_contract_coverage_rate={coverage_rate} "
            f"discovery_required_total={discovery_required_total} "
            f"discovery_required_passed={discovery_required_passed} "
            f"discovery_required_coverage_rate={discovery_coverage_rate} "
            f"skipped_contract_count={skipped_count} "
            f"skipped_lane_excluded_contract_count={skipped_lane_excluded_count} "
            f"skipped_actionable_contract_count={skipped_actionable_count} "
            f"failed_required_contract_count={failed_required} "
            f"failed_optional_contract_count={failed_optional}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if failed_required > 0:
        return 1
    if coverage_counter_overflow or discovery_counter_overflow:
        return 1
    if coverage_gate_failed:
        return 1
    if discovery_gate_failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
