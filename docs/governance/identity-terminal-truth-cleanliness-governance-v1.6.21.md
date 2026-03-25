# Identity Terminal Truth Cleanliness Governance (v1.6.21)

Status: Active (`ISSUE-039` closure conditions were satisfied on 2026-03-25 because clean terminal truth / canonical publishability / negative-feedback veto semantics are now protocol-owned machine law; dirty execution reports may still exist, but they now fail-close instead of occupying clean terminal truth)
Layer: protocol
Scope: additive strengthening that freezes the distinction between execution closure truth and clean terminal truth / canonical publishability, while promoting governed negative feedback from advisory metadata to machine-consumed veto semantics over clean terminal truth.
Execution mode: topic-level canonical SSOT for v1.6.21 terminal-truth-cleanliness governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_terminal_truth_cleanliness`.
2. `v1.6.21` does **not** reopen the already-frozen execution-closure semantics owned by:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
   - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
   - `scripts/validate_post_execution_mandatory.py`
   - `scripts/validate_writeback_continuity.py`
3. The stream exists because those lower-layer contracts correctly permit a legal review-required execution-closure branch, yet the protocol still needed one higher-order machine contract to decide whether a closed execution may occupy **clean terminal truth** or **canonical publishable result** semantics.
4. Therefore `review_required=true` / `next_action=review_required_*` must **not** be misread as “execution closure invalid”; it must be read as “execution closure may be legal while clean terminal truth and canonical publishability are vetoed”.
5. `v1.6.21` is additive strengthening only:
   - no pack-local workaround,
   - no validator loosening,
   - no hardcoded identity exception,
   - no reopening of `v1.6.17`, `v1.6.18`, `v1.6.19`, or `v1.6.20`.
6. Current-state judgment for this stream must anchor to:
   - `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/workbook-registry.current.yaml`
   - `docs/workbook/protocol-issue-register-v1.6.md`
   - `docs/workbook/protocol-deep-audit-workbook-v1.6.md`

## 1) Why v1.6.21 is required

The root philosophy already freezes a truth lifecycle:

1. truth exists,
2. truth is discoverable,
3. truth is admissible,
4. truth is bound,
5. truth is consumed.

But the protocol still needed one more explicit machine boundary:

> execution closure truth is not identical to clean terminal truth, and clean terminal truth is not identical to canonical publishability.

Without that higher-order distinction, a generic dirty result can still masquerade as a clean terminal result whenever the system only asks whether the execution finished, wrote back, or produced an artifact.

The core failure family is therefore not “execution cannot close”. It is:

- execution can close;
- writeback can succeed;
- next action can still be `review_required_*`, `rerun_*`, degraded, or repair-pending;
- yet a later consumer may still misread that state as `completed_clean` / publish-ready / final truth.

`v1.6.21` exists to hard-freeze that boundary.

## 2) Frozen semantic split

### 2.1 Execution closure remains a lower-layer truth

The stream preserves these lower-layer truths:

1. `strict_non_upgrade_closed`
   - `upgrade_required=false`
   - `all_ok=true`
   - `writeback_mode=STRICT_WRITEBACK`
   - `writeback_status in {WRITTEN, NOT_REQUIRED}`
2. `strict_upgrade_closed`
   - `upgrade_required=true`
   - `all_ok=true`
   - `writeback_status=WRITTEN`
3. A review-required execution path may therefore remain a **legal execution closure** when the inherited writeback / post-execution contracts say so.

### 2.2 Clean terminal truth is a higher-layer truth

A result may occupy `clean_terminal_truth` only when all of the following hold together:

1. execution closure is already legal,
2. no governed dirty signal remains active,
3. no negative feedback veto is active,
4. canonical publishability remains admissible.

### 2.3 Canonical publishability is stricter than execution closure

A result may be canonical/publishable only when it already satisfies clean terminal truth. Therefore:

- legal execution closure does not imply canonical publishability,
- review-required closure does not imply canonical publishability,
- degraded closure does not imply canonical publishability.

## 3) Frozen contract family

### 3.1 `terminal_truth_cleanliness_contract_v1`

Required machine projections:

- `identity_terminal_truth_cleanliness_status`
- `terminal_truth_contract_status`
- `terminal_state_machine_status`
- `terminal_state_class`
- `terminal_state_basis`
- `terminal_state_conflict_status`
- `requires_review`
- `retry_required`
- `revalidation_required`
- `repair_required`
- `quarantine_required`
- `requires_human`
- `terminal_failure`
- `state_transition_required`
- `state_machine_blockers`
- `execution_closure_status`
- `terminal_truth_cleanliness_status`
- `terminal_truth_class`
- `is_terminal_clean`
- `is_terminal_dirty`
- `terminal_truth_basis`
- `terminal_truth_blockers`

Hard semantics:

1. execution closure truth and terminal-truth cleanliness must stay distinct in payloads;
2. clean terminal truth requires a clean execution closure **plus** veto-free publishability;
3. dirty execution may still be execution-closed, but it must not be represented as clean terminal truth.
4. the same shared lane must also emit an explicit terminal-state equivalence projection so later consumers can distinguish `completed_clean`, `review_pending`, `revalidation_pending`, `repair_pending`, `retry_pending`, `quarantined`, `failed_terminal`, and `non_terminal_pending` rather than collapsing all non-clean states into one ambiguous bucket.

### 3.2 `negative_feedback_terminal_veto_contract_v1`

Required machine projections:

- `negative_feedback_terminal_veto_status`
- `negative_feedback_class`
- `feedback_severity`
- `terminal_veto_required`
- `terminal_veto_scope`
- `loopback_required`
- `loopback_target_stage`
- `loopback_reason`
- `pre_terminal_veto_applied`
- `next_state_after_veto`

Hard semantics:

1. negative feedback may veto **clean terminal truth** and **canonical publishability** without retroactively invalidating the lower execution-closure truth;
2. review-required negative feedback freezes `next_state_after_veto=review_pending` rather than falsely claiming clean closure;
3. degraded / contradiction / confidence / placeholder families freeze governed revalidation or repair paths rather than allowing silent clean-terminal promotion.

### 3.3 `canonical_publishable_result_gate_contract_v1`

Required machine projections:

- `canonical_publishable_result_status`
- `publishable`
- `publish_blockers`
- `canonical_result_eligible`
- `canonical_result_basis`
- `requires_repair_before_publish`

Hard semantics:

1. canonical publishability requires clean terminal truth;
2. dirty terminal states, review-required closures, degraded closures, placeholder outputs, unresolved contradictions, and confidence-below-floor states must stay non-publishable.

### 3.4 `instance_adoption_terminal_truth_probe_contract_v1`

Required machine projection:

- `instance_adoption_terminal_truth_probe_status`

Hard semantics:

1. instance/runtime report projections must not claim `is_terminal_clean=true`, `publishable=true`, or `canonical_result_eligible=true` while governed dirty signals remain active;
2. the protocol must detect adoption drift as machine inconsistency rather than relying on narrative review.

## 4) Dirty-signal law frozen by this stream

The shared helper now freezes the following dirty-signal families as protocol-owned machine inputs:

1. `review_required_next_action`
2. `degraded_writeback_mode`
3. `writeback_status=DEFERRED_*`
4. `all_ok=false`
5. `next_recovery_action_present`
6. `degrade_reason_present`
7. `prompt_change_pending`
8. `placeholder_result_present`
9. `unresolved_contradiction`
10. `confidence_below_floor`

Interpretation rule:

- dirty signal != execution closure invalid by default;
- dirty signal => clean terminal truth veto + canonical publishability veto.

## 5) Shared implementation boundary

`v1.6.21` is now landed as shared infrastructure through:

1. `scripts/terminal_truth_cleanliness_common.py`
   - shared contract skeleton,
   - shared dirty-signal classification,
   - shared negative-feedback veto projection,
   - shared clean-terminal / publishability derivation;
2. `scripts/validate_terminal_truth_cleanliness.py`
   - canonical machine validator,
   - including explicit terminal-state equivalence projection and fail-close state-coherence checks;
3. `scripts/ci/run_terminal_truth_cleanliness_probes_ci.sh`
   - positive clean fixture,
   - negative review-required fixture,
   - negative degraded fixture,
   - negative placeholder/repair fixture,
   - negative adoption-mismatch fixture;
4. `scripts/create_identity_pack.py`
   - auto-wires the contract for new packs;
5. `scripts/repair_contract_backfill.py`
   - backfills the contract for adopted packs and projects the shared fields onto the active execution report;
6. `scripts/execute_identity_upgrade.py`
   - emits the same projection family onto fresh execution reports;
7. `scripts/required_gate_bundle_runner.py`, `scripts/validate_required_contract_coverage.py`, and `scripts/ci/run_required_runtime_gates_ci.sh`
   - now consume the new validator lane as protocol-owned machine infrastructure.

## 6) Machine-law landing target: ASB16-RQ-056 (2026-03-25)

The machine-law intake for this stream is now:

- `ASB16-RQ-056`
- `rq_056_identity_terminal_truth_cleanliness_contract_v1`

Required stop condition:

1. one shared contract/validator/probe family exists;
2. create/backfill/fresh-run producer lanes all emit the same projection family;
3. clean fixture proof passes;
4. dirty runtime reports fail-close as non-clean / non-publishable rather than occupying clean terminal truth;
5. review-required execution closure remains legal at the lower layer while still vetoed from clean-terminal / canonical-publishable semantics.

Current landed evidence:

1. `bash scripts/ci/run_terminal_truth_cleanliness_probes_ci.sh` now passes;
2. `scripts/validate_terminal_truth_cleanliness.py` now preserves:
   - clean fixture -> `identity_terminal_truth_cleanliness_status=PASS_REQUIRED`, `terminal_state_machine_status=PASS_REQUIRED`, `terminal_state_class=completed_clean`
   - review-required fixture -> `execution_closure_status=PASS_REQUIRED`, `terminal_truth_class=review_required_execution_closure`, `publishable=false`, `terminal_state_class=review_pending`
   - degraded fixture -> `execution_closure_status=FAIL_REQUIRED`, `negative_feedback_terminal_veto_status=PASS_REQUIRED`, `terminal_veto_required=false`, `loopback_required=true`, `next_state_after_veto=revalidation_pending`, `terminal_state_class=revalidation_pending`
   - placeholder fixture -> `negative_feedback_class=placeholder_result`, `terminal_state_machine_status=PASS_REQUIRED`, `terminal_state_class=repair_pending`
   - adoption-mismatch fixture -> `terminal_state_machine_status=FAIL_REQUIRED` with explicit `state_machine_blockers` projection mismatch evidence
3. direct runtime replay on `base-repo-audit-expert-v3` against its latest workspace-local execution report now fail-closes as non-clean terminal truth because the active report remains pre-mutation-gate blocked (`all_ok=false`, `writeback_status=MISSING`, `next_action=satisfy_pre_mutation_gate_and_rerun_update`). The higher-order validator now keeps the degraded loopback projection coherent (`negative_feedback_terminal_veto_status=PASS_REQUIRED`) while still refusing to promote the report into clean terminal truth, while separately projecting `terminal_state_machine_status=PASS_REQUIRED` when the non-clean state itself is coherent.

## 7) Closure addendum (authoritative current-state judgment)

The authoritative judgment for `v1.6.21` is now:

1. the protocol no longer lacks a machine-owned distinction between execution closure and clean terminal truth;
2. negative feedback now has explicit veto semantics over clean terminal truth and canonical publishability;
3. review-required execution closure is preserved as legal execution closure while remaining non-clean / non-publishable;
4. dirty reports now fail-close on a shared validator lane instead of depending on pack-local interpretation;
5. the lane now also projects explicit terminal-state equivalence semantics so non-clean states remain machine-distinct rather than narratively inferred;
6. the stream is protocol-side closed because the missing shared law is landed.

This does **not** mean every runtime identity is currently clean. It means the protocol no longer permits dirty terminal states to masquerade as clean terminal truth.
