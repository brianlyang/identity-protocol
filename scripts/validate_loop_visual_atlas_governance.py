#!/usr/bin/env python3
from __future__ import annotations

from reference_visual_atlas_governance_common import (
    VisualAtlasConfig,
    emit_visual_atlas_cli,
)

CANONICAL_ATLAS_DOC = "docs/references/identity-protocol-loop-visual-atlas-v1.6.md"
CANONICAL_ASSET_ROOT = "docs/references/assets/identity-protocol-loop-visual-atlas"
V162_GOV_DOC = "docs/governance/identity-multimodal-plugin-enforcement-governance-v1.6.2.md"
V1617_GOV_DOC = "docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md"
V1617_REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.17-routing-learning-strengthening.md"

CONFIG = VisualAtlasConfig(
    status_key="loop_visual_atlas_governance_status",
    error_code="IP-LOOP-ATLAS-001",
    canonical_doc=CANONICAL_ATLAS_DOC,
    canonical_asset_root=CANONICAL_ASSET_ROOT,
    required_svg_files=(
        "identity_protocol_four_loops_v1617.svg",
        "identity_protocol_loop3_route_discovery_control_plane_v1617.svg",
        "identity_protocol_loop4_feedback_strengthening_control_plane_v1617.svg",
        "identity_protocol_4to1_bounded_loopback_adjudication_v1617.svg",
    ),
    svg_family_pattern=r"^identity_protocol_(four_loops|loop3_route_discovery_control_plane|loop4_feedback_strengthening_control_plane|4to1_bounded_loopback_adjudication)_v[0-9A-Za-z.]+\.svg$",
    atlas_doc_pattern=r"^identity-protocol-loop-visual-atlas-v[0-9.]+\.md$",
    atlas_required_markers=(
        "Status: Active canonical visual reference for the frozen four-loop / 4→1 loopback explanation surface.",
        "Classification: protocol-owned explanatory atlas; not a normative contract source.",
        "Canonical atlas markdown path is fixed to:",
        "Canonical asset root for all protocol-owned loop visuals is fixed to:",
        "do not scatter them across `docs/governance/`, `docs/review/`, `activity/evidence/`, or ad-hoc workspace folders",
        "The anti-scatter guarantee frozen by this atlas is limited to the `identity-protocol-local` repository surface.",
        "Workspace-external staging/evidence copies, including `activity/evidence/` mirrors or sibling-workspace scratch outputs, are outside this validator scope and remain non-canonical by definition.",
        "No diagram in this atlas may introduce backward compatibility, backstop, downgrade, lagging-pack shortcut, or undeclared rescue semantics.",
    ),
    index_required_markers=(
        "`docs/references/identity-protocol-loop-visual-atlas-v1.6.md`",
        "asset root: `docs/references/assets/identity-protocol-loop-visual-atlas/`",
    ),
    owner_doc_markers={
        V162_GOV_DOC: (
            "docs/references/identity-protocol-loop-visual-atlas-v1.6.md",
            "docs/references/assets/identity-protocol-loop-visual-atlas/",
            "This stream remains the semantic owner for the first-loop / second-loop kernel-authoritative surfaces shown in that atlas",
        ),
        V1617_GOV_DOC: (
            "docs/references/identity-protocol-loop-visual-atlas-v1.6.md",
            "docs/references/assets/identity-protocol-loop-visual-atlas/",
            "Loop 3 center = `route_discovery_convergence_contract_v1`",
            "Loop 4 center = `feedback_operational_prompt_contract_v1`",
            "bounded bridge = `feedback_to_judgement_loopback_contract_v1`",
        ),
        V1617_REVIEW_DOC: (
            "docs/references/identity-protocol-loop-visual-atlas-v1.6.md",
            "docs/references/assets/identity-protocol-loop-visual-atlas/",
            "the shared four-track primitive remains distinct from the `4→1` bridge",
            "first-loop revalidation remains authoritative after loopback reentry.",
        ),
    },
)


def main() -> int:
    return emit_visual_atlas_cli(
        CONFIG,
        description="Validate canonical loop visual atlas SSOT/directory governance.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
