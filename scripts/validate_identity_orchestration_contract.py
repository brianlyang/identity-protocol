#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQ_KEYS = [
    "required",
    "task_type_routes",
    "preflight_requirements",
    "fail_classification",
    "evidence_schema_fields",
]
REQ_ROUTE_KEYS = [
    "pipeline",
    "primary_skills",
    "fallback_skills",
    "required_mcp",
    "max_tool_calls",
    "max_runtime_minutes",
]


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")

    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p

    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy

    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate capability orchestration contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate orchestration contract for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    task = _load_json(task_path)
    c = task.get("capability_orchestration_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing capability_orchestration_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        print(f"[FAIL] capability_orchestration_contract missing fields: {missing}")
        return 1

    if c.get("required") is not True:
        print("[FAIL] capability_orchestration_contract.required must be true")
        return 1

    routes = c.get("task_type_routes") or {}
    if not isinstance(routes, dict) or not routes:
        print("[FAIL] task_type_routes must be non-empty object")
        return 1

    rc = 0
    for t, route in routes.items():
        if not isinstance(route, dict):
            print(f"[FAIL] task_type_routes.{t} must be object")
            rc = 1
            continue
        rm = [k for k in REQ_ROUTE_KEYS if k not in route]
        if rm:
            print(f"[FAIL] task_type_routes.{t} missing fields: {rm}")
            rc = 1
        if not isinstance(route.get("pipeline"), list) or not route.get("pipeline"):
            print(f"[FAIL] task_type_routes.{t}.pipeline must be non-empty list")
            rc = 1
        if not isinstance(route.get("primary_skills"), list) or not route.get("primary_skills"):
            print(f"[FAIL] task_type_routes.{t}.primary_skills must be non-empty list")
            rc = 1
        if not isinstance(route.get("required_mcp"), list) or not route.get("required_mcp"):
            print(f"[FAIL] task_type_routes.{t}.required_mcp must be non-empty list")
            rc = 1

    if not isinstance(c.get("preflight_requirements"), list) or not c.get("preflight_requirements"):
        print("[FAIL] preflight_requirements must be non-empty list")
        rc = 1

    expected_fails = {"route_wrong", "skill_gap", "mcp_unavailable", "tool_auth", "data_issue"}
    got_fails = set(c.get("fail_classification") or [])
    if not expected_fails.issubset(got_fails):
        print(f"[FAIL] fail_classification missing: {sorted(expected_fails - got_fails)}")
        rc = 1

    if not isinstance(c.get("evidence_schema_fields"), list) or len(c.get("evidence_schema_fields") or []) < 5:
        print("[FAIL] evidence_schema_fields must be a sufficiently complete list")
        rc = 1

    if rc:
        return 1

    print("Capability orchestration contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
