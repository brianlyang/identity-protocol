#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

SHADOW_ROOT="${TMP_ROOT}/shadow-repo"

printf '[RUN] positive audit snapshot index governance validation\n'
python3 "${REPO_ROOT}/scripts/validate_audit_snapshot_index.py" --repo-root "${REPO_ROOT}" >/dev/null

mkdir -p "${SHADOW_ROOT}/docs/governance/templates" "${SHADOW_ROOT}/scripts"

cp "${REPO_ROOT}/scripts/validate_audit_snapshot_index.py" "${SHADOW_ROOT}/scripts/validate_audit_snapshot_index.py"
cp "${REPO_ROOT}/scripts/repo_root_resolution_common.py" "${SHADOW_ROOT}/scripts/repo_root_resolution_common.py"
cp "${REPO_ROOT}/docs/governance/AUDIT_SNAPSHOT_INDEX.md" "${SHADOW_ROOT}/docs/governance/AUDIT_SNAPSHOT_INDEX.md"
cp "${REPO_ROOT}/docs/governance/audit-snapshot-policy-v1.2.11.md" "${SHADOW_ROOT}/docs/governance/audit-snapshot-policy-v1.2.11.md"
cp "${REPO_ROOT}/docs/governance/templates/audit-snapshot-template.md" "${SHADOW_ROOT}/docs/governance/templates/audit-snapshot-template.md"

while IFS= read -r file; do
  cp "${REPO_ROOT}/docs/governance/${file}" "${SHADOW_ROOT}/docs/governance/${file}"
done < <(cd "${REPO_ROOT}/docs/governance" && ls audit-snapshot-*.md)

python3 - <<'PY' "${SHADOW_ROOT}/docs/governance/AUDIT_SNAPSHOT_INDEX.md"
from pathlib import Path
import sys

path = Path(sys.argv[1]).resolve()
text = path.read_text(encoding="utf-8")
text = text.replace(
    "All audit-snapshot entries listed in this section are archival snapshots only. ",
    "",
)
path.write_text(text, encoding="utf-8")
PY

printf '[RUN] negative audit snapshot index governance validation\n'
if (cd "${SHADOW_ROOT}" && python3 scripts/validate_audit_snapshot_index.py --repo-root "${SHADOW_ROOT}" >/tmp/audit_snapshot_index_negative.log 2>&1); then
  echo '[FAIL] negative audit snapshot index governance probe must fail'
  cat /tmp/audit_snapshot_index_negative.log
  exit 1
fi

if ! grep -q 'required_index_marker_missing:All audit-snapshot entries listed in this section are archival snapshots only\.' /tmp/audit_snapshot_index_negative.log; then
  echo '[FAIL] negative audit snapshot index governance probe must detect missing archival snapshot marker'
  cat /tmp/audit_snapshot_index_negative.log
  exit 1
fi

echo "[PASS] audit snapshot index governance probes passed"
