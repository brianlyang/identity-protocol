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
| FIX-003 | 2026-02-28 | protocol | readiness preflight wiring for pack path gate | `b80521e` | DONE | PENDING_REVIEW |

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
| FIX-003 | PENDING | - | - | - |

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
