# Identity Role-Binding Contract (v1.4.6 draft)

## Purpose

Ensure an identity is not only scaffolded, but also **bound as a runnable role** with auditable evidence before activation/default switching.

## Contract key

`identity_role_binding_contract`

### Minimum fields

```json
{
  "identity_role_binding_contract": {
    "required": true,
    "role_type": "store_manager_runtime_operator",
    "catalog_registration_required": true,
    "runtime_bootstrap_pass_required": true,
    "activation_policy": "inactive_by_default",
    "switch_guard_required": true,
    "binding_evidence_path_pattern": "identity/runtime/examples/identity-role-binding-<identity-id>-*.json",
    "enforcement_validator": "scripts/validate_identity_role_binding.py"
  }
}
```

## Runtime semantics

1. Create success != role binding success.
2. Binding requires:
   - catalog registration exists
   - pack path + CURRENT_TASK exists
   - runtime bootstrap validation pass evidence exists
   - role-binding evidence exists and matches identity + role_type
3. Activation/default promotion requires switch guard pass.

## Validator

`scripts/validate_identity_role_binding.py`

Checks:
1. Catalog registration and identity resolution.
2. `gates.role_binding_gate=required`.
3. `identity_role_binding_contract.required=true` and schema completeness.
4. Binding evidence exists and contains required fields.
5. Evidence identity/role_type matches contract.
6. Bootstrap + switch guard status are PASS.
7. If identity is active or default, binding status must be BOUND_READY/BOUND_ACTIVE.

## Evidence examples

- Positive: `identity/runtime/examples/identity-role-binding-store-manager-sample.json`
- Negative: `identity/runtime/examples/role-binding/identity-role-binding-store-manager-negative-sample.json`

