# Identity Workbook Truth Sync Governance v1.6.x

## Governing law

- `accepted_issue_closure_chain_must_be_truth_synced_into_workbook_without_family_reopen`

## Scope

- This lane truth-syncs workbook surfaces for accepted `ISSUE-040`, `ISSUE-041`, and `ISSUE-042` closure only.
- It does not reopen family semantics, expand to issue-register truth sync, or authorize any additional write surface beyond this lane's fixed write set.

## Required workbook truth surface

The workbook row for each accepted family must satisfy all of the following:

1. `status` is `CLOSED`.
2. The accepted closure commits for that family are present on the workbook row.
3. The accepted governing semantics remain present as frozen stop conditions:
   - ISSUE-040: `no card, no handoff`; `no durable execution receipt, no continuation claim`; `reopen is machine-triggered only`.
   - ISSUE-041: `closure is incomplete when teardown receipts are missing`; `child tmp/probe/runtime residue without owner binding is not admitted`; `nested governed-root replay is not admitted`; `guard cleanup deletes only machine-admitted stale residue and must not overreach live runtime`.
   - ISSUE-042: `not written = not progressed`; `not validated = not complete`; `not committed = not closed`.
4. Stale pre-closure truth such as `status: OPEN` or `pending formalization` is not admitted inside the accepted family sections.

## Validation bundle

- `TMPDIR=$PWD/.tmp python3 scripts/validate_workbook_truth_sync.py --json-only`
- `TMPDIR=$PWD/.tmp bash scripts/ci/run_workbook_truth_sync_probes_ci.sh`
