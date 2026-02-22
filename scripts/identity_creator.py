#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def _activate_identity(catalog: Path, identity_id: str) -> int:
    import yaml

    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 1
    data = yaml.safe_load(catalog.read_text(encoding="utf-8")) or {}
    identities = data.get("identities") or []
    changed = False
    for item in identities:
        if isinstance(item, dict) and str(item.get("id", "")).strip() == identity_id:
            item["status"] = "active"
            changed = True
            break
    if not changed:
        print(f"[FAIL] identity not found in catalog: {identity_id}")
        return 1
    catalog.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"[OK] activated identity in catalog: {identity_id}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Unified identity-creator CLI wrapper (init/register/validate/compile/activate/update)"
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create an identity pack scaffold")
    p_init.add_argument("--id", required=True)
    p_init.add_argument("--title", required=True)
    p_init.add_argument("--description", required=True)
    p_init.add_argument("--profile", choices=["full-contract", "minimal"], default="full-contract")
    p_init.add_argument("--register", action="store_true")
    p_init.add_argument("--activate", action="store_true")
    p_init.add_argument("--set-default", action="store_true")
    p_init.add_argument("--catalog", default="identity/catalog/identities.yaml")
    p_init.add_argument("--pack-root", default="identity/packs")

    p_validate = sub.add_parser("validate", help="Run identity required validators for an identity")
    p_validate.add_argument("--identity-id", required=True)

    p_compile = sub.add_parser("compile", help="Compile runtime brief")
    p_compile.add_argument("--check", action="store_true", help="fail if compile output is not stable")

    p_activate = sub.add_parser("activate", help="Set identity status=active in catalog")
    p_activate.add_argument("--identity-id", required=True)
    p_activate.add_argument("--catalog", default="identity/catalog/identities.yaml")

    p_update = sub.add_parser("update", help="Run identity upgrade executor")
    p_update.add_argument("--identity-id", required=True)
    p_update.add_argument("--mode", choices=["review-required", "safe-auto"], default="review-required")
    p_update.add_argument("--out-dir", default="identity/runtime/reports")

    args = ap.parse_args()

    if args.command == "init":
        cmd = [
            "python3",
            "scripts/create_identity_pack.py",
            "--id",
            args.id,
            "--title",
            args.title,
            "--description",
            args.description,
            "--profile",
            args.profile,
            "--catalog",
            args.catalog,
            "--pack-root",
            args.pack_root,
        ]
        if args.register:
            cmd.append("--register")
        if args.activate:
            cmd.append("--activate")
        if args.set_default:
            cmd.append("--set-default")
        return _run(cmd)

    if args.command == "validate":
        checks = [
            ["python3", "scripts/validate_identity_runtime_contract.py", "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_upgrade_prereq.py", "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_update_lifecycle.py", "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_install_safety.py", "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_experience_feedback_governance.py", "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_capability_arbitration.py", "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_ci_enforcement.py", "--identity-id", args.identity_id],
        ]
        for cmd in checks:
            rc = _run(cmd)
            if rc != 0:
                return rc
        return 0

    if args.command == "compile":
        rc = _run(["python3", "scripts/compile_identity_runtime.py"])
        if rc != 0:
            return rc
        if args.check:
            return _run(["git", "diff", "--exit-code", "--", "identity/runtime/IDENTITY_COMPILED.md"])
        return 0

    if args.command == "activate":
        return _activate_identity(Path(args.catalog), args.identity_id)

    if args.command == "update":
        return _run(
            [
                "python3",
                "scripts/execute_identity_upgrade.py",
                "--identity-id",
                args.identity_id,
                "--mode",
                args.mode,
                "--out-dir",
                args.out_dir,
            ]
        )

    print(f"[FAIL] unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
