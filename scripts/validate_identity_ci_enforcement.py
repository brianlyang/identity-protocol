#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQ_KEYS = [
    "required",
    "required_workflows",
    "required_job",
    "required_validator_set_label",
    "required_validators",
    "candidate_validators_v1_2",
    "required_checks",
    "freshness_gate",
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
    ap = argparse.ArgumentParser(description="Validate CI enforcement contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate ci enforcement for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    task = _load_json(task_path)
    c = task.get("ci_enforcement_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing ci_enforcement_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        print(f"[FAIL] ci_enforcement_contract missing fields: {missing}")
        return 1

    if c.get("required") is not True:
        print("[FAIL] ci_enforcement_contract.required must be true")
        return 1

    rc = 0
    wf_dir = Path('.github/workflows')
    required_job = str(c.get("required_job"))
    validators = c.get("required_validators") or []
    candidate = c.get("candidate_validators_v1_2") or []
    if not isinstance(candidate, list):
        print("[FAIL] candidate_validators_v1_2 must be list")
        rc = 1
    if not str(c.get("required_validator_set_label", "")).strip():
        print("[FAIL] required_validator_set_label must be non-empty")
        rc = 1

    reusable_path = wf_dir / "_identity-required-gates.yml"
    reusable_text = reusable_path.read_text(encoding="utf-8") if reusable_path.exists() else ""

    for wf in c.get("required_workflows") or []:
        wf_path = wf_dir / f"{wf}.yml"
        if not wf_path.exists():
            print(f"[FAIL] required workflow file missing: {wf_path}")
            rc = 1
            continue
        text = wf_path.read_text(encoding="utf-8")
        if f"{required_job}:" not in text:
            print(f"[FAIL] workflow {wf_path} missing job: {required_job}")
            rc = 1
        uses_reusable = "uses: ./.github/workflows/_identity-required-gates.yml" in text
        if uses_reusable and not reusable_text:
            print(f"[FAIL] workflow {wf_path} references reusable required-gates workflow but {reusable_path} is missing")
            rc = 1
        for v in validators:
            if v in text:
                continue
            if uses_reusable and v in reusable_text:
                continue
            print(f"[FAIL] workflow {wf_path} missing validator call reference: {v}")
            rc = 1

    fg = c.get("freshness_gate") or {}
    if int(fg.get("handoff_logs_max_age_days", 0)) <= 0:
        print("[FAIL] freshness_gate.handoff_logs_max_age_days must be >0")
        rc = 1
    if int(fg.get("route_metrics_max_age_days", 0)) <= 0:
        print("[FAIL] freshness_gate.route_metrics_max_age_days must be >0")
        rc = 1

    checks = c.get("required_checks") or []
    if not any("protocol-ci / required-gates" == x for x in checks):
        print("[FAIL] required_checks must include protocol-ci / required-gates")
        rc = 1
    if not any("identity-protocol-ci / required-gates" == x for x in checks):
        print("[FAIL] required_checks must include identity-protocol-ci / required-gates")
        rc = 1

    overlap = sorted(set(validators).intersection(set(candidate)))
    if overlap:
        print(f"[FAIL] required_validators overlaps candidate_validators_v1_2: {overlap}")
        rc = 1

    if rc:
        return 1

    print("CI enforcement contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
