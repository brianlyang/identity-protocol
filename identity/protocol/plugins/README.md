# Identity Protocol Plugins (v1.6.2 baseline)

This directory is the canonical plugin governance root for protocol-level plugin enforcement.

## Scope

1. Keep plugin contracts, schemas, provider profiles, and registry metadata here.
2. Do not store plaintext API credentials in this tree.
3. Instances consume this governance data and should store runtime receipts only.

## Canonical files

1. `PLUGIN_REGISTRY.v1.6.2.yaml` (registry, when landed)
2. `PROVIDER_PROFILES.v1.6.2.yaml` (provider capabilities and endpoint policy)
3. `FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml` (single-source fail-close plugin wiring policy: paths + mapping + surfaces + prompt binding)
4. `PLUGIN_WIRING_PLAYBOOK.v1.6.2.md` (human-readable single-file plugin onboarding/wiring SSOT)
5. `PLUGIN_DOC_CONTROL.v1.6.2.yaml` (machine-readable plugin documentation control policy)
6. `schemas/*.schema.json` (strict schema validation)
7. `templates/provider-bindings.local.template.yaml` (instance-side minimal binding template: profile pointer + credential_ref only)

## Security

1. Secret values must come from env/vault at runtime.
2. Profiles may declare `*_env` keys and endpoint allowlists only.
3. Non-canonical plugin data outside `identity/protocol/plugins/**` should be rejected by strict protocol gates.
4. Instances must not copy plugin contracts/schemas/adapters into pack/runtime; instances only keep runtime bindings/receipts.

## Readability Contract

1. Plugin onboarding steps live in `PLUGIN_WIRING_PLAYBOOK.v1.6.2.md`.
2. Documentation control rules live in `PLUGIN_DOC_CONTROL.v1.6.2.yaml`.
3. `scripts/validate_control_plane_invariants.py` fail-closes when plugin README linkage or required tokens drift.
