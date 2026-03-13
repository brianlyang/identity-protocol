# Protocol Remediation Audit Ledger (v1.6.7 cross-layer runtime uniqueness stream)

Status: Active  
Scope: protocol-only review ledger for runtime `identity_id` uniqueness across project/global catalogs.

## 0) Stream objective

1. Prevent ambiguous runtime ownership where the same `identity_id` is active in both project and global catalogs.
2. Make duplicate ownership a machine fail-close condition, not a manual convention.
3. Keep v1.6.6 wrapper-channel closure intact while adding source arbitration closure.

## 1) Files landed in this checkpoint

1. `scripts/validate_identity_scope_isolation.py`
   - now includes cross-layer active runtime duplicate detection.
2. `scripts/repair_identity_cross_layer_uniqueness.py`
   - new repair tool for deterministic duplicate deactivation workflow.
3. `scripts/identity_creator.py`
   - `activate` and `update` preflight now hard-check uniqueness via scope isolation validator.
4. `docs/governance/identity-cross-layer-runtime-uniqueness-governance-v1.6.7.md`
5. `docs/review/protocol-remediation-audit-ledger-v1.6.7.md`

## 2) Replay summary (local serial verification)

### 2.1 Duplicate detection proof

Command:

1. `python3 scripts/validate_identity_scope_isolation.py --catalog <project_catalog> --repo-catalog <repo_catalog> --identity-id base-repo-architect`

Observed:

1. returned `rc=1`
2. error text indicates cross-layer active runtime duplicate and prints both catalog/pack paths.

### 2.2 Migration override path proof

Command:

1. `python3 scripts/validate_identity_scope_isolation.py ... --allow-cross-layer-runtime-duplicate`

Observed:

1. returned `rc=0` (explicit migration-only bypass path).

### 2.3 Non-runtime fixture compatibility proof

Command:

1. `python3 scripts/validate_identity_scope_isolation.py --catalog <project_catalog> --repo-catalog <repo_catalog> --identity-id store-manager`

Observed:

1. returned `rc=0` for fixture/demo identity row.

### 2.4 Build safety proof

Command:

1. `python3 -m py_compile scripts/validate_identity_scope_isolation.py scripts/repair_identity_cross_layer_uniqueness.py scripts/identity_creator.py`

Observed:

1. compile chain passes.

## 3) Closure interpretation

1. v1.6.7 now blocks “same runtime identity active in two layers” at machine gate level.
2. activate/update control surface is now protected by this rule.
3. full remediation still requires executing repair flow on already-duplicated identities.

## 4) Current posture

1. Policy: `PASS`
2. Implementation: `CONDITIONAL_PASS`
3. Remaining condition:
   - existing duplicated runtime identity rows must be converged to single-layer active ownership.

## 5) Stream continuity alias pointers

1. `identity/protocol/mappings/contract-binding.current.yaml`
2. `identity/protocol/mappings/control-plane-status.current.yaml`
3. `identity/protocol/mappings/control-plane-invariants.current.yaml`
4. `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
5. `identity/protocol/mappings/stream-doc-registry.current.yaml`

## 6) Follow-up from instance feedback batch (2026-03-13)

This section records cross-check against three additional protocol-side suggestions from runtime identities.

1. Host unique channel self-repair (`session_chain_wrapper_path` missing):
   - already covered by protocol tooling (`create_identity_pack.py` materialization + `repair_contract_backfill.py` normalization/backfill).
   - decision: no new stream needed; keep as enforced behavior under current v1.6.6/v1.6.7 toolchain.
2. Update output machine-readable explanation when `all_ok=false` with no failed validator rows:
   - addressed by adding explicit explanation fields in `scripts/execute_identity_upgrade.py`:
     - `check_total_count`, `failed_check_count`, `failed_check_ids`
     - `all_ok_false_reason_code`, `all_ok_false_reason`, `all_ok_false_reason_sources`
   - intent: remove ambiguity between “validator failure” and “non-closure reasons (writeback/manual review/prompt pending)”.
3. Validate freshness pre-hint:
   - addressed by `scripts/validate_execution_report_freshness.py` + propagation in
     `scripts/validate_identity_protocol_version_alignment.py`.
   - new machine-readable fields:
     - `next_action`, `hint`
   - if key inputs are newer than report, guidance now explicitly points to “update first, then validate”.
