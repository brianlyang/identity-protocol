# Roundtable: Protocol Root Dual-Mode Convergence (v1.4.9)

Date: 2026-02-23  
Type: Governance design memo (PR-ready, doc-only proposal)  
Status: Proposal (this commit does not implement script/runtime behavior changes)  
Scope: identity instance runtime path decoupling, skill-style convergence

## 1. Background

Real runtime operations exposed a repeatable failure mode:

- identity instance assets are complete under local runtime home (for example `/Users/yangxi/.codex/identity/office-ops-expert`)
- but execution quality still depends on whichever protocol repository happens to be the current shell workspace
- when the current workspace is stale, dirty, or temporarily offline, install/validate/upgrade paths become inconsistent

This violates local-instance-first goals from `docs/references/identity-instance-local-operations-and-feedback-governance-guide-v1.0.md`.

### 1.1 Is this situation real? (cross-check conclusion)

Yes. This is a real and reproducible condition in current baseline, not a hypothetical risk.

Repository cross-check facts:

1. Historical runtime-home behavior has had drift risk and no protocol-root pinning contract by default.
   - `scripts/resolve_identity_context.py`
   - `README.md` section "IDENTITY_HOME resolution order (canonical)"
2. Installer/creator currently resolve execution from current workspace scripts, and there is no documented mandatory `IDENTITY_PROTOCOL_HOME` runtime contract.
   - `scripts/identity_installer.py`
   - `scripts/identity_creator.py`
3. Existing preflight focuses on git sync status (`preflight_identity_runtime_sync.sh`) but does not solve multi-agent path divergence by itself.
   - `scripts/preflight_identity_runtime_sync.sh`
   - `docs/operations/runtime-preflight-checklist-v1.2.13.md`

Operational symptom pattern already observed in real runs:

- identity instance data can be healthy in one local runtime home
- but different operators/agents execute from different protocol checkouts (or stale checkouts)
- resulting validation/upgrade behavior differs, creating replay and audit instability

Decision statement:

- This proposal is justified by concrete repository behavior and runtime evidence pattern.
- It should be treated as release-quality governance hardening, not optional convenience.

### 1.2 Version-boundary note (avoid policy ambiguity)

To prevent mixed interpretations across upgrade windows:

1. `v1.4.9` era discussions captured historical runtime-home drift risk and legacy compatibility context.
2. `v1.4.10+` target baseline is the explicit order documented in runtime tooling/docs:
   - `IDENTITY_HOME` (if explicitly set)
   - `${CODEX_HOME}/identity`
   - `~/.codex/identity`
   - fallback `./.codex/identity` when creation fails
3. This memo focuses on protocol-root determinism and dual-mode governance, and does not redefine the local runtime-home contract.

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
- recommended as default for team/CI to minimize drift

### Mode B: Standalone local checkout

- operator uses any local protocol checkout directly
- useful for offline tests, branch experiments, or isolated hotfix verification

Contract:

- pass `--protocol-root /absolute/path/to/protocol-checkout`
- no requirement to mutate current shell workspace repository
- required to emit explicit run evidence (protocol root + git commit/tag)

### 3.1 Selection policy (must)

To avoid "config chaos" replacing "repo chaos", selection policy is mandatory:

1. Team default:
   - use Mode A (shared synchronized base)
2. Allowed exceptions:
   - use Mode B only for isolated experiments, rollback drills, or offline recovery
3. Evidence requirement:
   - every run report must include protocol-root and version evidence
4. Promotion rule:
   - artifacts generated under Mode B cannot be promoted unless replayed or cross-validated against Mode A

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

### 5.1 Script changes (proposal, not yet implemented in this doc-only commit)

1. `scripts/resolve_identity_context.py`:
   - propose adding `default_protocol_home()` with env-first resolution:
     - `IDENTITY_PROTOCOL_HOME`
     - fallback to current workspace root
   - propose adding `protocol-home` subcommand for deterministic introspection

2. `scripts/identity_installer.py`:
   - propose adding `--protocol-root` argument (default from `default_protocol_home()`)
   - propose requiring installer reports to include `protocol_root`

3. `scripts/identity_creator.py`:
   - propose adding global `--protocol-root`
   - propose validating protocol root contains `scripts/` and `identity/`
   - propose making `init/validate/compile/update` execute scripts from injected root
   - propose making `activate` flow run under injected protocol root context

### 5.2 Documentation changes (proposal, not yet implemented in this doc-only commit)

1. `README.md`:
   - propose adding protocol tooling root section
   - propose adding dual-mode usage note and command sample
   - propose linking this memo in governance document list

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

### 6.1 Evidence contract (machine-checkable, required)

All reports used for promotion arbitration must carry at least:

```json
{
  "identity_id": "base-repo-audit-expert-v3",
  "protocol_mode": "mode_a_shared",
  "protocol_root": "/abs/path/to/protocol",
  "protocol_commit_sha": "40-hex",
  "protocol_ref": "v1.4.10",
  "identity_home": "/Users/yangxi/.codex/identity",
  "catalog_path": "/Users/yangxi/.codex/identity/catalog.local.yaml",
  "generated_at": "2026-02-23T14:30:00Z"
}
```

Required semantics:

1. `protocol_mode` must be one of:
   - `mode_a_shared`
   - `mode_b_standalone`
2. `protocol_root` must be absolute path.
3. `protocol_commit_sha` must be 40-char git sha.
4. If multiple protocol roots appear in one promotion set, arbitration note is mandatory.

## 7. Release gate recommendation

Treat missing protocol-root evidence as release blocker for identity runtime changes:

- go/no-go rule:
  - if run report cannot prove `protocol_root`, block promotion
- rationale:
  - without exact tooling root, replay and root-cause audit are non-deterministic

Additional go/no-go gate:

1. If run evidence does not contain protocol-root + git commit/tag, block.
2. If promotion report mixes multiple protocol roots without explicit arbitration note, block.
3. If Mode B output has no Mode A replay evidence for high-impact changes, block.

### 7.1 Promotion arbitration rules (required)

Mode B artifact promotion to shared baseline requires all conditions:

1. Identity consistency:
   - same `identity_id` between Mode B evidence and Mode A replay evidence.
2. Case consistency:
   - same failure/case reference (for example `problem_case_id` / run correlation id).
3. Replay success:
   - Mode A replay status is `PASS` and required checks are complete.

High-impact change scope (must enforce Mode A replay before promotion):

1. `CURRENT_TASK.json`
2. `IDENTITY_PROMPT.md`
3. `RULEBOOK.jsonl`
4. any change marked by enforcement validators as identity-core surface mutation

Arbitration note minimum fields:

```json
{
  "arbitration_note_id": "arb-20260223-001",
  "decision": "promote_mode_b_artifact",
  "justification": "mode_a_replay_passed_same_case",
  "approved_by": "base-repo-architect",
  "approved_at": "2026-02-23T15:00:00Z"
}
```

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


## 9. Configuration authority and exact locations (must, reviewable)

This section converts policy intent into deterministic configuration points.

### 9.1 Required configuration keys

1. `IDENTITY_HOME`
   - **Meaning**: runtime identity asset root (local identity packs + local catalog + local reports).
   - **Scope**: instance data plane (who is running and where runtime artifacts are stored).
   - **Typical value**: `/Users/<user>/.codex/identity`.
   - **Used by**: creator/installer/update when resolving local pack paths and local catalog default.

2. `IDENTITY_PROTOCOL_HOME`
   - **Meaning**: protocol tooling root containing `scripts/`, `identity/`, validators, and workflow-facing governance logic.
   - **Scope**: control plane (which protocol implementation/version executes this run).
   - **Typical value**: `/abs/path/to/identity-protocol-checkout`.
   - **Used by**: runtime command entry (`python "$IDENTITY_PROTOCOL_HOME/scripts/..."`) and protocol-root evidence.

3. `catalog_path`
   - **Meaning**: concrete catalog file used by this command to resolve `identity_id -> pack_path`.
   - **Scope**: command-time identity routing source of truth.
   - **Typical value**: `${IDENTITY_HOME}/catalog.local.yaml`.
   - **Why critical**: even with correct `IDENTITY_HOME`, wrong `catalog_path` can route to stale/wrong pack.
   - **How set**: explicit `--catalog` (highest), otherwise default from `IDENTITY_HOME`.

4. `protocol_root`
   - **Meaning**: concrete protocol repository root used by the current execution (single-run resolved value).
   - **Scope**: run-level reproducibility and audit evidence.
   - **Typical value**: absolute path supplied by `--protocol-root` or resolved from `IDENTITY_PROTOCOL_HOME`.
   - **Why critical**: determines exactly which validators/scripts version produced this output.
   - **Evidence requirement**: must be absolute path and paired with `protocol_commit_sha` + `protocol_ref` in reports.

### 9.2 Precedence rules (single source of truth)

Protocol root resolution (proposal target):

1. CLI argument `--protocol-root`
2. env `IDENTITY_PROTOCOL_HOME`
3. current protocol workspace root (compatibility fallback; emit warning)

Identity home resolution (current baseline):

1. env `IDENTITY_HOME`
2. `${CODEX_HOME}/identity`
3. `~/.codex/identity`
4. fallback `./.codex/identity` (only when home path creation fails)

Catalog resolution:

1. CLI argument `--catalog`
2. `${IDENTITY_HOME}/catalog.local.yaml`

### 9.3 Where to configure (exact places)

#### A) Developer machine (recommended, stable default)

Configure in shell profile once (for example `~/.zshrc`):

```bash
export CODEX_HOME="$HOME/.codex"
export IDENTITY_HOME="$CODEX_HOME/identity"
export IDENTITY_PROTOCOL_HOME="/abs/path/to/identity-protocol"
```

Apply:

```bash
source ~/.zshrc
```

#### B) CI / Workflow (required for deterministic replay)

Set environment in workflow job (for example `.github/workflows/*`):

```yaml
env:
  CODEX_HOME: /home/runner/.codex
  IDENTITY_HOME: /home/runner/.codex/identity
  IDENTITY_PROTOCOL_HOME: ${{ github.workspace }}
```

#### C) Per-command override (isolated experiment / Mode B)

```bash
python "$IDENTITY_PROTOCOL_HOME/scripts/identity_creator.py"   --protocol-root "$IDENTITY_PROTOCOL_HOME"   update   --identity-id office-ops-expert   --catalog "$IDENTITY_HOME/catalog.local.yaml"   --mode review-required
```

### 9.4 Review checklist for configuration correctness

A reviewer MUST be able to answer all items with concrete evidence:

1. Which `protocol_root` was used in this run?
2. Which `identity_home` and `catalog_path` were used?
3. Are they absolute paths?
4. Is `protocol_commit_sha` a 40-char git SHA?
5. If multiple protocol roots were used, is `arbitration_note_id` present?
6. For high-impact surfaces, is there Mode A replay PASS evidence?

### 9.5 Anti-drift rules (must)

1. Do not rely on implicit shell cwd as long-term protocol source.
2. Do not promote Mode B artifacts without Mode A replay evidence for high-impact changes.
3. Do not merge release claims when report fields miss `protocol_root` + `protocol_commit_sha`.
4. Do not allow mixed protocol roots in one promotion set without arbitration note.

## 10. Implementation mapping (P0 -> scripts)

To convert this memo into enforceable behavior:

1. `scripts/identity_creator.py`
   - add `--protocol-root`
   - emit evidence fields: `protocol_mode`, `protocol_root`, `protocol_commit_sha`, `protocol_ref`, `identity_home`, `catalog_path`, `generated_at`
2. `scripts/identity_installer.py`
   - add/align protocol-root injection and same evidence fields
3. `scripts/execute_identity_upgrade.py`
   - include protocol-root evidence in upgrade report
4. new validator: `scripts/validate_identity_protocol_root_evidence.py`
5. new validator: `scripts/validate_identity_mode_promotion_arbitration.py`
6. CI gates wire-up:
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `.github/workflows/_identity-required-gates.yml`

## 11. Merge semantics and release communication

1. Doc PR can merge first as governance baseline.
2. Implementation PR reaches Full Go only when P0 script + validator + CI wiring are merged.
3. Release note must explicitly state whether `--protocol-root` is fully enforced or still proposal-only.
