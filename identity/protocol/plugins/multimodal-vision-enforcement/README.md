# multimodal-vision-enforcement

Protocol-governed plugin contract for multimodal vision-capable provider enforcement.

## Purpose

1. Ensure plugin naming/schema/threshold/path/copy-policy contracts remain deterministic.
2. Ensure provider profile capability (vision/tool/structured-json) matches plugin requirements.
3. Ensure runtime binding references use credential indirection (`env:`/`vault:`), not plaintext secrets.

## Contract

1. Requirement key: `asb16-rq-034`
2. Bundle target name: `multimodal_plugin_enforcement`
3. Contract id: `rq_034_multimodal_plugin_enforcement_contract_v1`
4. Validator: `scripts/validate_multimodal_plugin_enforcement.py`
5. Wiring playbook: `identity/protocol/plugins/PLUGIN_WIRING_PLAYBOOK.current.md`

## Canonical contract files

1. `plugin.contract.yaml`
2. `plugin.input.schema.json`
3. `plugin.output.schema.json`
4. `plugin.error-codes.yaml`

## Runtime note

Instances should not copy this contract. They only keep runtime bindings and receipts.
