#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-broadcast-delivery-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

WORKSPACE_ROOT="${TMP_ROOT}/workspace"
IDENTITY_HOME="${WORKSPACE_ROOT}/.identity"
CATALOG_PATH="${IDENTITY_HOME}/catalog.local.yaml"
IDENTITY_ID="broadcast-delivery-probe"
PACK_ROOT="${IDENTITY_HOME}/${IDENTITY_ID}"
TASK_PATH="${PACK_ROOT}/CURRENT_TASK.json"
SYNC_JSON="${TMP_ROOT}/broadcast-sync.json"
PASS_JSON="${TMP_ROOT}/broadcast-pass.json"
MISSING_JSON="${TMP_ROOT}/broadcast-missing-contract.json"
BACKFILL_JSON="${TMP_ROOT}/broadcast-backfill.json"
REPAIRED_JSON="${TMP_ROOT}/broadcast-repaired.json"
CLOSURE_JSON="${TMP_ROOT}/broadcast-closure.json"

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
    _identity_broadcast_delivery_contract_skeleton,
    materialize_protocol_host_gateway_artifacts,
)

task = {
    "identity_id": identity_id,
    "objective": {"title": "broadcast delivery probe", "status": "active"},
    "state_machine": {"current_state": "probe_active"},
    "required_validators": [],
    "identity_broadcast_delivery_contract_v1": _identity_broadcast_delivery_contract_skeleton(),
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

python3 "${ROOT}/scripts/run_identity_broadcast_delivery.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --run-id "broadcast-probe-sync" \
  --sync \
  --write-receipt \
  --json-only >"${SYNC_JSON}"

python3 - <<'PY' "${SYNC_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_broadcast_delivery_status"] == "PASS_REQUIRED", payload
assert payload["sync_applied"] is True, payload
receipt_path = pathlib.Path(payload["broadcast_receipt_path"])
assert receipt_path.exists(), payload
PY

python3 "${ROOT}/scripts/validate_identity_broadcast_delivery.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_broadcast_delivery_status"] == "PASS_REQUIRED", payload
assert payload["broadcast_contract_status"] == "PASS_REQUIRED", payload
assert payload["broadcast_runtime_contract_status"] == "PASS_REQUIRED", payload
assert payload["broadcast_delivery_sync_status"] == "PASS_REQUIRED", payload
PY

python3 - <<'PY' "${TASK_PATH}"
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
doc = json.loads(path.read_text(encoding="utf-8"))
doc.pop("identity_broadcast_delivery_contract_v1", None)
path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 "${ROOT}/scripts/validate_identity_broadcast_delivery.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --json-only >"${MISSING_JSON}"; then
  echo "[FAIL] broadcast delivery validator unexpectedly passed without dedicated contract"
  exit 1
fi

python3 - <<'PY' "${MISSING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_broadcast_delivery_status"] == "FAIL_REQUIRED", payload
assert "identity_broadcast_delivery_contract_missing_or_not_required" in payload.get("stale_reasons", []), payload
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
assert "identity_broadcast_delivery_contract_v1" in restored, payload
PY

python3 "${ROOT}/scripts/validate_identity_broadcast_delivery.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --json-only >"${REPAIRED_JSON}"

python3 - <<'PY' "${REPAIRED_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_broadcast_delivery_status"] == "PASS_REQUIRED", payload
assert payload["broadcast_contract_status"] == "PASS_REQUIRED", payload
PY

python3 "${ROOT}/scripts/check_identity_broadcast_migration_closure.py" \
  --catalog "${CATALOG_PATH}" \
  --workspace-runtime-only \
  --json-only >"${CLOSURE_JSON}"

python3 - <<'PY' "${CLOSURE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_broadcast_migration_closure_status"] == "PASS_REQUIRED", payload
assert payload["checked_identity_count"] == 1, payload
PY

echo "[PASS] identity broadcast delivery probes passed"
