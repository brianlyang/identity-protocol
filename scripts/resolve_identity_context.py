#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Literal

import yaml

ScopeName = Literal["EXPLICIT", "REPO", "USER", "ADMIN", "SYSTEM", "FALLBACK", "UNKNOWN"]


def _default_runtime_config_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        return (Path(codex_home).expanduser() / "identity" / "config" / "runtime-paths.env").resolve()
    return (Path.home() / ".codex" / "identity" / "config" / "runtime-paths.env").resolve()


def _load_runtime_env_defaults(config_path: Path | None = None) -> dict[str, str]:
    path = config_path or _default_runtime_config_path()
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        k = key.strip()
        v = val.strip().strip('"').strip("'")
        if k:
            out[k] = v
    return out


def _expand(path: str) -> Path:
    return Path(path).expanduser().resolve()


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


def _detect_repo_root(start: Path | None = None) -> Path:
    base = (start or Path.cwd()).resolve()
    out = _git(base, ["rev-parse", "--show-toplevel"])
    if out:
        return Path(out).expanduser().resolve()
    for parent in [base, *base.parents]:
        if (parent / ".git").exists():
            return parent.resolve()
    return base


def _default_user_identity_home() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        return (Path(codex_home).expanduser() / "identity").resolve()
    return (Path.home() / ".codex" / "identity").resolve()


def _default_repo_identity_home(start: Path | None = None) -> Path:
    return (_detect_repo_root(start) / ".agents" / "identity").resolve()


def _classify_scope_from_pack_path(
    pack_path: Path,
    *,
    repo_root: Path,
    user_root: Path,
    admin_root: Path,
) -> ScopeName:
    p = pack_path.expanduser().resolve()
    repo_scope_root = (repo_root / ".agents" / "identity").resolve()
    try:
        p.relative_to(repo_scope_root)
        return "REPO"
    except Exception:
        pass
    try:
        p.relative_to(user_root)
        return "USER"
    except Exception:
        pass
    try:
        p.relative_to(admin_root)
        return "ADMIN"
    except Exception:
        pass
    if str(p).startswith(str((repo_root / "identity").resolve())):
        return "SYSTEM"
    return "UNKNOWN"


def default_identity_home() -> Path:
    explicit_identity_home = os.environ.get("IDENTITY_HOME", "").strip()
    runtime_defaults = _load_runtime_env_defaults()
    configured_identity_home = runtime_defaults.get("IDENTITY_HOME", "").strip()

    if explicit_identity_home:
        raw = explicit_identity_home
    elif configured_identity_home:
        raw = configured_identity_home
    else:
        repo_home = _default_repo_identity_home()
        if repo_home.exists():
            raw = str(repo_home)
        else:
            raw = str(_default_user_identity_home())

    p = _expand(raw)
    try:
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        # Never fallback into protocol repo working tree; keep runtime data outside repo by default.
        fallback = (Path("/tmp") / "codex-identity-runtime" / os.environ.get("USER", "unknown")).resolve()
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def default_local_catalog_path(identity_home: Path | None = None) -> Path:
    home = identity_home or default_identity_home()
    return home / "catalog.local.yaml"


def default_local_instances_root(identity_home: Path | None = None) -> Path:
    home = identity_home or default_identity_home()
    canonical = home / "instances"
    singular_legacy = home / "identity"
    plural_legacy = home / "identities"
    legacy = home
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
    runtime_defaults = _load_runtime_env_defaults()
    configured = runtime_defaults.get("IDENTITY_PROTOCOL_HOME", "").strip()
    if explicit:
        p = _expand(explicit)
    elif configured:
        p = _expand(configured)
    else:
        p = Path.cwd().resolve()
    return p


def resolve_protocol_root(protocol_root: str | None = None) -> Path:
    if protocol_root:
        p = _expand(protocol_root)
    else:
        p = default_protocol_home()
    return p


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
    *,
    preferred_scope: str = "",
    allow_conflict: bool = False,
) -> dict[str, Any]:
    repo_catalog = load_yaml_or_empty(repo_catalog_path)
    local_catalog = load_yaml_or_empty(local_catalog_path)
    repo_rows = [x for x in (repo_catalog.get("identities") or []) if isinstance(x, dict)]
    local_rows = [x for x in (local_catalog.get("identities") or []) if isinstance(x, dict)]

    repo_identity = next((x for x in repo_rows if str(x.get("id", "")).strip() == identity_id), None)
    local_identity = next((x for x in local_rows if str(x.get("id", "")).strip() == identity_id), None)
    if not repo_identity and not local_identity:
        raise FileNotFoundError(f"identity not found in merged context: {identity_id}")

    repo_root = _detect_repo_root(repo_catalog_path.parent)
    user_root = _default_user_identity_home()
    admin_root = Path("/etc/codex/identity").resolve()

    candidates: list[dict[str, Any]] = []
    for source_layer, row, catalog_path in (
        ("local", local_identity, local_catalog_path),
        ("repo", repo_identity, repo_catalog_path),
    ):
        if not row:
            continue
        pack_raw = str((row or {}).get("pack_path", "")).strip()
        if not pack_raw:
            continue
        pack = Path(pack_raw).expanduser().resolve()
        profile = str((row or {}).get("profile", "")).strip().lower()
        runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
        if profile == "fixture" or runtime_mode == "demo_only":
            scope: ScopeName = "SYSTEM"
        else:
            scope = _classify_scope_from_pack_path(pack, repo_root=repo_root, user_root=user_root, admin_root=admin_root)
            # P0: avoid UNKNOWN scope entering runtime upgrade chain.
            # For local-catalog identities, UNKNOWN is coerced to USER semantics.
            if source_layer == "local" and scope == "UNKNOWN":
                scope = "USER"

        candidates.append(
            {
                "source_layer": source_layer,
                "catalog_path": str(catalog_path),
                "pack_path": str(pack),
                "status": str((row or {}).get("status", "")).strip(),
                "profile": str((row or {}).get("profile", "")).strip(),
                "runtime_mode": str((row or {}).get("runtime_mode", "")).strip(),
                "scope": scope,
            }
        )

    if not candidates:
        raise FileNotFoundError(f"identity found but pack_path missing: {identity_id}")

    canonical_paths = sorted({c["pack_path"] for c in candidates})
    conflict_detected = len(canonical_paths) > 1

    requested_scope = preferred_scope.strip().upper()
    chosen: dict[str, Any] | None = None
    if requested_scope:
        chosen = next((c for c in candidates if str(c.get("scope", "")).upper() == requested_scope), None)
        if not chosen:
            raise RuntimeError(
                f"scope mismatch for identity={identity_id}: requested={requested_scope}, "
                f"available={[c.get('scope') for c in candidates]}"
            )
    elif not conflict_detected:
        chosen = candidates[0]
    else:
        chosen = next((c for c in candidates if c.get("source_layer") == "local"), candidates[0])
        if not allow_conflict:
            raise RuntimeError(
                f"identity conflict detected for {identity_id}: multiple pack paths resolved={canonical_paths}. "
                "Pass --scope to arbitrate explicitly."
            )

    assert chosen is not None
    source_layer = str(chosen.get("source_layer", "")).strip() or "repo"
    return {
        "identity_id": identity_id,
        "source_layer": source_layer,
        "catalog_path": str(chosen.get("catalog_path", "")),
        "pack_path": str(chosen.get("pack_path", "")),
        "status": str(chosen.get("status", "")).strip(),
        "profile": str(chosen.get("profile", "")).strip() or ("fixture" if source_layer == "repo" else "runtime"),
        "runtime_mode": str(chosen.get("runtime_mode", "")).strip()
        or ("demo_only" if source_layer == "repo" else "local_only"),
        "resolved_scope": str(chosen.get("scope", "UNKNOWN")),
        "resolved_pack_path": str(chosen.get("pack_path", "")),
        "conflict_detected": conflict_detected,
        "candidate_matches": candidates,
    }


def _cmd_resolve(args: argparse.Namespace) -> int:
    repo_catalog = _expand(args.repo_catalog)
    local_catalog = _expand(args.local_catalog)
    if args.ensure_local_catalog:
        ensure_local_catalog(repo_catalog, local_catalog)
    ctx = resolve_identity(
        args.identity_id,
        repo_catalog,
        local_catalog,
        preferred_scope=args.scope,
        allow_conflict=args.allow_conflict,
    )
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
    c1.add_argument("--scope", default="", help="optional explicit scope arbitration: REPO/USER/ADMIN/SYSTEM")
    c1.add_argument("--allow-conflict", action="store_true", help="allow conflict and pick preferred runtime layer")
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
