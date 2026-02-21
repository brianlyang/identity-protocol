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
python scripts/validate_identity_upgrade_prereq.py --identity-id store-manager
python scripts/validate_identity_update_lifecycle.py --identity-id store-manager
python scripts/validate_identity_trigger_regression.py --identity-id store-manager
python scripts/validate_identity_collab_trigger.py --identity-id store-manager --self-test
python scripts/validate_identity_learning_loop.py --run-report identity/runtime/examples/store-manager-learning-sample.json
python scripts/validate_agent_handoff_contract.py --identity-id store-manager --self-test
# optional: scaffold a new identity pack
python scripts/create_identity_pack.py --id quality-supervisor --title "Quality Supervisor" --description "Cross-checks listing quality" --register
```

## Fast review path (skill mechanism alignment)

For fast, consistent review of the key skill mechanisms (trigger/create/update/validate + installer/creator split + mcp/tool collaboration), read in this order:

1. `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md` (canonical entry)
2. `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md` (full SOP)
3. `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md` (strategy/capability/execution collaboration)
4. `docs/specs/identity-update-lifecycle-contract-v1.2.4.md` (identity mirror of update chain)
5. `docs/specs/identity-trigger-regression-contract-v1.2.5.md` (positive/boundary/negative suites)
6. `identity/protocol/AGENT_HANDOFF_CONTRACT.md` (master/sub anti-drift contract)

## Governance and operations

- Review checklist:
  - `docs/review/protocol-review-checklist.md`
  - `docs/review/core-capability-verification-matrix.md`
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
  - `docs/guides/consumer-quickstart-skill-like-integration.md`
- Runtime bottom guardrails (ORRL):
  - `docs/specs/identity-bottom-guardrails-orrL-v1.2.md`
  - `docs/specs/identity-learning-loop-validation-v1.2.1.md`
  - `docs/specs/identity-update-lifecycle-contract-v1.2.4.md`
  - `docs/specs/identity-trigger-regression-contract-v1.2.5.md`
  - `docs/specs/identity-collaboration-trigger-contract-v1.3.0.md`
- Skill protocol baseline references for identity reviewers:
  - `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
  - `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
  - `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
- Branch protection last-mile checklist:
  - `docs/governance/branch-protection-required-checks-v1.2.8.md`
- Audit snapshots (fixed governance action):
  - `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
  - `docs/governance/audit-snapshot-policy-v1.2.11.md`
- Runtime test preflight (local sync gate):
  - `docs/operations/runtime-preflight-checklist-v1.2.13.md`
  - `scripts/preflight_identity_runtime_sync.sh`

## Protocol baseline review gate (MUST)

For any **identity capability upgrade** or **identity architecture decision**, maintainers must review and cite protocol baselines **before** giving conclusions:

1. `identity-protocol` canonical protocol files (this repository)
2. OpenAI Codex Skills official docs
3. Agent Skills specification
4. MCP official specification

This requirement is enforced via runtime contract keys:
- `gates.protocol_baseline_review_gate = "required"`
- `protocol_review_contract` (mandatory sources + evidence schema)

Validation is executed by:
- `scripts/validate_identity_runtime_contract.py`

## Identity update lifecycle (MUST, skill-style)

Identity must evolve with the same discipline as skill updates.

Required chain:
1. trigger
2. patch surface
3. validation
4. replay on original failing case

This is enforced via runtime keys:
- `gates.identity_update_gate = "required"`
- `identity_update_lifecycle_contract`

Validation is executed by:
- `scripts/validate_identity_update_lifecycle.py`

## Identity trigger regression (MUST, skill-style)

Identity update/routing changes must pass trigger regression with three suites:
- positive cases
- boundary cases
- negative cases

This is enforced via runtime key:
- `trigger_regression_contract`

Validation is executed by:
- `scripts/validate_identity_trigger_regression.py`

## Master/Sub handoff contract (MUST)

Delegated execution must emit structured handoff payloads and must not mutate top-level runtime contracts.

This is enforced via runtime keys:
- `gates.agent_handoff_gate = "required"`
- `agent_handoff_contract`

Validation is executed by:
- `scripts/validate_agent_handoff_contract.py`

## Human-collab trigger contract (MUST)

Human-required blockers (login/captcha/session/manual verification) must trigger auto-notify and receipt evidence.

This is enforced via runtime keys:
- `gates.collaboration_trigger_gate = "required"`
- `blocker_taxonomy_contract`
- `collaboration_trigger_contract`

Validation is executed by:
- `scripts/validate_identity_collab_trigger.py`

## Design principles

1. Align with official Codex skills model and discovery behavior.
2. Keep compatibility with native Codex config (`skills`, `mcp_servers`, `model_instructions_file`).
3. Keep identity concise, deterministic, and auditable.
4. Keep conflict resolution explicit: `canon > runtime > skill > tool preference`.
5. Require ORRL (Observe/Reason/Route/Ledger) gates for high-impact runs.
6. Require learning-loop validation to prove reasoning and rulebook linkage.
7. Require protocol baseline review evidence before identity-level upgrade conclusions.
8. Require skill-style identity update lifecycle (trigger/patch/validate/replay).
9. Require skill-style identity trigger regression (positive/boundary/negative).
10. Require master/sub handoff payload validation and mutation-safety checks.
11. Require human-collab blocker taxonomy + immediate auto-notify + receipt evidence.

## Status

- Protocol version: `v1.3.0` (draft)
- Discovery contract: `identity/protocol/IDENTITY_DISCOVERY.md`
- Creator skill: `identity-creator` (create + update validators)
