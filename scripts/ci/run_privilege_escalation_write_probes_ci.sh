#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-${REPO_ROOT}}/.tmp-runtime}}"
WORK_ROOT="${PRIVILEGE_ESCALATION_PROBE_WORK_ROOT:-${TMP_ROOT_BASE%/}/identity-privilege-escalation-probes}"
FIXTURE_ROOT="${WORK_ROOT}/fixtures"
RESULT_ROOT="${WORK_ROOT}/results"
MANIFEST_PATH="${WORK_ROOT}/manifest.privilege_escalation_write.json"

mkdir -p "${FIXTURE_ROOT}" "${RESULT_ROOT}"

python3 - <<'PY' "${FIXTURE_ROOT}"
from __future__ import annotations

import json
from pathlib import Path
import sys
import yaml

fixture_root = Path(sys.argv[1]).resolve()
fixture_root.mkdir(parents=True, exist_ok=True)
identity_root = fixture_root / "identity"

ids = [
    "probe-priv-unique",
    "probe-priv-recovery",
    "probe-priv-postcheck",
]
for identity_id in ids:
    (identity_root / identity_id).mkdir(parents=True, exist_ok=True)

catalog = {
    "default_identity": ids[0],
    "identities": [
        {
            "id": identity_id,
            "status": "active",
            "pack_path": str((identity_root / identity_id).resolve()),
            "profile": "runtime",
            "runtime_mode": "local_only",
        }
        for identity_id in ids
    ],
}

task = {
    "protocol_unique_entry_gate_contract_v1": {
        "required": True,
        "validator": "scripts/validate_protocol_unique_entry_gate.py",
        "entry_script": "scripts/required_gate_bundle_runner.py",
        "bundle_key": "required_gate_bundle_runner",
        "scope": "all_identity_instance_actions",
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
        "require_strict_operation_receipt": True,
        "entry_receipt_state_file": "runtime/state/required_gate_bundle_entry.latest.json",
        "entry_receipt_history_pattern": "runtime/reports/required-gate-bundle-entry/required-gate-bundle-entry-*.json",
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
        "ingress_wrapper_path": "identity/runtime/gate/protocol_ingress_wrapper.py",
        "egress_wrapper_path": "identity/runtime/gate/protocol_egress_wrapper.py",
        "session_chain_wrapper_path": "identity/runtime/gate/protocol_session_chain_wrapper.py",
        "gateway_contract_path": "identity/runtime/gate/protocol_gateway_contract.json",
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
            "signer_secret_env": "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_PROBE_PRIV",
        },
        "egress_receipt_policy": {"required": True},
        "egress_grant_policy": {
            "required": True,
            "max_age_seconds": 300,
            "signer_mode": "runtime_env_secret",
            "signer_secret_env": "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_PROBE_PRIV",
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

for identity_id in ids:
    pack = identity_root / identity_id
    (pack / "CURRENT_TASK.json").write_text(
        json.dumps(task, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (pack / "runtime" / "state").mkdir(parents=True, exist_ok=True)
    (pack / "runtime" / "state" / "protocol_gateway_signing_key.txt").write_text(
        "local-readable-attacker-key\n",
        encoding="utf-8",
    )

(fixture_root / "catalog.yaml").write_text(
    yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

CATALOG_PATH="${FIXTURE_ROOT}/catalog.yaml"
UNIQUE_ID="probe-priv-unique"
RECOVERY_ID="probe-priv-recovery"
POSTCHECK_ID="probe-priv-postcheck"
ACTOR_ID="assistant:ci-probe"
SESSION_ID="session-ci-priv"
RUN_ID="ci-priv-run"
export IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_PROBE_PRIV="gateway-env-secret-only"

for ID in "${UNIQUE_ID}" "${RECOVERY_ID}" "${POSTCHECK_ID}"; do
  python3 scripts/repair_contract_backfill.py \
    --catalog "${CATALOG_PATH}" \
    --identity-id "${ID}" \
    --apply \
    --json-only >/dev/null
done

UNIQUE_PACK="${FIXTURE_ROOT}/identity/${UNIQUE_ID}"
RECOVERY_PACK="${FIXTURE_ROOT}/identity/${RECOVERY_ID}"
POSTCHECK_PACK="${FIXTURE_ROOT}/identity/${POSTCHECK_ID}"

mkdir -p "${UNIQUE_PACK}/runtime/reports/required-gate-bundle-entry"
chmod 555 "${UNIQUE_PACK}/runtime/state" "${UNIQUE_PACK}/runtime/reports/required-gate-bundle-entry"

python3 - <<'PY' "${WORK_ROOT}/unique_wrapper_proof.json" "${WORK_ROOT}/unique_wrapper_proof.sig" "${UNIQUE_ID}" "${RUN_ID}" "${ACTOR_ID}" "${SESSION_ID}"
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import sys
from pathlib import Path

proof = {
    "schema_version": "v1",
    "identity_id": sys.argv[3],
    "operation": "validate",
    "run_id": sys.argv[4],
    "actor_id": sys.argv[5],
    "session_id": sys.argv[6],
    "work_layer": "protocol",
    "source_layer": "project",
    "surface_label": "host_ingress_wrapper",
    "issued_at_epoch": int(time.time()),
    "nonce": secrets.token_hex(16),
}
canonical = json.dumps(proof, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
sig = hmac.new(b"gateway-env-secret-only", canonical.encode("utf-8"), hashlib.sha256).hexdigest()
Path(sys.argv[1]).write_text(canonical, encoding="utf-8")
Path(sys.argv[2]).write_text(sig + "\n", encoding="utf-8")
PY

mkdir -p "${RECOVERY_PACK}/runtime/reports/host-visible-surface"
chmod 555 "${RECOVERY_PACK}/runtime/reports/host-visible-surface"

python3 - <<'PY' "${POSTCHECK_PACK}" "${POSTCHECK_ID}" "${ACTOR_ID}" "${SESSION_ID}"
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

pack_path = Path(sys.argv[1]).resolve()
identity_id = sys.argv[2]
actor_id = sys.argv[3]
session_id = sys.argv[4]
run_id = "ci-priv-receipt"
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
receipt_dir = pack_path / "runtime" / "reports" / "host-visible-surface"
receipt_dir.mkdir(parents=True, exist_ok=True)
fields = {
    "wrapper_surface_status": "PASS_REQUIRED",
    "entry_receipt_tuple_status": "PASS_REQUIRED",
    "headstamp_first_line_status": "PASS_REQUIRED",
    "send_time_gate_status": "PASS_REQUIRED",
    "final_emit_contract_status": "PASS_REQUIRED",
}
state_doc = {
    "schema_version": "v1",
    "identity_id": identity_id,
    "channels": {},
    "updated_at_utc": timestamp,
}
for idx, channel in enumerate(("commentary", "approval", "status", "final"), start=1):
    payload = {
        "emit_channel_id": channel,
        "created_at_utc": timestamp,
        "receipt_source": "runtime_dialogue",
        "actor_id": actor_id,
        "session_id": session_id,
        "run_id": run_id,
    }
    payload.update(fields)
    path = receipt_dir / f"host-visible-surface-{idx:02d}-{channel}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state_doc["channels"][channel] = {
        "last_receipt_path": str(path),
        "last_status": "PASS_REQUIRED",
        "receipt_source": "runtime_dialogue",
        "last_run_id": run_id,
        "updated_at_utc": timestamp,
    }
state_path = pack_path / "runtime" / "state" / "host_visible_surface_registry_state.json"
state_path.parent.mkdir(parents=True, exist_ok=True)
state_path.write_text(json.dumps(state_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
chmod 555 "${POSTCHECK_PACK}/runtime/state"

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
doc = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
error_code = str(doc.get("error_code", "")).strip()
stale = [str(item).strip() for item in (doc.get("stale_reasons") or []) if str(item).strip()]
mapping_errors = [str(item).strip() for item in (doc.get("mapping_errors") or []) if str(item).strip()]

if rc == 0:
    raise SystemExit(f"{name}: expected non-zero rc")
if error_code != "IP-PRIV-ESC-001":
    raise SystemExit(f"{name}: expected IP-PRIV-ESC-001, got {error_code!r}")

expected_prefix_by_name = {
    "probe_unique_entry_receipt_write_denied": "privilege_escalation_required:required_gate_bundle_entry_receipt_write",
    "probe_host_visible_recovery_write_denied": "privilege_escalation_required:host_visible_recovery_write",
    "probe_post_check_closure_state_write_denied": "privilege_escalation_required:host_transport_post_check_state_write",
}
expected_prefix = expected_prefix_by_name[name]
haystack = mapping_errors if name == "probe_unique_entry_receipt_write_denied" else stale
if not any(expected_prefix in item for item in haystack):
    raise SystemExit(f"{name}: missing stale reason prefix {expected_prefix!r}")
PY

  python3 - <<'PY' "${name}" "${timestamp_utc}" "${rc}" "${cmd_string}" "${stdout_path}" "${stderr_path}" "${meta_path}"
from __future__ import annotations

import json
from pathlib import Path
import sys

name, timestamp, rc, cmd_string, stdout_path, stderr_path, meta_path = sys.argv[1:]
entry = {
    "probe_name": name,
    "timestamp_utc": timestamp,
    "command": cmd_string,
    "rc": int(rc),
    "stdout_path": stdout_path,
    "stderr_path": stderr_path if Path(stderr_path).exists() else "",
}
Path(meta_path).write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[PASS] {name} (rc={rc})")
PY
}

run_probe probe_unique_entry_receipt_write_denied \
  python3 scripts/required_gate_bundle_runner.py \
    --catalog "${CATALOG_PATH}" \
    --identity-id "${UNIQUE_ID}" \
    --operation validate \
    --run-id "${RUN_ID}" \
    --actor-id "${ACTOR_ID}" \
    --session-id "${SESSION_ID}" \
    --resolved-work-layer protocol \
    --resolved-source-layer project \
    --lock-state LOCK_MATCH \
    --send-time-gate-status NOT_APPLICABLE \
    --outlet-bypass-detected false \
    --final-emit-contract-status NOT_APPLICABLE \
    --final-emit-policy-mode tool_choice_required \
    --final-emit-schema-status NOT_APPLICABLE \
    --surface-label host_ingress_wrapper \
    --wrapper-dispatch-token instance_wrapper_ingress_v1 \
    --wrapper-proof-json "$(cat "${WORK_ROOT}/unique_wrapper_proof.json")" \
    --wrapper-proof-signature "$(tr -d '\n' < "${WORK_ROOT}/unique_wrapper_proof.sig")" \
    --json-only

run_probe probe_host_visible_recovery_write_denied \
  python3 scripts/recover_host_visible_post_check_state.py \
    --catalog "${CATALOG_PATH}" \
    --repo-catalog identity/catalog/identities.yaml \
    --identity-id "${RECOVERY_ID}" \
    --operation validate \
    --actor-id "${ACTOR_ID}" \
    --session-id "${SESSION_ID}" \
    --run-id "${RUN_ID}" \
    --json-only

run_probe probe_post_check_closure_state_write_denied \
  python3 scripts/validate_host_transport_wiring_attestation.py \
    --catalog "${CATALOG_PATH}" \
    --identity-id "${POSTCHECK_ID}" \
    --operation validate \
    --require-live-receipts \
    --allowed-live-receipt-sources runtime_dialogue \
    --require-actor-id "${ACTOR_ID}" \
    --require-session-id "${SESSION_ID}" \
    --require-run-id ci-priv-receipt \
    --json-only

python3 - <<'PY' "${RESULT_ROOT}" "${MANIFEST_PATH}"
from __future__ import annotations

import json
from pathlib import Path
import sys

result_root = Path(sys.argv[1]).resolve()
manifest_path = Path(sys.argv[2]).resolve()
entries = []
for meta_path in sorted(result_root.glob("*.meta.json")):
    entries.append(json.loads(meta_path.read_text(encoding="utf-8")))
manifest = {
    "schema_version": "v1",
    "suite": "privilege_escalation_write_probes",
    "results": entries,
}
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[PASS] privilege escalation write probe suite wrote manifest: {manifest_path}")
PY
