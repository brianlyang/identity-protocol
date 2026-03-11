#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

INVARIANT_TUPLE_FIELDS: tuple[str, ...] = (
    "run_id_binding",
    "identity_id",
    "actor_id",
    "resolved_work_layer",
    "resolved_source_layer",
    "lock_state",
)
OPERATION_SCOPED_TUPLE_FIELDS: tuple[str, ...] = (
    "report_selected_path",
    "required_contract",
    "failed_required_contract_count",
    "send_time_gate_status",
    "outlet_bypass_detected",
    "final_emit_contract_status",
    "final_emit_policy_mode",
    "final_emit_schema_status",
)
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "run_id_binding": ("run_id_binding",),
    "identity_id": ("identity_id",),
    "actor_id": ("actor_id", "resolved_actor_id"),
    "resolved_work_layer": ("resolved_work_layer", "work_layer"),
    "resolved_source_layer": ("resolved_source_layer", "source_layer"),
    "lock_state": ("lock_state", "context_lock_state"),
    "report_selected_path": ("report_selected_path",),
    "required_contract": ("required_contract",),
    "failed_required_contract_count": ("failed_required_contract_count",),
    "send_time_gate_status": ("send_time_gate_status",),
    "outlet_bypass_detected": ("outlet_bypass_detected",),
    "final_emit_contract_status": ("final_emit_contract_status",),
    "final_emit_policy_mode": ("final_emit_policy_mode",),
    "final_emit_schema_status": ("final_emit_schema_status",),
    "parity_operation_scope": ("parity_operation_scope",),
    "required_contract_reason": ("required_contract_reason",),
}
TUPLE_FIELDS: tuple[str, ...] = (
    *INVARIANT_TUPLE_FIELDS,
    *OPERATION_SCOPED_TUPLE_FIELDS,
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


def _extract_field(payload: dict[str, Any], field: str) -> tuple[bool, Any, str]:
    aliases = FIELD_ALIASES.get(field, (field,))
    for key in aliases:
        if key in payload:
            return True, _normalize_value(payload.get(key)), key
    return False, "", ""


def _derive_parity_operation_scope(payload: dict[str, Any], surface_label: str) -> str:
    explicit_present, explicit_scope, _ = _extract_field(payload, "parity_operation_scope")
    explicit = str(explicit_scope or "").strip()
    if explicit_present and explicit:
        return explicit
    operation = str(payload.get("operation", "")).strip().lower()
    normalized_surface = str(surface_label or "").strip().lower()
    if operation in {"scan", "inspection"} and normalized_surface.endswith("_scan_probe"):
        return "scan_probe"
    if operation:
        return f"operation:{operation}"
    if normalized_surface:
        return f"surface:{normalized_surface}"
    return "default"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate tuple parity across bundle receipts.")
    parser.add_argument("--receipt", action="append", required=True, help="path to bundle receipt JSON; pass multiple times")
    parser.add_argument("--min-receipts", type=int, default=2, help="minimum receipt count required for tuple parity")
    parser.add_argument(
        "--require-distinct-surface-labels",
        action="store_true",
        help="require each compared receipt to carry distinct surface_label values",
    )
    parser.add_argument(
        "--require-distinct-operations",
        action="store_true",
        help="require each compared receipt to carry distinct operation values",
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
        parity_scope = _derive_parity_operation_scope(payload, surface_label)
        _, required_contract_reason, _ = _extract_field(payload, "required_contract_reason")
        receipts.append(
            {
                "path": str(path),
                "payload": payload,
                "surface_label": surface_label,
                "parity_operation_scope": str(parity_scope or "").strip(),
                "required_contract_reason": str(required_contract_reason or "").strip(),
            }
        )

    mismatches: dict[str, list[dict[str, Any]]] = {}
    missing_fields: dict[str, list[str]] = {}
    parity_contract_reasons: list[str] = []
    missing_surface_labels: list[str] = []
    duplicate_surface_labels: dict[str, list[str]] = {}
    missing_operations: list[str] = []
    duplicate_operations: dict[str, list[str]] = {}

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

    require_distinct_operations = bool(args.require_distinct_operations)
    if not load_errors and require_distinct_operations:
        operation_to_paths: dict[str, list[str]] = {}
        for item in receipts:
            payload = item.get("payload") or {}
            operation = str(payload.get("operation", "")).strip()
            path = str(item.get("path", ""))
            if not operation:
                missing_operations.append(path)
                continue
            operation_to_paths.setdefault(operation, []).append(path)
        duplicate_operations = {
            operation: paths for operation, paths in operation_to_paths.items() if len(paths) > 1
        }
        if missing_operations:
            parity_contract_reasons.append("operation_missing")
        distinct_operations = len(operation_to_paths)
        if distinct_operations < min_receipts:
            parity_contract_reasons.append(f"distinct_operations_not_met:{distinct_operations}/{min_receipts}")
        if duplicate_operations and min_receipts > 1:
            parity_contract_reasons.append("operation_not_unique")

    scope_groups: dict[str, list[dict[str, Any]]] = {}
    for item in receipts:
        scope_key = str(item.get("parity_operation_scope", "")).strip() or "default"
        scope_groups.setdefault(scope_key, []).append(item)

    if not load_errors and receipts and not parity_contract_reasons:
        # 1) Invariant tuple: compare across all receipts (cross-operation).
        baseline_payload = receipts[0]["payload"]
        baseline_path = str(receipts[0]["path"])
        for field in INVARIANT_TUPLE_FIELDS:
            baseline_present, baseline_value, baseline_key = _extract_field(baseline_payload, field)
            if not baseline_present:
                missing_fields.setdefault(field, []).append(baseline_path)
                continue
            for item in receipts:
                payload = item["payload"]
                path = str(item["path"])
                current_present, current_value, current_key = _extract_field(payload, field)
                if not current_present:
                    missing_fields.setdefault(field, []).append(path)
                    continue
                if current_value != baseline_value:
                    mismatches.setdefault(field, []).append(
                        {
                            "path": path,
                            "value": current_value,
                            "baseline": baseline_value,
                            "baseline_path": baseline_path,
                            "baseline_key": baseline_key,
                            "current_key": current_key,
                            "baseline_scope": str(receipts[0].get("parity_operation_scope", "")),
                            "current_scope": str(item.get("parity_operation_scope", "")),
                        }
                    )

        # 2) Operation-scoped tuple: compare only within the same parity-operation-scope group.
        for scope_key, rows in scope_groups.items():
            if len(rows) < 2:
                continue
            scope_baseline = rows[0]
            baseline_payload = scope_baseline["payload"]
            baseline_path = str(scope_baseline["path"])
            for field in OPERATION_SCOPED_TUPLE_FIELDS:
                baseline_present, baseline_value, baseline_key = _extract_field(baseline_payload, field)
                if not baseline_present:
                    missing_fields.setdefault(field, []).append(baseline_path)
                    continue
                for item in rows:
                    payload = item["payload"]
                    path = str(item["path"])
                    current_present, current_value, current_key = _extract_field(payload, field)
                    if not current_present:
                        missing_fields.setdefault(field, []).append(path)
                        continue
                    if current_value != baseline_value:
                        mismatches.setdefault(field, []).append(
                            {
                                "path": path,
                                "value": current_value,
                                "baseline": baseline_value,
                                "baseline_path": baseline_path,
                                "baseline_key": baseline_key,
                                "current_key": current_key,
                                "baseline_scope": scope_key,
                                "current_scope": scope_key,
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
        "core_tuple_fields": list(INVARIANT_TUPLE_FIELDS),
        "conditional_tuple_fields": list(OPERATION_SCOPED_TUPLE_FIELDS),
        "invariant_tuple_fields": list(INVARIANT_TUPLE_FIELDS),
        "operation_scoped_tuple_fields": list(OPERATION_SCOPED_TUPLE_FIELDS),
        "receipts_checked": [item["path"] for item in receipts],
        "surface_labels_checked": [
            {"path": item["path"], "surface_label": item.get("surface_label", "")}
            for item in receipts
        ],
        "parity_scopes_checked": [
            {
                "path": item["path"],
                "operation": str((item["payload"] or {}).get("operation", "")).strip(),
                "surface_label": item.get("surface_label", ""),
                "parity_operation_scope": item.get("parity_operation_scope", ""),
                "required_contract_reason": item.get("required_contract_reason", ""),
            }
            for item in receipts
        ],
        "scope_groups": {
            scope_key: [str(row.get("path", "")) for row in rows]
            for scope_key, rows in scope_groups.items()
        },
        "min_receipts": min_receipts,
        "require_distinct_surface_labels": require_distinct_labels,
        "require_distinct_operations": require_distinct_operations,
        "parity_contract_reasons": parity_contract_reasons,
        "missing_surface_labels": missing_surface_labels,
        "duplicate_surface_labels": duplicate_surface_labels,
        "operations_checked": [
            {"path": item["path"], "operation": str((item["payload"] or {}).get("operation", "")).strip()}
            for item in receipts
        ],
        "missing_operations": missing_operations,
        "duplicate_operations": duplicate_operations,
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
