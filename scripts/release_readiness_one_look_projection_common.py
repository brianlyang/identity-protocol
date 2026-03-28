#!/usr/bin/env python3
from __future__ import annotations

from health_report_experience_writeback_projection_common import (
    apply_release_readiness_health_report_experience_writeback_one_look,
)
from release_cloud_evidence_projection_common import (
    apply_release_readiness_release_cloud_evidence_one_look,
)
from release_readiness_foundational_projection_common import (
    apply_release_readiness_foundational_one_look,
)
from release_readiness_active_runtime_closure_projection_common import (
    apply_release_readiness_active_runtime_closure_one_look,
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


def build_release_readiness_one_look_projection(summary: dict[str, Any]) -> dict[str, Any]:
    one_look: dict[str, object] = {}
    apply_release_readiness_foundational_one_look(summary, one_look)
    apply_release_readiness_support_preflight_one_look(summary, one_look)
    apply_release_readiness_selected_check_scope_one_look(summary, one_look)
    apply_release_readiness_release_cloud_evidence_one_look(summary, one_look)
    apply_release_readiness_terminal_truth_boundary_one_look(summary, one_look)
    apply_release_readiness_health_report_experience_writeback_one_look(summary, one_look)
    apply_release_readiness_required_gate_bundle_one_look(summary, one_look)
    apply_release_readiness_repo_global_closure_one_look(summary, one_look)
    apply_release_readiness_active_runtime_closure_one_look(summary, one_look)
    apply_release_readiness_governance_probe_one_look(summary, one_look)
    return one_look
