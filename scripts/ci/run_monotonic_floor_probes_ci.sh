#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-${REPO_ROOT}}/.tmp-runtime}}"
WORK_ROOT="${MONOTONIC_PROBE_WORK_ROOT:-${TMP_ROOT_BASE%/}/identity-monotonic-floor-probes}"
FIXTURE_ROOT="${WORK_ROOT}/fixtures"
RESULT_ROOT="${WORK_ROOT}/results"
MANIFEST_PATH="${WORK_ROOT}/manifest.monotonic_floor_probes.json"

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
probe_floor_pack = identity_root / "probe-floor"
probe_mm_pack = identity_root / "probe-mm"

(probe_floor_pack / "runtime").mkdir(parents=True, exist_ok=True)
(probe_mm_pack / "runtime" / "plugins").mkdir(parents=True, exist_ok=True)
(probe_mm_pack / "runtime" / "reports").mkdir(parents=True, exist_ok=True)

catalog = {
    "default_identity": "probe-floor",
    "identities": [
        {
            "id": "probe-floor",
            "status": "active",
            "pack_path": str(probe_floor_pack),
        },
        {
            "id": "probe-mm",
            "status": "active",
            "pack_path": str(probe_mm_pack),
        },
    ],
}

reasoning_contract_floor = {
    "required": True,
    "contract_id": "rq_035_reasoning_loop_failclose_contract_v1",
    "plugin_id": "reasoning-loop-enforcement",
    "validator": "scripts/validate_reasoning_loop_failclose.py",
    "plugin_registry_path": "identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml",
    "contract_file": "identity/protocol/plugins/reasoning-loop-enforcement/plugin.contract.yaml",
    "reasoning_enforcement_level": "L0",
    "strict_run_id_binding": True,
    "runtime_report_selection_mode": "prefer_run_id",
}

reasoning_contract_mm = dict(reasoning_contract_floor)
reasoning_contract_mm["reasoning_enforcement_level"] = "L1"

multimodal_contract = {
    "required": True,
    "contract_id": "rq_034_multimodal_plugin_enforcement_contract_v1",
    "validator": "scripts/validate_multimodal_plugin_enforcement.py",
    "plugin_registry_path": "identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml",
    "provider_profiles_path": "identity/protocol/plugins/PROVIDER_PROFILES.current.yaml",
    "provider_binding_path_pattern": "runtime/plugins/provider-bindings.local.yaml",
}

(probe_floor_pack / "CURRENT_TASK.json").write_text(
    json.dumps(
        {
            "reasoning_loop_failclose_contract_v1": reasoning_contract_floor,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

(probe_mm_pack / "CURRENT_TASK.json").write_text(
    json.dumps(
        {
            "multimodal_plugin_enforcement_contract_v1": multimodal_contract,
            "reasoning_loop_failclose_contract_v1": reasoning_contract_mm,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

(probe_mm_pack / "runtime" / "plugins" / "provider-bindings.local.yaml").write_text(
    yaml.safe_dump(
        {
            "bindings": [
                {
                    "plugin_id": "multimodal-vision-enforcement",
                    "provider_profile_id": "glm46v_vision_prod",
                    "credential_ref": "vault:dummy/credential",
                    "enabled": True,
                }
            ]
        },
        sort_keys=False,
        allow_unicode=True,
    ),
    encoding="utf-8",
)

(probe_mm_pack / "runtime" / "reports" / "identity-upgrade-exec-probe-mm-1700000000.json").write_text(
    json.dumps(
        {
            "run_id": "identity-upgrade-exec-probe-mm-old",
            "check_results": [],
            "multimodal_runtime_evidence_status": "SKIPPED_NOT_REQUIRED",
            "runtime_stage_deferred": True,
            "runtime_stage_deferred_reason": "legacy_report_missing_runtime_stage_pre_execution",
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

(fixture_root / "catalog.yaml").write_text(
    yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

CATALOG_PATH="${FIXTURE_ROOT}/catalog.yaml"

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

if name == "reasoning_floor_l0_fail":
    if rc == 0:
        raise SystemExit("reasoning_floor_l0_fail: expected non-zero rc")
    if str(doc.get("reasoning_loop_failclose_status", "")).strip().upper() != "FAIL_REQUIRED":
        raise SystemExit("reasoning_floor_l0_fail: status mismatch")
    if str(doc.get("error_code", "")).strip() != "IP-RL-CONF-001":
        raise SystemExit("reasoning_floor_l0_fail: error_code mismatch")
elif name == "multimodal_update_defer_allowed":
    if rc != 0:
        raise SystemExit("multimodal_update_defer_allowed: expected rc=0")
    if str(doc.get("multimodal_plugin_enforcement_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("multimodal_update_defer_allowed: plugin status mismatch")
    if str(doc.get("multimodal_runtime_evidence_status", "")).strip().upper() != "SKIPPED_NOT_REQUIRED":
        raise SystemExit("multimodal_update_defer_allowed: runtime evidence status mismatch")
elif name == "multimodal_readiness_skip_blocked":
    if rc == 0:
        raise SystemExit("multimodal_readiness_skip_blocked: expected non-zero rc")
    if str(doc.get("multimodal_plugin_enforcement_status", "")).strip().upper() != "FAIL_REQUIRED":
        raise SystemExit("multimodal_readiness_skip_blocked: plugin status mismatch")
    error_code = str(doc.get("error_code", "")).strip()
    allowed_error_codes = {"IP-MM-RUN-003", "IP-MM-RUN-007", "IP-GATE-ENTRY-002"}
    if error_code not in allowed_error_codes:
        raise SystemExit(
            "multimodal_readiness_skip_blocked: unexpected error_code "
            + (error_code or "<empty>")
        )
else:
    raise SystemExit(f"unknown probe name: {name}")
PY

  local sha256
  sha256="$(python3 - <<'PY' "${stdout_path}"
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
)"

  python3 - <<'PY' "${meta_path}" "${name}" "${stdout_path}" "${sha256}" "${cmd_string}" "${rc}" "${timestamp_utc}"
from __future__ import annotations

import json
import sys
from pathlib import Path

meta_path = Path(sys.argv[1])
name = sys.argv[2]
stdout_path = Path(sys.argv[3])
sha256 = sys.argv[4]
cmd = sys.argv[5]
rc = int(sys.argv[6])
timestamp_utc = sys.argv[7]

payload = {
    "name": name,
    "file": str(stdout_path.resolve()),
    "sha256": sha256,
    "command": cmd,
    "rc": rc,
    "timestamp_utc": timestamp_utc,
}
meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

  echo "[MONOTONIC][PROBE] ${name} rc=${rc} file=${stdout_path}"
}

cd "${REPO_ROOT}"

run_probe reasoning_floor_l0_fail \
  python3 scripts/validate_reasoning_loop_failclose.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-floor \
  --operation validate \
  --json-only

run_probe multimodal_update_defer_allowed \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation update \
  --run-id identity-upgrade-exec-probe-mm-new \
  --target-name multimodal_plugin_enforcement \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

run_probe multimodal_readiness_skip_blocked \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation readiness \
  --run-id identity-upgrade-exec-probe-mm-new \
  --target-name multimodal_plugin_enforcement \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

python3 - <<'PY' "${RESULT_ROOT}" "${MANIFEST_PATH}"
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

result_root = Path(sys.argv[1]).resolve()
manifest_path = Path(sys.argv[2]).resolve()

entries = []
for path in sorted(result_root.glob("*.meta.json")):
    entries.append(json.loads(path.read_text(encoding="utf-8")))

manifest = {
    "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "entries": entries,
}
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False))
PY

echo "[MONOTONIC][PASS] manifest=${MANIFEST_PATH}"
