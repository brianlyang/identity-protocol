# Protocol Remediation Audit Ledger v1.6.x — Post-closure Handoff Projection Drift

Status: historical drift repaired; current follow-on hardening not yet accepted as of 2026-04-03  
Scope: review-side protocol feedback for base protocol hardening of control-plane canonical truth, repo-local owner binding, and receipt-scoped runtime evidence  
Tracked lane context: `control_plane_protocol_feedback_instance_state_runner_hardening`

## 1. Purpose and non-goal

This note exists to keep two judgments strictly separated:

1. the **historical post-closure handoff projection drift** was real and has already been repaired; and
2. the **follow-on protocol hardening** around hardcoded identity, identity lock-in, and runtime-tuple contamination is **not yet accepted** as a live package.

This note is therefore a review-side protocol feedback and diagnosis record.
It is **not** permission to claim that the entire follow-on package is already green.

## 2. Historical repaired bug

The authoritative post-closure transition law is:

- `closure_done -> auditor`
- `suggested_next_status = audit_ready`

The historical defect was that a persisted control-plane projection drifted away from that law and
could leave a lane in an executor-facing posture after closure.
That defect was a real protocol consistency bug.

More precisely:

- the route law itself was not the bug;
- the bug was **derived-field duplication without strong consistency enforcement**;
- a persisted projection drifted away from the authoritative transition law;
- this created a false continuation surface after closure.

The historical drift has been repaired.
It must remain recorded as repaired historical context.
It must **not** be rewritten as the current front-most live blocker unless new machine-visible evidence reproduces it.

## 3. Current live problem is deeper than the historical drift

The current problem is **not** that the old handoff drift is still live.
The current problem is that the base protocol boundary is still not fully frozen across these layers:

1. **canonical role law**
   - what role-level truth may appear in canonical control-plane mappings;
2. **repo-local owner binding**
   - what concrete owner/binding metadata may exist locally without becoming canonical truth;
3. **receipt-scoped runtime evidence**
   - where concrete runtime tuple literals are allowed to exist, and under what scoping;
4. **consumer admission**
   - what helper / validator / probe / ingest paths are allowed to read, assume, or project;
5. **documentation token contract**
   - whether the protocol documentation and the validators agree on the same hardening law.

This is why the current issue must not be misdescribed as a small parameter bug.
It is not accurately reduced to a single `--identity-id` mismatch.
It is a **base protocol contract hardening gap** spanning protocol contract, mapping truth, consumer admission, and documentation agreement.

## 4. Exact machine-law judgment on hardcoded identity and identity lock-in

### 4.1 Historical bad shape

The older shape had two protocol-level defects:

1. **hardcoded concrete identity**
   - concrete identity literals were allowed to influence machine-authoritative control-plane truth; and
2. **identity lock-in**
   - canonical truth expressed not only which role should act, but also effectively froze which concrete identity must satisfy that role.

That shape is not portable enough for a durable role-based identity protocol baseline.

### 4.2 Stronger current standard

The stronger standard now required is:

> Canonical protocol truth must remain role-level, portable, and free of concrete owner, runtime tuple,
> session tuple, actor tuple, subagent literal, collaborator literal, and run-scoped identity literal.
> Concrete bindings are admitted only in explicitly marked repo-local owner-binding or receipt-scoped
> runtime-evidence surfaces. Those surfaces are non-canonical, non-portable, and may not be projected,
> copied through, normalized, or relied on as canonical truth.

### 4.3 Exact prohibition

The following are **prohibited** in canonical truth:

- hardcoded concrete `identity_id` ownership as canonical law;
- run-scoped actor/session/runtime tuple literals;
- host-local execution tuple literals pretending to be versioned protocol truth;
- static owner-binding data written as if it were portable lane law;
- any consumer success path that silently depends on such literals.

The following are **admitted**, but only under explicit scoping:

- role ownership truth at the abstract role level;
- repo-local owner-binding overlay metadata, when clearly marked non-canonical and non-portable;
- receipt/evidence surfaces, when clearly marked runtime-only and non-authoritative for canonical law.

## 5. Current machine-visible evidence on 2026-04-03

The current live evidence does **not** support saying “hardcoded identity is fully solved” or
“identity instance consumption is fully green.”

### 5.1 Validator

Command:

`python3 scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py --json-only`

Current result:

- `status = FAIL_REQUIRED`
- `failures = ["mvp_doc_tokens"]`

At the same time, several important subchecks are already green:

- `canonical_role_bindings_removed = PASS`
- `owner_binding_runtime_evidence_shape = PASS`
- `route_compatibility_via_runtime_evidence_surface = PASS`
- `runtime_tuple_literal_pollution = PASS`

This means real structural progress has occurred.
It also means the package is still **not yet accepted**, because the validator is still red on
`mvp_doc_tokens`.

### 5.2 Probe

Command:

`TMPDIR=$PWD/.tmp bash scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh`

Current result:

- shell return code = `1`
- no green success receipt was emitted in the current check

Therefore the probe surface is also **not yet accepted**.

## 6. Reply-channel green is not the same as consumer-consumption green

This distinction must be explicit because conflating the two creates semantic pollution.

The following statement is **admitted**:

- some reply-channel / rail-switch / protocol-feedback emission surfaces may already show green or
  partially green evidence.

The following statement is **not admitted**:

- “therefore the identity instance consumer side is fully green.”

That implication is not machine-justified at the current state.
As long as the current hardening validator is `FAIL_REQUIRED` and the probe is non-green,
the broader consumer-consumption surface must **not** be described as fully closed.

## 7. Current front-most live red

The current front-most live red, based on the machine-visible evidence checked here, is:

1. `mvp_doc_tokens` validator failure; and
2. non-green probe execution for `control_plane_protocol_feedback_instance_state_runner_hardening`.

Therefore:

- the front-most live red is **not** the repaired historical post-closure drift itself;
- it is **not** accurately framed as a single identity-parameter mistake;
- it is the fact that the hardening package has not yet reached full protocol-contract acceptance.

## 8. Architect-owned protocol hardening required

This problem should now be treated as an architect-owned base protocol hardening task rather than as
an endless sequence of isolated local patchlets.

The protocol layer that needs freezing is:

1. **canonical role-law contract**
   - canonical mappings may express only portable role-level truth;
2. **owner-binding overlay contract**
   - local owner binding must be explicitly non-canonical, repo-local, and non-portable;
3. **runtime-evidence contract**
   - concrete runtime tuple literals are receipt-scoped only and may not reenter canonical truth;
4. **consumer admission contract**
   - helper / validator / probe / ingest paths must not require concrete identity from canonical truth;
5. **documentation token contract**
   - machine validators and documentation must encode the same hardening rule set.

Until that base law is frozen clearly, repeated red/green churn can recur because different layers
will each believe they are enforcing the protocol while still disagreeing on what the protocol allows.

## 9. Separation from sibling open items

The following items are real but must remain separate from this note unless separately reproduced and frozen:

- protocol feedback rail-switch / emission-obligation promotion gaps;
- context compaction / reread / execution-loop residuals;
- unrelated workbook or issue-family formalization items.

Keeping these separate is necessary to avoid false causal mixing.
This note is specifically about control-plane canonical truth, owner-binding abstraction, and
runtime-evidence contamination boundaries.

## 10. Current decision

The correct current decision is:

- **historical repaired item**
  - post-closure handoff projection drift remains closed as a repaired historical bug;
- **current live hardening state**
  - structural deconcretization progress is real and machine-visible;
- **current acceptance state**
  - the follow-on hardening package is **not yet accepted**;
- **front-most reason**
  - current machine-visible failure is the unresolved `mvp_doc_tokens` validator failure together with a non-green probe surface.

## 11. Required reading discipline for future closure claims

Future closure claims for this package must obey all of the following:

- do not say hardcoded identity is fully cleared unless validator and probe are both green;
- do not say identity lock-in is solved merely because one static binding field moved out of one file;
- do not say runtime tuple pollution is solved unless canonical truth remains clean and consumers remain clean;
- do not say reply-channel green implies full consumer-consumption closure;
- do not say the package is accepted while `mvp_doc_tokens` remains red or the probe remains non-green.

## 12. Review conclusion

This repository has already advanced beyond the older, more obviously unsafe shape in which concrete
identity could sit directly in canonical control-plane truth.
That progress is real and should not be erased.

But the stronger conclusion is also required:

the base protocol hardening is **not yet finished**.
The remaining work is not to reopen the old historical drift bug, but to finish freezing the protocol
boundary between canonical role law, repo-local owner binding, receipt-scoped runtime evidence, and
consumer admission, and to bring documentation token law into exact agreement with validator/probe law.
## Closure supplement — control_plane_role_binding_overlay_hardening

The follow-on hardening above is now materialized as a machine-authoritative closure package.
This supplement records the exact control-plane split that closes the abstraction-boundary defect
without reopening the repaired historical post-closure handoff bug.

### Runtime-evidence-only + fail-close standard

This review adopts the runtime-evidence-only + fail-close standard as the active machine-law reading for this package.

- canonical protocol truth must remain role-level, portable, and free of concrete runtime bindings
- concrete runtime identity/session/transaction/checkout-instance/host-path literals are admitted only within explicitly marked runtime-evidence surfaces
- helper and validator execution path reintroduced concrete identity dependence in the half-migrated state; final closeout removes that reentry from helper / validator / probe execution paths
- any reentry, projection, copy-through, normalization, or dependency of concrete runtime literals into canonical truth must fail-close before render success, ingest success, validation success, probe success, staging success, commit success, or terminal success receipt

### Exact closure result

The current active lane is now `control_plane_role_binding_overlay_hardening`.
Machine-authoritative closure now means:

- canonical registry no longer persists `role_bindings`
- canonical lane truth continues to express role law only
- repo-local concrete binding is materialized only in explicitly marked runtime-evidence surfaces
- `route_next_role(...)` returns role-level projection plus `binding_surface` metadata only
- success projections no longer emit concrete `identity_id`
- historical control-plane lanes remain preserved and route-compatible after the split

### Exact materialized runtime-evidence surfaces

- `identity/protocol/mappings/control-plane-owner-binding.current.yaml`
- `identity/protocol/mappings/control-plane-owner-binding.v1.yaml`

Those surfaces are now explicitly marked as:

- `truth_class = owner_binding_overlay`
- `scope = repo_local`
- `portable = false`
- `runtime_evidence_surface = true`
- `runtime_evidence_class = concrete_identity_binding`
- `canonical_reentry_policy = fail_close`
- `binding_policy = receipt_scoped_runtime_evidence_only`

### Exact canonical split now in force

Canonical control-plane truth retains:

- `status -> next_role`
- `writer_role`
- `read_only_roles`
- `execution_mode`
- `scope_lock_allowed_actions`

Concrete owner selection is no longer resolved from canonical or versioned truth.
The prior defect was not only hardcoded concrete identity coupling but also identity lock-in.
Final closeout removes the remaining helper-level freeze by ensuring helper / validator / probe
logic validates role-level projections and runtime-evidence metadata only.

### Protocol-governed sidecar supplement

A subagent is treated as a governed sidecar infrastructure object, not as canonical truth.
This supplement records subagent as a governed sidecar infrastructure object and keeps that object non-canonical.
It is governed separately from:

1. collaborator identity instance
2. outer delivery surface

Protocol-governed sidecar execution therefore requires:

- work contract
- capability discovery
- closure receipt
- integration receipt
- timeout/fail-close semantics

No concrete subagent/session/transaction/checkout-instance/host-path literal may inherit or project authority back into canonical truth.

### Exact closeout surfaces

- `identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md`
- `identity/protocol/mappings/control-plane-lane-registry.current.yaml`
- `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`
- `identity/protocol/mappings/control-plane-owner-binding.current.yaml`
- `identity/protocol/mappings/control-plane-owner-binding.v1.yaml`
- `docs/review/protocol-remediation-audit-ledger-v1.6.x-post-closure-handoff-projection-drift.md`
- `scripts/control_plane_lane_registry_common.py`
- `scripts/control_plane_lane_render.py`
- `scripts/control_plane_lane_next.py`
- `scripts/control_plane_lane_ingest.py`
- `scripts/control_plane_lane_stream_guard.py`
- `scripts/validate_identity_control_plane_bootstrap_mvp.py`
- `scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh`
- `scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py`
- `scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh`
- `scripts/validate_control_plane_role_binding_overlay_hardening.py`
- `scripts/ci/run_control_plane_role_binding_overlay_hardening_probes_ci.sh`
