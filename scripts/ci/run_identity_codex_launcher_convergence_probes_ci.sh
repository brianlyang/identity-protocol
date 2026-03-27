#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${REPO_ROOT}/scripts/shell_strict_entry_common.sh"

IDENTITY_ID="${IDENTITY_ID:-base-repo-closure-orchestrator}"
CATALOG_PATH="$(protocol_shell_entry_resolve_project_catalog "${CATALOG_PATH:-}")"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-codex-launcher-convergence-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

WORKSPACE_ROOT="${TMP_ROOT}/workspace"
EVIDENCE_ROOT="${TMP_ROOT}/evidence"
CODEX_HOME="${TMP_ROOT}/codex-home"
mkdir -p "${WORKSPACE_ROOT}" "${EVIDENCE_ROOT}" "${CODEX_HOME}"

PROBE_CONTEXT_JSON="${TMP_ROOT}/probe-context.json"
python3 "${REPO_ROOT}/scripts/materialize_launcher_convergence_probe_context.py" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --target-workspace-root "${WORKSPACE_ROOT}" \
  --json-only > "${PROBE_CONTEXT_JSON}"

python3 - "${PROBE_CONTEXT_JSON}" "${WORKSPACE_ROOT}" "${IDENTITY_ID}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_workspace = str(Path(sys.argv[2]).resolve())
expected_identity_id = str(sys.argv[3]).strip()
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["identity_id"] == expected_identity_id, payload
assert payload["target_workspace_root"] == expected_workspace, payload
assert payload["target_catalog_path"] == str((Path(expected_workspace) / ".identity" / "catalog.local.yaml").resolve()), payload
assert payload["target_pack_path"] == str((Path(expected_workspace) / ".identity" / expected_identity_id).resolve()), payload
assert payload["materialized_catalog_identity_count"] == 1, payload
materialized = payload["materialized_runtime_row"]
assert materialized["canonical_scope"] == "UNKNOWN", payload
assert materialized["canonical_pack_path"] == "", payload
print("launcher_convergence_probe_context_status=PASS_REQUIRED")
PY

TMP_CATALOG="${WORKSPACE_ROOT}/.identity/catalog.local.yaml"

DRY_JSON="${TMP_ROOT}/dry-run.json"
if python3 "${REPO_ROOT}/scripts/run_identity_codex_launcher_workspace_convergence.py" \
  --catalog "${TMP_CATALOG}" \
  --mode dry-run \
  --codex-home "${CODEX_HOME}" \
  --artifact-root "${EVIDENCE_ROOT}" \
  --run-token probe \
  --json-only > "${DRY_JSON}"; then
  echo "[FAIL] convergence dry-run unexpectedly returned success for known debtful workspace"
  exit 1
fi

python3 - "${DRY_JSON}" <<'PY'
import json
import sys

from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "FAIL_REQUIRED", payload
assert payload["repair_status"] == "dry_run_preview", payload
assert payload["planned_repair_count"] == 1, payload
assert payload["precheck_status"] == "FAIL_REQUIRED", payload
assert payload["mutation_applied"] is False, payload
assert payload["receipt_family"] == "identity_codex_launcher_workspace_convergence_receipt_v1", payload
PY

DRY_BUNDLE_JSON="${TMP_ROOT}/dry-run-bundle.json"
python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher_evidence_bundle.py" \
  --payload-json "${DRY_JSON}" \
  --require-ref-field precheck_evidence_ref \
  --require-ref-field evidence_ref \
  --require-ref-field manifest_ref \
  --require-summary-ref \
  --expected-kind launcher_convergence_receipt \
  --expected-kind launcher_convergence_precheck \
  --json-only > "${DRY_BUNDLE_JSON}"

echo "launcher_convergence_dry_run_status=FAIL_REQUIRED"

APPLY_JSON="${TMP_ROOT}/apply.json"
python3 "${REPO_ROOT}/scripts/run_identity_codex_launcher_workspace_convergence.py" \
  --catalog "${TMP_CATALOG}" \
  --mode apply \
  --codex-home "${CODEX_HOME}" \
  --artifact-root "${EVIDENCE_ROOT}" \
  --run-token probe \
  --json-only > "${APPLY_JSON}"

python3 - "${APPLY_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["repair_status"] in {"apply_repaired", "already_converged"}, payload
assert payload["mutation_applied"] is True, payload
assert payload["repaired_identity_count"] == 1, payload
assert payload["remaining_violation_count"] == 0, payload
assert payload["postcheck_status"] == "PASS_REQUIRED", payload
assert Path(payload["precheck_evidence_ref"]).exists(), payload
assert Path(payload["postcheck_evidence_ref"]).exists(), payload
assert Path(payload["evidence_ref"]).exists(), payload
assert Path(payload["manifest_ref"]).exists(), payload
row = payload["repair_results"][0]
assert row["metadata_repair_status"] == "PASS_REQUIRED", row
assert row["metadata_hygiene_status"] == "PASS_REQUIRED", row
assert row["backfill_status"] == "PASS_REQUIRED", row
assert row["install_status"] == "PASS_REQUIRED", row
assert row["validator_status"] == "PASS_REQUIRED", row
PY

APPLY_BUNDLE_JSON="${TMP_ROOT}/apply-bundle.json"
python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher_evidence_bundle.py" \
  --payload-json "${APPLY_JSON}" \
  --require-ref-field precheck_evidence_ref \
  --require-ref-field postcheck_evidence_ref \
  --require-ref-field evidence_ref \
  --require-ref-field manifest_ref \
  --require-summary-ref \
  --expected-kind launcher_convergence_receipt \
  --expected-kind launcher_convergence_precheck \
  --expected-kind launcher_convergence_postcheck \
  --json-only > "${APPLY_BUNDLE_JSON}"

echo "launcher_convergence_apply_status=PASS_REQUIRED"

AMBIENT_INSTALL_JSON="${TMP_ROOT}/ambient-install.json"
env \
  CODEX_HOME="${CODEX_HOME}" \
  IDENTITY_HOME="${WORKSPACE_ROOT}/.identity" \
  IDENTITY_CATALOG="${TMP_CATALOG}" \
  python3 "${REPO_ROOT}/scripts/install_identity_codex_launcher.py" \
    --catalog "${TMP_CATALOG}" \
    --identity-id "${IDENTITY_ID}" \
    --bin-dir "${CODEX_HOME}/bin" \
    --json-only > "${AMBIENT_INSTALL_JSON}"

python3 - "${AMBIENT_INSTALL_JSON}" "${WORKSPACE_ROOT}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
workspace_root = Path(sys.argv[2]).resolve()
expected_identity_home = (workspace_root / ".identity").resolve()
expected_runtime_env = (expected_identity_home / "config" / "runtime-paths.env").resolve()
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["launcher_config_identity_home"] == str(expected_identity_home), payload
assert payload["launcher_config_identity_home_source"] == "ambient_identity_home_env", payload
assert payload["runtime_paths_env"] == str(expected_runtime_env), payload
print("launcher_convergence_ambient_config_home_install_status=PASS_REQUIRED")
PY

AMBIENT_VALIDATE_JSON="${TMP_ROOT}/ambient-validate.json"
env \
  CODEX_HOME="${CODEX_HOME}" \
  IDENTITY_HOME="${WORKSPACE_ROOT}/.identity" \
  IDENTITY_CATALOG="${TMP_CATALOG}" \
  python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher.py" \
    --catalog "${TMP_CATALOG}" \
    --identity-id "${IDENTITY_ID}" \
    --bin-dir "${CODEX_HOME}/bin" \
    --require-installed \
    --json-only > "${AMBIENT_VALIDATE_JSON}"

python3 - "${AMBIENT_VALIDATE_JSON}" "${WORKSPACE_ROOT}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
workspace_root = Path(sys.argv[2]).resolve()
expected_identity_home = (workspace_root / ".identity").resolve()
assert payload["identity_codex_launcher_status"] == "PASS_REQUIRED", payload
assert payload["launcher_config_identity_home"] == str(expected_identity_home), payload
assert payload["launcher_config_identity_home_source"] == "ambient_identity_home_env", payload
assert payload["runtime_paths_status"] == "PASS_REQUIRED", payload
print("launcher_convergence_ambient_config_home_validate_status=PASS_REQUIRED")
PY

METADATA_HYGIENE_JSON="${TMP_ROOT}/metadata-hygiene.json"
python3 "${REPO_ROOT}/scripts/validate_runtime_catalog_metadata_hygiene.py" \
  --catalog "${TMP_CATALOG}" \
  --identity-id "${IDENTITY_ID}" \
  --require-active \
  --json-only > "${METADATA_HYGIENE_JSON}"

python3 - "${METADATA_HYGIENE_JSON}" "${IDENTITY_ID}" <<'PY'
import json
import sys

payload = json.loads(open(sys.argv[1], "r", encoding="utf-8").read())
identity_id = str(sys.argv[2]).strip()
assert payload["runtime_catalog_metadata_hygiene_status"] == "PASS_REQUIRED", payload
assert payload["checked_identity_count"] == 1, payload
assert payload["violation_count"] == 0, payload
rows = payload.get("checked_rows") or []
assert len(rows) == 1, payload
row = rows[0]
assert row["identity_id"] == identity_id, row
assert row["status"] == "PASS_REQUIRED", row
assert row["canonical_scope"] == "USER", row
print("launcher_convergence_metadata_hygiene_apply_status=PASS_REQUIRED")
PY

FRESH_TRUTH_SYNC_JSON="${TMP_ROOT}/fresh-truth-sync.json"
python3 "${REPO_ROOT}/scripts/refresh_identity_codex_launcher_evidence_truth_sync.py" \
  --artifact-root "${EVIDENCE_ROOT}" \
  --run-token probe \
  --workspace-root "${WORKSPACE_ROOT}" \
  --json-only > "${FRESH_TRUTH_SYNC_JSON}"

python3 - "${FRESH_TRUTH_SYNC_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["truth_sync_status"] == "PASS_REQUIRED", payload
assert payload["receipts_with_changes"] == 0, payload
assert payload["manifest_write_count"] == 0, payload
assert payload["repair_status"] == "already_truth_synced", payload
print("launcher_convergence_fresh_truth_sync_status=PASS_REQUIRED")
PY

python3 - "${APPLY_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
receipt_path = Path(payload["evidence_ref"]).resolve()
manifest_path = Path(payload["manifest_ref"]).resolve()
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
receipt["evidence_ref"] = ""
receipt["manifest_ref"] = ""
receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if manifest_path.exists():
    manifest_path.unlink()
PY

REFRESH_DRY_JSON="${TMP_ROOT}/refresh-dry-run.json"
if python3 "${REPO_ROOT}/scripts/refresh_identity_codex_launcher_evidence_truth_sync.py" \
  --artifact-root "${EVIDENCE_ROOT}" \
  --run-token probe \
  --workspace-root "${WORKSPACE_ROOT}" \
  --json-only > "${REFRESH_DRY_JSON}"; then
  echo "[FAIL] truth-sync dry-run unexpectedly passed on corrupted bundle"
  exit 1
fi

python3 - "${REFRESH_DRY_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "FAIL_REQUIRED", payload
assert payload["truth_sync_status"] == "FAIL_REQUIRED", payload
assert payload["receipts_with_changes"] == 1, payload
assert payload["receipt_ref_change_count"] == 1, payload
assert payload["manifest_write_count"] == 1, payload
assert payload["repair_status"] == "dry_run_changes_detected", payload
print("launcher_convergence_truth_sync_dry_run_status=FAIL_REQUIRED")
PY

REFRESH_APPLY_JSON="${TMP_ROOT}/refresh-apply.json"
python3 "${REPO_ROOT}/scripts/refresh_identity_codex_launcher_evidence_truth_sync.py" \
  --artifact-root "${EVIDENCE_ROOT}" \
  --run-token probe \
  --workspace-root "${WORKSPACE_ROOT}" \
  --apply \
  --json-only > "${REFRESH_APPLY_JSON}"

APPLY_RECEIPT_PATH="$(python3 - "${REFRESH_APPLY_JSON}" "${APPLY_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
apply_payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["truth_sync_status"] == "PASS_REQUIRED", payload
assert payload["repair_status"] == "apply_truth_synced", payload
receipt_path = Path(apply_payload["evidence_ref"]).resolve()
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
assert receipt["evidence_ref"] == str(receipt_path), receipt
print(receipt_path)
PY
)"

REFRESH_APPLY_BUNDLE_JSON="${TMP_ROOT}/refresh-apply-bundle.json"
python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher_evidence_bundle.py" \
  --receipt-path "${APPLY_RECEIPT_PATH}" \
  --require-summary-ref \
  --require-self-evidence-ref-match \
  --expected-kind launcher_convergence_receipt \
  --expected-kind launcher_convergence_precheck \
  --expected-kind launcher_convergence_postcheck \
  --json-only > "${REFRESH_APPLY_BUNDLE_JSON}"

echo "launcher_convergence_truth_sync_apply_status=PASS_REQUIRED"

if python3 "${REPO_ROOT}/scripts/run_identity_codex_launcher_workspace_convergence.py" \
  --catalog "${REPO_ROOT}/identity/catalog/identities.yaml" \
  --mode dry-run \
  --codex-home "${CODEX_HOME}" \
  --artifact-root "${EVIDENCE_ROOT}" \
  --run-token invalid \
  --json-only >"${TMP_ROOT}/invalid.json" 2>&1; then
  echo "[FAIL] convergence repo-catalog rejection unexpectedly passed"
  exit 1
fi
if ! grep -q 'IP-ILAUNCH-CONV-001' "${TMP_ROOT}/invalid.json"; then
  echo "[FAIL] convergence repo-catalog rejection missing expected error code"
  cat "${TMP_ROOT}/invalid.json"
  exit 1
fi

python3 - "${PROBE_CONTEXT_JSON}" "${APPLY_JSON}" "${METADATA_HYGIENE_JSON}" "${REFRESH_APPLY_JSON}" <<'PY'
import json
import sys
from pathlib import Path

probe_context = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
apply_payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
metadata_hygiene = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
truth_sync_apply = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))

print(
    json.dumps(
        {
            "identity_codex_launcher_convergence_probe_status": "PASS_REQUIRED",
            "probe_context_status": probe_context.get("status", ""),
            "metadata_hygiene_apply_status": metadata_hygiene.get(
                "runtime_catalog_metadata_hygiene_status", ""
            ),
            "truth_sync_apply_status": truth_sync_apply.get("truth_sync_status", ""),
            "repo_catalog_rejection_status": "PASS_REQUIRED",
            "repaired_identity_count": apply_payload.get("repaired_identity_count", 0),
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] identity codex launcher convergence probes passed"
