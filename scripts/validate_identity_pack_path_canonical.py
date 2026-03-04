#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

ERR_PATH_NON_CANONICAL = "IP-PATH-001"


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip()


def _detect_repo_root(start: Path | None = None) -> Path:
    base = (start or Path.cwd()).resolve()
    rc, out = _run(["git", "rev-parse", "--show-toplevel"], base)
    if rc == 0 and out:
        return Path(out).expanduser().resolve()
    for parent in [base, *base.parents]:
        if (parent / ".git").exists():
            return parent.resolve()
    return base


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"catalog root must be object: {path}")
    return raw


def _get_identity_row(catalog_path: Path, identity_id: str) -> dict[str, Any] | None:
    doc = _load_catalog(catalog_path)
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)


def _default_global_identity_home() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        return (Path(codex_home).expanduser().resolve() / "identity").resolve()
    return (Path.home() / ".codex" / "identity").resolve()


def _resolve_project_identity_home(repo_root: Path) -> Path:
    if repo_root.name == "identity-protocol-local":
        return (repo_root.parent / ".agents" / "identity").resolve()
    return (repo_root / ".agents" / "identity").resolve()


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _resolve_allowed_roots(catalog_path: Path, repo_root: Path, *, is_fixture: bool) -> list[Path]:
    roots: list[Path] = []
    roots.append(catalog_path.parent.resolve())

    env_identity_home = os.environ.get("IDENTITY_HOME", "").strip()
    if env_identity_home:
        roots.append(Path(env_identity_home).expanduser().resolve())

    roots.append(_default_global_identity_home())
    roots.append(_resolve_project_identity_home(repo_root))
    roots.append(Path("/etc/codex/identity").resolve())

    if is_fixture:
        roots.append((repo_root / "identity").resolve())
        roots.append((repo_root / "identity" / "packs").resolve())

    uniq: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(root)
    return uniq


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate catalog pack_path canonical absolute contract.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    row = _get_identity_row(catalog_path, args.identity_id)
    if row is None:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "pack_path_raw": "",
            "pack_path_resolved": "",
            "path_scope": "",
            "allowed_runtime_roots": [],
            "path_governance_status": "FAIL_REQUIRED",
            "path_error_codes": [ERR_PATH_NON_CANONICAL],
            "stale_reasons": ["identity_not_found_in_catalog"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[FAIL] {ERR_PATH_NON_CANONICAL} identity not found in catalog: {args.identity_id}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    profile = str(row.get("profile", "")).strip().lower()
    runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
    is_fixture = profile == "fixture" or runtime_mode == "demo_only"
    path_scope = "fixture" if is_fixture else "runtime"
    pack_raw = str(row.get("pack_path", "")).strip()
    repo_root = _detect_repo_root(Path.cwd())
    allowed_roots = _resolve_allowed_roots(catalog_path, repo_root, is_fixture=is_fixture)
    stale_reasons: list[str] = []

    if not pack_raw:
        stale_reasons.append("pack_path_missing")
        pack_candidate = None
        pack_resolved = None
    else:
        pack_candidate = Path(pack_raw).expanduser()
        pack_resolved = pack_candidate.resolve()

    if not pack_raw:
        pass
    elif not pack_candidate.is_absolute():
        stale_reasons.append("pack_path_not_absolute")
    elif str(pack_candidate) != str(pack_resolved):
        stale_reasons.append("pack_path_not_canonical")

    if pack_resolved is None or not pack_resolved.exists():
        stale_reasons.append("pack_path_not_found")

    if pack_resolved is not None and pack_resolved.exists():
        if not any(_within(pack_resolved, root) for root in allowed_roots):
            stale_reasons.append("pack_path_outside_allowed_runtime_roots")

    ok = len(stale_reasons) == 0
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path_raw": pack_raw,
        "pack_path_resolved": str(pack_resolved) if pack_resolved else "",
        "path_scope": path_scope,
        "allowed_runtime_roots": [str(p) for p in allowed_roots],
        "path_governance_status": "PASS_REQUIRED" if ok else "FAIL_REQUIRED",
        "path_error_codes": [] if ok else [ERR_PATH_NON_CANONICAL],
        "stale_reasons": stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print(
                "[OK] pack path canonical gate passed: "
                f"identity={args.identity_id} catalog={catalog_path} pack={pack_resolved}"
            )
        else:
            print(
                f"[FAIL] {ERR_PATH_NON_CANONICAL} pack path canonical gate failed: "
                f"identity={args.identity_id} catalog={catalog_path}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
