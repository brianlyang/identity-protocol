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

mkdir -p "${SHADOW_ROOT}"

python3 - <<'PY' "${REPO_ROOT}" "${SHADOW_ROOT}"
from pathlib import Path
import sys

repo_root = Path(sys.argv[1]).resolve()
shadow_root = Path(sys.argv[2]).resolve()

for child in repo_root.iterdir():
    if child.name in {"identity", "scripts"}:
        continue
    target = shadow_root / child.name
    if target.exists():
        continue
    target.symlink_to(child, target_is_directory=child.is_dir())

scripts_src = repo_root / "scripts"
scripts_dst = shadow_root / "scripts"
scripts_dst.mkdir(parents=True, exist_ok=True)
copied_scripts = {
    "materialize_control_plane_surfaces.py",
    "render_control_plane_budget.py",
    "render_control_plane_status.py",
    "validate_control_plane_budget.py",
    "validate_control_plane_budget_sync.py",
    "validate_control_plane_status_sync.py",
    "repo_root_resolution_common.py",
}
for child in scripts_src.iterdir():
    target = scripts_dst / child.name
    if child.name in copied_scripts:
        target.write_text(child.read_text(encoding="utf-8"), encoding="utf-8")
        continue
    if target.exists():
        continue
    target.symlink_to(child, target_is_directory=child.is_dir())

identity_src = repo_root / "identity"
identity_dst = shadow_root / "identity"
identity_dst.mkdir(parents=True, exist_ok=True)
for child in identity_src.iterdir():
    if child.name == "protocol":
        continue
    target = identity_dst / child.name
    if target.exists():
        continue
    target.symlink_to(child, target_is_directory=child.is_dir())

protocol_src = identity_src / "protocol"
protocol_dst = identity_dst / "protocol"
protocol_dst.mkdir(parents=True, exist_ok=True)
for child in protocol_src.iterdir():
    if child.name == "mappings":
        continue
    target = protocol_dst / child.name
    if target.exists():
        continue
    target.symlink_to(child, target_is_directory=child.is_dir())

mappings_src = protocol_src / "mappings"
mappings_dst = protocol_dst / "mappings"
mappings_dst.mkdir(parents=True, exist_ok=True)
copied_files = {
    "control-plane-budget.current.yaml",
    "control-plane-budget.v1.6.yaml",
    "control-plane-status.current.yaml",
    "control-plane-status.v1.6.json",
}
for child in mappings_src.iterdir():
    target = mappings_dst / child.name
    if child.name in copied_files:
        target.write_text(child.read_text(encoding="utf-8"), encoding="utf-8")
        continue
    if target.exists():
        continue
    target.symlink_to(child, target_is_directory=child.is_dir())
PY

printf '[RUN] positive release-closure control-plane status projection (shadow repo)\n'
python3 "${SHADOW_ROOT}/scripts/materialize_control_plane_surfaces.py" \
  --repo-root "${SHADOW_ROOT}" \
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
  --json-only > "${POSITIVE_SYNC_JSON}"

python3 - <<'PY' "${POSITIVE_SYNC_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("control_plane_status_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_release_closure_status_sync_not_green")
PY

python3 - <<'PY' "${SHADOW_ROOT}/scripts/render_control_plane_status.py"
from pathlib import Path
import sys

path = Path(sys.argv[1])
source_lines = path.read_text(encoding="utf-8").splitlines()
updated_lines: list[str] = []
candidate_block: list[str] | None = None
remove_candidate = False
paren_depth = 0
removed = 0
for line in source_lines:
    stripped = line.strip()
    if candidate_block is None and stripped == "CheckSpec(":
        paren_depth = 1
        candidate_block = [line]
        remove_candidate = False
        continue
    if candidate_block is not None:
        candidate_block.append(line)
        paren_depth += line.count("(") - line.count(")")
        if 'name="v16x_release_closure_summary"' in stripped:
            remove_candidate = True
        if paren_depth <= 0:
            if remove_candidate:
                removed += 1
            else:
                updated_lines.extend(candidate_block)
            candidate_block = None
            remove_candidate = False
            paren_depth = 0
        continue
    updated_lines.append(line)
if removed != 1:
    raise SystemExit("probe_setup_failed:missing_v16x_release_closure_summary_check_block")
path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
PY

printf '[RUN] negative release-closure control-plane status sync drift (shadow repo)\n'
if python3 "${SHADOW_ROOT}/scripts/validate_control_plane_status_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
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
