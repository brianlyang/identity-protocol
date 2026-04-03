#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/scripts/runtime_temp_path_common.sh"
TMP_ROOT="$(identity_runtime_mktemp_dir_sh "agent-relay-probes" "run")"
trap 'rm -rf "$TMP_ROOT"' EXIT

SNAPSHOT_JSON="$TMP_ROOT/leader_snapshot.json"
EXACT_RECEIPT="$TMP_ROOT/exact_receipt.json"
SUMMARY_RECEIPT="$TMP_ROOT/summary_receipt.json"
BAD_SUMMARY_RECEIPT="$TMP_ROOT/bad_summary_receipt.json"
BAD_EXACT_RECEIPT="$TMP_ROOT/bad_exact_receipt.json"

cat > "$SNAPSHOT_JSON" <<'JSON'
{
  "generated_at": "2026-03-18T08:00:00Z",
  "items": [
    {
      "identity_id": "base-repo-audit-expert-v3",
      "last_agent_message": "Identity-Context: actor_id=assistant:codex; identity_id=base-repo-audit-expert-v3; scope=USER; lock=LOCK_MATCH; source=project | Layer-Context: work_layer=protocol; source_layer=project\nMachine-Verification: verification_source=relay_probe; identity_id=base-repo-audit-expert-v3; prompt_version=v1.6; source_layer=project; verification_status=PASS_REQUIRED\nFINAL_ANSWER=relay_probe_ok"
    }
  ]
}
JSON

cat > "$EXACT_RECEIPT" <<JSON
{
  "schema_version": "agent_relay_final_answer_receipt_v1",
  "relay_surface": "agent_relay_final_answer",
  "relay_mode": "exact",
  "target_identity_id": "base-repo-audit-expert-v3",
  "question_tag": "relay-probe-exact",
  "source_artifact": "$SNAPSHOT_JSON",
  "source_snapshot_ts": "2026-03-18T08:00:00Z",
  "relay_text": "Identity-Context: actor_id=assistant:codex; identity_id=base-repo-audit-expert-v3; scope=USER; lock=LOCK_MATCH; source=project | Layer-Context: work_layer=protocol; source_layer=project\nMachine-Verification: verification_source=relay_probe; identity_id=base-repo-audit-expert-v3; prompt_version=v1.6; source_layer=project; verification_status=PASS_REQUIRED\nFINAL_ANSWER=relay_probe_ok",
  "delivery_authority": "identity_instance_output"
}
JSON

cat > "$SUMMARY_RECEIPT" <<JSON
{
  "schema_version": "agent_relay_final_answer_receipt_v1",
  "relay_surface": "agent_relay_final_answer",
  "relay_mode": "summary",
  "target_identity_id": "base-repo-audit-expert-v3",
  "question_tag": "relay-probe-summary",
  "source_artifact": "$SNAPSHOT_JSON",
  "source_snapshot_ts": "2026-03-18T08:00:00Z",
  "relay_text": "结论：实例正式答案已经产出 FINAL_ANSWER=relay_probe_ok。",
  "delivery_authority": "ungoverned_operator_summary"
}
JSON

cat > "$BAD_SUMMARY_RECEIPT" <<JSON
{
  "schema_version": "agent_relay_final_answer_receipt_v1",
  "relay_surface": "agent_relay_final_answer",
  "relay_mode": "summary",
  "target_identity_id": "base-repo-audit-expert-v3",
  "question_tag": "relay-probe-summary-bad",
  "source_artifact": "$SNAPSHOT_JSON",
  "source_snapshot_ts": "2026-03-18T08:00:00Z",
  "relay_text": "Identity-Context: actor_id=assistant:codex; identity_id=base-repo-audit-expert-v3; scope=USER; lock=LOCK_MATCH; source=project | Layer-Context: work_layer=protocol; source_layer=project\nMachine-Verification: verification_source=relay_probe; identity_id=base-repo-audit-expert-v3; prompt_version=v1.6; source_layer=project; verification_status=PASS_REQUIRED\n结论：这是违规的 summary 伪装。",
  "delivery_authority": "ungoverned_operator_summary"
}
JSON

cat > "$BAD_EXACT_RECEIPT" <<JSON
{
  "schema_version": "agent_relay_final_answer_receipt_v1",
  "relay_surface": "agent_relay_final_answer",
  "relay_mode": "exact",
  "target_identity_id": "base-repo-audit-expert-v3",
  "question_tag": "relay-probe-exact-bad",
  "source_artifact": "$SNAPSHOT_JSON",
  "source_snapshot_ts": "2026-03-18T08:00:00Z",
  "relay_text": "Identity-Context: actor_id=assistant:codex; identity_id=base-repo-audit-expert-v3; scope=USER; lock=LOCK_MATCH; source=project | Layer-Context: work_layer=protocol; source_layer=project\nMachine-Verification: verification_source=relay_probe; identity_id=base-repo-audit-expert-v3; prompt_version=v1.6; source_layer=project; verification_status=PASS_REQUIRED\nFINAL_ANSWER=tampered",
  "delivery_authority": "identity_instance_output"
}
JSON

python3 "$ROOT/scripts/validate_agent_relay_final_answer.py" --receipt "$EXACT_RECEIPT" --json-only > "$TMP_ROOT/exact.json"
python3 "$ROOT/scripts/validate_agent_relay_final_answer.py" --receipt "$SUMMARY_RECEIPT" --json-only > "$TMP_ROOT/summary.json"
if python3 "$ROOT/scripts/validate_agent_relay_final_answer.py" --receipt "$BAD_SUMMARY_RECEIPT" --json-only > "$TMP_ROOT/bad_summary.json"; then
  echo "[FAIL] bad summary relay unexpectedly passed"
  exit 1
fi
if python3 "$ROOT/scripts/validate_agent_relay_final_answer.py" --receipt "$BAD_EXACT_RECEIPT" --json-only > "$TMP_ROOT/bad_exact.json"; then
  echo "[FAIL] bad exact relay unexpectedly passed"
  exit 1
fi

python3 - "$TMP_ROOT/exact.json" "$TMP_ROOT/summary.json" "$TMP_ROOT/bad_summary.json" "$TMP_ROOT/bad_exact.json" <<'PY'
import json
import sys
paths = sys.argv[1:]
records = [json.loads(open(path, encoding='utf-8').read()) for path in paths]
exact, summary, bad_summary, bad_exact = records
assert exact["agent_relay_final_answer_status"] == "PASS_REQUIRED", exact
assert summary["agent_relay_final_answer_status"] == "PASS_REQUIRED", summary
assert bad_summary["error_code"] == "IP-RELAY-004", bad_summary
assert bad_exact["error_code"] == "IP-RELAY-003", bad_exact
print(json.dumps({
    "agent_relay_final_answer_probe_status": "PASS_REQUIRED",
    "exact_status": exact["agent_relay_final_answer_status"],
    "summary_status": summary["agent_relay_final_answer_status"],
    "bad_summary_error_code": bad_summary["error_code"],
    "bad_exact_error_code": bad_exact["error_code"],
    "tmp_root": sys.argv[1].rsplit('/', 1)[0],
}, ensure_ascii=False))
PY
