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
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _resolve_pack(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path)
        if p.exists():
            return p
    legacy = Path("identity") / identity_id
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"identity pack not found: {identity_id}")


def _resolve_report(identity_id: str, override: str) -> Path:
    if override:
        p = Path(override)
        if not p.exists():
            raise FileNotFoundError(f"execution report not found: {p}")
        return p
    pattern = f"identity-upgrade-exec-{identity_id}-*.json"
    candidates = [
        p
        for p in Path("identity/runtime/reports").glob(pattern)
        if not p.name.endswith("-patch-plan.json")
    ]
    if not candidates:
        raise FileNotFoundError(
            f"no execution report found in identity/runtime/reports for pattern {pattern}; "
            "provide --execution-report explicitly when reports are generated outside repo tree"
        )
    candidates.sort(key=lambda p: p.stat().st_mtime)
    return candidates[-1]


def _load_rulebook_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        ln = line.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except Exception:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate experience writeback after identity upgrade execution.")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--execution-report", default="")
    args = ap.parse_args()

    try:
        pack = _resolve_pack(Path(args.catalog), args.identity_id)
        report_path = _resolve_report(args.identity_id, args.execution_report)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    report = _load_json(report_path)
    run_id = str(report.get("run_id", "")).strip()
    if not run_id:
        print(f"[FAIL] report.run_id missing: {report_path}")
        return 1
    if str(report.get("identity_id", "")).strip() != args.identity_id:
        print(
            f"[FAIL] report.identity_id mismatch: expected={args.identity_id}, "
            f"got={report.get('identity_id')}"
        )
        return 1

    upgrade_required = bool(report.get("upgrade_required"))
    all_ok = bool(report.get("all_ok"))
    if not upgrade_required:
        print("[OK] upgrade_required=false; experience writeback not required")
        return 0
    if not all_ok:
        print("[OK] upgrade_required=true but all_ok=false; writeback enforcement deferred until successful run")
        return 0

    rulebook_path = pack / "RULEBOOK.jsonl"
    history_path = pack / "TASK_HISTORY.md"
    if not rulebook_path.exists():
        print(f"[FAIL] missing RULEBOOK: {rulebook_path}")
        return 1
    if not history_path.exists():
        print(f"[FAIL] missing TASK_HISTORY: {history_path}")
        return 1

    rows = _load_rulebook_rows(rulebook_path)
    matched_rows = [r for r in rows if str(r.get("evidence_run_id", "")).strip() == run_id]
    if not matched_rows:
        print(f"[FAIL] RULEBOOK has no row linked to run_id={run_id}")
        return 1

    history_text = history_path.read_text(encoding="utf-8")
    if run_id not in history_text:
        print(f"[FAIL] TASK_HISTORY missing run_id={run_id} entry")
        return 1

    wb = report.get("experience_writeback")
    if not isinstance(wb, dict):
        print("[FAIL] execution report missing experience_writeback object")
        return 1
    status = str(wb.get("status", "")).strip()
    if status != "WRITTEN":
        print(f"[FAIL] experience_writeback.status must be WRITTEN, got={status!r}")
        return 1

    print("[OK] experience writeback validation passed")
    print(f"     execution_report={report_path}")
    print(f"     run_id={run_id}")
    print(f"     rulebook_matches={len(matched_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
