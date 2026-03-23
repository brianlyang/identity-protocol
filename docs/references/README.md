# Protocol References Control Plane

Status: Active guidance  
Layer: protocol  
Scope: canonical `docs/references/` directory contract for protocol-owned reference surfaces and visual atlases

## Current control-plane alias refs

- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/contract-binding.current.yaml`
- `identity/protocol/mappings/semantic-term-registry.current.yaml`

## Fixed role

1. `docs/references/` is the canonical directory for protocol-owned explanatory references, supporting guides, and visual atlases that accelerate human review.
2. Normative ownership remains with protocol motherline, governance/review stream docs, contract binding, and machine validators unless a reference doc explicitly says otherwise.
3. A reference surface may be canonical for discoverability, naming, directory ownership, and onboarding, while still remaining non-normative for semantic truth.

## Reference-surface classes

1. Supporting guides
   - long-form reference or operator guidance that helps readers consume protocol semantics without becoming the semantic owner.
2. Visual atlas families
   - canonical explanatory markdown + version-stamped SVG asset roots used to accelerate review and onboarding.
3. Cross-vendor / lifecycle references
   - non-owner explanatory surfaces that summarize stable protocol usage patterns while remaining subordinate to governance and validators.

## Standardized visual-atlas onboarding contract

Any future protocol-owned visual atlas must follow this standard path; do not improvise the steps per stream.

### A. Canonical surfaces

1. Create one canonical atlas markdown document under `docs/references/`.
2. Create one canonical asset root under `docs/references/assets/<atlas-family>/`.
3. All protocol-owned SVG files for that atlas family must stay under that single asset root.
4. Atlas filenames must be version-stamped and topic-descriptive.

### B. SSOT anchors

1. The atlas markdown must include current-pointer anchors for:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
2. The atlas markdown must explicitly declare that it is a discoverability/reference surface, not the semantic owner.
3. The owning governance/review stream docs must backlink the atlas path and asset root in the same change.

### C. Registry + index wiring

1. Register the atlas markdown in `identity/protocol/mappings/stream-doc-registry.v1.6.yaml` as a `mandatory_static_doc`.
2. Add a `static_doc_required_alias_refs` row for that atlas markdown.
3. Add an entry to `docs/governance/AUDIT_SNAPSHOT_INDEX.md` describing the atlas family and asset root.

### D. Validator standard

1. Atlas-family validators must reuse `scripts/reference_visual_atlas_governance_common.py` instead of cloning bespoke ad-hoc logic.
2. Each atlas family should have one thin validator script that supplies:
   - canonical doc path
   - canonical asset root
   - required SVG inventory
   - required owner-doc backlink markers
   - required audit-index markers
3. Validators must enforce repo-internal anti-scatter only unless a later workspace-governance stream explicitly broadens scope.

### E. Required-gate wiring standard

1. New atlas-family validators must be consumed through:
   - `scripts/docs_command_contract_check.py`
   - `scripts/validate_control_plane_invariants.py`
2. Direct addition to top-level required-gates workflow steps is **not** the default path; that requires separate budget/invariant review.
3. This rule prevents visual-atlas growth from silently expanding strict workflow fan-out or direct validator-call budgets.

### F. Truth-sync standard

1. If docs-command counts change because a new canonical atlas doc is added, the canonical workbook docs must be updated in the same closure.
2. If control-plane status artifacts are regenerated, `scripts/validate_control_plane_status_sync.py` must still pass.
3. A visual atlas is not considered landed until:
   - atlas validator passes,
   - docs command contract check passes,
   - issue register consistency passes,
   - stream doc registry / alias refs are synchronized.

## Non-goals

1. `docs/references/` does not replace governance/review streams as semantic owners.
2. Visual atlases do not create new contracts by themselves.
3. A reference surface must not be used to bypass machine validators or re-open frozen semantics through informal diagrams.
