# Protocol Remediation Audit Ledger (v1.6.21 Terminal Truth Cleanliness)

Status: Active (`ISSUE-039` was protocol-side closed on 2026-03-25 after clean terminal truth / negative-feedback veto / canonical publishability semantics were promoted to one shared machine-law lane)
Layer: protocol
Scope: audit evidence for the additive stream that freezes clean terminal truth as distinct from execution closure while preserving inherited lower-layer execution-closure legality.
Execution mode: canonical review ledger for the v1.6.21 terminal-truth-cleanliness stream.

## 0) Current control-plane alias refs

- `identity/protocol/mappings/contract-binding.current.yaml`
- `identity/protocol/mappings/control-plane-status.current.yaml`
- `identity/protocol/mappings/semantic-term-registry.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/stream-scope-matrix.current.yaml`
- `identity/protocol/mappings/workbook-registry.current.yaml`
- `docs/workbook/protocol-issue-register-v1.6.md`
- `docs/workbook/protocol-deep-audit-workbook-v1.6.md`

## 1) Audit conclusion

The office-ops feedback direction was correct, but it required one important protocol correction:

1. the stream must **not** say `review_required => execution closure invalid`;
2. it must instead say:
   - execution closure truth may remain legal,
   - clean terminal truth may still be vetoed,
   - canonical publishability may still be vetoed.

That corrected semantic split is now landed.

## 2) Existing lower-layer evidence rechecked

The following lower-layer execution semantics remain valid and explicitly preserved:

1. `scripts/validate_post_execution_mandatory.py`
   - still permits strict non-upgrade closure and strict upgrade closure on their inherited terms;
2. `scripts/validate_writeback_continuity.py`
   - still governs `STRICT_WRITEBACK` versus `DEGRADED_WRITEBACK` and the required degraded fields;
3. existing governance/review anchors in `v1.5.0` / `v1.6.0`
   - still preserve the legal review-required execution branch.

Therefore the missing protocol law was never “execution closure semantics absent”. The missing law was “clean terminal truth / canonical publishability remained under-specified at the higher layer”.

## 3) Landed remediation

### 3.1 Shared helper landed

`scripts/terminal_truth_cleanliness_common.py` now freezes one shared derivation family for:

- execution-closure basis,
- dirty-signal collection,
- negative-feedback class,
- veto scope,
- loopback / review pending next state,
- clean terminal truth,
- canonical publishability,
- instance adoption projection drift.

### 3.2 Shared validator landed

`scripts/validate_terminal_truth_cleanliness.py` now emits the canonical machine payload:

- `identity_terminal_truth_cleanliness_status`
- `execution_closure_status`
- `terminal_truth_cleanliness_status`
- `terminal_truth_class`
- `terminal_state_machine_status`
- `terminal_state_class`
- `terminal_state_conflict_status`
- `terminal_clean_alias_surface_status`
- `negative_feedback_terminal_veto_status`
- `canonical_publishable_result_status`
- `instance_adoption_terminal_truth_probe_status`

### 3.3 Shared probe landed

`bash scripts/ci/run_terminal_truth_cleanliness_probes_ci.sh` now proves six bounded cases:

1. positive clean case;
2. negative review-required case that preserves execution closure while vetoing clean truth;
3. negative degraded case that requires revalidation;
4. negative placeholder case that requires repair-before-publish;
5. negative adoption-mismatch case that fail-closes terminal-state projection drift;
6. negative clean-alias-drift case that fail-closes generic `completed` / `done` alias reuse while the higher-order lane remains non-clean.

### 3.4 Shared producer/adoption wiring landed

The stream is no longer docs-only because:

1. `scripts/create_identity_pack.py` now auto-wires the contract;
2. `scripts/repair_contract_backfill.py` backfills the contract and projects the shared fields onto the active execution report for adopted packs;
3. `scripts/execute_identity_upgrade.py` now writes the same projection family onto fresh reports;
4. required-gate / readiness / CI coverage now includes the validator and probe lane.

## 4) Direct runtime audit fact

Direct runtime replay on the workspace-local `base-repo-audit-expert-v3` current execution report now produces the correct higher-order result:

- the active report is still pre-mutation-gate blocked;
- therefore `identity_terminal_truth_cleanliness_status` must fail;
- the report is non-clean and non-publishable;
- the degraded loopback projection itself remains coherent (`negative_feedback_terminal_veto_status=PASS_REQUIRED`) even though execution closure is not yet reached;
- the same payload can now separately expose `terminal_state_machine_status=PASS_REQUIRED` when the report is correctly classified as a non-clean pending state rather than an ambiguous pseudo-terminal result;
- generic clean-completion alias surfaces are now also checked on the same adoption lane, so `status=completed` / `done=true` can no longer silently reoccupy clean-terminal semantics once the higher-order lane stays red;
- this is now a machine-visible outcome rather than a narrative judgment.

This is the expected proof that dirty runtime state can no longer silently occupy clean terminal truth semantics.

## 5) Machine-law landing target: ASB16-RQ-056 (2026-03-25)

The machine-law intake row is now:

- `ASB16-RQ-056`
- `rq_056_identity_terminal_truth_cleanliness_contract_v1`

Current evidence set:

1. `scripts/terminal_truth_cleanliness_common.py`
2. `scripts/validate_terminal_truth_cleanliness.py`
3. `scripts/ci/run_terminal_truth_cleanliness_probes_ci.sh`
4. `scripts/create_identity_pack.py`
5. `scripts/repair_contract_backfill.py`
6. `scripts/execute_identity_upgrade.py`
7. `scripts/required_gate_bundle_runner.py`
8. `scripts/validate_required_contract_coverage.py`
9. `scripts/ci/run_required_runtime_gates_ci.sh`

## 6) Final audit judgment

`v1.6.21` is now protocol-side closed because the previously missing law is landed:

1. execution closure truth remains preserved,
2. clean terminal truth is now independently machine-judged,
3. canonical publishability now requires clean terminal truth,
4. negative feedback now has explicit veto semantics,
5. dirty terminal states now fail-close instead of ambiguously surviving as “done enough”;
6. non-clean states are now machine-distinguished through explicit terminal-state equivalence classes rather than inferred only from narrative review;
7. generic completed/done alias surfaces are now subordinated to the same higher-order machine law instead of remaining an ungoverned escape hatch.

That is the correct 1.6.x outcome: the current universe now has one more root-closed / machine-closed boundary, and 1.7.x does not need to inherit this debt.
