# Identity Protocol Plugins (v1.6.2 baseline)

This directory is the canonical plugin governance root for protocol-level plugin enforcement.

## Scope

1. Keep plugin contracts, schemas, provider profiles, and registry metadata here.
2. Do not store plaintext API credentials in this tree.
3. Instances consume this governance data and should store runtime receipts only.

## Canonical files

1. `PLUGIN_REGISTRY.v1.6.2.yaml` (registry, when landed)
2. `PROVIDER_PROFILES.v1.6.2.yaml` (provider capabilities and endpoint policy)
3. `schemas/*.schema.json` (strict schema validation)
4. `templates/provider-bindings.local.template.yaml` (instance-side minimal binding template: profile pointer + credential_ref only)

## Security

1. Secret values must come from env/vault at runtime.
2. Profiles may declare `*_env` keys and endpoint allowlists only.
3. Non-canonical plugin data outside `identity/protocol/plugins/**` should be rejected by strict protocol gates.
4. Instances must not copy plugin contracts/schemas/adapters into pack/runtime; instances only keep runtime bindings/receipts.
