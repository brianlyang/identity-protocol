# Audit Snapshot — 2026-02-24 — Identity Path Governance Final Closure (v1.4.12)

Date: 2026-02-24  
Role: Audit expert  
Scope: multi-round closure summary for architect execution  
Posture: `Code-plane = Go candidate`, `Release-plane = Conditional Go`

---

## 0) Executive conclusion

The core confusion reported by operators is valid and reproducible:

1. Identity runtime path selection was historically implicit.
2. Under sandbox constraints, global runtime often requires escalation.
3. Operators expected skills-like ergonomics ("choose project/global first, then run"), but identity flow was not consistently presented that way.

v1.4.12 governance now aligns to the correct direction, but release closure still requires strict evidence alignment and cloud gate run-id closure.

---

## 1) What is already closed (audit accepted)

### 1.1 Path governance policy is explicit

Documented policy exists and is coherent:

- `docs/governance/identity-runtime-path-selection-governance-v1.4.12.md`
- Two allowed modes only:
  - Mode P: project-local runtime (`<repo>/.agents/identity`)
  - Mode G: global runtime (`~/.codex/identity`)
- Forbidden: implicit mode execution.

### 1.2 Selector entrypoints exist (skills-style operator flow)

Script entrypoints are present and referenced:

- `scripts/identity_runtime_select.sh`
- `scripts/use_project_identity_runtime.sh`
- `scripts/use_local_identity_env.sh`

This closes the previous operator UX gap where mode selection was not an explicit first action.

### 1.3 Gate coverage is materially strengthened

The current governance chain includes:

- scope resolution/isolation/persistence validators
- writeback + permission-state validators
- workspace cleanliness validator
- protocol/runtime boundary controls

These are wired into local readiness/e2e and intended required-gates workflow chain.

---

## 2) What remains mandatory before `Full Go`

### 2.1 Cloud required-gates evidence closure

Current posture must remain `Conditional Go` until latest cloud run-id evidence is provided for required gates.

Acceptance:

1. required-gates run-id available
2. all required checks green on the target branch/tag
3. run artifacts reference the same policy set documented in this repository

### 2.2 Mode-evidence consistency in all closure checklists

All release-bound command sets must be mode-agnostic and not hardcode one catalog root.

Required standard:

1. use `$IDENTITY_CATALOG` in command examples
2. show selected `IDENTITY_HOME` + `IDENTITY_CATALOG` + `IDENTITY_PROTOCOL_HOME` before execution
3. fail-fast if tuple mismatch is detected

### 2.3 No protocol repository runtime drift

Runtime evidence/log/report output must not silently enter protocol repository runtime paths.

Required standard:

1. repository cleanliness gate must run before release claims
2. fixture/debug bypass (if any) must be explicit and audit-noted
3. runtime evidence accepted for release must come from runtime-scoped roots, not protocol fixture roots

---

## 3) Required architect action list (audit-to-implementation handoff)

All actions below are implementation tasks for base-repo architect.

1. Keep mode-selection-first behavior as a hard requirement in all runbooks and bootstrap docs.
2. Ensure every release checklist references `$IDENTITY_CATALOG` rather than user-specific absolute paths.
3. Keep release gate sequence strict: path-mode -> resolve tuple -> validate/heal -> update -> writeback -> permission-state -> cleanliness -> readiness/e2e.
4. Preserve `DEFERRED_PERMISSION_BLOCKED` as governance-detected but not release-pass.
5. Keep protocol/runtime isolation hard-block active by default; bypass only with explicit flag + audit rationale.
6. Publish cloud required-gates run-id evidence for final release closure.

---

## 4) Practical operator interpretation (for teams)

The practical rule is simple:

1. Select runtime mode first.
2. Verify tuple values.
3. Run closure chain.
4. Treat deferred writeback as incomplete.

This mirrors the skills usage expectation while preserving identity-specific runtime/writeback governance requirements.

---

## 5) Official reference appendix (cross-validation anchors)

These references support the governance interpretation used by this audit:

1. OpenAI Codex Skills (skills packaging and usage model):  
   `https://developers.openai.com/codex/skills/`
2. OpenAI Codex config layering (project/user config behavior):  
   `https://developers.openai.com/codex/config-reference/`
3. OpenAI Codex app server (sandbox/approval related runtime context):  
   `https://developers.openai.com/codex/app-server`

Inference note:

- This repository's identity runtime/writeback governance is stricter than skills packaging itself.
- The parity target is operator ergonomics (explicit mode selection), not feature identity between the two systems.

---

## 6) Release posture statement

Until cloud required-gates evidence is closed, audit posture remains:

- `Code-plane: Go candidate`
- `Release-plane: Conditional Go`

Do not promote to `Full Go` based on local-only evidence.
