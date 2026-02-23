#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from resolve_identity_context import default_identity_home, default_local_catalog_path, default_local_instances_root


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _repo_abs(repo_root: Path, p: str) -> Path:
    pp = Path(p).expanduser()
    if pp.is_absolute():
        return pp.resolve()
    return (repo_root / pp).resolve()


def main() -> int:
    identity_home = default_identity_home()
    ap = argparse.ArgumentParser(description="Migrate non-fixture repo instances to local IDENTITY_HOME.")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--local-catalog", default=str(default_local_catalog_path(identity_home)))
    ap.add_argument("--target-root", default=str(default_local_instances_root(identity_home)))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    repo_root = Path.cwd().resolve()
    repo_catalog = _load_yaml(Path(args.repo_catalog))
    local_catalog_path = Path(args.local_catalog).expanduser().resolve()
    target_root = Path(args.target_root).expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    local_catalog = {
        "version": str(repo_catalog.get("version") or "1.0"),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "default_identity": "",
        "identities": [],
    }
    if local_catalog_path.exists():
        local_catalog = _load_yaml(local_catalog_path)
        local_catalog.setdefault("identities", [])
        local_catalog.setdefault("default_identity", "")

    identities = [x for x in (repo_catalog.get("identities") or []) if isinstance(x, dict)]
    migrated: list[dict[str, Any]] = []
    rollback_map: dict[str, Any] = {"moved": []}
    for item in identities:
        iid = str(item.get("id", "")).strip()
        if not iid:
            continue
        profile = str(item.get("profile", "fixture")).strip() or "fixture"
        if profile == "fixture":
            continue
        pack_abs = _repo_abs(repo_root, str(item.get("pack_path", "")).strip())
        if not str(pack_abs).startswith(str(repo_root)):
            continue
        dst = target_root / iid
        row = dict(item)
        row["pack_path"] = str(dst)
        row["profile"] = "runtime"
        row["runtime_mode"] = "local_only"
        migrated.append(row)
        rollback_map["moved"].append({"id": iid, "from": str(pack_abs), "to": str(dst)})
        if args.apply:
            if pack_abs.exists() and pack_abs.is_dir() and not dst.exists():
                shutil.copytree(pack_abs, dst)
            elif pack_abs.exists() and pack_abs.is_dir():
                shutil.copytree(pack_abs, dst, dirs_exist_ok=True)

    if migrated:
        existing = {str(x.get("id", "")).strip(): x for x in (local_catalog.get("identities") or []) if isinstance(x, dict)}
        for row in migrated:
            existing[str(row.get("id", "")).strip()] = row
        local_catalog["identities"] = list(existing.values())

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_dir = identity_home / "reports"
    report = {
        "migration_id": f"repo-to-local-{ts}",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo_catalog": str(Path(args.repo_catalog)),
        "local_catalog": str(local_catalog_path),
        "target_root": str(target_root),
        "migrated_count": len(migrated),
        "migrated_identities": [x.get("id") for x in migrated],
    }
    rollback_path = report_dir / f"migration-rollback-map-{ts}.json"
    report_path = report_dir / f"migration-report-{ts}.json"

    if args.apply:
        _dump_yaml(local_catalog_path, local_catalog)
        _write_json(rollback_path, rollback_map)
        _write_json(report_path, report)
        print(f"[OK] migration applied; local catalog updated: {local_catalog_path}")
        print(f"report={report_path}")
        print(f"rollback_map={rollback_path}")
    else:
        print("[INFO] dry-run only; no files changed")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(json.dumps(rollback_map, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
