#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def identity_runtime_temp_root() -> Path:
    for key in ("IDENTITY_RUNTIME_TMP_ROOT", "RUNNER_TEMP", "TMPDIR", "TEMP", "TMP"):
        raw = str(os.environ.get(key, "")).strip()
        if raw:
            root = Path(raw).expanduser().resolve()
            root.mkdir(parents=True, exist_ok=True)
            return root
    root = Path(tempfile.gettempdir()).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def identity_runtime_slug(value: str, *, default: str = "runtime-temp") -> str:
    raw = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in str(value or "").strip())
    raw = raw.strip("-._")
    return raw or default


def identity_runtime_named_temp_root(name: str) -> Path:
    root = identity_runtime_temp_root() / "identity-runtime" / identity_runtime_slug(name)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def identity_runtime_mkdtemp(name: str, *, prefix: str = "run") -> Path:
    base = identity_runtime_named_temp_root(name)
    path = Path(tempfile.mkdtemp(prefix=f"{identity_runtime_slug(prefix)}.", dir=str(base))).resolve()
    return path


def runtime_temp_root() -> Path:
    return identity_runtime_temp_root()


def named_temp_root(name: str) -> Path:
    return identity_runtime_named_temp_root(name)


def _compose_runtime_channel(
    name: str = "",
    *,
    channel: str = "",
    operation: str = "",
    identity_id: str = "",
) -> str:
    if str(name or "").strip():
        return str(name).strip()
    parts = [str(channel or "").strip(), str(operation or "").strip(), str(identity_id or "").strip()]
    return "-".join(part for part in parts if part) or "runtime-temp"


def runtime_temp_dir(
    name: str = "",
    *,
    channel: str = "",
    operation: str = "",
    identity_id: str = "",
    run_token: str = "",
    prefix: str = "run",
) -> Path:
    resolved_name = _compose_runtime_channel(name, channel=channel, operation=operation, identity_id=identity_id)
    resolved_prefix = str(run_token or "").strip() or prefix
    return identity_runtime_mkdtemp(resolved_name, prefix=resolved_prefix)


def runtime_temp_file(
    name: str = "",
    filename: str = "",
    *,
    channel: str = "",
    operation: str = "",
    identity_id: str = "",
    run_token: str = "",
    stem: str = "",
    ext: str = "",
) -> Path:
    resolved_name = _compose_runtime_channel(name, channel=channel, operation=operation, identity_id=identity_id)
    root = identity_runtime_named_temp_root(resolved_name)
    resolved_stem = str(stem or filename or "artifact").strip()
    resolved_ext = str(ext or "").strip().lstrip(".")
    suffix = f".{resolved_ext}" if resolved_ext else ""
    token = str(run_token or "").strip()
    file_name = identity_runtime_slug(f"{resolved_stem}-{token}" if token else resolved_stem, default="artifact") + suffix
    path = (root / file_name).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
