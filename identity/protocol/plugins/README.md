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

## Security

1. Secret values must come from env/vault at runtime.
2. Profiles may declare `*_env` keys and endpoint allowlists only.
3. Non-canonical plugin data outside `identity/protocol/plugins/**` should be rejected by strict protocol gates.
4. Instances must not copy plugin contracts/schemas/adapters into pack/runtime; instances only keep runtime bindings/receipts.

## Readability Contract

1. Plugin onboarding steps live in `PLUGIN_WIRING_PLAYBOOK.current.md`.
2. Documentation control rules live in `PLUGIN_DOC_CONTROL.current.yaml`.
3. `scripts/validate_control_plane_invariants.py` fail-closes when plugin README linkage or required tokens drift.
