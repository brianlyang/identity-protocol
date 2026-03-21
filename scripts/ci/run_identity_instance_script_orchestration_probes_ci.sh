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
    selected = {
        "identity_id": identity_id,
        "pack_root": str(pack_root),
        "task_path": str(task_path),
        "manifest_path": str(manifest_path),
    }
    break

if selected is None:
    raise SystemExit("no orchestration-ready identity found for probes")

for key, value in selected.items():
    print(f"{key.upper()}={shlex.quote(str(value))}")
PY
)"

POS_MANIFEST_JSON="${TMP_ROOT}/positive-manifest.json"
POS_ORCH_JSON="${TMP_ROOT}/positive-orchestration.json"
NEG_MANIFEST_PACK="${TMP_ROOT}/negative-manifest-pack"
NEG_MANIFEST_JSON="${TMP_ROOT}/negative-manifest.json"
NEG_BINDING_PACK="${TMP_ROOT}/negative-binding-pack"
NEG_BINDING_JSON="${TMP_ROOT}/negative-binding.json"

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

python3 - "${POS_MANIFEST_JSON}" "${POS_ORCH_JSON}" "${NEG_MANIFEST_JSON}" "${NEG_BINDING_JSON}" "${IDENTITY_ID}" "${TMP_ROOT}" <<'PY'
import json
import sys

positive_manifest, positive_orch, negative_manifest, negative_binding = [
    json.loads(open(path, encoding="utf-8").read()) for path in sys.argv[1:5]
]
identity_id = sys.argv[5]
tmp_root = sys.argv[6]

assert positive_manifest["instance_script_manifest_status"] == "PASS_REQUIRED", positive_manifest
assert positive_orch["instance_script_orchestration_status"] == "PASS_REQUIRED", positive_orch
assert negative_manifest["instance_script_manifest_status"] == "FAIL_REQUIRED", negative_manifest
assert any("entry_target_missing" in reason for reason in negative_manifest.get("stale_reasons", [])), negative_manifest
assert negative_binding["instance_script_orchestration_status"] == "FAIL_REQUIRED", negative_binding
assert any("missing_script_id:" in reason for reason in negative_binding.get("stale_reasons", [])), negative_binding

print(
    json.dumps(
        {
            "identity_instance_script_orchestration_probe_status": "PASS_REQUIRED",
            "identity_id": identity_id,
            "positive_manifest_status": positive_manifest["instance_script_manifest_status"],
            "positive_orchestration_status": positive_orch["instance_script_orchestration_status"],
            "negative_manifest_failure": "entry_target_missing",
            "negative_binding_failure": "missing_script_id",
            "tmp_root": tmp_root,
        },
        ensure_ascii=False,
    )
)
PY
