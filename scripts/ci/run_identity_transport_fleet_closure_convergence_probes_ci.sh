#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-transport-fleet-closure-convergence-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

WORKSPACE_ROOT="${TMP_ROOT}/workspace"
IDENTITY_HOME="${WORKSPACE_ROOT}/.identity"
LOCAL_CATALOG_PATH="${IDENTITY_HOME}/catalog.local.yaml"
REPO_CATALOG_PATH="${WORKSPACE_ROOT}/identity/catalog/identities.yaml"
IDENTITY_ID="transport-fleet-closure-probe"
STRAY_IDENTITY_ID="transport-fleet-closure-stray"
PACK_ROOT="${IDENTITY_HOME}/${IDENTITY_ID}"
TASK_PATH="${PACK_ROOT}/CURRENT_TASK.json"
BACKFILL_JSON="${TMP_ROOT}/transport-backfill.json"
RUN_JSON="${TMP_ROOT}/transport-run.json"
BROADCAST_WORKSPACE_JSON="${TMP_ROOT}/broadcast-workspace.json"
COMMUNICATION_WORKSPACE_JSON="${TMP_ROOT}/communication-workspace.json"
BROADCAST_REPO_JSON="${TMP_ROOT}/broadcast-repo-inclusive.json"
COMMUNICATION_REPO_JSON="${TMP_ROOT}/communication-repo-inclusive.json"

mkdir -p "${PACK_ROOT}/runtime" "${PACK_ROOT}/scripts" "$(dirname "${REPO_CATALOG_PATH}")"

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

from blocker_taxonomy_common import BLOCKER_ALIAS_MAP_VERSION, CANONICAL_BLOCKER_TYPES  # type: ignore
from create_identity_pack import (  # type: ignore
    _agent_handoff_contract_skeleton,
    _collaboration_trigger_contract_skeleton,
    materialize_protocol_host_gateway_artifacts,
)

task = {
    "identity_id": identity_id,
    "objective": {"title": "transport fleet closure convergence probe", "status": "active"},
    "state_machine": {"current_state": "probe_active"},
    "required_validators": [],
    "agent_handoff_contract": _agent_handoff_contract_skeleton(),
    "collaboration_trigger_contract": _collaboration_trigger_contract_skeleton(),
    "blocker_taxonomy_contract": {
        "required": True,
        "required_blocker_types": list(CANONICAL_BLOCKER_TYPES),
        "blocker_alias_map_version": BLOCKER_ALIAS_MAP_VERSION,
        "blocker_classification_required_fields": [
            "blocker_type",
            "source",
            "detected_at",
            "requires_human_collab",
            "next_action",
        ],
    },
}

materialize_protocol_host_gateway_artifacts(
    task=task,
    identity_id=identity_id,
    pack_dir=pack_root,
    catalog_path=local_catalog_path,
    protocol_root=root,
)

(pack_root / "CURRENT_TASK.json").write_text(
    json.dumps(task, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

local_catalog_doc = {
    "identities": [
        {
            "id": identity_id,
            "pack_path": str(pack_root.resolve()),
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
            "scope": "USER",
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
        }
    ]
}

local_catalog_path.parent.mkdir(parents=True, exist_ok=True)
repo_catalog_path.parent.mkdir(parents=True, exist_ok=True)
local_catalog_path.write_text(yaml.safe_dump(local_catalog_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
repo_catalog_path.write_text(yaml.safe_dump(repo_catalog_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
PY

python3 "${ROOT}/scripts/repair_contract_backfill.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --apply \
  --json-only >"${BACKFILL_JSON}"

python3 - <<'PY' "${BACKFILL_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["communication_contract_auto_wire_status"] == "PASS_REQUIRED", payload
restored = set(payload.get("restored_communication_contract_keys", []))
assert "identity_broadcast_delivery_contract_v1" in restored, payload
assert "identity_communication_transport_contract_v1" in restored, payload
PY

python3 "${ROOT}/scripts/run_identity_communication_transport.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --run-id "transport-convergence-probe-sync" \
  --json-only >"${RUN_JSON}"

python3 - <<'PY' "${RUN_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_communication_transport_run_status"] == "PASS_REQUIRED", payload
assert payload["identity_communication_transport_status"] == "PASS_REQUIRED", payload
assert payload["broadcast_sync_executor_status"] == "PASS_REQUIRED", payload
assert payload["atomic_emit_bootstrap_status"] == "PASS_REQUIRED", payload
PY

python3 "${ROOT}/scripts/check_identity_broadcast_migration_closure.py" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --workspace-runtime-only \
  --json-only >"${BROADCAST_WORKSPACE_JSON}"

python3 "${ROOT}/scripts/check_identity_communication_transport_closure.py" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --workspace-runtime-only \
  --json-only >"${COMMUNICATION_WORKSPACE_JSON}"

python3 - <<'PY' "${ROOT}" "${BROADCAST_WORKSPACE_JSON}" "${COMMUNICATION_WORKSPACE_JSON}" "${IDENTITY_ID}"
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str((root / "scripts").resolve()))

from runtime_fleet_closure_common import FLEET_PROJECTION_POLICY_ID  # type: ignore

broadcast = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
communication = json.loads(pathlib.Path(sys.argv[3]).read_text(encoding="utf-8"))
identity_id = sys.argv[4]

assert broadcast["identity_broadcast_migration_closure_status"] == "PASS_REQUIRED", broadcast
assert communication["identity_communication_transport_closure_status"] == "PASS_REQUIRED", communication
assert broadcast["fleet_projection_policy_id"] == FLEET_PROJECTION_POLICY_ID, broadcast
assert communication["fleet_projection_policy_id"] == FLEET_PROJECTION_POLICY_ID, communication
assert broadcast["catalog_selection_mode"] == "workspace_runtime_only", broadcast
assert communication["catalog_selection_mode"] == "workspace_runtime_only", communication
assert broadcast["repo_catalog_included"] is False, broadcast
assert communication["repo_catalog_included"] is False, communication
assert broadcast["catalogs_checked"] == communication["catalogs_checked"], (broadcast, communication)
assert broadcast["catalogs_checked"] == [broadcast["checked_rows"][0]["catalog_path"]], broadcast
assert broadcast["checked_identity_count"] == 1, broadcast
assert communication["checked_identity_count"] == 1, communication
assert broadcast["checked_identity_ids"] == [identity_id], broadcast
assert communication["checked_identity_ids"] == [identity_id], communication
assert broadcast["checked_rows"][0]["identity_id"] == identity_id, broadcast
assert communication["checked_rows"][0]["identity_id"] == identity_id, communication
PY

if python3 "${ROOT}/scripts/check_identity_broadcast_migration_closure.py" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --json-only >"${BROADCAST_REPO_JSON}"; then
  echo "[FAIL] broadcast fleet closure unexpectedly passed in repo-inclusive mode with stray repo runtime identity"
  exit 1
fi

if python3 "${ROOT}/scripts/check_identity_communication_transport_closure.py" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --catalog "${LOCAL_CATALOG_PATH}" \
  --json-only >"${COMMUNICATION_REPO_JSON}"; then
  echo "[FAIL] communication fleet closure unexpectedly passed in repo-inclusive mode with stray repo runtime identity"
  exit 1
fi

python3 - <<'PY' "${ROOT}" "${BROADCAST_REPO_JSON}" "${COMMUNICATION_REPO_JSON}" "${IDENTITY_ID}" "${STRAY_IDENTITY_ID}" "${REPO_CATALOG_PATH}" "${LOCAL_CATALOG_PATH}"
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str((root / "scripts").resolve()))

from runtime_fleet_closure_common import FLEET_PROJECTION_POLICY_ID  # type: ignore

broadcast = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
communication = json.loads(pathlib.Path(sys.argv[3]).read_text(encoding="utf-8"))
identity_id = sys.argv[4]
stray_identity_id = sys.argv[5]
repo_catalog_path = str(pathlib.Path(sys.argv[6]).resolve())
local_catalog_path = str(pathlib.Path(sys.argv[7]).resolve())

assert broadcast["identity_broadcast_migration_closure_status"] == "FAIL_REQUIRED", broadcast
assert communication["identity_communication_transport_closure_status"] == "FAIL_REQUIRED", communication
assert broadcast["fleet_projection_policy_id"] == FLEET_PROJECTION_POLICY_ID, broadcast
assert communication["fleet_projection_policy_id"] == FLEET_PROJECTION_POLICY_ID, communication
assert broadcast["catalog_selection_mode"] == "repo_catalog_inclusive", broadcast
assert communication["catalog_selection_mode"] == "repo_catalog_inclusive", communication
assert broadcast["repo_catalog_included"] is True, broadcast
assert communication["repo_catalog_included"] is True, communication
assert broadcast["catalogs_checked"] == [repo_catalog_path, local_catalog_path], broadcast
assert communication["catalogs_checked"] == [repo_catalog_path, local_catalog_path], communication
assert broadcast["checked_identity_count"] == 2, broadcast
assert communication["checked_identity_count"] == 2, communication
assert set(broadcast["checked_identity_ids"]) == {identity_id, stray_identity_id}, broadcast
assert set(communication["checked_identity_ids"]) == {identity_id, stray_identity_id}, communication
assert broadcast["violation_count"] == 1, broadcast
assert communication["violation_count"] == 1, communication
assert broadcast["violations"][0]["identity_id"] == stray_identity_id, broadcast
assert communication["violations"][0]["identity_id"] == stray_identity_id, communication
assert broadcast["violations"][0]["catalog_path"] == repo_catalog_path, broadcast
assert communication["violations"][0]["catalog_path"] == repo_catalog_path, communication
PY

python3 - <<'PY' "${BROADCAST_WORKSPACE_JSON}" "${BROADCAST_REPO_JSON}"
import json
import pathlib
import sys

workspace_payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
repo_payload = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))

print(
    json.dumps(
        {
            "identity_transport_fleet_closure_convergence_probe_status": "PASS_REQUIRED",
            "workspace_checked_identity_count": workspace_payload.get("checked_identity_count", 0),
            "repo_inclusive_violation_count": repo_payload.get("violation_count", 0),
            "fleet_projection_policy_id": workspace_payload.get("fleet_projection_policy_id", ""),
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] identity transport fleet closure convergence probes passed"
