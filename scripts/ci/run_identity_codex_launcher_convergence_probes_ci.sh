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

export REPO_ROOT CATALOG_PATH IDENTITY_ID WORKSPACE_ROOT
python3 - <<'PY'
import json
import os
import shutil
from pathlib import Path

import yaml

catalog_path = Path(os.environ["CATALOG_PATH"]).resolve()
identity_id = os.environ["IDENTITY_ID"].strip()
workspace_root = Path(os.environ["WORKSPACE_ROOT"]).resolve()

doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
rows = [row for row in (doc.get("identities") or []) if isinstance(row, dict)]
row = next((row for row in rows if str(row.get("id", "")).strip() == identity_id), None)
if row is None:
    raise SystemExit(f"missing identity row: {identity_id}")
pack_src = Path(str(row.get("canonical_pack_path") or row.get("pack_path") or "")).expanduser().resolve()
if not pack_src.exists():
    raise SystemExit(f"missing pack source: {pack_src}")
pack_dst = (workspace_root / ".identity" / identity_id).resolve()
pack_dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(pack_src, pack_dst)
for rel in (Path("scripts/launchers/identity-codex-launcher.manifest.json"), Path("scripts/launchers/README.md")):
    target = pack_dst / rel
    if target.exists():
        target.unlink()
minimal_row = {
    "id": identity_id,
    "status": str(row.get("status", "active") or "active"),
    "profile": str(row.get("profile", "runtime") or "runtime"),
    "runtime_mode": str(row.get("runtime_mode", "local_only") or "local_only"),
    "canonical_scope": str(row.get("canonical_scope", "USER") or "USER"),
    "pack_path": str(pack_dst),
    "canonical_pack_path": str(pack_dst),
}
catalog_doc = {"identities": [minimal_row]}
catalog_dst = (workspace_root / ".identity" / "catalog.local.yaml").resolve()
catalog_dst.write_text(yaml.safe_dump(catalog_doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(json.dumps({"catalog": str(catalog_dst), "pack": str(pack_dst)}))
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
assert Path(payload["precheck_evidence_ref"]).exists(), payload
assert Path(payload["evidence_ref"]).exists(), payload
print("launcher_convergence_dry_run_status=FAIL_REQUIRED")
PY

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
row = payload["repair_results"][0]
assert row["backfill_status"] == "PASS_REQUIRED", row
assert row["install_status"] == "PASS_REQUIRED", row
assert row["validator_status"] == "PASS_REQUIRED", row
print("launcher_convergence_apply_status=PASS_REQUIRED")
PY

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

echo "[PASS] identity codex launcher convergence probes passed"
