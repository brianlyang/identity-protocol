#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


REQ_TOP = [
    "trigger_contract",
    "patch_surface_contract",
    "validation_contract",
    "replay_contract",
]

REQ_TRIGGER_KEYS = ["mandatory_conditions", "max_attempts_before_update"]
REQ_PATCH_KEYS = ["required_files", "required_rulebook_update"]
REQ_VALIDATION_KEYS = ["required_checks", "must_pass_all"]
REQ_REPLAY_KEYS = ["replay_required", "replay_same_case_required", "replay_fail_action"]


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


def _require_keys(block: dict[str, Any], keys: list[str], prefix: str) -> list[str]:
    missing = []
    for k in keys:
        if k not in block:
            missing.append(f"{prefix}.{k}")
    return missing


def _resolve_replay_evidence_path(identity_id: str, replay_contract: dict[str, Any], override: str) -> Path:
    if override:
        return Path(override)

    pattern = str(replay_contract.get("evidence_path_pattern") or "")
    if pattern:
        matched = sorted(Path(".").glob(pattern))
        if matched:
            return matched[-1]

    return Path(f"identity/runtime/examples/{identity_id}-update-replay-sample.json")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity update lifecycle contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--replay-evidence", default="")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"[FAIL] missing catalog: {catalog_path}")
        return 1

    try:
        task_path = _resolve_current_task(catalog_path, args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate update lifecycle for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    try:
        task = _load_json(task_path)
    except Exception as e:
        print(f"[FAIL] invalid CURRENT_TASK json: {e}")
        return 1

    gates = task.get("gates") or {}
    if gates.get("identity_update_gate") != "required":
        print("[FAIL] gates.identity_update_gate must be required")
        return 1
    print("[OK] gates.identity_update_gate=required")

    c = task.get("identity_update_lifecycle_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing identity_update_lifecycle_contract")
        return 1

    rc = 0
    for k in REQ_TOP:
        if k not in c:
            print(f"[FAIL] identity_update_lifecycle_contract missing: {k}")
            rc = 1
        else:
            print(f"[OK] identity_update_lifecycle_contract.{k} present")

    if rc:
        return 1

    trigger = c.get("trigger_contract") or {}
    patch = c.get("patch_surface_contract") or {}
    valid = c.get("validation_contract") or {}
    replay = c.get("replay_contract") or {}

    missing = []
    missing += _require_keys(trigger, REQ_TRIGGER_KEYS, "trigger_contract")
    missing += _require_keys(patch, REQ_PATCH_KEYS, "patch_surface_contract")
    missing += _require_keys(valid, REQ_VALIDATION_KEYS, "validation_contract")
    missing += _require_keys(replay, REQ_REPLAY_KEYS, "replay_contract")

    if missing:
        print(f"[FAIL] missing lifecycle fields: {missing}")
        return 1

    required_files = set(patch.get("required_files") or [])
    expected_files = {
        "CURRENT_TASK.json",
        "IDENTITY_PROMPT.md",
        "RULEBOOK.jsonl",
        "TASK_HISTORY.md",
    }
    if not expected_files.issubset(required_files):
        print(f"[FAIL] patch_surface_contract.required_files missing expected files: {sorted(expected_files - required_files)}")
        return 1
    print("[OK] patch_surface_contract.required_files contains all mandatory surfaces")

    required_file_paths = patch.get("required_file_paths") or []
    if required_file_paths:
        missing_paths = [p for p in required_file_paths if not Path(str(p)).exists()]
        if missing_paths:
            print(f"[FAIL] patch_surface_contract.required_file_paths not found: {missing_paths}")
            return 1
        print("[OK] patch_surface_contract.required_file_paths all exist")

    required_checks = set(valid.get("required_checks") or [])
    expected_checks = {
        "scripts/validate_identity_runtime_contract.py",
        "scripts/validate_identity_upgrade_prereq.py",
        "scripts/validate_identity_update_lifecycle.py",
        "scripts/validate_identity_trigger_regression.py",
        "scripts/validate_identity_collab_trigger.py",
        "scripts/validate_identity_install_safety.py",
        "scripts/validate_identity_experience_feedback_governance.py",
        "scripts/validate_identity_capability_arbitration.py",
    }
    if not expected_checks.issubset(required_checks):
        print(f"[FAIL] validation_contract.required_checks missing expected checks: {sorted(expected_checks - required_checks)}")
        return 1
    print("[OK] validation_contract.required_checks contains mandatory validators")

    trigger_regression = task.get("trigger_regression_contract") or {}
    if not isinstance(trigger_regression, dict) or not trigger_regression:
        print("[FAIL] missing trigger_regression_contract")
        return 1
    print("[OK] trigger_regression_contract present")

    # Replay evidence validation (execution-level)
    replay_evidence_path = _resolve_replay_evidence_path(args.identity_id, replay, args.replay_evidence)
    if not replay_evidence_path.exists():
        print(f"[FAIL] replay evidence file not found: {replay_evidence_path}")
        return 1

    try:
        replay_evidence = _load_json(replay_evidence_path)
    except Exception as e:
        print(f"[FAIL] replay evidence invalid json: {e}")
        return 1

    print(f"[OK] replay evidence loaded: {replay_evidence_path}")

    required_replay_fields = set(replay.get("required_fields") or ["identity_id", "replay_status", "patched_files", "validation_checks_passed"])
    missing_replay_fields = [f for f in required_replay_fields if f not in replay_evidence]
    if missing_replay_fields:
        print(f"[FAIL] replay evidence missing fields: {missing_replay_fields}")
        return 1

    if str(replay_evidence.get("identity_id") or "") != args.identity_id:
        print(
            f"[FAIL] replay evidence identity mismatch: expected={args.identity_id}, got={replay_evidence.get('identity_id')}"
        )
        return 1

    replay_status = str(replay_evidence.get("replay_status") or "")
    if replay_status != "PASS":
        print(f"[FAIL] replay evidence replay_status must be PASS, got={replay_status}")
        return 1

    patched_files = set(replay_evidence.get("patched_files") or [])
    if not expected_files.issubset(patched_files):
        print(f"[FAIL] replay evidence patched_files missing mandatory surfaces: {sorted(expected_files - patched_files)}")
        return 1

    checks_passed = set(replay_evidence.get("validation_checks_passed") or [])
    if not required_checks.issubset(checks_passed):
        print(
            f"[FAIL] replay evidence validation_checks_passed missing required checks: {sorted(required_checks - checks_passed)}"
        )
        return 1

    routes = ((task.get("routing_contract") or {}).get("problem_type_routes") or {})
    cap_gap = routes.get("capability_gap") or []
    if "identity-creator" not in cap_gap:
        print("[FAIL] routing_contract.problem_type_routes.capability_gap must include identity-creator")
        return 1
    print("[OK] capability_gap route includes identity-creator")

    print("Identity update lifecycle contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
