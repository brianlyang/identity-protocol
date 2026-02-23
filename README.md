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
- `${IDENTITY_HOME}/` — local runtime identity assets (packs + catalog), isolated from base repo sync
- `skills/identity-creator/` — creator skill to scaffold/validate identity packs
- `scripts/` — deterministic compile/validate tooling
- `docs/` — ADR, roundtable, research, review, migration playbooks

## Critical fix in v1.4.6: local-instance persistence boundary

This is the severe bug closed in v1.4.6 hardening:

- Runtime identities used to be created under repo paths (`identity/packs/...`), so pull/re-clone could overwrite or lose live instances.
- Now runtime instances default to **local-only** storage under `IDENTITY_HOME`, while repo identities (e.g. `store-manager`) are explicitly **fixture/demo**.

Enforcement:

- `create_identity_pack.py` defaults to local paths, blocks repo target unless `--repo-fixture`
- `identity_installer.py` defaults to local paths, blocks repo target unless `--allow-repo-target`
- `identity_creator.py` resolves runtime context from local catalog first (local > repo)
- `validate_identity_local_persistence.py` hard-fails invalid runtime placement
- Canonical runtime pack root is `${IDENTITY_HOME}` (skills-style root convention)
  (legacy `${IDENTITY_HOME}/identity`, `${IDENTITY_HOME}/identities`, and `${IDENTITY_HOME}/instances` are auto-compatible)

Governance record:
- `docs/governance/local-instance-persistence-boundary-v1.4.6.md`

### IDENTITY_HOME resolution order (canonical)

All creator/installer/runtime context resolution follows the same order:

1. If environment variable `IDENTITY_HOME` is set, use it.
2. Otherwise, if `CODEX_HOME` is set, use `${CODEX_HOME}/identity`.
3. Otherwise default to `~/.codex/identity`.
4. If creating that directory fails, fallback to current workspace local path: `./.codex/identity`.

Compatibility note:
- legacy runtime locations remain readable only inside `IDENTITY_HOME`
  (`${IDENTITY_HOME}/identity`, `${IDENTITY_HOME}/identities`, `${IDENTITY_HOME}/instances`).
- there is no implicit fallback to `~/.identity`; migrate old instances explicitly to `$CODEX_HOME/identity`.

This behavior is implemented in `scripts/resolve_identity_context.py::default_identity_home()`
and consumed by `create_identity_pack.py`, `identity_installer.py`, `identity_creator.py`,
and migration tooling.

## Quickstart

```bash
pip install -r requirements-dev.txt
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export IDENTITY_HOME="${IDENTITY_HOME:-$CODEX_HOME/identity}"

# optional: migrate legacy runtime identities from repo paths to local paths
python scripts/migrate_repo_instances_to_local.py --apply

python scripts/validate_identity_protocol.py
python scripts/validate_identity_local_persistence.py
python scripts/compile_identity_runtime.py
python scripts/validate_identity_manifest.py
python scripts/test_identity_discovery_contract.py
python scripts/validate_identity_runtime_contract.py
python scripts/validate_identity_role_binding.py --identity-id store-manager
python scripts/validate_identity_upgrade_prereq.py --identity-id store-manager
python scripts/validate_identity_update_lifecycle.py --identity-id store-manager
python scripts/validate_identity_trigger_regression.py --identity-id store-manager
python scripts/validate_identity_collab_trigger.py --identity-id store-manager --self-test
python scripts/validate_identity_learning_loop.py --run-report identity/runtime/examples/store-manager-learning-sample.json
python scripts/validate_agent_handoff_contract.py --identity-id store-manager --self-test
python scripts/validate_identity_orchestration_contract.py --identity-id store-manager
python scripts/validate_identity_knowledge_contract.py --identity-id store-manager
python scripts/validate_identity_experience_feedback.py --identity-id store-manager
python scripts/validate_identity_install_safety.py --identity-id store-manager
python scripts/validate_identity_install_provenance.py --identity-id store-manager
python scripts/validate_identity_experience_feedback_governance.py --identity-id store-manager
python scripts/validate_identity_capability_arbitration.py --identity-id store-manager
python scripts/validate_identity_ci_enforcement.py --identity-id store-manager
python scripts/validate_release_freeze_boundary.py
python scripts/export_route_quality_metrics.py --identity-id store-manager
# optional: execute upgrade cycle from metrics/arbitration thresholds
python scripts/execute_identity_upgrade.py --identity-id store-manager --mode review-required
# optional: run release-readiness bundle
python scripts/release_readiness_check.py --identity-id store-manager
# optional: scaffold a new local runtime identity
python scripts/create_identity_pack.py --id quality-supervisor --title "Quality Supervisor" --description "Cross-checks listing quality" --register
# optional: explicit fixture creation under repo (demo only)
python scripts/create_identity_pack.py --id demo-fixture --title "Demo Fixture" --description "Fixture identity" --repo-fixture --pack-root identity/packs --catalog identity/catalog/identities.yaml --register
```

## Mandatory git sync before runtime tests

When updating from the protocol git repository, run this sequence before any live/CI-like validation:

```bash
# 1) verify local protocol repo is synced with origin/main
bash scripts/preflight_identity_runtime_sync.sh /path/to/identity-protocol-local main

# 2) if stale, fast-forward only
git checkout main
git pull --ff-only

# 3) run required gates locally
python scripts/validate_identity_protocol.py
python scripts/validate_identity_runtime_contract.py --identity-id store-manager
python scripts/validate_identity_ci_enforcement.py --identity-id store-manager
# 4) when running e2e in identity-neutral baseline, pass explicit target IDs
IDENTITY_IDS=store-manager bash scripts/e2e_smoke_test.sh
```

## Fast review path (skill mechanism alignment)

For fast, consistent review of the key skill mechanisms (trigger/create/update/validate + installer/creator split + mcp/tool collaboration), read in this order:

1. `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md` (canonical entry)
2. `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md` (full SOP)
3. `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md` (strategy/capability/execution collaboration)
4. `docs/references/identity-skill-mcp-tool-extension-cross-validation-v1.4.1.md` (non-conflict mapping + capability-gap extension path)
5. `docs/references/identity-skill-mcp-cross-vendor-governance-guide-v1.0.md` (OpenAI/Anthropic/Gemini/MCP governance synthesis for protocol review)
6. `docs/references/identity-instance-local-operations-and-feedback-governance-guide-v1.0.md` (local-instance-first installer/creator + feedback-loop governance)
7. `docs/specs/identity-update-lifecycle-contract-v1.2.4.md` (identity mirror of update chain)
8. `docs/specs/identity-trigger-regression-contract-v1.2.5.md` (positive/boundary/negative suites)
9. `identity/protocol/AGENT_HANDOFF_CONTRACT.md` (master/sub anti-drift contract)
10. `docs/specs/identity-role-binding-contract-v1.4.6.md` (identity activation/switch guardrails)

## Governance and operations

### Documentation taxonomy (MUST)

- `docs/governance/`: enforceable internal policy, CI/release gates, and audit closure criteria.
- `docs/references/`: external references, cross-vendor mappings, and background material.

If a document defines required behavior for CI/release/audit decisions, it belongs in `docs/governance/`.

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
  - `docs/specs/identity-control-loop-v1.4.0.md`
- Skill protocol baseline references for identity reviewers:
  - `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
  - `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
  - `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
  - `docs/references/identity-skill-mcp-tool-extension-cross-validation-v1.4.1.md`
  - `docs/references/identity-skill-mcp-cross-vendor-governance-guide-v1.0.md`
  - `docs/references/identity-instance-local-operations-and-feedback-governance-guide-v1.0.md`
- Branch protection last-mile checklist:
  - `docs/governance/branch-protection-required-checks-v1.2.8.md`
- Audit snapshots (fixed governance action):
  - `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
  - `docs/governance/audit-snapshot-policy-v1.2.11.md`
  - `docs/governance/identity-instance-self-driven-upgrade-and-base-feedback-design-v1.4.6.md`
  - `docs/governance/local-instance-persistence-boundary-v1.4.6.md`
  - `docs/governance/audit-snapshot-2026-02-23-release-closure-v1.4.7.md`
  - `docs/governance/templates/upgrade-cross-validation-template.md`
- Runtime identity migration guide:
  - `docs/guides/runtime-instance-migration-guide-v1.4.7.md`
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

## Control-loop contracts (MUST)

Identity must run as a single closed loop:

`Observe -> Decide -> Orchestrate -> Validate -> Learn -> Update`

This is enforced by contract + validators:
- `capability_orchestration_contract` -> `scripts/validate_identity_orchestration_contract.py`
- `knowledge_acquisition_contract` -> `scripts/validate_identity_knowledge_contract.py`
- `experience_feedback_contract` -> `scripts/validate_identity_experience_feedback.py`
- `ci_enforcement_contract` -> `scripts/validate_identity_ci_enforcement.py`

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

- Protocol version: `v1.4.6` (draft)
- Discovery contract: `identity/protocol/IDENTITY_DISCOVERY.md`
- Creator skill: `identity-creator` (create + update validators)
