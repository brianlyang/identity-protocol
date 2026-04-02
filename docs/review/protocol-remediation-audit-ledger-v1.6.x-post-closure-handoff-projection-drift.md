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
