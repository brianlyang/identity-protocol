#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_CONTRACT_INVALID = "IP-GATE-ENTRY-002"


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _safe_load_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _resolve_pack_path(*, row: dict[str, Any], identity_id: str, catalog_path: Path, repo_root: Path, repo_catalog: Path) -> Path:
    raw_pack = str(row.get("pack_path", "")).strip()
    if raw_pack:
        pack_path = Path(raw_pack).expanduser()
        if not pack_path.is_absolute():
            pack_path = (catalog_path.parent / pack_path).resolve()
        return pack_path
    if catalog_path.resolve() == repo_catalog.resolve():
        return (repo_root / "identity" / "packs" / identity_id).resolve()
    return (catalog_path.parent / identity_id).resolve()


def _iter_catalog_rows(*, catalog_path: Path) -> list[dict[str, Any]]:
    doc = _safe_load_yaml(catalog_path)
    rows = doc.get("identities")
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            out.append(row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Check unique-entry max-age migration closure for active runtime identities.")
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
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    repo_catalog = (repo_root / str(args.repo_catalog)).resolve()

    catalog_candidates: list[Path] = [repo_catalog]
    for raw in args.catalog:
        token = str(raw or "").strip()
        if not token:
            continue
        p = Path(token).expanduser()
        if not p.is_absolute():
            p = (repo_root / p).resolve()
        catalog_candidates.append(p)
    if args.include_env_catalog:
        import os

        env_catalog = str(os.environ.get("IDENTITY_CATALOG", "")).strip()
        if env_catalog:
            catalog_candidates.append(Path(env_catalog).expanduser().resolve())

    dedup: list[Path] = []
    seen: set[Path] = set()
    for p in catalog_candidates:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        dedup.append(rp)

    checked_rows: list[dict[str, Any]] = []
    skipped_catalogs: list[str] = []
    violations: list[dict[str, Any]] = []
    stale_reasons: list[str] = []

    for catalog_path in dedup:
        if not catalog_path.exists() or not catalog_path.is_file():
            skipped_catalogs.append(str(catalog_path))
            continue
        rows = _iter_catalog_rows(catalog_path=catalog_path)
        for row in rows:
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

            row_state = {
                "identity_id": identity_id,
                "catalog_path": str(catalog_path),
                "pack_path": str(pack_path),
                "task_path": str(task_path),
                "max_age_seconds": 0,
                "status": STATUS_PASS_REQUIRED,
                "reason": "",
            }
            checked_rows.append(row_state)

            if not task_path.exists() or not task_path.is_file():
                row_state["status"] = STATUS_FAIL_REQUIRED
                row_state["reason"] = "current_task_missing"
                violations.append(dict(row_state))
                continue

            task_doc = _safe_load_json(task_path)
            contract = task_doc.get("protocol_unique_entry_gate_contract_v1")
            if not isinstance(contract, dict):
                row_state["status"] = STATUS_FAIL_REQUIRED
                row_state["reason"] = "unique_entry_contract_missing"
                violations.append(dict(row_state))
                continue

            raw_max_age = contract.get("entry_receipt_max_age_seconds", 0)
            try:
                max_age = int(raw_max_age)
            except Exception:
                max_age = 0
            row_state["max_age_seconds"] = max_age
            if max_age <= 0:
                row_state["status"] = STATUS_FAIL_REQUIRED
                row_state["reason"] = "entry_receipt_max_age_seconds_invalid"
                violations.append(dict(row_state))

    if not checked_rows:
        stale_reasons.append("no_active_runtime_identities_found")

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "unique_entry_contract_migration_closure_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_CONTRACT_INVALID,
        "repo_catalog": str(repo_catalog),
        "catalogs_checked": [str(x) for x in dedup],
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
