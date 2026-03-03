# Protocol Remediation Audit Ledger (v1.6 Pre-Release)

Status: Active
Layer: protocol-only tracking ledger (non-governance)
Purpose: Central place for architect + audit-expert planning, implementation replay, and closure decisions before `v1.6` tag.

## 0) Boundary and usage rules

1. This file is a review ledger, not a governance SSOT.
2. Governance contracts/requirements remain in:
   - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
   - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (historical baseline)
3. Source-document precedence:
   - `L1 topic governance SSOT`: `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
   - `L2 global protocol handoff SSOT`: `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
   - `L3 this remediation ledger`: `docs/review/protocol-remediation-audit-ledger-v1.6.md`
4. If this ledger conflicts with L1/L2, treat this ledger as stale and follow L1/L2.
5. Every remediation item must include:
   - commit sha
   - changed files
   - acceptance commands (rc + key fields)
   - execution context (`sandbox` / `escalated`)
   - residual risks
6. `v1.6` tag remains locked until governance unlock formula is satisfied.

---

## 1) v1.6 kickoff intake (carry-over from v1.5)

Kickoff date: 2026-03-03

Carry-over conclusions:

1. Protocol implementation closure for FIX-051/FIX-054 is retained.
2. Current project-scope runtime replay still shows `P0` blocker `IP-CAP-003` (env/auth preflight).
3. External posture remains `IMPL_READY (BLOCKED_BY_ENV_AUDIT)`; no full-closed/full-green claim allowed.

Carry-over evidence:

1. `/tmp/reaudit_643_fullscan_project_only_live.json`
2. `/tmp/reaudit_643_threeplane_live.json`
3. `docs/review/protocol-remediation-audit-ledger-v1.5.md` section `16.8.48`

---

## 2) Rolling summary (v1.6 stream)

| Fix ID | Date (UTC) | Layer | Scope | Commit | Architect Status | Audit Status |
| --- | --- | --- | --- | --- | --- | --- |
| FIX16-001 | 2026-03-03 | protocol | v1.6 governance+review document bootstrap | UNCOMMITTED | DONE | PENDING_REVIEW |
| FIX16-002 | 2026-03-03 | protocol | release unlock formula automation (`ASB16-RQ-001`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-003 | 2026-03-03 | protocol | capability boundary governance (`ASB16-RQ-002`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-004 | 2026-03-03 | protocol | status promotion evidence pipeline (`ASB16-RQ-003`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-005 | 2026-03-03 | protocol | outlet regression matrix (`ASB16-RQ-004`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-006 | 2026-03-03 | protocol | sidecar invariance regression lock (`ASB16-RQ-005`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-007 | 2026-03-03 | protocol | release-plane cloud evidence contract (`ASB16-RQ-006`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-008 | 2026-03-03 | protocol | cross-cwd absolute-input runbook (`ASB16-RQ-007`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-009 | 2026-03-03 | protocol | docs bridge consistency automation (`ASB16-RQ-008`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |

---

## 3) Fix records

### FIX16-001 - v1.6 governance/review bootstrap

- Date (UTC): 2026-03-03
- Layer declaration: `protocol`
- Execution context: `sandbox`
- Source refs:
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.5.md` section `16.8.48`

#### Change summary

1. Create v1.6 governance SSOT.
2. Create v1.6 review ledger.
3. Register v1.6 canonical entry in governance index.
4. Preserve v1.5 history as evidence-only baseline; no historical rewrite.

#### Acceptance commands (initial baseline)

1. `python3 scripts/docs_command_contract_check.py`
   - expected: `PASS`
2. `python3 scripts/validate_protocol_ssot_source.py`
   - expected: `OK`

#### Residual risks

1. `IP-CAP-003` environment blocker remains open and can keep project replay in `P0`.
2. Release plane still requires cloud gates evidence for closure.

### FIX16-002 - release unlock formula automation (`ASB16-RQ-001`)

- Status: `SPEC_READY`
- Goal: deterministic machine output of `unlock_allowed` and blocker set.

Acceptance target:

1. Same input, same output hash.
2. Includes `D1..D6`, `p0_total`, `p0_done`, `p0_not_done_refs`, `protocol_blockers`, `env_blockers`.

### FIX16-003 - capability boundary governance (`ASB16-RQ-002`)

- Status: `SPEC_READY`
- Goal: isolate env/auth blockers from protocol code closure claims.

Acceptance target:

1. `IP-CAP-*` consistently classified as env/auth in release summary.
2. Full-scan and three-plane classification is aligned with unlock report.

### FIX16-004 - status promotion evidence pipeline (`ASB16-RQ-003`)

- Status: `SPEC_READY`
- Goal: prevent narrative-only promotion to `DONE`.

Acceptance target:

1. Every promotion has commit + replay evidence + reviewer decision.
2. Missing evidence causes fail-closed promotion denial.

### FIX16-005 - outlet regression matrix (`ASB16-RQ-004`)

- Status: `SPEC_READY`
- Goal: guarantee compose/send-time invariance across required lanes.

Acceptance target:

1. creator/readiness/e2e/full-scan/three-plane all pass.
2. root/tmp cross-cwd parity remains stable.

### FIX16-006 - sidecar invariance lock (`ASB16-RQ-005`)

- Status: `SPEC_READY`
- Goal: preserve sidecar passthrough ordering and cwd invariance.

Acceptance target:

1. sidecar root/tmp parity pass.
2. sidecar `track_b.semantic_*` and `track_b.vendor_namespace_*` equivalent to direct validators with identical args.

### FIX16-007 - release-plane cloud evidence contract (`ASB16-RQ-006`)

- Status: `SPEC_READY`
- Goal: convert release-plane from `NOT_STARTED` to auditable closure path.

Acceptance target:

1. required cloud checks id/run-url/workflow-sha evidence present and cross-validated.
2. mismatch fails release-plane closure.

### FIX16-008 - cross-cwd absolute-input runbook (`ASB16-RQ-007`)

- Status: `SPEC_READY`
- Goal: prevent replay ambiguity when caller cwd is not protocol-root.

Acceptance target:

1. runbook examples include protocol-root and non-root variants.
2. absolute `--repo-catalog` guidance is explicit and validated.

### FIX16-009 - docs bridge consistency automation (`ASB16-RQ-008`)

- Status: `SPEC_READY`
- Goal: prevent governance/review status drift.

Acceptance target:

1. consistency checker flags contradictory state pairs.
2. bridge output includes exact anchors updated in both docs.

---

## 4) Reviewer decision log

| Fix ID | Audit Decision | Reviewer | Reviewed At (UTC) | Notes |
| --- | --- | --- | --- | --- |
| FIX16-001 | PENDING_REVIEW | audit-expert(codex) | - | bootstrap created; waiting command-contract replay |
| FIX16-002 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-003 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-004 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-005 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-006 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-007 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-008 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-009 | PENDING_INTAKE | - | - | requires implementation |

---

## 5) Current release posture snapshot (v1.6 kickoff)

1. `v1.6` release status: `NO_GO` (kickoff baseline).
2. Blocking class currently visible in live project replay: `IP-CAP-003` (env/auth preflight).
3. Required external reporting posture:
   - `IMPL_READY (BLOCKED_BY_ENV_AUDIT)`
4. This posture remains until:
   - env/auth blocker closure is replay-proven, and
   - v1.6 unlock formula conditions are satisfied.

---

## 6) References

1. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
2. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
3. `docs/review/protocol-remediation-audit-ledger-v1.5.md`
4. `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
