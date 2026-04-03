#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

POSITIVE_JSON="${TMP_ROOT}/positive.json"
BASELINE_RENDER_JSON="${TMP_ROOT}/baseline-render.json"
HYGIENE_BASELINE_JSON="${TMP_ROOT}/hygiene-baseline.json"
HYGIENE_UNTRACKED_JSON="${TMP_ROOT}/hygiene-untracked.json"
HYGIENE_PARTIAL_JSON="${TMP_ROOT}/hygiene-partial.json"
TOPOLOGY_NEGATIVE_JSON="${TMP_ROOT}/negative-topology.json"
NEGATIVE_JSON="${TMP_ROOT}/negative.json"
SHADOW_ROOT="${TMP_ROOT}/shadow-repo"

mkdir -p "${SHADOW_ROOT}"
python3 "${REPO_ROOT}/scripts/control_plane_probe_shadow_common.py" \
  --repo-root "${REPO_ROOT}" \
  --shadow-root "${SHADOW_ROOT}" \
  --copy-script render_control_plane_budget.py \
  --copy-script validate_control_plane_budget.py \
  --copy-script validate_control_plane_budget_sync.py \
  --copy-script repo_root_resolution_common.py \
  --copy-mapping control-plane-budget.current.yaml \
  --copy-mapping control-plane-budget.v1.6.yaml \
  --json-only > /dev/null

printf '[RUN] shadow baseline render control-plane budget\n'
python3 "${SHADOW_ROOT}/scripts/render_control_plane_budget.py" \
  --repo-root "${SHADOW_ROOT}" \
  --write \
  --json-only > "${BASELINE_RENDER_JSON}"

printf '[RUN] positive control-plane budget sync validation (shadow repo)\n'
python3 "${SHADOW_ROOT}/scripts/validate_control_plane_budget_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${POSITIVE_JSON}"

python3 - <<'PY' "${BASELINE_RENDER_JSON}" "${POSITIVE_JSON}"
import json
import sys
from pathlib import Path

render_payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
positive_payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
if not bool(render_payload.get("write_applied")):
    raise SystemExit("shadow_budget_render_write_not_applied")
if str(positive_payload.get("control_plane_budget_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_control_plane_budget_sync_not_green")
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

if str(baseline.get("control_plane_budget_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("baseline_budget_probe_should_be_green")

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

printf '[RUN] topology negative control-plane budget validation\n'
python3 "${SHADOW_ROOT}/scripts/render_control_plane_budget.py" \
  --repo-root "${SHADOW_ROOT}" \
  --write \
  --json-only > /dev/null

python3 - <<'PY' "${SHADOW_ROOT}"
from pathlib import Path
import sys
import yaml

shadow_root = Path(sys.argv[1]).resolve()
active_dst = shadow_root / "identity" / "protocol" / "mappings" / "control-plane-budget.v1.6.yaml"
doc = yaml.safe_load(active_dst.read_text(encoding="utf-8")) or {}
if not isinstance(doc, dict):
    raise SystemExit("topology_probe_setup_failed:budget_doc_not_mapping")
budgets = doc.get("budgets") or {}
direct = budgets.get("direct_validate_calls") or {}
if "scripts/release_readiness_check.py" not in direct:
    raise SystemExit("topology_probe_setup_failed:strict_surface_missing")
del direct["scripts/release_readiness_check.py"]
budgets["direct_validate_calls"] = direct
doc["budgets"] = budgets
active_dst.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
PY

python3 "${SHADOW_ROOT}/scripts/validate_control_plane_budget.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${TOPOLOGY_NEGATIVE_JSON}" || true

python3 - <<'PY' "${TOPOLOGY_NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("control_plane_budget_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("topology_negative_budget_probe_should_fail")
reasons = {str(item.get("reason", "")) for item in (payload.get("fail_violations") or []) if isinstance(item, dict)}
if "strict_surface_budget_topology_drift" not in reasons:
    raise SystemExit("topology_negative_budget_probe_missing_reason")
PY

python3 "${SHADOW_ROOT}/scripts/render_control_plane_budget.py" \
  --repo-root "${SHADOW_ROOT}" \
  --write \
  --json-only > /dev/null

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
