# Identity Host Unique Channel Governance (v1.6.6)

Status: Active (pre-development governance freeze)  
Layer: protocol  
Scope: project-side identity runtime unique ingress/egress enforcement + per-instance wrapper contract

Execution mode: topic-level canonical SSOT for v1.6.6 host-channel closure.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for v1.6.6 host-channel closure.
2. Historical statements in v1.6.0-v1.6.5 remain valid only when not superseded by this stream.
3. Current-state judgment must prioritize machine outputs from:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/validate_protocol_unique_entry_gate.py --catalog <catalog> --identity-id <id> --operation validate --require-entry-receipt --json-only`
   - `python3 scripts/docs_command_contract_check.py`
4. Temporary runtime directories and ad-hoc logs are replay artifacts only and are never normative contract input.
5. Normative mapping entrypoints are current-pointer files only:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`

## 0.1) Terminology lock (anti-drift, mandatory)

To avoid repeated execution drift:

1. In v1.6.6, `host-channel` is a stream identifier only.
2. Canonical three-layer terminology is fixed:
   - protocol base repository: `identity-protocol-local`
   - business project repository: `<project>` (for example `weixinstore`)
   - identity instance pack: `<project>/.identity/<identity_id>/`
3. Identity instance packs include two source layers and both are in scope:
   - project layer instance: `<project>/.identity/<identity_id>/...`
   - global layer instance: `${CODEX_HOME}/.identity/<identity_id>/...`
4. Operationally, all mandatory routing refers to the **project-side identity runtime adapter + instance pack wrappers**.
5. `Host` in this document does **not** imply modifying unrelated external repositories.
6. The hard requirement is wrapper downsink and wrapper-only invocation under `.identity/{identity_id}/runtime/gate/*` (or equivalent global-layer runtime root when source layer is global).

## 1) Why v1.6.6 exists

v1.6.1 closed protocol strict-surface headstamp/egress contracts.  
v1.6.4 closed plugin monotonic fail-close semantics.  
v1.6.5 hardened platform governance and required-check surfaces.

Remaining closure gap:

1. Project-side conversation dispatch can still bypass protocol ingress/egress contracts if runtime entrypoints call session-control directly.
2. Instance packs can declare unique-entry contract in `CURRENT_TASK.json`, but runtime routing may still skip enforcement when wrappers are absent or not consumed by project-side adapter routing.
3. Result: configuration may be correct while user-visible output path is still weakly coupled.

v1.6.6 closes this by freezing one host-channel contract:

1. Instance-side wrappers are mandatory and generated.
2. Project-side runtime dispatch must call wrappers only.
3. Protocol ingress/egress scripts remain single canonical authority.

## 2) Non-negotiable contracts (no ambiguity)

### 2.0 Project conversation mandatory wrapper contract (global, no bypass)

This rule is stronger than strict-operation gate coverage:

1. Every project-side inbound conversation message must pass instance ingress wrapper first.
2. Every project-side user-visible outbound message must pass instance egress wrapper first.
3. This applies even when operation is non-mutation/non-release.
4. Any project-side route that can emit user-visible content without wrapper path is invalid.

### 2.1 Canonical protocol scripts (fixed)

1. Unique ingress (can-do gate): `scripts/required_gate_bundle_runner.py`
2. Unique egress (can-send gate): `scripts/final_emit_governed.py`
3. Any alternate script path claiming equivalent authority is invalid.

### 2.2 Instance wrapper generation contract (mandatory)

For every identity pack, init/update must materialize wrapper layer under fixed roots:

1. `.identity/{identity_id}/runtime/gate/protocol_ingress_wrapper.py`
2. `.identity/{identity_id}/runtime/gate/protocol_egress_wrapper.py`
3. `.identity/{identity_id}/runtime/gate/protocol_gateway_contract.json`

Hard rules:

1. Wrappers must call only canonical protocol scripts (2.1).
2. Wrappers must propagate `run_id`, `session_id`, `actor_id`.
3. Wrapper path and policy must be declared in `CURRENT_TASK.json`.
4. `host_dispatch_mode` and `host_release_mode` must both be `wrapper_only`.
5. Missing wrapper files in strict operations are `FAIL_REQUIRED`.

### 2.2.3 Wrapper dispatch token contract (mandatory, anti-bypass)

To prevent direct protocol-script invocation from masquerading as wrapper flow:

1. ingress wrapper must pass a fixed dispatch token when invoking `required_gate_bundle_runner.py`.
2. strict `host_ingress_wrapper` surface calls without valid token are `FAIL_REQUIRED`.
3. token drift between instance wrapper contract and protocol runner is `FAIL_REQUIRED`.
4. this check is governance anti-bypass control; it does not replace receipt tuple parity checks.

### 2.2.4 No-hardcode routing policy contract (mandatory)

To avoid script/workflow “偷接线” drift, wrapper-routing policy is contract-derived, not hardcoded:

1. strict wrapper surface label must be read from instance contract policy:
   - `protocol_host_unique_channel_contract_v1.entry_receipt_policy.required_surface_label`
2. strict wrapper token expectation must be read from instance contract:
   - `protocol_host_unique_channel_contract_v1.ingress_wrapper_dispatch_token`
3. strict wrapper provenance status expectations must be read from:
   - `entry_receipt_policy.required_wrapper_surface_status`
   - `entry_receipt_policy.required_wrapper_dispatch_token_status`
4. protocol scripts may keep backward-compatible defaults only as migration fallback; strict runs fail-close when contract fields are missing/drifted.
5. direct script or workflow hardcoded policy values are non-compliant with v1.6.6 closure.

### 2.2.1 `protocol_gateway_contract.json` minimum schema contract (mandatory)

To make v1.6.6 directly implementable without per-team interpretation drift, the generated
`.identity/{identity_id}/runtime/gate/protocol_gateway_contract.json` must include at least:

1. `schema_version`
2. `identity_id`
3. `protocol_repo_root`
4. `protocol_ingress_script` (must resolve to `scripts/required_gate_bundle_runner.py`)
5. `protocol_egress_script` (must resolve to `scripts/final_emit_governed.py`)
6. `ingress_wrapper_path`
7. `egress_wrapper_path`
8. `catalog_path`
9. `entry_receipt_policy` (`required: true`)
10. `egress_receipt_policy` (`required: true`)
11. `headstamp_policy` (`required: true`)
12. `identity_tuple_fields` (must contain `actor_id`, `session_id`, `run_id`, `work_layer`, `source_layer`)

Schema/fail-close rules:

1. `additionalProperties` must be rejected by validator in strict mode.
2. `protocol_ingress_script` and `protocol_egress_script` must be explicit paths, not inferred defaults.
3. Any missing required field above is `FAIL_REQUIRED` during init/update validation.
4. Any canonical script mismatch is `FAIL_REQUIRED` (no alias authority).

### 2.2.2 Wrapper invocation envelope contract (mandatory)

Both wrappers must support one deterministic envelope with explicit tuple propagation.

Ingress minimum input envelope:

1. `actor_id`
2. `session_id`
3. `run_id`
4. `identity_id`
5. `work_layer`
6. `source_layer`
7. `operation`
8. `payload`

Egress minimum input envelope:

1. `actor_id`
2. `session_id`
3. `run_id`
4. `identity_id`
5. `work_layer`
6. `source_layer`
7. `candidate_output`
8. `ingress_receipt`

Any project adapter format is allowed only if it losslessly maps to the same envelope before wrapper invocation.

### 2.3 Project dispatch contract (mandatory)

Project-side session entrypoints must not dispatch user messages directly to instance business scripts.

Required model:

1. Project-side runtime receives inbound message.
2. Project-side runtime invokes per-instance ingress wrapper.
3. Ingress wrapper invokes `scripts/required_gate_bundle_runner.py`.
4. Execution is blocked unless unique-entry receipt is `PASS_REQUIRED`.

### 2.3.1 Project wrapper discovery order (mandatory)

To support protocol/instance split repositories without path ambiguity:

1. Project-side runtime must first resolve wrapper contract from instance runtime declaration (from generated `CURRENT_TASK.json` field).
2. Project-side runtime may fallback to `.identity/{identity_id}/runtime/gate/protocol_gateway_contract.json` only when declaration points to the same file.
3. Project-side runtime must reject any implicit mono-repo relative-path fallback.
4. Unresolved wrapper contract path is `FAIL_REQUIRED`.

### 2.4 Project release contract (mandatory)

Any user-visible output must pass egress wrapper before release.

Required model:

1. Candidate output enters per-instance egress wrapper.
2. Egress wrapper invokes `scripts/final_emit_governed.py`.
3. Send-time/headstamp contracts must pass for current turn.
4. Egress must validate ingress receipt parity for current turn:
   - `run_id` must match
   - `session_id` must match
   - `actor_id` must match
5. Missing/mismatched receipt or headstamp is `FAIL_REQUIRED`.

### 2.4.2 Failure-code family preservation contract (mandatory)

To keep audit replay stable across streams:

1. Missing/invalid unique-entry receipt must preserve bundle-entry family (`IP-GATE-ENTRY-*`).
2. Headstamp tuple failures must preserve headstamp family (`IP-HDSTAMP-*`).
3. Actor/session tuple failures must preserve actor-session family (`IP-ASB-*`) where applicable.
4. New wrappers must not replace canonical families with ad-hoc aliases.

### 2.4.1 Headstamp continuity contract (mandatory)

1. Egress wrapper must treat first-line identity tuple and layer tuple as send-time hard gate input.
2. If first-line identity/layer tuple is missing or mismatched, outbound release is blocked.
3. Headstamp errors must use canonical family from v1.6.1 boundary (`IP-HDSTAMP-*`), not ad-hoc aliases.

### 2.5 Layer boundary contract (protocol vs instance)

1. Protocol layer defines contracts, schema, validators, and fail-close semantics.
2. Instance layer defines business behavior and parameters only.
3. Protocol layer must not embed instance business logic.
4. Instance layer must not redefine protocol canonical ingress/egress semantics.

### 2.6 Performance boundary contract

1. Project gateway must be lightweight and deterministic.
2. Latency budget applies to gateway stage itself, not approval waiting time:
   - local gateway target: `P95 <= 300ms`.
3. Any new check added to ingress/egress must include budget impact evidence before promotion.

### 2.6.1 Wrapper vs gate-profile semantics (anti-confusion)

To prevent repeated ambiguity:

1. Mandatory wrapper path and gate strictness are different dimensions.
2. `Must pass wrapper` means ingress/egress wrappers always run for project-side I/O.
3. `strict_full` means required-gate profile for strict operations (`activate/update/mutation/readiness/e2e/ci/validate/three-plane`).
4. Non-mutation project rounds may use non-strict profile where policy allows, but cannot bypass wrappers and cannot bypass egress headstamp/send-time checks.
5. Any implementation that interprets non-strict profile as wrapper bypass is invalid.

### 2.7 Stream numbering and GitHub PR binding contract (mandatory)

To keep governance/review/implementation lifecycle deterministic, every stream number must bind to one auditable PR trail:

1. Any new stream version (`v1.6.x`) must include three artifacts before implementation-closure claim:
   - governance doc (`docs/governance/...`)
   - review ledger (`docs/review/...`)
   - SSOT registry row (`identity/protocol/mappings/stream-doc-registry.current.yaml` resolved target)
2. Every stream implementation cycle must provide one machine-readable PR binding receipt:
   - `activity/evidence/<stream>/<date>/stream_pr_binding.json`
3. `stream_pr_binding.json` required fields:
   - `stream_version`
   - `repository`

### 2.8 v1.6.6 closure freeze clauses (execution-facing)

The following clauses are frozen for v1.6.6 implementation acceptance:

1. Terminology/boundary freeze
   - protocol base repo: `identity-protocol-local`
   - business project repo: `<project>`
   - identity runtime pack: `<global>|<project>/.identity/<identity_id>/`
   - all unique ingress/egress + wrapper + receipt/headstamp rules must work for both `source_layer=global` and `source_layer=project`.
2. Dual-layer unique channel
   - protocol ingress script: `scripts/required_gate_bundle_runner.py`
   - protocol egress script: `scripts/final_emit_governed.py`
   - instance ingress wrapper: `runtime/gate/protocol_ingress_wrapper.py`
   - instance egress wrapper: `runtime/gate/protocol_egress_wrapper.py`
3. Per-round mandatory path
   - inbound must go ingress wrapper first
   - user-visible outbound must go egress wrapper first
   - any non-wrapper path is fail-close by contract
4. Light/heavy split (upgrade-only)
   - light rounds: `operation=inspection|scan` with `gate_profile=inspection_targeted`
   - heavy rounds: `validate/update/activate/mutation/readiness/e2e/ci/three-plane` with `gate_profile=strict_full`
   - downgrade from heavy to targeted is forbidden; light rounds can upgrade to strict.
5. Anti-bypass hard constraints
   - `host_dispatch_mode=wrapper_only`, `host_release_mode=wrapper_only`
   - runtime three-piece gateway artifacts mandatory
   - ingress receipt tuple must include `actor_id/session_id/run_id/work_layer/source_layer`
   - strict receipt provenance must pass wrapper surface + dispatch token parity
6. Controller separation
   - `identity_creator`: generate/update protocol contracts and wrapper bindings
   - `identity_installer`: materialize/repair runtime gateway files and path bindings
   - neither controller may weaken wrapper-only semantics.
   - `pull_request_number`
   - `pull_request_url`
   - `head_branch`
   - `base_branch`
   - `head_sha`
   - `merge_status`
   - `opened_at_utc`
4. Closure boundary:
   - no PR binding receipt => stream status cannot move to `implementation_code_completed`.
   - governance/review docs without SSOT registry row are treated as draft only.

### 2.8 YAML sprawl control contract (mandatory)

To prevent control-plane file sprawl in v1.6.x streams:

1. New stream registration must reuse existing mapping files:
   - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
2. Stream-level doc onboarding must be append-only row updates in existing mappings.
3. Creating new mapping YAML files for stream registration is forbidden unless schema/version boundary requires it and governance explicitly approves it.

### 2.9 Required evidence package contract (mandatory)

For each v1.6.6 implementation round, evidence must include:

1. `activity/evidence/v166-host-channel/<date>/stream_pr_binding.json`
2. `activity/evidence/v166-host-channel/<date>/wrapper_contract_snapshot.<identity_id>.json`
3. `activity/evidence/v166-host-channel/<date>/host_channel_replay.<scenario>.json`
4. `activity/evidence/v166-host-channel/<date>/EVIDENCE_MANIFEST.<tag>.json`

The first three are required payload artifacts, and manifest is the required tuple index (`command`, `rc`, `sha256`, `timestamp`).

## 3) Four-track cross verification (frozen consensus)

### T1 Roundtable (repo machine replay)

1. Required-gate strict surfaces remain machine green.
2. Unique-entry contract validator exists and is callable in strict operations.
3. Final egress wrapper contract is enforced on protocol strict surfaces.

### T2 Vendor (official safety model)

1. OpenAI Codex approvals/security model supports boundary enforcement without disabling core model capability.
2. Strict schema-first controls align with fail-close gateway semantics.

### T3 Network/platform governance

1. GitHub required checks + merge-group model validates centralized policy gates in CI.
2. Rulesets model supports centralized enforcement layering compatible with protocol/project split.

### T4 Protocol references

1. `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`
2. `docs/governance/identity-failclose-monotonic-governance-v1.6.4.md`
3. `docs/governance/github-ruleset-super-linter-dual-layer-governance-v1.6.5.md`

### T5 Context7 references

1. Super-linter changed-files mode (`VALIDATE_ALL_CODEBASE=false`) is validated as the recommended fast-feedback baseline for governance lanes.
2. Shared `.env` configuration loading model supports deterministic lint profile reuse across local and CI surfaces.

## 4) Implementation target set (v1.6.6)

### 4.1 Protocol-repo target

1. `scripts/identity_creator.py` init/update path must generate wrapper files + contract JSON.
2. `scripts/validate_protocol_unique_entry_gate.py` must validate wrapper declaration parity when strict operation requires receipt.
3. `scripts/validate_required_gate_surface_drift.py` must detect project-side bypass surfaces where applicable.

### 4.2 Project runtime target

1. Project runtime dispatch entrypoints must call ingress wrapper only.
2. Project runtime user-visible output release must call egress wrapper only.
3. Any direct session-control dispatch without wrapper contract must be blocked.

### 4.3 Cross-repo interoperability target

1. Protocol and instance repositories may be different roots.
2. Wrapper contract must resolve protocol script paths deterministically from explicit mapping/config.
3. Relative-path assumptions tied to one mono-repo layout are invalid.

### 4.4 Governance-review-PR coherence target

1. `stream-doc-registry` must contain v1.6.6 governance/review rows before implementation claim.
2. `doc-evidence-allowlist` must include v1.6.6 strict doc evidence patterns.
3. `stream_pr_binding.json` must be updated per implementation PR round.
4. `docs_command_contract_check` must remain green after stream registration updates.

## 5) Acceptance gate (must all pass)

1. `python3 scripts/validate_control_plane_invariants.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/validate_protocol_unique_entry_gate.py --catalog <catalog> --identity-id <id> --operation validate --require-entry-receipt --json-only`
4. `python3 scripts/docs_command_contract_check.py`
5. Project replay proves no direct-bypass outbound path under target entrypoints.
6. Stream PR binding receipt exists under persistent evidence path and matches current head SHA.
7. Project non-mutation replay still produces:
   - ingress wrapper receipt present
   - egress wrapper receipt present
   - headstamp/send-time status `PASS_REQUIRED`
8. Negative probe `direct dispatch -> direct release` is `FAIL_REQUIRED`.
9. `protocol_gateway_contract.json` passes required-field schema checks from 2.2.1.
10. Evidence package in 2.9 is present and allowed by `doc-evidence-allowlist.current.yaml`.
11. Negative probe `direct required_gate_bundle_runner host_ingress_wrapper call without wrapper token` is `FAIL_REQUIRED`.

Release decision:

1. Any failure in items above blocks v1.6.6 closure claim.

### 5.1 Implementation landing snapshot (2026-03-12, protocol repo + instance pack runtime)

The v1.6.6 host-channel contract is now code-backed in protocol repo runtime tooling.

Code landing set:

1. `scripts/create_identity_pack.py`
   - adds `protocol_host_unique_channel_contract_v1` into scaffold defaults.
   - generates per-instance artifacts on init:
     - `runtime/gate/protocol_ingress_wrapper.py`
     - `runtime/gate/protocol_egress_wrapper.py`
     - `runtime/gate/protocol_gateway_contract.json`
2. `scripts/repair_contract_backfill.py`
   - auto-wires `protocol_host_unique_channel_contract_v1` for existing instances.
   - materializes wrapper/contract artifacts during `--apply` update flow.
3. `scripts/validate_protocol_unique_entry_gate.py`
   - extends unique-entry validation to include host gateway wrapper contract parity.
   - enforces runtime file existence + canonical script binding + tuple field coverage.
   - validates generated `protocol_gateway_contract.json` required fields and canonical script refs.

Serial verification snapshot:

1. `python3 scripts/repair_contract_backfill.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --identity-id base-repo-audit-expert-v3 --apply --json-only`
   - `contract_backfill_status=PASS_REQUIRED`
   - `host_gateway_contract_auto_wire_status=PASS_REQUIRED`
2. `python3 scripts/required_gate_bundle_runner.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --identity-id base-repo-audit-expert-v3 --operation validate --run-id v166-host-wrap-1773284273 --target-name skill_path_integrity --actor-id assistant:codex --resolved-work-layer instance --resolved-source-layer project --lock-state LOCK_MATCH --send-time-gate-status PASS_REQUIRED --outlet-bypass-detected false --final-emit-contract-status PASS_REQUIRED --final-emit-policy-mode tool_choice_required --final-emit-schema-status PASS_REQUIRED --json-only`
   - `bundle_status=PASS_REQUIRED`
   - `protocol_unique_entry_receipt_status=PASS_REQUIRED`
3. `python3 scripts/validate_protocol_unique_entry_gate.py ... --force-check --require-entry-receipt --json-only`
   - `protocol_unique_entry_gate_status=PASS_REQUIRED`
   - `protocol_host_gateway_contract_status=PASS_REQUIRED`
   - `protocol_host_gateway_runtime_files_status=PASS_REQUIRED`
   - `protocol_host_gateway_runtime_contract_status=PASS_REQUIRED`
4. `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`
5. `python3 scripts/validate_control_plane_invariants.py --json-only` -> `PASS_REQUIRED`
6. `python3 scripts/validate_control_plane_status_sync.py --json-only` -> `PASS_REQUIRED`
7. `python3 scripts/docs_command_contract_check.py` -> `PASS`
8. `python3 scripts/validate_doc_evidence_persistence.py --json-only` -> `PASS_REQUIRED`

Interpretation:

1. v1.6.6 no longer relies on docs-only declaration for host unique-channel wrappers.
2. Init/update paths now emit and validate wrapper contracts as executable artifacts.
3. Closure posture remains implementation-progressive until project-side runtime dispatch/release entrypoints are fully wrapper-only.

### 5.2 Audit-delta hardening addendum (2026-03-12)

To close the latest audit deltas, this stream adds:

1. **Signer policy uplift (file-secret -> env-secret capable policy)**
   - `ingress_proof_policy` / `egress_grant_policy` now support:
     - `signer_mode`
     - `signer_secret_env`
   - `runtime_env_secret` mode is accepted by ingress/egress verifiers and parity validators.
2. **Required CI reverse probes**
   - new required CI delegate: `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
   - validates both fail-close cases:
     - forged local-key ingress proof direct runner
     - forged local-key egress grant direct final emit
3. **Source-layer resolve fallback hardening**
   - `resolve_identity_context` adds repo-adjacent `.identity/catalog.local.yaml` fallback classification to avoid intermittent `source_layer=unknown` under project runtime layout.

Posture remains:

1. policy: `PASS_REQUIRED`
2. implementation: `CONDITIONAL_PASS`
3. remaining blocker: project runtime dispatcher physical wrapper-only exposure proof.

### 5.3 Audit delta follow-up (2026-03-13, serialized replay)

This round applies additional hardening and freezes current risk boundary explicitly (no over-closure claim):

Implemented:

1. `required_gate_bundle_runner.py`
   - adds wrapper-parent attestation fields into receipt:
     - `wrapper_parent_attestation_required`
     - `wrapper_parent_attestation_status`
     - `wrapper_parent_attestation_expected_path`
     - `wrapper_parent_attestation_ppid`
   - enforces parent attestation under wrapper-provenance-required operations.
2. `final_emit_governed.py`
   - adds egress wrapper-parent attestation check when `host_release_mode=wrapper_only`.
   - emits attestation status fields in final-emit payload.
3. `validate_protocol_unique_entry_gate.py`
   - validates ingress receipt parent-attestation parity on provenance-required rounds.
4. `create_identity_pack.py` + instance wrapper runtime
   - wrapper runtime now canonicalizes catalog path to absolute path before protocol script handoff.
5. `resolve_identity_context.py`
   - adds cross-cwd catalog-root fallback so project-local catalog resolution remains `source_layer=project` when launched outside project cwd.

Serialized replay conclusion for this delta:

1. Positive chain can pass under actor/session-bound context:
   - ingress wrapper `PASS_REQUIRED`
   - egress wrapper `PASS_REQUIRED`
2. Direct runner/final-emit calls without wrapper attestation fail-close.
3. Closure state remains `CONDITIONAL_PASS` because same trust-domain self-injection is still not physically eliminated:
   - if attacker controls signer secret and wrapper attestation inputs in the same runtime trust domain, full physical non-forgeability is not yet guaranteed.

### 5.4 Update-chain wrapper routing correction (2026-03-13, serialized)

This correction freezes one implementation rule to prevent parent-attestation mismatch during strict update lanes:

1. `identity_creator.py` must not direct-call canonical protocol egress in wrapper-only mode.
2. For wrapper-only identities, creator strict paths must route through instance wrappers:
   - ingress: `.identity/<identity_id>/runtime/gate/protocol_ingress_wrapper.py`
   - egress: `.identity/<identity_id>/runtime/gate/protocol_egress_wrapper.py`
3. Routed ingress envelope must not override wrapper-owned surface label:
   - canonical required surface remains `host_ingress_wrapper`.
4. `session_id` must be propagated end-to-end across creator -> wrapper -> protocol scripts.

Serialized replay outcome (base-repo-architect):

1. pre-mutation egress guard in `identity_creator update` now reaches:
   - `final_emit_guard_status=PASS_REQUIRED`
   - `egress_wrapper_parent_attestation_status=PASS_REQUIRED`
2. previous mismatch signal (`egress_wrapper_parent_attestation_parent_command_mismatch`) is not reproduced after routing correction.
3. stale report freshness (`IP-PVA-001` / `IP-REL-001`) is now treated as in-run refreshable preflight drift (warn-and-continue) instead of hard stop; downstream strict bundle gates remain authoritative blockers.

### 5.5 Attestation strictness uplift + env-forge probes (2026-03-13, serialized)

To shrink same-domain bypass surface under wrapper-only policy, this stream further tightens attestation checks and CI probes:

1. `required_gate_bundle_runner.py` ingress parent attestation:
   - requires both:
     - `IDENTITY_PROTOCOL_INGRESS_WRAPPER_PATH` exact path match
     - parent commandline structural match to expected wrapper launcher
   - removes permissive `env-only` fallback path.
   - commandline discovery now prefers runtime process API (`psutil`), with `/proc`/`ps` fallback.
2. `final_emit_governed.py` egress parent attestation:
   - same strict rule as ingress:
     - env wrapper path must match
     - parent commandline must match expected egress wrapper launcher
   - commandline discovery uses same `psutil`-first strategy.
3. `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh` adds two mandatory negative probes:
   - `runner_env_secret_forge_blocked`
   - `final_emit_env_secret_forge_blocked`
   both simulate attacker self-injecting signer env secret + forged proof/grant and must fail-close.

Serialized replay summary for this uplift:

1. new env-self-injection probes are blocked (`rc=1`) in required probe suite.
2. strict wrapper chain remains reproducible for creator update pre-mutation:
   - `final_emit_guard_status=PASS_REQUIRED`
   - `egress_wrapper_parent_attestation_status=PASS_REQUIRED`
3. stream posture remains `CONDITIONAL_PASS` until signer root trust is physically separated from same-domain caller control.

### 5.6 L3 reasoning fallback bootstrap hardening (2026-03-13, serialized)

To avoid strict update lanes being blocked by legacy minimal learning samples, this stream adds
deterministic L3 bootstrap enrichment:

1. `scripts/repair_identity_learning_sample.py`
   - upgrades bootstrap payload to include L3-minimum fields used by `RQ-035` fail-close checks:
     - attempt fields: `result_code`, `target_reached`, `no_target_reached`, `next_action`, `evidence_refs`
     - run fields: `roundtable_evidence_refs`, `vendor_evidence_refs`, `network_evidence_refs`, `reference_evidence_refs`
     - external fields: `external_source_freshness_status`, `conflict_reconciliation_note`, `source_url_set`
   - auto-repairs existing learning sample files when the file exists but misses L3-required fields.
   - preserves existing sample `run_id` when enriching an existing sample.
2. This is a protocol-side method update only (not manual instance hand-edit):
   - instance owners run repair tool; tool performs down-sunk file mutation in instance runtime path.
3. This hardening changes blocker class:
   - from "bootstrap sample structurally insufficient for strict reasoning gate"
   - to "instance still owes real runtime evidence/writeback closure" (expected for conditional posture).

### 5.7 Post-execution + prompt-lifecycle auto-repair chain (2026-03-13, serialized)

To close recurring `IP-WRB-003` and prompt lifecycle hash-drift debt without manual instance edits,
v1.6.6 adds protocol-tool-driven repair steps:

1. New repair tooling:
   - `scripts/repair_identity_prompt_runtime_state.py`
     - repairs `runtime/state/prompt_contract.json` hash binding to current `IDENTITY_PROMPT.md`.
     - patches latest upgrade report prompt lifecycle fields to keep report/runtime hash parity.
   - `scripts/repair_identity_post_execution_mandatory.py`
     - repairs latest upgrade report mandatory post-execution fields (`writeback_*`, outlet/final-emit metadata, recovery action).
     - generates deterministic degraded receipt when outlet preflight receipt is absent.
2. `scripts/identity_creator.py update` now runs both repairs with `--apply` before strict update gate bundle.
3. Governance intent:
   - instance runtime files remain the landing location (`.identity/<id>/runtime/...`);
   - mutation method remains protocol-controlled tooling (no manual hand-edit requirement).

### 5.8 Tuple-parity strictness correction + serial replay (2026-03-13, serialized)

This round closes a strict-update false blocker without relaxing wrapper-only governance semantics.

Implemented:

1. `scripts/validate_required_gate_tuple_parity.py`
   - `--require-distinct-operations` no longer implicitly enforces distinct `surface_label`.
   - distinct surface labels remain enforceable only when explicitly requested via
     `--require-distinct-surface-labels`.
2. Governance intent:
   - update/validate strict lanes compare operation distinctness without forcing probe/update
     receipts to invent non-canonical wrapper labels.
   - full-scan parity still can require distinct surface labels via explicit flag.

Serialized replay facts (base-repo-architect):

1. 5 serial wrapper-chain self-test rounds (ingress -> unique-entry -> egress) all pass:
   - run ids:
     - `v166-selftest-r1-1773390943`
     - `v166-selftest-r2-1773390946`
     - `v166-selftest-r3-1773390948`
     - `v166-selftest-r4-1773390951`
     - `v166-selftest-r5-1773390953`
   - each round:
     - `bundle_status=PASS_REQUIRED`
     - `protocol_unique_entry_receipt_status=PASS_REQUIRED`
     - `protocol_unique_entry_gate_status=PASS_REQUIRED`
     - `final_emit_guard_status=PASS_REQUIRED`
2. 5 serial deep-scan rounds are stable and deterministic:
   - each round summary remains:
     - `p0=1`, `p1=0`, `ok=0`, `m2m_fail=1`
     - three-plane overall `Conditional Go`
3. Interpretation:
   - wrapper mandatory chain is stable and reproducible in serial replay.
   - remaining red items are instance runtime-evidence closure debt (for example multimodal /
     reasoning runtime evidence), not tuple-parity surface-label false negatives.

Posture after this correction:

1. `Policy PASS`
2. `Implementation CONDITIONAL PASS`

### 5.9 Final closure round (2026-03-13, serialized 5x5 replay)

This round closes the remaining v1.6.6 scan/three-plane wrapper-bypass surface by upgrading
runtime scanners to use the same wrapper-routed execution semantics as creator strict lanes.

Implemented:

1. `scripts/full_identity_protocol_scan.py`
   - required-gate bundle calls are wrapper-routed (ingress wrapper) under wrapper-only contracts.
   - send-time compose calls are wrapper-routed (egress wrapper) under wrapper-only contracts.
   - scan session id fallback is propagated into wrapper-routed required-gate calls.
   - scan tuple parity check no longer forces distinct surface labels for scan/scan replay pair.
2. `scripts/report_three_plane_status.py`
   - required-gate bundle calls are wrapper-routed (ingress wrapper) under wrapper-only contracts.
   - send-time compose preflight is wrapper-routed (egress wrapper) under wrapper-only contracts.
   - strict three-plane session id is propagated as wrapper fallback session.

Serialized replay result (base-repo-architect):

1. Self-test (5 serial rounds):
   - run ids:
     - `v166-selftest-post-r1-1773394376`
     - `v166-selftest-post-r2-1773394378`
     - `v166-selftest-post-r3-1773394380`
     - `v166-selftest-post-r4-1773394383`
     - `v166-selftest-post-r5-1773394385`
   - each round:
     - ingress `bundle_status=PASS_REQUIRED`
     - `protocol_unique_entry_receipt_status=PASS_REQUIRED`
     - unique-entry gate `PASS_REQUIRED`
     - egress `final_emit_guard_status=PASS_REQUIRED`
2. Deep scan (5 serial rounds):
   - each round:
     - `rc=0`
     - `summary: p0=0, p1=0, ok=1`
     - `summary_m2m: fail=0`
3. Mandatory closure interpretation:
   - wrapper-routed scan/three-plane path is now aligned with creator strict path.
   - previous m2m blocker set (`IP-HDSTAMP-003`, `IP-HDSTAMP-001`, wrapper provenance drift on scan)
     is not reproduced in serialized replay.

v1.6.6 acceptance posture (this stream, frozen):

1. `Policy PASS`
2. `Implementation PASS`

## 6) External references

1. OpenAI Codex approvals and sandbox:
   - [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security/#sandbox-and-approvals)
2. OpenAI Codex action safety baseline:
   - [GitHub Action security checklist](https://developers.openai.com/codex/github-action/#security-checklist)
3. OpenAI schema strictness baseline:
   - [Function calling strict mode](https://platform.openai.com/docs/guides/function-calling#strict-mode)
4. GitHub merge queue trigger compatibility:
   - [Actions event `merge_group`](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group)
5. GitHub required-check troubleshooting:
   - [Troubleshooting required status checks](https://docs.github.com/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)
6. MCP lifecycle contract:
   - [Model Context Protocol lifecycle](https://modelcontextprotocol.io/specification/draft/basic/lifecycle)
