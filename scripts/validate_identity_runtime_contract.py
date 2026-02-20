#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


REQ_TOP_LEVEL = [
    "objective",
    "state_machine",
    "gates",
    "source_of_truth",
    "escalation_policy",
    "evaluation_contract",
    "reasoning_loop_contract",
    "routing_contract",
    "rulebook_contract",
]

REQ_GATES = [
    "document_gate",
    "media_gate",
    "category_compliance_gate",
    "reject_memory_gate",
    "payload_evidence_gate",
    "multimodal_consistency_gate",
    "reasoning_loop_gate",
    "routing_gate",
    "rulebook_gate",
]


def _fail(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _resolve_current_task(catalog_path: Path, override: str) -> Path:
    if override:
        p = Path(override)
        if p.exists():
            return p
        raise FileNotFoundError(f"override current task not found: {p}")

    catalog = _load_yaml(catalog_path)
    default_id = str(catalog.get("default_identity", "")).strip()
    identities = catalog.get("identities") or []
    active = next((x for x in identities if str(x.get("id", "")).strip() == default_id), None)
    if not active:
        raise FileNotFoundError(f"default identity not found in catalog: {default_id}")

    pack_path = str(active.get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p

    legacy = Path("identity") / default_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy

    raise FileNotFoundError("CURRENT_TASK.json not found from catalog default identity")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity runtime ORRL contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--current-task", default="", help="optional explicit CURRENT_TASK path")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        return _fail(f"missing catalog: {catalog_path}")

    try:
        path = _resolve_current_task(catalog_path, args.current_task)
    except Exception as e:
        return _fail(str(e))

    print(f"[INFO] validating CURRENT_TASK: {path}")

    try:
        data = _load_json(path)
    except Exception as e:
        return _fail(f"invalid json in {path}: {e}")

    rc = 0
    for key in REQ_TOP_LEVEL:
        if key not in data:
            print(f"[FAIL] CURRENT_TASK missing top-level key: {key}")
            rc = 1
        else:
            print(f"[OK]   top-level key present: {key}")

    gates = data.get("gates") or {}
    if not isinstance(gates, dict):
        print("[FAIL] gates must be object")
        rc = 1
    else:
        for g in REQ_GATES:
            if gates.get(g) != "required":
                print(f"[FAIL] gates.{g} must be 'required'")
                rc = 1
            else:
                print(f"[OK]   gates.{g}=required")

    ec = data.get("evaluation_contract") or {}
    triplet = ec.get("required_evidence_triplet") or []
    if sorted(triplet) != sorted(["api_evidence", "event_evidence", "ui_evidence"]):
        print("[FAIL] evaluation_contract.required_evidence_triplet must include api/event/ui evidence")
        rc = 1
    else:
        print("[OK]   evaluation_contract.required_evidence_triplet contains api/event/ui")

    if ec.get("consistency_required") is not True:
        print("[FAIL] evaluation_contract.consistency_required must be true")
        rc = 1
    else:
        print("[OK]   evaluation_contract.consistency_required=true")

    rl = data.get("reasoning_loop_contract") or {}
    required_attempt_fields = {"attempt", "hypothesis", "patch", "expected_effect", "result"}
    got_fields = set(rl.get("mandatory_fields_per_attempt") or [])
    if not required_attempt_fields.issubset(got_fields):
        print("[FAIL] reasoning_loop_contract.mandatory_fields_per_attempt missing required fields")
        rc = 1
    else:
        print("[OK]   reasoning_loop_contract mandatory attempt fields complete")

    rt = data.get("routing_contract") or {}
    if rt.get("auto_route_enabled") is not True:
        print("[FAIL] routing_contract.auto_route_enabled must be true")
        rc = 1
    else:
        print("[OK]   routing_contract.auto_route_enabled=true")

    if not isinstance(rt.get("problem_type_routes"), dict) or not rt.get("problem_type_routes"):
        print("[FAIL] routing_contract.problem_type_routes must be non-empty object")
        rc = 1
    else:
        print("[OK]   routing_contract.problem_type_routes is non-empty")

    rb = data.get("rulebook_contract") or {}
    rulebook_path = Path(rb.get("rulebook_path", ""))
    if not rulebook_path or not rulebook_path.exists():
        print(f"[FAIL] rulebook_contract.rulebook_path missing or not found: {rulebook_path}")
        rc = 1
    else:
        print(f"[OK]   rulebook exists: {rulebook_path}")

    if rb.get("append_only") is not True:
        print("[FAIL] rulebook_contract.append_only must be true")
        rc = 1
    else:
        print("[OK]   rulebook_contract.append_only=true")

    required_rule_fields = set(rb.get("required_fields") or [])
    if rulebook_path.exists():
        lines = [ln.strip() for ln in rulebook_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if not lines:
            print("[FAIL] rulebook file is empty")
            rc = 1
        else:
            ok_rows = 0
            for i, ln in enumerate(lines[:50], start=1):
                try:
                    row = json.loads(ln)
                except Exception as e:
                    print(f"[FAIL] rulebook line {i} invalid json: {e}")
                    rc = 1
                    continue
                missing = [k for k in required_rule_fields if k not in row]
                if missing:
                    print(f"[FAIL] rulebook line {i} missing fields: {missing}")
                    rc = 1
                else:
                    ok_rows += 1
            if ok_rows:
                print(f"[OK]   validated {ok_rows} rulebook rows against required_fields")

    if rc == 0:
        print("Identity runtime contract validation PASSED")
    else:
        print("Identity runtime contract validation FAILED")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
