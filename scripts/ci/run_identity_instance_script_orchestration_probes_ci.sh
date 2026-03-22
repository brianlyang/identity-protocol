#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${ROOT}/scripts/shell_strict_entry_common.sh"
source "${ROOT}/scripts/runtime_temp_path_common.sh"

CATALOG_ARG=""
IDENTITY_ID="${IDENTITY_ID:-}"
WORK_LAYER="${WORK_LAYER:-instance}"
SOURCE_LAYER="${SOURCE_LAYER:-project}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --catalog)
      CATALOG_ARG="${2:-}"
      shift 2
      ;;
    --identity-id)
      IDENTITY_ID="${2:-}"
      shift 2
      ;;
    --work-layer)
      WORK_LAYER="${2:-instance}"
      shift 2
      ;;
    --source-layer)
      SOURCE_LAYER="${2:-project}"
      shift 2
      ;;
    *)
      echo "[FAIL] unknown argument: $1"
      exit 1
      ;;
  esac
done

CATALOG_PATH="$(protocol_shell_entry_resolve_project_catalog "${CATALOG_ARG}")"
export IDENTITY_RUNTIME_TMP_ROOT="${IDENTITY_RUNTIME_TMP_ROOT:-${ROOT}/.tmp}"
TMP_ROOT="$(identity_runtime_mktemp_dir_sh "identity-instance-script-orchestration-probes" "run")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

eval "$(
  ROOT="${ROOT}" CATALOG_PATH="${CATALOG_PATH}" IDENTITY_ID="${IDENTITY_ID}" WORK_LAYER="${WORK_LAYER}" SOURCE_LAYER="${SOURCE_LAYER}" python3 - <<'PY'
import os
import shlex
import sys
from pathlib import Path

import yaml

root = Path(os.environ["ROOT"]).resolve()
sys.path.insert(0, str(root / "scripts"))

from instance_script_orchestration_common import (  # noqa: E402
    STATUS_PASS_REQUIRED,
    build_route_orchestration_matrix,
    build_route_receipt_join_matrix,
    load_manifest_doc,
    orchestration_required,
    resolve_pack_task,
    validate_manifest_doc,
)

catalog_path = Path(os.environ["CATALOG_PATH"]).resolve()
requested_identity = str(os.environ.get("IDENTITY_ID", "")).strip()
work_layer = str(os.environ.get("WORK_LAYER", "instance")).strip().lower() or "instance"
source_layer = str(os.environ.get("SOURCE_LAYER", "project")).strip().lower() or "project"

catalog_doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
rows = [row for row in (catalog_doc.get("identities") or []) if isinstance(row, dict)]
candidate_ids = []
if requested_identity:
    candidate_ids = [requested_identity]
else:
    for row in rows:
        identity_id = str(row.get("id", "")).strip()
        if identity_id:
            candidate_ids.append(identity_id)

selected = None
for identity_id in candidate_ids:
    try:
        pack_root, task_path, task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task="",
            identity_id=identity_id,
        )
    except Exception:
        continue
    if not orchestration_required(task_doc):
        continue
    manifest_path, manifest_doc = load_manifest_doc(pack_root)
    if manifest_doc is None:
        continue
    manifest_validation = validate_manifest_doc(
        manifest_doc=manifest_doc,
        manifest_path=manifest_path,
        pack_root=pack_root,
        identity_id=identity_id,
    )
    if manifest_validation.get("status") != STATUS_PASS_REQUIRED:
        continue
    route_validation = build_route_orchestration_matrix(
        task_doc=task_doc,
        manifest_validation=manifest_validation,
        identity_id=identity_id,
        work_layer=work_layer,
        source_layer=source_layer,
    )
    if route_validation.get("status") != STATUS_PASS_REQUIRED:
        continue
    receipt_validation = build_route_receipt_join_matrix(
        pack_root=pack_root,
        task_doc=task_doc,
        manifest_validation=manifest_validation,
        route_validation=route_validation,
        identity_id=identity_id,
        require_observed=True,
    )
    if receipt_validation.get("status") != STATUS_PASS_REQUIRED:
        continue
    receipt_rows = [
        row
        for row in (receipt_validation.get("route_rows") or [])
        if isinstance(row, dict)
        and str(row.get("receipt_validation_status", "")).strip() == STATUS_PASS_REQUIRED
        and str(row.get("latest_receipt_path", "")).strip()
    ]
    if not receipt_rows:
        continue
    receipt_row = receipt_rows[0]
    selected = {
        "identity_id": identity_id,
        "pack_root": str(pack_root),
        "task_path": str(task_path),
        "manifest_path": str(manifest_path),
        "receipt_route": str(receipt_row.get("route", "")).strip(),
        "receipt_script_id": str(receipt_row.get("script_id", "")).strip(),
        "receipt_path": str(receipt_row.get("latest_receipt_path", "")).strip(),
    }
    break

if selected is None:
    raise SystemExit("no receipt-ready orchestration identity found for probes")

for key, value in selected.items():
    print(f"{key.upper()}={shlex.quote(str(value))}")
PY
)"

POS_MANIFEST_JSON="${TMP_ROOT}/positive-manifest.json"
POS_ORCH_JSON="${TMP_ROOT}/positive-orchestration.json"
POS_RECEIPT_JSON="${TMP_ROOT}/positive-receipt.json"
POS_CAPABILITY_JSON="${TMP_ROOT}/positive-capability-activation.json"
POS_LANE_JSON="${TMP_ROOT}/positive-lane-admission.json"
NEG_MANIFEST_PACK="${TMP_ROOT}/negative-manifest-pack"
NEG_MANIFEST_JSON="${TMP_ROOT}/negative-manifest.json"
NEG_BINDING_PACK="${TMP_ROOT}/negative-binding-pack"
NEG_BINDING_JSON="${TMP_ROOT}/negative-binding.json"
NEG_RECEIPT_JSON="${TMP_ROOT}/negative-receipt.json"
NEG_RECEIPT_PATH="${TMP_ROOT}/negative-receipt-override.json"
POS_LANE_PACK="${TMP_ROOT}/positive-lane-pack"
NEG_LANE_CONTRACT_PACK="${TMP_ROOT}/negative-lane-contract-pack"
NEG_LANE_CONTRACT_JSON="${TMP_ROOT}/negative-lane-contract.json"
NEG_LANE_RECEIPT_JSON="${TMP_ROOT}/negative-lane-receipt.json"
NEG_LANE_RECEIPT_PATH="${TMP_ROOT}/negative-lane-receipt-override.json"
HOOK_PACK="${TMP_ROOT}/hook-pack"
HOOK_CATALOG_PATH="${TMP_ROOT}/hook-catalog.local.yaml"
HOOK_RECEIPT_JSON="${TMP_ROOT}/hook-receipt.json"
HOOK_CAPABILITY_JSON="${TMP_ROOT}/hook-capability-activation.json"
NEG_HOOK_RECEIPT_JSON="${TMP_ROOT}/negative-hook-receipt.json"
NEG_HOOK_RECEIPT_PATH="${TMP_ROOT}/negative-hook-receipt-override.json"

mkdir -p "${NEG_MANIFEST_PACK}/scripts" "${NEG_BINDING_PACK}/scripts"
cp "${TASK_PATH}" "${NEG_MANIFEST_PACK}/CURRENT_TASK.json"
cp "${TASK_PATH}" "${NEG_BINDING_PACK}/CURRENT_TASK.json"
cp -R "${PACK_ROOT}/scripts/." "${NEG_MANIFEST_PACK}/scripts/"
cp -R "${PACK_ROOT}/scripts/." "${NEG_BINDING_PACK}/scripts/"

python3 "${ROOT}/scripts/validate_instance_script_manifest.py" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --json-only > "${POS_MANIFEST_JSON}"

python3 "${ROOT}/scripts/validate_identity_instance_script_orchestration.py" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --work-layer "${WORK_LAYER}" \
  --source-layer "${SOURCE_LAYER}" \
  --json-only > "${POS_ORCH_JSON}"

python3 "${ROOT}/scripts/validate_route_script_receipt_join.py" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --route "${RECEIPT_ROUTE}" \
  --script-id "${RECEIPT_SCRIPT_ID}" \
  --work-layer "${WORK_LAYER}" \
  --source-layer "${SOURCE_LAYER}" \
  --require-observed \
  --json-only > "${POS_RECEIPT_JSON}"

python3 "${ROOT}/scripts/validate_identity_capability_activation.py" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --work-layer "${WORK_LAYER}" \
  --source-layer "${SOURCE_LAYER}" \
  --activation-policy route-any-ready \
  --out "${POS_CAPABILITY_JSON}" >/dev/null

mkdir -p "${POS_LANE_PACK}/scripts" "${POS_LANE_PACK}/runtime/reports/instance-script-admission"
cp "${TASK_PATH}" "${POS_LANE_PACK}/CURRENT_TASK.json"
cp -R "${PACK_ROOT}/scripts/." "${POS_LANE_PACK}/scripts/"

python3 - "${POS_LANE_PACK}/CURRENT_TASK.json" "${POS_LANE_PACK}/runtime/reports/instance-script-admission" "${IDENTITY_ID}" "${RECEIPT_ROUTE}" "${RECEIPT_SCRIPT_ID}" <<'PY'
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

task_path = Path(sys.argv[1])
receipt_dir = Path(sys.argv[2])
identity_id = sys.argv[3]
route_name = sys.argv[4]
script_id = sys.argv[5]

task_doc = json.loads(task_path.read_text(encoding="utf-8"))
routes = (
    ((task_doc.get("capability_orchestration_contract") or {}).get("task_type_routes") or {})
    if isinstance(task_doc, dict)
    else {}
)
route_doc = routes.get(route_name)
if not isinstance(route_doc, dict):
    raise SystemExit(f"route not found for lane probe: {route_name}")

route_doc["allowed_execution_lanes"] = [
    {
        "lane_id": "serialized_single_lane",
        "lane_class": "webhook_single_flight",
        "lane_source": "governed_webhook",
        "endpoint_class": "analysis_webhook",
    }
]
route_doc["lane_admission_policy"] = {
    "mode": "declared_lane_only",
    "require_pass_status": True,
}
route_doc["lane_receipt_pattern"] = "runtime/reports/instance-script-admission/*.json"
route_doc["lane_block_on_fallback"] = True
task_path.write_text(json.dumps(task_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
receipt_path = receipt_dir / f"{route_name}-{script_id}-{timestamp}.json"
receipt_doc = {
    "schema_version": "v1",
    "receipt_family": "instance_script_admission_receipt",
    "identity_id": identity_id,
    "route_selected": route_name,
    "script_id": script_id,
    "lane_id": "serialized_single_lane",
    "lane_class": "webhook_single_flight",
    "lane_source": "governed_webhook",
    "lane_endpoint_class": "analysis_webhook",
    "lane_admission_status": "PASS_REQUIRED",
    "fallback_used": False,
    "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "message": "lane admission accepted by declared lane contract",
}
receipt_path.write_text(json.dumps(receipt_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

python3 "${ROOT}/scripts/validate_route_execution_lane_admission.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${POS_LANE_PACK}/CURRENT_TASK.json" \
  --route "${RECEIPT_ROUTE}" \
  --script-id "${RECEIPT_SCRIPT_ID}" \
  --require-observed \
  --json-only > "${POS_LANE_JSON}"

python3 - "${NEG_MANIFEST_PACK}/scripts/INSTANCE_SCRIPT_MANIFEST.json" <<'PY'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
doc = json.loads(manifest_path.read_text(encoding="utf-8"))
scripts = doc.get("scripts") or {}
if isinstance(scripts, dict):
    first_key = next(iter(scripts), "")
    if not first_key:
        raise SystemExit("manifest has no scripts to mutate")
    scripts[first_key]["entry_relpath"] = "scripts/missing-instance-script.py"
elif isinstance(scripts, list):
    if not scripts:
        raise SystemExit("manifest has no scripts to mutate")
    scripts[0]["entry_relpath"] = "scripts/missing-instance-script.py"
else:
    raise SystemExit("manifest scripts collection is not mutable")
manifest_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 "${ROOT}/scripts/validate_instance_script_manifest.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${NEG_MANIFEST_PACK}/CURRENT_TASK.json" \
  --json-only > "${NEG_MANIFEST_JSON}"; then
  echo "[FAIL] negative manifest probe unexpectedly passed"
  exit 1
fi

python3 - "${NEG_BINDING_PACK}/CURRENT_TASK.json" "${NEG_BINDING_PACK}/scripts/INSTANCE_SCRIPT_MANIFEST.json" <<'PY'
import json
import sys
from pathlib import Path

task_path = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
task_doc = json.loads(task_path.read_text(encoding="utf-8"))
routes = (
    ((task_doc.get("capability_orchestration_contract") or {}).get("task_type_routes") or {})
    if isinstance(task_doc, dict)
    else {}
)

selected_script_id = ""
for route_doc in routes.values():
    if not isinstance(route_doc, dict):
        continue
    primary_scripts = route_doc.get("primary_instance_scripts") or []
    if isinstance(primary_scripts, list) and primary_scripts:
        selected_script_id = str(primary_scripts[0]).strip()
        break

if not selected_script_id:
    raise SystemExit("no primary instance script id found for negative binding probe")

manifest_doc = json.loads(manifest_path.read_text(encoding="utf-8"))
scripts = manifest_doc.get("scripts") or {}
if isinstance(scripts, dict):
    scripts.pop(selected_script_id, None)
elif isinstance(scripts, list):
    manifest_doc["scripts"] = [
        row for row in scripts if str((row or {}).get("script_id", "")).strip() != selected_script_id
    ]
else:
    raise SystemExit("manifest scripts collection is not mutable")
manifest_path.write_text(json.dumps(manifest_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 "${ROOT}/scripts/validate_identity_instance_script_orchestration.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${NEG_BINDING_PACK}/CURRENT_TASK.json" \
  --work-layer "${WORK_LAYER}" \
  --source-layer "${SOURCE_LAYER}" \
  --json-only > "${NEG_BINDING_JSON}"; then
  echo "[FAIL] negative binding probe unexpectedly passed"
  exit 1
fi

python3 - "${RECEIPT_PATH}" "${NEG_RECEIPT_PATH}" <<'PY'
import json
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])
receipt_doc = json.loads(source_path.read_text(encoding="utf-8"))
receipt_doc["route_selected"] = "wrong_route"
target_path.write_text(json.dumps(receipt_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 "${ROOT}/scripts/validate_route_script_receipt_join.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${TASK_PATH}" \
  --route "${RECEIPT_ROUTE}" \
  --script-id "${RECEIPT_SCRIPT_ID}" \
  --receipt "${NEG_RECEIPT_PATH}" \
  --work-layer "${WORK_LAYER}" \
  --source-layer "${SOURCE_LAYER}" \
  --require-observed \
  --json-only > "${NEG_RECEIPT_JSON}"; then
  echo "[FAIL] negative receipt probe unexpectedly passed"
  exit 1
fi

cp -R "${POS_LANE_PACK}" "${NEG_LANE_CONTRACT_PACK}"

python3 - "${NEG_LANE_CONTRACT_PACK}/CURRENT_TASK.json" "${RECEIPT_ROUTE}" <<'PY'
import json
import sys
from pathlib import Path

task_path = Path(sys.argv[1])
route_name = sys.argv[2]
task_doc = json.loads(task_path.read_text(encoding="utf-8"))
routes = ((task_doc.get("capability_orchestration_contract") or {}).get("task_type_routes") or {})
route_doc = routes.get(route_name)
if not isinstance(route_doc, dict):
    raise SystemExit(f"route not found for negative lane contract probe: {route_name}")
route_doc.pop("lane_receipt_pattern", None)
task_path.write_text(json.dumps(task_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 "${ROOT}/scripts/validate_route_execution_lane_admission.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${NEG_LANE_CONTRACT_PACK}/CURRENT_TASK.json" \
  --route "${RECEIPT_ROUTE}" \
  --script-id "${RECEIPT_SCRIPT_ID}" \
  --json-only > "${NEG_LANE_CONTRACT_JSON}"; then
  echo "[FAIL] negative lane-contract probe unexpectedly passed"
  exit 1
fi

python3 - "${POS_LANE_PACK}/runtime/reports/instance-script-admission" "${NEG_LANE_RECEIPT_PATH}" <<'PY'
import json
import sys
from pathlib import Path

receipt_dir = Path(sys.argv[1])
target_path = Path(sys.argv[2])
source_path = sorted(receipt_dir.glob("*.json"))[-1]
receipt_doc = json.loads(source_path.read_text(encoding="utf-8"))
receipt_doc["lane_id"] = "undeclared_lane"
target_path.write_text(json.dumps(receipt_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 "${ROOT}/scripts/validate_route_execution_lane_admission.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${POS_LANE_PACK}/CURRENT_TASK.json" \
  --route "${RECEIPT_ROUTE}" \
  --script-id "${RECEIPT_SCRIPT_ID}" \
  --receipt "${NEG_LANE_RECEIPT_PATH}" \
  --require-observed \
  --json-only > "${NEG_LANE_RECEIPT_JSON}"; then
  echo "[FAIL] negative lane-receipt probe unexpectedly passed"
  exit 1
fi

mkdir -p "${HOOK_PACK}"
cp "${TASK_PATH}" "${HOOK_PACK}/CURRENT_TASK.json"
cp -R "${PACK_ROOT}/scripts" "${HOOK_PACK}/scripts"
cp -R "${PACK_ROOT}/runtime" "${HOOK_PACK}/runtime"

python3 - "${CATALOG_PATH}" "${HOOK_CATALOG_PATH}" "${IDENTITY_ID}" "${HOOK_PACK}" "${PACK_ROOT}" "${RECEIPT_PATH}" "${NEG_HOOK_RECEIPT_PATH}" <<'PY'
import json
import sys
from pathlib import Path

import yaml

catalog_path = Path(sys.argv[1]).resolve()
hook_catalog_path = Path(sys.argv[2]).resolve()
identity_id = sys.argv[3]
hook_pack = Path(sys.argv[4]).resolve()
pack_root = Path(sys.argv[5]).resolve()
source_receipt_path = Path(sys.argv[6]).resolve()
negative_receipt_path = Path(sys.argv[7]).resolve()

catalog_doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
rows = [row for row in (catalog_doc.get("identities") or []) if isinstance(row, dict)]
row = next((dict(item) for item in rows if str(item.get("id", "")).strip() == identity_id), None)
if row is None:
    raise SystemExit(f"identity not found for hook probe: {identity_id}")
row["pack_path"] = str(hook_pack)
hook_catalog_doc = {"identities": [row]}
hook_catalog_path.write_text(yaml.safe_dump(hook_catalog_doc, sort_keys=False), encoding="utf-8")

target_receipt_path = hook_pack / source_receipt_path.relative_to(pack_root)
receipt_doc = json.loads(target_receipt_path.read_text(encoding="utf-8"))
receipt_doc.update(
    {
        "semantic_anchor_ref": "anchor://continuity/basis-v1",
        "semantic_anchor_schema_id": "semantic_anchor_v1",
        "semantic_anchor_source": "governed_route_receipt",
        "semantic_anchor_revision": "rev-1",
        "semantic_anchor_digest": "sha256:123abc",
        "semantic_anchor_status": "PASS_REQUIRED",
        "outcome_sentinel_ref": "sentinel://continuity/advisory-v1",
        "outcome_sentinel_schema_id": "outcome_sentinel_v1",
        "outcome_sentinel_status": "advisory",
    }
)
target_receipt_path.write_text(json.dumps(receipt_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

negative_doc = dict(receipt_doc)
negative_doc.pop("semantic_anchor_digest", None)
negative_receipt_path.write_text(json.dumps(negative_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

python3 "${ROOT}/scripts/validate_route_script_receipt_join.py" \
  --catalog "${HOOK_CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --route "${RECEIPT_ROUTE}" \
  --script-id "${RECEIPT_SCRIPT_ID}" \
  --work-layer "${WORK_LAYER}" \
  --source-layer "${SOURCE_LAYER}" \
  --require-observed \
  --json-only > "${HOOK_RECEIPT_JSON}"

python3 "${ROOT}/scripts/validate_identity_capability_activation.py" \
  --catalog "${HOOK_CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --work-layer "${WORK_LAYER}" \
  --source-layer "${SOURCE_LAYER}" \
  --activation-policy route-any-ready \
  --out "${HOOK_CAPABILITY_JSON}" >/dev/null

if python3 "${ROOT}/scripts/validate_route_script_receipt_join.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${HOOK_PACK}/CURRENT_TASK.json" \
  --route "${RECEIPT_ROUTE}" \
  --script-id "${RECEIPT_SCRIPT_ID}" \
  --receipt "${NEG_HOOK_RECEIPT_PATH}" \
  --work-layer "${WORK_LAYER}" \
  --source-layer "${SOURCE_LAYER}" \
  --require-observed \
  --json-only > "${NEG_HOOK_RECEIPT_JSON}"; then
  echo "[FAIL] negative hook-receipt probe unexpectedly passed"
  exit 1
fi

python3 - "${POS_MANIFEST_JSON}" "${POS_ORCH_JSON}" "${POS_RECEIPT_JSON}" "${POS_CAPABILITY_JSON}" "${POS_LANE_JSON}" "${NEG_MANIFEST_JSON}" "${NEG_BINDING_JSON}" "${NEG_RECEIPT_JSON}" "${NEG_LANE_CONTRACT_JSON}" "${NEG_LANE_RECEIPT_JSON}" "${HOOK_RECEIPT_JSON}" "${HOOK_CAPABILITY_JSON}" "${NEG_HOOK_RECEIPT_JSON}" "${IDENTITY_ID}" "${TMP_ROOT}" "${ROOT}" "${CATALOG_PATH}" "${PACK_ROOT}" <<'PY'
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

(
    positive_manifest,
    positive_orch,
    positive_receipt,
    positive_capability,
    positive_lane,
    negative_manifest,
    negative_binding,
    negative_receipt,
    negative_lane_contract,
    negative_lane_receipt,
    hook_receipt,
    hook_capability,
    negative_hook_receipt,
) = [
    json.loads(open(path, encoding="utf-8").read()) for path in sys.argv[1:14]
]
identity_id = sys.argv[14]
tmp_root = sys.argv[15]
root = Path(sys.argv[16]).resolve()
catalog_path = Path(sys.argv[17]).resolve()
pack_root = Path(sys.argv[18]).resolve()

assert positive_manifest["instance_script_manifest_status"] == "PASS_REQUIRED", positive_manifest
assert positive_orch["instance_script_orchestration_status"] == "PASS_REQUIRED", positive_orch
assert positive_receipt["route_script_receipt_join_status"] == "PASS_REQUIRED", positive_receipt
assert positive_capability["capability_activation_status"] == "ACTIVATED", positive_capability
assert positive_capability["route_scope"] == "aggregate", positive_capability
assert positive_capability["route_scope_mode"] == "aggregate_summary", positive_capability
assert isinstance(positive_capability.get("route_ids"), list), positive_capability
assert positive_capability["route_selection_cardinality"] in {
    "zero_route",
    "single_route",
    "multi_route",
}, positive_capability
assert isinstance(positive_capability.get("declared_dependency_projection"), dict), positive_capability
assert isinstance(positive_capability.get("observed_dependency_projection"), dict), positive_capability
assert isinstance(positive_capability.get("dependency_gap_reasons"), list), positive_capability
assert isinstance(positive_capability.get("undeclared_usage_detected"), bool), positive_capability
assert isinstance(positive_capability.get("undeclared_usage_rows"), list), positive_capability
assert isinstance(positive_capability.get("missing_declared_dependency_detected"), bool), positive_capability
assert isinstance(positive_capability.get("missing_declared_dependency_rows"), list), positive_capability
assert positive_receipt["route_scope"] == "route_scoped", positive_receipt
assert positive_receipt["route_scope_mode"] == "route_receipt", positive_receipt
assert positive_receipt["route_ids"] == [positive_receipt["route"]], positive_receipt
assert positive_receipt["route_selection_cardinality"] == "single_route", positive_receipt
assert isinstance(positive_receipt.get("declared_dependency_projection"), dict), positive_receipt
assert isinstance(positive_receipt.get("observed_dependency_projection"), dict), positive_receipt
assert isinstance(positive_receipt.get("dependency_gap_reasons"), list), positive_receipt
assert isinstance(positive_receipt.get("undeclared_usage_detected"), bool), positive_receipt
assert isinstance(positive_receipt.get("undeclared_usage_rows"), list), positive_receipt
assert isinstance(positive_receipt.get("missing_declared_dependency_detected"), bool), positive_receipt
assert isinstance(positive_receipt.get("missing_declared_dependency_rows"), list), positive_receipt
assert positive_lane["route_execution_lane_admission_status"] == "PASS_REQUIRED", positive_lane
assert negative_manifest["instance_script_manifest_status"] == "FAIL_REQUIRED", negative_manifest
assert any("entry_target_missing" in reason for reason in negative_manifest.get("stale_reasons", [])), negative_manifest
assert negative_binding["instance_script_orchestration_status"] == "FAIL_REQUIRED", negative_binding
assert any("missing_script_id:" in reason for reason in negative_binding.get("stale_reasons", [])), negative_binding
assert negative_receipt["route_script_receipt_join_status"] == "FAIL_REQUIRED", negative_receipt
assert any("receipt_route_selected_mismatch" in reason for reason in negative_receipt.get("stale_reasons", [])), negative_receipt
assert negative_lane_contract["route_execution_lane_admission_status"] == "FAIL_REQUIRED", negative_lane_contract
assert any("missing_field:lane_receipt_pattern" in reason for reason in negative_lane_contract.get("stale_reasons", [])), negative_lane_contract
assert negative_lane_receipt["route_execution_lane_admission_status"] == "FAIL_REQUIRED", negative_lane_receipt
assert any("lane_receipt_lane_id_undeclared:" in reason for reason in negative_lane_receipt.get("stale_reasons", [])), negative_lane_receipt
assert hook_receipt["route_script_receipt_join_status"] == "PASS_REQUIRED", hook_receipt
assert hook_receipt["semantic_anchor_ref"] == "anchor://continuity/basis-v1", hook_receipt
assert hook_receipt["semantic_anchor_status"] == "PASS_REQUIRED", hook_receipt
assert hook_receipt["outcome_sentinel_ref"] == "sentinel://continuity/advisory-v1", hook_receipt
assert hook_receipt["outcome_sentinel_status"] == "advisory", hook_receipt
assert hook_capability["capability_activation_status"] == "ACTIVATED", hook_capability
assert hook_capability["semantic_anchor_ref"] == "anchor://continuity/basis-v1", hook_capability
assert hook_capability["outcome_sentinel_ref"] == "sentinel://continuity/advisory-v1", hook_capability
assert negative_hook_receipt["route_script_receipt_join_status"] == "FAIL_REQUIRED", negative_hook_receipt
assert any("semantic_anchor_missing:semantic_anchor_digest" in reason for reason in negative_hook_receipt.get("stale_reasons", [])), negative_hook_receipt

catalog_doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
catalog_rows = [row for row in (catalog_doc.get("identities") or []) if isinstance(row, dict)]
source_row = next((dict(row) for row in catalog_rows if str(row.get("id", "")).strip() == identity_id), None)
assert source_row is not None, {"identity_id": identity_id, "catalog_path": str(catalog_path)}

cross_pack_root = Path(tmp_root) / "cross-pack-adoption-probe"
good_catalog_path = cross_pack_root / "good-catalog.local.yaml"
dirty_catalog_path = cross_pack_root / "dirty-catalog.local.yaml"
cross_pack_root.mkdir(parents=True, exist_ok=True)


def _replace_identity_strings(value, source_identity: str, target_identity: str):
    if isinstance(value, str):
        return target_identity if value == source_identity else value
    if isinstance(value, list):
        return [_replace_identity_strings(item, source_identity, target_identity) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_identity_strings(item, source_identity, target_identity)
            for key, item in value.items()
        }
    return value


def _rewrite_pack_identity(target_pack_root: Path, source_identity: str, target_identity: str) -> None:
    for json_path in target_pack_root.rglob("*.json"):
        doc = json.loads(json_path.read_text(encoding="utf-8"))
        rewritten = _replace_identity_strings(doc, source_identity, target_identity)
        json_path.write_text(json.dumps(rewritten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_json(cmd: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, check=False)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            {
                "command": cmd,
                "rc": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        ) from exc
    assert isinstance(payload, dict), payload
    return proc.returncode, payload


def _write_catalog(path: Path, rows: list[dict]) -> None:
    path.write_text(yaml.safe_dump({"identities": rows}, sort_keys=False), encoding="utf-8")


def _scrub_topology_dirs(catalog_for_pack: Path, target_identity: str, target_pack_root: Path) -> dict:
    max_passes = 8
    for _ in range(max_passes):
        rc, payload = _run_json(
            [
                "python3",
                str((root / "scripts" / "validate_identity_instance_pack_topology.py").resolve()),
                "--catalog",
                str(catalog_for_pack),
                "--identity-id",
                target_identity,
                "--json-only",
            ]
        )
        if rc == 0 and payload.get("instance_pack_topology_status") == "PASS_REQUIRED":
            return payload
        removable = []
        for row in (payload.get("unknown_dir_rows") or []) + (payload.get("forbidden_dir_rows") or []):
            token = str(row).strip()
            if ":" not in token:
                continue
            _, relpath = token.split(":", 1)
            candidate = target_pack_root / relpath
            if candidate.exists():
                removable.append(candidate)
        if not removable:
            raise AssertionError(payload)
        for candidate in removable:
            if candidate.is_dir():
                shutil.rmtree(candidate)
            else:
                candidate.unlink()
    raise AssertionError({"topology_scrub_status": "FAIL_REQUIRED", "identity_id": target_identity})


def _make_pack_copy(
    *,
    source_pack_root: Path,
    source_identity: str,
    target_pack_root: Path,
    target_identity: str,
    target_catalog_path: Path,
    target_rows: list[dict],
    inject_forbidden_cache_dir: bool = False,
) -> dict:
    if target_pack_root.exists():
        shutil.rmtree(target_pack_root)
    shutil.copytree(source_pack_root, target_pack_root)
    _rewrite_pack_identity(target_pack_root, source_identity, target_identity)
    row = dict(source_row)
    row["id"] = target_identity
    row["pack_path"] = str(target_pack_root)
    target_rows.append(row)
    _write_catalog(target_catalog_path, target_rows)
    topology_payload = _scrub_topology_dirs(target_catalog_path, target_identity, target_pack_root)
    if inject_forbidden_cache_dir:
        cache_dir = target_pack_root / "scripts" / "__pycache__"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "probe.pyc").write_bytes(b"v1615-probe")
        rc, topology_payload = _run_json(
            [
                "python3",
                str((root / "scripts" / "validate_identity_instance_pack_topology.py").resolve()),
                "--catalog",
                str(target_catalog_path),
                "--identity-id",
                target_identity,
                "--json-only",
            ]
        )
        assert rc != 0, topology_payload
        assert topology_payload.get("instance_pack_topology_status") == "FAIL_REQUIRED", topology_payload
    return topology_payload


good_rows: list[dict] = []
good_pack_a = cross_pack_root / "good-pack-a"
good_pack_b = cross_pack_root / "good-pack-b"
_make_pack_copy(
    source_pack_root=pack_root,
    source_identity=identity_id,
    target_pack_root=good_pack_a,
    target_identity="v1615-cross-pack-good-a",
    target_catalog_path=good_catalog_path,
    target_rows=good_rows,
)
_make_pack_copy(
    source_pack_root=pack_root,
    source_identity=identity_id,
    target_pack_root=good_pack_b,
    target_identity="v1615-cross-pack-good-b",
    target_catalog_path=good_catalog_path,
    target_rows=good_rows,
)

dirty_rows: list[dict] = []
dirty_pack_good = cross_pack_root / "dirty-pack-good"
dirty_pack_bad = cross_pack_root / "dirty-pack-bad"
_make_pack_copy(
    source_pack_root=pack_root,
    source_identity=identity_id,
    target_pack_root=dirty_pack_good,
    target_identity="v1615-cross-pack-dirty-good",
    target_catalog_path=dirty_catalog_path,
    target_rows=dirty_rows,
)
_make_pack_copy(
    source_pack_root=pack_root,
    source_identity=identity_id,
    target_pack_root=dirty_pack_bad,
    target_identity="v1615-cross-pack-dirty-bad",
    target_catalog_path=dirty_catalog_path,
    target_rows=dirty_rows,
    inject_forbidden_cache_dir=True,
)

good_default_rc, good_default = _run_json(
    [
        "python3",
        str((root / "scripts" / "validate_identity_instance_script_cross_pack_adoption.py").resolve()),
        "--catalog",
        str(good_catalog_path),
        "--json-only",
    ]
)
assert good_default_rc == 0, good_default
assert good_default["instance_script_cross_pack_adoption_status"] == "PASS_REQUIRED", good_default
assert good_default["proof_boundary_mode"] == "orchestration_family_only", good_default
assert good_default["adoption_ready_identity_count"] == 2, good_default
assert good_default["topology_clean_adoption_ready_count"] == 2, good_default
assert good_default["topology_interlock_violation_count"] == 0, good_default

good_topology_rc, good_topology = _run_json(
    [
        "python3",
        str((root / "scripts" / "validate_identity_instance_script_cross_pack_adoption.py").resolve()),
        "--catalog",
        str(good_catalog_path),
        "--proof-boundary",
        "topology_clean",
        "--json-only",
    ]
)
assert good_topology_rc == 0, good_topology
assert good_topology["instance_script_cross_pack_adoption_status"] == "PASS_REQUIRED", good_topology
assert good_topology["proof_boundary_mode"] == "topology_clean", good_topology
assert good_topology["topology_clean_adoption_ready_count"] == 2, good_topology

dirty_default_rc, dirty_default = _run_json(
    [
        "python3",
        str((root / "scripts" / "validate_identity_instance_script_cross_pack_adoption.py").resolve()),
        "--catalog",
        str(dirty_catalog_path),
        "--json-only",
    ]
)
assert dirty_default_rc == 0, dirty_default
assert dirty_default["instance_script_cross_pack_adoption_status"] == "PASS_REQUIRED", dirty_default
assert dirty_default["proof_boundary_mode"] == "orchestration_family_only", dirty_default
assert dirty_default["adoption_ready_identity_count"] == 2, dirty_default
assert dirty_default["topology_clean_adoption_ready_count"] == 1, dirty_default
assert dirty_default["topology_interlock_violation_count"] == 1, dirty_default
assert any("v1615-cross-pack-dirty-bad:" in row for row in dirty_default.get("topology_interlock_violation_rows", [])), dirty_default

dirty_topology_rc, dirty_topology = _run_json(
    [
        "python3",
        str((root / "scripts" / "validate_identity_instance_script_cross_pack_adoption.py").resolve()),
        "--catalog",
        str(dirty_catalog_path),
        "--proof-boundary",
        "topology_clean",
        "--json-only",
    ]
)
assert dirty_topology_rc != 0, dirty_topology
assert dirty_topology["instance_script_cross_pack_adoption_status"] == "FAIL_REQUIRED", dirty_topology
assert dirty_topology["error_code"] == "IP-ORCH-ADOPT-003", dirty_topology
assert dirty_topology["topology_clean_adoption_ready_count"] == 1, dirty_topology
assert any("topology_not_pass" in row.get("stale_reasons", []) for row in dirty_topology.get("identity_rows", [])), dirty_topology

print(
    json.dumps(
        {
            "identity_instance_script_orchestration_probe_status": "PASS_REQUIRED",
            "identity_id": identity_id,
            "positive_manifest_status": positive_manifest["instance_script_manifest_status"],
            "positive_orchestration_status": positive_orch["instance_script_orchestration_status"],
            "positive_receipt_join_status": positive_receipt["route_script_receipt_join_status"],
            "positive_capability_activation_status": positive_capability["capability_activation_status"],
            "positive_aggregate_scope": positive_capability["route_scope"],
            "positive_execution_lane_status": positive_lane["route_execution_lane_admission_status"],
            "negative_manifest_failure": "entry_target_missing",
            "negative_binding_failure": "missing_script_id",
            "negative_receipt_failure": "receipt_route_selected_mismatch",
            "negative_lane_contract_failure": "missing_field:lane_receipt_pattern",
            "negative_lane_receipt_failure": "lane_receipt_lane_id_undeclared",
            "positive_optional_hook_projection_status": "PASS_REQUIRED",
            "negative_optional_hook_failure": "semantic_anchor_missing:semantic_anchor_digest",
            "positive_cross_pack_adoption_status": good_default["instance_script_cross_pack_adoption_status"],
            "positive_cross_pack_topology_clean_status": good_topology["instance_script_cross_pack_adoption_status"],
            "negative_cross_pack_topology_boundary_failure": dirty_topology["error_code"],
            "negative_cross_pack_topology_interlock_count": dirty_default["topology_interlock_violation_count"],
            "tmp_root": tmp_root,
        },
        ensure_ascii=False,
    )
)
PY
