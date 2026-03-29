#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

POSITIVE_JSON="${TMP_ROOT}/positive.json"
POSITIVE_SYNC_JSON="${TMP_ROOT}/positive-sync.json"
NEGATIVE_SYNC_JSON="${TMP_ROOT}/negative-sync.json"
SHADOW_ROOT="${TMP_ROOT}/shadow-repo"
RELEASE_CHECK_NAMES=(
  "release_doc_surface_governance"
  "v16x_release_closure_boundary"
  "v16x_release_closure_summary"
)

mkdir -p "${SHADOW_ROOT}"
python3 "${REPO_ROOT}/scripts/control_plane_probe_shadow_common.py" \
  --repo-root "${REPO_ROOT}" \
  --shadow-root "${SHADOW_ROOT}" \
  --copy-script materialize_control_plane_surfaces.py \
  --copy-script render_control_plane_budget.py \
  --copy-script render_control_plane_status.py \
  --copy-script release_closure_surface_registry_common.py \
  --copy-script validate_control_plane_budget.py \
  --copy-script validate_control_plane_budget_sync.py \
  --copy-script validate_control_plane_status_sync.py \
  --copy-script repo_root_resolution_common.py \
  --copy-mapping control-plane-budget.current.yaml \
  --copy-mapping control-plane-budget.v1.6.yaml \
  --copy-mapping control-plane-status.current.yaml \
  --copy-mapping control-plane-status.v1.6.json \
  --json-only > /dev/null

printf '[RUN] positive release-closure control-plane status projection (shadow repo)\n'
python3 "${SHADOW_ROOT}/scripts/materialize_control_plane_surfaces.py" \
  --repo-root "${SHADOW_ROOT}" \
  --check-name "${RELEASE_CHECK_NAMES[0]}" \
  --check-name "${RELEASE_CHECK_NAMES[1]}" \
  --check-name "${RELEASE_CHECK_NAMES[2]}" \
  --allow-partial-status-write \
  --write \
  --json-only > "${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if str(payload.get("materialize_control_plane_surfaces_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_control_plane_materialization_not_green")
if str(payload.get("budget_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_control_plane_materialization_budget_sync_not_green")
if str(payload.get("status_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_control_plane_materialization_status_sync_not_green")
status_render = payload.get("status_render") or {}
checks = {}
for row in status_render.get("checks") or []:
    if isinstance(row, dict):
        name = str(row.get("name", "")).strip()
        if name:
            checks[name] = row

for name in (
    "release_doc_surface_governance",
    "v16x_release_closure_boundary",
    "v16x_release_closure_summary",
):
    if name not in checks:
        raise SystemExit(f"missing_control_plane_release_closure_check:{name}")
    if str(checks[name].get("status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit(f"control_plane_release_closure_check_not_green:{name}")
PY

python3 "${SHADOW_ROOT}/scripts/validate_control_plane_status_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --check-name "${RELEASE_CHECK_NAMES[0]}" \
  --check-name "${RELEASE_CHECK_NAMES[1]}" \
  --check-name "${RELEASE_CHECK_NAMES[2]}" \
  --json-only > "${POSITIVE_SYNC_JSON}"

python3 - <<'PY' "${POSITIVE_SYNC_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("control_plane_status_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_release_closure_status_sync_not_green")
PY

python3 - <<'PY' "${SHADOW_ROOT}/identity/protocol/mappings/control-plane-status.v1.6.json"
from pathlib import Path
import json
import sys

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
checks = payload.get("checks")
if not isinstance(checks, list):
    raise SystemExit("probe_setup_failed:status_checks_missing")
filtered_checks = [
    row
    for row in checks
    if not (
        isinstance(row, dict)
        and str(row.get("name", "")).strip() == "v16x_release_closure_summary"
    )
]
if len(filtered_checks) == len(checks):
    raise SystemExit("probe_setup_failed:missing_v16x_release_closure_summary_status_row")
payload["checks"] = filtered_checks
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

printf '[RUN] negative release-closure control-plane status sync drift (shadow repo)\n'
if python3 "${SHADOW_ROOT}/scripts/validate_control_plane_status_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --check-name "${RELEASE_CHECK_NAMES[0]}" \
  --check-name "${RELEASE_CHECK_NAMES[1]}" \
  --check-name "${RELEASE_CHECK_NAMES[2]}" \
  --json-only > "${NEGATIVE_SYNC_JSON}"; then
  echo "[FAIL] release-closure control-plane status sync unexpectedly passed missing-check drift"
  exit 1
fi

python3 - <<'PY' "${NEGATIVE_SYNC_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if str(payload.get("control_plane_status_sync_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("negative_release_closure_status_sync_should_fail")
mismatches = payload.get("mismatches") or []
if not any(
    str(row.get("field", "")).strip() == "checks.name_set"
    and str(row.get("reason", "")).strip() == "check_set_drift"
    for row in mismatches
):
    raise SystemExit("negative_release_closure_status_sync_missing_check_set_drift")
PY

echo "[PASS] release-closure control-plane status probes passed"
