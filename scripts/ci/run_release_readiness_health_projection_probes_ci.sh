#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/release-readiness-health-projection-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

python3 - <<'PY' "${TMP_DIR}"
from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path.cwd().resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from health_report_experience_writeback_projection_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    build_health_report_experience_writeback_closure_projection,
)
from release_readiness_check import (
    _hydrate_one_look_projection,
)

tmp_dir = Path(sys.argv[1]).resolve()
identity_id = "probe-release-readiness-health"
execution_report = (tmp_dir / "execution-report.json").resolve()
execution_report.write_text("{}\n", encoding="utf-8")


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def summary_template(*, mode: str, selected: list[str], failed_scripts: list[str], first_failed: str, boundary_status: str) -> dict:
    return {
        "selected_check_mode": mode,
        "selected_check_names": list(selected),
        "command_execution": {
            "failed_scripts": list(failed_scripts),
            "first_failed_script": first_failed,
        },
        "terminal_truth_boundary_projection": {
            "terminal_truth_boundary_projection_status": STATUS_PASS_REQUIRED,
            "repair_lane_status": STATUS_PASS_REQUIRED,
            "experience_writeback_validation_status": boundary_status,
            "terminal_truth_observation_status": STATUS_PASS_REQUIRED,
            "admission_lane_projection": "NOT_BLOCKED_BY_TERMINAL_TRUTH",
            "repair_success_not_clean_terminal_truth": False,
            "terminal_truth_class": "clean_terminal_truth",
            "terminal_state_class": "completed_clean",
        },
    }


pass_health_dir = (tmp_dir / "health-pass").resolve()
pass_report = pass_health_dir / f"identity-health-{identity_id}-1001.json"
write_json(
    pass_report,
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
            "report_run_id": "probe-readiness-health-pass",
            "writeback_status": "WRITTEN",
            "writeback_rule_id": "rule-entry-readiness-pass",
            "rulebook_match_count": 1,
            "task_history_contains_run_id": True,
            "stale_reasons": [],
        },
    },
)
pass_summary = summary_template(
    mode="full",
    selected=[],
    failed_scripts=[],
    first_failed="",
    boundary_status=STATUS_PASS_REQUIRED,
)
pass_projection = build_health_report_experience_writeback_closure_projection(
    identity_id=identity_id,
    health_report_dir=str(pass_health_dir),
    execution_report=str(execution_report),
    command_execution=pass_summary["command_execution"],
    selected_check_mode=pass_summary["selected_check_mode"],
    selected_check_names=pass_summary["selected_check_names"],
    boundary_experience_writeback_validation_status=pass_summary["terminal_truth_boundary_projection"][
        "experience_writeback_validation_status"
    ],
)
assert pass_projection["projection_status"] == STATUS_PASS_REQUIRED, pass_projection
assert pass_projection["health_report_collection_status"] == STATUS_PASS_REQUIRED, pass_projection
assert pass_projection["health_report_contract_status"] == STATUS_PASS_REQUIRED, pass_projection
assert pass_projection["execution_report_ref_matches"] is True, pass_projection
assert pass_projection["report_selected_path_matches_execution_report"] is True, pass_projection
assert pass_projection["validation_status"] == STATUS_PASS_REQUIRED, pass_projection
pass_summary["health_report_experience_writeback_closure"] = pass_projection
_hydrate_one_look_projection(pass_summary)
pass_one_look = pass_summary["one_look"]
assert pass_one_look["health_report_experience_writeback_projection_status"] == STATUS_PASS_REQUIRED, pass_one_look
assert pass_one_look["health_report_contract_status"] == STATUS_PASS_REQUIRED, pass_one_look
assert pass_one_look["health_report_experience_writeback_validation_status"] == STATUS_PASS_REQUIRED, pass_one_look
assert pass_one_look["health_report_selected_path_matches_execution_report"] is True, pass_one_look

skip_summary = summary_template(
    mode="targeted_subset",
    selected=["scripts/ci/run_terminal_truth_boundary_projection_probes_ci.sh"],
    failed_scripts=[],
    first_failed="",
    boundary_status=STATUS_SKIPPED_NOT_REQUIRED,
)
skip_projection = build_health_report_experience_writeback_closure_projection(
    identity_id=identity_id,
    health_report_dir=str((tmp_dir / "health-skip").resolve()),
    execution_report=str(execution_report),
    command_execution=skip_summary["command_execution"],
    selected_check_mode=skip_summary["selected_check_mode"],
    selected_check_names=skip_summary["selected_check_names"],
    boundary_experience_writeback_validation_status=skip_summary["terminal_truth_boundary_projection"][
        "experience_writeback_validation_status"
    ],
)
assert skip_projection["projection_status"] == STATUS_SKIPPED_NOT_REQUIRED, skip_projection
assert "post_execution_health_projection_not_selected" in skip_projection["stale_reasons"], skip_projection

blocked_summary = summary_template(
    mode="full",
    selected=[],
    failed_scripts=["scripts/validate_identity_protocol_version_alignment.py"],
    first_failed="scripts/validate_identity_protocol_version_alignment.py",
    boundary_status=STATUS_SKIPPED_NOT_REQUIRED,
)
blocked_projection = build_health_report_experience_writeback_closure_projection(
    identity_id=identity_id,
    health_report_dir=str((tmp_dir / "health-blocked").resolve()),
    execution_report=str(execution_report),
    command_execution=blocked_summary["command_execution"],
    selected_check_mode=blocked_summary["selected_check_mode"],
    selected_check_names=blocked_summary["selected_check_names"],
    boundary_experience_writeback_validation_status=blocked_summary["terminal_truth_boundary_projection"][
        "experience_writeback_validation_status"
    ],
)
assert blocked_projection["projection_status"] == STATUS_SKIPPED_NOT_REQUIRED, blocked_projection
assert blocked_projection["health_report_collection_status"] == STATUS_SKIPPED_NOT_REQUIRED, blocked_projection
assert blocked_projection["health_report_contract_status"] == STATUS_SKIPPED_NOT_REQUIRED, blocked_projection
assert "health_report_projection_blocked_by_upstream_failure" in blocked_projection["stale_reasons"], blocked_projection

fail_health_dir = (tmp_dir / "health-fail").resolve()
fail_report = fail_health_dir / f"identity-health-{identity_id}-2001.json"
write_json(
    fail_report,
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
            "report_run_id": "probe-readiness-health-fail",
            "writeback_status": "WRITTEN",
            "writeback_rule_id": "rule-entry-readiness-fail",
            "rulebook_match_count": 1,
            "task_history_contains_run_id": True,
            "stale_reasons": [],
        },
    },
)
fail_summary = summary_template(
    mode="full",
    selected=[],
    failed_scripts=[],
    first_failed="",
    boundary_status=STATUS_PASS_REQUIRED,
)
fail_projection = build_health_report_experience_writeback_closure_projection(
    identity_id=identity_id,
    health_report_dir=str(fail_health_dir),
    execution_report=str(execution_report),
    command_execution=fail_summary["command_execution"],
    selected_check_mode=fail_summary["selected_check_mode"],
    selected_check_names=fail_summary["selected_check_names"],
    boundary_experience_writeback_validation_status=fail_summary["terminal_truth_boundary_projection"][
        "experience_writeback_validation_status"
    ],
)
assert fail_projection["projection_status"] == STATUS_FAIL_REQUIRED, fail_projection
assert "health_report_boundary_validation_status_mismatch" in fail_projection["stale_reasons"], fail_projection

print(
    json.dumps(
        {
            "release_readiness_health_projection_probe_status": STATUS_PASS_REQUIRED,
            "pass_projection_status": pass_projection["projection_status"],
            "skip_projection_status": skip_projection["projection_status"],
            "blocked_projection_status": blocked_projection["projection_status"],
            "fail_projection_status": fail_projection["projection_status"],
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] release readiness health projection probes passed"
