# Sandbox Blocking Writeback Remediation Requirements (v1.4.12)

Date: 2026-02-24  
Type: P0 remediation requirements (implementation-mandatory)  
Status: Proposal-Ready for architecture PR  
Owner: Base-repo architect + audit expert

---

## 1. Problem statement (P0)

Runtime identity instances are frequently stored outside the current execution sandbox writable roots.  
When `identity_creator update` or `execute_identity_upgrade.py` appends `RULEBOOK.jsonl` / `TASK_HISTORY.md`, writeback can be blocked by permission or sandbox constraints.

Impact:

1. Self-driven upgrade appears to run but fails to persist experience.
2. Identity learning loop breaks (`run happened` but `knowledge not committed`).
3. Multi-agent governance becomes non-deterministic because replay evidence is incomplete.

This is a release-blocking class issue for identity governance.

---

## 2. Goals and non-goals

### 2.1 Goals (must)

1. No silent writeback loss under sandbox/permission restrictions.
2. Every blocked writeback must produce auditable deferred evidence.
3. Recovery path must be deterministic and validator-enforced.
4. Release gates must fail when required writeback is not fully committed.

### 2.2 Non-goals

1. This document does not redesign identity protocol semantics.
2. This document does not remove sandbox security boundaries.
3. This document does not allow bypassing writeback requirements in release plane.

---

## 3. Current baseline and gap

### 3.1 Baseline already present

Current implementation already supports:

1. Deferred evidence on writeback blocked:
   - `writeback_status=DEFERRED_PERMISSION_BLOCKED`
   - `*-writeback-deferred.json`
2. Apply helper for deferred writeback:
   - `scripts/apply_deferred_identity_writeback.py`
3. Default hard-fail behavior when required writeback is not committed.

### 3.2 Remaining gaps (must close)

1. Apply helper path trust:
   - must not blindly trust arbitrary deferred file paths.
2. CI/release plane control:
   - must forbid permissive bypass (`--allow-deferred-writeback`) in required gates.
3. Path contract consistency:
   - evidence path matching must resolve against active identity instance root (`IDENTITY_HOME`), not stale repo-relative assumptions.

---

## 4. Required architecture contract

## 4.1 Two-root model (mandatory)

1. `IDENTITY_SOURCE_HOME`:
   - durable identity state (long-term source of truth).
2. `IDENTITY_RUNTIME_HOME`:
   - sandbox-writable runtime workspace used for execution.
3. `IDENTITY_HOME`:
   - execution-time pointer, defaults to `IDENTITY_RUNTIME_HOME`.

Policy:

1. Runtime writes occur in runtime home.
2. Promotion/commit to source home is explicit and validated.
3. Missing promotion evidence for required writeback is fail.

## 4.2 Writeback states (normative)

Allowed states:

1. `WRITTEN`: required writeback fully committed.
2. `DEFERRED_PERMISSION_BLOCKED`: blocked by sandbox/permission, deferred artifact emitted.
3. `MISSING`: required writeback absent or inconsistent.

Release rule:

1. For `upgrade_required=true && all_ok=true`, release gate accepts only `WRITTEN`.

---

## 5. Implementation requirements (scripts)

## 5.1 `scripts/execute_identity_upgrade.py` (mandatory)

1. Keep deferred emission behavior for permission/sandbox errors.
2. Keep default hard-fail for required writeback not committed.
3. Include in report:
   - `writeback_status`
   - `deferred_report_path`
   - `writeback_paths`
   - `writeback_rule_id`

## 5.2 `scripts/apply_deferred_identity_writeback.py` (mandatory hardening)

Must add:

1. `--catalog` and `--identity-id` parameters (required for non-dry run).
2. Resolve legal identity pack root from catalog.
3. Validate deferred target paths are under resolved pack root.
4. Reject cross-identity or out-of-root path writes.
5. Emit applied evidence with:
   - `source_deferred_report`
   - `identity_id`
   - `applied_at`
   - `path_validation=passed`

## 5.3 Validators (mandatory)

1. `scripts/validate_identity_experience_writeback.py`
   - must treat `DEFERRED_PERMISSION_BLOCKED` as non-pass unless a matching applied report exists.
2. New validator: `scripts/validate_identity_deferred_writeback_integrity.py`
   - validates deferred/applied chain integrity and identity-scoped paths.

---

## 6. CI and release gate wiring (mandatory)

Required gate integration:

1. `scripts/release_readiness_check.py`
2. `scripts/e2e_smoke_test.sh`
3. `.github/workflows/_identity-required-gates.yml`

Rules:

1. Required checks must fail if `writeback_status != WRITTEN` for required-upgrade runs.
2. CI must not allow `--allow-deferred-writeback` in release path.
3. Deferred runs may pass only in explicit local rescue mode and must be marked non-release.

---

## 7. Acceptance tests (must pass)

## 7.1 Permission-block simulation

1. Run update with write path intentionally non-writable.
2. Expect:
   - deferred artifact emitted
   - status `DEFERRED_PERMISSION_BLOCKED`
   - command exits non-zero by default.

## 7.2 Recovery apply

1. Restore writable path.
2. Run apply helper on deferred report.
3. Expect:
   - `*-applied.json` emitted
   - RULEBOOK/TASK_HISTORY appended with matching run id.

## 7.3 Integrity and scope checks

1. Modify deferred path to foreign identity root.
2. Run apply helper.
3. Expect hard fail with explicit scope violation.

## 7.4 Release-plane enforcement

1. Trigger upgrade-required run with deferred status.
2. Run readiness/e2e/required-gates.
3. Expect fail until applied evidence closes chain.

---

## 8. Rollout plan

1. Phase 1 (code hardening):
   - apply helper path validation + integrity validator.
2. Phase 2 (gate convergence):
   - release/e2e/workflow strict enforcement.
3. Phase 3 (migration):
   - re-validate existing deferred records and backfill applied evidence.
4. Phase 4 (release):
   - upgrade status from `Conditional Go` to `Full Go` only after cloud required checks are green.

---

## 9. Decision log template (for PR)

Use this template in PR description:

1. What sandbox block scenario was reproduced?
2. Which deferred artifact was generated (path + run id)?
3. Which applied artifact closed the chain?
4. Which validators/gates proved closure?
5. Why this change does not weaken existing role-binding/local-persistence constraints?

---

## 10. Source references

1. OpenAI Codex multi-agent approvals/sandbox:
   - https://developers.openai.com/codex/multi-agent/
2. MCP latest spec:
   - https://modelcontextprotocol.io/specification/latest
3. Repository governance baselines:
   - `docs/governance/local-instance-persistence-boundary-v1.4.6.md`
   - `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md`
   - `README.md` (writeback behavior under sandbox/permission constraints)
