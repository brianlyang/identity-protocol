#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-lane-handoff-ci"
protocol_root_probe_define_full_mirror

cd "$ROOT"

PROBE_TMP_DIR="${TMP_ROOT}/root-lane-handoff-probe"
mkdir -p "$PROBE_TMP_DIR"

CONTRACT_DOC="identity/protocol/LANE_HANDOFF_CONTRACT.md"
CURRENT_MAPPING="identity/protocol/mappings/root-lane-handoff.current.yaml"
VERSIONED_MAPPING="identity/protocol/mappings/root-lane-handoff.v1.yaml"
VALIDATOR="scripts/validate_protocol_root_lane_handoff.py"

python3 "$VALIDATOR" --json-only >/dev/null

cp "$CONTRACT_DOC" "$PROBE_TMP_DIR/contract.md"
cp "$CURRENT_MAPPING" "$PROBE_TMP_DIR/current.yaml"
cp "$VERSIONED_MAPPING" "$PROBE_TMP_DIR/versioned.yaml"

python3 - <<'PY' "$PROBE_TMP_DIR/contract.md"
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
text = text.replace('"artifact_classification": "compatibility"', '"artifact_classification": "canonical"', 1)
path.write_text(text, encoding='utf-8')
PY
if python3 "$VALIDATOR" --contract-doc "$PROBE_TMP_DIR/contract.md" --current-mapping "$PROBE_TMP_DIR/current.yaml" --versioned-mapping "$PROBE_TMP_DIR/versioned.yaml" --json-only >/dev/null 2>&1; then
  echo "negative probe failed: competing canonical classification was admitted" >&2
  exit 1
fi

cp "$CONTRACT_DOC" "$PROBE_TMP_DIR/contract.md"
python3 - <<'PY' "$PROBE_TMP_DIR/contract.md"
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
text = text.replace('This file is compatibility-only.', 'This file remains the authoritative root-domain contract for governed lane-handoff law.', 1)
path.write_text(text, encoding='utf-8')
PY
if python3 "$VALIDATOR" --contract-doc "$PROBE_TMP_DIR/contract.md" --current-mapping "$PROBE_TMP_DIR/current.yaml" --versioned-mapping "$PROBE_TMP_DIR/versioned.yaml" --json-only >/dev/null 2>&1; then
  echo "negative probe failed: authoritative competing phrase was admitted" >&2
  exit 1
fi

echo "PASS"
