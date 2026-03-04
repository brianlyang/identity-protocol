# Changelog

## Unreleased

- **v1.5.0 release gate hotfix: identity-required-gates workflow reliability**:
  - pinned workflow lint action to an existing upstream tag:
    - `.github/workflows/_identity-required-gates.yml` now uses
      `rhysd/actionlint@v1.7.11` (previous `@v1` alias no longer resolvable)
  - made upgrade report lookup shellcheck/actionlint compliant by replacing
    `ls`-based selection with `find + sort` and explicit empty-result fail-closed
    guard in the required runtime gates loop
  - fixed fixture/runtime evidence path resolution regressions in
    `scripts/validate_identity_runtime_contract.py`:
    - runtime evidence pattern lookup now supports pack-local first with
      repository-relative fallback for `identity/runtime/**` patterns
    - rulebook path resolution now supports repository-relative paths (for
      fixture identities) and pack-relative fallback (for runtime packs)
  - fixed scope arbitration for mixed SYSTEM/USER catalogs in prompt quality gate:
    - `scripts/validate_identity_prompt_quality.py` now accepts `--scope AUTO`
      (or empty) to infer scope from resolver context
    - required-gates workflow now calls prompt quality validator with
      `--scope AUTO` instead of forcing `--scope USER`

- **v1.4.13 protocol tool/vendor discovery-solution gate wiring (draft)**:
  - added protocol-level contract-first validators:
    - `scripts/validate_identity_tool_installation.py`
    - `scripts/validate_identity_vendor_api_discovery.py`
    - `scripts/validate_identity_vendor_api_solution.py`
    - shared resolver/helper: `scripts/tool_vendor_governance_common.py`
  - wired the new validator chain into required protocol execution paths:
    - `scripts/identity_creator.py validate`
    - `scripts/e2e_smoke_test.sh`
    - `scripts/release_readiness_check.py`
    - `scripts/full_identity_protocol_scan.py`
    - `.github/workflows/_identity-required-gates.yml`
  - extended runtime health collection and default scaffold contracts:
    - `scripts/collect_identity_health_report.py` now includes tool/vendor closure checks
    - `scripts/create_identity_pack.py` now injects optional contracts
      (`tool_installation_contract`, `vendor_api_discovery_contract`,
      `vendor_api_solution_contract`) with safe default `required=false`
    - `identity/store-manager/CURRENT_TASK.json` updated to include the same optional
      tool/vendor closure contract skeletons
  - route quality export compatibility fix for local runtime identities:
    - `scripts/export_route_quality_metrics.py` now supports absolute
      `handoff_log_path_pattern` values (via glob-based resolution) in addition
      to relative repo patterns, preventing false `NotImplementedError` in
      `e2e_smoke_test.sh` for instance-local runtime paths

- **v1.4.13 execution-report freshness + required-contract coverage semantics (draft)**:
  - added report freshness preflight validator:
    - `scripts/validate_execution_report_freshness.py`
    - structured freshness payload with policy gate (`strict|warn`) and
      stale/mismatch error code `IP-REL-001`
  - release readiness now enforces freshness before late-stage validators:
    - `scripts/release_readiness_check.py` now runs report freshness preflight
      and supports `--execution-report-policy`
    - auto report discovery now prioritizes prompt-sha-aligned report candidates
      when selecting latest execution report
  - added required-contract coverage classifier for tool/vendor closures:
    - `scripts/validate_required_contract_coverage.py`
    - machine-readable statuses:
      `PASS_REQUIRED` / `SKIPPED_NOT_REQUIRED` / `FAIL_REQUIRED` / `FAIL_OPTIONAL`
    - coverage metrics:
      `required_contract_coverage_rate`,
      `required_contract_total`,
      `required_contract_passed`,
      `skipped_contract_count`
    - optional policy threshold: `--min-required-contract-coverage`
  - coverage/freshness surfaced in governance chains:
    - `scripts/release_readiness_check.py`
    - `scripts/e2e_smoke_test.sh`
    - `scripts/report_three_plane_status.py`
    - `scripts/full_identity_protocol_scan.py`
    - `scripts/identity_creator.py validate`
    - `.github/workflows/_identity-required-gates.yml`
  - report candidate selection now follows pack-local first resolution:
    - `scripts/validate_execution_report_freshness.py` and
      `scripts/validate_identity_protocol_baseline_freshness.py` now search
      `<resolved_pack>/runtime/**` first and only fallback to shared roots
      (`/tmp`, `$IDENTITY_HOME`) when local candidates are absent
    - avoids cross-catalog identity-id collisions selecting another instance's
      report under dual-layer (project/global) environments
  - canonical handoff synced with local-first report binding semantics:
    - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`

- **v1.4.13 protocol baseline propagation + upgrade-wave closure (draft)**:
  - added protocol baseline freshness validator:
    - `scripts/validate_identity_protocol_baseline_freshness.py`
    - compares execution report `protocol_commit_sha` against current protocol
      HEAD under `report.protocol_root`
    - policy gate: `--baseline-policy strict|warn`
    - structured error codes:
      `IP-PBL-001` / `IP-PBL-002` / `IP-PBL-003` / `IP-PBL-004`
  - upgraded health checks with warn-aware contract semantics:
    - `scripts/collect_identity_health_report.py` adds
      `protocol_baseline_freshness` check (warn policy by default)
    - health report now emits:
      `warning_count`, `failed_count`, `checks[].status`, `checks[].error_code`
    - `scripts/validate_identity_health_contract.py` accepts `PASS/WARN/FAIL`
      and keeps `--require-pass` fail-only on `FAIL` checks
  - wired baseline freshness visibility into core governance chains:
    - `scripts/release_readiness_check.py` adds baseline preflight
      (`--baseline-policy`)
    - `scripts/full_identity_protocol_scan.py` adds
      `protocol_baseline_freshness` check and parsed fields
    - `scripts/report_three_plane_status.py` exposes baseline freshness detail
      in instance-plane output (warn-visible by default)
    - `scripts/e2e_smoke_test.sh` adds strict baseline freshness step
    - `.github/workflows/_identity-required-gates.yml` adds strict baseline
      freshness check on generated upgrade report
  - added batch protocol upgrade orchestrator:
    - `scripts/run_protocol_upgrade_wave.py`
    - supports catalog-driven stale detection + dry-run inventory +
      optional apply mode to trigger `identity_creator update`
    - emits machine-readable wave report:
      `outdated_identities`, `updated_count`, `blocked_count`, `items[]`
    - review-required convergence semantics hardened:
      - `identity_creator update` exit code `2` with empty hard error and
        review-required next action is now classified as `REVIEW_REQUIRED`
        instead of `BLOCKED`
      - wave payload now emits `review_required_count` and per-item
        `update_status` (`UPDATED` / `REVIEW_REQUIRED` / `BLOCKED` /
        `SKIPPED_*`) for clearer audit triage
    - stale/outdated detection policy now treats all non-`PASS` baseline states
      as convergence candidates (including `IP-PBL-002` report-missing),
      preventing false `identity_aligned_to_current_protocol` labels for
      bootstrap-required identities

- **v1.4.13 scope-arbitrated full-scan/three-plane stabilization (draft)**:
  - scope classification now treats `profile=fixture` / `runtime_mode=demo_only`
    as `SYSTEM` regardless catalog source layer:
    - `scripts/resolve_identity_context.py`
  - scope validators now support explicit arbitration without false conflict hard-fail:
    - `scripts/validate_identity_scope_resolution.py`
    - `scripts/validate_identity_scope_isolation.py`
  - three-plane reporter now accepts explicit scope binding:
    - `scripts/report_three_plane_status.py --scope REPO|USER|ADMIN|SYSTEM`
  - full scan now injects catalog-layer scope hints and forwards explicit scope to:
    - resolve/scope validators
    - three-plane reporter
  - full scan severity now keeps fixture/demo baseline `WARN` as non-blocking and
    skips prompt-quality hard-gate for fixture/demo identities to avoid
    protocol/fixture mixed-layer false P1 noise:
    - `scripts/full_identity_protocol_scan.py`

- **v1.4.13 layered-governance closure hardening (draft)**:
  - added unified three-plane governance reporter:
    - `scripts/report_three_plane_status.py`
    - standardized output contract now includes
      `instance_plane_status` / `repo_plane_status` / `release_plane_status`
      plus release evidence fields and `overall_release_decision`
  - upgraded `IDENTITY_PROMPT.md` from static doc to runtime contract object:
    - `execute_identity_upgrade.py` now writes prompt activation evidence fields into execution reports
    - added `scripts/validate_identity_prompt_activation.py`
    - wired prompt activation validator into e2e (`27.7/30`), release readiness, and three-plane status reporter
    - `execute_identity_upgrade.py` now applies deterministic prompt runtime-contract block updates
      during upgrade runs and records `hash_before/hash_after` lifecycle fields
    - added `scripts/validate_identity_prompt_lifecycle.py`
    - wired prompt lifecycle validator into e2e (`27.8/30`), release readiness, three-plane status,
      and active-runtime checks in full protocol scan
  - added full-repo identity governance scanner:
    - `scripts/full_identity_protocol_scan.py`
    - scans project/global catalogs with shared validator matrix and
      emits severity summary (`P0`/`P1`/`OK`) for cross-instance readiness
  - hardened instance-plane fail-operational closure and legacy debt repair:
    - added `scripts/repair_rulebook_schema_backfill.py` for idempotent historical
      `RULEBOOK.jsonl` schema backfill (focus: missing `scope`)
    - enhanced `scripts/repair_identity_learning_sample.py` to backfill existing
      run-linked rulebook rows instead of only appending new rows
    - wired rulebook schema backfill into `scripts/e2e_smoke_test.sh` preflight (step 2.45/30)
      and `identity_creator.py heal` auto-repair flow
  - update/e2e/reporting governance consistency uplift:
  - prompt lifecycle validator now supports deferred blocked execution semantics:
    - `scripts/validate_identity_prompt_lifecycle.py` now treats known
      pre-mutation blocked outcomes (`IP-UPG-001` / `IP-PERM-001`) as valid
      deferred lifecycle state when `all_ok=false`
    - review-required deferred outcomes with
      `next_action=review_required_create_pr_from_patch_plan` and
      `identity_prompt_change_note=prompt_change_deferred_due_to_failed_validators`
      are now classified as valid deferred lifecycle state (not false hard-fail)
    - prevents false P0 escalation when prompt mutation is intentionally
      blocked before writeback by policy/permission boundaries
    - `execute_identity_upgrade.py` now guarantees structured failure/report fields
      for recoverable vs hard-boundary interpretation
    - added capability activation evidence contract for skill/MCP/tool attachment:
      - `scripts/validate_identity_capability_activation.py`
      - `identity_creator update` now probes capability activation before upgrade execution
      - upgrade execution report now always includes
        `skills_used` / `mcp_tools_used` / `tool_calls_used` /
        `capability_activation_status` / `capability_activation_error_code`
      - wired capability evidence checks into:
        - `scripts/e2e_smoke_test.sh`
        - `scripts/release_readiness_check.py`
        - `scripts/report_three_plane_status.py`
        - `scripts/full_identity_protocol_scan.py`
      - normalized writeback validator invocation to use explicit
        `--repo-catalog + --local-catalog` binding in e2e/readiness/three-plane
        (prevents implicit global-catalog drift during instance-plane evaluation)
      - capability activation now enforces GitHub auth readiness:
        - `scripts/validate_identity_capability_activation.py` splits
          `github` MCP readiness into `cli_present` + `auth_ready`
        - when `required_mcp` includes `github` and auth is not ready,
          status is `BLOCKED` with `IP-CAP-003` (no false `ACTIVATED`)
      - `scripts/full_identity_protocol_scan.py` now supports
        `--scan-mode target --identity-ids ...` in addition to full scan mode,
        so release preflight can isolate target-instance posture from historical backlog
      - `scripts/export_route_quality_metrics.py` removed default repo runtime fallback:
        - defaults now require `IDENTITY_RUNTIME_OUTPUT_ROOT` or
          `<resolved_pack_path>/runtime`
        - repo fallback moved behind explicit
          `--allow-repo-runtime-fallback` (fixture/debug only)
      - `scripts/e2e_smoke_test.sh` now adds early global-runtime writeability preflight
        and fail-fast guidance to switch to `project` mode when global runtime is not writable
    - `e2e_smoke_test.sh` now emits dual-plane terminal states
      (`instance_plane_status`, `release_plane_status`)
  - repo-plane contract tooling improvements:
    - added `scripts/docs_command_contract_check.py` (dynamic index-driven coverage)
      and kept it decoupled from instance main chain
    - added `scripts/validate_release_plane_cloud_closure.py` for release-only cloud closure checks
  - identity session/runtime lifecycle quality:
    - added `scripts/sync_session_identity.py` to remove activation-chain missing-script warning
    - added single-active precheck/auto-converge option in activation/update paths
  - CI security/path governance hardening:
    - required-gates workflow now includes:
      - actionlint (workflow lint)
      - gitleaks (secret scanning)
      - ast-grep path governance rule:
        `.github/ast-grep/no-default-repo-runtime-fallback.yml`
  - governance documentation updates:
    - added
      `docs/governance/identity-token-efficiency-and-skill-parity-governance-v1.4.13.md`
    - added
      `docs/governance/identity-token-governance-audit-checklist-v1.4.13.md`
    - updated `README.md`, `docs/governance/AUDIT_SNAPSHOT_INDEX.md`,
      `docs/governance/identity-instance-closure-checklist-v1.4.12.md`
    - updated consumer integration references to prefer stable model instructions path
      `../identity-protocol-local/identity/runtime/IDENTITY_COMPILED.md`
      instead of relying on optional `../identity/runtime/IDENTITY_COMPILED.md` bridge files
  - creation/installer exception-path hardening + anti-pollution cleanup:
    - `scripts/create_identity_pack.py` now anchors repo boundary to detected `.git` root
      (no cwd-dependent drift), and keeps fixture/demo runtime artifacts under
      `<pack>/runtime` instead of mutating shared `identity/runtime` templates
    - `scripts/create_identity_pack.py` adds overlap guards that fail when bootstrap
      source==destination, preventing in-place fixture corruption
    - added optional `--skip-sample-bootstrap` (advanced/boundary testing only)
      to run boundary regression without runtime fixture mutation side effects
    - `scripts/identity_installer.py` aligns repo-target exception model with
      create flow: `--allow-repo-target` now requires explicit confirm token +
      purpose; registration now writes `profile` + `runtime_mode` consistently
    - added `scripts/validate_identity_creation_boundary.py` (4-case regression:
      missing confirm fail, repo runtime fail, local runtime pass, fixture pass)
      and wired it into `scripts/e2e_smoke_test.sh` + `scripts/release_readiness_check.py`
    - e2e compile step now writes to `/tmp/identity-compiled-runtime/*.md` to avoid
      tracked workspace churn from runtime brief generation
  - recoverable self-drive contract alignment (fail-operational):
    - `execute_identity_upgrade.py` now emits complete preflight-blocked evidence
      (synthetic `checks/check_results`, `required_checks`, matching patch plan,
      `creator_invocation`, and structured next_action) for capability/metrics blocked paths
      instead of empty check arrays
    - this removes false-fail in `validate_identity_self_upgrade_enforcement.py`
      for recoverable blocked reports (`IP-CAP-*`, metrics-missing) while keeping
      machine-auditable evidence integrity
  - capability activation policy extension:
    - `validate_identity_capability_activation.py` now emits per-route readiness matrix
      (`route_activation_matrix`, `route_ready_count`, `route_total_count`)
    - added `--activation-policy`:
      - `strict-union` (default, backward-compatible, keeps IP-CAP-003 hard block semantics)
      - `route-any-ready` (opt-in route-scoped activation semantics)
  - three-plane repo-status hardening:
    - `report_three_plane_status.py` repo-plane now includes tracked worktree cleanliness
      (`workspace_clean`, dirty entries) and blocks `repo_plane_status=CLOSED` when tracked files are dirty
  - ast-grep path governance rule strengthened:
    - `.github/ast-grep/no-default-repo-runtime-fallback.yml` now covers broader Python path variants
      and prevents unguarded repo `.codex/identity/runtime` fallback patterns across scripts
    - `scripts/export_route_quality_metrics.py` repo fallback path construction is now
      centralized via `_repo_runtime_metrics_path(...)` so explicit debug-only fallback
      remains auditable while avoiding rule false positives on guarded branches
  - runtime mode/catalog fail-fast guard:
    - added `scripts/validate_identity_runtime_mode_guard.py` to enforce resolver tuple
      (`source_layer`, `catalog_path`, `pack_path`, `resolved_scope`) against selected
      runtime mode before identity operations
    - wired guard into `identity_creator.py` (`validate`/`activate`/`update`),
      `scripts/release_readiness_check.py`, and `scripts/e2e_smoke_test.sh`
      to block project/global mode drift early with explicit remediation hints
  - activation session pointer consistency hardening:
    - canonical session pointer path standardized to
      `<catalog_dir>/session/active_identity.json` (legacy mirror remains
      `/tmp/identity-session/current.json`)
    - `scripts/sync_session_identity.py` now writes canonical pointer by default
      and mirror pointer as warning-only compatibility path
    - `identity_creator.py activate` now passes explicit canonical `--out` and
      treats canonical sync failure as transactional failure (rollback catalog/META/evidence)
    - added `scripts/validate_identity_session_pointer_consistency.py` and wired
      into activate flow, `e2e_smoke_test.sh`, `release_readiness_check.py`,
      `report_three_plane_status.py`, and `full_identity_protocol_scan.py`
  - blocked-arbitration semantics and release capability policy clarification:
    - `scripts/validate_identity_capability_arbitration.py` now applies
      blocked-aware linkage handling: when upgrade report shows
      `capability_activation_status=BLOCKED` and trigger reason contains
      `capability_activation_blocked:*`, metrics-trigger mismatch is bypassed
      as recoverable fail-operational state instead of hard failure
    - `scripts/release_readiness_check.py` now exposes
      `--capability-activation-policy {strict-union,route-any-ready}`
      and passes policy through to both preflight validation and
      auto-generated `identity_creator update` execution path
    - `scripts/identity_creator.py update` and
      `scripts/execute_identity_upgrade.py` now accept/propagate
      `--capability-activation-policy` for deterministic policy semantics across
      preflight and execution reports
  - dialogue governance contract landing (optional contract-first, protocol-only):
    - added shared helper `scripts/dialogue_governance_common.py`
      (contract resolution, report discovery, threshold parsing, warn/enforce outcome handling)
    - added dialogue validators with deterministic `IP-DCIC-*` semantics:
      - `scripts/validate_identity_dialogue_content.py`
      - `scripts/validate_identity_dialogue_cross_validation.py`
      - `scripts/validate_identity_dialogue_result_support.py`
    - wired dialogue validators into:
      - `scripts/e2e_smoke_test.sh` (instance-plane optional contract checks)
      - `scripts/release_readiness_check.py` (release-plane protocol gate chain)
      - `scripts/report_three_plane_status.py` (instance-plane validator matrix)
      - `scripts/full_identity_protocol_scan.py` (cross-catalog severity model)
      - `.github/workflows/_identity-required-gates.yml` (CI required-gates loop)
    - added protocol-governance documentation:
      - `docs/governance/identity-base-protocol-runtime-retro-and-governance-feedback-v1.4.13.md`
      - compatibility alias:
        `docs/governance/office-ops-expert-instance-runtime-retro-and-protocol-feedback-v1.4.13.md`
      - updated `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
  - dialogue-governance scaffold defaults for new identities:
    - `scripts/create_identity_pack.py` now injects
      `dialogue_governance_contract` skeleton into both `minimal` and `full-contract`
      init profiles with safe default `required=false`
    - `identity/store-manager/CURRENT_TASK.json` now includes the same contract skeleton
      as template baseline for future scaffolds
  - protocol SSOT hardening (handoff canonical + artifacts non-normative):
    - added `scripts/validate_protocol_ssot_source.py`
      (index policy marker checks, canonical handoff integrity checks, anti-normative artifact guard)
    - added `scripts/validate_protocol_handoff_coupling.py`
      (protocol-core file changes must include canonical handoff doc update in same git range)
    - added configurable protocol-core scope map:
      `docs/governance/templates/protocol-core-change-map.yaml`
      used by coupling validator to avoid hardcoded matcher drift
    - wired SSOT validators into:
      - `.github/workflows/_identity-required-gates.yml`
      - `scripts/release_readiness_check.py`
      - `scripts/e2e_smoke_test.sh`
    - updated `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
      with explicit execution directive:
      "execute by handoff only; artifacts are evidence mirrors"
  - protocol audit preflight hardening (local reproducibility + auth clarity):
    - added `scripts/preflight_protocol_audit_env.sh`
      (checks `gh auth status`, `actionlint`, and `ast-grep` availability)
    - supports `--install-missing` to reduce local-vs-CI tooling drift
    - supports `--require-gh-auth` for strict release profiles where capability auth
      readiness is mandatory
    - SSOT/README guidance now explicitly treats strict-union `IP-CAP-003`
      with unauthenticated `gh` as environment-auth blocked state
      (not protocol regression by itself)
  - instance baseline extension (separate from protocol contract change):
    - added `system-requirements-analyst` baseline identity assets:
      - `identity/catalog/identities.yaml` registration
      - `identity/packs/system-requirements-analyst/**` scaffold and runtime examples
    - explicit linkage for historical baseline commit: `6ecdaae`
    - governance classification: this is instance/baseline track (B-track),
      not protocol SSOT contract mutation
  - session pointer mirror deconfliction:
    - default mirror path switched from global `/tmp` to catalog-scoped
      `<catalog_dir>/session/mirror/current.json`
    - `validate_identity_session_pointer_consistency.py` now enforces canonical pointer
      by default while keeping mirror mismatch warning-only unless `--require-mirror`
    - `identity_creator.py activate` sync/verify now uses catalog-scoped mirror by default
  - local preflight parity with CI required-gates:
    - `scripts/preflight_protocol_audit_env.sh` now checks `gitleaks` availability
      in addition to `actionlint` and `ast-grep`
  - validate-chain alignment for local/release/e2e semantics:
    - `identity_creator.py validate` now includes dialogue validators:
      - `validate_identity_dialogue_content.py`
      - `validate_identity_dialogue_cross_validation.py`
      - `validate_identity_dialogue_result_support.py`
    - keeps contract-first semantics (`required=false` remains skip/non-blocking)
  - install/migration rewrite consistency hardening:
    - `identity_installer.py install` now runs path normalization rewrite after `_sync_pack`
      (same semantic level as adopt flow)
    - rewrite coverage expanded to `CURRENT_TASK.json` + `runtime/**/*.json` path-bearing fields
      with install report counters (`rewritten_files_count`, `rewritten_fields_count`)
    - `validate_identity_update_lifecycle.py` now resolves relative-first evidence paths
      against pack root for relocation-safe replay checks
    - `create_identity_pack.py` replay sample generator now writes relative
      `evidence_path` / `log_path` fields by default
  - validator portability hardening:
    - `validate_identity_role_binding.py` runtime live-revalidation no longer depends
      on caller cwd; validator path/cwd now anchored to script/repo root
  - FR-005 wording/implementation alignment:
    - DCIC documentation now explicitly states protocol defines gate routing path,
      while `dialogue_governance_contract.required` controls per-instance activation stage
      (`warn` / `enforce`)
  - release-freeze boundary governance alignment:
    - `validate_release_freeze_boundary.py` now allows catalog rows under
      `identity/packs/*` only when classified as `profile=fixture` + `runtime_mode=demo_only`
    - non-fixture rows under forbidden scope remain fail-closed
  - full-scan environment-auth severity normalization:
    - `full_identity_protocol_scan.py` now parses capability preflight output and
      classifies `IP-CAP-003` as environment-auth blocked (`P1`) rather than protocol regression (`P0`)

- **v1.4.12 self-upgrade closure follow-up (draft)**:
  - added handoff contract self-test fixtures for `base-repo-architect`
    under `identity/runtime/local/base-repo-architect/examples/handoff/{positive,negative}`
  - aligned self-drive verification evidence so `identity_creator update` can evaluate
    handoff self-test and changelog gates in the latest commit window
  - `.gitignore` now keeps the deterministic handoff self-test fixture files versioned
    while continuing to ignore volatile runtime-local outputs
  - prompt lifecycle governance strengthened (load/create/update):
    - runtime mode scripts now export `IDENTITY_SCOPE` (`REPO` for project mode, `USER` for global mode)
    - `identity_creator validate/update` now gate on `validate_identity_prompt_quality.py`
    - upgrade execution report now emits prompt activation evidence:
      `identity_prompt_path`, `identity_prompt_sha256`, `identity_prompt_activated_at`,
      `identity_prompt_source_layer`, `identity_prompt_status`
    - added `scripts/validate_identity_prompt_activation.py` and wired into readiness/e2e/required-gates
    - `create_identity_pack.py` now scaffolds a governance-complete default `IDENTITY_PROMPT.md`
      plus `identity_prompt_activation_contract` baseline
    - compile runtime brief now records prompt activation fingerprint (`path` + `sha256` + preview)
  - project-mode scope alignment hotfix:
    - `scripts/use_project_identity_runtime.sh` now exports `IDENTITY_SCOPE=USER`
      to match resolver/runtime `local_only` semantics and avoid REPO/USER mismatch failures
  - learning-loop identity isolation hardening:
    - `scripts/validate_identity_learning_loop.py` removed store-manager fallback
      and now fails fast when identity-scoped learning report is missing

- **v1.4.x runtime anti-pollution hardening (draft)**:
  - scope-resolution hardening (skills-style discovery + strict arbitration):
    - `scripts/resolve_identity_context.py` adds `resolved_scope`/`resolved_pack_path`
      and conflict hard-fail when one identity resolves to multiple pack paths unless explicit `--scope` is provided
    - added `scripts/validate_identity_scope_resolution.py`
    - wired scope-resolution validator into `identity_creator validate`, `release_readiness_check.py`, `e2e_smoke_test.sh`
    - `execute_identity_upgrade.py` execution/plan reports now include
      `resolved_scope` + `resolved_pack_path`
    - added scope governance validators:
      - `scripts/validate_identity_scope_isolation.py`
      - `scripts/validate_identity_scope_persistence.py`
  - installer governance lifecycle for duplicate runtime instances:
    - `identity_installer.py scan` (discover candidate duplicates)
    - `identity_installer.py adopt` (promote canonical instance to runtime catalog)
    - `identity_installer.py lock` (enforce canonical binding + instance_uid)
    - `identity_installer.py repair-paths` (rewrite legacy absolute CURRENT_TASK paths to canonical pack root)
  - portability + workspace hygiene hardening:
    - `scripts/configure_identity_runtime_paths.py` removed machine-specific defaults;
      now derives defaults from `${CODEX_HOME:-~/.codex}/identity` and cwd/protocol root
    - `.gitignore` now ignores runtime-generated evidence/log churn patterns to reduce working-tree pollution
  - runtime self-healing flow added:
    - `identity_creator.py heal` wraps `scan -> adopt -> lock -> repair-paths -> validate`
    - emits auditable heal report under `identity/runtime/reports/heal/`
    - added `scripts/repair_identity_baseline_evidence.py`
      and heal auto-repair pass for protocol/role-binding missing evidence scenarios
  - health diagnostics + CI control:
    - added `scripts/collect_identity_health_report.py` (collect failures + remediation suggestions)
    - added `scripts/validate_identity_health_contract.py` (enforce report schema + optional PASS requirement)
    - wired health collection/validation into release-readiness, e2e smoke test, and required-gates workflow
  - permission-state governance (sandbox/approval aligned):
    - `execute_identity_upgrade.py` now emits `permission_state`, `permission_error_code`, and `writeback_precheck`
    - added `scripts/validate_identity_permission_state.py`
    - release/e2e/workflow now enforce permission-state contract and reject deferred writeback in CI/release mode
  - added strict identity-scoped path validator:
    - `scripts/validate_identity_instance_isolation.py`
    - blocks cross-identity path markers (including `store-manager`) in runtime/local identities
  - removed store-manager global fallback behavior from learning/feedback/arbitration validators:
    - `scripts/validate_identity_learning_loop.py`
    - `scripts/validate_identity_experience_feedback_governance.py`
    - `scripts/validate_identity_experience_feedback.py`
    - `scripts/validate_identity_capability_arbitration.py`
  - wired isolation + persistence gates into release/e2e/required-gates:
    - `scripts/release_readiness_check.py` (catalog-aware local runtime validation)
    - `scripts/e2e_smoke_test.sh` (catalog-aware default for local runtime identities)
    - `.github/workflows/_identity-required-gates.yml`
  - state-source consistency hardening:
    - added `scripts/validate_identity_state_consistency.py`
    - strategy locked: **dual-write + strong consistency**
      - catalog is single decision source-of-truth for active status
      - `META.status` remains required mirrored state (must match catalog)
    - `identity_creator.py activate` now transactionally syncs `META.yaml` status from catalog and validates post-switch consistency
  - release posture:
    - **Conditional Go** (cloud workflow update still blocked by token `workflow` scope; no new run-id yet)
  - governance/audit documentation closure:
    - added `docs/governance/audit-snapshot-2026-02-24-self-heal-and-permission-state-v1.4.12.md`
    - added `docs/governance/audit-snapshot-2026-02-24-release-doc-governance-closure-v1.4.12.md`
    - added `docs/governance/audit-snapshot-2026-02-24-identity-path-governance-final-closure-v1.4.12.md`
    - added `docs/governance/runtime-artifact-isolation-root-cause-and-remediation-v1.4.12.md`
    - updated `docs/governance/AUDIT_SNAPSHOT_INDEX.md` and README governance index links
    - formalized release documentation closure set + release source-of-truth repository boundary
  - runtime artifact isolation hardening:
    - added `scripts/validate_release_workspace_cleanliness.py` and wired into readiness/e2e/required-gates
    - moved health/install/upgrade default report outputs away from repository runtime paths
    - installer repository install-report mirror changed to explicit opt-in (`--emit-repo-fixture-evidence`)
  - protocol/runtime hard boundary closure (skills-style isolation):
    - `scripts/execute_identity_upgrade.py` now blocks protocol-root pack execution by default (`IP-PATH-001`)
      and removes repo `.codex` runtime fallback from runtime output root resolution
    - `scripts/identity_creator.py update` now enforces protocol-root separation before upgrade
      (explicit fixture/debug override: `--allow-protocol-root-pack`)
    - `scripts/resolve_identity_context.py` fallback identity home moved from repo `.codex` to `/tmp/codex-identity-runtime/<user>`
  - workspace cleanliness coverage refinement:
    - `.gitignore` now includes runtime drift patterns for `*-learning-*` and `*-update-replay-*` evidence files
      and ignores repo-local `.codex/` runtime scratch directory
  - role-binding evidence path normalization:
    - `identity_creator.py` now rewrites legacy `identity/runtime/**` and `identity/runtime/local/<id>/**`
      evidence patterns to identity-scoped `<pack_path>/runtime/**` outputs
    - `validate_identity_role_binding.py` now resolves the same legacy patterns against pack runtime roots
    - `repair_identity_baseline_evidence.py` now repairs role-binding evidence into identity-scoped runtime roots
  - P0 closure snapshot:
    - P0-1..P0-6 closed on local verification (identity-scoped contamination hard-fail active)
  - P1 deferred snapshot:
    - P1-7..P1-13 remain tracked for next hardening batch (path-semantics/documentation/install fallback/self-test isolation follow-ups)

- **v1.4.6 planning hardening (draft)**:
  - local-instance persistence boundary enforcement:
    - added `scripts/resolve_identity_context.py` (repo+local catalog merge, local override)
    - added `scripts/validate_identity_local_persistence.py`
    - added `scripts/migrate_repo_instances_to_local.py`
    - `create_identity_pack.py` default output moved to `${IDENTITY_HOME}/instances`
      + `${IDENTITY_HOME}/catalog.local.yaml`, plus `--repo-fixture` escape hatch
    - `identity_installer.py` default target/catalog moved to local paths and blocks repo target
      unless `--allow-repo-target` is explicitly provided
    - `identity_creator.py` init/validate/activate/update now defaults to local catalog context
      and activation only mutates local catalog layer
  - fixture/runtime split codified in catalog schema:
    - `identity/catalog/identities.yaml` now marks `store-manager` as
      `profile=fixture` + `runtime_mode=demo_only`
    - `identity/catalog/schema/identities.schema.json` adds enums for
      `profile` and `runtime_mode`
  - local persistence + writeback gates wired to automation:
    - `scripts/release_readiness_check.py`
    - `scripts/e2e_smoke_test.sh`
    - `.github/workflows/_identity-required-gates.yml` (compile identity explicit + target resolver with diff coverage)
  - release-plane gate hardening follow-up:
    - `_identity-required-gates.yml` now fail-fast when identity target set resolves empty,
      preventing silent skip of all identity validators
    - `scripts/release_readiness_check.py` now auto-generates an upgrade execution report
      (when not provided) and always enforces `validate_identity_experience_writeback.py`
  - governance/readme hard record for severe persistence incident:
    - added `docs/governance/local-instance-persistence-boundary-v1.4.6.md`
    - README now documents demo/runtime split and local-instance-first operating model
  - final release closure documentation for maintainers:
    - added migration playbook: `docs/guides/runtime-instance-migration-guide-v1.4.7.md`
    - added release closure snapshot: `docs/governance/audit-snapshot-2026-02-23-release-closure-v1.4.7.md`
    - updated `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
  - canonicalized skills-style runtime home resolution in README + governance record:
    `IDENTITY_HOME` env override -> `${CODEX_HOME}/identity` -> `~/.codex/identity` default
    -> `./.codex/identity` fallback when home path creation fails
    (removed implicit `~/.identity` auto-branch; legacy migration is explicit)
  - aligned runtime directory naming with skills-style root convention:
    canonical runtime pack root is now `${IDENTITY_HOME}`
    (legacy `${IDENTITY_HOME}/identity`, `${IDENTITY_HOME}/identities`, and `${IDENTITY_HOME}/instances` remain auto-compatible)
  - release gate closure follow-up fixes:
    - synchronized release metadata markers to `v1.4.6` across
      `README.md` / `IDENTITY_PROTOCOL.md` / `VERSIONING.md` / `requirements-dev.txt`
      to unblock `validate_release_metadata_sync.py`
    - repaired `.github/workflows/_identity-required-gates.yml` resolver block
      and added explicit empty-target fail-fast + explicit compile target resolution
  - fixed `create_identity_pack.py` absolute path rewrite bug for local runtime roots:
    - prevents duplicated absolute prefixes during scaffold bootstrap
    - ensures generated CURRENT_TASK paths remain valid under `$CODEX_HOME/identity`
  - installer default source alignment hardening:
    - `identity_installer.py` now resolves source pack from local catalog `pack_path` first
    - default `--pack-root` now follows local runtime root instead of repo `identity/packs`
  - self-upgrade enforcement long-range audit compatibility:
    - `validate_identity_self_upgrade_enforcement.py` now supports legacy report check sets
      (version-aware fallback) to avoid false failures in cross-version ranges
  - release metadata baseline bumped to `v1.4.10` across:
    - `README.md`
    - `identity/protocol/IDENTITY_PROTOCOL.md`
    - `VERSIONING.md`
    - `requirements-dev.txt`
  - protocol-root dual-mode governance implementation (P0):
    - creator/installer/update reports now emit:
      `protocol_mode`, `protocol_root`, `protocol_commit_sha`, `protocol_ref`,
      `identity_home`, `catalog_path`, `generated_at`
    - added `scripts/validate_identity_protocol_root_evidence.py`
    - added `scripts/validate_identity_mode_promotion_arbitration.py`
    - wired new validators into:
      - `scripts/release_readiness_check.py`
      - `scripts/e2e_smoke_test.sh`
  - added role-binding governance contract and validator:
    - `scripts/validate_identity_role_binding.py`
    - `identity_role_binding_contract` + `gates.role_binding_gate=required`
    - activation/switch guard requires binding-ready evidence
  - runtime validator now enforces role-binding contract/evidence:
    - `scripts/validate_identity_runtime_contract.py`
  - identity creator now enforces role-binding on activation:
    - `scripts/identity_creator.py activate` blocks when role-binding validation fails
  - create scaffold now emits role-binding evidence samples and bootstrap checks:
    - `identity/runtime/examples/identity-role-binding-<identity-id>-sample.json`
    - `identity/runtime/examples/role-binding/identity-role-binding-<identity-id>-negative-sample.json`
    - `scripts/create_identity_pack.py --skip-bootstrap-check` available for local debug only
  - added role-binding spec:
    - `docs/specs/identity-role-binding-contract-v1.4.6.md`
  - added deep cross-validation execution mapping into v1.4.6 governance/snapshot docs:
    - `docs/governance/identity-instance-self-driven-upgrade-and-base-feedback-design-v1.4.6.md` (Git + Official Web + Context7)
    - `docs/governance/audit-snapshot-2026-02-23-v1.4.6-role-binding-bootstrap.md`
  - added PR-prep mandatory item for `identity-neutral baseline` migration:
    - base repo must not depend on business default identity (e.g., store-manager)
    - release closure template now includes identity-neutral evidence section
  - implemented identity-neutral baseline controls:
    - `identity/catalog/identities.yaml` now uses empty `default_identity`
    - `store-manager` switched to `inactive` fixture status by default
    - schema now allows empty/null `default_identity`
    - `scripts/validate_identity_protocol.py` accepts explicit no-default mode
    - `scripts/e2e_smoke_test.sh` now requires explicit `IDENTITY_IDS` when no active/default identity exists
  - hardened role-binding authenticity + CI target coverage:
    - `scripts/validate_identity_role_binding.py` now enforces:
      - live runtime bootstrap revalidation
      - binding evidence freshness window (`evidence_max_age_days`)
      - `BOUND_ACTIVE` requirement before active/default promotion
    - CI required-gates target resolver patch prepared:
      - active/default identities + PR-diff identities + fallback-all strategy
      - publish is currently blocked by workflow-scope permission on the active OAuth token
  - create scaffold registration flow safety hardening:
    - `scripts/create_identity_pack.py` now rolls back catalog mutation when bootstrap validation fails
  - create scaffold full-contract path normalization:
    - `scripts/create_identity_pack.py` now rewrites legacy `identity/<id>/...` references to `identity/packs/<id>/...`
    - fixes bootstrap/runtime failures for newly created identities caused by stale `rulebook_path` and patch-surface file paths
  - release-readiness parity hardening:
    - `scripts/release_readiness_check.py` now includes
      `scripts/validate_identity_self_upgrade_enforcement.py --base <sha> --head <sha>`
    - aligns readiness decision with e2e self-upgrade enforcement semantics
  - switch stability hardening (single-active transaction):
    - `scripts/identity_creator.py activate` now enforces single-active semantics
      (`target active + all others inactive`) with rollback on failure
    - activation writes role-binding promotion evidence (`BOUND_ACTIVE` for target,
      `BOUND_READY` for demoted identities) and switch report under
      `identity/runtime/reports/activation/`
  - role-binding evidence resolution hardening:
    - role-binding/protocol-prereq/runtime evidence selectors now prefer newest file by mtime
      instead of lexical filename ordering (prevents stale `*-sample.json` overshadowing live evidence)
  - creator update experience-writeback closure hardening:
    - `scripts/execute_identity_upgrade.py` now writes review-required success feedback back into
      `RULEBOOK.jsonl` + `TASK_HISTORY.md` with `evidence_run_id=run_id`
    - added validator `scripts/validate_identity_experience_writeback.py`
      to enforce run-report ↔ rulebook/task-history linkage
    - `scripts/e2e_smoke_test.sh` now validates experience writeback right after
      `identity_creator.py update --mode review-required`
    - `scripts/release_readiness_check.py` now supports optional
      `--execution-report` to include writeback validation in pre-release verification
  - new-identity bootstrap completeness hardening:
    - `create_identity_pack.py` now also seeds:
      - trigger-regression sample
      - route-quality metrics baseline
      - collaboration/handoff bootstrap logs
      - install provenance operation chain reports (`plan -> dry-run -> install -> verify`)
    - capability arbitration validator now checks dynamic identity-specific TASK_HISTORY allowlist path
  - added release freeze boundary validator:
    - `scripts/validate_release_freeze_boundary.py`
    - blocks release-range changes that introduce local instance packs under `identity/packs/*`
    - validates catalog `pack_path` does not drift into `identity/packs/*` scope
  - added release readiness bundle entrypoint:
    - `scripts/release_readiness_check.py`
    - deterministic pre-release validator sequence for local/CI parity
  - wired freeze boundary validation into required chains:
    - `.github/workflows/_identity-required-gates.yml`
    - `scripts/e2e_smoke_test.sh`
  - added governance design baseline for v1.4.6:
    - `docs/governance/identity-instance-self-driven-upgrade-and-base-feedback-design-v1.4.6.md`
    - codifies scope boundary: base repo governance hardening only; no local-instance pack ingestion
  - added release closure template:
    - `docs/governance/templates/release-closure-template-v1.4.6.md`
  - README governance taxonomy clarified:
    - `docs/governance/` = enforceable internal policy
    - `docs/references/` = external reference and cross-vendor background

- **post-release evidence closure (v1.4.5 draft)**:
  - appended self-upgrade execution evidence bundle for `store-manager`:
    - `identity/runtime/reports/identity-upgrade-exec-store-manager-1771788615.json`
    - `identity/runtime/reports/identity-upgrade-exec-store-manager-1771788615-patch-plan.json`
    - `identity/runtime/logs/upgrade/store-manager/identity-upgrade-exec-store-manager-1771788615-check-01..18.log`
  - purpose: close `identity-core -> evidence` traceability for the v1.4.5 gate-hardening commit

- **release hardening follow-up (v1.4.4 draft)**:
  - added required validator `scripts/validate_release_metadata_sync.py` to prevent recurring
    `README/IDENTITY_PROTOCOL/VERSIONING/requirements-dev` version drift
  - wired metadata sync validator into:
    - `.github/workflows/_identity-required-gates.yml`
    - `scripts/e2e_smoke_test.sh`
    - `identity_update_lifecycle_contract.validation_contract.required_checks`
  - refreshed replay evidence sample/log chain (`store-manager-update-replay-check-01..18`)
    so lifecycle required-check coverage remains deterministic after gate expansion
  - fixed `scripts/validate_identity_self_upgrade_enforcement.py` to correctly validate
    `--execution-report` in CI live-run mode even when no report file changed in git diff

- **release metadata synchronization follow-up (v1.4.4 draft)**:
  - `VERSIONING.md` release-metadata synchronization section updated to `v1.4.4+`
  - `requirements-dev.txt` baseline header synchronized to `v1.4.4 draft`
  - added explicit enforcement note to avoid recurrent stale metadata drift

- **self-upgrade execution authenticity hardening (v1.4.4 draft)**:
  - strengthened update lifecycle replay contract to require:
    - `creator_invocation`
    - `check_results[] = {command, started_at, ended_at, exit_code, log_path, sha256}`
  - `scripts/validate_identity_update_lifecycle.py` now verifies:
    - creator invocation semantics (`identity-creator`, `mode=update`)
    - command coverage against `validation_contract.required_checks`
    - log existence + sha256 integrity for each replay check result
  - `scripts/execute_identity_upgrade.py` now emits:
    - `creator_invocation`
    - `check_results` with per-check execution logs and hashes
    - structured log files under `identity/runtime/logs/upgrade/<identity-id>/`
  - `scripts/validate_identity_self_upgrade_enforcement.py` now enforces:
    - report-level `creator_invocation`
    - report-level `check_results` integrity (`log_path` + `sha256`)
  - evidence resolution hardened to reduce cross-identity leakage:
    - `scripts/validate_identity_runtime_contract.py`
    - `scripts/validate_identity_upgrade_prereq.py`
    - both now prefer identity-scoped evidence filenames when available
  - create scaffold hardening:
    - `scripts/create_identity_pack.py` adds `--profile` (`full-contract` default)
    - full-contract scaffold clones runtime baseline contract shape and writes identity-scoped samples
    - new `--activate` switch keeps register default non-disruptive (`inactive` unless explicitly activated)
  - added unified wrapper CLI:
    - `scripts/identity_creator.py` with `init|validate|compile|activate|update`
  - refreshed store-manager replay/protocol samples and upgrade execution evidence artifacts
  - added installer-plane executable and provenance enforcement:
    - `scripts/identity_installer.py` (`plan|dry-run|install|verify|rollback`)
    - `skills/identity-installer/SKILL.md`
    - runtime contract: `install_provenance_contract` + gate `install_provenance_gate`
    - validator: `scripts/validate_identity_install_provenance.py`
  - install safety semantics aligned with contract:
    - `compatible_upgrade` now defaults to `abort_and_explain` in installer execution
    - `validate_identity_install_safety.py` enforces `on_conflict=abort_and_explain` behavior
  - creator/installer boundary tightened:
    - removed `install` dispatch path from `scripts/identity_creator.py`
    - installer actions must use `scripts/identity_installer.py`
  - install provenance validator now enforces full operation chain evidence:
    - requires recent `plan -> dry-run -> install -> verify` reports per identity
  - CI required-gates now validates install provenance and enforces CI-bound upgrade execution report checks:
    - `generated_by=ci`, `github_run_id`, `github_sha`
    - report path passed from live CI execution (not repository static evidence)

- **self-upgrade non-bypass enforcement hardening (post-v1.4.3)**:
  - added required runtime contract block:
    - `self_upgrade_enforcement_contract` in `identity/store-manager/CURRENT_TASK.json`
  - added/strengthened validator:
    - `scripts/validate_identity_self_upgrade_enforcement.py`
    - now verifies identity-core edits require matching upgrade execution report + patch-plan pair
    - validates report schema and required validator command coverage
  - required validator set now explicitly includes:
    - `scripts/validate_identity_self_upgrade_enforcement.py`
  - CI and e2e required chains now enforce self-upgrade evidence gate before upgrade execution step
  - protocol/runtime validators now treat self-upgrade enforcement contract as core key:
    - `scripts/validate_identity_protocol.py`
    - `scripts/validate_identity_runtime_contract.py`

- **release closure + changelog governance hardening (v1.4.3 draft)**:
  - added local executable upgrade cycle runner:
    - `scripts/execute_identity_upgrade.py`
    - supports `review-required` / `safe-auto` modes
    - emits structured upgrade execution report under `identity/runtime/reports/`
  - capability arbitration validator now supports explicit upgrade linkage verification:
    - `scripts/validate_identity_capability_arbitration.py --upgrade-report <path>`
  - required gates now force metrics/threshold linkage evidence path:
    - `.github/workflows/_identity-required-gates.yml`
  - governance snapshot validator now accepts suffixed snapshot filenames:
    - `docs/governance/audit-snapshot-YYYY-MM-DD-*.md`
    - via `scripts/validate_audit_snapshot_index.py`
  - added release closure snapshot and index linkage for v1.4.2 closure:
    - `docs/governance/audit-snapshot-2026-02-21-release-closure-v1.4.2.md`
    - `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
  - added cross-vendor governance reference baseline:
    - `docs/references/identity-skill-mcp-cross-vendor-governance-guide-v1.0.md`
  - protocol raised to capability arbitration baseline:
    - `identity/protocol/IDENTITY_PROTOCOL.md` -> `v1.4.2 (draft)`
  - added changelog enforcement validator:
    - `scripts/validate_changelog_updated.py`
    - validates commit range and blocks significant protocol/runtime changes without `CHANGELOG.md` update
  - release metadata policy aligned:
    - `VERSIONING.md` now requires dependency-baseline review and changelog gate pass
    - `requirements-dev.txt` annotated as reviewed minimal baseline (no dependency delta in this batch)
  - required-gates and e2e now execute changelog validator in the default chain:
    - `.github/workflows/_identity-required-gates.yml`
    - `scripts/e2e_smoke_test.sh`
  - install safety contract and validator hardening (local-instance-first):
    - added runtime contract block: `install_safety_contract`
    - added validator: `scripts/validate_identity_install_safety.py`
    - added conflict semantics:
      - `idempotent_reinstall_allowed=true`
      - `same_signature_action=no_op_with_report`
      - destructive replace requires backup + rollback reference
  - experience feedback governance hardening (experience-contract single-source in v1.1):
    - enhanced `experience_feedback_contract` with data-governance fields:
      - `redaction_policy_required`
      - `retention_days`
      - `sensitive_fields_denylist`
      - `export_scope`
      - `feedback_log_path_pattern`
      - `promotion_requires_replay_pass`
    - added validator: `scripts/validate_identity_experience_feedback_governance.py`
    - added sample local feedback/install evidence:
      - `identity/runtime/logs/feedback/*.json`
      - `identity/runtime/examples/install/*.json`
  - safe-auto path-level enforcement:
    - `capability_arbitration_contract.safe_auto_patch_surface` now defines allowlist/denylist
    - `scripts/execute_identity_upgrade.py` blocks out-of-policy paths in `safe-auto` mode
  - required validator set versioning clarity:
    - `ci_enforcement_contract.required_validator_set_label = v1.1-required`
    - `candidate_validators_v1_2` declared as non-blocking next-phase candidates
  - protocol/README aligned to `v1.4.3 (draft)` and quickstart includes new validators

- **human-collab trigger protocol hardening (v1.3.0 draft)**:
  - added runtime required gate:
    - `gates.collaboration_trigger_gate=required`
  - added runtime contracts:
    - `blocker_taxonomy_contract`
    - `collaboration_trigger_contract`
  - standardized blocker taxonomy:
    - `login_required`
    - `captcha_required`
    - `session_expired`
    - `manual_verification_required`
  - added validator:
    - `scripts/validate_identity_collab_trigger.py`
  - validator enforces:
    - taxonomy coverage + classification fields
    - immediate auto-notify policy (`notify_timing=immediate`)
    - dedupe/state-change bypass
    - chat receipt and evidence log freshness
  - added collaboration evidence samples:
    - production-like log: `identity/runtime/logs/collaboration/*.json`
    - self-test samples: `identity/runtime/examples/collaboration-trigger/{positive,negative}/*.json`
  - CI required-gates updated (all workflow chains):
    - `.github/workflows/protocol-ci.yml`
    - `.github/workflows/identity-protocol-ci.yml`
    - `.github/workflows/_identity-required-gates.yml`
  - protocol docs updated:
    - `identity/protocol/IDENTITY_PROTOCOL.md` -> v1.3.0 draft
    - `identity/protocol/IDENTITY_RUNTIME.md`
    - `docs/specs/identity-collaboration-trigger-contract-v1.3.0.md`

- **ci startup reliability hotfix (v1.2.14 draft)**:
  - fixed zero-job startup failures in branch-protection bootstrap runs
  - inlined `required-gates` jobs back into:
    - `.github/workflows/protocol-ci.yml`
    - `.github/workflows/identity-protocol-ci.yml`
  - keeps job context names stable for branch protection setup:
    - `protocol-ci / required-gates`
    - `identity-protocol-ci / required-gates`
  - reusable workflow file remains as reference but no longer critical path

- **runtime sync preflight gate (v1.2.13 draft)**:
  - added local runtime sync checker:
    - `scripts/preflight_identity_runtime_sync.sh`
  - enforces local identity-protocol repo HEAD == `origin/main` before business runtime tests
  - added runtime preflight operations checklist:
    - `docs/operations/runtime-preflight-checklist-v1.2.13.md`
  - README governance section now includes runtime preflight references

- **audit snapshot CI gate (v1.2.12 draft)**:
  - added validator:
    - `scripts/validate_audit_snapshot_index.py`
  - validator enforces:
    - governance snapshot policy/template/index files exist
    - latest dated snapshot file exists
    - latest snapshot is referenced by `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
  - integrated into required gate chain:
    - `.github/workflows/_identity-required-gates.yml`
    - `scripts/e2e_smoke_test.sh`

- **audit snapshot institutionalization (v1.2.11 draft)**:
  - added fixed-action governance policy:
    - `docs/governance/audit-snapshot-policy-v1.2.11.md`
  - added reusable snapshot template:
    - `docs/governance/templates/audit-snapshot-template.md`
  - added snapshot index:
    - `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
  - added consolidated snapshot record:
    - `docs/governance/audit-snapshot-2026-02-21.md`
  - README governance section now includes snapshot policy and index links

- **handoff dual-track + freshness + consistency hardening (v1.2.9 draft)**:
  - `agent_handoff_contract.handoff_log_path_pattern` switched from example path to production runtime path:
    - `identity/runtime/logs/handoff/*.json`
  - added runtime handoff controls in `CURRENT_TASK`:
    - `minimum_logs_required`
    - `require_generated_at`
    - `max_log_age_days` (7-day freshness gate)
    - `enforce_task_id_match`
    - `require_identity_id_match`
    - `sample_log_path_pattern`
  - `validate_agent_handoff_contract.py` now enforces:
    - minimum production log count
    - `generated_at` timestamp presence/ISO validity/freshness
    - cross-file consistency (`task_id`, `identity_id`)
  - added production handoff evidence sample:
    - `identity/runtime/logs/handoff/handoff-2026-02-20-store-manager-10000514174106.json`
    - `identity/runtime/logs/handoff/artifacts/task-10000514174106-production-visual-check.md`
  - upgraded handoff protocol spec to v1.2.9 draft with dual-track section

- **route quality metrics export (new)**:
  - added `scripts/export_route_quality_metrics.py`
  - exports:
    - `route_hit_rate`
    - `misroute_rate`
    - `fallback_rate`
  - metrics artifact path:
    - `identity/runtime/metrics/store-manager-route-quality.json`
  - required-gates CI and e2e now execute metrics export per active identity

- **ci maintainability hardening (v1.2.8 draft)**:
  - consolidated duplicate workflow logic into reusable workflow:
    - `.github/workflows/_identity-required-gates.yml`
  - both CI workflows now call shared gate chain:
    - `.github/workflows/protocol-ci.yml`
    - `.github/workflows/identity-protocol-ci.yml`
  - added branch-protection last-mile checklist:
    - `docs/governance/branch-protection-required-checks-v1.2.8.md`
  - README governance section now links branch-protection checklist

- **master/sub anti-drift handoff contract hardening (v1.2.7 draft)**:
  - added canonical handoff spec:
    - `identity/protocol/AGENT_HANDOFF_CONTRACT.md`
  - added validator:
    - `scripts/validate_agent_handoff_contract.py`
  - validator enforces:
    - required handoff payload fields
    - artifacts path + kind checks
    - executable next_action fields
    - forbidden mutation detection
    - rulebook evidence linkage when rulebook update applied
  - added self-test sample packs:
    - positive samples: `identity/runtime/examples/handoff/positive/*.json`
    - negative samples: `identity/runtime/examples/handoff/negative/*.json`
  - added evidence artifacts for positive samples:
    - `identity/runtime/examples/handoff/artifacts/*`
  - runtime contract upgraded:
    - `gates.agent_handoff_gate=required`
    - `agent_handoff_contract` block added in `identity/store-manager/CURRENT_TASK.json`
    - lifecycle `validation_contract.required_checks` now includes handoff validator
  - CI required pipeline updated (both workflows):
    - `.github/workflows/protocol-ci.yml`
    - `.github/workflows/identity-protocol-ci.yml`
    - now runs `python scripts/validate_agent_handoff_contract.py --identity-id "$ID" --self-test`
  - e2e smoke updated to include handoff validator in gate chain:
    - `scripts/e2e_smoke_test.sh`
  - protocol and README fast-review path updated to include handoff contract:
    - `identity/protocol/IDENTITY_PROTOCOL.md`
    - `README.md`

- **audit hardening (v1.2.6 draft)**:
  - CI now enforces required gate chain for active identities in both workflows:
    - `.github/workflows/protocol-ci.yml`
    - `.github/workflows/identity-protocol-ci.yml`
  - required validators now executed in pipeline:
    - `validate_identity_runtime_contract.py`
    - `validate_identity_upgrade_prereq.py`
    - `validate_identity_update_lifecycle.py`
    - `validate_identity_trigger_regression.py`
    - `validate_identity_learning_loop.py`
  - `validate_identity_trigger_regression.py` now enforces semantic checks:
    - expected vs observed consistency
    - declared result vs calculated result
    - summary aggregation consistency
  - `validate_identity_update_lifecycle.py` now validates executable evidence:
    - required patch file paths existence
    - replay evidence presence and required fields
    - replay identity/status/patch surface/checks consistency
  - `validate_identity_protocol.py` now aligns with runtime contract blocks and conditional gate dependencies
  - `validate_identity_runtime_contract.py` now validates active identities by default (not default-only)
  - `validate_identity_learning_loop.py` now supports `--identity-id`
  - store-manager runtime portability and consistency updates:
    - replaced absolute local docs roots with portable relative roots
    - aligned `IDENTITY_PROMPT.md` version headers to v1.2
    - added replay evidence contract fields in `CURRENT_TASK.json`
    - added replay sample: `identity/runtime/examples/store-manager-update-replay-sample.json`
  - `scripts/e2e_smoke_test.sh` now runs full gate chain across active identities and verifies compiled brief baseline references

- **runtime compiled brief now includes baseline review references**:
  - updated `scripts/compile_identity_runtime.py` to include `protocol_review_contract.must_review_sources`
  - `identity/runtime/IDENTITY_COMPILED.md` now surfaces runtime baseline review references directly
  - keeps runtime/operator view aligned with protocol/review requirements

- **protocol canonical spec aligned to v1.2.5**:
  - updated `identity/protocol/IDENTITY_PROTOCOL.md` from `v1.2.4` to `v1.2.5 (draft)`
  - documented `trigger_regression_contract` as conditional runtime requirement
  - documented skill+mcp+tool collaboration boundary as baseline review requirement
  - synced conflict and alignment section with trigger-regression and collaboration checks

- **runtime baseline validator expanded for reference coverage**:
  - updated `scripts/validate_identity_runtime_contract.py`
  - baseline source set now also requires:
    - `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
    - `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
    - `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`

- **skill + mcp + tool collaboration baseline (new)**:
  - added `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
  - defines three-layer collaboration model:
    - skill (strategy)
    - mcp (capability access)
    - tool (execution)
  - includes runtime call chain, auth boundary model, staged execution template, and error routing classes
  - canonical skill reference now links this collaboration contract
  - README fast-review path now includes collaboration contract
  - runtime baseline review source list (`protocol_review_contract.must_review_sources`) now includes this collaboration contract

- **trigger-regression hardening (skill-style)**:
  - protocol upgraded to `v1.2.5 (draft)`
  - added `docs/specs/identity-trigger-regression-contract-v1.2.5.md`
  - added `trigger_regression_contract` runtime block in `identity/store-manager/CURRENT_TASK.json`
  - added validator: `scripts/validate_identity_trigger_regression.py`
  - e2e smoke test now includes trigger regression validation
  - lifecycle validator now requires trigger regression validator in required checks
  - added sample regression record: `identity/runtime/examples/store-manager-trigger-regression-sample.json`

- **skill protocol baseline references for identity reviewers**:
  - added canonical reference path: `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
  - added detailed versioned reference: `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
  - merged detailed mechanism for skill update handling:
    - update = creator-plane content patch + installer-plane runtime distribution
    - trigger/patch/validate/replay chain
    - post-update 4-layer validation (structure/resource/trigger-regression/smoke)
  - README and runtime baseline review sources now include canonical skill reference paths

- **identity update lifecycle contract hardening (skill-style)**:
  - protocol upgraded to `v1.2.4 (draft)`
  - added `docs/specs/identity-update-lifecycle-contract-v1.2.4.md`
  - added `gates.identity_update_gate=required` for runtime-evolution tasks
  - added `identity_update_lifecycle_contract` (trigger/patch/validation/replay)
  - added validator: `scripts/validate_identity_update_lifecycle.py`
  - e2e smoke test now includes lifecycle validation check
  - `store-manager` runtime now includes `capability_gap -> identity-creator` route
  - identity-creator skill now enforces update chain explicitly: trigger -> patch -> validate -> replay

- **baseline-review hardening for identity upgrades**:
  - README now documents a mandatory protocol baseline review gate for identity capability upgrades
  - protocol upgraded to `v1.2.3 (draft)` with `protocol_review_contract` requirements
  - runtime integration spec now includes baseline-review validation before identity-upgrade conclusions
- runtime contract control capability added:
  - `identity/store-manager/CURRENT_TASK.json` now includes `gates.protocol_baseline_review_gate=required`
  - `identity/store-manager/CURRENT_TASK.json` now includes `protocol_review_contract` and evidence-path requirement
  - sample evidence added: `identity/runtime/examples/protocol-baseline-review-sample.json`
- validator hardening:
  - `scripts/validate_identity_runtime_contract.py` now validates protocol baseline review evidence when gate is required
  - checks required evidence fields + mandatory source coverage (identity-protocol + skills + MCP references)
- **identity update-operation enforcement (skill-creator style)**:
  - new script: `scripts/validate_identity_upgrade_prereq.py`
  - e2e smoke now includes identity update prerequisite check for store-manager
  - identity-creator skill workflow now defines mandatory update flow for existing identities
  - identity-creator scaffold scripts now generate protocol baseline review gate/contracts by default

- protocol alignment hardening for skill/mcp-style determinism:
  - upgraded `identity/protocol/IDENTITY_PROTOCOL.md` to `v1.2.2 (draft)`
  - added explicit four core capability contracts (judgement/reasoning/routing/rule-learning)
  - clarified scenario-agnostic protocol boundary (identity != business payload)
- validator hardening:
  - `scripts/validate_identity_protocol.py` now validates **all identities** in catalog
  - pack contract now enforces `META.yaml` in addition to prompt/task/history
  - schema validation is now enforced in protocol validator via `jsonschema`
- runtime validator hardening:
  - `scripts/validate_identity_runtime_contract.py` now resolves CURRENT_TASK from catalog default identity
  - supports `--current-task` override for deterministic checks
- learning-loop validator hardening:
  - `scripts/validate_identity_learning_loop.py` now resolves CURRENT_TASK from catalog default identity
  - supports `--current-task` and `--run-report` overrides
  - adds run-report auto fallback by identity id
- benchmarked against:
  - OpenAI Codex Skills docs (`skills`, `app/features`, `app-server`)
  - Agent Skills standard (`home`, `specification`, `integrate-skills`, `what-are-skills`)
- added identity discovery contract draft:
  - `identity/protocol/IDENTITY_DISCOVERY.md`
- extended catalog schema and manifest fields:
  - `interface`, `policy`, `dependencies`, `observability`
- added validator scripts:
  - `scripts/validate_identity_manifest.py`
  - `scripts/test_identity_discovery_contract.py`
  - `scripts/validate_identity_runtime_contract.py`
  - `scripts/validate_identity_learning_loop.py`
- upgraded store-manager runtime contract to ORRL hard gates:
  - `identity/store-manager/CURRENT_TASK.json`
  - `identity/store-manager/RULEBOOK.jsonl`
- added learning-loop verification contract for reasoning (#2) and rulebook linkage (#4)
  - `identity/runtime/examples/store-manager-learning-sample.json`
  - `docs/specs/identity-learning-loop-validation-v1.2.1.md`
- upgraded e2e smoke test to include runtime ORRL + learning-loop validation
- added ORRL spec:
  - `docs/specs/identity-bottom-guardrails-orrL-v1.2.md`
- added deterministic identity scaffolder:
  - `scripts/create_identity_pack.py`
- upgraded `identity-creator` scaffold to generate `agents/identity.yaml`
- added benchmark report:
  - `docs/research/IDENTITY_PROTOCOL_BENCHMARK_SKILLS_2026-02-19.md`
- added operations docs:
  - `docs/specs/identity-compatibility-matrix.md`
  - `docs/operations/identity-rollback-drill.md`
  - `docs/guides/identity-creator-operations.md`

## v1.0.0 - 2026-02-18

First stable release:
- froze protocol contract in:
  - `docs/specs/identity-protocol-contract-v1.0.0.md`
- added formal release notes:
  - `docs/release/v1.0.0-release-notes.md`
- formalized stable compatibility policy in:
  - `VERSIONING.md`
- validated end-to-end workflow with compile/validate scripts and CI pass records

## v0.1.4 - 2026-02-18

First complete baseline pass with operational closure:
- added governance audit template:
  - `docs/governance/catalog-change-audit-template.md`
- added v1 completion roadmap:
  - `docs/release/v1-roadmap.md`
- added weixinstore upgrade execution checklist:
  - `docs/playbooks/weixinstore-upgrade-checklist-v0.1.3.md`
- added deterministic e2e smoke script:
  - `scripts/e2e_smoke_test.sh`
- executed local end-to-end tests and confirmed CI success runs on main

## v0.1.3 - 2026-02-18

Protocol completion and consumer ops guidance:
- added identity-creator command contract draft:
  - `docs/specs/identity-creator-cli-contract.md`
- added consumer integration and rollback playbook:
  - `docs/playbooks/weixinstore-consumer-integration.md`
- updated root quickstart and governance links:
  - `README.md`

## v0.1.2 - 2026-02-18

Protocol operations hardening:
- added GitHub Actions workflow for protocol validation and runtime brief consistency checks (`.github/workflows/protocol-ci.yml`)
- removed temporary MCP write-check marker file used during auth troubleshooting

## v0.1.1 - 2026-02-18

Protocol tooling and evidence expansion:
- added deterministic tooling: `scripts/validate_identity_protocol.py`, `scripts/compile_identity_runtime.py`
- added `requirements-dev.txt` for validator dependencies
- added `identity/store-manager` reference pack (`IDENTITY_PROMPT.md`, `CURRENT_TASK.json`, `TASK_HISTORY.md`)
- added roundtable/research/review docs:
  - `docs/roundtable/RT-2026-02-18-identity-creator-design.md`
  - `docs/research/cross-validation-and-sources.md`
  - `docs/review/protocol-review-checklist.md`

## v0.1.0 - 2026-02-18

Initial bootstrap release:
- identity protocol core (`identity/catalog`, `identity/protocol`, `identity/runtime`)
- `identity-creator` skill package with references and scripts
- runtime/path validation scripts
- ADR and curated origin discussion notes
