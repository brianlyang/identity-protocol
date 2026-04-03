#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-communication-transport-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

WORKSPACE_ROOT="${TMP_ROOT}/workspace"
IDENTITY_HOME="${WORKSPACE_ROOT}/.identity"
CATALOG_PATH="${IDENTITY_HOME}/catalog.local.yaml"
IDENTITY_ID="communication-transport-probe"
PACK_ROOT="${IDENTITY_HOME}/${IDENTITY_ID}"
TASK_PATH="${PACK_ROOT}/CURRENT_TASK.json"
FAIL_JSON="${TMP_ROOT}/communication-missing-contract.json"
BACKFILL_JSON="${TMP_ROOT}/communication-backfill.json"
RUN_JSON="${TMP_ROOT}/communication-run.json"
PASS_JSON="${TMP_ROOT}/communication-pass.json"
PREFIXED_PASS_JSON="${TMP_ROOT}/communication-prefixed-pass.json"
PREFIXED_RUN_JSON="${TMP_ROOT}/communication-prefixed-run.json"
MISSING_ROOT_JSON="${TMP_ROOT}/communication-missing-root.json"
REPAIRED_JSON="${TMP_ROOT}/communication-repaired.json"
CLOSURE_JSON="${TMP_ROOT}/communication-closure.json"

mkdir -p "${PACK_ROOT}/runtime" "${PACK_ROOT}/scripts"

python3 - "${ROOT}" "${PACK_ROOT}" "${CATALOG_PATH}" "${IDENTITY_ID}" <<'PY'
import json
import sys
from pathlib import Path

import yaml

root = Path(sys.argv[1]).resolve()
pack_root = Path(sys.argv[2]).resolve()
catalog_path = Path(sys.argv[3]).resolve()
identity_id = sys.argv[4]

sys.path.insert(0, str((root / "scripts").resolve()))

from create_identity_pack import (  # type: ignore
    _agent_handoff_contract_skeleton,
    _collaboration_trigger_contract_skeleton,
    materialize_protocol_host_gateway_artifacts,
)
from blocker_taxonomy_common import BLOCKER_ALIAS_MAP_VERSION, CANONICAL_BLOCKER_TYPES  # type: ignore

task = {
    "identity_id": identity_id,
    "objective": {"title": "communication transport probe", "status": "active"},
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
    catalog_path=catalog_path,
    protocol_root=root,
)

(pack_root / "CURRENT_TASK.json").write_text(
    json.dumps(task, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

catalog_doc = {
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
catalog_path.parent.mkdir(parents=True, exist_ok=True)
catalog_path.write_text(
    yaml.safe_dump(catalog_doc, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

if python3 "${ROOT}/scripts/validate_identity_communication_transport.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${ROOT}/identity/catalog/identities.yaml" \
  --json-only >"${FAIL_JSON}"; then
  echo "[FAIL] identity communication transport unexpectedly passed without dedicated contract"
  exit 1
fi

python3 - <<'PY' "${FAIL_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_communication_transport_status"] == "FAIL_REQUIRED", payload
assert "identity_communication_transport_contract_missing_or_not_required" in payload.get("stale_reasons", []), payload
PY

python3 "${ROOT}/scripts/repair_contract_backfill.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --apply \
  --json-only >"${BACKFILL_JSON}"

python3 - <<'PY' "${BACKFILL_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["communication_contract_auto_wire_status"] == "PASS_REQUIRED", payload
restored = set(payload.get("restored_communication_contract_keys", []))
assert "identity_communication_transport_contract_v1" in restored, payload
assert "identity_broadcast_delivery_contract_v1" in restored, payload
PY

python3 "${ROOT}/scripts/run_identity_communication_transport.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${ROOT}/identity/catalog/identities.yaml" \
  --run-id "communication-probe-sync" \
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

python3 "${ROOT}/scripts/validate_identity_communication_transport.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${ROOT}/identity/catalog/identities.yaml" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_communication_transport_status"] == "PASS_REQUIRED", payload
assert payload["broadcast_transport_status"] == "PASS_REQUIRED", payload
assert payload["protocol_feedback_atomic_transport_status"] == "PASS_REQUIRED", payload
PY

python3 "${ROOT}/scripts/validate_identity_communication_transport.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "identity-protocol-local/identity/catalog/identities.yaml" \
  --json-only >"${PREFIXED_PASS_JSON}"

python3 - <<'PY' "${PREFIXED_PASS_JSON}" "${ROOT}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
root = pathlib.Path(sys.argv[2]).resolve()
expected = (root / "identity" / "catalog" / "identities.yaml").resolve()
assert payload["identity_communication_transport_status"] == "PASS_REQUIRED", payload
assert pathlib.Path(payload["repo_catalog_path"]).resolve() == expected, payload
PY

python3 "${ROOT}/scripts/run_identity_communication_transport.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "identity-protocol-local/identity/catalog/identities.yaml" \
  --run-id "communication-probe-prefixed-sync" \
  --json-only >"${PREFIXED_RUN_JSON}"

python3 - <<'PY' "${PREFIXED_RUN_JSON}" "${ROOT}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
root = pathlib.Path(sys.argv[2]).resolve()
expected = (root / "identity" / "catalog" / "identities.yaml").resolve()
assert payload["identity_communication_transport_run_status"] == "PASS_REQUIRED", payload
assert payload["identity_communication_transport_status"] == "PASS_REQUIRED", payload
assert pathlib.Path(payload["repo_catalog_path"]).resolve() == expected, payload
PY

rm -rf "${PACK_ROOT}/runtime/protocol-feedback/inbox-from-protocol"

if python3 "${ROOT}/scripts/validate_identity_communication_transport.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${ROOT}/identity/catalog/identities.yaml" \
  --json-only >"${MISSING_ROOT_JSON}"; then
  echo "[FAIL] identity communication transport unexpectedly passed with missing inbox root"
  exit 1
fi

python3 - <<'PY' "${MISSING_ROOT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_communication_transport_status"] == "FAIL_REQUIRED", payload
reasons = payload.get("stale_reasons", [])
assert any("missing_runtime_root:runtime/protocol-feedback/inbox-from-protocol" == item for item in reasons), payload
PY

python3 "${ROOT}/scripts/repair_contract_backfill.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --apply \
  --json-only >/dev/null

python3 "${ROOT}/scripts/validate_identity_communication_transport.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${ROOT}/identity/catalog/identities.yaml" \
  --json-only >"${REPAIRED_JSON}"

python3 - <<'PY' "${REPAIRED_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_communication_transport_status"] == "PASS_REQUIRED", payload
assert payload["protocol_feedback_inbox_transport_status"] == "PASS_REQUIRED", payload
PY

python3 "${ROOT}/scripts/check_identity_communication_transport_closure.py" \
  --catalog "${CATALOG_PATH}" \
  --workspace-runtime-only \
  --json-only >"${CLOSURE_JSON}"

python3 - <<'PY' "${CLOSURE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_communication_transport_closure_status"] == "PASS_REQUIRED", payload
assert payload["checked_identity_count"] == 1, payload
PY

echo "[PASS] identity communication transport probes passed"
