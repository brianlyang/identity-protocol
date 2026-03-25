#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

POSITIVE_JSON="${TMP_ROOT}/positive.json"
NEGATIVE_JSON="${TMP_ROOT}/negative.json"
SHADOW_ROOT="${TMP_ROOT}/shadow-repo"

printf '[RUN] positive release-closure control-plane status projection\n'
python3 "${REPO_ROOT}/scripts/materialize_control_plane_surfaces.py" \
  --repo-root "${REPO_ROOT}" \
  --write \
  --json-only > "${POSITIVE_JSON}" || true

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

mkdir -p "${SHADOW_ROOT}"

python3 - <<'PY' "${REPO_ROOT}" "${SHADOW_ROOT}"
from pathlib import Path
import sys

repo_root = Path(sys.argv[1]).resolve()
shadow_root = Path(sys.argv[2]).resolve()

for child in repo_root.iterdir():
    if child.name == "scripts":
        continue
    target = shadow_root / child.name
    if target.exists():
        continue
    target.symlink_to(child, target_is_directory=child.is_dir())

scripts_dir = shadow_root / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)
for child in (repo_root / "scripts").iterdir():
    if child.name == "render_control_plane_status.py":
        continue
    target = scripts_dir / child.name
    if target.exists():
        continue
    target.symlink_to(child, target_is_directory=child.is_dir())
target = scripts_dir / "render_control_plane_status.py"
source_lines = (repo_root / "scripts" / "render_control_plane_status.py").read_text(encoding="utf-8").splitlines()
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
target.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
PY

printf '[RUN] negative release-closure control-plane status projection\n'
python3 "${SHADOW_ROOT}/scripts/render_control_plane_status.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${NEGATIVE_JSON}" || true

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

positive_checks = {
    str(row.get("name", "")).strip(): row
    for row in (positive.get("status_render") or {}).get("checks") or []
    if isinstance(row, dict) and str(row.get("name", "")).strip()
}
negative_checks = {
    str(row.get("name", "")).strip(): row
    for row in negative.get("checks") or []
    if isinstance(row, dict) and str(row.get("name", "")).strip()
}

if "v16x_release_closure_summary" not in positive_checks:
    raise SystemExit("positive control-plane projection missing v16x_release_closure_summary")
if "v16x_release_closure_summary" in negative_checks:
    raise SystemExit("negative control-plane projection must lose v16x_release_closure_summary after drift fixture")
if "v16x_release_closure_boundary" not in negative_checks:
    raise SystemExit("negative control-plane projection should keep neighboring release-closure checks")
PY

echo "[PASS] release-closure control-plane status probes passed"
