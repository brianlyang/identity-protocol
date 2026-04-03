#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

TMPDIR="${TMPDIR:-$ROOT/.tmp}"
mkdir -p "$TMPDIR"

python3 identity-protocol-local/scripts/validate_host_visible_native_attestation_projection.py --json-only >/dev/null

probe_tmp="$(mktemp -d "$TMPDIR/host-visible-native-attestation-probe.XXXXXX")"
trap 'rm -rf "$probe_tmp"' EXIT

governance_src="identity-protocol-local/docs/governance/identity-host-visible-native-attestation-projection-governance-v1.6.x.md"
review_src="identity-protocol-local/docs/review/protocol-remediation-audit-ledger-v1.6.x-host-visible-native-attestation-projection.md"

governance_neg="$probe_tmp/governance-negative.md"
cp "$governance_src" "$governance_neg"
python3 - "$governance_neg" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace("host_visible_post_check_metrics_status", "host_visible_post_check_metrics_status_removed")
path.write_text(text, encoding="utf-8")
PY

if HVNAP_GOVERNANCE_PATH="$governance_neg" \
    python3 identity-protocol-local/scripts/validate_host_visible_native_attestation_projection.py --json-only >/dev/null 2>&1; then
    echo '{"status":"FAIL","reason":"negative_probe_governance_field_removal_not_detected"}'
    exit 1
fi

review_neg="$probe_tmp/review-negative.md"
cp "$review_src" "$review_neg"
python3 - "$review_neg" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace("native_attestation_wiring_capability=unavailable", "native_attestation_wiring_capability=removed", 1)
path.write_text(text, encoding="utf-8")
PY

if HVNAP_REVIEW_PATH="$review_neg" \
    python3 identity-protocol-local/scripts/validate_host_visible_native_attestation_projection.py --json-only >/dev/null 2>&1; then
    echo '{"status":"FAIL","reason":"negative_probe_review_anchor_removal_not_detected"}'
    exit 1
fi

echo '{"status":"PASS","probes":["positive_validator_pass","negative_governance_field_removal_detected","negative_review_anchor_removal_detected"]}'
