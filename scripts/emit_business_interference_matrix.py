#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import load_json, resolve_pack_and_task


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _matrix_rows(task: dict[str, Any], *, mode: str) -> list[dict[str, Any]]:
    required_validators = [str(x).strip() for x in (task.get("required_validators") or []) if str(x).strip()]
    rows: list[dict[str, Any]] = []
    for idx, validator in enumerate(required_validators[:20]):
        rows.append(
            {
                "row_key": f"{mode}:{idx}:{Path(validator).name}",
                "lane_id": mode,
                "component": validator,
                "interference_level": "low" if "validate_" in validator else "none",
                "verdict": "PASS_REQUIRED",
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit business interference matrix receipt (RQ-016).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--mode", choices=["refresh", "strict"], required=True)
    ap.add_argument("--operation", default="update")
    ap.add_argument("--out", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    observed_at = _iso_now()
    matrix_rows = _matrix_rows(task, mode=args.mode)
    matrix_status = "PASS_REQUIRED" if matrix_rows else "SKIPPED_NOT_REQUIRED"

    report_dir = (pack_path / "runtime" / "reports").resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out).expanduser().resolve() if args.out.strip() else (
        report_dir / f"business-interference-matrix-{args.identity_id}-{args.mode}-{int(datetime.now(UTC).timestamp())}.json"
    ).resolve()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "operation": str(args.operation or "").strip() or "update",
        "mode": args.mode,
        "observed_at_utc": observed_at,
        "interference_matrix_status": matrix_status,
        "interference_matrix_row_count": len(matrix_rows),
        "interference_matrix_rows": matrix_rows,
        "interference_receipt_ref": str(out_path),
        "evidence_ref": str(out_path),
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"[OK] wrote: {out_path}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if matrix_status == "PASS_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
