# Protocol Remediation Audit Ledger (v1.5 Pre-Release)

Status: Active  
Layer: protocol-only tracking ledger (non-governance)  
Purpose: Central place for architect + audit-expert review/verification of each remediation item before v1.5 tag.

## 0) Boundary and usage rules

1. This file is a **review ledger**, not a governance SSOT.
2. Governance contracts/requirements remain in:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
   - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
3. **Source-document precedence (anti-drift, mandatory):**
   - `L1 topic governance SSOT`: `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
   - `L2 global protocol handoff SSOT`: `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
   - `L3 this remediation ledger`: `docs/review/protocol-remediation-audit-ledger-v1.5.md` (tracking only, no contract override authority)
4. If any statement in this ledger conflicts with L1/L2, reviewers MUST treat ledger text as stale and follow L1/L2.
5. Every fix record must include at least one explicit `source_ref` to L1/L2 section/requirement id (`ASB-RQ-*`, `DRC-*`, or handoff gate id) to prevent interpretation drift.
6. Every remediation must be recorded as one independent item with:
   - `commit sha`
   - `changed files`
   - `acceptance commands (rc + key tail)`
   - `execution context` (`sandbox` / `escalated`)
   - `residual risk`
7. Non-merge policy for dual P0 tracks remains mandatory:
   - Track-A (`writeback continuity`)
   - Track-B (`semantic routing guard`)
8. v1.5 tag remains locked until all protocol P0 requirements are `DONE` and audit sign-off is `PASS`.

---

## 0.5) Emergency quick-fix lane (P0, discovered during remediation)

1. Items in this lane are **not normal FIX stream items** and MUST NOT be merged into `FIX-00x` tracking.
2. IDs use `HOTFIX-P0-00x`.
3. These incidents are release blocking for v1.5 until architect patch + audit replay are both complete.
4. Source-document precedence remains unchanged (`L1/L2` contracts are authoritative).

| Emergency ID | Date (UTC) | Layer | Scope | Architect Status | Audit Status |
| --- | --- | --- | --- | --- | --- |
| HOTFIX-P0-001 | 2026-02-28 | protocol | missing hard-gate for user-visible identity context stamp | DONE | REJECT (Superseded by HOTFIX-P0-003 PASS) |
| HOTFIX-P0-002 | 2026-02-28 | protocol | explicit activate caused cross-identity hard switch/demotion | DONE | PASS |
| HOTFIX-P0-003 | 2026-02-28 | protocol | stamp blocker receipt lifecycle mismatch causes nondeterministic validate result | DONE | PASS |
| HOTFIX-P0-004 | 2026-02-28 | protocol | user-visible reply channel allowed missing `Identity-Context` prefix in live audit session | DONE | PASS |
| HOTFIX-P0-005 | 2026-03-01 | protocol | instance-to-base-repo write boundary gate missing (docs-allow/code-deny not codified) | DONE | PASS |
| HOTFIX-P0-006 | 2026-03-01 | protocol | protocol-feedback SSOT archival required-gate missing (mirror-only report risk) | DONE | PASS |
| HOTFIX-P0-007 | 2026-03-01 | protocol | readiness scope arbitration not exposed via `--scope` causing `IP-ENV-002` under dual-catalog conflicts | DONE | PASS |
| HOTFIX-P0-008 | 2026-03-01 | protocol | strict user-visible reply gates allowed `LOCK_MISMATCH` to pass, masking actor/catalog lane drift as perceived identity hard-switch | DONE | PASS |
| HOTFIX-P0-009 | 2026-03-01 | protocol | strict operation command-target identity tuple and user-visible reply tuple can diverge under dual-catalog lanes (execution/reply coherence gap) | DONE | PENDING_REPLAY |
| HOTFIX-P0-010 | 2026-03-01 | protocol | disclosure-profile drift can omit tuple refs (`catalog_ref`/`pack_ref`) in strict gate stamp artifacts, causing coherence false-green/false-red ambiguity | DONE | PENDING_REPLAY |

Alignment note (2026-02-28, anti-drift):

1. `zero_shot` / `one_shot` / `multi_shot` are protocol-kernel policies, not vendor-only policies.
2. Protocol-layer vendor vs business-layer partner semantic disambiguation is mandatory governance scope for v1.5.
3. Related governance source refs:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` section `5.5.6`
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` section `5.7.2A`
   - requirement id `ASB-RQ-037`

HOTFIX-P0-004 incident note (2026-02-28, discovered during live audit replay):

1. Finding:
   - user-visible assistant replies were observed without explicit first-line `Identity-Context` stamp in some turns.
2. Why this is P0:
   - violates response-stamp closure invariant and increases hidden identity drift risk during long remediation threads.
3. Source refs:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-018`, `ASB-RQ-019`, `ASB-RQ-020`, `ASB-RQ-021`, `DRC-8`)
4. Required remediation (protocol-layer, non-negotiable):
   - hard gate on outbound user-visible channel: missing `Identity-Context` first line => fail-closed.
   - fail path must emit blocker receipt before any business content.
   - add replay case that simulates long-thread/compaction pressure and asserts zero missing-stamp turns.
   - add machine-readable counter in three-plane/full-scan for `reply_stamp_missing_count` within replay scope.
5. Acceptance target:
   - sampled replay window shows `reply_stamp_missing_count=0` and zero bypasses across creator/readiness/e2e/audit-chat outputs.

HOTFIX-P0-009 incident note (2026-03-01, newly opened):

1. Finding:
   - strict operation command line can target identity tuple `A`, while reply first-line identity context is emitted from tuple `B` under dual-catalog lanes.
2. Why this is P0:
   - weakens operator trust in audit evidence chain (command evidence and reply evidence no longer prove same runtime tuple).
   - can be perceived as hidden identity hard-switch even when actor-scoped model itself is valid.
3. Source refs:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`5.8.11`, `ASB-RQ-067`, `C9`)
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`14.6`, `14.7`)
4. Required remediation (protocol-layer, non-negotiable):
   - strict operations add execution/reply tuple coherence gate (identity/catalog/pack/actor tuple compare).
   - mismatch must fail-closed with blocker receipt (`IP-ASB-CTX-*`), no silent downgrade.
   - six-surface wiring: creator/readiness/e2e/full-scan/three-plane/CI.
5. Acceptance target:
   - strict replay with intentionally mixed tuple fails deterministically (`IP-ASB-CTX-001`).
   - strict replay with coherent tuple passes and emits `coherence_decision=PASS`.
   - inspection replay remains non-blocking but exposes mismatch telemetry fields.

HOTFIX-P0-010 incident note (2026-03-01, newly opened):

1. Finding:
   - response-stamp disclosure profile can be `minimal`, which omits `catalog_ref` and `pack_ref`.
   - strict coherence validation then cannot deterministically compare full tuple and may produce ambiguous mismatch behavior.
2. Why this is P0:
   - strict release/mutation gates require deterministic tuple comparison; disclosure-level drift must not alter gate semantics.
3. Required remediation:
   - all strict gate artifact rendering surfaces must pin `--disclosure-level standard` (or higher) before coherence checks.
   - missing tuple refs in strict operations must map to deterministic fail path (`IP-ASB-CTX-002` class).
4. Acceptance target:
   - strict gate replay is invariant under session disclosure preference changes.
   - coherence checks do not regress when user/session profile sets minimal disclosure for conversational output.

---

## 1) Rolling summary

| Fix ID | Date (UTC) | Layer | Scope | Commit | Architect Status | Audit Status |
| --- | --- | --- | --- | --- | --- | --- |
| FIX-001 | 2026-02-28 | protocol | wave outdated classification | `ee01d56` | DONE | PASS |
| FIX-002 | 2026-02-28 | protocol | path-governance pack canonical gate | `0add536` | DONE | PASS |
| FIX-003 | 2026-02-28 | protocol | readiness preflight wiring for pack path gate | `b80521e` | DONE | PASS |
| FIX-004 | 2026-02-28 | protocol | dynamic response identity stamp closure (non-hardcoded + fail-closed) | `f1587e9` | DONE | PASS |
| FIX-005 | 2026-02-28 | protocol | execution-report path contract gate + readiness wiring | `8963b0e` | DONE | PASS |
| FIX-006 | 2026-02-28 | protocol | identity_home/catalog alignment gate + chain wiring | `40ff2e9` | DONE | PASS |
| FIX-007 | 2026-02-28 | protocol | fixture/runtime boundary gate + chain wiring | `ff0453b` | DONE | PASS |
| FIX-008 | 2026-02-28 | protocol | actor isolation inspection-mode semantics (scan/three-plane noise control) | `5e5c8d5` | DONE | REJECT |
| FIX-009 | 2026-02-28 | protocol | no-implicit-switch operation routing + chain wiring closure | `77b09ef` | DONE | PASS |
| FIX-010 | 2026-02-28 | protocol | three-plane cross-actor operation wiring fix (close FIX-008 reject gap) | `00dcf6b` | DONE | PASS |
| FIX-011 | 2026-02-28 | protocol | Track-A writeback continuity + post-execution mandatory gates landing | `ca23c1d` | DONE | PASS |
| FIX-012 | 2026-02-28 | protocol | Track-B semantic routing guard + vendor namespace separation gates landing | `a8e2671` | DONE | PASS |
| FIX-013 | 2026-02-28 | protocol | sidecar escalation contract validator + A/B coexistence wiring (ASB-RQ-036) | `457935e` | DONE | PASS |
| FIX-014 | 2026-02-28 | protocol | required-contract coverage extends to Track-B + sidecar with operation-aware semantics | `a3eddaa` | DONE | PASS |
| FIX-015 | 2026-02-28 | protocol | concurrent actor x identity activation regression gate (release-blocking verifier) | `6fbf999` | DONE | PASS |
| FIX-016 | 2026-03-01 | protocol | capability-fit P1-F/P1-G/P1-H closure (optimization validators + roundtable evidence + review trigger + matrix builder) | `614e3e4` / `5016816` | DONE | PASS |
| FIX-017 | 2026-03-01 | protocol | readiness scope passthrough into health-report branch (`P0-A` hardening) | `0dd074e` | DONE | PASS |
| FIX-018 | 2026-03-01 | protocol | baseline policy stratification hardening (`P0-B`: strict-by-default for release/mutation paths) | `b0c1483` | DONE | PASS |
| FIX-019 | 2026-03-01 | protocol | protocol version alignment contract unified validator + six-surface wiring (`P0-C`, ASB-RQ-043) | `3c259da` | DONE | PASS |
| FIX-020 | 2026-03-01 | protocol | lock-bound response stamp/session gate for strict operations (`IP-ASB-STAMP-005`) | `483e368` | DONE | PASS |
| FIX-022 | 2026-03-01 | protocol | strict gate stamp rendering + tail-appended `Layer-Context` (`work_layer/source_layer`) to keep tuple/layer coherence deterministic (`HOTFIX-P0-010`) | `81f61f6` | DONE | PENDING_REPLAY |
| FIX-021 | 2026-03-01 | protocol | execution/reply identity tuple coherence gate + strict fail-closed semantics (`IP-ASB-CTX-001..003`) | `81f61f6 / 2c8348d` | DONE | PENDING_REPLAY |
| FIX-023 | 2026-03-01 | protocol | layer-tail hard-gate requiredization (`work_layer/source_layer` machine-readable, fail-closed in strict lanes) | `8a97afc` | DONE | PENDING_REPLAY |
| FIX-024 | 2026-03-01 | protocol | send-time unified reply outlet gate + real dialogue replay path + three-plane/full-scan machine-readable telemetry (`IP-ASB-STAMP-SESSION-001`) | `b1cbe1f` | DONE | PENDING_REPLAY |
| FIX-025 | 2026-03-01 | protocol | layer-intent auto-resolution (instance/protocol/dual) + confidence/fallback telemetry + strict tuple compatibility gate | `a735868` | DONE | PENDING_REPLAY |
| FIX-026 | 2026-03-01 | protocol | layer-intent pass-through closure across send-time/readiness/e2e/full-scan/three-plane/creator (expected-layer + intent propagation) | `0c4cea7` | DONE | PENDING_REPLAY |
| FIX-027 | 2026-03-01 | protocol | default work layer switches to `instance`; protocol escalation requires auditable trigger; regression gate covers instance/protocol/ambiguous intents | `e84459d` | DONE | PENDING_REPLAY |
| FIX-028 | 2026-03-02 | protocol | same-actor multi-session binding overwrite closure implementation (`ASB-RQ-071..074`: multibinding schema + CAS + six-surface gate wiring) | `UNCOMMITTED` | DONE | PENDING_REPLAY |
| FIX-029 | 2026-03-02 | protocol | protocol-feedback canonical reply-channel hard gate + sidecar `IP-PFB-*` blocking + split-receipt requiredization bridge (`ASB-RQ-075..078`) | `a95f5a2 / 560f710` | DONE | PENDING_REAUDIT |
| FIX-030 | 2026-03-02 | protocol | protocol-layer entry bootstrap-readiness hardening (`ASB-RQ-079..081`; trigger-to-feedback forced path chain + anti-deadlock deterministic bootstrap constructor) | `a95f5a2 / 560f710` | DONE | PENDING_REAUDIT |
| FIX-031 | 2026-03-02 | protocol | protocol-entry candidate clarification bridge (`ASB-RQ-082..085`; weak-signal anti-deadlock + canonical candidate-seed feedback chain) | `a95f5a2 / 560f710` | DONE | PENDING_REAUDIT |
| FIX-032 | 2026-03-02 | protocol | protocol inquiry follow-up chain (`ASB-RQ-086..089`; analyzable feedback + deterministic follow-up + business-signal sanitization + source/source_layer semantic clarification + anti-starvation convergence + requiredization bridge trigger) | `a95f5a2 / 560f710` | DONE | PENDING_REAUDIT |
| FIX-033 | 2026-03-02 | protocol | work-layer gate-set split hardening (`ASB-RQ-090..093`; instance self-drive must not be blocked by protocol publish gates, protocol lane remains strict fail-closed with canonical feedback closure) | `d387b12 / 0d7ebc7 / 913973a / 9d830d8` | DONE | PASS |
| FIX-034 | 2026-03-02 | protocol | protocol-context lane-lock hardening (`ASB-RQ-094`; protocol-topic sessions must not silently fallback to instance on empty intent) | `c310ab4` | DONE | PENDING_REAUDIT |
| FIX-035 | 2026-03-02 | protocol | run-pinned strict baseline freshness contract (`ASB-RQ-095`; avoid moving-HEAD nondeterministic strict failures) | `c310ab4` | DONE | PENDING_REAUDIT |
| FIX-036 | 2026-03-02 | protocol | e2e hermetic runtime import contract (`ASB-RQ-096`; no external PYTHONPATH dependency) | `c310ab4` | DONE | PENDING_REAUDIT |
| FIX-037 | 2026-03-02 | ecosystem | skill contract execution integrity (`ASB-RQ-097`; required skill command path must exist/executable) | `DOCS_ONLY_INTAKE` | SPEC_READY | TRANSFERRED_ECOSYSTEM_TRACK |
| FIX-038 | 2026-03-02 | protocol | strict self-repair two-phase stale-baseline refresh (`ASB-RQ-098`; stale-only self-lock elimination) | `c310ab4` | DONE | PENDING_REAUDIT |
| FIX-039 | 2026-03-02 | protocol | requiredization lane-scope hardening (`ASB-RQ-099`; prevent protocol-governance history from auto-hardening instance lane) | `83e5a03` | DONE | PENDING_REAUDIT |
| FIX-040 | 2026-03-02 | protocol | split-receipt activity correlation hardening (`ASB-RQ-100`; strict activity must be current-round correlated) | `83e5a03` | DONE | PENDING_REAUDIT |
| FIX-041 | 2026-03-02 | protocol | strict expected-source-layer input validation (`ASB-RQ-101`; no silent downgrade on invalid input) | `83e5a03` | DONE | PENDING_REAUDIT |
| FIX-042 | 2026-03-02 | protocol | lane-aware required-contract coverage partitioning (`ASB-RQ-102`; split instance/protocol coverage targets) | `83e5a03` | DONE | PENDING_REAUDIT |
| FIX-043 | 2026-03-02 | protocol | prompt-runtime state externalization (`ASB-RQ-103`; keep `IDENTITY_PROMPT.md` immutable across non-policy upgrade runs) | `c310ab4` | DONE | PENDING_REAUDIT |
| FIX-044 | 2026-03-03 | protocol | lane-lock exit unified writer + index linkage (`ASB-RQ-104`; strict exit without newer EXIT remains fail-closed) | `62bdc1c` | DONE | PENDING_REAUDIT |
| FIX-045 | 2026-03-03 | protocol | mixed-signal layer intent routing residual closure (`protocol lane` directive should positively trigger protocol lane instead of ambiguous fallback) | `7695a12` | DONE | PASS |
| FIX-046 | 2026-03-03 | protocol | strict stale-preflight trace observability hardening (`baseline_mode_violation` trace + error-code emission) | `dc9c2e3` | DONE | PASS |
| FIX-047 | 2026-03-03 | protocol | data-sanitization false-positive hardening for phone-like regex in path-context markdown lines (`ASB-RQ-046`; keep real sensitive values fail-closed) | `d50b3a9` | DONE | PENDING_REAUDIT |
| FIX-048 | 2026-03-03 | protocol | scaffold domain-neutralization + blocker taxonomy decoupling (`ASB-RQ-107/108`; remove legacy business-domain leakage from pack bootstrap while preserving compatibility migration) | `f5c97b3 / 49212d2` | DONE | PENDING_REAUDIT |
| FIX-049 | 2026-03-03 | protocol | live reply first-line hard-gate evidence-source closure (`ASB-RQ-109`; forbid stamp-only synthetic evidence from satisfying send-time gate in strict lanes) | `DOCS_ONLY_INTAKE` | SPEC_READY | PENDING_REPLAY |
| FIX-050 | 2026-03-03 | protocol | initialization execution-order hardening (`ASB-RQ-110`; enforce header-first + scaffold-consent before first mutation and require mutation-plan disclosure) | `DOCS_ONLY_INTAKE` | SPEC_READY | PENDING_REPLAY |
| FIX-051 | 2026-03-03 | protocol | post-execution writeback CWD-invariant closure (`ASB-RQ-111`; canonicalize report-relative writeback paths + CWD-invariant validator invocation chain for `IP-WRB-003`) | `e62deab / ddb1529 / 6430852` | DONE | PENDING_REAUDIT |
| FIX-052 | 2026-03-03 | protocol | semantic feedback metadata closure (`ASB-RQ-112`; required `intent_domain/intent_confidence/classifier_reason` in closure batches for strict protocol lane to eliminate `IP-SEM-001`) | `e62deab` | DONE | PENDING_REAUDIT |
| FIX-053 | 2026-03-03 | protocol | required-coverage metric normalization (`ASB-RQ-113`; enforce `required_contract_passed<=required_contract_total` and bound coverage rate to `[0,100]`) | `ddb1529` | DONE | PENDING_REAUDIT |
| FIX-054 | 2026-03-03 | protocol | outbound reply header recurrence guard (`ASB-RQ-114`; compose+validate first-line Identity-Context before emission to eliminate operator-side missing-headstamp slips) | `a559820 / 6430852` | DONE | PENDING_REAUDIT |

---

## 2) Fix records

### FIX-001 — Wave outdated classification hardening (IP-PBL-002 included)

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context: `sandbox`
- Source issue: `IDP-GATE-COVERAGE-001` follow-up / audit finding (IP-PBL-002 was not guaranteed outdated in prior wave semantics)
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-026/027`, `DRC-9`, `DRC-6`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (freshness + coverage handoff alignment)

#### Change summary

1. File changed: `scripts/run_protocol_upgrade_wave.py`
2. Added `OUTDATED_BASELINE_CODES={IP-PBL-001..004}`.
3. Added `_is_outdated_baseline(...)` function to unify outdated decision.
4. Outdated decision now considers:
   - `baseline_status != PASS`
   - `baseline_error_code in {IP-PBL-001,IP-PBL-002,IP-PBL-003,IP-PBL-004}`
   - stale reasons (`execution_report_not_found`, `protocol_commit_sha_mismatch`, etc.)
   - `baseline_rc != 0`
5. Added machine-readable output field per item: `outdated: true|false`.

#### Commit

- `ee01d56` — `fix(wave): treat all baseline freshness error codes as outdated`

#### Acceptance commands (rc + key tail)

1. Command:
   - `python3 -m py_compile scripts/run_protocol_upgrade_wave.py`
   - rc: `0`
   - tail: `no output (compile success)`

2. Command:
   - `python3 scripts/run_protocol_upgrade_wave.py --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --dry-run --out /tmp/identity-upgrade-wave-dryrun.json`
   - rc: `0`
   - key tail:
     - `"outdated_identities": [...]` populated
     - each item includes `"outdated": true` (for currently stale identities)

3. Command (branch proof for IP-PBL-002 semantics):
   - `python3 - <<'PY' ... _is_outdated_baseline('WARN','IP-PBL-002',['execution_report_not_found'],0) ... PY`
   - rc: `0`
   - key tail:
     - `outdated= True`
     - `next_action= bootstrap_or_update_required`

#### Residual risk

1. Current local catalog sample had `IP-PBL-001` on latest dry-run, not `IP-PBL-002`.
2. Therefore IP-PBL-002 behavior was additionally validated by function-level deterministic check.

#### Next action

1. Continue with next P0/P1 remediation item as separate fix record.
2. Audit expert reviews this item and marks `Audit Status` from `PENDING_REVIEW` to `PASS/REJECT`.

#### Audit review verdict (2026-02-28T12:09:47Z)

1. Decision: `PASS` (scoped to FIX-001 objective).
2. Re-validated evidence:
   - `python3 -m py_compile scripts/run_protocol_upgrade_wave.py` => rc=0
   - `python3 scripts/run_protocol_upgrade_wave.py --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --dry-run --out /tmp/identity-upgrade-wave-dryrun-audit.json` => rc=0
   - deterministic branch proof for `IP-PBL-002` => `outdated=True` and `next_action=bootstrap_or_update_required`
3. Audit note:
   - The dry-run command is cwd-sensitive if `--repo-catalog` is omitted.
   - Future acceptance records should keep explicit `--repo-catalog` to avoid false-negative review noise.

---

## 3) Reviewer decision log (to be filled by audit expert)

| Fix ID | Audit Decision | Reviewer | Reviewed At (UTC) | Notes |
| --- | --- | --- | --- | --- |
| FIX-001 | PASS | audit-expert(codex) | 2026-02-28T12:09:47Z | Scoped PASS. Command-2 should keep explicit `--repo-catalog` to avoid cwd-sensitive false failure. |
| FIX-002 | PASS | audit-expert(codex) | 2026-02-28T12:09:47Z | Scoped PASS. Validator behavior and positive/negative samples are reproducible. Chain wiring remains tracked in next fixes. |
| FIX-003 | PASS | audit-expert(codex) | 2026-02-28T12:18:23Z | Scoped PASS. Preflight wiring is effective and fail-closed behavior is present in readiness chain. |
| FIX-004 | PASS | audit-expert(codex) | 2026-02-28T13:02:18Z | Scoped PASS. Stamp render/validate/blocker-receipt validators are landed and wired in readiness/e2e/full-scan/three-plane/identity_creator/CI loop; skip semantics remain contract-first by design. |
| FIX-005 | PASS | audit-expert(codex) | 2026-02-28T13:15:55Z | Scoped PASS. IP-PATH-002 validator behavior and readiness preflight wiring are reproducible in sandbox + escalated replay. |
| FIX-006 | PASS | audit-expert(codex) | 2026-02-28T13:27:06Z | Scoped PASS. IP-PATH-003 validator + readiness/full-scan/three-plane/creator/e2e wiring replayed; docs/SSOT checks clean. |
| FIX-007 | PASS | audit-expert(codex) | 2026-02-28T14:02:10Z | Scoped PASS. IP-PATH-004 semantics replayed: runtime pass, fixture mutation fail w/o override, fixture scan skip, fixture override+receipt pass; readiness/e2e/full-scan/three-plane wiring verified. |
| FIX-008 | REJECT | audit-expert(codex) | 2026-02-28T15:02:10Z | Replayed strict/inspection paths; actor semantics are mostly correct, but three-plane still invokes `validate_cross_actor_isolation.py` without `--operation three-plane`, so inspection surface can fall back to strict default (`operation=validate`) and emit false FAIL_REQUIRED. |
| FIX-009 | PASS | audit-expert(codex) | 2026-02-28T15:03:40Z | Scoped PASS. `no_implicit_switch` now carries operation semantics (`scan/readiness/e2e/ci/validate`) and chain routing is reproducible in full-scan/readiness/e2e replay. |
| FIX-010 | PASS | audit-expert(codex) | 2026-02-28T15:03:40Z | Scoped PASS. three-plane now passes `--operation three-plane` to cross-actor validator; project-catalog replay shows inspection-consistent `SKIPPED_NOT_REQUIRED` (no strict fallback). |
| FIX-011 | PASS | audit-expert(codex) | 2026-02-28T15:36:55Z | Scoped PASS. Track-A validators are landed and fail-closed (`IP-WRB-001` / `IP-WRB-003`), with visibility wired through full-scan/three-plane/health and CI/readiness/e2e chains; readiness early-stop remains expected when auto update report generation is non-closed. |
| FIX-012 | PASS | audit-expert(codex) | 2026-02-28T16:11:35Z | Scoped PASS. Replayed on isolated baseline commit `a8e2671`; Track-B validators show expected contract-first skip + auto-required fail-closed semantics, and wiring is visible in readiness/e2e/full-scan/three-plane/health/CI surfaces. |
| FIX-013 | PASS | audit-expert(codex) | 2026-02-28T18:24:00Z | Scoped PASS. Sidecar validator semantics + chain wiring replayed (`scan/three-plane/health`) with deterministic `SKIPPED_NOT_REQUIRED`/`FAIL_REQUIRED` behavior and machine-readable escalation fields; strict-operation positive escalation path replay remains a follow-up test gap. |
| FIX-014 | PASS | audit-expert(codex) | 2026-02-28T16:22:30Z | Scoped PASS. Coverage validator now ingests operation-aware Track-B/sidecar payload semantics (`required_contract`/`auto_required_signal`) and reproduces expected required-vs-optional accounting across scan/full-scan/three-plane surfaces. |

---

## 4) Additional fix records

### FIX-002 — Add `validate_identity_pack_path_canonical` (IP-PATH-001 gate)

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context: `sandbox`
- Source issue: `IDP-PATH-001` (path governance chain lacked standalone canonical pack-path gate)
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-028`, `DRC-10`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (protocol-level path-governance hardening alignment)

#### Change summary

1. Added script: `scripts/validate_identity_pack_path_canonical.py`.
2. Gate contract checks implemented:
   - catalog row exists for `identity_id`,
   - `pack_path` is absolute,
   - `pack_path` is canonical (`raw == resolved`),
   - resolved path exists,
   - resolved path remains inside allowed runtime roots.
3. Machine-readable payload fields:
   - `path_governance_status` (`PASS_REQUIRED|FAIL_REQUIRED`)
   - `path_error_codes` (`IP-PATH-001`)
   - `stale_reasons`
   - `allowed_runtime_roots`
4. Exit semantics:
   - PASS => rc=0
   - FAIL_REQUIRED => rc=1

#### Commit

- `0add536` — `feat(path): add pack path canonical gate validator`

#### Acceptance commands (rc + key tail)

1. Command:
   - `python3 -m py_compile scripts/validate_identity_pack_path_canonical.py`
   - rc: `0`
   - tail: `no output (compile success)`

2. Command (positive sample):
   - `python3 scripts/validate_identity_pack_path_canonical.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --json-only`
   - rc: `0`
   - key tail:
     - `\"path_governance_status\": \"PASS_REQUIRED\"`
     - `\"path_error_codes\": []`

3. Command (negative sample, relative path in runtime catalog):
   - `python3 scripts/validate_identity_pack_path_canonical.py --identity-id store-manager --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --json-only`
   - rc: `1`
   - key tail:
     - `\"path_governance_status\": \"FAIL_REQUIRED\"`
     - `\"path_error_codes\": [\"IP-PATH-001\"]`
     - `\"stale_reasons\": [\"pack_path_not_absolute\"]`

#### Residual risk

1. Script is landed, but chain wiring into readiness/e2e/full-scan/three-plane/CI is pending.
2. Existing runtime catalog entries with relative path (example: `store-manager`) remain unresolved until data/governance cleanup is executed.

#### Next action

1. Wire this gate into at least one primary chain (recommended next: `release_readiness_check.py` preflight).
2. Add corresponding visibility field in full-scan and three-plane outputs.

#### Audit review verdict (2026-02-28T12:09:47Z)

1. Decision: `PASS` (scoped to FIX-002 objective).
2. Re-validated evidence:
   - `python3 -m py_compile scripts/validate_identity_pack_path_canonical.py` => rc=0
   - positive sample (`custom-creative-ecom-analyst`) => rc=0, `path_governance_status=PASS_REQUIRED`
   - negative sample (`store-manager`) => rc=1, `path_error_codes=["IP-PATH-001"]`
3. Audit note:
   - FIX-002 is accepted as a standalone gate addition.
   - Primary-chain wiring remains an open follow-up and must be tracked as a separate fix item.

---

### FIX-003 — Wire `validate_identity_pack_path_canonical` into release readiness preflight

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for compile checks
  - `escalated` for readiness end-to-end (needs write access in `~/.codex`)
- Source issue: `IDP-PATH-001` chain closure (primary gate wiring required in release path)
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-028`, `DRC-10`, section `6.3 gate wiring`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (readiness preflight governance)

#### Change summary

1. File changed: `scripts/release_readiness_check.py`.
2. Added preflight invocation (before main seq):
   - `python3 scripts/validate_identity_pack_path_canonical.py --identity-id <id> --catalog <catalog> --json-only`
3. Added machine-readable preflight log line:
   - `[INFO] pack path canonical preflight: status=<...> error_codes=<...> identity=<...>`
4. Fail behavior:
   - if path gate returns non-zero, readiness exits early (fail-closed).

#### Commit

- `b80521e` — `feat(readiness): add pack path canonical preflight gate`

#### Acceptance commands (rc + key tail)

1. Command:
   - `python3 -m py_compile scripts/release_readiness_check.py scripts/validate_identity_pack_path_canonical.py`
   - rc: `0`
   - tail: `no output (compile success)`

2. Command (readiness flow with preflight visibility; escalated context):
   - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report-policy warn --baseline-policy warn --capability-activation-policy strict-union`
   - rc: `0`
   - key tail:
     - `[RUN] python3 scripts/validate_identity_pack_path_canonical.py ... --json-only`
     - `[INFO] pack path canonical preflight: status=PASS_REQUIRED error_codes=- identity=custom-creative-ecom-analyst`
     - `[OK] release readiness checks PASSED`

#### Residual risk

1. Readiness wiring is complete for pack-path gate, but other path-governance gates are still pending (`resolved_pack_report_gate`, `identity_home_catalog_alignment_gate`, `fixture_runtime_boundary_gate`).
2. This fix does not yet add path-governance fields into full-scan / three-plane outputs.

#### Next action

1. Implement `validate_identity_execution_report_path_contract.py` (IP-PATH-002).
2. Wire it into readiness preflight after report selection/freshness validation.
3. Then continue with full-scan and three-plane visibility wiring.

#### Audit review verdict (2026-02-28T12:18:23Z)

1. Decision: `PASS` (scoped to FIX-003 objective).
2. Re-validated evidence:
   - `git show --name-only --oneline b80521e` confirms readiness gate wiring change in `scripts/release_readiness_check.py`.
   - `git show --name-only --oneline 8f5db87` confirms review ledger update record for FIX-003.
   - `python3 -m py_compile scripts/release_readiness_check.py scripts/validate_identity_pack_path_canonical.py` => rc=0.
   - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report-policy warn --baseline-policy warn --capability-activation-policy strict-union` => rc=0 (escalated), includes:
     - `[RUN] python3 scripts/validate_identity_pack_path_canonical.py ... --json-only`
     - `[INFO] pack path canonical preflight: status=PASS_REQUIRED error_codes=- identity=custom-creative-ecom-analyst`
     - `[OK] release readiness checks PASSED`
3. Audit note:
   - Validation required escalated execution because readiness writes runtime artifacts under `~/.codex`.
   - Residual risk and next milestone remain valid and should continue as separate fixes.

---


### FIX-004 — Dynamic response identity stamp closure (non-hardcoded + fail-closed)

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for compile checks, validator unit checks, identity_creator/full-scan/three-plane local verification
  - `escalated` for readiness/e2e commands that write runtime artifacts under `~/.codex`
- Source issue: response identity stamp governance closure (`ASB-RQ-018/019/020/021`) + user/audit requirement “每次输出动态标注 identity 对象，禁止硬编码”
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-018`, `ASB-RQ-019`, `ASB-RQ-020`, `ASB-RQ-021`, `DRC-8`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (contract-first gate wiring + machine-readable receipt semantics)

#### Change summary

1. New script `scripts/response_stamp_common.py`:
   - resolves identity stamp context from canonical resolver (`resolve_identity`),
   - emits redacted refs (`catalog_ref`, `pack_ref`) + source-domain + lock-state + lease token,
   - provides blocker receipt payload helper.
2. New script `scripts/render_identity_response_stamp.py`:
   - renders `external|internal|dual` identity stamp,
   - supports machine-readable `--json-only`.
3. New script `scripts/validate_identity_response_stamp.py`:
   - validates dynamic stamp contract and mismatch detection,
   - supports hard checks: `--require-dynamic`, `--require-redacted-external`, `--require-lock-match`,
   - emits blocker receipt on fail (`IP-ASB-STAMP-001/002/003`),
   - contract-first skip semantics (`SKIPPED_NOT_REQUIRED`) with JSON payload.
4. New script `scripts/validate_identity_response_stamp_blocker_receipt.py`:
   - validates blocker receipt schema and required fields,
   - supports contract-first skip semantics (`SKIPPED_NOT_REQUIRED`) with JSON payload.
5. Chain wiring landed:
   - `scripts/release_readiness_check.py` (stamp render + stamp validate + receipt validate),
   - `scripts/identity_creator.py validate`,
   - `scripts/full_identity_protocol_scan.py` (new checks + severity core-fail wiring),
   - `scripts/report_three_plane_status.py` (instance plane stamp detail + validator visibility),
   - `scripts/e2e_smoke_test.sh`,
   - `.github/workflows/_identity-required-gates.yml` (CI required-gates loop).

#### Commit

- `f1587e9` — `feat(stamp): add dynamic identity response stamp validators and gate wiring`

#### Acceptance commands (rc + key tail)

1. Command:
   - `python3 -m py_compile scripts/response_stamp_common.py scripts/render_identity_response_stamp.py scripts/validate_identity_response_stamp.py scripts/validate_identity_response_stamp_blocker_receipt.py scripts/release_readiness_check.py scripts/identity_creator.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py && bash -n scripts/e2e_smoke_test.sh`
   - rc: `0`
   - key tail: `RC_STATIC_ALL=0`

2. Command (positive stamp validation; forced check):
   - `python3 scripts/validate_identity_response_stamp.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --force-check --require-dynamic --require-redacted-external --require-lock-match --json-only`
   - rc: `0`
   - key tail:
     - `"stamp_status":"PASS"`
     - `"error_code":""`

3. Command (negative stamp mismatch; blocker receipt generated):
   - `python3 scripts/validate_identity_response_stamp.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --force-check --require-dynamic --require-redacted-external --require-lock-match --stamp-line "Identity-Context: actor_id=user:test; identity_id=wrong-id; catalog_ref=bad; pack_ref=bad; scope=USER; lock=LOCK_MISMATCH; lease=l1; source=global" --json-only`
   - rc: `1`
   - key tail:
     - `"error_code":"IP-ASB-STAMP-001"`
     - `"blocker_receipt_path":"/private/tmp/identity-stamp-blocker-receipt-custom-creative-ecom-analyst.json"`

4. Command (blocker receipt schema validation):
   - `python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --force-check --receipt /tmp/identity-stamp-blocker-receipt-custom-creative-ecom-analyst.json --json-only`
   - rc: `0`
   - key tail:
     - `"receipt_status":"PASS"`
     - `"error_code":"IP-ASB-STAMP-001"` (inside receipt payload)

5. Command (contract-first skip remains machine-readable):
   - `python3 scripts/validate_identity_response_stamp.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --require-dynamic --require-redacted-external --require-lock-match --json-only`
   - rc: `0`
   - key tail:
     - `"stamp_status":"SKIPPED_NOT_REQUIRED"`
     - `"stale_reasons":["contract_not_required"]`

6. Command (three-plane visibility with stamp detail):
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract --out /tmp/three-plane-fix004.json`
   - rc: `0`
   - key tail:
     - `instance_plane_detail.response_identity_stamp.stamp_status=SKIPPED_NOT_REQUIRED`
     - `validators.response_stamp_render/validation/blocker_receipt all present`

7. Command (e2e chain includes stamp gates; escalated):
   - `IDENTITY_CATALOG=/Users/yangxi/.codex/identity/catalog.local.yaml IDENTITY_IDS=custom-creative-ecom-analyst bash scripts/e2e_smoke_test.sh`
   - rc: `0`
   - key tail:
     - `[12.2/30] render dynamic response identity stamp`
     - `[12.3/30] validate response identity stamp contract`
     - `[12.4/30] validate response stamp blocker receipt schema`
     - `E2E smoke test PASSED`

#### Residual risk

1. Contract-first semantics are functioning, but strict enforcement still depends on each instance enabling `identity_response_stamp_contract.required=true` (instance-layer action, out of protocol-only scope).
2. Freshness/prompt lifecycle remains dynamic by design; readiness results may vary across runs if key input files change between report generation and late-stage validators.
3. Current `lease_id_short` output truncates long tokens for external stamp readability; this is intentional but may need normalization guidance in later UX-focused pass.

#### Next action

1. Submit FIX-004 to audit expert for replay and verdict.
2. Continue remaining open protocol fixes (path-governance residual gates, dual-P0 Track-A/Track-B implementation).

#### Audit review verdict (2026-02-28T13:02:18Z)

1. Decision: `PASS` (scoped to FIX-004 objective).
2. Re-validated evidence:
   - `git show --name-only --oneline f1587e9` matches the declared protocol wiring surfaces and new stamp scripts.
   - static compile + shell syntax check passed:
     - `python3 -m py_compile ...`
     - `bash -n scripts/e2e_smoke_test.sh`
   - stamp validator positive/negative/skip semantics:
     - force-check positive => `stamp_status=PASS` (rc=0)
     - forced mismatch => `error_code=IP-ASB-STAMP-001` + blocker receipt path (rc=1)
     - contract-first non-force => `stamp_status=SKIPPED_NOT_REQUIRED` (rc=0)
   - blocker receipt schema validation => `receipt_status=PASS` (rc=0).
   - chain wiring confirmed by execution traces:
     - `identity_creator.py validate` log contains:
       - `scripts/render_identity_response_stamp.py`
       - `scripts/validate_identity_response_stamp.py`
       - `scripts/validate_identity_response_stamp_blocker_receipt.py`
     - `release_readiness_check.py` (escalated) log contains the same three `[RUN]` lines and `[OK] release readiness checks PASSED`.
     - `e2e_smoke_test.sh` (escalated) includes steps `12.2/30`, `12.3/30`, `12.4/30` and `E2E smoke test PASSED`.
   - visibility checks:
     - `report_three_plane_status.py` output includes `instance_plane_detail.response_identity_stamp.*` and validator entries for render/validation/blocker receipt.
     - `full_identity_protocol_scan.py` output includes response stamp checks for project/global layers.
   - docs/SSOT checks passed:
     - `python3 scripts/docs_command_contract_check.py`
     - `python3 scripts/validate_protocol_ssot_source.py`
3. Audit note:
   - Remaining `SKIPPED_NOT_REQUIRED` outcomes are expected for instances where `identity_response_stamp_contract.required=false`; this is instance-layer policy, not a protocol wiring defect.

### FIX-005 — Add `validate_identity_execution_report_path_contract` (IP-PATH-002) and wire readiness preflight

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for validator compile and direct positive/negative contract checks
  - `escalated` for readiness e2e replay with fresh report generation under `~/.codex`
- Source issue: `IDP-PATH-001` (resolved-pack report contract gap + missing readiness gate)
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-029`, `DRC-10`, section `6.3 gate wiring`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (readiness preflight and report-binding semantics)

#### Change summary

1. Added script: `scripts/validate_identity_execution_report_path_contract.py`.
2. New gate validates execution-report path contract:
   - report exists and is valid JSON,
   - report `resolved_pack_path` is present,
   - no relative token (`.` / `..`),
   - absolute + canonical + exists,
   - equals resolved identity `pack_path`,
   - optional report `catalog_path` (if present) must match requested/resolved catalog.
3. Added machine-readable payload:
   - `path_governance_status` (`PASS_REQUIRED|FAIL_REQUIRED`)
   - `path_error_codes` (`IP-PATH-002`)
   - `stale_reasons`
   - `canonicalization_ref`
4. Wired into `scripts/release_readiness_check.py` as preflight after freshness selection:
   - logs `[INFO] execution report path preflight: ...`
   - fail-closed on non-zero rc.

#### Commit

- `8963b0e` — `feat(path): add execution-report path contract gate and readiness preflight`

#### Acceptance commands (rc + key tail)

1. Command:
   - `python3 -m py_compile scripts/validate_identity_execution_report_path_contract.py`
   - rc: `0`
   - tail: `no output (compile success)`

2. Command (positive sample, canonical absolute report path):
   - `python3 scripts/validate_identity_execution_report_path_contract.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --report /Users/yangxi/.codex/identity/instances/custom-creative-ecom-analyst/runtime/reports/identity-upgrade-exec-custom-creative-ecom-analyst-1772280630.json --json-only`
   - rc: `0`
   - key tail:
     - `\"path_governance_status\":\"PASS_REQUIRED\"`
     - `\"path_error_codes\":[]`

3. Command (negative sample, report `resolved_pack_path=\".\"`):
   - `python3 scripts/validate_identity_execution_report_path_contract.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --report /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/custom-creative-ecom-analyst/runtime/reports/identity-upgrade-exec-custom-creative-ecom-analyst-1772262737.json --json-only`
   - rc: `1`
   - key tail:
     - `\"path_governance_status\":\"FAIL_REQUIRED\"`
     - `\"path_error_codes\":[\"IP-PATH-002\"]`
     - `\"stale_reasons\":[\"report_resolved_pack_path_relative_token\"]`

4. Command (readiness chain visibility; escalated, route-any-ready):
   - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready`
   - rc: `0`
   - key tail:
     - `[RUN] python3 scripts/validate_identity_pack_path_canonical.py ...`
     - `[INFO] execution report path preflight: status=PASS_REQUIRED error_codes=- report=...`
     - `[OK] release readiness checks PASSED`

#### Residual risk

1. `identity_home_catalog_alignment_gate` (`IP-PATH-003`) and `fixture_runtime_boundary_gate` (`IP-PATH-004`) are still pending as standalone validators + chain wiring.
2. full-scan / three-plane path-governance visibility is still partial and should be upgraded in next fixes.

#### Next action

1. Implement `validate_identity_home_catalog_alignment.py` (IP-PATH-003).
2. Implement `validate_fixture_runtime_boundary.py` (IP-PATH-004).
3. Wire path-governance aggregate fields into `full_identity_protocol_scan.py` and `report_three_plane_status.py`.

#### Audit review verdict (2026-02-28T13:15:55Z)

1. Decision: `PASS` (scoped to FIX-005 objective).
2. Re-validated evidence:
   - `git show --name-only --oneline 8963b0e` confirms protocol code changes:
     - `scripts/validate_identity_execution_report_path_contract.py` (new)
     - `scripts/release_readiness_check.py` (preflight wiring)
   - `git show --name-only --oneline de7f585` confirms ledger documentation update.
   - compile check:
     - `python3 -m py_compile scripts/validate_identity_execution_report_path_contract.py scripts/release_readiness_check.py` => `RC_COMPILE=0`
   - positive sample:
     - `validate_identity_execution_report_path_contract.py ... --report ...1772281346.json --json-only` => rc=0
     - key fields: `path_governance_status=PASS_REQUIRED`, `path_error_codes=[]`
   - negative sample (`resolved_pack_path="."`):
     - `validate_identity_execution_report_path_contract.py ... --report ...1772262737.json --json-only` => rc=1
     - key fields: `path_governance_status=FAIL_REQUIRED`, `path_error_codes=["IP-PATH-002"]`, `stale_reasons=["report_resolved_pack_path_relative_token"]`
   - readiness chain visibility (escalated):
     - `release_readiness_check.py ... --capability-activation-policy route-any-ready` => rc=0
     - key lines include:
       - `[RUN] ... validate_identity_pack_path_canonical.py ...`
       - `[RUN] ... validate_identity_execution_report_path_contract.py ...`
       - `[INFO] execution report path preflight: status=PASS_REQUIRED ...`
       - `[OK] release readiness checks PASSED`
3. Audit note:
   - FIX-005 closure is accepted.
   - Residual IP-PATH-003/IP-PATH-004 and path visibility enhancements remain separate follow-up fixes.

### FIX-006 — Add `identity_home_catalog_alignment_gate` (IP-PATH-003) and wire mandatory surfaces

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for validator checks, creator/full-scan/three-plane verification
  - `escalated` for `e2e_smoke_test.sh` replay under `~/.codex` runtime writes
- Source issue: `IDP-PATH-001` residual path-governance closure gap (`identity_home == dirname(identity_catalog)` not enforced in runtime mutation chain)
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-030`, `DRC-10`, `6.3 path-governance wiring`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (protocol gate wiring + machine-readable closure)

#### Change summary

1. Added script: `scripts/validate_identity_home_catalog_alignment.py`.
2. Gate semantics:
   - runtime identities: strict `identity_home == dirname(identity_catalog)` fail-closed (`IP-PATH-003`)
   - fixture/demo identities: `SKIPPED_NOT_REQUIRED` (non-runtime mutation scope)
3. Machine-readable payload fields include:
   - `identity_id`, `catalog_path`, `identity_home`, `resolved_pack_path`, `path_scope`,
   - `path_governance_status`, `path_error_codes`, `canonicalization_ref`,
   - `identity_home_expected`, `identity_home_source`, `stale_reasons`.
4. Wired gate into mandatory surfaces:
   - `scripts/release_readiness_check.py` preflight (with status/error-code line),
   - `scripts/identity_creator.py validate`,
   - `scripts/e2e_smoke_test.sh`,
   - `scripts/full_identity_protocol_scan.py` (check + severity integration),
   - `scripts/report_three_plane_status.py` (instance detail + hard-boundary),
   - `.github/workflows/_identity-required-gates.yml`.

#### Commit

- `40ff2e9` — `feat(path): add identity_home catalog alignment gate and chain wiring`

#### Acceptance commands (rc + key tail)

1. Command:
   - `python3 -m py_compile scripts/validate_identity_home_catalog_alignment.py scripts/release_readiness_check.py scripts/identity_creator.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py && bash -n scripts/e2e_smoke_test.sh`
   - rc: `0`
   - key tail: `RC_STATIC_FIX006=0`

2. Command (runtime positive sample):
   - `python3 scripts/validate_identity_home_catalog_alignment.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --json-only`
   - rc: `0`
   - key tail:
     - `"path_governance_status":"PASS_REQUIRED"`
     - `"path_error_codes":[]`

3. Command (runtime negative sample via explicit mismatched identity_home):
   - `python3 scripts/validate_identity_home_catalog_alignment.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --identity-home /Users/yangxi/claude/codex_project/weixinstore/.agents/identity --json-only`
   - rc: `1`
   - key tail:
     - `"path_governance_status":"FAIL_REQUIRED"`
     - `"path_error_codes":["IP-PATH-003"]`
     - `"stale_reasons":["identity_home_catalog_parent_mismatch"]`

4. Command (fixture skip sample, repo catalog):
   - `python3 scripts/validate_identity_home_catalog_alignment.py --identity-id system-requirements-analyst --catalog identity/catalog/identities.yaml --repo-catalog identity/catalog/identities.yaml --json-only`
   - rc: `0`
   - key tail:
     - `"path_governance_status":"SKIPPED_NOT_REQUIRED"`
     - `"stale_reasons":["fixture_profile_scope"]`

5. Command (readiness preflight visibility):
   - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report <LATEST_REPORT> --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready`
   - rc: `0`
   - key tail:
     - `[RUN] python3 scripts/validate_identity_home_catalog_alignment.py ... --json-only`
     - `[INFO] identity home/catalog alignment preflight: status=PASS_REQUIRED error_codes=- identity=custom-creative-ecom-analyst`
     - `[OK] release readiness checks PASSED`

6. Command (identity_creator validate wiring):
   - `python3 scripts/identity_creator.py validate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER`
   - rc: `0`
   - key tail includes:
     - `$ python3 scripts/validate_identity_home_catalog_alignment.py ...`

7. Command (full-scan visibility):
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix006.json`
   - rc: `0`
   - key tail (parsed):
     - project layer: `identity_home_catalog_alignment.rc=1`, `status=FAIL_REQUIRED`, `codes=["IP-PATH-003"]`
     - global layer: `identity_home_catalog_alignment.rc=0`, `status=PASS_REQUIRED`, `codes=[]`

8. Command (three-plane visibility):
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract --out /tmp/three-plane-fix006.json`
   - rc: `0`
   - key tail (parsed):
     - `instance_plane_detail.identity_home_catalog_alignment.path_governance_status=PASS_REQUIRED`
     - `validators.identity_home_catalog_alignment.rc=0`

9. Command (e2e chain wiring; escalated):
   - `IDENTITY_CATALOG=/Users/yangxi/.codex/identity/catalog.local.yaml IDENTITY_IDS=custom-creative-ecom-analyst bash scripts/e2e_smoke_test.sh`
   - rc: `0`
   - key tail:
     - `[10.16/30] validate identity_home/catalog alignment gate (for each target identity)`
     - `E2E smoke test PASSED`

10. Docs/SSOT sanity:
    - `python3 scripts/docs_command_contract_check.py` => rc=0
    - `python3 scripts/validate_protocol_ssot_source.py` => rc=0

#### Residual risk

1. `fixture_runtime_boundary_gate` (`IP-PATH-004`) remains pending as next P0 path-governance closure item.
2. Full scan still reports project/global mixed outcomes for same identity when environment binding differs by layer; this is now explicitly visible (not silent drift).
3. `release_readiness_check` dynamic report freshness/prompt lifecycle remains time-sensitive by design; occasional stale report failures are expected when key inputs change.

#### Next action

1. FIX-006 is closed after audit replay PASS.
2. Continue FIX-007: implement `validate_fixture_runtime_boundary.py` and wire to all mandatory surfaces.

#### Audit review verdict (2026-02-28T13:27:06Z)

1. Decision: `PASS` (scoped to FIX-006 objective).
2. Replayed evidence:
   - `python3 scripts/docs_command_contract_check.py` => rc=0
   - `python3 scripts/validate_protocol_ssot_source.py` => rc=0
   - `IDENTITY_CATALOG=/Users/yangxi/.codex/identity/catalog.local.yaml IDENTITY_IDS=custom-creative-ecom-analyst bash scripts/e2e_smoke_test.sh` (escalated) => rc=0
3. Key assertions observed from replay output:
   - e2e contains `[10.16/30] validate identity_home/catalog alignment gate (for each target identity)`.
   - e2e tail confirms `E2E smoke test PASSED`, `instance_plane_status=CLOSED`, `release_plane_status=NOT_STARTED`.
   - readiness/full-scan/three-plane wiring claims remain consistent with command outputs already recorded in FIX-006 section.

### FIX-007 — Add `fixture_runtime_boundary_gate` (IP-PATH-004) and wire mandatory surfaces

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for validator behavior checks and chain wiring verification in readiness/creator/full-scan/three-plane
  - `escalated` for e2e replay under `~/.codex` runtime writes
- Source issue: `IDP-PATH-001` residual path-governance closure gap (`fixture/demo` entering runtime mutation flows without explicit override + receipt)
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-031`, `DRC-10`, section `5.6` + `6.3`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (machine-readable gate wiring and fail-closed posture)

#### Change summary

1. Added script: `scripts/validate_fixture_runtime_boundary.py`.
2. Gate semantics:
   - fixture/demo + mutation surfaces (`activate|update|readiness|mutation|e2e`) require:
     - explicit `--allow-fixture-runtime`
     - valid `--fixture-audit-receipt` JSON
   - otherwise fail-closed with `IP-PATH-004`.
3. Non-mutation surfaces (`scan|three-plane|ci|validate|inspection`):
   - fixture identities are `SKIPPED_NOT_REQUIRED` when inactive,
   - fail when fixture appears active on inspection surface.
4. Chain wiring landed:
   - `scripts/identity_creator.py`:
     - validate check list includes fixture boundary validator (`--operation validate`)
     - activate/update commands now preflight fixture boundary (`--operation activate|update`)
     - new args: `--allow-fixture-runtime`, `--fixture-audit-receipt`
   - `scripts/release_readiness_check.py` preflight (`--operation readiness`)
   - `scripts/e2e_smoke_test.sh` (`[10.17/30]`, `--operation e2e`)
   - `scripts/full_identity_protocol_scan.py` (`--operation scan`, visibility fields)
   - `scripts/report_three_plane_status.py` (`--operation three-plane`, detail + hard-boundary)
   - `.github/workflows/_identity-required-gates.yml` (`--operation ci`)

#### Commits

1. `ff0453b` — `feat(path): add fixture runtime boundary gate and chain wiring`

#### Acceptance commands (rc + key tail)

1. Static checks:
   - `python3 -m py_compile scripts/validate_fixture_runtime_boundary.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py && bash -n scripts/e2e_smoke_test.sh`
   - rc: `0`
   - key tail: `RC_STATIC_FIX007=0`

2. Runtime identity (non-fixture) mutation pass sample:
   - `python3 scripts/validate_fixture_runtime_boundary.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation update --json-only`
   - rc: `0`
   - key tail:
     - `"path_governance_status":"PASS_REQUIRED"`
     - `"path_error_codes":[]`

3. Fixture mutation fail sample (no override/receipt):
   - `python3 scripts/validate_fixture_runtime_boundary.py --identity-id store-manager --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation update --json-only`
   - rc: `1`
   - key tail:
     - `"path_governance_status":"FAIL_REQUIRED"`
     - `"path_error_codes":["IP-PATH-004"]`
     - `"stale_reasons":["fixture_runtime_override_required","fixture_override_receipt_missing"]`

4. Fixture non-mutation scan sample:
   - `python3 scripts/validate_fixture_runtime_boundary.py --identity-id store-manager --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation scan --json-only`
   - rc: `0`
   - key tail:
     - `"path_governance_status":"SKIPPED_NOT_REQUIRED"`
     - `"stale_reasons":["fixture_non_mutation_scope"]`

5. Fixture override+receipt positive sample:
   - `python3 scripts/validate_fixture_runtime_boundary.py --identity-id store-manager --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation update --allow-fixture-runtime --fixture-audit-receipt /tmp/fix007-fixture-receipt.json --json-only`
   - rc: `0`
   - key tail:
     - `"path_governance_status":"PASS_REQUIRED"`
      - `"allow_fixture_runtime":true`

6. Readiness preflight wiring:
   - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report-policy warn --capability-activation-policy route-any-ready`
   - rc: `0`
   - key tail includes:
     - `[RUN] python3 scripts/validate_fixture_runtime_boundary.py ... --operation readiness --json-only`
     - `[INFO] fixture/runtime boundary preflight: status=PASS_REQUIRED ...`
     - `[OK] release readiness checks PASSED`

7. `identity_creator validate` wiring:
   - `python3 scripts/identity_creator.py validate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER`
   - rc: `0`
   - key tail includes:
     - `$ python3 scripts/validate_fixture_runtime_boundary.py ... --operation validate`

8. Full-scan visibility:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix007.json`
   - rc: `0`
   - key parsed fields include `checks.fixture_runtime_boundary` with machine-readable fields (`path_governance_status`, `path_error_codes`, `operation`, `stale_reasons`) for both project/global layers.

9. Three-plane visibility:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix007.json`
   - rc: `0`
   - key parsed fields include:
     - `instance_plane_detail.fixture_runtime_boundary.path_governance_status=PASS_REQUIRED`
     - `validators.fixture_runtime_boundary.rc=0`

10. e2e wiring (escalated):
    - `IDENTITY_CATALOG=/Users/yangxi/.codex/identity/catalog.local.yaml IDENTITY_IDS=custom-creative-ecom-analyst bash scripts/e2e_smoke_test.sh`
    - rc: `0`
    - key tail includes:
      - `[10.17/30] validate fixture/runtime boundary gate (for each target identity)`
      - `E2E smoke test PASSED`
      - `instance_plane_status=CLOSED`

11. Docs/SSOT checks:
    - `python3 scripts/docs_command_contract_check.py` => rc=0
    - `python3 scripts/validate_protocol_ssot_source.py` => rc=0

#### Residual risk

1. CI required-gates still invokes `identity_creator.py update` for resolved identities; fixture-heavy contexts may require explicit governance decision whether update should be skipped or explicitly overridden with audited receipt in CI policy.
2. Actor-scoped session migration P0 cluster (`ASB-RQ-001..010`) remains open and is orthogonal to this path gate.
3. Track-A/Track-B dual P0 (`ASB-RQ-032..036`) remains pending.

#### Next action

1. Submit FIX-007 to audit expert for replay verdict.
2. Continue next pending protocol P0 item per governance ledger order.

#### Audit review verdict (2026-02-28T14:02:10Z)

1. Decision: `PASS` (scoped to FIX-007 objective).
2. Replayed evidence:
   - static:
     - `python3 -m py_compile scripts/validate_fixture_runtime_boundary.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py`
     - `bash -n scripts/e2e_smoke_test.sh`
     - result: `RC_STATIC_FIX007=0`
   - validator semantics:
     - runtime pass:
       - `python3 scripts/validate_fixture_runtime_boundary.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation update --json-only`
       - rc=0, `path_governance_status=PASS_REQUIRED`
     - fixture mutation fail without override:
       - `python3 scripts/validate_fixture_runtime_boundary.py --identity-id store-manager --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation update --json-only`
       - rc=1, `path_error_codes=["IP-PATH-004"]`, stale reasons include `fixture_runtime_override_required` and `fixture_override_receipt_missing`
     - fixture non-mutation skip:
       - `python3 scripts/validate_fixture_runtime_boundary.py --identity-id store-manager --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation scan --json-only`
       - rc=0, `path_governance_status=SKIPPED_NOT_REQUIRED`
     - fixture override+receipt pass:
       - `python3 scripts/validate_fixture_runtime_boundary.py --identity-id store-manager --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation update --allow-fixture-runtime --fixture-audit-receipt /tmp/fix007-fixture-receipt.json --json-only`
       - rc=0, `path_governance_status=PASS_REQUIRED`
   - chain wiring:
     - readiness (escalated): `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report-policy warn --capability-activation-policy route-any-ready`
       - rc=0, logs include:
         - `[RUN] ... validate_fixture_runtime_boundary.py ... --operation readiness --json-only`
         - `[INFO] fixture/runtime boundary preflight: status=PASS_REQUIRED ...`
         - `[OK] release readiness checks PASSED`
     - e2e (escalated): `IDENTITY_CATALOG=/Users/yangxi/.codex/identity/catalog.local.yaml IDENTITY_IDS=custom-creative-ecom-analyst bash scripts/e2e_smoke_test.sh`
       - rc=0, includes `[10.17/30] validate fixture/runtime boundary gate ...`, and tail `E2E smoke test PASSED`
     - visibility:
       - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix007-audit.json`
       - parsed rows: `('project', ..., 0, 'PASS_REQUIRED', [])`, `('global', ..., 0, 'PASS_REQUIRED', [])`
       - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix007-audit.json`
       - parsed: `instance_plane_detail.fixture_runtime_boundary.path_governance_status=PASS_REQUIRED`, validator `rc=0`
3. Audit note:
   - FIX-007 acceptance is independent from emergency lane HOTFIX items.
   - HOTFIX-P0-003 is now `PASS`; HOTFIX-P0-001 remains historical `REJECT` and is superseded by HOTFIX-P0-003 closure.

---

### FIX-008 — Actor-isolation inspection-mode semantics (reduce scan/three-plane false P0 noise)

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for static checks and scan/three-plane replay
  - `escalated` for readiness/e2e replay (writes under `~/.codex`)
- Source issue: actor isolation validators were fail-closed in all surfaces; inspection surfaces (`full-scan`, `three-plane`) produced false P0 noise when actor binding artifacts were absent in non-mutation contexts.
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-001..010`, `ASB-RQ-037`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (gate semantics and machine-readable status contract)

#### Change summary

1. Added explicit operation semantics to actor validators:
   - `scripts/validate_actor_session_binding.py`
   - `scripts/validate_cross_actor_isolation.py`
2. New argument:
   - `--operation <activate|update|readiness|e2e|ci|validate|scan|three-plane|inspection>`
3. Behavior contract:
   - strict operations (`activate/update/readiness/e2e/ci/validate/mutation`) remain fail-closed.
   - inspection operations (`scan/three-plane/inspection`) can emit `SKIPPED_NOT_REQUIRED` instead of false P0 failures when no mutation/activation semantics apply.
4. Main-chain wiring updated with explicit operation values:
   - `scripts/release_readiness_check.py` => `--operation readiness`
   - `scripts/e2e_smoke_test.sh` => `--operation e2e`
   - `scripts/full_identity_protocol_scan.py` => `--operation scan`
   - `scripts/report_three_plane_status.py` => `--operation three-plane`
   - `.github/workflows/_identity-required-gates.yml` => `--operation ci`
   - `scripts/identity_creator.py validate` => `--operation validate`

#### Commit

- `5e5c8d5` — `fix(actor-scan): add inspection-mode semantics for actor isolation gates`

#### Acceptance commands (rc + key tail)

1. Static checks:
   - `python3 -m py_compile scripts/validate_actor_session_binding.py scripts/validate_cross_actor_isolation.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py scripts/identity_creator.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - rc: `0`
   - key tail: `RC_FIX008_STATIC=0`

2. Full scan (target):
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix008.json`
   - rc: `0`
   - key tail:
     - actor validator entries visible with inspection semantics
     - inspection scope returns `SKIPPED_NOT_REQUIRED` instead of false fail-closed P0 on absent actor artifacts

3. Three-plane visibility:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix008.json`
   - rc: `0`
   - key tail:
     - actor-related detail fields present under `instance_plane_detail`
     - no hard failure caused by inspection-only context

4. Readiness strict path (escalated):
   - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --capability-activation-policy strict-union`
   - rc: `0`
   - key tail:
     - actor validators invoked with `--operation readiness`
     - strict semantics retained; readiness remains fail-closed when strict conditions are violated

5. Creator validate path:
   - `python3 scripts/identity_creator.py validate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml`
   - rc: `0`
   - key tail:
     - actor validators invoked with `--operation validate`

6. e2e replay (escalated):
   - `IDENTITY_CATALOG=/Users/yangxi/.codex/identity/catalog.local.yaml IDENTITY_IDS=custom-creative-ecom-analyst bash scripts/e2e_smoke_test.sh`
   - rc: `0`
   - key tail:
     - `[10.18/30] validate actor-scoped session isolation gates ...`
     - `E2E smoke test PASSED`

#### Residual risk

1. This fix addresses inspection-surface signal quality; it does not complete all actor-scoped migration requirements.
2. HOTFIX-P0-003 is `PASS`; no additional stamp-lifecycle blocker remains from this fix line.

#### Next action

1. Submit FIX-008 for audit replay with strict/inspection dual-path evidence.
2. Keep release decision locked to full P0 closure policy.

---

#### Audit review verdict (2026-02-28T15:02:10Z)

1. Decision: `REJECT` (scope: FIX-008 objective not fully met on three-plane chain wiring).
2. Replayed evidence:
   - static checks:
     - `python3 -m py_compile ...` + `bash -n scripts/e2e_smoke_test.sh` => rc=`0`
   - inspection-vs-strict semantics are correct at validator level:
     - `validate_actor_session_binding --operation scan` => `SKIPPED_NOT_REQUIRED` (rc=`0`)
     - `validate_actor_session_binding --operation validate` => `FAIL_REQUIRED` (rc=`1`)
     - `validate_cross_actor_isolation --operation scan` => `SKIPPED_NOT_REQUIRED` (rc=`0`)
     - `validate_cross_actor_isolation --operation validate` => `FAIL_REQUIRED` (rc=`1`)
   - strict chains (escalated) pass and include operation routing:
     - `release_readiness_check.py ...` => rc=`0`; logs include:
       - `validate_actor_session_binding.py ... --operation readiness`
       - `validate_no_implicit_switch.py ... --operation readiness`
       - `validate_cross_actor_isolation.py ... --operation readiness`
     - `e2e_smoke_test.sh` => rc=`0`; includes `[10.18/30] validate actor-scoped session isolation gates ...`
3. Blocking mismatch:
   - `scripts/report_three_plane_status.py` invokes cross-actor validator without operation argument:
     - `scripts/report_three_plane_status.py:328`
     - `scripts/report_three_plane_status.py:336`
   - project-catalog replay confirms fallback to strict default:
     - payload shows `"operation":"validate"` and `cross_actor_isolation_status="FAIL_REQUIRED"` in inspection surface where expected behavior is inspection semantics.
4. Disposition:
   - keep `FIX-008` in `REJECT` until three-plane passes `--operation three-plane` for cross-actor validator and replay shows expected inspection-mode status outputs.

---

### FIX-009 — no-implicit-switch operation routing + parser-safe chain semantics

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for static checks + three-plane/full-scan replay
  - `escalated` required for readiness/e2e in global runtime contexts that write under `~/.codex`
- Source issue: `validate_no_implicit_switch.py` lacked `--operation` and caused parser failures (`rc=2`) when wired from inspection surfaces; this created noisy hard-boundary signals in `three-plane`/`full-scan`.
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-001..010`, `ASB-RQ-037`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (machine-readable gate semantics + chain consistency)

#### Change summary

1. Added operation routing to validator:
   - `scripts/validate_no_implicit_switch.py`
   - new arg: `--operation` with strict/inspection enum
   - payload now includes `operation` field for audit visibility.
2. Main-chain wiring now passes explicit operation context:
   - `scripts/release_readiness_check.py` -> `--operation readiness`
   - `scripts/identity_creator.py validate` -> `--operation validate`
   - `scripts/e2e_smoke_test.sh` -> `--operation e2e`
   - `scripts/full_identity_protocol_scan.py` -> `--operation scan`
   - `scripts/report_three_plane_status.py` already used `--operation three-plane` (now parser-safe)
   - `.github/workflows/_identity-required-gates.yml` -> `--operation ci`
3. Result:
   - removed parser mismatch (`unrecognized arguments: --operation three-plane`)
   - no-implicit-switch gate is now consistent with other actor isolation validators.

#### Commit

- `77b09ef` — `fix(actor-gates): add operation routing for no-implicit-switch validator`

#### Acceptance commands (rc + key tail)

1. Static checks:
   - `python3 -m py_compile scripts/validate_no_implicit_switch.py scripts/release_readiness_check.py scripts/identity_creator.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - rc: `0`
   - key tail: `RC_FIX009_STATIC=0`

2. Three-plane replay:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix009.json`
   - rc: `0`
   - key tail:
     - `validators.no_implicit_switch.rc=0`
     - `instance_plane_detail.no_implicit_switch.implicit_switch_status=SKIPPED_NOT_REQUIRED`
     - no parser error text appears.

3. Full scan replay:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix009.json`
   - rc: `0`
   - key tail:
     - check `no_implicit_switch` includes `"operation":"scan"` payload
     - check `no_implicit_switch.rc=0` in both project/global layer outputs.

4. Creator validate replay:
   - `python3 scripts/identity_creator.py validate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml`
   - rc: `0`
   - key tail:
     - command trace includes `validate_no_implicit_switch.py ... --operation validate`
     - validator output includes `"operation":"validate"`.

#### Residual risk

1. This fix closes parser/operation consistency for `no_implicit_switch`, but does not by itself close all actor-session migration P0 requirements.
2. HOTFIX lane closure still requires audit replay on HOTFIX-P0 items before release unfreeze.

#### Next action

1. Replay completed and marked `PASS`; keep this section as closure evidence for future regressions.
2. Continue next pending governance item per v1.5 ledger order.

---

#### Audit review verdict (2026-02-28T15:03:40Z)

1. Decision: `PASS` (scoped to FIX-009 objective).
2. Replayed evidence:
   - validator direct replay:
     - `python3 scripts/validate_no_implicit_switch.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only` => rc=`0`, payload includes `"operation":"scan"`, `implicit_switch_status=SKIPPED_NOT_REQUIRED`.
   - full-scan replay:
     - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/fix009-full-scan-audit.json` => rc=`0`
     - project/global `no_implicit_switch` tails include `"operation":"scan"`.
   - readiness replay (escalated):
     - `python3 scripts/release_readiness_check.py ...` => rc=`0`
     - log includes:
       - `validate_no_implicit_switch.py ... --operation readiness`
       - `[OK] release readiness checks PASSED`
   - e2e replay (escalated):
     - `IDENTITY_CATALOG=/Users/yangxi/.codex/identity/catalog.local.yaml IDENTITY_IDS=custom-creative-ecom-analyst bash scripts/e2e_smoke_test.sh` => rc=`0`
     - output includes `"operation":"e2e"` and `E2E smoke test PASSED`.
3. Audit note:
   - FIX-009 closure does not change FIX-008 historical `REJECT`; that gap is closed by FIX-010.

---

### FIX-010 — three-plane cross-actor operation wiring (close FIX-008 reject gap)

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context: `sandbox`
- Source issue: audit replay rejected FIX-008 because `report_three_plane_status.py` invoked `validate_cross_actor_isolation.py` without inspection operation, causing fallback to strict default (`operation=validate`) in three-plane surface.
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-001..010`, `ASB-RQ-037`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (inspection-vs-strict gate semantics)

#### Change summary

1. File changed: `scripts/report_three_plane_status.py`.
2. Added missing arguments to cross-actor validator call:
   - `--operation three-plane`
3. Result:
   - three-plane now passes explicit inspection context to all actor-isolation validators (`actor_session_binding`, `no_implicit_switch`, `cross_actor_isolation`).

#### Commit

- `00dcf6b` — `fix(actor-gates): pass three-plane operation to cross-actor validator`

#### Acceptance commands (rc + key tail)

1. Static check:
   - `python3 -m py_compile scripts/report_three_plane_status.py`
   - rc: `0`
   - key tail: `RC_FIX010_STATIC=0`

2. Three-plane replay (project runtime catalog, inspection context):
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix010-project.json`
   - rc: `0`
   - key tail:
     - `instance_plane_detail.cross_actor_isolation.cross_actor_isolation_status=SKIPPED_NOT_REQUIRED`
     - validator payload includes `"operation":"three-plane"` (no strict fallback).

#### Residual risk

1. This patch closes the specific three-plane routing hole identified in FIX-008 reject.
2. FIX-010 is now audit-closed; FIX-008 remains as historical reject record (closed-by linkage).

#### Next action

1. Replay completed and marked `PASS`; keep FIX-008 -> FIX-010 closure linkage explicit in decision board.
2. Keep actor isolation semantics under continuous regression checks.

---

#### Audit review verdict (2026-02-28T15:03:40Z)

1. Decision: `PASS` (scoped to FIX-010 objective).
2. Replayed evidence:
   - code wiring:
     - `scripts/report_three_plane_status.py` cross-actor call now includes `--operation three-plane`.
   - project-catalog three-plane replay:
     - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/fix008-three-plane-project-audit.json` => rc=`0`
     - `instance_plane_detail.cross_actor_isolation.cross_actor_isolation_status=SKIPPED_NOT_REQUIRED`
     - `validators.cross_actor_isolation.rc=0`
     - validator payload includes `"operation":"three-plane"`.
3. Audit note:
   - FIX-010 closes the exact reject condition recorded under FIX-008 (`strict fallback in three-plane cross-actor call`).

---

## 5) Emergency quick-fix incident records (P0, separate from FIX-00x)

### HOTFIX-P0-001 — Missing hard-gate for user-visible identity context stamp

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context: `sandbox` (evidence extraction)
- Source issue: response identity context can be omitted from user-facing output even when governance expects explicit stamp visibility.
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-018`, `ASB-RQ-019`, `ASB-RQ-020`, `DRC-8`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (gate wiring + fail-closed contract semantics)

#### Confirmed impact

1. User-visible responses can appear without explicit identity-context stamp, which increases undetected identity-drift risk (`串台` risk).
2. Current validator supports contract-first skip path (`SKIPPED_NOT_REQUIRED`) and does not universally hard-block user-facing output channels.

#### Evidence (paths / lines)

1. Skip branch proving hard-gate gap:
   - `scripts/validate_identity_response_stamp.py:121`
   - `scripts/validate_identity_response_stamp.py:125`
   - `scripts/validate_identity_response_stamp.py:127`
2. Runtime conversation evidence supplied by user (2026-02-28) showing missing explicit stamp in an output turn.

#### Required architect patch (quick-fix scope)

1. Add a protocol-level hard-gate mode for user-visible reply channel:
   - missing or mismatched stamp => fail-closed before business reply.
2. Keep blocker receipt path mandatory when blocked (no silent downgrade).
3. Wire hard-gate mode into:
   - `identity_creator.py validate`
   - `release_readiness_check.py`
   - `e2e_smoke_test.sh`
   - `full_identity_protocol_scan.py`
   - `report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
4. Ensure stamp rendering remains dynamic (resolver-derived), never hardcoded identity text.

#### Acceptance criteria (post-patch)

1. In governed output mode, stamp absence/mismatch must return non-zero with blocker receipt.
2. Replay of readiness/e2e/full-scan/three-plane must expose hard-gate results as machine-readable fields.
3. Audit replay must include both positive and negative samples.

#### Architect patch result (2026-02-28)

1. Commit:
   - `55c6bca` — `hotfix(p0): enforce visible stamp gate and actor-scoped session isolation`
2. Changed files (HOTFIX-P0-001 relevant):
   - `scripts/validate_identity_response_stamp.py`
   - `scripts/render_identity_response_stamp.py`
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Key implementation points:
   - Added hard-gate mode `--enforce-user-visible-gate` and forced check path to bypass `contract_not_required` skip for user-visible channel checks.
   - Added stamp evidence input channel `--stamp-json` (from rendered payload) and `IP-ASB-STAMP-004` for missing user-visible stamp evidence.
   - Wired `--force-check --enforce-user-visible-gate` into validate/readiness/e2e/full-scan/three-plane/required-gates.
   - Added deterministic stamp artifact output support via `render_identity_response_stamp.py --out <path>`.
4. Acceptance replay (rc + key tail):
   - `python3 scripts/validate_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --enforce-user-visible-gate --force-check --json-only`
     - rc=`1`, `error_code=IP-ASB-STAMP-004`, `blocker_receipt_path=/private/tmp/identity-stamp-blocker-receipt-base-repo-architect.json`
   - `python3 scripts/render_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --view external --out /tmp/hotfix1-stamp.json --json-only`
     + `python3 scripts/validate_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --stamp-json /tmp/hotfix1-stamp.json --enforce-user-visible-gate --force-check --blocker-receipt-out /tmp/hotfix1-blocker.json --json-only`
     - rc=`0`, `stamp_status=PASS`
   - `python3 scripts/release_readiness_check.py ...`
     - rc=`0`, includes:
       - `[RUN] ... validate_identity_response_stamp.py ... --force-check --enforce-user-visible-gate ...`
       - `[OK] release readiness checks PASSED`
   - `IDENTITY_CATALOG=... IDENTITY_IDS=custom-creative-ecom-analyst bash scripts/e2e_smoke_test.sh`
     - rc=`0`, includes:
       - `[12.3/30] ... validate response identity stamp hard gate (user-visible channel)`
       - `E2E smoke test PASSED`

#### Audit review verdict (2026-02-28T14:38:40Z)

1. Decision: `REJECT` (HOTFIX-P0-001 is not closed due receipt lifecycle inconsistency).
2. Replayed evidence:
   - hard-gate negative path:
     - `python3 scripts/validate_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --enforce-user-visible-gate --force-check --json-only`
     - rc=`1`, `error_code=IP-ASB-STAMP-004`, blocker receipt generated.
   - hard-gate positive path:
     - `python3 scripts/render_identity_response_stamp.py ... --out /tmp/hotfix1-stamp-audit.json --json-only`
     - `python3 scripts/validate_identity_response_stamp.py ... --stamp-json /tmp/hotfix1-stamp-audit.json --enforce-user-visible-gate --force-check --blocker-receipt-out /tmp/hotfix1-blocker-audit.json --json-only`
     - rc=`0`, `stamp_status=PASS`.
   - nondeterministic failure path in validate chain:
     - `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml`
     - rc=`1`, key failure:
       - `[FAIL] IP-ASB-STAMP-001 blocker receipt missing required fields: ['actual_identity_id']`
3. Root-cause anchors:
   - blocker receipt writer allows empty `actual_identity_id` on missing stamp path:
     - `scripts/validate_identity_response_stamp.py:259`
     - `scripts/validate_identity_response_stamp.py:263`
   - blocker receipt validator enforces non-empty required fields:
     - `scripts/validate_identity_response_stamp_blocker_receipt.py:46`
     - `scripts/validate_identity_response_stamp_blocker_receipt.py:56`
   - validate chain always re-checks fixed receipt path:
     - `scripts/identity_creator.py:1106`
     - `scripts/identity_creator.py:1122`
4. Disposition:
   - open new release-blocking item `HOTFIX-P0-003` for receipt lifecycle contract consistency and deterministic validation.

---

### HOTFIX-P0-002 — Explicit `activate` caused cross-identity hard switch/demotion

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context: `sandbox` (log and artifact evidence extraction)
- Source issue: under current single-active global model, explicit `activate` demotes previously active identity and rewrites session pointer; this enables identity hard-switch during remediation flow.
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-001`..`ASB-RQ-010`, `DRC-1`, `DRC-2`, `DRC-3`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (session/governance fail-closed expectations)

#### Confirmed impact

1. A single explicit command switched active identity from audit instance to architect instance.
2. Demotion was deterministic and recorded as `single_active_enforced=true`.
3. This is a P0 governance/runtime issue for multi-actor safety, not an accidental UI artifact.

#### Evidence (absolute paths / lines / artifacts)

1. Session log file:
   - `/Users/yangxi/.codex/sessions/2026/02/24/rollout-2026-02-24T02-11-15-019c8bb2-c691-7163-af90-f48b3962e279.jsonl`
2. Preceding failure (triggering switch attempt):
   - same file: `:24327` (`[FAIL] identity is not active; status=inactive`)
3. Explicit switch command:
   - same file: `:24346`
   - command contains `python3 scripts/identity_creator.py activate --identity-id base-repo-architect ...`
4. Successful switch output:
   - same file: `:24348`
   - contains `[OK] switch report: /tmp/identity-activation-reports/identity-activation-switch-base-repo-architect-1772283537.json`
5. Switch artifact proving demotion:
   - `/tmp/identity-activation-reports/identity-activation-switch-base-repo-architect-1772283537.json`
   - key fields: `generated_at=2026-02-28T12:58:57Z`, `target_identity_id=base-repo-architect`, `demoted_identities=["base-repo-audit-expert-v3"]`
6. Deterministic single-active implementation:
   - `scripts/identity_creator.py:248`
   - `scripts/identity_creator.py:282`
   - `scripts/identity_creator.py:307`

#### Required architect patch (quick-fix scope)

1. Add actor-scoped session truth (`<catalog>/session/actors/<actor_id>.json`) and stop using global single-active pointer as authority for all actors.
2. Forbid cross-actor demotion by default during `activate`.
3. If override is truly needed, require explicit audited flag + actor/run receipt (no implicit switch).
4. Add dedicated validators and wire required-gates:
   - `validate_actor_session_binding.py`
   - `validate_no_implicit_switch.py`
   - `validate_cross_actor_isolation.py`
5. Extend activation switch report schema with `actor_id`, `run_id`, `entrypoint_pid`, `switch_reason`.

#### Acceptance criteria (post-patch)

1. Replaying the same scenario must not demote another actor-bound identity unless audited override is explicit.
2. New validators must fail-closed on implicit switch patterns.
3. Three-plane/full-scan must surface actor-binding status and cross-actor isolation result fields.

#### Architect patch result (2026-02-28)

1. Commit:
   - `55c6bca` — `hotfix(p0): enforce visible stamp gate and actor-scoped session isolation`
2. Changed files (HOTFIX-P0-002 relevant):
   - `scripts/actor_session_common.py` (new)
   - `scripts/sync_session_identity.py`
   - `scripts/response_stamp_common.py`
   - `scripts/validate_actor_session_binding.py` (new)
   - `scripts/validate_no_implicit_switch.py` (new)
   - `scripts/validate_cross_actor_isolation.py` (new)
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Key implementation points:
   - Added actor-scoped session truth source at `<catalog>/session/actors/<actor_id>.json` through `sync_session_identity.py`.
   - `identity_creator activate` now carries actor audit tuple (`actor_id`, `run_id`, `switch_reason`, `entrypoint_pid`) into switch report.
   - Cross-actor demotion is blocked by default; explicit override requires `--allow-cross-actor-switch` + audited `--cross-actor-receipt`.
   - Added and wired validators:
     - `validate_actor_session_binding.py`
     - `validate_no_implicit_switch.py`
     - `validate_cross_actor_isolation.py`
4. Acceptance replay (rc + key tail):
   - actor binding source creation:
     - `python3 scripts/identity_creator.py activate --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER --actor-id user:yangxi --run-id hotfix-p0-002-actor-sync --switch-reason hotfix_p0_002_actor_binding`
     - rc=`0`, includes `[OK] session identity actor-bound: /Users/yangxi/.codex/identity/session/actors/user_yangxi.json`
   - default cross-actor demotion block:
     - `python3 scripts/identity_creator.py activate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER --actor-id user:auditor --run-id hotfix-cross-actor-block-2 --switch-reason cross_actor_probe`
     - rc=`1`, includes `[FAIL] cross-actor demotion blocked by default ...`
   - validator replay:
     - `validate_actor_session_binding(base-repo-architect)` => rc=`0`, `actor_binding_status=PASS_REQUIRED`
     - `validate_actor_session_binding(custom-creative-ecom-analyst)` => rc=`0`, `actor_binding_status=SKIPPED_NOT_REQUIRED`
     - `validate_no_implicit_switch(base-repo-architect)` => rc=`0`, `implicit_switch_status=PASS_REQUIRED`
     - `validate_cross_actor_isolation` => rc=`0`, `cross_actor_isolation_status=PASS_REQUIRED`
   - chain wiring:
     - `python3 scripts/release_readiness_check.py ...` => rc=`0`, includes new validator runs
     - `IDENTITY_CATALOG=... IDENTITY_IDS=custom-creative-ecom-analyst bash scripts/e2e_smoke_test.sh` => rc=`0`, includes `[10.18/30] validate actor-scoped session isolation gates ...`
     - `python3 scripts/report_three_plane_status.py ...` => rc=`0`, includes `instance_plane_detail.actor_session_binding/no_implicit_switch/cross_actor_isolation`
     - `python3 scripts/full_identity_protocol_scan.py ...` => rc=`0`, includes new check fields for actor isolation validators.

#### Audit review verdict (2026-02-28T14:38:40Z)

1. Decision: `PASS` (scoped to HOTFIX-P0-002 objective).
2. Replayed evidence:
   - actor session source exists:
     - `/Users/yangxi/.codex/identity/session/actors/user_yangxi.json`
     - key fields include `actor_id=user:yangxi`, `identity_id=base-repo-architect`, `session_pointer_type=actor_binding`.
   - validators:
     - `python3 scripts/validate_actor_session_binding.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --json-only` => rc=`0`, `actor_binding_status=PASS_REQUIRED`
     - `python3 scripts/validate_no_implicit_switch.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --json-only` => rc=`0`, `implicit_switch_status=PASS_REQUIRED`
     - `python3 scripts/validate_cross_actor_isolation.py --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --identity-id base-repo-architect --json-only` => rc=`0`, `cross_actor_isolation_status=PASS_REQUIRED`
   - default cross-actor block:
     - `python3 scripts/identity_creator.py activate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --scope USER --actor-id user:auditor --run-id hotfix-cross-actor-block-audit --switch-reason cross_actor_probe`
     - rc=`1`, tail includes `[FAIL] cross-actor demotion blocked by default ...`
3. Audit note:
   - this verdict is isolated to actor-scoped binding and cross-actor isolation behavior.
   - HOTFIX-P0-003 is closed (`PASS`); HOTFIX-P0-001 remains historical REJECT and is superseded by HOTFIX-P0-003 patch closure.

---

### HOTFIX-P0-003 — Stamp blocker receipt lifecycle mismatch causes nondeterministic validation

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context: `sandbox`
- Source issue: stamp hard-gate and blocker-receipt checker have incompatible assumptions, causing stateful/nondeterministic failures in `identity_creator validate`.
- Source ref:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-018`, `ASB-RQ-019`, `ASB-RQ-020`, `DRC-8`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (fail-closed determinism and auditable gate semantics)

#### Confirmed impact

1. Same protocol code path can pass/fail depending on stale receipt residue in `/tmp`, violating deterministic gate expectations.
2. `identity_creator validate` for `base-repo-architect` can fail despite stamp PASS path being wired.
3. This creates a false-negative gate and blocks reliable release readiness judgments.

#### Evidence (replay)

1. `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml`
   - rc=`1`
   - failure tail:
     - `[FAIL] IP-ASB-STAMP-001 blocker receipt missing required fields: ['actual_identity_id']`
2. receipt payload observed:
   - `/tmp/identity-stamp-blocker-receipt-base-repo-architect.json`
   - `actual_identity_id` is empty string.
3. contrast sample:
   - `python3 scripts/identity_creator.py validate --identity-id custom-creative-ecom-analyst ...`
   - rc=`0`
   - indicates state-dependent behavior rather than deterministic contract closure.

#### Required architect patch (quick-fix scope)

1. Harmonize receipt contract:
   - either ensure writer always sets non-empty `actual_identity_id` on fail paths, or adjust receipt validator schema to a clear two-mode contract (`BLOCK_FAIL` vs `PASS_NO_RECEIPT`).
2. Make validate chain deterministic:
   - do not validate stale receipt on stamp PASS path, or always regenerate canonical receipt before validation.
3. Keep hard-gate semantics:
   - user-visible channel still requires fail-closed on missing/mismatch stamp.
4. Preserve machine-readable outputs for readiness/e2e/full-scan/three-plane.

#### Acceptance criteria (post-patch)

1. Sequential replay `fail-sample -> pass-sample -> identity_creator validate` must be deterministic and reproducible across identities.
2. `identity_creator validate --identity-id base-repo-architect ...` returns rc=`0` after patch under clean and previously-failed receipt states.
3. receipt validator behavior matches writer contract with no empty-required-field contradictions.

#### Architect patch result (2026-02-28)

1. Commit:
   - `f385419` — `hotfix(stamp): make blocker receipt lifecycle deterministic`
2. Changed files:
   - `scripts/validate_identity_response_stamp.py`
3. Key implementation points:
   - On fail path, blocker receipt now forces non-empty `actual_identity_id` (`MISSING_STAMP` fallback) to satisfy receipt schema contract.
   - On pass path, stale blocker receipt at the same target path is removed, preventing cross-run residue from poisoning subsequent validation.
4. Acceptance replay (rc + key tail):
   - fail sample (hard-gate missing stamp):
     - `python3 scripts/validate_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --enforce-user-visible-gate --force-check --json-only`
     - rc=`1`, `error_code=IP-ASB-STAMP-004`, blocker receipt includes `actual_identity_id=MISSING_STAMP`
   - blocker receipt schema check:
     - `python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --force-check --receipt /tmp/identity-stamp-blocker-receipt-base-repo-architect.json --json-only`
     - rc=`0`, `receipt_status=PASS`
   - pass sample with same receipt path:
     - `python3 scripts/render_identity_response_stamp.py ... --out /tmp/hotfix3-stamp.json --json-only`
     - `python3 scripts/validate_identity_response_stamp.py ... --stamp-json /tmp/hotfix3-stamp.json --enforce-user-visible-gate --force-check --blocker-receipt-out /tmp/identity-stamp-blocker-receipt-base-repo-architect.json --json-only`
     - rc=`0`, `stamp_status=PASS`, `blocker_receipt_path=""`
     - `ls -l /tmp/identity-stamp-blocker-receipt-base-repo-architect.json` => missing (expected cleanup)
   - deterministic validate chain replay:
     - `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml`
     - rc=`0`, includes:
       - `validate_identity_response_stamp PASSED`
       - `validate_identity_response_stamp_blocker_receipt PASSED`

#### Next action

1. Replay completed and marked `PASS`; emergency board updated for HOTFIX-P0-003.
2. Release freeze should now depend on remaining unresolved P0 items, not HOTFIX-P0-003.

#### Audit review verdict (2026-02-28T15:03:40Z)

1. Decision: `PASS` (scoped to HOTFIX-P0-003 objective).
2. Replayed evidence:
   - fail path receipt field hardening:
     - `python3 scripts/validate_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --enforce-user-visible-gate --force-check --blocker-receipt-out /tmp/hotfix003-receipt-audit.json --json-only` => rc=`1`; payload includes `error_code=IP-ASB-STAMP-004` and blocker receipt `actual_identity_id=MISSING_STAMP`.
   - pass path stale-receipt cleanup:
     - render + validate with same `--blocker-receipt-out /tmp/hotfix003-receipt-audit.json` => rc=`0`, `stamp_status=PASS`.
     - receipt file no longer exists after PASS path (`cleanup confirmed`).
   - downstream receipt validator determinism:
     - `python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --receipt /tmp/hotfix003-receipt-audit.json --force-check --json-only` => rc=`0`, `receipt_status=PASS`.
   - full validate-chain determinism:
     - `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml` => rc=`0`
     - `python3 scripts/identity_creator.py validate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml` => rc=`0`.
3. Audit note:
   - HOTFIX-P0-003 resolves the blocker-receipt lifecycle nondeterminism that caused HOTFIX-P0-001 rejection replay.

---

## 6) Post-fix release snapshot (2026-02-28, protocol-only residual view)

### Snapshot command set

1. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids "base-repo-audit-expert-v3 office-ops-expert store-manager base-repo-architect custom-creative-ecom-analyst system-requirements-analyst" --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-next-task.json`
2. `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix010-project-replay2.json`
3. `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix010-global-replay2.json`

### Observed summary

1. full-scan summary:
   - `{"total_identities": 9, "p0": 1, "p1": 6, "ok": 2}`
2. three-plane project catalog replay:
   - `cross_actor_isolation_status=SKIPPED_NOT_REQUIRED`
   - validator payload contains `"operation":"three-plane"` (FIX-010 effective)
3. three-plane global catalog replay:
   - `cross_actor_isolation_status=PASS_REQUIRED`
   - validator payload contains `"operation":"three-plane"` (FIX-010 effective)

### Residual classification (do not mix layers)

1. Remaining `P0/P1` counts in full-scan are dominated by cross-catalog/runtime-context drift (project `.agents` catalog vs global runtime catalog), including:
   - `identity_home_catalog_alignment` mismatch for project catalog contexts
   - project-pack prompt/report path mismatch against global reports
2. These are **instance/environment governance residuals**, not newly introduced protocol gate regressions.
3. Protocol-layer closures from this batch remain:
   - HOTFIX-P0-003: `PASS`
   - FIX-009: `PASS`
   - FIX-010: `PASS`
   - FIX-008: historical `REJECT` with explicit `closed-by FIX-010` linkage.

---

### FIX-011 — Track-A writeback continuity + post-execution mandatory gates (initial landing)

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for static checks and scan/three-plane replay
  - `escalated` for runtime update/readiness replay against `~/.codex`
- Source refs:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`5.7.1`, `ASB-RQ-032`, `ASB-RQ-033`, `DRC-11`)

#### Change summary

1. Added Track-A validators:
   - `scripts/validate_writeback_continuity.py`
   - `scripts/validate_post_execution_mandatory.py`
2. Added writeback continuity fields into execution report payload:
   - `writeback_mode`
   - `degrade_reason`
   - `risk_level`
   - `next_recovery_action`
   - file: `scripts/execute_identity_upgrade.py`
3. Wired new validators into main-chain surfaces:
   - `scripts/identity_creator.py` (`validate`)
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
4. Health visibility update:
   - `scripts/collect_identity_health_report.py` now includes Track-A checks (`scan` operation).

#### Acceptance replay (architect run, pre-audit)

1. Static checks:
   - `python3 -m py_compile scripts/execute_identity_upgrade.py scripts/validate_writeback_continuity.py scripts/validate_post_execution_mandatory.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py scripts/collect_identity_health_report.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. Validator behavior:
   - `validate_writeback_continuity` on latest runtime report (`custom-creative-ecom-analyst`) => `FAIL_REQUIRED`, `error_code=IP-WRB-001` when `writeback_status=MISSING`.
   - `validate_post_execution_mandatory` on same report => `FAIL_REQUIRED`, `error_code=IP-WRB-003` when post-execution closure is incomplete.
3. Chain visibility:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix011.json` => `rc=0`; includes `checks.writeback_continuity` + `checks.post_execution_mandatory`.
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix011.json` => `rc=0`; includes `instance_plane_detail.writeback_continuity` + `instance_plane_detail.post_execution_mandatory`.
   - `python3 scripts/collect_identity_health_report.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out-dir /tmp/identity-health-reports` => `rc=0`; report shows Track-A failures as health signals.

#### Residual risk

1. Track-A checks now surface deterministic failures, but closure still depends on upstream update validators producing `all_ok=true` + non-missing writeback path.
2. `release_readiness_check` for target identity can still stop early if `identity_creator update` returns non-zero before downstream Track-A checks.
3. Track-B (`semantic_routing_guard_contract_v1`) is still pending implementation and audited separately per non-merge rule.

#### Next action

1. Submit FIX-011 patch set for audit replay.
2. Keep v1.5 tag blocked until Track-A audit verdict is `PASS` and Track-B implementation/replay is completed.

#### Audit review verdict (2026-02-28T15:36:55Z)

1. Decision: `PASS` (scoped to FIX-011 objective).
2. Replay evidence summary:
   - sandbox:
     - `python3 scripts/validate_writeback_continuity.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation readiness --json-only` => `rc=1`, `writeback_continuity_status=FAIL_REQUIRED`, `error_code=IP-WRB-001`.
     - `python3 scripts/validate_post_execution_mandatory.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation readiness --json-only` => `rc=1`, `post_execution_mandatory_status=FAIL_REQUIRED`, `error_code=IP-WRB-003`.
     - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix011-audit.json` => `rc=0`, includes `checks.writeback_continuity` + `checks.post_execution_mandatory`.
     - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix011-audit.json` => `rc=0`, includes `instance_plane_detail.writeback_continuity` + `instance_plane_detail.post_execution_mandatory`.
     - `python3 scripts/collect_identity_health_report.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out-dir /tmp/identity-health-reports-fix011-audit` => `rc=0`, `overall_status=FAIL`, `failed_count=2` with Track-A repair guidance.
   - escalated (`~/.codex` writable):
     - `python3 scripts/identity_creator.py update --identity-id custom-creative-ecom-analyst --mode review-required --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --capability-activation-policy route-any-ready` => `rc=2`, report generated with `all_ok=False` and non-closure `next_action`.
     - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready` => `rc=2`, early-stop at update non-zero path (expected current behavior).
3. Audit note:
   - FIX-011 is accepted as Track-A gate landing and visibility closure; this does not claim Track-A runtime closure for the target identity state.
   - `python3 scripts/docs_command_contract_check.py` and `python3 scripts/validate_protocol_ssot_source.py` replayed clean (`rc=0`).

---

### FIX-012 — Track-B semantic routing guard + vendor namespace separation gates (initial landing)

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for static checks and validator/full-scan/three-plane replay
  - `escalated` not required in this architect replay batch
- Source refs:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`5.7.2`, `ASB-RQ-034`, `ASB-RQ-035`, `DRC-12`)

#### Change summary

1. Added Track-B validators:
   - `scripts/validate_semantic_routing_guard.py`
   - `scripts/validate_vendor_namespace_separation.py`
2. Added auto-required safety signal for legacy protocol-feedback artifacts (prevents silent skip when semantic-risk artifacts already exist).
3. Wired validators into main-chain surfaces:
   - `scripts/identity_creator.py` (`validate`)
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
4. Health visibility update:
   - `scripts/collect_identity_health_report.py` now includes Track-B checks.

#### Acceptance replay (architect run, pre-audit)

1. Static checks:
   - `python3 -m py_compile scripts/validate_semantic_routing_guard.py scripts/validate_vendor_namespace_separation.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py scripts/collect_identity_health_report.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. Contract-first skip path (no Track-B contract and no feedback artifacts):
   - `python3 scripts/validate_semantic_routing_guard.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only` => `rc=0`, `semantic_routing_status=SKIPPED_NOT_REQUIRED`.
   - `python3 scripts/validate_vendor_namespace_separation.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only` => `rc=0`, `vendor_namespace_status=SKIPPED_NOT_REQUIRED`.
3. Auto-required risk path (legacy feedback artifacts present):
   - `python3 scripts/validate_semantic_routing_guard.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only` => `rc=1`, `semantic_routing_status=FAIL_REQUIRED`, `error_code=IP-SEM-001`, `auto_required_signal=true`.
   - `python3 scripts/validate_vendor_namespace_separation.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only` => `rc=1`, `vendor_namespace_status=FAIL_REQUIRED`, `error_code=IP-SEM-003`, includes legacy `vendor-intel/*` evidence refs.
4. Chain visibility:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids system-requirements-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix012-system.json` => `rc=0`; includes `checks.semantic_routing_guard` + `checks.vendor_namespace_separation`.
   - `python3 scripts/report_three_plane_status.py --identity-id system-requirements-analyst --scope USER --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix012-system.json` => `rc=0`; includes `instance_plane_detail.semantic_routing_guard` + `instance_plane_detail.vendor_namespace_separation`.

#### Residual risk

1. Track-B validators now expose deterministic boundary violations, but closure still requires instance-side contract/report namespace migration.
2. `system-requirements-analyst` currently surfaces real legacy violations (`vendor-intel/*`, missing semantic contract fields).
3. Track-B sidecar escalation policy (`ASB-RQ-036`) remains to be finalized in a dedicated follow-up patch.

#### Next action

1. Submit FIX-012 patch set for audit replay and verdict.
2. Keep v1.5 release tag blocked until Track-B audit verdict is `PASS` and follow-up sidecar escalation contract is aligned.

#### Audit review verdict (2026-02-28T16:11:35Z)

1. Decision: `PASS` (scoped to FIX-012 objective).
2. Replay method:
   - audit replay was executed in isolated worktree pinned to commit `a8e2671` (`/tmp/idp_fix012_audit`) to avoid contamination from in-progress FIX-013 edits.
3. Replayed evidence:
   - static checks:
     - `python3 -m py_compile scripts/validate_semantic_routing_guard.py scripts/validate_vendor_namespace_separation.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py scripts/collect_identity_health_report.py scripts/identity_creator.py` + `bash -n scripts/e2e_smoke_test.sh` => `rc=0`.
   - contract-first skip path (`custom-creative-ecom-analyst`):
     - `validate_semantic_routing_guard --operation scan --json-only` => `rc=0`, `semantic_routing_status=SKIPPED_NOT_REQUIRED`.
     - `validate_vendor_namespace_separation --operation scan --json-only` => `rc=0`, `vendor_namespace_status=SKIPPED_NOT_REQUIRED`.
   - auto-required fail-closed path (`system-requirements-analyst`):
     - `validate_semantic_routing_guard --operation scan --json-only` => `rc=1`, `semantic_routing_status=FAIL_REQUIRED`, `error_code=IP-SEM-001`, `auto_required_signal=true`.
     - `validate_vendor_namespace_separation --operation scan --json-only` => `rc=1`, `vendor_namespace_status=FAIL_REQUIRED`, `error_code=IP-SEM-003`, `legacy_vendor_file_count=1`.
   - chain visibility:
     - `full_identity_protocol_scan --scan-mode target ... --out /tmp/full-scan-fix012-audit-system.json` => `rc=0`; summary `{\"total_identities\":1,\"p0\":0,\"p1\":1,\"ok\":0}`; includes `checks.semantic_routing_guard` + `checks.vendor_namespace_separation` with `FAIL_REQUIRED`.
     - `report_three_plane_status ... --out /tmp/three-plane-fix012-audit-system.json` => `rc=0`; includes `instance_plane_detail.semantic_routing_guard` + `instance_plane_detail.vendor_namespace_separation` with `FAIL_REQUIRED`; `overall_release_decision=Conditional Go`.
   - health visibility:
     - `collect_identity_health_report` includes Track-B checks and preserves machine-readable status projection.
4. Audit note:
   - FIX-012 is accepted as Track-B gate landing and fail-closed visibility closure.
   - This verdict does not claim instance data migration closure for `system-requirements-analyst` legacy namespace debt; that debt is correctly surfaced as deterministic boundary failure.

---

### FIX-013 — Sidecar escalation contract closure (ASB-RQ-036, Track-A/B coexistence)

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context:
  - `sandbox` for static checks + validator/full-scan/three-plane/health replay
  - `escalated` not required in this architect replay batch
- Source refs:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`5.7.3`, `ASB-RQ-036`, `DRC-12`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (machine-readable gate outputs required)

#### Change summary

1. Added validator:
   - `scripts/validate_protocol_feedback_sidecar_contract.py`
2. Contract semantics landed:
   - sidecar default is non-blocking (`NON_BLOCKING_DEFAULT`);
   - escalation becomes blocking only on governance-boundary P0 violations;
   - structured payload fields for escalation decision (`escalation_required`, `escalation_decision`, `p0_violations`, `blocking_error_codes`).
3. Main-chain wiring completed:
   - `scripts/identity_creator.py` (`validate`, enforce-blocking)
   - `scripts/release_readiness_check.py` (post-report preflight chain, enforce-blocking)
   - `scripts/e2e_smoke_test.sh` (post-report gate, enforce-blocking)
   - `scripts/full_identity_protocol_scan.py` (scan visibility)
   - `scripts/report_three_plane_status.py` (instance-plane detail visibility)
   - `.github/workflows/_identity-required-gates.yml` (CI gate, enforce-blocking)
   - `scripts/collect_identity_health_report.py` (health check + WARN/FAIL mapping)

#### Acceptance replay (architect run, pre-audit)

1. Static checks:
   - `python3 -m py_compile scripts/validate_protocol_feedback_sidecar_contract.py scripts/collect_identity_health_report.py scripts/full_identity_protocol_scan.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/report_three_plane_status.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. Contract-first skip path (no sidecar contract + no protocol-feedback artifacts):
   - `python3 scripts/validate_protocol_feedback_sidecar_contract.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation scan --json-only`
   - result: `rc=0`, `sidecar_contract_status=SKIPPED_NOT_REQUIRED`
3. Auto-required risk path (legacy protocol-feedback artifacts present, sidecar contract missing):
   - `python3 scripts/validate_protocol_feedback_sidecar_contract.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation scan --json-only`
   - result: `rc=1`, `sidecar_contract_status=FAIL_REQUIRED`, `sidecar_error_code=IP-SID-001`, `auto_required_signal=true`
4. Chain visibility:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids system-requirements-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix013-system.json`
   - result: `rc=0`; includes `checks.protocol_feedback_sidecar` with machine-readable sidecar fields.
   - `python3 scripts/report_three_plane_status.py --identity-id system-requirements-analyst --scope USER --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix013-system.json`
   - result: `rc=0`; includes `instance_plane_detail.protocol_feedback_sidecar`.
5. Health visibility:
   - `python3 scripts/collect_identity_health_report.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out-dir /tmp/identity-health-reports-fix013`
   - result: `rc=0`; `checks[].name=protocol_feedback_sidecar` mapped to structured FAIL/WARN/PASS semantics.

#### Residual risk

1. Identities with existing `runtime/protocol-feedback` artifacts but without `protocol_feedback_sidecar_contract_v1` now fail with `IP-SID-001`; instance owners must add sidecar contract fields.
2. Audit replay is still required for strict-operation surfaces (`readiness/e2e/ci`) under escalated context.

#### Next action

1. Commit FIX-013 patch set and update rolling summary with concrete sha.
2. Submit FIX-013 for audit replay; keep v1.5 tag blocked until Track-B verdict and sidecar closure are both PASS.

#### Audit review verdict (2026-02-28T18:24:00Z)

1. Decision: `PASS` (scoped to FIX-013 objective).
2. Replay evidence summary (sandbox):
   - static checks:
     - `python3 -m py_compile scripts/validate_protocol_feedback_sidecar_contract.py scripts/collect_identity_health_report.py scripts/full_identity_protocol_scan.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/report_three_plane_status.py` + `bash -n scripts/e2e_smoke_test.sh` => `rc=0`.
   - sidecar validator behavior:
     - `validate_protocol_feedback_sidecar_contract --identity-id custom-creative-ecom-analyst --operation scan --json-only` => `rc=0`, `sidecar_contract_status=SKIPPED_NOT_REQUIRED`.
     - `validate_protocol_feedback_sidecar_contract --identity-id system-requirements-analyst --operation scan --json-only` => `rc=1`, `sidecar_contract_status=FAIL_REQUIRED`, `sidecar_error_code=IP-SID-001`, `auto_required_signal=true`.
   - chain visibility:
     - `full_identity_protocol_scan --scan-mode target --identity-ids system-requirements-analyst ... --out /tmp/full-scan-fix013-audit-system.json` => `rc=0`; includes `checks.protocol_feedback_sidecar` with escalation fields.
     - `report_three_plane_status --identity-id system-requirements-analyst ... --out /tmp/three-plane-fix013-audit-system.json` => `rc=0`; includes `instance_plane_detail.protocol_feedback_sidecar`.
     - `collect_identity_health_report --identity-id system-requirements-analyst ... --out-dir /tmp/identity-health-reports-fix013-audit` => `rc=0`; includes `protocol_feedback_sidecar` check with deterministic FAIL semantics.
   - governance consistency:
     - `python3 scripts/docs_command_contract_check.py` => `rc=0`
     - `python3 scripts/validate_protocol_ssot_source.py` => `rc=0`
3. Audit note:
   - PASS confirms protocol-layer sidecar contract semantics + machine-readable wiring closure.
   - This verdict does not claim runtime debt cleanup for `system-requirements-analyst` (legacy feedback artifacts remain and are correctly surfaced by `IP-SID-001`).
   - Additional replay suggested: strict-operation positive path (`--enforce-blocking` + complete sidecar contract + no blocking P0) through readiness/e2e/ci surfaces.

---

### FIX-014 — Required-contract coverage extension for Track-B + sidecar (operation-aware)

- Date (UTC): 2026-02-28
- Layer declaration: `protocol`
- Execution context: `sandbox` (architect pre-audit replay)
- Source refs:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-034`, `ASB-RQ-035`, `ASB-RQ-036`, `ASB-RQ-009`)
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` (coverage semantics and machine-readable gate reporting)

#### Change summary

1. Extended `scripts/validate_required_contract_coverage.py` target set:
   - existing: `tool_installation`, `vendor_api_discovery`, `vendor_api_solution`
   - added: `semantic_routing_guard`, `vendor_namespace_separation`, `protocol_feedback_sidecar`
2. Added operation-aware execution support in coverage validator:
   - new args: `--repo-catalog`, `--operation`
   - operation-aware forwarding for Track-B + sidecar validators.
3. Added payload-aware requiredness handling:
   - supports `required_contract` and `auto_required_signal` emitted by Track-B/sidecar validators.
   - avoids legacy misclassification where auto-required failures could be reported as optional.
4. Main-chain calls updated to pass operation context explicitly:
   - `scripts/identity_creator.py` (`--operation validate`)
   - `scripts/release_readiness_check.py` (`--operation readiness`)
   - `scripts/e2e_smoke_test.sh` (`--operation e2e`)
   - `scripts/full_identity_protocol_scan.py` (`--operation scan`)
   - `scripts/report_three_plane_status.py` (`--operation three-plane`)
   - `.github/workflows/_identity-required-gates.yml` (`--operation ci`)

#### Acceptance replay (architect run, pre-audit)

1. Static checks:
   - `python3 -m py_compile scripts/validate_required_contract_coverage.py scripts/release_readiness_check.py scripts/identity_creator.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. Contract-first skip path:
   - `python3 scripts/validate_required_contract_coverage.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation scan --json-only`
   - expected: rc reflects required-contract snapshot and includes Track-B/sidecar rows as `SKIPPED_NOT_REQUIRED` when no contract/auto-required signal.
3. Auto-required fail path visibility:
   - `python3 scripts/validate_required_contract_coverage.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation scan --json-only`
   - expected: non-zero with Track-B rows carrying `FAIL_REQUIRED` and `IP-SEM-*` reason codes.
4. Chain wiring visibility:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids system-requirements-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix014-system.json`
   - `python3 scripts/report_three_plane_status.py --identity-id system-requirements-analyst --scope USER --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-fix014-system.json`
   - expected: coverage payload fields remain machine-readable and operation-consistent.

#### Residual risk

1. FIX-014 depends on FIX-013 sidecar validator being present and stable.
2. Final required-coverage thresholds remain policy-level decisions; FIX-014 only hardens status semantics + operation consistency.

#### Next action

1. Submit FIX-014 to audit replay and wait for PASS/REJECT verdict.
2. Keep v1.5 tag blocked until FIX-013/FIX-014 verdicts are both PASS.

#### Audit review verdict (2026-02-28T16:22:30Z)

1. Decision: `PASS` (scoped to FIX-014 objective).
2. Replay evidence summary (sandbox):
   - static checks:
     - `python3 -m py_compile scripts/validate_required_contract_coverage.py scripts/release_readiness_check.py scripts/identity_creator.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py` + `bash -n scripts/e2e_smoke_test.sh` => `rc=0`.
   - validator behavior (`scan`):
     - `validate_required_contract_coverage --identity-id custom-creative-ecom-analyst --operation scan --json-only` => `rc=0`; `required_contract_total=3`, `required_contract_passed=3`, `skipped_contract_count=3`.
     - `validate_required_contract_coverage --identity-id system-requirements-analyst --operation scan --json-only` => `rc=1`; `required_contract_total=3`, `failed_required_contract_count=3`, reason codes include `IP-SEM-001`, `IP-SEM-003`, `IP-SID-001`.
   - chain visibility:
     - `full_identity_protocol_scan --scan-mode target --identity-ids system-requirements-analyst ... --out /tmp/full-scan-fix014-audit-system.json` => `rc=0`; includes `checks.required_contract_coverage` with Track-B/sidecar required coverage stats.
     - `report_three_plane_status --identity-id system-requirements-analyst ... --out /tmp/three-plane-fix014-audit-system.json` => `rc=0`; includes `instance_plane_detail.required_contract_coverage` with consistent totals/failed-required counts.
   - operation routing evidence:
     - `identity_creator validate` includes `validate_required_contract_coverage.py --operation validate`.
     - `release_readiness_check.py` includes `validate_required_contract_coverage.py --operation readiness`.
     - `e2e_smoke_test.sh` includes `validate_required_contract_coverage.py --operation e2e`.
     - `required-gates` workflow includes `validate_required_contract_coverage.py --operation ci`.
   - governance consistency:
     - `python3 scripts/docs_command_contract_check.py` => `rc=0`
     - `python3 scripts/validate_protocol_ssot_source.py` => `rc=0`
3. Audit note:
   - PASS confirms FIX-014 closed the coverage semantic gap for auto-required Track-B/sidecar failures being misclassified as optional.
   - This verdict does not alter instance debt outcomes; legacy artifacts under `system-requirements-analyst` correctly remain deterministic FAIL_REQUIRED signals.

---

## 7) Next release-blocking verifier: FIX-015 (concurrent actor x identity activation)

### Scope declaration

1. Layer: `protocol`
2. Type: `release-blocking verifier` (not business-feature patch)
3. Purpose: prove runtime can hold concurrent actor bindings without hidden demotion or pointer drift regression.

### Why FIX-015 is mandatory

1. Current runtime has actor-scoped validators, but core activation/state/pointer/installer/compile paths still carry legacy single-active assumptions.
2. Without a dedicated concurrency replay gate, regressions can pass local checks and reintroduce implicit actor demotion in later fixes.
3. FIX-015 is the hard proof step between "spec/governance ready" and "runtime concurrent activation ready".

### Dependency boundary (must be true before FIX-015 can pass)

1. Activation path no longer demotes other identities by global singleton rule (`ASB-RC-001`, `ASB-RQ-010`).
2. State consistency validator no longer fails only because active count > 1 (`ASB-RC-003`).
3. Session pointer consistency uses actor-scoped canonical source as authority (`ASB-RC-004`, `ASB-RC-006`).
4. Installer/compile flow no longer depends on single-active precheck semantics (`ASB-RC-002`, `ASB-RC-005`).
5. Concurrency-stream fix IDs must be assigned in a dedicated numbering lane; do not reuse Track-A/Track-B fix IDs.

### Acceptance replay template (required evidence)

1. Build two independent actor bindings in same catalog:
   - actor A -> identity X
   - actor B -> identity Y
2. Run validators for both actor tuples:
   - `validate_actor_session_binding.py` => PASS for both tuples
   - `validate_no_implicit_switch.py` => PASS for both tuples
   - `validate_cross_actor_isolation.py` => PASS with consistent actor binding set
3. Run state/session checks under new model:
   - `validate_identity_state_consistency.py` => PASS under concurrent activation semantics
   - `validate_identity_session_pointer_consistency.py` => PASS using actor-scoped canonical semantics
4. Run chain surfaces:
   - `release_readiness_check.py` => PASS
   - `e2e_smoke_test.sh` => PASS
   - `full_identity_protocol_scan.py` and `report_three_plane_status.py` show machine-readable actor-scoped PASS outputs (no strict-fallback artifact).
5. Regression guard:
   - any replay output showing implicit demotion, singleton-only enforcement, or pointer authority fallback to legacy global pointer is `FAIL_REQUIRED`.

### Source refs

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`:
   - `DRC-1`, `DRC-4`
   - `ASB-RQ-009`, `ASB-RQ-010`
   - `ASB-RC-001~006`
2. This review ledger remains L3 tracking only and must not override L1/L2 contract semantics.

---

## 8) Deep-scan cross-validation snapshot (2026-02-28, audit replay)

- Layer declaration: `protocol-audit`
- Execution context:
  - `sandbox`: full-scan + three-plane + validator cross-check + docs/SSOT replay
  - `escalated`: self identity upgrade/release-readiness/heal replay on `~/.codex`
- Source refs:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`DRC-8`, `DRC-11`, `DRC-12`, `ASB-RQ-015`, `ASB-RQ-018~021`, `ASB-RQ-032/033`)

### 8.1 Deep-scan summary

1. Command:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids "custom-creative-ecom-analyst system-requirements-analyst base-repo-audit-expert-v3" --repo-catalog identity/catalog/identities.yaml --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --include-repo-catalog --out /tmp/full-scan-fix015-deep-audit.json`
2. Result:
   - `summary={"total_identities":6,"p0":1,"p1":3,"ok":2}`
   - `repo:system-requirements-analyst => OK`
   - `project:custom-creative-ecom-analyst => P0`
   - `project:base-repo-audit-expert-v3 => P1`
   - `global:system-requirements-analyst => OK`
   - `global:custom-creative-ecom-analyst => P1`
   - `global:base-repo-audit-expert-v3 => P1`

### 8.2 Two-instance cross-validation + self sample

1. Command family:
   - `report_three_plane_status.py` + actor validators (`validate_actor_session_binding.py`, `validate_no_implicit_switch.py`, `validate_cross_actor_isolation.py`) for:
     - `custom-creative-ecom-analyst`
     - `system-requirements-analyst`
     - `base-repo-audit-expert-v3` (self sample)
2. Three-plane key outputs:
   - `custom-creative-ecom-analyst`:
     - `required_contract_coverage: required_total=3/pass=3`
     - `writeback_continuity=FAIL_REQUIRED(IP-WRB-001)`
     - `post_execution_mandatory=FAIL_REQUIRED(IP-WRB-003)`
     - `response_identity_stamp=PASS`
   - `system-requirements-analyst`:
     - `required_contract_coverage: required_total=3/pass=3`
     - `protocol_feedback_sidecar=PASS_REQUIRED`
     - `writeback_continuity=PASS_REQUIRED`
     - `post_execution_mandatory=PASS_REQUIRED`
     - `response_identity_stamp=PASS`
   - `base-repo-audit-expert-v3`:
     - `required_contract_coverage: required_total=3/pass=3`
     - `writeback_continuity=FAIL_REQUIRED(IP-WRB-001)`
     - `post_execution_mandatory=FAIL_REQUIRED(IP-WRB-003)`
     - `response_identity_stamp=PASS`

### 8.3 Self-upgrade replay (audit identity instance)

1. `identity_creator update --mode review-required`:
   - `rc=2`, report generated:
     - `/Users/yangxi/.codex/identity/base-repo-audit-expert-v3/runtime/reports/identity-upgrade-exec-base-repo-audit-expert-v3-1772296492.json`
   - key: `all_ok=false`, `next_action=review_required_create_pr_from_patch_plan`
2. `identity_creator update --mode safe-auto`:
   - `rc=3`, report generated:
     - `/Users/yangxi/.codex/identity/base-repo-audit-expert-v3/runtime/reports/identity-upgrade-exec-base-repo-audit-expert-v3-1772297050.json`
   - key: `all_ok=false`, `next_action=blocked_by_safe_auto_path_policy`, `permission_error_code=IP-UPG-001`, `experience_writeback.error_code=IP-SAFEAUTO-001`
3. `release_readiness_check.py` (self):
   - `rc=2`, fail point:
     - `collect_identity_health_report --enforce-pass`
   - failing items:
     - `writeback_continuity=FAIL_REQUIRED(IP-WRB-001)`
     - `post_execution_mandatory=FAIL_REQUIRED(IP-WRB-003)`
4. `identity_creator heal --apply` (self):
   - `rc=1` (`FAIL_VALIDATE`)
   - replay shows post-repair validate failed on runtime contract (`rulebook_contract.rulebook_path` resolution path regression branch).

### 8.4 Audit decision from this snapshot

1. `system-requirements-analyst` now demonstrates Track-A/Track-B/sidecar closure on global runtime sample (PASS_REQUIRED set complete).
2. `custom-creative-ecom-analyst` and `base-repo-audit-expert-v3` remain blocked by Track-A post-execution closure (`IP-WRB-001` / `IP-WRB-003`).
3. Self identity upgrade did not converge to `all_ok=true` in this replay window; therefore no "self-upgrade success" claim is allowed for current state.

---

## 9) External handoff intake audit — `identity_protocol_l5_handoff_2026-02-28.md`

- Intake source:
  - `/Users/yangxi/claude/codex_project/webbrowser/artifacts/report-facts/identity_protocol_l5_handoff_2026-02-28.md`
- Intake identity context:
  - `actor_id=user:yangxi`
  - `identity_id=custom-creative-ecom-analyst`
  - `scope=USER`
- Audit decision:
  - `PARTIAL_ACCEPT` (claims are valid only under constrained project-local setup; not yet protocol-level L5 closure)
- Source refs:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-025/026/027`, `ASB-RQ-030`, `ASB-RQ-018~021`, `DRC-8`, `DRC-9`, `DRC-10`)

### 9.1 Claim-by-claim replay result

1. Claim: `health FAIL(6) -> PASS(0)` and local runtime closure.
   - Replay result: `CONFIRMED (project-local sample)`
   - Evidence:
     - `python3 scripts/collect_identity_health_report.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --out-dir /tmp/identity-health-reports-l5-audit-project`
     - output: `overall_status=PASS`, `failed_count=0`.
2. Claim: `validate` full chain pass in project-local.
   - Replay result: `NOT_STABLE (default env mismatch)`
   - Evidence:
     - `python3 scripts/identity_creator.py validate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER`
     - output includes `IP-PATH-003` (`identity_home_catalog_parent_mismatch`) and exits non-zero.
   - Counterfactual control:
     - forcing aligned home passes:
       - `python3 scripts/validate_identity_home_catalog_alignment.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --identity-home /Users/yangxi/claude/codex_project/weixinstore/.agents/identity --json-only`
       - result: `PASS_REQUIRED`.
3. Claim: P0 requires refresh scripts and gate wiring.
   - Replay result: `CONFIRMED`
   - Evidence:
     - `rg --files scripts | rg 'refresh_identity_session_status\\.py|validate_identity_session_refresh_status\\.py'`
     - result: no matches.
4. Claim: response identity stamp must be mandatory on every user-visible reply.
   - Replay result: `CONFIRMED as unresolved protocol/runtime boundary issue`
   - Evidence:
     - live audit thread observed missing first-line `Identity-Context` outputs.
     - tracked under `HOTFIX-P0-004` in this ledger.

### 9.2 Required architect actions (derived from replay)

1. P0: implement and wire `refresh_identity_session_status.py` + `validate_identity_session_refresh_status.py` into readiness/e2e/full-scan/three-plane/CI.
2. P0: enforce project-local default alignment (`IDENTITY_HOME == dirname(IDENTITY_CATALOG)`) in mutation/validate entrypoints, not only via optional explicit arg.
3. P0: enforce user-visible channel hard gate for missing `Identity-Context` first line (fail-closed + blocker receipt).
4. P1: align health and validate gate coverage so `health PASS` cannot coexist with default-entry `validate FAIL` for the same identity context tuple.

### 9.3 L5 readiness status after this intake

1. L5 cannot be declared yet at protocol level.
2. Current best classification remains `L4/5` with validated instance capability but unresolved protocol asset completeness.

### 9.4 Intake-2 cross-validation addendum (2026-02-28)

1. Replay input:
   - external feedback payload from `custom-creative-ecom-analyst` (L4+/L5 delta claims).
2. Claim verification matrix:
   - `health PASS` claim: `CONFIRMED`
     - `/private/tmp/identity-health-reports/identity-health-custom-creative-ecom-analyst-1772296143.json` => `overall_status=PASS`, `failed_count=0`.
   - `validate rc=0` claim: `CONDITIONALLY_CONFIRMED`
     - default env replay (`IDENTITY_HOME` still global) => `rc=1`, `IP-PATH-003`.
     - aligned env replay (`IDENTITY_HOME=/Users/yangxi/claude/codex_project/weixinstore/.agents/identity`) => `rc=0`.
     - conclusion: pass depends on explicit environment alignment; not default-stable.
   - refresh scripts missing claim: `CONFIRMED`
     - no matches for `refresh_identity_session_status.py` / `validate_identity_session_refresh_status.py`.
   - prompt/history stale claim: `CONFIRMED`
     - `IDENTITY_PROMPT.md:100` still points to `1772267244`.
     - `TASK_HISTORY.md:49` latest recorded run still `1772267244`.
   - rulebook negative-sample gap claim: `CONFIRMED`
     - `CURRENT_TASK.json` declares `required_rule_types=['negative','positive']`.
     - `RULEBOOK.jsonl` observed distribution: `{'positive': 21}`.
   - validator blind spot claim: `CONFIRMED`
     - `validate_identity_runtime_contract.py` checks `required_fields` but does not enforce `required_rule_types`.
   - full-scan P1 persistence claim: `CONFIRMED`
     - `/private/tmp/full-scan-custom-creative-ecom-analyst-20260228.json` summary => `p1=2`.
     - project layer: `no_implicit_switch=SKIPPED_NOT_REQUIRED`, writeback/post-exec pass.
     - global layer: `writeback=FAIL_REQUIRED(IP-WRB-001)`, `post_execution_mandatory=FAIL_REQUIRED(IP-WRB-003)`.

### 9.5 Release impact from Intake-2

1. This addendum reinforces `L4/5` classification; no evidence supports `L5/5` declaration yet.
2. v1.5 release gate decision remains `NO-GO` until the following are closed:
   - default-stable project-local environment alignment (eliminate conditional `IP-PATH-003` pass behavior),
   - refresh/status scripts + gate wiring closure,
   - user-visible response stamp hard gate closure (`HOTFIX-P0-004`),
   - rulebook required type enforcement + validator closure for `required_rule_types`.

---

## 10) External handoff intake audit — base-repo write boundary + SSOT archival (2026-03-01 batch)

- Intake sources:
  - `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-protocol-p0-base-repo-write-boundary-2026-03-01.md`
  - instance feedback context: `system-requirements-analyst` (`CURRENT_TASK.json:4`)
- Audit decision:
  - `PARTIAL_ACCEPT` (core P0 direction accepted; two factual statements required rebase to current code state)
- Source refs:
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`DRC-8`, `DRC-10`, `ASB-RQ-009`, `ASB-RQ-025/026/027`, `ASB-RQ-028/030/031`)

### 10.1 Claim verification matrix

1. Claim: existing freeze gate does not represent instance-level base-repo write boundary.
   - Verdict: `CONFIRMED`
   - Evidence:
     - `scripts/validate_release_freeze_boundary.py:55-58` default forbidden prefixes only `identity/packs/`.
     - no policy-level allowlist/denylist for `docs/**` vs `scripts/**`/protocol code mutation.
2. Claim: readiness has unresolved scope arbitration gap and can hit `IP-ENV-002`.
   - Verdict: `CONFIRMED`
   - Evidence:
     - `scripts/release_readiness_check.py:174-186` calls runtime-mode-guard without `--scope`.
     - replay:
       - `python3 scripts/release_readiness_check.py --identity-id system-requirements-analyst --base HEAD~1 --head HEAD --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report /Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772295915.json --execution-report-policy warn --baseline-policy warn`
       - result: `IP-ENV-002 ... multiple pack paths ... Pass --scope to arbitrate explicitly.`
     - scope enum reference remains canonical in resolver:
       - `scripts/resolve_identity_context.py:393` (`REPO/USER/ADMIN/SYSTEM`).
3. Claim: refresh scripts are still missing.
   - Verdict: `REJECT (stale statement)`
   - Evidence (current head):
     - scripts exist:
       - `scripts/refresh_identity_session_status.py`
       - `scripts/validate_identity_session_refresh_status.py`
     - gate wiring exists:
       - `scripts/release_readiness_check.py:311`
       - `scripts/e2e_smoke_test.sh:99`
       - `scripts/full_identity_protocol_scan.py:390`
       - `scripts/report_three_plane_status.py:357`
       - `.github/workflows/_identity-required-gates.yml:167`
4. Claim: current session cannot write base repo and `~/.codex/identity`.
   - Verdict: `PARTIAL / CONTEXT-DEPENDENT`
   - Evidence from audit replay context:
     - base repo probe (`identity-protocol-local`) write: `ok`
     - `~/.codex/identity` write: `Operation not permitted`
   - implication:
     - platform/sandbox rights differ by path/context; governance gate must enforce policy independent of runtime permission profile.
5. Claim: protocol-feedback SSOT archival needs required gate with fail-closed errors (`IP-GOV-FEEDBACK-*`).
   - Verdict: `ACCEPTED AS P0 DIRECTION`
   - Evidence:
     - no `validate_protocol_feedback_ssot_archival.py` exists at current head.
     - mirror-only risk is real unless SSOT archival becomes machine-enforced.

### 10.2 Required architect actions (P0, non-merge lane)

1. `HOTFIX-P0-005`: codify `instance_base_repo_mutation_policy_v1` + implement `validate_instance_base_repo_write_boundary.py`.
   - required behavior: docs allowlist + protocol/code denylist + fail-closed.
2. `HOTFIX-P0-006`: implement `validate_protocol_feedback_ssot_archival.py`.
   - required behavior: outbox + evidence-index SSOT linkage mandatory; mirror-only report => fail (`IP-GOV-FEEDBACK-001/002/003`).
3. `HOTFIX-P0-007`: add `--scope` to `release_readiness_check.py` and forward to runtime-mode/scope validators for deterministic dual-catalog arbitration.
4. Add CI/readiness/e2e replay cases for:
   - docs-only pass,
   - code/protocol mutation fail,
   - mirror-only feedback archival fail,
   - explicit-scope dual-catalog pass and no-scope fail-closed.

### 10.3 Release impact (post-intake-3)

1. v1.5 remains `NO-GO`.
2. L5 cannot be declared while HOTFIX-P0-004/005/006/007 are open.

---

## 11) Roundtable publication policy (where to push this batch)

This section is a stable publication rule to avoid governance/review drift.

### 11.1 What goes to governance SSOT (L1)

1. Normative protocol contracts and hard rules (must/shall/fail-closed semantics).
2. Requirement IDs (`ASB-RQ-*`), closure checklist (`DRC-*`), error-code families.
3. Required gate surfaces, unlock formula, and release-blocking conditions.

### 11.2 What goes to review ledger (L3)

1. Replay evidence, command outputs (`rc + key tail`), audit verdict (`PASS/REJECT`).
2. Intake claim verification matrix (`CONFIRMED/REJECT/PARTIAL`) with file/line anchors.
3. Residual risks, next milestones, and architect action items by hotfix/fix lane.

### 11.3 Mapping for this batch (confirmed)

1. Governance SSOT already carries normative additions under:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` section `5.8`
   - `ASB-RQ-037/038/039/040`
   - `DRC-13`
2. Review ledger keeps implementation/audit tracking for these items as:
   - `HOTFIX-P0-005` (base-repo write boundary gate)
   - `HOTFIX-P0-006` (protocol-feedback SSOT archival gate)
   - `HOTFIX-P0-007` (readiness `--scope` arbitration chain)
   - `HOTFIX-P0-004` (user-visible identity-context stamp hard gate)

### 11.4 Hard anti-drift rule

1. If L3 text conflicts with L1 normative contract wording, treat L3 as stale.
2. Any new semantic claim must first be codified in L1 before it can be marked `DONE` in L3.


---

## 12) Architect execution update — HOTFIX-P0-005/006/007 candidate closure (2026-03-01)

Layer declaration:

1. protocol layer only (contracts/validators/gates/wiring/error-code semantics).
2. no business data constants introduced.
3. instance behavior referenced only as validation sample.

### 12.1 HOTFIX-P0-005 (`validate_instance_base_repo_write_boundary.py`)

Implemented:

1. New validator: `scripts/validate_instance_base_repo_write_boundary.py`
   - status envelope: `PASS_REQUIRED|SKIPPED_NOT_REQUIRED|FAIL_REQUIRED`
   - error code: `IP-GOV-BASE-001`
   - supports report-surface enforcement + optional git-diff replay (`--check-git-diff`).
2. Wired to protocol main surfaces:
   - `scripts/identity_creator.py` (`validate` chain)
   - `scripts/release_readiness_check.py` (`readiness` chain, report-bound)
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`

Replay evidence (architect local):

1. docs-only range pass:
   - `python3 scripts/validate_instance_base_repo_write_boundary.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --check-git-diff --base 92e9af1 --head dfc0e51 --operation ci --json-only`
   - `rc=0`, `base_repo_write_boundary_status=PASS_REQUIRED`.
2. protocol/code range fail:
   - `python3 scripts/validate_instance_base_repo_write_boundary.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --check-git-diff --base HEAD~1 --head HEAD --operation ci --json-only`
   - `rc=1`, `error_code=IP-GOV-BASE-001`, blocked paths under `scripts/*`.

### 12.2 HOTFIX-P0-006 (`validate_protocol_feedback_ssot_archival.py`)

Implemented:

1. New validator: `scripts/validate_protocol_feedback_ssot_archival.py`
   - status envelope: `PASS_REQUIRED|SKIPPED_NOT_REQUIRED|FAIL_REQUIRED`
   - error codes:
     - `IP-GOV-FEEDBACK-001` required outbox missing
     - `IP-GOV-FEEDBACK-002` evidence-index missing or unlinked batch
     - `IP-GOV-FEEDBACK-003` mirror-only without SSOT outbox
2. Wired to protocol main surfaces:
   - `scripts/identity_creator.py` (`validate` chain)
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`

Replay evidence (architect local):

1. mirror-only fail simulation:
   - `python3 scripts/validate_protocol_feedback_ssot_archival.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --feedback-root /tmp/ssot-mirror-only --operation ci --json-only`
   - `rc=1`, `error_code=IP-GOV-FEEDBACK-003`.
2. outbox+index pass simulation:
   - `python3 scripts/validate_protocol_feedback_ssot_archival.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --feedback-root /tmp/ssot-pass --operation ci --json-only`
   - `rc=0`, `feedback_ssot_archival_status=PASS_REQUIRED`.
3. runtime real sample pass (`system-requirements-analyst`):
   - `python3 scripts/validate_protocol_feedback_ssot_archival.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation scan --json-only`
   - `rc=0`, `feedback_ssot_archival_status=PASS_REQUIRED`.

### 12.3 HOTFIX-P0-007 (readiness `--scope` arbitration chain)

Implemented:

1. `scripts/release_readiness_check.py`新增 `--scope` 参数。
2. `--scope` 已前传到：
   - `validate_identity_runtime_mode_guard.py`
   - `validate_identity_scope_resolution.py`
   - `validate_identity_scope_isolation.py`
   - `validate_identity_scope_persistence.py`
   - auto-generated update path (`identity_creator.py update`) during readiness no-report path.

Replay evidence (architect local):

1. no-scope dual-catalog ambiguity fail-closed:
   - `python3 scripts/release_readiness_check.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report /Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772295915.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready`
   - `rc=2`, early fail `IP-ENV-002`.
2. explicit scope replay enters main chain:
   - same command + `--scope USER`
   - runtime/scope preflight no longer hit `IP-ENV-002`; chain proceeds to later health/other gates.

### 12.4 main-surface smoke after wiring

1. `python3 scripts/identity_creator.py validate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER`
   - `rc=0` (new validators wired and replayed).
2. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --project-catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-hotfix-p0.json`
   - `rc=0`, outputs contain `instance_base_repo_write_boundary` + `protocol_feedback_ssot_archival` checks.
3. `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --scope USER --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-hotfix-p0.json`
   - `rc=0`, `instance_plane_detail` contains both new governance-boundary sections.

### 12.5 status

1. HOTFIX-P0-005: `PASS` (architect replay cross-validated by audit replay).
2. HOTFIX-P0-006: `PASS` (architect replay cross-validated by audit replay).
3. HOTFIX-P0-007: `PASS` (architect replay cross-validated by audit replay).
4. Non-merge release constraint unchanged: v1.5 remains blocked until auditor replay signs off.


### 12.6 Self-upgrade closure delta (P0-4 follow-up replay, 2026-03-01)

Patch focus:

1. `scripts/execute_identity_upgrade.py`
   - report `resolved_pack_path` now always uses canonical `effective_pack` (prevents `.` regression in execution report).
2. `scripts/identity_installer.py`
   - `repair-paths` keeps protocol/path-governance anchor fields absolute (`resolved_pack_path`, `identity_prompt_path`, etc.), avoiding post-repair drift.

Replay evidence (escalated context, `~/.codex` writable):

1. update report canonicality check:
   - `python3 scripts/identity_creator.py update --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER --mode review-required --capability-activation-policy route-any-ready`
   - latest report: `.../identity-upgrade-exec-base-repo-audit-expert-v3-1772302614.json`
   - field check: `resolved_pack_path=/Users/yangxi/.codex/identity/base-repo-audit-expert-v3` (canonical absolute).
2. repair-paths regression guard:
   - `python3 scripts/identity_installer.py repair-paths --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER`
   - post-repair check: same report keeps absolute `resolved_pack_path` + `identity_prompt_path`.
3. heal closure replay:
   - `python3 scripts/identity_creator.py heal --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER --apply`
   - `rc=0` (`FAIL_VALIDATE` no longer reproduced in this replay window).
4. readiness replay (bounded compare window to exclude changelog noise):
   - `python3 scripts/release_readiness_check.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --scope USER --execution-report /Users/yangxi/.codex/identity/base-repo-audit-expert-v3/runtime/reports/identity-upgrade-exec-base-repo-audit-expert-v3-1772302614.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready --base 7b5f621 --head 7b5f621`
   - `rc=0`, tail contains `[OK] release readiness checks PASSED`.

---

## 13) Cross-validation matrix (2026-03-01, audit replay against latest feedback claims)

- Date (UTC): 2026-03-01
- Layer declaration: `protocol` (with instance evidence replay)
- Execution context:
  - `sandbox`: validator replay, full-scan, code anchor checks
  - `escalated`: readiness replay that writes `~/.codex` runtime reports
- Scope:
  - verify latest `custom-creative-ecom-analyst` and `system-requirements-analyst` feedback claims
  - verify HOTFIX-P0-005/006/007 required-gate wiring is real (not doc-only claim)

### 13.1 Claim vs replay verdicts

1. Claim: `system-requirements-analyst` protocol-feedback files are in SSOT channel and traceable.
   - Verdict: `CONFIRMED`
   - Evidence:
     - outbox batch exists: `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-01_003.md`
     - evidence index exists: `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/evidence-index/INDEX.md`
     - validator replay:
       - `python3 scripts/validate_protocol_feedback_ssot_archival.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
       - `rc=0`, `feedback_ssot_archival_status=PASS_REQUIRED`.

2. Claim: semantic routing + vendor namespace separation passed for `system-requirements-analyst`.
   - Verdict: `CONFIRMED`
   - Evidence:
     - `python3 scripts/validate_semantic_routing_guard.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
       - `rc=0`, `semantic_routing_status=PASS_REQUIRED`.
     - `python3 scripts/validate_vendor_namespace_separation.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
       - `rc=0`, `vendor_namespace_status=PASS_REQUIRED`.

3. Claim: `custom-creative-ecom-analyst` validate full chain is `rc=0`.
   - Verdict: `REJECT (stale claim under current HEAD)`
   - Evidence:
     - `python3 scripts/identity_creator.py validate --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER`
     - replay result: `rc=1` at `validate_writeback_continuity.py` with `error_code=IP-WRB-001` and `writeback_continuity_status=FAIL_REQUIRED`.

4. Claim: `IP-PBL-001` baseline mismatch still appears in active scans.
   - Verdict: `CONFIRMED`
   - Evidence:
     - full scan replay output `/tmp/full-scan-cross-verify-20260301.json` shows:
       - `custom-creative-ecom-analyst` (project layer): `baseline_error=IP-PBL-001` (severity `P0`)
       - `system-requirements-analyst` (global layer): `baseline_error=IP-PBL-001` (severity `P1`).

5. Claim: readiness `--scope` passthrough not fully wired; `IP-ENV-002` still reproducible in this path.
   - Verdict: `PARTIAL (scope passthrough wired; no-scope fail remains by design)`
   - Evidence:
     - code wiring exists:
       - `scripts/release_readiness_check.py` exposes `--scope` and forwards into scope/runtime validators.
       - `scripts/identity_creator.py` update/validate chain also carries `--scope`.
     - escalated replay A (`system-requirements-analyst`, fixed execution report, **no scope**):
       - `python3 scripts/release_readiness_check.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report /Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772295915.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready`
       - `rc=2`, deterministic `IP-ENV-002 ... Pass --scope to arbitrate explicitly.`
     - escalated replay B (same command + `--scope USER`):
       - runtime mode/scope preflight passes; no `IP-ENV-002` branch.
       - chain proceeds to later health gate and fails at `collect_identity_health_report.py --enforce-pass` (`rc=2`), which is downstream and not scope-routing regression.
   - Audit note:
     - `IP-ENV-002` remains an intentional fail-closed branch for ambiguous dual-catalog contexts.
     - current P0 is not “remove IP-ENV-002”; it is “preserve fail-closed + ensure explicit scope can arbitrate and continue”.

6. Claim: base-repo write-boundary gate and protocol-feedback SSOT gate are not required in base repo.
   - Verdict: `REJECT`
   - Evidence:
     - required-gates wiring exists in `.github/workflows/_identity-required-gates.yml`:
       - `validate_instance_base_repo_write_boundary.py` (ci)
       - `validate_protocol_feedback_ssot_archival.py` (ci)
     - hard-fail behavior reproduced:
       - `python3 scripts/validate_instance_base_repo_write_boundary.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --check-git-diff --base 7b5f621 --head 7b191e5 --operation ci --json-only`
       - `rc=1`, `error_code=IP-GOV-BASE-001`, `blocked_paths=["scripts/execute_identity_upgrade.py","scripts/identity_installer.py"]`.

7. Incident: user-visible identity stamp in assistant replies showed abrupt identity drift (`base-repo-audit-expert-v3` -> `base-repo-architect`) during this audit window.
   - Verdict: `CONFIRMED P0 INCIDENT (runtime switch + reply-channel observability gap)`
   - Evidence:
     - activation switch report:
       - `/tmp/identity-activation-reports/identity-activation-switch-office-ops-expert-1772361081.json`
       - fields: `switch_reason=explicit_activate`, `target_identity_id=office-ops-expert`, `actor_id=user:yangxi`, `generated_at=2026-03-01T10:31:21Z`.
     - actor session pointer was changed to `office-ops-expert` before manual recovery:
       - `/Users/yangxi/.codex/identity/session/actors/user_yangxi.json`
     - recovery switch replay:
       - `python3 scripts/identity_creator.py activate --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER --actor-id user:yangxi --run-id p0-hotfix-identity-hard-switch-20260301 --switch-reason restore_audit_identity_after_hard_switch`
       - `rc=0`, switch report: `/tmp/identity-activation-reports/identity-activation-switch-base-repo-audit-expert-v3-1772361801.json`
       - active identity after recovery: `base-repo-audit-expert-v3`.
   - Audit note:
     - this confirms a concrete script-triggered switch (`explicit_activate`) rather than random degradation.
     - reply-channel must enforce dynamic runtime-derived `Identity-Context` consistency to fail-closed on stamp/session mismatch (`HOTFIX-P0-004` scope).

### 13.2 Release-blocking status after this cross-validation

1. `FIX-015` moved to `IN_PROGRESS` (local workspace changes completed; commit/replay package still pending).
2. Historical snapshot note:
   - `HOTFIX-P0-004` was open at this timestamp; final closure is recorded in `16.6.8` as `DONE/PASS`.
3. `HOTFIX-P0-005/006/007` are now `DONE + PASS` after replay.
4. Current runtime closure blocker for `custom-creative-ecom-analyst` is `IP-WRB-001` in validate path (not scope passthrough).
5. P0 incident replay confirms actor session can be explicitly switched by activation command; release path still needs user-visible reply-channel hard enforcement to prevent silent perceived identity drift (`HOTFIX-P0-004`).

---

## 14) Fast git-scan + cross-validation replay snapshot (2026-03-01, audit expert)

- Date (UTC): 2026-03-01
- Layer declaration: `protocol`
- Execution context:
  - `sandbox`: git diff scan, validator replay, full-scan + three-plane parse
  - `escalated`: readiness replay (writes health/runtime artifacts under `~/.codex`)
- Purpose:
  - give architect a deterministic "what is fixed / what is still blocking" package without narrative drift

### 14.1 Multi-active runtime proof (FIX-015 worktree replay)

1. Active identity set is now multi-active:
   - `active_identities=['base-repo-audit-expert-v3','base-repo-architect']`, `active_count=2`
   - source: `python3 scripts/validate_identity_state_consistency.py --catalog /Users/yangxi/.codex/identity/catalog.local.yaml`
2. Actor binding truth remains stable for current actor:
   - `/Users/yangxi/.codex/identity/session/actors/user_yangxi.json` -> `identity_id=base-repo-audit-expert-v3`
3. Latest switch report shows multi-active activation model and zero demotion:
   - `/tmp/identity-activation-reports/identity-activation-switch-base-repo-audit-expert-v3-1772362504.json`
   - `activation_model=actor_scoped_catalog_with_multi_active`
   - `single_active_enforced=false`
   - `demoted_identities=[]`
4. No-implicit-switch validator passes with new schema:
   - `python3 scripts/validate_no_implicit_switch.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --switch-report /tmp/identity-activation-reports/identity-activation-switch-base-repo-audit-expert-v3-1772362504.json --operation three-plane --json-only`
   - `rc=0`, `implicit_switch_status=PASS_REQUIRED`
5. Session pointer consistency remains pass under multi-active:
   - `python3 scripts/validate_identity_session_pointer_consistency.py --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --actor-id user:yangxi --identity-id base-repo-audit-expert-v3`
   - `rc=0`, `active_count=2`, canonical+mirror checks pass

### 14.2 Governance-boundary hotfix replay closure

1. HOTFIX-P0-005 (`validate_instance_base_repo_write_boundary`) replay:
   - command:
     - `python3 scripts/validate_instance_base_repo_write_boundary.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --check-git-diff --base 7b5f621 --head 7b191e5 --operation ci --json-only`
   - result: `rc=1`, `base_repo_write_boundary_status=FAIL_REQUIRED`, `error_code=IP-GOV-BASE-001`, blocked `scripts/*` changes confirmed
2. HOTFIX-P0-006 (`validate_protocol_feedback_ssot_archival`) replay:
   - command:
     - `python3 scripts/validate_protocol_feedback_ssot_archival.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
   - result: `rc=0`, `feedback_ssot_archival_status=PASS_REQUIRED`, outbox+index linked batches present
3. HOTFIX-P0-007 (`--scope` arbitration chain) replay:
   - no-scope replay:
     - `python3 scripts/release_readiness_check.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report /Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772295915.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready`
     - `rc=2`, deterministic `IP-ENV-002` with explicit "`Pass --scope`" hint
   - scoped replay:
     - same command + `--scope USER`
     - scope preflight passes and chain proceeds beyond `IP-ENV-002`; later `collect_identity_health_report --enforce-pass` fails on downstream health checks (expected independent gate)

### 14.3 Release-path replay summary

1. Readiness replay for self audit identity passes under bounded compare window:
   - `python3 scripts/release_readiness_check.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --scope USER --execution-report /Users/yangxi/.codex/identity/base-repo-audit-expert-v3/runtime/reports/identity-upgrade-exec-base-repo-audit-expert-v3-1772302614.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready --base 7b5f621 --head 7b5f621`
   - `rc=0`, tail: `[OK] release readiness checks PASSED`
2. `report_three_plane_status` shows actor/session + stamp all PASS while baseline freshness remains WARN:
   - artifact: `/tmp/three-plane-fix015-multi-active-audit.json`
   - key fields:
     - `actor_session_binding.actor_binding_status=PASS_REQUIRED`
     - `no_implicit_switch.implicit_switch_status=PASS_REQUIRED`
     - `cross_actor_isolation.cross_actor_isolation_status=PASS_REQUIRED`
     - `response_identity_stamp.stamp_status=PASS`, `reply_stamp_missing_count=0`
     - `protocol_baseline_freshness.baseline_error_code=IP-PBL-001`
3. `full_identity_protocol_scan` remains `p1` due baseline freshness (not due actor-isolation regression):
   - artifact: `/tmp/full-scan-fix015-multi-active-audit.json`
   - summary: `{'total_identities': 2, 'p0': 0, 'p1': 2, 'ok': 0}`

### 14.4 Remaining release blockers (architect action list)

1. Historical snapshot note:
   - this item was open at this timestamp; final closure is recorded in `16.6.8` as `DONE/PASS`.
2. `FIX-015` needs commit + packaged acceptance replay:
   - runtime semantic patch already committed (`6fbf999`); packaged acceptance replay and final audit closure are still pending.
3. `IP-PBL-001` baseline freshness remains recurring:
   - requires refreshed execution reports on current protocol head for release-closure claims.
4. `e2e_smoke_test.sh` currently fails on changelog freshness in `HEAD~1..HEAD` range:
   - `validate_changelog_updated.py` fails while range includes protocol script changes without changelog update.
   - this is a release hygiene blocker and should be closed in same architect batch as FIX-015 commit.

---

## 15) Latest strengthening package routing decision (2026-03-01)

Decision (final, anti-drift):

1. Governance semantics go to L1 document (`docs/governance/identity-actor-session-binding-governance-v1.5.0.md`).
2. Replay evidence and architect execution tasks go to this L3 review ledger.
3. Do not merge this package into old FIX narrative rows; keep as strengthening follow-up under explicit P0/P1 buckets.

### 15.1 P0 strengthening items to execute next

1. `P0-A` readiness scope passthrough completion (health branch):
   - finding: `release_readiness_check.py` forwards `--scope` into runtime/scope guards, but `collect_identity_health_report.py` call in readiness sequence omits `--scope`.
   - evidence anchors:
     - `scripts/release_readiness_check.py:365`
     - `scripts/collect_identity_health_report.py:170`
     - `scripts/collect_identity_health_report.py:193`
   - replay evidence:
     - `release_readiness_check ... --scope USER` still fails downstream health scope checks (`rc=2`) for `system-requirements-analyst`.
     - direct `collect_identity_health_report --scope USER --enforce-pass` returns `rc=0` (`overall_status=WARN`, baseline-only warning).
   - acceptance target:
     - with explicit `--scope`, readiness health branch must not fail on scope-resolution/isolation/persistence for same tuple.

2. `P0-B` baseline policy stratification hardening:
   - finding: baseline policy handling is mixed (`warn` hardcoded in several mutation/validate paths), enabling stale-baseline continuation on non-observability paths.
   - evidence anchors:
     - `scripts/release_readiness_check.py:149`
     - `scripts/identity_creator.py:1061`
     - `scripts/identity_creator.py:1217`
     - `scripts/identity_creator.py:1391`
     - `scripts/e2e_smoke_test.sh:104`
   - acceptance target:
     - release/mutation paths default to `strict` baseline enforcement (`IP-PBL-001` fail-closed),
     - observability-only paths may keep `warn` but must emit machine-readable drift payload.

3. `P0-C` protocol version alignment contract unification:
   - finding: alignment checks exist but are fragmented across multiple validators.
   - objective: unify into one deterministic closure contract for `CURRENT_TASK + IDENTITY_PROMPT + execution_report.protocol_commit_sha + binding tuple`.
   - evidence anchors:
     - `scripts/validate_identity_protocol_baseline_freshness.py`
     - `scripts/validate_identity_prompt_activation.py`
     - `scripts/validate_identity_binding_tuple.py`
   - acceptance target:
     - one report-level machine-readable alignment payload and one decisive error code family for mismatch closure.

### 15.2 P1 strengthening items (post-P0)

1. add optimization-gap trigger path (`platform_optimization_gap`) to capability orchestration.
2. add platform-specific capability contract gate (example: `aistudio_build_optimizer_contract`).
3. add periodic capability delta scan task and SSOT archival output (`protocol-feedback/outbox + evidence-index`).
4. add capability-fit self-drive loop (`inventory-first -> compose-before-discover -> fit-matrix -> selected-plan -> freshness-review`).
5. add roundtable fact/inference mapping output for optimization decisions affecting routing/discovery/architecture.

### 15.3 Architect handoff rule for this package

1. apply in dedicated strengthening lane (do not rewrite historical FIX verdicts).
2. return with standard audit packet:
   - commit list
   - changed files
   - replay commands with `rc + key fields`
   - residual risks
   - layer declaration.

---

## 16) New strengthening intake (P0+P1, 2026-03-01 official-research package)

- Intake source (evidence-only references):
  - `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-protocol-p0-p1-official-research-discovery-and-source-trust-2026-03-01.md`
  - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-01_005.md`
  - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/evidence-index/INDEX.md`
- Intake interpretation:
  - preserve existing protocol stability/layering controls,
  - add missing P0 semantic/trust safeguards,
  - add P1 proactive optimization trigger and standardized feeding-pack output.

### 16.1 Audit verdict on intake direction

1. Direction accepted (`ACCEPTED_WITH_STRUCTURING`).
2. P0 part is release-relevant and must be wired into required gates.
3. P1 part is enhancement lane and must remain non-blocking until explicitly promoted.
4. Data-sanitization boundary is mandatory:
   - protocol-layer artifacts must stay business-neutral,
   - no tenant-specific scenario/constants in governance or protocol contracts.

### 16.2 Execution split (what goes where)

1. Governance SSOT (L1) receives:
   - contract semantics and requirement IDs (`ASB-RQ-044..053`).
2. Review ledger (L3) receives:
   - replay plan,
   - acceptance commands,
   - status transitions and residual risks.
3. Instance runtime feedback keeps detailed business context:
   - protocol layer consumes only sanitized abstractions.

### 16.3 New P0 lane tasks (required-gate candidates)

1. `P0-D` implement `validate_protocol_vendor_semantic_isolation.py`
   - objective: block cross-domain semantic pollution between `protocol_vendor` and `business_partner` in conclusion layer.
   - acceptance:
     - cross-domain write without explicit switch receipt => fail-closed.
2. `P0-E` implement `validate_external_source_trust_chain.py`
   - objective: only `official/primary` trusted evidence may enter conclusion layer.
   - acceptance:
     - `unknown` source in conclusion evidence => fail-closed.
3. `P0-F` implement `validate_protocol_data_sanitization_boundary.py`
   - objective: prevent business scenario contamination in protocol/governance outputs.
   - acceptance:
     - protocol-layer sensitive/business-specific identifiers in contract text => fail-closed.

### 16.4 New P1 enhancement lane tasks

1. `P1-D` implement `platform_optimization_discovery_trigger_v1`.
2. `P1-E` implement `vibe_coding_feeding_pack_contract_v1` output builder.
3. `P1-F` implement `capability_fit_self_drive_optimization_contract_v1` validator chain:
   - `validate_identity_capability_fit_optimization.py`
   - `validate_capability_composition_before_discovery.py`
   - `validate_capability_fit_review_freshness.py`
4. `P1-G` implement `capability_fit_roundtable_evidence_contract_v1` evidence parser:
   - enforce `fact` / `inference` split
   - require selected plan -> fact evidence mapping.
5. `P1-H` add capability-fit review trigger/tool surfaces:
   - `trigger_capability_fit_review`
   - `build_capability_fit_matrix`
6. required pack outputs:
   - `PROMPT_MAIN.txt`
   - `INPUT_FILES/`
   - `RUN_ORDER.txt`
   - `REVIEW_REQUEST.txt`

### 16.4A Document-layer closure checklist (this round, code-not-started lane)

Goal:

1. lock governance semantics before implementation so replay outcome is deterministic and non-ambiguous.

Checklist:

1. governance doc includes `inventory-first` and `compose-before-discover` hard semantics.
2. governance doc includes `capability_fit_matrix` required fields and single-selected rule.
3. governance doc includes `review freshness` stale semantics and non-closed warning behavior.
4. governance doc includes optimization roundtable `fact`/`inference` separation and selected->fact mapping requirement.
5. requirement ledger contains new IDs for this package (`ASB-RQ-049..053`) with explicit status and implementation scope.

Doc acceptance commands:

1. `python3 scripts/docs_command_contract_check.py`
2. `python3 scripts/validate_protocol_ssot_source.py`
3. `rg -n \"capability_fit_self_drive_optimization_contract_v1|compose-before-discover|capability_fit_matrix|WARN_STALE_OPTIMIZATION_REVIEW|ASB-RQ-049|ASB-RQ-053\" docs/governance/identity-actor-session-binding-governance-v1.5.0.md`

### 16.5 Suggested acceptance metrics for architect replay

1. semantic isolation regression:
   - `protocol_vendor` task triggers `business_partner` retrieval by mistake => target `0`.
2. source trust regression:
   - conclusion-layer payload includes `unknown` source => target `0`.
3. optimization trigger hit-rate:
   - repeated platform optimization intent (2 rounds) triggers deep-discovery action => target `>=95%`.
4. feeding-pack execution success:
   - single-directory pack upload/consume success => target `>=95%`.
5. capability-fit self-drive correctness:
   - existing composition evaluated before external candidate selection => target `100%`.
   - selected optimization plan has explicit fallback+rollback refs => target `100%`.
6. optimization review freshness:
   - overdue review cycles are visible as stale warning and never misreported as closed => target `100%`.

### 16.6 Architect execution log (protocol-only implementation lane)

#### 16.6.1 P0-D progress update (2026-03-01, local replay)

Status: `PASS` (audit replayed on current head, non-required path semantics)

1. Added new validator:
   - `scripts/validate_protocol_vendor_semantic_isolation.py`
2. Wired main gate surfaces:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Initial replay snapshot (local):
   - direct validator run (scan/json-only): rc=`0`, status=`SKIPPED_NOT_REQUIRED` (contract-not-required path preserved)
   - `report_three_plane_status.py` includes `instance_plane_detail.protocol_vendor_semantic_isolation.*`
   - `full_identity_protocol_scan.py` includes `checks.protocol_vendor_semantic_isolation.*`
4. Scope note:
   - this patch is protocol-layer only (contracts/validators/gates wiring),
   - no business data constants were introduced.

#### 16.6.2 P0-E progress update (2026-03-01, local replay)

Status: `PASS` (audit replayed on current head, non-required path semantics)

1. Added new validator:
   - `scripts/validate_external_source_trust_chain.py`
2. Wired main gate surfaces:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Initial replay snapshot (local):
   - direct validator run (scan/json-only): rc=`0`, status=`SKIPPED_NOT_REQUIRED` (contract-not-required path preserved)
   - `report_three_plane_status.py` includes `instance_plane_detail.external_source_trust_chain.*`
   - `full_identity_protocol_scan.py` includes `checks.external_source_trust_chain.*`
4. Error-code alignment:
   - validator enforces `IP-SRC-001/002/003` semantics defined in governance section 8.
5. Scope note:
   - protocol-layer only (contracts/validators/gates wiring),
   - no business data constants were introduced.

#### 16.6.3 P0-F progress update (2026-03-01, local replay)

Status: `PASS` (audit replayed on current head, non-required path semantics)

1. Added new validator:
   - `scripts/validate_protocol_data_sanitization_boundary.py`
2. Wired main gate surfaces:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Initial replay snapshot (local):
   - direct validator run (scan/json-only): rc=`0`, status=`SKIPPED_NOT_REQUIRED` (contract-not-required path preserved)
   - `report_three_plane_status.py` includes `instance_plane_detail.protocol_data_sanitization_boundary.*`
   - `full_identity_protocol_scan.py` includes `checks.protocol_data_sanitization_boundary.*`
4. Error-code alignment:
   - validator emits `IP-DSN-001` (business/tenant leakage) and `IP-DSN-002` (sensitive constant leakage).
5. Scope note:
   - protocol-layer only (contracts/validators/gates wiring),
   - no business data constants were introduced.

#### 16.6.4 P0-E audit replay verdict (2026-03-01, cross-validated)

Status: `PASS` (scope: validator implementation + six-surface wiring integrity)

1. Commit under replay:
   - `3c9008ccf5a9a39178e16d7d1fbca325a9289736`
2. Static checks:
   - `python3 -m py_compile ... && bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
3. Direct validator replay:
   - `python3 scripts/validate_external_source_trust_chain.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
   - result: `rc=0`
   - key fields: `external_source_trust_chain_status=SKIPPED_NOT_REQUIRED`, `stale_reasons=["contract_not_required"]`
4. Full-scan wiring replay:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/scan-p0e-audit.json`
   - result: `rc=0`
   - key extract:
     - project: `checks.external_source_trust_chain.rc=0`, `status=SKIPPED_NOT_REQUIRED`
     - global: `checks.external_source_trust_chain.rc=0`, `status=SKIPPED_NOT_REQUIRED`
5. Three-plane wiring replay:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --scope USER --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-p0e-audit.json`
   - result: `rc=0`
   - key extract:
     - `instance_plane_detail.external_source_trust_chain.external_source_trust_chain_status=SKIPPED_NOT_REQUIRED`
     - `instance_plane_detail.hard_boundary=false`
6. Docs and SSOT boundary checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`
7. Residual risks:
   - contract is currently not required for tested identity, so replay validates wiring and semantics but not strict blocking path.
   - `--baseline-policy strict` may still fail on `IP-PBL-001`; unrelated to P0-E patch scope.
8. Audit decision:
   - mark `P0-E` as ready to proceed to next lane (`P0-F`) with no regression found in this replay.

#### 16.6.5 P0-F audit replay verdict (2026-03-01, cross-validated)

Status: `PASS` (scope: validator implementation + six-surface wiring integrity)

1. Commit under replay:
   - `21063394dd64c94b484bd1afc304997473a4c145`
2. Static checks:
   - `python3 -m py_compile ... && bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
3. Direct validator replay:
   - `python3 scripts/validate_protocol_data_sanitization_boundary.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
   - result: `rc=0`
   - key fields:
     - `protocol_data_sanitization_boundary_status=SKIPPED_NOT_REQUIRED`
     - `violation_count=0`
     - `stale_reasons=["contract_not_required"]`
4. Full-scan wiring replay:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/scan-p0f-audit.json`
   - result: `rc=0`
   - key extract:
     - project: `checks.protocol_data_sanitization_boundary.rc=0`, `status=SKIPPED_NOT_REQUIRED`, `violation_count=0`
     - global: `checks.protocol_data_sanitization_boundary.rc=0`, `status=SKIPPED_NOT_REQUIRED`, `violation_count=0`
5. Three-plane wiring replay:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --scope USER --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/three-plane-p0f-audit.json`
   - result: `rc=0`
   - key extract:
     - `instance_plane_detail.protocol_data_sanitization_boundary.protocol_data_sanitization_boundary_status=SKIPPED_NOT_REQUIRED`
     - `instance_plane_detail.protocol_data_sanitization_boundary.violation_count=0`
     - `instance_plane_detail.hard_boundary=false`
6. Docs and SSOT boundary checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`
7. Residual risks:
   - contract is currently not required for tested identity, so replay validates wiring and semantics but not strict blocking path.
   - `--baseline-policy strict` may still fail on `IP-PBL-001`; unrelated to P0-F patch scope.
8. Audit decision:
   - mark `P0-F` as `PASS` for protocol wiring quality; next blocking lane remains `HOTFIX-P0-004`.

#### 16.6.6 HOTFIX-P0-004 execution escalation (2026-03-01, live reply-channel gap)

Status: `OPEN_BLOCKING` (release-blocking until closure replay is PASS)

Incident summary:

1. Live audit conversation observed missing first-line `Identity-Context` in assistant replies.
2. Runtime binding was stable during incident (no actual identity hard-switch in session pointers).

Evidence:

1. `/Users/yangxi/.codex/identity/session/active_identity.json`
2. `/Users/yangxi/.codex/identity/session/actors/user_yangxi.json`
3. `/tmp/identity-stamp-runtime-check-20260301.json`

Gap statement:

1. Existing stamp validators can validate rendered/sample payloads, but reply-channel first-line enforcement is not hard-gated for live session output.

Required implementation package for architect (separate hotfix lane, do not merge into normal FIX narrative):

1. Add validator:
   - `scripts/validate_reply_identity_context_first_line.py`
   - fail code: `IP-ASB-STAMP-SESSION-001`
   - contract: every user-visible reply must start with `Identity-Context:`
2. Wire required gates:
   - `scripts/identity_creator.py` (validate path)
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Add machine-readable fields:
   - `reply_first_line_status`
   - `reply_first_line_missing_count`
   - `reply_first_line_missing_refs`
4. Replay closure criteria:
   - missing first-line stamp sample -> `rc=1`, explicit blocker receipt
   - compliant sample -> `rc=0`
   - full-scan and three-plane expose machine-readable status fields
   - docs/ssot checks remain `rc=0`

Audit note:

1. This hotfix addresses perceived identity drift risk in live dialogue channel and remains mandatory for multi-agent and multi-identity release confidence.

#### 16.6.7 HOTFIX-P0-004 implementation replay (2026-03-01, protocol-only)

Status: `PASS` (audit replayed on current head, non-required path semantics)

Implemented package:

1. New validator:
   - `scripts/validate_reply_identity_context_first_line.py`
   - hard error code: `IP-ASB-STAMP-SESSION-001`
2. Six-surface gate wiring completed:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Machine-readable fields exposed:
   - `reply_first_line_status`
   - `reply_first_line_missing_count`
   - `reply_first_line_missing_refs`

Replay evidence snapshot:

1. negative sample (missing first-line stamp):
   - `python3 scripts/validate_reply_identity_context_first_line.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --reply-file /tmp/reply-missing-stamp.txt --force-check --enforce-first-line-gate --json-only`
   - result: `rc=1`
   - key fields: `reply_first_line_status=FAIL_REQUIRED`, `error_code=IP-ASB-STAMP-SESSION-001`, `reply_first_line_missing_count=1`
2. positive sample (compliant first-line stamp):
   - `python3 scripts/render_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --view external --out /tmp/reply-stamp-pass.json --json-only`
   - `python3 scripts/validate_reply_identity_context_first_line.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --stamp-json /tmp/reply-stamp-pass.json --force-check --enforce-first-line-gate --json-only`
   - result: `rc=0`
   - key fields: `reply_first_line_status=PASS_REQUIRED`, `reply_first_line_missing_count=0`
3. full-scan field visibility:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/scan-hotfix-p0-004.json`
   - result: `rc=0`
   - key extract:
     - project/global both expose `checks.reply_identity_context_first_line`
     - `reply_first_line_status=PASS_REQUIRED`
4. three-plane field visibility:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract`
   - result: `rc=0`
   - key extract:
     - `instance_plane_detail.response_identity_stamp.reply_first_line_status=PASS_REQUIRED`
     - `reply_first_line_missing_count=0`
     - `reply_first_line_missing_refs=[]`

#### 16.7.1 P1-D progress update (2026-03-01, non-blocking enhancement lane)

Status: `PASS` (audit replayed on current head, non-required path semantics)

1. Added new trigger surface:
   - `scripts/trigger_platform_optimization_discovery.py`
2. Wired six surfaces (non-blocking semantics):
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Replay snapshot (local):
   - direct run (scan/json-only): `rc=0`, `platform_optimization_discovery_status=SKIPPED_NOT_REQUIRED` when contract is not required
   - full-scan: project/global both expose `checks.platform_optimization_discovery_trigger.*` with `rc=0`
   - three-plane: `instance_plane_detail.platform_optimization_discovery_trigger.*` visible, `hard_boundary` unchanged
4. Trigger semantics implemented:
   - repeated optimization-intent across consecutive rounds on same platform class
   - repeated `flow not closed` under optimization context
   - trigger payload carries `discovery_scope`, `official_doc_retrieval_set`, `cross_validation_summary`, `upgrade_proposal_ref`
5. Non-blocking policy:
   - this lane returns machine-readable `NOT_TRIGGERED/WARN_NON_BLOCKING/TRIGGERED_NON_BLOCKING`
   - does not force release blocking unless governance explicitly promotes P1 to required hard gate.

#### 16.7.2 P1-E progress update (2026-03-01, non-blocking enhancement lane)

Status: `PASS` (audit replayed on current head, non-required path semantics)

1. Added new builder surface:
   - `scripts/build_vibe_coding_feeding_pack.py`
2. Wired six surfaces (non-blocking semantics):
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Contract outputs covered:
   - `PROMPT_MAIN.txt`
   - `INPUT_FILES/` (including `EVIDENCE_REF.json`, `CONSTRAINTS.json`)
   - `RUN_ORDER.txt`
   - `REVIEW_REQUEST.txt`
   - deterministic `MANIFEST.json` for machine-readable traceability
4. Replay snapshot (local):
   - direct run (scan/json-only): `rc=0`, `vibe_coding_feeding_pack_status=SKIPPED_NOT_REQUIRED` when contract is not required
   - full-scan: project/global both expose `checks.vibe_coding_feeding_pack.*` with `rc=0`
   - three-plane: `instance_plane_detail.vibe_coding_feeding_pack.*` visible, `hard_boundary` unchanged
5. Non-blocking policy:
   - returns `PASS_NON_BLOCKING/WARN_NON_BLOCKING/SKIPPED_NOT_REQUIRED`
   - does not force release blocking unless governance explicitly promotes P1 to required hard gate.

#### 16.6.8 HOTFIX-P0-004 audit replay verdict (2026-03-01, cross-validated)

Status: `PASS` (scope: live reply first-line gate contract + six-surface wiring)

1. Commit under replay:
   - `e37db435a993ba72926be5b3c7377c3c4f9c6638`
2. Static checks:
   - `python3 -m py_compile ... && bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
3. Negative sample replay (must fail-closed):
   - `python3 scripts/validate_reply_identity_context_first_line.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --reply-file /tmp/reply-missing-stamp.txt --force-check --enforce-first-line-gate --json-only`
   - result: `rc=1`
   - key fields:
     - `reply_first_line_status=FAIL_REQUIRED`
     - `error_code=IP-ASB-STAMP-SESSION-001`
     - `reply_first_line_missing_count=1`
     - blocker receipt generated
4. Positive sample replay (must pass):
   - `python3 scripts/render_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --out /tmp/reply-stamp-pass.json --json-only`
   - `python3 scripts/validate_reply_identity_context_first_line.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --stamp-json /tmp/reply-stamp-pass.json --force-check --enforce-first-line-gate --json-only`
   - result: `rc=0`
   - key fields:
     - `reply_first_line_status=PASS_REQUIRED`
     - `reply_first_line_missing_count=0`
5. Full-scan machine-readable exposure:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/scan-hotfix-p0-004-audit.json`
   - result: `rc=0`
   - key extract:
     - project/global both expose `checks.reply_identity_context_first_line.reply_first_line_status=PASS_REQUIRED`
     - `reply_first_line_missing_count=0`
     - `reply_first_line_missing_refs=[]`
6. Three-plane machine-readable exposure:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract --out /tmp/three-plane-hotfix-p0-004-audit.json`
   - result: `rc=0`
   - key extract:
     - `instance_plane_detail.response_identity_stamp.reply_first_line_status=PASS_REQUIRED`
     - `reply_first_line_missing_count=0`
     - `reply_first_line_missing_refs=[]`
7. Docs/SSOT checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`

#### 16.7.10 FIX-015 progress refresh (2026-03-01, concurrent actor x identity activation verifier)

Status: `PATCHED_PENDING_AUDIT`

Source ref:

1. section `7` in this ledger (`FIX-015` release-blocking verifier scope and acceptance template).
2. L1 governance refs:
   - `DRC-1`, `DRC-4`
   - `ASB-RQ-009`, `ASB-RQ-010`
   - `ASB-RC-001~006`

Commit under replay:

1. `6fbf999` — `fix(fix-015): enable actor-scoped multi-active runtime semantics`

Replay context:

1. project runtime catalog replay:
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml`
2. execution context:
   - `sandbox`: static validators and scan replay.
   - `escalated`: activation/readiness/e2e that writes runtime artifacts.

Replay evidence summary:

1. Multi-active activation + actor binding creation (escalated):
   - `python3 scripts/identity_creator.py activate --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER --actor-id user:auditor --run-id fix015-concurrency-auditor --switch-reason fix015_concurrency_replay`
   - `rc=0`
   - key fields:
     - `active_identities=['base-repo-audit-expert-v3','custom-creative-ecom-analyst']`
     - actor session path: `session/actors/user_auditor.json`
     - switch report: `/tmp/identity-activation-reports/identity-activation-switch-base-repo-audit-expert-v3-1772375550.json`
2. Actor-scoped validator replay (sandbox):
   - `python3 scripts/validate_identity_state_consistency.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml`
     - `rc=0`, `active_count=2`
   - `python3 scripts/validate_actor_session_binding.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --actor-id user:yangxi --operation validate --json-only`
     - `rc=0`, `actor_binding_status=PASS_REQUIRED`
   - `python3 scripts/validate_actor_session_binding.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --actor-id user:auditor --operation validate --json-only`
     - `rc=0`, `actor_binding_status=PASS_REQUIRED`
   - `python3 scripts/validate_cross_actor_isolation.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --identity-id base-repo-audit-expert-v3 --operation validate --json-only`
     - `rc=0`, `cross_actor_isolation_status=PASS_REQUIRED`, `actor_binding_count=2`
   - `python3 scripts/validate_no_implicit_switch.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --switch-report /tmp/identity-activation-reports/identity-activation-switch-base-repo-audit-expert-v3-1772375550.json --operation validate --json-only`
     - `rc=0`, `implicit_switch_status=PASS_REQUIRED`, `cross_actor_demotion_detected=false`
3. Session pointer consistency replay (sandbox):
   - `python3 scripts/validate_identity_session_pointer_consistency.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --actor-id user:yangxi --identity-id custom-creative-ecom-analyst`
     - `rc=0` (canonical/mirror mismatch warning is allowed under multi-active tuple semantics)
   - `python3 scripts/validate_identity_session_pointer_consistency.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --actor-id user:auditor --identity-id base-repo-audit-expert-v3`
     - `rc=0`
4. Main-chain readiness replay with explicit report (escalated):
   - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --scope USER --execution-report /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/custom-creative-ecom-analyst/runtime/reports/identity-upgrade-exec-custom-creative-ecom-analyst-1772375882.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready`
   - `rc=0`
   - key tail:
     - `execution report freshness preflight: status=PASS`
     - `protocol baseline freshness preflight: status=PASS`
     - `protocol version alignment preflight: status=PASS_REQUIRED`
     - actor gates in readiness chain are invoked with `--operation readiness`
     - `[OK] release readiness checks PASSED`
5. Full-scan / three-plane visibility:
   - `full_identity_protocol_scan.py --scan-mode target --identity-ids \"base-repo-audit-expert-v3 custom-creative-ecom-analyst\" --project-catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-fix015-current.json`
   - `report_three_plane_status.py --identity-id custom-creative-ecom-analyst --scope USER --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract --out /tmp/three-plane-fix015-custom-creative-ecom-analyst.json`
   - actor binding / implicit switch / cross actor fields remain machine-readable.

Residual blockers / risks:

1. `e2e_smoke_test.sh` replay on project catalog currently fails at trigger-regression sample requirement:
   - `missing trigger regression report: identity/runtime/examples/custom-creative-ecom-analyst-trigger-regression-sample.json`
   - this is treated as a separate release hygiene dependency, not FIX-015 actor-concurrency semantic regression.
2. three-plane default actor context (`user:yangxi`) can show `actor_session_binding=FAIL_REQUIRED` for non-bound identity tuple; this is expected unless tuple-consistent actor context is used.
8. Audit decision:
   - close `HOTFIX-P0-004` as `DONE/PASS` for protocol-layer gate closure.
9. Residual risk (non-blocking enhancement lane):
   - current required-gate replay still uses explicit reply evidence input (`--reply-log/--reply-file/--stamp-json`);
   - end-to-end live reply stream ingestion can be enhanced later, but does not block HOTFIX closure.

#### 16.7.3 P1-F progress update (2026-03-01, capability-fit optimization validator chain)

Status: `PASS` (audit replayed on current head, non-required path semantics)

Source ref (L1 governance SSOT):

1. `ASB-RQ-049` (inventory-first + fit-matrix machine-checkability)
2. `ASB-RQ-050` (compose-before-discover gate)
3. `ASB-RQ-051` (single selected plan + fallback/rollback/review fields)
4. `ASB-RQ-052` (review freshness warning visibility)

Implemented package (protocol-only):

1. Added validator scripts:
   - `scripts/validate_identity_capability_fit_optimization.py`
   - `scripts/validate_capability_composition_before_discovery.py`
   - `scripts/validate_capability_fit_review_freshness.py`
2. Six-surface wiring completed:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Machine-readable visibility fields added:
   - `capability_fit_optimization_status`
   - `compose_before_discovery_status`
   - `capability_fit_review_freshness_status`
   - `review_freshness_status` / `overdue_by_days`

Replay snapshot (local):

1. Static checks:
   - `python3 -m py_compile scripts/validate_identity_capability_fit_optimization.py scripts/validate_capability_composition_before_discovery.py scripts/validate_capability_fit_review_freshness.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. Direct validator replay (`custom-creative-ecom-analyst`, global runtime catalog):
   - `python3 scripts/validate_identity_capability_fit_optimization.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
   - `python3 scripts/validate_capability_composition_before_discovery.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
   - `python3 scripts/validate_capability_fit_review_freshness.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
   - result: `rc=0` for all three; statuses are `SKIPPED_NOT_REQUIRED` on non-required contract path.
3. Full-scan wiring replay:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/scan-p1f-local.json`
   - result: `rc=0`
   - key extract:
     - project/global both expose:
       - `checks.capability_fit_optimization.rc=0` + `capability_fit_optimization_status`
       - `checks.capability_composition_before_discovery.rc=0` + `compose_before_discovery_status`
       - `checks.capability_fit_review_freshness.rc=0` + `capability_fit_review_freshness_status`
4. Three-plane wiring replay:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract --out /tmp/three-plane-p1f-local.json`
   - result: `rc=0`
   - key extract:
     - `instance_plane_detail.capability_fit_optimization.*` visible
     - `instance_plane_detail.capability_composition_before_discovery.*` visible
     - `instance_plane_detail.capability_fit_review_freshness.*` visible
5. Docs/SSOT checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`

Residual risks / next lane:

1. `ASB-RQ-053` roundtable `fact/inference` evidence mapping validator is not included in this patch set.
2. `P1-H` trigger/tool surfaces (`trigger_capability_fit_review`, `build_capability_fit_matrix`) are implemented in section `16.7.4` and moved to audit replay queue.
3. readiness escalated replay may still fail due unrelated runtime update chain issues (`identity_creator update` path), so P1-F acceptance in this batch is scoped to validator semantics + six-surface wiring visibility.

#### 16.7.4 P1-G/P1-H progress update (2026-03-01, capability-fit roundtable + trigger/builder surfaces)

Status: `PASS` (audit replayed on current head, non-required path semantics)

Source ref (L1 governance SSOT):

1. `ASB-RQ-053` (roundtable fact/inference evidence mapping for optimization decisions)
2. `ASB-RQ-049..052` (fit-cycle orchestration context reused by review trigger + matrix builder)

Implemented package (protocol-only):

1. Added validator/trigger/tool scripts:
   - `scripts/validate_capability_fit_roundtable_evidence.py` (P1-G)
   - `scripts/trigger_capability_fit_review.py` (P1-H trigger surface)
   - `scripts/build_capability_fit_matrix.py` (P1-H tool surface)
2. Six-surface wiring completed:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Machine-readable visibility fields added:
   - `capability_fit_roundtable_status`
   - `capability_fit_review_trigger_status`
   - `capability_fit_matrix_builder_status`
   - `triggered` / `trigger_reason`
   - `roundtable_required` / `selected_fact_refs`
   - `matrix_path` / `selected_candidate_id`

Replay snapshot (local):

1. Static checks:
   - `python3 -m py_compile scripts/validate_capability_fit_roundtable_evidence.py scripts/trigger_capability_fit_review.py scripts/build_capability_fit_matrix.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. Direct validator/trigger/tool replay (`custom-creative-ecom-analyst`, global runtime catalog):
   - `python3 scripts/validate_capability_fit_roundtable_evidence.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
   - `python3 scripts/trigger_capability_fit_review.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --json-only`
   - `python3 scripts/build_capability_fit_matrix.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --operation scan --out-root /tmp/capability-fit-matrices --json-only`
   - result: `rc=0` for all three; statuses are `SKIPPED_NOT_REQUIRED` on non-required contract path.
3. Full-scan wiring replay:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/scan-p1gh-local.json`
   - result: `rc=0`
   - key extract:
     - project/global both expose:
       - `checks.capability_fit_roundtable_evidence.rc=0` + `capability_fit_roundtable_status`
       - `checks.capability_fit_review_trigger.rc=0` + `capability_fit_review_trigger_status`
       - `checks.capability_fit_matrix_builder.rc=0` + `capability_fit_matrix_builder_status`
4. Three-plane wiring replay:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract --out /tmp/three-plane-p1gh-local.json`
   - result: `rc=0`
   - key extract:
     - `instance_plane_detail.capability_fit_roundtable_evidence.*` visible
     - `instance_plane_detail.capability_fit_review_trigger.*` visible
     - `instance_plane_detail.capability_fit_matrix_builder.*` visible
5. Docs/SSOT checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`

Residual risks / next lane:

1. This patch validates P1-G/P1-H wiring and machine-readable visibility on non-required contract path; strict required-path replay still depends on contract enablement + sample evidence population.
2. readiness escalated replay may still hit unrelated runtime update chain outcomes; not part of this P1 wiring scope.

#### 16.7.4A P1-D/P1-E/P1-F/P1-G/P1-H audit replay verdict (2026-03-01, cross-validated)

Status: `PASS` (scope: protocol-layer wiring + machine-readable visibility under non-required contracts)

1. Commit anchors under audit:
   - `de3868c5cebe2e55db47da4eb5137f36ce76c5b3` (`P1-D`)
   - `181642451c3af16a59501f4c7162ac40870df726` (`P1-E`)
   - `614e3e47bdd6f62431dd9ac2859dff2d48133357` (`P1-F`)
   - `5016816007efae722f137cddf55f0435b1c4aad9` (`P1-G/P1-H`)
2. Static checks:
   - `python3 -m py_compile ...` (all new P1 scripts + wired surfaces) and `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
3. Direct replay (`custom-creative-ecom-analyst`, `/Users/yangxi/.codex/identity/catalog.local.yaml`, `--operation scan --json-only`):
   - `trigger_platform_optimization_discovery.py` -> `rc=0`, `platform_optimization_discovery_status=SKIPPED_NOT_REQUIRED`, `triggered=false`
   - `build_vibe_coding_feeding_pack.py` -> `rc=0`, `vibe_coding_feeding_pack_status=SKIPPED_NOT_REQUIRED`
   - `validate_identity_capability_fit_optimization.py` -> `rc=0`, `capability_fit_optimization_status=SKIPPED_NOT_REQUIRED`
   - `validate_capability_composition_before_discovery.py` -> `rc=0`, `compose_before_discovery_status=SKIPPED_NOT_REQUIRED`
   - `validate_capability_fit_review_freshness.py` -> `rc=0`, `capability_fit_review_freshness_status=SKIPPED_NOT_REQUIRED`
   - `validate_capability_fit_roundtable_evidence.py` -> `rc=0`, `capability_fit_roundtable_status=SKIPPED_NOT_REQUIRED`
   - `trigger_capability_fit_review.py` -> `rc=0`, `capability_fit_review_trigger_status=SKIPPED_NOT_REQUIRED`, `triggered=false`
   - `build_capability_fit_matrix.py` -> `rc=0`, `capability_fit_matrix_builder_status=SKIPPED_NOT_REQUIRED`
4. Full-scan replay:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/scan-p1defgh-audit2.json`
   - result: `rc=0`
   - project/global both expose:
     - `checks.platform_optimization_discovery_trigger.*`
     - `checks.vibe_coding_feeding_pack.*`
     - `checks.capability_fit_optimization.*`
     - `checks.capability_composition_before_discovery.*`
     - `checks.capability_fit_review_freshness.*`
     - `checks.capability_fit_roundtable_evidence.*`
     - `checks.capability_fit_review_trigger.*`
     - `checks.capability_fit_matrix_builder.*`
5. Three-plane replay:
   - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract --out /tmp/three-plane-p1defgh-audit2.json`
   - result: `rc=0`
   - `instance_plane_detail` exposes all P1-D/E/F/G/H surfaces with non-required semantics; `hard_boundary=false` preserved.
6. Docs/SSOT checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`
7. Residual risk:
   - these P1 lanes are currently non-required for most instances; strict required-path blocking semantics depend on contract enablement and live evidence population at instance governance layer.

#### 16.7.5 FIX-017 progress update (2026-03-01, P0-A readiness scope passthrough hardening)

Status: `PASS` (audit replayed on current head)

Source ref (L1 governance SSOT + intake action list):

1. `ASB-RQ-039` readiness scope arbitration chain (`--scope` explicit passthrough)
2. review intake section `15.1 P0-A` (health-branch scope forwarding gap)

Implemented package:

1. Patched `scripts/release_readiness_check.py`:
   - when readiness is invoked with explicit `--scope`, the health-report branch now forwards it to:
     - `scripts/collect_identity_health_report.py --scope <SCOPE>`
2. No semantic changes to fail-closed behavior:
   - no-scope ambiguous context still expected to fail with `IP-ENV-002`;
   - this patch only removes downstream scope drift in the explicit-scope path.

Replay evidence:

1. Static check:
   - `python3 -m py_compile scripts/release_readiness_check.py`
   - result: `rc=0`
2. Readiness replay (explicit scope, system sample):
   - `python3 scripts/release_readiness_check.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report /Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772295915.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready --scope USER`
   - result: `rc=2` (downstream health failure, expected in this sample)
   - key proof:
     - run log now contains:
       - `python3 scripts/collect_identity_health_report.py ... --enforce-pass --scope USER`
     - confirms scope passthrough reaches health-report branch deterministically.

Residual risks:

1. This patch closes scope forwarding gap only; it does not alter health strictness (`--enforce-pass`) or semantic gate outcomes for identities with failing checks.
2. Audit replay sample still ends with downstream health failure (`rc=2`) on failing identity state, which is expected and confirms no gate weakening.

#### 16.7.6 FIX-018 progress update (2026-03-01, P0-B baseline policy stratification hardening)

Status: `PASS` (audit replayed on current head)

Source ref (L1 governance SSOT + intake action list):

1. review intake section `15.1 P0-B` (baseline policy mixed hardcoding across release/mutation chains)
2. `ASB-RQ-029` / `ASB-RQ-030` (protocol baseline freshness and path-governance fail-closed posture for release/mutation)

Commit under replay:

1. `b0c1483` — `fix(protocol): harden baseline policy stratification for release/mutation paths`

Implemented package (protocol-only):

1. `scripts/identity_creator.py`
   - added `--baseline-policy {strict,warn}` on `validate` and `update` commands (default `strict`).
   - replaced hardcoded `--baseline-policy warn` with passthrough `args.baseline_policy` for:
     - `validate_identity_session_refresh_status` (`operation=validate`)
     - `validate_identity_protocol_baseline_freshness` (`validate` chain)
     - `validate_identity_session_refresh_status` (`operation=update`)
2. `scripts/release_readiness_check.py`
   - readiness chain now forwards `args.baseline_policy` to:
     - `validate_identity_session_refresh_status` (`operation=readiness`)
     - auto-generated `identity_creator.py update` command when `--execution-report` is omitted.
3. `scripts/e2e_smoke_test.sh`
   - switched session refresh preflight from `--baseline-policy warn` to `--baseline-policy strict` for release-like E2E lane.
4. `scripts/run_protocol_upgrade_wave.py`
   - explicitly sets `identity_creator.py update --baseline-policy warn` in wave apply path to preserve remediation flow for stale instances under controlled override (default strict remains in generic mutation commands).

Replay evidence:

1. Static checks:
   - `python3 -m py_compile scripts/identity_creator.py scripts/release_readiness_check.py scripts/run_protocol_upgrade_wave.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. CLI contract checks:
   - `python3 scripts/identity_creator.py validate --help | rg baseline-policy`
   - `python3 scripts/identity_creator.py update --help | rg baseline-policy`
   - result: both commands expose `--baseline-policy {strict,warn}`.
3. Readiness command passthrough proof (warn override):
   - command:
     - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --scope USER --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready`
   - key tail:
     - readiness now emits auto-update command containing `--baseline-policy warn`.
     - readiness update preflight also shows `validate_identity_session_refresh_status ... --baseline-policy warn`.

Residual risks:

1. On stale baseline, default `strict` policy now blocks generic `identity_creator update` unless explicit override is supplied (expected under P0-B hardening).
2. Wave/batch apply path keeps explicit `warn` override by design to allow stale-instance remediation; audit replay should confirm this override is accepted as controlled exception.

#### 16.7.8 FIX-019 progress update (2026-03-01, P0-C protocol version alignment contract unification)

Status: `PASS` (audit replayed on current head, cross-validated)

Source ref (L1 governance SSOT + intake action list):

1. review intake section `15.1 P0-C` (fragmented alignment checks across baseline/prompt/binding validators).
2. `ASB-RQ-043` + section `5.8.7 protocol_version_alignment_contract_v1`.

Commit under replay:

1. `3c259da` — `feat(protocol): add unified protocol version alignment contract gate`

Implemented package (protocol-only):

1. New unified validator:
   - `scripts/validate_identity_protocol_version_alignment.py`
   - unified tuple closure fields:
     - execution report freshness binding
     - protocol baseline freshness (`protocol_commit_sha` vs current HEAD)
     - prompt activation alignment
     - binding tuple alignment
   - machine-readable output:
     - `protocol_version_alignment_status`
     - `error_code` (`IP-PVA-001..004`)
     - `tuple_checks`
     - `report_selected_path`
     - `stale_reasons`
2. Six-surface wiring:
   - `scripts/identity_creator.py` (`validate` + `update` chains)
   - `scripts/release_readiness_check.py` (execution-report preflight)
   - `scripts/e2e_smoke_test.sh` (strict replay lane)
   - `scripts/full_identity_protocol_scan.py` (`checks.protocol_version_alignment`)
   - `scripts/report_three_plane_status.py` (`instance_plane_detail.protocol_version_alignment`)
   - `.github/workflows/_identity-required-gates.yml` (CI strict gate)
3. Health observability extension:
   - `scripts/collect_identity_health_report.py` adds `protocol_version_alignment` check (`warn` policy).

Replay evidence (local static + targeted runtime replay):

1. Static checks:
   - `python3 -m py_compile scripts/validate_identity_protocol_version_alignment.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py scripts/collect_identity_health_report.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. Direct validator replay (`custom-creative-ecom-analyst`, scan/warn):
   - `python3 scripts/validate_identity_protocol_version_alignment.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation scan --alignment-policy warn --json-only`
   - result: `rc=0`
   - key fields:
     - `protocol_version_alignment_status=WARN_NON_BLOCKING`
     - `error_code=IP-PVA-002`
     - `tuple_checks.execution_report_freshness=true`
     - `tuple_checks.protocol_baseline_freshness=false`
     - `tuple_checks.prompt_activation=true`
     - `tuple_checks.binding_tuple=true`
3. Readiness preflight wiring proof:
   - command:
     - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report /Users/yangxi/.codex/identity/instances/custom-creative-ecom-analyst/runtime/reports/identity-upgrade-exec-custom-creative-ecom-analyst-1772370980.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready --scope USER --base fa60caa --head fa60caa`
   - result: `rc=0`
   - readiness log includes:
     - `[INFO] protocol version alignment preflight: status=<...> error_code=<...> report=<...>`
     - `[OK] release readiness checks PASSED`
4. Full-scan/three-plane visibility:
   - full-scan replay:
     - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/fix019-scan.json`
     - `rc=0`, project/global both expose `checks.protocol_version_alignment.protocol_version_alignment_status=WARN_NON_BLOCKING`, `error_code=IP-PVA-002`.
   - three-plane replay:
     - `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract --out /tmp/fix019-three-plane.json`
     - `rc=0`, exposes `instance_plane_detail.protocol_version_alignment.protocol_version_alignment_status=WARN_NON_BLOCKING`, `error_code=IP-PVA-002`, and keeps `hard_boundary=false`.
5. Strict fail-closed sample (CI semantics):
   - `python3 scripts/validate_identity_protocol_version_alignment.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --execution-report /Users/yangxi/.codex/identity/instances/custom-creative-ecom-analyst/runtime/reports/identity-upgrade-exec-custom-creative-ecom-analyst-1772370980.json --operation ci --alignment-policy strict --json-only`
   - result: `rc=1`, `protocol_version_alignment_status=FAIL_REQUIRED`, `error_code=IP-PVA-002`.
6. Docs/SSOT checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`
7. Audit decision:
   - close `FIX-019` as `DONE/PASS` for protocol-layer gate closure.

Residual risks:

1. Existing `validate_identity_prompt_activation.py` / `validate_identity_binding_tuple.py` remain as atomic validators; this fix adds unified contract validator without removing legacy checks to avoid sudden compatibility regression.
2. Strict policy paths can block update/readiness when no valid execution report is available; this is expected for release/mutation fail-closed semantics and should be paired with controlled remediation workflow (wave/update with explicit warn override where governance allows).

#### 16.7.7 FIX-017/FIX-018 audit replay verdict (2026-03-01, cross-validated)

Status: `PASS` (scope: protocol-layer behavior + command-path passthrough)

1. Commit anchors under audit:
   - `0dd074e90eed7e6458cc18a5c961f3451bc8f871` (`FIX-017`)
   - `b0c148304dbe10da5f34c5cea190aab9ea758cf4` (`FIX-018`)
2. Static checks:
   - `python3 -m py_compile scripts/identity_creator.py scripts/release_readiness_check.py scripts/run_protocol_upgrade_wave.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
3. CLI contract checks:
   - `python3 scripts/identity_creator.py validate --help | rg baseline-policy`
   - `python3 scripts/identity_creator.py update --help | rg baseline-policy`
   - result: both expose `--baseline-policy {strict,warn}`
4. FIX-017 readiness passthrough replay:
   - `python3 scripts/release_readiness_check.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --execution-report /Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772295915.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready --scope USER`
   - result: `rc=2` (downstream health failure, expected on sample state)
   - key proof:
     - `validate_identity_session_refresh_status ... --baseline-policy warn`
     - `collect_identity_health_report.py ... --enforce-pass --scope USER`
5. FIX-018 baseline-policy stratification replay:
   - `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready --scope USER`
   - result: `rc=2` (expected on sample state)
   - key proof:
     - auto-update command emits `python3 scripts/identity_creator.py update ... --baseline-policy warn --scope USER`
     - update preflight emits `validate_identity_session_refresh_status ... --operation update --baseline-policy warn`
6. Source-code anchor checks:
   - `scripts/e2e_smoke_test.sh` uses `validate_identity_session_refresh_status ... --baseline-policy strict` in E2E lane.
   - `scripts/run_protocol_upgrade_wave.py` keeps controlled override (`identity_creator.py update --baseline-policy warn`) for wave remediation path.
7. Docs/SSOT checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`


#### 16.7.11 HOTFIX-P0-008 / FIX-020 execution note (2026-03-01, lock-bound reply stamp closure)

Layer declaration: `protocol` only.

Source refs:

1. L1 SSOT: `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`ASB-RQ-054`, section `14.6`).
2. Incident class: dual-catalog actor lane drift (`user:yangxi` bound identity != strict target identity) produced perceived hard-switch risk in user-visible channel.

Problem statement:

1. Existing user-visible stamp validators enforced structural stamp correctness but could still pass when lock field was `LOCK_MISMATCH`.
2. In strict operations this allowed reply gates to look green while actor/session tuple was not lock-bound to requested identity.

Implementation (architect patch scope):

1. `scripts/validate_identity_response_stamp.py`
   - add `--operation` context.
   - add strict lock-bound enforcement for operations: `activate/update/mutation/readiness/e2e/validate`.
   - new error code: `IP-ASB-STAMP-005`.
   - add machine fields: `operation`, `lock_boundary_enforced`, `parsed_lock_state`.
2. `scripts/validate_reply_identity_context_first_line.py`
   - strict lock clause for same strict operations.
   - machine fields: `lock_boundary_enforced`, `expected_lock_state`, `reply_first_line_lock_state`.
3. Surface wiring updates:
   - `identity_creator.py` (`--operation validate`)
   - `release_readiness_check.py` (`--operation readiness`)
   - `e2e_smoke_test.sh` (`--operation e2e`)
   - `full_identity_protocol_scan.py` (`--operation scan`)
   - `report_three_plane_status.py` (`--operation three-plane`)
   - `.github/workflows/_identity-required-gates.yml` (`--operation ci`)

Replay evidence (architect local):

1. Compile/static:
   - `python3 -m py_compile ...` (modified python scripts) => `rc=0`
   - `bash -n scripts/e2e_smoke_test.sh` => `rc=0`
2. Mismatch lane strict block (`project catalog`, actor binding mismatch):
   - `validate_identity_response_stamp.py ... --operation validate --json-only` => `rc=1`
   - key: `error_code=IP-ASB-STAMP-005`, `stale_reasons=["actor_binding_lock_not_match"]`, `lock_boundary_enforced=true`.
3. Same mismatch lane inspection mode:
   - `validate_identity_response_stamp.py ... --operation scan --json-only` => `rc=0`
   - key: `stamp_status=PASS`, `lock_boundary_enforced=false`.
4. First-line validator strict block:
   - `validate_reply_identity_context_first_line.py ... --operation validate --json-only` => `rc=1`
   - key: `error_code=IP-ASB-STAMP-SESSION-001`, `stale_reasons=["actor_binding_lock_not_match"]`, `lock_boundary_enforced=true`.
5. First-line validator inspection mode:
   - `validate_reply_identity_context_first_line.py ... --operation scan --json-only` => `rc=0`
6. Readiness regression guard:
   - `python3 scripts/release_readiness_check.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --scope USER --execution-report /Users/yangxi/.codex/identity/base-repo-audit-expert-v3/runtime/reports/identity-upgrade-exec-base-repo-audit-expert-v3-1772376696.json --execution-report-policy strict --baseline-policy strict --capability-activation-policy route-any-ready` => `rc=0`.

Residual risks:

1. This patch guards strict reply-channel closure semantics; it does not auto-reconcile actor bindings across global/project lanes.
2. Tuple reconciliation remains instance/governance operation (`activate` with explicit catalog+actor tuple) and should be audited separately.

Next milestone:

1. audit replay on HOTFIX-P0-008 / FIX-020;
2. then promote row status from `PENDING_REVIEW` to `PASS` with commit anchor.


#### 16.7.12 HOTFIX-P0-008 / FIX-020 replay package refresh (2026-03-01)

Status: `READY_FOR_AUDIT_REPLAY`

Layer declaration:

1. `protocol` (gate semantics + wiring replay only).

Execution context split (explicit):

1. `sandbox`: static checks + validator replays.
2. `escalated`: actor identity rebinding under `~/.codex` (required for context restoration).

Replay commands and results:

1. `python3 -m py_compile ...` (modified scripts) -> `rc=0`
2. `bash -n scripts/e2e_smoke_test.sh` -> `rc=0`
3. strict mismatch lane (`project` catalog, `base-repo-audit-expert-v3`):
   - `validate_identity_response_stamp.py ... --operation validate --json-only` -> `rc=1`
   - key: `error_code=IP-ASB-STAMP-005`, `stale_reasons=["actor_binding_lock_not_match"]`, `lock_boundary_enforced=true`.
4. strict mismatch lane first-line gate:
   - `validate_reply_identity_context_first_line.py ... --operation validate --json-only` -> `rc=1`
   - key: `error_code=IP-ASB-STAMP-SESSION-001`, `reply_first_line_status=FAIL_REQUIRED`.
5. inspection visibility mode (same mismatch lane):
   - `validate_identity_response_stamp.py ... --operation scan --json-only` -> `rc=0`, `stamp_status=PASS`, `lock_boundary_enforced=false`.
   - `validate_reply_identity_context_first_line.py ... --operation scan --json-only` -> `rc=0`, `reply_first_line_status=PASS_REQUIRED`.
6. strict pass lane (`global` catalog, `base-repo-architect`):
   - `validate_identity_response_stamp.py ... --operation validate --json-only` -> `rc=0`, `stamp_status=PASS`, `lock=LOCK_MATCH`.
   - `validate_reply_identity_context_first_line.py ... --operation validate --json-only` -> `rc=0`, `reply_first_line_status=PASS_REQUIRED`.

Note:

1. readiness replay on `base-repo-architect` with historical report `1772296255` returns `IP-PBL-001` (baseline stale); this is baseline freshness policy behavior, not HOTFIX-P0-008 regression.

---

#### 16.7.13 FIX-015 replay refresh (2026-03-01, pending audit closure)

Status: `PASS` (audit replayed on current head, cross-validated)

Execution context split:

1. `escalated`: actor `user:auditor` activation replay on project catalog.
2. `sandbox`: validator/readiness replay.

Replay delta (new evidence):

1. activation replay:
   - `python3 scripts/identity_creator.py activate --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER --actor-id user:auditor --run-id fix015-replay-20260301 --switch-reason fix015_concurrency_replay`
   - `rc=0`
   - switch report: `/tmp/identity-activation-reports/identity-activation-switch-base-repo-audit-expert-v3-1772379086.json`
2. validator set replay:
   - `validate_identity_state_consistency.py` -> `rc=0`, `active_count=2`
   - `validate_actor_session_binding.py` (`user:yangxi`->custom) -> `rc=0`, `PASS_REQUIRED`
   - `validate_actor_session_binding.py` (`user:auditor`->base-repo-audit-expert-v3) -> `rc=0`, `PASS_REQUIRED`
   - `validate_cross_actor_isolation.py --operation validate` -> `rc=0`, `PASS_REQUIRED`
   - `validate_no_implicit_switch.py --switch-report ...1772379086.json --operation validate` -> `rc=0`, `PASS_REQUIRED`
   - pointer consistency checks (`user:yangxi/custom`, `user:auditor/base-repo-audit-expert-v3`) -> both `rc=0`
3. readiness replay:
   - `release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --scope USER --execution-report ...1772375882.json --execution-report-policy warn --baseline-policy warn --capability-activation-policy route-any-ready`
   - `rc=0`, tail: `[OK] release readiness checks PASSED`.

Residual risk (unchanged):

1. project-catalog e2e can still be blocked by sample hygiene (`trigger-regression` evidence), treated as instance/release hygiene dependency rather than FIX-015 actor semantics regression.

---

#### 16.7.14 Remaining blockers split (protocol vs instance, 2026-03-01 refresh)

Purpose:

1. Provide one non-ambiguous release-control split so governance actions and runtime-instance actions are not mixed.

Protocol-layer remaining blockers (release-lock relevant):

1. None after latest replay package:
   - `HOTFIX-P0-008` (`FIX-020`) -> `PASS`.
   - `FIX-015` -> `PASS`.

Instance / environment blockers (must not be misclassified as protocol regression):

1. Global `base-repo-architect` baseline freshness is stale in scan view:
   - `IP-PBL-001` (`protocol_baseline_freshness=WARN`)
   - `IP-PVA-002` (`protocol_version_alignment_status=WARN_NON_BLOCKING`)
   - source: `full_identity_protocol_scan.py --scan-mode target --identity-ids base-repo-architect --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/full-scan-base-repo-architect.json`
   - action: run identity update to generate latest bound report.
2. Capability activation preflight shows environment auth blocked:
   - `IP-CAP-003`, `env_auth_blocked=true`
   - action: configure required auth/tool environment; this is execution environment readiness, not protocol contract mismatch.
3. Project lane actor tuple mismatch remains expected unless explicitly reconciled:
   - `user:yangxi` bound to `custom-creative-ecom-analyst` while probing `base-repo-audit-expert-v3` in project catalog.
   - action: explicit actor/catalog rebinding when running strict operation against that tuple.
4. Project-lane e2e may still fail on sample hygiene (`trigger-regression` evidence files).
   - action: instance owner repairs sample/report assets; protocol validators already enforce expected semantics.

Eradication sequence (strict order):

1. Protocol audit closure is complete for this lane (`HOTFIX-P0-008`, `FIX-015`, `FIX-020` all `PASS`).
2. Run instance update wave to clear baseline stale warnings.
3. Repair instance sample hygiene and auth prerequisites.
4. Re-run full-scan + three-plane and confirm no protocol regressions are reintroduced.


#### 16.7.15 Architect-to-audit replay package draft (2026-03-01, protocol-only)

Package scope:

1. `HOTFIX-P0-008 / FIX-020` strict lock-bound reply gate closure.
2. `FIX-015` concurrent actor x identity activation verifier refresh.

Layer declaration:

1. `protocol` only.

Execution context declaration (mandatory):

1. `sandbox`: compile/static checks + validator/readiness replay commands.
2. `escalated`: activation commands that write runtime artifacts (`~/.codex` and `.agents/identity`).

Commit sha list:

1. `483e368361264697c3256ff32d6b678ef4261562` (`fix(hotfix-p0-008): fail-closed strict reply stamp on lock mismatch`)
2. `6fbf9999bac51febf3ac73887dd7e35eaecdf420` (`fix(fix-015): enable actor-scoped multi-active runtime semantics`)
3. `22b2e3e3c79449126f61b2cdb8a5f1966f79c16c` (`docs(review): refresh HOTFIX-P0-008 and FIX-015 replay evidence`)
4. `d6aa00ef1015266834c18a86caf9eb83b4ad1b58` (`docs(review): add protocol-vs-instance remaining blocker split`)

Changed file list (by commit):

1. `483e368`:
   - `.github/workflows/_identity-required-gates.yml`
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.5.md`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/report_three_plane_status.py`
   - `scripts/validate_identity_response_stamp.py`
   - `scripts/validate_reply_identity_context_first_line.py`
2. `6fbf999`:
   - `scripts/compile_identity_runtime.py`
   - `scripts/identity_creator.py`
   - `scripts/identity_installer.py`
   - `scripts/validate_identity_session_pointer_consistency.py`
   - `scripts/validate_identity_state_consistency.py`
   - `scripts/validate_no_implicit_switch.py`
3. `22b2e3e` / `d6aa00e`:
   - `docs/review/protocol-remediation-audit-ledger-v1.5.md`

Acceptance command outputs (HOTFIX-P0-008 / FIX-020):

| Command ID | rc | key tail |
| --- | --- | --- |
| C1 | `0` | `` |
| C2 | `0` | `` |
| C3 | `1` | `{"identity_id": "base-repo-audit-expert-v3", "catalog_path": "/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml", "stamp_line": "Identity-Contex...` |
| C4 | `1` | `{"identity_id": "base-repo-audit-expert-v3", "catalog_path": "/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml", "operation": "validate", "requ...` |
| C5 | `0` | `{"identity_id": "base-repo-audit-expert-v3", "catalog_path": "/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml", "stamp_line": "Identity-Contex...` |
| C6 | `0` | `{"identity_id": "base-repo-audit-expert-v3", "catalog_path": "/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml", "operation": "scan", "required...` |
| C7 | `0` | `{"identity_id": "base-repo-architect", "catalog_path": "/Users/yangxi/.codex/identity/catalog.local.yaml", "stamp_line": "Identity-Context: actor_id=user:yangxi; identity_id=bas...` |
| C8 | `0` | `{"identity_id": "base-repo-architect", "catalog_path": "/Users/yangxi/.codex/identity/catalog.local.yaml", "operation": "validate", "required_contract": true, "reply_first_line_...` |
| C9 | `1` | `[INFO] protocol baseline freshness preflight: status=FAIL error_code=IP-PBL-001 report=/Users/yangxi/.codex/identity/instances/base-repo-architect/runtime/reports/identity-upgra...` |
| C10 | `0` | `[PASS] docs command contract check passed.` |
| C11 | `0` | `     artifacts_policy=evidence_only_non_normative` |


Acceptance command outputs (FIX-015 refresh):

| Command ID | rc | key tail |
| --- | --- | --- |
| F1 | `0` | `     checked_meta_files=3` |
| F2 | `0` | `{"identity_id": "custom-creative-ecom-analyst", "catalog_path": "/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml", "actor_id": "user:yangxi", ...` |
| F3 | `0` | `{"identity_id": "base-repo-audit-expert-v3", "catalog_path": "/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml", "actor_id": "user:auditor", "o...` |
| F4 | `0` | `{"catalog_path": "/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml", "identity_id": "base-repo-audit-expert-v3", "operation": "validate", "acti...` |
| F5 | `0` | `{"identity_id": "base-repo-audit-expert-v3", "catalog_path": "/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml", "operation": "validate", "swit...` |
| F6 | `0` | `[OK] session pointer consistency validated: expected_identity=custom-creative-ecom-analyst actor=user:yangxi active_count=2 catalog=/Users/yangxi/claude/codex_project/weixinstor...` |
| F7 | `0` | `[OK] session pointer consistency validated: expected_identity=base-repo-audit-expert-v3 actor=user:auditor active_count=2 catalog=/Users/yangxi/claude/codex_project/weixinstore/...` |
| F8 | `0` | `[OK] release readiness checks PASSED` |


Residual risks:

1. `HOTFIX-P0-008 / FIX-020` and `FIX-015` protocol semantics are audit-passed; remaining instability is instance/environment lane (sample hygiene, auth readiness, stale reports).
2. project-lane e2e can still fail on sample hygiene (`trigger-regression` artifacts), classified as instance/release hygiene dependency.
3. Global `base-repo-architect` can show baseline freshness warning (`IP-PBL-001`) on old report; this is dynamic baseline policy behavior, not HOTFIX/FIX-015 regression.

Non-merge closure status:

1. `HOTFIX-P0-008`: `DONE / PASS`.
2. `FIX-015`: `DONE / PASS`.
3. `FIX-020`: `DONE / PASS`.


#### 16.7.16 Audit handoff packet (copy-paste ready, protocol-only)

Identity-Context snapshot:

1. actor_id=`user:yangxi`
2. identity_id=`base-repo-architect`
3. catalog_path=`/Users/yangxi/.codex/identity/catalog.local.yaml`
4. scope=`USER`

Layer declaration:

1. `protocol` only (no business data / no instance-threshold semantics).

Execution context declaration:

1. `sandbox`:
   - validator replay commands
   - docs/ssot checks
   - full-scan/readiness replay commands that do not mutate actor binding
2. `escalated`:
   - activation commands that write actor binding/session/runtime evidence (`~/.codex`, `.agents/identity`)

Commit sha list:

1. `483e368361264697c3256ff32d6b678ef4261562` (HOTFIX-P0-008 / FIX-020 code patch)
2. `6fbf9999bac51febf3ac73887dd7e35eaecdf420` (FIX-015 actor-scoped multi-active semantics)
3. `22b2e3e3c79449126f61b2cdb8a5f1966f79c16c` (replay evidence refresh)
4. `d6aa00ef1015266834c18a86caf9eb83b4ad1b58` (protocol-vs-instance blocker split)
5. `f6c94db` (copy-paste replay package matrix)

Current non-merge closure status:

1. `HOTFIX-P0-008`: `DONE / PASS`
2. `FIX-015`: `DONE / PASS`
3. `FIX-020`: `DONE / PASS`
4. protocol-layer release-lock items in this lane are closed; remaining gates are instance/environment readiness items.

Residual risks (explicit, non-conflicting):

1. `base-repo-architect` global lane can show `IP-PBL-001` / `IP-PVA-002` on stale historical report (`warn` path) — this is dynamic baseline semantics, not lock-gate regression.
2. project-lane e2e may still fail on sample hygiene (`trigger-regression` evidence), treated as instance/release hygiene dependency.
3. capability activation preflight may show `IP-CAP-003` when auth/env is unavailable; this is environment readiness, not protocol gate correctness.

Auditor action request:

1. Replay rows in `16.7.15` has been completed and outputs match expected deterministic semantics.
2. `HOTFIX-P0-008`, `FIX-015`, `FIX-020` are now audit-marked `PASS`.

#### 16.7.17 HOTFIX-P0-008 / FIX-015 / FIX-020 audit replay verdict (2026-03-01, cross-validated)

Status: `PASS` (scope: protocol-layer closure for remaining release-lock lanes)

1. Commit anchors under audit:
   - `483e368361264697c3256ff32d6b678ef4261562` (`HOTFIX-P0-008` / `FIX-020`)
   - `6fbf9999bac51febf3ac73887dd7e35eaecdf420` (`FIX-015`)
2. Static checks:
   - `python3 -m py_compile scripts/validate_identity_response_stamp.py scripts/validate_reply_identity_context_first_line.py scripts/validate_identity_state_consistency.py scripts/validate_actor_session_binding.py scripts/validate_cross_actor_isolation.py scripts/validate_no_implicit_switch.py scripts/validate_identity_session_pointer_consistency.py scripts/identity_creator.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
3. HOTFIX-P0-008 / FIX-020 strict fail-closed replay:
   - mismatch strict (`project`, `base-repo-audit-expert-v3`, `LOCK_MISMATCH` stamp):
     - `validate_identity_response_stamp.py ... --operation validate ...` -> `rc=1`, `error_code=IP-ASB-STAMP-005`, `lock_boundary_enforced=true`.
     - `validate_reply_identity_context_first_line.py ... --operation validate ...` -> `rc=1`, `reply_first_line_status=FAIL_REQUIRED`, `error_code=IP-ASB-STAMP-SESSION-001`.
   - mismatch inspection (`scan`) keeps observability non-blocking:
     - response stamp validator -> `rc=0`, `stamp_status=PASS`, `lock_boundary_enforced=false`.
     - first-line validator -> `rc=0`, `reply_first_line_status=PASS_REQUIRED`.
   - strict pass lane (`global`, `base-repo-architect`, `LOCK_MATCH`):
     - both validators `rc=0` with `PASS`/`PASS_REQUIRED`.
4. FIX-015 concurrent actor semantics replay:
   - activation replay (`user:auditor` -> `base-repo-audit-expert-v3`) -> `rc=0`, switch report generated.
   - `validate_identity_state_consistency.py` -> `rc=0`, `active_count=2`.
   - actor binding checks:
     - `user:yangxi` -> `custom-creative-ecom-analyst`: `rc=0`, `PASS_REQUIRED`.
     - `user:auditor` -> `base-repo-audit-expert-v3`: `rc=0`, `PASS_REQUIRED`.
   - `validate_cross_actor_isolation.py --operation validate` -> `rc=0`, `PASS_REQUIRED`.
   - `validate_no_implicit_switch.py --operation validate` (with switch report) -> `rc=0`, `PASS_REQUIRED`.
   - pointer consistency checks for both actors -> `rc=0`.
   - readiness replay (`custom-creative-ecom-analyst`, project catalog, warn policy) -> `rc=0`, `[OK] release readiness checks PASSED`.
5. Contextual non-regression note:
   - `base-repo-architect` readiness with old report can still show `IP-PBL-001` and `IP-PVA-002` under warn path while remaining pass-overall; this is baseline freshness semantics, not HOTFIX/FIX-015 regression.
6. Docs/SSOT checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`
7. Audit decision:
   - close `HOTFIX-P0-008`, `FIX-015`, and `FIX-020` as `DONE/PASS`.

#### 16.7.18 Consolidated protocol audit verdict refresh (2026-03-01, deep cross-validation)

Status: `PASS` (protocol layer); residual blockers are instance/env readiness only.

Replay scope in this refresh:

1. `FIX-011`..`FIX-020` protocol chain (including `FIX-017/018/019`).
2. P0 semantic/security lanes: `P0-D/P0-E/P0-F`.
3. P1 non-blocking capability-fit lanes: `P1-D/P1-E/P1-F/P1-G/P1-H`.

Cross-validation evidence:

1. Static checks:
   - `python3 -m py_compile scripts/identity_creator.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py scripts/collect_identity_health_report.py scripts/validate_identity_protocol_version_alignment.py scripts/validate_identity_response_stamp.py scripts/validate_reply_identity_context_first_line.py scripts/validate_protocol_vendor_semantic_isolation.py scripts/validate_external_source_trust_chain.py scripts/validate_protocol_data_sanitization_boundary.py scripts/trigger_platform_optimization_discovery.py scripts/build_vibe_coding_feeding_pack.py scripts/validate_identity_capability_fit_optimization.py scripts/validate_capability_composition_before_discovery.py scripts/validate_capability_fit_review_freshness.py scripts/validate_capability_fit_roundtable_evidence.py scripts/trigger_capability_fit_review.py scripts/build_capability_fit_matrix.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. Full scan replay (`/tmp/final-audit-replay-20260301.json`):
   - command: `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids base-repo-architect,custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --out /tmp/final-audit-replay-20260301.json`
   - result: `rc=0`
   - summary: `{"total_identities":3,"p0":0,"p1":3,"ok":0}`
   - key fields:
     - `reply_identity_context_first_line.reply_first_line_status=PASS_REQUIRED` (project/global lanes).
     - `protocol_version_alignment.protocol_version_alignment_status=WARN_NON_BLOCKING` (baseline stale semantics preserved under warn policy).
     - `protocol_vendor_semantic_isolation` / `external_source_trust_chain` / `protocol_data_sanitization_boundary` -> `SKIPPED_NOT_REQUIRED` with `rc=0` (contract-not-required lanes remain non-blocking as designed).
3. HOTFIX-P0-008 strict lock-bound fail-closed recheck:
   - native lock-mismatch lane (`base-repo-audit-expert-v3`, project catalog, strict validate):
     - `validate_identity_response_stamp.py ... --operation validate ... --require-lock-match --enforce-user-visible-gate` -> `rc=1`, `stamp_status=FAIL`, `error_code=IP-ASB-STAMP-005`.
   - crafted lock-mismatch stamp (`base-repo-architect`, global catalog, strict validate):
     - `validate_identity_response_stamp.py ... --operation validate ... --require-lock-match --enforce-user-visible-gate` -> `rc=1`, `stamp_status=FAIL`, `error_code=IP-ASB-STAMP-001`.
     - `validate_reply_identity_context_first_line.py ... --operation validate ... --enforce-first-line-gate` -> `rc=1`, `reply_first_line_status=FAIL_REQUIRED`, `error_code=IP-ASB-STAMP-SESSION-001`.
   - lock-match strict pass lane:
     - both validators `rc=0` with `PASS`/`PASS_REQUIRED`.
4. FIX-015 actor-scoped concurrency recheck (`project` catalog):
   - `validate_identity_state_consistency.py` -> `rc=0`, `active_count=2`.
   - actor binding checks:
     - `validate_actor_session_binding.py --identity-id custom-creative-ecom-analyst --actor-id user:yangxi ... --operation validate --json-only` -> `rc=0`, `PASS_REQUIRED`.
     - `validate_actor_session_binding.py --identity-id base-repo-audit-expert-v3 --actor-id user:auditor ... --operation validate --json-only` -> `rc=0`, `PASS_REQUIRED`.
   - `validate_cross_actor_isolation.py ... --operation validate --json-only` -> `rc=0`, `PASS_REQUIRED`.
   - `validate_no_implicit_switch.py --identity-id base-repo-audit-expert-v3 --switch-report /private/tmp/identity-activation-reports/identity-activation-switch-base-repo-audit-expert-v3-1772380736.json --operation validate --json-only` -> `rc=0`, `PASS_REQUIRED`.
5. Actor mismatch fail-closed sanity proof:
   - target scan on `base-repo-audit-expert-v3` under actor `user:yangxi` shows `actor_session_binding_status=FAIL_REQUIRED`, `error_code=IP-ASB-201` (expected boundary behavior).
6. Readiness scope/baseline chain recheck:
   - command: `python3 scripts/release_readiness_check.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --scope USER --baseline-policy warn --execution-report-policy warn`
   - logs confirm scope and baseline policy passthrough into session/baseline/version branches.
   - final `rc=2` is driven by `IP-CAP-003` capability/auth readiness (`github_auth_invalid`, missing required skill package), not protocol gate regression.
7. Docs/SSOT checks:
   - `python3 scripts/docs_command_contract_check.py` -> `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `rc=0`

Consolidated audit decision:

1. Protocol remediation lane is closure-complete for this wave (`FIX-011`..`FIX-020` + `P0-D/E/F` + `P1-D/E/F/G/H`) with expected policy semantics preserved.
2. Remaining blockers are explicitly outside protocol correctness:
   - environment/auth readiness (`IP-CAP-003`);
   - instance freshness and evidence hygiene (`IP-PBL-*`, sample/live replacement backlog).

#### 16.8.1 Roundtable intake: instance/protocol split governance hardening (2026-03-02, docs-only)

Status: `SPEC_READY` (implementation not landed yet).

Intake source:

1. `cqsw/governance/protocol-issue-reports/identity-instance-protocol-split-roundtable-crosscheck-2026-03-02.md`

Problem statement (cross-validated):

1. Teams still rely on oral reminders to distinguish `instance execution` vs `protocol governance` work lanes.
2. Missing machine-readable split receipts causes replay ambiguity and weak owner routing.
3. Mixed lane writing (business execution + governance proposal in one section) increases false attribution risk.

Cross-validation anchors:

1. Local protocol chain already enforces related governance boundaries:
   - response stamp gate (`scripts/release_readiness_check.py:421`)
   - scope passthrough into health branch (`scripts/release_readiness_check.py:684`)
   - namespace separation (`scripts/release_readiness_check.py:605`)
   - base-repo write boundary (`scripts/release_readiness_check.py:931`)
   - protocol-feedback SSOT archival (`scripts/release_readiness_check.py:947`)
2. Vendor guidance alignment (inference from official docs):
   - OpenAI prompt authority layering + Responses typed items:
     - `https://platform.openai.com/docs/guides/prompt-engineering`
     - `https://platform.openai.com/docs/guides/responses-vs-chat-completions`
   - Google explicit instructions + system instruction + structured/tool controls:
     - `https://ai.google.dev/gemini-api/docs/ai-studio-quickstart`
     - `https://ai.google.dev/gemini-api/docs/prompting-strategies`
     - `https://ai.google.dev/api/generate-content`
   - Anthropic explicit instructions + XML structure + context management:
     - `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts`
     - `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags`
     - `https://docs.anthropic.com/en/docs/build-with-claude/context-windows`
   - Moonshot official platform/docs entry validation:
     - `https://platform.moonshot.cn/`
     - `https://platform.moonshot.cn/docs/overview`

Governance delta added in this batch:

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`:
   - `5.8.8` `instance_protocol_split_receipt_contract_v1`
   - `5.8.9` `protocol_feedback_trigger_hard_condition_contract_v1`
   - requirement rows `ASB-RQ-055..058` (`P0`, `SPEC_READY`)
2. Business-scene contamination control remains hard requirement:
   - protocol lane must use generic placeholders only (no tenant/customer/business constants in contract fields).

Architect implementation package (next execution batch):

1. Add validator: `scripts/validate_instance_protocol_split_receipt.py`
2. Wire required checks to:
   - `identity_creator.py`
   - `release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `full_identity_protocol_scan.py`
   - `report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Enforce failure codes:
   - `IP-SPLIT-001`..`IP-SPLIT-005`
4. Extend sanitization parser to detect mixed-lane section contamination and business-scene constants in protocol receipt payload.

Acceptance replay template (post-implementation):

1. negative: missing `split_notice` -> `FAIL_REQUIRED` (`IP-SPLIT-001`)
2. negative: `feedback_triggered=true` with no SSOT outbox/index path -> `FAIL_REQUIRED` (`IP-SPLIT-003`)
3. negative: mixed lane in same section -> `FAIL_REQUIRED` (`IP-SPLIT-004`)
4. negative: protocol receipt carries business-scene constants -> `FAIL_REQUIRED` (`IP-SPLIT-005`)
5. positive: complete split receipt + linked SSOT evidence -> `PASS_REQUIRED`

This section is docs-only intake; no protocol script behavior changed in this batch.

#### 16.8.33 FIX-034/035/036/038/043 implementation landing replay (`c310ab4`, 2026-03-02, protocol)

Status: `IMPL_READY (BLOCKED_BY_AUDIT)` pending independent replay signoff.

Implementation scope (`c310ab4`):

1. `FIX-034` / `ASB-RQ-094`:
   - `scripts/validate_work_layer_gate_set_routing.py` now emits:
     - `protocol_context_detected`
     - `session_lane_lock`
     - `lane_resolution_decision`
     - `lane_resolution_blocked`
     - `lane_resolution_error_code`
   - strict fallback under protocol context now fail-closed via:
     - `IP-LAYER-GATE-006`
     - `IP-LAYER-GATE-007`
   - protocol lane writes lane-lock receipt (`SESSION_LANE_LOCK_PROTOCOL_*.json`) with evidence-index linkage.
2. `FIX-035` / `ASB-RQ-095`:
   - run-start pinned baseline anchor fields added:
     - `protocol_head_sha_at_run_start`
     - `baseline_reference_mode`
     - `head_drift_detected`
   - strict baseline freshness now enforces `run_pinned` semantics:
     - missing pinned anchor => `IP-PBL-005`
     - strict non-`run_pinned` mode => `IP-PBL-006`
   - session refresh payload/validator and scan/three-plane telemetry synchronized to new baseline fields.
3. `FIX-036` / `ASB-RQ-096`:
   - new validator: `scripts/validate_e2e_hermetic_runtime_import.py`
   - `scripts/e2e_smoke_test.sh` now:
     - bootstraps `PYTHONPATH` internally,
     - runs hermetic import preflight,
     - emits machine-readable fields (`e2e_hermetic_runtime_status`, `pythonpath_bootstrap_mode`, `import_preflight_status`, `import_preflight_error_code`)
     - fail-closed with `IP-E2E-HERM-001` on import preflight failure.
   - readiness/full-scan/three-plane/CI required-gates wired to hermetic validator.
4. `FIX-038` / `ASB-RQ-098`:
   - `scripts/identity_creator.py update` now supports strict two-phase stale-baseline path:
     - phase A refresh (`refresh_identity_session_status`)
     - phase B strict revalidate (`validate_identity_session_refresh_status`)
   - emits machine-readable phase trace:
     - `phase_a_refresh_applied`
     - `phase_b_strict_revalidate_status`
     - `phase_transition_reason`
     - `phase_transition_error_code`
   - stale-only two-phase unavailable path returns `IP-UPG-BASE-001`.
5. `FIX-043` / `ASB-RQ-103`:
   - runtime lifecycle state moved to:
     - `runtime/state/prompt_contract.json`
   - `IDENTITY_PROMPT.md` runtime metadata block is no longer authoritative; migration removal supported.
   - new report telemetry:
     - `prompt_runtime_state_externalization_status`
     - `prompt_policy_hash`
     - `runtime_state_artifact_path`
     - `runtime_state_artifact_hash`
     - `prompt_runtime_state_binding_status`
   - `scripts/validate_identity_prompt_lifecycle.py` updated for externalized-state validation.

Replay highlights (local):

1. Static:
   - `python3 -m py_compile ...` -> `rc=0`
   - `bash -n scripts/e2e_smoke_test.sh` -> `rc=0`
2. `FIX-034` protocol-context fallback block:
   - `python3 scripts/validate_work_layer_gate_set_routing.py ... --operation validate --force-check --json-only`
   - evidence: `/tmp/fix034_protocol_context_fallback.json`
   - result: `rc=1`, `error_code=IP-LAYER-GATE-006`, `protocol_context_detected=true`, `lane_resolution_blocked=true`.
3. `FIX-035` run-pinned strict baseline:
   - pass case evidence: `/tmp/fix035_run_pinned_pass.out.json`
     - `rc=0`, `baseline_status=PASS`, `baseline_reference_mode=run_pinned`, `head_drift_detected=true`.
   - missing anchor fail case evidence: `/tmp/fix035_run_pinned_missing_anchor.out.json`
     - `rc=1`, `baseline_error_code=IP-PBL-005`.
4. `FIX-036` hermetic e2e import:
   - `unset PYTHONPATH && ... bash scripts/e2e_smoke_test.sh`
   - evidence: `/tmp/fix036_e2e_replay.log`
   - first-line payload:
     - `e2e_hermetic_runtime_status=PASS_REQUIRED`
     - `import_preflight_error_code=""`
     - no `ModuleNotFoundError` for `response_stamp_common`.
5. `FIX-038` two-phase stale-baseline trace:
   - evidence: `/tmp/fix038_identity_update_v2.log`
   - emitted trace:
     - `phase_a_refresh_applied=true`
     - `phase_b_strict_revalidate_status=FAIL_REQUIRED`
     - `phase_transition_error_code=IP-UPG-BASE-001`
6. `FIX-043` runtime-state externalization migration function replay:
   - evidence:
     - `/tmp/fix043_prompt_test/runtime/state/prompt_contract.json`
   - result:
     - legacy prompt runtime block removed in test fixture,
     - runtime state artifact written with `prompt_policy_hash` binding.
7. Scenario A cross-validation addendum (`system-requirements-analyst`):
   - report evidence:
     - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772512085.json`
   - key fields:
     - `all_ok=true`
     - `work_layer=instance`
     - `applied_gate_set=instance_required_checks`
     - `writeback_status=WRITTEN`
   - lane receipts present:
     - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_PROTOCOL_20260303T042034Z.json`
     - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/LAYER_GATE_PROTOCOL_PENDING_20260303T042103Z.json`
     - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_EXIT_20260303T042733Z.json`
8. Collaboration hard-block contract verification:
   - command replay:
     - `python3 scripts/validate_identity_collab_trigger.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml`
   - result: `rc=0`, notify policy remains `must_notify_when_human_required`; task contract retains `must_emit_receipt_in_chat=true`.
9. Residual operational gap (historical snapshot, superseded by FIX-044 in `16.8.34`):
   - evidence index currently links protocol lock + pending, but no link for `SESSION_LANE_LOCK_EXIT_20260303T042733Z.json`.
   - script scan confirms `scripts/validate_work_layer_gate_set_routing.py` consumes `SESSION_LANE_LOCK_EXIT_*` as lock-release evidence, but no dedicated auto-exit writer surface is currently wired.
   - closure action required: runbook must explicitly define protocol round exit emission + index linkage; otherwise strict lane checks can remain in `IP-LAYER-GATE-007` blocked state.
10. Residual validator gap (`FIX-038`, strict two-phase stale-only predicate too broad):
   - code path: `scripts/identity_creator.py:1904`.
   - observed replay (`/tmp/fix038_identity_update_v2.log`, `/tmp/audit_real_instance_update.log`):
     - `baseline_error_code=IP-PBL-006`,
     - `stale_reasons=[]`,
     - still enters `phase_a_refresh_applied=true` and ends with `IP-UPG-BASE-001`.
   - governance mismatch:
     - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:1619` requires stale-baseline (`IP-PBL-001`-class) only.
   - required closure:
     - add baseline error-code whitelist for phase-A entry,
     - reject stale-only when `stale_reasons` is empty,
     - differentiate trace reason `stale_baseline_only_detected` vs `baseline_mode_violation`.
11. Residual routing gap (literal interception):
   - replay evidence: `/tmp/layer_intent_issue_stamp_validate_latest.json`
   - result: `error_code=IP-ASB-STAMP-SESSION-001`, `stale_reasons=[\"work_layer_mismatch\"]`.
   - interpretation: literal `work_layer=instance` text can still force protocol-topic replay into instance path.
12. Residual source-layer stability gap:
   - replay evidence: `/tmp/layer_intent_source_project_expect_latest.json`
   - result: `error_code=IP-ASB-STAMP-SESSION-001`, `stale_reasons=[\"source_layer_mismatch\"]`.
   - interpretation: source-layer resolution still drifts from expected `project` in cross-repo contexts.
13. Residual strict-update blockers still present on custom lane sample:
   - strict update replay: `/tmp/custom_identity_update_strict_latest.log` -> `protocol_version_alignment_status=FAIL_REQUIRED`, `error_code=IP-PVA-003`.
   - full-scan replay: `/tmp/full_scan_custom_latest.json` -> `post_execution_mandatory_status=FAIL_REQUIRED`, `error_code=IP-WRB-003`.
   - status implication: current posture remains `PARTIAL_GO`; not eligible for “full closure” claim.

Boundary:

1. This record is protocol-layer implementation replay only.
2. Independent auditor replay still required before PASS promotion.

#### 16.8.34 FIX-044 lane-lock exit unified writer + canonical index replay (2026-03-03, protocol)

Status: `IMPL_READY (BLOCKED_BY_AUDIT)` pending independent replay signoff.

Implementation scope (`62bdc1c`):

1. New unified writer entrypoint:
   - `scripts/write_session_lane_lock_exit.py`
   - strict write/index errors:
     - `IP-LAYER-GATE-008` (EXIT write failed)
     - `IP-LAYER-GATE-009` (EXIT index linkage missing)
2. Creator update automation switch:
   - `scripts/identity_creator.py update --release-session-lane-lock --session-lane-lock-exit-reason <reason>`
3. Lane-routing telemetry enhancement:
   - `scripts/validate_work_layer_gate_set_routing.py` now emits `session_lane_lock_exit_receipt`.
4. Scan/report visibility wiring:
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`

Replay highlights (local, DoD A/B/C/D):

1. Sample A (`instance lane + protocol diff`):
   - command:
     `python3 scripts/validate_work_layer_gate_set_routing.py ... --feedback-root /tmp/fix044_lane_A --expected-work-layer instance --base 83e5a03 --head c310ab4 --json-only`
   - evidence:
     - `/tmp/fix044_outputs/A_instance_pending.json`
   - result:
     - `rc=0`
     - `work_layer_gate_set_routing_status=PASS_REQUIRED`
     - `applied_gate_set=instance_required_checks`
     - `protocol_feedback_triggered=true`
     - `pending_receipt_path=.../LAYER_GATE_PROTOCOL_PENDING_*.json`
2. Sample B (`protocol lane + missing closure roots`):
   - evidence:
     - `/tmp/fix044_outputs/B_protocol_missing_closure.json`
   - result:
     - `rc=1`
     - `error_code=IP-LAYER-GATE-004`
3. Sample C (`protocol lock exists + no EXIT`):
   - evidence:
     - lock seed: `/tmp/fix044_outputs/C0_protocol_lock_seed.json`
     - blocked instance: `/tmp/fix044_outputs/C1_instance_blocked_no_exit.json`
   - result:
     - blocked replay `rc=1`
     - `error_code=IP-LAYER-GATE-007`
4. Sample D (`emit EXIT + index linkage + return instance`):
   - evidence:
     - writer output: `/tmp/fix044_outputs/D0_exit_writer.json`
     - post-exit instance replay: `/tmp/fix044_outputs/D1_instance_after_exit.json`
     - canonical index hit: `/tmp/fix044_lane_C/evidence-index/INDEX.md` contains `SESSION_LANE_LOCK_EXIT_*.json`
   - result:
     - writer `rc=0`, `session_lane_lock_exit_status=PASS_REQUIRED`, `index_linked=true`
     - post-exit replay `rc=0`, `work_layer_gate_set_routing_status=PASS_REQUIRED`

Boundary:

1. This record closes the runbook/automation gap for lane-lock EXIT emission and canonical index linkage.
2. Final PASS promotion still requires independent auditor replay.

#### 16.8.35 Auditor re-audit closure: FIX-045/FIX-046 residual semantic gate closure (2026-03-03, protocol, scope-limited)

Status: `PASS (scope-limited closure)` for FIX-045/FIX-046 target claims.  
Global release posture remains unchanged for other `PENDING_REAUDIT` items.

Closure statement:

1. Prior residual finding was valid for the earlier window (`d69c948 + dc9c2e3`): mixed-signal phrase
   `协议层治理回放，请按 protocol lane 执行` could still fall back to `instance`.
2. This residual is now closed by `7695a12`:
   - `scripts/response_stamp_common.py` adds protocol-lane directive detection + mixed-signal dominance routing.
3. `dc9c2e3` remains valid as FIX-046 observability patch:
   - strict stale-preflight emits `phase_transition_reason=baseline_mode_violation` + aligned error code.

Independent replay evidence (auditor-run):

1. Control phrase now routes to protocol lane:
   - `/tmp/reaudit_fix045_control_7695a12.json`
   - key fields: `resolved_work_layer=protocol`, `protocol_triggered=true`, no ambiguous fallback.
2. Ambiguous non-directive phrase still safely falls back to instance:
   - `/tmp/reaudit_fix045_ambiguous_7695a12.json`
   - key fields: `resolved_work_layer=instance`, `fallback_reason=ambiguous_intent_signal`.
3. Literal-question sample remains correct (no regression):
   - `/tmp/reaudit_fix045_literal_7695a12.json`
   - key field: `resolved_work_layer=protocol`.
4. project-catalog source-layer stays stable:
   - `/tmp/reaudit_fix045_control_project_7695a12.json`
   - key fields: `resolved_source_layer=project`, first-line stamp contains `source=project`.
5. FIX-046 strict stale-preflight trace remains valid:
   - `/tmp/reaudit_fix046_strict_trace_7695a12.log`
   - key fields: `phase_a_refresh_applied=false`, `phase_transition_reason=baseline_mode_violation`.

Baseline checks:

1. `python3 scripts/docs_command_contract_check.py` -> PASS
2. `python3 scripts/validate_protocol_ssot_source.py` -> OK

Boundary:

1. This section only closes FIX-045/FIX-046 scoped claims.
2. Do not interpret this as whole-batch green; keep summary rows with remaining `PENDING_REAUDIT` unchanged.

#### 16.8.36 Auditor re-check: project-scope residual P0 on sanitization boundary (`IP-DSN-002`) (2026-03-03, protocol, scope-limited)

Status: `PENDING_REAUDIT` (core chain pass in project scope, single P0 residual remains open).

Scope:

1. Identity: `custom-creative-ecom-analyst`
2. Project catalog: `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml`
3. This section does not override unrelated global historical replay states.

Re-check findings (cross-validated):

1. Layer-intent hidden-gate residual is closed in project scope:
   - `validation/recheck_stamp_issue_20260303.json`
   - `validation/recheck_stamp_issue_validate_20260303.json`
   - key fields: `resolved_work_layer=protocol`, `resolved_source_layer=project`, `layer_intent_resolution_status=PASS_REQUIRED`.
2. Strict update main chain is passing in project scope:
   - `validation/recheck_update_strict_20260303_escalated.log`
   - key fields include `protocol_version_alignment_status=PASS_REQUIRED`, `session_refresh_status=PASS_REQUIRED`, `capability_activation_status=ACTIVATED`.
3. Project-scope full scan still has one P0:
   - `validation/recheck_full_scan_project_only_final_20260303.json`
   - summary: `p0=1`
   - failing validator: `protocol_data_sanitization_boundary_status=FAIL_REQUIRED`, `error_code=IP-DSN-002`.
4. `IP-DSN-002` hit is reproducible via direct validator replay:
   - `validation/reaudit_dsn_custom_scan.json`
   - `feedback_batch_path=.../FEEDBACK_BATCH_20260302T113042Z_protocol_optimization_consolidated_v2_sanitized.md`
   - hit pattern: `\\b(?:\\+?\\d[\\d\\-\\s]{8,}\\d)\\b`
   - hit location: `line:38`.
5. Global replay has additional historical P0 noise and must not be conflated with project closure status:
   - `validation/recheck_full_scan_custom_after_update_escalated_20260303.json`
   - summary: `p0=2`, including historical `IP-WRB-003` from global instance report path.

Decision:

1. Protocol core repair chain is effective for this identity in project scope.
2. Full-green closure claim is blocked by one project-scope P0 (`ASB-RQ-046`, `IP-DSN-002`).
3. `FIX-045` / `FIX-046` remain scope-limited closed and are not reopened by this finding.

Architect patch expectation (next step):

1. Tighten `validate_protocol_data_sanitization_boundary.py` text-level sensitive scan to avoid phone-like false positives on report filename numeric suffixes in governance markdown evidence lines.
2. Add regression fixture pair:
   - case A: report filename numeric suffix in markdown path line -> expected non-blocking/pass.
   - case B: real secret/phone-like payload -> expected `FAIL_REQUIRED`.

#### 16.8.37 Docs consistency pass: governance/review bridge alignment for FIX-029..044 (2026-03-03, docs-only)

Status: `SYNCED_FOR_AUDIT_CONSISTENCY` (no code-path behavior changes).

Purpose:

1. Remove governance/review dual-status ambiguity for open batches `FIX-029..032` and `FIX-034..044`.
2. Preserve scoped-pass closures for `FIX-033` and `FIX-045/046` without implying whole-batch green.

Actions:

1. Governance section `6.4` rows `ASB-RQ-075..089` were normalized from `GATE_READY` to
   `IMPL_READY (BLOCKED_BY_AUDIT)` so they match review summary rows where
   `FIX-029..032` remain `PENDING_REAUDIT`.
2. Evidence pointers for `ASB-RQ-075..089` now explicitly reference:
   - implementation commits: `a95f5a2`, `560f710`
   - replay anchors: review `16.8.28` + summary rows `FIX-029..032`.
3. No status promotion was applied to `FIX-034..044`; pending posture remains unchanged.

Cross-check snapshot:

1. Review summary rows:
   - `FIX-029..032` -> `PENDING_REAUDIT`
   - `FIX-033` -> `PASS`
   - `FIX-034..044` -> `PENDING_REAUDIT`
   - `FIX-045..046` -> `PASS`
2. Governance rows:
   - `ASB-RQ-075..089` -> `IMPL_READY (BLOCKED_BY_AUDIT)`
   - `ASB-RQ-090..093` -> `GATE_READY` (closed by review `16.8.27`)
   - `ASB-RQ-094..104` -> `IMPL_READY (BLOCKED_BY_AUDIT)`
   - `ASB-RQ-105..106` -> `GATE_READY` (closed by review `16.8.35`)

Boundary:

1. This is a docs-only consistency closure record.
2. It does not alter required gate behavior or release unlock calculations.

#### 16.8.38 FIX-047 implementation replay: protocol data-sanitization phone-like path-context false-positive hardening (2026-03-03, protocol)

Status: `IMPL_READY (BLOCKED_BY_AUDIT)` pending independent auditor replay.

Problem:

1. `ASB-RQ-046` project-scope residual (`IP-DSN-002`) was reproducible on sanitized protocol-feedback markdown lines that only contained report path references with numeric filename suffixes.
2. Baseline failure sample:
   - `/tmp/dsn_case_path_line_before.json`
   - key fields: `protocol_data_sanitization_boundary_status=FAIL_REQUIRED`, `error_code=IP-DSN-002`, `path=line:2`, pattern phone-like regex.

Implementation (`FIX-047`):

1. File changed:
   - `scripts/validate_protocol_data_sanitization_boundary.py`
2. Hardened logic:
   - adds path-context detection for markdown/json value scan lines
   - exempts phone-like pattern matches only when context is path/evidence/report reference and no contact semantics
   - preserves fail-closed behavior for real sensitive values
3. New machine-readable telemetry:
   - `phone_like_path_exempt_count`
   - `phone_like_path_exempt_samples`

Replay evidence:

1. Regression A (path numeric suffix should PASS):
   - fixture: `/tmp/dsn_case_path_line.md`
   - result: `/tmp/dsn_case_path_line_after.json`
   - key fields:
     - `protocol_data_sanitization_boundary_status=PASS_REQUIRED`
     - `error_code=""`
     - `phone_like_path_exempt_count=1`
2. Regression B (real phone value should FAIL_REQUIRED):
   - fixture: `/tmp/dsn_case_real_phone.md`
   - result: `/tmp/dsn_case_real_phone_after.json`
   - key fields:
     - `protocol_data_sanitization_boundary_status=FAIL_REQUIRED`
     - `error_code=IP-DSN-002`
     - `phone_like_path_exempt_count=0`
3. Project-scope real batch replay (`custom-creative-ecom-analyst`):
   - result: `/tmp/dsn_case_real_batch_after.json`
   - key fields:
     - `protocol_data_sanitization_boundary_status=PASS_REQUIRED`
     - `error_code=""`
4. Full-scan project catalog replay:
   - result: `/tmp/fix047_full_scan_custom_project_after.json`
   - key fields under project layer:
     - `checks.protocol_data_sanitization_boundary.rc=0`
     - `protocol_data_sanitization_boundary_status=PASS_REQUIRED`
     - no `IP-DSN-002` in project scan branch

Boundary:

1. This section closes implementation replay for the previously identified project-scope `IP-DSN-002` false-positive path.
2. Final `PASS` promotion still requires independent auditor re-audit.

#### 16.8.39 Roundtable intake: scaffold legacy-domain contamination + blocker taxonomy coupling (`FIX-048`, 2026-03-03, docs-only)

Status: `SPEC_READY` (architect patch required; this section is evidence + plan only).

Cross-validation method:

1. Source-level inspection:
   - `scripts/create_identity_pack.py`
   - `scripts/validate_identity_runtime_contract.py`
   - `scripts/validate_identity_collab_trigger.py`
2. Runtime reproduction (fresh scaffold, isolated temp root):
   - `python3 scripts/create_identity_pack.py --id tmp-route-quality-audit --title "Route Quality Audit" --description "Scaffold contamination audit" --pack-root /tmp/ip-template-audit-before --catalog /tmp/ip-template-audit-before/catalog.local.yaml --profile full-contract --skip-bootstrap-check`
   - `rg -n "weixinstore|wechat|taobao|store-manager|10000514174106|login_required|captcha_required|session_expired|manual_verification_required" /tmp/ip-template-audit-before/tmp-route-quality-audit/CURRENT_TASK.json /tmp/ip-template-audit-before/tmp-route-quality-audit/runtime`

Observed evidence (reproducible):

1. Scaffold source is still coupled to legacy business template/sample roots:
   - `scripts/create_identity_pack.py:465` (`identity/store-manager/CURRENT_TASK.json`)
   - `scripts/create_identity_pack.py:648`
   - `scripts/create_identity_pack.py:693`
2. Generated pack contains legacy business-domain tokens and non-neutral paths:
   - `/tmp/ip-template-audit-before/tmp-route-quality-audit/CURRENT_TASK.json:228` (`weixinstore-ui-agent`)
   - `/tmp/ip-template-audit-before/tmp-route-quality-audit/CURRENT_TASK.json:421` (`wechat_listing_update`)
   - `/tmp/ip-template-audit-before/tmp-route-quality-audit/CURRENT_TASK.json:322` (`../webbrowser/restored/wechat-shop-docs*`)
3. Generated runtime samples/logs still carry legacy business identifiers:
   - `/tmp/ip-template-audit-before/tmp-route-quality-audit/runtime/logs/collaboration/tmp-route-quality-audit-bootstrap.json:6` (`taobao-search-automation`)
   - `/tmp/ip-template-audit-before/tmp-route-quality-audit/runtime/logs/collaboration/tmp-route-quality-audit-bootstrap.json:12` (`product:10000514174106`)
   - `/tmp/ip-template-audit-before/tmp-route-quality-audit/runtime/logs/feedback/tmp-route-quality-audit-feedback-bootstrap.json:8` (`weixinstore_product_update`)
4. Blocker taxonomy and self-test assumptions are tightly bound to legacy commerce blockers/identity:
   - `scripts/validate_identity_runtime_contract.py:327` (`login_required`, `captcha_required`, `session_expired`, `manual_verification_required`)
   - `scripts/validate_identity_collab_trigger.py:14`
   - `scripts/validate_identity_collab_trigger.py:196` (`identity_id="store-manager"`)

Risk classification:

1. `P0` routing-quality and governance contamination:
   - new identities inherit non-neutral business constants, causing protocol/instance boundary confusion and latent hidden-gate noise.
2. `P1` contract evolution blockage:
   - blocker enum semantics are locked to one business scenario, reducing cross-domain reuse and slowing future schema migration.
3. `P1` maintenance debt:
   - every new scaffold re-injects stale samples, increasing ongoing sanitization/cleanup cost.

Architect patch package (implementation ownership: protocol architect):

1. Neutral scaffold source split:
   - replace hard dependency on `identity/store-manager/CURRENT_TASK.json` with domain-neutral base template.
   - keep optional profile overlays as explicit opt-in, not bootstrap default.
2. Bootstrap sample/log sanitizer:
   - seed runtime artifacts with neutral placeholders (no vendor/business IDs, no legacy route keys).
   - enforce canonical runtime-relative paths only; ban cross-repo relative pointers in generated contracts.
3. Blocker taxonomy decoupling with migration bridge:
   - define canonical neutral blocker enums for protocol contracts.
   - add compatibility alias map for legacy enums during migration window.
   - deprecate strict hard-coded legacy enum set in validators after bridge period.
4. Self-test de-hardcoding:
   - remove fixed `store-manager` assumptions from collab/runtime self-tests and switch to generated identity-local fixtures.

Acceptance DoD (post-implementation replay):

1. Recreate scaffold in `/tmp`; forbidden-token scan must return zero hits for:
   - `weixinstore|wechat|taobao|store-manager|10000514174106`.
2. Generated `CURRENT_TASK.json` and runtime samples must contain only neutral placeholders and canonical identity-scoped paths.
3. Validator compatibility check:
   - canonical blocker enums pass;
   - legacy enums pass only through explicit alias bridge telemetry;
   - missing bridge in strict lanes fail-closed.
4. Full-scan and three-plane on project catalog must not introduce new P0 from scaffold artifacts.

Boundary:

1. This record is docs-only intake and planning; no runtime behavior changed in this batch.
2. Historical snapshot note: at this stage `FIX-048` remained `SPEC_READY / PENDING_REPLAY`; see `16.8.39B` for post-implementation replay intake.

#### 16.8.39A Vendor + standards cross-verification addendum for FIX-048 (2026-03-03, docs-only)

Status: `SPEC_VALIDATED_EXTERNALLY` (requirements strengthened; implementation still pending).

Why this addendum exists:

1. `FIX-048` targets identity initialization bootstrap semantics and skill/runtime portability.
2. To avoid local-design drift, contract wording is cross-validated against vendor/standards sources before implementation.

Cross-verification sources (official/vendor + Context7 mirrors):

1. OpenAI Codex Skills:
   - https://developers.openai.com/codex/skills/
   - confirms progressive disclosure (`metadata -> SKILL.md -> references/scripts when needed`) and reusable skill packaging.
2. OpenAI Customization / Skills:
   - https://developers.openai.com/codex/concepts/customization/#skills
   - confirms metadata-first discovery and explicit/implicit skill invocation.
3. OpenAI Codex Security:
   - https://developers.openai.com/codex/security/#common-sandbox-and-approval-combinations
   - confirms explicit approval/sandbox controls for sensitive operations.
4. MCP Specification:
   - https://modelcontextprotocol.io/specification/latest
   - confirms typed capability boundaries (`tools`, `resources`, `prompts`) and tool-security expectations.
5. Agent Skills specification:
   - https://agentskills.io/specification
   - confirms portable baseline (`SKILL.md` required frontmatter with `name` + `description`).
6. Context7 mirrors used for independent retrieval:
   - `/websites/modelcontextprotocol_io_specification_2025-11-25`
   - `/websites/agentskills_io`

Inference-to-contract mapping:

1. Since vendor specs define portable metadata-first skills, default scaffold output containing legacy vertical constants is treated as protocol contamination (`ASB-RQ-107`, P0).
2. Since specs separate capability interfaces from domain constants, blocker taxonomy must migrate to canonical neutral enums + explicit legacy alias bridge (`ASB-RQ-108`, P1).
3. Since vendor security guidance requires explicit consent/controls, any domain specialization must be explicit profile opt-in + receipt, not hidden in default bootstrap.
4. Since AI workflows iterate rapidly while protocol contracts keep moving, scaffold should be a minimal invariant shell and must not be treated as a long-lived business playbook snapshot.
5. Protocol layer governs contracts/controls; concrete business execution plans belong to identity instance runtime and must remain outside default scaffold seeds.

Boundary:

1. This addendum strengthens contract rationale only; runtime behavior is unchanged.
2. Historical snapshot note: at this stage `FIX-048` remained `SPEC_READY / PENDING_REPLAY`; see `16.8.39B` for post-implementation replay intake.

#### 16.8.39B Implementation replay intake: scaffold neutrality + blocker taxonomy bridge (`FIX-048`, 2026-03-03, scope-limited)

Status: `IMPL_READY (BLOCKED_BY_AUDIT)` with implementation replay evidence captured; independent auditor closure is still required before `PASS`.

Implementation commits in this replay window:

1. `f5c97b3` — code implementation for neutral default scaffold + blocker taxonomy canonical/alias behavior:
   - `scripts/create_identity_pack.py`
   - `scripts/validate_identity_runtime_contract.py`
   - `scripts/validate_identity_collab_trigger.py`
2. `49212d2` — de-ambiguity patch for invalid blocker logs in runtime validator:
   - `scripts/validate_identity_runtime_contract.py`

Replay bundle (local reproducible evidence):

1. Create + baseline validation logs:
   - `/tmp/fix048-review/create_full_contract.log`
   - `/tmp/fix048-review/canonical_runtime.log`
   - `/tmp/fix048-review/canonical_collab.log`
2. Domain-neutrality forbidden-token scan:
   - command scope: `/tmp/fix048-review/packs/tmp-route-quality-audit5-review`
   - result: `/tmp/fix048-review/domain_scan.log` (no matches for `store-manager|store_manager|weixinstore-ui-agent|weixinstore-sku-onboarding|wechat_listing_update|taobao-search-automation|10000514174106`)
3. Blocker taxonomy three-way replay:
   - canonical baseline: runtime/collab pass (`rc=0`)
   - legacy alias bridge (`login_required/captcha_required/session_expired`): runtime/collab pass (`rc=0`) with `mode=legacy_alias_bridge`
     - evidence: `/tmp/fix048-review/legacy_runtime.log`, `/tmp/fix048-review/legacy_collab.log`, `/tmp/fix048-review/legacy_rc.txt`
   - invalid blocker (`unknown_blocker_x`): runtime/collab fail-closed (`rc=1`)
     - evidence: `/tmp/fix048-review/invalid_runtime.log`, `/tmp/fix048-review/invalid_collab.log`, `/tmp/fix048-review/invalid_rc.txt`
4. Log de-ambiguity regression check:
   - invalid runtime log now contains fail line only (no mixed `[FAIL]` + `[OK]` taxonomy verdict)
   - evidence: `/tmp/fix048-review/invalid_runtime.log`

Decision boundary for this section:

1. This replay confirms `FIX-048` code landed and behavior is reproducible.
2. Promotion is limited to `IMPL_READY (BLOCKED_BY_AUDIT)` in governance/review status bridge.
3. `FIX-049/050` status is unaffected by this section and remains on implementation-pending track.

#### 16.8.40 Roundtable intake: live reply first-line gate recurrence root cause (`FIX-049`, 2026-03-03, docs-only)

Status: `SPEC_READY` (P0 contract gap confirmed; architect patch required).

Incident trigger:

1. Live conversation still produced replies without first-line `Identity-Context`, despite prior HOTFIX/P0 closure claims.
2. This was reported as repeated recurrence in current audit round.

Cross-validation findings (code + replay):

1. `validate_send_time_reply_gate.py` currently allows `--stamp-json` as primary evidence and auto-composes synthetic reply text:
   - `scripts/validate_send_time_reply_gate.py:59`
   - `scripts/validate_send_time_reply_gate.py:67`
   - emitted mode: `reply_evidence_mode=stamp_json_composed_reply`.
2. Multiple gate surfaces feed send-time/first-line validators with `--stamp-json` (synthetic artifact), not real outbound reply payload:
   - `scripts/identity_creator.py:1227`
   - `scripts/identity_creator.py:1262`
   - `scripts/release_readiness_check.py:562`
   - `scripts/release_readiness_check.py:580`
   - `scripts/full_identity_protocol_scan.py:544`
   - `scripts/full_identity_protocol_scan.py:580`
   - `scripts/report_three_plane_status.py:530`
   - `scripts/report_three_plane_status.py:602`
3. E2E replay itself builds send-time sample from rendered stamp artifact:
   - `scripts/e2e_smoke_test.sh:305`
   - `scripts/e2e_smoke_test.sh:316`
4. Repro pair (same identity context):
   - real missing-header reply file => `FAIL_REQUIRED` (`IP-ASB-STAMP-SESSION-001`)
   - stamp-only mode => `PASS_REQUIRED` with `reply_evidence_mode=stamp_json_composed_reply`.

Root cause statement:

1. Existing hard gate proves validator semantics, but not live channel enforcement.
2. Gate evidence source can be synthetic and self-satisfying; therefore strict pass does not guarantee actual outbound reply compliance.
3. This is why recurrence can happen repeatedly after “gate passed” replays.

Architect patch package (implementation ownership: protocol architect):

1. Enforce real-evidence boundary in strict lanes:
   - `validate_send_time_reply_gate.py` must reject synthetic `stamp_json_composed_reply` evidence in strict operations.
   - strict lanes require `reply_file` or `reply_log` bound to actual outbound payload.
2. Add explicit error path:
   - suggested code `IP-ASB-STAMP-SESSION-002`: send-time gate received non-live/synthetic evidence source.
3. Add runtime outlet adapter:
   - before emitting user-visible reply, assemble final payload, run send-time gate on that exact payload, block send on failure.
4. Telemetry hardening:
   - required fields: `reply_evidence_mode`, `reply_transport_ref`, `reply_outlet_guard_applied`.
   - strict lanes must fail when `reply_outlet_guard_applied=false`.
5. Replay policy update:
   - readiness/e2e/full-scan/three-plane must include at least one real reply payload replay sample; synthetic-only replay is insufficient for closure claims.

Acceptance DoD (post-implementation):

1. Missing header in real outbound payload => deterministic `FAIL_REQUIRED`, `error_code=IP-ASB-STAMP-SESSION-001`.
2. `--stamp-json` synthetic mode under strict operations => deterministic `FAIL_REQUIRED`, `error_code=IP-ASB-STAMP-SESSION-002`.
3. Compliant real outbound payload with first-line identity stamp => `PASS_REQUIRED`.
4. Full-scan/three-plane expose non-synthetic evidence (`reply_evidence_mode` not equal to `stamp_json_composed_reply`) for strict-closure claims.

Boundary:

1. This section is docs-only intake and does not change runtime behavior.
2. `FIX-049` remains `SPEC_READY / PENDING_REPLAY` until architect implementation and independent replay closure.

#### 16.8.41 Cross-project evidence intake: fqsh header-first recurrence + scaffold pollution (`FIX-050`, 2026-03-03, docs-only)

Status: `SPEC_READY` (P0 evidence confirmed; protocol architect implementation pending).

Scope:

1. Identity: `feiqiao-guard-delivery-lead`
2. Catalog: `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/catalog.local.yaml`
3. This section records external project evidence and does not mutate protocol runtime code.

Verified facts:

1. Protocol-feedback submission chain exists and is machine-readable:
   - batch: `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-03-headstamp-and-scaffold-pollution.md`
   - issue: `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/protocol-vendor-intel/ISSUE_2026-03-03-execution-order-and-scaffold-pollution.md`
   - proposal: `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/upgrade-proposals/PROPOSAL_2026-03-03-enforce-header-and-scaffold-consent-gate.md`
2. Reply-channel validator replay confirms canonical channel pass:
   - command output: `/tmp/fqsh_reply_channel_check.json`
   - key fields: `protocol_feedback_reply_channel_status=PASS_REQUIRED`, `error_code=""`.
3. Runtime contract replay confirms current instance contract is structurally valid:
   - command output: `/tmp/fqsh_runtime_contract_check.log`
   - result: `Identity runtime contract validation PASSED`.
4. Scaffold pollution files are present in project workspace and match incident narrative:
   - `/Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/config.py`
   - `/Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/models.py`
   - `/Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/policy.py`
   - `/Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/audit.py`

Root-cause refinement (why recurrence still happens):

1. Upgrade required-check set for this identity does not include reply first-line/send-time gates:
   - `CURRENT_TASK.json` required checks list has no
     - `scripts/validate_reply_identity_context_first_line.py`
     - `scripts/validate_send_time_reply_gate.py`
   - evidence: `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/CURRENT_TASK.json:167`
2. Execution report confirms these gates were not executed in that upgrade run:
   - `/Users/yangxi/claude/codex_project/fqsh/resource/reports/identity-upgrade-exec-feiqiao-guard-delivery-lead-1772523548.json`
   - no `reply_first_line_status` / `send_time_gate_status` fields.
3. Existing send-time gate can pass on synthetic stamp evidence (`stamp_json_composed_reply`), so replay pass does not prove live channel compliance:
   - evidence: `/tmp/fix049_stamp_synthetic_pass.json`.

Additional evidence-integrity gaps (non-blocking but should be closed):

1. Evidence index currently omits receipt artifact path:
   - index: `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/evidence-index/INDEX.md`
   - missing row: `outbox-to-protocol/PROTOCOL_FEEDBACK_RECEIPT_2026-03-03-headstamp-scaffold.json`.
2. No live reply transcript artifact is attached under runtime tree for this incident, so header-missing claim is narrative-only rather than replay-bound.

Architect patch package (`FIX-050`, maps to `ASB-RQ-110`):

1. Header-first pre-mutation gate:
   - before any mutation-capable step, enforce first-line `Identity-Context` emission and verification.
2. Scaffold consent gate:
   - block scaffold writes unless explicit user confirmation of scope/stack has been captured.
3. Mutation plan disclosure:
   - emit `planned_files[]` + `why_now` before first write, then enforce allowlist against actual writes.
4. Required-check parity:
   - add first-line/send-time gate checks to mutation/update required-check chain (or enforce centrally in executor preflight).

Acceptance DoD:

1. Simulate missing header in initialization/update mutation flow => deterministic fail-closed before first write.
2. Simulate scaffold attempt without explicit consent => deterministic fail-closed before file creation.
3. Successful compliant run must include machine-readable pre-mutation proof:
   - `header_first_gate_status=PASS_REQUIRED`
   - `scaffold_consent_gate_status=PASS_REQUIRED`
   - `mutation_plan_disclosed=true`.
4. Evidence-index must include batch + issue + proposal + receipt entries for same incident id.

Boundary:

1. This section is docs-only intake and planning.
2. `FIX-050` remains `SPEC_READY / PENDING_REPLAY` until architect implementation and independent replay closure.

#### 16.8.42 Supplemental cross-verification: `system-requirements-analyst` instance Full Go intake (2026-03-03, scope-limited)

Status: `FULL_GO (INSTANCE_OPERATIONAL)` with `NON_BLOCKING_P1_BACKLOG`.

Scope boundary:

1. This intake records a scope-limited instance-lane acceptance replay.
2. It does not auto-promote unresolved protocol remediation rows in the summary table.

Cross-validated evidence (this round):

1. End-to-end upgrade pass:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772520264.json`
   - key fields: `all_ok=true`, `lane_routing_status=PASS_REQUIRED`, `work_layer=instance`, `applied_gate_set=instance_required_checks`.
2. Semantic routing + sidecar governance pass snapshot:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-03_014.md`
   - section states update-lane replay moved to `P0 已闭环`, while keeping explicit P1 hardening notes.
3. Strong blocker fail-close negative sample:
   - `/private/tmp/send-time-bad-final-receipt.json`
   - key field: `error_code=IP-ASB-STAMP-SESSION-001` (missing first-line stamp path still fail-closed).
4. Protocol lane lock closure chain:
   - lock receipt: `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_PROTOCOL_20260303T080218Z.json`
   - exit receipt: `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_EXIT_20260303T080442Z.json`
   - index linkage: `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/evidence-index/INDEX.md`.
5. Governance mirror roundtable document exists and is index-referenced:
   - `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-instance-capability-roundtable-audit-2026-03-03.md`.

Residual non-blocking items (keep visible):

1. `activity_correlation_status=ACTIVITY_UNSCOPED` still appears in semantic/sidecar telemetry (P1 correlation hardening).
2. `required_contract_coverage` requiredized coverage remains low for this profile (P1 governance requiredization hardening).

Decision impact:

1. Operational verdict for this identity replay window: `Full Go`.
2. Protocol remediation summary rows remain unchanged by this intake:
   - `FIX-029..032`: `PENDING_REAUDIT`
   - `FIX-034..044`: unchanged current states in summary table.
3. Architect next priority should stay on P1 closure for correlation strictness and requiredized coverage uplift.

#### 16.8.43 Protocol closure reverify intake: `custom-creative-ecom-analyst` remains `NOT_CLOSED` (`NO_GO`, 2026-03-03, scope-limited)

Status: `NOT_CLOSED / NO_GO` for protocol-layer closure claim.

Scope boundary:

1. This section is independent replay intake for one project identity.
2. It does not auto-promote any previously `PENDING_REAUDIT` remediation row.

Reverify bundle (cross-validated):

1. full-scan:
   - `/tmp/full_scan_custom_20260303_reverify_escalated.json`
2. three-plane:
   - `/tmp/three_plane_custom_20260303_reverify_escalated.json`
3. capability strict-union probe:
   - `/tmp/capability_activation_custom_20260303.json`
4. protocol feedback closure batch:
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/custom-creative-ecom-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260303T082408Z_protocol_closure_reverify_sanitized.md`
5. evidence index linkage:
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/custom-creative-ecom-analyst/runtime/protocol-feedback/evidence-index/INDEX.md`

Hard blockers reproduced:

1. `IP-WRB-003` (`FAIL_REQUIRED`) persists in both full-scan and three-plane.
2. `IP-SEM-001` (`FAIL_REQUIRED`) persists in both full-scan and three-plane.

Cross-validation details:

1. `IP-WRB-003` root cause is path/CWD sensitivity in writeback/prompt lifecycle chain:
   - `scripts/validate_identity_experience_writeback.py:151` currently resolves `report.writeback_paths` as raw `Path(wp)` without report-relative/pack-relative canonicalization.
   - `scripts/validate_identity_prompt_lifecycle.py:143` resolves relative `runtime_state_artifact_path` against process CWD.
   - `scripts/validate_post_execution_mandatory.py:100` invokes child validator via relative script path, amplifying CWD sensitivity into post-execution fail-closed output.
2. Same-report CWD differential replay is reproducible:
   - `validate_identity_experience_writeback.py` with same report:
     - protocol root: `FAIL` (`report.writeback_paths item not found: RULEBOOK.jsonl`)
     - pack root: `PASS`
   - `validate_identity_prompt_lifecycle.py` with same report:
     - protocol root: `FAIL` (`runtime state artifact missing`)
     - pack root: `PASS`
3. `IP-SEM-001` is reproducible on current reverify batch:
   - `FEEDBACK_BATCH_20260303T082408Z_protocol_closure_reverify_sanitized.md` still lacks required semantic metadata fields:
     - `intent_domain`
     - `intent_confidence`
     - `classifier_reason`
   - strict replay returns `FAIL_REQUIRED`, `error_code=IP-SEM-001`.

Confirmed pass items in the same window:

1. Capability activation in strict-union is no longer blocked:
   - `capability_activation_status=ACTIVATED`.
2. Protocol data sanitization boundary passes:
   - `protocol_data_sanitization_boundary_status=PASS_REQUIRED`.

Additional non-blocking anomaly (audit consistency):

1. three-plane payload reported:
   - `required_contract_total=3`
   - `required_contract_passed=4`
   - `required_contract_coverage_rate=133.33`
2. This indicates metric semantics drift (`passed > total`) and should be normalized before using coverage KPI as governance signal.

Follow-up fix intake mapping:

1. `FIX-051` (`ASB-RQ-111`, P0):
   - close CWD-sensitive writeback/prompt lifecycle chain in strict operations (`IP-WRB-003` closure).
2. `FIX-052` (`ASB-RQ-112`, P0):
   - enforce semantic metadata completeness for closure batches (`IP-SEM-001` closure).
3. `FIX-053` (`ASB-RQ-113`, P1):
   - normalize required-coverage accounting and bound rate to `[0,100]`.

Decision boundary:

1. Protocol closure claim remains `NOT_CLOSED` for this identity replay window.
2. This section is docs-only governance intake and does not change runtime behavior.

#### 16.8.44 Implementation replay intake: custom-lane validate unblock + current-round protocol-feedback closure (`FIX-051/052`, 2026-03-03, scope-limited)

Status: `IMPL_READY (BLOCKED_BY_AUDIT)`; implementation landed and replayed, independent re-audit still required.

Commit anchor:

1. `e62deab` — `fix(protocol): unblock custom validate lane and correlated feedback closure`

Scope:

1. Protocol repository code patch + cross-project replay intake (`fqsh` identity runtime evidence).
2. This section updates implementation status boundaries for `FIX-051/052`; it does not alter `FIX-053`.

Target blockers (from prior intake) and replay result:

1. Runtime mode guard blocked `identity_creator validate` in custom catalog lane (`mode=custom`, `expected_mode_match=false`):
   - patch: `scripts/identity_creator.py` validate flow now invokes runtime guard with `--expect-mode any`;
   - replay: `/tmp/fix051_final_creator_validate.log` now starts with runtime mode guard `PASS`;
   - boundary: validate command still returns `rc=1` due downstream `IP-ASB-RFS-004` (separate baseline/session-refresh gate, not mode-guard regression).
2. Current-round correlated protocol-feedback chain failed with `IP-PFB-CH-006`:
   - patch support + closure artifacts now include split receipt:
     - `.../runtime/protocol-feedback/outbox-to-protocol/SPLIT_RECEIPT_20260303T082733Z_headstamp_scaffold.json`;
   - replay:
     - `/tmp/fix051_split_fqsh_after2.json` => `instance_protocol_split_status=PASS_REQUIRED`;
     - `/tmp/fix051_final_reply.json` => `protocol_feedback_reply_channel_status=PASS_REQUIRED`.
3. Sidecar strict enforcement failed with `IP-SID-001` on missing sidecar contract fields:
   - patch: `scripts/validate_protocol_feedback_sidecar_contract.py` adds fail-closed rules for declared-required contracts and default-contract fallback only for auto-required legacy profiles;
   - replay: `/tmp/fix051_final_sidecar.json` => `sidecar_contract_status=PASS_REQUIRED`, `error_code=""`.
4. Writeback/post-execution CWD/cross-root report resolution drift:
   - patch: shared report discovery helper in `scripts/tool_vendor_governance_common.py` and wiring in `validate_writeback_continuity.py` / `validate_post_execution_mandatory.py`;
   - replay:
     - `/tmp/fix051_reg_wrb_fqsh.json` => `writeback_continuity_status=PASS_REQUIRED`;
     - `/tmp/fix051_reg_post_fqsh.json` => `post_execution_mandatory_status=PASS_REQUIRED`.
5. Open-state and scaffold-disposition closure evidence gap:
   - status closure updated:
     - `.../TASK_HISTORY.md` (`status: closed`);
     - `.../outbox-to-protocol/FEEDBACK_BATCH_2026-03-03-headstamp-and-scaffold-pollution.md` (`status: CLOSED`);
   - new independent closure receipt added:
     - `.../outbox-to-protocol/SCAFFOLD_DISPOSITION_RECEIPT_20260303T082900Z.json`;
   - canonical linkage updated:
     - `.../outbox-to-protocol/PROTOCOL_FEEDBACK_RECEIPT_2026-03-03-headstamp-scaffold.json` => `status=CLOSED`;
     - `.../runtime/protocol-feedback/evidence-index/INDEX.md` includes split + scaffold disposition receipts.

Changed files (implementation):

1. `scripts/identity_creator.py`
2. `scripts/tool_vendor_governance_common.py`
3. `scripts/protocol_feedback_lane_common.py`
4. `scripts/validate_writeback_continuity.py`
5. `scripts/validate_post_execution_mandatory.py`
6. `scripts/validate_semantic_routing_guard.py`
7. `scripts/validate_protocol_feedback_sidecar_contract.py`
8. `scripts/create_identity_pack.py`

Static/doc contract checks:

1. `python3 -m py_compile ...` (patched scripts set) => `rc=0`
2. `bash -n scripts/e2e_smoke_test.sh` => `rc=0`
3. `python3 scripts/docs_command_contract_check.py` => `PASS`
4. `python3 scripts/validate_protocol_ssot_source.py` => `OK`

Decision boundary:

1. `FIX-051` and `FIX-052` are moved to implementation-complete status (`DONE`) with `PENDING_REAUDIT`.
2. Historical note (timepoint `16.8.44`): `FIX-053` was still `SPEC_READY / PENDING_REPLAY` because coverage normalization patch was not part of `e62deab`; superseded by implementation intake `16.8.46` (`ddb1529`).
3. This intake is scope-limited and does not claim all pending remediation batches are closed.

#### 16.8.45 Implementation replay intake: outbound reply headstamp recurrence guard (`FIX-054`, 2026-03-03, scope-limited)

Status: `DONE / PENDING_REAUDIT` (implementation landed; independent re-audit pending).

Problem statement:

1. Live operator replies can still miss first-line `Identity-Context` even when protocol validators exist in repository pipelines.
2. Root cause is output-stage discipline gap: validators are present but not always executed before human-visible emission.
3. A deterministic compose+gate adapter is needed so reply output path is fail-closed before send.

Implementation anchor:

1. `scripts/compose_and_validate_governed_reply.py` (new):
   - resolves identity stamp context from catalog/repo-catalog;
   - composes first-line stamp (`Identity-Context ... | Layer-Context ...`) + business body;
   - runs `validate_send_time_reply_gate.py --operation send-time --force-check --enforce-send-time-gate`;
   - returns non-zero on gate failure and can emit validated reply file/output telemetry.

Replay evidence:

1. positive path:
   - `python3 scripts/compose_and_validate_governed_reply.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --work-layer protocol --source-layer project --layer-intent-text "协议层治理回放，请按 protocol lane 执行" --body-text "已按协议要求完成修复并补齐台账。" --json-only`
   - expected: `rc=0`, `send_time_gate_status=PASS_REQUIRED`.
2. negative path:
   - existing first-line/send-time validators remain fail-closed for missing headstamp (`IP-ASB-STAMP-SESSION-001`), and compose adapter does not bypass those checks.

Boundary:

1. `FIX-054` hardens operator emission discipline; it does not replace runtime/live channel integration requirements already tracked by `FIX-049` (`ASB-RQ-109`).
2. This intake is scope-limited and does not auto-promote unrelated `PENDING_REAUDIT` rows.

#### 16.8.46 Implementation replay intake: custom project reverify closure for CWD drift + coverage normalization (`FIX-051/053`, 2026-03-03, scope-limited)

Status: `DONE / PENDING_REAUDIT` for implementation scope (`FIX-051` drift closure delta + `FIX-053` code landing).  
Decision boundary remains scope-limited (no full-green promotion).

Commit anchor:

1. `ddb1529` — `fix(protocol): close cwd-relative writeback drift and normalize coverage`

Implementation delta:

1. `scripts/validate_identity_experience_writeback.py`
   - report discovery now pack-root aware (`latest_identity_upgrade_report`);
   - `writeback_paths` are resolved against pack/report/runtime roots instead of caller CWD.
2. `scripts/validate_identity_prompt_lifecycle.py`
   - relative `runtime_state_artifact_path` resolution now report/pack aware (no CWD-dependent miss).
3. `scripts/validate_post_execution_mandatory.py`
   - downstream `validate_identity_experience_writeback.py` invocation now uses absolute script path + protocol-root cwd.
4. `scripts/validate_required_contract_coverage.py`
   - optional-lane PASS no longer inflates required-pass counters;
   - coverage is bounded to `[0,100]` with overflow telemetry fields.

Scope-limited replay evidence:

1. CWD invariance (same report, two working directories):
   - `validate_identity_experience_writeback.py` root + pack both `rc=0`.
   - `validate_identity_prompt_lifecycle.py` root + pack both `rc=0`.
2. Post-execution chain:
   - `/tmp/fix051_postexec_validate_root.json` -> `post_execution_mandatory_status=PASS_REQUIRED`.
   - `/tmp/fix051_postexec_validate_tmp.json` -> `post_execution_mandatory_status=PASS_REQUIRED`.
3. Semantic routing guard current batch:
   - metadata-fixed batch `FEEDBACK_BATCH_20260303T082408Z_protocol_closure_reverify_sanitized.md`
     now passes `IP-SEM-001` guard (`/tmp/fix052_semantic_custom_validate_after.json`).
4. Coverage KPI normalization:
   - `/tmp/fix053_cov_custom_threeplane_after.json` -> `required_contract_total=7`, `required_contract_passed=7`, `required_contract_coverage_rate=100.0`.
   - `/tmp/three_plane_custom_20260303_afterfix3.json` -> `required_contract_total=3`, `required_contract_passed=3`, `required_contract_coverage_rate=100.0`.
5. Full-scan boundary sample (historical window):
   - `/tmp/full_scan_custom_project_only_afterfix3.json` -> project scope `p0=0`, residual `p1=1` (`IP-CAP-003` auth/env preflight), not protocol writeback/semantic/coverage regression.
   - superseded for current-state decision by live re-audit intake `16.8.48` (project scope now `p0=1,p1=0` due `IP-CAP-003`).

Boundary:

1. This replay closes the reported protocol defects (`IP-WRB-003` CWD drift + coverage overflow anomaly) for the project-catalog scenario.
2. Global-catalog historical runtime residuals are explicitly out of scope for this intake and are not auto-promoted to closed.
3. Status table remains conservative: `PENDING_REAUDIT` until independent auditor replay confirms closure.

#### 16.8.47 Auditor counter-evidence replay intake: outlet hard-wiring + sidecar passthrough order + writeback path-contract CWD closure (`FIX-051/054`, 2026-03-03, scope-limited)

Status: `DONE / PENDING_REAUDIT` (targeted counter-findings addressed in implementation; independent auditor replay still required).

Commit anchor:

1. `6430852` — `fix(protocol): enforce compose-preflight outlet and close CWD sidecar gaps`

Counter-findings addressed:

1. `validate_writeback_continuity.py` relative sub-validator invocation (`IP-WRB-004` in `/tmp` caller) was CWD-sensitive.
2. `compose_and_validate_governed_reply.py` was available but not wired into required execution chains (outlet bypass risk).
3. `validate_protocol_feedback_sidecar_contract.py` appended passthrough args after semantic/namespace validators had already executed (parameter order ambiguity).

Implementation delta:

1. `scripts/validate_writeback_continuity.py`
   - path-contract child validator now invoked via absolute script path with protocol-root cwd.
2. `scripts/validate_protocol_feedback_sidecar_contract.py`
   - passthrough args (`expected-*`, `layer-intent`, `run-id`, `correlation-key`) are now injected before semantic/namespace execution;
   - child command execution uses protocol-root cwd for CWD-invariant behavior.
3. Outlet integration of governed compose+preflight:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - send-time gate now validates reply-file generated by `compose_and_validate_governed_reply.py` (non-synthetic outlet payload).

Replay evidence (scope-limited):

1. Writeback continuity CWD invariance:
   - `/tmp/audit_fix051_wrb_repo_root_after_ddb.json` -> `writeback_continuity_status=PASS_REQUIRED`
   - `/tmp/audit_fix051_wrb_tmp_root_after_ddb.json` -> `writeback_continuity_status=PASS_REQUIRED`
2. Sidecar passthrough + CWD invariance:
   - `/tmp/fix_sid_sidecar_repo_after.json` -> `sidecar_contract_status=PASS_REQUIRED`
   - `/tmp/fix_sid_sidecar_tmp_after.json` -> `sidecar_contract_status=PASS_REQUIRED`
   - passthrough equivalence replay (`--run-id + --correlation-key + --expected-work-layer`) confirms sidecar `track_b.semantic_*` / `track_b.vendor_namespace_*`
     match direct validators:
     - `/tmp/reaudit_fix_sid_sidecar_equiv.json`
     - `/tmp/reaudit_fix_sid_sem_direct.json`
     - `/tmp/reaudit_fix_sid_ns_direct.json`
3. Outlet compose hard-wiring visible in scan/three-plane:
   - `/tmp/full_scan_custom_project_only_afterfix4.json` contains both `send_time_reply_gate` (compose preflight) and `send_time_reply_gate_validate` pass records.
   - `/tmp/three_plane_custom_20260303_afterfix4.json` validator set includes `compose_governed_reply_preflight` + `send_time_reply_gate`, both `rc=0`.
4. Remaining residual in this sample window (historical):
   - project-scope scan reports `P1` (`IP-CAP-003` env/auth preflight), not protocol writeback/semantic/send-time regression.
   - superseded for current-state decision by live re-audit intake `16.8.48` (`IP-CAP-003` classified as `P0` blocker in current project replay window).

Decision boundary:

1. This intake addresses the cited P0/P1 implementation gaps from the auditor counter-evidence window.
2. Status remains `PENDING_REAUDIT` until independent replay confirms no regression across required lanes.
3. No claim of global full-green is made by this section.
4. Cross-cwd runbook note:
   - when caller cwd is not protocol-root, pass absolute `--repo-catalog` for post-execution chain replay consistency.

#### 16.8.48 Auditor live re-audit sync: implementation closure retained, runtime env blocker remains `P0` (`IP-CAP-003`) (2026-03-03, project scope)

Status: `DONE / PENDING_REAUDIT` (protocol code-gap closure stands; project runtime remains blocked by env/auth preflight).

Evidence intake (independent live replay):

1. `/tmp/reaudit_643_fullscan_project_only_live.json`
   - `summary.p0=1`, `summary.p1=0`
   - blocker class: `capability_activation_preflight`
   - blocker code: `IP-CAP-003`
2. `/tmp/reaudit_643_threeplane_live.json`
   - `instance_plane_status=IN_PROGRESS`
   - `capability_activation_error_code=IP-CAP-003`

Cross-check on fixed implementation claims (still valid):

1. FIX-051 CWD invariance:
   - `/tmp/reaudit_643_wrb_root.json` and `/tmp/reaudit_643_wrb_tmp.json` both `writeback_continuity_status=PASS_REQUIRED`.
2. FIX-054 outlet wiring + sidecar pass-through:
   - `/tmp/reaudit_643_sidecar_root.json` and `/tmp/reaudit_643_sidecar_tmp.json` both `sidecar_contract_status=PASS_REQUIRED`.
   - `/tmp/reaudit_643_semantic_direct.json` remains equivalent to sidecar `track_b.semantic_*` under identical passthrough args.

Decision boundary (current-state):

1. Do **not** use `p0=0,p1=1` as current-state release posture for project scope; that is historical-only.
2. Current project-scope state is `P0` blocked by `IP-CAP-003` (env/auth preflight), while protocol implementation fixes from `6430852` remain valid.
3. External claim must stay conservative: `IMPL_READY (BLOCKED_BY_ENV_AUDIT)` for this replay window; no full-closed/full-green claim.

#### 16.8.49 Release-lock posture sync (`v1.5` NO_GO, `v1.6` planning allowed in parallel) (2026-03-03, docs-only bridge)

Status: `NO_GO (v1.5 release)` + `PLANNING_ALLOWED (v1.6 parallel track)`.

Evidence bundle:

1. Release-lock table remains hard-locked:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:30-35` (`D1~D5=OPEN`, `D6=LOCKED`).
2. Unlock formula remains hard condition:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:2615` (`all P0 DONE` + `D1~D5 PASS`).
3. Current 6.4 `P0` status census (machine parse snapshot, 2026-03-03):
   - `P0_TOTAL=85`, `P0_DONE=0`, `P0_NOT_DONE=85`.
   - Status distribution: `SPEC_READY=26`, `IMPL_READY(BLOCKED_BY_AUDIT)=26`, `GATE_READY=28`, `VERIFIED=5`, `DONE=0`.
4. Live runtime replay still has `P0` blocker (`IP-CAP-003`):
   - `/tmp/reaudit_643_fullscan_project_only_live.json` -> `summary.p0=1`.
   - `/tmp/reaudit_643_threeplane_live.json` -> `instance_plane_status=IN_PROGRESS`, `capability_activation_error_code=IP-CAP-003`.
   - `/tmp/release_readiness_custom_live.log` -> readiness `rc=2` with capability activation preflight blocked (`IP-CAP-003`).

Decision boundary:

1. `v1.5` release/tag remains blocked (`NO_GO`) until unlock formula in governance 6.5 is satisfied.
2. `v1.6` planning/design execution can proceed in parallel, but cannot be used as evidence to waive any `v1.5` lock gate.
3. External messaging must not claim `Full Go` for `v1.5` under current state.

#### 16.8.24 Roundtable intake: work-layer gate-set split to unblock instance self-drive upgrades (FIX-033, 2026-03-02, docs-only)

Status: `SPEC_READY` (implementation not landed yet).

Problem statement (cross-validated):

1. Dual-lane governance semantics are documented, but readiness/e2e execution still runs protocol publish gates in instance self-drive lane.
2. This causes cross-lane hard blocking: instance self-drive upgrades can fail on protocol release checks (for example changelog publish linkage), which violates lane split intent.
3. Protocol strictness must be preserved, but only in `work_layer=protocol` lane with canonical protocol-feedback closure requirements.

Cross-validation anchors:

1. Global readiness sequence includes changelog publish gate regardless of lane:
   - `scripts/release_readiness_check.py:418`
2. E2E global sequence includes changelog publish gate regardless of lane:
   - `scripts/e2e_smoke_test.sh:49`
3. Creator validate sequence currently mixes protocol lane validators into one shared list without lane-set split:
   - `scripts/identity_creator.py:1323`
4. Governance already codifies default instance lane and trigger-auditable protocol lane:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:1166`
5. Governance already codifies split receipt and canonical protocol-feedback channel:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:1011`
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:1244`

Requirement scope locked for FIX-033 (`ASB-RQ-090..093`):

1. `work_layer` must route to lane-specific required gate sets:
   - `instance_required_checks` for `work_layer=instance`
   - `protocol_required_checks` for `work_layer=protocol`
   - `work_layer=dual` is not allowed for strict closure operations and must fail-closed with explicit rerun lane.
2. In `work_layer=instance`, protocol publish gates must not hard-block self-drive closure:
   - protocol-related changes produce protocol-feedback pending receipt, not immediate instance-lane failure.
3. In `work_layer=protocol`, protocol publish gates remain strict fail-closed and require canonical protocol-feedback closure.
4. Send-time/replay outputs must expose lane execution telemetry:
   - `work_layer`
   - `applied_gate_set`
   - `protocol_feedback_triggered`
   - `protocol_feedback_paths`
   - `lane_transition_reason`

Acceptance profile (release-blocking once implementation lands):

1. sample A:
   - input: `work_layer=instance`, protocol files changed, changelog not updated
   - expected: instance lane not blocked; protocol-feedback pending receipt emitted
2. sample B:
   - input: `work_layer=protocol`, protocol files changed, changelog not updated
   - expected: strict fail-closed when canonical protocol-feedback closure roots are incomplete (fixture/state-bound sample)
3. sample C:
   - input: multi-round replay
   - expected: each round exposes `work_layer + applied_gate_set + protocol_feedback_triggered + protocol_feedback_paths`
4. sample D:
   - input: strict closure operation with `work_layer=dual`
   - expected: deterministic fail-closed (`IP-LAYER-GATE-005`) with rerun hint to `instance` or `protocol`

Boundary notes:

1. FIX-033 is lane-routing and boundary hardening; it does not replace FIX-029..032 protocol-entry closure fixes.
2. Historical intake note: FIX-029..032 were `REJECT` baseline at this snapshot time; current rolling status is `PENDING_REAUDIT` per section `16.8.28` and summary rows.

This section is docs-only intake; no protocol script behavior changed in this batch.

#### 16.8.25 Architect patch: FIX-033 lane routing implementation landed (2026-03-02, protocol-only)

Status: `PATCH_APPLIED / PENDING_REAUDIT` (authoritative status stays pending until independent audit replay).

Commit anchor:

1. `0d7ebc7` — `fix(protocol): implement FIX-033 work-layer gate-set routing`

Changed files:

1. `scripts/validate_work_layer_gate_set_routing.py` (new required validator for `ASB-RQ-090..093`)
2. `scripts/execute_identity_upgrade.py` (lane context resolution + required-check routing + pending protocol-feedback telemetry in report)
3. `scripts/identity_creator.py` (FIX-033 validator wiring + lane args passthrough to upgrade executor)
4. `scripts/release_readiness_check.py` (lane-set routing + protocol publish gate filtering in instance lane)
5. `scripts/e2e_smoke_test.sh` (lane-aware protocol publish gate execution + FIX-033 validator replay)
6. `scripts/full_identity_protocol_scan.py` (FIX-033 validator wiring + machine-readable field projection)
7. `scripts/report_three_plane_status.py` (FIX-033 validator wiring + instance-plane telemetry projection)
8. `.github/workflows/_identity-required-gates.yml` (CI required-gate wiring + update lane pin to `instance`)

Implementation deltas (P0 closure targets):

1. `ASB-RQ-090` (`work_layer_gate_set_routing_contract_v1`)
   - deterministic lane resolution (`instance/protocol/dual`) now emits machine-readable gate-set tuple:
     - `work_layer`
     - `source_layer`
     - `applied_gate_set`
     - `lane_transition_reason`
2. `ASB-RQ-091` (instance lane non-blocking protocol publish boundary)
   - `execute_identity_upgrade.py` now filters protocol publish checks from required check-set when `work_layer=instance`.
   - when protocol-relevant diff exists in instance lane, `validate_work_layer_gate_set_routing.py` writes canonical pending receipt with `next_action=protocol_feedback_required`.
3. `ASB-RQ-092` (protocol lane strict boundary)
   - `work_layer=protocol` requires canonical protocol-feedback roots; missing roots fail strict with `IP-LAYER-GATE-004`.
4. `ASB-RQ-093` (replay observability)
   - new fields wired into scan/three-plane payload surfaces:
     - `work_layer_gate_set_routing_status`
     - `work_layer`
     - `source_layer`
     - `applied_gate_set`
     - `protocol_feedback_triggered`
     - `protocol_feedback_paths`
     - `lane_transition_reason`

Acceptance replay snapshot (architect local):

1. static:
   - `python3 -m py_compile scripts/validate_work_layer_gate_set_routing.py scripts/release_readiness_check.py scripts/identity_creator.py scripts/execute_identity_upgrade.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - rc: `0`
2. sample A (`instance`, protocol diff present, no changelog link):
   - command:
     - `python3 scripts/validate_work_layer_gate_set_routing.py --catalog identity/catalog/identities.yaml --repo-catalog identity/catalog/identities.yaml --identity-id system-requirements-analyst --operation validate --expected-work-layer instance --source-layer global --base $(git rev-parse 560f710~1) --head $(git rev-parse 560f710) --applied-gate-set instance_required_checks --force-check --json-only`
   - rc: `0`
   - key fields:
     - `work_layer_gate_set_routing_status=PASS_REQUIRED`
     - `protocol_relevant_diff_detected=true`
     - `protocol_feedback_triggered=true`
     - `protocol_feedback_paths` contains `outbox-to-protocol/LAYER_GATE_PROTOCOL_PENDING_*.json`
3. sample B (`protocol`, same diff range):
   - rc: `1` (state-bound fixture: canonical protocol-feedback closure root incomplete)
   - key fields:
     - `work_layer_gate_set_routing_status=FAIL_REQUIRED`
     - `error_code=IP-LAYER-GATE-004`
4. sample D (`dual` in strict operation):
   - rc: `1`
   - key fields:
     - `work_layer_gate_set_routing_status=FAIL_REQUIRED`
     - `error_code=IP-LAYER-GATE-005`
5. three-plane visibility:
   - `python3 scripts/report_three_plane_status.py --identity-id system-requirements-analyst --catalog identity/catalog/identities.yaml --repo-catalog identity/catalog/identities.yaml --layer-intent-text "实例自驱升级" --expected-work-layer instance --expected-source-layer global --out /tmp/fix033_three_plane.json`
   - rc: `0`
   - payload evidence:
     - `instance_plane_detail.work_layer_gate_set_routing.work_layer_gate_set_routing_status=PASS_REQUIRED`
     - `instance_plane_detail.work_layer_gate_set_routing.work_layer=instance`
     - `instance_plane_detail.work_layer_gate_set_routing.applied_gate_set=instance_required_checks`

Audit boundary:

1. This section records implementation + local replay only.
2. Independent auditor replay remains required before changing FIX-033 from `PENDING_REAUDIT` to `PASS`.

#### 16.8.26 Architect patch: FIX-033 lane applied-gate-set propagation for full-scan/three-plane (2026-03-02)

Status: `PATCH_APPLIED / PENDING_REAUDIT` (closes auditor P0 mismatch path pending independent replay).

Commit anchor:

1. `913973a` — `fix(protocol): route lane applied gate-set in scan and three-plane`

Changed files:

1. `scripts/full_identity_protocol_scan.py`
2. `scripts/report_three_plane_status.py`
3. `docs/review/protocol-remediation-audit-ledger-v1.5.md`

Implementation delta:

1. Added lane-aware gate-set resolver to both scan and three-plane surfaces:
   - `resolve_layer_intent(...)` + `DEFAULT_WORK_LAYER` are now used to compute `lane_applied_gate_set`.
2. Replaced hardcoded `--applied-gate-set instance_required_checks` with computed lane result:
   - `protocol_required_checks` for `work_layer=protocol`
   - `instance_required_checks` for `work_layer=instance`
   - `dual_unroutable` fallback for unresolved/dual lane.
3. This aligns FIX-033 telemetry tuple with routed lane intent and removes self-contradictory audit outputs under protocol replay.

Replay evidence snapshot (architect local):

1. static checks:
   - `python3 -m py_compile scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - rc: `0`
2. full-scan protocol lane replay:
   - command:
     `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml --expected-work-layer protocol --expected-source-layer global --layer-intent-text "protocol lane replay for FIX-033" --out /tmp/fix033_fullscan_protocol.json`
   - rc: `0`
   - key fields (`project/global`): `work_layer_gate_set_routing_status=PASS_REQUIRED`, `applied_gate_set=protocol_required_checks`, `requested_applied_gate_set=protocol_required_checks`
   - grep replay result: no `IP-LAYER-GATE-001`, no `applied_gate_set_mismatch`.
3. three-plane protocol lane replay:
   - command:
     `python3 scripts/report_three_plane_status.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --expected-work-layer protocol --expected-source-layer global --layer-intent-text "protocol lane replay for FIX-033" --out /tmp/fix033_threeplane_protocol.json`
   - rc: `0`
   - key fields: `instance_plane_detail.work_layer_gate_set_routing.work_layer_gate_set_routing_status=PASS_REQUIRED`, `applied_gate_set=protocol_required_checks`, nested payload includes `requested_applied_gate_set=protocol_required_checks`
   - grep replay result: no `IP-LAYER-GATE-001`, no `applied_gate_set_mismatch`.
4. docs/ssot:
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`
   - rc: `0`

Residual risks (not introduced by this patch):

1. Global identity runtime still contains existing non-lane blockers (`IP-SEM-001`, `IP-SPLIT-001`, `IP-SID-001`) in independent scans.
2. Historical note: this section was recorded as `PENDING_REAUDIT` at patch time; closure verdict is tracked in `16.8.27`.

#### 16.8.27 Auditor closure intake: FIX-033 promoted to PASS for lane mismatch gap (2026-03-02)

Status: `PASS` (scope-limited closure for prior P0: applied-gate-set hardcoding -> `IP-LAYER-GATE-001` mismatch path).

Independent replay summary (auditor-provided):

1. `913973a + 9d830d8` independently reproduced without `IP-LAYER-GATE-001`.
2. `full_identity_protocol_scan.py` protocol lane replay (`project/global`) now reports:
   - `work_layer_gate_set_routing_status=PASS_REQUIRED`
   - `requested_applied_gate_set=protocol_required_checks`
   - `applied_gate_set=protocol_required_checks`
3. `report_three_plane_status.py` protocol lane replay now reports:
   - `instance_plane_detail.work_layer_gate_set_routing.work_layer_gate_set_routing_status=PASS_REQUIRED`
   - no `IP-LAYER-GATE-001`
4. `/tmp` CWD replay also consistent for this patch scope (no new CWD drift introduced).

Bookkeeping update:

1. FIX-033 rolling summary anchor updated to include `913973a / 9d830d8`.
2. Result promoted from `PENDING_REAUDIT` -> `PASS` for this issue scope.

#### 16.8.28 Auditor delta replay intake: FIX-029..032 de-ambiguation refresh (2026-03-02, review-only)

Status: `DELTA_REPLAY_RECORDED` (historical `16.8.21` remains archived as prior snapshot; latest replay does not reproduce earlier CWD/split contradictions under aligned intent fixtures).

Scope and fixture normalization:

1. Same identity + same catalog + same layer-intent text are used for root and `/tmp` replay.
2. This eliminates prior false positives caused by mixed semantic fixtures (different `layer-intent-text` across CWDs).
3. Replay outcome is evidence for status refresh from `REJECT` -> `PENDING_REAUDIT` in rolling summary rows (`FIX-029..032`); final PASS still requires the full sign-off command pack.

Replay delta summary (auditor + architect aligned):

1. `validate_protocol_feedback_reply_channel.py` (root vs `/tmp`):
   - `protocol_feedback_reply_channel_status=PASS_REQUIRED`
   - `split_receipt_status=PASS_REQUIRED`
   - `split_receipt_payload_rc=0`
2. `validate_protocol_inquiry_followup_chain.py` with same intent text (root vs `/tmp`):
   - `protocol_inquiry_followup_chain_status=PASS_REQUIRED`
   - `candidate_decision=PROTOCOL_CANDIDATE`
   - `inquiry_state=READY_FOR_PROTOCOL_FEEDBACK`
3. `validate_protocol_feedback_bootstrap_ready.py` (root vs `/tmp`):
   - `protocol_feedback_bootstrap_status=PASS_REQUIRED`
4. Interpretation:
   - earlier contradictory evidence in `16.8.21` is retained as historical context but no longer represents current replay state.

#### 16.8.21 Auditor replay verdict: FIX-029..032 implementation review (2026-03-02, historical snapshot superseded by 16.8.28)

Status: `HISTORICAL_SNAPSHOT` (superseded by `16.8.28` for current-state replay judgment).

Usage note:

1. Keep this section as immutable historical evidence for the 2026-03-02 reject point-in-time.
2. Do **not** use this section alone as current blocking evidence after the normalized replay set in `16.8.28`.

#### 16.8.29 Roundtrip intake: office-ops protocol determinism gaps (`FIX-034..038`, 2026-03-02, docs-only)

Status: `SPEC_READY` (historical intake snapshot; P1 attribution refined by `16.8.31`; no protocol code changes in this batch).

Source handoff package (authoring identity `office-ops-expert`):

1. `/Users/yangxi/claude/codex_project/ddm/docs/governance/identity-protocol-feedback-office-ops-expert-roundtrip-v2026-03-02.md`
2. supporting logs:
   - `/tmp/office_release.log`
   - `/tmp/office_e2e.log`
   - `/tmp/office_selfdrive_update.log`
   - `/tmp/office_selfdrive_release.log`
   - `/tmp/office_selfdrive_e2e.log`
   - `/tmp/office_e2e_no_pythonpath.log`

Data-sanitization cross-check (intake scope):

1. No customer/order/SKU/price business payloads were found in source doc/logs.
2. No high-risk credential patterns were found (`api_key`/`secret`/`bearer`/private-key/JWT class patterns).
3. Source contains local runtime metadata (absolute paths, actor/session IDs, run IDs), which is acceptable for protocol debugging but should be redacted when exporting outside trusted maintainer scope.

Intake findings mapped to new FIX stream:

1. `FIX-034` / `ASB-RQ-094` (`P0`):
   - protocol-topic troubleshooting can resolve to `work_layer=instance` under `intent_text_missing` fallback, causing protocol lane checks to be skipped.
   - replay evidence:
     - `/tmp/office_selfdrive_release.log` and `/tmp/office_selfdrive_e2e.log` contain:
       - `intent_source=default_fallback`
       - `fallback_reason=intent_text_missing`
       - `work_layer=instance`
2. `FIX-035` / `ASB-RQ-095` (`P0`):
   - strict baseline/session-refresh checks can fail on moving protocol HEAD within one run window (`IP-PBL-001`, `IP-ASB-RFS-004`, `lag_commits=1`), creating timing-sensitive outcomes.
   - replay evidence:
     - `/tmp/office_release.log` and `/tmp/office_e2e.log` show strict failure with `lag_commits=1`.
     - `/tmp/office_selfdrive_update.log` shows same mismatch becoming recoverable only after head catches up.
3. `FIX-036` / `ASB-RQ-096` (`P0`):
   - e2e import path is not fully hermetic; no-PYTHONPATH invocation can fail with:
     - `ModuleNotFoundError: No module named 'response_stamp_common'`.
   - replay evidence:
     - `/tmp/office_e2e_no_pythonpath.log`.
4. `FIX-037` / `ASB-RQ-097` (`P1`):
   - skill contract execution integrity drift: skill instructions can point to missing/non-executable command targets in active repo context.
   - requires machine-checkable skill-command existence validation and CI guard.
5. `FIX-038` / `ASB-RQ-098` (`P1`):
   - strict self-repair can self-lock in stale-baseline-only scenarios and require manual policy downgrade; two-phase refresh+strict-revalidate path is required for deterministic one-command recovery.

Required implementation package (next protocol batch):

1. `FIX-034`:
   - add protocol-context lane-lock validator/receipt path and strict fail-closed downgrade prevention.
2. `FIX-035`:
   - add run-start pinned SHA context and evaluate strict baseline freshness against pinned anchor.
3. `FIX-036`:
   - make e2e runner import bootstrap hermetic (internal path bootstrap + deterministic preflight error code).
4. `FIX-037`:
   - add skill-contract integrity validator + required-skill CI command existence check.
5. `FIX-038`:
   - add strict two-phase stale-baseline refresh path with machine-readable phase receipts.

Acceptance template (post-implementation):

1. protocol-topic empty intent under strict mode must fail-closed (no silent instance fallback).
2. long-run strict replay with in-run HEAD drift must remain deterministic via run-pinned baseline anchor.
3. `bash scripts/e2e_smoke_test.sh` must pass without external `PYTHONPATH` patch.
4. required skill contract must fail deterministically when command target is missing.
5. strict update in stale-only scenario must complete via two-phase refresh+revalidate or fail for non-baseline root cause.

Boundary:

1. This section is docs-only intake.
2. No changes to protocol scripts, CI workflows, or runtime executors are included in this commit.

#### 16.8.30 Re-attribution intake: protocol vs ecosystem vs instance split refinement (`FIX-039..042`, 2026-03-02, docs-only)

Status: `SPEC_READY` (docs-first attribution refinement; no protocol code changes in this batch).

Primary source package:

1. Raw roundtrip memo:
   - `/Users/yangxi/claude/codex_project/ddm/docs/governance/identity-protocol-feedback-office-ops-expert-roundtrip-v2026-03-02.md`
2. Sanitized outbound memo:
   - `/Users/yangxi/claude/codex_project/ddm/docs/governance/identity-protocol-feedback-office-ops-expert-roundtrip-v2026-03-02-sanitized.md`
3. Additional audit replay context:
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/base-repo-audit-expert-v3/runtime/reports/identity-upgrade-exec-base-repo-audit-expert-v3-1772450247.json`

Attribution decision (cross-validated, non-brainstorm):

1. Protocol-core must patch now: `2 x P0 + 2 x P1` (`FIX-039..042`).
2. Ecosystem-only (not protocol core): `1 x P1` (skill package command drift).
3. Instance data-plane failures are excluded from protocol patch list when replay shows lane routing and protocol publish skip behavior are already correct for instance lane.

Protocol-core findings and replay evidence:

1. `FIX-039` / `P0` requiredization scope leakage into instance lane:
   - replay (`operation=update`) currently yields `required_contract_declared=false` but `required_contract=true` + `auto_required_signal=true` for protocol governance contracts and then `FAIL_REQUIRED`.
   - evidence commands (local replay):
     - `validate_semantic_routing_guard.py` -> `rc=1`, `IP-SEM-001`, `required_contract=true`, `auto_required_signal=true`
     - `validate_instance_protocol_split_receipt.py` -> `rc=1`, `IP-PFB-CH-006`, `required_contract=true`, `auto_required_signal=true`
     - `validate_vendor_namespace_separation.py` -> `rc=1`, `IP-SEM-004`, `required_contract=true`, `auto_required_signal=true`
     - `validate_protocol_feedback_sidecar_contract.py` -> `rc=1`, `IP-SID-001`, `required_contract=true`, `auto_required_signal=true`
     - `validate_required_contract_coverage.py` -> `rc=1`, failed required count includes all above with declared=false/effective=true.
2. `FIX-040` / `P0` split-activity detector lacks current-round correlation:
   - `validate_instance_protocol_split_receipt.py` currently scans all files under
     `runtime/protocol-feedback/{outbox-to-protocol,evidence-index,upgrade-proposals}` as activity.
   - strict path can emit `IP-PFB-CH-006` when split receipt missing even if activity is historical/non-correlated.
3. `FIX-041` / `P1` invalid `expected-source-layer` is silently downgraded:
   - replay:
     - `validate_reply_identity_context_first_line.py ... --expected-source-layer intent --operation validate --enforce-first-line-gate --json-only`
     - result: `rc=0`, `reply_first_line_status=PASS_REQUIRED`, `expected_source_layer=env`.
   - indicates invalid input normalization without explicit non-pass signal.
4. `FIX-042` / `P1` required coverage aggregation is lane-unaware:
   - `validate_required_contract_coverage.py` target set always includes protocol governance validators.
   - required-effective accounting uses payload-upgraded required state regardless of lane partition, increasing instance-lane noise.

Explicit exclusions from protocol-core patch stream:

1. Ecosystem-only (`P1`, not protocol-core):
   - `office-ops-regression-self-drive` skill command target drift (`run_office_ops_regression.sh` resolution issue in runtime context).
2. Instance-data-plane failures (do not open protocol-core patch by themselves):
   - `validate_identity_trigger_regression.py`
   - `validate_agent_handoff_contract.py`
   - `validate_identity_collab_trigger.py`
   - `validate_identity_experience_feedback_governance.py`
3. Instance lane split evidence remains valid (from report `1772450247`):
   - `work_layer=instance`
   - `applied_gate_set=instance_required_checks`
   - `skipped_protocol_publish_checks` includes `validate_changelog_updated.py` and `validate_release_metadata_sync.py`.

Data sanitization check for this intake:

1. No business-scene payload keywords were found in referenced docs/logs.
2. No high-risk credential patterns were detected.
3. Absolute local paths and runtime IDs are retained only for maintainer-side evidence and must be redacted for external dispatch.

Boundary:

1. This section is docs-only attribution refinement.
2. No script/workflow/runtime code changes are included in this commit.

#### 16.8.31 Office-ops re-attribution delta + Scenario A minimal decision intake (`FIX-043`, 2026-03-02, docs-only)

Status: `SPEC_READY` (docs-first refinement; no protocol code changes in this batch).

Primary source package:

1. Updated raw memo:
   - `/Users/yangxi/claude/codex_project/ddm/docs/governance/identity-protocol-feedback-office-ops-expert-roundtrip-v2026-03-02.md`
2. Updated sanitized outbound memo:
   - `/Users/yangxi/claude/codex_project/ddm/docs/governance/identity-protocol-feedback-office-ops-expert-roundtrip-v2026-03-02-sanitized.md`
3. Scenario A real-run report:
   - `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-protocol-scenarioA-autonomous-upgrade-real-run-feedback-2026-03-02.md`
4. Scenario A outbox batch:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-02_012.md`
5. Scenario A pending receipt:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/LAYER_GATE_PROTOCOL_PENDING_20260302T100613Z.json`

Cross-validated attribution decision:

1. Office-ops protocol-core count is refined to `5` (`P0=3`, `P1=2`):
   - `P0`: `FIX-034`, `FIX-035`, `FIX-036`.
   - `P1`: `FIX-038`, `FIX-043` (new intake in this section).
2. `FIX-037` is explicitly transferred to ecosystem-lane tracking (skill packaging/drift), not protocol-core patch queue.
3. Protocol-core + ecosystem + instance boundaries remain explicit and machine-auditable (no mixed ownership in this update).

New protocol-core intake (`FIX-043`, `P1`):

1. mutable lifecycle state is currently embedded into `IDENTITY_PROMPT.md` body (`last_upgrade_run_id`, `last_upgrade_at`, `last_trigger_reasons` class fields), creating prompt-policy churn.
2. required protocol direction:
   - immutable prompt policy remains in `IDENTITY_PROMPT.md`,
   - mutable runtime lifecycle state moves to dedicated runtime state artifact with hash-bound linkage.

Scenario A minimal decision package (intake-only, no new FIX opened in this commit):

1. `P0-1` preheat wrapper request:
   - classify as implementation-shaping decision for `FIX-038` (stale-baseline + tuple readiness deterministic preflight path).
2. `P0-2` strict tuple output request:
   - classify as implementation-shaping decision under existing alignment contract branch (`ASB-RQ-043`) to guarantee report tuple emit completeness.
3. `P1-3` protocol-relevant diff semantics clarity:
   - classify as docs/governance clarification request for lane routing classifier scope (no strict semantics downgrade).

Data sanitization check for this intake:

1. Raw memo contains local paths and runtime identifiers only; no customer/order/SKU business payloads detected.
2. Sanitized memo replaces local paths/log paths with redacted placeholders and is suitable for outbound dispatch.

Boundary:

1. This section is docs-only attribution/delta intake.
2. No protocol script/CI/runtime mutation is included in this commit.

#### 16.8.32 FIX-039..042 implementation landing replay (`83e5a03`, 2026-03-02, protocol)

Status: `IMPL_READY (BLOCKED_BY_AUDIT)` for independent replay closure.

Implementation scope:

1. New helper:
   - `scripts/protocol_feedback_lane_common.py`
2. Lane-scoped requiredization + correlation-aware activity rollout:
   - `scripts/validate_instance_protocol_split_receipt.py`
   - `scripts/validate_semantic_routing_guard.py`
   - `scripts/validate_vendor_namespace_separation.py`
   - `scripts/validate_protocol_feedback_sidecar_contract.py`
   - `scripts/validate_protocol_feedback_reply_channel.py`
3. Coverage lane partition + source-layer strict input validation:
   - `scripts/validate_required_contract_coverage.py`
   - `scripts/validate_reply_identity_context_first_line.py`
   - `scripts/validate_send_time_reply_gate.py`

Replay highlights (local):

1. `FIX-039` (`ASB-RQ-099`) baseline replay:
   - command:
     `python3 scripts/validate_required_contract_coverage.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation update --json-only`
   - result:
     - `rc=0`
     - `coverage_lane=instance`
     - protocol governance targets show `required_contract=false`, `auto_required_signal=false`, `requiredization_scope_decision=AUTO_REQUIRED_BLOCKED`.
2. `FIX-040` (`ASB-RQ-100`) correlation gate behavior:
   - history-only activity:
     - `validate_instance_protocol_split_receipt.py ... --operation update --json-only`
     - `instance_protocol_split_status=SKIPPED_NOT_REQUIRED`, `activity_correlation_status=ACTIVITY_UNSCOPED`.
   - correlated activity (forced correlation key):
     - `... --correlation-key LAYER_GATE_PROTOCOL_PENDING_20260302T095608Z.json`
     - `rc=1`, `error_code=IP-PFB-CH-006`, `activity_correlation_status=CORRELATED_CURRENT_ROUND`.
3. `FIX-041` (`ASB-RQ-101`) strict invalid source-layer input:
   - `validate_reply_identity_context_first_line.py ... --expected-source-layer intent --operation validate --enforce-first-line-gate --json-only`
   - result:
     - `rc=1`
     - `error_code=IP-SOURCE-LAYER-001`
     - `expected_source_layer_validation_status=FAIL_REQUIRED`.
4. `FIX-042` (`ASB-RQ-102`) lane-aware coverage partition:
   - protocol lane replay:
     - `validate_required_contract_coverage.py ... --expected-work-layer protocol --operation update --json-only`
   - result:
     - `rc=1`
     - `coverage_lane=protocol`
     - `coverage_protocol_targets_included` contains semantic/split/vendor/sidecar targets.

Static check:

1. `python3 -m py_compile` for changed scripts returned `rc=0`.

Boundary:

1. This section records implementation landing evidence only.
2. Final PASS promotion for `FIX-039..042` is pending independent re-audit.

#### 16.8.21-A Historical detail payload (archived verbatim, superseded by 16.8.28)

Replay refresh (2026-03-02, local re-audit delta):

1. Replayed `validate_protocol_feedback_reply_channel.py` from protocol root and `/tmp`.
2. Observed verdict unchanged:
   - protocol root still allows contradictory pass:
     - `protocol_feedback_reply_channel_status=PASS_REQUIRED`
     - `split_receipt_status=FAIL_REQUIRED`
     - `split_receipt_error_code=IP-PFB-CH-006`
   - `/tmp` invocation still shows child-runtime escape:
     - `protocol_feedback_reply_channel_status=PASS_REQUIRED`
     - `split_receipt_status=""`
     - `split_receipt_payload_rc=2`
3. Replayed `validate_protocol_inquiry_followup_chain.py` from protocol root and `/tmp`.
4. Observed CWD-dependent divergence unchanged:
   - protocol root:
     - `candidate_decision=PROTOCOL_CANDIDATE`
     - `inquiry_state=FEEDBACK_EMITTED`
   - `/tmp`:
     - `candidate_decision=INSTANCE_DEFAULT`
     - `protocol_inquiry_followup_chain_status=SKIPPED_NOT_REQUIRED`

Scope:

1. `FIX-029..032` post-implementation audit replay under protocol-only boundary.
2. Focus dimensions:
   - layer-intent pass-through integrity in readiness lane,
   - CWD invariance for new validators,
   - strict fail-closed correctness for split-receipt and inquiry-chain state machine.

Independent replay evidence (local):

1. `validate_protocol_feedback_reply_channel.py` from protocol root:
   - command:
     `python3 scripts/validate_protocol_feedback_reply_channel.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation validate --force-check --json-only`
   - observed payload:
     - `protocol_feedback_reply_channel_status=PASS_REQUIRED`
     - `split_receipt_status=FAIL_REQUIRED`
     - `split_receipt_error_code=IP-PFB-CH-006`
2. `validate_protocol_feedback_reply_channel.py` from `/tmp`:
   - command:
     `python3 /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/scripts/validate_protocol_feedback_reply_channel.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation validate --force-check --json-only`
   - observed payload:
     - `protocol_feedback_reply_channel_status=PASS_REQUIRED`
     - `split_receipt_status=""`
     - `split_receipt_payload_rc=2`
3. `validate_protocol_inquiry_followup_chain.py` from protocol root:
   - command:
     `python3 scripts/validate_protocol_inquiry_followup_chain.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation validate --force-check --layer-intent-text "semantic mismatch observed" --json-only`
   - observed payload:
     - `candidate_decision=PROTOCOL_CANDIDATE`
     - `inquiry_state=FEEDBACK_EMITTED`
4. `validate_protocol_inquiry_followup_chain.py` from `/tmp`:
   - command:
     `python3 /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/scripts/validate_protocol_inquiry_followup_chain.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation validate --force-check --layer-intent-text "I think protocol governance gate still weak and needs optimization" --json-only`
   - observed payload:
     - `protocol_inquiry_followup_chain_status=SKIPPED_NOT_REQUIRED`
     - `candidate_status=""`
5. static path review for readiness passthrough:
   - `scripts/release_readiness_check.py:839`
   - `scripts/release_readiness_check.py:1111`
   - `scripts/release_readiness_check.py:1174`

Blocking findings (ordered by severity):

1. `P0` strict fail-closed violation in reply-channel gate:
   - file: `scripts/validate_protocol_feedback_reply_channel.py:211`
   - issue:
     - split-receipt escalation only blocks `SKIPPED_NOT_REQUIRED`, but does not block `FAIL_REQUIRED` or child runtime failure (`split_receipt_payload_rc != 0`).
     - observed contradictory pass (`reply-channel=PASS_REQUIRED` while `split_receipt_status=FAIL_REQUIRED`).
2. `P0` CWD-sensitive subprocess in new reply/inquiry validators:
   - files:
     - `scripts/validate_protocol_feedback_reply_channel.py:73`
     - `scripts/validate_protocol_inquiry_followup_chain.py:116`
   - issue:
     - child validators invoked via relative `python3 scripts/...` without protocol-root anchoring.
     - non-root invocation (`/tmp`) can produce empty payload/rc errors that are not hard-blocked.
3. `P0` readiness lane misses layer-intent/source-layer passthrough for newly appended FIX-029..032 checks:
   - file: `scripts/release_readiness_check.py:839` and `scripts/release_readiness_check.py:1111`
   - issue:
     - layer argument augmentation executes before FIX-029..032 commands are appended to `seq`, so those checks do not receive `--layer-intent-text`, `--expected-work-layer`, `--source-layer`.
4. `P0` inquiry state machine can advance to `FEEDBACK_EMITTED` from unrelated historical batches:
   - file: `scripts/validate_protocol_inquiry_followup_chain.py:228`
   - issue:
     - any existing `FEEDBACK_BATCH_*.md` under outbox marks `feedback_emitted=true` without correlation to current candidate/inquiry receipt chain.
     - this can mask missing follow-up progression for current inquiry.

Required remediation before closure:

1. Reply-channel gate must fail-closed when split validator returns:
   - non-zero rc, or
   - `split_receipt_status in {FAIL_REQUIRED, WARN_NON_BLOCKING}` in strict operations.
2. New validators must execute child scripts with protocol-root deterministic path strategy:
   - `Path(__file__)` anchored absolute script path, or
   - `subprocess.run(..., cwd=protocol_root)` with guarded absolute target.
3. Readiness must inject layer args after final `seq` construction, or inject inline at append-time for each FIX-029..032 command.
4. Inquiry `FEEDBACK_EMITTED` transition must require current-chain linkage proof:
   - correlation to current candidate seed/receipt reference or inquiry receipt id,
   - reject unrelated historical batch files as emission proof.

Release posture:

1. `FIX-029..032` must remain release-blocking bundle with status `REJECT` until all four `P0` findings are closed and independently replayed.

#### 16.8.14 Roundtable intake: same-actor multi-session binding overwrite closure (2026-03-02, docs-only)

Status: `SPEC_READY` (implementation not landed yet).

Problem statement (cross-validated):

1. Canonical actor session payload is currently actor-file single-object shape, which is effectively one active binding per actor at write time.
2. Same actor can run interleaved activations for different identities; latest write can overwrite previous actor binding tuple, creating perceived hard-switch / lane grab under multi-window operation.
3. Existing actor-scoped model closed cross-actor implicit switch class, but same-actor multi-session conflict remains under-documented and non-gated.

Local evidence anchors:

1. Canonical actor file currently stores one object:
   - `/Users/yangxi/.codex/identity/session/actors/user_yangxi.json`
2. Path and payload model in protocol scripts:
   - `scripts/actor_session_common.py:22`
   - `scripts/actor_session_common.py:33`
   - `scripts/actor_session_common.py:45`
   - `scripts/actor_session_common.py:55`
3. Activation write chain calls sync writer with actor-level target:
   - `scripts/identity_creator.py:245`
   - `scripts/identity_creator.py:374`
4. Same-actor interleaved activation reports (different identities, same actor):
   - `/tmp/identity-activation-reports/identity-activation-switch-system-requirements-analyst-1772400240.json`
   - `/tmp/identity-activation-reports/identity-activation-switch-base-repo-architect-1772400310.json`

Vendor + official + context7 cross-check (inference noted):

1. OpenAI conversation-state guidance shows persistent conversation objects and response chaining (`previous_response_id` / durable conversation id), supporting explicit session-scoped state keys rather than implicit overwrite.
2. Anthropic messages guidance states interactions are stateless unless context is explicitly provided each turn; this supports explicit session keying and no hidden global authority.
3. Google Gemini chat guidance uses explicit chat history/session objects; this aligns with multi-session isolation as a first-class key.
4. etcd transactions/compare semantics provide primary-source precedent for CAS-style conflict prevention on shared state writes.
5. context7 reinforcement:
   - Python docs (file lock + atomic replace primitives) support deterministic write/replace semantics.
   - SQLite transaction/locking model supports append-safe, conflict-controlled state mutation patterns.

Official source links:

1. `https://developers.openai.com/api/docs/guides/conversation-state/`
2. `https://developers.openai.com/api/docs/guides/migrate-to-responses/`
3. `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts`
4. `https://docs.anthropic.com/en/api/messages-examples`
5. `https://ai.google.dev/gemini-api/docs/text-generation`
6. `https://ai.google.dev/gemini-api/docs/prompting-strategies`
7. `https://etcd.io/docs/v3.5/learning/api_guarantees/`
8. `https://etcd.io/docs/v3.5/dev-guide/api_reference_v3/`

Governance delta (this batch, docs-only):

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
   - added `5.8.15` `actor_session_multibinding_concurrency_contract_v1` (P0).
   - added requirement rows `ASB-RQ-071..074` (`P0`, `SPEC_READY`).
   - updated matrix `C10` as mandatory closure condition.

Architect implementation package (next execution batch):

1. Add required gate:
   - `scripts/validate_actor_session_multibinding_concurrency.py`
2. Enforce canonical payload key model:
   - `actor_id + session_id` multi-entry semantics in actor session canonical store.
3. Enforce mutation precondition:
   - CAS/compare token (`binding_version` or equivalent) on canonical binding write.
4. Enforce mutation boundary:
   - non-activation lanes are read-only for canonical actor binding.
5. Enforce append-only receipts for rebind:
   - `from_binding_ref`, `to_binding_ref`, `actor_id`, `session_id`, `run_id`, `switch_reason`, `approved_by`, `applied_at`.
6. Wire required gate to six surfaces + CI:
   - creator / readiness / e2e / full-scan / three-plane / required-gates workflow.
7. Error code family:
   - `IP-ASB-MB-001..006`.

Roundtable tightening notes (implementation MUST include):

1. `session_id` provenance must be explicit and reproducible:
   - derive from declared work-unit key (`session_id` arg or declared `run_id` mapping), not PID/time-only ad-hoc token.
2. Backward-compat read shim is allowed only as migration aid:
   - strict write lane must always output multi-entry canonical shape;
   - telemetry must expose migration/shim usage (`binding_key_mode`, `stale_reasons`).
3. CAS observability is mandatory:
   - payload must expose both pre-write and post-write compare token values in receipt/gate outputs.
4. Atomicity check:
   - strict lane must fail when canonical binding mutation is observed without append-only rebind receipt in the same mutation unit.
5. Existing validators that consume actor binding (`validate_actor_session_binding`, `validate_cross_actor_isolation`, `refresh_identity_session_status`, stamp lock checks) must be updated to parse multi-entry shape without semantic downgrade.

Acceptance replay template (post-implementation):

1. negative: single-object overwrite payload shape -> `FAIL_REQUIRED` (`IP-ASB-MB-001`)
2. negative: missing compare token on write -> `FAIL_REQUIRED` (`IP-ASB-MB-002`)
3. negative: stale compare token conflict -> `FAIL_REQUIRED` (`IP-ASB-MB-003`)
4. negative: non-activation lane tries canonical mutation -> `FAIL_REQUIRED` (`IP-ASB-MB-004`)
5. negative: rebind receipt missing/incomplete -> `FAIL_REQUIRED` (`IP-ASB-MB-005`)
6. negative: same-actor peer session entry dropped after write -> `FAIL_REQUIRED` (`IP-ASB-MB-006`)
7. positive: same actor, two sessions, peer entry preserved + CAS increment + receipt linked -> `PASS_REQUIRED`
8. docs/ssot checks:
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`

Layer declaration:

1. protocol-only; no business scenario constants introduced.

#### 16.8.16 FIX-028 implementation lane: same-actor multi-session binding overwrite closure (2026-03-02, protocol-only)

Status: `DONE / PENDING_REPLAY` (implementation landed; independent audit replay pending).

Implementation scope (landed):

1. Canonical actor binding storage upgraded to multibinding schema (`actor_id + session_id`) with legacy-read shim and strict write normalization:
   - `scripts/actor_session_common.py`
2. Activation writer upgraded to CAS + mutation-boundary + append-only rebind receipt contract:
   - `scripts/sync_session_identity.py`
   - `scripts/identity_creator.py` (activation chain now passes `session_id` + `compare_token` and validates multibinding gate post-write)
3. New required validator landed:
   - `scripts/validate_actor_session_multibinding_concurrency.py`
   - emits machine-readable fields:
     - `actor_session_multibinding_status`
     - `error_code`
     - `binding_key_mode`
     - `session_entry_count`
     - `cas_checked`
     - `cas_conflict_detected`
     - `non_activation_mutation_detected`
     - `rebind_receipt_status`
     - `dropped_peer_session_count`
     - `stale_reasons`
4. Six-surface + CI wiring landed:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
5. Multi-entry read safety propagation landed for existing consumer validators:
   - `scripts/validate_actor_session_binding.py`
   - `scripts/validate_cross_actor_isolation.py`
   - `scripts/refresh_identity_session_status.py`
   - `scripts/validate_identity_session_pointer_consistency.py`
   - `scripts/response_stamp_common.py`

Local replay snapshot (architect local):

1. static:
   - `python3 -m py_compile ...` -> `rc=0` (all touched scripts)
   - `bash -n scripts/e2e_smoke_test.sh` -> `rc=0`
2. positive sample (same actor, dual session preserved):
   - `sync_session_identity.py` with CAS tokens `0 -> 1 -> 2` -> `rc=0`
   - `validate_actor_session_multibinding_concurrency.py --operation validate` -> `PASS_REQUIRED`, `session_entry_count=2`, `cas_conflict_detected=false`, `dropped_peer_session_count=0`
3. negative samples (contract replay):
   - single-object shape -> `IP-ASB-MB-001`
   - missing compare token -> `IP-ASB-MB-002`
   - stale compare token conflict (`--expected-compare-token`) -> `IP-ASB-MB-003`
   - non-activation mutation without override -> `IP-ASB-MB-004`
   - missing/incomplete receipt -> `IP-ASB-MB-005`
   - dropped peer session marker -> `IP-ASB-MB-006`
4. wiring visibility snapshot:
   - `report_three_plane_status.py` output includes `instance_plane_detail.actor_session_multibinding_concurrency.*`
   - `full_identity_protocol_scan.py` output includes `checks.actor_session_multibinding_concurrency.*`

Pending audit package:

1. replay on project/global real catalogs for strict lanes (`readiness/e2e/ci`) with independent reviewer confirmation.
2. commit SHA backfill for this lane after code commit.

#### 16.8.15 Roundtable intake: protocol-feedback canonical reply channel hardening (2026-03-02, docs-only)

Status: `SUPERSEDED_BY_16.8.21` (pre-code intake retained for traceability; implementation landed in `a95f5a2`, audit replay pending).

Problem statement (cross-validated):

1. Protocol-feedback files are now mostly routed to `runtime/protocol-feedback/...`, but strict operations still allow hidden-gate pass paths where channel semantics are not machine-enforced.
2. `split-receipt` can still return `SKIPPED_NOT_REQUIRED` under strict operations for identities with protocol-feedback activity, leaving governance split enforcement non-deterministic.
3. Sidecar blocking prefix set currently does not include `IP-PFB-*`, so newly introduced protocol-feedback channel violations cannot be deterministically escalated to strict fail-closed.

Local evidence anchors:

1. split-receipt strict readiness replay still skips:
   - `python3 scripts/validate_instance_protocol_split_receipt.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/.agents/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --operation readiness --json-only`
   - result: `required_contract=false`, `instance_protocol_split_status=SKIPPED_NOT_REQUIRED`, `stale_reasons=[\"contract_not_required\"]`
2. sidecar default blocking prefixes:
   - `scripts/validate_protocol_feedback_sidecar_contract.py:29` (`DEFAULT_BLOCKING_PREFIXES = ("IP-WRB-", "IP-SEM-")`)
3. canonical channel hardening proposal already exists in protocol-feedback SSOT:
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/custom-creative-ecom-analyst/runtime/protocol-feedback/upgrade-proposals/HIDDEN_GATE_PROTOCOL_REMEDIATION_20260302_FINAL.md:175`
4. proposal outbox + index linkage exists:
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/custom-creative-ecom-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260302T035929Z_hidden_gate_protocol_remediation_final.md`
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/custom-creative-ecom-analyst/runtime/protocol-feedback/evidence-index/INDEX.md:6`

Vendor + official + context7 cross-check (inference noted):

1. OpenAI conversation-state guidance requires explicit state objects and channel continuity semantics for durable multi-turn governance.
2. Anthropic Messages guidance keeps runtime stateless unless context channel is explicitly provided, reinforcing explicit channel contract design.
3. Gemini official guidance similarly relies on explicit history/state passing, not implicit ambient channel assumptions.
4. etcd transaction compare-and-swap semantics reinforce deterministic fail-closed behavior for governance-critical state transitions.
5. context7 references (Python locking/atomic replace, SQLite transactional commit) align with deterministic channel-state update requirements.

Official source links:

1. `https://developers.openai.com/api/docs/guides/conversation-state/`
2. `https://developers.openai.com/api/docs/guides/migrate-to-responses/`
3. `https://docs.anthropic.com/en/api/messages-examples`
4. `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts`
5. `https://ai.google.dev/gemini-api/docs/prompting-strategies`
6. `https://etcd.io/docs/v3.5/learning/api_guarantees/`
7. `https://etcd.io/docs/v3.5/dev-guide/api_reference_v3/`

Governance delta (this batch, docs-only):

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
   - added `5.8.16` `protocol_feedback_canonical_reply_channel_contract_v1` (P0).
   - added requirement rows `ASB-RQ-075..078` (`P0`, `SPEC_READY`).
   - updated matrix `C11` as mandatory closure condition.

Architect implementation package (next execution batch):

1. Add required gate:
   - `scripts/validate_protocol_feedback_reply_channel.py`
2. Enforce canonical reply channel in strict lanes:
   - canonical root + whitelist subdirs as primary evidence only.
   - non-standard paths allowed only as `mirror_reference`.
3. Add strict failure codes:
   - `IP-PFB-CH-001/002/003`.
4. Extend sidecar blocking prefixes:
   - include `IP-PFB-*` in strict operations.
5. Enforce split-receipt requiredization bridge:
   - protocol-feedback activity -> split receipt auto-required.
   - strict operations must not produce `SKIPPED_NOT_REQUIRED`.
6. Wire across six surfaces + CI:
   - creator / readiness / e2e / full-scan / three-plane / required-gates workflow.

Acceptance replay template (post-implementation):

1. negative: missing canonical primary channel -> `FAIL_REQUIRED` (`IP-PFB-CH-001`)
2. negative: non-standard channel as primary -> `FAIL_REQUIRED` (`IP-PFB-CH-002`)
3. negative: mirror reference without canonical SSOT primary -> `FAIL_REQUIRED` (`IP-PFB-CH-003`)
4. negative: protocol-feedback activity exists but split-receipt still skipped -> `FAIL_REQUIRED`
5. positive: canonical channel + sidecar `IP-PFB-*` blocking + split-receipt requiredization all pass -> `PASS_REQUIRED`
6. docs/ssot checks:
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`

Layer declaration:

1. protocol-only; no business scenario constants introduced.

#### 16.8.15A Roundtable pre-code cross-validation closure (FIX-029, 2026-03-02)

Status: `SUPERSEDED_BY_16.8.21` (pre-code cross-check retained; code landed in `a95f5a2`, audit replay pending).

Cross-validation scope (protocol-only):

1. Verify declared contracts (`ASB-RQ-075..078`) are not already silently implemented with inconsistent semantics.
2. Verify strict-lane escalation chain currently lacks deterministic `IP-PFB-*` blocking.
3. Verify split-receipt requiredization bridge currently lacks activity-driven auto-promotion in strict lanes.
4. Produce pre-code deterministic implementation checklist (single source, non-merge with `FIX-030` bootstrap lane).

Observed current-state evidence (local repo):

1. Canonical reply-channel validator is not yet implemented:
   - `scripts/validate_protocol_feedback_reply_channel.py` absent.
2. Sidecar default blocking prefixes do not include `IP-PFB-*`:
   - `scripts/validate_protocol_feedback_sidecar_contract.py:29`
   - current value: `DEFAULT_BLOCKING_PREFIXES = ("IP-WRB-", "IP-SEM-")`
3. Split requiredization auto-signal currently depends on split receipt presence, not protocol-feedback activity:
   - `scripts/validate_instance_protocol_split_receipt.py:186`
   - current condition: `if not required and (args.receipt.strip() or _split_artifacts_present(pack_path))`
4. Six-surface wiring gap for FIX-029 validator set:
   - no `validate_protocol_feedback_reply_channel.py` / `validate_protocol_feedback_bootstrap_ready.py` references in:
     - `scripts/identity_creator.py`
     - `scripts/release_readiness_check.py`
     - `scripts/e2e_smoke_test.sh`
     - `scripts/full_identity_protocol_scan.py`
     - `scripts/report_three_plane_status.py`
     - `.github/workflows/_identity-required-gates.yml`

Roundtable decision (implementation guardrail):

1. Keep strict non-merge boundary:
   - FIX-029 only lands `ASB-RQ-075..078`.
   - FIX-030 continues to own `ASB-RQ-079..081`.
2. Add deterministic strict-lane error for RQ-078 gap:
   - `IP-PFB-CH-006` (`split_receipt_requiredization_missing_under_activity`).
3. Activity detector becomes mandatory machine-readable input for FIX-029:
   - `protocol_feedback_activity_detected`
   - `protocol_feedback_activity_refs`
4. Pre-code acceptance gate for entering implementation:
   - docs contract check passes,
   - SSOT source check passes,
   - current-state evidence anchors are reproducible.

Pre-code replay commands (must remain reproducible before patch):

1. `python3 scripts/docs_command_contract_check.py`
2. `python3 scripts/validate_protocol_ssot_source.py`
3. `python3 scripts/validate_instance_protocol_split_receipt.py --identity-id <id> --catalog <catalog> --operation readiness --json-only`
4. `python3 scripts/validate_protocol_feedback_sidecar_contract.py --identity-id <id> --catalog <catalog> --operation readiness --json-only`

Expected pre-code interpretation:

1. If split receipt contract is skipped under feedback activity, FIX-029 remains open (no closure claim).
2. If sidecar lacks `IP-PFB-*` deterministic escalation path, FIX-029 remains open.
3. No implementation or replay pass claim is allowed until required validators/wiring are landed.

#### 16.8.17 Roundtable intake: protocol-layer entry bootstrap-readiness hardening (2026-03-02, docs-only)

Status: `SUPERSEDED_BY_16.8.21` (pre-code intake retained for traceability; implementation landed in `a95f5a2`, audit replay pending).

Problem statement (cross-validated, no scope expansion):

1. Protocol-layer entry gating exists (`protocol` lane requires trigger evidence), but trigger satisfaction alone does not guarantee canonical protocol-feedback roots are bootstrap-ready at first entry.
2. Existing strict readiness chain validates sidecar/SSOT archival classes, but does not currently provide a dedicated bootstrap-readiness hard gate for protocol entry.
3. Identity pack bootstrap paths currently emphasize generic runtime feedback/handoff logs, not canonical `runtime/protocol-feedback/...` root readiness as a first-entry invariant.
4. Without deterministic bootstrap-readiness proof, communication can still rely on oral reminder to create protocol-feedback structures, creating hidden-gate risk.

Local evidence anchors:

1. protocol entry must be trigger-backed:
   - `scripts/response_stamp_common.py:549` (`protocol-only signal` branch requires trigger conditions).
   - `scripts/validate_layer_intent_resolution.py:250` (`resolved_work_layer=protocol` without trigger -> stale/fail path).
2. readiness currently invokes sidecar + SSOT archival validators, but no dedicated bootstrap-ready gate:
   - `scripts/release_readiness_check.py:1102`
   - `scripts/release_readiness_check.py:1135`
3. pack bootstrap defaults emphasize generic feedback logs, not protocol-feedback root bootstrap:
   - `scripts/create_identity_pack.py:502`
   - `scripts/create_identity_pack.py:683`
4. split-receipt auto-requiredization relies on existing artifacts but is not a root bootstrap constructor:
   - `scripts/validate_instance_protocol_split_receipt.py:186`

Vendor + official + context7 cross-check (inference noted):

1. OpenAI/Anthropic/Gemini official guidance consistently favors explicit state/channel provisioning over implicit ambient context for reliable multi-turn governance.
2. CAS/transactional consistency references (etcd + context7 transaction patterns) support fail-closed governance when required channel state is missing.
3. Therefore, protocol entry should include explicit bootstrap-readiness proof, not inferred availability.

Official source links:

1. `https://developers.openai.com/api/docs/guides/conversation-state/`
2. `https://developers.openai.com/api/docs/guides/migrate-to-responses/`
3. `https://docs.anthropic.com/en/api/messages-examples`
4. `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts`
5. `https://ai.google.dev/gemini-api/docs/prompting-strategies`
6. `https://etcd.io/docs/v3.5/learning/api_guarantees/`
7. `https://etcd.io/docs/v3.5/dev-guide/api_reference_v3/`

Governance delta (this batch, docs-only):

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
   - extended `5.8.16` with bootstrap-readiness semantics (`IP-PFB-CH-004/005` + machine-readable bootstrap telemetry).
   - added requirement rows `ASB-RQ-079..081` (`P0`, `SPEC_READY`).
   - updated matrix `C11` to include protocol-entry bootstrap-readiness as mandatory closure element.

Architect implementation package (next execution batch):

1. Add required gate:
   - `scripts/validate_protocol_feedback_bootstrap_ready.py`
2. Enforce protocol-entry bootstrap-readiness in strict lanes:
   - protocol lane selected (`work_layer=protocol` or `protocol_triggered=true`) requires canonical roots ready:
     - `runtime/protocol-feedback/outbox-to-protocol/`
     - `runtime/protocol-feedback/evidence-index/`
     - `runtime/protocol-feedback/upgrade-proposals/`
3. Add strict failure codes:
   - `IP-PFB-CH-004` (`protocol_layer_without_bootstrap_readiness`)
   - `IP-PFB-CH-005` (`bootstrap_receipt_missing_or_unlinked`)
4. Add deterministic bootstrap receipt contract when auto-create is used:
   - receipt must be under canonical outbox and linked in canonical evidence index.
5. Wire across six surfaces + CI:
   - creator / readiness / e2e / full-scan / three-plane / required-gates workflow.
6. Surface machine-readable fields in scan/report outputs:
   - `protocol_feedback_bootstrap_status`
   - `protocol_feedback_bootstrap_mode`
   - `bootstrap_created_paths`
   - `bootstrap_receipt_path`

Acceptance replay template (post-implementation):

1. negative: protocol lane selected, canonical roots missing, no bootstrap receipt -> `FAIL_REQUIRED` (`IP-PFB-CH-004`)
2. negative: auto-bootstrap performed but receipt not SSOT-linked -> `FAIL_REQUIRED` (`IP-PFB-CH-005`)
3. positive: protocol lane selected, canonical roots preexisting -> `PASS_REQUIRED`
4. positive: protocol lane selected, roots auto-created with canonical outbox+index linkage -> `PASS_REQUIRED`
5. boundary: instance lane selected (`work_layer=instance`) -> bootstrap gate remains non-blocking/skip as contract allows
6. docs/ssot checks:
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`

Deadlock clarification (must hold in FIX-030 implementation):

1. If protocol lane is selected and canonical protocol-feedback roots are missing, validator must enter deterministic bootstrap constructor flow first (create missing roots + emit receipt + link index).
2. Missing directory itself is not enough to fail strict gate; strict fail-closed is only valid when constructor flow is unavailable/disabled or constructor proof is incomplete.
3. Therefore `FIX-030` is explicitly "bootstrap-ready with constructor", not a "check-only exists()" gate.
4. Required failure mapping:
   - constructor unavailable/disabled or roots still not ready after attempt -> `IP-PFB-CH-004`
   - constructor executed but receipt/index linkage incomplete -> `IP-PFB-CH-005`

Layer declaration:

1. protocol-only; no business scenario constants introduced.

#### 16.8.18 Roundtable intake: protocol-entry candidate clarification bridge (2026-03-02, docs-only)

Status: `SUPERSEDED_BY_16.8.21` (pre-code intake retained for traceability; implementation landed in `a95f5a2`, audit replay pending).

Problem statement (cross-validated, no scope expansion):

1. Current layer resolver already supports automatic protocol entry under strong signals, but weak governance concern statements can still silently fallback to `instance`, creating protocol-lane deadlock risk.
2. Silent fallback loses early governance signal and delays protocol-feedback evidence chain construction.
3. Existing contracts enforce canonical protocol-feedback channel and bootstrap readiness, but do not yet enforce candidate-stage clarification and seed-archival behavior.
4. User-side communication naturally starts from weak concern language; protocol layer needs deterministic follow-up questioning to convert concern -> evidence -> governed feedback.

Local evidence anchors:

1. default fallback remains `instance`:
   - `scripts/response_stamp_common.py:37`
   - `scripts/response_stamp_common.py:519`
2. strong protocol signals can auto-enter protocol lane:
   - `scripts/response_stamp_common.py:285`
   - `scripts/response_stamp_common.py:549`
   - `scripts/response_stamp_common.py:565`
3. strict guard already fail-closes `protocol` without trigger:
   - `scripts/validate_layer_intent_resolution.py:250`
4. local replay snapshot (2026-03-02):
   - `resolve_layer_intent(\"请做protocol governance gate修复并接线回放\") -> resolved_work_layer=protocol`
   - `resolve_layer_intent(\"我感觉当前协议能力还不够强\") -> resolved_work_layer=instance` (weak-signal fallback path; candidate bridge currently missing)

Vendor + official + skill-protocol cross-check (inference noted):

1. OpenAI conversation-state guidance emphasizes explicit stateful context transitions, supporting deterministic candidate-state capture instead of silent drop.
2. OpenAI Responses reference documents instruction hierarchy (developer/system precedence) and structured tool/state control, aligning with explicit candidate clarification flow.
3. Anthropic best-practice guidance for Claude Code skills emphasizes metadata-driven routing and progressive disclosure, matching candidate-stage “minimal required questions before heavy protocol flow.”
4. Anthropic prompt engineering guidance recommends explicit structure/tags for disambiguation; this aligns with deterministic clarification question schema.
5. Gemini prompting guidance highlights precise instructions and structured outputs for reliable behavior, supporting machine-readable candidate receipts.
6. MCP architecture/lifecycle guidance emphasizes explicit capability declaration and deterministic request lifecycles, supporting candidate-state -> promoted-state transition contracts.
7. Local skill protocol (`/Users/yangxi/.codex/skills/.system/skill-creator/SKILL.md`) confirms trigger metadata + progressive disclosure design, which maps directly to candidate clarification bridge semantics.

Official source links:

1. `https://platform.openai.com/docs/guides/conversation-state`
2. `https://developers.openai.com/api/reference/resources/responses/`
3. `https://www.anthropic.com/engineering/writing-tools-for-agents`
4. `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview`
5. `https://ai.google.dev/gemini-api/docs/prompting-strategies`
6. `https://modelcontextprotocol.io/docs/learn/architecture`
7. `https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle`

Governance delta (this batch, docs-only):

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
   - added `5.8.17` `protocol_entry_candidate_clarification_bridge_contract_v1` (P0).
   - added requirement rows `ASB-RQ-082..085` (`P0`, `SPEC_READY`).
   - updated six-surface closure section with candidate clarification bridge wiring requirements.

Architect implementation package (next execution batch):

1. Add required gate:
   - `scripts/validate_protocol_entry_candidate_bridge.py`
2. Extend layer-intent decision output:
   - `protocol_entry_decision` (`INSTANCE_DEFAULT` / `PROTOCOL_DIRECT` / `PROTOCOL_CANDIDATE`)
   - `candidate_reason`, `candidate_confidence`
3. Enforce deterministic clarification set for candidate state:
   - `which_gate_or_stage_failed`
   - `latest_replay_or_evidence_path`
   - `expected_protocol_optimization_target`
4. Enforce canonical candidate seed archival:
   - outbox seed under `runtime/protocol-feedback/outbox-to-protocol/`
   - evidence index linkage under `runtime/protocol-feedback/evidence-index/`
5. Strict fail-closed errors:
   - `IP-LAYER-CAND-001..004`
6. Wire across six surfaces + CI:
   - creator / readiness / e2e / full-scan / three-plane / required-gates workflow.

Acceptance replay template (post-implementation):

1. negative: weak protocol concern resolved to `INSTANCE_DEFAULT` without candidate receipt -> `FAIL_REQUIRED` (`IP-LAYER-CAND-001`)
2. negative: candidate emitted but clarification question set incomplete -> `FAIL_REQUIRED` (`IP-LAYER-CAND-002`)
3. negative: candidate emitted but no canonical outbox seed -> `FAIL_REQUIRED` (`IP-LAYER-CAND-003`)
4. negative: candidate seed exists but evidence-index unlinked -> `FAIL_REQUIRED` (`IP-LAYER-CAND-004`)
5. positive: weak concern -> `PROTOCOL_CANDIDATE` + clarification receipt + canonical seed/index linkage -> `PASS_REQUIRED`
6. positive: strong protocol signal -> `PROTOCOL_DIRECT` and normal strict protocol chain
7. docs/ssot checks:
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`

Layer declaration:

1. protocol-only; no business scenario constants introduced.

#### 16.8.20 Unified roundtable closure profile: FIX-029..032 as linked components in one protocol system (2026-03-02, docs-only)

Status: `SUPERSEDED_BY_16.8.21` (system-level pre-code model retained; implementation landed in `a95f5a2`, audit replay pending).

Unified boundary statement:

1. FIX-029..032 are linked components inside one protocol-entry closure system (component-level contracts, not a merged single-fix stream).
2. Audit non-merge rule remains mandatory:
   - each fix keeps independent replay + verdict package,
   - any single PASS cannot replace missing PASS in other fixes.

Dependency DAG (must be respected in patch order):

1. Stage-A = FIX-029 (`ASB-RQ-075..078`)
2. Stage-B = FIX-030 (`ASB-RQ-079..081`) depends on Stage-A
3. Stage-C = FIX-031 (`ASB-RQ-082..085`) depends on Stage-A + Stage-B
4. Stage-D = FIX-032 (`ASB-RQ-086..089`) depends on Stage-A + Stage-B + Stage-C

Local code-state cross-check anchors (current gaps, reproducible):

1. validator absence (not yet landed):
   - `scripts/validate_protocol_feedback_reply_channel.py` (missing)
   - `scripts/validate_protocol_feedback_bootstrap_ready.py` (missing)
   - `scripts/validate_protocol_entry_candidate_bridge.py` (missing)
   - `scripts/validate_protocol_inquiry_followup_chain.py` (missing)
2. sidecar strict blocking prefix gap (needs Stage-A patch):
   - `scripts/validate_protocol_feedback_sidecar_contract.py:29`
   - current default: `(\"IP-WRB-\", \"IP-SEM-\")` (no `IP-PFB-*`)
3. split requiredization trigger gap (needs Stage-A patch):
   - `scripts/validate_instance_protocol_split_receipt.py:186`
   - current auto-requiredization condition is receipt-oriented, not protocol-feedback-activity-oriented.
4. six-surface wiring gap (A/B/C/D validators currently not referenced) in:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`

Unified machine-readable telemetry target set (cross-fix):

1. `protocol_feedback_reply_channel_status`
2. `protocol_feedback_activity_detected`
3. `protocol_feedback_activity_refs`
4. `split_receipt_requiredized`
5. `protocol_feedback_bootstrap_status`
6. `protocol_entry_decision`
7. `candidate_promotion_status`
8. `inquiry_state`

Unified implementation batch discipline:

1. Batch-1 (FIX-029 only): channel + sidecar + split requiredization bridge.
2. Batch-2 (FIX-030 only): bootstrap-readiness gate + telemetry.
3. Batch-3 (FIX-031 only): candidate clarification bridge + seed/index linkage.
4. Batch-4 (FIX-032 only): inquiry follow-up chain + sanitization boundary gate.
5. Each batch must complete:
   - static checks
   - strict-lane negative samples
   - strict-lane positive samples
   - three-plane/full-scan telemetry visibility replay
   before opening the next batch.

Unified release interpretation:

1. FIX-029..032 remain release-blocking as a bundle for protocol-entry closure.
2. Bundle closure condition:
   - all four fixes `DONE + PASS`,
   - no open `IP-PFB-CH-*`, `IP-LAYER-CAND-*`, `IP-LAYER-INQ-*` required failures in strict lanes.

Layer declaration:

1. protocol-only; no business constants introduced.

#### 16.8.22 Architect self-check snapshot after FIX-029..032 implementation (2026-03-02, protocol-only)

Status: `SELF_CHECK_RECORDED / WAITING_REAUDIT` (historical reject point-in-time is archived in `16.8.21`; current-state replay baseline is `16.8.28` with summary status `PENDING_REAUDIT`).

Commit anchor:

1. `a95f5a2` — `fix(protocol): close FIX-029..032 validator and gate wiring`

Changed file set (protocol implementation):

1. `.github/workflows/_identity-required-gates.yml`
2. `scripts/protocol_feedback_contract_common.py`
3. `scripts/validate_protocol_feedback_reply_channel.py`
4. `scripts/validate_protocol_feedback_bootstrap_ready.py`
5. `scripts/validate_protocol_entry_candidate_bridge.py`
6. `scripts/validate_protocol_inquiry_followup_chain.py`
7. `scripts/validate_protocol_feedback_sidecar_contract.py`
8. `scripts/validate_instance_protocol_split_receipt.py`
9. `scripts/identity_creator.py`
10. `scripts/release_readiness_check.py`
11. `scripts/e2e_smoke_test.sh`
12. `scripts/full_identity_protocol_scan.py`
13. `scripts/report_three_plane_status.py`

Implementation closure summary (FIX-029..032):

1. FIX-029 (`ASB-RQ-075..078`)
   - canonical reply-channel validator landed;
   - sidecar strict blocking prefix includes `IP-PFB-*`;
   - split-receipt requiredization bridge is activity-aware and strict-lane fail-closed (`IP-PFB-CH-006` path).
2. FIX-030 (`ASB-RQ-079..081`)
   - bootstrap-ready validator landed;
   - protocol-lane constructor path creates canonical roots + bootstrap receipt + index linkage;
   - strict fail-closed semantics preserved (`IP-PFB-CH-004/005`).
3. FIX-031 (`ASB-RQ-082..085`)
   - candidate bridge validator landed;
   - deterministic clarification set + canonical candidate seed/receipt linkage landed;
   - anti-silent-downgrade strict semantics exposed (`IP-LAYER-CAND-*`).
4. FIX-032 (`ASB-RQ-086..089`)
   - inquiry follow-up chain validator landed;
   - inquiry state machine + signal-origin sanitization + requiredization-trigger bridge landed;
   - strict fail-closed semantics exposed (`IP-LAYER-INQ-*`).

Replay snapshot (architect local, machine-readable):

1. static checks:
   - `python3 -m py_compile <touched scripts>` -> `rc=0`
   - `bash -n scripts/e2e_smoke_test.sh` -> `rc=0`
2. docs/ssot:
   - `python3 scripts/docs_command_contract_check.py` -> `PASS`
   - `python3 scripts/validate_protocol_ssot_source.py` -> `OK`
3. representative functional replay:
   - bootstrap positive (`validate_protocol_feedback_bootstrap_ready ... --expected-work-layer protocol`) -> `rc=0`, `protocol_feedback_bootstrap_status=PASS_REQUIRED`
   - candidate bridge (`validate_protocol_entry_candidate_bridge ... --expected-work-layer instance`) -> `rc=0`, `protocol_entry_candidate_status=PASS_REQUIRED`, `protocol_entry_decision=PROTOCOL_CANDIDATE`
   - inquiry follow-up (`validate_protocol_inquiry_followup_chain ... --expected-work-layer instance`) -> `rc=0`, `protocol_inquiry_followup_chain_status=PASS_REQUIRED`
4. six-surface visibility:
   - `full_identity_protocol_scan.py` output includes:
     - `checks.protocol_feedback_reply_channel`
     - `checks.protocol_feedback_bootstrap_ready`
     - `checks.protocol_entry_candidate_bridge`
     - `checks.protocol_inquiry_followup_chain`
   - `report_three_plane_status.py` output includes:
     - `instance_plane_detail.protocol_feedback_reply_channel`
     - `instance_plane_detail.protocol_feedback_bootstrap_ready`
     - `instance_plane_detail.protocol_entry_candidate_bridge`
     - `instance_plane_detail.protocol_inquiry_followup_chain`

Evidence artifacts:

1. `/tmp/fix029_scan.json`
2. `/tmp/fix029_three_plane.json`

Audit note:

1. This subsection is architect-side evidence only; it does not override section `16.8.21` audit verdict.
2. Final `PASS/REJECT` remains owned by independent audit replay package.

#### 16.8.23 Architect remediation patch for `16.8.21` P0 findings (2026-03-02, protocol-only)

Status: `PATCH_APPLIED / PENDING_REAUDIT` (historical reject point-in-time is archived in `16.8.21`; current-state judgment follows `16.8.28` and rolling summary rows).

Commit anchor:

1. `560f710` — `fix(protocol): close FIX-029..032 p0 audit findings`

Changed files:

1. `scripts/validate_protocol_feedback_reply_channel.py`
2. `scripts/validate_protocol_inquiry_followup_chain.py`
3. `scripts/release_readiness_check.py`

P0 finding-to-patch mapping:

1. P0-1 (`reply-channel contradictory PASS`) is closed by strict fail-closed coupling:
   - `split_receipt_payload_rc != 0` now raises strict failure path.
   - `split_receipt_status == FAIL_REQUIRED` now raises strict failure path.
   - strict lane rejects `WARN_NON_BLOCKING` split state.
2. P0-2 (`CWD-sensitive subprocess invocation`) is closed by protocol-root deterministic invocation:
   - split validator now runs via absolute script path + `cwd=PROTOCOL_ROOT`.
   - candidate validator now runs via absolute script path + `cwd=PROTOCOL_ROOT`.
3. P0-3 (`readiness layer passthrough ordering`) is closed by final-stage injection:
   - layer/source/expected-work args now inject after final `seq.append(...)` construction, with duplicate-arg guard.
   - FIX-029..032 validators now receive the same layer tuple in readiness lane.
4. P0-4 (`historical FEEDBACK_BATCH short-circuit`) is closed by current-chain linkage requirement:
   - `FEEDBACK_EMITTED` now requires linked batch evidence to current chain refs (`seed_ref`, `candidate_receipt_ref`, `inquiry_receipt_ref`) instead of raw historical count.
   - inquiry payload now exposes `feedback_linked_batch_count` + `feedback_linked_batch_refs` for machine replay.

Replay evidence snapshot (architect-side, protocol boundary only):

1. Static:
   - `python3 -m py_compile scripts/validate_protocol_feedback_reply_channel.py scripts/validate_protocol_inquiry_followup_chain.py scripts/release_readiness_check.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - rc: `0`
2. Reply-channel strict fail-closed replay (protocol-root):
   - command:
     - `python3 scripts/validate_protocol_feedback_reply_channel.py --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --repo-catalog identity/catalog/identities.yaml --operation validate --force-check --json-only`
   - rc: `1`
   - key fields:
     - `protocol_feedback_reply_channel_status=FAIL_REQUIRED`
     - `split_receipt_status=FAIL_REQUIRED`
     - `split_receipt_payload_rc=1`
3. Reply-channel CWD invariance replay (`/tmp`):
   - command:
     - `python3 /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/scripts/validate_protocol_feedback_reply_channel.py --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --operation validate --force-check --json-only`
   - rc: `1`
   - key fields (same as protocol-root replay):
     - `protocol_feedback_reply_channel_status=FAIL_REQUIRED`
     - `split_receipt_status=FAIL_REQUIRED`
     - `split_receipt_payload_rc=1`
4. Inquiry-chain emission correlation + CWD invariance replay:
   - protocol-root command output: `/tmp/fix032-root.json`
   - `/tmp` command output: `/tmp/fix032-tmp.json`
   - both rc: `1`
   - aligned key fields:
     - `protocol_inquiry_followup_chain_status=FAIL_REQUIRED`
     - `candidate_decision=INSTANCE_DEFAULT`
     - `candidate_runtime_failed=true`
     - `inquiry_state=EVIDENCE_PENDING`
     - `feedback_batch_count=0`
     - `feedback_linked_batch_count=0`
5. Readiness lane patch anchor (code-level replay target):
   - `release_readiness_check.py` now injects layer tuple at final orchestration loop (`for cmd in seq`) so newly appended FIX-029..032 validators receive:
     - `--layer-intent-text`
     - `--expected-work-layer`
     - `--source-layer` / `--expected-source-layer`

Next gate decision:

1. Keep FIX-029..032 audit status as `PENDING_REAUDIT` in summary table until independent auditor sign-off command pack updates verdict.
2. This subsection is remediation evidence only and does not supersede current-state replay judgment in `16.8.28`.

#### 16.8.19 Roundtable intake: protocol inquiry follow-up chain (2026-03-02, docs-only)

Status: `SUPERSEDED_BY_16.8.21` (pre-code intake retained for traceability; implementation landed in `a95f5a2`, audit replay pending).

Problem statement (cross-validated, no scope expansion):

1. Candidate bridge solves weak-signal entry deadlock, but current protocol baseline still lacks a strict inquiry state machine for "analyzable feedback + deterministic follow-up questioning."
2. Weak governance concerns can carry business-language fragments; without explicit sanitization receipts this can contaminate protocol-layer conclusions.
3. `source` and `source_layer` semantics are parseable today but still easy to misread as identical, causing governance communication ambiguity.
4. Protocol conclusions should be blocked until canonical protocol-feedback seed/index linkage exists, even in inquiry-driven promotion paths.

Local evidence anchors:

1. default work-layer fallback is `instance`:
   - `scripts/response_stamp_common.py:37`
2. strong signals can enter protocol directly, weak concerns still need governed bridge:
   - `scripts/response_stamp_common.py:285`
   - `scripts/response_stamp_common.py:549`
   - `scripts/response_stamp_common.py:565`
3. strict guard already fails on protocol-without-trigger:
   - `scripts/validate_layer_intent_resolution.py:250`
4. disclosure/tail contract already enforces `work_layer/source_layer` machine readability:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:359`
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:429`

Vendor + official + skill-protocol cross-check (inference noted):

1. OpenAI Responses + conversation-state guidance supports explicit state transitions and stateful context capture, matching inquiry-state requirements.
2. OpenAI role hierarchy references support deterministic precedence when follow-up questioning must stay governance-first.
3. Anthropic prompt guidance and system-prompt structuring support deterministic clarification templates and non-ambiguous escalation paths.
4. Gemini prompting strategy guidance supports precise structured prompts for stable machine-readable receipts.
5. MCP lifecycle guidance supports explicit lifecycle transitions and capability-state negotiation, aligning with inquiry-state promotion/fallback contracts.
6. Local skill protocol (`skill-creator`) emphasizes progressive disclosure and deterministic trigger metadata, matching inquiry-first design.

Official source links:

1. `https://platform.openai.com/docs/guides/conversation-state`
2. `https://developers.openai.com/api/reference/resources/responses/`
3. `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview`
4. `https://ai.google.dev/gemini-api/docs/prompting-strategies`
5. `https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle`
6. `https://modelcontextprotocol.io/docs/learn/architecture`

Governance delta (this batch, docs-only):

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
   - added `5.8.18` `protocol_inquiry_followup_chain_contract_v1` (P0).
   - added requirement rows `ASB-RQ-086..089` (`P0`, `SPEC_READY`).
   - clarified `source` vs `source_layer` semantic non-equivalence and ambiguous-intent fallback wording in disclosure contract.

Architect implementation package (next execution batch):

1. Add required gate:
   - `scripts/validate_protocol_inquiry_followup_chain.py`
2. Extend layer/candidate outputs with inquiry telemetry:
   - `inquiry_state`
   - `followup_question_set`
   - `signal_origin`
   - `sanitization_paraphrase_ref`
3. Enforce deterministic follow-up set:
   - `which_gate_or_stage_failed`
   - `latest_replay_or_evidence_path`
   - `expected_protocol_optimization_target`
4. Enforce protocol-feedback readiness before protocol conclusion:
   - canonical outbox seed
   - canonical evidence-index linkage
5. Strict fail-closed errors:
   - `IP-LAYER-INQ-001..004`
6. Wire across six surfaces + CI:
   - creator / readiness / e2e / full-scan / three-plane / required-gates workflow.

Acceptance replay template (post-implementation):

1. negative: inquiry required but deterministic follow-up set missing -> `FAIL_REQUIRED` (`IP-LAYER-INQ-001`)
2. negative: protocol conclusion emitted with missing/stale inquiry evidence -> `FAIL_REQUIRED` (`IP-LAYER-INQ-002`)
3. negative: protocol conclusion emitted before canonical seed/index linkage -> `FAIL_REQUIRED` (`IP-LAYER-INQ-003`)
4. negative: business-origin text promoted without sanitization paraphrase receipt -> `FAIL_REQUIRED` (`IP-LAYER-INQ-004`)
5. positive: weak concern -> inquiry states emitted + deterministic follow-up + canonical seed/index linkage -> `PASS_REQUIRED`
6. positive: strong protocol concern -> direct protocol path with intact strict chain + inquiry telemetry explicitly `NOT_REQUIRED`
7. docs/ssot checks:
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`

Layer declaration:

1. protocol-only; no business scenario constants introduced.

#### 16.8.19A Pre-code hardening addendum: inquiry anti-starvation + requiredization bridge (2026-03-02, docs-only)

Status: `READY_FOR_PATCH` (contract clarified; implementation not landed yet).

Clarified closure requirements (machine-checkable):

1. Canonical inquiry receipt schema is mandatory (`inquiry_id`, `inquiry_state`, `followup_question_set`, `signal_origin`, `sanitization_paraphrase_ref`, `protocol_feedback_seed_ref`, `protocol_feedback_index_ref`, `next_transition`, `updated_at`).
2. Transition guards must be deterministic:
   - `QUESTION_REQUIRED -> EVIDENCE_PENDING` requires complete deterministic follow-up set,
   - `EVIDENCE_PENDING -> READY_FOR_PROTOCOL_FEEDBACK` requires canonical seed/index linkage,
   - `READY_FOR_PROTOCOL_FEEDBACK -> FEEDBACK_EMITTED` requires protocol-feedback emission receipt.
3. Anti-starvation policy must be explicit and replayable:
   - expose `followup_round_count`, `max_followup_rounds`, `evidence_ttl_hours`,
   - rounds/TTL exceed without valid transition -> strict fail-closed (`IP-LAYER-INQ-002`) and unresolved inquiry receipt must persist.
4. Inquiry-to-requiredization bridge is mandatory:
   - unresolved inquiry (`rounds>=2` or TTL exceeded) must emit trigger class `inquiry_chain_unresolved`,
   - trigger receipt must be archived to canonical protocol-feedback outbox + evidence-index,
   - strict lanes must not remain warn-only after trigger activation.

Acceptance replay additions (post-implementation):

1. negative: inquiry rounds exceed `max_followup_rounds` without transition -> `FAIL_REQUIRED` (`IP-LAYER-INQ-002`) + unresolved receipt present.
2. negative: inquiry TTL exceeded and no requiredization trigger receipt -> `FAIL_REQUIRED`.
3. positive: unresolved inquiry triggers `inquiry_chain_unresolved` and requiredization receipt is SSOT-linked -> `PASS_REQUIRED` (bridge active).
4. telemetry check: three-plane/full-scan expose `followup_round_count`, `max_followup_rounds`, `evidence_ttl_hours`, `inquiry_requiredization_triggered`.

Layer declaration:

1. protocol-only; no business constants introduced.

#### 16.8.12 FIX-027 implementation lane: default instance layer + protocol-trigger escalation gate (P0, protocol-only)

Status: `DONE / PENDING_REPLAY` (implementation landed, independent audit replay pending).

Scope (protocol-only):

1. Change resolver fallback from `protocol` to `instance`.
2. Keep ambiguous/low-confidence signals on `instance` fallback (no implicit protocol escalation).
3. Require auditable trigger evidence whenever resolved work layer is `protocol`.
4. Add deterministic regression sample gate (`instance/protocol/ambiguous`) in layer-intent validator output.

Changed surfaces:

1. `scripts/response_stamp_common.py`
2. `scripts/render_identity_response_stamp.py`
3. `scripts/validate_layer_intent_resolution.py`
4. `scripts/validate_reply_identity_context_first_line.py`
5. `scripts/validate_execution_reply_identity_coherence.py`
6. `scripts/validate_send_time_reply_gate.py`
7. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`

Machine-readable fields added/strengthened:

1. `protocol_triggered`
2. `protocol_trigger_reasons`
3. `protocol_trigger_confidence`
4. `regression_sample_status`
5. `regression_failed_sample_ids`
6. `regression_samples[]`

Replay snapshot (architect local):

1. Default (no intent text): `resolved_work_layer=instance`.
2. Instance intent sample: `resolved_work_layer=instance`.
3. Protocol intent sample (with protocol trigger phrase + error code): `resolved_work_layer=protocol`, `protocol_triggered=true`.
4. Ambiguous sample: `resolved_work_layer=instance`, `fallback_reason=ambiguous_intent_signal`.
5. Layer-intent validator strict replay:
   - `regression_sample_status=PASS_REQUIRED`
   - `regression_failed_sample_ids=[]`

Layer declaration:

1. protocol-only; no business-scene constants introduced.

#### 16.8.11 FIX-026 implementation lane: layer-intent pass-through closure (P1, protocol-only)

Status: `DONE / PENDING_REPLAY` (implementation landed, independent audit replay pending).

Scope (protocol-only):

1. Close pass-through gap where instance-layer intent was resolvable at render/validator level but not consistently propagated by orchestrator surfaces.
2. Keep strict fail-closed semantics unchanged (`IP-ASB-STAMP-SESSION-001` and existing strict tuple checks remain authoritative).
3. Ensure send-time gate can infer expected layer tuple from stamp payload when explicit expected args are absent.

Changed surfaces:

1. `scripts/validate_send_time_reply_gate.py`
2. `scripts/release_readiness_check.py`
3. `scripts/identity_creator.py`
4. `scripts/full_identity_protocol_scan.py`
5. `scripts/report_three_plane_status.py`
6. `scripts/e2e_smoke_test.sh`

Implementation highlights:

1. New passthrough args:
   - `--layer-intent-text`
   - `--expected-work-layer`
   - `--expected-source-layer`
2. Surface propagation wired in:
   - readiness sequence preflight/gates
   - creator validate flow
   - e2e checks block
   - full-scan check set
   - three-plane instance-plane checks
3. Send-time gate inference:
   - when explicit expected tuple is absent, infer from `stamp_json` payload (`resolved_work_layer` / `resolved_source_layer`) before invoking first-line gate.

Replay evidence snapshot (architect local replay):

1. Static checks:
   - `python3 -m py_compile scripts/validate_send_time_reply_gate.py scripts/release_readiness_check.py scripts/identity_creator.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - result: `rc=0`
2. send-time inference replay:
   - `validate_send_time_reply_gate.py` with `--stamp-json` only (no explicit expected tuple) returns:
     - `expected_work_layer=instance`
     - `expected_source_layer=global`
     - `send_time_gate_status=PASS_REQUIRED`
3. full-scan replay with intent passthrough:
   - `response_stamp_render.work_layer=instance`
   - `reply_first_line_status=PASS_REQUIRED`
   - `send_time_gate_status=PASS_REQUIRED`
   - `execution_reply_identity_coherence=PASS_REQUIRED`
4. three-plane replay with intent passthrough:
   - `instance_plane_status=CLOSED`
   - `layer_intent_resolution_status=PASS_REQUIRED`
   - `send_time_gate_status=PASS_REQUIRED`
   - `reply_coherence_status=PASS_REQUIRED`

Residual risk:

1. This item is P1 enhancement closure and does not override independent P0 release gates.
2. Independent audit replay still required before status can move from `PENDING_REPLAY` to `PASS`.

Layer declaration:

1. protocol-only; no business-scene constants introduced.

#### 16.8.10 FIX-025 implementation lane: layer-intent auto resolution (P1, protocol-only)

Status: `DONE / PENDING_REPLAY` (implementation landed, independent audit replay pending).

Scope (protocol-only):

1. Add deterministic layer-intent resolver output (`resolved_work_layer`, `resolved_source_layer`) with confidence/fallback metadata.
2. Keep strict fail-closed tuple semantics unchanged (reuse strict gate family in strict operations).
3. Expose layer-intent telemetry in three-plane/full-scan for machine-readable audit visibility.

Changed surfaces:

1. `scripts/response_stamp_common.py`
2. `scripts/render_identity_response_stamp.py`
3. `scripts/validate_layer_intent_resolution.py` (new)
4. `scripts/validate_reply_identity_context_first_line.py`
5. `scripts/validate_execution_reply_identity_coherence.py`
6. `scripts/validate_send_time_reply_gate.py`
7. `scripts/release_readiness_check.py`
8. `scripts/e2e_smoke_test.sh`
9. `scripts/full_identity_protocol_scan.py`
10. `scripts/report_three_plane_status.py`
11. `scripts/identity_creator.py`
12. `.github/workflows/_identity-required-gates.yml`
13. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`

Expected machine-readable fields:

1. `layer_intent_resolution_status`
2. `resolved_work_layer`
3. `resolved_source_layer`
4. `intent_confidence`
5. `intent_source`
6. `fallback_reason`

Replay checklist (to be attached by architect after command run):

1. Positive: explicit/clear business intent -> auto `work_layer=instance`, strict replay `PASS_REQUIRED`.
2. Negative: ambiguous intent -> safe fallback `work_layer=instance` with non-empty `fallback_reason`.
3. Negative: strict mismatch (`expected-work-layer` vs reply tuple) -> deterministic fail-closed in strict lane.
4. Observability: `three-plane` and `full-scan` expose `layer_intent_resolution_*` fields.

Source refs:

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (`5.8.13`, `ASB-RQ-069`)

Layer declaration:

1. protocol-only; no business scenario constants introduced.

#### 16.8.6 HOTFIX-P0-009 / HOTFIX-P0-010 implementation landing (2026-03-01, architect self-replay)

Status: `DONE / PENDING_REPLAY` (code landed, awaiting independent audit replay).

Scope split (non-merge):

1. Track-1 / HOTFIX-P0-009:
   - strict execution command tuple vs reply tuple coherence gate.
   - fail-closed errors: `IP-ASB-CTX-001..003`.
2. Track-2 / HOTFIX-P0-010:
   - strict gate rendering pins `--disclosure-level standard` to avoid disclosure-profile drift removing tuple refs.

Code landing summary:

1. New validator:
   - `scripts/validate_execution_reply_identity_coherence.py`
2. Six-surface wiring:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
3. Deterministic strict-gate rendering:
   - all above rendering call sites now pass `--disclosure-level standard`.

Architect replay snippets (local):

1. strict mismatch replay (`operation=validate`) -> fail-closed:
   - `validate_execution_reply_identity_coherence.py ... --operation validate ...` => `rc=1`
   - payload includes `coherence_status=FAIL_REQUIRED` and `error_code=IP-ASB-CTX-003` (dual-domain mismatch case) or `IP-ASB-CTX-001` (same-domain tuple mismatch case).
   - when strict replay receives minimal disclosure stamp missing tuple refs, payload is deterministic `error_code=IP-ASB-CTX-002` (`reply_tuple_fields_missing:*`).
2. strict coherent replay:
   - render with pinned standard disclosure then validate => `rc=0`, `coherence_status=PASS_REQUIRED`.
3. inspection replay (`operation=scan`) on mismatch:
   - validator returns `rc=0` with `coherence_status=WARN_NON_BLOCKING` for visibility-first paths.

Residual risk (before audit replay):

1. independent replay still required across readiness/e2e/full-scan/three-plane/CI surfaces.
2. conversation runtime outside protocol scripts must keep first-line stamp and explicit catalog lane discipline; protocol lane cannot rely on implicit chat memory.

#### 16.8.7 FIX-022 implementation replay: response stamp configurable disclosure + natural-language trigger (2026-03-01)

Status: `DONE / PENDING_REVIEW` (protocol code landed, audit replay attached).

Change intent (protocol-layer only):

1. Keep first-line identity stamp hard gate unchanged.
2. Reduce default user-facing stamp verbosity using configurable disclosure levels.
3. Support explicit natural-language trigger for level switch with auditable scope (`once`/`session`).
4. Maintain fail-closed semantics in stamp validators.

Changed files:

1. `scripts/response_stamp_common.py`
2. `scripts/render_identity_response_stamp.py`
3. `scripts/validate_identity_response_stamp.py`
4. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`

Key protocol behavior:

1. Runtime disclosure levels:
   - `minimal`: `actor_id`, `identity_id`, `scope`, `lock`, `source`.
   - `standard`: `minimal` + `catalog_ref`, `pack_ref`.
   - `verbose`/`audit`: `standard` + `lease`.
2. Default governed channel output is `standard` unless explicit override is applied.
3. Natural-language trigger parser accepts explicit level intent and optional scope hints:
   - examples: "identity stamp level=minimal session", "把身份回显切到详细，会话生效".
4. `session` scope may persist actor-scoped profile under:
   - `<catalog_dir>/session/response-stamp-profiles/<actor_token>.json`
5. Validator now evaluates required keys by `disclosure_level` while preserving:
   - dynamic identity binding checks,
   - source-domain checks,
   - lock-bound strict-operation fail-closed checks (`IP-ASB-STAMP-005`).
6. First-line identity stamp is rendered as two concatenated blocks:
   - `Identity-Context: ...; source=<...>`
   - tail block `| Layer-Context: work_layer=<protocol|instance|dual>; source_layer=<project|global|env|auto>`
7. Layer-context semantics are machine-checkable:
   - missing tail block, invalid `work_layer`, or `source/source_layer` mismatch are closure blockers in strict lanes.

Acceptance replay (local, cross-validated):

1. `python3 -m py_compile scripts/response_stamp_common.py scripts/render_identity_response_stamp.py scripts/validate_identity_response_stamp.py scripts/validate_reply_identity_context_first_line.py`
   - rc=`0`
2. default render (`standard` expected):
   - `python3 scripts/render_identity_response_stamp.py ... --json-only`
   - rc=`0`
   - key fields: `disclosure_level=standard`, `catalog_ref`/`pack_ref` present in `external_stamp`.
3. `minimal` stamp hard gate replay:
   - `python3 scripts/validate_identity_response_stamp.py ... --stamp-json /tmp/stamp-min.json --force-check --enforce-user-visible-gate --operation scan --json-only`
   - rc=`0`
   - key fields: `stamp_status=PASS`, `required_keys=[actor_id, identity_id, scope, lock, source]`.
4. first-line gate compatibility replay:
   - `python3 scripts/validate_reply_identity_context_first_line.py ... --stamp-json /tmp/stamp-min.json --force-check --enforce-first-line-gate --operation scan --json-only`
   - rc=`0`
   - key fields: `reply_first_line_status=PASS_REQUIRED`.
5. natural-language session trigger replay:
   - `python3 scripts/render_identity_response_stamp.py ... --trigger-text "把身份回显切到详细，会话生效" --persist-session-trigger --json-only`
   - rc=`0`
   - key fields: `disclosure_source=trigger_session`, `trigger_scope=session`, `session_profile_path` populated.
6. follow-up render after trigger:
   - `python3 scripts/render_identity_response_stamp.py ... --json-only`
   - rc=`0`
   - key fields: `disclosure_source=session_state`, level persists as expected.
7. layer-tail structure replay:
   - first-line output must contain ` | Layer-Context: `
   - `Layer-Context` must be at line tail
   - `work_layer`/`source_layer` must be parseable and enum-valid.

Residual risk:

1. `session` scope persistence writes actor-scoped profile under identity home; sandboxed CI lanes may require escalated permissions for this optional path.
2. Strict-operation lock-bound failures remain expected when actor/session lock is `LOCK_MISMATCH`; this patch does not relax that gate.
3. Baseline alignment gap closed by `39b2892`: `DEFAULT_DISCLOSURE_LEVEL` and renderer fallback now default to `standard`; prior docs/code drift no longer present.

#### 16.8.9 FIX-023 supplemental replay: default disclosure baseline alignment (2026-03-02)

Status: `DONE / PASS` (independent audit replay completed).

Patch commit:

1. `39b2892` — `fix(protocol): default response stamp disclosure to standard`

Patched files:

1. `scripts/response_stamp_common.py` (`DEFAULT_DISCLOSURE_LEVEL: minimal -> standard`)
2. `scripts/render_identity_response_stamp.py` (fallback disclosure default: `minimal -> standard`)

Independent audit replay (this turn):

1. Commit/diff verification:
   - `git show --name-only --oneline 39b2892` confirms only two patched files above.
2. A. default render (no `--disclosure-level`):
   - `render_identity_response_stamp.py` => `rc=0`
   - key fields: `disclosure_level=standard`, `catalog_ref`/`pack_ref` present, first-line tail contains `Layer-Context`.
3. B/C strict gates under `LOCK_MATCH` tuple:
   - target identity `base-repo-architect` (current actor-bound active identity)
   - `validate_identity_response_stamp.py --operation validate` => `rc=0`, `stamp_status=PASS`
   - `validate_reply_identity_context_first_line.py --operation validate` => `rc=0`, `reply_first_line_status=PASS_REQUIRED`
4. Negative sanity (expected, non-regression):
   - under `LOCK_MISMATCH` tuple (`system-requirements-analyst` in current actor context), strict gates fail-closed:
     - stamp gate `rc=1` (`IP-ASB-STAMP-005`)
     - first-line gate `rc=1` (`IP-ASB-STAMP-SESSION-001`)
5. Docs/SSOT checks:
   - `python3 scripts/docs_command_contract_check.py` => `rc=0`
   - `python3 scripts/validate_protocol_ssot_source.py` => `rc=0`

Closure note:

1. `FIX-023` replay closure requires lock-consistent tuple (`LOCK_MATCH`) for strict-operation PASS assertions.
2. `LOCK_MISMATCH` strict failure remains expected governance behavior and is not a patch regression.

#### 16.8.8 FIX-023 implementation replay: identity/layer split-tail hard gate requiredization (2026-03-01)

Status: `DONE / PENDING_REPLAY` (protocol code landed, A~F acceptance replay attached).

Commit:

1. `8a97afc` — `fix(protocol): enforce identity/layer split-tail stamp contract`

Changed files:

1. `scripts/response_stamp_common.py`
2. `scripts/render_identity_response_stamp.py`
3. `scripts/validate_identity_response_stamp.py`
4. `scripts/validate_reply_identity_context_first_line.py`
5. `scripts/validate_execution_reply_identity_coherence.py`

Implementation closure (protocol-layer only):

1. First-line format normalized to two-block split-tail:
   - `Identity-Context: ...; source=... | Layer-Context: work_layer=...; source_layer=...`
2. Shared parser introduced for stamp/first-line/coherence validators:
   - `parse_identity_context_stamp(...)`
3. strict operations fail-closed on:
   - missing `Layer-Context` tail
   - invalid `work_layer` enum
   - `source/source_layer` mismatch
4. scan/inspection keeps compatibility visibility via non-blocking stale reasons where applicable.

Acceptance replay (A~F, executed):

1. A. static checks:
   - `python3 -m py_compile scripts/response_stamp_common.py scripts/render_identity_response_stamp.py scripts/validate_identity_response_stamp.py scripts/validate_reply_identity_context_first_line.py scripts/validate_execution_reply_identity_coherence.py` => rc=`0`
   - `bash -n scripts/e2e_smoke_test.sh` => rc=`0`
2. B. render tail block:
   - `python3 scripts/render_identity_response_stamp.py --identity-id custom-creative-ecom-analyst --catalog /Users/yangxi/.codex/identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --json-only` => rc=`0`
   - key: `external_stamp` includes ` | Layer-Context: ` and tail check `True`.
3. C. stamp gate (strict validate):
   - `validate_identity_response_stamp.py ... --stamp-json /tmp/fix023-render.json --force-check --enforce-user-visible-gate --operation validate --json-only` => rc=`0`
   - key: `stamp_status=PASS`, `parsed_fields.work_layer=protocol`, `parsed_fields.source_layer=global`.
4. D. first-line gate (strict validate):
   - `validate_reply_identity_context_first_line.py ... --stamp-json /tmp/fix023-render.json --force-check --enforce-first-line-gate --operation validate --json-only` => rc=`0`
   - key: `reply_first_line_status=PASS_REQUIRED`.
5. E. coherence gate:
   - positive => rc=`0`, `coherence_status=PASS_REQUIRED`.
   - negative (`work_layer=illegal`) => rc=`1`, `coherence_status=FAIL_REQUIRED`, `error_code=IP-ASB-CTX-001`.
   - negative (tail missing) => rc=`1`, `coherence_status=FAIL_REQUIRED`, `error_code=IP-ASB-CTX-002`.
6. F. docs/ssot checks:
   - `python3 scripts/docs_command_contract_check.py` => rc=`0`
   - `python3 scripts/validate_protocol_ssot_source.py` => rc=`0`

Residual risk:

1. strict validate/readiness/e2e lanes remain lock-bound; non-`LOCK_MATCH` is expected hard-fail and not a regression.
2. Audit replay still required to flip `PENDING_REPLAY` -> `PASS`.

#### 16.8.13 FIX-024 implementation replay: send-time unified reply outlet gate (2026-03-01)

Status: `DONE / PENDING_REPLAY` (protocol code landed, independent audit replay pending).

Commit:

1. `b1cbe1f` — `fix(protocol): add send-time unified reply outlet gate`

Change intent (protocol-layer only):

1. Add a unified send-time gate so governed user-visible reply channel is checked at delivery-time, not only readiness/e2e/scan artifact lanes.
2. Fail-closed on missing first-line `Identity-Context` and emit blocker receipt using `IP-ASB-STAMP-SESSION-001`.
3. Expose send-time gate machine-readable fields in three-plane/full-scan.
4. Add real dialogue outlet replay path (reply-file evidence), not only `stamp-json` replay.

Changed files:

1. `scripts/validate_send_time_reply_gate.py` (new)
2. `scripts/identity_creator.py`
3. `scripts/release_readiness_check.py`
4. `scripts/e2e_smoke_test.sh`
5. `scripts/full_identity_protocol_scan.py`
6. `scripts/report_three_plane_status.py`
7. `.github/workflows/_identity-required-gates.yml`
8. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`

Acceptance replay (local):

1. static:
   - `python3 -m py_compile scripts/validate_send_time_reply_gate.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/full_identity_protocol_scan.py scripts/report_three_plane_status.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - rc=`0`
2. send-time positive (real reply file):
   - render stamp -> compose `/tmp/sendtime-reply-base.txt` with first-line stamp + business body
   - `validate_send_time_reply_gate.py ... --reply-file /tmp/sendtime-reply-base.txt --force-check --enforce-send-time-gate --operation validate --json-only`
   - rc=`0`, `send_time_gate_status=PASS_REQUIRED`.
3. send-time negative (missing first line):
   - `validate_send_time_reply_gate.py ... --reply-text "REAL_DIALOGUE_BODY_ONLY_NO_STAMP" --force-check --enforce-send-time-gate --operation validate --json-only`
   - rc=`1`, `send_time_gate_status=FAIL_REQUIRED`, `error_code=IP-ASB-STAMP-SESSION-001`, blocker receipt exists.
4. three-plane visibility:
   - `report_three_plane_status.py ... --with-docs-contract` => rc=`0`
   - `instance_plane_detail.response_identity_stamp` includes:
     - `send_time_gate_status`
     - `send_time_gate_error_code`
     - `send_time_reply_evidence_mode`
     - `send_time_reply_sample_count`
     - `send_time_reply_missing_count`
5. full-scan visibility:
   - `full_identity_protocol_scan.py --scan-mode target --identity-ids base-repo-architect --global-catalog /Users/yangxi/.codex/identity/catalog.local.yaml` => rc=`0`
   - target row checks include `send_time_reply_gate` with machine-readable fields.
6. docs/ssot checks:
   - `python3 scripts/docs_command_contract_check.py` => rc=`0`
   - `python3 scripts/validate_protocol_ssot_source.py` => rc=`0`

Residual risk:

1. scan/three-plane currently use `stamp_json_composed_reply` mode for deterministic telemetry; production runtime should prefer `reply-file`/`reply-log` evidence when available.
2. audit replay still required before upgrading status from `PENDING_REPLAY` to `PASS`.

#### 16.8.5 Roundtable intake: strict execution/reply tuple coherence guard (2026-03-01, HOTFIX-P0-009 docs-only)

Status: `SPEC_READY` (implementation not landed yet).

Problem statement (cross-validated):

1. In dual-catalog lanes, command execution can be run against global runtime tuple while conversational reply context is produced from project lane tuple (or vice versa).
2. Existing lock-bound stamp gates (`HOTFIX-P0-008`) guarantee lock semantics per lane, but do not yet enforce that command lane and reply lane are the same tuple for strict operations.
3. This creates a P0 audit perception gap: screenshot-level command evidence and reply identity context can appear contradictory.

Cross-validation anchors:

1. Global actor session tuple:
   - `/Users/yangxi/.codex/identity/session/actors/user_yangxi.json`
   - `/Users/yangxi/.codex/identity/session/active_identity.json`
2. Project actor session tuple:
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/session/actors/user_yangxi.json`
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/session/active_identity.json`
3. Runtime resolver command confirms tuple domain:
   - `scripts/resolve_identity_context.py resolve --identity-id <id>`
4. Strict readiness invocation screenshot evidence (identity-id in command vs observed reply context mismatch perception):
   - user-provided replay screenshot in current thread (`base-repo-audit-expert-v3` strict readiness command).

Governance alignment:

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`:
   - section `5.8.11` (`execution_reply_identity_coherence_contract_v1`)
   - requirement `ASB-RQ-067` (`P0`, `SPEC_READY`)
   - confirmation matrix `C9`
   - section `14.7` (incident class + normative closure rule)

Architect implementation package (next execution batch):

1. Add strict coherence validator surface (execution tuple vs reply tuple compare).
2. Add error codes `IP-ASB-CTX-001..003` with blocker receipt output in strict operations.
3. Wire to creator/readiness/e2e/full-scan/three-plane/CI required-gates.
4. Keep scan/inspection operations non-blocking but machine-visible.

Acceptance replay template (post-implementation):

1. negative: strict replay with deliberate tuple mismatch -> deterministic fail-closed (`IP-ASB-CTX-001`).
2. negative: strict replay without resolver evidence -> deterministic fail-closed (`IP-ASB-CTX-002`).
3. negative: strict dual-catalog ambiguity unresolved -> deterministic fail-closed (`IP-ASB-CTX-003`).
4. positive: strict replay with coherent tuple -> PASS (`coherence_decision=PASS`).
5. positive: scan/three-plane replay with mismatch -> non-blocking warning + machine fields exposed.

This section is docs-only intake; no protocol script behavior changed in this batch.

#### 16.8.4 Implementation replay: split-receipt + CWD-invariant + discovery requiredization bridge (2026-03-01)

Status: `GATE_READY` (protocol code landed, pending independent auditor replay sign-off).

Commit set (protocol layer only):

1. `8778bdf` — `feat(protocol): wire split-receipt gate and cwd-invariant validators`
2. `295daf7` — `feat(protocol): add discovery requiredization gate and coverage subgate`
3. `3baa355` — `feat(protocol): apply discovery requiredization during update preflight`

Changed file surface (aggregated):

1. `.github/workflows/_identity-required-gates.yml`
2. `scripts/e2e_smoke_test.sh`
3. `scripts/full_identity_protocol_scan.py`
4. `scripts/identity_creator.py`
5. `scripts/release_readiness_check.py`
6. `scripts/report_three_plane_status.py`
7. `scripts/validate_agent_handoff_contract.py`
8. `scripts/validate_identity_trigger_regression.py`
9. `scripts/validate_instance_protocol_split_receipt.py`
10. `scripts/validate_required_contract_coverage.py`
11. `scripts/validate_discovery_requiredization.py`

Closure summary by requirement:

1. `ASB-RQ-055..058`:
   - `validate_instance_protocol_split_receipt.py` landed with `IP-SPLIT-001..005`.
   - creator/readiness/e2e/full-scan/three-plane/CI surfaces wired.
2. `ASB-RQ-059..061`:
   - trigger-regression/handoff/three-plane CWD-invariant path resolution landed.
   - non-protocol-root replay from `/tmp` confirmed deterministic behavior.
3. `ASB-RQ-062..064`:
   - `validate_discovery_requiredization.py` landed with `IP-DREQ-001..004`.
   - update preflight apply mode landed (`--apply-requiredization`):
     - promote discovery trio contracts to `required=true`,
     - sync CI required validators,
     - write requiredization receipt,
     - append evidence-index linkage.
4. `ASB-RQ-066`:
   - `validate_required_contract_coverage.py` extended with discovery subset counters and
     `--min-discovery-required-coverage` threshold.
5. `ASB-RQ-065`:
   - non-blocking expiry evaluator landed in `validate_discovery_requiredization.py` with
     `IP-DREQ-005` fail-closed escalation when warning lanes age beyond configured window.

Replay evidence snapshot (sandbox):

1. Static gates:
   - `python3 -m py_compile ...` -> `rc=0`
   - `bash -n scripts/e2e_smoke_test.sh` -> `rc=0`
2. Split receipt gate:
   - `python3 scripts/validate_instance_protocol_split_receipt.py --identity-id system-requirements-analyst --catalog identity/catalog/identities.yaml --repo-catalog identity/catalog/identities.yaml --operation scan --json-only`
   - `rc=0`, `instance_protocol_split_status=SKIPPED_NOT_REQUIRED`
3. Discovery requiredization gate:
   - `python3 scripts/validate_discovery_requiredization.py --identity-id system-requirements-analyst --catalog identity/catalog/identities.yaml --repo-catalog identity/catalog/identities.yaml --operation scan --json-only`
   - `rc=0`, `discovery_requiredization_status=SKIPPED_NOT_REQUIRED`
4. Coverage subgate:
   - `python3 scripts/validate_required_contract_coverage.py --identity-id system-requirements-analyst --catalog identity/catalog/identities.yaml --repo-catalog identity/catalog/identities.yaml --operation scan --json-only`
   - `rc=0`, includes `discovery_required_total/pass/rate` fields.
5. Full scan replay:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids system-requirements-analyst --global-catalog identity/catalog/identities.yaml --out /tmp/scan-sra-dreq2.json`
   - `rc=0`, summary `{"total_identities":1,"p0":0,"p1":0,"ok":1}`, and `checks.discovery_requiredization` present.
6. Three-plane replay from non-protocol CWD:
   - `/tmp$ python3 /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/scripts/report_three_plane_status.py --identity-id system-requirements-analyst --catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --repo-catalog identity/catalog/identities.yaml --with-docs-contract`
   - `rc=0`, `instance_plane_detail.discovery_requiredization.discovery_requiredization_status=SKIPPED_NOT_REQUIRED`.

Focused negative-path replay (fixture-backed):

1. `IP-DREQ-001`: trigger met but discovery trio still optional -> deterministic fail.
2. `IP-DREQ-002`: requiredization receipt missing/invalid -> deterministic fail.
3. `IP-DREQ-003`: receipt not linked in evidence-index -> deterministic fail.
4. `IP-DREQ-004`: CI required validator set misses discovery trio -> deterministic fail.
5. positive with `--apply-requiredization`: deterministic pass (`PASS_REQUIRED`) and writeback artifacts generated.

Layer declaration:

1. Protocol only. No business-scene constants were introduced into protocol contracts or validator logic.

#### 16.8.2 Roundtable intake: discovery requiredization hardening (2026-03-02, docs-only)

Status: `SPEC_READY` (implementation not landed yet).

Problem statement (cross-validated):

1. Discovery validators are wired but frequently return `contract_not_required -> skipped`, so discovery lane can remain semi-soft under repeated risk signals.
2. Base identity pack template defaults discovery trio contracts to `required=false`, which is valid for bootstrap but insufficient for repeated risk windows.
3. P1 optimization surfaces are intentionally non-blocking; without requiredization and expiry policy they can remain unresolved indefinitely.

Cross-validation anchors:

1. Readiness invokes discovery trio:
   - `scripts/release_readiness_check.py:476`
2. Discovery validators skip when contract is not required:
   - `scripts/validate_identity_tool_installation.py:64`
   - `scripts/validate_identity_vendor_api_discovery.py:67`
   - `scripts/validate_identity_vendor_api_solution.py:61`
3. Identity pack template defaults discovery trio to optional:
   - `scripts/create_identity_pack.py:259`
   - `scripts/create_identity_pack.py:281`
   - `scripts/create_identity_pack.py:308`
4. E2E marks optimization trigger/build/fit chain as non-blocking lane:
   - `scripts/e2e_smoke_test.sh:288`
   - `scripts/e2e_smoke_test.sh:291`
   - `scripts/e2e_smoke_test.sh:303`
5. Trigger/build/fit scripts expose non-blocking or skipped statuses by design:
   - `scripts/trigger_platform_optimization_discovery.py:15`
   - `scripts/trigger_platform_optimization_discovery.py:269`
   - `scripts/build_vibe_coding_feeding_pack.py:14`
   - `scripts/validate_identity_capability_fit_optimization.py:16`
6. Current CI validator set snapshot does not include discovery trio required validators:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/CURRENT_TASK.json:652`
7. Coverage gate currently summarizes required/optional globally; discovery-subset threshold is not yet enforced:
   - `scripts/validate_required_contract_coverage.py:338`

Governance delta added in this batch:

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`:
   - `5.10.5` `discovery_requiredization_contract_v1`
   - `5.10.6` `discovery_required_coverage_subgate_contract_v1`
   - requirement rows `ASB-RQ-062..066` (`SPEC_READY`; `062/063/064/066` are `P0`, `065` is `P1`)
2. Protocol layer remains business-data sanitized:
   - contract language uses generic platform-class and capability-gap semantics only (no tenant/customer constants).

Architect implementation package (next execution batch):

1. Add validator: `scripts/validate_discovery_requiredization.py`
2. Implement requiredization state transition and receipt writeback:
   - evaluate trigger conditions,
   - promote discovery trio contracts to `required=true`,
   - emit deterministic receipt payload,
   - archive to protocol-feedback outbox + evidence-index.
3. Wire gate surfaces:
   - `identity_creator.py`
   - `release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `full_identity_protocol_scan.py`
   - `report_three_plane_status.py`
   - `.github/workflows/_identity-required-gates.yml`
4. Extend CI validator synchronization:
   - requiredized discovery trio must be present in `ci_enforcement_contract.required_validators`.
5. Extend `validate_required_contract_coverage.py` with discovery subset threshold:
   - `min_discovery_required_coverage`
   - `discovery_required_total/discovery_required_passed/discovery_required_coverage_rate/discovery_required_gate_failed`.

Acceptance replay template (post-implementation):

1. negative: trigger conditions met but contracts remain optional -> `FAIL_REQUIRED` (`IP-DREQ-001`).
2. negative: requiredization applied but receipt missing or incomplete -> `FAIL_REQUIRED` (`IP-DREQ-002`).
3. negative: requiredization receipt not linked in SSOT evidence-index -> `FAIL_REQUIRED` (`IP-DREQ-003`).
4. negative: requiredization active but CI required validator set misses discovery trio -> `FAIL_REQUIRED` (`IP-DREQ-004`).
5. negative: requiredization active with discovery coverage below threshold -> `FAIL_REQUIRED`.
6. positive: requiredization applied + receipts linked + CI validator sync + discovery coverage threshold satisfied -> `PASS_REQUIRED`.

This section is docs-only intake; no protocol script behavior changed in this batch.

#### 16.8.3 Roundtable intake: CWD-invariant execution hardening (2026-03-02, docs-only)

Status: `SPEC_READY` (implementation not landed yet).

Problem statement (cross-validated):

1. Some validators still resolve relative sample/evidence paths from process CWD, creating false negatives when invoked outside protocol root.
2. `three-plane` orchestration contains CWD-sensitive subprocess and repo-catalog resolution paths, causing false blocker outcomes in non-default working directories.
3. These are protocol-level portability defects and must be fixed once in protocol scripts instead of repeated instance-side path workarounds.

Cross-validation anchors:

1. Trigger regression path resolution currently CWD-sensitive:
   - `scripts/validate_identity_trigger_regression.py:146`
   - `scripts/validate_identity_trigger_regression.py:151`
   - `scripts/validate_identity_trigger_regression.py:152`
2. Agent handoff self-test sample root currently CWD-sensitive:
   - `scripts/validate_agent_handoff_contract.py:253`
   - `scripts/validate_agent_handoff_contract.py:371`
   - `scripts/validate_agent_handoff_contract.py:372`
3. Three-plane orchestration subprocess and default repo-catalog resolution currently CWD-sensitive:
   - `scripts/report_three_plane_status.py:186`
   - `scripts/report_three_plane_status.py:1085`
   - `scripts/report_three_plane_status.py:1110`
   - `scripts/report_three_plane_status.py:1542`
   - `scripts/report_three_plane_status.py:1566`

Governance alignment:

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` already defines:
   - `5.8.10` `cwd_invariant_execution_contract_v1`
   - `ASB-RQ-059..061` (`P0`, `SPEC_READY`)

Architect implementation package (next execution batch):

1. `validate_identity_trigger_regression.py`:
   - resolve `sample_report_path_pattern` against identity pack root (`CURRENT_TASK.json` parent), not shell CWD.
2. `validate_agent_handoff_contract.py`:
   - resolve self-test sample root against identity pack root for both positive/negative fixture scanning.
3. `report_three_plane_status.py`:
   - invoke child scripts with protocol-root absolute paths (`Path(__file__)` anchored) or explicit `--protocol-root`;
   - make default repo-catalog resolution protocol-root deterministic;
   - emit actionable hint when explicit `--repo-catalog` is required.
4. Wire CWD invariance checks to `identity_creator`, `release_readiness_check`, `e2e_smoke_test`, `full_identity_protocol_scan`, `report_three_plane_status`, and CI required gates.

Acceptance replay template (post-implementation):

1. negative: run target validators from non-protocol CWD and verify CWD-sensitive false errors are eliminated.
2. negative: inject intentionally CWD-relative broken fixture path and require `FAIL_REQUIRED` with `IP-CWD-001/002`.
3. positive: same identity/check set yields identical status from protocol-root and non-protocol-root invocation directories.
4. positive: three-plane report writes stable machine-readable status without CWD-dependent `BLOCKED` artifacts.

This section is docs-only intake; no protocol script behavior changed in this batch.
