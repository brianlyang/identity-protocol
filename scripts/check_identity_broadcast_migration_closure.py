#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml
from resolve_identity_context import resolve_local_catalog_path, resolve_repo_catalog_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_BROADCAST_MIGRATION_INVALID = "IP-GATE-BCAST-DELIVERY-003"


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


def _run_validator(*, repo_root: Path, catalog_path: Path, identity_id: str) -> tuple[int, dict[str, Any]]:
    script = (repo_root / "scripts" / "validate_identity_broadcast_delivery.py").resolve()
    proc = subprocess.run(
        ["python3", str(script), "--catalog", str(catalog_path), "--identity-id", identity_id, "--json-only"],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
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
            payload = {"validator_stdout": stdout}
    return proc.returncode, payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Check broadcast delivery migration closure across active runtime identities.")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--catalog", action="append", default=[])
    ap.add_argument("--include-env-catalog", action="store_true")
    ap.add_argument("--workspace-runtime-only", action="store_true")
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
        env_catalog = str(os.environ.get("IDENTITY_CATALOG", "")).strip()
        if env_catalog:
            catalog_candidates.append(resolve_local_catalog_path(env_catalog, start=caller_anchor))

    dedup: list[Path] = []
    seen: set[Path] = set()
    for path in catalog_candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        dedup.append(resolved)

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
            validator_rc, validator_payload = _run_validator(
                repo_root=repo_root,
                catalog_path=catalog_path,
                identity_id=identity_id,
            )
            delivery_status = str(validator_payload.get("identity_broadcast_delivery_status", "")).strip().upper()
            row_state = {
                "identity_id": identity_id,
                "catalog_path": str(catalog_path),
                "validator_rc": validator_rc,
                "identity_broadcast_delivery_status": delivery_status,
                "broadcast_delivery_sync_status": str(validator_payload.get("broadcast_delivery_sync_status", "")).strip().upper(),
                "broadcast_projection_parity_status": str(validator_payload.get("broadcast_projection_parity_status", "")).strip().upper(),
                "broadcast_visible_count": int(validator_payload.get("broadcast_visible_count", 0) or 0),
                "broadcast_unread_count": int(validator_payload.get("broadcast_unread_count", 0) or 0),
                "broadcast_pending_ack_count": int(validator_payload.get("broadcast_pending_ack_count", 0) or 0),
                "broadcast_critical_unacked_count": int(validator_payload.get("broadcast_critical_unacked_count", 0) or 0),
                "stale_reasons": [str(item).strip() for item in (validator_payload.get("stale_reasons") or []) if str(item).strip()],
                "status": STATUS_PASS_REQUIRED if validator_rc == 0 and delivery_status == STATUS_PASS_REQUIRED else STATUS_FAIL_REQUIRED,
            }
            checked_rows.append(row_state)
            if row_state["status"] != STATUS_PASS_REQUIRED:
                violations.append(dict(row_state))

    if not checked_rows:
        stale_reasons.append("no_active_runtime_identities_found")

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "identity_broadcast_migration_closure_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_BROADCAST_MIGRATION_INVALID,
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
