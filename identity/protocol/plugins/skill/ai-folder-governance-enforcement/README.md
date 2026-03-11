# ai-folder-governance-enforcement

This plugin wires file governance skill enforcement into required gates.

- requirement_key: `asb16-rq-020`
- bundle_target_name: `skill_path_integrity`
- validator: `scripts/validate_v16_skill_path_integrity.py`
- integration_kind: `skill`
- protocol_contract_root: `identity/protocol/plugins/skill`
- instance_runtime_root: `.identity/{identity_id}/runtime/plugins/skills`

Source of truth and wiring constraints are governed by `PLUGIN_WIRING_PLAYBOOK.current.md`.
