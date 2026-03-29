#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseClosureRootGroundingLaneSpec:
    lane_id: str
    validator_rel: str
    probe_rel: str


RELEASE_CLOSURE_ROOT_GROUNDING_LANE_SPECS: tuple[
    ReleaseClosureRootGroundingLaneSpec, ...
] = (
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_corpus_precedence",
        validator_rel="scripts/validate_protocol_root_corpus_precedence.py",
        probe_rel="scripts/ci/run_protocol_root_corpus_precedence_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_corpus_question_routing",
        validator_rel="scripts/validate_protocol_root_corpus_question_routing.py",
        probe_rel="scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_design_question_closure",
        validator_rel="scripts/validate_protocol_root_design_question_closure.py",
        probe_rel="scripts/ci/run_protocol_root_design_question_closure_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_stream_design_admissibility",
        validator_rel="scripts/validate_protocol_root_stream_design_admissibility.py",
        probe_rel="scripts/ci/run_protocol_root_stream_design_admissibility_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_machine_law_primacy",
        validator_rel="scripts/validate_protocol_root_machine_law_primacy.py",
        probe_rel="scripts/ci/run_protocol_root_machine_law_primacy_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_machine_world_ontology",
        validator_rel="scripts/validate_protocol_root_machine_world_ontology.py",
        probe_rel="scripts/ci/run_protocol_root_machine_world_ontology_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_truth_lifecycle",
        validator_rel="scripts/validate_protocol_root_truth_lifecycle.py",
        probe_rel="scripts/ci/run_protocol_root_truth_lifecycle_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_current_truth_epistemology",
        validator_rel="scripts/validate_protocol_root_current_truth_epistemology.py",
        probe_rel="scripts/ci/run_protocol_root_current_truth_epistemology_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_protocol_instance_responsibility",
        validator_rel="scripts/validate_protocol_root_protocol_instance_responsibility.py",
        probe_rel="scripts/ci/run_protocol_root_protocol_instance_responsibility_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_decision_evidence_admissibility",
        validator_rel="scripts/validate_protocol_root_decision_evidence_admissibility.py",
        probe_rel="scripts/ci/run_protocol_root_decision_evidence_admissibility_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_success_path_state_admissibility",
        validator_rel="scripts/validate_protocol_root_success_path_state_admissibility.py",
        probe_rel="scripts/ci/run_protocol_root_success_path_state_admissibility_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_entry_surface_legitimacy",
        validator_rel="scripts/validate_protocol_root_entry_surface_legitimacy.py",
        probe_rel="scripts/ci/run_protocol_root_entry_surface_legitimacy_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_error_terminality",
        validator_rel="scripts/validate_protocol_root_error_terminality.py",
        probe_rel="scripts/ci/run_protocol_root_error_terminality_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_artifact_family_admissibility",
        validator_rel="scripts/validate_protocol_root_artifact_family_admissibility.py",
        probe_rel="scripts/ci/run_protocol_root_artifact_family_admissibility_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_prompt_bootstrap",
        validator_rel="scripts/validate_protocol_root_prompt_bootstrap.py",
        probe_rel="scripts/ci/run_protocol_root_prompt_bootstrap_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_identity_discovery",
        validator_rel="scripts/validate_protocol_root_identity_discovery.py",
        probe_rel="scripts/ci/run_protocol_root_identity_discovery_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_agent_handoff",
        validator_rel="scripts/validate_protocol_root_agent_handoff.py",
        probe_rel="scripts/ci/run_protocol_root_agent_handoff_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_identity_instance_self_judgement",
        validator_rel="scripts/validate_protocol_root_identity_instance_self_judgement.py",
        probe_rel="scripts/ci/run_protocol_root_identity_instance_self_judgement_probes_ci.sh",
    ),
    ReleaseClosureRootGroundingLaneSpec(
        lane_id="protocol_root_operator_answer_surface",
        validator_rel="scripts/validate_protocol_root_operator_answer_surface.py",
        probe_rel="scripts/ci/run_protocol_root_operator_answer_surface_probes_ci.sh",
    ),
)

RELEASE_CLOSURE_ROOT_GROUNDING_ORDER: tuple[str, ...] = tuple(
    spec.lane_id for spec in RELEASE_CLOSURE_ROOT_GROUNDING_LANE_SPECS
)
RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER = (
    "release_closure_root_grounding_order="
    + "|".join(RELEASE_CLOSURE_ROOT_GROUNDING_ORDER)
)
RELEASE_CLOSURE_ROOT_GROUNDING_LANE_MARKERS: tuple[str, ...] = tuple(
    f"release_closure_root_grounding_lane={lane_id}"
    for lane_id in RELEASE_CLOSURE_ROOT_GROUNDING_ORDER
)
RELEASE_CLOSURE_ROOT_GROUNDING_VALIDATOR_PATHS: tuple[str, ...] = tuple(
    spec.validator_rel for spec in RELEASE_CLOSURE_ROOT_GROUNDING_LANE_SPECS
)
RELEASE_CLOSURE_ROOT_GROUNDING_PROBE_PATHS: tuple[str, ...] = tuple(
    spec.probe_rel for spec in RELEASE_CLOSURE_ROOT_GROUNDING_LANE_SPECS
)
RELEASE_CLOSURE_ROOT_GROUNDING_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER,
    *RELEASE_CLOSURE_ROOT_GROUNDING_LANE_MARKERS,
    *RELEASE_CLOSURE_ROOT_GROUNDING_VALIDATOR_PATHS,
    *RELEASE_CLOSURE_ROOT_GROUNDING_PROBE_PATHS,
)
