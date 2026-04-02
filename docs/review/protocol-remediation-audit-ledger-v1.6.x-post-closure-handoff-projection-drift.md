# Protocol Remediation Audit Ledger v1.6.x — Post-closure Handoff Projection Drift

Status: historical drift repaired on 2026-04-02 by machine-validated closeout follow-up (`d7a685a`)  
Scope: bounded control-plane remediation for `control_plane_protocol_feedback_instance_state_runner_hardening`

## Framing

This note is a protocol-feedback and historical-diagnosis ledger entry.
It is **not** a claim that the authoritative repo still carries a live handoff mismatch.

The defect was historically real: a post-closure projection drift existed between the
lane's authoritative transition law and one of its persisted control-plane projections.
That drift has since been repaired. The active authoritative state now remains aligned.

## Historical bug statement

The lane's post-closure law is:

- `closure_done -> auditor`
- suggested next status = `audit_ready`

The historical defect was that a persisted control-plane projection drifted away from that
law during closeout handling, which made the lane vulnerable to one of two failures:

1. re-entering an executor-owned posture after closure; or
2. fail-closing when a valid post-closure registry snapshot was replayed.

The drift was associated with closure-ingested projection state around
`3c1241499bcc7d6d8cd44a6c0c1fd72a0f38e916`, while the bounded repair landed in
`d7a685a608220edc228f537e1e6e5b971b205dbb`.

## Repair interpretation

The bounded repair that landed in `d7a685a` does all of the following:

1. preserves the lane's executor-owned pre-closure state semantics;
2. admits the lane's auditor-owned `closure_done` state as a valid live machine state;
3. aligns the persisted registry row so that the live target lane now carries:
   - `status: closure_done`
   - `next_role: auditor`
4. narrows the closeout fixed-write-set contract to the machine-authoritative necessity subset;
5. extends the validator to accept both repo-root and shadow-probe relative registry pointers;
6. upgrades the lane probe so it proves validator admissibility after closure receipt ingestion.

## Current authoritative state

Current machine-authoritative surfaces are aligned:

- registry lane status = `closure_done`
- registry next role = `auditor`
- derived next role for `closure_done` = `auditor`
- suggested next status = `audit_ready`

Accordingly, this item should be interpreted as a repaired historical consistency bug,
not as an active live routing defect.

## Machine evidence

The following bounded checks passed after the repair:

```bash
python3 scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py --json-only
TMPDIR=/tmp bash scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh
python3 scripts/validate_control_plane_status_sync.py --json-only
```

Expected / observed outcomes:

- lane validator = `PASS_REQUIRED`
- lane probe bundle = `PASS`
- control-plane status sync = `PASS_REQUIRED`
- live next role = `auditor`
- suggested next status = `audit_ready`

## Result

The post-closure handoff projection drift is retained here as historical protocol feedback.
It no longer exists in the active machine contract, and it no longer serves as a current
front-most blocker for this lane.


## Additional structural review — canonical role law vs repo-local owner binding

A subsequent read-only audit found a **separate but related abstraction-boundary issue** in
current control-plane truth surfaces. This does **not** reopen the historical post-closure
projection drift described above, but it does explain why continuation / handoff defects can
remain fragile even after individual drift bugs are repaired.

### Read-only machine evidence

The current authoritative control-plane package still couples three different truth classes:

1. **canonical role law**
   - example: `closure_done -> auditor`
   - example: `suggested_next_status = audit_ready`
2. **repo-local owner binding**
   - example: `auditor -> base-repo-audit-expert-v3`
   - example: `executor -> base-repo-closure-orchestrator`
3. **runtime tuple / run-scoped binding exclusion policy**
   - concrete runtime tuple literals are already forbidden in canonical surfaces
   - the repo explicitly rejects run-scoped values such as `assistant:*` or `run:*`

The important detail is that the current package cleanly rejects **runtime tuple pollution**,
but it still persists **hardcoded concrete identity bindings** inside machine-authoritative
control-plane truth.

For avoidance of doubt, the admitted shape is currently:

- `role -> concrete identity_id`

and not the more abstract portable shape:

- `role -> role semantics only`

### Exact affected surfaces

Read-only audit evidence came from these authoritative files:

- `scripts/control_plane_lane_registry_common.py`
- `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`
- `scripts/validate_identity_control_plane_bootstrap_mvp.py`

Current machine facts established from those surfaces:

- `EXPECTED_ROLE_BINDINGS` maps roles directly to concrete identities:
  - `architect -> base-repo-architect`
  - `executor -> base-repo-closure-orchestrator`
  - `auditor -> base-repo-audit-expert-v3`
  - `office -> office-ops-expert`
- `route_next_role(...)` currently resolves not only the next role, but also the concrete
  `identity_id` from those bindings.
- `control-plane-lane-registry.v1.yaml` persists `role_bindings` in the canonical versioned
  registry surface.
- `validate_identity_control_plane_bootstrap_mvp.py` currently treats those concrete
  `role_bindings` as accepted machine truth rather than incidental local overlays.

This is a **hard identity binding** pattern: the concrete identity is written into
machine-authoritative control-plane truth, instead of being deferred to a distinct repo-local
overlay or runtime-local binding surface.

It also creates an **identity lock-in / identity freeze** pattern:

- canonical truth does not stop at expressing `which role owns this transition`
- canonical truth also freezes `which concrete identity must satisfy that role`
- rebinding owner resolution therefore requires editing versioned canonical truth, instead of
  swapping a repo-local owner-binding overlay

In machine-law terms, this means the current package is not only carrying hardcoded concrete
identity bindings; it is also **locking those concrete identities into canonical role flow**.

### Protocol interpretation

This means the current repo is **not internally contradicting its own present machine-law**.
The validator and the canonical registry presently agree that these concrete role bindings are
admitted. So the issue is **not** “the repo is violating its current rule.”

The issue is instead a **protocol abstraction-boundary defect**:

- canonical role law
- repo-local owner binding
- runtime tuple surfaces

are not yet cleanly separated.

### Non-ambiguous machine-law judgment

To eliminate semantic ambiguity, the exact judgment is split into two layers:

1. **current implemented machine-law compatibility**
   - **compatible**
   - reason: the current canonical registry and validator both explicitly admit
     `role_bindings` and concrete `identity_id` resolution
2. **portable role-only protocol baseline compatibility**
   - **not compatible**
   - reason: the canonical control-plane package still contains **hardcoded concrete identity
     bindings**, so the role law is not yet fully abstracted from repo-local owner binding

Therefore the correct conclusion is:

- this is **not** a claim that the current repo is violating its own present validator-admitted
  law;
- this **is** a claim that the current canonical control-plane truth is **not abstract enough**
  and still carries **hardcoded / written-in concrete identity coupling**;
- this also means the canonical layer currently exhibits **identity lock-in**, because role
  semantics and concrete identity selection are frozen together in the same authoritative truth
  surface.

That coupling creates a persistent risk surface for:

- continuation drift
- projection drift
- derived-field duplication
- post-closure next-hop confusion
- anti-loop hardening that succeeds lane-by-lane but remains globally fragile

### Current judgment

The precise judgment is:

> the current canonical control-plane package still contains **hardcoded concrete identity
> bindings** (that is, **written-in hard identity coupling** rather than pure role-only law).
> It therefore also exhibits **identity lock-in**: the protocol does not only say which role
> should act next, it also writes in which concrete identity is bound to that role inside the
> canonical control-plane truth itself.
> This is currently **machine-admitted** by the repo's present registry and validator surfaces,
> so it is **not** a direct contradiction of the present implementation.
> But it is **not abstract enough** for a portable role-only identity protocol baseline, and
> therefore should be treated as a control-plane hardening target.

### Recommended hardening

#### P0

1. **Split canonical role law from concrete owner binding**
   - canonical layer should carry role semantics only:
     - `status -> next_role`
     - `writer_role`
     - `read_only_roles`
     - `execution_mode`
   - owner binding should live in a distinct overlay surface:
     - `role -> identity_id`
     - explicitly marked as repo-local / non-portable
   - canonical v1 truth should no longer carry **hardcoded concrete identity bindings**
   - canonical v1 truth should no longer **lock concrete identities into role flow**

2. **Make continuation-critical fields strongly consistent**
   - especially:
     - `next_role`
     - `suggested_next_status`
   - admitted strategies:
     - derive only and do not persist independently, or
     - persist plus strict `persisted == derived` validation, or
     - force recomputation whenever status changes

3. **Split role routing from identity resolution**
   - `route_next_role(...)` should ideally return role semantics only
   - a separate resolver should map role -> identity binding from a designated local overlay

#### P1

4. **Remove duplicated lane-level role bindings where possible**
   - keep a single authoritative binding profile, or
   - use explicit references instead of repeated embedded mappings

5. **Split validator layers**
   - role-law validator
   - owner-binding validator
   - runtime tuple exclusion validator

6. **Promote a cross-lane invariant**
   - when `status == closure_done`, executor must never remain the next actor
   - any persisted projection that still points next-hop ownership back to executor should
     fail-close immediately

#### P2

7. **Label repo-local bindings explicitly**
   - recommended markers:
     - `scope = repo_local`
     - `truth_class = owner_binding_overlay`
     - `portable = false`

8. **Treat continuation drift and projection drift as one hardening family**
   - not as isolated lane-specific accidents only
   - this is the family most directly connected to historic dead-loop fragility

### Separation from the repaired historical bug

This structural concern should be tracked as a **follow-on hardening topic**.
It should **not** be misread as evidence that the repaired post-closure projection drift has
reopened. The historical bug above is repaired; the remaining concern is that the protocol’s
current control-plane abstraction is still tighter to repo-local owner identity than an ideal
portable baseline would allow.


## Closure supplement — control_plane_role_binding_overlay_hardening

The follow-on hardening above is now materialized as a machine-authoritative closure package.
This supplement records the exact control-plane split that closed the abstraction-boundary defect
without reopening the repaired historical post-closure handoff bug.

### Exact closure result

The current active lane is now `control_plane_role_binding_overlay_hardening`.
Machine-authoritative closure now means:

- canonical registry no longer persists `role_bindings`
- canonical lane truth continues to express role law only
- repo-local concrete owner binding is materialized only in the owner-binding overlay surfaces
- `route_next_role` semantics and concrete `identity_id` resolution are split
- historical control-plane lanes remain preserved and route-compatible after the split

### Exact materialized owner-binding overlay surfaces

- `identity/protocol/mappings/control-plane-owner-binding.current.yaml`
- `identity/protocol/mappings/control-plane-owner-binding.v1.yaml`

Those surfaces are now explicitly marked as:

- `truth_class = owner_binding_overlay`
- `scope = repo_local`
- `portable = false`
- `binding_policy = role_to_identity_binding_overlay`

### Exact canonical split now in force

Canonical control-plane truth retains:

- `status -> next_role`
- `writer_role`
- `read_only_roles`
- `execution_mode`
- `scope_lock_allowed_actions`

Concrete owner selection is now resolved only from the repo-local owner-binding overlay.
This means the prior hardcoded concrete identity bindings and identity lock-in are no longer
co-located with canonical control-plane lane truth.

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
