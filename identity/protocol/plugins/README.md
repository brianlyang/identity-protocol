# Identity Protocol Plugins

This directory is the canonical plugin governance root for protocol-level plugin enforcement.

## Foundational philosophy inheritance

1. This governed extension inherits `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` as the bottom-theory source for semantic singularity, fail-close preference, and lifecycle closure.
2. It inherits `identity/protocol/IDENTITY_RUNTIME.md` as the runtime constitution for execution, recovery, and current-turn authority boundaries.
3. Plugin law is an extension surface under the root protocol. It does not weaken, replace, or re-author root constitutions or runtime law.

## Extension authority boundary

1. Keep plugin contracts, schemas, provider profiles, and registry metadata here.
2. Do not store plaintext API credentials in this tree.
3. Instances consume this governance data and should store runtime receipts only.
4. Plugin onboarding prose and frozen contract prose explain governed extension law, but they are not machine verdict surfaces by themselves.

## Runtime adjudication boundary

1. Plugin READMEs and contract prose are interpretive/onboarding surfaces only.
2. They are not terminal surfaces for current-turn legality.
3. Current-turn legality must resolve from machine-consumed enforcement surfaces such as:
   - `PLUGIN_REGISTRY.current.yaml`
   - `FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - validators
   - probes
   - runtime state
   - receipts

## Truth lifecycle discipline

1. Plugin contract existence is not operational closure.
2. The lifecycle must remain explicit and ordered:
   - `truth_exists`
   - `truth_discoverable`
   - `truth_admissible`
   - `truth_bound`
   - `truth_consumed`
3. A plugin may be documented and registered yet still fail operational closure if it is not discoverable by the instance, admissible for the current turn, bound to the current run, or consumed by the next operational step.

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
   Single-intake authoring/check flow is active through `PLUGIN_JOIN_INTAKE.current.yaml` +
   `scripts/sync_plugin_join_wiring.py --check --json-only`.
   Auto-apply generation mode remains optional and does not block current fail-close governance.
6. Prove integration with machine checks:
   `validate_control_plane_invariants`, `validate_required_gate_surface_drift`, plugin projection validator, and target full-scan regression.

Hard rule:
control behavior is enforced by registry/governance/mapping pointers; plugin business logic must not be hardcoded in workflow shell steps.
