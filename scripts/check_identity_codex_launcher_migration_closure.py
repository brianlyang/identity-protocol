#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml
from resolve_identity_context import resolve_local_catalog_path, resolve_repo_catalog_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_LAUNCHER_MIGRATION_INVALID = "IP-ILAUNCH-003"


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _iter_catalog_rows(*, catalog_path: Path) -> list[dict[str, Any]]:
    doc = _safe_load_yaml(catalog_path)
    rows = doc.get("identities")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _resolve_pack_path(*, row: dict[str, Any], identity_id: str, catalog_path: Path, repo_root: Path, repo_catalog: Path) -> Path:
    raw_pack = str(row.get("canonical_pack_path") or row.get("pack_path") or "").strip()
    if raw_pack:
        pack_path = Path(raw_pack).expanduser()
        if not pack_path.is_absolute():
            pack_path = (catalog_path.parent / pack_path).resolve()
        return pack_path
    if catalog_path.resolve() == repo_catalog.resolve():
        return (repo_root / "identity" / "packs" / identity_id).resolve()
    return (catalog_path.parent / identity_id).resolve()


def _run_launcher_validator(*, repo_root: Path, catalog_path: Path, identity_id: str) -> tuple[int, dict[str, Any]]:
    validator = (repo_root / "scripts" / "validate_identity_codex_launcher.py").resolve()
    proc = subprocess.run(
        [
            "python3",
            str(validator),
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--require-installed",
            "--json-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    payload: dict[str, Any] = {}
    stdout = str(proc.stdout or "").strip()
    if stdout:
        try:
            decoded = json.loads(stdout)
            if isinstance(decoded, dict):
                payload = decoded
        except Exception:
            payload = {
                "transport_error": "validator_stdout_not_json",
                "validator_stdout": stdout,
            }
    if not payload:
        payload = {
            "transport_error": "validator_stdout_missing",
            "validator_stdout": stdout,
            "validator_stderr": str(proc.stderr or "").strip(),
        }
    return proc.returncode, payload


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check active-runtime identity Codex launcher migration closure across catalogs."
    )
    ap.add_argument(
        "--repo-catalog",
        default="identity/catalog/identities.yaml",
        help="repository catalog path (default: identity/catalog/identities.yaml)",
    )
    ap.add_argument(
        "--catalog",
        action="append",
        default=[],
        help="additional catalog(s) to check; missing paths are skipped",
    )
    ap.add_argument(
        "--include-env-catalog",
        action="store_true",
        help="include $IDENTITY_CATALOG when set",
    )
    ap.add_argument(
        "--workspace-runtime-only",
        action="store_true",
        help="exclude the repository fixture catalog and check only explicitly provided workspace/runtime catalogs",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    caller_anchor = Path.cwd().resolve()
    repo_catalog = resolve_repo_catalog_path(args.repo_catalog, start=Path(__file__).resolve())

    catalog_candidates: list[Path] = [] if args.workspace_runtime_only else [repo_catalog]
    for raw in args.catalog:
        token = str(raw or "").strip()
        if not token:
            continue
        catalog_candidates.append(resolve_local_catalog_path(token, start=caller_anchor))
    if args.include_env_catalog:
        import os

        env_catalog = str(os.environ.get("IDENTITY_CATALOG", "")).strip()
        if env_catalog:
            catalog_candidates.append(resolve_local_catalog_path(env_catalog, start=caller_anchor))

    dedup: list[Path] = []
    seen: set[Path] = set()
    for p in catalog_candidates:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        dedup.append(rp)

    checked_rows: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    skipped_catalogs: list[str] = []
    stale_reasons: list[str] = []

    for catalog_path in dedup:
        if not catalog_path.exists() or not catalog_path.is_file():
            skipped_catalogs.append(str(catalog_path))
            continue
        for row in _iter_catalog_rows(catalog_path=catalog_path):
            identity_id = str(row.get("id", "")).strip()
            status = str(row.get("status", "")).strip().lower()
            profile = str(row.get("profile", "")).strip().lower()
            runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
            if not identity_id or status != "active" or profile != "runtime" or runtime_mode == "demo_only":
                continue

            pack_path = _resolve_pack_path(
                row=row,
                identity_id=identity_id,
                catalog_path=catalog_path,
                repo_root=repo_root,
                repo_catalog=repo_catalog,
            )
            task_path = (pack_path / "CURRENT_TASK.json").resolve()
            validator_rc, validator_payload = _run_launcher_validator(
                repo_root=repo_root,
                catalog_path=catalog_path,
                identity_id=identity_id,
            )
            launcher_status = str(validator_payload.get("identity_codex_launcher_status", "")).strip().upper()
            stale = validator_payload.get("stale_reasons")
            if not isinstance(stale, list):
                stale = []
            stale = [str(item).strip() for item in stale if str(item).strip()]
            reason = ""
            if validator_rc != 0:
                reason = ",".join(stale) if stale else str(validator_payload.get("error_code", "")).strip() or "launcher_validator_failed"
            elif launcher_status != STATUS_PASS_REQUIRED:
                reason = ",".join(stale) if stale else "launcher_not_pass_required"

            row_state = {
                "identity_id": identity_id,
                "catalog_path": str(catalog_path),
                "pack_path": str(pack_path),
                "task_path": str(task_path),
                "canonical_scope": str(row.get("canonical_scope", "")).strip(),
                "validator_rc": validator_rc,
                "launcher_status": launcher_status,
                "launcher_required": bool(validator_payload.get("launcher_required", False)),
                "install_required": bool(validator_payload.get("install_required", False)),
                "pack_assets_status": str(validator_payload.get("pack_assets_status", "")).strip().upper(),
                "installed_launcher_status": str(validator_payload.get("installed_launcher_status", "")).strip().upper(),
                "runtime_paths_status": str(validator_payload.get("runtime_paths_status", "")).strip().upper(),
                "launcher_config_identity_home": str(validator_payload.get("launcher_config_identity_home", "")).strip(),
                "runtime_identity_home": str(validator_payload.get("runtime_identity_home", "")).strip(),
                "runtime_paths_env": str(validator_payload.get("runtime_paths_env", "")).strip(),
                "stale_reasons": stale,
                "reason": reason,
                "status": STATUS_PASS_REQUIRED if validator_rc == 0 and launcher_status == STATUS_PASS_REQUIRED else STATUS_FAIL_REQUIRED,
            }
            checked_rows.append(row_state)
            if row_state["status"] != STATUS_PASS_REQUIRED:
                violations.append(dict(row_state))

    if not checked_rows:
        stale_reasons.append("no_active_runtime_identities_found")

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "identity_codex_launcher_migration_closure_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_LAUNCHER_MIGRATION_INVALID,
        "repo_catalog": str(repo_catalog),
        "repo_catalog_included": not args.workspace_runtime_only,
        "catalogs_checked": [str(path) for path in dedup],
        "skipped_catalogs": skipped_catalogs,
        "checked_identity_count": len(checked_rows),
        "violation_count": len(violations),
        "checked_rows": checked_rows,
        "violations": violations,
        "stale_reasons": stale_reasons,
    }
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
