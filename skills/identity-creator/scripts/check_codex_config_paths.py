#!/usr/bin/env python3
"""Check .codex/config.toml relative path resolution for model instructions and skills."""

from __future__ import annotations

import pathlib
import sys
import tomllib


def main() -> int:
    cfg_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".codex/config.toml")
    if not cfg_path.exists():
        print(f"[FAIL] config not found: {cfg_path}")
        return 1

    cfg_base = cfg_path.parent
    with cfg_path.open("rb") as f:
        cfg = tomllib.load(f)

    failed = False

    def check_path(label: str, rel: str) -> None:
        nonlocal failed
        p = (cfg_base / rel).resolve()
        exists = p.exists()
        mark = "OK" if exists else "FAIL"
        print(f"[{mark}] {label}: {rel} -> {p}")
        if not exists:
            failed = True

    mi = cfg.get("model_instructions_file")
    if isinstance(mi, str):
        check_path("model_instructions_file", mi)
    else:
        print("[WARN] model_instructions_file missing")

    skills_cfg = cfg.get("skills", {}).get("config", [])
    if isinstance(skills_cfg, list):
        for idx, item in enumerate(skills_cfg, start=1):
            sp = item.get("path") if isinstance(item, dict) else None
            if isinstance(sp, str):
                check_path(f"skills.config[{idx}].path", sp)
            else:
                print(f"[WARN] skills.config[{idx}] missing path")
    else:
        print("[WARN] skills.config not found")

    if failed:
        print("\nPath check FAILED. Fix paths relative to .codex/config.toml directory.")
        return 1

    print("\nPath check PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
