#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${REPO_ROOT}/scripts/shell_strict_entry_common.sh"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/weak-live-pointer-locality.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}"

python3 - <<'PY' "${TMP_ROOT}"
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str((Path.cwd() / "scripts").resolve()))
from identity_weak_live_linkage_common import weak_live_linkage_contract_skeleton

base = Path(sys.argv[1]).resolve()
identity_id = "weak-live-pointer-locality-probe"
pack_root = (base / ".identity" / identity_id).resolve()
foreign_pack = (base / "foreign/.identity" / identity_id).resolve()

for pack in (pack_root, foreign_pack):
    (pack / "runtime/state").mkdir(parents=True, exist_ok=True)
    (pack / "runtime/reports").mkdir(parents=True, exist_ok=True)

foreign_report = (foreign_pack / "runtime/reports" / f"identity-upgrade-exec-{identity_id}-runA.json").resolve()
foreign_report.write_text(
    json.dumps(
        {
            "run_id": "runA",
            "session_id": "run:runA",
            "resolved_pack_path": str(foreign_pack),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

(pack_root / "runtime/state/active_execution_report.json").write_text(
    json.dumps(
        {
            "run_id": "runA",
            "report_path": str(foreign_report),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

task = {
    "identity_weak_live_linkage_contract_v1": weak_live_linkage_contract_skeleton(),
    "experience_feedback_contract": {
        "required": True,
        "sample_report_path_pattern": str(foreign_report),
        "report_freshness_status": "PASS_REQUIRED",
        "run_id_binding_status": "PASS_REQUIRED",
        "strict_live_proof_status": "PASS_REQUIRED",
    },
}
(pack_root / "CURRENT_TASK.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(pack_root / "IDENTITY_PROMPT.md").write_text("# weak-live pointer locality probe\n", encoding="utf-8")

catalog = {
    "identities": [
        {
            "id": identity_id,
            "pack_path": str(pack_root),
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
        }
    ]
}
(base / ".identity").mkdir(parents=True, exist_ok=True)
(base / ".identity/catalog.local.yaml").write_text(yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False), encoding="utf-8")
PY

JSON_OUT="${TMP_ROOT}/weak-live-pointer-locality.json"
python3 "${REPO_ROOT}/scripts/validate_identity_weak_live_linkage.py" \
  --catalog "${TMP_ROOT}/.identity/catalog.local.yaml" \
  --identity-id "weak-live-pointer-locality-probe" \
  --json-only > "${JSON_OUT}"

python3 - <<'PY' "${JSON_OUT}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload["identity_weak_live_linkage_status"] != "PASS_REQUIRED":
    raise SystemExit(f"weak-live validator should still evaluate contract lane: {payload}")
if payload.get("current_run_pointer") not in {"", None}:
    raise SystemExit(f"foreign active pointer must not be projected as current-run pointer: {payload}")
if payload.get("current_run_pointer_resolution_mode") != "external_pointer_report_rejected":
    raise SystemExit(f"foreign active pointer must fail-close via shared strict-live primitive: {payload}")
rows = payload.get("family_rows") or []
sample = next((row for row in rows if row.get("family") == "sample_report_only"), None)
if not isinstance(sample, dict):
    raise SystemExit(f"sample family row missing: {payload}")
if sample.get("run_binding_status") != "FAIL_REQUIRED":
    raise SystemExit(f"foreign pointer must not elevate sample family to live-bound status: {sample}")
reasons = sample.get("reasons") or []
if "sample_or_history_live_run_binding_unproven" not in reasons:
    raise SystemExit(f"sample family should explain missing live binding after foreign-pointer rejection: {sample}")
PY

echo "[PASS] weak-live linkage pointer locality probes passed"
