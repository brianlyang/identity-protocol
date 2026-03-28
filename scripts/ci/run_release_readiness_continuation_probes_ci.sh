#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKSPACE_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/release-readiness-continuation-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}"

PYTHONPATH="${REPO_ROOT}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
python3 - "${REPO_ROOT}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from governed_runtime_summary_surface_common import build_governed_runtime_summary_surface_payload
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
)
from release_readiness_selected_check_scope_common import (
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
)

surface = build_governed_runtime_summary_surface_payload("release_readiness_summary")
constraints = tuple(surface.get("operational_constraints") or [])
missing = [
    marker
    for marker in (
        *RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
        *RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
        *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
    )
    if marker not in constraints
]
if missing:
    raise SystemExit(json.dumps({"missing_surface_constraints": missing}, ensure_ascii=False))
PY

IDENTITY_ID="${IDENTITY_ID:-base-repo-closure-orchestrator}"
CATALOG_PATH="${WORKSPACE_ROOT}/.identity/catalog.local.yaml"
REPORT_GLOB="${WORKSPACE_ROOT}/.identity/${IDENTITY_ID}/runtime/reports/identity-upgrade-exec-${IDENTITY_ID}-*.json"
LATEST_REPORT="$(python3 scripts/resolve_latest_identity_upgrade_report.py \
  --identity-id "${IDENTITY_ID}" \
  --search-root "${WORKSPACE_ROOT}/.identity/${IDENTITY_ID}/runtime/reports" \
  --print-path-only)"

if [[ ! -f "${CATALOG_PATH}" ]]; then
  echo "[FAIL] expected project-local catalog missing: ${CATALOG_PATH}"
  exit 1
fi
if [[ -z "${LATEST_REPORT}" || ! -f "${LATEST_REPORT}" ]]; then
  echo "[FAIL] expected latest execution report missing for ${IDENTITY_ID}"
  echo "       search pattern hint: ${REPORT_GLOB}"
  exit 1
fi

SUMMARY_PATH="${TMP_ROOT}/release-readiness-summary.json"
REPORT_PATH="${TMP_ROOT}/release-readiness-continuation-report.json"
SUMMARY_PATH_CWD_SAFE="${TMP_ROOT}/release-readiness-summary-cwd-safe.json"
REPORT_PATH_CWD_SAFE="${TMP_ROOT}/release-readiness-continuation-report-cwd-safe.json"
PROBE_CHECK_01="scripts/validate_runtime_catalog_metadata_hygiene.py"
PROBE_CHECK_02="scripts/validate_audit_snapshot_index.py"

echo "[INFO] positive: governed release-readiness continuation runner"
python3 scripts/run_release_readiness_continuation.py \
  --summary-out "${SUMMARY_PATH}" \
  --batch-size 1 \
  --max-rounds 3 \
  --report-out "${REPORT_PATH}" \
  --json-only \
  -- \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --execution-report "${LATEST_REPORT}" \
  --actor-id assistant:codex \
  --check-name "${PROBE_CHECK_01}" \
  --check-name "${PROBE_CHECK_02}" \
  >/tmp/release-readiness-continuation-positive.json

python3 - "${REPORT_PATH}" "${SUMMARY_PATH}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
summary = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

assert report["continuation_status"] == "PASS_REQUIRED", report
assert report["continuation_reason"] == "summary_finalized", report
assert report["round_count"] == 2, report
assert len(report["rounds"]) == 2, report
assert report["rounds"][0]["summary_lifecycle_status"] == "IN_PROGRESS", report
assert report["rounds"][1]["summary_lifecycle_status"] == "FINALIZED", report
assert report["final_summary"]["resume_projection"]["resume_projection_status"] == "PASS_REQUIRED", report
assert report["final_summary"]["resume_projection"]["resume_reason"] == "resume_after_last_completed_check", report
assert report["final_summary"]["resume_projection"]["same_path_as_summary_out"] is True, report
assert report["final_summary"]["resume_projection"]["resume_capture_mode"] == "stable_prewrite_snapshot", report
assert summary["summary_lifecycle_status"] == "FINALIZED", summary
assert summary["summary_checkpoint_kind"] == "final", summary
assert summary["release_readiness_status"] in {"PASS_REQUIRED", "FAIL_REQUIRED"}, summary
PY

echo "[INFO] positive: governed release-readiness continuation runner remains caller-cwd independent"
(
  cd "${WORKSPACE_ROOT}"
  python3 "${REPO_ROOT}/scripts/run_release_readiness_continuation.py" \
    --summary-out "${SUMMARY_PATH_CWD_SAFE}" \
    --batch-size 1 \
    --max-rounds 3 \
    --report-out "${REPORT_PATH_CWD_SAFE}" \
    --json-only \
    -- \
    --identity-id "${IDENTITY_ID}" \
    --catalog "${CATALOG_PATH}" \
    --execution-report "${LATEST_REPORT}" \
    --actor-id assistant:codex \
    --check-name "${PROBE_CHECK_01}" \
    --check-name "${PROBE_CHECK_02}" \
    >/tmp/release-readiness-continuation-positive-cwd-safe.json
)

python3 - "${REPORT_PATH_CWD_SAFE}" "${SUMMARY_PATH_CWD_SAFE}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
summary = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

assert report["continuation_status"] == "PASS_REQUIRED", report
assert report["continuation_reason"] == "summary_finalized", report
assert report["round_count"] == 2, report
assert report["release_readiness_script_path"].endswith("/scripts/release_readiness_check.py"), report
assert report["rounds"][0]["round_workdir"].endswith("/identity-protocol-local"), report
assert summary["summary_lifecycle_status"] == "FINALIZED", summary
assert summary["summary_checkpoint_kind"] == "final", summary

print(json.dumps({
    "release_readiness_continuation_probe_status": "PASS_REQUIRED",
    "round_count": report["round_count"],
    "release_readiness_script_path": report["release_readiness_script_path"],
    "caller_cwd_safe": True,
}, ensure_ascii=False))
PY

echo "[PASS] governed release-readiness continuation runner finalized over multiple rounds"
