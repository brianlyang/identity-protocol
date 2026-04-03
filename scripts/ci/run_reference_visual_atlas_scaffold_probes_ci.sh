#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/reference-visual-atlas-scaffold-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

DRY_ROOT="${TMP_ROOT}/dry-run-preview"
WRITE_ROOT="${TMP_ROOT}/write-preview"
DRY_JSON="${TMP_ROOT}/dry-run.json"
WRITE_JSON="${TMP_ROOT}/write.json"

COMMON_ARGS=(
  --atlas-family-slug identity-protocol-example-visual-atlas
  --doc-version v1.6
  --stream-version v1.6.99
  --validator-slug example
  --title "Identity Protocol Example Visual Atlas"
  --surface-summary "example explanation surface"
  --purpose-sentence "the example routing model and non-goals"
  --status-key example_visual_atlas_governance_status
  --error-code IP-EXAMPLE-ATLAS-001
  --svg-name identity_protocol_example_overview_v1699.svg
  --svg-name identity_protocol_example_state_machine_v1699.svg
  --owner-doc docs/governance/example-governance-v1.6.99.md
  --owner-doc docs/review/example-review-v1.6.99.md
)

python3 "${ROOT}/scripts/generate_reference_visual_atlas_scaffold.py" \
  "${COMMON_ARGS[@]}" \
  --output-root "${DRY_ROOT}" \
  --dry-run \
  --json-only >"${DRY_JSON}"

python3 - <<'PY' "${DRY_JSON}" "${DRY_ROOT}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
dry_root = pathlib.Path(sys.argv[2])

assert payload["reference_visual_atlas_scaffold_status"] == "PASS_PREVIEW", payload
assert payload["write_mode"] == "dry_run", payload
assert payload["canonical_doc"] == "docs/references/identity-protocol-example-visual-atlas-v1.6.md", payload
assert payload["validator_script"] == "scripts/validate_example_visual_atlas_governance.py", payload
assert "docs/references/assets/identity-protocol-example-visual-atlas/.gitkeep" in payload["generated_paths"], payload
assert not dry_root.exists(), dry_root
PY

python3 "${ROOT}/scripts/generate_reference_visual_atlas_scaffold.py" \
  "${COMMON_ARGS[@]}" \
  --output-root "${WRITE_ROOT}" \
  --json-only >"${WRITE_JSON}"

python3 - <<'PY' "${WRITE_JSON}" "${WRITE_ROOT}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
write_root = pathlib.Path(sys.argv[2])

assert payload["reference_visual_atlas_scaffold_status"] == "PASS_WRITTEN", payload
assert payload["write_mode"] == "write", payload
assert write_root.exists(), write_root
for rel in payload["generated_paths"]:
    assert (write_root / rel).exists(), rel
PY

python3 -m py_compile "${WRITE_ROOT}/scripts/validate_example_visual_atlas_governance.py"

grep -F 'identity/protocol/mappings/stream-doc-registry.current.yaml' \
  "${WRITE_ROOT}/docs/references/identity-protocol-example-visual-atlas-v1.6.md" >/dev/null
grep -E 'preview(-| )?only|preview output' "${WRITE_ROOT}/NEXT_STEPS.md" >/dev/null
grep -F 'The canonical explanatory visual atlas for this stream is:' \
  "${WRITE_ROOT}/scripts/validate_example_visual_atlas_governance.py" >/dev/null

if python3 "${ROOT}/scripts/generate_reference_visual_atlas_scaffold.py" \
  "${COMMON_ARGS[@]}" \
  --output-root "${WRITE_ROOT}" \
  --json-only >"${TMP_ROOT}/unexpected-overwrite.json"; then
  echo "[FAIL] scaffold generator unexpectedly overwrote preview tree without --force"
  exit 1
fi

python3 "${ROOT}/scripts/generate_reference_visual_atlas_scaffold.py" \
  "${COMMON_ARGS[@]}" \
  --output-root "${WRITE_ROOT}" \
  --force \
  --json-only >"${TMP_ROOT}/force-write.json"

python3 - <<'PY' "${TMP_ROOT}/force-write.json"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["reference_visual_atlas_scaffold_status"] == "PASS_WRITTEN", payload
assert payload["write_mode"] == "write", payload
PY

echo "[PASS] reference visual atlas scaffold probes passed"
