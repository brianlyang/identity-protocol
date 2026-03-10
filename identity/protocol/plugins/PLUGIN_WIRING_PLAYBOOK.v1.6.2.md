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

## Mandatory wiring checklist

1. Add plugin contract bundle files under `identity/protocol/plugins/<plugin-id>/`:
   - `plugin.contract.yaml`
   - `plugin.input.schema.json`
   - `plugin.output.schema.json`
   - `plugin.error-codes.yaml`
   - `README.md`
2. Register plugin in `identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml`:
   - `plugin_id`
   - `requirement_key`
   - `bundle_target_name`
   - `gate_mode=fail_close_strict`
   - `ssot_mapping_ref`
3. Add governance profile in `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml`:
   - `requirement_key`
   - `target_name`
   - `validator_script`
   - `required_gate_surfaces`
   - `required_report_fields`
4. Add requirement row in `identity/protocol/mappings/contract-binding.v1.6.yaml`:
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
9. If plugin needs provider runtime bindings:
   - use `identity/protocol/plugins/templates/provider-bindings.local.template.yaml`
   - do not store plaintext secrets in repo

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
