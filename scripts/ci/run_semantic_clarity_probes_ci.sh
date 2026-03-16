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

python3 - "$TMP_ROOT/semantic_term_positive.json" "$TMP_ROOT/cli_catalog_positive.json" "$TMP_ROOT/stream_scope_positive.json" "$TMP_ROOT/runtime_boundary_positive.json" <<'PY'
import json,sys
semantic=json.load(open(sys.argv[1]))
cli=json.load(open(sys.argv[2]))
stream=json.load(open(sys.argv[3]))
boundary=json.load(open(sys.argv[4]))
assert semantic.get("semantic_term_registry_status") == "PASS_REQUIRED", semantic
assert cli.get("cli_catalog_default_semantics_status") == "PASS_REQUIRED", cli
assert stream.get("stream_scope_semantic_integrity_status") == "SKIPPED_NOT_REQUIRED", stream
assert boundary.get("runtime_file_boundary_governance_status") == "PASS_REQUIRED", boundary
print("[PASS] positive semantic clarity lane")
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
