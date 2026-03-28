#!/usr/bin/env python3
from __future__ import annotations

from release_readiness_one_look_topology_common import (
    apply_release_readiness_one_look_families,
)


def build_release_readiness_one_look_projection(summary: dict[str, object]) -> dict[str, object]:
    one_look: dict[str, object] = {}
    apply_release_readiness_one_look_families(summary, one_look)
    return one_look
