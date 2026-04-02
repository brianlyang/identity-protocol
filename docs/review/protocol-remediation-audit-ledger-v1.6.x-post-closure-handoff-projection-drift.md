# Protocol Remediation Audit Ledger v1.6.x — Post-closure Handoff Projection Drift

Status: Fixed on 2026-04-02 by machine-validated closeout follow-up (`d7a685a`)  
Scope: bounded control-plane remediation for `control_plane_protocol_feedback_instance_state_runner_hardening`

## Summary

A control-plane projection drift existed between the lane's post-closure semantics and
its persisted live execution contract:

- the lane had to support `closure_done -> auditor`
- the executable validator previously admitted only `architect_ready`
- the probe bundle did not prove that a closure-ingested shadow registry remained validator-admissible

This made the lane vulnerable to re-entering an executor-owned posture after closure
or to fail-closing when a valid post-closure registry snapshot was replayed.

## Fix landed

The bounded repair that landed in `d7a685a` does all of the following:

1. preserves the lane's executor-owned pre-closure state semantics;
2. admits the lane's auditor-owned `closure_done` state as a valid live machine state;
3. aligns the persisted registry row so that the live target lane now carries:
   - `status: closure_done`
   - `next_role: auditor`
4. narrows the closeout fixed-write-set contract to the machine-authoritative necessity subset;
5. extends the validator to accept both repo-root and shadow-probe relative registry pointers;
6. upgrades the lane probe so it proves validator admissibility after closure receipt ingestion.

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

The drift is no longer present in the active machine contract.
The lane is now closed in a machine-admissible post-closure state and hands off to the auditor path
without requiring executor re-entry.
