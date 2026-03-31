# Identity Control Plane MVP

contract_id: `identity_control_plane_bootstrap_mvp`  
classification: `net_new_control_plane_bootstrap`

## Scope

This MVP turns lane execution into a machine-readable control-plane object with five
minimal surfaces:

- `lane-registry`
- `preflight`
- `render`
- `ingest`
- `next-step routing`
- `lane-card-bound stream guard`

admitted_delta_only:

- control-plane MVP only
- orchestration of accepted upstream law packs and residual lanes as machine objects
- no reopen or writeback of ISSUE-040 / ISSUE-041 / ISSUE-042 / ISSUE-043 / ISSUE-044 / ISSUE-045 / ISSUE-046 / ISSUE-047 / ISSUE-048
- no broader handoff, headstamp, or continuation rewrite
- no platform-wide automation beyond this bootstrap MVP

## Execution modes

The MVP supports three first-class `execution_mode` values:

1. `split_roles`
   - architect freezes the lane card
   - executor performs mutation / validator / probe / commit
   - auditor and office remain read-only acceptance roles

2. `autonomous_reinforcement`
   - a single identity instance or expert may consume the lane card and the immutable accepted upstream law pack
   - admitted flow: `mutation -> validator -> probe -> commit -> receipt`
   - post-commit routing is automatic to async read-only audit
   - no forced architect -> closure -> audit relay

3. `bootstrap_stream`
   - a bounded stream is allowed while the control-plane surface itself is being created
   - stream must still remain lane-card-bound
   - scope lock triggers the same stream guard contraction as other lanes

## ISSUE-043 consumer linkage contract

ISSUE-043 remains `CLOSED / immutable`. The MVP may only consume it through an
`accepted_upstream_law_ref` and read-only input surfaces.

Allowed read-only consumed fields:

- `accepted_upstream_law_ref`
- `issue_id`
- `contract_id`
- `law_ref`
- `reinforcement_entry_surface`
- `reinforcement_scope_status`
- `whole_lane_completion_target`
- `whole_lane_completion_status`
- `non_owner_reinforcement_status`
- `cross_layer_completion_admission_status`
- `canonical_owner_truth_preservation_status`
- `root_semantic_redefinition_status`
- `stale_reasons`

Required read-only boundaries:

- `accepted_upstream_law_ref` is consumed as immutable upstream law metadata
- `allowed_entry_surfaces` may include `root`, `middle`, and `consumer`
- `forbidden_rewrite_markers` must forbid:
  - `owner_truth_overwrite`
  - `root_semantic_redefinition`
  - `whole_lane_reopen`
- the MVP must not write back to ISSUE-043 governance / review / workbook / register truth

## Lane schema

Every lane entry in the registry carries the following minimum schema:

- `lane_id`
- `classification`
- `status`
- `active`
- `execution_mode`
- `writer_role`
- `read_only_roles`
- `role_bindings`
- `exact_fixed_write_set`
- `read_only_input_surfaces`
- `validator_command`
- `probe_command`
- `validator_expected_status`
- `probe_expected_status`
- `warn_preservation_policy`
- `expected_terminal_status`
- `admitted_delta_only`
- `fail_close_token`
- `blocker_id`
- `next_role`
- `accepted_upstream_law_ref`
- `allowed_entry_surfaces`
- `handoff_required`
- `post_commit_acceptance_mode`
- `forbidden_rewrite_markers`
- `receipt_schema_version`

## Role bindings

The registry resolves machine roles to concrete identities:

- `architect = base-repo-architect`
- `executor = base-repo-closure-orchestrator`
- `auditor = base-repo-audit-expert-v3`
- `office = office-ops-expert`

`next_role` must therefore always be machine-resolvable to a concrete identity.

## Status policy

The minimum state machine is:

- `pending_architect`
- `architect_ready`
- `preflight_passed`
- `closure_running`
- `closure_done`
- `audit_ready`
- `audit_passed`
- `office_ready`
- `accepted`
- `fail_closed`
- `hold`

Expected validation policy is explicit per lane:

- `validator_expected_status`
- `probe_expected_status`
- `expected_terminal_status`
- `warn_preservation_policy`

This lets the control plane distinguish:

- `PASS_REQUIRED` lanes
- `PASS` lanes
- `PASS with WARN-preserved` lanes

## Receipt schema

`receipt_schema_version` is shared across `render`, `ingest`, and `stream_guard`.
The normalized receipt carries:

- `receipt_schema_version`
- `validator_result.status`
- `probe_result.status`
- `staged_paths[]`
- `commit_id`
- `blocker_receipt`
- `fail_close_token`
- `normalized_receipt`

The MVP does not ingest free-form commentary. Structured receipt payloads are
required for machine state changes.

## Script surfaces and I/O

### `scripts/control_plane_lane_preflight.py`

- input:
  - registry pointer
  - lane id
- output:
  - scope lock receipt
  - contracted `allowed_next_actions`
- registry field impact:
  - optionally updates `status -> preflight_passed`

### `scripts/control_plane_lane_render.py`

- input:
  - registry pointer
  - lane id
- output:
  - machine-visible lane card
  - role bindings
  - execution mode
  - status policy
  - receipt template
- registry field impact:
  - none

### `scripts/control_plane_lane_ingest.py`

- input:
  - structured receipt
  - registry pointer
  - lane id
- output:
  - normalized receipt
  - new status
  - routed next role
- registry field impact:
  - optionally updates `status`, `blocker_id`, and `next_role`

### `scripts/control_plane_lane_next.py`

- input:
  - registry pointer
  - lane id
  - optional status override
- output:
  - next role
  - next identity
  - suggested next status
- registry field impact:
  - none

### `scripts/control_plane_lane_stream_guard.py`

- input:
  - registry pointer
  - lane id
  - structured receipt
- output:
  - guard status
  - fail-close reasons
  - normalized receipt
- registry field impact:
  - none

## Stream guard rules

Once scope lock is active, allowed next actions shrink to:

- mutate `exact_fixed_write_set`
- run validator
- run probe
- stage `exact_fixed_write_set`
- make one isolated commit
- ingest structured receipt

After scope lock the guard must fail-close on:

- reread
- recap
- re-anchor
- whole-family reinspection
- upstream law rewrite
- ISSUE-043 truth writeback
- staged paths escaping the fixed write set

For closeout, the staged path requirement tightens from subset to exact fixed-write-set parity.
