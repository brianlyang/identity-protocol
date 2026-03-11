# Plugin Wiring Playbook (v1.6.2)

This is the single readable SSOT for adding a new protocol fail-close plugin.

Use this file first. Other files are implementation targets.

Machine policy for this playbook and plugin READMEs:

- `identity/protocol/plugins/PLUGIN_DOC_CONTROL.current.yaml`

## Goal

1. Keep plugin onboarding readable as the repo grows.
2. Prevent “added plugin but forgot one wiring file” drift.
3. Keep strong control-plane behavior without hardcoding plugin business logic.

## Existing reference plugins

1. `multimodal-vision-enforcement`
   - `requirement_key`: `asb16-rq-034`
   - `bundle_target_name`: `multimodal_plugin_enforcement`
2. `reasoning-loop-enforcement`
   - `requirement_key`: `asb16-rq-035`
   - `bundle_target_name`: `reasoning_loop_failclose_enforcement`

## Control-plane file map (config-first)

1. Plugin registry pointer:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml`
   - stores plugin rows (`plugin_id`, `requirement_key`, `bundle_target_name`, `gate_mode`, `ssot_mapping_ref`)
2. Plugin fail-close profile pointer:
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
   - stores per-plugin strict surfaces + projection/report requirements
3. Requirement mapping pointer:
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - stores requirement-level validator/surface/report/error-code contracts
4. Layer-targeted gate profile pointer:
   - `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`
   - controls `strict_full` vs targeted inspection trimming (strict operations stay no-trim)
5. Stream-doc registry pointer:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - keeps governance/review SSOT docs in one machine-resolved set

## Integration kind + fixed directory contract

All plugin onboarding must declare `integration_kind` and use fixed roots only:

1. `skill`
   - `protocol_contract_root=identity/protocol/plugins/skill`
   - `instance_runtime_root=.identity/{identity_id}/runtime/plugins/skills`
2. `mcp`
   - `protocol_contract_root=identity/protocol/plugins/mcp`
   - `instance_runtime_root=.identity/{identity_id}/runtime/plugins/mcp`
3. `api`
   - `protocol_contract_root=identity/protocol/plugins`
   - `instance_runtime_root=.identity/{identity_id}/runtime/plugins/api`

Hard boundary:

1. Non-canonical roots are invalid for fail-close plugin onboarding.
2. `contract_file` must stay under the selected `protocol_contract_root`.
3. Skill installation stays instance-side (lightweight attach model), while protocol only manages:
   - contract wiring
   - report/evidence fields
   - strict gate routing
4. File-organizer skill can be used as seed reference for skill-style folder governance:
   - `https://github.com/ComposioHQ/awesome-claude-skills/blob/master/file-organizer/SKILL.md`

## Mandatory wiring checklist

0. Select one `integration_kind` first (`skill | mcp | api`) and use only canonical roots:
   - `skill`:
     - `protocol_contract_root=identity/protocol/plugins/skill`
     - `instance_runtime_root=.identity/{identity_id}/runtime/plugins/skills`
   - `mcp`:
     - `protocol_contract_root=identity/protocol/plugins/mcp`
     - `instance_runtime_root=.identity/{identity_id}/runtime/plugins/mcp`
   - `api`:
     - `protocol_contract_root=identity/protocol/plugins`
     - `instance_runtime_root=.identity/{identity_id}/runtime/plugins/api`
   - Any non-canonical root is invalid for fail-close onboarding.
1. Add plugin contract bundle files under `<protocol_contract_root>/<plugin-id>/`:
   - `plugin.contract.yaml`
   - `plugin.input.schema.json`
   - `plugin.output.schema.json`
   - `plugin.error-codes.yaml`
   - `README.md`
2. Register plugin in `identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml` (resolved by alias):
   - `plugin_id`
   - `integration_kind`
   - `protocol_contract_root`
   - `instance_runtime_root`
   - `requirement_key`
   - `bundle_target_name`
   - `gate_mode=fail_close_strict`
   - `ssot_mapping_ref`
3. Add governance profile in `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml` (resolved by alias):
   - `requirement_key`
   - `target_name`
   - `validator_script`
   - `required_gate_surfaces`
   - `required_report_fields`
4. Add requirement row in `identity/protocol/mappings/contract-binding.current.yaml` (resolved by alias):
   - `kernel_contract_id`
   - `validator_ids`
   - `gate_surfaces`
   - `report_field_refs`
   - `error_code_refs`
5. Wire required gate routing in `scripts/required_gate_bundle_runner.py`:
   - requirement in `BUNDLE_REQUIREMENT_ORDER`
   - requirement -> `target_name`
   - `target_name` -> status field
6. Ensure strict-surface drift guard includes the requirement:
   - `scripts/validate_required_gate_surface_drift.py`
7. Ensure projection surfaces include plugin output fields:
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
8. Ensure per-plugin README points back to this playbook and includes:
   - `requirement_key`
   - `bundle_target_name`
   - `integration_kind`
   - `protocol_contract_root`
   - `instance_runtime_root`
9. If plugin needs provider runtime bindings:
   - register/update provider capability profile in `identity/protocol/plugins/PROVIDER_PROFILES.current.yaml`
   - use `identity/protocol/plugins/templates/provider-bindings.local.template.yaml`
   - do not store plaintext secrets in repo

## Runtime and CI routing boundary

1. Runtime strict routing:
   - `scripts/required_gate_bundle_runner.py` resolves plugin+mapping+gate-profile pointers and enforces fail-close.
2. CI required runtime gates:
   - `scripts/ci/run_required_runtime_gates_ci.sh` must invoke bundle runner; do not direct-call plugin validators from workflow shell.
3. Full-scan targeted regression:
   - `scripts/ci/run_full_scan_target_regression_ci.sh` and `scripts/validate_full_scan_target_regression.py` enforce `p0=0` on target source-layer.
4. GitHub offload boundary (v1.6.3):
   - branch/ruleset/merge-queue can offload control-plane mechanics,
   - semantic plugin fail-close checks remain protocol validator responsibilities.

## Required verification commands

```bash
python3 scripts/validate_control_plane_invariants.py --json-only
python3 scripts/validate_required_gate_surface_drift.py --json-only
python3 scripts/validate_failclose_plugin_projection.py \
  --catalog identity/catalog.local.yaml \
  --identity-id <id> \
  --operation validate \
  --run-id <run_id> \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode strict \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only
```

## Drift policy

1. Any fail-close plugin without this playbook link in its plugin README is invalid.
2. Any fail-close plugin without `requirement_key` or `bundle_target_name` in plugin README is invalid.
3. Any plugin added only in docs but not registry/governance/mapping/bundle is invalid.
4. Temporary logs and `/tmp/*` paths are evidence only and must not become normative wiring instructions.
