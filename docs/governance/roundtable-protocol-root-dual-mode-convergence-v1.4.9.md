# Roundtable: Protocol Root Dual-Mode Convergence (v1.4.9)

Date: 2026-02-23  
Type: Governance design memo (PR-ready, doc-only proposal)  
Scope: identity instance runtime path decoupling, skill-style convergence

## 1. Background

Real runtime operations exposed a repeatable failure mode:

- identity instance assets are complete under local runtime home (for example `/Users/yangxi/.codex/identity/office-ops-expert`)
- but execution quality still depends on whichever protocol repository happens to be the current shell workspace
- when the current workspace is stale, dirty, or temporarily offline, install/validate/upgrade paths become inconsistent

This violates local-instance-first goals from `docs/references/identity-instance-local-operations-and-feedback-governance-guide-v1.0.md`.

## 2. Roundtable synthesis

This roundtable is an engineering synthesis aligned to repository baselines and cross-vendor governance references, not a literal transcript of external vendor participants.

Baselines used:

1. identity-protocol runtime/validator contracts (this repository)
2. skill installer/creator split references:
   - `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
   - `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
3. identity local operations and feedback governance:
   - `docs/references/identity-instance-local-operations-and-feedback-governance-guide-v1.0.md`
4. cross-vendor identity/skill/mcp governance mapping:
   - `docs/references/identity-skill-mcp-cross-vendor-governance-guide-v1.0.md`

Consensus:

- Runtime instance location and protocol tooling location must be explicit and independently controlled.
- Distribution path must converge to skill protocol behavior: installer-plane for distribution, creator-plane for identity mutation.
- Execution evidence must always include the concrete protocol tooling root used by this run.

## 3. Dual-mode contract

Identity runtime supports two equivalent operating modes:

### Mode A: Shared synchronized base

- one team-managed protocol checkout is continuously synchronized
- all identity instances reference this root
- recommended for CI and stable shared operations

Contract:

- `IDENTITY_PROTOCOL_HOME=/absolute/path/to/identity-protocol`
- execution commands may run from any workspace, but tool scripts are loaded from `IDENTITY_PROTOCOL_HOME`

### Mode B: Standalone local checkout

- operator uses any local protocol checkout directly
- useful for offline tests, branch experiments, or isolated hotfix verification

Contract:

- pass `--protocol-root /absolute/path/to/protocol-checkout`
- no requirement to mutate current shell workspace repository

## 4. Skill-protocol convergence mapping

To prevent model-driven path drift, identity protocol follows skill protocol split:

1. installer-plane:
   - install/reinstall/distribute pack artifacts
   - never mutates identity behavior contracts directly
2. creator-plane:
   - identity contract evolution, validation orchestration, upgrade execution
   - must carry lifecycle evidence (trigger/patch/validation/replay)

Convergence requirement:

- both planes must accept protocol root injection (`IDENTITY_PROTOCOL_HOME` or `--protocol-root`)
- both planes must emit protocol-root evidence in reports for audit reproducibility

## 5. Proposed implementation (for architecture PR)

### 5.1 Script changes (proposal)

1. `scripts/resolve_identity_context.py`:
   - added `default_protocol_home()` with env-first resolution:
     - `IDENTITY_PROTOCOL_HOME`
     - fallback to current workspace root
   - added `protocol-home` subcommand for deterministic introspection

2. `scripts/identity_installer.py`:
   - added `--protocol-root` argument (default from `default_protocol_home()`)
   - installer reports now include `protocol_root`

3. `scripts/identity_creator.py`:
   - added global `--protocol-root`
   - validates protocol root contains `scripts/` and `identity/`
   - `init/validate/compile/update` now execute scripts from injected root
   - `activate` flow runs under injected protocol root context

### 5.2 Documentation changes (proposal)

1. `README.md`:
   - added protocol tooling root section
   - added dual-mode usage note and command sample
   - linked this memo in governance document list

## 6. Verification checklist (required before merge)

Use the matrix below before merge/release:

1. shared base mode:
   - set `IDENTITY_PROTOCOL_HOME` to synchronized checkout
   - run creator `validate` for at least one runtime identity
2. standalone mode:
   - pass `--protocol-root` pointing to a second checkout
   - run same `validate` and `update` commands
3. evidence:
   - installer report contains `protocol_root`
   - command output logs show scripts executed from the injected root
4. compatibility:
   - existing workflows without `--protocol-root` continue to run

## 7. Release gate recommendation

Treat missing protocol-root evidence as release blocker for identity runtime changes:

- go/no-go rule:
  - if run report cannot prove `protocol_root`, block promotion
- rationale:
  - without exact tooling root, replay and root-cause audit are non-deterministic

## 8. Practical examples (absolute paths)

Shared synchronized base mode:

```bash
export IDENTITY_HOME="/Users/yangxi/.codex/identity"
export IDENTITY_PROTOCOL_HOME="/Users/yangxi/claude/codex_project/ddm/identity-protocol-regression-v1.4.9"
python "$IDENTITY_PROTOCOL_HOME/scripts/identity_creator.py" \
  --protocol-root "$IDENTITY_PROTOCOL_HOME" \
  validate \
  --identity-id office-ops-expert
```

Standalone local checkout mode:

```bash
python /Users/yangxi/claude/codex_project/ddm/identity-protocol-regression-v1.4.9/scripts/identity_creator.py \
  --protocol-root /Users/yangxi/claude/codex_project/ddm/identity-protocol-regression-v1.4.9 \
  update \
  --identity-id office-ops-expert \
  --mode review-required \
  --catalog /Users/yangxi/.codex/identity/catalog.local.yaml
```
