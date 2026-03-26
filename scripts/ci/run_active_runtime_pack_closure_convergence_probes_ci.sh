#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/active-runtime-pack-closure-convergence-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

WORKSPACE_ROOT="${TMP_ROOT}/workspace"
IDENTITY_HOME="${WORKSPACE_ROOT}/.identity"
LOCAL_CATALOG_PATH="${IDENTITY_HOME}/catalog.local.yaml"
REPO_CATALOG_PATH="${WORKSPACE_ROOT}/identity/catalog/identities.yaml"
IDENTITY_ID="runtime-pack-closure-probe"
STRAY_IDENTITY_ID="runtime-pack-closure-stray"
PACK_ROOT="${IDENTITY_HOME}/${IDENTITY_ID}"
UNIQUE_ENTRY_WORKSPACE_JSON="${TMP_ROOT}/unique-entry-workspace.json"
VERSION_BASELINE_WORKSPACE_JSON="${TMP_ROOT}/version-baseline-workspace.json"
UNIQUE_ENTRY_REPO_JSON="${TMP_ROOT}/unique-entry-repo.json"
VERSION_BASELINE_REPO_JSON="${TMP_ROOT}/version-baseline-repo.json"

mkdir -p "${PACK_ROOT}/runtime" "$(dirname "${REPO_CATALOG_PATH}")"

python3 - "${ROOT}" "${PACK_ROOT}" "${LOCAL_CATALOG_PATH}" "${REPO_CATALOG_PATH}" "${IDENTITY_ID}" "${STRAY_IDENTITY_ID}" <<'PY'
import json
import sys
from pathlib import Path

import yaml

root = Path(sys.argv[1]).resolve()
pack_root = Path(sys.argv[2]).resolve()
local_catalog_path = Path(sys.argv[3]).resolve()
repo_catalog_path = Path(sys.argv[4]).resolve()
identity_id = sys.argv[5]
stray_identity_id = sys.argv[6]

sys.path.insert(0, str((root / "scripts").resolve()))

from protocol_infra_contract import (  # type: ignore
    UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS,
)
from version_baseline_common import resolve_version_baseline  # type: ignore

baseline = resolve_version_baseline(repo_root=root)
if not baseline.get("ok"):
    raise SystemExit(f"version baseline unavailable: {baseline}")
agent_identity = dict(baseline.get("agent_identity") or {})
scaffold_metadata = dict(baseline.get("scaffold_metadata") or {})
meta_doc = dict(baseline.get("meta") or {})
catalog_baseline = dict(baseline.get("catalog") or {})

current_task = {
    "identity_id": identity_id,
    "agent_identity": agent_identity,
    "scaffold_metadata": scaffold_metadata,
    "protocol_unique_entry_gate_contract_v1": {
        "required": True,
        "entry_receipt_max_age_seconds": 86400,
        "entry_receipt_selector_policy_id": UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID,
        "entry_receipt_selector_precedence": list(UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE),
        "entry_receipt_selector_source_fields": list(UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS),
    },
}
(pack_root / "CURRENT_TASK.json").write_text(json.dumps(current_task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(pack_root / "META.yaml").write_text(yaml.safe_dump(meta_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")

local_catalog_doc = {
    "identities": [
        {
            "id": identity_id,
            "pack_path": str(pack_root.resolve()),
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
            "scope": "USER",
            **catalog_baseline,
        }
    ]
}
repo_catalog_doc = {
    "identities": [
        {
            "id": stray_identity_id,
            "pack_path": str((repo_catalog_path.parent.parent / "packs" / stray_identity_id).resolve()),
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
            "scope": "USER",
            **catalog_baseline,
        }
    ]
}

local_catalog_path.parent.mkdir(parents=True, exist_ok=True)
repo_catalog_path.parent.mkdir(parents=True, exist_ok=True)
local_catalog_path.write_text(yaml.safe_dump(local_catalog_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
repo_catalog_path.write_text(yaml.safe_dump(repo_catalog_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
PY

python3 "${ROOT}/scripts/check_unique_entry_contract_migration_closure.py" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --workspace-runtime-only \
  --json-only >"${UNIQUE_ENTRY_WORKSPACE_JSON}"

python3 "${ROOT}/scripts/check_version_baseline_migration_closure.py" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --workspace-runtime-only \
  --json-only >"${VERSION_BASELINE_WORKSPACE_JSON}"

python3 - <<'PY' "${ROOT}" "${UNIQUE_ENTRY_WORKSPACE_JSON}" "${VERSION_BASELINE_WORKSPACE_JSON}" "${IDENTITY_ID}"
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str((root / "scripts").resolve()))

from runtime_pack_closure_common import PACK_SCAN_POLICY_ID  # type: ignore

unique_entry = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
version_baseline = json.loads(pathlib.Path(sys.argv[3]).read_text(encoding="utf-8"))
identity_id = sys.argv[4]

assert unique_entry["unique_entry_contract_migration_closure_status"] == "PASS_REQUIRED", unique_entry
assert version_baseline["version_baseline_migration_closure_status"] == "PASS_REQUIRED", version_baseline
assert unique_entry["pack_scan_policy_id"] == PACK_SCAN_POLICY_ID, unique_entry
assert version_baseline["pack_scan_policy_id"] == PACK_SCAN_POLICY_ID, version_baseline
assert unique_entry["catalog_selection_mode"] == "workspace_runtime_only", unique_entry
assert version_baseline["catalog_selection_mode"] == "workspace_runtime_only", version_baseline
assert unique_entry["repo_catalog_included"] is False, unique_entry
assert version_baseline["repo_catalog_included"] is False, version_baseline
assert unique_entry["catalogs_checked"] == version_baseline["catalogs_checked"], (unique_entry, version_baseline)
assert unique_entry["checked_identity_ids"] == [identity_id], unique_entry
assert version_baseline["checked_identity_ids"] == [identity_id], version_baseline
assert unique_entry["checked_identity_count"] == 1, unique_entry
assert version_baseline["checked_identity_count"] == 1, version_baseline
assert unique_entry["checked_rows"][0]["identity_id"] == identity_id, unique_entry
assert version_baseline["checked_rows"][0]["identity_id"] == identity_id, version_baseline
PY

if python3 "${ROOT}/scripts/check_unique_entry_contract_migration_closure.py" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --json-only >"${UNIQUE_ENTRY_REPO_JSON}"; then
  echo "[FAIL] unique-entry pack closure unexpectedly passed in repo-inclusive mode with stray repo runtime identity"
  exit 1
fi

if python3 "${ROOT}/scripts/check_version_baseline_migration_closure.py" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --json-only >"${VERSION_BASELINE_REPO_JSON}"; then
  echo "[FAIL] version-baseline pack closure unexpectedly passed in repo-inclusive mode with stray repo runtime identity"
  exit 1
fi

python3 - <<'PY' "${ROOT}" "${UNIQUE_ENTRY_REPO_JSON}" "${VERSION_BASELINE_REPO_JSON}" "${IDENTITY_ID}" "${STRAY_IDENTITY_ID}" "${REPO_CATALOG_PATH}" "${LOCAL_CATALOG_PATH}"
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str((root / "scripts").resolve()))

from runtime_pack_closure_common import PACK_SCAN_POLICY_ID  # type: ignore

unique_entry = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
version_baseline = json.loads(pathlib.Path(sys.argv[3]).read_text(encoding="utf-8"))
identity_id = sys.argv[4]
stray_identity_id = sys.argv[5]
repo_catalog_path = str(pathlib.Path(sys.argv[6]).resolve())
local_catalog_path = str(pathlib.Path(sys.argv[7]).resolve())

assert unique_entry["unique_entry_contract_migration_closure_status"] == "FAIL_REQUIRED", unique_entry
assert version_baseline["version_baseline_migration_closure_status"] == "FAIL_REQUIRED", version_baseline
assert unique_entry["pack_scan_policy_id"] == PACK_SCAN_POLICY_ID, unique_entry
assert version_baseline["pack_scan_policy_id"] == PACK_SCAN_POLICY_ID, version_baseline
assert unique_entry["catalog_selection_mode"] == "repo_catalog_inclusive", unique_entry
assert version_baseline["catalog_selection_mode"] == "repo_catalog_inclusive", version_baseline
assert unique_entry["repo_catalog_included"] is True, unique_entry
assert version_baseline["repo_catalog_included"] is True, version_baseline
assert unique_entry["catalogs_checked"] == [repo_catalog_path, local_catalog_path], unique_entry
assert version_baseline["catalogs_checked"] == [repo_catalog_path, local_catalog_path], version_baseline
assert set(unique_entry["checked_identity_ids"]) == {identity_id, stray_identity_id}, unique_entry
assert set(version_baseline["checked_identity_ids"]) == {identity_id, stray_identity_id}, version_baseline
assert unique_entry["violation_count"] == 1, unique_entry
assert version_baseline["violation_count"] == 1, version_baseline
assert unique_entry["violations"][0]["identity_id"] == stray_identity_id, unique_entry
assert version_baseline["violations"][0]["identity_id"] == stray_identity_id, version_baseline
assert unique_entry["violations"][0]["catalog_path"] == repo_catalog_path, unique_entry
assert version_baseline["violations"][0]["catalog_path"] == repo_catalog_path, version_baseline
PY

python3 - <<'PY' "${UNIQUE_ENTRY_WORKSPACE_JSON}" "${UNIQUE_ENTRY_REPO_JSON}"
import json
import pathlib
import sys

workspace_payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
repo_payload = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))

print(
    json.dumps(
        {
            "active_runtime_pack_closure_convergence_probe_status": "PASS_REQUIRED",
            "workspace_checked_identity_count": workspace_payload.get("checked_identity_count", 0),
            "repo_inclusive_violation_count": repo_payload.get("violation_count", 0),
            "pack_scan_policy_id": workspace_payload.get("pack_scan_policy_id", ""),
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] active runtime pack closure convergence probes passed"
