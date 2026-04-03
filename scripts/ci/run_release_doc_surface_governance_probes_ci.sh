#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

POSITIVE_JSON="${TMP_ROOT}/positive.json"
NEGATIVE_JSON="${TMP_ROOT}/negative.json"
SHADOW_ROOT="${TMP_ROOT}/shadow-repo"

printf '[RUN] positive release-doc surface governance validation\n'
python3 "${REPO_ROOT}/scripts/validate_release_doc_surface_governance.py" --repo-root "${REPO_ROOT}" --json-only > "${POSITIVE_JSON}"

python3 "${REPO_ROOT}/scripts/probe_shadow_fixture_common.py" \
  --repo-root "${REPO_ROOT}" \
  --shadow-root "${SHADOW_ROOT}" \
  --copy-file identity/protocol/mappings/stream-doc-registry.current.yaml \
  --copy-file identity/protocol/mappings/stream-doc-registry.v1.6.yaml \
  --copy-file docs/release/identity-v1.6x-release-closure-summary.md \
  --copy-file docs/release/v1-roadmap.md \
  --copy-file docs/release/v1.0.0-release-notes.md \
  --json-only > /dev/null

python3 - <<'PY' "${SHADOW_ROOT}/identity/protocol/mappings/stream-doc-registry.v1.6.yaml" "${SHADOW_ROOT}/docs/release/v1-roadmap.md"
from pathlib import Path
import sys

registry_path = Path(sys.argv[1]).resolve()
roadmap_path = Path(sys.argv[2]).resolve()

registry_text = registry_path.read_text(encoding="utf-8")
registry_text = registry_text.replace("  - docs/release/v1.0.0-release-notes.md\n", "")
registry_path.write_text(registry_text, encoding="utf-8")

roadmap_text = roadmap_path.read_text(encoding="utf-8")
roadmap_text = roadmap_text.replace("historical archival", "historical")
roadmap_path.write_text(roadmap_text, encoding="utf-8")
PY

printf '[RUN] negative release-doc surface governance validation\n'
if python3 "${REPO_ROOT}/scripts/validate_release_doc_surface_governance.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-doc surface governance probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("release_doc_surface_governance_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-doc surface governance status must PASS_REQUIRED")

if negative.get("release_doc_surface_governance_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-doc surface governance status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
if not any(reason.startswith("unclassified_release_docs_present:") for reason in reasons):
    raise SystemExit("negative release-doc surface governance must detect unclassified release doc drift")
if not any(reason.startswith("release_archival_doc_missing_marker:docs/release/v1-roadmap.md:historical archival") for reason in reasons):
    raise SystemExit("negative release-doc surface governance must detect archival marker drift")
PY

echo "[PASS] release doc surface governance probes passed"
