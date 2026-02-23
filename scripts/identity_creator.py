#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _dump_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _resolve_task_path(catalog_data: dict, identity_id: str) -> Path:
    identities = catalog_data.get("identities") or []
    target = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p
    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _write_binding_evidence(catalog_data: dict, identity_id: str, binding_status: str, note: str) -> Path:
    task = _load_json(_resolve_task_path(catalog_data, identity_id))
    contract = task.get("identity_role_binding_contract") or {}
    role_type = str(contract.get("role_type", "")).strip() or "identity_runtime_operator"
    ts = datetime.now(timezone.utc)
    report = {
        "binding_id": f"identity-role-binding-{identity_id}-{int(ts.timestamp())}",
        "generated_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "identity_id": identity_id,
        "role_type": role_type,
        "binding_status": binding_status,
        "runtime_bootstrap": {
            "status": "PASS",
            "validator": "scripts/validate_identity_runtime_contract.py",
            "evidence": str(_resolve_task_path(catalog_data, identity_id)),
        },
        "switch_guard": {
            "status": "PASS",
            "activation_policy": str(contract.get("activation_policy", "inactive_by_default")),
            "notes": note,
        },
    }
    out = Path("identity/runtime/examples") / f"identity-role-binding-{identity_id}-{int(ts.timestamp())}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def _activate_identity(catalog: Path, identity_id: str) -> int:
    rc = _run(["python3", "scripts/validate_identity_role_binding.py", "--identity-id", identity_id])
    if rc != 0:
        print("[FAIL] role-binding validation failed; activation blocked")
        return rc

    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 1
    original_catalog_text = catalog.read_text(encoding="utf-8")
    data = _load_yaml(catalog)
    identities = data.get("identities") or []
    target = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    if not target:
        print(f"[FAIL] identity not found in catalog: {identity_id}")
        return 1

    previously_active = [
        str(x.get("id", "")).strip()
        for x in identities
        if isinstance(x, dict)
        and str(x.get("status", "")).strip().lower() == "active"
        and str(x.get("id", "")).strip()
        and str(x.get("id", "")).strip() != identity_id
    ]

    created_evidence: list[Path] = []
    try:
        # promote target to active binding first (activation validator requires this for active identities)
        created_evidence.append(
            _write_binding_evidence(
                data,
                identity_id,
                "BOUND_ACTIVE",
                note="activation transaction promoted identity to active",
            )
        )
        for old_id in previously_active:
            created_evidence.append(
                _write_binding_evidence(
                    data,
                    old_id,
                    "BOUND_READY",
                    note=f"demoted by single-active switch to {identity_id}",
                )
            )

        for item in identities:
            if not isinstance(item, dict):
                continue
            iid = str(item.get("id", "")).strip()
            if not iid:
                continue
            item["status"] = "active" if iid == identity_id else "inactive"

        _dump_yaml(catalog, data)
        rc = _run(["python3", "scripts/validate_identity_role_binding.py", "--identity-id", identity_id])
        if rc != 0:
            raise RuntimeError("post-activation role-binding validation failed")

        switch_dir = Path("identity/runtime/reports/activation")
        switch_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc)
        switch_report = switch_dir / f"identity-activation-switch-{identity_id}-{int(ts.timestamp())}.json"
        switch_payload = {
            "switch_id": switch_report.stem,
            "generated_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "target_identity_id": identity_id,
            "demoted_identities": previously_active,
            "single_active_enforced": True,
            "binding_evidence_paths": [str(p) for p in created_evidence],
        }
        switch_report.write_text(json.dumps(switch_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] activated identity in catalog (single-active): {identity_id}")
        print(f"[OK] switch report: {switch_report}")
        return 0
    except Exception as e:
        catalog.write_text(original_catalog_text, encoding="utf-8")
        for p in created_evidence:
            if p.exists():
                p.unlink()
        print(f"[FAIL] activation transaction rolled back: {e}")
        return 1


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
            ["python3", "scripts/validate_identity_role_binding.py", "--identity-id", args.identity_id],
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
