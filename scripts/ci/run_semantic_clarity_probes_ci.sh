#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

TMP_ROOT="$(mktemp -d /tmp/semantic-clarity-probes.XXXXXX)"
cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

echo "[info] semantic clarity probes: positive lane"
python3 scripts/validate_semantic_term_registry.py --json-only > "$TMP_ROOT/semantic_term_positive.json"
python3 scripts/validate_cli_catalog_default_semantics.py --json-only > "$TMP_ROOT/cli_catalog_positive.json"
python3 scripts/validate_stream_scope_semantic_integrity.py --base HEAD --head HEAD --json-only > "$TMP_ROOT/stream_scope_positive.json"
python3 scripts/validate_runtime_file_boundary_governance.py --json-only > "$TMP_ROOT/runtime_boundary_positive.json"
python3 scripts/validate_response_authority_consumer_semantics.py --json-only > "$TMP_ROOT/authority_consumer_positive.json"

python3 - "$TMP_ROOT/semantic_term_positive.json" "$TMP_ROOT/cli_catalog_positive.json" "$TMP_ROOT/stream_scope_positive.json" "$TMP_ROOT/runtime_boundary_positive.json" "$TMP_ROOT/authority_consumer_positive.json" <<'PY'
import json,sys
semantic=json.load(open(sys.argv[1]))
cli=json.load(open(sys.argv[2]))
stream=json.load(open(sys.argv[3]))
boundary=json.load(open(sys.argv[4]))
authority=json.load(open(sys.argv[5]))
assert semantic.get("semantic_term_registry_status") == "PASS_REQUIRED", semantic
assert cli.get("cli_catalog_default_semantics_status") == "PASS_REQUIRED", cli
assert stream.get("stream_scope_semantic_integrity_status") == "SKIPPED_NOT_REQUIRED", stream
assert boundary.get("runtime_file_boundary_governance_status") == "PASS_REQUIRED", boundary
assert authority.get("response_authority_consumer_semantics_status") == "PASS_REQUIRED", authority
print("[PASS] positive semantic clarity lane")
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
assert obj.get("identity_authority_resolution_mode") == "compatibility_pointer_non_authoritative", obj
assert "compatibility_pointer_non_authoritative" in (obj.get("stale_reasons") or []), obj
assert "actor_context_missing" in (obj.get("stale_reasons") or []), obj
print("[PASS] non-authoritative compatibility pointer blocked")
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
  "canonical_session_pointer": "__CATALOG_DIR__/session/active_identity.json"
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
print("[PASS] authority residue repair lane")
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
mkdir -p "$TMP_ROOT/neg-boundary/docs/governance" "$TMP_ROOT/neg-boundary/docs/review" "$TMP_ROOT/neg-boundary/identity/protocol/mappings"
cat > "$TMP_ROOT/neg-boundary/docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md" <<'MD'
# broken doc
This text wrongly says all protocol-governed instance runtime files under `runtime/state`, `runtime/gate`, `runtime/plugins`, and `runtime/protocol-feedback`.
MD
cat > "$TMP_ROOT/neg-boundary/docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md" <<'MD'
# broken review
missing boundary tokens on purpose
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
assert "governance_doc_missing_required_tokens" in (obj.get("stale_reasons") or []), obj
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

echo "[PASS] run_semantic_clarity_probes_ci.sh complete"
