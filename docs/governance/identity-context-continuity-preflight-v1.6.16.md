# Identity Context Continuity Preflight (v1.6.16)

Status: Preflight research only (not yet opened as an active stream, 2026-03-22)  
Layer: protocol  
Scope: identity-instance context continuity, checkpointing, re-entry briefing, restart/recover migration handoff  
Execution mode: preflight SSOT for deciding whether and how to open a dedicated `v1.6.16` stream

## 0) Purpose and boundary

This document records the mandatory preflight research requested before formally opening any `v1.6.16` stream work.

The target problem is specific:

1. after restart / new window / `clear` / compaction / context explosion, an identity instance needs a governed way to recover task continuity quickly;
2. that recovery must be machine-governed and auditable rather than dependent on chat memory or operator recollection;
3. the solution must fit the already-frozen `v1.6.13` / `v1.6.14` / `v1.6.15` boundaries instead of reopening them.

This preflight does **not** yet claim:

- that `v1.6.16` has been opened in stream registry / scope matrix / allowlist;
- that a validator or creator rollout already exists;
- that raw full-chat replay is the right design;
- that Codex product-native history should be treated as identity protocol authority.

## 1) Current-base review result (deep scan of local protocol foundation)

### 1.1 Runtime truth and repo baseline

Runtime truth for the current speaking identity resolves correctly through the local project-layer catalog:

- `identity_id=base-repo-closure-orchestrator`
- `source_layer=project`
- `catalog_path=/Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml`
- `pack_path=/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-closure-orchestrator`

Protocol repo baseline on 2026-03-22:

- `git -C identity-protocol-local status --short`
- result: one untracked note file only
  - `.IDENTITY.run__switch-back-base-repo-closure-orchestrator-20260319T000000Z.md`
- interpretation: not a code-lane red light, but strictly speaking the repo is not byte-for-byte empty-clean.

### 1.2 Current machine gates and closure lanes

The current protocol base is materially healthier than the earlier unstable phase. Verified commands and results:

1. `python3 identity-protocol-local/scripts/docs_command_contract_check.py`
   - `PASS`
   - `docs checked: 79`
   - `command snippets checked: 860`
2. `python3 identity-protocol-local/scripts/validate_issue_register_consistency.py --json-only`
   - `PASS_REQUIRED`
   - workbook control plane closed
   - `ISSUE-001 .. ISSUE-023` all `CLOSED`
3. `python3 identity-protocol-local/scripts/validate_native_chat_bootstrap_entry_stream.py --json-only`
   - `PASS_REQUIRED`
   - `standard_closure_status=CLOSED`
   - `promotion_status=PROMOTION_REVIEW_ELIGIBLE`
4. `bash identity-protocol-local/scripts/ci/run_identity_codex_launcher_probes_ci.sh`
   - `PASS`
   - `launcher_dry_run_status=PASS_REQUIRED`
5. `bash identity-protocol-local/scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
   - `PASS_REQUIRED`
   - positive and negative probe lanes both behave as expected

Preflight conclusion: the current protocol foundation is good enough to design a new stream without first reopening `v1.6.13` / `v1.6.14` / `v1.6.15` semantics.

### 1.3 Key local red finding relevant to `v1.6.16`

The most important deep-scan finding is not in workbook or launcher gates. It is in the current pack topology contract:

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

This matters because it proves the following design constraint is real, not theoretical:

1. `v1.6.13` froze pack-root `scripts/` as canonical, but current topology contract rows still do **not** automatically tolerate arbitrary subdirectories under `scripts/`.
2. Even the already-landed `scripts/launchers/` subtree can fail-close if topology contract rows are not explicitly updated.
3. Therefore `v1.6.16` cannot casually assume that a new subtree such as `scripts/context-continuity/` is safe.

This is the single most important local constraint for continuity design.

## 2) What already exists in the protocol today

`v1.6.16` is not starting from zero. The protocol already contains partial continuity-related building blocks, but they are spread across different governance families and are not yet assembled into one dedicated continuity lane.

### 2.1 Existing machine-governed foundations

1. `v1.6.13` already freezes the instance-owned executable surface at pack-root `scripts/`.
2. `v1.6.14` already freezes launcher/install/startup ownership and explicitly treats startup as the correct place to bind governed entry behavior.
3. `v1.6.15` already freezes route -> script -> lower-capability -> receipt join and proves instance scripts can be machine-routed rather than operator-guessed.
4. `docs/governance/identity-workbook-governance-v1.6.md` already freezes a cross-stream workbook/governance/review/registry/validator control plane for protocol-wide issue governance.
5. `identity/protocol/AGENT_HANDOFF_CONTRACT.md` already freezes identity vs skill vs MCP/tool role separation and structured handoff payload discipline.
6. `docs/operations/runtime-preflight-checklist-v1.2.13.md` already states the key law in plain language: critical runtime operations must be externalized into executable gates, not left to chat memory.
7. `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md` already freezes that any protocol-governed runtime downsink family must be registry-bound and fail-close, not ad hoc.

### 2.2 Deep-scan synthesis

The current repository already contains these continuity-adjacent concepts:

- handoff;
- migration;
- anti-forget continuity;
- runtime preflight;
- actor-session binding hygiene;
- route/script receipt evidence;
- workbook-based cross-stream governance.

But none of them yet gives a dedicated answer to this narrower problem:

> when an identity instance opens a fresh window or loses effective context, what is the canonical continuity artifact, where does it live, how is it produced, how is it consumed, and how is it prevented from becoming a fake authority source?

That missing answer is exactly why a dedicated `v1.6.16` stream is justified.

## 3) Four-track cross-verification

## 3.1 T1 — internal roundtable / inherited protocol boundary

Cross-check against local protocol governance leads to these conclusions:

1. identity protocol already separates:
   - identity guidance;
   - machine contracts;
   - instance-owned executable surfaces;
   - lower capability layers;
   - runtime evidence / reports.
2. the handoff contract already requires failures to be attributed to one layer before patching.
3. workbook/governance/review/registry/validator together already form an automated governance family; any continuity stream should join that family rather than invent a private audit side-channel.
4. continuity therefore should be modeled as a **new control-plane family**, not as a prose-only note in `IDENTITY_PROMPT.md` and not as a workspace helper hack.

## 3.2 T2 — vendor / OpenAI docs verification

OpenAI official documentation strongly supports a startup-bound continuity model rather than a “late-turn memory reconstruction” model.

### A) Codex startup guidance discovery

From the official Codex AGENTS guidance doc:

- Codex builds its instruction chain when it starts, once per run / launched session.
- discovery is root-down and size-limited.
- project fallback files are part of that startup discovery chain.

Implication:

- continuity artifacts that are meant to help a new session recover state should be **startup-consumable** or at least launcher/resume-consumable;
- they should not be treated as a post-hoc manual patch after the run is already underway.

Official source:
- https://developers.openai.com/codex/guides/agents-md/#how-codex-discovers-guidance

### B) Codex config surface

From the official Codex config reference:

- `model_instructions_file`
- `project_doc_fallback_filenames`
- `history.persistence`
- `history.max_bytes`
- `compact_prompt`
- `model_auto_compact_token_limit`
- `mcp_servers.<id>.required`

These confirm that vendor surfaces already distinguish:

1. startup instructions;
2. history persistence / compaction;
3. MCP startup requirements.

Implication:

- identity continuity must not try to masquerade as Codex-native history authority;
- instead it should integrate with governed startup/resume/recover entry while keeping authority in protocol-controlled assets.

Official source:
- https://developers.openai.com/codex/config-reference/#configtoml

### C) Responses API conversation state

The Responses API reference confirms:

- `conversation` and `previous_response_id` are explicit conversation-state carriers;
- `store` controls output retention;
- when using `previous_response_id`, prior instructions are not automatically carried if you replace them;
- `truncation=auto` may drop items from the beginning of the conversation.

Implication:

- raw chat history is not a stable authority surface;
- continuity must preserve explicit state in a separate governed artifact if it needs deterministic re-entry.

Official source:
- https://developers.openai.com/api/reference/resources/responses/methods/create/

### D) Prompt caching guidance

Prompt caching guidance reinforces a structural pattern that is also useful for continuity artifacts:

- exact shared prefixes are valuable;
- stable content belongs at the beginning;
- dynamic content belongs later.

Implication:

- a re-entry brief should likely be structured as:
  - stable prefix: identity truth / task truth / lane truth / active contracts
  - dynamic tail: latest checkpoint summary / next actions / fresh evidence refs

Official source:
- https://platform.openai.com/docs/guides/prompt-caching

## 3.3 T3 — Context7 verification (LangGraph + MCP)

### A) LangGraph persistence / durable execution pattern

Context7 material for LangGraph persistence shows several mature patterns that map cleanly onto the identity continuity problem:

1. persistence is keyed by `thread_id`;
2. short-term checkpointing and cross-thread store/memory are distinct;
3. checkpoint history can be listed and replayed;
4. replay/fork from checkpoint is explicit, not implicit;
5. durable execution is a first-class concept rather than an accidental side effect.

Implication for `v1.6.16`:

- continuity should distinguish per-thread rolling state from cross-thread migration/handoff state;
- checkpoint ids and replay boundaries should be explicit;
- continuity should not collapse “latest visible answer”, “checkpointed machine state”, and “cross-thread memory” into one blob.

Context7 source family:
- `/websites/langchain_oss_python_langgraph`
- topic: persistence / checkpointing / durable execution

### B) MCP lifecycle / capability negotiation pattern

Context7 material for MCP shows:

1. initialization is a negotiated startup lifecycle;
2. capabilities are declared up front;
3. core server primitives are `tools`, `resources`, and `prompts`;
4. tasks are a cross-cutting durable execution utility rather than a hidden byproduct.

Implication for `v1.6.16`:

- identity continuity belongs **above** MCP, not inside MCP capability semantics;
- but the lifecycle model is useful: continuity should also be explicit about declaration, production, and consumption rather than magically inferred.

Context7 source family:
- `/modelcontextprotocol/modelcontextprotocol`

## 3.4 T4 — local references and historical protocol continuity

Local references add two important constraints:

1. `identity-instance-local-operations-and-feedback-governance-guide-v1.0.md` already says upgrades must preserve local instance continuity by default and emit structured feedback for both instance loop and base loop.
2. `runtime-preflight-checklist-v1.2.13.md` explicitly states that critical operational memory must be externalized into executable gates.

Implication:

- `v1.6.16` should not just generate operator notes;
- it should generate structured continuity artifacts that can serve both:
  - the instance recovery loop;
  - the protocol improvement loop.

## 4) Preflight design conclusions

### 4.1 Core design law

**Checkpoint / continuity artifacts must be treated as derived continuity assets, not as authority sources.**

Authority remains in the already-governed sources:

- `IDENTITY_PROMPT.md`
- `CURRENT_TASK.json`
- stream governance / review docs
- workbook control plane
- runtime receipts / reports / state families already governed by prior streams

Continuity artifacts may summarize and point to authority, but they must not silently override it.

### 4.2 What `v1.6.16` should solve

The stream should solve these concrete problems only:

1. fast re-entry after new window / restart / `clear` / compaction;
2. bounded, machine-readable checkpointing for identity work continuity;
3. migration handoff between sessions or windows;
4. explicit recovery from context overload without depending on raw chat transcript luck.

It should **not** try to solve:

- general-purpose memory for all time;
- business-domain knowledge storage;
- Codex-native history replacement;
- MCP server capability design;
- whole-protocol replay engine semantics.

### 4.3 Recommended continuity artifact family

The most coherent model from preflight research is a four-part family:

1. **rolling checkpoint**
   - short-horizon continuity snapshot;
   - optimized for quick same-task re-entry.
2. **stage checkpoint**
   - deeper checkpoint after a meaningful phase boundary;
   - optimized for resuming after a larger interruption.
3. **migration / handoff checkpoint**
   - emitted before restart, clear, recover, or intentional context reset;
   - optimized for cross-window continuity.
4. **re-entry brief**
   - startup/resume-consumable distilled brief;
   - references the latest valid checkpoint family and active authority surfaces.

### 4.4 Recommended trigger model

Turn count alone is too weak. Event-only triggering is also too loose. The best preflight conclusion is a hybrid model:

- default rolling checkpoint: every 15 turns
- default stage checkpoint: every 30 turns
- default migration / handoff checkpoint: every 60 turns

Plus forced triggers before any of the following:

- `clear` / manual context reset
- compaction / context overflow boundary
- launcher-driven restart / recover / resume migration
- major commit or major gate pass/fail
- lane switch or stream-opening transition
- root-cause discovery that materially changes the task plan

This preserves cadence while still aligning with actual operational transitions.

### 4.5 What the continuity artifact should contain

Preflight research supports keeping the artifact compact and layered rather than dumping raw transcript.

A continuity artifact should likely preserve at least:

- identity truth
  - `identity_id`
  - `source_layer`
  - `work_layer`
  - active pack / catalog refs
- task truth
  - current objective
  - active lane / stream focus
  - next required actions
- authority refs
  - current `CURRENT_TASK.json`
  - active governance / review / workbook refs
  - current critical receipt refs
- bounded recent execution summary
  - what was actually completed
  - what remains blocked
  - what changed since previous checkpoint
- recovery hints
  - safe next command(s)
  - whether resume is allowed
  - whether a fresh run is required
  - whether manual operator action is required

The artifact should **not** default to storing raw full transcript as the primary continuity object.

## 5) Topology and path-governance consequences

This preflight cannot recommend continuity implementation without restating the topology constraint:

1. current `v1.6.13` topology validation already fails on `scripts/launchers` because the subtree is not registered in pack topology rows;
2. `v1.6.8` path immutability requires new protocol-governed runtime write families to be registry-bound;
3. therefore `v1.6.16` must not start by inventing uncontrolled directories.

### 5.1 Immediate implication

Do **not** assume `scripts/context-continuity/` is currently legal.

### 5.2 Safe opening options

The next stream should choose one of these two infrastructure-safe paths:

1. **flat-script-first opening**
   - keep instance-owned continuity producers as flat files directly under pack-root `scripts/`;
   - add runtime receipt/report families for continuity artifacts through governed registries.
2. **topology-extension-first opening**
   - explicitly revise pack topology contract rows to admit a governed continuity subtree under `scripts/`;
   - only then allow subdirectory-based continuity helpers.

Preflight recommendation: start with **flat-script-first** unless there is a strong reason to widen topology immediately.

## 6) How `v1.6.16` should relate to existing streams

The clean ownership split should be:

- `v1.6.13`
  - where instance-owned executable sources may live
- `v1.6.14`
  - how Codex is installed / started / resumed / recovered through the governed launcher
- `v1.6.15`
  - how routes select instance scripts and how those scripts join lower capability surfaces and receipts
- `v1.6.16`
  - how continuity checkpoints and re-entry briefs are produced, stored, selected, and consumed across session boundaries

This keeps `v1.6.16` from reopening launcher semantics or topology semantics while still making them usable for real recovery.

## 7) Recommended opening package for the next step

After this preflight, the next formal opening step should be a dedicated stream package, not ad hoc implementation.

Recommended opening bundle:

1. governance doc
   - `docs/governance/identity-context-continuity-governance-v1.6.16.md`
2. paired review ledger
   - `docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md`
3. discovery / registry entries
   - stream doc registry
   - stream scope matrix
   - evidence allowlist
4. machine contracts and validators
   - continuity artifact schema/validator
   - continuity probe lane
   - readiness / required-gate integration
5. creator / backfill / launcher rollout hooks
   - only after the continuity contract is frozen

## 8) Final preflight decision

The deep-scan and cross-verification result is:

1. a dedicated `v1.6.16` stream is justified;
2. it should be framed as **identity context continuity / checkpoint / re-entry / migration handoff**;
3. it should **not** be framed as raw transcript persistence or Codex history replacement;
4. the current protocol base is strong enough to support this opening;
5. the main local design blocker is not semantics but topology/path discipline:
   - current pack topology does not automatically permit new `scripts/*` subtrees,
   - and any new runtime artifact family must be registry-bound.

So the correct next move is:

- formally open `v1.6.16` as a continuity stream,
- keep checkpoints as derived continuity assets,
- bind them into launcher/resume/recover entry,
- and avoid uncontrolled new directory expansion.

## 9) Source set used in this preflight

### Local protocol sources

- `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md`
- `docs/governance/identity-codex-launcher-governance-v1.6.14.md`
- `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
- `docs/governance/identity-workbook-governance-v1.6.md`
- `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
- `identity/protocol/AGENT_HANDOFF_CONTRACT.md`
- `docs/operations/runtime-preflight-checklist-v1.2.13.md`
- `docs/references/identity-instance-local-operations-and-feedback-governance-guide-v1.0.md`

### Official / external references

- OpenAI Codex AGENTS guidance:
  - https://developers.openai.com/codex/guides/agents-md/#how-codex-discovers-guidance
- OpenAI Codex config reference:
  - https://developers.openai.com/codex/config-reference/#configtoml
- OpenAI Responses API create reference:
  - https://developers.openai.com/api/reference/resources/responses/methods/create/
- OpenAI prompt caching guide:
  - https://platform.openai.com/docs/guides/prompt-caching
- Context7 / LangGraph persistence family:
  - `/websites/langchain_oss_python_langgraph`
- Context7 / MCP lifecycle + tasks family:
  - `/modelcontextprotocol/modelcontextprotocol`
