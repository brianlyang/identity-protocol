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
4. `instance_owned_technical_debt`, `instance_clean_proof`, and `protocol_residual_issue` appear with frozen meanings.
5. Review wording explicitly states: `No instance-clean proof, no protocol escalation.`
6. Review wording explicitly states protocol does not backstop instance-owned technical debt.
7. Governance doc explicitly states: runtime default is `instance_autonomous_runtime` unless explicitly declared as `protocol_controlled_mirror_artifact`.
8. Shell set is exactly:
   - `runtime/gate/protocol_ingress_wrapper.py`
   - `runtime/gate/protocol_egress_wrapper.py`
   - `runtime/gate/protocol_session_chain_wrapper.py`
9. `runtime/gate/protocol_gateway_contract.json` is treated as mirror artifact, not shell code.
10. `v1.6.10` exists in active stream registry and is not listed under legacy archival docs.
11. `v1.6.10` does not absorb `ASB16-RQ-039/040/041`.
12. No non-landed “must-have validator” remains in doc text.

## 3.1 Ownership split freeze

1. `identity protocol` is the shared contract and upgrade framework; it does **not** backstop `instance_owned_technical_debt`.
2. `instance_owned_technical_debt` includes missing instance-local skills/config/transport/install/replay hygiene and other local recovery obligations.
3. `instance_clean_proof` is required before any remaining issue may be escalated as `protocol_residual_issue`.
4. `No instance-clean proof, no protocol escalation.`
5. `protocol_residual_issue` is limited to shared contract / wiring / validator / CI / governance defects that remain after `instance_clean_proof`.
6. Host/runtime entry gaps stay a separate boundary and must not be relabeled as either instance debt or protocol residual.

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
     `authoritative_decision_allowed=false`;
   - future canonical/mirror writes also persist compatibility-projection provenance
     (`compatibility_projection_actor_id`, `compatibility_projection_identity_id`,
     `compatibility_projection_session_id`, `compatibility_projection_binding_ref`,
     `compatibility_projection_run_id`) so the last overwrite stays explicitly non-authoritative.
3. `scripts/identity_creator.py`
   - `--switch-guard-scope actor_global` now reads actor-store compatibility projection directly
     instead of reusing the ambiguous actor-scope selector;
   - this closes the multi-identity blind spot where later session activations could overwrite the
     shared pointer without tripping actor-global switch detection.
4. `scripts/validate_actor_session_multibinding_concurrency.py`
   - when `--session-id` is supplied, session-primary projection is read from `last_mutation_by_session`.
5. `scripts/validate_identity_session_pointer_consistency.py`
   - strict pointer validation still fail-closes on shared-pointer mismatch by default;
   - explicit `--allow-compatibility-projection-drift` only acknowledges mismatch when the shared pointer proves
     actor-global compatibility provenance for a different session.
6. governed response/headstamp consumers
   - `scripts/identity_runtime_authority_common.py` now treats compatibility pointers as non-authoritative
     unless explicit legacy fallback is enabled;
   - `scripts/response_stamp_common.py` no longer silently falls back from missing actor context into
     shared compatibility pointers;
   - `scripts/render_identity_response_stamp.py`, `scripts/compose_and_validate_governed_reply.py`, and
     `scripts/validate_reply_identity_context_first_line.py` now propagate resolved actor/session context
     instead of reusing raw empty CLI input.
7. static anti-forget surface
   - `scripts/validate_response_authority_consumer_semantics.py` scans response/headstamp authority consumers and
     fail-closes when any consumer drops `session_id`, reintroduces `resolve_actor_id()` host fallback, or reuses
     compatibility-pointer literals as authority hints.
   - default scan set now includes `scripts/final_emit_governed.py`, so final single-entry egress stays under the
     same authority-consumer drift guard as render/compose/first-line validators.
   - authority-provider / validator helper modules now declare `AUTHORITY_CONSUMER_EXEMPT = True`, and the validator
     fail-closes any newly discovered authority consumer that is neither registered nor explicitly exempt.
   - `scripts/validate_strict_actor_entry_semantics.py` scans strict orchestrators that launch governed
     render/first-line/headstamp/final-emit checks and blocks hidden `assistant:codex` defaults or missing
     `IP-ACTOR-ENTRY-001` / `resolve_required_protocol_actor_id()` entry gates.
   - the same validator now also blocks strict regression wrappers that default `--project-catalog` back to
     `identity/catalog/identities.yaml` instead of runtime-local catalog semantics.
   - shell strict-entry wrappers now route through `scripts/shell_strict_entry_common.sh`; the validator covers the
     registered shell entry set and records explicit probe-only exemptions for fixture scripts such as semantic clarity
     and gateway / privilege probe lanes.

### 10.3 Replay evidence

1. semantic clarity probe lane:
   - residue present => `repair_actor_session_authority_residue.py` returns `FAIL_REQUIRED`
   - repair applied => actor-session validation returns `last_mutation_projection_scope=session_primary`
   - repaired compatibility pointers now expose explicit actor/session/binding provenance, not only demotion flags
   - no actor context + compatibility pointer only => render path fail-closes instead of adopting pointer authority
   - env actor + bound session => render path restores headstamp output deterministically
   - cross-session pointer drift without explicit allowance => strict pointer validator fail-closes
   - cross-session pointer drift with explicit compatibility provenance => strict pointer validator acknowledges
     non-authoritative drift while tuple-bound session authority stays intact
   - actor-global switch guard now blocks later cross-session overwrite attempts before role-binding validation
   - negative authority-consumer drift probe => static validator blocks missing session passthrough, host fallback
     resolver reuse, compatibility-pointer literal reuse, and unregistered authority-consumer surfaces
   - negative strict actor entry probe => static validator blocks hidden `assistant:codex` defaults and missing
     strict actor entry gates on authority-adjacent orchestrators
   - negative strict project-catalog probe => static validator blocks strict regression wrappers that silently
     revert project catalog input to the repo fixture
   - negative strict shell-entry probe => static validator blocks unregistered shell strict surfaces plus shell actor
     / project-catalog defaults before they re-enter runtime lanes
2. live runtime replay:
   - `/tmp/actor_session_authority_residue_apply_20260317.json`
   - `/tmp/actor_session_authority_residue_scan_20260317.json`

### 10.4 Verdict

1. The remaining “identity switched / authority looked mixed” confusion included a producer-side blind spot:
   actor-global guard read an ambiguous actor selector while shared compatibility pointers kept being overwritten by
   later sessions.
2. Runtime-file governance now closes that gap by combining:
   - direct actor-global compatibility projection reads for switch guard;
   - explicit compatibility-projection provenance on shared pointers;
   - strict cross-session drift validation that only allows non-authoritative residue when provenance is present.
3. Repair stays protocol-owned and generic; no per-identity hardcoded migration was introduced.

### 10.5 Compile/replay compatibility mirror clarification (2026-03-18)

1. compile/replay compatibility mirror clarification is now frozen under v1.6.10 runtime-file governance.
2. compile/replay metadata may read compatibility mirror; current-session authority must not.
3. compiled/runtime examples are therefore treated as compile-time projections from the currently resolved runtime, not standalone live authority.

### 10.6 Compiled brief artifact class + legacy compatibility path freeze (2026-03-18)

1. `identity/runtime/IDENTITY_COMPILED.md` is now reviewed as a `tracked_compiled_brief_artifact`, not an ordinary runtime evidence/log artifact.
2. The file is a governed generated artifact and must not be interpreted as:
   - instance-autonomous runtime state
   - generic `protocol_controlled_mirror_artifact`
3. The current path is frozen as a `legacy_canonical_compatibility_path`; consumer/config/docs continue to use it until a separately approved taxonomy migration lands.
4. Source-first rule is frozen:
   - semantic changes land in docs/template/script sources first,
   - then `scripts/compile_identity_runtime.py` regenerates the brief,
   - direct manual semantic editing of `identity/runtime/IDENTITY_COMPILED.md` is non-compliant.
