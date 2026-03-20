#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


COMPATIBILITY_MIRROR_POINTER_PATH_FIELD = "compatibility_mirror_pointer_path"
SESSION_POINTER_COMPATIBILITY_PATH_FIELD = "session_pointer_compatibility_path"
LEGACY_CANONICAL_POINTER_FIELD = "legacy_canonical_session_pointer"


def apply_compatibility_mirror_pointer_path(payload: dict, pointer_path: Path | str) -> dict:
    payload[COMPATIBILITY_MIRROR_POINTER_PATH_FIELD] = str(pointer_path)
    payload.pop("canonical_session_pointer", None)
    return payload
