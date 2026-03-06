#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

_TOKEN_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def _slug(value: str, *, fallback: str) -> str:
    token = _TOKEN_RE.sub("-", str(value or "").strip()).strip("-._")
    return token or fallback


def runtime_temp_root() -> Path:
    for key in ("IDENTITY_RUNTIME_TMP_ROOT", "RUNNER_TEMP", "TMPDIR", "TEMP", "TMP"):
        raw = str(os.environ.get(key, "")).strip()
        if raw:
            root = Path(raw).expanduser().resolve()
            root.mkdir(parents=True, exist_ok=True)
            return root
    root = Path(tempfile.gettempdir()).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def runtime_temp_dir(*, channel: str, operation: str = "general", identity_id: str = "shared", run_token: str = "") -> Path:
    base = (
        runtime_temp_root()
        / "identity-runtime"
        / _slug(channel, fallback="channel")
        / _slug(operation, fallback="operation")
        / _slug(identity_id, fallback="identity")
    )
    if str(run_token or "").strip():
        base = base / _slug(run_token, fallback="run")
    base.mkdir(parents=True, exist_ok=True)
    return base


def runtime_temp_file(
    *,
    channel: str,
    operation: str,
    identity_id: str,
    stem: str,
    ext: str,
    run_token: str = "",
) -> Path:
    suffix = str(ext or "").strip()
    if suffix and not suffix.startswith("."):
        suffix = f".{suffix}"
    filename = f"{_slug(stem, fallback='artifact')}{suffix}"
    return runtime_temp_dir(
        channel=channel,
        operation=operation,
        identity_id=identity_id,
        run_token=run_token,
    ) / filename


def named_temp_root(name: str) -> Path:
    root = runtime_temp_root() / _slug(name, fallback="runtime-temp")
    root.mkdir(parents=True, exist_ok=True)
    return root
