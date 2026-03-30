# Identity Instance Protocol Delta Adoption Governance v1.6.x

Minimal governance skeleton for instance_protocol_delta_adoption_contract_v1.

Instance protocol delta adoption must be machine-visible, writable, and reviewable.
Protocol authority must resolve to a single authoritative protocol root before adoption can pass.
Current protocol head, last seen protocol commit, and last adopted protocol commit must remain distinct.
Only relevant capability families are scanned for delta adoption.
Relevant protocol deltas must fail-close when authoritative protocol owner surfaces are not ready.
Relevant protocol deltas must fail-close when instance-local adoption markers are missing.
protocol_delta_adoption and instance_script_protocol_adoption must remain distinct.

Required machine-visible instance protocol delta adoption fields:
- protocol_current_head
- last_seen_protocol_commit
- last_adopted_protocol_commit
- relevant_unadopted_commit_count
- relevant_unadopted_commits
- protocol_delta_adoption_status
- protocol_delta_adoption_mode
- capability_families
- protocol_root
- state_path
- stale_reasons

Required status values:
- PASS_REQUIRED
- FAIL_REQUIRED

Required mode values:
- continuous_protocol_delta_adoption_ready
- relevant_protocol_delta_pending_adoption
- protocol_owner_surface_not_ready
- instance_local_adoption_markers_missing
- protocol_authority_resolution_failed

```json
{
  "lane_id": "instance_protocol_delta_adoption_contract_v1",
  "governing_law": "relevant_protocol_delta_adoption_requires_protocol_and_local_readiness",
  "fixed_write_set": [
    "docs/governance/identity-instance-protocol-delta-adoption-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-instance-protocol-delta-adoption.md",
    "scripts/instance_protocol_delta_adoption_contract_common.py",
    "scripts/validate_instance_protocol_delta_adoption.py",
    "scripts/ci/run_instance_protocol_delta_adoption_probes_ci.sh"
  ],
  "layer_state": "protocol-instance-bridge",
  "next_exact_action": [
    "formalize instance protocol delta adoption only",
    "freeze authoritative protocol head, last seen head, and last adopted head as separate machine-visible states",
    "fail-close relevant protocol deltas when protocol owner surfaces or instance-local adoption markers are not ready"
  ],
  "validation_bundle": [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_instance_protocol_delta_adoption.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_instance_protocol_delta_adoption_probes_ci.sh"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for instance_protocol_delta_adoption_contract_v1 only"
}
```
