#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

POSITIVE_JSON="${TMP_ROOT}/positive.json"
HYGIENE_BASELINE_JSON="${TMP_ROOT}/hygiene-baseline.json"
HYGIENE_UNTRACKED_JSON="${TMP_ROOT}/hygiene-untracked.json"
HYGIENE_PARTIAL_JSON="${TMP_ROOT}/hygiene-partial.json"
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
for child in scripts_src.iterdir():
    target = scripts_dst / child.name
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

for child in mappings_src.iterdir():
    target = mappings_dst / child.name
    if target.exists():
        continue
    if child.name in {"control-plane-budget.current.yaml", "control-plane-budget.v1.6.yaml"}:
        target.write_text(child.read_text(encoding="utf-8"), encoding="utf-8")
        continue
    target.symlink_to(child, target_is_directory=child.is_dir())
PY

printf '[RUN] metric hygiene baseline validation\n'
python3 "${SHADOW_ROOT}/scripts/validate_control_plane_budget.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${HYGIENE_BASELINE_JSON}"

python3 - <<'PY' "${SHADOW_ROOT}"
from pathlib import Path
import sys

shadow_root = Path(sys.argv[1]).resolve()
(shadow_root / "scripts" / "validate_control_plane_budget_metric_scope_probe.py").write_text(
    "#!/usr/bin/env python3\nERR_SCOPE_PROBE = \"IP-SCOPE-PROBE-001\"\n",
    encoding="utf-8",
)
PY

printf '[RUN] metric hygiene untracked-validator validation\n'
python3 "${SHADOW_ROOT}/scripts/validate_control_plane_budget.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${HYGIENE_UNTRACKED_JSON}"

python3 - <<'PY' "${REPO_ROOT}" "${SHADOW_ROOT}"
from pathlib import Path
import sys

repo_root = Path(sys.argv[1]).resolve()
shadow_root = Path(sys.argv[2]).resolve()
target = shadow_root / "scripts" / "release_readiness_check.py"
if target.is_symlink() or target.exists():
    target.unlink()
text = (repo_root / "scripts" / "release_readiness_check.py").read_text(encoding="utf-8")
if not text:
    raise SystemExit("partial_probe_source_missing")
target.write_text(text + "\n# partial-prefix hygiene probe IP-BUDGET-HYGIENE-\n", encoding="utf-8")
PY

printf '[RUN] metric hygiene partial-prefix validation\n'
python3 "${SHADOW_ROOT}/scripts/validate_control_plane_budget.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${HYGIENE_PARTIAL_JSON}"

python3 - <<'PY' "${HYGIENE_BASELINE_JSON}" "${HYGIENE_UNTRACKED_JSON}" "${HYGIENE_PARTIAL_JSON}"
import json
import sys
from pathlib import Path

baseline = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
untracked = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
partial = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))

base_observed = baseline.get("observed") or {}
untracked_observed = untracked.get("observed") or {}
partial_observed = partial.get("observed") or {}

if str(untracked.get("control_plane_budget_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("untracked_validator_probe_should_remain_green")
if int(base_observed.get("validator_scripts", -1)) != int(untracked_observed.get("validator_scripts", -2)):
    raise SystemExit("untracked_validator_should_not_increase_governed_validator_count")
untracked_paths = set(str(item) for item in (untracked_observed.get("untracked_validator_scripts") or []))
if not any(path.endswith("validate_control_plane_budget_metric_scope_probe.py") for path in untracked_paths):
    raise SystemExit("untracked_validator_probe_not_projected")

if str(partial.get("control_plane_budget_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("partial_prefix_probe_should_remain_green")
if int(base_observed.get("error_codes", -1)) != int(partial_observed.get("error_codes", -2)):
    raise SystemExit("partial_prefix_should_not_increase_error_code_count")
if int(base_observed.get("error_code_families", -1)) != int(partial_observed.get("error_code_families", -2)):
    raise SystemExit("partial_prefix_should_not_increase_error_code_family_count")
ignored_tokens = set(str(item) for item in (partial_observed.get("ignored_partial_error_code_tokens") or []))
if "IP-BUDGET-HYGIENE-" not in ignored_tokens:
    raise SystemExit("partial_prefix_probe_not_projected")
PY

python3 - <<'PY' "${REPO_ROOT}" "${SHADOW_ROOT}"
from pathlib import Path
import sys
import yaml

repo_root = Path(sys.argv[1]).resolve()
shadow_root = Path(sys.argv[2]).resolve()
active_dst = shadow_root / "identity" / "protocol" / "mappings" / "control-plane-budget.v1.6.yaml"
doc = yaml.safe_load(active_dst.read_text(encoding="utf-8")) or {}
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
