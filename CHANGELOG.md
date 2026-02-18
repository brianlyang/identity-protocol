# Changelog

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
