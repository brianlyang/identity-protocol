#!/usr/bin/env python3
"""Validate identity catalog against schema + protocol semantics (all identities)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import validate as jsonschema_validate

REQ_TASK_KEYS = {
    "objective",
    "state_machine",
    "gates",
    "source_of_truth",
    "escalation_policy",
    "required_artifacts",
    "post_execution_mandatory",
    "evaluation_contract",
    "reasoning_loop_contract",
    "routing_contract",
    "rulebook_contract",
    "learning_verification_contract",
    "blocker_taxonomy_contract",
    "collaboration_trigger_contract",
    "capability_orchestration_contract",
    "knowledge_acquisition_contract",
    "experience_feedback_contract",
    "install_safety_contract",
    "install_provenance_contract",
    "ci_enforcement_contract",
    "capability_arbitration_contract",
    "self_upgrade_enforcement_contract",
}

REQ_PACK_FILES = [
    "IDENTITY_PROMPT.md",
    "CURRENT_TASK.json",
    "TASK_HISTORY.md",
    "META.yaml",
]


def fail(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _resolve_pack_path(root: Path, item: dict[str, Any]) -> Path | None:
    pack_path = str(item.get("pack_path", "")).strip()
    if pack_path:
        p = root / pack_path
        if p.exists():
            return p

    identity_id = str(item.get("id", "")).strip()
    if identity_id:
        legacy = root / "identity" / identity_id
        if legacy.exists():
            return legacy
    return None


def main() -> int:
    root = Path('.')
    schema_path = root / 'identity/catalog/schema/identities.schema.json'
    catalog_path = root / 'identity/catalog/identities.yaml'

    if not schema_path.exists():
        return fail(f"missing schema file: {schema_path}")
    if not catalog_path.exists():
        return fail(f"missing catalog file: {catalog_path}")

    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    catalog: dict[str, Any] = _load_yaml(catalog_path)

    try:
        jsonschema_validate(catalog, schema)
    except Exception as e:
        return fail(f"schema validation failed: {e}")

    identities = catalog.get('identities')
    if not isinstance(identities, list) or not identities:
        return fail("identities must be a non-empty list")

    default_id = str(catalog.get('default_identity', '')).strip()
    if not default_id:
        return fail("default_identity must be non-empty")

    ids: set[str] = set()
    has_default = False
    rc = 0

    for i, item in enumerate(identities):
        prefix = f"identities[{i}]"
        if not isinstance(item, dict):
            print(f"[FAIL] {prefix} must be an object")
            rc = 1
            continue

        identity_id = str(item.get('id', '')).strip()
        if identity_id in ids:
            print(f"[FAIL] duplicate identity id: {identity_id}")
            rc = 1
        ids.add(identity_id)
        if identity_id == default_id:
            has_default = True

        pack_dir = _resolve_pack_path(root, item)
        if not pack_dir:
            print(f"[FAIL] {prefix} pack_path/legacy path not found")
            rc = 1
            continue

        for fname in REQ_PACK_FILES:
            fpath = pack_dir / fname
            if not fpath.exists():
                print(f"[FAIL] {prefix} missing pack file: {fpath}")
                rc = 1

        task_path = pack_dir / 'CURRENT_TASK.json'
        if task_path.exists():
            try:
                task = json.loads(task_path.read_text(encoding='utf-8'))
            except Exception as e:
                print(f"[FAIL] {prefix} invalid CURRENT_TASK.json: {e}")
                rc = 1
                continue

            missing = [k for k in sorted(REQ_TASK_KEYS) if k not in task]
            if missing:
                print(f"[FAIL] {prefix} CURRENT_TASK missing core runtime keys: {missing}")
                rc = 1
            else:
                print(f"[OK]   {identity_id}: CURRENT_TASK core runtime keys present")

            gates = task.get("gates") or {}
            if gates.get("protocol_baseline_review_gate") == "required" and "protocol_review_contract" not in task:
                print(f"[FAIL] {prefix} protocol_baseline_review_gate=required but protocol_review_contract missing")
                rc = 1
            if gates.get("identity_update_gate") == "required" and "identity_update_lifecycle_contract" not in task:
                print(f"[FAIL] {prefix} identity_update_gate=required but identity_update_lifecycle_contract missing")
                rc = 1
            if gates.get("collaboration_trigger_gate") == "required":
                if "blocker_taxonomy_contract" not in task:
                    print(f"[FAIL] {prefix} collaboration_trigger_gate=required but blocker_taxonomy_contract missing")
                    rc = 1
                if "collaboration_trigger_contract" not in task:
                    print(f"[FAIL] {prefix} collaboration_trigger_gate=required but collaboration_trigger_contract missing")
                    rc = 1
            if gates.get("orchestration_gate") == "required" and "capability_orchestration_contract" not in task:
                print(f"[FAIL] {prefix} orchestration_gate=required but capability_orchestration_contract missing")
                rc = 1
            if gates.get("knowledge_acquisition_gate") == "required" and "knowledge_acquisition_contract" not in task:
                print(f"[FAIL] {prefix} knowledge_acquisition_gate=required but knowledge_acquisition_contract missing")
                rc = 1
            if gates.get("experience_feedback_gate") == "required" and "experience_feedback_contract" not in task:
                print(f"[FAIL] {prefix} experience_feedback_gate=required but experience_feedback_contract missing")
                rc = 1
            if gates.get("install_safety_gate") == "required" and "install_safety_contract" not in task:
                print(f"[FAIL] {prefix} install_safety_gate=required but install_safety_contract missing")
                rc = 1
            if gates.get("install_provenance_gate") == "required" and "install_provenance_contract" not in task:
                print(f"[FAIL] {prefix} install_provenance_gate=required but install_provenance_contract missing")
                rc = 1
            if gates.get("ci_enforcement_gate") == "required" and "ci_enforcement_contract" not in task:
                print(f"[FAIL] {prefix} ci_enforcement_gate=required but ci_enforcement_contract missing")
                rc = 1
            if gates.get("arbitration_gate") == "required" and "capability_arbitration_contract" not in task:
                print(f"[FAIL] {prefix} arbitration_gate=required but capability_arbitration_contract missing")
                rc = 1

            if "identity_update_lifecycle_contract" in task and "trigger_regression_contract" not in task:
                print(f"[FAIL] {prefix} identity_update_lifecycle_contract exists but trigger_regression_contract missing")
                rc = 1

    if not has_default:
        print(f"[FAIL] default_identity {default_id} is not present in identities")
        rc = 1

    if rc == 0:
        print("[OK] identity protocol validation passed (all identities)")
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
