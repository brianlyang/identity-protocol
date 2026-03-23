# Identity Protocol Artifact-Family Routing Visual Atlas (v1.6)

Status: Active canonical visual reference for the frozen artifact-family routing / memory-like interpretation surface.
Classification: protocol-owned explanatory atlas; not a normative contract source.

## 0) Why this atlas exists

1. The identity protocol now carries a human-facing visual atlas for the `v1.6.18` artifact-family routing stream so reviewers do not have to reconstruct the memory-like layering model from scattered chat residue.
2. This atlas is canonical for **directory ownership, asset naming, explanatory discoverability, and quick reviewer comprehension** only.
3. Normative truth remains anchored to:
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
   - `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.18-artifact-family-routing.md`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
   - the corresponding validator / probe lanes that machine-consume those contracts
4. This atlas is SSOT-governed as a canonical reference surface, but it is not the normative owner of family semantics.
5. The atlas visualizes the six-layer interpretation model, the viability checklist, and the three-state upgrade-safety discipline so future readers can quickly understand why generic `memory` language is non-canonical.

## 0.1) Current-pointer anchors (mandatory)

1. This atlas must keep these current-pointer anchors visible in-document so SSOT drift is machine-detectable:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
2. If the atlas drops those current-pointer anchors, the document is stale even when the SVG assets still render.

## 1) Fixed directory freeze (mandatory)

1. Canonical atlas markdown path is fixed to:
   - `docs/references/identity-protocol-artifact-family-routing-visual-atlas-v1.6.md`
2. Canonical asset root for all protocol-owned artifact-family routing visuals is fixed to:
   - `docs/references/assets/identity-protocol-artifact-family-routing-visual-atlas/`
3. Future protocol-owned artifact-family routing SVG files must live under that asset root; do not scatter them across `docs/governance/`, `docs/review/`, `activity/evidence/`, or ad-hoc workspace folders as the current reference surface.
4. Working copies or generation scratch outside this root are non-canonical staging only and must not be cited as current-state protocol truth.
5. When artifact-family routing semantics change, the owning governance/review docs and the affected SVG assets must be updated in the same commit or PR so the explanatory surface cannot drift behind the normative one.

## 1.1) Anti-scatter scope boundary (mandatory)

1. The anti-scatter guarantee frozen by this atlas is limited to the `identity-protocol-local` repository surface.
2. Repo-internal scope means the canonical atlas document plus atlas-family SVG assets under this repository root; that is the only surface scanned by `scripts/validate_artifact_family_visual_atlas_governance.py`.
3. Workspace-external staging/evidence copies, including `activity/evidence/` mirrors or sibling-workspace scratch outputs, are outside this validator scope and remain non-canonical by definition.
4. Any future desire to govern workspace-wide staging copies must open a separate workspace-governance lane; it must not be smuggled into protocol SSOT claims by wording inflation.

## 2) Fixed semantic boundary (mandatory)

1. This atlas visualizes the artifact-family routing model only; it does not create a new generic memory subsystem.
2. `memory` is not a canonical protocol sink name and must never be rendered as a generic success-path bucket in these visuals.
3. The atlas may visualize the eight frozen families, but it may not merge them into one reusable “memory bucket”.
4. `reject_memory_gate` and `*_contract` blocks remain control-plane declarations; the atlas may show that separation, but may not depict them as storage roots.
5. `runtime/memory-absorption/**` remains quarantine / re-materialization only; no diagram may promote it to an active continuity, dialogue, learning, or protocol-feedback sink.
6. No diagram in this atlas may introduce backward compatibility, backstop, downgrade, lagging-pack shortcut, or undeclared rescue semantics.

## 3) File naming rule

1. Protocol-owned SVG filenames under the canonical asset root must remain version-stamped and topic-descriptive.
2. The current frozen asset family is:
   - `identity_protocol_artifact_family_routing_matrix_v1618.svg`
   - `identity_protocol_artifact_family_viability_model_v1618.svg`
   - `identity_protocol_artifact_family_upgrade_truth_v1618.svg`
3. New versions may add new version-stamped files under the same canonical asset root, but must not fork a second asset directory for the same atlas family.

## 4) Canonical asset inventory

1. Artifact-family routing matrix
   - Path: `docs/references/assets/identity-protocol-artifact-family-routing-visual-atlas/identity_protocol_artifact_family_routing_matrix_v1618.svg`
   - Relative link: [identity_protocol_artifact_family_routing_matrix_v1618.svg](assets/identity-protocol-artifact-family-routing-visual-atlas/identity_protocol_artifact_family_routing_matrix_v1618.svg)
   - Purpose: show the six-layer interpretation flow from a colloquial “memory” request to one exact frozen family, including the eight canonical family endpoints.
2. Family viability model
   - Path: `docs/references/assets/identity-protocol-artifact-family-routing-visual-atlas/identity_protocol_artifact_family_viability_model_v1618.svg`
   - Relative link: [identity_protocol_artifact_family_viability_model_v1618.svg](assets/identity-protocol-artifact-family-routing-visual-atlas/identity_protocol_artifact_family_viability_model_v1618.svg)
   - Purpose: show the five-signal viability test: semantic owner, canonical root, shared producer, shared consumer/validator, and active replay.
3. Upgrade-safe runtime truth
   - Path: `docs/references/assets/identity-protocol-artifact-family-routing-visual-atlas/identity_protocol_artifact_family_upgrade_truth_v1618.svg`
   - Relative link: [identity_protocol_artifact_family_upgrade_truth_v1618.svg](assets/identity-protocol-artifact-family-routing-visual-atlas/identity_protocol_artifact_family_upgrade_truth_v1618.svg)
   - Purpose: show the required / optional / quarantine three-state discipline that prevents upgrades from killing healthy lines or manufacturing fake green.

## 5) Consumption rule for reviewers and implementers

1. Use this atlas to accelerate onboarding, architecture review, and cross-team discussion.
2. Do **not** use this atlas as the only source for current-state protocol judgments; always cross-check the owning governance/review docs, contract bindings, and live validators/probes.
3. If a diagram conflicts with a normative contract or machine validator, the diagram is stale by definition and must be corrected.
4. If future protocol work requires new artifact-family routing visuals, add them under the same canonical asset root and update this atlas instead of opening a new scattered visual family.
