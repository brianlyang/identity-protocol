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

Alignment note (2026-02-28, anti-drift):

1. `zero_shot` / `one_shot` / `multi_shot` are protocol-kernel policies, not vendor-only policies.
2. Protocol-layer vendor vs business-layer partner semantic disambiguation is mandatory governance scope for v1.5.
3. Related governance source refs:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` section `5.5.6`
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` section `5.7.2A`
   - requirement id `ASB-RQ-037`

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
