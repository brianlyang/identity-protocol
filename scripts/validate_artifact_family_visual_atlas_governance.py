#!/usr/bin/env python3
from __future__ import annotations

from reference_visual_atlas_governance_common import (
    VisualAtlasConfig,
    emit_visual_atlas_cli,
)

CANONICAL_ATLAS_DOC = "docs/references/identity-protocol-artifact-family-routing-visual-atlas-v1.6.md"
CANONICAL_ASSET_ROOT = "docs/references/assets/identity-protocol-artifact-family-routing-visual-atlas"
V1618_GOV_DOC = "docs/governance/identity-artifact-family-routing-governance-v1.6.18.md"
V1618_REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.18-artifact-family-routing.md"

CONFIG = VisualAtlasConfig(
    status_key="artifact_family_visual_atlas_governance_status",
    error_code="IP-AFR-ATLAS-001",
    canonical_doc=CANONICAL_ATLAS_DOC,
    canonical_asset_root=CANONICAL_ASSET_ROOT,
    required_svg_files=(
        "identity_protocol_artifact_family_routing_matrix_v1618.svg",
        "identity_protocol_artifact_family_viability_model_v1618.svg",
        "identity_protocol_artifact_family_upgrade_truth_v1618.svg",
    ),
    svg_family_pattern=r"^identity_protocol_artifact_family_(routing_matrix|viability_model|upgrade_truth)_v[0-9A-Za-z.]+\.svg$",
    atlas_doc_pattern=r"^identity-protocol-artifact-family-routing-visual-atlas-v[0-9.]+\.md$",
    atlas_required_markers=(
        "Status: Active canonical visual reference for the frozen artifact-family routing / memory-like interpretation surface.",
        "Classification: protocol-owned explanatory atlas; not a normative contract source.",
        "Canonical atlas markdown path is fixed to:",
        "Canonical asset root for all protocol-owned artifact-family routing visuals is fixed to:",
        "do not scatter them across `docs/governance/`, `docs/review/`, `activity/evidence/`, or ad-hoc workspace folders",
        "The anti-scatter guarantee frozen by this atlas is limited to the `identity-protocol-local` repository surface.",
        "The atlas visualizes the six-layer interpretation model, the viability checklist, and the three-state upgrade-safety discipline",
        "`memory` is not a canonical protocol sink name and must never be rendered as a generic success-path bucket in these visuals.",
    ),
    index_required_markers=(
        "`docs/references/identity-protocol-artifact-family-routing-visual-atlas-v1.6.md`",
        "asset root: `docs/references/assets/identity-protocol-artifact-family-routing-visual-atlas/`",
    ),
    owner_doc_markers={
        V1618_GOV_DOC: (
            "docs/references/identity-protocol-artifact-family-routing-visual-atlas-v1.6.md",
            "docs/references/assets/identity-protocol-artifact-family-routing-visual-atlas/",
            "The canonical explanatory visual atlas for this stream is:",
            "This atlas explains the six-layer interpretation model, the family viability test, and the three-state upgrade-safety rule only.",
        ),
        V1618_REVIEW_DOC: (
            "docs/references/identity-protocol-artifact-family-routing-visual-atlas-v1.6.md",
            "docs/references/assets/identity-protocol-artifact-family-routing-visual-atlas/",
            "Audit accepts that atlas as discoverability-only explanatory SSOT for this stream, while normative truth remains the governance doc, protocol motherline, contract binding, and machine validators.",
        ),
    },
)


def main() -> int:
    return emit_visual_atlas_cli(
        CONFIG,
        description="Validate canonical artifact-family routing visual atlas SSOT/directory governance.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
