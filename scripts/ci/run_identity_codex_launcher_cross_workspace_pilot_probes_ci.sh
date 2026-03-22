#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CURRENT_WORKSPACE_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-codex-launcher-cross-workspace-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

DISCOVERY_JSON="${TMP_ROOT}/discovery.json"
python3 - "${CURRENT_WORKSPACE_ROOT}" "${IDENTITY_LAUNCHER_PILOT_CATALOG:-}" > "${DISCOVERY_JSON}" <<'PY'
import json
import sys
from pathlib import Path

import yaml

current_workspace_root = Path(sys.argv[1]).resolve()
explicit_catalog = str(sys.argv[2] or "").strip()
current_catalog = (current_workspace_root / ".identity" / "catalog.local.yaml").resolve()


def active_runtime_identity_ids(catalog_path: Path) -> list[str]:
    doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    rows = doc.get("identities") or []
    active: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        identity_id = str(row.get("id", "")).strip()
        if not identity_id:
            continue
        if str(row.get("status", "")).strip().lower() != "active":
            continue
        if str(row.get("profile", "")).strip().lower() != "runtime":
            continue
        if str(row.get("runtime_mode", "")).strip().lower() == "demo_only":
            continue
        active.append(identity_id)
    return active


def build_result(catalog_path: Path) -> dict[str, object]:
    ids = active_runtime_identity_ids(catalog_path)
    return {
        "catalog_path": str(catalog_path.resolve()),
        "workspace_root": str(catalog_path.resolve().parent.parent),
        "active_runtime_identity_ids": ids,
        "checked_identity_count": len(ids),
    }

candidate_catalogs: list[Path] = []
if explicit_catalog:
    candidate_catalogs.append(Path(explicit_catalog).expanduser().resolve())
else:
    sibling_root = current_workspace_root.parent.resolve()
    for path in sorted(sibling_root.glob("*/.identity/catalog.local.yaml")):
        if path.resolve() == current_catalog:
            continue
        candidate_catalogs.append(path.resolve())

for candidate in candidate_catalogs:
    if not candidate.exists() or not candidate.is_file():
        continue
    result = build_result(candidate)
    if result["checked_identity_count"]:
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(0)

raise SystemExit("no eligible cross-workspace runtime catalog discovered")
PY

SOURCE_CATALOG="$(python3 - <<'PY' "${DISCOVERY_JSON}"
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(payload['catalog_path'])
PY
)"
SOURCE_WORKSPACE_ROOT="$(python3 - <<'PY' "${DISCOVERY_JSON}"
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(payload['workspace_root'])
PY
)"
FIRST_IDENTITY_ID="$(python3 - <<'PY' "${DISCOVERY_JSON}"
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(payload['active_runtime_identity_ids'][0])
PY
)"

TMP_WORKSPACE_ROOT="${TMP_ROOT}/workspace"
TMP_IDENTITY_HOME="${TMP_WORKSPACE_ROOT}/.identity"
TMP_CATALOG="${TMP_IDENTITY_HOME}/catalog.local.yaml"
TMP_CODEX_HOME="${TMP_ROOT}/codex-home"
TMP_EVIDENCE_ROOT="${TMP_ROOT}/evidence"
mkdir -p "${TMP_WORKSPACE_ROOT}" "${TMP_CODEX_HOME}" "${TMP_EVIDENCE_ROOT}"

python3 - "${SOURCE_WORKSPACE_ROOT}" "${TMP_WORKSPACE_ROOT}" <<'PY'
import shutil
import sys
from pathlib import Path

import yaml

source_workspace = Path(sys.argv[1]).resolve()
target_workspace = Path(sys.argv[2]).resolve()
source_identity = (source_workspace / '.identity').resolve()
target_identity = (target_workspace / '.identity').resolve()
shutil.copytree(source_identity, target_identity, symlinks=False, ignore=shutil.ignore_patterns('__pycache__'))

catalog_path = (target_identity / 'catalog.local.yaml').resolve()
doc = yaml.safe_load(catalog_path.read_text(encoding='utf-8')) or {}
rows = doc.get('identities') or []
rewritten = []
for row in rows:
    if not isinstance(row, dict):
        continue
    next_row = dict(row)
    identity_id = str(next_row.get('id', '')).strip()
    if identity_id:
        pack_path = (target_identity / identity_id).resolve()
        next_row['pack_path'] = str(pack_path)
        next_row['canonical_pack_path'] = str(pack_path)
    rewritten.append(next_row)
doc['identities'] = rewritten
catalog_path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding='utf-8')
PY

DRY_JSON="${TMP_ROOT}/dry-run.json"
if python3 "${REPO_ROOT}/scripts/run_identity_codex_launcher_workspace_convergence.py" \
  --catalog "${TMP_CATALOG}" \
  --mode dry-run \
  --codex-home "${TMP_CODEX_HOME}" \
  --artifact-root "${TMP_EVIDENCE_ROOT}" \
  --run-token cross-workspace-pilot \
  --json-only > "${DRY_JSON}"; then
  echo "[FAIL] cross-workspace launcher convergence dry-run unexpectedly returned success"
  exit 1
fi

python3 - "${DRY_JSON}" "${TMP_CATALOG}" "${TMP_WORKSPACE_ROOT}" <<'PY'
import json
import hashlib
import sys
from pathlib import Path

def resolve_manifest_member(manifest_path: Path, value: str) -> Path:
    raw = Path(str(value).strip())
    if raw.is_absolute():
        return raw.resolve()
    return (manifest_path.parent / raw).resolve()

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_catalog = str(Path(sys.argv[2]).resolve())
expected_workspace = str(Path(sys.argv[3]).resolve())
assert payload['status'] == 'FAIL_REQUIRED', payload
assert payload['workspace_catalog_authority_mode'] == 'workspace_local_runtime_catalog', payload
assert payload['catalog_path'] == expected_catalog, payload
assert payload['workspace_root'] == expected_workspace, payload
assert payload['checked_identity_count'] > 0, payload
assert payload['planned_repair_count'] > 0, payload
assert payload['repair_status'] == 'dry_run_preview', payload
assert Path(payload['manifest_ref']).exists(), payload
manifest_path = Path(payload['manifest_ref']).resolve()
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
kinds = {str(row.get('kind', '')).strip() for row in (manifest.get('evidence_records') or []) if isinstance(row, dict)}
assert kinds == {'launcher_convergence_receipt', 'launcher_convergence_precheck'}, kinds
for row in manifest.get('evidence_records') or []:
    mirror = resolve_manifest_member(manifest_path, str(row['mirror_path']))
    digest = hashlib.sha256(mirror.read_bytes()).hexdigest()
    assert digest == str(row['sha256']).strip(), row
print('launcher_cross_workspace_dry_run_status=FAIL_REQUIRED')
PY

APPLY_JSON="${TMP_ROOT}/apply.json"
python3 "${REPO_ROOT}/scripts/run_identity_codex_launcher_workspace_convergence.py" \
  --catalog "${TMP_CATALOG}" \
  --mode apply \
  --codex-home "${TMP_CODEX_HOME}" \
  --artifact-root "${TMP_EVIDENCE_ROOT}" \
  --run-token cross-workspace-pilot \
  --json-only > "${APPLY_JSON}"

python3 - "${APPLY_JSON}" "${TMP_CATALOG}" "${TMP_WORKSPACE_ROOT}" <<'PY'
import json
import hashlib
import sys
from pathlib import Path

def resolve_manifest_member(manifest_path: Path, value: str) -> Path:
    raw = Path(str(value).strip())
    if raw.is_absolute():
        return raw.resolve()
    return (manifest_path.parent / raw).resolve()

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_catalog = str(Path(sys.argv[2]).resolve())
expected_workspace = str(Path(sys.argv[3]).resolve())
assert payload['status'] == 'PASS_REQUIRED', payload
assert payload['catalog_path'] == expected_catalog, payload
assert payload['workspace_root'] == expected_workspace, payload
assert payload['checked_identity_count'] > 0, payload
assert payload['remaining_violation_count'] == 0, payload
assert payload['postcheck_status'] == 'PASS_REQUIRED', payload
assert Path(payload['evidence_ref']).exists(), payload
assert Path(payload['manifest_ref']).exists(), payload
manifest_path = Path(payload['manifest_ref']).resolve()
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
kinds = {str(row.get('kind', '')).strip() for row in (manifest.get('evidence_records') or []) if isinstance(row, dict)}
assert kinds == {
    'launcher_convergence_receipt',
    'launcher_convergence_precheck',
    'launcher_convergence_postcheck',
}, kinds
for row in manifest.get('evidence_records') or []:
    mirror = resolve_manifest_member(manifest_path, str(row['mirror_path']))
    digest = hashlib.sha256(mirror.read_bytes()).hexdigest()
    assert digest == str(row['sha256']).strip(), row
print('launcher_cross_workspace_apply_status=PASS_REQUIRED')
PY

FRESH_TRUTH_SYNC_JSON="${TMP_ROOT}/fresh-truth-sync.json"
python3 "${REPO_ROOT}/scripts/refresh_identity_codex_launcher_evidence_truth_sync.py" \
  --artifact-root "${TMP_EVIDENCE_ROOT}" \
  --run-token cross-workspace-pilot \
  --workspace-root "${TMP_WORKSPACE_ROOT}" \
  --json-only > "${FRESH_TRUTH_SYNC_JSON}"

python3 - "${FRESH_TRUTH_SYNC_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert payload['status'] == 'PASS_REQUIRED', payload
assert payload['truth_sync_status'] == 'PASS_REQUIRED', payload
assert payload['receipts_with_changes'] == 0, payload
assert payload['manifest_write_count'] == 0, payload
assert payload['repair_status'] == 'already_truth_synced', payload
print('launcher_cross_workspace_fresh_truth_sync_status=PASS_REQUIRED')
PY

CLOSURE_JSON="${TMP_ROOT}/closure.json"
(cd "${TMP_WORKSPACE_ROOT}" && \
  env -u IDENTITY_HOME -u IDENTITY_CATALOG -u IDENTITY_PROTOCOL_HOME \
    CODEX_HOME="${TMP_CODEX_HOME}" \
    python3 "${REPO_ROOT}/scripts/check_identity_codex_launcher_migration_closure.py" \
      --catalog .identity/catalog.local.yaml \
      --workspace-runtime-only \
      --json-only) > "${CLOSURE_JSON}"

python3 - "${CLOSURE_JSON}" "${TMP_CODEX_HOME}" "${TMP_CATALOG}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_identity_home = str((Path(sys.argv[2]).resolve() / '.identity').resolve())
expected_catalog = str(Path(sys.argv[3]).resolve())
assert payload['identity_codex_launcher_migration_closure_status'] == 'PASS_REQUIRED', payload
assert payload['catalogs_checked'] == [expected_catalog], payload
assert payload['checked_identity_count'] > 0, payload
for row in payload['checked_rows']:
    assert row['runtime_paths_status'] == 'PASS_REQUIRED', row
    assert row['launcher_config_identity_home'] == expected_identity_home, row
    assert row['runtime_identity_home'] == str(Path(expected_catalog).parent.resolve()), row
print('launcher_cross_workspace_closure_status=PASS_REQUIRED')
PY

RESOLVE_JSON="${TMP_ROOT}/resolve.json"
(cd "${TMP_WORKSPACE_ROOT}" && \
  env -u IDENTITY_HOME -u IDENTITY_CATALOG -u IDENTITY_PROTOCOL_HOME \
    CODEX_HOME="${TMP_CODEX_HOME}" \
    python3 "${REPO_ROOT}/scripts/resolve_identity_context.py" \
      resolve \
      --identity-id "${FIRST_IDENTITY_ID}") > "${RESOLVE_JSON}"

python3 - "${RESOLVE_JSON}" "${TMP_CATALOG}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_catalog = str(Path(sys.argv[2]).resolve())
assert payload['catalog_path'] == expected_catalog, payload
assert payload['source_layer'] == 'project', payload
assert payload['resolved_scope'] == 'USER', payload
assert payload['candidate_matches'], payload
assert payload['candidate_matches'][0]['scope'] == 'USER', payload
print('launcher_cross_workspace_resolve_status=PASS_REQUIRED')
PY

VALIDATOR_JSON="${TMP_ROOT}/validator.json"
env -u IDENTITY_HOME -u IDENTITY_CATALOG -u IDENTITY_PROTOCOL_HOME \
  CODEX_HOME="${TMP_CODEX_HOME}" \
  python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher.py" \
    --catalog "${TMP_CATALOG}" \
    --identity-id "${FIRST_IDENTITY_ID}" \
    --require-installed \
    --json-only > "${VALIDATOR_JSON}"

python3 - "${VALIDATOR_JSON}" "${TMP_CODEX_HOME}" "${TMP_CATALOG}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_identity_home = str((Path(sys.argv[2]).resolve() / '.identity').resolve())
expected_catalog = str(Path(sys.argv[3]).resolve())
assert payload['identity_codex_launcher_status'] == 'PASS_REQUIRED', payload
assert payload['runtime_paths_status'] == 'PASS_REQUIRED', payload
assert payload['launcher_config_identity_home'] == expected_identity_home, payload
assert payload['runtime_identity_home'] == str(Path(expected_catalog).parent.resolve()), payload
print('launcher_cross_workspace_validator_status=PASS_REQUIRED')
PY

echo "[PASS] identity codex launcher cross-workspace pilot probes passed"
