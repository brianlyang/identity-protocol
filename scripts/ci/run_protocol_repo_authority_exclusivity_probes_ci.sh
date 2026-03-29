#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-repo-authority-exclusivity-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_repo_authority_exclusivity.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_repo_authority_exclusivity_status"] == "PASS_REQUIRED", payload
assert payload["protocol_repo_dirname_matches"] is True, payload
assert payload["protocol_repo_markers_present"] is True, payload
assert payload["protocol_repo_root_matches_git_top_level"] is True, payload
assert payload["host_container_authority_status"] == "PASS_REQUIRED", payload
assert payload["stale_reasons"] == [], payload
PY

NESTED_PASS_ROOT="${TMP_ROOT}/nested-pass/host-root"
INNER_PASS_REPO="${NESTED_PASS_ROOT}/identity-protocol-local"
mkdir -p "${INNER_PASS_REPO}/scripts" "${INNER_PASS_REPO}/identity" "${INNER_PASS_REPO}/docs"
git -C "${TMP_ROOT}" init -q "${NESTED_PASS_ROOT}"
git -C "${TMP_ROOT}" init -q "${INNER_PASS_REPO}"

NESTED_PASS_JSON="${TMP_ROOT}/nested-pass.json"
python3 "${ROOT}/scripts/validate_protocol_repo_authority_exclusivity.py" \
  --repo-root "${INNER_PASS_REPO}" \
  --json-only >"${NESTED_PASS_JSON}"

python3 - <<'PY' "${NESTED_PASS_JSON}" "${NESTED_PASS_ROOT}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
outer_root = pathlib.Path(sys.argv[2]).resolve()
assert payload["protocol_repo_authority_exclusivity_status"] == "PASS_REQUIRED", payload
assert payload["protocol_repo_root_matches_git_top_level"] is True, payload
assert payload["host_container_present"] is True, payload
assert payload["enclosing_host_git_root_count"] >= 1, payload
assert str(outer_root) in payload["enclosing_host_git_roots"], payload
assert payload["host_container_authority_status"] == "PASS_REQUIRED", payload
PY

OUTER_CAPTURE_ROOT="${TMP_ROOT}/outer-capture/host-root"
INNER_CAPTURE_REPO="${OUTER_CAPTURE_ROOT}/identity-protocol-local"
mkdir -p "${INNER_CAPTURE_REPO}/scripts" "${INNER_CAPTURE_REPO}/identity" "${INNER_CAPTURE_REPO}/docs"
git -C "${TMP_ROOT}" init -q "${OUTER_CAPTURE_ROOT}"

OUTER_CAPTURE_JSON="${TMP_ROOT}/outer-capture.json"
if python3 "${ROOT}/scripts/validate_protocol_repo_authority_exclusivity.py" \
  --repo-root "${INNER_CAPTURE_REPO}" \
  --json-only >"${OUTER_CAPTURE_JSON}"; then
  echo "[FAIL] protocol repo authority exclusivity validator unexpectedly passed outer-host capture"
  exit 1
fi

python3 - <<'PY' "${OUTER_CAPTURE_JSON}" "${OUTER_CAPTURE_ROOT}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
outer_root = pathlib.Path(sys.argv[2]).resolve()
assert payload["protocol_repo_authority_exclusivity_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-PRAE-003", payload
assert payload["protocol_repo_root_matches_git_top_level"] is False, payload
assert payload["host_container_present"] is True, payload
assert payload["protocol_repo_git_top_level"] == str(outer_root), payload
assert payload["host_container_authority_status"] == "FAIL_REQUIRED", payload
assert any(reason.startswith("protocol_repo_root_not_independent_git_toplevel:") for reason in payload["stale_reasons"]), payload
PY

DIRNAME_REPO="${TMP_ROOT}/dirname-mismatch/protocol-root"
mkdir -p "${DIRNAME_REPO}/scripts" "${DIRNAME_REPO}/identity" "${DIRNAME_REPO}/docs"
git -C "${TMP_ROOT}" init -q "${DIRNAME_REPO}"

DIRNAME_JSON="${TMP_ROOT}/dirname-mismatch.json"
if python3 "${ROOT}/scripts/validate_protocol_repo_authority_exclusivity.py" \
  --repo-root "${DIRNAME_REPO}" \
  --json-only >"${DIRNAME_JSON}"; then
  echo "[FAIL] protocol repo authority exclusivity validator unexpectedly passed dirname mismatch"
  exit 1
fi

python3 - <<'PY' "${DIRNAME_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_repo_authority_exclusivity_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-PRAE-001", payload
assert payload["protocol_repo_dirname_matches"] is False, payload
assert payload["protocol_repo_root_matches_git_top_level"] is True, payload
assert any(reason.startswith("protocol_repo_dirname_mismatch:") for reason in payload["stale_reasons"]), payload
PY

echo "[PASS] protocol repo authority exclusivity probes passed"
