#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQ_KEYS = [
    "required",
    "positive_rulebook_path",
    "negative_rulebook_path",
    "required_fields",
    "cross_layer_feedback_targets",
    "promote_requires_replay_pass",
    "sample_report_path_pattern",
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


def _validate_rulebook(path: Path, req_fields: list[str], label: str) -> int:
    if not path.exists():
        print(f"[FAIL] {label} not found: {path}")
        return 1
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        print(f"[FAIL] {label} empty: {path}")
        return 1
    rc = 0
    for i, ln in enumerate(lines, start=1):
        try:
            row = json.loads(ln)
        except Exception as e:
            print(f"[FAIL] {label} line {i} invalid json: {e}")
            rc = 1
            continue
        missing = [k for k in req_fields if k not in row]
        if missing:
            print(f"[FAIL] {label} line {i} missing fields: {missing}")
            rc = 1
    if rc == 0:
        print(f"[OK] {label} validated: {path}")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate experience feedback contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate experience feedback for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    task = _load_json(task_path)
    c = task.get("experience_feedback_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing experience_feedback_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        print(f"[FAIL] experience_feedback_contract missing fields: {missing}")
        return 1

    if c.get("required") is not True:
        print("[FAIL] experience_feedback_contract.required must be true")
        return 1

    req_fields = c.get("required_fields") or []
    rc = 0
    rc |= _validate_rulebook(Path(c.get("positive_rulebook_path")), req_fields, "positive_rulebook")
    rc |= _validate_rulebook(Path(c.get("negative_rulebook_path")), req_fields, "negative_rulebook")

    targets = set(c.get("cross_layer_feedback_targets") or [])
    need = {"routing_contract", "capability_orchestration_contract", "gates"}
    if not need.issubset(targets):
        print(f"[FAIL] cross_layer_feedback_targets missing: {sorted(need-targets)}")
        rc = 1

    replay_gate = c.get("promote_requires_replay_pass")
    if replay_gate is None:
        replay_gate = c.get("promotion_requires_replay_pass")
    if replay_gate is not True:
        print("[FAIL] replay-pass promotion gate must be true (promote_requires_replay_pass or promotion_requires_replay_pass)")
        rc = 1

    report_path = Path(args.report) if args.report else Path("identity/runtime/examples") / f"{args.identity_id}-experience-feedback-sample.json"
    if not report_path.exists():
        files = sorted(Path('.').glob(c.get("sample_report_path_pattern", "")))
        if files:
            report_path = files[-1]
    if not report_path.exists():
        print(f"[FAIL] missing experience feedback sample report: {report_path}")
        return 1

    report = _load_json(report_path)
    all_updates = (report.get("positive_updates") or []) + (report.get("negative_updates") or [])
    if not all_updates:
        print("[FAIL] sample report requires positive_updates or negative_updates")
        return 1

    for i, u in enumerate(all_updates):
        if not isinstance(u, dict):
            print(f"[FAIL] update[{i}] must be object")
            rc = 1
            continue
        missing_u = [k for k in req_fields if k not in u]
        if missing_u:
            print(f"[FAIL] update[{i}] missing fields: {missing_u}")
            rc = 1
        if u.get("replay_status") != "PASS":
            print(f"[FAIL] update[{i}].replay_status must be PASS")
            rc = 1

    if rc:
        return 1

    if args.self_test:
        pos = sorted(Path("identity/runtime/examples/experience/positive").glob("*.json"))
        neg = sorted(Path("identity/runtime/examples/experience/negative").glob("*.json"))
        if len(pos) < 2 or len(neg) < 1:
            print("[FAIL] experience self-test requires >=2 positive and >=1 negative samples")
            return 1
        # positives should pass required fields + replay PASS
        for p in pos:
            r = _load_json(p)
            updates = (r.get("positive_updates") or []) + (r.get("negative_updates") or [])
            if not updates:
                print(f"[FAIL] positive sample missing updates: {p}")
                return 1
            for i, u in enumerate(updates):
                miss = [k for k in req_fields if k not in u]
                if miss:
                    print(f"[FAIL] positive sample missing fields {miss}: {p}#{i}")
                    return 1
                if u.get("replay_status") != "PASS":
                    print(f"[FAIL] positive sample replay_status must be PASS: {p}#{i}")
                    return 1
        # negatives should contain at least one non-PASS replay
        for p in neg:
            r = _load_json(p)
            updates = (r.get("positive_updates") or []) + (r.get("negative_updates") or [])
            if not updates:
                print(f"[FAIL] negative sample missing updates: {p}")
                return 1
            if not any(u.get("replay_status") != "PASS" for u in updates if isinstance(u, dict)):
                print(f"[FAIL] negative sample did not include replay_status!=PASS: {p}")
                return 1
        print("[OK] experience self-test passed")

    print("Experience feedback contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
