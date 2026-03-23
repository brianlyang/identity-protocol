#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-dialogue-retention-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

PACK_ROOT="${TMP_ROOT}/identity/probe-dialogue-retention"
CATALOG_PATH="${TMP_ROOT}/identity/catalog.local.yaml"
CODEX_HOME_FIXTURE="${TMP_ROOT}/codex-home"
THREAD_ID="019cad9b-f10a-7ba0-9d65-77c3946c03ef-probe"
SOURCE_SESSION_FILE="${CODEX_HOME_FIXTURE}/sessions/2026/03/23/rollout-2026-03-23T00-00-00-${THREAD_ID}.jsonl"
REPLY_FILE="${TMP_ROOT}/verified-reply.txt"
SYNC_JSON="${TMP_ROOT}/dialogue-sync.json"
HOOK_JSON="${TMP_ROOT}/delivery-hook.json"
VALIDATOR_JSON="${TMP_ROOT}/dialogue-validator.json"
POST_VALIDATOR_JSON="${TMP_ROOT}/dialogue-validator-post.json"

mkdir -p "${PACK_ROOT}/runtime" "${PACK_ROOT}/scripts" "$(dirname "${SOURCE_SESSION_FILE}")"

action_python() {
  python3 - "$@"
}

action_python "${REPO_ROOT}" "${PACK_ROOT}" "${CATALOG_PATH}" <<'PY'
import json
import sys
from pathlib import Path
import yaml

repo_root = Path(sys.argv[1]).resolve()
pack_root = Path(sys.argv[2]).resolve()
catalog_path = Path(sys.argv[3]).resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))
from identity_context_continuity_materialization_common import materialize_identity_context_continuity_assets
from identity_dialogue_retention_common import materialize_identity_dialogue_retention_assets

task = {
    "objective": {"title": "dialogue retention probe", "status": "active"},
    "state_machine": {"current_state": "probe_active"},
    "required_validators": [],
}
pack_root.mkdir(parents=True, exist_ok=True)
(pack_root / "CURRENT_TASK.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(pack_root / "scripts" / "emit_current_thread_final_reply.py").write_text(
    "#!/usr/bin/env python3\n# probe emitter install marker\nHOOK='run_identity_delivery_runtime_hooks.py'\ndelivery_hook_result = {}\n",
    encoding="utf-8",
)
materialize_identity_context_continuity_assets(task=task, identity_id=pack_root.name, pack_dir=pack_root, apply=True)
materialize_identity_dialogue_retention_assets(task=task, identity_id=pack_root.name, pack_dir=pack_root, apply=True)
(pack_root / "CURRENT_TASK.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
catalog_doc = {
    "identities": [
        {
            "id": pack_root.name,
            "pack_path": str(pack_root),
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
            "scope": "USER",
        }
    ]
}
catalog_path.write_text(yaml.safe_dump(catalog_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
PY

cat > "${SOURCE_SESSION_FILE}" <<'EOF'
{"type":"session_meta","id":"meta-1"}
{"type":"event_msg","role":"user","content":"hello"}
{"type":"event_msg","role":"assistant","content":"world"}
EOF
cat > "${REPLY_FILE}" <<'EOF'
Identity-Context: actor_id=assistant:codex; identity_id=probe-dialogue-retention; scope=USER; lock=LOCK_MATCH; source=project | Layer-Context: work_layer=instance; source_layer=project
Machine-Verification: authority_source=actor_session_store; identity_id=probe-dialogue-retention; status=active; prompt_version=v1.6; source_layer=project

probe reply body
EOF

CODEX_HOME="${CODEX_HOME_FIXTURE}" CODEX_THREAD_ID="${THREAD_ID}" IDENTITY_PROTOCOL_HOME="${REPO_ROOT}" \
python3 "${REPO_ROOT}/scripts/run_identity_dialogue_retention_guard_runtime.py" \
  --guard-script "${PACK_ROOT}/scripts/emit_current_thread_final_reply.py" \
  --catalog "${CATALOG_PATH}" \
  sync \
  --reply-file "${REPLY_FILE}" \
  --json-only > "${SYNC_JSON}"

python3 "${REPO_ROOT}/scripts/validate_identity_dialogue_retention.py" \
  --identity-id probe-dialogue-retention \
  --catalog "${CATALOG_PATH}" \
  --json-only > "${VALIDATOR_JSON}"

CODEX_HOME="${CODEX_HOME_FIXTURE}" CODEX_THREAD_ID="${THREAD_ID}" IDENTITY_PROTOCOL_HOME="${REPO_ROOT}" \
python3 "${REPO_ROOT}/scripts/run_identity_delivery_runtime_hooks.py" \
  --emitter-script "${PACK_ROOT}/scripts/emit_current_thread_final_reply.py" \
  --catalog "${CATALOG_PATH}" \
  --reply-file "${REPLY_FILE}" \
  --json-only > "${HOOK_JSON}"

python3 "${REPO_ROOT}/scripts/validate_identity_dialogue_retention.py" \
  --identity-id probe-dialogue-retention \
  --catalog "${CATALOG_PATH}" \
  --json-only > "${POST_VALIDATOR_JSON}"

action_python "${PACK_ROOT}" "${SYNC_JSON}" "${HOOK_JSON}" "${VALIDATOR_JSON}" "${POST_VALIDATOR_JSON}" <<'PY'
import json
import sys
from pathlib import Path

pack_root = Path(sys.argv[1]).resolve()
sync_payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
hook_payload = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
validator_payload = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
post_validator_payload = json.loads(Path(sys.argv[5]).read_text(encoding="utf-8"))

guard_state = json.loads((pack_root / "runtime/state/context-continuity/guard-state.json").read_text(encoding="utf-8"))
receipt_doc = json.loads((pack_root / sync_payload["receipt_ref"]).read_text(encoding="utf-8"))

assert sync_payload["status"] == "PASS_REQUIRED", sync_payload
assert sync_payload["source_session_line_count"] == 3, sync_payload
assert receipt_doc["mirror_exact_source_match"] is True, receipt_doc
assert validator_payload["protocol_dialogue_retention_status"] == "PASS_REQUIRED", validator_payload
assert hook_payload["status"] == "PASS_REQUIRED", hook_payload
assert hook_payload["dialogue_retention_status"] == "PASS_REQUIRED", hook_payload
assert hook_payload["context_continuity_status"] == "PASS_REQUIRED", hook_payload
assert hook_payload["pending_reentry_consumption_detected"] is True, hook_payload
assert guard_state["last_action"] == "post-recover", guard_state
assert guard_state["last_reentry_consumption_receipt_ref"], guard_state
assert post_validator_payload["protocol_dialogue_retention_status"] == "PASS_REQUIRED", post_validator_payload
print("[PASS] identity dialogue retention probes passed")
PY
