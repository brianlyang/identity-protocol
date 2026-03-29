#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseReadinessPostClosureAdjudicationStageSpec:
    stage_id: str
    validator_command: tuple[str, ...] = ()
    probe_command: tuple[str, ...] = ()


RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_SPECS: tuple[
    ReleaseReadinessPostClosureAdjudicationStageSpec, ...
] = (
    ReleaseReadinessPostClosureAdjudicationStageSpec(
        stage_id="runtime_summary_surface_governance",
        probe_command=("bash", "scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh"),
    ),
    ReleaseReadinessPostClosureAdjudicationStageSpec(
        stage_id="one_look_topology",
        validator_command=(
            "python3",
            "scripts/validate_release_readiness_one_look_topology.py",
            "--json-only",
        ),
        probe_command=("bash", "scripts/ci/run_release_readiness_one_look_topology_probes_ci.sh"),
    ),
    ReleaseReadinessPostClosureAdjudicationStageSpec(
        stage_id="repo_global_closure_topology",
        validator_command=(
            "python3",
            "scripts/validate_release_readiness_repo_global_closure_topology.py",
            "--json-only",
        ),
        probe_command=(
            "bash",
            "scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh",
        ),
    ),
    ReleaseReadinessPostClosureAdjudicationStageSpec(
        stage_id="active_runtime_closure_topology",
        validator_command=(
            "python3",
            "scripts/validate_release_readiness_active_runtime_closure_topology.py",
            "--json-only",
        ),
        probe_command=(
            "bash",
            "scripts/ci/run_release_readiness_active_runtime_closure_topology_probes_ci.sh",
        ),
    ),
    ReleaseReadinessPostClosureAdjudicationStageSpec(
        stage_id="terminal_truth_bridge",
        validator_command=(
            "python3",
            "scripts/validate_release_readiness_terminal_truth_bridge.py",
            "--json-only",
        ),
        probe_command=(
            "bash",
            "scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh",
        ),
    ),
    ReleaseReadinessPostClosureAdjudicationStageSpec(
        stage_id="governance_probe_topology",
        validator_command=(
            "python3",
            "scripts/validate_release_readiness_governance_probe_topology.py",
            "--json-only",
        ),
        probe_command=(
            "bash",
            "scripts/ci/run_release_readiness_governance_probe_topology_probes_ci.sh",
        ),
    ),
)

RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER: tuple[str, ...] = tuple(
    spec.stage_id for spec in RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_SPECS
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_COMMAND_SEQUENCE: tuple[tuple[str, ...], ...] = tuple(
    command
    for spec in RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_SPECS
    for command in (spec.validator_command, spec.probe_command)
    if command
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER = (
    "release_readiness_post_closure_adjudication_order="
    + "|".join(RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER)
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_MARKERS: tuple[str, ...] = tuple(
    f"release_readiness_post_closure_adjudication_stage={stage_id}"
    for stage_id in RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_VALIDATOR = (
    "scripts/validate_release_readiness_post_closure_adjudication_topology.py"
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE = (
    "scripts/ci/run_release_readiness_post_closure_adjudication_topology_probes_ci.sh"
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_VALIDATOR_COMMAND: tuple[str, ...] = (
    "python3",
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_VALIDATOR,
    "--json-only",
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_COMMAND: tuple[str, ...] = (
    "bash",
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE,
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROOF_LANES: tuple[str, ...] = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_VALIDATOR,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE,
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_SUMMARY_KEY = (
    "release_readiness_post_closure_adjudication_topology_probe"
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_ONE_LOOK_FIELD = (
    "release_readiness_post_closure_adjudication_topology_probe_status"
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_STATUS_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_ONE_LOOK_FIELD,
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_KEEP_FIELDS: tuple[str, ...] = (
    "positive_validator_output",
)
RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
    *RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_MARKERS,
    *RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROOF_LANES,
)
