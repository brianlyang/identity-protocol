# Protocol Remediation Audit Ledger v1.6.x — Child Runtime Owner Binding

Minimal audit ledger skeleton for ISSUE-041B child runtime owner binding admission.

Child tmp, probe, and runtime roots require admitted owner binding before admission.
Unowned child tmp, probe, and runtime roots are not admitted.
Child runtime owner binding status, owner, root scope, root kinds, and live runtime exclusion status are required admission fields.
Admission must fail-close whenever child owner binding is missing.
Live runtime exclusion must remain machine-visible wherever child residue admission is evaluated.

Required machine-visible owner binding fields:
- child_runtime_owner_binding_status
- child_runtime_owner
- child_runtime_root_scope
- child_runtime_root_kinds
- live_runtime_exclusion_status

```json
{
  "lane_id": "issue_041b_child_runtime_owner_binding_admission_contract_v1",
  "governing_law": "unowned_child_tmp_probe_runtime_not_admitted",
  "fixed_write_set": [
    "docs/governance/identity-child-runtime-owner-binding-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-child-runtime-owner-binding.md",
    "scripts/child_runtime_owner_binding_contract_common.py",
    "scripts/validate_child_runtime_owner_binding_contract.py",
    "scripts/ci/run_child_runtime_owner_binding_probes_ci.sh"
  ],
  "layer_state": "protocol-base-repo",
  "next_exact_action": [
    "formalize child tmp/probe/runtime owner binding admission only",
    "fail-close child tmp/probe/runtime roots with no admitted owner binding",
    "keep live-runtime exclusion machine-visible where required by the contract"
  ],
  "validation_bundle": [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_child_runtime_owner_binding_contract.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_child_runtime_owner_binding_probes_ci.sh"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-041B only"
}
```

Acceptance notes:
- owner binding must stay durable and machine-visible for child tmp, probe, and runtime roots;
- admission claims are invalid when child owner binding proof is absent;
- fail-close prevents freeform carry-forward of unowned child runtime residue.
