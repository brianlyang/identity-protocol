#!/usr/bin/env python3
from __future__ import annotations

from reference_visual_atlas_governance_common import (
    VisualAtlasConfig,
    emit_visual_atlas_cli,
)

CANONICAL_ATLAS_DOC = "${canonical_doc_rel}"
CANONICAL_ASSET_ROOT = "${canonical_asset_root_rel}"

CONFIG = VisualAtlasConfig(
    status_key="${status_key}",
    error_code="${error_code}",
    canonical_doc=CANONICAL_ATLAS_DOC,
    canonical_asset_root=CANONICAL_ASSET_ROOT,
    required_svg_files=(
${required_svg_files_py}
    ),
    svg_family_pattern=r"${svg_family_pattern}",
    atlas_doc_pattern=r"${atlas_doc_pattern}",
    atlas_required_markers=(
${atlas_required_markers_py}
    ),
    index_required_markers=(
${index_required_markers_py}
    ),
    owner_doc_markers={
${owner_doc_markers_py}
    },
)


def main() -> int:
    return emit_visual_atlas_cli(
        CONFIG,
        description="Validate canonical visual atlas SSOT/directory governance.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
