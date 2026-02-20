#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml


REQUIRED_PACK_FILES = [
    "IDENTITY_PROMPT.md",
    "CURRENT_TASK.json",
    "TASK_HISTORY.md",
    "META.yaml",
]


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _resolve_identity(catalog_path: Path, identity_id: str) -> dict[str, Any]:
    catalog = _load_yaml(catalog_path)
    if not identity_id:
        identity_id = str(catalog.get("default_identity", "")).strip()
    target = next((x for x in (catalog.get("identities") or []) if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    return {"identity": target, "identity_id": identity_id, "default_identity": catalog.get("default_identity")}


def _run_check(cmd: list[str]) -> dict[str, Any]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "code": p.returncode,
        "ok": p.returncode == 0,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Show identity status with contract validator health")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"[FAIL] missing catalog: {catalog_path}")
        return 1

    try:
        ctx = _resolve_identity(catalog_path, args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    identity = ctx["identity"]
    identity_id = str(ctx["identity_id"])
    pack_path = Path(str(identity.get("pack_path", "")).strip())

    files = []
    for fn in REQUIRED_PACK_FILES:
        p = pack_path / fn
        files.append({"file": fn, "exists": p.exists(), "path": str(p)})

    checks = [
        _run_check(["python3", "scripts/validate_identity_runtime_contract.py", "--current-task", str(pack_path / "CURRENT_TASK.json")]),
        _run_check(["python3", "scripts/validate_identity_upgrade_prereq.py", "--identity-id", identity_id]),
        _run_check(["python3", "scripts/validate_identity_update_lifecycle.py", "--identity-id", identity_id]),
    ]

    report = {
        "identity_id": identity_id,
        "default_identity": ctx.get("default_identity"),
        "pack_path": str(pack_path),
        "pack_files": files,
        "checks": checks,
        "all_checks_pass": all(c["ok"] for c in checks),
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"identity_id={identity_id} pack_path={pack_path}")
        for f in files:
            print(f"- file {f['file']}: exists={f['exists']}")
        for c in checks:
            print(f"- check ok={c['ok']} code={c['code']}: {c['cmd']}")
        print(f"all_checks_pass={report['all_checks_pass']}")

    return 0 if report["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
