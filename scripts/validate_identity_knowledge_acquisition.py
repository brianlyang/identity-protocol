#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQ_KEYS = [
    "required",
    "must_research_when",
    "source_priority",
    "evidence_fields",
    "sample_report_path_pattern",
    "high_frequency_domains",
]
REQ_EVIDENCE_FIELDS = ["claim", "source", "source_level", "confidence", "expiry", "applies_to"]


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
    ap = argparse.ArgumentParser(description="Validate knowledge acquisition contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate knowledge acquisition for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    task = _load_json(task_path)
    c = task.get("knowledge_acquisition_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing knowledge_acquisition_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        print(f"[FAIL] knowledge_acquisition_contract missing fields: {missing}")
        return 1

    if c.get("required") is not True:
        print("[FAIL] knowledge_acquisition_contract.required must be true")
        return 1

    src_pri = c.get("source_priority") or []
    if src_pri[:2] != ["official_spec", "repo_contract"]:
        print("[FAIL] source_priority must prioritize official_spec and repo_contract")
        return 1

    ef = c.get("evidence_fields") or []
    if any(x not in ef for x in REQ_EVIDENCE_FIELDS):
        print("[FAIL] evidence_fields missing required knowledge evidence fields")
        return 1

    pattern = c.get("sample_report_path_pattern")
    report_path = Path(args.report) if args.report else Path("identity/runtime/examples") / f"{args.identity_id}-knowledge-acquisition-sample.json"
    if not report_path.exists():
        # fallback pattern search
        files = sorted(Path('.').glob(pattern)) if pattern else []
        if files:
            report_path = files[-1]
    if not report_path.exists():
        print(f"[FAIL] missing knowledge acquisition sample report: {report_path}")
        return 1

    report = _load_json(report_path)
    records = report.get("records") or []
    if not isinstance(records, list) or not records:
        print("[FAIL] report.records must be a non-empty array")
        return 1

    allowed_levels = set(src_pri)
    rc = 0
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            print(f"[FAIL] records[{i}] must be object")
            rc = 1
            continue
        miss = [k for k in REQ_EVIDENCE_FIELDS if k not in rec]
        if miss:
            print(f"[FAIL] records[{i}] missing fields: {miss}")
            rc = 1
        if rec.get("source_level") not in allowed_levels:
            print(f"[FAIL] records[{i}].source_level must be in {sorted(allowed_levels)}")
            rc = 1

    if not isinstance(c.get("high_frequency_domains"), dict) or not c.get("high_frequency_domains"):
        print("[FAIL] high_frequency_domains must be non-empty object")
        rc = 1

    if rc:
        return 1
    print("Knowledge acquisition contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
