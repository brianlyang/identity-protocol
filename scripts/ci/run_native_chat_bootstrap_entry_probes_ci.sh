#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP_ROOT_BASE="$ROOT/.tmp-native-chat-bootstrap-entry-probes"
mkdir -p "$TMP_ROOT_BASE"
TMP_ROOT="$(mktemp -d "$TMP_ROOT_BASE/run.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

REAL_SUMMARY="$ROOT/activity/evidence/v1612-native-chat-bootstrap-entry/2026-03-19/bootstrap_entry_summary.v1.6.12.json"
REAL_MANIFEST="$ROOT/activity/evidence/v1612-native-chat-bootstrap-entry/2026-03-19/EVIDENCE_MANIFEST.v1.6.12-native-chat-bootstrap-entry.json"
POSITIVE_JSON="$TMP_ROOT/positive.json"
NEG_SUMMARY="$TMP_ROOT/bad-summary.json"
NEG_MANIFEST_FROM_SUMMARY="$TMP_ROOT/bad-summary.manifest.json"
NEG_SUMMARY_OUT="$TMP_ROOT/bad-summary.out.json"
NEG2_SUMMARY="$TMP_ROOT/bad-manifest.summary.json"
NEG2_MANIFEST="$TMP_ROOT/bad-manifest.json"
NEG_MANIFEST_OUT="$TMP_ROOT/bad-manifest.out.json"

python3 "$ROOT/scripts/validate_native_chat_bootstrap_entry_stream.py" --json-only > "$POSITIVE_JSON"

python3 - "$REAL_SUMMARY" "$REAL_MANIFEST" "$NEG_SUMMARY" "$NEG_MANIFEST_FROM_SUMMARY" <<'PY'
import json
import sys
from pathlib import Path
summary = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
manifest = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
summary['fast_audit']['status'] = 'FAIL_REQUIRED'
manifest['summary_ref'] = Path(sys.argv[3]).resolve().relative_to(Path.cwd().resolve()).as_posix()
Path(sys.argv[3]).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
Path(sys.argv[4]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY

if python3 "$ROOT/scripts/validate_native_chat_bootstrap_entry_stream.py" \
  --check-scope bundle_only \
  --summary "$NEG_SUMMARY" \
  --manifest "$NEG_MANIFEST_FROM_SUMMARY" \
  --json-only > "$NEG_SUMMARY_OUT"; then
  echo "[FAIL] negative summary probe unexpectedly passed"
  exit 1
fi

python3 - "$REAL_SUMMARY" "$REAL_MANIFEST" "$NEG2_SUMMARY" "$NEG2_MANIFEST" <<'PY'
import json
import sys
from pathlib import Path
summary = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
manifest = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
manifest['evidence_records'] = [
    row for row in (manifest.get('evidence_records') or [])
    if str((row or {}).get('kind', '')).strip() != 'wrapper_dry_run_exec'
]
manifest['summary_ref'] = Path(sys.argv[3]).resolve().relative_to(Path.cwd().resolve()).as_posix()
Path(sys.argv[3]).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
Path(sys.argv[4]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY

if python3 "$ROOT/scripts/validate_native_chat_bootstrap_entry_stream.py" \
  --check-scope bundle_only \
  --summary "$NEG2_SUMMARY" \
  --manifest "$NEG2_MANIFEST" \
  --json-only > "$NEG_MANIFEST_OUT"; then
  echo "[FAIL] negative manifest probe unexpectedly passed"
  exit 1
fi

python3 - "$POSITIVE_JSON" "$NEG_SUMMARY_OUT" "$NEG_MANIFEST_OUT" <<'PY'
import json
import sys
positive, neg_summary, neg_manifest = [
    json.loads(open(path, encoding='utf-8').read()) for path in sys.argv[1:]
]
assert positive['status'] == 'PASS_REQUIRED', positive
assert positive['stream_opening_status'] == 'PASS_REQUIRED', positive
assert positive['promotion_status'] == 'NON_PROMOTIONAL_LOCK', positive
assert positive['live_smoke_contract_classification'] == 'HOST_RUNTIME_INCONCLUSIVE_NON_PROMOTIONAL', positive
assert neg_summary['status'] == 'FAIL_REQUIRED', neg_summary
assert 'fast_audit_not_pass_required' in neg_summary['failures'], neg_summary
assert neg_manifest['status'] == 'FAIL_REQUIRED', neg_manifest
assert 'manifest_missing_record_kind:wrapper_dry_run_exec' in neg_manifest['failures'], neg_manifest
print(json.dumps({
    'native_chat_bootstrap_entry_probe_status': 'PASS_REQUIRED',
    'positive_stream_opening_status': positive['stream_opening_status'],
    'positive_promotion_status': positive['promotion_status'],
    'negative_summary_failure': 'fast_audit_not_pass_required',
    'negative_manifest_failure': 'manifest_missing_record_kind:wrapper_dry_run_exec',
    'tmp_root': sys.argv[1].rsplit('/', 1)[0],
}, ensure_ascii=False))
PY
