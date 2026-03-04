#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from response_stamp_common import blocker_receipt, resolve_stamp_context
from tool_vendor_governance_common import contract_required, load_json

ERR_BLOCKER_RECEIPT = "IP-ASB-STAMP-001"


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "identity_response_stamp_contract",
        "response_stamp_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _resolve_pack_and_task(catalog_path: Path, identity_id: str) -> tuple[Path, Path]:
    import yaml

    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_raw = str((row or {}).get("pack_path", "")).strip()
    if not pack_raw:
        raise FileNotFoundError(f"pack_path missing for identity: {identity_id}")
    pack = Path(pack_raw).expanduser().resolve()
    if not pack.exists():
        raise FileNotFoundError(f"pack_path not found: {pack}")
    task = pack / "CURRENT_TASK.json"
    if not task.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found: {task}")
    return pack, task


def _validate_receipt_schema(payload: dict[str, Any]) -> list[str]:
    required = (
        "error_code",
        "expected_identity_id",
        "actual_identity_id",
        "source_domain",
        "resolver_ref",
        "next_action",
        "generated_at",
    )
    missing = [k for k in required if not str(payload.get(k, "")).strip()]
    return missing


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate blocker receipt contract for response stamp mismatch.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--receipt", default="")
    ap.add_argument("--force-check", action="store_true", help="run checks even when contract.required is false")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        _, task_path = _resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    if not args.force_check and not contract_required(contract):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "receipt_status": "SKIPPED_NOT_REQUIRED",
            "error_code": "",
            "stale_reasons": ["contract_not_required"],
            "required_contract": False,
            "receipt_path": "",
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[OK] response stamp blocker receipt contract not required for identity={args.identity_id}; skipped")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        ctx = resolve_stamp_context(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            explicit_catalog=bool(args.catalog.strip()),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve stamp context: {exc}")
        return 1

    receipt_path = Path(args.receipt).expanduser().resolve() if args.receipt.strip() else None
    if receipt_path and receipt_path.exists():
        try:
            receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[FAIL] {ERR_BLOCKER_RECEIPT} invalid receipt json: {receipt_path} ({exc})")
            return 1
    else:
        receipt_payload = blocker_receipt(
            error_code=ERR_BLOCKER_RECEIPT,
            expected_identity_id=ctx.identity_id,
            actual_identity_id=f"{ctx.identity_id}-mismatch",
            source_domain=ctx.source_domain,
            resolver_ref=f"{catalog_path.parent}/session/active_identity.json",
            next_action="refresh_identity_binding_then_retry",
        )

    if not isinstance(receipt_payload, dict):
        print(f"[FAIL] {ERR_BLOCKER_RECEIPT} receipt payload must be object")
        return 1

    missing = _validate_receipt_schema(receipt_payload)
    if missing:
        print(f"[FAIL] {ERR_BLOCKER_RECEIPT} blocker receipt missing required fields: {missing}")
        return 1

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "receipt_path": str(receipt_path) if receipt_path else "",
        "receipt_status": "PASS",
        "receipt_fields": receipt_payload,
    }
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"[OK] response stamp blocker receipt validated for identity={args.identity_id}")
        print("validate_identity_response_stamp_blocker_receipt PASSED")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
