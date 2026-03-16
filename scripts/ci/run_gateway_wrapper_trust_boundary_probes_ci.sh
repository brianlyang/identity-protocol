#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-${REPO_ROOT}}/.tmp-runtime}}"
WORK_ROOT="${GATEWAY_PROBE_WORK_ROOT:-${TMP_ROOT_BASE%/}/identity-gateway-boundary-probes}"
FIXTURE_ROOT="${WORK_ROOT}/fixtures"
RESULT_ROOT="${WORK_ROOT}/results"
MANIFEST_PATH="${WORK_ROOT}/manifest.gateway_wrapper_trust_boundary.json"

mkdir -p "${FIXTURE_ROOT}" "${RESULT_ROOT}"

python3 - <<'PY' "${FIXTURE_ROOT}"
from __future__ import annotations

import json
from pathlib import Path
import yaml
import sys

fixture_root = Path(sys.argv[1]).resolve()
fixture_root.mkdir(parents=True, exist_ok=True)

identity_root = fixture_root / "identity"
probe_pack = identity_root / "probe-gateway"
(probe_pack / "runtime" / "state").mkdir(parents=True, exist_ok=True)

catalog = {
    "default_identity": "probe-gateway",
    "identities": [
        {
            "id": "probe-gateway",
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
        "contract_id": "rq_036_protocol_unique_entry_gate_contract_v1",
        "validator": "scripts/validate_protocol_unique_entry_gate.py",
        "entry_script": "scripts/required_gate_bundle_runner.py",
        "bundle_key": "required_gate_bundle_runner",
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
        "scope": "all_identity_instance_actions",
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
            "signer_secret_env": "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_PROBE_GATEWAY",
        },
        "egress_receipt_policy": {"required": True},
        "egress_grant_policy": {
            "required": True,
            "max_age_seconds": 300,
            "signer_mode": "runtime_env_secret",
            "signer_secret_env": "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_PROBE_GATEWAY",
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
    "skill_path_integrity_contract_v1": {
        "required": True,
        "contract_id": "rq_020_skill_path_integrity_contract_v1",
        "validator": "scripts/validate_skill_path_integrity.py",
        "required_skills": [],
    },
}

(probe_pack / "CURRENT_TASK.json").write_text(
    json.dumps(task, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
(probe_pack / "runtime" / "state" / "protocol_gateway_signing_key.txt").write_text(
    "local-readable-attacker-key\n",
    encoding="utf-8",
)
(fixture_root / "catalog.yaml").write_text(
    yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

CATALOG_PATH="${FIXTURE_ROOT}/catalog.yaml"
IDENTITY_ID="probe-gateway"
ACTOR_ID="assistant:ci-probe"
SESSION_ID="session-gateway-probe"
SESSION_CHAIN_RUN_ID="probe-gateway-session-chain-headstamp"
INGRESS_WRAPPER_PATH="${FIXTURE_ROOT}/identity/probe-gateway/runtime/gate/protocol_ingress_wrapper.py"
EGRESS_WRAPPER_PATH="${FIXTURE_ROOT}/identity/probe-gateway/runtime/gate/protocol_egress_wrapper.py"
SESSION_CHAIN_WRAPPER_PATH="${FIXTURE_ROOT}/identity/probe-gateway/runtime/gate/protocol_session_chain_wrapper.py"
export IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_PROBE_GATEWAY="gateway-env-secret-only"

python3 scripts/repair_contract_backfill.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --apply \
  --json-only >/dev/null

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

def stale_reasons(d: dict) -> list[str]:
    out: list[str] = []
    for key in ("stale_reasons", "mapping_errors"):
        rows = d.get(key)
        if isinstance(rows, list):
            out.extend(str(x).strip() for x in rows if str(x).strip())
    return out

if name == "runner_local_key_forge_blocked":
    if rc == 0:
        raise SystemExit("runner_local_key_forge_blocked: expected non-zero rc")
    reasons = stale_reasons(doc)
    proof_status = str(doc.get("wrapper_dispatch_proof_status", "")).strip().upper()
    if proof_status != "FAIL_REQUIRED" and "wrapper_dispatch_proof_signature_invalid" not in reasons:
        raise SystemExit("runner_local_key_forge_blocked: expected signature/provenance block")
elif name == "runner_env_secret_forge_blocked":
    if rc == 0:
        raise SystemExit("runner_env_secret_forge_blocked: expected non-zero rc")
    reasons = stale_reasons(doc)
    if (
        "wrapper_parent_attestation_parent_command_mismatch" not in reasons
        and "wrapper_parent_attestation_parent_command_missing" not in reasons
    ):
        raise SystemExit("runner_env_secret_forge_blocked: expected parent attestation block")
elif name == "final_emit_local_key_forge_blocked":
    if rc == 0:
        raise SystemExit("final_emit_local_key_forge_blocked: expected non-zero rc")
    reasons = stale_reasons(doc)
    if "egress_grant_signature_invalid" not in reasons and str(doc.get("error_code", "")).strip() != "IP-HDSTAMP-003":
        raise SystemExit("final_emit_local_key_forge_blocked: expected grant signature block")
elif name == "final_emit_env_secret_forge_blocked":
    if rc == 0:
        raise SystemExit("final_emit_env_secret_forge_blocked: expected non-zero rc")
    reasons = stale_reasons(doc)
    if (
        "egress_wrapper_parent_attestation_parent_command_mismatch" not in reasons
        and "egress_wrapper_parent_attestation_parent_command_missing" not in reasons
    ):
        raise SystemExit("final_emit_env_secret_forge_blocked: expected parent attestation block")
elif name == "direct_text_emit":
    if rc == 0:
        raise SystemExit("direct_text_emit: expected non-zero rc")
    reasons = stale_reasons(doc)
    if "egress_grant_missing" not in reasons and str(doc.get("error_code", "")).strip() != "IP-HDSTAMP-003":
        raise SystemExit("direct_text_emit: expected missing grant headstamp block")
elif name == "channel_bypass_emit":
    if rc == 0:
        raise SystemExit("channel_bypass_emit: expected non-zero rc")
    reasons = stale_reasons(doc)
    if (
        "session_chain_parent_attestation_env_path_missing" not in reasons
        and "session_chain_parent_attestation_parent_command_mismatch" not in reasons
        and "session_chain_parent_attestation_parent_command_missing" not in reasons
        and "ingress_receipt_run_id_mismatch" not in reasons
    ):
        raise SystemExit("channel_bypass_emit: expected channel bypass attestation block")
elif name == "egress_wrapper_direct_call_blocked":
    if rc == 0:
        raise SystemExit("egress_wrapper_direct_call_blocked: expected non-zero rc")
    reasons = stale_reasons(doc)
    if (
        "session_chain_parent_attestation_env_path_missing" not in reasons
        and "session_chain_parent_attestation_parent_command_mismatch" not in reasons
        and "session_chain_parent_attestation_parent_command_missing" not in reasons
    ):
        raise SystemExit("egress_wrapper_direct_call_blocked: expected session-chain parent attestation block")
elif name == "session_chain_headstamp_first_line_required":
    if rc != 0:
        raise SystemExit("session_chain_headstamp_first_line_required: expected zero rc")
    status = str(doc.get("protocol_session_chain_wrapper_status", "")).strip().upper()
    if status != "PASS_REQUIRED":
        raise SystemExit("session_chain_headstamp_first_line_required: expected PASS_REQUIRED status")
    preview = doc.get("reply_preview")
    first_line = ""
    if isinstance(preview, list) and preview:
        first_line = str(preview[0] or "").strip()
    if not first_line.startswith("Identity-Context:"):
        raise SystemExit("session_chain_headstamp_first_line_required: missing Identity-Context first line")
    if str(doc.get("headstamp_first_line_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("session_chain_headstamp_first_line_required: headstamp_first_line_status must be PASS_REQUIRED")
    required_tuple = (
        "outlet_channel_id",
        "outlet_preflight_receipt",
        "outlet_bypass_detected",
        "final_emit_channel_id",
        "final_emit_policy_mode",
        "final_emit_schema_id",
        "final_emit_schema_status",
        "final_emit_contract_status",
        "emit_channel_id",
        "wrapper_surface_status",
        "entry_receipt_tuple_status",
    )
    missing_tuple = [key for key in required_tuple if key not in doc]
    if missing_tuple:
        raise SystemExit(
            "session_chain_headstamp_first_line_required: tuple fields missing: " + ",".join(sorted(missing_tuple))
        )
    if str(doc.get("final_emit_contract_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("session_chain_headstamp_first_line_required: final_emit_contract_status must be PASS_REQUIRED")
    if str(doc.get("entry_receipt_tuple_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("session_chain_headstamp_first_line_required: entry_receipt_tuple_status must be PASS_REQUIRED")
elif name == "strict_first_line_missing_evidence_blocked":
    if rc == 0:
        raise SystemExit("strict_first_line_missing_evidence_blocked: expected non-zero rc")
    status = str(doc.get("reply_first_line_status", "")).strip().upper()
    if status != "FAIL_REQUIRED":
        raise SystemExit("strict_first_line_missing_evidence_blocked: expected FAIL_REQUIRED status")
    reasons = stale_reasons(doc)
    if "reply_evidence_missing" not in reasons:
        raise SystemExit("strict_first_line_missing_evidence_blocked: expected reply_evidence_missing reason")
    enforce_mode = str(doc.get("reply_first_line_gate_enforce_mode", "")).strip().lower()
    if enforce_mode != "strict_default":
        raise SystemExit("strict_first_line_missing_evidence_blocked: expected strict_default enforce mode")
elif name == "resolve_context_timeout_guard":
    if rc != 0:
        raise SystemExit("resolve_context_timeout_guard: expected zero rc")
    status = str(doc.get("gateway_timeout_guard_probe_status", "")).strip().upper()
    if status != "PASS_REQUIRED":
        raise SystemExit("resolve_context_timeout_guard: expected PASS_REQUIRED status")
    marker_present = bool(doc.get("gateway_timeout_guard_probe_marker_present", False))
    if not marker_present:
        raise SystemExit("resolve_context_timeout_guard: expected timeout marker present")
    error_code = str(doc.get("gateway_timeout_guard_probe_observed_error_code", "")).strip()
    if error_code != "IP-CTX-TOOL-001":
        raise SystemExit("resolve_context_timeout_guard: expected IP-CTX-TOOL-001 error code")
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

  echo "[GATEWAY][PROBE] ${name} rc=${rc} file=${stdout_path}"
}

cd "${REPO_ROOT}"

FORGED_RUNNER_PAYLOAD_JSON="${RESULT_ROOT}/runner_forged_proof.json"
FORGED_RUNNER_PAYLOAD_SIG="${RESULT_ROOT}/runner_forged_proof.sig"
FORGED_RUNNER_ENV_PAYLOAD_JSON="${RESULT_ROOT}/runner_forged_env_proof.json"
FORGED_RUNNER_ENV_PAYLOAD_SIG="${RESULT_ROOT}/runner_forged_env_proof.sig"
FORGED_EGRESS_GRANT_JSON="${RESULT_ROOT}/egress_forged_grant.json"
FORGED_EGRESS_GRANT_SIG="${RESULT_ROOT}/egress_forged_grant.sig"
FORGED_EGRESS_ENV_GRANT_JSON="${RESULT_ROOT}/egress_forged_env_grant.json"
FORGED_EGRESS_ENV_GRANT_SIG="${RESULT_ROOT}/egress_forged_env_grant.sig"

python3 - <<'PY' "${FORGED_RUNNER_PAYLOAD_JSON}" "${FORGED_RUNNER_PAYLOAD_SIG}"
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
    "identity_id": "probe-gateway",
    "operation": "validate",
    "run_id": "probe-gateway-forged-runner",
    "actor_id": "assistant:ci-probe",
    "session_id": "session-gateway-probe",
    "work_layer": "instance",
    "source_layer": "project",
    "surface_label": "host_ingress_wrapper",
    "issued_at_epoch": int(time.time()),
    "nonce": secrets.token_hex(16),
}
canonical = json.dumps(proof, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
sig = hmac.new(b"local-readable-attacker-key", canonical.encode("utf-8"), hashlib.sha256).hexdigest()
Path(sys.argv[1]).write_text(canonical, encoding="utf-8")
Path(sys.argv[2]).write_text(sig + "\n", encoding="utf-8")
PY

run_probe runner_local_key_forge_blocked \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --run-id probe-gateway-forged-runner \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --surface-label host_ingress_wrapper \
  --wrapper-dispatch-token instance_wrapper_ingress_v1 \
  --wrapper-proof-json "$(cat "${FORGED_RUNNER_PAYLOAD_JSON}")" \
  --wrapper-proof-signature "$(tr -d '\n' < "${FORGED_RUNNER_PAYLOAD_SIG}")" \
  --json-only

python3 - <<'PY' "${FORGED_RUNNER_ENV_PAYLOAD_JSON}" "${FORGED_RUNNER_ENV_PAYLOAD_SIG}"
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
    "identity_id": "probe-gateway",
    "operation": "validate",
    "run_id": "probe-gateway-forged-runner-env",
    "actor_id": "assistant:ci-probe",
    "session_id": "session-gateway-probe",
    "work_layer": "instance",
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

run_probe runner_env_secret_forge_blocked \
  env IDENTITY_PROTOCOL_INGRESS_WRAPPER_PATH="${INGRESS_WRAPPER_PATH}" \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --run-id probe-gateway-forged-runner-env \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --surface-label host_ingress_wrapper \
  --wrapper-dispatch-token instance_wrapper_ingress_v1 \
  --wrapper-proof-json "$(cat "${FORGED_RUNNER_ENV_PAYLOAD_JSON}")" \
  --wrapper-proof-signature "$(tr -d '\n' < "${FORGED_RUNNER_ENV_PAYLOAD_SIG}")" \
  --json-only

python3 - <<'PY' "${FORGED_EGRESS_GRANT_JSON}" "${FORGED_EGRESS_GRANT_SIG}"
from __future__ import annotations
import hashlib
import hmac
import json
import secrets
import time
import sys
from pathlib import Path

body = "forged grant direct egress probe"
grant = {
    "schema_version": "v1",
    "identity_id": "probe-gateway",
    "actor_id": "assistant:ci-probe",
    "session_id": "session-gateway-probe",
    "run_id": "probe-gateway-forged-egress",
    "outlet_channel_id": "final_emit_governed",
    "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    "ingress_receipt_id": "forged-ingress-receipt-id",
    "issued_at_epoch": int(time.time()),
    "nonce": secrets.token_hex(16),
}
canonical = json.dumps(grant, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
sig = hmac.new(b"local-readable-attacker-key", canonical.encode("utf-8"), hashlib.sha256).hexdigest()
Path(sys.argv[1]).write_text(canonical, encoding="utf-8")
Path(sys.argv[2]).write_text(sig + "\n", encoding="utf-8")
PY

run_probe final_emit_local_key_forge_blocked \
  python3 scripts/final_emit_governed.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --run-id probe-gateway-forged-egress \
  --body-text "forged grant direct egress probe" \
  --work-layer instance \
  --source-layer project \
  --strict-explicit-context \
  --egress-grant-json "$(cat "${FORGED_EGRESS_GRANT_JSON}")" \
  --egress-grant-signature "$(tr -d '\n' < "${FORGED_EGRESS_GRANT_SIG}")" \
  --json-only

python3 - <<'PY' "${FORGED_EGRESS_ENV_GRANT_JSON}" "${FORGED_EGRESS_ENV_GRANT_SIG}"
from __future__ import annotations
import hashlib
import hmac
import json
import secrets
import time
import sys
from pathlib import Path

body = "forged env grant direct egress probe"
grant = {
    "schema_version": "v1",
    "identity_id": "probe-gateway",
    "actor_id": "assistant:ci-probe",
    "session_id": "session-gateway-probe",
    "run_id": "probe-gateway-forged-egress-env",
    "outlet_channel_id": "final_emit_governed",
    "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    "ingress_receipt_id": "forged-ingress-receipt-id",
    "issued_at_epoch": int(time.time()),
    "nonce": secrets.token_hex(16),
}
canonical = json.dumps(grant, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
sig = hmac.new(b"gateway-env-secret-only", canonical.encode("utf-8"), hashlib.sha256).hexdigest()
Path(sys.argv[1]).write_text(canonical, encoding="utf-8")
Path(sys.argv[2]).write_text(sig + "\n", encoding="utf-8")
PY

run_probe final_emit_env_secret_forge_blocked \
  env IDENTITY_PROTOCOL_EGRESS_WRAPPER_PATH="${EGRESS_WRAPPER_PATH}" \
  python3 scripts/final_emit_governed.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --run-id probe-gateway-forged-egress-env \
  --body-text "forged env grant direct egress probe" \
  --work-layer instance \
  --source-layer project \
  --strict-explicit-context \
  --egress-grant-json "$(cat "${FORGED_EGRESS_ENV_GRANT_JSON}")" \
  --egress-grant-signature "$(tr -d '\n' < "${FORGED_EGRESS_ENV_GRANT_SIG}")" \
  --json-only

run_probe direct_text_emit \
  python3 scripts/final_emit_governed.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --run-id probe-gateway-direct-text-emit \
  --body-text "direct text emit bypass probe" \
  --work-layer instance \
  --source-layer project \
  --strict-explicit-context \
  --json-only

run_probe channel_bypass_emit \
  python3 "${EGRESS_WRAPPER_PATH}" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --run-id probe-gateway-channel-bypass \
  --work-layer instance \
  --source-layer project \
  --candidate-output "channel bypass emit probe" \
  --ingress-receipt "${FIXTURE_ROOT}/identity/probe-gateway/runtime/state/required_gate_bundle_entry.latest.json" \
  --json-only

python3 "${INGRESS_WRAPPER_PATH}" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation inspection \
  --run-id probe-gateway-direct-egress \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --work-layer instance \
  --source-layer project \
  --json-only >/dev/null

run_probe egress_wrapper_direct_call_blocked \
  python3 "${EGRESS_WRAPPER_PATH}" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --run-id probe-gateway-direct-egress \
  --work-layer instance \
  --source-layer project \
  --candidate-output "direct egress wrapper bypass probe" \
  --ingress-receipt "${FIXTURE_ROOT}/identity/probe-gateway/runtime/state/required_gate_bundle_entry.latest.json" \
  --json-only

python3 scripts/recover_host_visible_post_check_state.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog identity/catalog/identities.yaml \
  --identity-id "${IDENTITY_ID}" \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --run-id "${SESSION_CHAIN_RUN_ID}" \
  --json-only >/dev/null

run_probe session_chain_headstamp_first_line_required \
  python3 "${SESSION_CHAIN_WRAPPER_PATH}" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --actor-id "${ACTOR_ID}" \
  --session-id "${SESSION_ID}" \
  --run-id "${SESSION_CHAIN_RUN_ID}" \
  --work-layer instance \
  --source-layer project \
  --operation inspection \
  --message "session chain headstamp required probe" \
  --json-only

run_probe strict_first_line_missing_evidence_blocked \
  python3 scripts/validate_reply_identity_context_first_line.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog identity/catalog/identities.yaml \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --force-check \
  --json-only

run_probe resolve_context_timeout_guard \
  python3 scripts/probe_gateway_timeout_guard.py \
  --protocol-root "${REPO_ROOT}" \
  --timeout-seconds 1 \
  --sleep-seconds 2 \
  --json-only

python3 - <<'PY' "${MANIFEST_PATH}" "${RESULT_ROOT}"
from __future__ import annotations

import json
from pathlib import Path
import sys

manifest_path = Path(sys.argv[1]).resolve()
result_root = Path(sys.argv[2]).resolve()
items = []
for meta_path in sorted(result_root.glob("*.meta.json")):
    doc = json.loads(meta_path.read_text(encoding="utf-8"))
    items.append(doc)

manifest = {
    "suite": "gateway_wrapper_trust_boundary_probes_ci",
    "count": len(items),
    "items": items,
}
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[GATEWAY][MANIFEST] {manifest_path}")
PY
