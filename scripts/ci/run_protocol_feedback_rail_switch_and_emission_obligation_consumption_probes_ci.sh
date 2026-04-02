#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT="${TMPDIR:-$REPO_ROOT/.tmp}"
mkdir -p "$TMP_ROOT"
WORK_ROOT="$(mktemp -d "$TMP_ROOT/protocol-feedback-issue049-probes.XXXXXX")"
trap 'rm -rf "$WORK_ROOT"' EXIT

VALIDATOR="$REPO_ROOT/scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py"
POSITIVE_JSON="$WORK_ROOT/positive.json"
SKIP_EMIT_JSON="$WORK_ROOT/skip-emit.json"
SKIP_OUTBOX_JSON="$WORK_ROOT/skip-outbox.json"
DOC_DRIFT_JSON="$WORK_ROOT/doc-drift.json"
NEGATIVE_ROOT="$WORK_ROOT/doc-drift-root"

TMPDIR="$TMP_ROOT" python3 "$VALIDATOR" --repo-root "$REPO_ROOT" --json-only > "$POSITIVE_JSON"

set +e
TMPDIR="$TMP_ROOT" python3 "$VALIDATOR" --repo-root "$REPO_ROOT" --skip-atomic-emit --json-only > "$SKIP_EMIT_JSON"
SKIP_EMIT_RC=$?
TMPDIR="$TMP_ROOT" python3 "$VALIDATOR" --repo-root "$REPO_ROOT" --skip-outbox-sync --json-only > "$SKIP_OUTBOX_JSON"
SKIP_OUTBOX_RC=$?
set -e

python3 - "$REPO_ROOT" "$NEGATIVE_ROOT" <<'PY'
from pathlib import Path
import shutil
import sys

repo_root = Path(sys.argv[1]).resolve()
negative_root = Path(sys.argv[2]).resolve()
paths = [
    'docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md',
    'docs/review/protocol-remediation-audit-ledger-v1.6.x-protocol-feedback-rail-switch-and-emission-obligation-consumption.md',
    'docs/workbook/protocol-issue-register-v1.6.md',
    'docs/workbook/protocol-deep-audit-workbook-v1.6.md',
    'scripts/protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_common.py',
    'scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py',
    'scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh',
]
for rel in paths:
    src = repo_root / rel
    dst = negative_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

governance = negative_root / 'docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md'
text = governance.read_text(encoding='utf-8')
needle = 'protocol_feedback_emit_invoked'
if needle not in text:
    raise SystemExit(f'missing mutation needle: {needle}')
governance.write_text(text.replace(needle, 'protocol_feedback_emit_invoked_removed', 1), encoding='utf-8')
PY

set +e
TMPDIR="$TMP_ROOT" python3 "$VALIDATOR" --repo-root "$NEGATIVE_ROOT" --json-only > "$DOC_DRIFT_JSON"
DOC_DRIFT_RC=$?
set -e

python3 - "$POSITIVE_JSON" "$SKIP_EMIT_JSON" "$SKIP_EMIT_RC" "$SKIP_OUTBOX_JSON" "$SKIP_OUTBOX_RC" "$DOC_DRIFT_JSON" "$DOC_DRIFT_RC" <<'PY'
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
skip_emit = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
skip_emit_rc = int(sys.argv[3])
skip_outbox = json.loads(Path(sys.argv[4]).read_text(encoding='utf-8'))
skip_outbox_rc = int(sys.argv[5])
doc_drift = json.loads(Path(sys.argv[6]).read_text(encoding='utf-8'))
doc_drift_rc = int(sys.argv[7])

if positive.get('status') != 'PASS_REQUIRED':
    raise SystemExit('positive validator did not PASS_REQUIRED')
if positive.get('protocol_feedback_rule_consumption_status') != 'PASS_REQUIRED':
    raise SystemExit('positive validator did not materialize rule consumption')
if skip_emit_rc == 0:
    raise SystemExit('skip-atomic-emit negative unexpectedly succeeded')
if skip_emit.get('status') != 'FAIL_REQUIRED':
    raise SystemExit('skip-atomic-emit negative did not FAIL_REQUIRED')
if 'protocol_feedback_emit_not_invoked' not in skip_emit.get('stale_reasons', []):
    raise SystemExit('skip-atomic-emit negative missing protocol_feedback_emit_not_invoked')
if skip_outbox_rc == 0:
    raise SystemExit('skip-outbox-sync negative unexpectedly succeeded')
if skip_outbox.get('status') != 'FAIL_REQUIRED':
    raise SystemExit('skip-outbox-sync negative did not FAIL_REQUIRED')
if 'protocol_feedback_channel_not_entered' not in skip_outbox.get('stale_reasons', []):
    raise SystemExit('skip-outbox-sync negative missing protocol_feedback_channel_not_entered')
if doc_drift_rc == 0:
    raise SystemExit('doc-drift negative unexpectedly succeeded')
if doc_drift.get('status') != 'FAIL_REQUIRED':
    raise SystemExit('doc-drift negative did not FAIL_REQUIRED')
if doc_drift.get('documentation_contract_status') != 'FAIL_REQUIRED':
    raise SystemExit('doc-drift negative did not fail documentation contract status')
if 'documentation_contract_drift' not in doc_drift.get('stale_reasons', []):
    raise SystemExit('doc-drift negative missing documentation_contract_drift')
PY

echo "PASS"
