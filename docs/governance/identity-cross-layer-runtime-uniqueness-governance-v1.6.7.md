# Identity Cross-Layer Runtime Uniqueness Governance (v1.6.7)

Status: Active  
Owners: protocol architecture / governance lane  
Scope: protocol runtime identity arbitration (`project` vs `global` local catalogs)

## 1) Why v1.6.7 is a new stream (not folded into v1.6.6)

1. v1.6.6 closes wrapper-bound execution channels (ingress/egress) and per-round governance transport.
2. v1.6.6 does not, by itself, guarantee that a runtime `identity_id` has a single active owner across
   both `project` and `global` catalogs.
3. The newly confirmed risk is cross-layer runtime ambiguity:
   - same `identity_id` active in both catalogs
   - different `pack_path` values
   - runtime can switch behavior depending on selected catalog root.
4. Therefore v1.6.7 is opened as a dedicated stream for identity source-of-truth uniqueness.

## 2) Frozen terminology and boundary

1. Protocol base repo: `identity-protocol-local`.
2. Business project repo: `<project>` (example: `weixinstore`).
3. Identity runtime layers:
   - project layer: `<project>/.identity/catalog.local.yaml`
   - global layer: `${CODEX_HOME}/.identity/catalog.local.yaml` (fallback `~/.codex/.identity/catalog.local.yaml`)
4. This stream governs runtime identity ownership arbitration only; it does not redefine v1.6.6 wrapper contracts.

## 3) Mandatory policy (hard constraints)

1. Runtime identities (`profile!=fixture`, `runtime_mode!=demo_only`) must not be active in both project and global catalogs under the same `identity_id`.
2. If both layers contain active runtime rows for the same `identity_id`, fail-close is mandatory.
3. Fixture/demo rows are excluded from this hard duplicate block.
4. Update/activate paths must validate this rule before mutation execution.

## 4) Protocol tooling closure in this stream

1. `scripts/validate_identity_scope_isolation.py`
   - extended to enforce cross-layer runtime uniqueness
   - blocks active runtime duplicates with explicit details + remediation hint.
2. `scripts/repair_identity_cross_layer_uniqueness.py`
   - provides repair contract for deactivating duplicate layer entry
   - supports check mode and `--apply` mode with explicit `--prefer-layer`.
3. `scripts/identity_creator.py`
   - `activate` preflight now hard-runs scope isolation/uniqueness validation
   - `update` preflight now hard-runs scope isolation/uniqueness validation.

## 5) Acceptance gates (v1.6.7)

All below are required for stream closure:

1. `python3 scripts/validate_identity_scope_isolation.py --catalog <project_catalog> --repo-catalog <repo_catalog> --identity-id <id>`
   - duplicate active runtime across layers => must fail-close.
2. `python3 scripts/validate_identity_scope_isolation.py ... --allow-cross-layer-runtime-duplicate`
   - migration-only override path remains explicit and non-default.
3. `python3 scripts/repair_identity_cross_layer_uniqueness.py --identity-id <id> --repo-catalog <repo_catalog> --prefer-layer project --json-only`
   - check mode exposes duplicate state deterministically.
4. `python3 -m py_compile scripts/validate_identity_scope_isolation.py scripts/repair_identity_cross_layer_uniqueness.py scripts/identity_creator.py`
   - compile contract must pass.

## 6) No-sprawl constraint

1. v1.6.7 reuses existing mapping YAML files.
2. No new mapping YAML file is introduced by this stream.
3. Stream registration and evidence allowlist are appended minimally to existing v1.6 mapping files.

## 7) Cross-stream linkage (v1.6.6 + v1.6.7)

1. v1.6.6 ensures “every round goes through wrapper channel”.
2. v1.6.7 ensures “the identity behind that wrapper channel is uniquely owned per runtime context”.
3. Combined interpretation:
   - v1.6.6 closes execution transport.
   - v1.6.7 closes identity source arbitration.

## 8) Stream posture

1. Policy posture: `PASS` (constraints and tooling are explicit).
2. Implementation posture: `CONDITIONAL_PASS` until existing duplicate runtime rows are remediated per identity.

## 9) Stream continuity alias pointers

1. `identity/protocol/mappings/contract-binding.current.yaml`
2. `identity/protocol/mappings/control-plane-invariants.current.yaml`
3. `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
4. `identity/protocol/mappings/stream-doc-registry.current.yaml`
