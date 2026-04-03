#!/usr/bin/env python3
from __future__ import annotations

from reference_visual_atlas_governance_common import (
    VisualAtlasConfig,
    emit_visual_atlas_cli,
)

CANONICAL_ATLAS_DOC = "docs/references/identity-protocol-breakthrough-sequence-visual-atlas-v1.6.md"
CANONICAL_ASSET_ROOT = "docs/references/assets/identity-protocol-breakthrough-sequence-visual-atlas"
ATLAS_DOC = "docs/references/identity-protocol-breakthrough-sequence-visual-atlas-v1.6.md"
ATLAS_ASSET_ROOT = "docs/references/assets/identity-protocol-breakthrough-sequence-visual-atlas/"

CONFIG = VisualAtlasConfig(
    status_key="breakthrough_sequence_visual_atlas_governance_status",
    error_code="IP-BSEQ-ATLAS-001",
    canonical_doc=CANONICAL_ATLAS_DOC,
    canonical_asset_root=CANONICAL_ASSET_ROOT,
    required_svg_files=(
        "identity_protocol_breakthrough_sequence_v16x.svg",
    ),
    svg_family_pattern=r"^(identity_protocol_breakthrough_sequence)_v[0-9A-Za-z.]+\.svg$",
    atlas_doc_pattern=r"^identity-protocol-breakthrough-sequence-visual-atlas-v[0-9.]+\.md$",
    atlas_required_markers=(
        "Status: Active canonical visual reference for the frozen breakthrough sequence from headstamp to cross-context launcher continuity closure.",
        "Classification: protocol-owned explanatory atlas; not a normative contract source.",
        "Canonical atlas markdown path is fixed to:",
        "Canonical asset root for all protocol-owned breakthrough sequence visuals is fixed to:",
        "do not scatter them across `docs/governance/`, `docs/review/`, `activity/evidence/`, or ad-hoc workspace folders",
        "The anti-scatter guarantee frozen by this atlas is limited to the `identity-protocol-local` repository surface.",
        "First real break was headstamp / machine-verification rather than launcher convenience.",
        "Breakthrough order for this atlas is fixed to: headstamp / machine-verification -> runtime authority / source-of-truth -> launcher command surface -> governed continuity runtime proof -> cross-context stable short-command closure.",
        "`v1.6.18` artifact-family routing now acts as a stabilizer that prevents the continuity/reentry layer from collapsing back into a generic `memory` bucket.",
        "No diagram in this atlas may introduce backward compatibility, backstop, downgrade, lagging-pack shortcut, hardcoded thread identifiers, or undeclared rescue semantics.",
    ),
    index_required_markers=(
        "`docs/references/identity-protocol-breakthrough-sequence-visual-atlas-v1.6.md`",
        "asset root: `docs/references/assets/identity-protocol-breakthrough-sequence-visual-atlas/`",
    ),
    owner_doc_markers={
        "docs/governance/identity-headstamp-egress-governance-v1.6.1.md": (
            ATLAS_DOC,
            ATLAS_ASSET_ROOT,
            "The canonical explanatory visual atlas for this stream is:",
        ),
        "docs/review/protocol-remediation-audit-ledger-v1.6.1-headstamp.md": (
            ATLAS_DOC,
            ATLAS_ASSET_ROOT,
            "The canonical explanatory visual atlas for this stream is:",
        ),
        "docs/governance/identity-codex-launcher-governance-v1.6.14.md": (
            ATLAS_DOC,
            ATLAS_ASSET_ROOT,
            "The canonical explanatory visual atlas for this stream is:",
        ),
        "docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md": (
            ATLAS_DOC,
            ATLAS_ASSET_ROOT,
            "The canonical explanatory visual atlas for this stream is:",
        ),
        "docs/governance/identity-context-continuity-governance-v1.6.16.md": (
            ATLAS_DOC,
            ATLAS_ASSET_ROOT,
            "The canonical explanatory visual atlas for this stream is:",
        ),
        "docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md": (
            ATLAS_DOC,
            ATLAS_ASSET_ROOT,
            "The canonical explanatory visual atlas for this stream is:",
        ),
        "docs/governance/identity-artifact-family-routing-governance-v1.6.18.md": (
            ATLAS_DOC,
            ATLAS_ASSET_ROOT,
            "The canonical explanatory visual atlas for this stream is:",
        ),
        "docs/review/protocol-remediation-audit-ledger-v1.6.18-artifact-family-routing.md": (
            ATLAS_DOC,
            ATLAS_ASSET_ROOT,
            "The canonical explanatory visual atlas for this stream is:",
        ),
    },
)


def main() -> int:
    return emit_visual_atlas_cli(
        CONFIG,
        description="Validate canonical breakthrough-sequence visual atlas SSOT/directory governance.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
