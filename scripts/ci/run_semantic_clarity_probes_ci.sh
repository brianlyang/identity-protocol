#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
cd "$REPO_ROOT"

source "$REPO_ROOT/scripts/runtime_temp_path_common.sh"
TMP_ROOT="$(identity_runtime_mktemp_dir_sh "semantic-clarity-probes" "run")"
cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

echo "[info] semantic clarity probes: positive lane"
python3 scripts/validate_semantic_term_registry.py --json-only > "$TMP_ROOT/semantic_term_positive.json"
python3 scripts/validate_cli_catalog_default_semantics.py --json-only > "$TMP_ROOT/cli_catalog_positive.json"
python3 scripts/validate_stream_scope_semantic_integrity.py --base HEAD --head HEAD --json-only > "$TMP_ROOT/stream_scope_positive.json"
python3 scripts/validate_runtime_file_boundary_governance.py --json-only > "$TMP_ROOT/runtime_boundary_positive.json"
python3 scripts/validate_compatibility_legacy_boundary.py --json-only > "$TMP_ROOT/compatibility_legacy_boundary_positive.json"
python3 scripts/validate_compiled_brief_projection_boundary.py --json-only > "$TMP_ROOT/compiled_brief_positive.json"
python3 scripts/validate_strict_actor_entry_semantics.py --json-only > "$TMP_ROOT/strict_actor_entry_positive.json"
python3 scripts/validate_response_authority_consumer_semantics.py --json-only > "$TMP_ROOT/authority_consumer_positive.json"
python3 scripts/validate_activate_cwd_invariance.py --json-only > "$TMP_ROOT/activate_cwd_positive.json"

python3 - "$TMP_ROOT/semantic_term_positive.json" "$TMP_ROOT/cli_catalog_positive.json" "$TMP_ROOT/stream_scope_positive.json" "$TMP_ROOT/runtime_boundary_positive.json" "$TMP_ROOT/compatibility_legacy_boundary_positive.json" "$TMP_ROOT/compiled_brief_positive.json" "$TMP_ROOT/strict_actor_entry_positive.json" "$TMP_ROOT/authority_consumer_positive.json" "$TMP_ROOT/activate_cwd_positive.json" <<'PY'
import json,sys
semantic=json.load(open(sys.argv[1]))
cli=json.load(open(sys.argv[2]))
stream=json.load(open(sys.argv[3]))
boundary=json.load(open(sys.argv[4]))
legacy_boundary=json.load(open(sys.argv[5]))
compiled_brief=json.load(open(sys.argv[6]))
strict_actor=json.load(open(sys.argv[7]))
authority=json.load(open(sys.argv[8]))
activate_cwd=json.load(open(sys.argv[9]))
assert semantic.get("semantic_term_registry_status") == "PASS_REQUIRED", semantic
assert cli.get("cli_catalog_default_semantics_status") == "PASS_REQUIRED", cli
assert stream.get("stream_scope_semantic_integrity_status") == "SKIPPED_NOT_REQUIRED", stream
assert boundary.get("runtime_file_boundary_governance_status") == "PASS_REQUIRED", boundary
assert legacy_boundary.get("compatibility_legacy_boundary_status") == "PASS_REQUIRED", legacy_boundary
assert compiled_brief.get("compiled_brief_projection_boundary_status") == "PASS_REQUIRED", compiled_brief
assert compiled_brief.get("top_hard_guard_status") == "PASS_REQUIRED", compiled_brief
assert strict_actor.get("strict_actor_entry_semantics_status") == "PASS_REQUIRED", strict_actor
assert authority.get("response_authority_consumer_semantics_status") == "PASS_REQUIRED", authority
assert activate_cwd.get("activate_cwd_invariance_status") == "PASS_REQUIRED", activate_cwd
print("[PASS] positive semantic clarity lane")
PY

echo "[info] semantic clarity probes: compatibility legacy boundary negative lane"
cat > "$TMP_ROOT/compatibility_legacy_boundary_negative.md" <<'EOF'
legacy_canonical_compatibility_path
EOF
set +e
python3 scripts/validate_compatibility_legacy_boundary.py \
  --extra-forbidden-target "$TMP_ROOT/compatibility_legacy_boundary_negative.md" \
  --json-only > "$TMP_ROOT/compatibility_legacy_boundary_negative.json"
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "[FAIL] compatibility legacy boundary validator should fail when the guarded term appears in a forbidden target"
  exit 1
fi
python3 - "$TMP_ROOT/compatibility_legacy_boundary_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("compatibility_legacy_boundary_status") == "FAIL_REQUIRED", obj
assert any(item.get("reason") == "legacy_compatibility_term_present_in_forbidden_surface" for item in (obj.get("violations") or [])), obj
print("[PASS] compatibility legacy boundary negative lane")
PY

echo "[info] semantic clarity probes: native chat compiled brief freeze"
python3 scripts/compile_identity_runtime.py \
  --catalog "$WORKSPACE_ROOT/.identity/catalog.local.yaml" \
  --identity-id base-repo-closure-orchestrator \
  --actor-id assistant:codex \
  --output "$TMP_ROOT/native_chat_compiled.md"
python3 scripts/validate_compiled_brief_projection_boundary.py \
  --compiled-brief "$TMP_ROOT/native_chat_compiled.md" \
  --json-only > "$TMP_ROOT/native_chat_compiled_boundary.json"
python3 - "$TMP_ROOT/native_chat_compiled_boundary.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("compiled_brief_projection_boundary_status") == "PASS_REQUIRED", obj
assert obj.get("default_machine_profile") == "mini", obj
assert obj.get("top_hard_guard_status") == "PASS_REQUIRED", obj
print("[PASS] native chat compiled brief freeze")
PY
cp "$TMP_ROOT/native_chat_compiled.md" "$TMP_ROOT/native_chat_compiled_missing_tuple_guard.md"
python3 - "$TMP_ROOT/native_chat_compiled_missing_tuple_guard.md" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
token = (
    "- If `CODEX_SESSION_ID` / `IDENTITY_SESSION_ID` is missing, or the current-turn actor/session tuple cannot be "
    "resolved, line 1 and line 2 MUST fall back to the two-line withheld/conflict envelope; never drop the "
    "headstamp completely."
)
if token not in text:
    raise SystemExit("compiled_brief_tuple_guard_missing")
path.write_text(text.replace(token + "\n", "", 1), encoding="utf-8")
PY
set +e
python3 scripts/validate_compiled_brief_projection_boundary.py \
  --compiled-brief "$TMP_ROOT/native_chat_compiled_missing_tuple_guard.md" \
  --json-only > "$TMP_ROOT/native_chat_compiled_missing_tuple_guard_boundary.json"
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "[FAIL] compiled brief validator should fail when tuple-missing failure-envelope rule disappears"
  exit 1
fi
python3 - "$TMP_ROOT/native_chat_compiled_missing_tuple_guard_boundary.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("compiled_brief_projection_boundary_status") == "FAIL_REQUIRED", obj
assert obj.get("top_hard_guard_status") == "FAIL_REQUIRED", obj
assert "compiled_brief_top_reply_hard_guard_missing_or_not_front_loaded" in (obj.get("stale_reasons") or []), obj
print("[PASS] tuple-missing failure-envelope rule required in compiled brief")
PY
cp "$TMP_ROOT/native_chat_compiled.md" "$TMP_ROOT/native_chat_compiled_bad.md"
python3 - "$TMP_ROOT/native_chat_compiled_bad.md" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
marker = "- Failure example line 2:"
replacement = (
    marker
    + " `Machine-Verification: verification_source=<verification_source>; verification_status=FAIL_REQUIRED; "
    "current_pointer_identity_id=<stale_pointer_identity_id>; next_hop_admission_status=FAIL_REQUIRED`"
)
if marker not in text:
    raise SystemExit("compiled_brief_failure_marker_missing")
path.write_text(text.replace(marker + " `Machine-Verification:", replacement, 1), encoding="utf-8")
PY
set +e
python3 scripts/validate_compiled_brief_projection_boundary.py \
  --compiled-brief "$TMP_ROOT/native_chat_compiled_bad.md" \
  --json-only > "$TMP_ROOT/native_chat_compiled_bad_boundary.json"
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "[FAIL] compiled brief validator should fail when stale current_pointer_identity_id leaks into failure envelope"
  exit 1
fi
python3 - "$TMP_ROOT/native_chat_compiled_bad_boundary.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("compiled_brief_projection_boundary_status") == "FAIL_REQUIRED", obj
assert "current_pointer_identity_id=" in (obj.get("forbidden_token_hits") or []), obj
print("[PASS] stale current_pointer_identity_id forbidden in compiled brief")
PY

echo "[info] semantic clarity probes: native chat prompt hard guard"
mkdir -p "$TMP_ROOT/prompt-hard-guard/.identity/alpha"
cat > "$TMP_ROOT/prompt-hard-guard/.identity/catalog.local.yaml" <<'YAML'
identities:
  - id: alpha
    pack_path: __PACK_ROOT__/alpha
    status: active
    profile: runtime
    runtime_mode: local_only
YAML
python3 - "$TMP_ROOT/prompt-hard-guard/.identity/catalog.local.yaml" "$TMP_ROOT/prompt-hard-guard/.identity" <<'PY'
from pathlib import Path
import sys
catalog = Path(sys.argv[1]).resolve()
pack_root = Path(sys.argv[2]).resolve()
catalog.write_text(catalog.read_text(encoding="utf-8").replace("__PACK_ROOT__", str(pack_root)), encoding="utf-8")
PY
cat > "$TMP_ROOT/prompt-hard-guard/.identity/alpha/CURRENT_TASK.json" <<'JSON'
{
  "agent_identity": {
    "role": "alpha-role",
    "prompt_version": "probe-alpha"
  },
  "objective": {
    "title": "Alpha prompt hard guard probe"
  },
  "state_machine": {
    "current_state": "ready"
  },
  "native_chat_headstamp_contract_v1": {
    "required": true,
    "default_machine_profile": "mini",
    "prompt_hard_guard_template_ref": "identity/protocol/plugins/templates/native-chat-headstamp.prompt_hard_guard_v1.json"
  },
  "derived_prompt_conformance_contract_v1": {
    "required": true,
    "validator": "scripts/validate_prompt_derivation_conformance.py",
    "kernel_contract_version": "v1.6",
    "derived_from_contract_ids": [
      "rq_014_prompt_bootstrap_capability_contract_v1",
      "rq_015_prompt_capability_matrix_fail_closed_contract_v1"
    ],
    "fail_action": "block_when_prompt_derivation_metadata_incomplete"
  }
}
JSON
cat > "$TMP_ROOT/prompt-hard-guard/.identity/alpha/IDENTITY_PROMPT.md" <<'MD'
# Identity Prompt: Alpha

## Mission
Keep the prompt minimal before repair.
MD
set +e
python3 scripts/validate_identity_prompt_quality.py \
  --catalog "$TMP_ROOT/prompt-hard-guard/.identity/catalog.local.yaml" \
  --identity-id alpha > "$TMP_ROOT/prompt_hard_guard_negative.log" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "[FAIL] prompt quality validator should fail when native-chat hard guard is missing"
  exit 1
fi
grep -q "Native Chat Headstamp Hard Guard" "$TMP_ROOT/prompt_hard_guard_negative.log"
set +e
python3 scripts/validate_prompt_derivation_conformance.py \
  --catalog "$TMP_ROOT/prompt-hard-guard/.identity/catalog.local.yaml" \
  --identity-id alpha \
  --json-only > "$TMP_ROOT/prompt_hard_guard_derivation_negative.json" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "[FAIL] prompt derivation validator should fail when native-chat contract id is missing from derived metadata"
  exit 1
fi
python3 - "$TMP_ROOT/prompt_hard_guard_derivation_negative.json" <<'PY'
import json
import sys

obj = json.load(open(sys.argv[1], encoding="utf-8"))
assert obj.get("error_code") == "IP-PDER-004", obj
assert "native_chat_prompt_contract_id_missing_from_derived_metadata" in (obj.get("stale_reasons") or []), obj
print("[PASS] native chat prompt derivation metadata hard guard")
PY
python3 scripts/repair_contract_backfill.py \
  --catalog "$TMP_ROOT/prompt-hard-guard/.identity/catalog.local.yaml" \
  --identity-id alpha \
  --apply \
  --json-only > "$TMP_ROOT/prompt_hard_guard_repair.json"
python3 scripts/validate_identity_prompt_quality.py \
  --catalog "$TMP_ROOT/prompt-hard-guard/.identity/catalog.local.yaml" \
  --identity-id alpha > "$TMP_ROOT/prompt_hard_guard_positive.log"
python3 scripts/validate_prompt_derivation_conformance.py \
  --catalog "$TMP_ROOT/prompt-hard-guard/.identity/catalog.local.yaml" \
  --identity-id alpha \
  --json-only > "$TMP_ROOT/prompt_hard_guard_derivation.json"
python3 - "$TMP_ROOT/prompt-hard-guard/.identity/alpha/IDENTITY_PROMPT.md" "$TMP_ROOT/prompt-hard-guard/.identity/alpha/CURRENT_TASK.json" "$TMP_ROOT/prompt_hard_guard_repair.json" "$TMP_ROOT/prompt_hard_guard_derivation.json" <<'PY'
from pathlib import Path
import json
import sys

prompt = Path(sys.argv[1]).read_text(encoding="utf-8")
task = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
repair = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
derivation = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
required = [
    "Native Chat Headstamp Hard Guard",
    "There is no headerless assistant-authored native-chat reply path.",
    "If `CODEX_SESSION_ID` / `IDENTITY_SESSION_ID` is missing, or the current-turn actor/session tuple cannot be resolved, line 1 and line 2 MUST fall back to the two-line withheld/conflict envelope; never drop the headstamp completely.",
    "Failure visible order: `Identity-Context(withheld_or_conflict) -> Machine-Verification(verification_status=FAIL_REQUIRED) -> body`.",
    "Failure line 1 may claim only `requested_identity_id`; it MUST NOT project a success identity when the current-turn machine tuple is missing, conflicted, or polluted.",
    "Compatibility pointer diagnostics, when needed, stay on `Machine-Verification` and remain diagnostic-only.",
]
for token in required:
    if token not in prompt:
        raise SystemExit(f"native_chat_prompt_hard_guard_missing_token: {token}")
if not repair.get("identity_prompt_runtime_governance", {}).get("changed", False):
    raise SystemExit("native_chat_prompt_hard_guard_repair_not_recorded")
derived_ids = ((task.get("derived_prompt_conformance_contract_v1") or {}).get("derived_from_contract_ids") or [])
if "rq_033_native_chat_headstamp_prompt_contract_v1" not in derived_ids:
    raise SystemExit("native_chat_prompt_hard_guard_contract_id_not_backfilled")
restored = repair.get("restored_prompt_contract_list_fields", {})
if "rq_033_native_chat_headstamp_prompt_contract_v1" not in (restored.get("derived_prompt_conformance_contract_v1.derived_from_contract_ids") or []):
    raise SystemExit("native_chat_prompt_hard_guard_contract_id_restore_not_recorded")
if derivation.get("prompt_derivation_conformance_status") != "PASS_REQUIRED":
    raise SystemExit("native_chat_prompt_hard_guard_derivation_not_pass")
print("[PASS] native chat prompt hard guard")
PY

echo "[info] semantic clarity probes: workspace-root strict-entry replay"
(
  cd "$WORKSPACE_ROOT"
  python3 identity-protocol-local/scripts/validate_strict_actor_entry_semantics.py --json-only > "$TMP_ROOT/strict_actor_entry_workspace_root.json"
)
python3 - "$TMP_ROOT/strict_actor_entry_workspace_root.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("strict_actor_entry_semantics_status") == "PASS_REQUIRED", obj
assert obj.get("discovered_surface_file_count", 0) > 0, obj
assert obj.get("discovered_shell_surface_file_count", 0) > 0, obj
print("[PASS] workspace-root strict-entry replay")
PY

echo "[info] semantic clarity probes: authority fallback hardening lane"
mkdir -p "$TMP_ROOT/authority-fallback/.identity/session/actors"
cat > "$TMP_ROOT/authority-fallback/.identity/catalog.local.yaml" <<'YAML'
identities:
  - id: alpha
    pack_path: /tmp/alpha
    status: active
    profile: runtime
    runtime_mode: local_only
  - id: beta
    pack_path: /tmp/beta
    status: active
    profile: runtime
    runtime_mode: local_only
YAML
cat > "$TMP_ROOT/authority-fallback/.identity/session/actors/assistant_codex.json" <<'JSON'
{
  "schema_version": "actor_session_multibinding_v1",
  "actor_id": "assistant:codex",
  "catalog_path": "__CATALOG__",
  "binding_key_mode": "actor_id+identity_id+session_id",
  "binding_version": 2,
  "compare_token": "2",
  "session_entry_count": 1,
  "bindings": [
    {
      "actor_id": "assistant:codex",
      "session_id": "run:alpha",
      "identity_id": "alpha",
      "catalog_path": "__CATALOG__",
      "pack_path": "/tmp/alpha",
      "status": "active",
      "bound_at": "2026-03-17T00:00:00Z",
      "updated_at": "2026-03-17T00:00:00Z",
      "binding_ref": "assistant:codex:alpha:run:alpha:v2",
      "binding_version": 2,
      "compare_token": "2",
      "mutation_lane": "activate",
      "run_id": "alpha",
      "switch_reason": "probe",
      "approved_by": "system:auto"
    }
  ]
}
JSON
cat > "$TMP_ROOT/authority-fallback/.identity/session/active_identity.json" <<'JSON'
{
  "identity_id": "beta",
  "catalog_path": "__CATALOG__",
  "pack_path": "/tmp/beta",
  "status": "active",
  "synced_at": "2026-03-17T00:00:00Z",
  "session_pointer_type": "canonical",
  "authority_role": "compatibility_mirror",
  "authoritative_decision_allowed": false
}
JSON
python3 - "$TMP_ROOT/authority-fallback/.identity/catalog.local.yaml" <<'PY'
from pathlib import Path
import sys
catalog = Path(sys.argv[1]).resolve()
catalog_dir = catalog.parent
for path in [
    catalog_dir / "session" / "actors" / "assistant_codex.json",
    catalog_dir / "session" / "active_identity.json",
]:
    raw = path.read_text(encoding="utf-8")
    raw = raw.replace("__CATALOG__", str(catalog))
    path.write_text(raw, encoding="utf-8")
PY

env -u CODEX_ACTOR_ID python3 scripts/render_identity_response_stamp.py \
  --identity-id alpha \
  --catalog "$TMP_ROOT/authority-fallback/.identity/catalog.local.yaml" \
  --repo-catalog identity/catalog/identities.yaml \
  --json-only > "$TMP_ROOT/authority_fallback_negative.json" || true
python3 - "$TMP_ROOT/authority_fallback_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("identity_authority_status") == "FAIL_REQUIRED", obj
assert obj.get("identity_authority_actor_id", "") == "", obj
assert obj.get("identity_authority_actor_resolution_mode") == "missing", obj
assert obj.get("identity_authority_resolution_mode") == "actor_context_missing", obj
assert "actor_context_missing" in (obj.get("stale_reasons") or []), obj
assert "authoritative_identity_unresolved" in (obj.get("stale_reasons") or []), obj
print("[PASS] non-authoritative compatibility pointer blocked")
PY

CODEX_ACTOR_ID=assistant:codex python3 scripts/render_identity_response_stamp.py \
  --identity-id alpha \
  --catalog "$TMP_ROOT/authority-fallback/.identity/catalog.local.yaml" \
  --repo-catalog identity/catalog/identities.yaml \
  --json-only > "$TMP_ROOT/authority_fallback_missing_session.json" || true
python3 - "$TMP_ROOT/authority_fallback_missing_session.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("identity_authority_status") == "FAIL_REQUIRED", obj
assert obj.get("identity_authority_actor_id") == "assistant:codex", obj
assert obj.get("identity_authority_resolution_mode") == "actor_binding_session_context_missing", obj
assert "session_context_missing:actor_id=assistant:codex" in (obj.get("stale_reasons") or []), obj
assert obj.get("identity_authority_next_action") == "pass_session_id_then_retry", obj
print("[PASS] actor binding without session id cannot drive current-session authority")
PY

CODEX_ACTOR_ID=assistant:codex python3 scripts/render_identity_response_stamp.py \
  --identity-id alpha \
  --catalog "$TMP_ROOT/authority-fallback/.identity/catalog.local.yaml" \
  --repo-catalog identity/catalog/identities.yaml \
  --session-id run:alpha \
  --json-only > "$TMP_ROOT/authority_fallback_positive.json"
python3 - "$TMP_ROOT/authority_fallback_positive.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("identity_id") == "alpha", obj
assert obj.get("identity_authority_status") == "PASS_REQUIRED", obj
assert obj.get("identity_authority_resolution_mode") == "actor_binding_session_scoped", obj
assert "external_stamp" in obj, obj
print("[PASS] env actor + session binding renders headstamp")
PY

echo "[info] semantic clarity probes: foreign project env authority precedence lane"
mkdir -p "$TMP_ROOT/authority-env/codex/.identity" \
  "$TMP_ROOT/authority-env/foreign/.identity" \
  "$TMP_ROOT/authority-env/foreign/identity-protocol-local" \
  "$TMP_ROOT/authority-env/current-no-session/.git" \
  "$TMP_ROOT/authority-env/current-with-session/.git" \
  "$TMP_ROOT/authority-env/current-with-session/identity-protocol-local" \
  "$TMP_ROOT/authority-env/current-with-session/.identity/session"
cat > "$TMP_ROOT/authority-env/codex/.identity/catalog.local.yaml" <<'YAML'
identities:
  - id: global-authority
    pack_path: /tmp/global-authority
    status: active
    profile: runtime
    runtime_mode: local_only
YAML
cat > "$TMP_ROOT/authority-env/foreign/.identity/catalog.local.yaml" <<'YAML'
identities:
  - id: foreign-project-authority
    pack_path: /tmp/foreign-project-authority
    status: active
    profile: runtime
    runtime_mode: local_only
YAML
cat > "$TMP_ROOT/authority-env/current-with-session/.identity/catalog.local.yaml" <<'YAML'
identities:
  - id: current-project-authority
    pack_path: /tmp/current-project-authority
    status: active
    profile: runtime
    runtime_mode: local_only
YAML
cat > "$TMP_ROOT/authority-env/current-with-session/.identity/session/active_identity.json" <<'JSON'
{
  "identity_id": "current-project-authority",
  "status": "active",
  "session_pointer_type": "canonical",
  "authority_role": "compatibility_mirror",
  "authoritative_decision_allowed": false
}
JSON
(
  cd "$TMP_ROOT/authority-env/current-no-session"
  CODEX_HOME="$TMP_ROOT/authority-env/codex" \
  IDENTITY_HOME="$TMP_ROOT/authority-env/foreign/.identity" \
  IDENTITY_CATALOG="$TMP_ROOT/authority-env/foreign/.identity/catalog.local.yaml" \
  IDENTITY_PROTOCOL_HOME="$TMP_ROOT/authority-env/foreign/identity-protocol-local" \
  IDENTITY_ENV_SOURCE=project_runtime_forced \
  python3 "$REPO_ROOT/scripts/resolve_identity_context.py" resolve \
    --identity-id global-authority \
    --repo-catalog "$REPO_ROOT/identity/catalog/identities.yaml" \
    > "$TMP_ROOT/authority_env_global_fallback.json"
)
python3 - "$TMP_ROOT/authority_env_global_fallback.json" "$TMP_ROOT/authority-env/codex/.identity/catalog.local.yaml" <<'PY'
import json,sys
from pathlib import Path
obj=json.load(open(sys.argv[1]))
expected_catalog=str(Path(sys.argv[2]).resolve())
assert obj.get("identity_id") == "global-authority", obj
assert obj.get("source_layer") == "global", obj
assert obj.get("catalog_path") == expected_catalog, obj
print("[PASS] foreign project env ignored when current project has no session pointer")
PY
(
  cd "$TMP_ROOT/authority-env/current-with-session"
  CODEX_HOME="$TMP_ROOT/authority-env/codex" \
  IDENTITY_HOME="$TMP_ROOT/authority-env/foreign/.identity" \
  IDENTITY_CATALOG="$TMP_ROOT/authority-env/foreign/.identity/catalog.local.yaml" \
  IDENTITY_PROTOCOL_HOME="$TMP_ROOT/authority-env/foreign/identity-protocol-local" \
  IDENTITY_ENV_SOURCE=project_runtime_forced \
  python3 "$REPO_ROOT/scripts/resolve_identity_context.py" resolve \
    --identity-id current-project-authority \
    --repo-catalog "$REPO_ROOT/identity/catalog/identities.yaml" \
    > "$TMP_ROOT/authority_env_current_project.json"
)
python3 - "$TMP_ROOT/authority_env_current_project.json" "$TMP_ROOT/authority-env/current-with-session/.identity/catalog.local.yaml" <<'PY'
import json,sys
from pathlib import Path
obj=json.load(open(sys.argv[1]))
expected_catalog=str(Path(sys.argv[2]).resolve())
assert obj.get("identity_id") == "current-project-authority", obj
assert obj.get("source_layer") == "project", obj
assert obj.get("catalog_path") == expected_catalog, obj
print("[PASS] current project session pointer wins over foreign project env")
PY

echo "[info] semantic clarity probes: projection consumer isolation lane"
(
  cd "$WORKSPACE_ROOT"
  python3 identity-protocol-local/scripts/refresh_identity_session_status.py \
    --identity-id alpha \
    --catalog "$TMP_ROOT/authority-fallback/.identity/catalog.local.yaml" \
    --repo-catalog identity/catalog/identities.yaml \
    --actor-id assistant:codex \
    --baseline-policy warn \
    --json-only > "$TMP_ROOT/projection_refresh_workspace_root.json"
  python3 identity-protocol-local/scripts/validate_identity_session_refresh_status.py \
    --identity-id alpha \
    --catalog "$TMP_ROOT/authority-fallback/.identity/catalog.local.yaml" \
    --repo-catalog identity/catalog/identities.yaml \
    --actor-id assistant:codex \
    --baseline-policy warn \
    --operation scan \
    --json-only > "$TMP_ROOT/projection_refresh_validate_workspace_root.json"
)
python3 - "$TMP_ROOT/projection_refresh_workspace_root.json" "$TMP_ROOT/projection_refresh_validate_workspace_root.json" <<'PY'
import json,sys
refresh=json.load(open(sys.argv[1]))
validate=json.load(open(sys.argv[2]))
assert refresh.get("identity_id") == "alpha", refresh
assert refresh.get("actor_id") == "assistant:codex", refresh
assert refresh.get("session_id") == "run:alpha", refresh
assert refresh.get("session_id_source") == "actor_binding_identity", refresh
assert refresh.get("pointer_consistency") == "FAIL", refresh
assert "legacy_pointer_identity_mismatch" in (refresh.get("risk_flags") or []), refresh
assert "actor_binding_missing" not in (refresh.get("risk_flags") or []), refresh
assert validate.get("session_refresh_status") == "WARN_NON_BLOCKING", validate
assert validate.get("actor_id") == "assistant:codex", validate
assert validate.get("session_id") == "run:alpha", validate
assert validate.get("session_id_source") == "actor_binding_identity", validate
assert validate.get("baseline_status") == "WARN", validate
assert validate.get("baseline_error_code") == "IP-PBL-002", validate
assert validate.get("error_code") == "IP-ASB-RFS-002", validate
assert all("can't open file" not in str(reason) for reason in (validate.get("stale_reasons") or [])), validate
print("[PASS] projection consumer isolation replay")
PY

echo "[info] semantic clarity probes: actor-session authority residue repair lane"
mkdir -p "$TMP_ROOT/authority-residue/.identity/session/actors" "$TMP_ROOT/authority-residue/.identity/session/mirror"
cat > "$TMP_ROOT/authority-residue/.identity/catalog.local.yaml" <<'YAML'
identities:
  - id: probe-identity
    pack_path: /tmp/probe-identity
    status: active
    profile: runtime
    runtime_mode: local_only
YAML
cat > "$TMP_ROOT/authority-residue/.identity/session/actors/user_test.json" <<'JSON'
{
  "schema_version": "actor_session_multibinding_v1",
  "actor_id": "user:test",
  "catalog_path": "__CATALOG__",
  "binding_key_mode": "actor_id+identity_id+session_id",
  "binding_version": 3,
  "compare_token": "3",
  "session_entry_count": 1,
  "bindings": [
    {
      "actor_id": "user:test",
      "session_id": "run:probe",
      "identity_id": "probe-identity",
      "catalog_path": "__CATALOG__",
      "pack_path": "/tmp/probe-identity",
      "status": "active",
      "bound_at": "2026-03-17T00:00:00Z",
      "updated_at": "2026-03-17T00:00:00Z",
      "binding_ref": "user:test:probe-identity:run:probe:v3",
      "binding_version": 3,
      "compare_token": "3",
      "mutation_lane": "activate",
      "run_id": "probe",
      "switch_reason": "probe",
      "approved_by": "system:auto"
    }
  ],
  "rebind_receipts": [
    {
      "from_binding_ref": "NONE",
      "to_binding_ref": "user:test:probe-identity:run:probe:v3",
      "actor_id": "user:test",
      "session_id": "run:probe",
      "run_id": "probe",
      "switch_reason": "probe",
      "approved_by": "system:auto",
      "applied_at": "2026-03-17T00:00:00Z"
    }
  ],
  "last_mutation": {
    "mutation_lane": "activate",
    "session_id": "run:probe",
    "run_id": "probe",
    "switch_reason": "probe",
    "approved_by": "system:auto",
    "compare_token_before": "2",
    "compare_token_after": "3",
    "applied_at": "2026-03-17T00:00:00Z"
  }
}
JSON
cat > "$TMP_ROOT/authority-residue/.identity/session/active_identity.json" <<'JSON'
{
  "identity_id": "probe-identity",
  "catalog_path": "__CATALOG__",
  "pack_path": "/tmp/probe-identity",
  "status": "active",
  "synced_at": "2026-03-17T00:00:00Z",
  "session_pointer_type": "canonical"
}
JSON
cat > "$TMP_ROOT/authority-residue/.identity/session/mirror/current.json" <<'JSON'
{
  "identity_id": "probe-identity",
  "catalog_path": "__CATALOG__",
  "pack_path": "/tmp/probe-identity",
  "status": "active",
  "synced_at": "2026-03-17T00:00:00Z",
  "session_pointer_type": "mirror",
  "compatibility_mirror_pointer_path": "__CATALOG_DIR__/session/active_identity.json"
}
JSON
python3 - "$TMP_ROOT/authority-residue/.identity/catalog.local.yaml" <<'PY'
from pathlib import Path
import sys
catalog = Path(sys.argv[1]).resolve()
catalog_dir = catalog.parent
for path in [
    catalog_dir / "session" / "actors" / "user_test.json",
    catalog_dir / "session" / "active_identity.json",
    catalog_dir / "session" / "mirror" / "current.json",
]:
    raw = path.read_text(encoding="utf-8")
    raw = raw.replace("__CATALOG__", str(catalog))
    raw = raw.replace("__CATALOG_DIR__", str(catalog_dir))
    path.write_text(raw, encoding="utf-8")
PY

set +e
python3 scripts/repair_actor_session_authority_residue.py \
  --catalog "$TMP_ROOT/authority-residue/.identity/catalog.local.yaml" \
  --all-actors \
  --json-only > "$TMP_ROOT/authority_residue_negative.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected authority residue pre-repair probe to fail"
  exit 1
fi
python3 - "$TMP_ROOT/authority_residue_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("actor_session_authority_residue_status") == "FAIL_REQUIRED", obj
assert obj.get("actor_store_residue_count", 0) >= 1, obj
assert obj.get("pointer_residue_count", 0) >= 1, obj
print("[PASS] authority residue negative probe blocked")
PY

python3 scripts/repair_actor_session_authority_residue.py \
  --catalog "$TMP_ROOT/authority-residue/.identity/catalog.local.yaml" \
  --all-actors \
  --apply \
  --json-only > "$TMP_ROOT/authority_residue_apply.json"
python3 scripts/validate_actor_session_multibinding_concurrency.py \
  --catalog "$TMP_ROOT/authority-residue/.identity/catalog.local.yaml" \
  --actor-id user:test \
  --session-id run:probe \
  --operation ci \
  --json-only > "$TMP_ROOT/authority_residue_validate.json"
python3 - "$TMP_ROOT/authority_residue_apply.json" "$TMP_ROOT/authority_residue_validate.json" "$TMP_ROOT/authority-residue/.identity/session/active_identity.json" <<'PY'
import json,sys
apply_obj=json.load(open(sys.argv[1]))
validate_obj=json.load(open(sys.argv[2]))
pointer=json.load(open(sys.argv[3]))
assert apply_obj.get("actor_session_authority_residue_status") == "PASS_REQUIRED", apply_obj
assert apply_obj.get("applied_actor_store_count", 0) >= 1, apply_obj
assert apply_obj.get("applied_pointer_count", 0) >= 1, apply_obj
assert validate_obj.get("actor_session_multibinding_status") == "PASS_REQUIRED", validate_obj
assert validate_obj.get("last_mutation_projection_scope") == "session_primary", validate_obj
assert pointer.get("authority_role") == "compatibility_mirror", pointer
assert pointer.get("authoritative_decision_allowed") is False, pointer
assert pointer.get("status") == "active", pointer
assert pointer.get("identity_id") == "probe-identity", pointer
assert pointer.get("session_primary_truth_available") is True, pointer
assert pointer.get("session_primary_session_id") == "run:probe", pointer
assert pointer.get("compatibility_projection_scope") == "", pointer
assert pointer.get("compatibility_projection_role") == "", pointer
assert pointer.get("compatibility_projection_actor_id") == "", pointer
assert pointer.get("compatibility_projection_identity_id") == "", pointer
assert pointer.get("compatibility_projection_session_id") == "", pointer
print("[PASS] authority residue repair lane")
PY

echo "[info] semantic clarity probes: cross-session compatibility projection drift lane"
mkdir -p "$TMP_ROOT/cross-session-drift/.identity/session/mirror" "$TMP_ROOT/cross-session-drift/.identity/session/actors"
mkdir -p "$TMP_ROOT/cross-session-drift/.identity/alpha" "$TMP_ROOT/cross-session-drift/.identity/beta"
mkdir -p "$TMP_ROOT/cross-session-drift/identity-protocol-local"
cat > "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" <<'YAML'
identities:
  - id: alpha
    pack_path: __PACK_ROOT__/alpha
    status: active
    profile: runtime
    runtime_mode: local
  - id: beta
    pack_path: __PACK_ROOT__/beta
    status: active
    profile: runtime
    runtime_mode: local
YAML
python3 - "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" "$TMP_ROOT/cross-session-drift/.identity" <<'PY'
from pathlib import Path
import sys
catalog = Path(sys.argv[1]).resolve()
pack_root = Path(sys.argv[2]).resolve()
raw = catalog.read_text(encoding="utf-8")
catalog.write_text(raw.replace("__PACK_ROOT__", str(pack_root)), encoding="utf-8")
PY
cat > "$TMP_ROOT/cross-session-drift/.identity/alpha/CURRENT_TASK.json" <<'JSON'
{
  "agent_identity": {
    "role": "alpha-role",
    "prompt_version": "probe-alpha"
  },
  "objective": {
    "title": "Alpha compile probe"
  },
  "state_machine": {
    "current_state": "ready"
  },
  "native_chat_headstamp_contract_v1": {
    "default_machine_profile": "mini"
  }
}
JSON
cat > "$TMP_ROOT/cross-session-drift/.identity/beta/CURRENT_TASK.json" <<'JSON'
{
  "agent_identity": {
    "role": "beta-role",
    "prompt_version": "probe-beta"
  },
  "objective": {
    "title": "Beta compile probe"
  },
  "state_machine": {
    "current_state": "ready"
  },
  "native_chat_headstamp_contract_v1": {
    "default_machine_profile": "audit"
  }
}
JSON
python3 scripts/sync_session_identity.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --identity-id alpha \
  --actor-id assistant:codex \
  --session-id run:alpha \
  --session-id-source explicit_session_id \
  --run-id alpha \
  --compare-token 0 \
  --mutation-lane activate > "$TMP_ROOT/cross_session_alpha_sync.log"
python3 - "$TMP_ROOT/cross_session_alpha_sync.log" "$TMP_ROOT/cross-session-drift/.identity/session/active_identity.json" <<'PY'
from pathlib import Path
import json
import sys
log = Path(sys.argv[1]).read_text(encoding="utf-8")
pointer = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert "canonical compatibility pointer neutralized: reason=compatibility_projection_write_disabled_by_policy" in log, log
assert pointer.get("identity_id") == "", pointer
assert pointer.get("status") == "compatibility_projection_unavailable", pointer
assert pointer.get("compatibility_projection_status") == "UNAVAILABLE", pointer
assert pointer.get("compatibility_projection_reason") == "projection_missing", pointer
assert pointer.get("compatibility_projection_write_allowed") is False, pointer
assert pointer.get("compatibility_projection_write_reason") == "compatibility_projection_write_disabled_by_policy", pointer
print("[PASS] bootstrap compatibility pointer neutralized when policy disables projection writes")
PY
set +e
python3 scripts/validate_identity_session_pointer_consistency.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --identity-id alpha \
  --actor-id assistant:codex \
  --session-id run:alpha \
  --strict-session-primary > "$TMP_ROOT/cross_session_alpha_pointer.log" 2>&1
rc=$?
set -e
if [[ "$rc" -ne 0 ]]; then
  echo "[FAIL] expected alpha strict pointer validation to pass before competing session is added"
  cat "$TMP_ROOT/cross_session_alpha_pointer.log"
  exit 1
fi
python3 - "$TMP_ROOT/cross_session_alpha_pointer.log" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
assert "compatibility_projection_drift=yes" in text, text
assert "projection_status=UNAVAILABLE" in text, text
assert "projection_session=<none>" in text, text
print("[PASS] strict pointer validation acknowledges unavailable projection under disabled-write policy")
PY

python3 scripts/sync_session_identity.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --identity-id beta \
  --actor-id assistant:codex \
  --session-id run:beta \
  --session-id-source explicit_session_id \
  --run-id beta \
  --compare-token 1 \
  --switch-prestate-mode session_primary \
  --switch-from-identity "" \
  --mutation-lane activate > "$TMP_ROOT/cross_session_beta_unapproved.log"
python3 - "$TMP_ROOT/cross_session_beta_unapproved.log" "$TMP_ROOT/cross-session-drift/.identity/session/active_identity.json" "$TMP_ROOT/cross-session-drift/.identity/session/actors/assistant_codex.json" <<'PY'
from pathlib import Path
import json
import sys
log = Path(sys.argv[1]).read_text(encoding="utf-8")
pointer = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
actor_store = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
beta = next(
    item for item in actor_store.get("bindings", [])
    if item.get("session_id") == "run:beta" and item.get("identity_id") == "beta"
)
assert "canonical compatibility pointer neutralized: reason=compatibility_projection_write_disabled_by_policy" in log, log
assert pointer.get("identity_id") == "", pointer
assert pointer.get("status") == "compatibility_projection_unavailable", pointer
assert beta.get("compatibility_projection_allowed") is False, beta
assert beta.get("compatibility_projection_reason") == "compatibility_projection_write_disabled_by_policy", beta
print("[PASS] unapproved cross-session activate cannot re-enable compatibility projection when writes are disabled")
PY

cat > "$TMP_ROOT/cross-session-drift/switch-alpha-to-beta.json" <<'JSON'
{
  "receipt_id": "switch-alpha-to-beta",
  "actor_id": "assistant:codex",
  "from_identity_id": "alpha",
  "to_identity_id": "beta",
  "approved_by": "system:test",
  "approved_at": "2026-03-18T00:00:00Z",
  "reason": "semantic-clarity-cross-session-drift-probe"
}
JSON
python3 scripts/sync_session_identity.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --identity-id beta \
  --actor-id assistant:codex \
  --session-id run:beta-switch \
  --session-id-source explicit_session_id \
  --run-id beta-switch \
  --compare-token 2 \
  --switch-intent-receipt "$TMP_ROOT/cross-session-drift/switch-alpha-to-beta.json" \
  --switch-prestate-mode session_primary \
  --switch-from-identity "" \
  --mutation-lane activate > "$TMP_ROOT/cross_session_beta_sync.log"
python3 - "$TMP_ROOT/cross_session_beta_sync.log" "$TMP_ROOT/cross-session-drift/.identity/session/active_identity.json" "$TMP_ROOT/cross-session-drift/.identity/session/actors/assistant_codex.json" <<'PY'
from pathlib import Path
import json
import sys
log = Path(sys.argv[1]).read_text(encoding="utf-8")
pointer = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
actor_store = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
alpha = next(
    item for item in actor_store.get("bindings", [])
    if item.get("session_id") == "run:alpha" and item.get("identity_id") == "alpha"
)
beta = next(
    item for item in actor_store.get("bindings", [])
    if item.get("session_id") == "run:beta-switch" and item.get("identity_id") == "beta"
)
assert "canonical compatibility pointer neutralized: reason=compatibility_projection_write_disabled_by_policy" in log, log
assert pointer.get("identity_id") == "", pointer
assert pointer.get("status") == "compatibility_projection_unavailable", pointer
assert beta.get("compatibility_projection_allowed") is False, beta
assert beta.get("compatibility_projection_reason") == "compatibility_projection_write_disabled_by_policy", beta
assert alpha.get("compatibility_projection_allowed") is False, alpha
assert alpha.get("compatibility_projection_reason") == "compatibility_projection_write_disabled_by_policy", alpha
print("[PASS] approved cross-session switch still preserves unavailable compatibility projection under disabled-write policy")
PY

python3 scripts/validate_identity_session_pointer_consistency.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --identity-id beta \
  --actor-id assistant:codex \
  --session-id run:beta-switch \
  --strict-session-primary > "$TMP_ROOT/cross_session_pointer_positive.log"
python3 - "$TMP_ROOT/cross_session_pointer_positive.log" "$TMP_ROOT/cross-session-drift/.identity/session/active_identity.json" <<'PY'
from pathlib import Path
import json
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
pointer = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert "compatibility_projection_drift=yes" in text, text
assert "projection_status=UNAVAILABLE" in text, text
assert "projection_session=<none>" in text, text
assert pointer.get("identity_id", "") == "", pointer
assert pointer.get("status") == "compatibility_projection_unavailable", pointer
print("[PASS] strict pointer validation acknowledges unavailable projection after approved cross-session switch")
PY

echo "[info] semantic clarity probes: session-primary authority resolver lane"
python3 scripts/resolve_runtime_authoritative_identity.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --actor-id assistant:codex \
  --session-id run:alpha \
  --json-only > "$TMP_ROOT/cross_session_authority_resolver_positive.json"
python3 - "$TMP_ROOT/cross_session_authority_resolver_positive.json" <<'PY'
import json
import sys
obj = json.load(open(sys.argv[1], encoding="utf-8"))
assert obj.get("runtime_authoritative_identity_status") == "PASS_REQUIRED", obj
assert obj.get("authoritative_identity_id") == "alpha", obj
assert obj.get("resolution_mode") == "actor_binding_session_scoped", obj
print("[PASS] session-primary authority resolver returns the bound session identity")
PY
set +e
python3 scripts/resolve_runtime_authoritative_identity.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --actor-id assistant:codex \
  --session-id run:alpha \
  --identity-id beta \
  --json-only > "$TMP_ROOT/cross_session_authority_resolver_negative.json" 2>&1
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] session-primary authority resolver should fail-close on explicit identity mismatch"
  cat "$TMP_ROOT/cross_session_authority_resolver_negative.json"
  exit 1
fi
python3 - "$TMP_ROOT/cross_session_authority_resolver_negative.json" <<'PY'
import json
import sys
obj = json.load(open(sys.argv[1], encoding="utf-8"))
assert obj.get("runtime_authoritative_identity_status") == "FAIL_REQUIRED", obj
assert any(str(reason).startswith("identity_authority_mismatch:") for reason in (obj.get("stale_reasons") or [])), obj
print("[PASS] session-primary authority resolver blocks explicit identity mismatch")
PY

echo "[info] semantic clarity probes: compile runtime session-primary lane"
python3 scripts/compile_identity_runtime.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --actor-id assistant:codex \
  --session-id run:alpha \
  --output "$TMP_ROOT/cross-session-drift/compiled-alpha.md"
python3 scripts/validate_compiled_brief_projection_boundary.py \
  --compiled-brief "$TMP_ROOT/cross-session-drift/compiled-alpha.md" \
  --json-only > "$TMP_ROOT/cross_session_compile_positive.json"
python3 - "$TMP_ROOT/cross_session_compile_positive.json" <<'PY'
import json
import sys
obj = json.load(open(sys.argv[1], encoding="utf-8"))
assert obj.get("compiled_brief_projection_boundary_status") == "PASS_REQUIRED", obj
assert obj.get("default_machine_profile") == "mini", obj
assert obj.get("top_hard_guard_status") == "PASS_REQUIRED", obj
print("[PASS] compile runtime follows session-primary contract source without projecting a stale success identity")
PY
set +e
python3 scripts/compile_identity_runtime.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --actor-id assistant:codex \
  --output "$TMP_ROOT/cross-session-drift/compiled-ambiguous.md" > "$TMP_ROOT/cross_session_compile_ambiguous.log" 2>&1
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] compile runtime should fail-close when actor has multiple session-primary identities and no session-id"
  cat "$TMP_ROOT/cross_session_compile_ambiguous.log"
  exit 1
fi
python3 - "$TMP_ROOT/cross_session_compile_ambiguous.log" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
assert "actor has multiple session-primary identities; pass --session-id or --identity-id explicitly" in text, text
print("[PASS] compile runtime fail-closes on ambiguous actor-only resolution")
PY

cat > "$TMP_ROOT/cross-session-drift/inspection-override.json" <<'JSON'
{"receipt_id":"inspection-override","reason":"semantic-clarity-observation-lane-probe"}
JSON
python3 scripts/sync_session_identity.py \
  --catalog "$TMP_ROOT/cross-session-drift/.identity/catalog.local.yaml" \
  --identity-id beta \
  --actor-id assistant:codex \
  --session-id run:inspection \
  --session-id-source explicit_session_id \
  --run-id inspection \
  --compare-token 3 \
  --mutation-lane inspection \
  --governance-override-receipt "$TMP_ROOT/cross-session-drift/inspection-override.json" > "$TMP_ROOT/cross_session_inspection.log"
python3 - "$TMP_ROOT/cross_session_inspection.log" "$TMP_ROOT/cross-session-drift/.identity/session/active_identity.json" <<'PY'
from pathlib import Path
import json
import sys
log = Path(sys.argv[1]).read_text(encoding="utf-8")
pointer = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert "canonical pointer write skipped: reason=non_activate_lane_observation_only" in log, log
assert "non_activate_lane_observation_only" in log, log
assert pointer.get("identity_id") == "", pointer
assert pointer.get("status") == "compatibility_projection_unavailable", pointer
print("[PASS] observation lane cannot mutate canonical pointer while projection writes remain disabled")
PY

echo "[info] semantic clarity probes: cross-layer uniqueness lane"
mkdir -p "$TMP_ROOT/cross-layer-uniqueness/project/.identity" "$TMP_ROOT/cross-layer-uniqueness/global/.identity"
cat > "$TMP_ROOT/cross-layer-uniqueness/project/.identity/catalog.local.yaml" <<'YAML'
identities:
  - id: base-repo-architect
    pack_path: /tmp/base-repo-architect-project
    status: active
    profile: runtime
    runtime_mode: local_only
YAML
cat > "$TMP_ROOT/cross-layer-uniqueness/global/.identity/catalog.local.yaml" <<'YAML'
identities:
  - id: base-repo-architect
    pack_path: /tmp/base-repo-architect-global
    status: inactive
    profile: runtime
    runtime_mode: local_only
YAML
cat > "$TMP_ROOT/cross-layer-uniqueness/repo-catalog.yaml" <<'YAML'
identities: []
YAML
set +e
CODEX_HOME="$TMP_ROOT/cross-layer-uniqueness/global" \
python3 scripts/validate_identity_scope_isolation.py \
  --catalog "$TMP_ROOT/cross-layer-uniqueness/project/.identity/catalog.local.yaml" \
  --repo-catalog "$TMP_ROOT/cross-layer-uniqueness/repo-catalog.yaml" \
  --identity-id base-repo-architect \
  --json-only > "$TMP_ROOT/cross_layer_uniqueness_negative.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected cross-layer uniqueness validator to block duplicate runtime identity id"
  exit 1
fi
python3 - "$TMP_ROOT/cross_layer_uniqueness_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("scope_isolation_status") == "FAIL_REQUIRED", obj
assert obj.get("runtime_duplicate_detected") is True, obj
assert "cross_layer_runtime_identity_id_duplicate_detected" in (obj.get("stale_reasons") or []), obj
print("[PASS] cross-layer uniqueness validator blocks runtime duplicate")
PY

set +e
CODEX_HOME="$TMP_ROOT/cross-layer-uniqueness/global" \
python3 scripts/repair_identity_cross_layer_uniqueness.py \
  --project-catalog "$TMP_ROOT/cross-layer-uniqueness/project/.identity/catalog.local.yaml" \
  --global-catalog "$TMP_ROOT/cross-layer-uniqueness/global/.identity/catalog.local.yaml" \
  --repo-catalog "$TMP_ROOT/cross-layer-uniqueness/repo-catalog.yaml" \
  --identity-id base-repo-architect \
  --prefer-layer project \
  --json-only > "$TMP_ROOT/cross_layer_uniqueness_repair_check.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected repair check mode to report duplicate before apply"
  exit 1
fi
CODEX_HOME="$TMP_ROOT/cross-layer-uniqueness/global" \
python3 scripts/repair_identity_cross_layer_uniqueness.py \
  --project-catalog "$TMP_ROOT/cross-layer-uniqueness/project/.identity/catalog.local.yaml" \
  --global-catalog "$TMP_ROOT/cross-layer-uniqueness/global/.identity/catalog.local.yaml" \
  --repo-catalog "$TMP_ROOT/cross-layer-uniqueness/repo-catalog.yaml" \
  --identity-id base-repo-architect \
  --prefer-layer project \
  --apply \
  --json-only > "$TMP_ROOT/cross_layer_uniqueness_repair_apply.json"
CODEX_HOME="$TMP_ROOT/cross-layer-uniqueness/global" \
python3 scripts/validate_identity_scope_isolation.py \
  --catalog "$TMP_ROOT/cross-layer-uniqueness/project/.identity/catalog.local.yaml" \
  --repo-catalog "$TMP_ROOT/cross-layer-uniqueness/repo-catalog.yaml" \
  --identity-id base-repo-architect \
  --json-only > "$TMP_ROOT/cross_layer_uniqueness_positive.json"
python3 - "$TMP_ROOT/cross_layer_uniqueness_repair_check.json" "$TMP_ROOT/cross_layer_uniqueness_repair_apply.json" "$TMP_ROOT/cross_layer_uniqueness_positive.json" "$TMP_ROOT/cross-layer-uniqueness/global/.identity/catalog.local.yaml" <<'PY'
import json,sys,yaml
check=json.load(open(sys.argv[1]))
apply=json.load(open(sys.argv[2]))
positive=json.load(open(sys.argv[3]))
global_doc=yaml.safe_load(open(sys.argv[4])) or {}
archive=global_doc.get("identity_uniqueness_archive") or []
assert check.get("status") == "FAIL_REQUIRED", check
assert apply.get("status") == "PASS_REQUIRED", apply
assert positive.get("scope_isolation_status") == "PASS_REQUIRED", positive
assert positive.get("runtime_duplicate_detected") is False, positive
assert len(global_doc.get("identities") or []) == 0, global_doc
assert len(archive) == 1, global_doc
assert archive[0].get("identity_id") == "base-repo-architect", archive
print("[PASS] cross-layer uniqueness repair archives and removes duplicate layer entry")
PY

echo "[info] semantic clarity probes: negative lane (semantic term forbidden phrase)"
mkdir -p "$TMP_ROOT/neg-semantic/docs"
cat > "$TMP_ROOT/neg-semantic/docs/probe.md" <<'MD'
This sentence says: multi-active state is a protocol violation.
MD
cat > "$TMP_ROOT/neg-semantic/semantic-term-registry.current.yaml" <<'YAML'
schema_version: 1
pointer_version: v1
active_file: semantic-term-registry.v1.yaml
YAML
cat > "$TMP_ROOT/neg-semantic/semantic-term-registry.v1.yaml" <<'YAML'
schema_version: 1
registry_version: test
stream_version: v1.6
terms:
  - term_id: catalog_multi_active
    canonical_term: catalog_multi_active
    semantics: ok
    allowed_scope: [catalog]
forbidden_phrases:
  - phrase: "multi-active state is a protocol violation"
    replacement: "catalog_multi_active is allowed"
scan_roots:
  - docs/probe.md
include_active_stream_docs: false
YAML

set +e
python3 scripts/validate_semantic_term_registry.py \
  --repo-root "$TMP_ROOT/neg-semantic" \
  --registry semantic-term-registry.current.yaml \
  --json-only > "$TMP_ROOT/semantic_term_negative.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected semantic term forbidden-phrase probe to fail"
  exit 1
fi
python3 - "$TMP_ROOT/semantic_term_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-SEMREG-001", obj
assert "forbidden_phrase_detected" in (obj.get("stale_reasons") or []), obj
print("[PASS] negative semantic term forbidden phrase blocked")
PY

echo "[info] semantic clarity probes: negative lane (instance debt ownership forbidden phrase)"
mkdir -p "$TMP_ROOT/neg-semantic-instance/docs"
cat > "$TMP_ROOT/neg-semantic-instance/docs/probe.md" <<'MD'
This sentence says: protocol will backstop instance technical debt.
MD
cat > "$TMP_ROOT/neg-semantic-instance/semantic-term-registry.current.yaml" <<'YAML'
schema_version: 1
pointer_version: v1
active_file: semantic-term-registry.v1.yaml
YAML
cat > "$TMP_ROOT/neg-semantic-instance/semantic-term-registry.v1.yaml" <<'YAML'
schema_version: 1
registry_version: test
stream_version: v1.6
terms:
  - term_id: instance_owned_technical_debt
    canonical_term: instance_owned_technical_debt
    semantics: ok
    allowed_scope: [instance_runtime]
  - term_id: instance_clean_proof
    canonical_term: instance_clean_proof
    semantics: ok
    allowed_scope: [review_acceptance]
  - term_id: protocol_residual_issue
    canonical_term: protocol_residual_issue
    semantics: ok
    allowed_scope: [governance]
forbidden_phrases:
  - phrase: "protocol will backstop instance technical debt"
    replacement: "instance_owned_technical_debt remains instance-owned; protocol_residual_issue starts only after instance_clean_proof"
scan_roots:
  - docs/probe.md
include_active_stream_docs: false
YAML
set +e
python3 scripts/validate_semantic_term_registry.py \
  --repo-root "$TMP_ROOT/neg-semantic-instance" \
  --registry semantic-term-registry.current.yaml \
  --json-only > "$TMP_ROOT/semantic_term_instance_negative.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected instance debt ownership forbidden-phrase probe to fail"
  exit 1
fi
python3 - "$TMP_ROOT/semantic_term_instance_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-SEMREG-001", obj
assert "forbidden_phrase_detected" in (obj.get("stale_reasons") or []), obj
print("[PASS] negative instance debt ownership forbidden phrase blocked")
PY

echo "[info] semantic clarity probes: negative lane (runtime catalog default fallback)"
mkdir -p "$TMP_ROOT/neg-cli/scripts"
cat > "$TMP_ROOT/neg-cli/scripts/bad.py" <<'PY'
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
PY
set +e
python3 scripts/validate_cli_catalog_default_semantics.py \
  --repo-root "$TMP_ROOT/neg-cli" \
  --scripts-root scripts \
  --json-only > "$TMP_ROOT/cli_catalog_negative.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected cli catalog default semantics probe to fail"
  exit 1
fi
python3 - "$TMP_ROOT/cli_catalog_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-CLICAT-001", obj
assert obj.get("runtime_catalog_repo_fixture_default_hits"), obj
print("[PASS] negative cli catalog fallback blocked")
PY

echo "[info] semantic clarity probes: negative lane (runtime boundary missing required tokens)"
mkdir -p "$TMP_ROOT/neg-boundary/docs/governance" "$TMP_ROOT/neg-boundary/docs/review" "$TMP_ROOT/neg-boundary/identity/protocol/mappings" "$TMP_ROOT/neg-boundary/identity/protocol"
cat > "$TMP_ROOT/neg-boundary/docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md" <<'MD'
# broken doc
This text wrongly says all protocol-governed instance runtime files under `runtime/state`, `runtime/gate`, `runtime/plugins`, and `runtime/protocol-feedback`.
MD
cat > "$TMP_ROOT/neg-boundary/docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md" <<'MD'
# broken review
missing boundary tokens on purpose
MD
cat > "$TMP_ROOT/neg-boundary/identity/protocol/IDENTITY_PROTOCOL.md" <<'MD'
# broken protocol overview
protocol will backstop instance technical debt
MD
cat > "$TMP_ROOT/neg-boundary/identity/protocol/mappings/stream-doc-registry.current.yaml" <<'YAML'
schema_version: 1
pointer_version: v1
active_file: identity/protocol/mappings/stream-doc-registry.v1.yaml
YAML
cat > "$TMP_ROOT/neg-boundary/identity/protocol/mappings/stream-doc-registry.v1.yaml" <<'YAML'
schema_version: 1
version: v1.6
stream_docs:
  - stream_version: v1.6.10
    governance_doc: docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md
    review_doc: docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md
legacy_archival_docs: []
YAML
cat > "$TMP_ROOT/neg-boundary/identity/protocol/mappings/semantic-term-registry.current.yaml" <<'YAML'
schema_version: 1
pointer_version: v1
active_file: identity/protocol/mappings/semantic-term-registry.v1.yaml
YAML
cat > "$TMP_ROOT/neg-boundary/identity/protocol/mappings/semantic-term-registry.v1.yaml" <<'YAML'
schema_version: 1
registry_version: test
stream_version: v1.6
terms:
  - term_id: protocol_generated_gateway_shell
    canonical_term: protocol_generated_gateway_shell
    semantics: ok
    allowed_scope: [runtime_gate]
  - term_id: protocol_controlled_mirror_artifact
    canonical_term: protocol_controlled_mirror_artifact
    semantics: ok
    allowed_scope: [runtime_gate]
  - term_id: instance_autonomous_runtime
    canonical_term: instance_autonomous_runtime
    semantics: ok
    allowed_scope: [instance_runtime]
  - term_id: instance_owned_technical_debt
    canonical_term: instance_owned_technical_debt
    semantics: ok
    allowed_scope: [instance_runtime]
  - term_id: instance_clean_proof
    canonical_term: instance_clean_proof
    semantics: ok
    allowed_scope: [review_acceptance]
  - term_id: protocol_residual_issue
    canonical_term: protocol_residual_issue
    semantics: ok
    allowed_scope: [governance]
forbidden_phrases: []
scan_roots: []
include_active_stream_docs: false
YAML
set +e
python3 scripts/validate_runtime_file_boundary_governance.py \
  --repo-root "$TMP_ROOT/neg-boundary" \
  --json-only > "$TMP_ROOT/runtime_boundary_negative.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected runtime boundary governance probe to fail"
  exit 1
fi
python3 - "$TMP_ROOT/runtime_boundary_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-RFILE-BDRY-001", obj
assert (
    "governance_doc_missing_required_tokens" in (obj.get("stale_reasons") or [])
    or "protocol_overview_missing_required_tokens" in (obj.get("stale_reasons") or [])
), obj
print("[PASS] negative runtime boundary missing-token probe blocked")
PY

echo "[info] semantic clarity probes: negative lane (authority consumer drift)"
mkdir -p "$TMP_ROOT/neg-authority/scripts"
cat > "$TMP_ROOT/neg-authority/scripts/bad_authority_consumer.py" <<'PY'
from actor_session_common import resolve_actor_id
from response_stamp_common import resolve_stamp_context

def bad(args, catalog_path, repo_catalog_path):
    ctx = resolve_stamp_context(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
    )
    actor = resolve_actor_id(args.actor_id)
    resolver_ref = f"{catalog_path.parent}/session/active_identity.json"
    return ctx, actor, resolver_ref
PY
set +e
python3 scripts/validate_response_authority_consumer_semantics.py \
  --repo-root "$TMP_ROOT/neg-authority" \
  --scan-file scripts/bad_authority_consumer.py \
  --json-only > "$TMP_ROOT/authority_consumer_negative.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected authority consumer drift probe to fail"
  exit 1
fi
python3 - "$TMP_ROOT/authority_consumer_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-HDSTAMP-CONSUMER-001", obj
reasons=set(obj.get("stale_reasons") or [])
assert "authority_consumer_registry_coverage_missing" in reasons, obj
assert "stamp_context_session_passthrough_missing" in reasons, obj
assert "host_fallback_actor_resolver_forbidden" in reasons, obj
assert "compatibility_pointer_literal_forbidden" in reasons, obj
print("[PASS] negative authority consumer drift probe blocked")
PY

echo "[info] semantic clarity probes: negative lane (strict actor entry fallback)"
mkdir -p "$TMP_ROOT/neg-strict-actor/scripts"
cat > "$TMP_ROOT/neg-strict-actor/scripts/bad_strict_actor_entry.py" <<'PY'
import argparse
import os
from actor_session_common import resolve_actor_id

ap = argparse.ArgumentParser()
ap.add_argument("--actor-id", default=os.environ.get("CODEX_ACTOR_ID", "assistant:codex"))
ap.add_argument("--project-catalog", default="identity/catalog/identities.yaml")

def run():
    actor = resolve_actor_id("")
    cmd = [
        "python3",
        "scripts/full_identity_protocol_scan.py",
        "--project-catalog",
        "identity/catalog/identities.yaml",
        "--actor-id",
        actor,
    ]
    return cmd
PY
cat > "$TMP_ROOT/neg-strict-actor/scripts/bad_strict_shell_entry.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

CATALOG_PATH="${CATALOG_PATH:-identity/catalog/identities.yaml}"
HEADSTAMP_ACTOR_ID="${HEADSTAMP_ACTOR_ID:-${CODEX_ACTOR_ID:-assistant:codex}}"
python3 scripts/full_identity_protocol_scan.py \
  --project-catalog "${CATALOG_PATH}" \
  --actor-id "${HEADSTAMP_ACTOR_ID}"
SH
cat > "$TMP_ROOT/neg-strict-actor/scripts/run_native_chat_headstamp_smoke.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

source ./scripts/shell_strict_entry_common.sh
CATALOG_PATH="$(protocol_shell_entry_resolve_project_catalog "${CATALOG_PATH:-}")"
EXPECTED_ACTOR_ID="$(protocol_shell_entry_require_actor_id "${HEADSTAMP_ACTOR_ID:-}")"
EXPECTED_SESSION_ID="$(protocol_shell_entry_require_session_id "${HEADSTAMP_SESSION_ID:-}")"
IDENTITY_ID="$(protocol_shell_entry_resolve_session_primary_identity "${CATALOG_PATH}" "${EXPECTED_ACTOR_ID}" "${EXPECTED_SESSION_ID}" "${IDENTITY_ID:-probe}")"
python3 - <<'PY'
import os
import subprocess

env = os.environ.copy()
cmd = ["codex", "exec", "--ephemeral", "--output-last-message", "/tmp/probe.txt", "probe"]
subprocess.run(cmd, env=env, check=False)
PY
SH
set +e
python3 scripts/validate_strict_actor_entry_semantics.py \
  --repo-root "$TMP_ROOT/neg-strict-actor" \
  --scripts-root scripts \
  --json-only > "$TMP_ROOT/strict_actor_entry_negative.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected strict actor entry fallback probe to fail"
  exit 1
fi
python3 - "$TMP_ROOT/strict_actor_entry_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-ACTOR-ENTRY-SEM-001", obj
reasons=set(obj.get("stale_reasons") or [])
assert "strict_actor_default_literal_forbidden" in reasons, obj
assert "strict_project_catalog_repo_fixture_default_forbidden" in reasons, obj
assert "strict_actor_entry_gate_missing" in reasons, obj
assert "shell_strict_actor_default_literal_forbidden" in reasons, obj
assert "shell_strict_project_catalog_repo_fixture_default_forbidden" in reasons, obj
assert "shell_strict_entry_registry_missing" in reasons, obj
assert "shell_strict_codex_tuple_handoff_missing" in reasons, obj
print("[PASS] negative strict actor entry fallback blocked")
PY

echo "[info] semantic clarity probes: negative lane (stream scope matrix alias fail-close)"
cat > "$TMP_ROOT/invalid-stream-matrix.current.yaml" <<'YAML'
schema_version: 1
pointer_version: v1
YAML

if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
  set +e
  python3 scripts/validate_stream_scope_semantic_integrity.py \
    --base HEAD~1 \
    --head HEAD \
    --stream-matrix "$TMP_ROOT/invalid-stream-matrix.current.yaml" \
    --json-only > "$TMP_ROOT/stream_scope_negative.json"
  rc=$?
  set -e
  if [[ "$rc" -eq 0 ]]; then
    echo "[FAIL] expected stream scope semantic integrity alias probe to fail"
    exit 1
  fi
  python3 - "$TMP_ROOT/stream_scope_negative.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-SSCOPE-001", obj
assert any("stream_matrix_alias_error" in x for x in (obj.get("stale_reasons") or [])), obj
print("[PASS] negative stream scope alias fail-close blocked")
PY
else
  echo "[warn] skip stream scope negative probe: HEAD~1 unavailable"
fi

echo "[info] semantic clarity probes: host-native explanatory envelope exclusion"
cat > "$TMP_ROOT/operator_envelope_exclusion_probe.json" <<'JSON'
{
  "response_stamp_profile": {
    "enabled": true,
    "format": "structured_block",
    "template_ref": "identity/protocol/plugins/templates/response-stamp.operator_dual_segment_v1.json"
  },
  "external_stamp": "Identity-Context: actor_id=assistant:codex; identity_id=probe-host-native; scope=USER; source=project | Layer-Context: work_layer=protocol; source_layer=project",
  "machine_verification": {
    "verification_source": "not_claimed",
    "display_headstamp_identity_id": "probe-host-native",
    "authoritative_identity_id": "probe-host-native",
    "headstamp_consistency_status": "PASS_REQUIRED",
    "surface_class": "host_native_chat_panel",
    "native_attestation_wiring_capability": "unavailable",
    "closure_blocker_scope": "EXCLUDED_NON_BLOCKING",
    "current_chat_surface_native_machine_attested": false,
    "next_hop_admission_status": "FAIL_REQUIRED"
  },
  "display_headstamp_line": "Display-Headstamp: Identity-Context: actor_id=assistant:codex; identity_id=probe-host-native; scope=USER; source=project | Layer-Context: work_layer=protocol; source_layer=project",
  "machine_verification_line": "Machine-Verification: verification_source=not_claimed; display_headstamp_identity_id=probe-host-native; authoritative_identity_id=probe-host-native; headstamp_consistency_status=PASS_REQUIRED; surface_class=host_native_chat_panel; native_attestation_wiring_capability=unavailable; closure_blocker_scope=EXCLUDED_NON_BLOCKING; current_chat_surface_native_machine_attested=false; next_hop_admission_status=FAIL_REQUIRED",
  "operator_envelope_lines": [
    "Display-Headstamp: Identity-Context: actor_id=assistant:codex; identity_id=probe-host-native; scope=USER; source=project | Layer-Context: work_layer=protocol; source_layer=project",
    "Machine-Verification: verification_source=not_claimed; display_headstamp_identity_id=probe-host-native; authoritative_identity_id=probe-host-native; headstamp_consistency_status=PASS_REQUIRED; surface_class=host_native_chat_panel; native_attestation_wiring_capability=unavailable; closure_blocker_scope=EXCLUDED_NON_BLOCKING; current_chat_surface_native_machine_attested=false; next_hop_admission_status=FAIL_REQUIRED"
  ]
}
JSON
python3 scripts/validate_response_stamp_operator_envelope.py \
  --stamp-json "$TMP_ROOT/operator_envelope_exclusion_probe.json" \
  --repo-root "$REPO_ROOT" \
  --json-only > "$TMP_ROOT/operator_envelope_exclusion_probe_result.json"
python3 - "$TMP_ROOT/operator_envelope_exclusion_probe_result.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("operator_headstamp_envelope_status") == "PASS_REQUIRED", obj
assert obj.get("explanatory_surface_exclusion_status") == "PASS_REQUIRED", obj
assert obj.get("parsed_machine_verification", {}).get("closure_blocker_scope") == "EXCLUDED_NON_BLOCKING", obj
assert obj.get("parsed_machine_verification", {}).get("current_chat_surface_native_machine_attested") == "false", obj
print("[PASS] host-native explanatory envelope exclusion probe")
PY

echo "[info] semantic clarity probes: process-dialogue headstamp scope contract"
cat > "$TMP_ROOT/process_message_positive.json" <<'JSON'
{
  "message_author_role": "assistant",
  "message_kind": "checkpoint",
  "response_stamp_profile": {
    "enabled": true,
    "format": "structured_block",
    "template_ref": "identity/protocol/plugins/templates/response-stamp.operator_dual_segment_v1.json"
  },
  "external_stamp": "Identity-Context: actor_id=assistant:codex; identity_id=probe-process; scope=USER; source=project | Layer-Context: work_layer=protocol; source_layer=project",
  "machine_verification": {
    "verification_source": "not_claimed",
    "display_headstamp_identity_id": "probe-process",
    "authoritative_identity_id": "probe-process",
    "headstamp_consistency_status": "PASS_REQUIRED"
  },
  "display_headstamp_line": "Display-Headstamp: Identity-Context: actor_id=assistant:codex; identity_id=probe-process; scope=USER; source=project | Layer-Context: work_layer=protocol; source_layer=project",
  "machine_verification_line": "Machine-Verification: verification_source=not_claimed; display_headstamp_identity_id=probe-process; authoritative_identity_id=probe-process; headstamp_consistency_status=PASS_REQUIRED",
  "operator_envelope_lines": [
    "Display-Headstamp: Identity-Context: actor_id=assistant:codex; identity_id=probe-process; scope=USER; source=project | Layer-Context: work_layer=protocol; source_layer=project",
    "Machine-Verification: verification_source=not_claimed; display_headstamp_identity_id=probe-process; authoritative_identity_id=probe-process; headstamp_consistency_status=PASS_REQUIRED"
  ]
}
JSON
python3 scripts/validate_response_stamp_operator_envelope.py \
  --stamp-json "$TMP_ROOT/process_message_positive.json" \
  --repo-root "$REPO_ROOT" \
  --json-only > "$TMP_ROOT/process_message_positive_result.json"
python3 - "$TMP_ROOT/process_message_positive_result.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("operator_headstamp_envelope_status") == "PASS_REQUIRED", obj
assert obj.get("message_headstamp_requirement_scope") == "REQUIRED_ASSISTANT_PROCESS_MESSAGE", obj
assert obj.get("message_headstamp_requirement_reason") == "assistant_process_message:checkpoint", obj
assert obj.get("headstamp_required_for_message") is True, obj
assert obj.get("message_headstamp_requirement_status") == "PASS_REQUIRED", obj
assert obj.get("operator_envelope_validation_applied") is True, obj
print("[PASS] assistant process message requires and accepts shared headstamp")
PY

cat > "$TMP_ROOT/process_message_missing_headstamp.json" <<'JSON'
{
  "message_author_role": "assistant",
  "message_kind": "status_update"
}
JSON
set +e
python3 scripts/validate_response_stamp_operator_envelope.py \
  --stamp-json "$TMP_ROOT/process_message_missing_headstamp.json" \
  --repo-root "$REPO_ROOT" \
  --json-only > "$TMP_ROOT/process_message_missing_headstamp_result.json"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "[FAIL] expected assistant process message without headstamp to fail"
  exit 1
fi
python3 - "$TMP_ROOT/process_message_missing_headstamp_result.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("operator_headstamp_envelope_status") == "FAIL_REQUIRED", obj
assert obj.get("message_headstamp_requirement_scope") == "REQUIRED_ASSISTANT_PROCESS_MESSAGE", obj
assert obj.get("headstamp_required_for_message") is True, obj
assert obj.get("message_headstamp_requirement_status") == "FAIL_REQUIRED", obj
assert "assistant_process_message_headstamp_missing" in (obj.get("stale_reasons") or []), obj
print("[PASS] assistant process message missing headstamp fails closed")
PY

cat > "$TMP_ROOT/process_message_excluded_tool_event.json" <<'JSON'
{
  "message_author_role": "tool",
  "message_kind": "tool_stderr"
}
JSON
python3 scripts/validate_response_stamp_operator_envelope.py \
  --stamp-json "$TMP_ROOT/process_message_excluded_tool_event.json" \
  --repo-root "$REPO_ROOT" \
  --json-only > "$TMP_ROOT/process_message_excluded_tool_event_result.json"
python3 - "$TMP_ROOT/process_message_excluded_tool_event_result.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("operator_headstamp_envelope_status") == "PASS_REQUIRED", obj
assert obj.get("message_headstamp_requirement_scope") == "EXCLUDED_HOST_TOOL_SYSTEM_EVENT", obj
assert obj.get("message_headstamp_requirement_reason") == "host_tool_system_event_excluded", obj
assert obj.get("headstamp_required_for_message") is False, obj
assert obj.get("message_headstamp_requirement_status") == "PASS_REQUIRED", obj
assert obj.get("operator_envelope_validation_applied") is False, obj
assert obj.get("response_stamp_profile_status") == "SKIPPED_NOT_REQUIRED", obj
print("[PASS] host/tool/system event stays outside headstamp requirement")
PY

echo "[info] semantic clarity probes: three-plane host-native exclusion aggregation"
python3 - "$REPO_ROOT" <<'PY'
import argparse
import importlib.util
import json
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
scripts_dir = repo_root / "scripts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(repo_root))
script = scripts_dir / "report_three_plane_status.py"
spec = importlib.util.spec_from_file_location("three_plane_exclusion_probe_mod", script)
if spec is None or spec.loader is None:
    raise SystemExit("[FAIL] unable to load report_three_plane_status.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

render_payload = {
    "display_headstamp_line": "Display-Headstamp: Identity-Context: actor_id=assistant:codex; identity_id=probe; scope=USER; source=project | Layer-Context: work_layer=protocol; source_layer=project",
    "machine_verification_line": "Machine-Verification: verification_source=not_claimed; display_headstamp_identity_id=probe; authoritative_identity_id=probe; headstamp_consistency_status=PASS_REQUIRED; surface_class=host_native_chat_panel; native_attestation_wiring_capability=unavailable; closure_blocker_scope=EXCLUDED_NON_BLOCKING; current_chat_surface_native_machine_attested=false; next_hop_admission_status=FAIL_REQUIRED",
}
validator_payload = {
    "operator_headstamp_envelope_status": "PASS_REQUIRED",
    "explanatory_surface_exclusion_status": "PASS_REQUIRED",
    "machine_verification_line": render_payload["machine_verification_line"],
    "parsed_machine_verification": {
        "closure_blocker_scope": "EXCLUDED_NON_BLOCKING",
        "current_chat_surface_native_machine_attested": "false",
        "next_hop_admission_status": "FAIL_REQUIRED",
    },
    "stale_reasons": [],
}

def fake_run(cmd, *, cwd=None):
    target = cmd[1] if len(cmd) > 1 else ""
    if target.endswith("render_identity_response_stamp.py"):
        return 0, json.dumps(render_payload), ""
    if target.endswith("validate_response_stamp_operator_envelope.py"):
        return 0, json.dumps(validator_payload), ""
    raise AssertionError(cmd)

mod._run = fake_run
args = argparse.Namespace(
    catalog="/tmp/catalog.yaml",
    repo_catalog="identity/catalog/identities.yaml",
    identity_id="probe",
    session_id="run:test",
)
projection = mod._build_current_chat_surface_exclusion_projection(
    args=args,
    actor_id="assistant:codex",
    layer_intent_text="protocol lane",
    effective_work_layer="protocol",
    effective_source_layer="project",
    stamp_render_payload={
        "display_headstamp_identity_id": "probe",
        "authoritative_identity_id": "probe",
        "headstamp_consistency_status": "PASS_REQUIRED",
    },
)
assert projection.get("excluded_from_blocker_aggregation") is True, projection
assert projection.get("effective_blocker_scope") == "EXCLUDED_NON_BLOCKING", projection
axes = mod._build_governance_closure_axes(
    instance_status="CLOSED",
    repo_status="CLOSED",
    release_status="BLOCKED",
    m2m_projection={"m2m_binding_closure_status": "PASS"},
    tuple_context_projection={"tuple_context_status": "PASS_REQUIRED"},
    current_chat_surface_exclusion=projection,
)
assert axes.get("current_chat_surface_excluded_from_blocker_aggregation") is True, axes
assert axes.get("current_chat_surface_effective_blocker_scope") == "EXCLUDED_NON_BLOCKING", axes
assert "host_native_chat_panel" in (axes.get("non_blocking_exclusions") or []), axes

validator_payload_bad = dict(validator_payload)
validator_payload_bad["explanatory_surface_exclusion_status"] = "FAIL_REQUIRED"
validator_payload_bad["stale_reasons"] = ["explanatory_surface_exclusion_invalid:verification_source_not_not_claimed"]

def fake_run_bad(cmd, *, cwd=None):
    target = cmd[1] if len(cmd) > 1 else ""
    if target.endswith("render_identity_response_stamp.py"):
        return 0, json.dumps(render_payload), ""
    if target.endswith("validate_response_stamp_operator_envelope.py"):
        return 1, json.dumps(validator_payload_bad), ""
    raise AssertionError(cmd)

mod._run = fake_run_bad
bad_projection = mod._build_current_chat_surface_exclusion_projection(
    args=args,
    actor_id="assistant:codex",
    layer_intent_text="protocol lane",
    effective_work_layer="protocol",
    effective_source_layer="project",
    stamp_render_payload={
        "display_headstamp_identity_id": "probe",
        "authoritative_identity_id": "probe",
        "headstamp_consistency_status": "PASS_REQUIRED",
    },
)
assert bad_projection.get("excluded_from_blocker_aggregation") is False, bad_projection
bad_axes = mod._build_governance_closure_axes(
    instance_status="BLOCKED",
    repo_status="CLOSED",
    release_status="BLOCKED",
    m2m_projection={"m2m_binding_closure_status": "PASS"},
    tuple_context_projection={"tuple_context_status": "PASS_REQUIRED"},
    current_chat_surface_exclusion=bad_projection,
)
assert any(
    str(reason).startswith("host_native_chat_surface_exclusion_not_frozen")
    for reason in (bad_axes.get("conditional_reasons") or [])
), bad_axes
print("[PASS] three-plane host-native exclusion aggregation probe")
PY

echo "[info] semantic clarity probes: three-plane/full-scan consumer parity"
python3 - "$REPO_ROOT" <<'PY'
import argparse
import importlib.util
import json
import pathlib
import sys

repo_root = pathlib.Path(sys.argv[1]).resolve()
scripts_dir = repo_root / "scripts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(repo_root))


def load_module(name: str, script_name: str):
    script = scripts_dir / script_name
    spec = importlib.util.spec_from_file_location(name, script)
    if spec is None or spec.loader is None:
        raise SystemExit(f"[FAIL] unable to load {script_name}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


three_plane = load_module("three_plane_consumer_parity_probe_mod", "report_three_plane_status.py")
full_scan = load_module("full_scan_consumer_parity_probe_mod", "full_identity_protocol_scan.py")

render_payload = {
    "display_headstamp_line": "Display-Headstamp: Identity-Context: actor_id=assistant:codex; identity_id=probe; scope=USER; source=project | Layer-Context: work_layer=protocol; source_layer=project",
    "machine_verification_line": "Machine-Verification: verification_source=not_claimed; display_headstamp_identity_id=probe; authoritative_identity_id=probe; headstamp_consistency_status=PASS_REQUIRED; surface_class=host_native_chat_panel; native_attestation_wiring_capability=unavailable; closure_blocker_scope=EXCLUDED_NON_BLOCKING; current_chat_surface_native_machine_attested=false; next_hop_admission_status=FAIL_REQUIRED",
}
validator_payload = {
    "operator_headstamp_envelope_status": "PASS_REQUIRED",
    "explanatory_surface_exclusion_status": "PASS_REQUIRED",
    "machine_verification_line": render_payload["machine_verification_line"],
    "parsed_machine_verification": {
        "closure_blocker_scope": "EXCLUDED_NON_BLOCKING",
        "current_chat_surface_native_machine_attested": "false",
        "next_hop_admission_status": "FAIL_REQUIRED",
    },
    "stale_reasons": [],
}


def fake_run(cmd, *, cwd=None):
    target = cmd[1] if len(cmd) > 1 else ""
    if target.endswith("render_identity_response_stamp.py"):
        return 0, json.dumps(render_payload), ""
    if target.endswith("validate_response_stamp_operator_envelope.py"):
        return 0, json.dumps(validator_payload), ""
    raise AssertionError(cmd)


args = argparse.Namespace(
    catalog="/tmp/catalog.yaml",
    repo_catalog="identity/catalog/identities.yaml",
    identity_id="probe",
    session_id="run:test",
)
three_plane._run = fake_run
projection = three_plane._build_current_chat_surface_exclusion_projection(
    args=args,
    actor_id="assistant:codex",
    layer_intent_text="protocol lane",
    effective_work_layer="protocol",
    effective_source_layer="project",
    stamp_render_payload={
        "display_headstamp_identity_id": "probe",
        "authoritative_identity_id": "probe",
        "headstamp_consistency_status": "PASS_REQUIRED",
    },
)
axes = three_plane._build_governance_closure_axes(
    instance_status="CLOSED",
    repo_status="CLOSED",
    release_status="BLOCKED",
    m2m_projection={"m2m_binding_closure_status": "PASS"},
    tuple_context_projection={"tuple_context_status": "PASS_REQUIRED"},
    current_chat_surface_exclusion=projection,
)
scan_projection = full_scan._build_current_chat_surface_projection_from_three_plane(
    three_plane_payload={
        "current_chat_surface_exclusion": projection,
        "governance_closure_axes": axes,
    }
)
assert scan_projection.get("effective_blocker_scope") == "EXCLUDED_NON_BLOCKING", scan_projection
assert scan_projection.get("excluded_from_blocker_aggregation") is True, scan_projection
assert scan_projection.get("control_state") == "CONTROLLED_EXCLUSION", scan_projection
assert scan_projection.get("machine_verification_line") == render_payload["machine_verification_line"], scan_projection

validator_payload_bad = dict(validator_payload)
validator_payload_bad["explanatory_surface_exclusion_status"] = "FAIL_REQUIRED"
validator_payload_bad["stale_reasons"] = ["explanatory_surface_exclusion_invalid:verification_source_not_not_claimed"]


def fake_run_bad(cmd, *, cwd=None):
    target = cmd[1] if len(cmd) > 1 else ""
    if target.endswith("render_identity_response_stamp.py"):
        return 0, json.dumps(render_payload), ""
    if target.endswith("validate_response_stamp_operator_envelope.py"):
        return 1, json.dumps(validator_payload_bad), ""
    raise AssertionError(cmd)


three_plane._run = fake_run_bad
bad_projection = three_plane._build_current_chat_surface_exclusion_projection(
    args=args,
    actor_id="assistant:codex",
    layer_intent_text="protocol lane",
    effective_work_layer="protocol",
    effective_source_layer="project",
    stamp_render_payload={
        "display_headstamp_identity_id": "probe",
        "authoritative_identity_id": "probe",
        "headstamp_consistency_status": "PASS_REQUIRED",
    },
)
bad_axes = three_plane._build_governance_closure_axes(
    instance_status="BLOCKED",
    repo_status="CLOSED",
    release_status="BLOCKED",
    m2m_projection={"m2m_binding_closure_status": "PASS"},
    tuple_context_projection={"tuple_context_status": "PASS_REQUIRED"},
    current_chat_surface_exclusion=bad_projection,
)
bad_scan_projection = full_scan._build_current_chat_surface_projection_from_three_plane(
    three_plane_payload={
        "current_chat_surface_exclusion": bad_projection,
        "governance_closure_axes": bad_axes,
    }
)
assert bad_scan_projection.get("effective_blocker_scope") == "BLOCKING", bad_scan_projection
assert bad_scan_projection.get("excluded_from_blocker_aggregation") is False, bad_scan_projection
assert bad_scan_projection.get("control_state") == "RAW_FAIL_BLOCKING", bad_scan_projection
print("[PASS] three-plane/full-scan host-native exclusion consumer parity probe")
PY

echo "[PASS] run_semantic_clarity_probes_ci.sh complete"
