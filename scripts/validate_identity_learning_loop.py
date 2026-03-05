#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _fail(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def _resolve_current_task(catalog_path: Path, override: str, identity_id: str) -> tuple[Path, str, Path]:
    if override:
        p = Path(override)
        if not p.exists():
            raise FileNotFoundError(f"override current task not found: {p}")
        return p, identity_id or "(override)", p.parent

    catalog = _load_yaml(catalog_path)
    target_id = identity_id or str(catalog.get("default_identity", "")).strip()
    identities = catalog.get("identities") or []
    active = next((x for x in identities if str(x.get("id", "")).strip() == target_id), None)
    if not active:
        raise FileNotFoundError(f"identity not found in catalog: {target_id}")

    pack_path = str(active.get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p, target_id, Path(pack_path)

    legacy = Path("identity") / target_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy, target_id, legacy.parent

    raise FileNotFoundError("CURRENT_TASK.json not found from catalog identity")


def _resolve_run_report(identity_id: str, pack_dir: Path, override: str) -> Path:
    if override:
        return Path(override)

    preferred = pack_dir / "runtime" / "examples" / f"{identity_id}-learning-sample.json"
    if preferred.exists():
        return preferred
    fallback_repo = (Path("identity") / "runtime" / "examples" / f"{identity_id}-learning-sample.json").resolve()
    if fallback_repo.exists():
        return fallback_repo
    # Do not fall back across identities; missing identity-scoped evidence must fail-fast.
    return preferred


def _resolve_rulebook_path(rulebook_raw: str, *, pack_dir: Path) -> Path:
    candidate = Path(rulebook_raw).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    repo_relative = candidate.resolve()
    pack_relative = (pack_dir / candidate).resolve()
    if repo_relative.exists():
        return repo_relative
    return pack_relative


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity learning loop evidence (reasoning + rulebook linkage)")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", default="", help="validate for explicit identity id")
    ap.add_argument("--current-task", default="")
    ap.add_argument("--run-report", default="")
    ap.add_argument("--rulebook", default="")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        return _fail(f"missing catalog: {catalog_path}")

    try:
        task_path, identity_id, pack_dir = _resolve_current_task(catalog_path, args.current_task, args.identity_id)
    except Exception as e:
        return _fail(str(e))

    run_report_path = _resolve_run_report(identity_id, pack_dir, args.run_report)

    if not task_path.exists():
        return _fail(f"missing current task file: {task_path}")
    task = _load_json(task_path)

    lvc = task.get("learning_verification_contract") or {}
    rlc = task.get("reasoning_loop_contract") or {}
    rb_contract = task.get("rulebook_contract") or {}

    if not lvc:
        return _fail("learning_verification_contract missing in CURRENT_TASK")

    if not run_report_path.exists():
        return _fail(f"missing run report: {run_report_path}")
    run = _load_json(run_report_path)

    print(f"[INFO] identity={identity_id} current_task={task_path}")
    print(f"[INFO] run_report={run_report_path}")

    rc = 0

    run_id = str(run.get("run_id") or "").strip()
    if lvc.get("run_id_required", False) and not run_id:
        print("[FAIL] run_id is required by learning_verification_contract")
        rc = 1
    else:
        print(f"[OK]   run_id={run_id}")

    attempts = run.get("reasoning_attempts") or []
    if lvc.get("reasoning_trace_required", False):
        if not isinstance(attempts, list) or not attempts:
            print("[FAIL] reasoning_trace_required=true but reasoning_attempts is empty")
            rc = 1
        else:
            print(f"[OK]   reasoning_attempts count={len(attempts)}")

    required_attempt_fields = set(rlc.get("mandatory_fields_per_attempt") or [])
    for i, att in enumerate(attempts, start=1):
        if not isinstance(att, dict):
            print(f"[FAIL] attempt[{i}] must be object")
            rc = 1
            continue
        missing = [k for k in required_attempt_fields if k not in att]
        if missing:
            print(f"[FAIL] attempt[{i}] missing fields: {missing}")
            rc = 1
        else:
            print(f"[OK]   attempt[{i}] fields complete")

    if args.rulebook:
        rulebook_path = Path(args.rulebook)
    else:
        rb_val = str(rb_contract.get("rulebook_path") or "").strip()
        if rb_val:
            rulebook_path = _resolve_rulebook_path(rb_val, pack_dir=pack_dir)
        else:
            rulebook_path = pack_dir / "RULEBOOK.jsonl"
    if lvc.get("rulebook_update_required", False):
        if not rulebook_path.exists():
            print(f"[FAIL] rulebook not found: {rulebook_path}")
            rc = 1
        else:
            link_field = str(lvc.get("rulebook_link_field") or "evidence_run_id")
            matched = 0
            lines = [ln.strip() for ln in rulebook_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            for ln in lines:
                try:
                    row = json.loads(ln)
                except Exception:
                    continue
                if str(row.get(link_field) or "").strip() == run_id:
                    matched += 1
            if matched <= 0:
                print(f"[FAIL] no rulebook records linked by {link_field}={run_id}")
                rc = 1
            else:
                print(f"[OK]   linked rulebook records found: {matched}")

    if rc == 0:
        print("Identity learning-loop validation PASSED")
    else:
        print("Identity learning-loop validation FAILED")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
