# Protocol Remediation Audit Ledger v1.6.x — Post-closure Handoff Projection Drift

Status: historical drift repaired; follow-on base protocol hardening accepted in the authoritative checkout as of 2026-04-03 (`add91c04e5e802b49a801ada19c1927288482a84`)  
Scope: review-side protocol feedback for base protocol hardening of control-plane canonical truth, repo-local owner binding, and receipt-scoped runtime evidence  
Tracked lane context: `control_plane_protocol_feedback_instance_state_runner_hardening`

## 1. Purpose and non-goal

This note exists to keep three judgments strictly separated:

1. the **historical post-closure handoff projection drift** was real and has already been repaired;
2. the **pre-closeout hardening checkpoint** around hardcoded identity, identity lock-in, and runtime-tuple contamination was real and was correctly judged red at that earlier checkpoint; and
3. the **current authoritative checkout state** is now machine-accepted for the scoped control-plane package after closeout validation and probe replay on 2026-04-03.

This note therefore serves both as:

- a review-side protocol feedback and diagnosis record for the pre-closeout red state; and
- a post-closeout audit ledger that records the later machine-authoritative acceptance boundary.

It is **not** permission to rewrite the old historical drift as the current blocker.
It is also **not** permission to overgeneralize the current package-level green state into a claim that every sibling consumer surface in the repository is already fully closed.

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

## 3. The then-live problem was deeper than the historical drift

At the pre-closeout checkpoint, the live problem was **not** that the old handoff drift was still live.
The then-live problem was that the base protocol boundary was still not fully frozen across these layers:

1. **canonical role law**
   - what role-level truth may appear in canonical control-plane mappings;
2. **repo-local owner binding**
   - what concrete owner/binding metadata may exist locally without becoming canonical truth;
3. **receipt-scoped runtime evidence**
   - where concrete runtime tuple literals are allowed to exist, and under what scoping;
4. **consumer admission**
   - what helper / validator / probe / ingest paths were allowed to read, assume, or project; and
5. **documentation token contract**
   - whether the protocol documentation and the validators encoded the same hardening law.

That diagnosis was correct.
It was not accurately reducible to a single `--identity-id` mismatch.
It was a **base protocol contract hardening gap** spanning protocol contract, mapping truth, consumer admission, and documentation agreement.

## 4. Exact machine-law judgment on hardcoded identity and identity lock-in

### 4.1 Historical bad shape

The older shape had two protocol-level defects:

1. **hardcoded concrete identity**
   - concrete identity literals were allowed to influence machine-authoritative control-plane truth; and
2. **identity lock-in**
   - canonical truth expressed not only which role should act, but also effectively froze which concrete identity must satisfy that role.

That shape was not portable enough for a durable role-based identity protocol baseline.

### 4.2 Stronger current standard

The stronger standard now enforced is:

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

The current authoritative checkout evidence now supports saying that the scoped control-plane hardening package is machine-accepted.
It does **not** support collapsing that package-level acceptance into a blanket statement that every sibling consumer surface is fully green.

### 5.1 Authoritative closeout commit

The current authoritative checkout materialized the closeout at:

- commit id = `add91c04e5e802b49a801ada19c1927288482a84`
- commit subject = `Deconcretize control-plane bindings into receipt-scoped runtime evidence`
- commit timestamp = `2026-04-03 01:49:43 +0800`

This commit contains the review ledger update together with the corresponding protocol, validator, helper, and probe surfaces.
That matters because the acceptance claim is not document-only; it is tied to the versioned control-plane package that validated and probed green.

### 5.2 Validators

Commands replayed in the authoritative checkout:

- `python3 scripts/validate_control_plane_role_binding_overlay_hardening.py --json-only`
- `python3 scripts/validate_identity_control_plane_bootstrap_mvp.py --json-only`
- `python3 scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py --json-only`

Current results in the authoritative checkout:

- `validate_control_plane_role_binding_overlay_hardening.py -> PASS_REQUIRED`
- `validate_identity_control_plane_bootstrap_mvp.py -> PASS_REQUIRED`
- `validate_control_plane_protocol_feedback_instance_state_runner_hardening.py -> PASS_REQUIRED`

This means the prior red state around `mvp_doc_tokens` and related half-migrated helper paths is no longer the current live state.
Those earlier failures remain historically important, but they are no longer the current machine-visible fact for this package.

### 5.3 Probes

Commands replayed in the authoritative checkout:

- `TMPDIR=/tmp bash scripts/ci/run_control_plane_role_binding_overlay_hardening_probes_ci.sh`
- `TMPDIR=/tmp bash scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh`
- `TMPDIR=/tmp bash scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh`

Current results in the authoritative checkout:

- `run_control_plane_role_binding_overlay_hardening_probes_ci.sh -> PASS`
- `run_identity_control_plane_bootstrap_mvp_probes_ci.sh -> PASS`
- `run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh -> PASS`

The protocol-feedback probe replay also covers the supplemental sidecar-oriented surfaces required by the current package, including sidecar contract replay, SSOT archival replay, sidecar cwd parity replay, and workspace state consistency replay.

## 6. Reply-channel green is not the same as consumer-consumption green

This distinction must remain explicit because conflating the two creates semantic pollution.

The following statement is **admitted**:

- the scoped control-plane package is now machine-green in the authoritative checkout.

The following statement is **also admitted**:

- reply-channel / rail-switch / protocol-feedback emission surfaces showing green are no longer, by themselves, the entire basis of acceptance; the current acceptance claim is grounded in validator + probe replay against the authoritative checkout.

The following statement is **still not admitted**:

- “therefore every broader identity instance consumer surface in the repository is fully green.”

The correct reading is narrower:

- the specific closeout package is accepted;
- the old front-most red inside this package is closed; and
- broader sibling consumer-consumption surfaces must still be judged on their own machine-visible evidence.

## 7. Current front-most decision boundary

The current front-most live red is **not** this package.
Within the scoped control-plane closeout package, the prior red has been closed by the accepted commit and green validator/probe replay.

Therefore:

- the front-most live issue is **not** the repaired historical post-closure drift itself;
- it is **not** accurately framed as a single identity-parameter mistake;
- it is **not** now the unresolved `mvp_doc_tokens` failure for this package; and
- any remaining work should be treated as a sibling or follow-on formalization item rather than as evidence that this already-accepted closeout package is still red.

## 8. Architect-owned protocol hardening outcome and residual work

This problem was correctly treated as an architect-owned base protocol hardening task rather than as
an endless sequence of isolated local patchlets.

For this package, the protocol layer that needed freezing is now materially frozen across these layers:

1. **canonical role-law contract**
   - canonical mappings express portable role-level truth only;
2. **owner-binding overlay contract**
   - local owner binding is explicitly non-canonical, repo-local, and non-portable;
3. **runtime-evidence contract**
   - concrete runtime tuple literals are receipt-scoped only and may not reenter canonical truth;
4. **consumer admission contract**
   - helper / validator / probe / ingest paths do not require concrete identity from canonical truth; and
5. **documentation token contract**
   - the active documentation and validators are now aligned for the accepted package.

The remaining architect-owned work, if opened later, should be framed more narrowly:

- further sidecar formalization beyond the current supplement;
- sibling lane formalization not covered by this accepted package; and
- broader repository governance surfaces that were intentionally kept separate from this note.

## 9. Separation from sibling open items

The following items are real but must remain separate from this note unless separately reproduced and frozen:

- protocol feedback rail-switch / emission-obligation promotion gaps beyond this accepted package;
- context compaction / reread / execution-loop residuals;
- unrelated workbook or issue-family formalization items; and
- future subagent sidecar formalization lanes that go beyond the current supplement.

Keeping these separate is necessary to avoid false causal mixing.
This note is specifically about control-plane canonical truth, owner-binding abstraction, and
runtime-evidence contamination boundaries, together with the now-accepted closeout for that package.

## 10. Current decision

The correct current decision is:

- **historical repaired item**
  - post-closure handoff projection drift remains closed as a repaired historical bug;
- **pre-closeout diagnosis**
  - the earlier red diagnosis on hardcoded identity, identity lock-in, runtime tuple contamination, and documentation drift was correct;
- **current live hardening state**
  - structural deconcretization progress has been completed and is now machine-visible in the authoritative checkout;
- **current acceptance state**
  - the follow-on hardening package is **accepted** for the scoped control-plane package; and
- **current basis**
  - validator replay is green, probe replay is green, and the acceptance is materialized in commit `add91c04e5e802b49a801ada19c1927288482a84`.

## 11. Required reading discipline for future closure claims

Future closure claims for this package must obey all of the following:

- do not say hardcoded identity was fully cleared unless validator and probe are both green in the authoritative checkout;
- do not say identity lock-in was solved merely because one static binding field moved out of one file;
- do not say runtime tuple pollution was solved unless canonical truth remains clean and consumers remain clean;
- do not say reply-channel green implies full consumer-consumption closure across unrelated surfaces;
- do not erase the fact that the package was previously red before the accepted closeout; and
- do admit that this specific package is now accepted when the claim is scoped to the accepted commit and its green validator/probe replay.

## 12. Review conclusion

This repository has now moved beyond the older, more obviously unsafe shape in which concrete
identity could sit directly in canonical control-plane truth.
That progress is real and is no longer merely provisional.

The stronger current conclusion is therefore:

- the base protocol hardening for this scoped control-plane package is now accepted;
- the old historical drift bug remains closed as historical context rather than a reopened blocker; and
- the protocol boundary between canonical role law, repo-local owner binding, receipt-scoped runtime evidence, and consumer admission has been materially frozen for this package.

The remaining work is not to reopen the old historical drift bug and not to deny the accepted state of this package.
The remaining work, if any, is to formalize sibling surfaces and deeper sidecar governance without letting those future tasks pollute the current acceptance boundary.

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
