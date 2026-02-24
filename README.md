# identity-protocol

Protocol-grade identity control plane for autonomous coding agents.

## Current release posture (v1.4.x baseline)

- **Code-plane**: upgraded with local-runtime boundary + identity-scoped anti-pollution gates.
- **Release-plane**: **Conditional Go** until cloud `required-gates` is green with the latest workflow changes.
- Do **not** externally claim `Full Go` before all required cloud checks are green.

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
2. Otherwise, if shared config file exists, use it:
   - `${CODEX_HOME:-~/.codex}/identity/config/runtime-paths.env`
   - key: `IDENTITY_HOME=...`
3. Otherwise, if `CODEX_HOME` is set, use `${CODEX_HOME}/identity`.
4. Otherwise default to `~/.codex/identity`.
5. If creating that directory fails, fallback to current workspace local path: `./.codex/identity`.

Compatibility note:
- legacy runtime locations remain readable only inside `IDENTITY_HOME`
  (`${IDENTITY_HOME}/identity`, `${IDENTITY_HOME}/identities`, `${IDENTITY_HOME}/instances`).
- there is no implicit fallback to `~/.identity`; migrate old instances explicitly to `$CODEX_HOME/identity`.

This behavior is implemented in `scripts/resolve_identity_context.py::default_identity_home()`
and consumed by `create_identity_pack.py`, `identity_installer.py`, `identity_creator.py`,
and migration tooling.

### Identity scope resolution (governance uplift)

To align with skills-style discovery while preserving runtime safety, identity execution now carries an explicit scope interpretation:

1. CLI explicit (`--catalog`, `--target-root`, `--scope`)
2. environment/runtime config (`IDENTITY_HOME`, `runtime-paths.env`)
3. repo scope (`<repo>/.agents/identity`) when present
4. user scope (`${CODEX_HOME:-~/.codex}/identity`)
5. fallback scope (`./.codex/identity`, recovery-only)

If one `identity_id` resolves to multiple pack paths across layers, tooling now fails by default until explicit arbitration (`--scope`) is provided. This prevents silent cross-scope contamination.

Operational governance commands:

```bash
# detect duplicate instances across repo/user roots
python3 scripts/identity_installer.py scan --identity-id <id>

# adopt one canonical source and lock runtime catalog binding
python3 scripts/identity_installer.py adopt --identity-id <id> --source-pack <path> --scope USER
python3 scripts/identity_installer.py lock --identity-id <id> --scope USER
```

Mandatory scope validators:
- `scripts/validate_identity_scope_resolution.py`
- `scripts/validate_identity_scope_isolation.py`
- `scripts/validate_identity_scope_persistence.py`

Runtime self-healing entrypoint:

```bash
# dry-run (scan only)
python3 scripts/identity_creator.py heal --identity-id <id> --catalog <local-catalog>

# apply canonicalization + repair + validate
python3 scripts/identity_creator.py heal --identity-id <id> --catalog <local-catalog> --scope USER --apply
```

Heal executes: `scan -> adopt -> lock -> repair-paths -> validate`, and emits a JSON report under `/tmp/identity-heal-reports/` by default.
If validate fails due to missing protocol/role-binding baseline evidence, heal auto-triggers
`scripts/repair_identity_baseline_evidence.py` and re-validates once.

Health diagnostics (error collection + remediation suggestions):

```bash
python3 scripts/collect_identity_health_report.py \
  --identity-id <id> \
  --catalog <catalog> \
  --out-dir /tmp/identity-health-reports \
  --enforce-pass

python3 scripts/validate_identity_health_contract.py \
  --identity-id <id> \
  --report-dir /tmp/identity-health-reports \
  --require-pass
```

These health commands are wired into release-readiness, e2e, and required-gates to keep CI contract-controlled.

Permission-state contract:

```bash
python3 scripts/validate_identity_permission_state.py \
  --identity-id <id> \
  --report <identity-upgrade-exec-report.json> \
  --require-written
```

In CI/release contexts, deferred writeback due to permission blocking is explicitly rejected.

Protocol/runtime hard boundary (P0):

- Runtime execution is blocked when `pack_path` is inside the protocol repository root.
- Exception is explicit fixture/debug mode only:
  - `identity_creator.py update --allow-protocol-root-pack`
  - `execute_identity_upgrade.py --allow-protocol-root-pack`
- Runtime output root resolution no longer falls back to `<protocol_root>/.codex/...`.
  Default external fallback is `/tmp/identity-runtime/<identity-id>`.

### Shared base-repo path config (recommended for team testing)

To avoid per-shell drift, configure shared defaults once:

```bash
python3 scripts/configure_identity_runtime_paths.py \
  --identity-home "${IDENTITY_HOME:-${CODEX_HOME:-$HOME/.codex}/identity}" \
  --protocol-home "${IDENTITY_PROTOCOL_HOME:-$(pwd)}"
```

This writes:
- `${CODEX_HOME:-$HOME/.codex}/identity/config/runtime-paths.env`
  - `IDENTITY_HOME=...`
  - `IDENTITY_PROTOCOL_HOME=...`

`IDENTITY_PROTOCOL_HOME` resolution order:
1. environment variable `IDENTITY_PROTOCOL_HOME`
2. shared config file key `IDENTITY_PROTOCOL_HOME`
3. current working directory

Implementation note:
- `scripts/configure_identity_runtime_paths.py` defaults are now machine-portable:
  - `IDENTITY_HOME` default derives from `${CODEX_HOME:-~/.codex}/identity`
  - `IDENTITY_PROTOCOL_HOME` default derives from current repo root/cwd
  - no user-specific absolute path is hardcoded

### Protocol root control (dual-mode governance)

For deterministic replay and auditable upgrades, runtime reports now carry protocol-root evidence:

- `protocol_mode` (`mode_a_shared` / `mode_b_standalone`)
- `protocol_root`
- `protocol_commit_sha`
- `protocol_ref`
- `identity_home`
- `catalog_path`
- `generated_at`

Field semantics (authoritative):

- `IDENTITY_HOME` (env): runtime identity storage root (local instance source of truth).
  - Holds runtime packs and local catalog.
  - Recommended: `${CODEX_HOME}/identity`.
- `IDENTITY_PROTOCOL_HOME` (env): protocol repository root to execute creator/installer/update toolchain.
  - Used to pin which protocol code version generated evidence.
- `catalog_path` (report field): exact catalog file used in this run (repo catalog or local catalog).
  - This is execution evidence, not a config replacement.
  - Lets auditors prove which catalog drove resolution at runtime.
- `protocol_root` (report field): absolute protocol repo/worktree root that executed this run.
  - Combined with `protocol_commit_sha` and `protocol_ref` for replayability and cross-root arbitration.

Recommended shared mode (Mode A):

```bash
export IDENTITY_PROTOCOL_HOME="/abs/path/to/identity-protocol"
python "$IDENTITY_PROTOCOL_HOME/scripts/identity_creator.py" update \
  --identity-id store-manager \
  --protocol-mode mode_a_shared
```

Standalone mode (Mode B) must include promotion arbitration evidence before high-impact changes are promoted.

## Runtime hard boundary (must follow)

For runtime operations (validate/activate/update/install/writeback), always use local context:

- `IDENTITY_HOME` runtime root
- local catalog `${IDENTITY_HOME}/catalog.local.yaml`
- identity-scoped runtime evidence paths

### Forbidden operations

- Do **not** use repo `identity/catalog/identities.yaml` as runtime status source.
- Do **not** use repo `identity/packs/*` as runtime live instance packs.
- Do **not** allow global sample fallback from another identity (including `store-manager`).
- Do **not** accept cross-identity evidence/log/sample matches.
- Do **not** use `META.status` as activation scheduling source; activation source-of-truth is catalog (`catalog.local.yaml`).

### State consistency gate

- Active status source-of-truth: catalog (`catalog.local.yaml` for runtime).
- Strategy selected in v1.4.x hardening: **dual-write + strong consistency**.
  - catalog drives activation/scheduling decisions.
  - `META.status` is a required mirrored field for audit/readability.
  - activation transaction must keep catalog + META synchronized.
- Validator: `scripts/validate_identity_state_consistency.py`

## Quickstart

```bash
pip install -r requirements-dev.txt

# Step 0 (required): select identity runtime mode before any update/install
# Recommended (project-local, sandbox-friendly):
source ./scripts/identity_runtime_select.sh project
# Alternative (global runtime, may require escalation in restricted sandbox):
# source ./scripts/identity_runtime_select.sh global

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

## Minimum acceptance commands (release gate)

Before any release claim, run and keep output artifacts:

```bash
python3 scripts/identity_creator.py validate --identity-id office-ops-expert --catalog "${IDENTITY_HOME}/catalog.local.yaml"
python3 scripts/validate_identity_local_persistence.py --runtime-mode
python3 scripts/release_readiness_check.py --identity-id office-ops-expert --base HEAD~1 --head HEAD
IDENTITY_IDS=office-ops-expert bash scripts/e2e_smoke_test.sh
python3 scripts/validate_identity_instance_isolation.py --catalog "${IDENTITY_HOME}/catalog.local.yaml" --identity-id office-ops-expert
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
  - `docs/governance/audit-snapshot-2026-02-24-self-heal-and-permission-state-v1.4.12.md`
  - `docs/governance/audit-snapshot-2026-02-24-release-doc-governance-closure-v1.4.12.md`
  - `docs/governance/runtime-artifact-isolation-root-cause-and-remediation-v1.4.12.md`
  - `docs/governance/audit-snapshot-2026-02-25-protocol-runtime-boundary-closure-v1.4.12.md`

### Release documentation closure set (MUST, same PR batch)

For any release posture update (Conditional Go/Full Go), the following files must be synchronized in one review batch:

1. `README.md`
2. `CHANGELOG.md`
3. `VERSIONING.md`
4. `requirements-dev.txt`
5. `identity/protocol/IDENTITY_PROTOCOL.md`
6. `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
7. latest `docs/governance/audit-snapshot-*.md` record

### Release evidence repository boundary (MUST)

The release/audit source-of-truth repository is:

`/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local`

Before running release commands, verify working directory and branch:

```bash
cd /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local
pwd
git rev-parse --abbrev-ref HEAD
```
  - `docs/governance/audit-snapshot-2026-02-23-release-closure-v1.4.7.md`
  - `docs/governance/audit-prep-v1.4.12-scope-runtime-closure.md`
  - `docs/governance/audit-snapshot-2026-02-24-self-heal-and-permission-state-v1.4.12.md`
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

- Protocol version: `v1.4.10` (draft)
- Discovery contract: `identity/protocol/IDENTITY_DISCOVERY.md`
- Creator skill: `identity-creator` (create + update validators)
