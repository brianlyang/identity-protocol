#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _latest_for_identity(report_dir: Path, identity_id: str) -> Path | None:
    rows = sorted(report_dir.glob(f"identity-health-{identity_id}-*.json"), key=lambda p: p.stat().st_mtime)
    return rows[-1] if rows else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity health report contract.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--report-dir", default="/tmp/identity-health-reports")
    ap.add_argument("--require-pass", action="store_true")
    args = ap.parse_args()

    if args.report:
        path = Path(args.report).expanduser().resolve()
    else:
        latest = _latest_for_identity(Path(args.report_dir).expanduser().resolve(), args.identity_id)
        if latest is None:
            print(f"[FAIL] no health report found for identity={args.identity_id} in {args.report_dir}")
            return 1
        path = latest

    if not path.exists():
        print(f"[FAIL] report not found: {path}")
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    required = ["report_id", "generated_at", "identity_id", "overall_status", "checks", "recommendations"]
    miss = [k for k in required if k not in data]
    if miss:
        print(f"[FAIL] health report missing fields: {miss}")
        return 1

    if str(data.get("identity_id", "")).strip() != args.identity_id:
        print("[FAIL] health report identity mismatch")
        return 1

    checks = data.get("checks") or []
    if not isinstance(checks, list) or not checks:
        print("[FAIL] health report checks must be non-empty list")
        return 1

    failed = [c for c in checks if not bool(c.get("ok"))]
    recs = data.get("recommendations") or []
    if failed and not recs:
        print("[FAIL] failed health checks require non-empty recommendations")
        return 1

    if args.require_pass and str(data.get("overall_status", "")).upper() != "PASS":
        print(f"[FAIL] health overall status is not PASS: {data.get('overall_status')}")
        return 2

    print(f"[OK] health report contract validated: {path}")
    print(f"     overall_status={data.get('overall_status')} failed_checks={len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
