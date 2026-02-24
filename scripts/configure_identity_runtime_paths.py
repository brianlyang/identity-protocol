#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path


def _default_codex_home() -> Path:
    raw = os.environ.get("CODEX_HOME", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def _default_identity_home() -> Path:
    explicit = os.environ.get("IDENTITY_HOME", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (_default_codex_home() / "identity").resolve()


def _default_protocol_home() -> Path:
    explicit = os.environ.get("IDENTITY_PROTOCOL_HOME", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path.cwd().resolve()


def main() -> int:
    ap = argparse.ArgumentParser(description="Write shared runtime path config for identity protocol tooling.")
    ap.add_argument("--identity-home", default=str(_default_identity_home()))
    ap.add_argument("--protocol-home", default=str(_default_protocol_home()))
    ap.add_argument("--config-path", default=str(_default_identity_home() / "config" / "runtime-paths.env"))
    args = ap.parse_args()

    config_path = Path(args.config_path).expanduser().resolve()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    payload = (
        "# identity runtime shared path config\n"
        "# priority: environment variable > this file > built-in fallback\n"
        f"IDENTITY_HOME={Path(args.identity_home).expanduser().resolve()}\n"
        f"IDENTITY_PROTOCOL_HOME={Path(args.protocol_home).expanduser().resolve()}\n"
    )
    config_path.write_text(payload, encoding="utf-8")
    print(f"[OK] wrote runtime path config: {config_path}")
    print(payload.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
