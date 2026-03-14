#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-${REPO_ROOT}}/.tmp-runtime}}"
WORK_ROOT="${UNIQUE_ENTRY_TUPLE_PROBE_WORK_ROOT:-${TMP_ROOT_BASE%/}/identity-unique-entry-tuple-probes}"
FIXTURE_ROOT="${WORK_ROOT}/fixtures"
RESULT_ROOT="${WORK_ROOT}/results"
MANIFEST_PATH="${WORK_ROOT}/manifest.unique_entry_tuple_binding.json"

mkdir -p "${FIXTURE_ROOT}" "${RESULT_ROOT}"

python3 - <<'PY' "${FIXTURE_ROOT}" "${REPO_ROOT}"
from __future__ import annotations

import json
import sys
from pathlib import Path
import yaml

fixture_root = Path(sys.argv[1]).resolve()
repo_root = Path(sys.argv[2]).resolve()
fixture_root.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str((repo_root / "scripts").resolve()))
from create_identity_pack import materialize_protocol_host_gateway_artifacts

identity_root = fixture_root / "identity"
probe_pack = identity_root / "probe-tuple-binding"
(probe_pack / "runtime" / "state").mkdir(parents=True, exist_ok=True)
catalog_path = fixture_root / "catalog.yaml"

catalog = {
    "default_identity": "probe-tuple-binding",
    "identities": [
        {
            "id": "probe-tuple-binding",
            "status": "active",
            "pack_path": str(probe_pack),
            "profile": "runtime",
            "runtime_mode": "local_only",
        }
    ],
}

task = {
    "protocol_unique_entry_gate_contract_v1": {
        "required": True,
        "contract_id": "protocol_unique_entry_gate_contract_v1",
        "validator": "scripts/validate_protocol_unique_entry_gate.py",
        "entry_script": "scripts/required_gate_bundle_runner.py",
        "bundle_key": "required_gate_bundle_runner",
        "entry_error_family": ["IP-GATE-ENTRY-001", "IP-GATE-ENTRY-002"],
        "enforce_on_operations": [
            "activate",
            "update",
            "mutation",
            "readiness",
            "e2e",
            "ci",
            "validate",
            "three-plane",
        ],
        "scope": "all_identity_instance_actions",
        "require_strict_operation_receipt": True,
        "entry_receipt_state_file": "runtime/state/required_gate_bundle_entry.latest.json",
        "entry_receipt_history_pattern": "runtime/reports/required-gate-bundle-entry/required-gate-bundle-entry-*.json",
        "entry_receipt_max_age_seconds": 1800,
        "entry_receipt_required_fields": [
            "bundle_key",
            "bundle_contract_id",
            "identity_id",
            "operation",
            "surface_label",
            "wrapper_dispatch_required",
            "wrapper_surface_status",
            "wrapper_dispatch_token_status",
            "wrapper_dispatch_proof_required",
            "wrapper_dispatch_proof_status",
            "run_id_binding",
            "actor_id",
            "session_id",
            "bundle_status",
            "error_code",
        ],
    },
    "protocol_host_unique_channel_contract_v1": {
        "required": True,
        "contract_id": "protocol_host_unique_channel_contract_v1",
        "validator": "scripts/validate_protocol_unique_entry_gate.py",
        "protocol_ingress_script": "scripts/required_gate_bundle_runner.py",
        "protocol_egress_script": "scripts/final_emit_governed.py",
        "ingress_wrapper_path": "runtime/gate/protocol_ingress_wrapper.py",
        "egress_wrapper_path": "runtime/gate/protocol_egress_wrapper.py",
        "session_chain_wrapper_path": "runtime/gate/protocol_session_chain_wrapper.py",
        "gateway_contract_path": "runtime/gate/protocol_gateway_contract.json",
        "entry_receipt_policy": {
            "required": True,
            "required_surface_label": "host_ingress_wrapper",
            "required_wrapper_surface_status": "PASS_REQUIRED",
            "required_wrapper_dispatch_token_status": "PASS_REQUIRED",
        },
        "ingress_proof_policy": {
            "required": True,
            "max_age_seconds": 300,
            "signer_mode": "runtime_env_secret",
            "signer_secret_env": "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_PROBE_TUPLE_BINDING",
        },
        "egress_receipt_policy": {"required": True},
        "egress_grant_policy": {
            "required": True,
            "max_age_seconds": 300,
            "signer_mode": "runtime_env_secret",
            "signer_secret_env": "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_PROBE_TUPLE_BINDING",
        },
        "headstamp_policy": {"required": True},
        "identity_tuple_fields": ["actor_id", "session_id", "run_id", "work_layer", "source_layer"],
        "host_dispatch_mode": "wrapper_only",
        "host_release_mode": "wrapper_only",
        "ingress_wrapper_dispatch_token": "instance_wrapper_ingress_v1",
        "operation_profile_policy": {
            "strict_operations": [
                "activate",
                "update",
                "mutation",
                "readiness",
                "e2e",
                "ci",
                "validate",
                "three-plane",
            ],
            "light_operations": ["inspection", "scan"],
            "strict_gate_profile": "strict_full",
            "light_gate_profile": "inspection_targeted",
            "allow_upgrade_only": True,
        },
    },
}

materialize_protocol_host_gateway_artifacts(
    task=task,
    identity_id="probe-tuple-binding",
    pack_dir=probe_pack,
    catalog_path=catalog_path,
    protocol_root=repo_root,
)

(probe_pack / "CURRENT_TASK.json").write_text(
    json.dumps(task, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
catalog_path.write_text(
    yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

CATALOG_PATH="${FIXTURE_ROOT}/catalog.yaml"
IDENTITY_ID="probe-tuple-binding"
ACTOR_ID="assistant:ci-probe"
SESSION_ID="session-tuple-binding-probe"
RUN_ID="probe-tuple-binding-run"
INGRESS_WRAPPER_PATH="${FIXTURE_ROOT}/identity/probe-tuple-binding/runtime/gate/protocol_ingress_wrapper.py"
RECEIPT_PATH="${RESULT_ROOT}/receipt.validate.json"

python3 - <<'PY' "${RECEIPT_PATH}" "${IDENTITY_ID}" "${RUN_ID}" "${ACTOR_ID}" "${SESSION_ID}" "${INGRESS_WRAPPER_PATH}"
from __future__ import annotations

import json
import sys
from pathlib import Path

receipt_path = Path(sys.argv[1]).resolve()
identity_id = sys.argv[2]
run_id = sys.argv[3]
actor_id = sys.argv[4]
session_id = sys.argv[5]
ingress_wrapper_path = str(Path(sys.argv[6]).resolve())

receipt = {
    "bundle_contract_id": "hotfix_p0_007_ucg_control_plane_freeze_contract_v1",
    "bundle_key": "required_gate_bundle_runner",
    "bundle_status": "PASS_REQUIRED",
    "error_code": "",
    "identity_id": identity_id,
    "operation": "validate",
    "run_id_binding": run_id,
    "actor_id": actor_id,
    "session_id": session_id,
    "surface_label": "host_ingress_wrapper",
    "wrapper_surface_status": "PASS_REQUIRED",
    "wrapper_dispatch_token_status": "PASS_REQUIRED",
    "wrapper_dispatch_required": True,
    "wrapper_dispatch_proof_required": True,
    "wrapper_dispatch_proof_status": "PASS_REQUIRED",
    "wrapper_parent_attestation_required": True,
    "wrapper_parent_attestation_status": "PASS_REQUIRED",
    "wrapper_parent_attestation_expected_path": ingress_wrapper_path,
}
receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

run_probe() {
  local name="$1"
  shift
  local cmd=("$@")

  local stdout_path="${RESULT_ROOT}/${name}.stdout.json"
  local stderr_path="${RESULT_ROOT}/${name}.stderr.log"
  local meta_path="${RESULT_ROOT}/${name}.meta.json"
  local timestamp_utc
  timestamp_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local cmd_string
  cmd_string="$(printf '%q ' "${cmd[@]}")"
  cmd_string="${cmd_string% }"

  set +e
  "${cmd[@]}" >"${stdout_path}" 2>"${stderr_path}"
  local rc=$?
  set -e

  if [ ! -s "${stderr_path}" ]; then
    rm -f "${stderr_path}"
  fi

  python3 - <<'PY' "${name}" "${rc}" "${stdout_path}"
from __future__ import annotations

import json
import sys
from pathlib import Path

name = sys.argv[1]
rc = int(sys.argv[2])
stdout_path = Path(sys.argv[3])
doc = json.loads(stdout_path.read_text(encoding="utf-8"))

if name == "tuple_binding_incomplete_blocked":
    if rc == 0:
        raise SystemExit("tuple_binding_incomplete_blocked: expected non-zero rc")
    stale = [str(x).strip() for x in (doc.get("stale_reasons") or []) if str(x).strip()]
    if not any(token.startswith("entry_receipt_tuple_binding_incomplete:") for token in stale):
        raise SystemExit("tuple_binding_incomplete_blocked: expected tuple_binding_incomplete stale reason")
    if str(doc.get("protocol_unique_entry_receipt_tuple_context_status", "")).strip().upper() != "FAIL_REQUIRED":
        raise SystemExit("tuple_binding_incomplete_blocked: tuple_context_status must be FAIL_REQUIRED")
elif name == "tuple_binding_complete_pass":
    if rc != 0:
        raise SystemExit("tuple_binding_complete_pass: expected zero rc")
    if str(doc.get("protocol_unique_entry_gate_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("tuple_binding_complete_pass: gate status must be PASS_REQUIRED")
    if str(doc.get("protocol_unique_entry_receipt_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("tuple_binding_complete_pass: receipt status must be PASS_REQUIRED")
else:
    raise SystemExit(f"unknown probe: {name}")
PY

  local sha256
  sha256="$(python3 - <<'PY' "${stdout_path}"
from __future__ import annotations
import hashlib, sys
from pathlib import Path
path = Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
)"

  python3 - <<'PY' "${meta_path}" "${name}" "${stdout_path}" "${sha256}" "${cmd_string}" "${rc}" "${timestamp_utc}"
from __future__ import annotations
import json, sys
from pathlib import Path
meta_path = Path(sys.argv[1])
payload = {
    "name": sys.argv[2],
    "file": str(Path(sys.argv[3]).resolve()),
    "sha256": sys.argv[4],
    "command": sys.argv[5],
    "rc": int(sys.argv[6]),
    "timestamp_utc": sys.argv[7],
}
meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

  echo "[UNIQUE-ENTRY][PROBE] ${name} rc=${rc} file=${stdout_path}"
}

cd "${REPO_ROOT}"

run_probe tuple_binding_incomplete_blocked \
  python3 scripts/validate_protocol_unique_entry_gate.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --run-id "${RUN_ID}" \
  --entry-receipt "${RECEIPT_PATH}" \
  --force-check \
  --require-entry-receipt \
  --json-only

run_probe tuple_binding_complete_pass \
  python3 scripts/validate_protocol_unique_entry_gate.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --run-id "${RUN_ID}" \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --entry-receipt "${RECEIPT_PATH}" \
  --force-check \
  --require-entry-receipt \
  --json-only

python3 - <<'PY' "${RESULT_ROOT}" "${MANIFEST_PATH}"
from __future__ import annotations

import json
import sys
from pathlib import Path

result_root = Path(sys.argv[1]).resolve()
manifest_path = Path(sys.argv[2]).resolve()
entries = []
for meta_path in sorted(result_root.glob("*.meta.json")):
    doc = json.loads(meta_path.read_text(encoding="utf-8"))
    entries.append(doc)
manifest = {
    "suite": "unique_entry_tuple_binding_probes",
    "result_root": str(result_root),
    "probe_count": len(entries),
    "probes": entries,
}
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(str(manifest_path))
PY

echo "[UNIQUE-ENTRY][PROBE] manifest=${MANIFEST_PATH}"
echo "[UNIQUE-ENTRY][PROBE] status=PASS"
