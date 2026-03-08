# Identity Headstamp Egress Governance (v1.6.1)

Status: Draft (headstamp/HUD extraction stream from v1.6.0)  
Governance layer: protocol  
Scope: outbound user-visible headstamp and final egress control plane only  
Owner: identity protocol base-repo architect  
Execution mode: topic-level canonical SSOT for headstamp/HUD closure after v1.6.0

## 0) Extraction Directive (Mandatory)

### 0.1 Why v1.6.1 exists

1. Headstamp/HUD issues have recurred across many rounds and are no longer manageable as scattered v1.6.0 patches.
2. A dedicated stream is required to avoid repeated partial fixes and contradictory status interpretations.
3. From this document onward, headstamp/HUD governance is executed in one place only.

### 0.2 SSOT precedence for headstamp/HUD topics

1. L1 (topic SSOT): `docs/governance/identity-headstamp-egress-governance-v1.6.1.md` (this file)
2. L2 (historical baseline): `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
3. L3 (global protocol baseline): `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`

Hard rule:

1. Any new headstamp/HUD normative update must be written in v1.6.1.
2. v1.6.0 headstamp sections are frozen as historical evidence and cannot be used as active execution source.

### 0.3 Extracted legacy anchors (frozen references)

1. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md:502` (`4.21` headstamp pre-send hard gate)
2. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md:1152` (`ASB16-RQ-032 PARTIAL` normalization rule)
3. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md:1193` (Batch-4 headstamp omission/bypass decomposition)
4. `docs/review/protocol-remediation-audit-ledger-v1.6.md:79` (`FIX16-029` headstamp pre-send intake)
5. `docs/review/protocol-remediation-audit-ledger-v1.6.md:89` (`HOTFIX16-P0-002` headstamp continuity gap)
6. `docs/review/protocol-remediation-audit-ledger-v1.6.md:97` (`HOTFIX16-P0-010` HUD tuple hardening)

## 1) Problem Model and Recurrence Taxonomy

### 1.1 Scope definition

Headstamp/HUD issue means any failure in:

1. first-line emission (`Identity-Context` + `Layer-Context`)
2. actor/identity/session tuple consistency
3. send-time/final-egress enforcement
4. parity projection and recurrence observability

### 1.2 Recurrence families (H-series)

1. `H01`: headstamp line missing or malformed
2. `H02`: actor/identity binding mismatch
3. `H03`: first-line exists but not emitted through governed egress
4. `H04`: non-canonical outlet channel accepted
5. `H05`: final emit policy/schema mismatch
6. `H06`: strict lane accepted synthetic evidence
7. `H07`: strict lane accepted missing `--actor-id`
8. `H08`: lock/session tuple mismatch across surfaces
9. `H09`: tuple parity omitted core HUD fields
10. `H10`: three-plane/full-scan projection missing HUD tuple fields
11. `H11`: recurrence validator and send-time validator classify same defect differently
12. `H12`: direct/manual path bypasses governed compose/send-time chain
13. `H13`: workflow/script surface misses mandatory bundle args
14. `H14`: source-layer lexical drift in strict lane
15. `H15`: run binding selected by unstable default (mtime-sensitive fallback)
16. `H16`: sidecar/history noise causes false closure perception
17. `H17`: health checks green while egress contract still non-required

## 2) v1.6.1 Contract (Headstamp/Egress)

### 2.1 Single Egress SSOT

1. User-visible outbound text must pass through `scripts/compose_and_validate_governed_reply.py`.
2. The compose output must be validated by `scripts/validate_send_time_reply_gate.py` before release to user channel.
3. Any path that emits text without this chain is protocol violation (fail-close).

### 2.2 Canonical first-line tuple

Required first two lines:

1. `Identity-Context: actor_id=...; identity_id=...; scope=...; lock=...; source=...`
2. `Layer-Context: work_layer=...; source_layer=...`

Strict tuple invariants:

1. `actor_id`
2. `identity_id`
3. `resolved_work_layer`
4. `resolved_source_layer`
5. `lock_state`
6. `run_id_binding`

### 2.3 Strict lane actor rule

1. strict operations (`validate/readiness/e2e/ci/update/three-plane`) require explicit `--actor-id`.
2. Missing explicit actor in strict lane is immediate fail-close.
3. Fallback actor resolution is compatibility-only and cannot be promotion-grade evidence.

### 2.4 Canonical source-layer rule

1. Strict source-layer set: `{project,global}`.
2. Legacy tokens (`local/repo/env/auto`) are migration metadata only.
3. Any strict receipt using legacy source token is invalid.

## 3) Error Family Convergence

### 3.1 Canonical family (v1.6.1 required)

1. `IP-HDSTAMP-001` -> headstamp missing or malformed
2. `IP-HDSTAMP-002` -> actor/layer binding mismatch
3. `IP-HDSTAMP-003` -> pre-send receipt missing

### 3.2 Compatibility alias mapping (non-final)

1. `IP-ASB-STAMP-SESSION-001/002/003/004/005/006/007` may appear during migration diagnostics.
2. Promotion-grade classification must map to canonical `IP-HDSTAMP-*` family.
3. Mixed families in same surface for same defect are treated as non-converged.

## 4) Mandatory Control-Plane Wiring Matrix

| Control | Script | Mandatory surfaces |
| --- | --- | --- |
| governed compose entry | `scripts/compose_and_validate_governed_reply.py` | creator/readiness/e2e/full-scan/three-plane/ci |
| send-time hard gate | `scripts/validate_send_time_reply_gate.py` | creator/readiness/e2e/full-scan/three-plane/ci |
| first-line validator | `scripts/validate_reply_identity_context_first_line.py` | creator/readiness/e2e/full-scan/three-plane/ci |
| recurrence closure | `scripts/validate_headstamp_recurrence_closure.py` | scan/three-plane/ci |
| tuple parity | `scripts/validate_required_gate_tuple_parity.py` | three-plane/full-scan/ci |
| strict surface drift/arg contract | `scripts/validate_required_gate_surface_drift.py` | ci + local preflight |

## 5) Acceptance Matrix (Promotion-Grade)

### 5.1 Positive

1. governed compose + explicit actor + canonical outlet + live evidence -> `PASS_REQUIRED`

### 5.2 Negative

1. missing/malformed first line -> `FAIL_REQUIRED` + `IP-HDSTAMP-001`
2. actor tuple mismatch -> `FAIL_REQUIRED` + `IP-HDSTAMP-002`
3. missing pre-send receipt -> `FAIL_REQUIRED` + `IP-HDSTAMP-003`
4. non-canonical outlet -> `FAIL_REQUIRED` (`final emit channel contract`)
5. strict lane without actor -> `FAIL_REQUIRED` (`actor explicitness contract`)

### 5.3 Cross-surface parity

1. `validate` vs `three-plane` receipts must agree on core tuple fields.
2. Any mismatch is release blocker.

## 6) Current Open Blockers (as-of 2026-03-08)

1. Single-egress enforcement is not yet guaranteed for every assistant-visible path outside governed compose invocation.
2. Headstamp error-family convergence is incomplete; compatibility `IP-ASB-STAMP-SESSION-*` still appears in runtime evidence.
3. Some status surfaces can still appear green while headstamp closure is not promotion-grade complete.

Status boundary:

1. `SPEC_READY / PENDING_INTAKE` remains valid.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

## 7) Four-Track Cross Verification (Roundtable Model)

1. `T1 governance`: this file + v1.6.0 frozen anchors are consistent.
2. `T2 vendor`: MCP lifecycle supports explicit initialization/negotiation before action; aligns with pre-send hard gate strategy.
3. `T3 reference`: OpenAI Codex Skills emphasizes explicit input/output and trigger validation; aligns with strict egress contract.
4. `T4 replay`: promotion requires positive/negative/parity replay receipts under current head SHA.

Reference links:

1. `https://modelcontextprotocol.io/specification/draft/basic/lifecycle`
2. `https://developers.openai.com/codex/skills/#best-practices`
3. `https://developers.openai.com/codex/agent-approvals-security/#sandbox-and-approvals`
4. `https://agentskills.io/specification`

## 8) Execution Policy (No More Scatter)

1. All headstamp/HUD protocol changes, replay notes, and closure decisions must be appended to v1.6.1 governance + v1.6.1 review ledger.
2. v1.6.0 keeps historical text for traceability but cannot receive new headstamp normative clauses.
3. New discussions about headstamp/HUD opened in other docs are invalid unless linked back to this v1.6.1 stream.
