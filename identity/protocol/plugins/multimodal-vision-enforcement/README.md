# multimodal-vision-enforcement

Protocol-governed plugin contract for multimodal vision-capable provider enforcement.

## Foundational philosophy inheritance

1. This plugin inherits `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` as the source for fail-close semantics and lifecycle closure.
2. It inherits `identity/protocol/IDENTITY_RUNTIME.md` for runtime authority boundaries.

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

## Runtime adjudication boundary

1. This README and its contract prose freeze governed extension law; they do not decide current-turn legality by themselves.
2. Current-turn legality must resolve from registry/mapping bindings, `scripts/validate_multimodal_plugin_enforcement.py`, runtime state, and receipts.

## Truth lifecycle note

1. `truth_exists`: the contract bundle exists.
2. `truth_discoverable`: registry/profile surfaces expose the plugin to the instance.
3. `truth_admissible`: current requirement and gate mapping accept the plugin as authoritative for the turn.
4. `truth_bound`: runtime binding and evidence are attached to the current run.
5. `truth_consumed`: the next operational step actually uses the bound plugin evidence in enforcement.

## Runtime note

Instances should not copy this contract. They only keep runtime bindings and receipts.
