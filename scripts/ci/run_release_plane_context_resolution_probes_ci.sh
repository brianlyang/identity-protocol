#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

PYTHONPATH="${REPO_ROOT}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
python3 - <<'PY'
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from resolve_release_plane_cloud_evidence import (
    resolve_release_plane_context,
    resolve_release_plane_runtime_inputs,
)

no_context = resolve_release_plane_context(
    default_target_branch="main",
    default_release_head_sha="deadbeef",
    env={},
)
assert no_context["release_plane_context_requested"] is False, no_context
assert no_context["release_plane_context_sources"] == [], no_context
for key in (
    "target_branch",
    "release_head_sha",
    "required_gates_run_id",
    "run_url",
    "workflow_file_sha",
    "run_head_sha",
    "run_workflow_file_sha",
):
    assert no_context[key] == "", (key, no_context)

baseline_only = resolve_release_plane_context(
    explicit_target_branch="main",
    default_target_branch="main",
    default_release_head_sha="feedface",
    env={},
)
assert baseline_only["release_plane_context_requested"] is True, baseline_only
assert "explicit_target_branch" in baseline_only["release_plane_context_sources"], baseline_only
assert baseline_only["target_branch"] == "main", baseline_only
assert baseline_only["release_head_sha"] == "feedface", baseline_only
assert baseline_only["workflow_file_sha"] == "feedface", baseline_only
assert baseline_only["run_head_sha"] == "feedface", baseline_only
assert baseline_only["run_workflow_file_sha"] == "feedface", baseline_only
assert baseline_only["required_gates_run_id"] == "", baseline_only
assert baseline_only["run_url"] == "", baseline_only

ambient_github = resolve_release_plane_context(
    default_target_branch="main",
    default_release_head_sha="cafebabe",
    env={
        "GITHUB_RUN_ID": "12345",
        "GITHUB_REPOSITORY": "openai/example",
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REF_NAME": "release/test",
    },
)
assert ambient_github["release_plane_context_requested"] is True, ambient_github
assert "ambient_github_run_url" in ambient_github["release_plane_context_sources"], ambient_github
assert ambient_github["target_branch"] == "release/test", ambient_github
assert ambient_github["release_head_sha"] == "cafebabe", ambient_github
assert ambient_github["required_gates_run_id"] == "12345", ambient_github
assert ambient_github["run_url"] == "https://github.com/openai/example/actions/runs/12345", ambient_github
assert ambient_github["workflow_file_sha"] == "cafebabe", ambient_github
assert ambient_github["run_head_sha"] == "cafebabe", ambient_github
assert ambient_github["run_workflow_file_sha"] == "cafebabe", ambient_github

checks_json_context = resolve_release_plane_context(
    explicit_checks_json="/tmp/checks.json",
    default_target_branch="main",
    default_release_head_sha="beadfeed",
    env={},
)
assert checks_json_context["release_plane_context_requested"] is True, checks_json_context
assert checks_json_context["checks_json"] == "/tmp/checks.json", checks_json_context
assert checks_json_context["release_head_sha"] == "beadfeed", checks_json_context

no_context_runtime = resolve_release_plane_runtime_inputs(
    identity_id="probe",
    operation="three-plane",
    default_target_branch="main",
    default_release_head_sha="deadbeef",
    env={},
)
assert no_context_runtime["release_plane_context_requested"] is False, no_context_runtime
assert no_context_runtime["target_branch"] == "", no_context_runtime
assert no_context_runtime["release_head_sha"] == "", no_context_runtime
assert no_context_runtime["release_adapter_payload"]["release_cloud_evidence_adapter_status"] == "SKIPPED_NOT_REQUIRED", no_context_runtime
assert no_context_runtime["release_adapter_payload"]["stale_reasons"] == [], no_context_runtime

with tempfile.TemporaryDirectory() as tmpdir:
    gh_runs_path = Path(tmpdir) / "gh-runs.json"
    gh_runs_path.write_text(json.dumps([
        {
            "databaseId": 301,
            "headBranch": "release/probe",
            "headSha": "feedbead",
            "url": "https://github.com/openai/example/actions/runs/301",
            "workflowName": "required-gates",
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-03-28T00:00:00Z",
        },
        {
            "databaseId": 300,
            "headBranch": "release/probe",
            "headSha": "feedbead",
            "url": "https://github.com/openai/example/actions/runs/300",
            "workflowName": "release-cloud",
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-03-27T23:59:00Z",
        },
    ], ensure_ascii=False), encoding="utf-8")
    gh_runtime = resolve_release_plane_runtime_inputs(
        identity_id="probe",
        operation="three-plane",
        explicit_target_branch="release/probe",
        explicit_gh_runs_json=str(gh_runs_path),
        default_release_head_sha="feedbead",
        github_repository="openai/example",
        env={},
    )
    assert gh_runtime["release_plane_context_requested"] is True, gh_runtime
    assert gh_runtime["release_head_sha"] == "feedbead", gh_runtime
    assert gh_runtime["required_gates_run_id"] == "301", gh_runtime
    assert gh_runtime["run_url"] == "https://github.com/openai/example/actions/runs/301", gh_runtime
    assert gh_runtime["checks_json"], gh_runtime
    assert gh_runtime["release_adapter_payload"]["adapter_source_kind"] == "gh_run_list_json", gh_runtime
    assert gh_runtime["release_adapter_payload"]["release_cloud_evidence_adapter_status"] == "PASS_REQUIRED", gh_runtime

print(json.dumps({
    "release_plane_context_resolution_probe_status": "PASS_REQUIRED",
    "no_context_requested": no_context["release_plane_context_requested"],
    "baseline_only_sources": baseline_only["release_plane_context_sources"],
    "ambient_run_url": ambient_github["run_url"],
    "runtime_inputs_no_context_adapter_status": no_context_runtime["release_adapter_payload"]["release_cloud_evidence_adapter_status"],
}, ensure_ascii=False))
PY

echo "[PASS] release plane context resolution probes passed"
