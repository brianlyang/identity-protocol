#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-lane-audit-summary-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}/.."

SUMMARY_JSON="${TMP_ROOT}/summary.json"
python3 "${REPO_ROOT}/scripts/render_protocol_lane_audit_summary.py" --json-only > "${SUMMARY_JSON}"

python3 - "${SUMMARY_JSON}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["range_mode"] in {"default_head_parent", "explicit_range", "commit_pinned"}, payload
assert payload["base"], payload
assert payload["head"], payload
assert isinstance(payload["changed_files"], list), payload
lane_summary = payload["lane_summary"]
assert lane_summary["launcher_lane_status"] == "PASS_REQUIRED", lane_summary
assert lane_summary["workbook_canonical_freshness_status"] == "PASS_REQUIRED", lane_summary
assert lane_summary["projection_docs_checker_gate_status"] == "NOT_GATING_BOUNDARY_ONLY", lane_summary
assert lane_summary["protocol_gate_depends_on_projection_docs_checker_counts"] is False, lane_summary
assert lane_summary["lane_change_scope"], lane_summary

stream_scope = payload["stream_scope"]
if lane_summary["stream_touch_evidence_status"] == "NOT_APPLICABLE_NO_STREAM_DOCS_TOUCHED":
    assert stream_scope["stream_scope_semantic_integrity_status"] == "SKIPPED_NOT_REQUIRED", stream_scope
    assert stream_scope.get("touched_stream_versions") == [], stream_scope
else:
    assert lane_summary["stream_touch_evidence_status"] == "APPLICABLE_PASS_REQUIRED", lane_summary

workbook = payload["workbook_consistency"]
freshness_contract = workbook["freshness_contract"]
assert freshness_contract["canonical_workbook_docs_checker_counts_required"] is True, freshness_contract
assert freshness_contract["projection_docs_checker_parity_gate_active"] is False, freshness_contract
assert sorted(freshness_contract["projection_boundary_only_roles"]) == [
    "deep_audit_projection",
    "issue_register_projection",
], freshness_contract
print("protocol_lane_audit_summary_status=PASS_REQUIRED")
PY

echo "[PASS] protocol lane audit summary probes passed"
