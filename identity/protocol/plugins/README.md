# Identity Protocol Plugins (v1.6.2 baseline)

This directory is the canonical plugin governance root for protocol-level plugin enforcement.

## Scope

1. Keep plugin contracts, schemas, provider profiles, and registry metadata here.
2. Do not store plaintext API credentials in this tree.
3. Instances consume this governance data and should store runtime receipts only.

## Canonical files

1. `PLUGIN_REGISTRY.current.yaml` (stable registry entry; points to current versioned registry)
2. `PROVIDER_PROFILES.current.yaml` (stable provider profile entry; points to current versioned provider profile file)
3. `FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml` (stable fail-close governance entry; points to current versioned policy)
4. `PLUGIN_WIRING_PLAYBOOK.current.md` (stable playbook entry; points to current versioned playbook)
5. `PLUGIN_DOC_CONTROL.current.yaml` (stable doc-control entry; points to current versioned policy)
6. `schemas/*.schema.json` (strict schema validation)
7. `templates/provider-bindings.local.template.yaml` (instance-side minimal binding template: profile pointer + credential_ref only)

## Control-plane pointers (integration boundary)

1. `identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml` is the plugin registration SSOT (requirement/bundle/gate-mode wiring).
2. `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml` is the strict fail-close profile SSOT.
3. `identity/protocol/mappings/contract-binding.current.yaml` is the requirement-level contract mapping source.
4. `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml` controls strict vs targeted gate-profile trimming behavior.
5. `identity/protocol/mappings/stream-doc-registry.current.yaml` is the machine SSOT for active governance/review streams.
6. Plugin docs are onboarding guides only; runtime enforcement comes from validators + control-plane pointers above.

## Security

1. Secret values must come from env/vault at runtime.
2. Profiles may declare `*_env` keys and endpoint allowlists only.
3. Non-canonical plugin data outside `identity/protocol/plugins/**` should be rejected by strict protocol gates.
4. Instances must not copy plugin contracts/schemas/adapters into pack/runtime; instances only keep runtime bindings/receipts.

## Readability Contract

1. Plugin onboarding steps live in `PLUGIN_WIRING_PLAYBOOK.current.md`.
2. Documentation control rules live in `PLUGIN_DOC_CONTROL.current.yaml`.
3. `scripts/validate_control_plane_invariants.py` fail-closes when plugin README linkage or required tokens drift.

## Plugin Join Flow (config-first, fail-close)

0. Choose one integration kind and fixed roots first (no ad-hoc paths):
   - `skill`
     - `protocol_contract_root=identity/protocol/plugins/skill`
     - `instance_runtime_root=.identity/{identity_id}/runtime/plugins/skills`
   - `mcp`
     - `protocol_contract_root=identity/protocol/plugins/mcp`
     - `instance_runtime_root=.identity/{identity_id}/runtime/plugins/mcp`
   - `api`
     - `protocol_contract_root=identity/protocol/plugins`
     - `instance_runtime_root=.identity/{identity_id}/runtime/plugins/api`
1. Define plugin contract bundle under `<protocol_contract_root>/<plugin-id>/`:
   `plugin.contract.yaml`, input/output schemas, error-code map, and per-plugin README.
2. Author plugin join through the canonical minimum tuple:
   `plugin_id`, `requirement_key`, `bundle_target_name`, `gate_mode`, `ssot_mapping_ref`.
   Mandatory extension fields:
   `integration_kind`, `protocol_contract_root`, `instance_runtime_root`.
3. Keep wiring configuration-driven across control-plane sources:
   `PLUGIN_REGISTRY.current.yaml`, `FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`,
   `identity/protocol/mappings/contract-binding.current.yaml`,
   `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`,
   `identity/protocol/mappings/stream-doc-registry.current.yaml`.
4. Bundle runner onboarding must be mapping-derived:
   new plugin join must not depend on adding plugin-specific static maps in `scripts/required_gate_bundle_runner.py`.
5. Operating model (v1.6.4 code-sync baseline):
   fail-close plugin requirement onboarding is mapping-derived in bundle runner; plugin-specific static map edits are not required.
   Single-intake generation remains the target for the next hardening slice.
6. Prove integration with machine checks:
   `validate_control_plane_invariants`, `validate_required_gate_surface_drift`, plugin projection validator, and target full-scan regression.

Hard rule:
control behavior is enforced by registry/governance/mapping pointers; plugin business logic must not be hardcoded in workflow shell steps.
