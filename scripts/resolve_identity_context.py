#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml


def _expand(path: str) -> Path:
    return Path(path).expanduser().resolve()


def default_identity_home() -> Path:
    explicit_identity_home = os.environ.get("IDENTITY_HOME", "").strip()
    if explicit_identity_home:
        raw = explicit_identity_home
    else:
        codex_home = os.environ.get("CODEX_HOME", "").strip()
        if codex_home:
            raw = str(Path(codex_home).expanduser() / "identity")
        else:
            raw = "~/.codex/identity"
    p = _expand(raw)
    try:
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        fallback = (Path.cwd() / ".codex" / "identity").resolve()
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def default_local_catalog_path(identity_home: Path | None = None) -> Path:
    home = identity_home or default_identity_home()
    return home / "catalog.local.yaml"


def default_local_instances_root(identity_home: Path | None = None) -> Path:
    home = identity_home or default_identity_home()
    canonical = home
    singular_legacy = home / "identity"
    plural_legacy = home / "identities"
    legacy = home / "instances"
    if canonical.exists():
        return canonical
    if singular_legacy.exists():
        return singular_legacy
    if plural_legacy.exists():
        return plural_legacy
    if legacy.exists():
        return legacy
    return canonical


def default_protocol_home() -> Path:
    explicit = os.environ.get("IDENTITY_PROTOCOL_HOME", "").strip()
    if explicit:
        p = _expand(explicit)
    else:
        p = Path.cwd().resolve()
    return p


def resolve_protocol_root(protocol_root: str | None = None) -> Path:
    if protocol_root:
        p = _expand(protocol_root)
    else:
        p = default_protocol_home()
    return p


def _git(path: Path, args: list[str]) -> str:
    try:
        p = subprocess.run(
            ["git", *args],
            cwd=str(path),
            capture_output=True,
            text=True,
            check=False,
        )
        if p.returncode != 0:
            return ""
        return (p.stdout or "").strip()
    except Exception:
        return ""


def collect_protocol_evidence(protocol_root: str | None = None, protocol_mode: str = "mode_a_shared") -> dict[str, str]:
    root = resolve_protocol_root(protocol_root)
    commit = _git(root, ["rev-parse", "HEAD"])
    ref = _git(root, ["describe", "--tags", "--always", "--dirty"])
    return {
        "protocol_mode": str(protocol_mode or "").strip() or "mode_a_shared",
        "protocol_root": str(root),
        "protocol_commit_sha": commit,
        "protocol_ref": ref,
    }


def load_yaml_or_empty(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def merged_catalog(repo_catalog_path: Path, local_catalog_path: Path) -> dict[str, Any]:
    repo = load_yaml_or_empty(repo_catalog_path)
    local = load_yaml_or_empty(local_catalog_path)

    repo_identities = [x for x in (repo.get("identities") or []) if isinstance(x, dict)]
    local_identities = [x for x in (local.get("identities") or []) if isinstance(x, dict)]

    by_id: dict[str, dict[str, Any]] = {}
    for item in repo_identities:
        iid = str(item.get("id", "")).strip()
        if iid:
            d = dict(item)
            d["_source_layer"] = "repo"
            by_id[iid] = d
    for item in local_identities:
        iid = str(item.get("id", "")).strip()
        if iid:
            d = dict(item)
            d["_source_layer"] = "local"
            by_id[iid] = d

    default_identity = str(local.get("default_identity", "") or "").strip() or str(
        repo.get("default_identity", "") or ""
    ).strip()

    return {
        "version": str(local.get("version") or repo.get("version") or "1.0"),
        "updated_at": str(local.get("updated_at") or repo.get("updated_at") or ""),
        "default_identity": default_identity,
        "identities": list(by_id.values()),
        "_repo_catalog_path": str(repo_catalog_path),
        "_local_catalog_path": str(local_catalog_path),
    }


def ensure_local_catalog(repo_catalog_path: Path, local_catalog_path: Path) -> dict[str, Any]:
    local = load_yaml_or_empty(local_catalog_path)
    if local.get("identities"):
        return local
    repo = load_yaml_or_empty(repo_catalog_path)
    seed = {
        "version": str(repo.get("version") or "1.0"),
        "updated_at": str(repo.get("updated_at") or ""),
        "default_identity": "",
        "identities": [dict(x) for x in (repo.get("identities") or []) if isinstance(x, dict)],
    }
    dump_yaml(local_catalog_path, seed)
    return seed


def resolve_identity(
    identity_id: str,
    repo_catalog_path: Path,
    local_catalog_path: Path,
) -> dict[str, Any]:
    merged = merged_catalog(repo_catalog_path, local_catalog_path)
    identity = next(
        (x for x in merged.get("identities", []) if str((x or {}).get("id", "")).strip() == identity_id),
        None,
    )
    if not identity:
        raise FileNotFoundError(f"identity not found in merged context: {identity_id}")
    source_layer = str(identity.get("_source_layer", "")).strip() or "repo"
    pack_path = str(identity.get("pack_path", "")).strip()
    return {
        "identity_id": identity_id,
        "source_layer": source_layer,
        "catalog_path": str(local_catalog_path if source_layer == "local" else repo_catalog_path),
        "pack_path": pack_path,
        "status": str(identity.get("status", "")).strip(),
        "profile": str(identity.get("profile", "")).strip() or ("fixture" if source_layer == "repo" else "runtime"),
        "runtime_mode": str(identity.get("runtime_mode", "")).strip()
        or ("demo_only" if source_layer == "repo" else "local_only"),
    }


def _cmd_resolve(args: argparse.Namespace) -> int:
    repo_catalog = _expand(args.repo_catalog)
    local_catalog = _expand(args.local_catalog)
    if args.ensure_local_catalog:
        ensure_local_catalog(repo_catalog, local_catalog)
    ctx = resolve_identity(args.identity_id, repo_catalog, local_catalog)
    print(json.dumps(ctx, ensure_ascii=False, indent=2))
    return 0


def _cmd_merge(args: argparse.Namespace) -> int:
    repo_catalog = _expand(args.repo_catalog)
    local_catalog = _expand(args.local_catalog)
    if args.ensure_local_catalog:
        ensure_local_catalog(repo_catalog, local_catalog)
    out = merged_catalog(repo_catalog, local_catalog)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    identity_home = default_identity_home()
    default_local_catalog = default_local_catalog_path(identity_home)
    ap = argparse.ArgumentParser(description="Resolve identity context across repo catalog and local catalog.")
    sub = ap.add_subparsers(dest="command", required=True)

    c1 = sub.add_parser("resolve", help="Resolve an identity from merged catalog context.")
    c1.add_argument("--identity-id", required=True)
    c1.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    c1.add_argument("--local-catalog", default=str(default_local_catalog))
    c1.add_argument("--ensure-local-catalog", action="store_true")
    c1.set_defaults(func=_cmd_resolve)

    c2 = sub.add_parser("merge", help="Dump merged catalog (local overrides repo).")
    c2.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    c2.add_argument("--local-catalog", default=str(default_local_catalog))
    c2.add_argument("--ensure-local-catalog", action="store_true")
    c2.set_defaults(func=_cmd_merge)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
