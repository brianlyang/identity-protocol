# Identity Protocol Loop Visual Atlas (v1.6)

Status: Active canonical visual reference for the frozen four-loop / 4→1 loopback explanation surface.
Classification: protocol-owned explanatory atlas; not a normative contract source.

## 0) Why this atlas exists

1. The identity protocol now carries a human-facing visual atlas for the four-loop control plane and the bounded `4→1` loopback bridge so reviewers can inspect the control structure without reconstructing it from scattered chat residue.
2. This atlas is canonical for **directory ownership, asset naming, and explanatory visual discoverability** only.
3. Normative truth remains anchored to the protocol contract and machine-consumed surfaces, especially:
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
   - `docs/governance/identity-multimodal-plugin-enforcement-governance-v1.6.2.md`
   - `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.17-routing-learning-strengthening.md`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
   - the corresponding validator / probe lanes that machine-consume those contracts
4. This atlas is SSOT-governed as a canonical reference surface, but it is not itself the normative owner of loop semantics.
5. This atlas must stay generic and protocol-only. It must not absorb business scenarios, search heuristics, vendor/product examples, or instance-specific playbooks.

## 0.1) Current-pointer anchors (mandatory)

1. This atlas must keep these current-pointer anchors visible in-document so SSOT drift is machine-detectable:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
2. If the atlas drops those current-pointer anchors, the document is stale even when the SVG assets still render.

## 1) Fixed directory freeze (mandatory)

1. Canonical atlas markdown path is fixed to:
   - `docs/references/identity-protocol-loop-visual-atlas-v1.6.md`
2. Canonical asset root for all protocol-owned loop visuals is fixed to:
   - `docs/references/assets/identity-protocol-loop-visual-atlas/`
3. Future protocol-owned loop SVG files must live under that asset root; do not scatter them across `docs/governance/`, `docs/review/`, `activity/evidence/`, or ad-hoc workspace folders as the current reference surface.
4. Working copies or generation scratch outside this root are non-canonical staging only and must not be cited as current-state protocol truth.
5. When loop semantics change, the owning governance/review docs and the affected SVG assets must be updated in the same commit or PR so the explanatory surface cannot drift behind the normative one.

## 1.1) Anti-scatter scope boundary (mandatory)

1. The anti-scatter guarantee frozen by this atlas is limited to the `identity-protocol-local` repository surface.
2. Repo-internal scope means the canonical atlas document plus atlas-family SVG assets under this repository root; that is the only surface scanned by `scripts/validate_loop_visual_atlas_governance.py`.
3. Workspace-external staging/evidence copies, including `activity/evidence/` mirrors or sibling-workspace scratch outputs, are outside this validator scope and remain non-canonical by definition.
4. Any future desire to govern workspace-wide staging copies must open a separate workspace-governance lane; it must not be smuggled into protocol SSOT claims by wording inflation.

## 2) Fixed semantic boundary (mandatory)

1. Loop 1 and Loop 2 remain kernel-authoritative and semantically anchored by the first two capability contracts; this atlas may visualize them, but may not redefine them.
2. Loop 3 and Loop 4 remain the strengthened centers owned by `v1.6.17`; this atlas may visualize their control-plane structure, but may not create a second semantic owner.
3. `roundtable_four_track_cross_validation_contract_v1` remains a shared primitive, not a fifth loop and not the `4→1` bridge.
4. `feedback_to_judgement_loopback_contract_v1` remains a bounded bridge that returns preflight aid only; it never becomes first-loop truth.
5. Conflict after loopback reentry must continue to mean demotion / rollback plus negative-feedback writeback; this atlas may illustrate that rule, but may not relax it.
6. No diagram in this atlas may introduce backward compatibility, backstop, downgrade, lagging-pack shortcut, or undeclared rescue semantics.

## 3) File naming rule

1. Protocol-owned SVG filenames under the canonical asset root must remain version-stamped and topic-descriptive.
2. The current frozen asset family is:
   - `identity_protocol_four_loops_v1617.svg`
   - `identity_protocol_loop3_route_discovery_control_plane_v1617.svg`
   - `identity_protocol_loop4_feedback_strengthening_control_plane_v1617.svg`
   - `identity_protocol_4to1_bounded_loopback_adjudication_v1617.svg`
3. New versions may add new version-stamped files under the same canonical asset root, but must not fork a second asset directory for the same atlas family.

## 4) Canonical asset inventory

1. Overall four-loop overview
   - Path: `docs/references/assets/identity-protocol-loop-visual-atlas/identity_protocol_four_loops_v1617.svg`
   - Relative link: [identity_protocol_four_loops_v1617.svg](assets/identity-protocol-loop-visual-atlas/identity_protocol_four_loops_v1617.svg)
   - Purpose: show Loop 1 / Loop 2 kernel authority, Loop 3 / Loop 4 strengthened centers, the shared four-track primitive, and the bounded `4→1` bridge in one adjudication view.
2. Loop 3 control plane
   - Path: `docs/references/assets/identity-protocol-loop-visual-atlas/identity_protocol_loop3_route_discovery_control_plane_v1617.svg`
   - Relative link: [identity_protocol_loop3_route_discovery_control_plane_v1617.svg](assets/identity-protocol-loop-visual-atlas/identity_protocol_loop3_route_discovery_control_plane_v1617.svg)
   - Purpose: show `route_discovery_convergence_contract_v1` as the third-loop strengthened center with explicit candidate comparison, serial acceptance, and shared four-track consumption.
3. Loop 4 control plane
   - Path: `docs/references/assets/identity-protocol-loop-visual-atlas/identity_protocol_loop4_feedback_strengthening_control_plane_v1617.svg`
   - Relative link: [identity_protocol_loop4_feedback_strengthening_control_plane_v1617.svg](assets/identity-protocol-loop-visual-atlas/identity_protocol_loop4_feedback_strengthening_control_plane_v1617.svg)
   - Purpose: show `feedback_operational_prompt_contract_v1` as a replay-gated, rollback-capable, TTL-bounded strengthening lane rather than a kernel rewrite.
4. `4→1` bounded loopback adjudication
   - Path: `docs/references/assets/identity-protocol-loop-visual-atlas/identity_protocol_4to1_bounded_loopback_adjudication_v1617.svg`
   - Relative link: [identity_protocol_4to1_bounded_loopback_adjudication_v1617.svg](assets/identity-protocol-loop-visual-atlas/identity_protocol_4to1_bounded_loopback_adjudication_v1617.svg)
   - Purpose: show `feedback_to_judgement_loopback_contract_v1` as a preflight-only bounded bridge with mandatory first-loop revalidation, conflict demotion, rollback, and negative-feedback writeback.

## 5) Consumption rule for reviewers and implementers

1. Use this atlas to accelerate human review, onboarding, and architecture discussion.
2. Do **not** use this atlas as the only source for current-state protocol judgments; always cross-check the owning governance/review docs, contract bindings, and live validators/probes.
3. If a diagram conflicts with a normative contract or machine validator, the diagram is stale by definition and must be corrected.
4. If future protocol work requires new loop visuals, add them under the same canonical asset root and update this atlas instead of opening a new scattered visual family.
