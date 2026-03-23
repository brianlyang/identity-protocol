# identity-protocol

Protocol-grade identity control plane for autonomous coding agents.

## Core goal & value (why this system exists)

The core objective is to make agent execution **deterministic, auditable, and release-safe**.

This system is intentionally designed to solve three recurring failure modes:

1. **“Can run” but not “can prove”**  
   We require machine-checkable evidence (reports + validators), not chat-memory success claims.
2. **Path/scope drift across project/global roots**  
   Runtime mode selection, explicit catalog binding, and scope checks prevent silent cross-instance contamination.
3. **Identity becoming a static shell**  
   `IDENTITY_PROMPT.md` is treated as a runtime contract object (activation, validation, hash evidence, lifecycle updates), not just a passive file.
   Current loading model is **command-time reload** (per validate/update/e2e/readiness invocation), not daemon hot-reload.
   Upgrade execution reports now carry prompt activation/lifecycle evidence fields:
   `identity_prompt_path`, `identity_prompt_sha256`, `identity_prompt_bytes`,
   `identity_prompt_activated_at`, `identity_prompt_source_layer`, `identity_prompt_scope`,
   `identity_prompt_status`, `prompt_change_required`, `prompt_change_applied`,
   `identity_prompt_hash_before`, `identity_prompt_hash_after`, `identity_prompt_change_note`.

### Practical outcomes

- Better release safety: required gates block promotion when critical contracts fail.
- Lower audit cost: every key decision can be traced to report fields and validator outputs.
- Continuous identity evolution: prompt/rulebook/task-history can evolve with explicit evidence and replayability.

## Identity launcher quickstart (one-shot copyable commands)

`v1.6.14` freezes launcher command discovery as a protocol-owned surface, so operators should not manually assemble
identity startup/resume commands in chat.

Preferred operator surface:

- short launcher: `id-<identity-id>`

Explicit generic surface:

- `identity-codex --identity-id <identity-id> -- <codex args>`

Print the full copyable command bundle for any governed identity:

```bash
identity-codex commands --identity-id <identity-id>
```

If the per-identity short launcher is already installed, the even shorter surface is:

```bash
id-<identity-id> commands
```

If you want the bundle to evaluate resume readiness, pass the host thread UUID explicitly:

```bash
identity-codex commands --identity-id <identity-id> --thread-id <host-thread-uuid>
```

If you are running the discovery flow outside the currently authoritative identity session binding,
seed the run tuple explicitly so the bundle can still produce a fresh-shell-executable resume command:

```bash
identity-codex commands --identity-id <identity-id> --thread-id <host-thread-uuid> --session-id <run:session-id>
```

Critical semantic boundary:

- `resume <host-thread-uuid>` is still the **Codex transcript recovery target**.
- `--session-id run:<...>` is only the launcher-side identity session tuple closure.
- `--session-id` does **not** replace `resume <host-thread-uuid>`.
- the host thread UUID must **never** be reinterpreted as the identity session tuple.

What this prints:

- preferred short start command, for example `id-<identity-id>`
- absolute-path fallback start command under `${CODEX_HOME}/bin/`
- preferred short resume command as a reference surface, plus the protocol-owned fresh-shell resume command when resume is actually executable
- generic `identity-codex --identity-id ...` equivalents for repair/documentation flows
- all commands are terminal-native direct commands; shell-wrapped `zsh -lic '...'` surfaces are non-canonical
- `recommended_user_command` is selected by fresh-shell executability, not by host-thread UUID presence alone
- when the ambient shell catalog does not match the resolved identity catalog, the recommended command carries explicit `--catalog <resolved-catalog>`
- when resume needs identity-session tuple closure, the recommended resume command carries explicit `--session-id run:<...>`
- `resume_status` can be `PASS_REQUIRED` only when both the host thread UUID and the authoritative identity session tuple are resolved
- when no fresh-shell resume command is available, `recommended_user_command` falls back to the start command instead of promoting a stale shortcut

For identity instances and other protocol consumers, use the structured surface:

```bash
identity-codex commands --identity-id <identity-id> --json-only
```

That JSON is the protocol-owned guidance bundle. It now carries:

- `recommended_user_command`
- `catalog_context_status`
- `host_thread_id_status`
- `identity_session_tuple_status`
- `resume_command_fresh_shell_executable_status`
- `copyable_commands.start`
- `copyable_commands.resume`
- `instance_answer_guidance`
- `continuity_support` for launcher/instance internal consumers only

So the protocol provides the structured command bundle, while the identity instance gives the concrete final answer to the user.

Operational rule:

- if someone asks “`identity_id=XXX` 如何启动 / 如何续接”, the answer should come from this protocol-owned command bundle,
  not from manual command拼接, python helper invocation, or workspace-specific wrapper folklore.

## Identity continuity recovery quickstart (v1.6.16 ask/answer surface)

`v1.6.16` is independent from launcher startup, but it now freezes a protocol-owned answer surface for
identity-visible continuity questions such as:

- “开一个新窗口，怎么把我迁过去？”
- “clear 之后，怎么再加入记忆恢复任务？”

Operator rule:

- the operator should ask the identity instance directly;
- the identity instance should answer from the governed reentry answer bundle;
- launcher start/resume command lookup still belongs to `v1.6.14`.

Protocol/internal renderer for that answer surface:

```bash
python3 scripts/render_identity_context_reentry_answers.py --identity-id <identity-id> --json-only
```

That bundle returns structured facts such as:

- `overall_reentry_readiness_status`
- `live_reentry_consumption_proof_status`
- `recommended_reentry_answer_mode`
- `intent_answers.migrate_new_window`
- `intent_answers.reload_after_clear`
- `copyable_reentry_task_block`

Operational rule for identity instances:

- when asked about new-window migration or clear-after-reset recovery, return the concrete governed reentry task block from this bundle;
- do **not** manually assemble recovery payloads from transcript memory;
- do **not** inject or hardcode thread UUIDs on the continuity surface;
- if readiness is not `PASS_REQUIRED`, do **not** claim memory recovery is ready;
- if readiness is `PASS_REQUIRED` but live proof is not yet observed, you may return the governed reentry task block, but must explicitly state that successful recovery is only proven after `instance_reentry_consumption_receipt` is emitted.
- if readiness and live proof are both `PASS_REQUIRED`, you may state that governed recovery is live-proven, but launcher start/resume command lookup still remains delegated to `v1.6.14`.
- continuity outputs must land only in these fixed runtime families:
  - `runtime/reports/context-continuity/continuity-rolling-*.json`
  - `runtime/reports/context-continuity/continuity-stage-*.json`
  - `runtime/reports/context-continuity/continuity-migration-*.json`
  - `runtime/state/context-continuity/active-reentry-brief.json`
  - `runtime/reports/context-continuity/*-receipt.json`
- treat `runtime/memory-absorption/**` as legacy absorption/quarantine only; canonical outputs must be re-materialized into their governed lane paths rather than consumed there.
- live adoption is a **hard-downsink/template-materialization** requirement, not a chat convention:
  - pack-local `scripts/` must contain these exact files: `run_identity_context_continuity_guard.sh`, `emit_identity_context_checkpoint.py`, `materialize_identity_reentry_brief.py`, and `emit_identity_reentry_consumption_receipt.py`;
  - the shell guard is the proactive cadence/trigger dispatcher; the Python scripts are deterministic payload emitters;
  - the shell guard must persist `runtime/state/context-continuity/guard-state.json` and write `runtime/reports/context-continuity/guard-*.json`;
  - those `guard-*.json` files are auxiliary protocol-owned control receipts and are explicitly outside the four-role `RQ-046` receipt-family join; they may coexist under the same report root without invalidating receipt-family closure;
  - they must be registered in `scripts/INSTANCE_SCRIPT_MANIFEST.json`;
  - they must write only to `runtime/reports/context-continuity/continuity-rolling-*.json`, `runtime/reports/context-continuity/continuity-stage-*.json`, `runtime/reports/context-continuity/continuity-migration-*.json`, `runtime/state/context-continuity/active-reentry-brief.json`, and the corresponding receipt files under `runtime/reports/context-continuity/`.
- required-coverage semantics for this family are also frozen:
  - once `context_continuity_contract_v1` / `reentry_brief_consumption_contract_v1` are required in `CURRENT_TASK.json` and the canonical continuity runtime surfaces are materialized, `validate_required_contract_coverage.py` must count `identity_context_continuity`, `identity_reentry_brief`, `identity_reentry_consumption`, and `identity_context_continuity_receipts` as instance-adopted protocol targets;
  - they must not be silently demoted back to lane-excluded `SKIPPED_NOT_REQUIRED` merely because generic current-round protocol-entry correlation is absent.

### Artifact-family routing quick reference (v1.6.18)

`memory` is not a canonical protocol sink. Inside identity protocol scope, every persisted artifact must resolve to one exact governed family:

- pack rulebook family -> `RULEBOOK.jsonl`
- pack task-history family -> `TASK_HISTORY.md`
- runtime dialogue-retention family -> `runtime/reports/dialogue-retention/**`, `runtime/state/dialogue-retention/**`
- runtime dialogue-governance family -> `runtime/reports/dialogue-content-synthesis-<identity-id>-*.json`, `runtime/reports/dialogue-cross-validation-matrix-<identity-id>-*.json`, `runtime/reports/dialogue-result-support-<identity-id>-*.json`
- runtime experience-feedback family -> `runtime/rulebooks/positive.jsonl`, `runtime/rulebooks/negative.jsonl`, `runtime/examples/*experience-feedback*.json`, `runtime/logs/feedback/*.json`
- runtime protocol-feedback family -> `runtime/protocol-feedback/**`
- runtime continuity/reentry family -> `runtime/reports/context-continuity/**`, `runtime/state/context-continuity/**`
- runtime memory-absorption family -> `runtime/memory-absorption/**` (quarantine/re-materialization only)

Hard routing rules:

- `RULEBOOK.jsonl` and `runtime/rulebooks/*.jsonl` are not the same object.
- `TASK_HISTORY.md` is chronology, not continuity.
- `runtime/reports/dialogue-retention/**` and `runtime/state/dialogue-retention/**` are governed raw-dialogue mirrors plus receipts/supplements, not continuity or dialogue-governance summaries.
- `runtime/protocol-feedback/**` is governance communication, not generic learning/continuity storage.
- `runtime/memory-absorption/**` cannot satisfy active continuity, dialogue, learning, or protocol-feedback obligations.
- declaration keys and gates such as `reject_memory_gate`, `dialogue_retention_contract_v1`, `dialogue_governance_contract`, `experience_feedback_contract`, `context_continuity_contract_v1`, and `reentry_brief_consumption_contract_v1` are control-plane declarations, not artifact sinks.

### Protocol SSOT governance (canonical source + coupling)

- Canonical protocol-strengthening source:
  `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
- `artifacts/` content is evidence-only and non-normative.
- Protocol core-change scope is maintained in:
  `docs/governance/templates/protocol-core-change-map.yaml`
- Enforcement validators:
  - `scripts/validate_protocol_ssot_source.py`
  - `scripts/validate_protocol_handoff_coupling.py`
- Local preflight helper (tooling + auth readiness):
  - `scripts/preflight_protocol_audit_env.sh`
  - run before protocol audits:
    - `bash scripts/preflight_protocol_audit_env.sh`
    - `bash scripts/preflight_protocol_audit_env.sh --require-gh-auth` (release-grade strict profile)
  - checks local parity for:
    - `actionlint`
    - `ast-grep`
    - `gitleaks`
    - `gh auth status -h github.com`
  - when `gh auth` is not ready, strict-union readiness may fail with `IP-CAP-003`;
    treat this as environment-auth not-ready state, not protocol-regression.

### Dialogue governance (optional, contract-first)

For identities that need stronger conversation-to-result evidence guarantees, add
`dialogue_governance_contract` to `CURRENT_TASK.json` and provide dialogue artifacts.

Three optional validators are available and are wired into e2e/readiness/required-gates:

```bash
python3 scripts/validate_identity_dialogue_content.py --identity-id <id> --catalog <catalog>
python3 scripts/validate_identity_dialogue_cross_validation.py --identity-id <id> --catalog <catalog>
python3 scripts/validate_identity_dialogue_result_support.py --identity-id <id> --catalog <catalog>
```

Rollout semantics are contract-driven:

- `required=false` (or contract absent): validators skip without blocking.
- `required=true` + `rollout_mode=warn`: issues are reported but non-blocking.
- `required=true` + `rollout_mode=enforce`: violations fail with deterministic codes
  (`IP-DCIC-001..004`).
- dialogue synthesis belongs under governed dialogue report paths:
  - `runtime/reports/dialogue-content-synthesis-<identity-id>-*.json`
  - `runtime/reports/dialogue-cross-validation-matrix-<identity-id>-*.json`
  - `runtime/reports/dialogue-result-support-<identity-id>-*.json`

Scaffold default:

- `identity_creator init` / `create_identity_pack.py` now inject a
  `dialogue_governance_contract` skeleton by default with `required=false`,
  so new identities are protocol-ready with zero runtime disruption.

### Boundary model: Identity vs Agent vs Skill vs MCP vs Tool

To avoid capability overlap and policy conflicts, use this layered model:

1. **Identity Prompt (governance layer, highest priority)**  
   Defines role, guardrails, decision policy (Full Go / Conditional Go / Not Go), and escalation rules.
2. **Agent (orchestration layer)**  
   Plans and executes tasks under identity governance constraints.
3. **Skill (method layer)**  
   Provides reusable task workflows; cannot override identity safety/governance boundaries.
4. **MCP (integration transport layer)**  
   Connects external systems/capabilities.
5. **Tool (action layer)**  
   Performs concrete operations (file edit, command run, API call). Tool success never equals governance success by itself.

Enforcement principle: **Identity governance > Skill procedure > MCP/Tool execution**.

## Current release posture (v1.5.1 formal baseline)

- **Code-plane**: local-runtime boundary + identity-scoped anti-pollution gates are landed and replayed.
- **Release-plane**: **Full Go (main)** for `v1.5.1` after required cloud gate closure.
- Release evidence anchors:
  - tag: `v1.5.1`
  - main/tag commit: `5d562a0ae1f785102f2d4001583545969ff215c1`
  - workflow: `identity-protocol-ci`
  - run-id: `22708478725`
  - required gate: `required-gates / validate-identity = success`

### Plane blocking policy (must not mix)

1. **Instance-plane = fail-operational**
   - local identity runtime must keep recoverable progress (`auto-repair` / `deferred` / `next_action`).
   - only hard-stop for true safety boundaries (cross-identity contamination, path boundary, permission boundary).
2. **Release-plane = fail-closed**
   - cloud required-gates and release evidence decide Full Go.
   - release checks must not block day-to-day instance self-drive iteration.

### Unified three-plane status output (standard report template)

Use one command to emit a normalized governance snapshot (instance/repo/release planes):

```bash
source ./scripts/identity_runtime_select.sh project
python3 scripts/report_three_plane_status.py \
  --identity-id base-repo-audit-expert-v3 \
  --with-docs-contract
```

Required top-level output keys (for audit handoff):

- `target_branch`
- `release_head_sha`
- `required_gates_run_id`
- `run_url`
- `workflow_file_sha`
- `required_checks_set`
- `instance_plane_status`
- `repo_plane_status`
- `release_plane_status`
- `overall_release_decision` (`Full Go` only when all three planes are `CLOSED`)

Release-plane cloud closure remains optional for day-to-day self-drive:
- no cloud run evidence -> `release_plane_status=NOT_STARTED`
- provide required-gates evidence -> script evaluates cloud closure conditions and returns `CLOSED/BLOCKED`

For cross-instance operational hygiene, run full scan periodically:

```bash
python3 scripts/full_identity_protocol_scan.py --with-docs-contract
```

This produces an all-identity summary across project/global catalogs and marks findings by severity (`P0`/`P1`/`OK`).

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

- `create_identity_pack.py` defaults to local paths; repo fixture mode requires `--repo-fixture` + confirm token + purpose
- `identity_installer.py` defaults to local paths; repo target mode requires `--allow-repo-target` + confirm token + purpose
- `identity_creator.py` resolves runtime context from local catalog first (local > repo)
- `validate_identity_local_persistence.py` hard-fails invalid runtime placement
- Canonical runtime pack root is `${IDENTITY_HOME}` (skills-style root convention)
  (legacy `${IDENTITY_HOME}/identity`, `${IDENTITY_HOME}/identities`, and `${IDENTITY_HOME}/instances` are auto-compatible)

Governance record:
- `docs/governance/local-instance-persistence-boundary-v1.4.6.md`

### IDENTITY_HOME resolution order (canonical, v1.6)

All creator/installer/runtime context resolution follows canonical two-layer path governance:

1. If environment variable `IDENTITY_HOME` is set, use it.
2. Otherwise, if shared config file exists, use it:
   - `${CODEX_HOME:-~/.codex}/.identity/config/runtime-paths.env`
   - key: `IDENTITY_HOME=...`
3. Otherwise, if `CODEX_HOME` is set, use `${CODEX_HOME}/.identity`.
4. Otherwise default to `~/.codex/.identity`.

Fail-close rule:

- no implicit runtime fallback to `./.codex/.identity` or `/tmp`.
- non-canonical runtime roots are migration-only signals and must not drive strict runtime decisions.

This behavior is implemented in `scripts/resolve_identity_context.py::default_identity_home()`
and consumed by `create_identity_pack.py`, `identity_installer.py`, `identity_creator.py`,
and migration tooling.

### Identity scope resolution (governance uplift)

Identity strict execution now carries exactly two runtime source layers:

1. `project` => `<project>/.identity`
2. `global` => `${CODEX_HOME:-~/.codex}/.identity`

Legacy labels (`local/repo/env/auto`) are compatibility metadata only and must not be used as strict
release/readiness/update gating semantics.

If one `identity_id` resolves to multiple pack paths across layers, tooling fails by default until explicit arbitration (`--scope`) is provided. This prevents silent cross-scope contamination.

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
  --identity-home "${IDENTITY_HOME:-${CODEX_HOME:-$HOME/.codex}/.identity}" \
  --protocol-home "${IDENTITY_PROTOCOL_HOME:-$(pwd)}"
```

This writes:
- `${CODEX_HOME:-$HOME/.codex}/.identity/config/runtime-paths.env`
  - `IDENTITY_HOME=...`
  - `IDENTITY_PROTOCOL_HOME=...`

`IDENTITY_PROTOCOL_HOME` resolution order:
1. environment variable `IDENTITY_PROTOCOL_HOME`
2. shared config file key `IDENTITY_PROTOCOL_HOME`
3. current working directory

Implementation note:
- `scripts/configure_identity_runtime_paths.py` defaults are now machine-portable:
  - `IDENTITY_HOME` default derives from `${CODEX_HOME:-~/.codex}/.identity`
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
- Session pointer compatibility path: `<catalog_dir>/session/active_identity.json`
- Session pointer mirror path (default): `<catalog_dir>/session/mirror/current.json`
  (legacy `/tmp/identity-session/current.json` is compatibility-only and opt-in).
- Strategy selected in v1.4.x hardening: **dual-write + strong consistency**.
  - catalog drives activation/scheduling decisions.
  - `META.status` is a required mirrored field for audit/readability.
  - activation transaction must sync canonical session pointer and rollback on
    canonical sync failure.
  - activation transaction must keep catalog + META synchronized.
  - compatibility pointers are non-authoritative mirrors; governed reply/headstamp
    authority must come from explicit actor/session binding (or explicit legacy mode),
    not from silent pointer fallback.
- Validator: `scripts/validate_identity_state_consistency.py`
  + `scripts/validate_identity_session_pointer_consistency.py`

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

# NOTE (v1.4.12+ hardening):
# release-bound scripts no longer allow implicit catalog fallback.
# You must pass --catalog or export IDENTITY_CATALOG from selected runtime mode.
#
# Runtime mode drift guard (v1.4.13+):
# Fail fast if resolved catalog/pack does not match selected mode.
python3 scripts/validate_identity_runtime_mode_guard.py --identity-id store-manager --catalog "${IDENTITY_CATALOG}"

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
# optional: make capability policy explicit (default=strict-union)
python scripts/release_readiness_check.py --identity-id store-manager --capability-activation-policy strict-union
# optional (instance iteration / route-level degrade): allow at-least-one-route-ready
python scripts/release_readiness_check.py --identity-id store-manager --capability-activation-policy route-any-ready
# optional: scaffold a new local runtime identity
python scripts/create_identity_pack.py --id quality-supervisor --title "Quality Supervisor" --description "Cross-checks listing quality" --register
# optional: explicit fixture creation under repo (demo only; requires double confirmation)
python scripts/create_identity_pack.py --id demo-fixture --title "Demo Fixture" --description "Fixture identity" --repo-fixture --repo-fixture-confirm "I_UNDERSTAND_REPO_FIXTURE_WRITE" --repo-fixture-purpose "demo fixture for protocol validation only" --pack-root identity/packs --catalog identity/catalog/identities.yaml --register
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
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (canonical SSOT; do not use artifacts mirror as normative source)

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

`${IDENTITY_PROTOCOL_HOME:-<identity-protocol-local-repo>}`

Before running release commands, verify working directory and branch:

```bash
cd "${IDENTITY_PROTOCOL_HOME:-<identity-protocol-local-repo>}"
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

- Protocol version: `v1.6.14` (draft)
- Discovery contract: `identity/protocol/IDENTITY_DISCOVERY.md`
- Creator skill: `identity-creator` (create + update validators)
