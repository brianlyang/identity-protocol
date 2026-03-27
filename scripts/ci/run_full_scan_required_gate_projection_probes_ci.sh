#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

python3 - <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path.cwd().resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from full_identity_protocol_scan_projection_profile_common import (
    resolve_full_identity_protocol_scan_projection_profile,
)
from full_scan_required_gate_bundle_projection_common import (
    build_full_scan_required_gate_bundle_three_plane_projection,
)
from required_gate_bundle_projection_common import (
    build_projection_profile_excluded_required_gate_bundle_target_projection,
)

pass_projection = {
    "projection_status": "PASS_REQUIRED",
    "scope_class": "",
    "scope_reason": "",
    "failed_required_target_count": 0,
    "failed_target_names": [],
    "stale_reasons": [],
    "rows_without_projected_report_fields": [],
    "actor_id": "assistant:codex",
    "resolved_work_layer": "instance",
    "resolved_source_layer": "project",
    "lock_state": "LOCK_MATCH",
    "report_selected_path": "/tmp/full-scan-required-gate-probe.json",
    "report_selection_mode": "explicit_report_override",
    "report_selected_authority_class": "explicit_report_override",
    "report_pointer_resolution_mode": "explicit_report_override",
    "report_pointer_path": "",
}
pass_summary = build_full_scan_required_gate_bundle_three_plane_projection(
    pass_projection,
    prefix="required_gate_bundle",
)
assert pass_summary["required_gate_bundle_projection_status"] == "PASS_REQUIRED", pass_summary
assert pass_summary["required_gate_bundle_actor_id"] == "assistant:codex", pass_summary
assert pass_summary["required_gate_bundle_resolved_work_layer"] == "instance", pass_summary
assert pass_summary["required_gate_bundle_resolved_source_layer"] == "project", pass_summary
assert pass_summary["required_gate_bundle_lock_state"] == "LOCK_MATCH", pass_summary
assert pass_summary["required_gate_bundle_report_selected_path"] == "/tmp/full-scan-required-gate-probe.json", pass_summary
assert pass_summary["required_gate_bundle_report_selection_mode"] == "explicit_report_override", pass_summary
assert pass_summary["required_gate_bundle_report_authority_class"] == "explicit_report_override", pass_summary
assert pass_summary["required_gate_bundle_report_pointer_resolution_mode"] == "explicit_report_override", pass_summary
assert pass_summary["required_gate_bundle_report_pointer_path"] == "", pass_summary

shadow_summary = build_full_scan_required_gate_bundle_three_plane_projection(
    pass_projection,
    prefix="required_gate_bundle_shadow",
)
assert shadow_summary["required_gate_bundle_shadow_projection_status"] == "PASS_REQUIRED", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_actor_id"] == "assistant:codex", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_resolved_work_layer"] == "instance", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_resolved_source_layer"] == "project", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_lock_state"] == "LOCK_MATCH", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_report_selection_mode"] == "explicit_report_override", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_report_authority_class"] == "explicit_report_override", shadow_summary

profile = resolve_full_identity_protocol_scan_projection_profile("terminal_truth_boundary_projection")
excluded_projection = build_projection_profile_excluded_required_gate_bundle_target_projection(
    profile_id=profile.profile_id,
    execution_mode=profile.execution_mode,
    description=profile.description,
    excluded_area="required_gate_bundle_projection",
    owner_surface="full_identity_protocol_scan_summary",
)
excluded_summary = build_full_scan_required_gate_bundle_three_plane_projection(
    excluded_projection,
    prefix="required_gate_bundle",
)
assert excluded_summary["required_gate_bundle_projection_status"] == "SKIPPED_NOT_REQUIRED", excluded_summary
assert excluded_summary["required_gate_bundle_scope_class"] == "bounded_projection_profile_exclusion", excluded_summary
assert excluded_summary["required_gate_bundle_scope_reason"] == "projection_profile_out_of_scope", excluded_summary
assert excluded_summary["required_gate_bundle_actor_id"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_resolved_work_layer"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_resolved_source_layer"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_lock_state"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_selected_path"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_selection_mode"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_authority_class"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_pointer_resolution_mode"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_pointer_path"] == "", excluded_summary

print(
    json.dumps(
        {
            "full_scan_required_gate_projection_probe_status": "PASS_REQUIRED",
            "pass_projection_status": pass_summary["required_gate_bundle_projection_status"],
            "excluded_projection_status": excluded_summary["required_gate_bundle_projection_status"],
            "excluded_scope_class": excluded_summary["required_gate_bundle_scope_class"],
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] full-scan required-gate projection probes passed"
