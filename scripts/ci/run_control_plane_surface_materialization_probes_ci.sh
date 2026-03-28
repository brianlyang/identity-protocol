#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

SHADOW_ROOT="${TMP_ROOT}/shadow-repo"
NEGATIVE_JSON="${TMP_ROOT}/negative.json"
POSITIVE_JSON="${TMP_ROOT}/positive.json"
NEGATIVE_SYNC_JSON="${TMP_ROOT}/negative-budget-sync.json"
POSITIVE_BUDGET_SYNC_JSON="${TMP_ROOT}/positive-budget-sync.json"
POSITIVE_STATUS_SYNC_JSON="${TMP_ROOT}/positive-status-sync.json"
DIRECT_RENDER_JSON="${TMP_ROOT}/direct-render.json"
DIRECT_RENDER_SYNC_JSON="${TMP_ROOT}/direct-render-sync.json"
INCOMPLETE_STATUS_JSON="${TMP_ROOT}/incomplete-status.json"
STATUS_SCOPE_DRIFT_JSON="${TMP_ROOT}/status-scope-drift.json"
STATUS_SUMMARY_DRIFT_JSON="${TMP_ROOT}/status-summary-drift.json"

mkdir -p "${SHADOW_ROOT}"

python3 - <<'PY' "${REPO_ROOT}" "${SHADOW_ROOT}"
from pathlib import Path
import sys
import yaml

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

budget_doc = yaml.safe_load((mappings_dst / "control-plane-budget.v1.6.yaml").read_text(encoding="utf-8")) or {}
guard = budget_doc.get("convergence_guard") or {}
ceilings = guard.get("ceilings") or {}
current_error_codes = int(ceilings.get("error_codes", 0) or 0)
ceilings["error_codes"] = max(0, current_error_codes - 1)
guard["ceilings"] = ceilings
budget_doc["convergence_guard"] = guard
(mappings_dst / "control-plane-budget.v1.6.yaml").write_text(
    yaml.safe_dump(budget_doc, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

printf '[RUN] verify stale shadow control-plane budget before materialization\n'
python3 "${SHADOW_ROOT}/scripts/validate_control_plane_budget_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${NEGATIVE_SYNC_JSON}" || true

python3 - <<'PY' "${NEGATIVE_SYNC_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("control_plane_budget_sync_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("expected_stale_shadow_budget_sync_fail")
if int(payload.get("mismatch_count", 0)) <= 0:
    raise SystemExit("expected_shadow_budget_sync_mismatch_count")
PY

printf '[RUN] negative dry-run control-plane materialization\n'
python3 "${SHADOW_ROOT}/scripts/materialize_control_plane_surfaces.py" \
  --repo-root "${SHADOW_ROOT}" \
  --check-name control_plane_budget \
  --check-name control_plane_budget_sync \
  --allow-partial-status-write \
  --json-only > "${NEGATIVE_JSON}" || true

python3 - <<'PY' "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("materialize_control_plane_surfaces_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("dry_run_materialization_should_fail_on_stale_shadow_repo")
if str(payload.get("budget_sync_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("dry_run_materialization_should_preserve_budget_sync_failure")
if str(payload.get("status_sync_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("dry_run_materialization_should_preserve_status_sync_failure")
PY

printf '[RUN] positive canonical control-plane materialization\n'
python3 "${SHADOW_ROOT}/scripts/materialize_control_plane_surfaces.py" \
  --repo-root "${SHADOW_ROOT}" \
  --check-name control_plane_budget \
  --check-name control_plane_budget_sync \
  --allow-partial-status-write \
  --write \
  --json-only > "${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("materialize_control_plane_surfaces_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("materialization_should_pass_after_write")
for key in (
    "budget_validation_status",
    "budget_sync_status",
    "status_sync_status",
):
    if str(payload.get(key, "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit(f"materialization_result_not_green:{key}")
if str(payload.get("control_plane_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("materialization_should_render_green_control_plane_status")
if not bool(payload.get("write_applied", False)):
    raise SystemExit("materialization_should_report_write_applied")
PY

python3 - <<'PY' "${SHADOW_ROOT}/identity/protocol/mappings/control-plane-status.v1.6.json"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
checks = payload.get("checks")
if not isinstance(checks, list):
    raise SystemExit("status_artifact_checks_missing_after_partial_materialization")
names = [str(row.get("name", "")).strip() for row in checks if isinstance(row, dict)]
if len(names) <= 2:
    raise SystemExit("partial_materialization_should_not_truncate_status_artifact")
if "control_plane_budget" not in names or "control_plane_budget_sync" not in names:
    raise SystemExit("selected_checks_missing_after_partial_materialization")
if "protocol_root_corpus_governance" not in names:
    raise SystemExit("non_selected_check_missing_after_partial_materialization")
if payload.get("selected_check_names") not in ([], None):
    raise SystemExit("persisted_full_status_artifact_should_not_remain_subset_scoped")
PY

python3 "${SHADOW_ROOT}/scripts/validate_control_plane_budget_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${POSITIVE_BUDGET_SYNC_JSON}"
python3 "${SHADOW_ROOT}/scripts/validate_control_plane_status_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --check-name control_plane_budget \
  --check-name control_plane_budget_sync \
  --json-only > "${POSITIVE_STATUS_SYNC_JSON}"

python3 - <<'PY' "${POSITIVE_BUDGET_SYNC_JSON}" "${POSITIVE_STATUS_SYNC_JSON}"
import json
import sys
from pathlib import Path

budget = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
status = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

if str(budget.get("control_plane_budget_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_materialized_budget_sync_not_green")
if str(status.get("control_plane_status_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_materialized_status_sync_not_green")
if str(status.get("live_control_plane_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_materialized_live_control_plane_not_green")
if str(status.get("file_control_plane_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("positive_materialized_file_control_plane_not_green")
PY

python3 "${SHADOW_ROOT}/scripts/render_control_plane_status.py" \
  --repo-root "${SHADOW_ROOT}" \
  --check-name control_plane_budget \
  --write \
  --json-only > "${DIRECT_RENDER_JSON}"

python3 - <<'PY' "${SHADOW_ROOT}/identity/protocol/mappings/control-plane-status.v1.6.json"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
checks = payload.get("checks")
if not isinstance(checks, list):
    raise SystemExit("status_artifact_checks_missing_after_direct_partial_render")
names = [str(row.get("name", "")).strip() for row in checks if isinstance(row, dict)]
if len(names) <= 2:
    raise SystemExit("direct_partial_render_should_not_truncate_status_artifact")
if "control_plane_budget" not in names:
    raise SystemExit("direct_partial_render_selected_check_missing")
if "protocol_root_corpus_governance" not in names:
    raise SystemExit("direct_partial_render_non_selected_check_missing")
if payload.get("selected_check_names") not in ([], None):
    raise SystemExit("direct_partial_render_should_persist_full_artifact_scope")
PY

python3 "${SHADOW_ROOT}/scripts/validate_control_plane_status_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${DIRECT_RENDER_SYNC_JSON}"

python3 - <<'PY' "${DIRECT_RENDER_SYNC_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("control_plane_status_sync_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit("direct_partial_render_full_status_sync_not_green")
PY

python3 - <<'PY' "${SHADOW_ROOT}/identity/protocol/mappings/control-plane-status.v1.6.json"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
payload["selected_check_names"] = ["control_plane_budget"]
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 "${SHADOW_ROOT}/scripts/validate_control_plane_status_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${STATUS_SCOPE_DRIFT_JSON}"; then
  echo "[FAIL] control-plane status sync unexpectedly passed selected-check scope drift"
  exit 1
fi

python3 - <<'PY' "${STATUS_SCOPE_DRIFT_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("control_plane_status_sync_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("selected_check_scope_drift_should_fail_status_sync")
if not any(
    str(row.get("field", "")).strip() == "selected_check_names"
    and str(row.get("reason", "")).strip() == "selected_check_scope_drift"
    for row in (payload.get("mismatches") or [])
):
    raise SystemExit("selected_check_scope_drift_mismatch_missing")
PY

python3 "${SHADOW_ROOT}/scripts/render_control_plane_status.py" \
  --repo-root "${SHADOW_ROOT}" \
  --write \
  --json-only > /dev/null

python3 - <<'PY' "${SHADOW_ROOT}/identity/protocol/mappings/control-plane-status.v1.6.json"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
summary = payload.get("summary") or {}
summary["pass_count"] = int(summary.get("pass_count", 0) or 0) + 1
payload["summary"] = summary
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 "${SHADOW_ROOT}/scripts/validate_control_plane_status_sync.py" \
  --repo-root "${SHADOW_ROOT}" \
  --json-only > "${STATUS_SUMMARY_DRIFT_JSON}"; then
  echo "[FAIL] control-plane status sync unexpectedly passed summary drift"
  exit 1
fi

python3 - <<'PY' "${STATUS_SUMMARY_DRIFT_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("control_plane_status_sync_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("summary_drift_should_fail_status_sync")
if not any(
    str(row.get("field", "")).strip() == "summary"
    and str(row.get("reason", "")).strip() == "summary_drift"
    for row in (payload.get("mismatches") or [])
):
    raise SystemExit("summary_drift_mismatch_missing")
PY

python3 - <<'PY' "${SHADOW_ROOT}/identity/protocol/mappings/control-plane-status.v1.6.json"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
checks = payload.get("checks")
if not isinstance(checks, list):
    raise SystemExit("status_artifact_checks_missing_before_incomplete_fixture")
payload["checks"] = [
    row
    for row in checks
    if not (
        isinstance(row, dict)
        and str(row.get("name", "")).strip() == "protocol_root_corpus_governance"
    )
]
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 "${SHADOW_ROOT}/scripts/materialize_control_plane_surfaces.py" \
  --repo-root "${SHADOW_ROOT}" \
  --check-name control_plane_budget \
  --allow-partial-status-write \
  --write \
  --json-only > "${INCOMPLETE_STATUS_JSON}"; then
  echo "[FAIL] materializer unexpectedly passed incomplete-current-file partial status write"
  exit 1
fi

python3 - <<'PY' "${INCOMPLETE_STATUS_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if str(payload.get("materialize_control_plane_surfaces_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("incomplete_current_file_partial_write_should_fail")
reasons = payload.get("stale_reasons") or []
if not any(
    "status_write_failed:partial_status_write_current_file_incomplete:" in str(reason)
    for reason in reasons
):
    raise SystemExit("incomplete_current_file_partial_write_failure_reason_missing")
PY

echo "[PASS] control-plane surface materialization probes passed"
