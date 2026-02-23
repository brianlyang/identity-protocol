#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from resolve_identity_context import default_local_catalog_path, load_yaml_or_empty


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _is_repo_path(path: str, repo_root: Path) -> bool:
    if not path:
        return False
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    return str(p).startswith(str(repo_root))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate local-instance persistence boundary (fixture/demo vs local runtime).")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--local-catalog", default=str(default_local_catalog_path()))
    ap.add_argument("--runtime-mode", action="store_true", help="enforce local catalog existence for runtime operations")
    args = ap.parse_args()

    repo_root = Path.cwd().resolve()
    repo_catalog = _load_yaml(Path(args.repo_catalog))
    local_catalog_path = Path(args.local_catalog).expanduser().resolve()
    local_catalog = load_yaml_or_empty(local_catalog_path)

    rc = 0
    repo_identities = [x for x in (repo_catalog.get("identities") or []) if isinstance(x, dict)]
    for item in repo_identities:
        iid = str(item.get("id", "")).strip()
        profile = str(item.get("profile", "fixture")).strip() or "fixture"
        runtime_mode = str(item.get("runtime_mode", "demo_only")).strip() or "demo_only"
        pack_path = str(item.get("pack_path", "")).strip()
        if profile != "fixture" and _is_repo_path(pack_path, repo_root):
            print(f"[FAIL] non-fixture identity is stored in repo path: id={iid} pack_path={pack_path}")
            rc = 1
        if profile == "runtime" and runtime_mode == "demo_only":
            print(f"[FAIL] runtime identity cannot be marked demo_only: id={iid}")
            rc = 1

    if args.runtime_mode:
        if not local_catalog_path.exists():
            print(f"[FAIL] runtime-mode requires local catalog: {local_catalog_path}")
            return 1

    local_identities = [x for x in (local_catalog.get("identities") or []) if isinstance(x, dict)]
    for item in local_identities:
        iid = str(item.get("id", "")).strip()
        profile = str(item.get("profile", "runtime")).strip() or "runtime"
        runtime_mode = str(item.get("runtime_mode", "local_only")).strip() or "local_only"
        pack_path = str(item.get("pack_path", "")).strip()
        if profile != "fixture" and _is_repo_path(pack_path, repo_root):
            print(f"[FAIL] local runtime identity points into repo path: id={iid} pack_path={pack_path}")
            rc = 1
        if profile == "runtime" and runtime_mode == "demo_only":
            print(f"[FAIL] local runtime identity cannot be demo_only: id={iid}")
            rc = 1

    if rc == 0:
        print("[OK] local persistence boundary validation passed")
        print(f"     repo_catalog={Path(args.repo_catalog)}")
        print(f"     local_catalog={local_catalog_path} exists={local_catalog_path.exists()}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
