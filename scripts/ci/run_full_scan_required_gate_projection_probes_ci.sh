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
    FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_MARKER,
    FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
    build_full_scan_required_gate_bundle_three_plane_projection,
    build_full_scan_required_gate_bundle_projection_summary_skeleton,
)
from required_gate_bundle_projection_common import (
    build_projection_profile_excluded_required_gate_bundle_target_projection,
)

pass_projection = {
    "bundle_status": "PASS_REQUIRED",
    "projection_status": "PASS_REQUIRED",
    "scope_class": "",
    "scope_reason": "",
    "failed_required_target_count": 0,
    "failed_target_names": [],
    "stale_reasons": [],
    "rows_without_projected_report_fields": [],
    "missing_mapping_requirements": ["rq_missing_projection_mapping"],
    "actor_id": "assistant:codex",
    "resolved_work_layer": "instance",
    "resolved_source_layer": "project",
    "lock_state": "LOCK_MATCH",
    "run_id_binding": "run:full-scan-required-gate-probe",
    "report_selected_path": "/tmp/full-scan-required-gate-probe.json",
    "report_logical_identity_key": '{"identity_id":"probe-identity","run_id":"run:full-scan-required-gate-probe","catalog_path":"/tmp/catalog.local.yaml","resolved_pack_path":"/tmp/.identity/probe-identity","identity_prompt_sha256":"prompt-sha"}',
    "report_selection_mode": "explicit_report_override",
    "report_selected_authority_class": "explicit_report_override",
    "report_pointer_resolution_mode": "explicit_report_override",
    "report_pointer_path": "",
}
pass_summary = build_full_scan_required_gate_bundle_three_plane_projection(
    pass_projection,
    prefix="required_gate_bundle",
)
assert pass_summary["required_gate_bundle_status"] == "PASS_REQUIRED", pass_summary
assert pass_summary["required_gate_bundle_projection_status"] == "PASS_REQUIRED", pass_summary
assert pass_summary["required_gate_bundle_actor_id"] == "assistant:codex", pass_summary
assert pass_summary["required_gate_bundle_resolved_work_layer"] == "instance", pass_summary
assert pass_summary["required_gate_bundle_resolved_source_layer"] == "project", pass_summary
assert pass_summary["required_gate_bundle_lock_state"] == "LOCK_MATCH", pass_summary
assert pass_summary["required_gate_bundle_run_id_binding"] == "run:full-scan-required-gate-probe", pass_summary
assert pass_summary["required_gate_bundle_report_selected_path"] == "/tmp/full-scan-required-gate-probe.json", pass_summary
assert pass_summary["required_gate_bundle_report_logical_identity_key"] == pass_projection["report_logical_identity_key"], pass_summary
assert pass_summary["required_gate_bundle_report_selection_mode"] == "explicit_report_override", pass_summary
assert pass_summary["required_gate_bundle_report_authority_class"] == "explicit_report_override", pass_summary
assert pass_summary["required_gate_bundle_report_pointer_resolution_mode"] == "explicit_report_override", pass_summary
assert pass_summary["required_gate_bundle_report_pointer_path"] == "", pass_summary
assert pass_summary["required_gate_bundle_missing_mapping_requirements"] == ["rq_missing_projection_mapping"], pass_summary

shadow_summary = build_full_scan_required_gate_bundle_three_plane_projection(
    pass_projection,
    prefix="required_gate_bundle_shadow",
)
assert shadow_summary["required_gate_bundle_shadow_status"] == "PASS_REQUIRED", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_projection_status"] == "PASS_REQUIRED", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_actor_id"] == "assistant:codex", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_resolved_work_layer"] == "instance", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_resolved_source_layer"] == "project", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_lock_state"] == "LOCK_MATCH", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_run_id_binding"] == "run:full-scan-required-gate-probe", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_report_logical_identity_key"] == pass_projection["report_logical_identity_key"], shadow_summary
assert shadow_summary["required_gate_bundle_shadow_report_selection_mode"] == "explicit_report_override", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_report_authority_class"] == "explicit_report_override", shadow_summary
assert shadow_summary["required_gate_bundle_shadow_missing_mapping_requirements"] == [
    "rq_missing_projection_mapping"
], shadow_summary

scan_probe_summary = build_full_scan_required_gate_bundle_three_plane_projection(
    pass_projection,
    prefix="required_gate_bundle_scan_probe",
)
assert scan_probe_summary["required_gate_bundle_scan_probe_status"] == "PASS_REQUIRED", scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_projection_status"] == "PASS_REQUIRED", scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_actor_id"] == "assistant:codex", scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_resolved_work_layer"] == "instance", scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_resolved_source_layer"] == "project", scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_lock_state"] == "LOCK_MATCH", scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_run_id_binding"] == "run:full-scan-required-gate-probe", scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_report_logical_identity_key"] == pass_projection["report_logical_identity_key"], scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_report_selection_mode"] == "explicit_report_override", scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_report_authority_class"] == "explicit_report_override", scan_probe_summary
assert scan_probe_summary["required_gate_bundle_scan_probe_missing_mapping_requirements"] == [
    "rq_missing_projection_mapping"
], scan_probe_summary

summary_skeleton = build_full_scan_required_gate_bundle_projection_summary_skeleton()
assert summary_skeleton["identities_with_projection"] == 0, summary_skeleton
assert summary_skeleton["projection_pass"] == 0, summary_skeleton
assert summary_skeleton["projection_fail"] == 0, summary_skeleton
assert summary_skeleton["projection_skipped_not_required"] == 0, summary_skeleton
assert summary_skeleton["projection_fail_identity_ids"] == [], summary_skeleton
assert summary_skeleton["projection_scope_excluded_identity_ids"] == [], summary_skeleton
assert summary_skeleton["rows_without_projected_report_fields"] == [], summary_skeleton
assert summary_skeleton["missing_mapping_requirements"] == [], summary_skeleton
assert summary_skeleton["projection_stale_reasons"] == [], summary_skeleton
assert FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_MARKER in FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS, (
    FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_MARKER,
    FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
)

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
assert excluded_summary["required_gate_bundle_status"] == "SKIPPED_NOT_REQUIRED", excluded_summary
assert excluded_summary["required_gate_bundle_projection_status"] == "SKIPPED_NOT_REQUIRED", excluded_summary
assert excluded_summary["required_gate_bundle_scope_class"] == "bounded_projection_profile_exclusion", excluded_summary
assert excluded_summary["required_gate_bundle_scope_reason"] == "projection_profile_out_of_scope", excluded_summary
assert excluded_summary["required_gate_bundle_actor_id"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_resolved_work_layer"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_resolved_source_layer"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_lock_state"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_run_id_binding"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_selected_path"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_logical_identity_key"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_selection_mode"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_authority_class"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_pointer_resolution_mode"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_report_pointer_path"] == "", excluded_summary
assert excluded_summary["required_gate_bundle_missing_mapping_requirements"] == [], excluded_summary

excluded_scan_probe_summary = build_full_scan_required_gate_bundle_three_plane_projection(
    excluded_projection,
    prefix="required_gate_bundle_scan_probe",
)
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_status"] == "SKIPPED_NOT_REQUIRED", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_projection_status"] == "SKIPPED_NOT_REQUIRED", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_scope_class"] == "bounded_projection_profile_exclusion", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_scope_reason"] == "projection_profile_out_of_scope", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_actor_id"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_resolved_work_layer"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_resolved_source_layer"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_lock_state"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_run_id_binding"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_report_selected_path"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_report_logical_identity_key"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_report_selection_mode"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_report_authority_class"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_report_pointer_resolution_mode"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_report_pointer_path"] == "", excluded_scan_probe_summary
assert excluded_scan_probe_summary["required_gate_bundle_scan_probe_missing_mapping_requirements"] == [], excluded_scan_probe_summary

print(
    json.dumps(
        {
            "full_scan_required_gate_projection_probe_status": "PASS_REQUIRED",
            "pass_projection_status": pass_summary["required_gate_bundle_projection_status"],
            "excluded_projection_status": excluded_summary["required_gate_bundle_projection_status"],
            "scan_probe_projection_status": scan_probe_summary["required_gate_bundle_scan_probe_projection_status"],
            "excluded_scope_class": excluded_summary["required_gate_bundle_scope_class"],
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] full-scan required-gate projection probes passed"
