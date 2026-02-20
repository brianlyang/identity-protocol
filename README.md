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
python scripts/validate_identity_runtime_contract.py
python scripts/validate_identity_learning_loop.py --run-report identity/runtime/examples/store-manager-learning-sample.json
# optional: scaffold a new identity pack
python scripts/create_identity_pack.py --id quality-supervisor --title "Quality Supervisor" --description "Cross-checks listing quality" --register
```

## Governance and operations

- Review checklist:
  - `docs/review/protocol-review-checklist.md`
- Roundtable decision notes:
  - `docs/roundtable/RT-2026-02-18-identity-creator-design.md`
- Research and source cross-validation:
  - `docs/research/cross-validation-and-sources.md`
  - `docs/research/IDENTITY_PROTOCOL_BENCHMARK_SKILLS_2026-02-19.md`
- Consumer integration and rollback playbook:
  - `docs/playbooks/weixinstore-consumer-integration.md`
  - `docs/operations/identity-rollback-drill.md`
  - `docs/specs/identity-compatibility-matrix.md`
  - `docs/guides/identity-creator-operations.md`
- Runtime bottom guardrails (ORRL):
  - `docs/specs/identity-bottom-guardrails-orrL-v1.2.md`
  - `docs/specs/identity-learning-loop-validation-v1.2.1.md`

## Design principles

1. Align with official Codex skills model and discovery behavior.
2. Keep compatibility with native Codex config (`skills`, `mcp_servers`, `model_instructions_file`).
3. Keep identity concise, deterministic, and auditable.
4. Keep conflict resolution explicit: `canon > runtime > skill > tool preference`.
5. Require ORRL (Observe/Reason/Route/Ledger) gates for high-impact runs.
6. Require learning-loop validation to prove reasoning and rulebook linkage.

## Status

- Protocol version: `v1.2.1` (learning-loop-verifiable draft)
- Discovery contract: `identity/protocol/IDENTITY_DISCOVERY.md`
- Creator skill: `identity-creator` (manifest-aware scaffold + validators)
