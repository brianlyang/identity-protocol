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

## 1) Rolling summary

| Fix ID | Date (UTC) | Layer | Scope | Commit | Architect Status | Audit Status |
| --- | --- | --- | --- | --- | --- | --- |
| FIX-001 | 2026-02-28 | protocol | wave outdated classification | `ee01d56` | DONE | PASS |
| FIX-002 | 2026-02-28 | protocol | path-governance pack canonical gate | `0add536` | DONE | PASS |
| FIX-003 | 2026-02-28 | protocol | readiness preflight wiring for pack path gate | `b80521e` | DONE | PASS |
| FIX-004 | 2026-02-28 | protocol | dynamic response identity stamp closure (non-hardcoded + fail-closed) | `f1587e9` | DONE | PASS |
| FIX-005 | 2026-02-28 | protocol | execution-report path contract gate + readiness wiring | `8963b0e` | DONE | PASS |
| FIX-006 | 2026-02-28 | protocol | identity_home/catalog alignment gate + chain wiring | `40ff2e9` | DONE | PENDING_REVIEW |

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
| FIX-006 | PENDING_REVIEW | audit-expert(codex) | 2026-02-28T13:28:00Z | FIX-006 implementation landed in `40ff2e9`; waiting replay on IP-PATH-003 validator + multi-surface gate wiring. |

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

1. Submit FIX-006 to audit expert for replay verdict.
2. Continue FIX-007: implement `validate_fixture_runtime_boundary.py` and wire to all mandatory surfaces.
