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
import hashlib
import sys
from pathlib import Path

def resolve_manifest_member(manifest_path: Path, value: str) -> Path:
    raw = Path(str(value).strip())
    if raw.is_absolute():
        return raw.resolve()
    return (manifest_path.parent / raw).resolve()

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "FAIL_REQUIRED", payload
assert payload["repair_status"] == "dry_run_preview", payload
assert payload["planned_repair_count"] == 1, payload
assert payload["precheck_status"] == "FAIL_REQUIRED", payload
assert payload["mutation_applied"] is False, payload
assert payload["receipt_family"] == "identity_codex_launcher_workspace_convergence_receipt_v1", payload
assert Path(payload["precheck_evidence_ref"]).exists(), payload
assert Path(payload["evidence_ref"]).exists(), payload
assert Path(payload["manifest_ref"]).exists(), payload
manifest_path = Path(payload["manifest_ref"]).resolve()
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
assert str(manifest["summary_ref"]).strip(), manifest
records = manifest.get("evidence_records") or []
assert isinstance(records, list) and records, manifest
kinds = {str(row.get("kind", "")).strip() for row in records if isinstance(row, dict)}
assert kinds == {"launcher_convergence_receipt", "launcher_convergence_precheck"}, kinds
for row in records:
    mirror = resolve_manifest_member(manifest_path, str(row["mirror_path"]))
    digest = hashlib.sha256(mirror.read_bytes()).hexdigest()
    assert digest == str(row["sha256"]).strip(), row
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
import hashlib
import sys
from pathlib import Path

def resolve_manifest_member(manifest_path: Path, value: str) -> Path:
    raw = Path(str(value).strip())
    if raw.is_absolute():
        return raw.resolve()
    return (manifest_path.parent / raw).resolve()

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
assert row["backfill_status"] == "PASS_REQUIRED", row
assert row["install_status"] == "PASS_REQUIRED", row
assert row["validator_status"] == "PASS_REQUIRED", row
manifest_path = Path(payload["manifest_ref"]).resolve()
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
records = manifest.get("evidence_records") or []
kinds = {str(row.get("kind", "")).strip() for row in records if isinstance(row, dict)}
assert kinds == {
    "launcher_convergence_receipt",
    "launcher_convergence_precheck",
    "launcher_convergence_postcheck",
}, kinds
for row in records:
    mirror = resolve_manifest_member(manifest_path, str(row["mirror_path"]))
    digest = hashlib.sha256(mirror.read_bytes()).hexdigest()
    assert digest == str(row["sha256"]).strip(), row
print("launcher_convergence_apply_status=PASS_REQUIRED")
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

python3 - "${REFRESH_APPLY_JSON}" "${APPLY_JSON}" <<'PY'
import json
import hashlib
import sys
from pathlib import Path

def resolve_manifest_member(manifest_path: Path, value: str) -> Path:
    raw = Path(str(value).strip())
    if raw.is_absolute():
        return raw.resolve()
    return (manifest_path.parent / raw).resolve()

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
apply_payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["truth_sync_status"] == "PASS_REQUIRED", payload
assert payload["repair_status"] == "apply_truth_synced", payload
receipt_path = Path(apply_payload["evidence_ref"]).resolve()
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
assert receipt["evidence_ref"] == str(receipt_path), receipt
manifest_path = Path(receipt["manifest_ref"]).resolve()
assert manifest_path.exists(), receipt
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
assert str(manifest["summary_ref"]).strip(), manifest
for row in manifest.get("evidence_records") or []:
    mirror = resolve_manifest_member(manifest_path, str(row["mirror_path"]))
    digest = hashlib.sha256(mirror.read_bytes()).hexdigest()
    assert digest == str(row["sha256"]).strip(), row
print("launcher_convergence_truth_sync_apply_status=PASS_REQUIRED")
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
