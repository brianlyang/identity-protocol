#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

TUPLE_FIELDS: tuple[str, ...] = (
    "run_id_binding",
    "report_selected_path",
    "required_contract",
    "failed_required_contract_count",
    "send_time_gate_status",
    "outlet_bypass_detected",
)


def _load_payload(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("payload is not object")
    return data


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return bool(value)
    if value is None:
        return ""
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate tuple parity across bundle receipts.")
    parser.add_argument("--receipt", action="append", required=True, help="path to bundle receipt JSON; pass multiple times")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    receipts: list[dict[str, Any]] = []
    load_errors: list[str] = []
    for raw in args.receipt:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            load_errors.append(f"missing_receipt:{path}")
            continue
        try:
            payload = _load_payload(path)
        except Exception as exc:
            load_errors.append(f"invalid_receipt:{path}:{exc}")
            continue
        receipts.append({"path": str(path), "payload": payload})

    mismatches: dict[str, list[dict[str, Any]]] = {}
    missing_fields: dict[str, list[str]] = {}

    if not load_errors and receipts:
        baseline_payload = receipts[0]["payload"]
        for field in TUPLE_FIELDS:
            baseline_value = _normalize_value(baseline_payload.get(field))
            for item in receipts:
                payload = item["payload"]
                path = item["path"]
                if field not in payload:
                    missing_fields.setdefault(field, []).append(path)
                    continue
                current_value = _normalize_value(payload.get(field))
                if current_value != baseline_value:
                    mismatches.setdefault(field, []).append(
                        {
                            "path": path,
                            "value": current_value,
                            "baseline": baseline_value,
                        }
                    )

    if load_errors:
        parity_status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-001"
    elif missing_fields or mismatches:
        parity_status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-003"
    else:
        parity_status = STATUS_PASS_REQUIRED
        error_code = ""

    payload = {
        "required_gate_tuple_parity_status": parity_status,
        "error_code": error_code,
        "tuple_fields": list(TUPLE_FIELDS),
        "receipts_checked": [item["path"] for item in receipts],
        "load_errors": load_errors,
        "missing_fields": missing_fields,
        "mismatches": mismatches,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[TUPLE] parity_status={parity_status} receipts_checked={len(receipts)} "
            f"load_errors={len(load_errors)} mismatch_fields={len(mismatches)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 1 if parity_status == STATUS_FAIL_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
