# Identity Extension Cross-Validation Reference v1.4.1

## Purpose

Archive the latest architecture discussion and provide a review-ready, implementation-oriented reference for extending identity capability without drifting from protocol baselines.

This document is intended to answer three recurring review questions:

1. Do new contracts conflict with `IDENTITY_PROTOCOL.md` four core capabilities?
2. How should runtime evolve when required skill/MCP/tool capability is missing?
3. How do we prevent extension sprawl (over-extension -> divergence)?

---

## Baseline conclusion (non-conflict statement)

Current control-loop extensions are **implementation contracts**, not capability redefinitions.

- Four core capabilities remain invariant in `identity/protocol/IDENTITY_PROTOCOL.md`:
  1. accurate judgement
  2. reasoning loop
  3. auto-routing
  4. rule learning
- New contracts are execution-level controls:
  - `capability_orchestration_contract`
  - `knowledge_acquisition_contract`
  - `experience_feedback_contract`
  - `ci_enforcement_contract`

Therefore:

- **No semantic conflict** with four-core capability definitions.
- **No governance-layer replacement**.
- **Yes, this is a strict extension** (contract-first hardening + validator enforcement + CI required gates).

---

## Mapping matrix: four-core -> extension contracts

| Four-core capability (protocol) | Extension contract(s) | Why this is an extension (not replacement) |
|---|---|---|
| Accurate judgement | capability_orchestration, knowledge_acquisition | Adds source quality + tool/route preflight checks to improve judgement evidence quality. |
| Reasoning loop | knowledge_acquisition, experience_feedback | Adds evidence grading + replay-triggered learning update to keep attempt traces actionable. |
| Auto-routing | capability_orchestration, ci_enforcement | Converts route policy into deterministic checks and required-gates enforcement. |
| Rule learning | experience_feedback, ci_enforcement | Enforces positive/negative rule accumulation and validator-backed replay promotion. |

---

## Capability-gap lifecycle (when skill/MCP/tool is missing)

When runtime finds no usable capability, apply this deterministic path:

1. **Detect**
   - Mark `capability_gap` and classify scope.
2. **Classify**
   - `skill_gap` / `mcp_gap` / `tool_gap` / `access_gap`.
3. **Route**
   - `skill_gap` -> skill creation/update path (`skill-creator` style).
   - `mcp_gap` -> MCP server integration + auth + health checks.
   - `tool_gap` -> tool surface extension in MCP.
   - `access_gap` -> collaboration-trigger flow (human-required path).
4. **Patch**
   - Apply minimal viable capability patch for the active objective first.
5. **Validate**
   - Structure + dynamic smoke + trigger regression + replay evidence.
6. **Learn**
   - Write positive/negative experience records and update route/rule weighting.

This lifecycle is the practical runtime mirror of:

- `trigger -> patch -> validate -> replay` (identity update lifecycle contract)
- `Observe -> Decide -> Orchestrate -> Validate -> Learn -> Update` (control-loop baseline)

---

## Anti-divergence guardrails (must keep)

To prevent extension sprawl:

1. **No redefinition rule**
   - Extension contracts must not redefine the four core capabilities.
2. **Mapping-required rule**
   - Every new contract must map to at least one four-core capability in review artifacts.
3. **Validator-required rule**
   - No contract is considered active without deterministic validator coverage.
4. **CI-required rule**
   - Required validators must be included in required-gates workflows.
5. **Replay-required rule**
   - No update completion without replay pass on the original failing case.
6. **Cross-protocol review rule**
   - Identity base changes must cite skill and MCP collaboration references before merge.

---

## Review checklist for future extensions

Before merge, verify:

1. Baseline protocol review evidence exists:
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
   - `docs/references/skill-*.md`
2. New contract has:
   - runtime key in `CURRENT_TASK.json`
   - validator script
   - CI required-gates integration
   - self-test or positive/negative example evidence
3. Non-conflict mapping table updated (four-core alignment).
4. Snapshot/governance evidence updated.
5. Local sync preflight and e2e smoke pass.

---

## References

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`
- `docs/specs/identity-control-loop-v1.4.0.md`
- `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
- `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
- `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
