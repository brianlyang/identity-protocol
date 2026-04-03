# Reference Visual Atlas Scaffold - Next Steps

This scaffold is a **preview output**, not a canonical landed atlas yet.

Generated target surfaces:

- atlas markdown: `${canonical_doc_rel}`
- asset root: `${canonical_asset_root_rel_slash}`
- validator: `${validator_script_rel}`

## Before copying this scaffold into the protocol repo

1. Replace any remaining draft wording so the atlas prose matches the owning stream exactly.
2. Produce the real version-stamped SVG files listed in the inventory.
3. Confirm the owner docs below are the correct governance/review surfaces for this atlas family:
${owner_docs_bullets}

## Required truth-sync after copying into the protocol repo

1. Register `${canonical_doc_rel}` in `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`.
2. Add the required alias-ref row for `${canonical_doc_rel}`.
3. Add the atlas family entry to `docs/governance/AUDIT_SNAPSHOT_INDEX.md`.
4. Add backlinks in each owner doc to:
   - `${canonical_doc_rel}`
   - `${canonical_asset_root_rel_slash}`
5. Rerun:
   - `python3 ${validator_script_rel} --json-only`
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_issue_register_consistency.py --json-only`

## Non-goal

Generating this scaffold does **not** by itself land a new canonical atlas family. Canonical status starts only after registry/index/backlink truth-sync and validator green closure.
