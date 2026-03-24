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
reports_root = runtime_root / "reports"
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
reports_root.mkdir(parents=True, exist_ok=True)
(reports_root / f"{identity_id}-active-run.json").write_text(
    json.dumps(
        {
            "run_id": f"{identity_id}-sample-run",
            "generated_at": "2026-03-24T00:00:00Z",
            "artifacts": [],
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
(pack_root / "runtime" / "state" / "active_execution_report.json").write_text(
    json.dumps(
        {
            "run_id": f"{identity_id}-sample-run",
            "report_path": str((reports_root / f"{identity_id}-active-run.json").resolve()),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
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

python3 - "${ROOT}" "${CATALOG_PATH}" "${IDENTITY_ID}" "${PACK_ROOT}" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
catalog_path = Path(sys.argv[2]).resolve()
identity_id = sys.argv[3]
pack_root = Path(sys.argv[4]).resolve()
prompt_path = (pack_root / "IDENTITY_PROMPT.md").resolve()
runtime_state_path = (pack_root / "runtime" / "state" / "prompt_contract.json").resolve()
active_run_report = (pack_root / "runtime" / "reports" / f"{identity_id}-active-run.json").resolve()


def parse_payload(text: str) -> dict:
    text = str(text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


validators = [
    ("scripts/validate_prompt_bootstrap_capability.py", "prompt_bootstrap_contract_status"),
    ("scripts/validate_prompt_capability_matrix.py", "prompt_capability_matrix_status"),
    ("scripts/validate_prompt_derivation_conformance.py", "prompt_derivation_conformance_status"),
]

for script, status_field in validators:
    proc = subprocess.run(
        [
            "python3",
            script,
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--operation",
            "ci",
            "--json-only",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"prompt validator unexpectedly failed before live proof: {script}\n{proc.stderr or proc.stdout}")
    payload = parse_payload(proc.stdout)
    assert payload[status_field] == "PASS_REQUIRED", payload
    assert payload["requiredization_current_round_linked"] is False, payload
    assert payload["current_run_driver_binding_status"] == "FAIL_REQUIRED", payload
    assert payload["evidence_origin"] == "prompt_presence", payload

prompt_sha = sha256(prompt_path)
runtime_state_path.write_text(
    json.dumps(
        {
            "schema": "prompt_runtime_state_v1",
            "identity_prompt_path": str(prompt_path),
            "prompt_policy_hash": prompt_sha,
            "last_upgrade_run_id": f"{identity_id}-sample-run",
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
active_run_report.write_text(
    json.dumps(
        {
            "run_id": f"{identity_id}-sample-run",
            "identity_prompt_path": str(prompt_path),
            "identity_prompt_hash_after": prompt_sha,
            "prompt_policy_hash": prompt_sha,
            "runtime_state_artifact_path": str(runtime_state_path),
            "prompt_runtime_state_binding_status": "PASS_REQUIRED",
            "prompt_runtime_state_externalization_status": "PASS_REQUIRED",
            "artifacts": [],
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

for script, status_field in validators:
    proc = subprocess.run(
        [
            "python3",
            script,
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--operation",
            "ci",
            "--json-only",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"prompt validator unexpectedly failed after live proof: {script}\n{proc.stderr or proc.stdout}")
    payload = parse_payload(proc.stdout)
    assert payload[status_field] == "PASS_REQUIRED", payload
    assert payload["requiredization_current_round_linked"] is True, payload
    assert payload["current_run_driver_binding_status"] == "PASS_REQUIRED", payload
    assert payload["driver_run_id"] == f"{identity_id}-sample-run", payload
    assert payload["driver_projection_digest"] == prompt_sha, payload
    assert payload["evidence_origin"] == "live", payload
PY

PROMPT_ABSORBED_JSON="${TMP_ROOT}/weak-live-linkage-prompt-absorbed.json"
python3 "${ROOT}/scripts/validate_identity_weak_live_linkage.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --operation ci \
  --json-only >"${PROMPT_ABSORBED_JSON}"

python3 - <<'PY' "${PROMPT_ABSORBED_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_weak_live_linkage_status"] == "PASS_REQUIRED", payload
assert payload["overall_linkage_status"] == "FAIL_REQUIRED", payload
assert payload["operational_closure_class"] == "sample_or_history_green", payload
assert payload["false_green_family"] == "sample_report_only", payload
prompt_family = next(row for row in payload["family_rows"] if row.get("family") == "prompt_presence_only")
assert prompt_family["run_binding_status"] == "PASS_REQUIRED", prompt_family
assert prompt_family["consumption_status"] == "PASS_REQUIRED", prompt_family
PY

python3 - "${ROOT}" "${CATALOG_PATH}" "${IDENTITY_ID}" "${PACK_ROOT}" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
catalog_path = Path(sys.argv[2]).resolve()
identity_id = sys.argv[3]
pack_root = Path(sys.argv[4]).resolve()
runtime_examples = pack_root / "runtime" / "examples"
runtime_reports = pack_root / "runtime" / "reports"
active_run_report = runtime_reports / f"{identity_id}-active-run.json"
active_pointer = pack_root / "runtime" / "state" / "active_execution_report.json"


def parse_payload(text: str) -> dict:
    text = str(text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        return json.loads(text[start : end + 1])

validators = [
    (
        "capability_arbitration",
        "scripts/validate_identity_capability_arbitration.py",
        "capability_arbitration_status",
        runtime_examples / f"{identity_id}-capability-arbitration-sample.json",
        runtime_reports / f"{identity_id}-capability-arbitration-live.json",
    ),
    (
        "experience_feedback",
        "scripts/validate_identity_experience_feedback.py",
        "experience_feedback_status",
        runtime_examples / f"{identity_id}-experience-feedback-sample.json",
        runtime_reports / f"{identity_id}-experience-feedback-live.json",
    ),
    (
        "knowledge_acquisition",
        "scripts/validate_identity_knowledge_acquisition.py",
        "knowledge_acquisition_status",
        runtime_examples / f"{identity_id}-knowledge-acquisition-sample.json",
        runtime_reports / f"{identity_id}-knowledge-acquisition-live.json",
    ),
    (
        "trigger_regression",
        "scripts/validate_identity_trigger_regression.py",
        "trigger_regression_status",
        runtime_examples / f"{identity_id}-trigger-regression-sample.json",
        runtime_reports / f"{identity_id}-trigger-regression-live.json",
    ),
]

for name, script, status_field, _sample_path, _live_path in validators:
    proc = subprocess.run(
        [
            "python3",
            script,
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"{name} sample projection unexpectedly failed: {proc.stderr or proc.stdout}")
    payload = parse_payload(proc.stdout)
    assert payload[status_field] == "PASS_REQUIRED", payload
    assert payload["evidence_origin"] == "sample", payload
    assert payload["strict_live_proof_status"] == "FAIL_REQUIRED", payload
    assert payload["strict_live_operational_status"] == "FAIL_REQUIRED", payload
    assert payload["operational_closure_class"] == "sample_or_history_green", payload
    assert payload["live_binding_strength"] == "weak", payload
    assert payload["next_hop_consumption_status"] == "FAIL_REQUIRED", payload
    assert payload["report_selection_mode"] == "fallback_report", payload

live_run_id = f"{identity_id}-live-run"
artifacts: list[str] = []
for _name, _script, _status_field, sample_path, live_path in validators:
    doc = json.loads(sample_path.read_text(encoding="utf-8"))
    doc["run_id"] = live_run_id
    live_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifacts.append(str(live_path.resolve()))

active_doc = json.loads(active_run_report.read_text(encoding="utf-8"))
active_doc["run_id"] = live_run_id
active_doc["generated_at"] = "2026-03-24T00:00:00Z"
active_doc["artifacts"] = artifacts
active_run_report.write_text(json.dumps(active_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
active_pointer.write_text(
    json.dumps(
        {
            "run_id": live_run_id,
            "report_path": str(active_run_report.resolve()),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

for name, script, status_field, _sample_path, live_path in validators:
    proc = subprocess.run(
        [
            "python3",
            script,
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"{name} live projection unexpectedly failed: {proc.stderr or proc.stdout}")
    payload = parse_payload(proc.stdout)
    assert payload[status_field] == "PASS_REQUIRED", payload
    assert payload["evidence_origin"] == "live", payload
    assert payload["run_id_binding_status"] == "PASS_REQUIRED", payload
    assert payload["strict_live_proof_status"] == "PASS_REQUIRED", payload
    assert payload["strict_live_operational_status"] == "PASS_REQUIRED", payload
    assert payload["operational_closure_class"] == "full_operational_closure", payload
    assert payload["live_binding_strength"] == "strict", payload
    assert payload["next_hop_consumption_status"] == "PASS_REQUIRED", payload
    assert payload["report_selection_mode"] == "current_run_live_report", payload
    assert payload["live_candidate_selected_path"] == str(live_path.resolve()), payload
PY

SAMPLE_ABSORBED_JSON="${TMP_ROOT}/weak-live-linkage-sample-absorbed.json"
python3 "${ROOT}/scripts/validate_identity_weak_live_linkage.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --operation ci \
  --json-only >"${SAMPLE_ABSORBED_JSON}"

python3 - <<'PY' "${SAMPLE_ABSORBED_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_weak_live_linkage_status"] == "PASS_REQUIRED", payload
assert payload["overall_linkage_status"] == "FAIL_REQUIRED", payload
assert payload["false_green_family"] == "loop_meta_only", payload
sample_family = next(row for row in payload["family_rows"] if row.get("family") == "sample_report_only")
assert sample_family["run_binding_status"] == "PASS_REQUIRED", sample_family
assert sample_family["consumption_status"] == "PASS_REQUIRED", sample_family
assert sample_family["closure_class"] == "full_operational_closure", sample_family
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
