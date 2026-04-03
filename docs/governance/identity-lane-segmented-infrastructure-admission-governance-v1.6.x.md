# Identity lane segmented infrastructure admission governance v1.6.x

## Status

- `status`: ACTIVE
- `scope`: `v1.6.x` root infra
- `governing_issue`: `ISSUE-045`

## Governing law

Lane segmented infrastructure admission must be machine-visible, bounded, and repo-consumable.

Root, middle, and tail lane segments must each have admissible entry rules.

Continuation and takeover must consume repo-visible baton surfaces, not chat reconstruction.

Required baton fields remain fixed: `lane_id`, `governing_law`, `fixed_write_set`, `layer_state`, `next_exact_action`, `validation_bundle`, `reopen_triggers`, `commit_gate`.

Middle-layer implementation must not reopen or redefine accepted root law.

Tail truth-sync may synchronize accepted closure only.

Tail truth-sync must not reinterpret, replace, or originate accepted root law.

Tail truth-sync must not become a source of root law.

Bounded planning is admitted, but repeated pre-mutation planning / re-anchoring / compaction without mutation progress is not admitted.

## Execution-loop state fields

The following state family is machine-visible and required for `ISSUE-045`:

- `planning_budget_status`
- `scope_lock_status`
- `mutation_phase_entry_status`
- `repeated_plan_restatement_status`
- `repeated_reanchor_status`
- `repeated_compaction_without_progress_status`
- `execution_loop_status`
- `stale_reasons`

Normative interpretation:

- `planning_budget_status` must remain bounded and scope-locked once the fixed write set is known.
- `scope_lock_status` must remain locked to the admitted lane scope.
- `mutation_phase_entry_status` must become visible before repetition of planning/re-anchoring is admitted.
- `repeated_plan_restatement_status`, `repeated_reanchor_status`, and `repeated_compaction_without_progress_status` are `FAIL_REQUIRED` once mutation progress has not been entered under a locked scope.
- `execution_loop_status` must fail-close as `execution_loop_not_entering_mutation_phase` when fixed write set and scope are already locked but execution still repeats planning, reread, or compaction without entering mutation / validator / probe / commit.
- `stale_reasons` must record the fail-close reason family, including `execution_loop_not_entering_mutation_phase` where applicable.

## Ordered execution sequence

`ISSUE-045` admits one bounded execution sequence only:

1. `common`
2. `governance/review`
3. `validator`
4. `probe`
5. `workbook/register`

## Admissible segmented entry rules

### Root

- `root` entry may freeze or refine governing law, canonical owner boundary, and fail-close semantics only on authoritative repo surfaces.
- `root` entry must emit repo-visible baton state before delegated continuation is admitted.
- `root` entry is `FAIL_REQUIRED` if it depends on chat recap instead of repo-visible baton surfaces.

### Middle

- `middle` entry may implement accepted law through shared helpers, validators, probes, CI consumers, and bounded consumer absorption only.
- `middle` entry must consume the frozen baton field family without redefining governing law.
- `middle` entry is `FAIL_REQUIRED` if it reopens accepted root semantics, widens write scope beyond the admitted baton, or substitutes chat reconstruction for repo-visible state.

### Tail

- `tail` entry may synchronize accepted closure into workbook, review, ledger, issue register, or other truth-sync surfaces only after accepted upstream law exists.
- `tail` entry must preserve accepted law as received from authoritative owner docs.
- `tail` entry is `FAIL_REQUIRED` if it reinterprets, replaces, originates, or back-propagates root law through truth-sync text.

## Baton admission rules

1. Continuation is admitted only when baton state is repo-visible and bounded.
2. Chat recap may assist humans, but it is not an admitted baton surface.
3. Any takeover that cannot point to the fixed baton field family must fail closed.
4. Segment transitions must preserve one authoritative governing law across `root`, `middle`, and `tail`.

## PASS / FAIL semantics

- `PASS_REQUIRED`
  - the lane exposes one repo-visible baton family with all required fields;
  - admissible entry rules for `root`, `middle`, and `tail` are frozen on authoritative governance/review surfaces;
  - continuation can proceed without reconstructing full chat context;
  - tail truth-sync is explicitly bounded to accepted closure synchronization only.
- `FAIL_REQUIRED`
  - any required baton field is missing, renamed, or substituted with narrative-only recap;
  - any segment reopens accepted law outside its admissible scope;
  - `tail` truth-sync attempts to reinterpret, replace, or originate accepted root law;
  - continuation or takeover depends on chat reconstruction rather than repo-visible baton state.

## Canonical lane payload

The payload below freezes the authoritative baton shape for `ISSUE-045`. Paths under `fixed_write_set` include the downstream implementation surfaces that must consume this law without reopening it.

```json
{
  "lane_id": "issue_045_lane_segmented_infrastructure_admission_contract_v1",
  "governing_law": "segmented_lane_entry_and_closure_must_be_repo_visible_and_non_reinterpretive",
  "fixed_write_set": [
    "docs/governance/identity-lane-segmented-infrastructure-admission-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-segmented-infrastructure-admission.md",
    "scripts/lane_segmented_infrastructure_admission_contract_common.py",
    "scripts/validate_lane_segmented_infrastructure_admission.py",
    "scripts/ci/run_lane_segmented_infrastructure_admission_probes_ci.sh"
  ],
  "layer_state": "protocol-lane-infrastructure",
  "next_exact_action": [
    "formalize lane segmented infrastructure admission only",
    "freeze admissible entry rules for root, middle, and tail lane segments",
    "freeze required baton fields: lane_id, governing_law, fixed_write_set, layer_state, next_exact_action, validation_bundle, reopen_triggers, commit_gate",
    "fail-close tail truth-sync when it reinterprets or rewrites accepted root law"
  ],
  "validation_bundle": [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_lane_segmented_infrastructure_admission.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_lane_segmented_infrastructure_admission_probes_ci.sh"
  ],
  "execution_loop_state_fields": [
    "planning_budget_status",
    "scope_lock_status",
    "mutation_phase_entry_status",
    "repeated_plan_restatement_status",
    "repeated_reanchor_status",
    "repeated_compaction_without_progress_status",
    "execution_loop_status",
    "stale_reasons"
  ],
  "ordered_execution_sequence": [
    "common",
    "governance/review",
    "validator",
    "probe",
    "workbook/register"
  ],
  "bounded_planning_rule": "bounded planning is admitted, but repeated pre-mutation planning / re-anchoring / compaction without mutation progress is not admitted",
  "fail_close_reason": "execution_loop_not_entering_mutation_phase",
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-045 only"
}
```

## Closure effect

`ISSUE-045` is closed at the law-freeze layer once this governance document and its paired review ledger become the canonical owner surfaces for segmented lane admission. Downstream validator/probe consumers must absorb this contract through the fixed write set rather than reopening the governing law in chat.
