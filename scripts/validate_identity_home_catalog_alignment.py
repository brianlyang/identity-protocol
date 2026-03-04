#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml

from resolve_identity_context import resolve_identity

ERR_HOME_CATALOG_ALIGNMENT = "IP-PATH-003"


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"catalog root must be object: {path}")
    return raw


def _identity_row(catalog_path: Path, identity_id: str) -> dict[str, Any] | None:
    doc = _load_catalog(catalog_path)
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)


def _resolve_identity_home(explicit_identity_home: str) -> tuple[Path, str]:
    if explicit_identity_home.strip():
        return Path(explicit_identity_home).expanduser().resolve(), "explicit"
    env_identity_home = os.environ.get("IDENTITY_HOME", "").strip()
    if env_identity_home:
        return Path(env_identity_home).expanduser().resolve(), "env:IDENTITY_HOME"
    env_codex_home = os.environ.get("CODEX_HOME", "").strip()
    if env_codex_home:
        return (Path(env_codex_home).expanduser().resolve() / "identity").resolve(), "env:CODEX_HOME"
    return (Path.home() / ".codex" / "identity").resolve(), "default:~/.codex/identity"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity_home == dirname(identity_catalog) alignment for runtime mutation flows.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-home", default="", help="optional explicit identity_home; defaults to IDENTITY_HOME/CODEX_HOME resolution")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()

    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    row = _identity_row(catalog_path, args.identity_id)
    if row is None:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "identity_home": "",
            "resolved_pack_path": "",
            "path_scope": "runtime_mutation",
            "path_governance_status": "FAIL_REQUIRED",
            "path_error_codes": [ERR_HOME_CATALOG_ALIGNMENT],
            "canonicalization_ref": "Path.resolve(strict=False)",
            "identity_home_expected": str(catalog_path.parent.resolve()),
            "identity_home_source": "",
            "stale_reasons": ["identity_not_found_in_catalog"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[FAIL] {ERR_HOME_CATALOG_ALIGNMENT} identity not found in catalog: {args.identity_id}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    profile = str(row.get("profile", "")).strip().lower()
    runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
    is_fixture = profile == "fixture" or runtime_mode == "demo_only"
    path_scope = "fixture_boundary" if is_fixture else "runtime_mutation"

    identity_home, identity_home_source = _resolve_identity_home(args.identity_home)
    identity_home_expected = catalog_path.parent.resolve()

    stale_reasons: list[str] = []
    resolved_pack_path = ""
    try:
        resolved = resolve_identity(
            args.identity_id,
            repo_catalog_path,
            catalog_path,
            allow_conflict=True,
        )
        resolved_pack_path = str(Path(str(resolved.get("pack_path", "")).strip()).expanduser().resolve())
    except Exception as exc:
        stale_reasons.append(f"identity_resolution_failed:{exc}")

    if is_fixture:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "identity_home": str(identity_home),
            "resolved_pack_path": resolved_pack_path,
            "path_scope": path_scope,
            "path_governance_status": "SKIPPED_NOT_REQUIRED",
            "path_error_codes": [],
            "canonicalization_ref": "Path.resolve(strict=False)",
            "identity_home_expected": str(identity_home_expected),
            "identity_home_source": identity_home_source,
            "stale_reasons": ["fixture_profile_scope"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[OK] identity home/catalog alignment skipped for fixture identity={args.identity_id}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if identity_home != identity_home_expected:
        stale_reasons.append("identity_home_catalog_parent_mismatch")

    ok = len(stale_reasons) == 0
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "identity_home": str(identity_home),
        "resolved_pack_path": resolved_pack_path,
        "path_scope": path_scope,
        "path_governance_status": "PASS_REQUIRED" if ok else "FAIL_REQUIRED",
        "path_error_codes": [] if ok else [ERR_HOME_CATALOG_ALIGNMENT],
        "canonicalization_ref": "Path.resolve(strict=False)",
        "identity_home_expected": str(identity_home_expected),
        "identity_home_source": identity_home_source,
        "stale_reasons": stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print(
                "[OK] identity home/catalog alignment gate passed: "
                f"identity={args.identity_id} identity_home={identity_home} catalog_parent={identity_home_expected}"
            )
        else:
            print(
                f"[FAIL] {ERR_HOME_CATALOG_ALIGNMENT} identity home/catalog alignment gate failed: "
                f"identity={args.identity_id} identity_home={identity_home} catalog_parent={identity_home_expected}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
