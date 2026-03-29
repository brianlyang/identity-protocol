#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=./probe_runtime_tmp_common.sh
source "${ROOT}/scripts/ci/probe_runtime_tmp_common.sh"
probe_runtime_tmp_bootstrap "${ROOT}" "identity-artifact-family-routing-probes" "run"

WORKSPACE_ROOT="${TMP_ROOT}/workspace"
IDENTITY_HOME="${WORKSPACE_ROOT}/.identity"
CATALOG_PATH="${IDENTITY_HOME}/catalog.local.yaml"
IDENTITY_ID="artifact-family-routing-probe"
PACK_ROOT="${IDENTITY_HOME}/${IDENTITY_ID}"
TASK_PATH="${PACK_ROOT}/CURRENT_TASK.json"
REPO_CATALOG="${ROOT}/identity/catalog/identities.yaml"

mkdir -p "${PACK_ROOT}/runtime" "${PACK_ROOT}/scripts"

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

from identity_artifact_family_routing_common import artifact_family_routing_contract_skeleton
from identity_dialogue_retention_common import materialize_identity_dialogue_retention_assets

task = {
    "identity_id": identity_id,
    "objective": {"title": "artifact family routing probe", "status": "active"},
    "state_machine": {"current_state": "probe_active"},
    "required_validators": [],
    "gates": {
        "reject_memory_gate": "required",
    },
    "artifact_family_routing_contract_v1": artifact_family_routing_contract_skeleton(),
}

(pack_root / "TASK_HISTORY.md").write_text("# Task history\n", encoding="utf-8")
(pack_root / "RULEBOOK.jsonl").write_text("", encoding="utf-8")
(pack_root / "scripts" / "emit_current_thread_final_reply.py").write_text(
    "#!/usr/bin/env python3\n"
    "# probe emitter install marker\n"
    "HOOK='run_identity_delivery_runtime_hooks.py'\n"
    "delivery_hook_result = {}\n",
    encoding="utf-8",
)

materialize_identity_dialogue_retention_assets(
    task=task,
    identity_id=identity_id,
    pack_dir=pack_root,
    apply=True,
)
(pack_root / "CURRENT_TASK.json").write_text(
    json.dumps(task, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

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
catalog_path.write_text(
    yaml.safe_dump(catalog_doc, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

PASS_JSON="${TMP_ROOT}/artifact-family-routing-pass.json"
python3 "${ROOT}/scripts/validate_identity_artifact_family_routing.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${REPO_CATALOG}" \
  --operation ci \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["artifact_family_routing_status"] == "PASS_REQUIRED", payload
assert payload["runtime_dialogue_retention_family_status"] == "PASS_REQUIRED", payload
PY

python3 - <<'PY' "${TASK_PATH}"
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
doc = json.loads(path.read_text(encoding="utf-8"))
doc.pop("artifact_family_routing_contract_v1", None)
path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

MISSING_JSON="${TMP_ROOT}/artifact-family-routing-missing-contract.json"
if python3 "${ROOT}/scripts/validate_identity_artifact_family_routing.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${REPO_CATALOG}" \
  --operation ci \
  --json-only >"${MISSING_JSON}"; then
  echo "[FAIL] artifact-family routing validator unexpectedly passed without contract"
  exit 1
fi

python3 - <<'PY' "${MISSING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["error_code"] == "IP-AFR-001", payload
assert "artifact_family_routing_contract_missing" in payload.get("stale_reasons", []), payload
PY

BACKFILL_JSON="${TMP_ROOT}/artifact-family-routing-backfill.json"
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
assert payload["artifact_family_routing_contract_auto_wire_status"] == "PASS_REQUIRED", payload
PY

REPAIRED_JSON="${TMP_ROOT}/artifact-family-routing-repaired.json"
python3 "${ROOT}/scripts/validate_identity_artifact_family_routing.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${REPO_CATALOG}" \
  --operation ci \
  --json-only >"${REPAIRED_JSON}"

python3 - <<'PY' "${REPAIRED_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["artifact_family_routing_status"] == "PASS_REQUIRED", payload
assert payload["runtime_experience_feedback_family_status"] == "PASS_REQUIRED", payload
assert payload["runtime_continuity_reentry_family_status"] == "PASS_REQUIRED", payload
PY

python3 - <<'PY' "${TASK_PATH}" "${PACK_ROOT}"
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
pack_root = pathlib.Path(sys.argv[2]).resolve()
doc = json.loads(path.read_text(encoding="utf-8"))
feedback = doc.setdefault("experience_feedback_contract", {})
feedback["required"] = False
feedback["positive_rulebook_path"] = str((pack_root / "RULEBOOK.jsonl").resolve())
path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

COLLISION_JSON="${TMP_ROOT}/artifact-family-routing-collision.json"
if python3 "${ROOT}/scripts/validate_identity_artifact_family_routing.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${REPO_CATALOG}" \
  --operation ci \
  --json-only >"${COLLISION_JSON}"; then
  echo "[FAIL] artifact-family routing validator unexpectedly passed after rulebook collision"
  exit 1
fi

python3 - <<'PY' "${COLLISION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["error_code"] in {"IP-AFR-002", "IP-AFR-003"}, payload
assert "experience_positive_rulebook_collides_with_pack_rulebook" in payload.get("stale_reasons", []), payload
PY

echo "[PASS] identity artifact-family routing probes passed"
