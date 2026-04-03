# ${atlas_title}

${status_line}
Classification: protocol-owned explanatory atlas; not a normative contract source.

## 0) Why this atlas exists

1. This atlas provides a canonical visual reference for `${stream_version}` across ${surface_summary}.
2. This atlas is canonical for directory ownership, asset naming, explanatory discoverability, and onboarding acceleration only.
3. Normative truth remains the owning governance/review stream docs, the protocol motherline, contract binding, and machine validators.
4. This atlas is SSOT-governed as a canonical reference surface, but it is not the normative owner of semantic truth.
5. This atlas explains ${purpose_sentence} only.

## 1) Current-pointer anchors

1. This atlas must keep these current-pointer anchors visible in-document so SSOT drift is machine-detectable:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
2. If the atlas drops those current-pointer anchors, the document is stale even when the SVG assets still render.

## 2) Canonical surfaces

1. Canonical atlas markdown path is fixed to:
   - `${canonical_doc_rel}`
2. Canonical asset root for all protocol-owned ${asset_topic_label} visuals is fixed to:
   - `${canonical_asset_root_rel}`
3. All protocol-owned SVG assets for this atlas family must stay under that single asset root; do not scatter them across `docs/governance/`, `docs/review/`, `activity/evidence/`, or ad-hoc workspace folders.
4. Future version-stamped SVGs for this atlas family must remain under the same asset root rather than creating a sibling asset directory.

## 3) Anti-scatter boundary

1. The anti-scatter guarantee frozen by this atlas is limited to the `identity-protocol-local` repository surface.
2. Repo-internal scope means the canonical atlas document plus atlas-family SVG assets under this repository root.
3. Workspace-external staging/evidence copies, including `activity/evidence/` mirrors or sibling-workspace scratch outputs, are outside this validator scope and remain non-canonical by definition.

## 4) Semantic boundary

1. This atlas explains ${purpose_sentence} only.
2. The atlas may accelerate reviewer comprehension, but any conflict against governance / contract-binding / validator surfaces means the atlas is stale.
3. No diagram in this atlas may introduce backward compatibility, backstop, downgrade, lagging-pack shortcut, or undeclared rescue semantics.

## 5) Canonical SVG inventory

${svg_inventory_block}

## 6) Landing checklist for this atlas family

1. Register `${canonical_doc_rel}` in `identity/protocol/mappings/stream-doc-registry.v1.6.yaml` as a `mandatory_static_doc`.
2. Add a `static_doc_required_alias_refs` row for `${canonical_doc_rel}`.
3. Add an entry to `docs/governance/AUDIT_SNAPSHOT_INDEX.md` referencing `${canonical_doc_rel}` and `${canonical_asset_root_rel_slash}`.
4. Add owner-doc backlinks in each owning governance/review doc.
5. Land the thin validator at `${validator_script_rel}` on top of `scripts/reference_visual_atlas_governance_common.py`.
6. Rerun:
   - `python3 ${validator_script_rel} --json-only`
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_issue_register_consistency.py --json-only`
