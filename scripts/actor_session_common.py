#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


def resolve_actor_id(explicit_actor_id: str = "") -> str:
    actor = str(explicit_actor_id or "").strip()
    if actor:
        return actor
    env_actor = str(os.environ.get("CODEX_ACTOR_ID", "")).strip()
    if env_actor:
        return env_actor
    user = str(os.environ.get("USER", "unknown")).strip() or "unknown"
    return f"user:{user}"


def actor_session_dir(catalog_path: Path) -> Path:
    return (catalog_path.parent / "session" / "actors").resolve()


def actor_session_filename(actor_id: str) -> str:
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", str(actor_id or "").strip()).strip("._")
    if not token:
        token = "unknown_actor"
    return f"{token}.json"


def actor_session_path(catalog_path: Path, actor_id: str) -> Path:
    return (actor_session_dir(catalog_path) / actor_session_filename(actor_id)).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def load_actor_binding(catalog_path: Path, actor_id: str) -> dict[str, Any]:
    p = actor_session_path(catalog_path, actor_id)
    if not p.exists():
        return {}
    data = _load_json(p)
    if data:
        data["actor_session_path"] = str(p)
    return data


def list_actor_bindings(catalog_path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    root = actor_session_dir(catalog_path)
    if not root.exists():
        return out
    for p in sorted(root.glob("*.json")):
        data = _load_json(p)
        if not data:
            continue
        data["actor_session_path"] = str(p.resolve())
        out.append(data)
    return out

