from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
ERR_DISCOVERY_FAILED = "IP-XWCTX-001"
ERR_MATERIALIZATION_FAILED = "IP-XWCTX-002"
ERR_ACTIVE_REPORT_DISCOVERY_FAILED = "IP-XWCTX-003"


def _load_catalog_doc(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return doc if isinstance(doc, dict) else {}


def active_runtime_identity_ids(catalog_path: Path) -> list[str]:
    doc = _load_catalog_doc(catalog_path)
    rows = doc.get("identities") or []
    active: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        identity_id = str(row.get("id", "")).strip()
        if not identity_id:
            continue
        if str(row.get("status", "")).strip().lower() != "active":
            continue
        if str(row.get("profile", "")).strip().lower() != "runtime":
            continue
        if str(row.get("runtime_mode", "")).strip().lower() == "demo_only":
            continue
        active.append(identity_id)
    return active


def discover_cross_workspace_runtime_catalog(
    *,
    current_workspace_root: Path,
    explicit_catalog: str = "",
) -> dict[str, Any]:
    current_workspace_root = current_workspace_root.expanduser().resolve()
    current_catalog = (current_workspace_root / ".identity" / "catalog.local.yaml").resolve()

    candidate_catalogs: list[Path] = []
    if str(explicit_catalog or "").strip():
        candidate_catalogs.append(Path(str(explicit_catalog).strip()).expanduser().resolve())
    else:
        sibling_root = current_workspace_root.parent.resolve()
        for path in sorted(sibling_root.glob("*/.identity/catalog.local.yaml")):
            resolved = path.resolve()
            if resolved == current_catalog:
                continue
            candidate_catalogs.append(resolved)

    for candidate in candidate_catalogs:
        if not candidate.exists() or not candidate.is_file():
            continue
        identity_ids = active_runtime_identity_ids(candidate)
        if identity_ids:
            return {
                "source_catalog_path": str(candidate.resolve()),
                "source_workspace_root": str(candidate.resolve().parent.parent),
                "active_runtime_identity_ids": identity_ids,
                "checked_identity_count": len(identity_ids),
                "first_identity_id": identity_ids[0],
            }
    raise RuntimeError("no eligible cross-workspace runtime catalog discovered")


def materialize_cross_workspace_runtime_identity_home(
    *,
    source_workspace_root: Path,
    target_workspace_root: Path,
) -> dict[str, Any]:
    source_workspace_root = source_workspace_root.expanduser().resolve()
    target_workspace_root = target_workspace_root.expanduser().resolve()
    source_identity = (source_workspace_root / ".identity").resolve()
    target_identity = (target_workspace_root / ".identity").resolve()
    if not source_identity.exists():
        raise RuntimeError(f"source_identity_home_missing:{source_identity}")
    if target_identity.exists():
        raise RuntimeError(f"target_identity_home_already_exists:{target_identity}")

    shutil.copytree(source_identity, target_identity, symlinks=False, ignore=shutil.ignore_patterns("__pycache__"))

    catalog_path = (target_identity / "catalog.local.yaml").resolve()
    doc = _load_catalog_doc(catalog_path)
    rows = doc.get("identities") or []
    rewritten: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        next_row = dict(row)
        identity_id = str(next_row.get("id", "")).strip()
        if identity_id:
            pack_path = (target_identity / identity_id).resolve()
            next_row["pack_path"] = str(pack_path)
            next_row["canonical_pack_path"] = ""
            next_row["canonical_scope"] = "UNKNOWN"
        rewritten.append(next_row)
    doc["identities"] = rewritten
    catalog_path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")

    return {
        "target_identity_home": str(target_identity),
        "target_catalog_path": str(catalog_path),
        "target_workspace_root": str(target_workspace_root),
    }


def discover_materialized_active_execution_report(
    *,
    materialized_catalog_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    from strict_live_evidence_resolution_common import resolve_active_execution_context

    materialized_catalog_path = materialized_catalog_path.expanduser().resolve()
    repo_root = repo_root.expanduser().resolve()
    doc = _load_catalog_doc(materialized_catalog_path)
    rows = doc.get("identities") or []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("status", "")).strip().lower() != "active":
            continue
        if str(row.get("profile", "")).strip().lower() != "runtime":
            continue
        if str(row.get("runtime_mode", "")).strip().lower() == "demo_only":
            continue
        identity_id = str(row.get("id", "")).strip()
        pack_path = Path(str(row.get("pack_path", "")).strip()).expanduser().resolve()
        if not identity_id or not pack_path.exists():
            continue
        context = resolve_active_execution_context(pack_path)
        report_path = str(context.get("report_path", "")).strip()
        if not report_path:
            continue
        resolved_report = Path(report_path).expanduser().resolve()
        if not resolved_report.exists():
            continue
        return {
            "identity_id": identity_id,
            "pack_path": str(pack_path),
            "report_path": str(resolved_report),
            "run_id": str(context.get("run_id", "")).strip(),
            "repo_root": str(repo_root),
        }
    raise RuntimeError("no eligible runtime identity with active execution report discovered")


def materialize_cross_workspace_runtime_probe_context(
    *,
    current_workspace_root: Path,
    target_workspace_root: Path,
    explicit_catalog: str = "",
    repo_root: Path | None = None,
    require_active_execution_report: bool = False,
) -> dict[str, Any]:
    discovery = discover_cross_workspace_runtime_catalog(
        current_workspace_root=current_workspace_root,
        explicit_catalog=explicit_catalog,
    )
    materialized = materialize_cross_workspace_runtime_identity_home(
        source_workspace_root=Path(str(discovery["source_workspace_root"])),
        target_workspace_root=target_workspace_root,
    )
    payload = {
        "status": STATUS_PASS_REQUIRED,
        "error_code": "",
        **discovery,
        **materialized,
    }
    if repo_root is not None:
        try:
            active_report = discover_materialized_active_execution_report(
                materialized_catalog_path=Path(str(materialized["target_catalog_path"])),
                repo_root=repo_root,
            )
            payload["active_execution_report"] = active_report
        except Exception as exc:
            if require_active_execution_report:
                raise RuntimeError(str(exc)) from exc
            payload["active_execution_report"] = {
                "identity_id": "",
                "pack_path": "",
                "report_path": "",
                "run_id": "",
                "discovery_error": str(exc),
            }
    return payload
