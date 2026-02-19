# identity-protocol

Protocol-grade identity control plane for autonomous coding agents.

This repository standardizes identity as a first-class layer parallel to:
- **skills** (capability packaging)
- **MCP** (tool transport/execution)

Identity defines:
- governance boundaries (hard guardrails)
- runtime state contract (single source of truth)
- adaptive learning loop (failure -> update -> replay)

## Structure

- `identity/catalog/` — identity metadata registry and schema
- `identity/protocol/` — protocol and runtime integration specs
- `identity/runtime/` — compiled runtime brief
- `skills/identity-creator/` — creator skill to scaffold/validate identity packs
- `scripts/` — deterministic compile/validate tooling
- `docs/` — ADR, roundtable, research, review, migration playbooks

## Quickstart

```bash
pip install -r requirements-dev.txt
python scripts/validate_identity_protocol.py
python scripts/compile_identity_runtime.py
python scripts/validate_identity_manifest.py
python scripts/test_identity_discovery_contract.py
```

## Governance and operations

- Review checklist:
  - `docs/review/protocol-review-checklist.md`
- Roundtable decision notes:
  - `docs/roundtable/RT-2026-02-18-identity-creator-design.md`
- Research and source cross-validation:
  - `docs/research/cross-validation-and-sources.md`
- Consumer integration and rollback playbook:
  - `docs/playbooks/weixinstore-consumer-integration.md`

## Design principles

1. Align with official Codex skills model and discovery behavior.
2. Keep compatibility with native Codex config (`skills`, `mcp_servers`, `model_instructions_file`).
3. Keep identity concise, deterministic, and auditable.
4. Keep conflict resolution explicit: `canon > runtime > skill > tool preference`.

## Status

- Protocol version: `v1.1` (benchmark-hardened draft)
- Discovery contract: `identity/protocol/IDENTITY_DISCOVERY.md`
- Creator skill: `identity-creator` (manifest-aware scaffold + validators)
