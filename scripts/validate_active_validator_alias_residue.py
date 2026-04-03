#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
ERR_ALIAS_RESIDUE = "IP-VALIAS-001"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
WRAPPER_TOKENS = (
    "validate_v16_cross_verification_tracks.py",
    "validate_v16_intake_evidence_core.py",
    "validate_v16_intake_evidence_quorum.py",
    "validate_v16_cross_workflow_schema.py",
    "validate_v16_dedup_monotonicity.py",
    "validate_v16_skill_path_integrity.py",
)
STRICT_TARGETS = (
    "scripts/create_identity_pack.py",
    "scripts/validate_required_contract_coverage.py",
    "scripts/validate_replay_archive_contract.py",
    "identity/store-manager/CURRENT_TASK.json",
    "identity/packs/system-requirements-analyst/CURRENT_TASK.json",
    "identity/protocol/mappings/control-plane-status.v1.6.json",
)
CONTRACT_BINDING_TARGET = "identity/protocol/mappings/contract-binding.v1.6.yaml"


def _resolve_repo_root(raw_repo_root: str) -> Path:
    token = str(raw_repo_root or "").strip()
    if token:
        return Path(token).expanduser().resolve()
    return REPO_ROOT


def _workspace_root(repo_root: Path) -> Path:
    return repo_root.parent if repo_root.name == "identity-protocol-local" else repo_root


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _discover_catalog_path(repo_root: Path, explicit_catalog: str) -> tuple[Path | None, str]:
    token = str(explicit_catalog or "").strip()
    if token:
        path = Path(token).expanduser().resolve()
        return (path, "") if path.exists() else (path, "catalog_not_found")

    env_catalog = str(os.environ.get("IDENTITY_CATALOG", "")).strip()
    candidates: list[Path] = []
    if env_catalog:
        candidates.append(Path(env_catalog).expanduser().resolve())
    workspace_catalog = (_workspace_root(repo_root) / ".identity" / "catalog.local.yaml").resolve()
    repo_catalog = (repo_root / ".identity" / "catalog.local.yaml").resolve()
    for candidate in (workspace_catalog, repo_catalog):
        if candidate not in candidates:
            candidates.append(candidate)
    for candidate in candidates:
        if candidate.exists():
            return candidate, ""
    return None, "catalog_not_found"


def _scan_text_target(path: Path, rel_label: str, violations: list[dict[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for token in WRAPPER_TOKENS:
        if token in text:
            violations.append(
                {
                    "file": rel_label,
                    "reason": "wrapper_validator_still_active",
                    "token": token,
                }
            )


def _collect_runtime_pack_targets(catalog_path: Path) -> list[dict[str, str]]:
    doc = _load_yaml(catalog_path)
    rows = doc.get("identities")
    if not isinstance(rows, list):
        return []

    targets: list[dict[str, str]] = []
    seen: set[Path] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status", "")).strip().lower()
        profile = str(row.get("profile", "")).strip().lower()
        runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
        if status != "active" or profile != "runtime" or runtime_mode == "demo_only":
            continue
        pack_token = str(row.get("canonical_pack_path") or row.get("pack_path") or "").strip()
        if not pack_token:
            continue
        task_path = (Path(pack_token).expanduser().resolve() / "CURRENT_TASK.json").resolve()
        if task_path in seen or not task_path.exists():
            continue
        seen.add(task_path)
        targets.append(
            {
                "identity_id": str(row.get("id", "")).strip(),
                "task_path": str(task_path),
            }
        )
    return targets


def _walk_json_strings(value: Any, *, path: str = "$") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_key = str(key)
            child_path = f"{path}.{child_key}"
            rows.extend(_walk_json_strings(child, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_walk_json_strings(child, path=f"{path}[{index}]"))
    elif isinstance(value, str):
        rows.append((path, value))
    return rows


def _scan_runtime_pack_target(target: dict[str, str], violations: list[dict[str, str]]) -> None:
    task_path = Path(target["task_path"]).resolve()
    try:
        payload = json.loads(task_path.read_text(encoding="utf-8"))
    except Exception as exc:
        violations.append(
            {
                "file": str(task_path),
                "reason": "runtime_pack_current_task_parse_failed",
                "token": str(exc),
            }
        )
        return

    for json_path, value in _walk_json_strings(payload):
        for token in WRAPPER_TOKENS:
            if value != f"scripts/{token}":
                continue
            violations.append(
                {
                    "file": str(task_path),
                    "identity_id": target.get("identity_id", ""),
                    "reason": "wrapper_validator_still_active_runtime_pack",
                    "token": token,
                    "json_path": json_path,
                }
            )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate that compatibility wrapper validators no longer remain active.")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = _resolve_repo_root(args.repo_root)
    violations: list[dict[str, str]] = []

    for rel in STRICT_TARGETS:
        _scan_text_target((repo_root / rel).resolve(), rel, violations)

    contract_binding_text = (repo_root / CONTRACT_BINDING_TARGET).read_text(encoding="utf-8")
    for token in WRAPPER_TOKENS:
        marker = f"{token}::wrapper_compatibility_optional"
        if token in contract_binding_text and marker not in contract_binding_text:
            violations.append(
                {
                    "file": CONTRACT_BINDING_TARGET,
                    "reason": "wrapper_validator_not_demoted_to_optional_alias",
                    "token": token,
                }
            )

    catalog_path, catalog_error = _discover_catalog_path(repo_root, args.catalog)
    runtime_pack_targets: list[dict[str, str]] = []
    runtime_pack_inventory_status = STATUS_SKIPPED_NOT_REQUIRED
    if catalog_path and not catalog_error:
        runtime_pack_targets = _collect_runtime_pack_targets(catalog_path)
        runtime_pack_inventory_status = STATUS_PASS_REQUIRED
        for target in runtime_pack_targets:
            _scan_runtime_pack_target(target, violations)

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "active_validator_alias_residue_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_ALIAS_RESIDUE,
        "repo_root": str(repo_root),
        "strict_targets": list(STRICT_TARGETS),
        "contract_binding_target": CONTRACT_BINDING_TARGET,
        "runtime_catalog_path": "" if not catalog_path else str(catalog_path),
        "runtime_catalog_error": catalog_error,
        "runtime_pack_inventory_status": runtime_pack_inventory_status,
        "runtime_pack_targets": runtime_pack_targets,
        "violations": violations,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
