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
PROJECT_RUNTIME_FORCED_ENV_SOURCE = "project_runtime_forced"


def _default_runtime_config_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        return (Path(codex_home).expanduser() / ".identity" / "config" / "runtime-paths.env").resolve()
    return (Path.home() / ".codex" / ".identity" / "config" / "runtime-paths.env").resolve()


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


def _normalize_anchor(path: Path | None = None) -> Path:
    anchor = (path or Path.cwd()).expanduser().resolve()
    if anchor.is_file():
        anchor = anchor.parent
    return anchor


def _workspace_root_from_repo_root(repo_root: Path) -> Path:
    resolved = repo_root.expanduser().resolve()
    if resolved.name == "identity-protocol-local":
        return resolved.parent.resolve()
    return resolved


def _runtime_resolution_base(start: Path | None = None) -> Path:
    anchor = _normalize_anchor(start)
    cwd = Path.cwd().resolve()
    repo_root = _detect_repo_root(anchor)
    workspace_root = _workspace_root_from_repo_root(repo_root)
    if _within(cwd, workspace_root):
        return anchor
    return cwd


def _detect_repo_root(start: Path | None = None) -> Path:
    base = _normalize_anchor(start)
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
        return (Path(codex_home).expanduser() / ".identity").resolve()
    return (Path.home() / ".codex" / ".identity").resolve()


def _default_repo_identity_home(start: Path | None = None) -> Path:
    repo_root = _detect_repo_root(_runtime_resolution_base(start))
    if repo_root.name == "identity-protocol-local":
        return (repo_root.parent / ".identity").resolve()
    return (repo_root / ".identity").resolve()


def _project_identity_home_from_repo_catalog(repo_root: Path, repo_catalog_path: Path | None = None) -> Path:
    if repo_catalog_path is not None:
        try:
            repo_catalog = repo_catalog_path.expanduser().resolve()
            # canonical repo catalog: <protocol_root>/identity/catalog/identities.yaml
            if repo_catalog.parent.name == "catalog" and repo_catalog.parent.parent.name == "identity":
                protocol_root = repo_catalog.parent.parent.parent.resolve()
                if protocol_root.name == "identity-protocol-local":
                    return (protocol_root.parent / ".identity").resolve()
                return (protocol_root / ".identity").resolve()
        except Exception:
            pass
    return _default_repo_identity_home(repo_root)


def _runtime_identity_home_from_catalog(catalog_path: Path) -> Path | None:
    resolved = catalog_path.expanduser().resolve()
    if resolved.name == "catalog.local.yaml" and resolved.parent.name == ".identity":
        return resolved.parent.resolve()
    return None


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _project_runtime_env_source() -> str:
    return str(os.environ.get("IDENTITY_ENV_SOURCE", "")).strip().lower()


def _session_pointer_exists(identity_home: Path) -> bool:
    for candidate in (
        identity_home / "session" / "active_identity.json",
        identity_home / "session" / "mirror" / "current.json",
    ):
        if candidate.exists():
            return True
    return False


def _guard_forced_project_identity_home(candidate: Path, *, start: Path | None = None) -> Path:
    if _project_runtime_env_source() != PROJECT_RUNTIME_FORCED_ENV_SOURCE:
        return candidate
    current_repo_home = _default_repo_identity_home(start)
    cwd = (start or Path.cwd()).resolve()
    if candidate == current_repo_home:
        return candidate
    if candidate.name == ".identity" and _within(cwd, candidate.parent):
        return candidate
    if _session_pointer_exists(current_repo_home):
        return current_repo_home
    return _default_user_identity_home()


def _guard_forced_project_local_catalog_path(candidate: Path, *, start: Path | None = None) -> Path:
    if _project_runtime_env_source() != PROJECT_RUNTIME_FORCED_ENV_SOURCE:
        return candidate
    current_repo_home = _default_repo_identity_home(start)
    current_repo_catalog = (current_repo_home / "catalog.local.yaml").resolve()
    cwd = Path.cwd().resolve()
    if candidate == current_repo_catalog:
        return candidate
    if candidate.name == "catalog.local.yaml" and candidate.parent.name == ".identity" and _within(
        cwd, candidate.parent.parent
    ):
        return candidate
    if _session_pointer_exists(current_repo_home):
        return current_repo_catalog
    return (_default_user_identity_home() / "catalog.local.yaml").resolve()


def _default_protocol_home_fallback(start: Path | None = None) -> Path:
    base = _runtime_resolution_base(start)
    repo_root = _detect_repo_root(base)
    if repo_root.name == "identity-protocol-local":
        return repo_root.resolve()
    nested = (repo_root / "identity-protocol-local").resolve()
    if nested.exists():
        return nested
    return base


def _guard_forced_project_protocol_home(candidate: Path, *, start: Path | None = None) -> Path:
    if _project_runtime_env_source() != PROJECT_RUNTIME_FORCED_ENV_SOURCE:
        return candidate
    fallback = _default_protocol_home_fallback(start)
    cwd = (start or Path.cwd()).resolve()
    if candidate == fallback:
        return candidate
    if candidate.name == "identity-protocol-local" and _within(cwd, candidate.parent):
        return candidate
    if _within(cwd, candidate):
        return candidate
    return fallback


def _classify_catalog_source_layer(
    catalog_path: Path,
    *,
    repo_root: Path,
    user_root: Path,
    repo_catalog_path: Path,
) -> str:
    c = catalog_path.expanduser().resolve()
    if c == repo_catalog_path.expanduser().resolve():
        return "repo_metadata"
    runtime_identity_home = _runtime_identity_home_from_catalog(c)
    if runtime_identity_home is not None:
        if _within(runtime_identity_home, user_root):
            return "global"
        return "project"
    project_root = _project_identity_home_from_repo_catalog(repo_root, repo_catalog_path)
    if _within(c, project_root):
        return "project"
    # Fallback: in some launch contexts repo_catalog path is non-canonical, but
    # runtime local catalog still lives under repo-adjacent ".identity".
    repo_adjacent_project_roots = {
        (repo_root / ".identity").resolve(),
        (repo_root.parent / ".identity").resolve(),
    }
    if c.name == "catalog.local.yaml" and any(_within(c, r) for r in repo_adjacent_project_roots):
        return "project"
    # Cross-cwd fallback: allow deterministic project classification when the
    # resolved local catalog itself is under "<project>/.identity" and that
    # project contains an identity-protocol-local checkout.
    if c.name == "catalog.local.yaml" and c.parent.name == ".identity":
        project_root_from_catalog = c.parent.parent.resolve()
        if (project_root_from_catalog / "identity-protocol-local").exists():
            return "project"
    if _within(c, user_root):
        return "global"
    return "unknown"


def _classify_scope_from_pack_path(
    pack_path: Path,
    *,
    repo_root: Path,
    project_root: Path,
    user_root: Path,
    admin_root: Path,
) -> ScopeName:
    p = pack_path.expanduser().resolve()
    if _within(p, project_root):
        return "USER"
    if _within(p, user_root):
        return "USER"
    if _within(p, admin_root):
        return "ADMIN"
    if _within(p, (repo_root / "identity").resolve()):
        return "SYSTEM"
    # Legacy project-local runtime paths (e.g. .agents/identity) should not degrade to UNKNOWN.
    if _within(p, repo_root):
        return "USER"
    return "UNKNOWN"


def default_identity_home(start: Path | None = None) -> Path:
    explicit_identity_home = os.environ.get("IDENTITY_HOME", "").strip()
    runtime_defaults = _load_runtime_env_defaults()
    configured_identity_home = runtime_defaults.get("IDENTITY_HOME", "").strip()

    if explicit_identity_home:
        p = _guard_forced_project_identity_home(_expand(explicit_identity_home), start=start)
    elif configured_identity_home:
        p = _guard_forced_project_identity_home(_expand(configured_identity_home), start=start)
    else:
        repo_home = _default_repo_identity_home(start)
        if repo_home.exists():
            p = repo_home
        else:
            p = _default_user_identity_home()
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fail-close behavior: keep canonical target and let callers surface writability error.
        pass
    return p


def default_local_catalog_path(identity_home: Path | None = None, *, start: Path | None = None) -> Path:
    explicit_catalog = str(os.environ.get("IDENTITY_CATALOG", "")).strip()
    runtime_defaults = _load_runtime_env_defaults()
    configured_catalog = str(runtime_defaults.get("IDENTITY_CATALOG", "")).strip()
    if explicit_catalog:
        return _guard_forced_project_local_catalog_path(_expand(explicit_catalog), start=start)
    if configured_catalog:
        return _guard_forced_project_local_catalog_path(_expand(configured_catalog), start=start)
    home = identity_home or default_identity_home(start=start)
    return home / "catalog.local.yaml"


def default_local_instances_root(identity_home: Path | None = None, *, start: Path | None = None) -> Path:
    home = identity_home or default_identity_home(start=start)
    return home.resolve()


def default_workspace_root(start: Path | None = None) -> Path:
    protocol_home = default_protocol_home(start=start)
    if protocol_home.name == "identity-protocol-local":
        return protocol_home.parent.resolve()
    return protocol_home.resolve()


def default_repo_catalog_path(*, start: Path | None = None) -> Path:
    return (default_protocol_home(start=start) / "identity" / "catalog" / "identities.yaml").resolve()


def _dedupe_path_candidates(candidates: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve())
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate.resolve())
    return out


def resolve_repo_catalog_path(raw_repo_catalog: str | Path | None, *, start: Path | None = None) -> Path:
    token = str(raw_repo_catalog or "").strip()
    if not token:
        return default_repo_catalog_path(start=start)
    raw_path = Path(token).expanduser()
    if raw_path.is_absolute():
        return raw_path.resolve()

    protocol_root = default_protocol_home(start=start)
    workspace_root = default_workspace_root(start=start)
    candidates: list[Path] = []
    if raw_path.parts and raw_path.parts[0] == protocol_root.name:
        candidates.append((workspace_root / raw_path).resolve())
    else:
        candidates.append((protocol_root / raw_path).resolve())
        candidates.append((workspace_root / raw_path).resolve())
    candidates = _dedupe_path_candidates(candidates)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_local_catalog_path(raw_local_catalog: str | Path | None, *, start: Path | None = None) -> Path:
    token = str(raw_local_catalog or "").strip()
    if not token:
        return default_local_catalog_path(start=start)
    raw_path = Path(token).expanduser()
    if raw_path.is_absolute():
        return raw_path.resolve()

    anchor_root = _normalize_anchor(start)
    workspace_root = default_workspace_root(start=start)
    protocol_root = default_protocol_home(start=start)
    candidates = _dedupe_path_candidates(
        [
            (anchor_root / raw_path).resolve(),
            (workspace_root / raw_path).resolve(),
            (protocol_root / raw_path).resolve(),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_protocol_root_from_repo_catalog(repo_catalog_path: Path | str, *, start: Path | None = None) -> Path:
    resolved = Path(repo_catalog_path).expanduser().resolve()
    if resolved.parent.name == "catalog" and resolved.parent.parent.name == "identity":
        return resolved.parent.parent.parent.resolve()
    return default_protocol_home(start=start)


def default_protocol_home(start: Path | None = None) -> Path:
    explicit = os.environ.get("IDENTITY_PROTOCOL_HOME", "").strip()
    runtime_defaults = _load_runtime_env_defaults()
    configured = runtime_defaults.get("IDENTITY_PROTOCOL_HOME", "").strip()
    if explicit:
        p = _guard_forced_project_protocol_home(_expand(explicit), start=start)
    elif configured:
        p = _guard_forced_project_protocol_home(_expand(configured), start=start)
    else:
        p = _default_protocol_home_fallback(start)
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
        "protocol_head_sha_at_run_start": commit,
        "baseline_reference_mode": "run_pinned",
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
            d["_source_layer"] = "repo_metadata"
            by_id[iid] = d
    for item in local_identities:
        iid = str(item.get("id", "")).strip()
        if iid:
            d = dict(item)
            d["_source_layer"] = "runtime_catalog"
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
    repo_project_root = _project_identity_home_from_repo_catalog(repo_root, repo_catalog_path)
    local_project_root = _runtime_identity_home_from_catalog(local_catalog_path) or repo_project_root
    local_source_layer = _classify_catalog_source_layer(
        local_catalog_path,
        repo_root=repo_root,
        user_root=user_root,
        repo_catalog_path=repo_catalog_path,
    )
    repo_source_layer = _classify_catalog_source_layer(
        repo_catalog_path,
        repo_root=repo_root,
        user_root=user_root,
        repo_catalog_path=repo_catalog_path,
    )

    candidates: list[dict[str, Any]] = []
    for source_layer, row, catalog_path in (
        (local_source_layer, local_identity, local_catalog_path),
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
            scope = _classify_scope_from_pack_path(
                pack,
                repo_root=repo_root,
                project_root=local_project_root,
                user_root=user_root,
                admin_root=admin_root,
            )
            # P0: avoid UNKNOWN scope entering runtime upgrade chain.
            # For runtime catalogs, UNKNOWN is coerced to USER semantics.
            if source_layer in {"project", "global"} and scope == "UNKNOWN":
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

    if repo_identity and (allow_conflict or not local_identity):
        pack_raw = str((repo_identity or {}).get("pack_path", "")).strip()
        if pack_raw:
            pack = Path(pack_raw).expanduser().resolve()
            profile = str((repo_identity or {}).get("profile", "")).strip().lower()
            runtime_mode = str((repo_identity or {}).get("runtime_mode", "")).strip().lower()
            if profile == "fixture" or runtime_mode == "demo_only":
                scope = "SYSTEM"
            else:
                scope = _classify_scope_from_pack_path(
                    pack,
                    repo_root=repo_root,
                    project_root=repo_project_root,
                    user_root=user_root,
                    admin_root=admin_root,
                )
                if scope == "UNKNOWN":
                    scope = "SYSTEM"
            candidates.append(
                {
                    "source_layer": repo_source_layer,
                    "catalog_path": str(repo_catalog_path),
                    "pack_path": str(pack),
                    "status": str((repo_identity or {}).get("status", "")).strip(),
                    "profile": str((repo_identity or {}).get("profile", "")).strip(),
                    "runtime_mode": str((repo_identity or {}).get("runtime_mode", "")).strip(),
                    "scope": scope,
                }
            )

    if not candidates:
        if repo_identity and not local_identity:
            raise FileNotFoundError(
                f"identity found only in repo metadata catalog; migrate into canonical runtime catalog first: {identity_id}"
            )
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
        chosen = next((c for c in candidates if c.get("source_layer") in {"project", "global"}), candidates[0])
        if not allow_conflict:
            raise RuntimeError(
                f"identity conflict detected for {identity_id}: multiple pack paths resolved={canonical_paths}. "
                "Pass --scope to arbitrate explicitly."
            )

    assert chosen is not None
    source_layer = str(chosen.get("source_layer", "")).strip() or "unknown"
    resolved_scope = str(chosen.get("scope", "")).strip().upper()
    if not resolved_scope or resolved_scope == "UNKNOWN":
        # Fail-close normalization: runtime candidates never leak UNKNOWN scope.
        resolved_scope = "USER" if source_layer in {"project", "global", "unknown"} else "SYSTEM"
    return {
        "identity_id": identity_id,
        "source_layer": source_layer,
        "catalog_path": str(chosen.get("catalog_path", "")),
        "pack_path": str(chosen.get("pack_path", "")),
        "status": str(chosen.get("status", "")).strip(),
        "profile": str(chosen.get("profile", "")).strip() or ("fixture" if source_layer == "repo_metadata" else "runtime"),
        "runtime_mode": str(chosen.get("runtime_mode", "")).strip()
        or ("demo_only" if source_layer == "repo_metadata" else "local_only"),
        "resolved_scope": resolved_scope,
        "resolved_pack_path": str(chosen.get("pack_path", "")),
        "conflict_detected": conflict_detected,
        "candidate_matches": candidates,
    }


def _cmd_resolve(args: argparse.Namespace) -> int:
    repo_catalog = resolve_repo_catalog_path(args.repo_catalog, start=Path(__file__).resolve())
    local_catalog = resolve_local_catalog_path(args.local_catalog, start=Path.cwd())
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
    repo_catalog = resolve_repo_catalog_path(args.repo_catalog, start=Path(__file__).resolve())
    local_catalog = resolve_local_catalog_path(args.local_catalog, start=Path.cwd())
    if args.ensure_local_catalog:
        ensure_local_catalog(repo_catalog, local_catalog)
    out = merged_catalog(repo_catalog, local_catalog)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve identity context across repo catalog and local catalog.")
    sub = ap.add_subparsers(dest="command", required=True)

    c1 = sub.add_parser("resolve", help="Resolve an identity from merged catalog context.")
    c1.add_argument("--identity-id", required=True)
    c1.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    c1.add_argument("--local-catalog", default="")
    c1.add_argument("--ensure-local-catalog", action="store_true")
    c1.add_argument("--scope", default="", help="optional explicit scope arbitration: REPO/USER/ADMIN/SYSTEM")
    c1.add_argument("--allow-conflict", action="store_true", help="allow conflict and pick preferred runtime layer")
    c1.set_defaults(func=_cmd_resolve)

    c2 = sub.add_parser("merge", help="Dump merged catalog (local overrides repo).")
    c2.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    c2.add_argument("--local-catalog", default="")
    c2.add_argument("--ensure-local-catalog", action="store_true")
    c2.set_defaults(func=_cmd_merge)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
