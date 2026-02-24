# Roundtable Deep Audit: Full Repo Scan + Sandbox/Path Convergence (v1.4.12)

Status: Draft for architect review  
Date: 2026-02-24  
Scope: `v1.4.5 -> v1.4.12` hardening continuity review  
Baseline worktree: branch `docs/v1.4.12-multi-agent-governance`, `HEAD=0934976`

## 1. Audit Objective

This audit closes a recurring operational gap:

1. identity runtime assets drift across roots and get overwritten by repo updates.
2. sandbox/permission constraints block writeback and break learning-loop closure.
3. cross-identity contamination still appears through legacy fallback logic.

The goal is to produce a release-grade decision input for base-repo architects:

1. what is closed;
2. what remains P0/P1;
3. what exact changes should be gated before Full Go.

## 2. Method (Cross-Validation)

This document uses three evidence planes and requires consistency across all:

1. **Code plane**: full repo deep scan (`scripts/`, workflow, readiness/e2e chain, governance docs).
2. **Official web plane**: OpenAI / Anthropic / Gemini / MCP official docs.
3. **Context7 plane**: MCP + multi-agent framework docs used only as corroboration, not primary authority.

Important: this is a governance synthesis based on official/public documentation and repository evidence. It is not a literal transcript of vendor architects.

## 3. Baseline Evidence

### 3.1 Repository evidence (deep scan)

Key files scanned:

1. `scripts/resolve_identity_context.py`
2. `scripts/execute_identity_upgrade.py`
3. `scripts/apply_deferred_identity_writeback.py`
4. `scripts/validate_identity_learning_loop.py`
5. `scripts/validate_identity_runtime_contract.py`
6. `scripts/validate_identity_role_binding.py`
7. `scripts/validate_identity_experience_writeback.py`
8. `.github/workflows/_identity-required-gates.yml`
9. `scripts/release_readiness_check.py`
10. `scripts/e2e_smoke_test.sh`

### 3.2 Official web evidence (primary)

1. OpenAI Codex multi-agent:
   - https://developers.openai.com/codex/multi-agent/
   - https://developers.openai.com/codex/concepts/multi-agents/
2. Anthropic MCP connector:
   - https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector
3. Gemini function calling:
   - https://ai.google.dev/gemini-api/docs/function-calling
4. MCP specification:
   - https://modelcontextprotocol.io/specification/latest

### 3.3 Context7 corroboration

Selected library IDs:

1. `/modelcontextprotocol/specification`
2. `/langchain-ai/langgraph`
3. `/microsoft/autogen`

Use in this document: corroborate capability boundaries, stateful/multi-agent patterns, and human-in-the-loop control points.

## 4. Fact -> Governance Inference Matrix

### 4.1 OpenAI Codex multi-agent

Facts from official docs:

1. multi-agent execution introduces delegated task execution boundaries.
2. approval/sandbox behavior is a first-class runtime concern in delegated execution.

Inference for this repo:

1. identity writeback cannot rely on implicit writable paths.
2. writeback failures must be explicit, auditable, and recoverable, never silent-pass.

### 4.2 Anthropic MCP connector + MCP spec

Facts:

1. MCP defines explicit capabilities (`tools`, `resources`, `prompts`) and discovery/list semantics.
2. integration should use explicit contract surfaces, not hidden assumptions.

Inference:

1. identity runtime and protocol roots must be explicit fields in evidence (`protocol_root`, `protocol_commit_sha`, `catalog_path`).
2. fallback that silently crosses identity scope violates contract-driven governance.

### 4.3 Gemini function-calling

Facts:

1. tool/function interfaces are explicit and schema-driven.
2. orchestration reliability depends on deterministic argument/target resolution.

Inference:

1. required-gates must fail fast on empty identity target set.
2. validators should be identity-scoped first, with no demo/global fallback.

### 4.4 Context7 corroboration (LangGraph/AutoGen/MCP)

Corroborated pattern:

1. stateful multi-agent execution needs durable state keys and scoped thread/runtime context.
2. human-in-the-loop checkpoints are explicit interruption/resume events.

Inference:

1. `DEFERRED_PERMISSION_BLOCKED` + deferred apply tool is directionally correct.
2. release path must forbid permissive deferred bypass in CI/release lanes.

## 5. Findings (Severity-Ordered)

## 5.1 P0-Closed (already implemented in current branch)

1. **Writeback no longer silently drifts under sandbox block**
   - Evidence:
     - `scripts/execute_identity_upgrade.py:248`
     - `scripts/execute_identity_upgrade.py:269`
     - `scripts/execute_identity_upgrade.py:279`
   - Summary:
     - emits `DEFERRED_PERMISSION_BLOCKED`
     - CI forbids permissive `--allow-deferred-writeback`
     - keeps release lane strict by default.

2. **Deferred writeback replay now identity-scoped**
   - Evidence:
     - `scripts/apply_deferred_identity_writeback.py:46`
     - `scripts/apply_deferred_identity_writeback.py:53`
     - `scripts/apply_deferred_identity_writeback.py:67`
   - Summary:
     - requires `--identity-id` and `--catalog`
     - validates target paths are exactly `<pack>/RULEBOOK.jsonl` and `<pack>/TASK_HISTORY.md`.

## 5.2 P0-Open (must close before Full Go)

1. **Learning-loop validator still has hard demo fallback**
   - Evidence:
     - `scripts/validate_identity_learning_loop.py:63`
     - `scripts/validate_identity_learning_loop.py:64`
   - Risk:
     - runtime identity can pass validation using `store-manager` sample.
   - Required fix:
     - remove fallback; identity-scoped sample must exist or fail.

2. **Workflow gate chain does not enforce isolation/state-consistency validators**
   - Evidence:
     - no `validate_identity_instance_isolation.py` hit in `.github/workflows/_identity-required-gates.yml`
     - no `validate_identity_state_consistency.py` hit in `.github/workflows/_identity-required-gates.yml`
   - Risk:
     - local passes may not match cloud enforcement semantics for contamination/state-source conflicts.
   - Required fix:
     - wire both validators into required-gates identity loop.

## 5.3 P1-Open (should close in same cycle if possible)

1. **Legacy repo-path fallback remains in core validators/executors**
   - Evidence:
     - `scripts/validate_identity_runtime_contract.py:100`
     - `scripts/validate_identity_role_binding.py:41`
     - `scripts/validate_identity_experience_writeback.py:36`
     - `scripts/execute_identity_upgrade.py:46`
   - Risk:
     - mixed-root behavior persists under old artifacts; increases drift and ambiguity.
   - Required fix:
     - runtime mode default to strict local path only; legacy path support behind explicit compatibility switch.

2. **`default_local_instances_root()` keeps multiple legacy aliases**
   - Evidence:
     - `scripts/resolve_identity_context.py:71`
     - `scripts/resolve_identity_context.py:74`
     - `scripts/resolve_identity_context.py:76`
   - Risk:
     - implicit alias acceptance weakens “single canonical runtime root” governance.
   - Required fix:
     - keep one canonical runtime root, convert others into migration-only paths.

## 6. Root-Cause Synthesis

The repeated instability is not one bug; it is policy/code drift across layers:

1. Policy says local-instance-first and identity-scoped strictness.
2. Some validators still include legacy/global/demo fallback for compatibility.
3. Cloud gate chain is not yet fully aligned with strict local audit gates.

Therefore, upgrades appear partially successful but still permit contamination paths.

## 7. Remediation Plan (Architect-Ready)

### 7.1 P0 patch set (release blocking)

1. Remove `store-manager` fallback from learning-loop validator.
2. Add `validate_identity_instance_isolation.py` and `validate_identity_state_consistency.py` to required-gates.
3. Add the same two checks to local release-readiness/e2e if missing in active branch.

### 7.2 P1 patch set (same release train recommended)

1. Replace implicit `identity/<id>` fallback with explicit compatibility mode.
2. Make compatibility mode opt-in, with warning + sunset timeline.
3. Keep canonical runtime root as single default; relegate legacy roots to migration tooling only.

### 7.3 P2 hardening (post-release)

1. Add machine-readable policy manifest for path semantics.
2. Add “cross-identity contamination chaos test” fixture.
3. Add weekly drift report comparing local gates vs required-gates list.

## 8. Acceptance Criteria

Full Go requires all conditions below:

1. `validate_identity_learning_loop.py` contains no demo/global fallback.
2. required-gates includes isolation + state-consistency checks.
3. local `release_readiness_check.py` and `e2e_smoke_test.sh` remain semantically aligned with required-gates.
4. any `upgrade_required=true && all_ok=true` run has `writeback_status=WRITTEN` in release lane.
5. no runtime identity validator resolves samples/evidence from another identity.

## 9. Minimum Verification Commands

Run on clean checkout of target branch:

```bash
python3 scripts/validate_identity_protocol.py
python3 scripts/validate_identity_local_persistence.py
python3 scripts/validate_identity_runtime_contract.py --identity-id office-ops-expert
python3 scripts/validate_identity_role_binding.py --identity-id office-ops-expert
python3 scripts/validate_identity_learning_loop.py --identity-id office-ops-expert
python3 scripts/release_readiness_check.py --identity-id office-ops-expert --base HEAD~1 --head HEAD
IDENTITY_IDS=office-ops-expert bash scripts/e2e_smoke_test.sh
```

Workflow verification (cloud):

1. open required-gates run logs;
2. confirm isolation + consistency steps executed for each target identity;
3. confirm no empty-target bypass.

## 10. Release Posture

Current recommendation from this deep audit:

1. **Code-plane**: Conditional Go.
2. **Release-plane**: Conditional Go.

Upgrade to Full Go only after P0-open items in section 5.2 are closed and cloud required-gates evidence is available.

## 11. Non-Conflict Statement

This v1.4.12 deep-audit document is additive and does not conflict with v1.4.5-v1.4.11 hardening goals:

1. it tightens identity-scoped enforcement;
2. it does not roll back local-instance-first architecture;
3. it aligns release gates with the same strictness already expected in local audit paths.

## 12. References

1. OpenAI Codex multi-agent:
   - https://developers.openai.com/codex/multi-agent/
   - https://developers.openai.com/codex/concepts/multi-agents/
2. Anthropic MCP connector:
   - https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector
3. Gemini function calling:
   - https://ai.google.dev/gemini-api/docs/function-calling
4. MCP specification:
   - https://modelcontextprotocol.io/specification/latest
5. Context7 corroboration IDs:
   - `/modelcontextprotocol/specification`
   - `/langchain-ai/langgraph`
   - `/microsoft/autogen`
