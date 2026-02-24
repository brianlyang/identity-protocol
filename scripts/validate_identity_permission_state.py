#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_STATES = {
    "PRECHECK",
    "RUN_READONLY",
    "NEEDS_ESCALATION",
    "ESCALATION_GRANTED",
    "ESCALATION_DENIED",
    "WRITEBACK_ATTEMPT",
    "WRITEBACK_WRITTEN",
    "WRITEBACK_DEFERRED",
    "WRITEBACK_FAILED",
    "DONE",
}
ALLOWED_CODES = {"", "IP-PERM-001", "IP-PERM-002", "IP-PERM-003", "IP-PATH-001", "IP-CI-001", "IP-REC-001"}


def _latest(identity_id: str, report_dir: Path) -> Path | None:
    rows = sorted(report_dir.glob(f"identity-upgrade-exec-{identity_id}-*.json"), key=lambda p: p.stat().st_mtime)
    return rows[-1] if rows else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate permission-state contract in identity upgrade report.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--report-dir", default="/tmp/identity-upgrade-reports")
    ap.add_argument("--require-written", action="store_true")
    ap.add_argument("--ci", action="store_true")
    args = ap.parse_args()

    report_path = Path(args.report).expanduser().resolve() if args.report else _latest(args.identity_id, Path(args.report_dir).expanduser().resolve())
    if report_path is None or not report_path.exists():
        print(f"[FAIL] execution report not found for identity={args.identity_id}")
        return 1

    data = json.loads(report_path.read_text(encoding="utf-8"))
    state = str(data.get("permission_state", "")).strip()
    code = str(data.get("permission_error_code", "")).strip()
    wb = str(data.get("writeback_status", "")).strip()
    pre = data.get("writeback_precheck") or {}

    if not state:
        print("[FAIL] permission_state missing")
        return 1
    if state not in ALLOWED_STATES:
        print(f"[FAIL] invalid permission_state: {state}")
        return 1
    if code not in ALLOWED_CODES:
        print(f"[FAIL] invalid permission_error_code: {code}")
        return 1
    if not isinstance(pre, dict) or "all_writable" not in pre:
        print("[FAIL] writeback_precheck missing required fields")
        return 1

    if wb == "DEFERRED_PERMISSION_BLOCKED" and code not in {"IP-PERM-001", "IP-PERM-002", "IP-PERM-003"}:
        print("[FAIL] deferred permission block must include IP-PERM-00x code")
        return 1

    if args.ci and wb == "DEFERRED_PERMISSION_BLOCKED":
        print("[FAIL] CI cannot accept deferred permission writeback")
        return 2

    if args.require_written and wb != "WRITTEN":
        print(f"[FAIL] writeback_status must be WRITTEN, got {wb}")
        return 2

    print(f"[OK] permission state validated: {report_path}")
    print(f"     permission_state={state} writeback_status={wb} error_code={code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
