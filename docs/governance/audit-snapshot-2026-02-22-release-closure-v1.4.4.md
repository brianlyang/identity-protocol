# Audit Snapshot — 2026-02-22 (Release Closure v1.4.4)

## Scope

- Repository: `brianlyang/identity-protocol`
- Primary change set: PR #29
- Merge commit on `main`: `91ff6953e8ad6408110ca14fb20162d671ccee00`
- Release line: `v1.4.4 (draft)` governance hardening

## Trigger

Closure snapshot for final audit round focused on:

1. self-upgrade process authenticity
2. installer/creator plane boundary separation
3. install safety contract alignment
4. install provenance chain enforcement

## Findings -> Remediation Mapping

### 1) install safety contract vs installer behavior mismatch

- Finding: contract required `on_conflict=abort_and_explain` while compatible upgrade path was previously permissive.
- Remediation:
  - `scripts/identity_installer.py`
    - `compatible_upgrade -> abort_and_explain` by default
  - `scripts/validate_identity_install_safety.py`
    - enforces:
      - `compatible_upgrade -> abort_and_explain`
      - `fresh_install -> guarded_apply`
      - `destructive_replace -> guarded_apply + backup_ref + rollback_ref`

### 2) creator/installer plane boundary drift

- Finding: installer action path was exposed via creator wrapper, weakening separation.
- Remediation:
  - `scripts/identity_creator.py`
    - removed install dispatch path
  - installer operations must use:
    - `scripts/identity_installer.py`
    - `skills/identity-installer/SKILL.md`

### 3) operations_required treated as allowed one-of

- Finding: install provenance validator accepted single operation report.
- Remediation:
  - `scripts/validate_identity_install_provenance.py`
    - enforces recent chain evidence:
      - `plan -> dry-run -> install -> verify`
  - evidence generated under:
    - `identity/runtime/reports/install/identity-install-store-manager-*.json`

### 4) self-upgrade authenticity hardening

- Finding: report existence alone was insufficient for process authenticity.
- Remediation:
  - `scripts/execute_identity_upgrade.py`
    - emits `execution_context {generated_by, github_run_id, github_sha}`
    - emits `check_results[]` with `command/started_at/ended_at/exit_code/log_path/sha256`
  - `scripts/validate_identity_self_upgrade_enforcement.py`
    - validates report integrity and required checks against CURRENT_TASK contract
    - supports CI-bound verification:
      - `--execution-report`
      - `--require-ci-binding`
      - `--expect-github-run-id`
      - `--expect-github-sha`
  - required-gates workflow runs live update execution then validates the generated report

## CI / Validation Evidence

Local closure run:

- `bash scripts/e2e_smoke_test.sh` => PASS (25-step chain)

Key mandatory checks in chain include:

- `scripts/validate_identity_install_safety.py`
- `scripts/validate_identity_install_provenance.py`
- `scripts/validate_identity_self_upgrade_enforcement.py`
- `scripts/validate_identity_capability_arbitration.py --upgrade-report <generated>`

Cloud-side release gate requirement (final publish condition):

- `protocol-ci / required-gates` must pass on merged head
- `identity-protocol-ci / required-gates` must pass on merged head

## Residual Risk

1. Cloud required checks may be delayed at audit capture time; release announcement must wait for green status.
2. Replay/upgrade evidence still relies on repository-managed artifacts for history; real-time CI report binding is enforced in workflow path and should remain required.

## Release Readiness Statement

- Code-level and contract-level remediation: **complete**
- Audit status pending cloud checks: **Conditional Go**
- Full release statement allowed only after required checks are green.
