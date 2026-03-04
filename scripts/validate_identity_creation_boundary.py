#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml

REPO_FIXTURE_CONFIRM_TOKEN = "I_UNDERSTAND_REPO_FIXTURE_WRITE"


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def _contains(text: str, pattern: str) -> bool:
    return pattern in text


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _find_identity(catalog_path: Path, identity_id: str) -> dict[str, Any] | None:
    if not catalog_path.exists():
        return None
    doc = _load_yaml(catalog_path)
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Boundary regression for create_identity_pack.py (repo fixture escape-hatch hardening)."
    )
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    create_script = repo_root / "scripts" / "create_identity_pack.py"
    if not create_script.exists():
        print(f"[FAIL] create script not found: {create_script}")
        return 2

    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="identity-create-boundary-") as td:
        temp_root = Path(td)
        fake_repo = temp_root / "fake-repo"
        (fake_repo / ".git").mkdir(parents=True, exist_ok=True)
        (fake_repo / "identity" / "catalog").mkdir(parents=True, exist_ok=True)

        local_root = temp_root / "local-runtime"
        local_root.mkdir(parents=True, exist_ok=True)

        common = [
            "python3",
            str(create_script),
            "--profile",
            "minimal",
            "--skip-bootstrap-check",
            "--skip-sample-bootstrap",
        ]

        case1_cmd = common + [
            "--id",
            "fixture-case1",
            "--title",
            "Fixture Case1",
            "--description",
            "fixture boundary negative",
            "--repo-fixture",
            "--pack-root",
            str(fake_repo / "identity" / "packs"),
            "--catalog",
            str(fake_repo / "identity" / "catalog" / "identities.yaml"),
        ]
        rc, out, err = _run(case1_cmd, cwd=fake_repo)
        if rc == 0 or not _contains(out + err, "requires explicit confirmation token"):
            failures.append("case1: expected missing-confirm failure")

        case2_cmd = common + [
            "--id",
            "runtime-case2",
            "--title",
            "Runtime Case2",
            "--description",
            "runtime repo-path negative",
            "--pack-root",
            str(fake_repo / "identity" / "packs"),
            "--catalog",
            str(local_root / "catalog.local.yaml"),
        ]
        rc, out, err = _run(case2_cmd, cwd=fake_repo)
        if rc == 0 or not _contains(out + err, "runtime identity must not be created under repository path"):
            failures.append("case2: expected runtime repo-path failure")

        runtime_catalog = local_root / "catalog.local.yaml"
        case3_cmd = common + [
            "--id",
            "runtime-case3",
            "--title",
            "Runtime Case3",
            "--description",
            "runtime local path positive",
            "--pack-root",
            str(local_root / "instances"),
            "--catalog",
            str(runtime_catalog),
            "--register",
        ]
        rc, out, err = _run(case3_cmd, cwd=fake_repo)
        if rc != 0:
            failures.append(f"case3: expected success but rc={rc}")
        else:
            row = _find_identity(runtime_catalog, "runtime-case3")
            if not row:
                failures.append("case3: catalog missing runtime-case3")
            else:
                if str(row.get("profile", "")).lower() != "runtime":
                    failures.append(f"case3: profile mismatch={row.get('profile')}")
                if str(row.get("runtime_mode", "")).lower() != "local_only":
                    failures.append(f"case3: runtime_mode mismatch={row.get('runtime_mode')}")

        fixture_catalog = fake_repo / "identity" / "catalog" / "identities.yaml"
        fixture_catalog.write_text(
            "version: '1.0'\nupdated_at: '2026-02-25'\ndefault_identity: ''\nidentities: []\n",
            encoding="utf-8",
        )
        case4_cmd = common + [
            "--id",
            "fixture-case4",
            "--title",
            "Fixture Case4",
            "--description",
            "fixture positive",
            "--repo-fixture",
            "--repo-fixture-confirm",
            REPO_FIXTURE_CONFIRM_TOKEN,
            "--repo-fixture-purpose",
            "boundary-regression",
            "--pack-root",
            str(fake_repo / "identity" / "packs"),
            "--catalog",
            str(fixture_catalog),
            "--register",
        ]
        rc, out, err = _run(case4_cmd, cwd=fake_repo)
        if rc != 0:
            failures.append(f"case4: expected success but rc={rc}")
        else:
            row = _find_identity(fixture_catalog, "fixture-case4")
            if not row:
                failures.append("case4: catalog missing fixture-case4")
            else:
                if str(row.get("profile", "")).lower() != "fixture":
                    failures.append(f"case4: profile mismatch={row.get('profile')}")
                if str(row.get("runtime_mode", "")).lower() != "demo_only":
                    failures.append(f"case4: runtime_mode mismatch={row.get('runtime_mode')}")

    if failures:
        print("[FAIL] identity creation boundary regression failed:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("[OK] identity creation boundary regression passed (4/4 cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
