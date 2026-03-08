# multimodal-vision-enforcement

Protocol-governed plugin contract for multimodal vision-capable provider enforcement.

## Purpose

1. Ensure plugin naming/schema/threshold/path/copy-policy contracts remain deterministic.
2. Ensure provider profile capability (vision/tool/structured-json) matches plugin requirements.
3. Ensure runtime binding references use credential indirection (`env:`/`vault:`), not plaintext secrets.

## Canonical contract files

1. `plugin.contract.yaml`
2. `plugin.input.schema.json`
3. `plugin.output.schema.json`
4. `plugin.error-codes.yaml`

## Runtime note

Instances should not copy this contract. They only keep runtime bindings and receipts.
