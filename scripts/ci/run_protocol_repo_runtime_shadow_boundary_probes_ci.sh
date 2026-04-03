#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}"

echo "[info] protocol-repo runtime shadow boundary probes: positive validator replay"
python3 scripts/validate_runtime_file_boundary_governance.py --json-only > "${TMP_ROOT}/runtime_shadow_positive.json"
python3 - "${TMP_ROOT}/runtime_shadow_positive.json" <<'PY'
import json
import sys

obj = json.load(open(sys.argv[1], encoding="utf-8"))
assert obj.get("runtime_file_boundary_governance_status") == "PASS_REQUIRED", obj
assert not obj.get("gitignore_missing_patterns"), obj
assert not obj.get("runtime_selector_missing_tokens"), obj
print("[PASS] positive runtime shadow boundary validator replay passed")
PY

echo "[info] protocol-repo runtime shadow boundary probes: negative missing .identity ignore"
mkdir -p "${TMP_ROOT}/neg-shadow/docs/governance" \
         "${TMP_ROOT}/neg-shadow/docs/review" \
         "${TMP_ROOT}/neg-shadow/identity/protocol/mappings" \
         "${TMP_ROOT}/neg-shadow/identity/protocol" \
         "${TMP_ROOT}/neg-shadow/scripts"

cat > "${TMP_ROOT}/neg-shadow/.gitignore" <<'EOF_GITIGNORE'
.identity-protocol/
.codex/
.tmp/
.IDENTITY.run__*.md
EOF_GITIGNORE

cat > "${TMP_ROOT}/neg-shadow/scripts/use_project_identity_runtime.sh" <<'EOF_SELECTOR'
#!/usr/bin/env bash
echo "broken selector"
EOF_SELECTOR

cat > "${TMP_ROOT}/neg-shadow/docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md" <<'EOF_GOV'
# runtime boundary
.gitignore
.identity/
.identity-protocol/
.codex/
.tmp/
.IDENTITY.run__*.md
local runtime shadow
scripts/use_project_identity_runtime.sh
Boundary freeze (authoritative)
protocol_generated_gateway_shell
protocol_controlled_mirror_artifact
instance_autonomous_runtime
runtime/gate/protocol_ingress_wrapper.py
runtime/gate/protocol_egress_wrapper.py
runtime/gate/protocol_session_chain_wrapper.py
runtime/gate/protocol_gateway_contract.json
Runtime default is `instance_autonomous_runtime` unless explicitly declared as `protocol_controlled_mirror_artifact`.
PROTOCOL_GENERATED_GATEWAY_SHELL_PATHS
PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_PATHS
tracked_compiled_brief_artifact
tracked_compiled_brief_frozen_path
legacy_canonical_compatibility_path
identity/runtime/IDENTITY_COMPILED.md
governed generated artifact
not ordinary runtime evidence/log artifact
not instance-autonomous runtime state
source-first
instance_owned_technical_debt
instance_clean_proof
protocol_residual_issue
No instance-clean proof, no protocol escalation.
does **not** backstop `instance_owned_technical_debt`
EOF_GOV

cat > "${TMP_ROOT}/neg-shadow/docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md" <<'EOF_REVIEW'
# runtime boundary review
protocol_generated_gateway_shell
protocol_controlled_mirror_artifact
instance_autonomous_runtime
tracked_compiled_brief_artifact
tracked_compiled_brief_frozen_path
legacy_canonical_compatibility_path
scripts/validate_runtime_file_boundary_governance.py
scripts/ci/run_semantic_clarity_probes_ci.sh
runtime/gate/protocol_gateway_contract.json
identity/runtime/IDENTITY_COMPILED.md
governed generated artifact
direct manual semantic editing
.gitignore
.identity/
.identity-protocol/
.codex/
.tmp/
.IDENTITY.run__*.md
local runtime shadow
scripts/use_project_identity_runtime.sh
instance_owned_technical_debt
instance_clean_proof
protocol_residual_issue
No instance-clean proof, no protocol escalation.
does **not** backstop `instance_owned_technical_debt`
EOF_REVIEW

cat > "${TMP_ROOT}/neg-shadow/identity/protocol/IDENTITY_PROTOCOL.md" <<'EOF_PROTOCOL'
# protocol overview
Core ownership and escalation contract
instance_owned_technical_debt
instance_clean_proof
protocol_residual_issue
No instance-clean proof, no protocol escalation.
does **not** backstop instance-owned technical debt
autonomous optimization unit
Host/runtime entry gaps remain a separate boundary
EOF_PROTOCOL

cat > "${TMP_ROOT}/neg-shadow/identity/protocol/mappings/stream-doc-registry.current.yaml" <<'EOF_STREAM_CURRENT'
schema_version: 1
pointer_version: v1
active_file: identity/protocol/mappings/stream-doc-registry.v1.yaml
EOF_STREAM_CURRENT

cat > "${TMP_ROOT}/neg-shadow/identity/protocol/mappings/stream-doc-registry.v1.yaml" <<'EOF_STREAM'
schema_version: 1
version: v1.6
stream_docs:
  - stream_version: v1.6.10
    governance_doc: docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md
    review_doc: docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md
legacy_archival_docs: []
EOF_STREAM

cat > "${TMP_ROOT}/neg-shadow/identity/protocol/mappings/semantic-term-registry.current.yaml" <<'EOF_TERM_CURRENT'
schema_version: 1
pointer_version: v1
active_file: identity/protocol/mappings/semantic-term-registry.v1.yaml
EOF_TERM_CURRENT

cat > "${TMP_ROOT}/neg-shadow/identity/protocol/mappings/semantic-term-registry.v1.yaml" <<'EOF_TERMS'
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
  - term_id: tracked_compiled_brief_artifact
    canonical_term: tracked_compiled_brief_artifact
    semantics: ok
    allowed_scope: [governance]
  - term_id: tracked_compiled_brief_frozen_path
    canonical_term: tracked_compiled_brief_frozen_path
    semantics: ok
    allowed_scope: [governance]
  - term_id: legacy_canonical_compatibility_path
    canonical_term: legacy_canonical_compatibility_path
    semantics: ok
    allowed_scope: [governance]
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
EOF_TERMS

set +e
python3 scripts/validate_runtime_file_boundary_governance.py \
  --repo-root "${TMP_ROOT}/neg-shadow" \
  --json-only > "${TMP_ROOT}/runtime_shadow_negative.json"
rc=$?
set -e
if [[ "${rc}" -eq 0 ]]; then
  echo "[FAIL] expected runtime shadow boundary probe to fail"
  exit 1
fi

python3 - "${TMP_ROOT}/runtime_shadow_negative.json" <<'PY'
import json
import sys

obj = json.load(open(sys.argv[1], encoding="utf-8"))
assert obj.get("error_code") == "IP-RFILE-BDRY-001", obj
reasons = set(obj.get("stale_reasons") or [])
assert "gitignore_missing_runtime_shadow_ignore_patterns" in reasons, obj
assert "runtime_selector_missing_parent_runtime_shadow_tokens" in reasons, obj
assert ".identity/" in (obj.get("gitignore_missing_patterns") or []), obj
print("[PASS] negative runtime shadow boundary probe blocked")
PY
