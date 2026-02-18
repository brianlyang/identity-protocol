# Weixinstore Origin Notes (Curated)

This document preserves high-value context from the founding design discussions for `identity-protocol`.

## Why identity protocol exists

The team observed that skill-only orchestration solved execution but not long-horizon stability:
- repeated audit failures reappeared
- context could drift during long operations
- tool power increased faster than governance quality

Identity protocol was introduced as a control plane parallel to skills and MCP.

## Founding principles

1. **Parallel architecture, not nested architecture**
   - Identity must be first-class, at the same layer as skills and MCP.
2. **Dual-track model**
   - Hard guardrails (non-bypass governance)
   - Adaptive growth (learning loop and strategy updates)
3. **Single source of truth at runtime**
   - `CURRENT_TASK.json` is authoritative execution state.
4. **Evidence-first operations**
   - high-impact actions require artifact paths and traceability.
5. **Offline escalation only for true blockers**
   - e.g., qualification/certificate/category permission requiring human action.

## High-value lessons from live operations

### 1) Config path resolution pitfall

A critical outage occurred because project `.codex/config.toml` relative paths were interpreted from `.codex/`, not repository root.

Correct pattern:
- `model_instructions_file = "../identity/runtime/IDENTITY_COMPILED.md"`
- `[[skills.config]].path = "../skills/.../SKILL.md"`

Prevention:
- run `skills/identity-creator/scripts/check_codex_config_paths.py`.

### 2) Strong execution needs strong memory

Reject/review loops require durable memory constraints, not ad-hoc re-submission.
- preserve raw feedback
- extract reason patterns
- map to deterministic fixes
- replay with gate checks

### 3) Keep protocol concise and enforceable

Avoid turning identity into a giant handbook.
- protocol files define contract
- references carry context
- scripts enforce repeatable checks

## Standards alignment commitments

Identity protocol follows and extends:
- Codex skills model (discoverability, progressive disclosure, explicit scope)
- AGENTS instruction-chain precedence
- config layering and security-conscious execution

See also:
- `skills/identity-creator/references/standards-alignment.md`
- `identity/protocol/IDENTITY_PROTOCOL.md`
