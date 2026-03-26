#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/doc-command-surface-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_registry_repo() {
  local dst="$1"
  mkdir -p "${dst}/identity/protocol/mappings" "${dst}/scripts/ci" "${dst}/docs/governance" "${dst}/docs/review"
  cp "${ROOT}/identity/protocol/mappings/doc-command-surface.current.yaml" "${dst}/identity/protocol/mappings/"
  cp "${ROOT}/identity/protocol/mappings/doc-command-surface.v1.yaml" "${dst}/identity/protocol/mappings/"
  cp "${ROOT}/identity/protocol/mappings/stream-doc-registry.current.yaml" "${dst}/identity/protocol/mappings/"
  cp "${ROOT}/identity/protocol/mappings/stream-doc-registry.v1.6.yaml" "${dst}/identity/protocol/mappings/"
  cp "${ROOT}/scripts/doc_command_surface_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_doc_command_surface_registry.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_doc_command_surface_probes_ci.sh" "${dst}/scripts/ci/"
  for rel in \
    docs/governance/audit-snapshot-2026-02-23-v1.4.6-role-binding-bootstrap.md \
    docs/governance/audit-snapshot-2026-02-24-release-doc-governance-closure-v1.4.12.md \
    docs/governance/identity-actor-session-binding-governance-v1.5.0.md \
    docs/review/protocol-remediation-audit-ledger-v1.5.md \
    docs/governance/github-native-control-plane-specialization-v1.6.3.md \
    docs/review/protocol-remediation-audit-ledger-v1.6.6.md \
    docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md \
    docs/review/protocol-remediation-audit-ledger-v1.6.12-native-chat-bootstrap-entry.md \
    docs/review/protocol-remediation-audit-ledger-v1.6.13-instance-pack-topology.md \
    docs/governance/identity-codex-launcher-governance-v1.6.14.md \
    docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md; do
    mkdir -p "${dst}/$(dirname "${rel}")"
    cp "${ROOT}/${rel}" "${dst}/${rel}"
  done
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_doc_command_surface_registry.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["doc_command_surface_registry_status"] == "PASS_REQUIRED", payload
assert {row["mode"] for row in payload["surface_modes"]} == {
    "live_contract",
    "historical_replay_trace",
    "compatibility_bridge_trace",
}, payload
assert "identity-protocol-local" in payload["self_prefixes"], payload
PY

INVALID_MODE_REPO="${TMP_ROOT}/invalid-mode-repo"
mirror_registry_repo "${INVALID_MODE_REPO}"
python3 - <<'PY' "${INVALID_MODE_REPO}/identity/protocol/mappings/doc-command-surface.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["surface_modes"][0]["mode"] = "bad_mode"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

INVALID_MODE_JSON="${TMP_ROOT}/invalid-mode.json"
if python3 "${ROOT}/scripts/validate_doc_command_surface_registry.py" \
  --repo-root "${INVALID_MODE_REPO}" \
  --json-only >"${INVALID_MODE_JSON}"; then
  echo "[FAIL] doc-command surface validator unexpectedly passed invalid mode drift"
  exit 1
fi

python3 - <<'PY' "${INVALID_MODE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["doc_command_surface_registry_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-DCSR-002", payload
assert any(
    reason == "structure_violation:surface_modes:mode_set_mismatch"
    for reason in payload["stale_reasons"]
), payload
PY

MISSING_SELECTOR_REPO="${TMP_ROOT}/missing-selector-repo"
mirror_registry_repo "${MISSING_SELECTOR_REPO}"
python3 - <<'PY' "${MISSING_SELECTOR_REPO}/identity/protocol/mappings/doc-command-surface.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["doc_command_surface_rows"][4]["script_rules"][0].pop("script_rel", None)
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_SELECTOR_JSON="${TMP_ROOT}/missing-selector.json"
if python3 "${ROOT}/scripts/validate_doc_command_surface_registry.py" \
  --repo-root "${MISSING_SELECTOR_REPO}" \
  --json-only >"${MISSING_SELECTOR_JSON}"; then
  echo "[FAIL] doc-command surface validator unexpectedly passed missing selector drift"
  exit 1
fi

python3 - <<'PY' "${MISSING_SELECTOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["doc_command_surface_registry_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-DCSR-002", payload
assert any(
    reason == "structure_violation:doc_command_surface_rows:rule_selector_must_choose_exactly_one_of_script_rel_or_script_prefix"
    for reason in payload["stale_reasons"]
), payload
PY

RANDOM_REPO="${TMP_ROOT}/random-checkout-name"
mkdir -p "${RANDOM_REPO}/scripts" "${RANDOM_REPO}/identity/protocol/mappings"
cp "${ROOT}/scripts/docs_command_contract_check.py" "${RANDOM_REPO}/scripts/"
cp "${ROOT}/scripts/doc_command_surface_common.py" "${RANDOM_REPO}/scripts/"
cp "${ROOT}/scripts/contract_binding_mapping_common.py" "${RANDOM_REPO}/scripts/"
cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${RANDOM_REPO}/scripts/"
cp "${ROOT}/scripts/repo_root_resolution_common.py" "${RANDOM_REPO}/scripts/"
cp "${ROOT}/scripts/reference_visual_atlas_governance_common.py" "${RANDOM_REPO}/scripts/"
cp "${ROOT}/identity/protocol/mappings/doc-command-surface.current.yaml" "${RANDOM_REPO}/identity/protocol/mappings/"
cp "${ROOT}/identity/protocol/mappings/doc-command-surface.v1.yaml" "${RANDOM_REPO}/identity/protocol/mappings/"
touch "${RANDOM_REPO}/scripts/validate_headstamp_recurrence_closure.py"

python3 - <<'PY' "${RANDOM_REPO}"
import importlib.util
import pathlib
import sys

repo = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repo / "scripts"))
spec = importlib.util.spec_from_file_location(
    "docs_command_contract_check", repo / "scripts" / "docs_command_contract_check.py"
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
target, cwd = module.resolve_script_target(
    repo,
    "identity-protocol-local/scripts/validate_headstamp_recurrence_closure.py",
    ("identity-protocol-local",),
)
assert target == (repo / "scripts" / "validate_headstamp_recurrence_closure.py").resolve(), (target, cwd)
assert cwd == repo, (target, cwd)
PY

echo "[PASS] doc command surface probes passed"
