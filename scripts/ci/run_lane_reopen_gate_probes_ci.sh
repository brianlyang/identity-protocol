#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
export TMPDIR="${TMPDIR:-${REPO_ROOT}/.tmp}"
mkdir -p "${TMPDIR}"

PROBE_ROOT="${TMPDIR}/lane-reopen-gate-contract-probes"
rm -rf "${PROBE_ROOT}"
mkdir -p "${PROBE_ROOT}"

GOV_DOC="${REPO_ROOT}/docs/governance/identity-lane-reopen-gate-governance-v1.6.x.md"
REVIEW_DOC="${REPO_ROOT}/docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-reopen-gate.md"
VALIDATOR="${REPO_ROOT}/scripts/validate_lane_reopen_gate_contract.py"

expect_pass() {
  local label="$1"
  shift
  local output_file="${PROBE_ROOT}/${label}.json"
  python3 "${VALIDATOR}" --json-only "$@" >"${output_file}"
  python3 - "${output_file}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("lane_reopen_gate_contract_status") != "PASS_REQUIRED":
    raise SystemExit(
        f"expected PASS_REQUIRED, got {payload.get('lane_reopen_gate_contract_status')}"
    )
if payload.get("errors"):
    raise SystemExit(f"expected no errors, got {payload['errors']}")
PY
}

expect_fail() {
  local label="$1"
  shift
  local output_file="${PROBE_ROOT}/${label}.json"
  if python3 "${VALIDATOR}" --json-only "$@" >"${output_file}"; then
    echo "expected ${label} to fail validation" >&2
    exit 1
  fi
  python3 - "${output_file}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("lane_reopen_gate_contract_status") != "FAIL_REQUIRED":
    raise SystemExit(
        f"expected FAIL_REQUIRED, got {payload.get('lane_reopen_gate_contract_status')}"
    )
if not payload.get("errors"):
    raise SystemExit("expected validation errors for negative probe")
PY
}

prepare_case() {
  local case_name="$1"
  local case_dir="${PROBE_ROOT}/${case_name}"
  mkdir -p "${case_dir}"
  cp "${GOV_DOC}" "${case_dir}/governance.md"
  cp "${REVIEW_DOC}" "${case_dir}/review.md"
  echo "${case_dir}"
}

mutate_contract() {
  local governance_path="$1"
  local review_path="$2"
  local mode="$3"
  python3 - "${REPO_ROOT}" "${governance_path}" "${review_path}" "${mode}" <<'PY'
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
governance_path = Path(sys.argv[2])
review_path = Path(sys.argv[3])
mode = sys.argv[4]

sys.path.insert(0, str(repo_root / "scripts"))
from lane_reopen_gate_contract_common import (
    extract_contract_payload,
    replace_contract_payload,
)

targets = [governance_path, review_path]

for target in targets:
    text = target.read_text(encoding="utf-8")
    payload = extract_contract_payload(text)
    if mode == "missing_commit_gate":
        payload.pop("commit_gate", None)
    elif mode == "governing_law_drift":
        payload["governing_law"] = "reopen_must_be_machine_triggered__drifted"
    elif mode == "fixed_write_set_extra":
        payload["fixed_write_set"] = payload["fixed_write_set"] + ["docs/out-of-scope.md"]
    elif mode == "next_exact_action_drift":
        payload["next_exact_action"] = payload["next_exact_action"] + ["allow broad reopen review"]
    elif mode == "reopen_trigger_extra":
        payload["reopen_triggers"] = payload["reopen_triggers"] + ["chat-history ambiguity"]
    elif mode == "commit_gate_drift":
        payload["commit_gate"] = "multiple commits allowed"
    else:
        raise SystemExit(f"unknown mutation mode: {mode}")
    target.write_text(replace_contract_payload(text, payload), encoding="utf-8")
PY
}

mutate_remove_semantic_phrase() {
  local governance_path="$1"
  local review_path="$2"
  python3 - "${governance_path}" "${review_path}" <<'PY'
import sys
from pathlib import Path

targets = [Path(sys.argv[1]), Path(sys.argv[2])]
phrase = "Reopen must be machine-triggered after handoff."
replacement = "Reopen may be discussed informally after handoff."

for target in targets:
    text = target.read_text(encoding="utf-8")
    if phrase not in text:
        raise SystemExit(f"required phrase missing before mutation in {target}")
    target.write_text(text.replace(phrase, replacement, 1), encoding="utf-8")
PY
}

expect_pass "baseline" --governance-doc "${GOV_DOC}" --review-doc "${REVIEW_DOC}"

case_dir="$(prepare_case missing_required_field)"
mutate_contract "${case_dir}/governance.md" "${case_dir}/review.md" missing_commit_gate
expect_fail "missing_required_field" --governance-doc "${case_dir}/governance.md" --review-doc "${case_dir}/review.md"

case_dir="$(prepare_case governing_law_drift)"
mutate_contract "${case_dir}/governance.md" "${case_dir}/review.md" governing_law_drift
expect_fail "governing_law_drift" --governance-doc "${case_dir}/governance.md" --review-doc "${case_dir}/review.md"

case_dir="$(prepare_case fixed_write_set_extra)"
mutate_contract "${case_dir}/governance.md" "${case_dir}/review.md" fixed_write_set_extra
expect_fail "fixed_write_set_extra" --governance-doc "${case_dir}/governance.md" --review-doc "${case_dir}/review.md"

case_dir="$(prepare_case next_exact_action_drift)"
mutate_contract "${case_dir}/governance.md" "${case_dir}/review.md" next_exact_action_drift
expect_fail "next_exact_action_drift" --governance-doc "${case_dir}/governance.md" --review-doc "${case_dir}/review.md"

case_dir="$(prepare_case reopen_trigger_extra)"
mutate_contract "${case_dir}/governance.md" "${case_dir}/review.md" reopen_trigger_extra
expect_fail "reopen_trigger_extra" --governance-doc "${case_dir}/governance.md" --review-doc "${case_dir}/review.md"

case_dir="$(prepare_case commit_gate_drift)"
mutate_contract "${case_dir}/governance.md" "${case_dir}/review.md" commit_gate_drift
expect_fail "commit_gate_drift" --governance-doc "${case_dir}/governance.md" --review-doc "${case_dir}/review.md"

case_dir="$(prepare_case missing_semantic_phrase)"
mutate_remove_semantic_phrase "${case_dir}/governance.md" "${case_dir}/review.md"
expect_fail "missing_semantic_phrase" --governance-doc "${case_dir}/governance.md" --review-doc "${case_dir}/review.md"

echo "PASS: lane reopen gate probes"
