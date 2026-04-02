# Protocol Remediation Audit Ledger v1.6.x — Post-closure Handoff Projection Drift

Status: Confirmed protocol consistency bug (`control_plane_protocol_feedback_instance_state_runner_hardening`; analysis frozen 2026-04-02 at `e4759e677a33d47bd70e99ae158c1619c872b743`; minimal repair landed in `d7a685a608220edc228f537e1e6e5b971b205dbb`)  
Scope: bounded protocol feedback for control-plane projection consistency after closure receipt

## 0) Bounded analysis context

- Resume seed: `.identity/base-repo-closure-orchestrator/runtime/state/restart-handoff-20260402T154946+0800.md`
- Runtime identity was re-resolved before judgment and remained:
  - `identity_id = base-repo-closure-orchestrator`
  - `source_layer = project`
  - `runtime_mode = local_only`
  - `catalog_path = ${PWD}/.identity/catalog.local.yaml`
  - `pack_path = ${PWD}/.identity/base-repo-closure-orchestrator`
- Authoritative nested repo for this judgment:
  - repo: `identity-protocol-local`
  - branch: `chore/v1610-runtime-file-governance`
  - HEAD: `e4759e677a33d47bd70e99ae158c1619c872b743`
- Post-analysis minimal repair commit:
  - `d7a685a608220edc228f537e1e6e5b971b205dbb` — `Close protocol-feedback lane and hand off to auditor`
- This feedback intentionally avoids repo-wide redump and stays bounded to:
  - `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`
  - `scripts/control_plane_lane_registry_common.py`
  - `scripts/control_plane_lane_ingest.py`
  - `scripts/control_plane_lane_next.py`
  - `identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md`
  - narrow commit history for the affected lane only

## 1) Executive summary

The affected lane currently carries the combination:

- `status: closure_done`
- `next_role: executor`

That state is internally inconsistent with the authoritative control-plane transition law, which already says:

- `closure_done -> auditor`
- `suggested_next_status = audit_ready`

The protocol bug is therefore not a missing abstraction and not evidence that the route resolver is conceptually wrong. It is a **post-closure handoff projection drift**: a persisted derived field (`next_role`) drifted away from the authoritative transition semantics during closure receipt ingestion.

## 2) Confirmed facts

### 2.1 Registry row still carries a stale post-closure next_role

File:

- `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`

Affected row excerpt:

```yaml
- lane_id: control_plane_protocol_feedback_instance_state_runner_hardening
  classification: existing_surface_alignment
  status: closure_done
  active: true
  expected_terminal_status: closure_done
  next_role: executor
  handoff_required: true
```

### 2.2 Route resolver already carries the correct semantic owner

File:

- `scripts/control_plane_lane_registry_common.py`

Relevant branch:

```python
elif status == "closure_done":
    role = "auditor"
    suggested = "audit_ready"
```

### 2.3 Protocol doc already states the same post-success routing

File:

- `identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md`

Frozen post-success routing meaning:

- successful closure receipt advances the lane to `status = closure_done`
- the next role must be `auditor`
- the suggested next status must be `audit_ready`

### 2.4 Historical introduction point is identified

The narrow commit trace shows:

1. `0ef4ebf25ac9efe0802e5591d847cef8d151a1d0` — `Align control-plane bootstrap with authoritative checkout binding`
   - route semantics were already correct here (`closure_done -> auditor`, `audit_ready`)
2. `22d54d3b927b0ee1f634ae9a160596e7d53e27e2` — `Author control-plane feedback instance-state runner execution contract`
   - the lane was authored in a self-consistent pre-closure state with `status: architect_ready` and `next_role: executor`
3. `3c1241499bcc7d6d8cd44a6c0c1fd72a0f38e916` — `Ingest feedback instance-state runner closure receipt`
   - the lane advanced to `status: closure_done` but retained `next_role: executor`
   - this is the confirmed drift introduction point
4. `e4759e677a33d47bd70e99ae158c1619c872b743` — `Rebaseline control-plane budget and status projections`
   - current HEAD still inherits the mismatch

## 3) Precise diagnosis

1. `route_next_role(status)` and the protocol doc remain the semantic owners of post-status handoff meaning.
2. The registry field `next_role` is a persisted projection / convenience field, not an independent law source.
3. Closure receipt ingestion updated `status` but did not refresh every dependent projection field.
4. Because some handoff consumers can read the registry row directly, the stale field can misroute continuation even while the semantic owner remains correct.
5. Root cause class: **derived-field duplication without strong consistency enforcement**.

## 4) Why this matters for anti-stuck work

This drift is small in write-set size but high in operational damage:

- it can point continuation back to the executor after executor-phase closure;
- it can create false “still waiting on executor” interpretations;
- it can seed executor-side no-op continuation or reopen loops;
- it makes the control plane emit contradictory truth at exactly the handoff boundary where liveness matters most.

This is why the issue belongs to the recent anti-stuck / continuation-hardening family rather than being dismissed as a cosmetic YAML typo.

## 5) Classification

- Confirmed bug type: protocol consistency bug
- Narrow subtype: post-closure handoff projection drift
- Primary root cause: derived-field duplication without strong consistency enforcement
- Not supported by evidence:
  - that high abstraction itself is wrong
  - that `route_next_role(...)` is semantically wrong
  - that the entire identity instance is the root cause

## 6) Required handling

### 6.1 Immediate functional repair

Patch the authoritative lane row in:

- `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`

Change:

```yaml
next_role: executor
```

to:

```yaml
next_role: auditor
```

This is the minimal correctness repair.

### 6.2 Narrow validation bundle after patch

Run only the lane-local bundle; do not reopen repo-wide inspection:

```bash
python3 scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py --json-only
TMPDIR=$PWD/.tmp bash scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh
```

Expected outcome:

- validator = `PASS_REQUIRED`
- probe bundle = `PASS`
- closure ingest replay resolves `new_status = closure_done`
- next-role resolution resolves auditor / `audit_ready` consistently

### 6.3 Structural hardening

At least one of the following must land soon after the minimal fix:

1. validator invariant: persisted `next_role` must equal `route_next_role(status).role`;
2. validator invariant: persisted `suggested_next_status` must equal the route-resolver projection whenever that field is stored;
3. ingest / write-back paths must refresh all derived handoff fields whenever `status` changes;
4. preferred longer-term cleanup: stop storing `next_role` as an editable static field and derive it from status at render time.

## 7) Confirmed versus open items

### 7.1 Confirmed

- `next_role` drift at `status: closure_done` is real.
- The drift is independent of the runtime identity source of truth.
- The confirmed introduction point is commit `3c1241499bcc7d6d8cd44a6c0c1fd72a0f38e916`.

### 7.2 Open but intentionally separated

The lane currently also shows:

```yaml
status: closure_done
active: true
```

That may or may not be correct depending on whether `active` means:

- “still tracked until audit completes”, or
- “still awaiting executor-phase work”.

This question is real but separate. It must not block the already-confirmed `next_role` repair.

## 8) Acceptance criteria

This feedback item is not fully closed until all of the following are true:

1. the registry row for `control_plane_protocol_feedback_instance_state_runner_hardening` shows `next_role: auditor` when `status: closure_done`;
2. route resolver, registry projection, and protocol doc all agree on the post-closure handoff;
3. the lane-local validator and probe bundle pass after the patch;
4. a future closure receipt replay cannot reintroduce stale `next_role: executor`;
5. future control-plane lanes with `closure_done` cannot drift silently without machine-visible failure.

## 9) Timeline appendix

- `0ef4ebf25ac9efe0802e5591d847cef8d151a1d0` — route semantics already correct
- `e8a8e00d4e6d665a6ac4bf522694cc896126fe26` — lane registered into the control plane
- `22d54d3b927b0ee1f634ae9a160596e7d53e27e2` — lane authored consistently in pre-closure state
- `3c1241499bcc7d6d8cd44a6c0c1fd72a0f38e916` — drift introduced during closure receipt ingestion
- `2697777d2d7ccf74f54dc0b7ad52723bf47fbd05` — status/path normalization landed around the same anti-stuck hardening window
- `e4759e677a33d47bd70e99ae158c1619c872b743` — current analysis head

## 10) Boundary note

This document is a review-side protocol feedback artifact only. Workbook / register / governance expansion should be handled as a separate bounded write set after the minimal repair rather than being conflated into this note.
