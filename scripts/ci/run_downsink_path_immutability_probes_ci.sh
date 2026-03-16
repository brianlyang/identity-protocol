#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-${REPO_ROOT}}/.tmp-runtime}}"
WORK_ROOT="${DOWNSINK_PROBE_WORK_ROOT:-${TMP_ROOT_BASE%/}/identity-downsink-path-probes}"
FIXTURE_ROOT="${WORK_ROOT}/fixtures"
RESULT_ROOT="${WORK_ROOT}/results"
BASELINE_TASK_PATH="${WORK_ROOT}/baseline.CURRENT_TASK.json"
PROBE_MATRIX_PATH="${WORK_ROOT}/path_probe_matrix.v168.json"
MANIFEST_PATH="${WORK_ROOT}/manifest.downsink_path_immutability.v168.json"

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
probe_pack = identity_root / "probe-downsink"
(probe_pack / "runtime" / "state").mkdir(parents=True, exist_ok=True)

catalog = {
    "default_identity": "probe-downsink",
    "identities": [
        {
            "id": "probe-downsink",
            "status": "active",
            "pack_path": str(probe_pack),
            "profile": "runtime",
            "runtime_mode": "local_only",
        }
    ],
}

(probe_pack / "CURRENT_TASK.json").write_text("{}\n", encoding="utf-8")
(fixture_root / "catalog.yaml").write_text(
    yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

CATALOG_PATH="${FIXTURE_ROOT}/catalog.yaml"
IDENTITY_ID="probe-downsink"
TASK_PATH="${FIXTURE_ROOT}/identity/probe-downsink/CURRENT_TASK.json"

cd "${REPO_ROOT}"

python3 scripts/repair_contract_backfill.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --apply \
  --json-only >/dev/null
cp "${TASK_PATH}" "${BASELINE_TASK_PATH}"

restore_task() {
  cp "${BASELINE_TASK_PATH}" "${TASK_PATH}"
}

rebuild_runtime_mirror() {
  python3 scripts/repair_contract_backfill.py \
    --catalog "${CATALOG_PATH}" \
    --identity-id "${IDENTITY_ID}" \
    --apply \
    --json-only >/dev/null
}

run_probe() {
  local name="$1"
  local expected_rc="$2"
  local status_field="$3"
  local expected_status="$4"
  shift 4
  local cmd=("$@")

  local stdout_path="${RESULT_ROOT}/${name}.stdout.json"
  local stderr_path="${RESULT_ROOT}/${name}.stderr.log"
  local meta_path="${RESULT_ROOT}/${name}.meta.json"
  local timestamp_utc
  timestamp_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  set +e
  "${cmd[@]}" >"${stdout_path}" 2>"${stderr_path}"
  local rc=$?
  set -e

  python3 - <<'PY' "${name}" "${expected_rc}" "${rc}" "${status_field}" "${expected_status}" "${stdout_path}"
from __future__ import annotations

import json
import sys
from pathlib import Path

name = sys.argv[1]
expected_rc = int(sys.argv[2])
actual_rc = int(sys.argv[3])
status_field = sys.argv[4]
expected_status = sys.argv[5]
stdout_path = Path(sys.argv[6])

if actual_rc != expected_rc:
    raise SystemExit(f"{name}: rc mismatch expected={expected_rc} actual={actual_rc}")

doc = json.loads(stdout_path.read_text(encoding="utf-8"))
status = str(doc.get(status_field, "")).strip().upper()
if status != expected_status:
    raise SystemExit(f"{name}: status mismatch field={status_field} expected={expected_status} actual={status}")
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
  local cmd_string
  cmd_string="$(printf '%q ' "${cmd[@]}")"
  cmd_string="${cmd_string% }"

  python3 - <<'PY' "${meta_path}" "${name}" "${stdout_path}" "${stderr_path}" "${rc}" "${expected_rc}" "${status_field}" "${expected_status}" "${sha256}" "${cmd_string}" "${timestamp_utc}"
from __future__ import annotations
import json
import sys
from pathlib import Path

meta_path = Path(sys.argv[1])
payload = {
    "name": sys.argv[2],
    "stdout_file": str(Path(sys.argv[3]).resolve()),
    "stderr_file": str(Path(sys.argv[4]).resolve()),
    "rc": int(sys.argv[5]),
    "expected_rc": int(sys.argv[6]),
    "status_field": sys.argv[7],
    "expected_status": sys.argv[8],
    "stdout_sha256": sys.argv[9],
    "command": sys.argv[10],
    "timestamp_utc": sys.argv[11],
}
meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

  echo "[DOWNSINK][PROBE] ${name} rc=${rc} file=${stdout_path}"
}

mutate_registry_entry_path() {
  local path_id="$1"
  local new_path="$2"
  python3 - <<'PY' "${TASK_PATH}" "${path_id}" "${new_path}"
from __future__ import annotations

import json
import sys
from pathlib import Path

task_path = Path(sys.argv[1]).resolve()
path_id = sys.argv[2]
new_path = sys.argv[3]
doc = json.loads(task_path.read_text(encoding="utf-8"))
contract = doc.get("protocol_downsink_path_immutability_contract_v1", {})
registry = contract.get("path_registry", {})
for domain in registry.values():
    if not isinstance(domain, dict):
        continue
    entries = domain.get("entries")
    if not isinstance(entries, list):
        continue
    for entry in entries:
        if isinstance(entry, dict) and str(entry.get("path_id", "")).strip() == path_id:
            entry["path"] = new_path
task_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
}

# Positive probes
restore_task
rebuild_runtime_mirror
run_probe probe_canonical_registry_pass 0 protocol_downsink_path_immutability_status PASS_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_immutability.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --json-only

run_probe probe_canonical_write_guard_pass 0 protocol_downsink_path_write_guard_status PASS_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_write_guard.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --json-only

run_probe probe_feedback_inquiry_requiredization_trigger_allowed 0 protocol_downsink_path_write_guard_status PASS_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_write_guard.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --probe-write-path "runtime/protocol-feedback/outbox-to-protocol/INQUIRY_REQUIREDIZATION_TRIGGER_20260316T000000Z.json" \
  --json-only

run_probe probe_feedback_sanitization_paraphrase_allowed 0 protocol_downsink_path_write_guard_status PASS_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_write_guard.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --probe-write-path "runtime/protocol-feedback/outbox-to-protocol/SANITIZATION_PARAPHRASE_20260316T000000Z.json" \
  --json-only

run_probe probe_feedback_session_lane_lock_protocol_allowed 0 protocol_downsink_path_write_guard_status PASS_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_write_guard.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --probe-write-path "runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_PROTOCOL_20260316T000000Z.json" \
  --json-only

run_probe probe_feedback_session_lane_lock_exit_allowed 0 protocol_downsink_path_write_guard_status PASS_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_write_guard.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --probe-write-path "runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_EXIT_20260316T000000Z.json" \
  --json-only

run_probe probe_canonical_literal_lock_pass 0 protocol_downsink_path_literal_lock_status PASS_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_literal_lock.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --json-only

# Negative probe: non-canonical mutation
restore_task
mutate_registry_entry_path "runtime_gate.ingress_wrapper" "runtime/gate/noncanonical_ingress_wrapper.py"
run_probe probe_path_registry_mutation_noncanonical 1 protocol_downsink_path_immutability_status FAIL_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_immutability.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --json-only

# Negative probe: parent escape
restore_task
mutate_registry_entry_path "runtime_gate.ingress_wrapper" "../runtime/gate/protocol_ingress_wrapper.py"
run_probe probe_parent_escape 1 protocol_downsink_path_immutability_status FAIL_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_immutability.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --json-only

# Negative probe: symlink escape
restore_task
rebuild_runtime_mirror
OUTBOX_DIR="${FIXTURE_ROOT}/identity/probe-downsink/runtime/protocol-feedback/outbox-to-protocol"
EXTERNAL_DIR="${WORK_ROOT}/symlink-external"
python3 - <<'PY' "${OUTBOX_DIR}" "${EXTERNAL_DIR}"
from __future__ import annotations

import shutil
import sys
from pathlib import Path

outbox_dir = Path(sys.argv[1])
external_dir = Path(sys.argv[2]).resolve()
external_dir.mkdir(parents=True, exist_ok=True)
external_target = (external_dir / "mirrored-outbox")
external_target.mkdir(parents=True, exist_ok=True)
if outbox_dir.exists() or outbox_dir.is_symlink():
    if outbox_dir.is_symlink() or outbox_dir.is_file():
        outbox_dir.unlink()
    else:
        shutil.rmtree(outbox_dir)
outbox_dir.parent.mkdir(parents=True, exist_ok=True)
outbox_dir.symlink_to(external_target, target_is_directory=True)
PY
run_probe probe_symlink_escape 1 protocol_downsink_path_write_guard_status FAIL_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_write_guard.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --json-only
python3 - <<'PY' "${OUTBOX_DIR}"
from __future__ import annotations
import sys
from pathlib import Path
outbox_dir = Path(sys.argv[1])
if outbox_dir.is_symlink():
    outbox_dir.unlink()
outbox_dir.mkdir(parents=True, exist_ok=True)
PY

# Negative probe: protocol-feedback non-registry write
restore_task
rebuild_runtime_mirror
run_probe probe_feedback_nonregistry_write 1 protocol_downsink_path_write_guard_status FAIL_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_write_guard.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --probe-write-path "runtime/protocol-feedback/noncanonical/FEEDBACK_BATCH_probe.md" \
  --json-only

# Negative probe: protocol-feedback noncanonical filename under canonical directory
restore_task
rebuild_runtime_mirror
run_probe probe_feedback_noncanonical_filename_write 1 protocol_downsink_path_write_guard_status FAIL_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_write_guard.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --probe-write-path "runtime/protocol-feedback/outbox-to-protocol/freeform_note_probe.md" \
  --json-only

# Negative probe: broadcast receipt non-registry write
restore_task
rebuild_runtime_mirror
run_probe probe_broadcast_nonregistry_receipt 1 protocol_downsink_path_write_guard_status FAIL_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_write_guard.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --probe-write-path "runtime/reports/noncanonical/broadcast-receipt-probe.json" \
  --json-only

# Negative probe: source literal lock with unregistered governed path
restore_task
rebuild_runtime_mirror
run_probe probe_unregistered_literal_fail 1 protocol_downsink_path_literal_lock_status FAIL_REQUIRED \
  python3 scripts/validate_protocol_downsink_path_literal_lock.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --operation validate \
  --probe-path-literal "runtime/protocol-feedback/outbox-legacy/FEEDBACK_BATCH_probe.md" \
  --json-only

python3 - <<'PY' "${RESULT_ROOT}" "${PROBE_MATRIX_PATH}" "${MANIFEST_PATH}"
from __future__ import annotations

import json
from pathlib import Path
import sys

result_root = Path(sys.argv[1]).resolve()
probe_matrix_path = Path(sys.argv[2]).resolve()
manifest_path = Path(sys.argv[3]).resolve()

rows = []
for meta_file in sorted(result_root.glob("*.meta.json")):
    rows.append(json.loads(meta_file.read_text(encoding="utf-8")))

probe_matrix = {
    "schema_version": "v1",
    "stream_version": "v1.6.8",
    "probe_count": len(rows),
    "probes": rows,
}
probe_matrix_path.write_text(json.dumps(probe_matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

manifest = {
    "schema_version": "v1",
    "stream_version": "v1.6.8",
    "work_root": str(result_root.parent),
    "probe_matrix_file": str(probe_matrix_path),
    "result_dir": str(result_root),
    "probe_meta_files": [str(p.resolve()) for p in sorted(result_root.glob("*.meta.json"))],
    "probe_stdout_files": [str(p.resolve()) for p in sorted(result_root.glob("*.stdout.json"))],
}
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

echo "[DOWNSINK][PROBE] PASS manifest=${MANIFEST_PATH}"
