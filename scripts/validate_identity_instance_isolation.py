#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PATH_FIELDS: list[tuple[str, ...]] = [
    ("protocol_review_contract", "evidence_report_path_pattern"),
    ("identity_role_binding_contract", "binding_evidence_path_pattern"),
    ("trigger_regression_contract", "sample_report_path_pattern"),
    ("knowledge_acquisition_contract", "sample_report_path_pattern"),
    ("experience_feedback_contract", "positive_rulebook_path"),
    ("experience_feedback_contract", "negative_rulebook_path"),
    ("experience_feedback_contract", "sample_report_path_pattern"),
    ("experience_feedback_contract", "feedback_log_path_pattern"),
    ("collaboration_trigger_contract", "evidence_log_path_pattern"),
    ("agent_handoff_contract", "handoff_log_path_pattern"),
    ("install_safety_contract", "install_report_path_pattern"),
    ("install_provenance_contract", "report_path_pattern"),
    ("identity_update_lifecycle_contract", "replay_contract", "evidence_path_pattern"),
    ("capability_arbitration_contract", "arbitration_log_path_pattern"),
]


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_task(catalog_path: Path, identity_id: str) -> tuple[Path, list[str], dict[str, Any]]:
    catalog = _load_yaml(catalog_path)
    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    target = next((x for x in identities if str(x.get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    all_ids = [str(x.get("id", "")).strip() for x in identities if str(x.get("id", "")).strip()]

    pack_path = str(target.get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p, all_ids, target
    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy, all_ids, target
    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _get_nested(d: dict[str, Any], path: tuple[str, ...]) -> Any:
    cur: Any = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def main() -> int:
    ap = argparse.ArgumentParser(description="Block cross-identity path contamination in CURRENT_TASK.")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    args = ap.parse_args()

    task_path, all_ids, target_row = _resolve_task(Path(args.catalog), args.identity_id)
    task = _load_json(task_path)
    target = args.identity_id
    profile = str(target_row.get("profile", "")).strip().lower()
    runtime_mode = str(target_row.get("runtime_mode", "")).strip().lower()
    strict_local_runtime = profile == "runtime" or runtime_mode == "local_only"
    foreign_ids = [x for x in all_ids if x and x != target]
    foreign_ids.extend(["store-manager"] if target != "store-manager" else [])
    foreign_ids = sorted(set(foreign_ids))

    rc = 0
    for field in PATH_FIELDS:
        value = _get_nested(task, field)
        if value is None:
            continue
        val = str(value).strip()
        if not val:
            continue
        if "<identity-id>" in val:
            val = val.replace("<identity-id>", target)
        if strict_local_runtime and target not in val:
            print(f"[FAIL] {'.'.join(field)} must include target identity_id={target}: {value}")
            rc = 1
        hit = [x for x in foreign_ids if x in val]
        if hit:
            print(f"[FAIL] {'.'.join(field)} contains foreign identity markers {hit}: {value}")
            rc = 1

    if rc != 0:
        return 1
    print(f"[OK] identity instance isolation paths validated for identity={target}")
    print(f"     current_task={task_path}")
    print(f"     strict_local_runtime={str(strict_local_runtime).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
