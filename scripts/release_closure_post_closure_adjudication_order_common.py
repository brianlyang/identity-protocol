#!/usr/bin/env python3
from __future__ import annotations

from release_closure_surface_literal_canonicality_common import (
    collect_release_closure_surface_literal_stale_reasons,
)
from release_readiness_post_closure_adjudication_common import (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
)


def collect_release_closure_post_closure_adjudication_order_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_surface_literal_stale_reasons(
        text,
        label=label,
        literal_key="release_readiness_post_closure_adjudication_order",
        canonical_marker=RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
        stale_reason_suffix="post_closure_adjudication_order_line_not_canonical",
    )
