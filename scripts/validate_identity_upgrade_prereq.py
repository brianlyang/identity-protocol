#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_identity_task(catalog_path: Path, identity_id: str) -> Path:
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


def _source_signature(item: dict[str, Any]) -> str:
    if item.get("repo") and item.get("path"):
        return f"{item.get('repo')}::{item.get('path')}"
    if item.get("url"):
        return str(item.get("url"))
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate protocol baseline review prerequisites for identity update operations"
    )
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--evidence", default="", help="optional explicit evidence json path")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"[FAIL] missing catalog: {catalog_path}")
        return 1

    try:
        task_path = _resolve_identity_task(catalog_path, args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validating identity update prereq for: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    try:
        task = _load_json(task_path)
    except Exception as e:
        print(f"[FAIL] invalid CURRENT_TASK json: {e}")
        return 1

    gates = task.get("gates") or {}
    if gates.get("protocol_baseline_review_gate") != "required":
        print("[FAIL] gates.protocol_baseline_review_gate must be required for identity update safety")
        return 1
    print("[OK] gates.protocol_baseline_review_gate=required")

    prc = task.get("protocol_review_contract") or {}
    if not isinstance(prc, dict) or not prc:
        print("[FAIL] protocol_review_contract missing")
        return 1

    required_before = set(prc.get("required_before") or [])
    if "identity_capability_upgrade" not in required_before or "identity_architecture_decision" not in required_before:
        print("[FAIL] protocol_review_contract.required_before must include identity_capability_upgrade and identity_architecture_decision")
        return 1
    print("[OK] protocol_review_contract.required_before contains upgrade + architecture scope")

    pattern = str(prc.get("evidence_report_path_pattern") or "")
    if not pattern and not args.evidence:
        print("[FAIL] protocol_review_contract.evidence_report_path_pattern missing")
        return 1

    if args.evidence:
        evidence_files = [Path(args.evidence)]
    else:
        evidence_files = sorted(Path(".").glob(pattern))

    if not evidence_files:
        print(f"[FAIL] no protocol review evidence matched: {pattern}")
        return 1

    latest = evidence_files[-1]
    print(f"[INFO] using evidence: {latest}")
    try:
        evidence = _load_json(latest)
    except Exception as e:
        print(f"[FAIL] invalid evidence json: {e}")
        return 1

    required_fields = set(prc.get("required_evidence_fields") or [])
    missing_fields = [k for k in required_fields if k not in evidence]
    if missing_fields:
        print(f"[FAIL] evidence missing fields: {missing_fields}")
        return 1
    print("[OK] evidence required fields present")

    expected_sources = [_source_signature(s) for s in (prc.get("must_review_sources") or []) if isinstance(s, dict)]
    reviewed_sources = [_source_signature(s) for s in (evidence.get("sources_reviewed") or []) if isinstance(s, dict)]
    missing_sources = [s for s in expected_sources if s and s not in set(reviewed_sources)]
    if missing_sources:
        print(f"[FAIL] evidence missing mandatory source coverage: {missing_sources}")
        return 1
    print("[OK] evidence covers all mandatory sources")

    print("Identity update prerequisite validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
