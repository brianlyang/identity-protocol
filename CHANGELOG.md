# Changelog

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
