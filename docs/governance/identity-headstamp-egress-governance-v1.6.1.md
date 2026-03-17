# Identity Headstamp Egress Governance (v1.6.1)

Status: Draft (headstamp/HUD extraction stream from v1.6.0)  
Governance layer: protocol  
Scope: outbound user-visible headstamp and final egress control plane only  
Owner: identity protocol base-repo architect  
Execution mode: topic-level canonical SSOT for headstamp/HUD closure after v1.6.0

## 0) Extraction Directive (Mandatory)

### 0.1 Why v1.6.1 exists

1. Headstamp/HUD issues have recurred across many rounds and are no longer manageable as scattered v1.6.0 patches.
2. A dedicated stream is required to avoid repeated partial fixes and contradictory status interpretations.
3. From this document onward, headstamp/HUD governance is executed in one place only.

### 0.2 SSOT precedence for headstamp/HUD topics

1. L1 (topic SSOT): `docs/governance/identity-headstamp-egress-governance-v1.6.1.md` (this file)
2. L2 (historical baseline): `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
3. L3 (global protocol baseline): `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`

Hard rule:

1. Any new headstamp/HUD normative update must be written in v1.6.1.
2. v1.6.0 headstamp sections are frozen as historical evidence and cannot be used as active execution source.

### 0.2A Cross-stream boundary (v1.6.2 multimodal)

1. Multimodal-plugin governance is executed in:
   - `docs/governance/identity-multimodal-plugin-enforcement-governance-v1.6.2.md`
2. v1.6.1 must not absorb multimodal-plugin normative clauses.
3. If a headstamp issue references multimodal state, link to v1.6.2 evidence instead of duplicating contracts here.

### 0.3 Extracted legacy anchors (frozen references)

1. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md:502` (`4.21` headstamp pre-send hard gate)
2. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md:1152` (`ASB16-RQ-032 PARTIAL` normalization rule)
3. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md:1193` (Batch-4 headstamp omission/bypass decomposition)
4. `docs/review/protocol-remediation-audit-ledger-v1.6.md:79` (`FIX16-029` headstamp pre-send intake)
5. `docs/review/protocol-remediation-audit-ledger-v1.6.md:89` (`HOTFIX16-P0-002` headstamp continuity gap)
6. `docs/review/protocol-remediation-audit-ledger-v1.6.md:97` (`HOTFIX16-P0-010` HUD tuple hardening)

## 1) Problem Model and Recurrence Taxonomy

### 1.1 Scope definition

Headstamp/HUD issue means any failure in:

1. first-line emission (`Identity-Context` + `Layer-Context`)
2. actor/identity/session tuple consistency
3. send-time/final-egress enforcement
4. parity projection and recurrence observability

### 1.2 Recurrence families (H-series)

1. `H01`: headstamp line missing or malformed
2. `H02`: actor/identity binding mismatch
3. `H03`: first-line exists but not emitted through governed egress
4. `H04`: non-canonical outlet channel accepted
5. `H05`: final emit policy/schema mismatch
6. `H06`: strict lane accepted synthetic evidence
7. `H07`: strict lane accepted missing `--actor-id`
8. `H08`: lock/session tuple mismatch across surfaces
9. `H09`: tuple parity omitted core HUD fields
10. `H10`: three-plane/full-scan projection missing HUD tuple fields
11. `H11`: recurrence validator and send-time validator classify same defect differently
12. `H12`: direct/manual path bypasses governed compose/send-time chain
13. `H13`: workflow/script surface misses mandatory bundle args
14. `H14`: source-layer lexical drift in strict lane
15. `H15`: run binding selected by unstable default (mtime-sensitive fallback)
16. `H16`: sidecar/history noise causes false closure perception
17. `H17`: health checks green while egress contract still non-required

## 2) v1.6.1 Contract (Headstamp/Egress)

### 2.1 Single Egress SSOT

1. User-visible outbound text must pass through `scripts/final_emit_governed.py`.
2. `final_emit_governed.py` is the only L3 egress entry and internally routes to `scripts/compose_and_validate_governed_reply.py`.
3. The compose output must be validated by `scripts/validate_send_time_reply_gate.py` before release to user channel.
4. Any path that emits text without this chain is protocol violation (fail-close).

### 2.2 Canonical first-line tuple

Required first two lines:

1. `Identity-Context: actor_id=...; identity_id=...; scope=...; lock=...; source=...`
2. `Layer-Context: work_layer=...; source_layer=...`

Strict tuple invariants:

1. `actor_id`
2. `identity_id`
3. `resolved_work_layer`
4. `resolved_source_layer`
5. `lock_state`
6. `run_id_binding`

### 2.3 Strict lane actor rule

1. strict operations (`validate/readiness/e2e/ci/update/three-plane`) require explicit `--actor-id`.
2. Missing explicit actor in strict lane is immediate fail-close.
3. Fallback actor resolution is compatibility-only and cannot be promotion-grade evidence.

### 2.4 Canonical source-layer rule

1. Strict source-layer set: `{project,global}`.
2. Legacy tokens (`local/repo/env/auto`) are migration metadata only.
3. Any strict receipt using legacy source token is invalid.

### 2.5 Instance self-wiring rule (no manual parameter burden)

1. `scripts/final_emit_governed.py` must support auto context resolution when explicit flags are absent:
   - catalog: `project/.identity/catalog.local.yaml` first, then `~/.codex/.identity/catalog.local.yaml`
   - identity: actor binding -> session active pointer -> catalog active/default fallback
   - actor: `--actor-id` -> `CODEX_ACTOR_ID` -> `assistant:codex`
2. Any unresolved/ambiguous auto context is `FAIL_REQUIRED` and must not emit reply body.
3. Strict surfaces can pass explicit flags for determinism, but runtime default path must be auto-wirable for instance autonomy.

## 3) Error Family Convergence

### 3.1 Canonical family (v1.6.1 required)

1. `IP-HDSTAMP-001` -> headstamp missing or malformed
2. `IP-HDSTAMP-002` -> actor/layer binding mismatch
3. `IP-HDSTAMP-003` -> pre-send receipt missing

### 3.2 Compatibility alias mapping (migration-only)

1. `IP-ASB-STAMP-SESSION-*` and `IP-FE-*` are legacy aliases only.
2. Promotion-grade payload field `error_code` must emit canonical `IP-HDSTAMP-*` only.
3. Legacy aliases may be retained in `legacy_error_code`/`compat_error_code` for replay migration, but cannot replace canonical `error_code`.
4. Mixed families in same surface for same defect are treated as non-converged.

## 4) Mandatory Control-Plane Wiring Matrix

| Control | Script | Mandatory surfaces |
| --- | --- | --- |
| final egress single entry | `scripts/final_emit_governed.py` | creator/readiness/e2e/full-scan/three-plane/ci |
| governed compose internal stage | `scripts/compose_and_validate_governed_reply.py` | internal only (must not be used as surface entry) |
| send-time hard gate | `scripts/validate_send_time_reply_gate.py` | creator/readiness/e2e/full-scan/three-plane/ci |
| first-line validator | `scripts/validate_reply_identity_context_first_line.py` | creator/readiness/e2e/full-scan/three-plane/ci |
| recurrence closure | `scripts/validate_headstamp_recurrence_closure.py` | scan/three-plane/ci |
| tuple parity | `scripts/validate_required_gate_tuple_parity.py` | three-plane/full-scan/ci |
| strict surface drift/arg contract | `scripts/validate_required_gate_surface_drift.py` | ci + local preflight |

## 5) Acceptance Matrix (Promotion-Grade)

### 5.1 Positive

1. governed compose + explicit actor + canonical outlet + live evidence -> `PASS_REQUIRED`

### 5.2 Negative

1. missing/malformed first line -> `FAIL_REQUIRED` + `IP-HDSTAMP-001`
2. actor tuple mismatch -> `FAIL_REQUIRED` + `IP-HDSTAMP-002`
3. missing pre-send receipt -> `FAIL_REQUIRED` + `IP-HDSTAMP-003`
4. non-canonical outlet -> `FAIL_REQUIRED` (`final emit channel contract`)
5. strict lane without actor -> `FAIL_REQUIRED` (`actor explicitness contract`)

### 5.3 Cross-surface parity

1. `validate` vs `three-plane` receipts must agree on core tuple fields.
2. Any mismatch is release blocker.

## 6) Current Open Blockers (as-of 2026-03-09)

1. Historical note: this round opened with single-egress enforcement not yet guaranteed for every assistant-visible path outside governed compose invocation.
2. Headstamp error-family convergence on strict control plane is **closed** (`error_code` canonicalized to `IP-HDSTAMP-*`).
3. Some status surfaces can still appear green while headstamp closure is not promotion-grade complete (instance/business debt remains out of protocol scope).

### 6.1 Closure Update (as-of 2026-03-10)

1. Protocol strict surfaces now pass single-egress hard gate (`validate_required_gate_surface_drift` = `PASS_REQUIRED`), so v1.6.1 protocol-layer egress closure is no longer blocked by missing wrapper enforcement.
2. Remaining residuals are instance/business replay debts, not protocol control-plane wiring gaps.

Status boundary:

1. `SPEC_READY / PENDING_INTAKE` remains valid.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

## 7) Four-Track Cross Verification (Roundtable Model)

1. `T1 governance`: this file + v1.6.0 frozen anchors are consistent.
2. `T2 vendor`: MCP lifecycle supports explicit initialization/negotiation before action; aligns with pre-send hard gate strategy.
3. `T3 reference`: OpenAI Codex Skills emphasizes explicit input/output and trigger validation; aligns with strict egress contract.
4. `T4 replay`: promotion requires positive/negative/parity replay receipts under current head SHA.

Reference links:

1. `https://modelcontextprotocol.io/specification/draft/basic/lifecycle`
2. `https://developers.openai.com/codex/skills/#best-practices`
3. `https://developers.openai.com/codex/agent-approvals-security/#sandbox-and-approvals`
4. `https://agentskills.io/specification`

## 8) Execution Policy (No More Scatter)

1. All headstamp/HUD protocol changes, replay notes, and closure decisions must be appended to v1.6.1 governance + v1.6.1 review ledger.
2. v1.6.0 keeps historical text for traceability but cannot receive new headstamp normative clauses.
3. New discussions about headstamp/HUD opened in other docs are invalid unless linked back to this v1.6.1 stream.

## 9) Round-30.3 Addendum — canonical error-family convergence closure

### 9.1 Scope

1. Stream: v1.6.1 headstamp/HUD control-plane.
2. Objective: remove mixed canonical/compatibility error families from strict emit path.
3. Non-goal: instance business report debt (`IP-WRB-*`, prompt lifecycle) remediation.

### 9.2 Protocol patch set (strict surfaces)

1. Canonical mapping centralized in `scripts/headstamp_error_family_common.py`.
2. Strict validators/wrappers now emit canonical `IP-HDSTAMP-*` as `error_code`:
   - `scripts/validate_send_time_reply_gate.py`
   - `scripts/validate_reply_identity_context_first_line.py`
   - `scripts/compose_and_validate_governed_reply.py`
   - `scripts/final_emit_governed.py`
   - `scripts/validate_headstamp_recurrence_closure.py`
   - `scripts/validate_layer_intent_resolution.py`
3. Projection classifiers include canonical family:
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`

### 9.3 Four-track cross verification (roundtable/vendor/reference/replay)

1. `T1 governance`: canonical family is now explicit SSOT for `error_code`.
2. `T2 vendor`: MCP lifecycle “initialize/validate before action” stays aligned with pre-send fail-close.
3. `T3 reference`: Codex/Skills explicit I/O validation remains aligned with single governed egress gate.
4. `T4 replay`: positive/negative recurrence probes replayed under persistent evidence root:
   - `activity/evidence/v161-headstamp-convergence/2026-03-09/`

### 9.4 Acceptance snapshot

1. `final_emit_governed.positive.base-repo-architect` -> `PASS_REQUIRED` (rc=0).
2. `final_emit_governed.negative.nongoverned.base-repo-architect` -> `FAIL_REQUIRED` + `IP-HDSTAMP-003`.
3. `send_time_gate.negative.inline.base-repo-architect` -> `FAIL_REQUIRED` + `IP-HDSTAMP-003`.
4. `compose_actor_mismatch.base-repo-architect` -> `FAIL_REQUIRED` + `IP-HDSTAMP-002`.
5. `headstamp_recurrence.base-repo-architect` -> `PASS_REQUIRED` (rc=0).

### 9.5 Cross-surface replay (three-plane/full-scan, strict actor/session bound)

1. `report_three_plane_status` replay under explicit actor/session binding:
   - actor: `assistant:codex`
   - session: `run:asb-m2m-hotfix-20260309`
   - result: rc=0, `m2m_binding_closure_status=PASS`, release remains `Conditional Go` due release-plane preconditions (non-headstamp scope).
2. `full_identity_protocol_scan --scan-mode target --target-source-layer project` replay under same actor/session binding:
   - result: rc=0, `summary.ok=1`, `summary_m2m.pass=1`.
3. `IP-ASB-STAMP-SESSION-*` / `IP-FE-*` no longer appear in these replay outputs as surfaced defect codes; headstamp negatives are canonicalized to `IP-HDSTAMP-*`.
4. Evidence paths:
   - `activity/evidence/v161-headstamp-convergence/2026-03-09/three_plane.base-repo-architect.json`
   - `activity/evidence/v161-headstamp-convergence/2026-03-09/full_scan_target.base-repo-architect.json`
   - `activity/evidence/v161-headstamp-convergence/2026-03-09/legacy_code_presence_scan.txt`

## 10) Stream Continuity Alias Pointers

1. This stream must keep its protocol references pointer-driven (not version-literal coupled).
2. Required alias anchors for v1.6.1:
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
3. Versioned snapshots can still appear as historical evidence, but normative wiring must resolve through these current aliases.

## 11) Post-v1.6.6 deepened interpretation for v1.6.1 (2026-03-13)

This section freezes the lessons learned from the v1.6.6 unique-channel closure and
reinterprets v1.6.1 with execution-grade semantics.

### 11.1 Core reframing

1. Missing HUD/headstamp is treated as an execution-path contract violation, not a text-formatting issue.
2. `send-time` validation alone is necessary but not sufficient for recurrence closure.
3. Headstamp continuity becomes reliable only when inbound and outbound are both wrapper-bound in the same round.

### 11.2 Execution invariants inherited from v1.6.6

1. Every inbound round must pass instance ingress wrapper before business action.
2. Every user-visible outbound must pass instance egress wrapper before release.
3. `wrapper_only` dispatch/release modes must be enforced as fail-close, not declaration-only.
4. Receipt tuple consistency (`run_id/session_id/actor_id`) is mandatory across ingress -> gate -> egress.

### 11.3 v1.6.1 ownership after v1.6.6 closure

1. v1.6.1 remains the canonical semantic owner for headstamp/HUD error family (`IP-HDSTAMP-*`) and send-time gate meaning.
2. v1.6.6 provides the execution-channel closure that guarantees those semantics are reached on every round.
3. Therefore, v1.6.1 semantic closure and v1.6.6 channel closure are coupled, not competing streams.

### 11.4 Operational interpretation lock

1. If a user-visible reply appears without HUD/headstamp, the round must be treated as invalid and escalated as contract breach.
2. Manual workaround outside protocol tooling is non-compliant.
3. Remediation path must stay tool-driven (`identity_creator` / `identity_installer` / `repair_contract_backfill`) and pointer-resolved.

### 11.5 Status statement (cross-stream)

1. v1.6.1 is the semantic SSOT for headstamp/HUD.
2. v1.6.6 is the channel-enforcement closure for per-round mandatory entry/egress routing.
3. Acceptance interpretation for future audits must require both dimensions together:
   semantic correctness (v1.6.1) + transport non-bypassability (v1.6.6).

## 12) Cross-stream coupling re-audit (v1.6.1 × v1.6.6, 2026-03-13)

This section records a direct replay to verify that v1.6.6 acts as the execution
deepening base for v1.6.1 headstamp semantics.

### 12.1 Re-audit objective

1. Prove that headstamp/HUD semantics are not only validator-green but also wrapper-delivered per round.
2. Prove that v1.6.1 and v1.6.6 are composable in the same actor/session/run tuple.

### 12.2 Serialized replay tuple

1. identity: `base-repo-architect`
2. actor/session: `assistant:codex` / `session-wrapper-chain`
3. run id: `v161-v166-link-audit-20260313-2`
4. source/work layer: `project` / `protocol`

### 12.3 Observed machine outcomes

1. ingress wrapper (`operation=scan`) returned:
   - `bundle_status=PASS_REQUIRED`
   - `protocol_unique_entry_receipt_status=PASS_REQUIRED`
   - `wrapper_surface_status=PASS_REQUIRED`
   - `wrapper_dispatch_token_status=PASS_REQUIRED`
   - `wrapper_dispatch_proof_status=PASS_REQUIRED`
   - `wrapper_parent_attestation_status=PASS_REQUIRED`
2. unique-entry validator (`--require-entry-receipt`) returned:
   - `protocol_unique_entry_gate_status=PASS_REQUIRED`
   - `protocol_host_gateway_contract_status=PASS_REQUIRED`
   - `protocol_host_gateway_runtime_files_status=PASS_REQUIRED`
   - `protocol_host_gateway_runtime_contract_status=PASS_REQUIRED`
3. v1.6.1 recurrence validator (`operation=scan`) returned:
   - `headstamp_recurrence_closure_status=PASS_REQUIRED`
   - `dynamic_replay_status=PASS_REQUIRED`
   - canonical negative families remained `IP-HDSTAMP-*`
4. egress wrapper (same run + ingress receipt) returned:
   - `send_time_gate_status=PASS_REQUIRED`
   - `final_emit_guard_status=PASS_REQUIRED`
   - `egress_wrapper_parent_attestation_status=PASS_REQUIRED`
   - `outlet_channel_id=final_emit_governed`

### 12.4 Coupling interpretation

1. v1.6.6 is confirmed as execution-channel foundation: it enforces wrapper-only ingress/egress path and tuple binding.
2. v1.6.1 is confirmed as semantic foundation: it governs HUD/headstamp and canonical error-family behavior.
3. Combined result:
   - semantic pass is delivered through non-bypass transport path in the same round.
   - this closes the historical gap where headstamp could be “declared green” but not transport-bound.

### 12.5 Boundary note

1. Strict-operation failures unrelated to headstamp semantics (for example multimodal/runtime evidence debts) remain independent tracks.
2. Such debts do not invalidate this coupling proof, but they still block their own strict lanes by fail-close policy.

## 13) Strict-default first-line evidence fail-close (2026-03-15)

### 13.1 Root-cause closure statement

1. A strict operation could invoke `validate_reply_identity_context_first_line.py` with `--force-check` but without `--enforce-first-line-gate`.
2. In that path, empty reply evidence (`reply_sample_count=0`) could pass, which created a loophole for HUD/headstamp omission in strict lanes.
3. This loophole is classified as a v1.6.1 semantic breach (`H01` + strict fail-close violation).

### 13.2 Normative rule (MUST)

1. For strict operations (`activate/update/mutation/readiness/e2e/ci/validate/three-plane`), first-line evidence gate is mandatory by default.
2. Missing reply evidence in strict operation MUST return:
   - `reply_first_line_status=FAIL_REQUIRED`
   - `error_code=IP-HDSTAMP-001`
   - `stale_reasons` containing `reply_evidence_missing`
3. `--enforce-first-line-gate` remains supported, but strict-default enforcement no longer depends on that explicit flag.

### 13.3 Regression prevention

1. CI gateway trust-boundary probes MUST include a negative case where strict operation omits first-line evidence and is blocked.
2. Surface-drift validator MUST assert this probe invocation exists, so future refactors cannot silently remove it.

## 14) Three-plane host-visible precheck run-id closure (2026-03-16)

### 14.1 Problem statement

1. `three-plane` strict execution could enter send-time gate with host-visible post-check state seeded by a stale recovery run id.
2. This created deterministic false red on headstamp path:
   - `IP-HDSTAMP-003`
   - stale reasons containing `host_visible_surface_live_channel_run_id_mismatch:*`.
3. Required-gate bundle could also consume a non-session run token, amplifying tuple drift in strict lanes.

### 14.2 Normative closure rules (MUST)

1. `report_three_plane_status.py` MUST derive strict run binding from session tuple first:
   - `session_id=run:<id>` => run token `<id>`.
2. Before compose/send-time checks, three-plane MUST run host-visible post-check recovery with the same tuple:
   - `recover_host_visible_post_check_state --operation three-plane --actor-id --session-id --run-id <session-derived>`.
3. Required-gate bundle invocations inside three-plane MUST inherit:
   - session-derived run token (highest priority),
   - execution report tuple pointer (`--report-selected-path`) when available.

### 14.3 Fail-close boundary

1. If host-visible recovery fails (`recovery_status=FAIL_REQUIRED`), three-plane remains blocked.
2. This is infrastructure fail-close; no identity-specific allowlist or manual receipt editing is permitted.

### 14.4 Non-hardcode guarantee

1. Closure uses tuple-derived tokens and runtime report path fallback.
2. No identity id literal pinning and no absolute-path hardcoding is introduced.

## 15) Operator envelope template + response stamp profile materialization freeze (2026-03-17)

### 15.1 Problem statement

1. Shared stamp rendering already existed, but `CURRENT_TASK.json` did not consistently materialize `response_stamp_profile`.
2. This left disclosure/default template behavior split across governance text and renderer defaults, instead of a runtime SSOT.
3. Chat/operator-visible surfaces also lacked a shared outer envelope for:
   - visible `Display-Headstamp`
   - machine-readable `Machine-Verification`

### 15.2 Normative closure rules (MUST)

1. Every generated/backfilled identity `CURRENT_TASK.json` MUST materialize `response_stamp_profile`.
2. Default governed user-visible profile is frozen as:
   - `enabled=true`
   - `format=structured_block`
   - `audience_mode=external`
   - `redaction_policy=strict`
   - `template_ref=identity/protocol/plugins/templates/response-stamp.operator_dual_segment_v1.json`
   - `on_mismatch=blocker_receipt`
   - `disclosure_level=standard`
3. `response_stamp_profile` remains presentation-only and MUST NOT weaken first-line gate, authority resolution, or next-hop admission semantics.

### 15.3 Shared operator envelope

1. v1.6.1 freezes a shared operator envelope template:
   - line 1: `Display-Headstamp: <canonical external stamp>`
   - line 2: `Machine-Verification: <ordered machine fields>`
2. The canonical template file is:
   - `identity/protocol/plugins/templates/response-stamp.operator_dual_segment_v1.json`
3. Shared rendering MUST reuse:
   - `scripts/response_stamp_common.py`
   - `scripts/render_identity_response_stamp.py`
4. Identity instances may supply runtime values and wiring only; they MUST NOT fork literal layout or field ordering per identity.

### 15.4 Machine-verification segment boundary

1. `Machine-Verification` is an operator envelope segment, not a replacement for canonical governed artifact internals.
2. Governed reply artifact first line remains the raw `Identity-Context: ... | Layer-Context: ...` stamp.
3. Operator envelope machine fields must reuse existing protocol field names, especially:
   - `display_headstamp_identity_id`
   - `authoritative_identity_id`
   - `headstamp_consistency_status`
4. New synonymous truth fields are forbidden.

### 15.5 Regression prevention

1. `scripts/validate_response_stamp_operator_envelope.py` is the shared validator for the operator envelope.
2. `scripts/ci/run_required_runtime_gates_ci.sh` MUST invoke that validator after `render_identity_response_stamp.py`.
3. `scripts/validate_required_gate_surface_drift.py` MUST guard this CI wiring so template validation cannot silently disappear.

### 15.6 Controlled-runtime visible reply envelope closure (2026-03-17)

1. Shared operator envelope rendering must not stop at stamp JSON generation; controlled runtime reply emitters must reuse it for user-visible output.
2. `scripts/compose_and_validate_governed_reply.py` and `scripts/final_emit_governed.py` MUST emit the visible reply through:
   - `render_visible_reply_with_operator_envelope(...)`
3. `scripts/create_identity_pack.py` session-chain wrapper materialization MUST preserve the shared envelope fields from final emit:
   - `display_headstamp_line`
   - `machine_verification_line`
   - `operator_envelope_lines`
   - `visible_reply_preview`
   and MUST print the propagated `visible_reply` instead of reconstructing a new literal locally.
4. Machine-verification payloads on controlled runtime surfaces must use the current-surface-specific field:
   - `current_surface_native_machine_attested`
   instead of generic synonyms.
5. Canonical first-line semantics remain machine-owned; operator envelope is the user-visible outer segment and MUST NOT create a new authority source.
