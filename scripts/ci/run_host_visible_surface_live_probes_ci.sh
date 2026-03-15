#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-${REPO_ROOT}}/.tmp-runtime}}"
WORK_ROOT="${HOST_VISIBLE_SURFACE_PROBE_WORK_ROOT:-${TMP_ROOT_BASE%/}/identity-host-visible-surface-probes}"
FIXTURE_ROOT="${WORK_ROOT}/fixtures"
RESULT_ROOT="${WORK_ROOT}/results"
MANIFEST_PATH="${WORK_ROOT}/manifest.host_visible_surface_live.json"

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
probe_pack = identity_root / "probe-visible"
probe_pack.mkdir(parents=True, exist_ok=True)

catalog = {
    "default_identity": "probe-visible",
    "identities": [
        {
            "id": "probe-visible",
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
    }
}

(probe_pack / "CURRENT_TASK.json").write_text(
    json.dumps(task, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
(fixture_root / "catalog.yaml").write_text(
    yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

CATALOG_PATH="${FIXTURE_ROOT}/catalog.yaml"
IDENTITY_ID="probe-visible"

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
reasons = [str(x).strip() for x in (doc.get("stale_reasons") or []) if str(x).strip()]
status = str(doc.get("host_transport_wiring_attestation_status", "")).strip().upper()

if name == "host_visible_contract_static":
    if rc != 0:
        raise SystemExit("host_visible_contract_static: expected zero rc")
    if status != "PASS_REQUIRED":
        raise SystemExit("host_visible_contract_static: expected PASS_REQUIRED status")
elif name == "host_visible_live_receipts_pass":
    if rc != 0:
        raise SystemExit("host_visible_live_receipts_pass: expected zero rc")
    if status != "PASS_REQUIRED":
        raise SystemExit("host_visible_live_receipts_pass: expected PASS_REQUIRED status")
elif name == "host_visible_commentary_bypass_blocked":
    if rc == 0:
        raise SystemExit("host_visible_commentary_bypass_blocked: expected non-zero rc")
    token = "host_visible_surface_live_channel_status_not_pass:commentary:headstamp_first_line_status"
    if token not in reasons:
        raise SystemExit("host_visible_commentary_bypass_blocked: expected commentary fail-close token")
elif name == "host_visible_receipt_stale_blocked":
    if rc == 0:
        raise SystemExit("host_visible_receipt_stale_blocked: expected non-zero rc")
    if not any(
        token.startswith("host_visible_surface_live_channel_receipt_stale:commentary:")
        for token in reasons
    ):
        raise SystemExit("host_visible_receipt_stale_blocked: expected stale receipt fail-close token")
else:
    raise SystemExit(f"unknown probe name: {name}")
PY

  python3 - <<'PY' \
    "${name}" "${timestamp_utc}" "${rc}" "${cmd_string}" "${stdout_path}" "${stderr_path}" "${meta_path}"
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

run_probe host_visible_contract_static \
  python3 scripts/validate_host_transport_wiring_attestation.py \
    --catalog "${CATALOG_PATH}" \
    --identity-id "${IDENTITY_ID}" \
    --json-only

python3 - <<'PY' "${CATALOG_PATH}" "${IDENTITY_ID}" "${REPO_ROOT}"
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

repo_root = Path(sys.argv[3]).resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from tool_vendor_governance_common import resolve_pack_and_task

catalog_path = Path(sys.argv[1]).resolve()
identity_id = sys.argv[2]
pack_path, _ = resolve_pack_and_task(catalog_path, identity_id)
receipt_dir = pack_path / "runtime" / "reports" / "host-visible-surface"
receipt_dir.mkdir(parents=True, exist_ok=True)

fields = {
    "wrapper_surface_status": "PASS_REQUIRED",
    "entry_receipt_tuple_status": "PASS_REQUIRED",
    "headstamp_first_line_status": "PASS_REQUIRED",
    "send_time_gate_status": "PASS_REQUIRED",
    "final_emit_contract_status": "PASS_REQUIRED",
}
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
state_path = pack_path / "runtime" / "state" / "host_visible_surface_registry_state.json"
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
        "receipt_source": "ci_fixture",
    }
    payload.update(fields)
    path = receipt_dir / f"host-visible-surface-{idx:02d}-{channel}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state_doc["channels"][channel] = {
        "last_receipt_path": str(path),
        "last_status": "PASS_REQUIRED",
        "receipt_source": "ci_fixture",
        "last_run_id": f"fixture-{idx:02d}",
        "updated_at_utc": timestamp,
    }
state_path.parent.mkdir(parents=True, exist_ok=True)
state_path.write_text(json.dumps(state_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

run_probe host_visible_live_receipts_pass \
  python3 scripts/validate_host_transport_wiring_attestation.py \
    --catalog "${CATALOG_PATH}" \
    --identity-id "${IDENTITY_ID}" \
    --require-live-receipts \
    --allowed-live-receipt-sources runtime_dialogue,ci_fixture \
    --json-only

python3 - <<'PY' "${CATALOG_PATH}" "${IDENTITY_ID}" "${REPO_ROOT}"
from __future__ import annotations

import os
import time
from pathlib import Path
import sys

repo_root = Path(sys.argv[3]).resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from tool_vendor_governance_common import resolve_pack_and_task

catalog_path = Path(sys.argv[1]).resolve()
identity_id = sys.argv[2]
pack_path, _ = resolve_pack_and_task(catalog_path, identity_id)
path = pack_path / "runtime" / "reports" / "host-visible-surface" / "host-visible-surface-01-commentary.json"
stale_epoch = int(time.time()) - 600
os.utime(path, (stale_epoch, stale_epoch))
PY

run_probe host_visible_receipt_stale_blocked \
  python3 scripts/validate_host_transport_wiring_attestation.py \
    --catalog "${CATALOG_PATH}" \
    --identity-id "${IDENTITY_ID}" \
    --require-live-receipts \
    --allowed-live-receipt-sources runtime_dialogue,ci_fixture \
    --json-only

python3 - <<'PY' "${CATALOG_PATH}" "${IDENTITY_ID}" "${REPO_ROOT}"
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

repo_root = Path(sys.argv[3]).resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from tool_vendor_governance_common import resolve_pack_and_task

catalog_path = Path(sys.argv[1]).resolve()
identity_id = sys.argv[2]
pack_path, _ = resolve_pack_and_task(catalog_path, identity_id)
receipt_dir = pack_path / "runtime" / "reports" / "host-visible-surface"
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
path = receipt_dir / "host-visible-surface-01-commentary.json"
doc = json.loads(path.read_text(encoding="utf-8"))
doc["created_at_utc"] = timestamp
path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

python3 - <<'PY' "${CATALOG_PATH}" "${IDENTITY_ID}" "${REPO_ROOT}"
from __future__ import annotations

import json
from pathlib import Path
import sys

repo_root = Path(sys.argv[3]).resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from tool_vendor_governance_common import resolve_pack_and_task

catalog_path = Path(sys.argv[1]).resolve()
identity_id = sys.argv[2]
pack_path, _ = resolve_pack_and_task(catalog_path, identity_id)
path = pack_path / "runtime" / "reports" / "host-visible-surface" / "host-visible-surface-01-commentary.json"
doc = json.loads(path.read_text(encoding="utf-8"))
doc["headstamp_first_line_status"] = "FAIL_REQUIRED"
path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

run_probe host_visible_commentary_bypass_blocked \
  python3 scripts/validate_host_transport_wiring_attestation.py \
    --catalog "${CATALOG_PATH}" \
    --identity-id "${IDENTITY_ID}" \
    --require-live-receipts \
    --allowed-live-receipt-sources runtime_dialogue,ci_fixture \
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
    "suite": "host_visible_surface_live_probes",
    "results": entries,
}
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[PASS] host visible surface probe suite wrote manifest: {manifest_path}")
PY
