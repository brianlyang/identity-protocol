from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
ERR_DISCOVERY_FAILED = "IP-ILCPCTX-001"
ERR_MATERIALIZATION_FAILED = "IP-ILCPCTX-002"

LAUNCHER_ASSET_RELATIVE_PATHS = (
    Path("scripts/launchers/identity-codex-launcher.manifest.json"),
    Path("scripts/launchers/README.md"),
)


def _load_catalog_doc(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return doc if isinstance(doc, dict) else {}


def _resolve_row_path(*, raw_path: str, catalog_path: Path, identity_id: str) -> Path:
    raw = str(raw_path or "").strip()
    if not raw:
        return (catalog_path.parent / identity_id).resolve()
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (catalog_path.parent / path).resolve()


def _select_runtime_row(*, catalog_path: Path, identity_id: str) -> dict[str, Any]:
    doc = _load_catalog_doc(catalog_path)
    rows = doc.get("identities") or []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("id", "")).strip() != identity_id:
            continue
        return dict(row)
    raise RuntimeError(f"missing_identity_row:{identity_id}")


def _materialized_minimal_runtime_row(*, row: dict[str, Any], identity_id: str, target_pack_path: Path) -> dict[str, Any]:
    return {
        "id": identity_id,
        "status": str(row.get("status", "active") or "active"),
        "profile": str(row.get("profile", "runtime") or "runtime"),
        "runtime_mode": str(row.get("runtime_mode", "local_only") or "local_only"),
        "canonical_scope": "UNKNOWN",
        "pack_path": str(target_pack_path.resolve()),
        "canonical_pack_path": "",
    }


def materialize_launcher_convergence_probe_context(
    *,
    catalog_path: Path,
    identity_id: str,
    target_workspace_root: Path,
    preserve_launcher_assets: bool = False,
) -> dict[str, Any]:
    catalog_path = catalog_path.expanduser().resolve()
    target_workspace_root = target_workspace_root.expanduser().resolve()
    row = _select_runtime_row(catalog_path=catalog_path, identity_id=identity_id)

    source_pack_path = _resolve_row_path(
        raw_path=str(row.get("canonical_pack_path") or row.get("pack_path") or ""),
        catalog_path=catalog_path,
        identity_id=identity_id,
    )
    if not source_pack_path.exists():
        raise RuntimeError(f"missing_source_pack:{source_pack_path}")

    target_identity_home = (target_workspace_root / ".identity").resolve()
    if target_identity_home.exists():
        raise RuntimeError(f"target_identity_home_already_exists:{target_identity_home}")
    target_identity_home.mkdir(parents=True, exist_ok=False)

    target_pack_path = (target_identity_home / identity_id).resolve()
    shutil.copytree(source_pack_path, target_pack_path, symlinks=False, ignore=shutil.ignore_patterns("__pycache__"))

    stripped_assets: list[str] = []
    if not preserve_launcher_assets:
        for relpath in LAUNCHER_ASSET_RELATIVE_PATHS:
            candidate = (target_pack_path / relpath).resolve()
            if candidate.exists():
                candidate.unlink()
                stripped_assets.append(relpath.as_posix())

    materialized_row = _materialized_minimal_runtime_row(
        row=row,
        identity_id=identity_id,
        target_pack_path=target_pack_path,
    )
    target_catalog_path = (target_identity_home / "catalog.local.yaml").resolve()
    target_catalog_path.write_text(
        yaml.safe_dump({"identities": [materialized_row]}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    return {
        "status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "identity_id": identity_id,
        "source_catalog_path": str(catalog_path),
        "source_pack_path": str(source_pack_path),
        "target_workspace_root": str(target_workspace_root),
        "target_identity_home": str(target_identity_home),
        "target_catalog_path": str(target_catalog_path),
        "target_pack_path": str(target_pack_path),
        "source_row_status": str(row.get("status", "") or "").strip(),
        "source_row_profile": str(row.get("profile", "") or "").strip(),
        "source_row_runtime_mode": str(row.get("runtime_mode", "") or "").strip(),
        "preserve_launcher_assets": bool(preserve_launcher_assets),
        "stripped_launcher_assets": stripped_assets,
        "stripped_launcher_asset_count": len(stripped_assets),
        "materialized_catalog_identity_count": 1,
        "materialized_runtime_row": materialized_row,
    }
