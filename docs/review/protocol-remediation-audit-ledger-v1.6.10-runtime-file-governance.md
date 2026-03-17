# Protocol Remediation Audit Ledger (v1.6.10 runtime file governance)

Status: Active review ledger draft (boundary freeze, 2026-03-17)
Scope: audit ledger for runtime dynamic file governance boundary closure in v1.6.x stream

## 0) Audit objective

Current-pointer continuity refs (mandatory):

- `identity/protocol/mappings/contract-binding.current.yaml`
- `identity/protocol/mappings/control-plane-status.current.yaml`
- `identity/protocol/mappings/control-plane-invariants.current.yaml`
- `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/semantic-term-registry.current.yaml`
- `identity/protocol/mappings/stream-scope-matrix.current.yaml`

1. Freeze the boundary between protocol-generated gateway shells, protocol-controlled mirror artifacts, and instance-autonomous runtime.
2. Ensure v1.6.10 is implementation-grade rather than doc-only.
3. Keep v1.6.6 wrapper-only guarantees and v1.6.8 downsink immutability guarantees intact.
4. Ensure v1.6.10 does not absorb skill supply-chain topics.

## 1) Frozen risks

1. Wrapper governance may be over-expanded into blanket runtime ownership.
2. Mirror artifacts may be mislabeled as shells.
3. Runtime autonomy may be weakened by wording alone, without explicit contract elevation.
4. Draft docs may cite non-landed validators and therefore miss code-landing quality.

## 2) Landed strengthening required for closure

### 2.1 Canonical protocol contract

1. `scripts/protocol_infra_contract.py` must define:
   - `PROTOCOL_GENERATED_GATEWAY_SHELL_PATHS`
   - `PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_PATHS`
   - canonical terms for the three ownership classes
2. The closed shell set must remain exactly three wrapper files.
3. The mirror floor must include `runtime/gate/protocol_gateway_contract.json` and may only expand through explicit protocol declarations.

### 2.2 Validators

1. `scripts/validate_runtime_file_boundary_governance.py`
2. `scripts/validate_semantic_term_registry.py`
3. `scripts/validate_stream_scope_semantic_integrity.py`
4. `scripts/validate_required_gate_surface_drift.py`

### 2.3 CI and replay wiring

1. `bash scripts/ci/run_semantic_clarity_probes_ci.sh`
2. `bash scripts/ci/run_downsink_path_immutability_probes_ci.sh`
3. Existing v1.6.6 wrapper / host-visible replay lanes remain green.

## 3) Mandatory review checklist

1. `protocol_generated_gateway_shell` appears in governance + review docs.
2. `protocol_controlled_mirror_artifact` appears in governance + review docs.
3. `instance_autonomous_runtime` appears in governance + review docs.
4. Governance doc explicitly states: runtime default is `instance_autonomous_runtime` unless explicitly declared as `protocol_controlled_mirror_artifact`.
5. Shell set is exactly:
   - `runtime/gate/protocol_ingress_wrapper.py`
   - `runtime/gate/protocol_egress_wrapper.py`
   - `runtime/gate/protocol_session_chain_wrapper.py`
6. `runtime/gate/protocol_gateway_contract.json` is treated as mirror artifact, not shell code.
7. `v1.6.10` exists in active stream registry and is not listed under legacy archival docs.
8. `v1.6.10` does not absorb `ASB16-RQ-039/040/041`.
9. No non-landed “must-have validator” remains in doc text.

## 4) Probe matrix

### 4.1 Positive (required green)

1. `probe_runtime_file_boundary_governance_pass`
2. `probe_semantic_term_registry_pass`
3. `probe_stream_scope_semantic_integrity_pass_or_skip`
4. `probe_downsink_path_immutability_pass`

### 4.2 Negative (required red)

1. `probe_runtime_boundary_doc_missing_required_tokens_blocked`
2. `probe_runtime_boundary_forbidden_phrase_blocked`
3. `probe_runtime_boundary_stream_registry_missing_active_row_blocked`
4. `probe_runtime_boundary_shell_mirror_overlap_blocked`

## 5) Non-conflict assertions

1. No new protocol claim may convert all runtime files into protocol-owned artifacts.
2. No wrapper-local semantic override is allowed.
3. No instance-local runtime file may be promoted to protocol-generated solely by path adjacency.
4. No skill supply-chain file or requirement may be co-streamed into v1.6.10.

## 6) Cross-verification lanes

1. Roundtable lane: v1.6.6 + v1.6.8 inheritance remains coherent.
2. Vendor lane: OPA + Sigstore boundary/provenance models support the distinction between generated shells and governed mirrors.
3. Reference lane: SLSA + Trace Context reinforce provenance/observability boundaries.
4. Search/OpenAIDoc lane: eval/tracing guidance supports machine-checked boundaries and explicit workflow visibility.

## 7) Acceptance criteria

Machine status fields that must remain visible in strict lane documentation and replay payloads:

- `required_gate_surface_drift_status`
- `required_contract_coverage_status`

1. `python3 scripts/validate_runtime_file_boundary_governance.py --json-only` => `PASS_REQUIRED`
2. `python3 scripts/validate_semantic_term_registry.py --json-only` => `PASS_REQUIRED`
3. `python3 scripts/validate_stream_scope_semantic_integrity.py --base HEAD --head HEAD --json-only` => `SKIPPED_NOT_REQUIRED` or valid strict verdict
4. `python3 scripts/validate_required_gate_surface_drift.py --json-only` => `PASS_REQUIRED`
5. `python3 scripts/validate_required_contract_coverage.py --catalog <catalog> --identity-id <id> --operation validate --json-only` => payload includes `required_contract_coverage_status`
6. `bash scripts/ci/run_semantic_clarity_probes_ci.sh` => positive lane green, negative lanes red-as-expected
7. Wrapper replay / host-visible continuity lanes remain non-regressed.

## 8) Evidence pointers

1. `docs/review/evidence/v1.6.10/CROSS_VERIFICATION_MANIFEST.v1610.20260316.json`
2. `activity/evidence/v1610-runtime-file-governance/<date>/`

## 9) v1.6.10 one-to-one correspondence replay checklist

Replay objective: prevent v1.6.10 boundary text from becoming doc-only memory.

Required machine checks:

1. `python3 scripts/validate_runtime_file_boundary_governance.py --json-only`
2. `python3 scripts/validate_semantic_term_registry.py --json-only`
3. `python3 scripts/validate_stream_scope_semantic_integrity.py --base HEAD --head HEAD --json-only`
4. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
5. `python3 scripts/validate_required_contract_coverage.py --catalog <catalog> --identity-id <id> --operation validate --json-only`
6. `bash scripts/ci/run_semantic_clarity_probes_ci.sh`
7. `bash scripts/ci/run_downsink_path_immutability_probes_ci.sh`

Interpretation contract:

1. If any v1.6.10 clause changes without the boundary validator and semantic clarity replay, classify as anti-forget regression.
2. Anti-forget regressions are fail-close in strict operations.

## 10) Addendum (2026-03-17): actor-session authority residue replay

### 10.1 Scope

1. Runtime-file governance must cover persisted actor-session authority semantics, not only wrapper shells and mirror path ownership.
2. The specific residue addressed here:
   - actor stores missing `last_mutation_by_session` / authority metadata;
   - compatibility pointers missing explicit non-authoritative mirror metadata.

### 10.2 Code closure

1. `scripts/repair_actor_session_authority_residue.py`
   - scans `<catalog_dir>/session/actors/*.json`;
   - rewrites persisted actor-session authority residue via normalized protocol schema;
   - updates canonical + mirror compatibility pointers with explicit demotion metadata.
2. `scripts/sync_session_identity.py`
   - future canonical/mirror writes now persist `authority_role=compatibility_mirror` and
     `authoritative_decision_allowed=false`.
3. `scripts/validate_actor_session_multibinding_concurrency.py`
   - when `--session-id` is supplied, session-primary projection is read from `last_mutation_by_session`.

### 10.3 Replay evidence

1. semantic clarity probe lane:
   - residue present => `repair_actor_session_authority_residue.py` returns `FAIL_REQUIRED`
   - repair applied => actor-session validation returns `last_mutation_projection_scope=session_primary`
2. live runtime replay:
   - `/tmp/actor_session_authority_residue_apply_20260317.json`
   - `/tmp/actor_session_authority_residue_scan_20260317.json`

### 10.4 Verdict

1. The remaining “identity switched / authority looked mixed” confusion is now classified as runtime-file residue,
   not unresolved core actor-session logic.
2. Repair stays protocol-owned and generic; no per-identity hardcoded migration was introduced.
