#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from contract_bootstrap_emitter_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    materialize_required_bootstrap_emitters,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Materialize contract-declared bootstrap emitter receipts under shared protocol control."
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task_doc = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    result = materialize_required_bootstrap_emitters(
        repo_root=REPO_ROOT,
        catalog_path=catalog_path,
        identity_id=args.identity_id,
        task_doc=task_doc,
        operation=args.operation,
        apply=args.apply,
        force_required=args.force_required,
    )

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        **result,
    }

    _emit(payload, json_only=args.json_only)
    return 0 if payload["materialized_bootstrap_emitter_status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
