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
    parser.add_argument("--min-receipts", type=int, default=2, help="minimum receipt count required for tuple parity")
    parser.add_argument(
        "--require-distinct-surface-labels",
        action="store_true",
        help="require each compared receipt to carry distinct surface_label values",
    )
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
        surface_label = str(payload.get("surface_label", "")).strip()
        receipts.append({"path": str(path), "payload": payload, "surface_label": surface_label})

    mismatches: dict[str, list[dict[str, Any]]] = {}
    missing_fields: dict[str, list[str]] = {}
    parity_contract_reasons: list[str] = []
    missing_surface_labels: list[str] = []
    duplicate_surface_labels: dict[str, list[str]] = {}

    min_receipts = max(1, int(args.min_receipts))
    if not load_errors and len(receipts) < min_receipts:
        parity_contract_reasons.append(f"min_receipts_not_met:{len(receipts)}/{min_receipts}")

    require_distinct_labels = bool(args.require_distinct_surface_labels) or min_receipts > 1
    if not load_errors and require_distinct_labels:
        label_to_paths: dict[str, list[str]] = {}
        for item in receipts:
            label = str(item.get("surface_label", "")).strip()
            path = str(item.get("path", ""))
            if not label:
                missing_surface_labels.append(path)
                continue
            label_to_paths.setdefault(label, []).append(path)
        duplicate_surface_labels = {
            label: paths for label, paths in label_to_paths.items() if len(paths) > 1
        }
        if missing_surface_labels:
            parity_contract_reasons.append("surface_label_missing")
        distinct_labels = len(label_to_paths)
        if distinct_labels < min_receipts:
            parity_contract_reasons.append(f"distinct_surface_labels_not_met:{distinct_labels}/{min_receipts}")
        if duplicate_surface_labels and min_receipts > 1:
            parity_contract_reasons.append("surface_label_not_unique")

    if not load_errors and receipts and not parity_contract_reasons:
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
    elif parity_contract_reasons or missing_fields or mismatches:
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
        "surface_labels_checked": [
            {"path": item["path"], "surface_label": item.get("surface_label", "")}
            for item in receipts
        ],
        "min_receipts": min_receipts,
        "require_distinct_surface_labels": require_distinct_labels,
        "parity_contract_reasons": parity_contract_reasons,
        "missing_surface_labels": missing_surface_labels,
        "duplicate_surface_labels": duplicate_surface_labels,
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
