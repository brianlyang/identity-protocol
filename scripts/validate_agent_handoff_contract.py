#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQ_FIELDS = [
    "handoff_id",
    "task_id",
    "from_agent",
    "to_agent",
    "input_scope",
    "actions_taken",
    "artifacts",
    "result",
    "next_action",
    "rulebook_update",
]

ALLOWED_RESULTS = {"PASS", "FAIL", "BLOCKED"}
FORBIDDEN_MUTATIONS = {
    "gates",
    "protocol_review_contract",
    "identity_update_lifecycle_contract",
    "trigger_regression_contract",
}


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


def _iter_handoff_files(pattern: str, explicit_file: str) -> list[Path]:
    if explicit_file:
        p = Path(explicit_file)
        return [p] if p.exists() else []
    return sorted(Path(".").glob(pattern))


def _validate_record(path: Path) -> tuple[int, list[str]]:
    logs: list[str] = []
    rc = 0

    try:
        rec = _load_json(path)
    except Exception as e:
        return 1, [f"[FAIL] invalid handoff json {path}: {e}"]

    missing = [k for k in REQ_FIELDS if k not in rec]
    if missing:
        logs.append(f"[FAIL] {path} missing required fields: {missing}")
        return 1, logs

    if str(rec.get("result")) not in ALLOWED_RESULTS:
        logs.append(f"[FAIL] {path} result must be one of {sorted(ALLOWED_RESULTS)}")
        rc = 1

    if not isinstance(rec.get("actions_taken"), list) or not rec.get("actions_taken"):
        logs.append(f"[FAIL] {path} actions_taken must be non-empty array")
        rc = 1

    artifacts = rec.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        logs.append(f"[FAIL] {path} artifacts must be non-empty array")
        rc = 1
    else:
        for i, a in enumerate(artifacts):
            if not isinstance(a, dict):
                logs.append(f"[FAIL] {path} artifacts[{i}] must be object")
                rc = 1
                continue
            p = str(a.get("path") or "").strip()
            if not p:
                logs.append(f"[FAIL] {path} artifacts[{i}].path missing")
                rc = 1
                continue
            if not Path(p).exists():
                logs.append(f"[FAIL] {path} artifacts[{i}].path not found: {p}")
                rc = 1

    next_action = rec.get("next_action")
    if not isinstance(next_action, dict):
        logs.append(f"[FAIL] {path} next_action must be object")
        rc = 1
    else:
        for k in ["owner", "action", "input"]:
            if not str(next_action.get(k) or "").strip():
                logs.append(f"[FAIL] {path} next_action.{k} missing/empty")
                rc = 1

    attempted = set(rec.get("attempted_mutations") or [])
    forbidden = sorted(FORBIDDEN_MUTATIONS.intersection(attempted))
    if forbidden:
        logs.append(f"[FAIL] {path} attempted forbidden mutations: {forbidden}")
        rc = 1

    rulebook = rec.get("rulebook_update")
    if not isinstance(rulebook, dict):
        logs.append(f"[FAIL] {path} rulebook_update must be object")
        rc = 1
    else:
        applied = bool(rulebook.get("applied"))
        if applied and not str(rulebook.get("evidence_run_id") or "").strip():
            logs.append(f"[FAIL] {path} rulebook_update.applied=true requires evidence_run_id")
            rc = 1

    if rc == 0:
        logs.append(f"[OK] {path} handoff contract passed")
    return rc, logs


def _run_self_test(sample_root: Path) -> int:
    pos = sorted((sample_root / "positive").glob("*.json"))
    neg = sorted((sample_root / "negative").glob("*.json"))

    if not pos or not neg:
        print(f"[FAIL] self-test requires positive and negative samples under {sample_root}")
        return 1

    rc = 0
    for p in pos:
        prc, logs = _validate_record(p)
        for ln in logs:
            print(ln)
        if prc != 0:
            print(f"[FAIL] positive sample should pass: {p}")
            rc = 1

    for n in neg:
        nrc, logs = _validate_record(n)
        for ln in logs:
            print(ln)
        if nrc == 0:
            print(f"[FAIL] negative sample should fail: {n}")
            rc = 1

    if rc == 0:
        print("[OK] handoff self-test passed")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate master/sub handoff contract evidence")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--file", default="", help="validate one explicit handoff file")
    ap.add_argument("--self-test", action="store_true", help="run positive/negative sample self-test")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    task = _load_json(task_path)
    contract = task.get("agent_handoff_contract") or {}
    if not isinstance(contract, dict) or not contract:
        print("[FAIL] missing agent_handoff_contract in CURRENT_TASK")
        return 1

    pattern = str(contract.get("handoff_log_path_pattern") or "")
    if not pattern and not args.file:
        print("[FAIL] agent_handoff_contract.handoff_log_path_pattern missing")
        return 1

    files = _iter_handoff_files(pattern, args.file)
    if not files:
        print(f"[FAIL] no handoff logs found (pattern={pattern}, file={args.file})")
        return 1

    rc = 0
    for p in files:
        irc, logs = _validate_record(p)
        for ln in logs:
            print(ln)
        rc = max(rc, irc)

    if args.self_test:
        sample_root = Path("identity/runtime/examples/handoff")
        rc = max(rc, _run_self_test(sample_root))

    if rc == 0:
        print("validate_agent_handoff_contract PASSED")
    else:
        print("validate_agent_handoff_contract FAILED")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
