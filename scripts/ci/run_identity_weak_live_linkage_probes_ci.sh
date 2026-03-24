#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-weak-live-linkage-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

WORKSPACE_ROOT="${TMP_ROOT}/workspace"
IDENTITY_HOME="${WORKSPACE_ROOT}/.identity"
CATALOG_PATH="${IDENTITY_HOME}/catalog.local.yaml"
IDENTITY_ID="weak-live-linkage-probe"
PACK_ROOT="${IDENTITY_HOME}/${IDENTITY_ID}"
TASK_PATH="${PACK_ROOT}/CURRENT_TASK.json"

mkdir -p "${PACK_ROOT}/runtime" "${PACK_ROOT}/scripts" "${PACK_ROOT}/runtime/state"

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

from create_identity_pack import (
    _bootstrap_neutral_identity_samples,
    _neutral_full_contract_current_task,
)
from identity_weak_live_linkage_common import weak_live_linkage_contract_skeleton
from native_chat_headstamp_common import prompt_hard_guard_required_tokens

runtime_root = pack_root / "runtime"
task = _neutral_full_contract_current_task(
    identity_id,
    "Weak live linkage probe",
    "Hermetic weak live linkage probe pack",
    agent_identity_versions={
        "methodology_version": "v1.6",
        "prompt_version": "v1.6",
        "json_version": "v1.6",
    },
)
task["identity_weak_live_linkage_contract_v1"] = weak_live_linkage_contract_skeleton()
_bootstrap_neutral_identity_samples(identity_id, runtime_root, task["task_id"])

prompt_contract = task.get("prompt_bootstrap_capability_contract_v1", {})
required_drivers = prompt_contract.get("required_capability_drivers", []) if isinstance(prompt_contract, dict) else []
matrix_contract = task.get("prompt_capability_matrix_fail_closed_contract_v1", {})
required_driver_ids = matrix_contract.get("required_driver_ids", []) if isinstance(matrix_contract, dict) else []

prompt_lines = [
    f"# {identity_id}",
    "",
    "This prompt intentionally preserves declaration/presence surfaces without live driver receipts.",
    "Required capability drivers:",
]
for token in list(required_drivers) + list(required_driver_ids):
    prompt_lines.append(f"- {token}")
native_chat_contract = task.get("native_chat_headstamp_contract_v1", {})
required_literals = prompt_hard_guard_required_tokens(
    default_machine_profile=str(native_chat_contract.get("default_machine_profile", "mini")),
    template_ref=str(native_chat_contract.get("prompt_hard_guard_template_ref", "")).strip(),
)
prompt_lines.extend(["", "Native chat hard guard literals:"])
for literal in required_literals:
    prompt_lines.append(literal)
(pack_root / "IDENTITY_PROMPT.md").write_text("\n".join(prompt_lines) + "\n", encoding="utf-8")
(pack_root / "TASK_HISTORY.md").write_text("# Task history\n", encoding="utf-8")
(pack_root / "RULEBOOK.jsonl").write_text("", encoding="utf-8")
(pack_root / "runtime" / "state").mkdir(parents=True, exist_ok=True)
(pack_root / "runtime" / "state" / "active_execution_report.json").write_text(
    json.dumps({"selected_report_path": str((runtime_root / "examples" / f"{identity_id}-capability-arbitration-sample.json").resolve())}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
(pack_root / "CURRENT_TASK.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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
catalog_path.write_text(yaml.safe_dump(catalog_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
PY

PASS_JSON="${TMP_ROOT}/weak-live-linkage-pass.json"
python3 "${ROOT}/scripts/validate_identity_weak_live_linkage.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --operation ci \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_weak_live_linkage_status"] == "PASS_REQUIRED", payload
assert payload["weak_live_linkage_contract_status"] == "PASS_REQUIRED", payload
assert payload["operational_closure_class"] == "sample_or_history_green", payload
assert payload["false_green_family"] == "prompt_presence_only", payload
assert payload["philosophy_truth_lifecycle_status"] == "PASS_REQUIRED", payload
PY

python3 - <<'PY' "${TASK_PATH}"
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
doc = json.loads(path.read_text(encoding="utf-8"))
doc.pop("identity_weak_live_linkage_contract_v1", None)
path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

MISSING_JSON="${TMP_ROOT}/weak-live-linkage-missing-contract.json"
if python3 "${ROOT}/scripts/validate_identity_weak_live_linkage.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --operation ci \
  --json-only >"${MISSING_JSON}"; then
  echo "[FAIL] weak-live-linkage validator unexpectedly passed without contract"
  exit 1
fi

python3 - <<'PY' "${MISSING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_weak_live_linkage_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-WLL-001", payload
assert "required_contract_disabled_or_missing" in payload.get("contract_issues", []), payload
PY

BACKFILL_JSON="${TMP_ROOT}/weak-live-linkage-backfill.json"
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
assert payload["weak_live_linkage_contract_auto_wire_status"] == "PASS_REQUIRED", payload
PY

python3 - <<'PY' "${TASK_PATH}"
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
doc = json.loads(path.read_text(encoding="utf-8"))
contract = doc["identity_weak_live_linkage_contract_v1"]
contract["shared_cross_validation_primitive_refs"] = ["broken_shared_primitive"]
path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

BROKEN_JSON="${TMP_ROOT}/weak-live-linkage-broken-roundtable.json"
if python3 "${ROOT}/scripts/validate_identity_weak_live_linkage.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --operation ci \
  --json-only >"${BROKEN_JSON}"; then
  echo "[FAIL] weak-live-linkage validator unexpectedly passed with broken roundtable primitive ref"
  exit 1
fi

python3 - <<'PY' "${BROKEN_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_weak_live_linkage_status"] == "FAIL_REQUIRED", payload
assert "roundtable_shared_primitive_missing" in payload.get("contract_issues", []), payload
PY

echo "[PASS] identity weak live linkage probes passed"
