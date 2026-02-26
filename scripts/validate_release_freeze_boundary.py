#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def _run_git(args: list[str]) -> str:
    p = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return p.stdout.strip()


def _changed_files(base: str, head: str) -> list[tuple[str, str]]:
    out = _run_git(["diff", "--name-status", base, head])
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        status, path = parts[0].strip(), parts[1].strip()
        rows.append((status, path))
    return rows


def _load_catalog(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"catalog root must be object: {path}")
    return raw


def _is_fixture_demo_row(row: dict) -> bool:
    profile = str(row.get("profile", "fixture")).strip() or "fixture"
    runtime_mode = str(row.get("runtime_mode", "demo_only")).strip() or "demo_only"
    return profile == "fixture" and runtime_mode == "demo_only"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Validate release freeze boundary: base repo must not absorb local identity "
            "instance packs during release hardening."
        )
    )
    ap.add_argument("--base", default="", help="git base sha; defaults to HEAD~1")
    ap.add_argument("--head", default="", help="git head sha; defaults to HEAD")
    ap.add_argument(
        "--forbidden-path-prefixes",
        nargs="*",
        default=["identity/packs/"],
        help="path prefixes not allowed in release changes",
    )
    ap.add_argument(
        "--catalog",
        default="identity/catalog/identities.yaml",
        help="identity catalog path",
    )
    args = ap.parse_args()

    base = args.base.strip() or _run_git(["rev-parse", "HEAD~1"])
    head = args.head.strip() or _run_git(["rev-parse", "HEAD"])

    changed = _changed_files(base, head)
    forbidden_hits: list[str] = []
    for status, p in changed:
        # deletions remove forbidden assets and should be allowed.
        if status == "D":
            continue
        for prefix in args.forbidden_path_prefixes:
            if p.startswith(prefix):
                forbidden_hits.append(f"{status}\t{p}")
                break

    if forbidden_hits:
        print("[FAIL] release freeze boundary violated: forbidden path changes detected:")
        for hit in forbidden_hits:
            print(f"  - {hit}")
        print("Hint: keep local-instance packs outside base repo release scope.")
        return 1

    catalog_path = Path(args.catalog)
    catalog = _load_catalog(catalog_path)
    identities = catalog.get("identities") or []
    bad_pack_paths: list[str] = []
    fixture_pack_paths: list[str] = []
    for row in identities:
        if not isinstance(row, dict):
            continue
        identity_id = str(row.get("id", "")).strip()
        pack_path = str(row.get("pack_path", "")).strip()
        if not identity_id or not pack_path.startswith("identity/packs/"):
            continue
        if _is_fixture_demo_row(row):
            fixture_pack_paths.append(f"{identity_id} -> {pack_path}")
            continue
        profile = str(row.get("profile", "")).strip() or "runtime"
        runtime_mode = str(row.get("runtime_mode", "")).strip() or "local_only"
        bad_pack_paths.append(
            f"{identity_id} -> {pack_path} (profile={profile}, runtime_mode={runtime_mode})"
        )

    if bad_pack_paths:
        print("[FAIL] identity catalog contains pack_path entries under forbidden scope:")
        for row in bad_pack_paths:
            print(f"  - {row}")
        return 1

    if fixture_pack_paths:
        print("[INFO] fixture/demo catalog entries under identity/packs are allowed:")
        for row in fixture_pack_paths:
            print(f"  - {row}")

    print("[OK] release freeze boundary validated")
    print(f"[OK] checked commit range: {base}..{head}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"[FAIL] git command failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
