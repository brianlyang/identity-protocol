#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from resolve_identity_context import resolve_identity, resolve_local_catalog_path, resolve_repo_catalog_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
ERR_RUNTIME_CATALOG_METADATA_INVALID = "IP-RCATMETA-001"


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _dump_yaml(path: Path, doc: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _iter_runtime_rows(doc: dict[str, Any], *, identity_id: str = "") -> list[dict[str, Any]]:
    rows = doc.get("identities")
    if not isinstance(rows, list):
        return []
    target = str(identity_id or "").strip()
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_identity_id = str(row.get("id", "")).strip()
        if target and row_identity_id != target:
            continue
        if not row_identity_id:
            continue
        if str(row.get("status", "")).strip().lower() != "active":
            continue
        if str(row.get("profile", "")).strip().lower() != "runtime":
            continue
        if str(row.get("runtime_mode", "")).strip().lower() == "demo_only":
            continue
        out.append(row)
    return out


def _resolve_row_path(raw_path: str, *, catalog_path: Path, fallback_identity_id: str) -> Path:
    raw = str(raw_path or "").strip()
    if not raw:
        return (catalog_path.parent / fallback_identity_id).resolve()
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (catalog_path.parent / path).resolve()


def _inspect_row(
    *,
    row: dict[str, Any],
    catalog_path: Path,
    repo_catalog_path: Path,
) -> dict[str, Any]:
    identity_id = str(row.get("id", "")).strip()
    raw_pack_path = str(row.get("pack_path", "")).strip()
    raw_canonical_pack_path = str(row.get("canonical_pack_path", "")).strip()
    raw_canonical_scope = str(row.get("canonical_scope", "")).strip().upper()

    row_pack_path = _resolve_row_path(raw_pack_path, catalog_path=catalog_path, fallback_identity_id=identity_id)
    canonical_pack_path = _resolve_row_path(
        raw_canonical_pack_path,
        catalog_path=catalog_path,
        fallback_identity_id=identity_id,
    ) if raw_canonical_pack_path else Path("")

    stale_reasons: list[str] = []
    resolved: dict[str, Any] = {}
    resolve_error = ""
    try:
        resolved = resolve_identity(
            identity_id,
            repo_catalog_path,
            catalog_path,
            preferred_scope="",
            allow_conflict=False,
        )
    except Exception as exc:  # pragma: no cover - defensive transport guard
        resolve_error = f"{type(exc).__name__}:{exc}"
        stale_reasons.append("runtime_truth_unresolved")

    expected_pack_path = Path(str(resolved.get("pack_path", "")).strip()).expanduser().resolve() if resolved else Path("")
    expected_scope = str(resolved.get("resolved_scope", "")).strip().upper()

    if not raw_pack_path:
        stale_reasons.append("pack_path_missing")
    elif expected_pack_path and row_pack_path != expected_pack_path:
        stale_reasons.append("pack_path_mismatch")

    if not raw_canonical_pack_path:
        stale_reasons.append("canonical_pack_path_missing")
    elif expected_pack_path and canonical_pack_path != expected_pack_path:
        stale_reasons.append("canonical_pack_path_mismatch")

    if not raw_canonical_scope:
        stale_reasons.append("canonical_scope_missing")
    elif raw_canonical_scope == "UNKNOWN":
        stale_reasons.append("canonical_scope_unknown")
    elif expected_scope and raw_canonical_scope != expected_scope:
        stale_reasons.append("canonical_scope_mismatch")

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    return {
        "identity_id": identity_id,
        "catalog_path": str(catalog_path),
        "status": status,
        "row_status": str(row.get("status", "")).strip(),
        "row_profile": str(row.get("profile", "")).strip(),
        "row_runtime_mode": str(row.get("runtime_mode", "")).strip(),
        "pack_path": raw_pack_path,
        "pack_path_resolved": str(row_pack_path),
        "canonical_pack_path": raw_canonical_pack_path,
        "canonical_pack_path_resolved": str(canonical_pack_path) if raw_canonical_pack_path else "",
        "canonical_scope": raw_canonical_scope,
        "resolved_scope": expected_scope,
        "resolved_pack_path": str(expected_pack_path) if resolved else "",
        "resolved_source_layer": str(resolved.get("source_layer", "")).strip() if resolved else "",
        "resolve_error": resolve_error,
        "stale_reasons": stale_reasons,
    }


def inspect_runtime_catalog_metadata_hygiene(
    *,
    catalog_path: str | Path,
    repo_catalog_path: str | Path,
    identity_id: str = "",
    require_active: bool = False,
) -> dict[str, Any]:
    resolved_catalog_path = resolve_local_catalog_path(catalog_path, start=Path.cwd())
    resolved_repo_catalog_path = resolve_repo_catalog_path(repo_catalog_path, start=Path(__file__).resolve())
    catalog_doc = _safe_load_yaml(resolved_catalog_path)
    rows = _iter_runtime_rows(catalog_doc, identity_id=identity_id)

    checked_rows = [
        _inspect_row(
            row=row,
            catalog_path=resolved_catalog_path,
            repo_catalog_path=resolved_repo_catalog_path,
        )
        for row in rows
    ]
    violations = [row for row in checked_rows if str(row.get("status", "")).strip().upper() != STATUS_PASS_REQUIRED]
    stale_reasons: list[str] = []
    if not checked_rows and require_active:
        stale_reasons.append("no_active_runtime_identities_found")
    if not checked_rows and not require_active:
        status = STATUS_SKIPPED_NOT_REQUIRED
    else:
        status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED

    return {
        "runtime_catalog_metadata_hygiene_status": status,
        "error_code": "" if status != STATUS_FAIL_REQUIRED else ERR_RUNTIME_CATALOG_METADATA_INVALID,
        "required_contract": bool(require_active or checked_rows),
        "catalog_path": str(resolved_catalog_path),
        "repo_catalog": str(resolved_repo_catalog_path),
        "checked_identity_count": len(checked_rows),
        "violation_count": len(violations),
        "checked_rows": checked_rows,
        "violations": violations,
        "stale_reasons": stale_reasons,
    }


def repair_runtime_catalog_metadata_hygiene(
    *,
    catalog_path: str | Path,
    repo_catalog_path: str | Path,
    identity_id: str = "",
    apply: bool = False,
    require_active: bool = False,
) -> dict[str, Any]:
    resolved_catalog_path = resolve_local_catalog_path(catalog_path, start=Path.cwd())
    resolved_repo_catalog_path = resolve_repo_catalog_path(repo_catalog_path, start=Path(__file__).resolve())
    preflight = inspect_runtime_catalog_metadata_hygiene(
        catalog_path=resolved_catalog_path,
        repo_catalog_path=resolved_repo_catalog_path,
        identity_id=identity_id,
        require_active=require_active,
    )
    catalog_doc = _safe_load_yaml(resolved_catalog_path)
    rows = catalog_doc.get("identities")
    if not isinstance(rows, list):
        rows = []

    violation_ids = {
        str(row.get("identity_id", "")).strip()
        for row in (preflight.get("violations") or [])
        if isinstance(row, dict) and str(row.get("identity_id", "")).strip()
    }
    repair_rows: list[dict[str, Any]] = []
    changed = False

    for row in rows:
        if not isinstance(row, dict):
            continue
        row_identity_id = str(row.get("id", "")).strip()
        if row_identity_id not in violation_ids:
            continue
        resolved = resolve_identity(
            row_identity_id,
            resolved_repo_catalog_path,
            resolved_catalog_path,
            preferred_scope="",
            allow_conflict=False,
        )
        expected_pack_path = str(Path(str(resolved.get("pack_path", "")).strip()).expanduser().resolve())
        expected_scope = str(resolved.get("resolved_scope", "")).strip().upper()
        row_changes: list[str] = []

        if str(row.get("pack_path", "")).strip() != expected_pack_path:
            row["pack_path"] = expected_pack_path
            row_changes.append("pack_path")
        if str(row.get("canonical_pack_path", "")).strip() != expected_pack_path:
            row["canonical_pack_path"] = expected_pack_path
            row_changes.append("canonical_pack_path")
        if str(row.get("canonical_scope", "")).strip().upper() != expected_scope:
            row["canonical_scope"] = expected_scope
            row_changes.append("canonical_scope")

        if row_changes:
            changed = True
        repair_rows.append(
            {
                "identity_id": row_identity_id,
                "resolved_pack_path": expected_pack_path,
                "resolved_scope": expected_scope,
                "changed_fields": row_changes,
            }
        )

    if apply and changed:
        catalog_doc["identities"] = rows
        _dump_yaml(resolved_catalog_path, catalog_doc)

    postflight = inspect_runtime_catalog_metadata_hygiene(
        catalog_path=resolved_catalog_path,
        repo_catalog_path=resolved_repo_catalog_path,
        identity_id=identity_id,
        require_active=require_active,
    ) if apply else preflight

    repair_status = "already_hygienic"
    if violation_ids and not apply:
        repair_status = "dry_run_preview"
    elif violation_ids and apply and changed:
        repair_status = "apply_repaired"
    elif violation_ids and apply and not changed:
        repair_status = "apply_noop"

    return {
        "runtime_catalog_metadata_repair_status": (
            STATUS_PASS_REQUIRED
            if str(postflight.get("runtime_catalog_metadata_hygiene_status", "")).strip().upper()
            in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED}
            else STATUS_FAIL_REQUIRED
        ),
        "repair_status": repair_status,
        "apply_requested": bool(apply),
        "changed": bool(changed),
        "planned_repair_count": len(violation_ids),
        "repaired_identity_count": len([row for row in repair_rows if row.get("changed_fields")]),
        "repair_rows": repair_rows,
        "precheck": preflight,
        "postcheck": postflight,
        "runtime_catalog_metadata_hygiene_status": str(
            postflight.get("runtime_catalog_metadata_hygiene_status", "")
        ).strip(),
        "error_code": "" if str(postflight.get("runtime_catalog_metadata_hygiene_status", "")).strip().upper()
        in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED}
        else ERR_RUNTIME_CATALOG_METADATA_INVALID,
    }
