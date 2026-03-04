#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ERR_FIXTURE_RUNTIME_BOUNDARY = "IP-PATH-004"

MUTATION_OPS = {"activate", "update", "readiness", "mutation", "e2e"}
INSPECTION_OPS = {"scan", "three-plane", "ci", "validate", "inspection"}


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"catalog root must be object: {path}")
    return raw


def _identity_row(catalog_path: Path, identity_id: str) -> dict[str, Any] | None:
    doc = _load_catalog(catalog_path)
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)


def _load_receipt(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _valid_receipt(
    receipt: dict[str, Any],
    *,
    identity_id: str,
    catalog_path: Path,
    operation: str,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    required = ("receipt_id", "identity_id", "catalog_path", "operation", "approved_by", "purpose", "approved_at")
    for key in required:
        if not str(receipt.get(key, "")).strip():
            reasons.append(f"fixture_override_receipt_missing_field:{key}")

    if str(receipt.get("identity_id", "")).strip() != identity_id:
        reasons.append("fixture_override_receipt_identity_mismatch")
    if str(receipt.get("catalog_path", "")).strip() != str(catalog_path):
        reasons.append("fixture_override_receipt_catalog_mismatch")

    rec_op = str(receipt.get("operation", "")).strip().lower()
    if rec_op not in {operation, "mutation"}:
        reasons.append("fixture_override_receipt_operation_mismatch")

    return len(reasons) == 0, reasons


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate fixture/runtime boundary for runtime mutation flows.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument(
        "--operation",
        choices=sorted(MUTATION_OPS | INSPECTION_OPS),
        default="mutation",
        help="execution surface semantics; mutation surfaces enforce fail-closed for fixture/demo identities",
    )
    ap.add_argument("--allow-fixture-runtime", action="store_true", help="explicit override for fixture runtime mutation")
    ap.add_argument(
        "--fixture-audit-receipt",
        default="",
        help="required JSON receipt path when --allow-fixture-runtime is set on mutation surfaces",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    operation = str(args.operation or "mutation").strip().lower()

    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    row = _identity_row(catalog_path, args.identity_id)
    if row is None:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "resolved_pack_path": "",
            "profile": "",
            "runtime_mode": "",
            "status": "",
            "operation": operation,
            "path_scope": "runtime_boundary",
            "path_governance_status": "FAIL_REQUIRED",
            "path_error_codes": [ERR_FIXTURE_RUNTIME_BOUNDARY],
            "canonicalization_ref": "Path.resolve(strict=False)",
            "allow_fixture_runtime": bool(args.allow_fixture_runtime),
            "fixture_audit_receipt": "",
            "stale_reasons": ["identity_not_found_in_catalog"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[FAIL] {ERR_FIXTURE_RUNTIME_BOUNDARY} identity not found in catalog: {args.identity_id}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    profile = str(row.get("profile", "")).strip().lower()
    runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
    status = str(row.get("status", "")).strip().lower()
    pack_raw = str(row.get("pack_path", "")).strip()
    pack_path = str(Path(pack_raw).expanduser().resolve()) if pack_raw else ""
    is_fixture = profile == "fixture" or runtime_mode == "demo_only"
    is_mutation = operation in MUTATION_OPS

    stale_reasons: list[str] = []
    receipt_path = Path(args.fixture_audit_receipt).expanduser().resolve() if args.fixture_audit_receipt.strip() else None
    receipt_payload: dict[str, Any] = {}

    if is_fixture and is_mutation:
        if not args.allow_fixture_runtime:
            stale_reasons.append("fixture_runtime_override_required")
        if not receipt_path:
            stale_reasons.append("fixture_override_receipt_missing")
        elif not receipt_path.exists():
            stale_reasons.append("fixture_override_receipt_not_found")
        else:
            receipt_payload = _load_receipt(receipt_path)
            if not receipt_payload:
                stale_reasons.append("fixture_override_receipt_invalid_json")
            else:
                ok_receipt, receipt_reasons = _valid_receipt(
                    receipt_payload,
                    identity_id=args.identity_id,
                    catalog_path=catalog_path,
                    operation=operation,
                )
                if not ok_receipt:
                    stale_reasons.extend(receipt_reasons)

    if is_fixture and (not is_mutation):
        if status == "active":
            stale_reasons.append("fixture_active_in_non_mutation_surface")

    if not is_fixture:
        path_status = "PASS_REQUIRED"
        path_error_codes: list[str] = []
    else:
        if stale_reasons:
            path_status = "FAIL_REQUIRED"
            path_error_codes = [ERR_FIXTURE_RUNTIME_BOUNDARY]
        else:
            if is_mutation:
                path_status = "PASS_REQUIRED"
                path_error_codes = []
            else:
                path_status = "SKIPPED_NOT_REQUIRED"
                path_error_codes = []
                stale_reasons = ["fixture_non_mutation_scope"]

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": pack_path,
        "profile": profile,
        "runtime_mode": runtime_mode,
        "status": status,
        "operation": operation,
        "path_scope": "runtime_mutation" if is_mutation else "inspection",
        "path_governance_status": path_status,
        "path_error_codes": path_error_codes,
        "canonicalization_ref": "Path.resolve(strict=False)",
        "allow_fixture_runtime": bool(args.allow_fixture_runtime),
        "fixture_audit_receipt": str(receipt_path) if receipt_path else "",
        "stale_reasons": stale_reasons,
        "fixture_receipt_fields": receipt_payload if receipt_payload else {},
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if path_status == "PASS_REQUIRED":
            print(
                "[OK] fixture/runtime boundary gate passed: "
                f"identity={args.identity_id} operation={operation} fixture={is_fixture}"
            )
        elif path_status == "SKIPPED_NOT_REQUIRED":
            print(
                "[OK] fixture/runtime boundary gate skipped (inspection scope): "
                f"identity={args.identity_id} operation={operation}"
            )
        else:
            print(
                f"[FAIL] {ERR_FIXTURE_RUNTIME_BOUNDARY} fixture/runtime boundary gate failed: "
                f"identity={args.identity_id} operation={operation}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if path_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
