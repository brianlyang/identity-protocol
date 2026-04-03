#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/contract-bootstrap-emitter-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

PACK_ROOT="${TMP_ROOT}/probe-pack"
CATALOG_PATH="${TMP_ROOT}/catalog.local.yaml"
mkdir -p "${PACK_ROOT}/runtime/reports" "${PACK_ROOT}/runtime/protocol-feedback"

cat > "${PACK_ROOT}/CURRENT_TASK.json" <<'JSON'
{
  "handoff_collab_freshness_autorotation_contract_v1": {
    "required": true,
    "bootstrap_emitter": "scripts/rotate_handoff_collab_freshness.py",
    "validator": "scripts/validate_handoff_collab_freshness_rotation.py",
    "rotation_receipt_pattern": "runtime/reports/handoff-collab-freshness-rotation-*.json",
    "required_fields": [
      "rotation_applied",
      "freshness_age_days",
      "rotation_receipt_ref",
      "freshness_status"
    ],
    "fail_action": "block_when_freshness_rotation_receipt_missing_or_failed"
  }
}
JSON

cat > "${CATALOG_PATH}" <<YAML
version: 1
updated_at: "2026-03-25T00:00:00Z"
default_identity: bootstrap-probe-identity
identities:
  - id: bootstrap-probe-identity
    status: active
    profile: runtime
    runtime_mode: local_only
    canonical_scope: USER
    pack_path: ${PACK_ROOT}
    canonical_pack_path: ${PACK_ROOT}
YAML

POSITIVE_JSON="${TMP_ROOT}/positive-materialize.json"
python3 "${ROOT}/scripts/materialize_contract_bootstrap_emitters.py" \
  --catalog "${CATALOG_PATH}" \
  --identity-id bootstrap-probe-identity \
  --operation readiness \
  --apply \
  --json-only > "${POSITIVE_JSON}"

python3 - "${POSITIVE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["materialized_bootstrap_emitter_status"] == "PASS_REQUIRED", payload
assert payload["required_bootstrap_emitter_count"] == 1, payload
rows = payload["rows"]
assert len(rows) == 1, payload
row = rows[0]
assert row["status"] == "PASS_REQUIRED", row
receipt_ref = row["payload"].get("rotation_receipt_ref", "")
assert receipt_ref, row
assert Path(receipt_ref).exists(), row
PY

POSITIVE_VALIDATE_JSON="${TMP_ROOT}/positive-validate.json"
python3 "${ROOT}/scripts/validate_handoff_collab_freshness_rotation.py" \
  --catalog "${CATALOG_PATH}" \
  --identity-id bootstrap-probe-identity \
  --operation readiness \
  --json-only > "${POSITIVE_VALIDATE_JSON}"

python3 - "${POSITIVE_VALIDATE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["handoff_collab_freshness_rotation_status"] == "PASS_REQUIRED", payload
assert payload["producer_readiness"] is True, payload
assert payload["requiredization_current_round_linked"] is True, payload
PY

MATRIX_PACK_ROOT="${TMP_ROOT}/matrix-pack"
MATRIX_CATALOG_PATH="${TMP_ROOT}/matrix-catalog.local.yaml"
mkdir -p "${MATRIX_PACK_ROOT}/runtime/reports" "${MATRIX_PACK_ROOT}/runtime/protocol-feedback"

cat > "${MATRIX_PACK_ROOT}/CURRENT_TASK.json" <<'JSON'
{
  "required_validators": [
    "scripts/validate_identity_tool_installation.py",
    "scripts/validate_identity_vendor_api_discovery.py",
    "scripts/validate_identity_vendor_api_solution.py"
  ],
  "refresh_strict_business_interference_matrix_contract_v1": {
    "required": true,
    "matrix_emitter": "scripts/emit_business_interference_matrix.py",
    "validator": "scripts/validate_refresh_strict_business_interference.py",
    "refresh_receipt_pattern": "runtime/reports/business-interference-matrix-*-refresh-*.json",
    "strict_receipt_pattern": "runtime/reports/business-interference-matrix-*-strict-*.json",
    "required_fields": [
      "refresh_receipt_ref",
      "strict_receipt_ref",
      "interference_row_count_refresh",
      "interference_row_count_strict"
    ],
    "fail_action": "block_when_refresh_strict_interference_matrix_not_closed"
  }
}
JSON

cat > "${MATRIX_CATALOG_PATH}" <<YAML
version: 1
updated_at: "2026-03-26T00:00:00Z"
default_identity: matrix-probe-identity
identities:
  - id: matrix-probe-identity
    status: active
    profile: runtime
    runtime_mode: local_only
    canonical_scope: USER
    pack_path: ${MATRIX_PACK_ROOT}
    canonical_pack_path: ${MATRIX_PACK_ROOT}
YAML

MATRIX_MATERIALIZE_JSON="${TMP_ROOT}/matrix-materialize.json"
python3 "${ROOT}/scripts/materialize_contract_bootstrap_emitters.py" \
  --catalog "${MATRIX_CATALOG_PATH}" \
  --identity-id matrix-probe-identity \
  --operation readiness \
  --apply \
  --json-only > "${MATRIX_MATERIALIZE_JSON}"

python3 - "${MATRIX_MATERIALIZE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["materialized_bootstrap_emitter_status"] == "PASS_REQUIRED", payload
assert payload["required_bootstrap_emitter_count"] == 1, payload
rows = payload["rows"]
assert len(rows) == 1, payload
row = rows[0]
assert row["emitter_role"] == "matrix_emitter", row
assert row["status"] == "PASS_REQUIRED", row
assert row["invocation_count"] == 2, row
invocations = {item["invocation_id"]: item for item in row["invocations"]}
assert set(invocations) == {"refresh", "strict"}, row
for invocation_id, invocation in invocations.items():
    assert invocation["status"] == "PASS_REQUIRED", invocation
    receipt_ref = invocation["payload"].get("interference_receipt_ref", "")
    assert receipt_ref, invocation
    assert Path(receipt_ref).exists(), invocation
PY

MATRIX_VALIDATE_JSON="${TMP_ROOT}/matrix-validate.json"
python3 "${ROOT}/scripts/validate_refresh_strict_business_interference.py" \
  --catalog "${MATRIX_CATALOG_PATH}" \
  --identity-id matrix-probe-identity \
  --operation readiness \
  --json-only > "${MATRIX_VALIDATE_JSON}"

python3 - "${MATRIX_VALIDATE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["refresh_strict_business_interference_status"] == "PASS_REQUIRED", payload
assert payload["producer_readiness"] is True, payload
assert payload["requiredization_current_round_linked"] is True, payload
assert Path(payload["refresh_receipt_ref"]).exists(), payload
assert Path(payload["strict_receipt_ref"]).exists(), payload
assert payload["interference_row_count_refresh"] == 3, payload
assert payload["interference_row_count_strict"] == 3, payload
PY

NEGATIVE_TASK="${PACK_ROOT}/CURRENT_TASK.json"
python3 - "${NEGATIVE_TASK}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
doc = json.loads(path.read_text(encoding="utf-8"))
doc["handoff_collab_freshness_autorotation_contract_v1"]["bootstrap_emitter"] = "scripts/missing-bootstrap-emitter.py"
path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

NEGATIVE_JSON="${TMP_ROOT}/negative-materialize.json"
if python3 "${ROOT}/scripts/materialize_contract_bootstrap_emitters.py" \
  --catalog "${CATALOG_PATH}" \
  --identity-id bootstrap-probe-identity \
  --operation readiness \
  --apply \
  --json-only > "${NEGATIVE_JSON}"; then
  echo "[FAIL] bootstrap emitter materializer unexpectedly passed missing-emitter negative lane"
  exit 1
fi

python3 - "${NEGATIVE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["materialized_bootstrap_emitter_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CBE-001", payload
assert any(reason.startswith("bootstrap_emitter_exception:") for reason in payload["stale_reasons"]), payload
PY

echo "[PASS] contract bootstrap emitter probes passed"
