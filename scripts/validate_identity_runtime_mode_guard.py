#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from resolve_identity_context import resolve_identity


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _detect_repo_root(start: Path | None = None) -> Path:
    base = (start or Path.cwd()).resolve()
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(base),
        capture_output=True,
        text=True,
    )
    if p.returncode == 0 and p.stdout.strip():
        return Path(p.stdout.strip()).expanduser().resolve()
    for parent in [base, *base.parents]:
        if (parent / ".git").exists():
            return parent.resolve()
    return base


def _resolve_project_identity_home(repo_root: Path) -> Path:
    if repo_root.name == "identity-protocol-local":
        return (repo_root.parent / ".agents" / "identity").resolve()
    return (repo_root / ".agents" / "identity").resolve()


def _resolve_global_identity_home() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        return (Path(codex_home).expanduser().resolve() / "identity").resolve()
    return (Path.home() / ".codex" / "identity").resolve()


def _infer_runtime_mode(catalog_path: Path, project_identity_home: Path, global_identity_home: Path) -> str:
    if _within(catalog_path, project_identity_home):
        return "project"
    if _within(catalog_path, global_identity_home):
        return "global"
    return "custom"


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail-fast guard: validate runtime mode/catalog/pack binding before identity operations.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="", help="local runtime catalog path (required unless IDENTITY_CATALOG is set)")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="")
    ap.add_argument(
        "--expect-mode",
        choices=["auto", "project", "global", "custom", "any"],
        default="auto",
        help="auto requires catalog to map to project/global canonical mode",
    )
    ap.add_argument("--json", action="store_true", help="print full payload as JSON")
    args = ap.parse_args()

    explicit_catalog = args.catalog.strip()
    env_catalog = os.environ.get("IDENTITY_CATALOG", "").strip()
    catalog_raw = explicit_catalog or env_catalog
    if not catalog_raw:
        print("[FAIL] IP-ENV-001 missing catalog binding")
        print("       pass --catalog <path> or export IDENTITY_CATALOG first")
        print("       fix: source ./scripts/identity_runtime_select.sh project")
        return 2

    catalog_path = Path(catalog_raw).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] IP-ENV-001 catalog path not found: {catalog_path}")
        print("       fix: source ./scripts/identity_runtime_select.sh project")
        return 2

    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    repo_root = _detect_repo_root(Path.cwd())
    project_identity_home = _resolve_project_identity_home(repo_root)
    global_identity_home = _resolve_global_identity_home()
    inferred_mode = _infer_runtime_mode(catalog_path, project_identity_home, global_identity_home)

    try:
        resolved = resolve_identity(
            args.identity_id,
            repo_catalog_path,
            catalog_path,
            preferred_scope=args.scope,
        )
    except Exception as exc:
        print(f"[FAIL] IP-ENV-002 resolve failed: {exc}")
        print("       fix: source ./scripts/identity_runtime_select.sh project")
        return 2

    resolved_catalog = Path(str(resolved.get("catalog_path", "")).strip()).expanduser().resolve()
    resolved_pack = Path(str(resolved.get("pack_path", "")).strip()).expanduser().resolve()
    source_layer = str(resolved.get("source_layer", "")).strip().lower()
    resolved_scope = str(resolved.get("resolved_scope", "")).strip().upper()

    checks: dict[str, bool] = {
        "catalog_exists": catalog_path.exists(),
        "resolved_source_local": source_layer == "local",
        "resolved_catalog_matches_requested": resolved_catalog == catalog_path,
        "resolved_scope_known": resolved_scope != "UNKNOWN",
        "pack_exists": resolved_pack.exists(),
    }

    if inferred_mode == "project":
        checks["pack_within_mode_root"] = _within(resolved_pack, project_identity_home)
    elif inferred_mode == "global":
        checks["pack_within_mode_root"] = _within(resolved_pack, global_identity_home)
    else:
        checks["pack_within_mode_root"] = True

    expected_mode = args.expect_mode
    if expected_mode == "auto":
        checks["mode_recognized"] = inferred_mode in {"project", "global"}
        checks["expected_mode_match"] = checks["mode_recognized"]
    elif expected_mode == "any":
        checks["mode_recognized"] = True
        checks["expected_mode_match"] = True
    else:
        checks["mode_recognized"] = True
        checks["expected_mode_match"] = inferred_mode == expected_mode

    env_catalog_mismatch = False
    env_catalog_path = None
    if env_catalog:
        env_catalog_path = Path(env_catalog).expanduser().resolve()
        env_catalog_mismatch = env_catalog_path != catalog_path

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "repo_catalog_path": str(repo_catalog_path),
        "resolved_catalog_path": str(resolved_catalog),
        "pack_path": str(resolved_pack),
        "source_layer": source_layer,
        "resolved_scope": resolved_scope,
        "inferred_mode": inferred_mode,
        "expected_mode": expected_mode,
        "repo_root": str(repo_root),
        "project_identity_home": str(project_identity_home),
        "global_identity_home": str(global_identity_home),
        "checks": checks,
        "env_catalog_path": str(env_catalog_path) if env_catalog_path else "",
        "env_catalog_mismatch": env_catalog_mismatch,
        "fix_hint": "source ./scripts/identity_runtime_select.sh project",
    }

    ok = all(bool(v) for v in checks.values())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if not ok:
        print("[FAIL] runtime mode guard blocked execution")
        print(
            f"       identity={args.identity_id} mode={inferred_mode} "
            f"catalog={catalog_path} pack={resolved_pack}"
        )
        for k, v in checks.items():
            print(f"       {k}={v}")
        if inferred_mode == "global":
            print("       fix: source ./scripts/identity_runtime_select.sh global")
        elif inferred_mode == "project":
            print("       fix: source ./scripts/identity_runtime_select.sh project")
        elif expected_mode in {"project", "global"}:
            print(f"       fix: source ./scripts/identity_runtime_select.sh {expected_mode}")
        else:
            print("       fix: choose explicit mode first, then rerun command")
            print("            source ./scripts/identity_runtime_select.sh project")
        return 2

    print(
        "[OK] runtime mode guard passed: "
        f"identity={args.identity_id} mode={inferred_mode} "
        f"catalog={catalog_path} pack={resolved_pack} scope={resolved_scope}"
    )
    if env_catalog_mismatch:
        print(
            "[WARN] IDENTITY_CATALOG env differs from requested catalog "
            f"(env={env_catalog_path}); explicit --catalog takes precedence."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
