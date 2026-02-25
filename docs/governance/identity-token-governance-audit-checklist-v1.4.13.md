# Identity Token Governance Audit Checklist (v1.4.13)

## Plane policy

Each report must include:

1. `instance-plane status`
2. `repo-plane status`
3. `release-plane status`

Allowed states:

- `NOT_STARTED` / `IN_PROGRESS` / `BLOCKED` / `CLOSED`

Any non-closed plane => overall posture is `Conditional Go`.

## Instance-plane closure checklist

1. update report exists for target identity
2. mandatory report fields present:
   - `permission_state`
   - `writeback_status`
   - `experience_writeback.status`
   - `experience_writeback.error_code`
   - `next_action`
3. learning-loop validation passes (identity-scoped sample, no cross-identity fallback)
4. binding tuple validation passes
5. permission-state semantics pass (`--ci`)

## Repo-plane checklist

1. no cross-identity fallback in runtime validators
2. docs command contract checker (repo-plane only) passes
3. scope/path contract consistency checks pass
4. release workspace cleanliness gate remains green

## Release-plane cloud closure (strict)

Cloud closure requires all:

1. `target_branch`
2. `release_head_sha`
3. `required_gates_run_id`
4. `run.head_sha == release_head_sha`
5. required checks all success
6. `workflow_file_sha` alignment

Validator:

```bash
python3 scripts/validate_release_plane_cloud_closure.py \
  --target-branch <target_branch> \
  --release-head-sha <release_head_sha> \
  --required-gates-run-id <required_gates_run_id> \
  --run-url <run_url> \
  --workflow-file-sha <workflow_file_sha> \
  --run-head-sha <run_head_sha> \
  --run-workflow-file-sha <run_workflow_file_sha> \
  --checks-json <required_checks.json>
```

## Repo-plane command contract check

```bash
python3 scripts/docs_command_contract_check.py
```

This check is not an instance main-chain gate.

