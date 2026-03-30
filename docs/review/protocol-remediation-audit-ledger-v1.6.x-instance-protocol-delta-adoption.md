# Protocol Remediation Audit Ledger v1.6.x — Instance Protocol Delta Adoption

## ISSUE-044 absorb receipt

- lane_id: `instance_protocol_delta_adoption_contract_v1`
- issue_id: `ISSUE-044`
- absorbed_law_id: `scope_locked_mutation_phase_runtime_enforcement_contract_v1`
- absorbed_protocol_delta_commit: `f616889`
- closure_shape: `consumer-facing adoption surface must recognize the runtime guard law as a relevant adopted protocol delta`
- boundary: `absorb only; runtime-enforcement semantics remain root-infra owned`

### audit assertions

1. The relevant protocol delta set includes
   `scope_locked_mutation_phase_runtime_enforcement_contract_v1`.
2. The adopted protocol delta set includes
   `scope_locked_mutation_phase_runtime_enforcement_contract_v1` when adoption
   state is written as current.
3. Validator output fails closed when the runtime guard law is not adopted into
   the consumer-facing instance adoption surface.
4. Probe coverage includes a negative case that removes the absorbed law from
   the adopted protocol delta set and expects fail-close.

### expected validator / probe

- validator: `TMPDIR=$PWD/.tmp python3 scripts/validate_instance_protocol_delta_adoption.py --json-only`
- probe: `TMPDIR=$PWD/.tmp bash scripts/ci/run_instance_protocol_delta_adoption_probes_ci.sh`
