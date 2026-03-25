#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-runtime-mode-guard-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}"

PROJECT_CATALOG="$(python3 - <<'PY'
from pathlib import Path
repo_root = Path.cwd().resolve()
if repo_root.name == "identity-protocol-local":
    print((repo_root.parent / ".identity" / "catalog.local.yaml").resolve())
else:
    print((repo_root / ".identity" / "catalog.local.yaml").resolve())
PY
)"
REPO_CATALOG="${REPO_ROOT}/identity/catalog/identities.yaml"

echo "[RUN] resolve positive/negative runtime-mode guard fixtures dynamically"
SELECTION_JSON="$(python3 - <<'PY' "${PROJECT_CATALOG}" "${REPO_CATALOG}"
from __future__ import annotations
import json
import sys
from pathlib import Path
import yaml

project_catalog = Path(sys.argv[1]).resolve()
repo_catalog = Path(sys.argv[2]).resolve()
project_home = project_catalog.parent.resolve()
repo_root = repo_catalog.parent.parent.parent.resolve()

project_doc = yaml.safe_load(project_catalog.read_text(encoding="utf-8")) or {}
repo_doc = yaml.safe_load(repo_catalog.read_text(encoding="utf-8")) or {}
project_rows = [x for x in (project_doc.get("identities") or []) if isinstance(x, dict)]
repo_rows = [x for x in (repo_doc.get("identities") or []) if isinstance(x, dict)]
project_ids = {str(x.get("id", "")).strip() for x in project_rows if str(x.get("id", "")).strip()}

def _resolve_pack(pack_raw: str) -> Path:
    token = str(pack_raw or "").strip()
    if not token:
        return Path("/nonexistent")
    raw = Path(token).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    return (repo_root / raw).resolve()

positive = None
for row in project_rows:
    iid = str(row.get("id", "")).strip()
    pack = _resolve_pack(str(row.get("pack_path", "")))
    if iid and pack.exists() and pack.is_dir() and project_home in [pack, *pack.parents]:
        positive = iid
        break

negative = None
for row in repo_rows:
    iid = str(row.get("id", "")).strip()
    if not iid or iid in project_ids:
        continue
    profile = str(row.get("profile", "")).strip().lower()
    runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
    pack = _resolve_pack(str(row.get("pack_path", "")))
    if (profile == "fixture" or runtime_mode == "demo_only") and pack.exists():
        negative = iid
        break

if not positive:
    raise SystemExit("no runtime-admitted identity found in project catalog")
if not negative:
    raise SystemExit("no repo-metadata-only fixture identity found in repo catalog")

print(json.dumps({"positive_identity_id": positive, "negative_identity_id": negative}, ensure_ascii=False))
PY
)"

POSITIVE_ID="$(python3 - <<'PY' "${SELECTION_JSON}"
import json, sys
print(json.loads(sys.argv[1])["positive_identity_id"])
PY
)"
NEGATIVE_ID="$(python3 - <<'PY' "${SELECTION_JSON}"
import json, sys
print(json.loads(sys.argv[1])["negative_identity_id"])
PY
)"

echo "[RUN] positive runtime-admitted project-catalog identity guard replay (${POSITIVE_ID})"
IDENTITY_CATALOG="${PROJECT_CATALOG}" python3 - <<'PY' "${POSITIVE_ID}" "${PROJECT_CATALOG}" "${REPO_CATALOG}"
from __future__ import annotations
import json
import subprocess
import sys

identity_id, project_catalog, repo_catalog = sys.argv[1:4]
proc = subprocess.run(
    [
        "python3",
        "scripts/validate_identity_runtime_mode_guard.py",
        "--identity-id",
        identity_id,
        "--catalog",
        project_catalog,
        "--repo-catalog",
        repo_catalog,
        "--expect-mode",
        "auto",
        "--operation",
        "readiness",
        "--json-only",
    ],
    capture_output=True,
    text=True,
    check=False,
)
if proc.returncode != 0:
    raise SystemExit(proc.stdout + proc.stderr)
payload = json.loads(proc.stdout)
assert payload["runtime_mode_guard_status"] == "PASS_REQUIRED", payload
assert payload["binding_class"] == "runtime_catalog_admitted", payload
assert payload["checks"]["resolved_catalog_matches_requested"] is True, payload
assert payload["checks"]["resolved_source_layer_runtime"] is True, payload
print(json.dumps({"positive_runtime_mode_guard_probe_status": "PASS_REQUIRED", "identity_id": identity_id}, ensure_ascii=False))
PY

echo "[RUN] negative repo-metadata fallback identity guard replay (${NEGATIVE_ID})"
IDENTITY_CATALOG="${PROJECT_CATALOG}" python3 - <<'PY' "${NEGATIVE_ID}" "${PROJECT_CATALOG}" "${REPO_CATALOG}"
from __future__ import annotations
import json
import subprocess
import sys

identity_id, project_catalog, repo_catalog = sys.argv[1:4]
proc = subprocess.run(
    [
        "python3",
        "scripts/validate_identity_runtime_mode_guard.py",
        "--identity-id",
        identity_id,
        "--catalog",
        project_catalog,
        "--repo-catalog",
        repo_catalog,
        "--expect-mode",
        "auto",
        "--operation",
        "readiness",
        "--json-only",
    ],
    capture_output=True,
    text=True,
    check=False,
)
if proc.returncode == 0:
    raise SystemExit(f"expected fail-close for repo-metadata fallback identity: {identity_id}")
payload = json.loads(proc.stdout)
assert payload["runtime_mode_guard_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ENV-004", payload
assert payload["binding_class"] == "repo_metadata_fallback_unadmitted", payload
assert payload["repo_metadata_fallback_detected"] is True, payload
assert "repo_metadata_identity_not_adopted_into_runtime_catalog" in (payload.get("stale_reasons") or []), payload
print(json.dumps({"negative_runtime_mode_guard_probe_status": "PASS_REQUIRED", "identity_id": identity_id}, ensure_ascii=False))
PY

echo "[PASS] identity runtime mode guard probes passed"
