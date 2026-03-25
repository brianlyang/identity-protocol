#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

POSITIVE_JSON="${TMP_ROOT}/positive.json"
NEGATIVE_JSON="${TMP_ROOT}/negative.json"
SHADOW_ROOT="${TMP_ROOT}/shadow-repo"

printf '[RUN] positive control-plane budget sync validation\n'
python3 "${REPO_ROOT}/scripts/validate_control_plane_budget_sync.py" \
  --repo-root "${REPO_ROOT}" \
  --json-only > "${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("control_plane_budget_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_control_plane_budget_sync_not_green")
PY

mkdir -p "${SHADOW_ROOT}"

python3 - <<'PY' "${REPO_ROOT}" "${SHADOW_ROOT}"
from pathlib import Path
import sys
import yaml

repo_root = Path(sys.argv[1]).resolve()
shadow_root = Path(sys.argv[2]).resolve()

for child in repo_root.iterdir():
    if child.name == "identity":
        continue
    target = shadow_root / child.name
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

current_name = "control-plane-budget.current.yaml"
active_name = "control-plane-budget.v1.6.yaml"

for child in mappings_src.iterdir():
    if child.name in {current_name, active_name}:
        continue
    target = mappings_dst / child.name
    if target.exists():
        continue
    target.symlink_to(child, target_is_directory=child.is_dir())

current_src = mappings_src / current_name
current_dst = mappings_dst / current_name
current_dst.write_text(current_src.read_text(encoding="utf-8"), encoding="utf-8")

active_src = mappings_src / active_name
active_dst = mappings_dst / active_name
doc = yaml.safe_load(active_src.read_text(encoding="utf-8")) or {}
if not isinstance(doc, dict):
    raise SystemExit("probe_setup_failed:budget_doc_not_mapping")

guard = doc.get("convergence_guard") or {}
ceilings = guard.get("ceilings") or {}
current_error_code_ceiling = int(ceilings.get("error_codes", 0))
ceilings["error_codes"] = max(0, current_error_code_ceiling - 1)
guard["ceilings"] = ceilings
doc["convergence_guard"] = guard
active_dst.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
PY

printf '[RUN] negative control-plane budget sync validation\n'
python3 "${SHADOW_ROOT}/scripts/validate_control_plane_budget_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${NEGATIVE_JSON}" || true

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
negative = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

if str(positive.get("control_plane_budget_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_control_plane_budget_sync_not_green")
if str(negative.get("control_plane_budget_sync_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("negative_control_plane_budget_sync_should_fail")
if int(negative.get("mismatch_count", 0)) <= 0:
    raise SystemExit("negative_control_plane_budget_sync_missing_mismatch_payload")
PY

echo "[PASS] control-plane budget sync probes passed"
