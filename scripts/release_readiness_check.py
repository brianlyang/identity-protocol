#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def _run(cmd: list[str]) -> int:
    print(f"[RUN] {' '.join(cmd)}")
    p = subprocess.run(cmd)
    if p.returncode != 0:
        print(f"[FAIL] command failed ({p.returncode}): {' '.join(cmd)}")
        return p.returncode
    return 0


def _git_rev(expr: str) -> str:
    p = subprocess.run(["git", "rev-parse", expr], check=True, capture_output=True, text=True)
    return p.stdout.strip()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _resolve_pack_path(catalog_path: str, identity_id: str) -> Path | None:
    p = Path(catalog_path).expanduser().resolve()
    if not p.exists():
        return None
    try:
        doc = _load_yaml(p)
    except Exception:
        return None
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        return None
    pack_raw = str((row or {}).get("pack_path", "")).strip()
    if not pack_raw:
        return None
    pack = Path(pack_raw).expanduser().resolve()
    return pack if pack.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Run release-readiness validators in a deterministic order.")
    ap.add_argument("--identity-id", default="store-manager")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    ap.add_argument(
        "--execution-report",
        default="",
        help="optional identity upgrade execution report path; when provided, enforce experience writeback linkage",
    )
    ap.add_argument(
        "--upgrade-report-dir",
        default="",
        help="optional explicit directory to search for auto-generated execution report",
    )
    ap.add_argument(
        "--catalog",
        default="",
        help="catalog path override. required unless IDENTITY_CATALOG is set.",
    )
    args = ap.parse_args()

    base = args.base.strip() or _git_rev("HEAD~1")
    head = args.head.strip() or _git_rev("HEAD")
    identity_id = args.identity_id.strip()
    explicit_catalog = args.catalog.strip()
    env_catalog = os.environ.get("IDENTITY_CATALOG", "").strip()
    catalog = explicit_catalog or env_catalog
    if not catalog:
        print("[FAIL] catalog is required (implicit fallback disabled).")
        print("       pass --catalog <path> or set IDENTITY_CATALOG after mode selection.")
        print("       recommended: source ./scripts/identity_runtime_select.sh project")
        return 2
    if not Path(catalog).expanduser().exists():
        print(f"[FAIL] catalog path does not exist: {catalog}")
        return 2

    seq: list[list[str]] = [
        ["python3", "scripts/validate_identity_protocol.py"],
        ["python3", "scripts/validate_identity_local_persistence.py"],
        ["python3", "scripts/validate_identity_creation_boundary.py"],
        ["python3", "scripts/validate_identity_scope_resolution.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_scope_isolation.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_scope_persistence.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_state_consistency.py", "--catalog", catalog],
        [
            "python3",
            "scripts/collect_identity_health_report.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--out-dir",
            "/tmp/identity-health-reports",
            "--enforce-pass",
        ],
        [
            "python3",
            "scripts/validate_identity_health_contract.py",
            "--identity-id",
            identity_id,
            "--report-dir",
            "/tmp/identity-health-reports",
            "--require-pass",
        ],
        ["python3", "scripts/validate_audit_snapshot_index.py"],
        ["python3", "scripts/validate_changelog_updated.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_release_metadata_sync.py"],
        ["python3", "scripts/validate_release_freeze_boundary.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_release_workspace_cleanliness.py"],
        ["python3", "scripts/validate_identity_instance_isolation.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_runtime_contract.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_role_binding.py", "--catalog", catalog, "--identity-id", identity_id],
        # scope must come from bound runtime/catalog resolution (single source of truth).
        ["python3", "scripts/validate_identity_prompt_quality.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_update_lifecycle.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_install_safety.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_install_provenance.py", "--catalog", catalog, "--identity-id", identity_id],
        [
            "python3",
            "scripts/validate_identity_capability_activation.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_self_upgrade_enforcement.py",
            "--identity-id",
            identity_id,
            "--base",
            base,
            "--head",
            head,
            "--catalog",
            catalog,
        ],
        ["python3", "scripts/validate_identity_ci_enforcement.py", "--catalog", catalog, "--identity-id", identity_id],
    ]
    execution_report = args.execution_report.strip()
    if not execution_report:
        gen_cmd = [
            "python3",
            "scripts/identity_creator.py",
            "update",
            "--identity-id",
            identity_id,
            "--mode",
            "review-required",
            "--catalog",
            catalog,
        ]
        rc = _run(gen_cmd)
        if rc != 0:
            return rc
        roots: list[Path] = []
        if args.upgrade_report_dir.strip():
            roots.append(Path(args.upgrade_report_dir.strip()).expanduser().resolve())
        pack_path = _resolve_pack_path(catalog, identity_id)
        if pack_path is not None:
            roots.append((pack_path / "runtime" / "reports").resolve())
            roots.append((pack_path / "runtime").resolve())
        roots.append(Path("/tmp/identity-upgrade-reports"))
        roots.append(Path("/tmp/identity-runtime"))
        if os.environ.get("IDENTITY_HOME", "").strip():
            roots.append(Path(os.environ["IDENTITY_HOME"]).expanduser().resolve())
        candidates: list[Path] = []
        for root in roots:
            if not root.exists():
                continue
            for p in glob.glob(str(root / "**" / f"identity-upgrade-exec-{identity_id}-*.json"), recursive=True):
                pp = Path(p)
                if pp.name.endswith("-patch-plan.json"):
                    continue
                candidates.append(pp)
        candidates = sorted(candidates, key=lambda p: p.stat().st_mtime)
        if not candidates:
            print(
                "[FAIL] writeback validation requires execution report, but auto-generation produced none: "
                f"searched_roots={','.join(str(r) for r in roots)} pattern=identity-upgrade-exec-{identity_id}-*.json"
            )
            return 2
        execution_report = str(candidates[-1])
        print(f"[INFO] auto-generated execution report: {execution_report}")

    seq.append(
        [
            "python3",
            "scripts/validate_identity_protocol_root_evidence.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_mode_promotion_arbitration.py",
            "--identity-id",
            identity_id,
            "--base",
            base,
            "--head",
            head,
            "--report",
            execution_report,
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_experience_writeback.py",
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--local-catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--execution-report",
            execution_report,
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_permission_state.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
            "--require-written",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_binding_tuple.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_capability_activation.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
            "--require-activated",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_prompt_activation.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--report",
            execution_report,
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_prompt_lifecycle.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
        ]
    )

    for cmd in seq:
        rc = _run(cmd)
        if rc != 0:
            return rc

    print("[OK] release readiness checks PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"[FAIL] subprocess error: {exc}", file=sys.stderr)
        raise SystemExit(2)
