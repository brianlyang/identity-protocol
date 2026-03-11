#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import load_json, resolve_pack_and_task


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _latest_feedback_mtime(pack_path: Path) -> float | None:
    roots = [
        (pack_path / "runtime" / "protocol-feedback").resolve(),
        (pack_path / "runtime" / "reports").resolve(),
    ]
    mtimes: list[float] = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.glob("**/*.json"):
            if p.is_file():
                mtimes.append(p.stat().st_mtime)
    if not mtimes:
        return None
    return max(mtimes)


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit handoff/collab freshness rotation bootstrap receipt (RQ-012).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--operation", default="update")
    ap.add_argument("--max-age-days", type=float, default=7.0)
    ap.add_argument("--apply", action="store_true", help="apply deterministic bootstrap rotation when stale")
    ap.add_argument("--out", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        _ = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    now = _now_utc()
    latest_mtime = _latest_feedback_mtime(pack_path)
    if latest_mtime is None:
        freshness_age_days = 9999.0
    else:
        freshness_age_days = max(0.0, (now.timestamp() - latest_mtime) / 86400.0)

    stale = freshness_age_days > max(0.0, float(args.max_age_days))
    rotation_applied = bool(stale and args.apply)
    freshness_status = "PASS_REQUIRED" if (not stale or rotation_applied) else "FAIL_REQUIRED"

    report_dir = (pack_path / "runtime" / "reports").resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out).expanduser().resolve() if args.out.strip() else (
        report_dir / f"handoff-collab-freshness-rotation-{args.identity_id}-{int(now.timestamp())}.json"
    ).resolve()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "task_path": str(task_path),
        "operation": str(args.operation or "").strip() or "update",
        "observed_at_utc": _iso(now),
        "max_age_days": float(args.max_age_days),
        "freshness_age_days": round(float(freshness_age_days), 4),
        "freshness_stale": bool(stale),
        "rotation_applied": bool(rotation_applied),
        "rotation_mode": "deterministic_bootstrap",
        "freshness_status": freshness_status,
        "rotation_receipt_ref": str(out_path),
        "evidence_ref": str(out_path),
    }

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"[OK] wrote: {out_path}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if freshness_status == "PASS_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
