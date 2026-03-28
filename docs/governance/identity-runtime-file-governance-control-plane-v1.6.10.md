# Identity Runtime File Governance Control Plane (v1.6.10)

Status: Active protocol stream (boundary freeze + metadata hygiene closure, 2026-03-23)
Layer: protocol
Scope: runtime dynamic file governance boundary only; this stream does **not** blanket-own instance runtime state and does **not** absorb skill supply-chain semantics.

Execution mode: v1.6.x continuity stream. This stream strengthens protocol/runtime file governance boundaries without forking into v1.7.x.

## 0) Version discipline and stream boundary (mandatory)

1. Stream version is fixed at `v1.6.10`.
2. This stream inherits and must not weaken:
   - `docs/governance/identity-host-unique-channel-governance-v1.6.6.md`
   - `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
3. This stream is protocol infrastructure only, not instance-specific patching.
4. This stream must not absorb skill supply-chain requirements (`ASB16-RQ-039/040/041`); stream-scope enforcement must fail-close if those topics enter `v1.6.10`.
5. Current-pointer continuity refs (mandatory):
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`

## 1) Problem statement (frozen)

Prior runtime-file wording allowed semantic overreach:

1. `wrapper` governance and `instance runtime autonomy` could be conflated.
2. `runtime/gate/*` shell files and `runtime/*` autonomous state could be described with the same ownership language.
3. Draft wording could be read as “protocol owns all runtime files”, which is false and would destroy instance autonomy.
4. Some v1.6.10 draft clauses referenced future/non-landed validators, which is below code-landing quality.

## 2) Design objective (authoritative)

The objective is **not** to make protocol the owner of all runtime files.

The objective is to freeze the boundary as:

1. **wrapper 强控 / mirror 受约束 / runtime 默认自治**
2. `protocol_generated_gateway_shell` is protocol-template-controlled.
3. `protocol_controlled_mirror_artifact` is protocol-contract-controlled.
4. Runtime default is `instance_autonomous_runtime` unless explicitly declared as `protocol_controlled_mirror_artifact`.
5. No file becomes protocol-owned merely because it lives under `runtime/`.

### 2.1 Core ownership and escalation freeze (authoritative)

1. `identity protocol` is the shared contract and upgrade framework; it does **not** backstop `instance_owned_technical_debt`.
2. `instance_owned_technical_debt` remains instance-owned until the instance completes self-heal and produces `instance_clean_proof`.
3. `instance_clean_proof` is required before any remaining issue may be escalated as `protocol_residual_issue`.
4. `No instance-clean proof, no protocol escalation.`
5. `protocol_residual_issue` is limited to shared contract / wiring / validator / CI / governance defects that remain after `instance_clean_proof`.
6. Host/runtime entry gaps are a separate boundary and must not be relabeled as either `instance_owned_technical_debt` or `protocol_residual_issue`.
7. Closed protocol layers must not be reopened by unresolved instance-owned technical debt.

## 3) Boundary freeze (authoritative)

### 3.1 Canonical classes

1. `protocol_generated_gateway_shell`
   - protocol-defined thin boundary shell
   - generated from protocol canonical template
   - may validate / attest / dispatch / fail-close
   - may **not** become an instance-local control plane
2. `protocol_controlled_mirror_artifact`
   - protocol-contract-controlled mirror or downsink artifact
   - fields / schema / allowed paths are protocol-governed
   - content may still be instance-produced within contract boundaries
3. `instance_autonomous_runtime`
   - default class for runtime files not explicitly elevated into protocol governance
   - instance owns lifecycle / evolution / local recovery
   - protocol may validate boundary interactions but may not silently take over authorship

### 3.2 Exact `protocol_generated_gateway_shell` set (closed set)

The closed shell set is exactly:

1. `runtime/gate/protocol_ingress_wrapper.py`
2. `runtime/gate/protocol_egress_wrapper.py`
3. `runtime/gate/protocol_session_chain_wrapper.py`

Canonical code source is `scripts/protocol_infra_contract.py`:

- `PROTOCOL_GENERATED_GATEWAY_SHELL_PATHS`
- `HOST_GATEWAY_REQUIRED_DISPATCH_MODE=wrapper_only`
- `HOST_GATEWAY_REQUIRED_RELEASE_MODE=wrapper_only`

No additional runtime file may claim shell status unless added to the canonical protocol contract first.

### 3.3 Exact `protocol_controlled_mirror_artifact` floor

The minimum mirror floor is:

1. `runtime/gate/protocol_gateway_contract.json`

Canonical code source is `scripts/protocol_infra_contract.py`:

- `PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_PATHS`

Additional runtime files under `runtime/state`, `runtime/reports`, `runtime/plugins`, or `runtime/protocol-feedback` become protocol-governed **only when** they are explicitly declared by a protocol contract / path registry / validator surface. Path adjacency alone grants no protocol ownership.

### 3.4 Default autonomy rule (mandatory)

1. All runtime files outside the closed shell set and explicit mirror declarations remain `instance_autonomous_runtime`.
2. Protocol validators may guard ingress/egress/path immutability/host-visible semantics, but they may not rewrite instance autonomy into template ownership by implication.
3. Wrapper refresh is allowed; runtime blanket regeneration is forbidden.

## 4) Code-landing quality standard (must be machine-enforced)

v1.6.10 is implementation-grade only if every clause above is bound to landed machine checks.

### 4.1 Required machine surfaces

1. `scripts/validate_runtime_file_boundary_governance.py`
2. `scripts/validate_semantic_term_registry.py`
3. `scripts/validate_stream_scope_semantic_integrity.py`
4. `scripts/validate_required_gate_surface_drift.py`
5. `scripts/validate_required_contract_coverage.py`
6. `scripts/validate_protocol_downsink_path_immutability.py`
7. `scripts/validate_protocol_downsink_path_write_guard.py`
8. `scripts/validate_host_transport_wiring_attestation.py`
9. `scripts/validate_compatibility_legacy_boundary.py`

### 4.2 Required CI / replay surfaces

1. `scripts/ci/run_semantic_clarity_probes_ci.sh`
2. `scripts/ci/run_downsink_path_immutability_probes_ci.sh`
3. `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
4. `scripts/ci/run_host_visible_surface_live_probes_ci.sh`

### 4.3 Fail-close quality rules

1. If governance/review docs use forbidden boundary language, semantic clarity must fail-close.
2. If `v1.6.10` docs are not present in active stream registry, boundary validation must fail-close.
3. If shell paths drift from protocol constants, boundary validation must fail-close.
4. If a mirror artifact is mislabeled as shell, boundary validation must fail-close.
5. If instance-autonomous runtime is described as protocol-generated by default, semantic clarity must fail-close.
6. If `v1.6.10` references non-landed validators as mandatory implementation, review quality is insufficient and must be corrected before closure.

## 5) Conflict-avoidance matrix (must remain true)

1. No weakening of `wrapper_only` dispatch/release requirements from v1.6.6.
2. No weakening of downsink path immutability guarantees from v1.6.8.
3. No identity-specific exception list.
4. No hardcoded per-instance path takeover.
5. No stream-topic contamination from skill supply-chain controls.
6. No “runtime/ path adjacency implies protocol ownership” compatibility branch.

## 6) Cross-verification synthesis (roundtable/vendor/reference/search/context7/openaidoc)

### 6.1 Roundtable / internal

1. v1.6.6 already proves wrapper-only host boundary ownership.
2. v1.6.8 already proves registry-first downsink governance.
3. v1.6.10 freezes the ownership boundary between those protocol controls and instance autonomy.

### 6.2 Vendor / policy-as-code

1. OPA supports machine-testable policy boundaries.
2. Sigstore supports provenance for generated artifacts without turning every downstream file into canonical source.

### 6.3 Reference / standards

1. SLSA distinguishes provenance/governance from downstream mutable runtime state.
2. W3C Trace Context and OpenTelemetry reinforce cross-hop observability without collapsing ownership domains.

### 6.4 Search / external practice guidance

1. OpenAI eval guidance reinforces pass/fail graders bound to CI.
2. OpenAI tracing guidance reinforces explicit, auditable workflow boundaries rather than implicit fallback ownership.

## 7) Acceptance gates

1. `validate_runtime_file_boundary_governance.py` => `PASS_REQUIRED`
2. `validate_semantic_term_registry.py` => `PASS_REQUIRED`
3. `validate_stream_scope_semantic_integrity.py` => `PASS_REQUIRED` or `SKIPPED_NOT_REQUIRED` when no active stream doc changes are in range
4. `validate_required_gate_surface_drift.py` => `PASS_REQUIRED`
5. `run_semantic_clarity_probes_ci.sh` => positive lane green, negative lanes red-as-expected
6. `run_downsink_path_immutability_probes_ci.sh` => green/red semantics preserved
7. Wrapper/direct-host semantics remain unchanged:
   - `wrapper_only`
   - `95% pre-send pass + 100% post-check detectability + 100% next-hop block + 100% next-hop headstamp`

## 8) Evidence and report contract

1. PR-tracked manifest: `docs/review/evidence/v1.6.10/`
2. Runtime-local replay artifacts: `activity/evidence/v1610-runtime-file-governance/<date>/`
3. Required evidence themes:
   - boundary validator output
   - semantic clarity replay
   - stream-scope replay
   - downsink path replay
   - host-visible continuity replay

## 9) One-to-one anti-forget correspondence matrix (mandatory)

1. boundary semantics must stay wired through:
   - `scripts/validate_runtime_file_boundary_governance.py`
2. semantic term hygiene must stay wired through:
   - `scripts/validate_semantic_term_registry.py`
3. stream-topic isolation must stay wired through:
   - `scripts/validate_stream_scope_semantic_integrity.py`
4. runtime-file anti-forget surface must stay wired through:
   - `scripts/validate_required_gate_surface_drift.py`
   - `scripts/validate_response_authority_consumer_semantics.py`
5. CI replay must stay wired through:
   - `scripts/ci/run_semantic_clarity_probes_ci.sh`
   - `scripts/ci/run_downsink_path_immutability_probes_ci.sh`
6. if any new v1.6.10 clause lacks the above machine surfaces, it is a fail-close anti-forget regression.

## 10) Addendum (2026-03-17): actor-session authority residue belongs to runtime-file governance

1. `session/actors/*.json` are instance-runtime authoritative state files, but their persisted schema must remain
   protocol-governed so session-primary authority is machine-readable.
2. `session/active_identity.json` and `session/mirror/current.json` are
   `protocol_controlled_mirror_artifact`, not authority sources.
3. Runtime-file governance must therefore enforce:
   - actor stores persist `last_mutation_by_session` plus explicit compatibility projection metadata;
   - actor-global switch guards read the actor-store compatibility projection directly and must not reuse
     ambiguous actor-scope selectors that return empty under multi-identity state;
   - compatibility pointers persist `authority_role=compatibility_mirror`;
   - compatibility pointers persist `authoritative_decision_allowed=false`;
   - compatibility pointers persist compatibility-projection provenance fields
     (`compatibility_projection_actor_id`, `compatibility_projection_identity_id`,
     `compatibility_projection_session_id`, `compatibility_projection_binding_ref`,
     `compatibility_projection_run_id`) so any later overwrite remains machine-auditable;
   - response/headstamp authority consumers must ignore compatibility pointers by default and may
     read them only under explicit legacy fallback mode;
   - runtime repair is done through protocol-owned generic tooling, not instance-specific patch scripts.
4. `scripts/repair_actor_session_authority_residue.py` is allowed under v1.6.10 because it repairs
   runtime-file semantics without promoting actor stores or pointers into protocol-owned source-of-truth.
5. `scripts/ci/run_semantic_clarity_probes_ci.sh` must replay negative residue detection and positive repair
   application whenever v1.6.10 changes touch actor-session runtime files or compatibility pointers.
6. response/headstamp authority-consumer drift must fail-close through:
   - `scripts/validate_response_authority_consumer_semantics.py`
   - negative probe: missing `session_id` passthrough / `resolve_actor_id()` host fallback / compatibility-pointer literal reuse.

7. strict actor-entry orchestrators that launch governed headstamp / final-emit / reply-coherence checks must not
   ship a hidden `assistant:codex` fallback; they must either use `resolve_required_protocol_actor_id()` or fail-close
   with `IP-ACTOR-ENTRY-001` before they fan out strict checks.
8. strict scan / regression orchestrators must resolve `--project-catalog` from runtime-local catalog semantics
   (`IDENTITY_CATALOG` or project `.identity/catalog.local.yaml`) and must not silently default that lane back to
   `identity/catalog/identities.yaml`.
9. shell strict-entry orchestrators are covered by the same anti-forget lane:
   - `scripts/shell_strict_entry_common.sh` is the protocol-owned resolver for runtime-local `CATALOG_PATH` and
     required actor entry in shell;
   - `scripts/validate_strict_actor_entry_semantics.py` must scan both Python orchestrators and the registered shell
     entry set (`scripts/ci/run_full_scan_target_regression_ci.sh`, `scripts/ci/run_required_runtime_gates_ci.sh`,
     `scripts/e2e_smoke_test.sh`);
   - probe / fixture shell surfaces may stay exempt only through an explicit exemption registry, never by omission;
   - fixture-only governance drift probes such as `scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh`
     remain exemption-eligible only because they mutate copied script/doc fixtures and do not launch live strict-entry
     runtime surfaces.
10. compatibility projection is diagnostic-only, never authority and never a strict green-path allowance:
    - tuple-bound session renders continue to resolve from `(actor_id,session_id)->identity_id`;
    - strict pointer / health lanes must run on session-primary truth and fail-close when shared pointers remain stale
      or when compatibility projection attempts to stay `AVAILABLE` on active surfaces;
    - diagnostic projection metadata may remain only to explain `UNAVAILABLE` / `SUPPRESSED_MULTI_IDENTITY`
      states, not to legalize cross-session drift on current runtime truth.

### 10.1 Addendum (2026-03-18): compile/replay compatibility mirror clarification

1. compile/replay metadata may read compatibility mirror; current-session authority must not.
2. generated compile/runtime examples MUST be labeled as compile-time projections from the currently resolved runtime and MUST NOT be described as standalone live authority.
3. `session/active_identity.json` and `session/mirror/current.json` may therefore appear in compiled briefs or replay metadata as compatibility context, but actor-session authority still resolves from the authoritative actor/session store.

### 10.2 Addendum (2026-03-18): compiled brief artifact class + legacy compatibility path freeze

1. `identity/runtime/IDENTITY_COMPILED.md` is frozen as a `tracked_compiled_brief_artifact`.
2. Its artifact attributes are:
   - `governed generated artifact`
   - not ordinary runtime evidence/log artifact
   - not instance-autonomous runtime state
   - not a generic `protocol_controlled_mirror_artifact`
3. Its current location `identity/runtime/IDENTITY_COMPILED.md` is frozen as a `legacy_canonical_compatibility_path`.
4. Generated compiled-brief artifacts and positive compiled-brief machine gates must use the neutral path-status term `tracked_compiled_brief_frozen_path`; the legacy term remains governance/migration taxonomy only and must not be required for pass-default compiled-brief outputs.
5. Until directory taxonomy governance separately approves a new family:
   - consumer/config/docs continue to use the current path,
   - no new canonical directory family may be created for compiled briefs,
   - no canonical path migration may be bundled into ordinary feature work.
6. `legacy_canonical_compatibility_path` may remain in governance/migration and compatibility replay surfaces during this freeze window, but it must not re-enter current-turn authority resolution, strict user-visible native-chat lanes, or pass-default compiled-brief machine gates.
7. `scripts/validate_compatibility_legacy_boundary.py` is the machine boundary guard for strict/user-visible/authority lanes, and `scripts/validate_compiled_brief_projection_boundary.py` is the machine gate that enforces `tracked_compiled_brief_frozen_path` on generated compiled-brief pass-default surfaces.
8. `identity/runtime/IDENTITY_COMPILED.md` must follow source-first generation only:
   - semantic/content changes land in governance/template/script sources first,
   - then `scripts/compile_identity_runtime.py` regenerates the compiled brief,
   - direct manual semantic editing of the compiled brief is forbidden.

### 10.3 Addendum (2026-03-23): runtime catalog metadata hygiene closure without launcher-semantic reopen

1. Raw workspace-local runtime catalog self-description is now a dedicated `v1.6.10` hygiene lane:
   - `scripts/validate_runtime_catalog_metadata_hygiene.py`
   - `scripts/repair_runtime_catalog_metadata_hygiene.py`
2. This lane exists to repair raw row underdescription such as `canonical_scope=UNKNOWN` or empty `canonical_pack_path` **without** weakening resolver truth and **without** reopening `v1.6.14` launcher semantics.
3. The closure family is now wired through the launcher-control-plane surfaces while staying semantically separate from launcher ownership:
   - `scripts/check_identity_codex_launcher_migration_closure.py` now projects `runtime_catalog_metadata_hygiene_status`;
   - `scripts/run_identity_codex_launcher_workspace_convergence.py` now performs metadata hygiene repair before launcher closure;
   - `scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh` and `scripts/ci/run_identity_codex_launcher_cross_workspace_pilot_probes_ci.sh` seed stale metadata and prove apply-time repair.
4. Required gates and readiness now consume the same metadata hygiene validator, so raw-row cleanup is no longer a chat-only or workbook-only follow-on.
5. Current closure note (2026-03-23): `python3 scripts/validate_runtime_catalog_metadata_hygiene.py --catalog ../.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --require-active --json-only` returns `PASS_REQUIRED` with `checked_identity_count=4` and `violation_count=0`.
6. Interpretation is frozen:
   - resolver truth remains authority-first;
   - raw metadata hygiene is protocol-owned and fail-close;
   - launcher convergence remains closed on its own lane;
   - future cleanup must extend this validator/repair family rather than reintroducing weaker resolver logic or launcher-semantic drift.

### 10.4 Addendum (2026-03-28): nested protocol-repo runtime shadow boundary

1. When `identity-protocol-local` is checked out under a parent workspace, authoritative runtime remains the parent
   workspace `.identity/`, not repo-root `.identity/` inside the nested protocol checkout.
2. Repo-root `.identity/`, `.identity-protocol/`, `.codex/`, `.tmp/`, and `.IDENTITY.run__*.md` are local runtime
   shadow / scratch surfaces and must remain unversioned through `.gitignore`.
3. `scripts/use_project_identity_runtime.sh` must prefer the parent project root when the protocol repo is checked
   out as a subdirectory; this keeps runtime artifacts outside protocol_root and avoids `IP-PATH-001` boundary
   failures.
4. Repo-root `.identity/` inside the nested protocol checkout may exist only as non-authoritative local runtime
   shadow / local runtime shadow, probe scratch, or compatibility workspace residue; it must not be promoted to current-turn runtime
   authority or version-controlled evidence.
5. `scripts/validate_runtime_file_boundary_governance.py` must fail-close if the nested protocol checkout loses the
   `.gitignore` runtime-shadow ignore floor or if `scripts/use_project_identity_runtime.sh` stops projecting the
   parent-project runtime selection boundary.

## 11) References

1. `docs/governance/identity-host-unique-channel-governance-v1.6.6.md`
2. `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
3. `scripts/protocol_infra_contract.py`
4. https://slsa.dev/spec/v1.0/
5. https://w3c.github.io/trace-context/
6. https://github.com/open-policy-agent/opa/tree/main/docs
7. https://github.com/sigstore/docs
8. https://developers.openai.com/api/docs/guides/evals/
9. https://developers.openai.com/api/docs/guides/evaluation-best-practices/
## 2026-03-20 Closure Addendum - temp-path and compatibility-pointer terminology

- `ISSUE-006` is closed for the repaired live surfaces by converging temp/probe allocation onto `scripts/runtime_temp_path_common.py` / `scripts/runtime_temp_path_common.sh`; `scripts/validate_runtime_temp_path_contract.py` is the machine gate.
- `ISSUE-010` is closed by renaming live compatibility payload terminology from canonical-pointer labels to `compatibility_mirror_pointer_path` / `session_pointer_compatibility_path`; `scripts/validate_compatibility_pointer_terminology.py` is the machine gate.
- These closures preserve historical replay semantics while prohibiting new live runtime drift.
