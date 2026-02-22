# Changelog

## Unreleased

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
