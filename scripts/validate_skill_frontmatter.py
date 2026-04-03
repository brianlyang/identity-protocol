#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from tool_vendor_governance_common import (
    contract_required,
    load_json,
    path_within,
    resolve_pack_and_task,
    root_family_for_path,
    select_skill_enforcement_roots,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_FRONTMATTER_MISSING = "IP-SFRONT-001"
ERR_FRONTMATTER_PARSE = "IP-SFRONT-002"
ERR_FRONTMATTER_REQUIRED_FIELDS = "IP-SFRONT-003"
ERR_SKILL_PATH_DEPENDENCY = "IP-SFRONT-004"

STRICT_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "scan",
    "three-plane",
    "inspection",
    "mutation",
}

CONTRACT_KEYS = (
    "skill_frontmatter_contract_v1",
    "skill_frontmatter_contract",
    "rq_040_skill_frontmatter_contract_v1",
)
DEFAULT_REQUIRED_FIELDS = (
    "skill_id",
    "version",
    "owner",
    "source",
)
DEFAULT_SELECTED_PATH_SCOPE_POLICY = "all_selected_paths"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog_doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    rows = catalog_doc.get("identities")
    if not isinstance(rows, list):
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("id", "")).strip() != identity_id:
            continue
        profile = str(row.get("profile", "")).strip().lower()
        runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
        return profile == "fixture" or runtime_mode == "demo_only"
    return False


def _run_skill_path_integrity(*, catalog: Path, identity_id: str, operation: str) -> tuple[int, dict[str, Any], str]:
    cmd = [
        "python3",
        "scripts/validate_skill_path_integrity.py",
        "--catalog",
        str(catalog),
        "--identity-id",
        identity_id,
        "--operation",
        operation,
        "--json-only",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    raw = (proc.stdout or "").strip()
    payload: dict[str, Any] = {}
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                payload = data
        except Exception:
            payload = {}
    tail = ""
    if raw:
        tail = raw.splitlines()[-1]
    elif (proc.stderr or "").strip():
        tail = (proc.stderr or "").strip().splitlines()[-1]
    return proc.returncode, payload, tail


def _parse_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---\n"):
        return None, "frontmatter_header_missing"
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return None, "frontmatter_terminator_missing"
    body = parts[0][4:] if parts[0].startswith("---\n") else parts[0]
    try:
        loaded = yaml.safe_load(body) or {}
    except Exception:
        return None, "frontmatter_yaml_parse_failed"
    if not isinstance(loaded, dict):
        return None, "frontmatter_yaml_not_object"
    return loaded, ""


def _policy_token(contract: dict[str, Any]) -> str:
    token = str(contract.get("selected_path_scope_policy", "")).strip().lower()
    return token or DEFAULT_SELECTED_PATH_SCOPE_POLICY


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate skill frontmatter contract (RQ-040).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required = contract_required(contract)
    if args.force_required:
        required = True

    fixture_identity = _is_fixture_identity(catalog_path, args.identity_id)
    if fixture_identity:
        required = False

    required_fields_raw = contract.get("required_frontmatter_fields")
    if isinstance(required_fields_raw, list):
        required_fields = [str(x).strip() for x in required_fields_raw if str(x).strip()]
    else:
        required_fields = [str(x) for x in DEFAULT_REQUIRED_FIELDS]

    rc_skill, skill_payload, skill_tail = _run_skill_path_integrity(
        catalog=catalog_path,
        identity_id=args.identity_id,
        operation=args.operation,
    )
    skill_status = str(skill_payload.get("path_integrity_status", "")).strip().upper()
    skill_rows = skill_payload.get("skill_path_rows") if isinstance(skill_payload.get("skill_path_rows"), list) else []
    active_repo_root = Path(str(skill_payload.get("active_repo_root", "")).strip() or pack_path.parent.parent).expanduser().resolve()
    active_runtime_root = Path(
        str(skill_payload.get("active_runtime_root", "")).strip() or (Path.home() / ".codex")
    ).expanduser().resolve()
    allowed_skill_roots = [
        Path(str(raw)).expanduser().resolve()
        for raw in (skill_payload.get("allowed_skill_roots") or [])
        if str(raw).strip()
    ]
    selected_path_scope_policy = _policy_token(contract)
    enforcement_roots = select_skill_enforcement_roots(
        allowed_skill_roots=allowed_skill_roots,
        active_repo_root=active_repo_root,
        active_runtime_root=active_runtime_root,
        policy=selected_path_scope_policy,
    )

    frontmatter_rows: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    missing_frontmatter_skills: list[str] = []
    missing_required_field_rows: list[dict[str, Any]] = []
    skipped_unmanaged_rows: list[dict[str, Any]] = []

    for row in skill_rows:
        if not isinstance(row, dict):
            continue
        skill = str(row.get("skill", "")).strip()
        path_raw = str(row.get("path", "")).strip()
        path_exists = bool(row.get("path_exists", False))
        if not skill or not path_raw or not path_exists:
            continue
        skill_path = Path(path_raw).expanduser().resolve()
        if not skill_path.exists() or not skill_path.is_file():
            continue
        selected_root_family = root_family_for_path(skill_path, allowed_skill_roots)
        governed_selected_path = path_within(skill_path, active_repo_root)
        if enforcement_roots and not any(path_within(skill_path, root) for root in enforcement_roots):
            skipped_unmanaged_rows.append(
                {
                    "skill": skill,
                    "path": str(skill_path),
                    "selected_root_family": str(selected_root_family) if selected_root_family else "",
                    "governed_selected_path": governed_selected_path,
                    "skip_reason": "selected_path_outside_enforcement_scope",
                }
            )
            continue

        frontmatter, parse_reason = _parse_frontmatter(skill_path)
        missing_fields: list[str] = []
        if frontmatter is None:
            missing_frontmatter_skills.append(skill)
            if parse_reason:
                parse_errors.append(f"{skill}:{parse_reason}")
        else:
            for field in required_fields:
                value = frontmatter.get(field)
                if str(value or "").strip() == "":
                    missing_fields.append(field)
            if missing_fields:
                missing_required_field_rows.append(
                    {
                        "skill": skill,
                        "path": str(skill_path),
                        "missing_fields": missing_fields,
                    }
                )

        frontmatter_rows.append(
            {
                "skill": skill,
                "path": str(skill_path),
                "frontmatter_parse_reason": parse_reason,
                "frontmatter_found": frontmatter is not None,
                "frontmatter_keys": sorted(list(frontmatter.keys())) if isinstance(frontmatter, dict) else [],
                "missing_required_fields": missing_fields,
                "selected_root_family": str(selected_root_family) if selected_root_family else "",
                "governed_selected_path": governed_selected_path,
            }
        )

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "fixture_identity": fixture_identity,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": True,
        "requiredization_current_round_linked": bool(skill_rows),
        "skill_frontmatter_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "required_frontmatter_fields": required_fields,
        "selected_path_scope_policy": selected_path_scope_policy,
        "active_repo_root": str(active_repo_root),
        "active_runtime_root": str(active_runtime_root),
        "enforcement_roots": [str(root) for root in enforcement_roots],
        "frontmatter_rows": frontmatter_rows,
        "skipped_unmanaged_rows": skipped_unmanaged_rows,
        "missing_frontmatter_skills": missing_frontmatter_skills,
        "frontmatter_parse_errors": parse_errors,
        "missing_required_field_rows": missing_required_field_rows,
        "skill_path_integrity": {
            "status": skill_status,
            "rc": rc_skill,
            "tail": skill_tail,
            "stale_reasons": list(skill_payload.get("stale_reasons") or []) if isinstance(skill_payload.get("stale_reasons"), list) else [],
        },
        "evidence_ref": str(task_path),
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["fixture_profile_scope"] if fixture_identity else ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if rc_skill != 0 or skill_status != STATUS_PASS_REQUIRED:
        payload["skill_frontmatter_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SKILL_PATH_DEPENDENCY
        payload["stale_reasons"] = ["skill_path_integrity_not_pass_required"]
        _emit(payload, json_only=args.json_only)
        return 1

    if missing_frontmatter_skills:
        payload["skill_frontmatter_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_FRONTMATTER_MISSING
        payload["stale_reasons"] = ["skill_frontmatter_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if parse_errors:
        payload["skill_frontmatter_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_FRONTMATTER_PARSE
        payload["stale_reasons"] = ["skill_frontmatter_parse_error"]
        _emit(payload, json_only=args.json_only)
        return 1

    if missing_required_field_rows:
        payload["skill_frontmatter_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_FRONTMATTER_REQUIRED_FIELDS
        payload["stale_reasons"] = ["skill_frontmatter_required_fields_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["skill_frontmatter_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
