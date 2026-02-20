# Changelog

## Unreleased

- **trigger-regression hardening (skill-style)**:
  - protocol upgraded to `v1.2.5 (draft)`
  - added `docs/specs/identity-trigger-regression-contract-v1.2.5.md`
  - added `trigger_regression_contract` runtime block in `identity/store-manager/CURRENT_TASK.json`
  - added validator: `scripts/validate_identity_trigger_regression.py`
  - e2e smoke test now includes trigger regression validation
  - lifecycle validator now requires trigger regression validator in required checks
  - added sample regression record: `identity/runtime/examples/store-manager-trigger-regression-sample.json`

- **skill protocol baseline references for identity reviewers**:
  - added `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
  - README now links skill reference baseline and trigger-regression contract

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
