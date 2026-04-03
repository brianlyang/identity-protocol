#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from runtime_fleet_closure_common import STATUS_FAIL_REQUIRED, STATUS_PASS_REQUIRED
from runtime_pack_closure_common import PACK_SCAN_POLICY_ID, collect_active_runtime_pack_closure
from version_baseline_common import (
    REQUIRED_AGENT_IDENTITY_FIELDS,
    REQUIRED_CATALOG_FIELDS,
    REQUIRED_META_FIELDS,
    REQUIRED_SCAFFOLD_METADATA_FIELDS,
    resolve_version_baseline,
)

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


def _build_row_evaluator(*, baseline_agent: dict[str, Any], baseline_scaffold: dict[str, Any], baseline_meta: dict[str, Any], baseline_catalog: dict[str, Any]):
    def _evaluate_row(**kwargs: Any) -> dict[str, Any]:
        pack_path = kwargs.get("pack_path")
        if not isinstance(pack_path, Path):
            raise TypeError("pack_path_missing")
        catalog_row = kwargs.get("catalog_row")
        row = catalog_row if isinstance(catalog_row, dict) else {}
        task_path = (pack_path / "CURRENT_TASK.json").resolve()
        meta_path = (pack_path / "META.yaml").resolve()

        row_state: dict[str, Any] = {
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
        return row_state

    return _evaluate_row


def main() -> int:
    ap = argparse.ArgumentParser(description="Check active runtime scaffold-version migration closure against version baseline SSOT.")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--catalog", action="append", default=[])
    ap.add_argument("--include-env-catalog", action="store_true")
    ap.add_argument("--workspace-runtime-only", action="store_true", help="exclude the repository fixture catalog and check only explicitly provided workspace/runtime catalogs")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    baseline = resolve_version_baseline(repo_root=repo_root)
    if not baseline.get("ok"):
        payload = {
            "version_baseline_migration_closure_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_VERSION_BASELINE,
            "repo_catalog": str((repo_root / str(args.repo_catalog)).resolve()),
            "repo_catalog_included": not bool(args.workspace_runtime_only),
            "catalog_selection_mode": "workspace_runtime_only" if args.workspace_runtime_only else "repo_catalog_inclusive",
            "catalogs_checked": [],
            "checked_identity_count": 0,
            "checked_identity_ids": [],
            "violation_count": 0,
            "checked_rows": [],
            "violations": [],
            "pack_scan_policy_id": PACK_SCAN_POLICY_ID,
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

    evaluator = _build_row_evaluator(
        baseline_agent=dict(baseline.get("agent_identity") or {}),
        baseline_scaffold=dict(baseline.get("scaffold_metadata") or {}),
        baseline_meta=dict(baseline.get("meta") or {}),
        baseline_catalog=dict(baseline.get("catalog") or {}),
    )
    payload = collect_active_runtime_pack_closure(
        repo_root=repo_root,
        repo_catalog_arg=args.repo_catalog,
        raw_catalogs=args.catalog,
        include_env_catalog=bool(args.include_env_catalog),
        workspace_runtime_only=bool(args.workspace_runtime_only),
        caller_anchor=Path.cwd().resolve(),
        caller_start=Path(__file__).resolve(),
        payload_status_key="version_baseline_migration_closure_status",
        error_code=ERR_VERSION_BASELINE,
        row_evaluator=evaluator,
        extra_payload={
            "version_baseline": {
                "entry_file": str(baseline.get("entry_path", "")),
                "resolved_file": str(baseline.get("resolved_path", "")),
                "stream_version": str(baseline.get("stream_version", "")),
            }
        },
    )

    print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if str(payload.get("version_baseline_migration_closure_status", "")).strip().upper() == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
