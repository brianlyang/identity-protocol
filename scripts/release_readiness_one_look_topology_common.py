#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from health_report_experience_writeback_projection_common import (
    apply_release_readiness_health_report_experience_writeback_one_look,
)
from release_cloud_evidence_projection_common import (
    apply_release_readiness_release_cloud_evidence_one_look,
)
from release_readiness_active_runtime_closure_projection_common import (
    apply_release_readiness_active_runtime_closure_one_look,
)
from release_readiness_foundational_projection_common import (
    apply_release_readiness_foundational_one_look,
)
from release_readiness_governance_probe_projection_common import (
    apply_release_readiness_governance_probe_one_look,
)
from release_readiness_repo_global_closure_projection_common import (
    apply_release_readiness_repo_global_closure_one_look,
)
from release_readiness_required_gate_bundle_projection_common import (
    apply_release_readiness_required_gate_bundle_one_look,
)
from release_readiness_selected_check_scope_common import (
    apply_release_readiness_selected_check_scope_one_look,
)
from release_readiness_support_preflight_projection_common import (
    apply_release_readiness_support_preflight_one_look,
)
from terminal_truth_boundary_projection_common import (
    apply_release_readiness_terminal_truth_boundary_one_look,
)


@dataclass(frozen=True)
class ReleaseReadinessOneLookFamilySpec:
    family_id: str
    applier_name: str
    applier: Callable[[dict[str, object], dict[str, object]], None]


RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS: tuple[ReleaseReadinessOneLookFamilySpec, ...] = (
    ReleaseReadinessOneLookFamilySpec(
        family_id="foundational",
        applier_name="apply_release_readiness_foundational_one_look",
        applier=apply_release_readiness_foundational_one_look,
    ),
    ReleaseReadinessOneLookFamilySpec(
        family_id="support_preflight",
        applier_name="apply_release_readiness_support_preflight_one_look",
        applier=apply_release_readiness_support_preflight_one_look,
    ),
    ReleaseReadinessOneLookFamilySpec(
        family_id="selected_check_scope",
        applier_name="apply_release_readiness_selected_check_scope_one_look",
        applier=apply_release_readiness_selected_check_scope_one_look,
    ),
    ReleaseReadinessOneLookFamilySpec(
        family_id="release_cloud_evidence",
        applier_name="apply_release_readiness_release_cloud_evidence_one_look",
        applier=apply_release_readiness_release_cloud_evidence_one_look,
    ),
    ReleaseReadinessOneLookFamilySpec(
        family_id="terminal_truth_boundary",
        applier_name="apply_release_readiness_terminal_truth_boundary_one_look",
        applier=apply_release_readiness_terminal_truth_boundary_one_look,
    ),
    ReleaseReadinessOneLookFamilySpec(
        family_id="health_report_experience_writeback",
        applier_name="apply_release_readiness_health_report_experience_writeback_one_look",
        applier=apply_release_readiness_health_report_experience_writeback_one_look,
    ),
    ReleaseReadinessOneLookFamilySpec(
        family_id="required_gate_bundle",
        applier_name="apply_release_readiness_required_gate_bundle_one_look",
        applier=apply_release_readiness_required_gate_bundle_one_look,
    ),
    ReleaseReadinessOneLookFamilySpec(
        family_id="repo_global_closure",
        applier_name="apply_release_readiness_repo_global_closure_one_look",
        applier=apply_release_readiness_repo_global_closure_one_look,
    ),
    ReleaseReadinessOneLookFamilySpec(
        family_id="active_runtime_closure",
        applier_name="apply_release_readiness_active_runtime_closure_one_look",
        applier=apply_release_readiness_active_runtime_closure_one_look,
    ),
    ReleaseReadinessOneLookFamilySpec(
        family_id="governance_probe",
        applier_name="apply_release_readiness_governance_probe_one_look",
        applier=apply_release_readiness_governance_probe_one_look,
    ),
)

RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER: tuple[str, ...] = tuple(
    spec.family_id for spec in RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS
)
RELEASE_READINESS_ONE_LOOK_FAMILY_APPLIER_NAMES: tuple[str, ...] = tuple(
    spec.applier_name for spec in RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS
)
RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER = (
    "release_readiness_one_look_family_order="
    + "|".join(RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER)
)
RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER,
    *(
        f"release_readiness_one_look_family={family_id}"
        for family_id in RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER
    ),
)


def apply_release_readiness_one_look_families(
    summary: dict[str, object],
    one_look: dict[str, object],
) -> None:
    if not isinstance(one_look, dict):
        return
    for spec in RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS:
        spec.applier(summary, one_look)
