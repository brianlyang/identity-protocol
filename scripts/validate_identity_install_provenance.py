#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
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
    ap = argparse.ArgumentParser(description="Validate install provenance contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    task = _load_json(task_path)

    gates = task.get("gates") or {}
    if gates.get("install_provenance_gate") != "required":
        print("[FAIL] gates.install_provenance_gate must be required")
        return 1

    c = task.get("install_provenance_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing install_provenance_contract")
        return 1
    required_fields = [
        "required",
        "installer_tool_required",
        "operations_required",
        "report_path_pattern",
        "required_report_fields",
        "required_invocation_fields",
        "enforcement_validator",
    ]
    miss = [k for k in required_fields if k not in c]
    if miss:
        print(f"[FAIL] install_provenance_contract missing fields: {miss}")
        return 1
    if c.get("required") is not True:
        print("[FAIL] install_provenance_contract.required must be true")
        return 1

    report_path = Path(args.report) if args.report else None
    all_reports = sorted(Path(".").glob(str(c.get("report_path_pattern", ""))))
    if not report_path or not report_path.exists():
        if all_reports:
            report_path = all_reports[-1]
    if not report_path or not report_path.exists():
        print(f"[FAIL] install provenance report not found: {c.get('report_path_pattern')}")
        return 1

    report = _load_json(report_path)
    miss_report = [k for k in (c.get("required_report_fields") or []) if k not in report]
    if miss_report:
        print(f"[FAIL] install report missing required fields: {miss_report}")
        return 1
    if str(report.get("identity_id", "")).strip() != args.identity_id:
        print("[FAIL] install report identity_id mismatch")
        return 1
    op = str(report.get("operation", "")).strip()
    if op not in set(c.get("operations_required") or []):
        print(f"[FAIL] install report operation not in allowed set: {op}")
        return 1
    inv = report.get("installer_invocation") or {}
    if not isinstance(inv, dict):
        print("[FAIL] install report installer_invocation must be object")
        return 1
    miss_inv = [k for k in (c.get("required_invocation_fields") or []) if k not in inv]
    if miss_inv:
        print(f"[FAIL] installer_invocation missing fields: {miss_inv}")
        return 1
    if str(inv.get("tool", "")).strip() != str(c.get("installer_tool_required", "")).strip():
        print("[FAIL] installer_invocation.tool mismatch with contract")
        return 1

    # enforce operations_required as a full observed chain in recent window
    required_ops = [str(x) for x in (c.get("operations_required") or []) if str(x).strip()]
    if required_ops:
        # use reports from same identity only
        chain_reports: list[dict[str, Any]] = []
        for p in all_reports:
            try:
                d = _load_json(p)
            except Exception:
                continue
            if str(d.get("identity_id", "")).strip() != args.identity_id:
                continue
            ts_raw = str(d.get("generated_at", "")).strip()
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except Exception:
                continue
            chain_reports.append({"path": p, "data": d, "ts": ts})
        if not chain_reports:
            print("[FAIL] no identity-scoped install reports available for operations_required chain validation")
            return 1
        latest_ts = max(x["ts"] for x in chain_reports)
        window_hours = 24
        recent = [x for x in chain_reports if x["ts"] >= latest_ts - timedelta(hours=window_hours)]
        observed_ops = {str(x["data"].get("operation", "")).strip() for x in recent}
        missing_ops = [op for op in required_ops if op not in observed_ops]
        if missing_ops:
            print(
                "[FAIL] install provenance missing required operation chain entries "
                f"within last {window_hours}h: {missing_ops}"
            )
            return 1

    print(f"[OK] install provenance validated: {report_path}")
    print("validate_identity_install_provenance PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
