# Protocol Remediation Audit Ledger (v1.6.16 identity-context-continuity stream)

Status: Active (opening-state contract freeze landed, 2026-03-22; validator/readiness/creator rollout pending)  
Scope: protocol review ledger for continuity checkpoints, migration handoff checkpoints, and startup-consumable re-entry briefing

## 0) Stream objective

Current-state judgment for this stream must remain anchored to:

- `identity/protocol/mappings/control-plane-status.current.yaml`
- `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/stream-scope-matrix.current.yaml`

1. Freeze the canonical continuity artifact family for identity instances.
2. Freeze the default cadence + forced-trigger model used to emit governed continuity artifacts.
3. Freeze the authority boundary that keeps continuity artifacts subordinate to `IDENTITY_PROMPT.md`, `CURRENT_TASK.json`, active governance/review docs, workbook surfaces, and runtime receipts.
4. Freeze the canonical producer / consumer split so startup re-entry can consume continuity safely without reopening launcher, topology, or route/script semantics.
5. Freeze the target runtime continuity families and implementation path without pretending rollout is already complete.

## 1) Opening findings absorbed into this stream

### 1.1 Current local protocol base is strong enough to open this stream

At stream opening time, the current local protocol base was rechecked and found materially stable:

1. `python3 identity-protocol-local/scripts/docs_command_contract_check.py` -> `PASS`
2. `python3 identity-protocol-local/scripts/validate_issue_register_consistency.py --json-only` -> `PASS_REQUIRED`
3. `python3 identity-protocol-local/scripts/validate_native_chat_bootstrap_entry_stream.py --json-only` -> `PASS_REQUIRED`
4. `bash identity-protocol-local/scripts/ci/run_identity_codex_launcher_probes_ci.sh` -> `PASS`
5. `bash identity-protocol-local/scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh` -> `PASS_REQUIRED`

Interpretation:

- `v1.6.13` / `v1.6.14` / `v1.6.15` are stable enough to act as inherited foundations;
- `v1.6.16` therefore opens as a continuity stream, not as a repair stream for those lanes.

### 1.2 Opening red constraint that this stream must respect

The key pre-opening local red finding was:

```bash
python3 identity-protocol-local/scripts/validate_identity_instance_pack_topology.py \
  --identity-id base-repo-closure-orchestrator \
  --current-task .identity/base-repo-closure-orchestrator/CURRENT_TASK.json \
  --json-only
```

Result:

- `instance_pack_topology_status=FAIL_REQUIRED`
- `error_code=IP-IPACK-003`
- `unknown_dir_rows=["unregistered_dir:scripts/launchers"]`

Opening interpretation:

1. the protocol cannot assume arbitrary new subtrees under pack-root `scripts/` are already topology-legal;
2. continuity implementation therefore must not start by creating uncontrolled trees such as `scripts/context-continuity/`;
3. continuity rollout must either stay flat under pack-root `scripts/` first or land explicit topology/path registration alongside implementation.

## 2) Ownership boundary frozen in this stream

### 2.1 Protocol-owned surfaces landed in this opening package

1. `docs/governance/identity-context-continuity-governance-v1.6.16.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md`
3. `docs/governance/identity-context-continuity-preflight-v1.6.16.md`
4. `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
5. `identity/protocol/mappings/stream-scope-matrix.v1.6.yaml`
6. `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
7. `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
8. `identity/protocol/IDENTITY_PROTOCOL.md`
9. `identity/protocol/IDENTITY_RUNTIME.md`

### 2.2 Inherited protocol-owned surfaces consumed by this stream

1. `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md`
2. `docs/governance/identity-codex-launcher-governance-v1.6.14.md`
3. `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
4. `docs/governance/identity-workbook-governance-v1.6.md`
5. `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
6. `identity/protocol/AGENT_HANDOFF_CONTRACT.md`
7. `docs/operations/runtime-preflight-checklist-v1.2.13.md`
8. `docs/references/identity-instance-local-operations-and-feedback-governance-guide-v1.0.md`

### 2.3 Workspace / instance-owned surfaces that this stream governs by contract but does not yet roll out globally

1. pack-local continuity producer scripts under pack-root `scripts/`
2. runtime continuity artifacts under:
   - `runtime/reports/context-continuity/`
   - `runtime/state/context-continuity/`
3. launcher/startup consumption of `reentry_brief` through inherited `v1.6.14` entry ownership
4. route-aware use of continuity-capable instance scripts through inherited `v1.6.15` route ownership

## 3) Four-track review checklist

### 3.1 T1 roundtable / internal topology

1. Keep identity/skill/MCP-tool attribution intact using `identity/protocol/AGENT_HANDOFF_CONTRACT.md`.
2. Keep continuity artifacts inside the same protocol governance family as workbook/governance/review/registry/validator rather than as a private audit side-channel.
3. Confirm that continuity does not become an ambient memory layer outside explicit identity binding.

### 3.2 T2 vendor / OpenAI Codex evidence

1. Confirm that Codex startup guidance is run-scoped and startup-bound.
2. Confirm that Codex config already separates startup instruction surfaces from history/compaction controls.
3. Confirm that Responses API conversation state and truncation behavior do not justify treating raw transcript as authority.
4. Canonical vendor anchors:
   - `https://developers.openai.com/codex/guides/agents-md/#how-codex-discovers-guidance`
   - `https://developers.openai.com/codex/config-reference/#configtoml`
   - `https://developers.openai.com/api/reference/resources/responses/methods/create/`
   - `https://platform.openai.com/docs/guides/prompt-caching`

### 3.3 T3 Context7 / persistence / MCP reference boundary

1. Confirm that durable checkpointing, replay, and fork should be explicit rather than inferred.
2. Confirm that continuity belongs above MCP capability primitives (`tools`, `resources`, `prompts`) rather than inside them.
3. Canonical reference family:
   - Context7 library id `/websites/langchain_oss_python_langgraph`
   - Context7 library id `/modelcontextprotocol/modelcontextprotocol`

### 3.4 T4 protocol / inherited-stream references

1. `v1.6.13` owns pack-root executable topology.
2. `v1.6.14` owns launcher/install/startup/resume/recover entry.
3. `v1.6.15` owns route/script/lower-capability/receipt join.
4. `v1.6.12` owns bootstrap tuple truth.
5. `v1.6.16` owns only continuity checkpoints and re-entry briefing.
6. `docs/governance/identity-context-continuity-preflight-v1.6.16.md` remains the pre-opening record and must not be mistaken for the active stream doc.

## 4) Frozen implementation checklist

1. Canonical continuity roles are:
   - `rolling_checkpoint`
   - `stage_checkpoint`
   - `migration_checkpoint`
   - `reentry_brief`
2. The default cadence policy is the named profile `default_turns_15_30_60`; alternative profiles must be governed named profiles rather than hidden constants.
3. Forced trigger classes remain part of the canonical model:
   - `clear_or_context_reset`
   - `compaction_boundary`
   - `launcher_restart_or_recover`
   - `resume_migration`
   - `major_commit`
   - `major_gate_flip`
   - `lane_switch`
   - `root_cause_turn`
4. Continuity artifacts remain derived continuity assets and must not override authority surfaces.
5. `authority_refs`, `task_focus_summary`, `completed_since_previous`, `open_blockers`, `next_actions`, `receipt_refs`, `supersedes_ref`, and `freshness` are frozen field families for future implementation.
6. The runtime continuity root should stay narrow:
   - one report root
   - one state root
   - role split by payload / naming rather than root proliferation
7. `reentry_brief` is the canonical startup-consumable artifact and must stay compact enough for re-entry instead of becoming long-history replay.
8. Resume thread UUIDs, actor-session tuples, and continuity ids remain distinct identity classes and must not be semantically collapsed.

## 5) Opening-state non-goals frozen for audit

1. This opening does not claim validator/readiness/creator rollout is complete.
2. This opening does not claim any fleet pack is already `v1.6.16` adopted.
3. This opening does not claim raw transcript persistence is the new protocol motherline.
4. This opening does not reopen `v1.6.13` / `v1.6.14` / `v1.6.15` semantics.
5. This opening does not yet solve isolated historical replay of continuity state.

## 6) Follow-on implementation obligations

The next implementation stage should land, in order:

1. protocol-owned continuity validators and probe lane
2. contract/path registration rollout through creator/backfill/update flows
3. launcher/startup re-entry consumption under inherited `v1.6.14` ownership
4. one real pilot identity adoption proving continuity production + re-entry consumption
5. only after that, stricter readiness / required-gate promotion

Candidate target surfaces for the follow-on stage:

- scripts/validate_identity_context_continuity.py
- scripts/validate_identity_reentry_brief.py
- scripts/ci/run_identity_context_continuity_probes_ci.sh
- scripts/create_identity_pack.py
- scripts/repair_contract_backfill.py
- scripts/identity_creator.py

## 7) Audit conclusion for this opening checkpoint

This opening checkpoint is acceptable as a **formal stream opening** because it does three things cleanly:

1. it converts continuity from a loose idea into an explicit protocol-owned boundary;
2. it keeps continuity subordinate to existing authority surfaces instead of letting it become a fake memory authority;
3. it identifies the real implementation constraint up front — topology/path registration discipline — rather than hiding it under later patchwork.

The correct interpretation of this ledger is therefore:

- `v1.6.16` is now a real governed stream;
- it is open at the boundary/contract/design level;
- implementation closure is a follow-on phase, not something this opening falsely claims.
