#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKSPACE_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-lane-audit-summary-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${WORKSPACE_ROOT}"

render_summary() {
  local repo_root="$1"
  local workspace_root="$2"
  local output_path="$3"
  shift 3
  python3 "${REPO_ROOT}/scripts/render_protocol_lane_audit_summary.py" \
    --repo-root "${repo_root}" \
    --workspace-root "${workspace_root}" \
    "$@" \
    --json-only > "${output_path}"
}

render_summary_expect_rc() {
  local expected_rc="$1"
  shift
  local actual_rc=0
  set +e
  render_summary "$@"
  actual_rc=$?
  set -e
  if [[ "${actual_rc}" -ne "${expected_rc}" ]]; then
    echo "[FAIL] unexpected summary renderer exit code: expected ${expected_rc}, got ${actual_rc}" >&2
    return 1
  fi
}

create_temp_workspace() {
  local name="$1"
  local ws_root="${TMP_ROOT}/${name}-workspace"
  git clone --quiet --local "${REPO_ROOT}" "${ws_root}/identity-protocol-local" >/dev/null 2>&1
  ln -s "${WORKSPACE_ROOT}/.identity" "${ws_root}/.identity"
  ln -s "${WORKSPACE_ROOT}/scripts" "${ws_root}/scripts"
  mkdir -p "${ws_root}/activity"
  ln -s "${WORKSPACE_ROOT}/activity/evidence" "${ws_root}/activity/evidence"
  printf '%s\n' "${ws_root}"
}

commit_temp_repo() {
  local repo_root="$1"
  local message="$2"
  git -C "${repo_root}" config user.name protocol-ci >/dev/null
  git -C "${repo_root}" config user.email protocol-ci@example.invalid >/dev/null
  git -C "${repo_root}" add -A
  git -C "${repo_root}" commit -m "${message}" >/dev/null
}

SUMMARY_JSON="${TMP_ROOT}/summary.json"
render_summary "${REPO_ROOT}" "${WORKSPACE_ROOT}" "${SUMMARY_JSON}"

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

PARITY_WS="$(create_temp_workspace projection-parity)"
PARITY_REPO="${PARITY_WS}/identity-protocol-local"
python3 - "${PARITY_REPO}/identity/protocol/mappings/workbook-registry.v1.6.yaml" "${PARITY_WS}" "${WORKSPACE_ROOT}" <<'PY'
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import yaml

DOCS_RE = re.compile(r"docs checked:\s*(\d+)", flags=re.IGNORECASE)
SNIPPETS_RE = re.compile(r"command snippets checked:\s*(\d+)", flags=re.IGNORECASE)

registry_path = Path(sys.argv[1]).resolve()
parity_ws = Path(sys.argv[2]).resolve()
live_ws = Path(sys.argv[3]).resolve()
repo_root = registry_path.parents[3]
doc = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
family = doc["active_workbook_family"]
issue_register_doc = repo_root / str(family.get("issue_register_doc", "")).strip()
canonical_text = issue_register_doc.read_text(encoding="utf-8")
docs_match = DOCS_RE.search(canonical_text)
snippets_match = SNIPPETS_RE.search(canonical_text)
if not docs_match or not snippets_match:
    raise SystemExit("missing canonical docs checker markers in issue register doc")
canonical_docs = int(docs_match.group(1))
canonical_snippets = int(snippets_match.group(1))
evidence_root = parity_ws / "activity" / "evidence"
if evidence_root.is_symlink():
    evidence_root.unlink()
evidence_root.mkdir(parents=True, exist_ok=True)

for row in family.get("projection_exports", []) or []:
    row["freshness_mode"] = "summary_snapshot_parity_required"
    rel = str(row.get("path", "")).strip()
    if not rel:
        continue
    source_path = (live_ws / rel).resolve()
    target_path = (parity_ws / rel).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)
    projection_text = target_path.read_text(encoding="utf-8")
    if not DOCS_RE.search(projection_text) or not SNIPPETS_RE.search(projection_text):
        raise SystemExit(f"missing projection docs checker markers: {target_path}")
    projection_text = DOCS_RE.sub(f"docs checked: {canonical_docs}", projection_text, count=1)
    projection_text = SNIPPETS_RE.sub(
        f"command snippets checked: {canonical_snippets}",
        projection_text,
        count=1,
    )
    target_path.write_text(projection_text, encoding="utf-8")
registry_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY
commit_temp_repo "${PARITY_REPO}" "probe: parity required projection freshness"
PARITY_JSON="${TMP_ROOT}/summary-projection-parity.json"
render_summary "${PARITY_REPO}" "${PARITY_WS}" "${PARITY_JSON}" --commit HEAD

python3 - "${PARITY_JSON}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
lane_summary = payload["lane_summary"]
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["range_mode"] == "commit_pinned", payload
assert lane_summary["projection_docs_checker_gate_status"] == "PARITY_REQUIRED", lane_summary
assert lane_summary["protocol_gate_depends_on_projection_docs_checker_counts"] is True, lane_summary
print("protocol_lane_audit_summary_projection_parity_status=PASS_REQUIRED")
PY

CANONICAL_WS="$(create_temp_workspace canonical-mismatch)"
CANONICAL_REPO="${CANONICAL_WS}/identity-protocol-local"
python3 - "${CANONICAL_REPO}/docs/workbook/protocol-issue-register-v1.6.md" "${CANONICAL_REPO}/docs/workbook/protocol-deep-audit-workbook-v1.6.md" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import re

COUNT_RE = re.compile(r"command snippets checked:\s*(\d+)", flags=re.IGNORECASE)

for raw in sys.argv[1:]:
    path = Path(raw).resolve()
    text = path.read_text(encoding="utf-8")
    match = COUNT_RE.search(text)
    if not match:
        raise SystemExit(f"missing canonical docs checker count marker: {path}")
    current = int(match.group(1))
    mutated = max(current - 1, 0)
    path.write_text(COUNT_RE.sub(f"command snippets checked: {mutated}", text, count=1), encoding="utf-8")
PY
commit_temp_repo "${CANONICAL_REPO}" "probe: break canonical workbook docs checker counts"
CANONICAL_JSON="${TMP_ROOT}/summary-canonical-mismatch.json"
render_summary_expect_rc 1 "${CANONICAL_REPO}" "${CANONICAL_WS}" "${CANONICAL_JSON}" --commit HEAD

python3 - "${CANONICAL_JSON}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
lane_summary = payload["lane_summary"]
workbook = payload["workbook_consistency"]
assert payload["status"] == "FAIL_REQUIRED", payload
assert lane_summary["canonical_docs_checker_violation_count"] > 0, lane_summary
assert workbook["issue_register_consistency_status"] == "FAIL_REQUIRED", workbook
assert workbook["violation_partitions"]["canonical_docs_checker"], workbook
print("protocol_lane_audit_summary_canonical_mismatch_status=FAIL_REQUIRED")
PY

STREAM_TOUCH_COMMIT="$(git -C "${REPO_ROOT}" log -n 1 --format=%H -- docs/governance/identity-codex-launcher-governance-v1.6.14.md docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md)"
STREAM_JSON="${TMP_ROOT}/summary-stream-touch.json"
render_summary "${REPO_ROOT}" "${WORKSPACE_ROOT}" "${STREAM_JSON}" --commit "${STREAM_TOUCH_COMMIT}"

python3 - "${STREAM_JSON}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
lane_summary = payload["lane_summary"]
stream_scope = payload["stream_scope"]
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["range_mode"] == "commit_pinned", payload
assert lane_summary["stream_touch_evidence_status"].startswith("APPLICABLE_"), lane_summary
assert "v1.6.14" in (stream_scope.get("touched_stream_versions") or []), stream_scope
print("protocol_lane_audit_summary_stream_touch_status=PASS_REQUIRED")
PY

ISOLATED_JSON="${TMP_ROOT}/summary-isolated-historical-replay.json"
python3 "${REPO_ROOT}/scripts/validate_protocol_lane_isolated_historical_replay.py" \
  --repo-root "${REPO_ROOT}" \
  --workspace-root "${WORKSPACE_ROOT}" \
  --commit HEAD \
  --json-only > "${ISOLATED_JSON}"

python3 - "${ISOLATED_JSON}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["isolated_historical_replay_status"] == "PASS_REQUIRED", payload
assert payload["projection_parity_match"] is True, payload
assert payload["direct_projection"]["status"] == "PASS_REQUIRED", payload
assert payload["isolated_projection"]["status"] == "PASS_REQUIRED", payload
print("protocol_lane_audit_summary_isolated_replay_status=PASS_REQUIRED")
PY

echo "[PASS] protocol lane audit summary probes passed"
