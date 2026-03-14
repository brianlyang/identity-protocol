#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any

REQUIREMENT_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*-rq-\d{3}$")
REQUIREMENT_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]*-RQ-\d{3}$")
STREAM_VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")


def is_requirement_key(value: str) -> bool:
    token = str(value or "").strip().lower()
    return bool(token and REQUIREMENT_KEY_RE.fullmatch(token))


def is_requirement_id(value: str) -> bool:
    token = str(value or "").strip().upper()
    return bool(token and REQUIREMENT_ID_RE.fullmatch(token))


def is_stream_version(value: str) -> bool:
    token = str(value or "").strip()
    return bool(token and STREAM_VERSION_RE.fullmatch(token))


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        token = str(item or "").strip()
        if token:
            out.append(token)
    return out


def collect_requirement_rows(mapping_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not isinstance(mapping_doc, dict):
        return rows
    for key, value in mapping_doc.items():
        if key == "_meta" or not isinstance(value, dict):
            continue
        requirement_key = str(key or "").strip()
        requirement_id = str(value.get("requirement_id", "") or "").strip()
        if is_requirement_key(requirement_key) or is_requirement_id(requirement_id):
            rows[requirement_key] = value
    return rows


def requirement_row_keys(mapping_doc: dict[str, Any]) -> list[str]:
    return sorted(collect_requirement_rows(mapping_doc).keys())


def requirement_id_to_key(mapping_doc: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for requirement_key, row in collect_requirement_rows(mapping_doc).items():
        requirement_id = str(row.get("requirement_id", "") or "").strip().upper()
        if requirement_id:
            out[requirement_id] = requirement_key
    return out


def requirement_keys_by_surface(mapping_doc: dict[str, Any], *, surface: str) -> list[str]:
    needle = str(surface or "").strip()
    if not needle:
        return []
    out: list[str] = []
    for requirement_key, row in collect_requirement_rows(mapping_doc).items():
        gates = _as_str_list(row.get("gate_surfaces"))
        if needle in gates or "*" in gates:
            out.append(requirement_key)
    return sorted(out)
