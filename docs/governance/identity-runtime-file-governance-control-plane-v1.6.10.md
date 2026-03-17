# Identity Runtime File Governance Control Plane (v1.6.10)

Status: Active protocol stream draft (boundary freeze, 2026-03-17)
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

## 11) Addendum (2026-03-17): actor-session authority residue belongs to runtime-file governance

1. `session/actors/*.json` are instance-runtime authoritative state files, but their persisted schema must remain
   protocol-governed so session-primary authority is machine-readable.
2. `session/active_identity.json` and `session/mirror/current.json` are
   `protocol_controlled_mirror_artifact`, not authority sources.
3. Runtime-file governance must therefore enforce:
   - actor stores persist `last_mutation_by_session` plus explicit compatibility projection metadata;
   - compatibility pointers persist `authority_role=compatibility_mirror`;
   - compatibility pointers persist `authoritative_decision_allowed=false`;
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

## 10) References

1. `docs/governance/identity-host-unique-channel-governance-v1.6.6.md`
2. `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
3. `scripts/protocol_infra_contract.py`
4. https://slsa.dev/spec/v1.0/
5. https://w3c.github.io/trace-context/
6. https://github.com/open-policy-agent/opa/tree/main/docs
7. https://github.com/sigstore/docs
8. https://developers.openai.com/api/docs/guides/evals/
9. https://developers.openai.com/api/docs/guides/evaluation-best-practices/
