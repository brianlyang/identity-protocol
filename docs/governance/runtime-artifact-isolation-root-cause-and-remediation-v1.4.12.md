# Runtime Artifact Isolation — Root Cause & Remediation (v1.4.12)

## Problem statement

Runtime execution artifacts repeatedly polluted base-repository working trees (`identity/runtime/...`), causing:
- noisy diffs and audit drift,
- reduced review signal quality,
- repeated false-positive/false-negative release checks.

This was not user-error only; it was primarily a **default path design issue**.

## Root-cause analysis

1. Multiple core scripts used repository-local defaults:
   - report/log/metrics/examples defaults pointed to `identity/runtime/...`.
2. Some flows wrote compatibility mirrors to repository paths by default.
3. .gitignore coverage was partial and did not cover all real write surfaces.
4. e2e/readiness workflows lacked a dedicated clean-workspace gate.

## Remediation implemented in this batch

### A) Runtime output root hardening
- `scripts/execute_identity_upgrade.py`
  - Introduced runtime output root resolver with writable fallback chain:
    1) `IDENTITY_RUNTIME_OUTPUT_ROOT`
    2) `<resolved_pack_path>/runtime`
    3) `<repo>/.codex/identity/runtime/<identity-id>`
    4) `/tmp/identity-runtime/<identity-id>`
  - Upgrade reports/logs/arbitration artifacts now write to runtime output root.

### B) Identity creator hardening
- `scripts/identity_creator.py`
  - `update` and `heal` default out-dir switched to `/tmp/...` safe defaults.
  - activation report output moved to `/tmp/identity-activation-reports`.
  - update enforces scope/pack alignment before execution.

### C) Health/report defaults moved out of repository paths
- `scripts/collect_identity_health_report.py` default out-dir -> `/tmp/identity-health-reports`
- `scripts/validate_identity_health_contract.py` default report-dir -> `/tmp/identity-health-reports`

### D) Metrics defaults moved out of repository paths
- `scripts/export_route_quality_metrics.py`
  - default output now resolves to `IDENTITY_RUNTIME_OUTPUT_ROOT` or repo-local `.codex` runtime root.

### E) Installer mirror behavior changed
- `scripts/identity_installer.py`
  - install report mirror to `identity/runtime/examples/install/...` is now **opt-in** via:
    - `--emit-repo-fixture-evidence`
  - default report/backup directories moved to `/tmp/identity-install-reports` and `/tmp/identity-install-backups`.

### F) New cleanliness gate
- Added `scripts/validate_release_workspace_cleanliness.py`
  - fails when runtime artifacts pollute repository worktree.
- Wired into:
  - `scripts/release_readiness_check.py`
  - `scripts/e2e_smoke_test.sh`
  - `.github/workflows/_identity-required-gates.yml`

### G) Broadened ignore coverage
- `.gitignore` expanded for runtime reports/metrics/rulebooks/logs/install-report patterns.

## Additional scope correction in this batch

- `scripts/e2e_smoke_test.sh` now runs scope/health pre-checks per each `IDENTITY_IDS` target, removing PRIMARY ID drift risk.

## Remaining work (tracked)

1. `create_identity_pack.py` template-level runtime pattern semantics still contain repository-form placeholders for compatibility; they are rewritten to runtime roots during pack generation, but template semantics should be fully normalized in next patch to reduce confusion.
2. `compile_identity_runtime.py` still writes repository-managed compiled summary by design (`identity/runtime/IDENTITY_COMPILED.md`); this is governance artifact, not runtime test artifact, and remains intentionally tracked.

## Release posture

- Code-plane: **Go (local)**
- Release-plane: **Conditional Go** until cloud required-gates run-id evidence closes on release head.
