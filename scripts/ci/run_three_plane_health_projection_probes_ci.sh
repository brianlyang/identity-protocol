#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/three-plane-health-projection-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

python3 - <<'PY' "${TMP_DIR}"
from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path.cwd().resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from health_report_experience_writeback_projection_common import (
    HEALTH_REPORT_EXPERIENCE_WRITEBACK_CLOSURE_EXCLUDED_AREA,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
)
from report_three_plane_status import _build_three_plane_health_report_experience_writeback_closure
from three_plane_projection_profile_common import resolve_three_plane_projection_profile

tmp_dir = Path(sys.argv[1]).resolve()
identity_id = "probe-three-plane-health"
execution_report = (tmp_dir / "execution-report.json").resolve()
execution_report.write_text("{}\n", encoding="utf-8")


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


pass_health_dir = (tmp_dir / "health-pass").resolve()
write_json(
    pass_health_dir / f"identity-health-{identity_id}-1001.json",
    {
        "identity_id": identity_id,
        "execution_report_ref": str(execution_report),
        "experience_writeback_closure": {
            "status": "PASS",
            "validation_status": STATUS_PASS_REQUIRED,
            "report_selected_path": str(execution_report),
            "report_selection_mode": "explicit_report",
            "report_selected_authority_class": "explicit_report_argument",
            "report_pointer_resolution_mode": "explicit_report",
            "report_run_id": "probe-three-plane-health-pass",
            "writeback_status": "WRITTEN",
            "writeback_rule_id": "rule-entry-three-plane-pass",
            "rulebook_match_count": 1,
            "task_history_contains_run_id": True,
            "stale_reasons": [],
        },
    },
)

pass_projection = _build_three_plane_health_report_experience_writeback_closure(
    projection_profile=resolve_three_plane_projection_profile("full"),
    identity_id=identity_id,
    health_report_dir=str(pass_health_dir),
    execution_report_path=execution_report,
    boundary_experience_writeback_validation_status=STATUS_PASS_REQUIRED,
    failed_scripts=[],
    first_failed_script="",
)
assert pass_projection["projection_status"] == STATUS_PASS_REQUIRED, pass_projection
assert pass_projection["health_report_collection_status"] == STATUS_PASS_REQUIRED, pass_projection
assert pass_projection["health_report_contract_status"] == STATUS_PASS_REQUIRED, pass_projection
assert pass_projection["report_selected_path_matches_execution_report"] is True, pass_projection
assert pass_projection["validation_status"] == STATUS_PASS_REQUIRED, pass_projection

projection_only = _build_three_plane_health_report_experience_writeback_closure(
    projection_profile=resolve_three_plane_projection_profile("terminal_truth_boundary_projection"),
    identity_id=identity_id,
    health_report_dir=str(pass_health_dir),
    execution_report_path=execution_report,
    boundary_experience_writeback_validation_status=STATUS_PASS_REQUIRED,
    failed_scripts=[],
    first_failed_script="",
)
assert projection_only["projection_status"] == STATUS_SKIPPED_NOT_REQUIRED, projection_only
assert projection_only["projection_skip_status"] == STATUS_SKIPPED_NOT_REQUIRED, projection_only
assert projection_only["projection_excluded_area"] == HEALTH_REPORT_EXPERIENCE_WRITEBACK_CLOSURE_EXCLUDED_AREA, projection_only
assert projection_only["validation_status"] == STATUS_SKIPPED_NOT_REQUIRED, projection_only

fail_health_dir = (tmp_dir / "health-fail").resolve()
write_json(
    fail_health_dir / f"identity-health-{identity_id}-2001.json",
    {
        "identity_id": identity_id,
        "execution_report_ref": str(execution_report),
        "experience_writeback_closure": {
            "status": "PASS",
            "validation_status": STATUS_FAIL_REQUIRED,
            "report_selected_path": str(execution_report),
            "report_selection_mode": "explicit_report",
            "report_selected_authority_class": "explicit_report_argument",
            "report_pointer_resolution_mode": "explicit_report",
            "report_run_id": "probe-three-plane-health-fail",
            "writeback_status": "WRITTEN",
            "writeback_rule_id": "rule-entry-three-plane-fail",
            "rulebook_match_count": 1,
            "task_history_contains_run_id": True,
            "stale_reasons": [],
        },
    },
)

fail_projection = _build_three_plane_health_report_experience_writeback_closure(
    projection_profile=resolve_three_plane_projection_profile("full"),
    identity_id=identity_id,
    health_report_dir=str(fail_health_dir),
    execution_report_path=execution_report,
    boundary_experience_writeback_validation_status=STATUS_PASS_REQUIRED,
    failed_scripts=[],
    first_failed_script="",
)
assert fail_projection["projection_status"] == STATUS_FAIL_REQUIRED, fail_projection
assert "health_report_boundary_validation_status_mismatch" in fail_projection["stale_reasons"], fail_projection

print(
    json.dumps(
        {
            "three_plane_health_projection_probe_status": STATUS_PASS_REQUIRED,
            "pass_projection_status": pass_projection["projection_status"],
            "projection_only_status": projection_only["projection_status"],
            "fail_projection_status": fail_projection["projection_status"],
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] three-plane health projection probes passed"
