#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml

from version_baseline_common import (
    REQUIRED_AGENT_IDENTITY_FIELDS,
    REQUIRED_CATALOG_FIELDS,
    REQUIRED_META_FIELDS,
    REQUIRED_SCAFFOLD_METADATA_FIELDS,
    resolve_version_baseline,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_VERSION_BASELINE = "IP-PVA-002"


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


def _catalog_candidates(*, repo_root: Path, repo_catalog: Path, raw_catalogs: list[str], include_env_catalog: bool) -> list[Path]:
    out: list[Path] = [repo_catalog.resolve()]
    for raw in raw_catalogs:
        token = str(raw or "").strip()
        if not token:
            continue
        p = Path(token).expanduser()
        if not p.is_absolute():
            p = (repo_root / p).resolve()
        out.append(p.resolve())
    if include_env_catalog:
        env_catalog = str(os.environ.get("IDENTITY_CATALOG", "")).strip()
        if env_catalog:
            out.append(Path(env_catalog).expanduser().resolve())
    dedup: list[Path] = []
    seen: set[Path] = set()
    for p in out:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        dedup.append(rp)
    return dedup


def main() -> int:
    ap = argparse.ArgumentParser(description="Check active runtime scaffold-version migration closure against version baseline SSOT.")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--catalog", action="append", default=[])
    ap.add_argument("--include-env-catalog", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    repo_catalog = (repo_root / str(args.repo_catalog)).resolve()

    baseline = resolve_version_baseline(repo_root=repo_root)
    if not baseline.get("ok"):
        payload = {
            "version_baseline_migration_closure_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_VERSION_BASELINE,
            "repo_catalog": str(repo_catalog),
            "catalogs_checked": [],
            "checked_identity_count": 0,
            "violation_count": 0,
            "checked_rows": [],
            "violations": [],
            "version_baseline": {
                "entry_file": str(baseline.get("entry_path", "")),
                "resolved_file": str(baseline.get("resolved_path", "")),
                "stream_version": str(baseline.get("stream_version", "")),
                "error": str(baseline.get("error", "")),
                "missing_fields": baseline.get("missing_fields", []),
            },
            "stale_reasons": ["version_baseline_unavailable"],
        }
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    catalogs = _catalog_candidates(
        repo_root=repo_root,
        repo_catalog=repo_catalog,
        raw_catalogs=args.catalog,
        include_env_catalog=bool(args.include_env_catalog),
    )

    baseline_agent = dict(baseline.get("agent_identity") or {})
    baseline_scaffold = dict(baseline.get("scaffold_metadata") or {})
    baseline_meta = dict(baseline.get("meta") or {})
    baseline_catalog = dict(baseline.get("catalog") or {})

    checked_rows: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    skipped_catalogs: list[str] = []
    stale_reasons: list[str] = []

    for catalog_path in catalogs:
        if not catalog_path.exists() or not catalog_path.is_file():
            skipped_catalogs.append(str(catalog_path))
            continue
        catalog_doc = _safe_load_yaml(catalog_path)
        rows = catalog_doc.get("identities")
        rows = rows if isinstance(rows, list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
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
            meta_path = (pack_path / "META.yaml").resolve()

            row_state: dict[str, Any] = {
                "identity_id": identity_id,
                "catalog_path": str(catalog_path),
                "pack_path": str(pack_path),
                "task_path": str(task_path),
                "meta_path": str(meta_path),
                "status": STATUS_PASS_REQUIRED,
                "mismatches": [],
                "missing": [],
            }

            task_doc = _safe_load_json(task_path) if task_path.exists() else {}
            meta_doc = _safe_load_yaml(meta_path) if meta_path.exists() else {}
            agent = task_doc.get("agent_identity") if isinstance(task_doc.get("agent_identity"), dict) else {}
            scaffold = task_doc.get("scaffold_metadata") if isinstance(task_doc.get("scaffold_metadata"), dict) else {}

            if not task_path.exists():
                row_state["missing"].append("current_task_missing")
            if not meta_path.exists():
                row_state["missing"].append("meta_missing")

            for field in REQUIRED_AGENT_IDENTITY_FIELDS:
                expected = str(baseline_agent.get(field, "")).strip()
                observed = str(agent.get(field, "")).strip()
                if expected and observed != expected:
                    row_state["mismatches"].append(
                        {"field": f"task.agent_identity.{field}", "expected": expected, "observed": observed}
                    )
            for field in REQUIRED_SCAFFOLD_METADATA_FIELDS:
                expected = str(baseline_scaffold.get(field, "")).strip()
                observed = str(scaffold.get(field, "")).strip()
                if expected and observed != expected:
                    row_state["mismatches"].append(
                        {"field": f"task.scaffold_metadata.{field}", "expected": expected, "observed": observed}
                    )
            for field in REQUIRED_META_FIELDS:
                expected = str(baseline_meta.get(field, "")).strip()
                observed = str(meta_doc.get(field, "")).strip() if isinstance(meta_doc, dict) else ""
                if expected and observed != expected:
                    row_state["mismatches"].append(
                        {"field": f"meta.{field}", "expected": expected, "observed": observed}
                    )
            for field in REQUIRED_CATALOG_FIELDS:
                expected = str(baseline_catalog.get(field, "")).strip()
                observed = str(row.get(field, "")).strip()
                if expected and observed != expected:
                    row_state["mismatches"].append(
                        {"field": f"catalog.{field}", "expected": expected, "observed": observed}
                    )

            if row_state["missing"] or row_state["mismatches"]:
                row_state["status"] = STATUS_FAIL_REQUIRED
                violations.append(dict(row_state))

            checked_rows.append(row_state)

    if not checked_rows:
        stale_reasons.append("no_active_runtime_identities_found")

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "version_baseline_migration_closure_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_VERSION_BASELINE,
        "repo_catalog": str(repo_catalog),
        "catalogs_checked": [str(x) for x in catalogs],
        "skipped_catalogs": skipped_catalogs,
        "checked_identity_count": len(checked_rows),
        "violation_count": len(violations),
        "checked_rows": checked_rows,
        "violations": violations,
        "version_baseline": {
            "entry_file": str(baseline.get("entry_path", "")),
            "resolved_file": str(baseline.get("resolved_path", "")),
            "stream_version": str(baseline.get("stream_version", "")),
        },
        "stale_reasons": stale_reasons,
    }

    print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
