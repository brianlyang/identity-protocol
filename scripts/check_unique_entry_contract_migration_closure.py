#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from protocol_infra_contract import (
    UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS,
)
from runtime_fleet_closure_common import STATUS_FAIL_REQUIRED, STATUS_PASS_REQUIRED
from runtime_pack_closure_common import collect_active_runtime_pack_closure

ERR_CONTRACT_INVALID = "IP-GATE-ENTRY-002"


def _safe_load_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _evaluate_row(**kwargs: Any) -> dict[str, Any]:
    pack_path = kwargs.get("pack_path")
    if not isinstance(pack_path, Path):
        raise TypeError("pack_path_missing")
    task_path = (pack_path / "CURRENT_TASK.json").resolve()
    row_state = {
        "task_path": str(task_path),
        "max_age_seconds": 0,
        "selector_policy_id": "",
        "selector_precedence": [],
        "selector_source_fields": [],
        "status": STATUS_PASS_REQUIRED,
        "reason": "",
    }
    if not task_path.exists() or not task_path.is_file():
        row_state["status"] = STATUS_FAIL_REQUIRED
        row_state["reason"] = "current_task_missing"
        return row_state

    task_doc = _safe_load_json(task_path)
    contract = task_doc.get("protocol_unique_entry_gate_contract_v1")
    if not isinstance(contract, dict):
        row_state["status"] = STATUS_FAIL_REQUIRED
        row_state["reason"] = "unique_entry_contract_missing"
        return row_state

    raw_max_age = contract.get("entry_receipt_max_age_seconds", 0)
    try:
        max_age = int(raw_max_age)
    except Exception:
        max_age = 0
    row_state["max_age_seconds"] = max_age
    row_state["selector_policy_id"] = str(contract.get("entry_receipt_selector_policy_id", "")).strip()
    row_state["selector_precedence"] = [
        str(x).strip() for x in (contract.get("entry_receipt_selector_precedence") or []) if str(x).strip()
    ]
    row_state["selector_source_fields"] = [
        str(x).strip() for x in (contract.get("entry_receipt_selector_source_fields") or []) if str(x).strip()
    ]
    if max_age <= 0:
        row_state["status"] = STATUS_FAIL_REQUIRED
        row_state["reason"] = "entry_receipt_max_age_seconds_invalid"
        return row_state
    if row_state["selector_policy_id"] != UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID:
        row_state["status"] = STATUS_FAIL_REQUIRED
        row_state["reason"] = "entry_receipt_selector_policy_id_invalid"
        return row_state
    if list(row_state["selector_precedence"]) != list(UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE):
        row_state["status"] = STATUS_FAIL_REQUIRED
        row_state["reason"] = "entry_receipt_selector_precedence_invalid"
        return row_state
    if list(row_state["selector_source_fields"]) != list(UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS):
        row_state["status"] = STATUS_FAIL_REQUIRED
        row_state["reason"] = "entry_receipt_selector_source_fields_invalid"
    return row_state


def main() -> int:
    ap = argparse.ArgumentParser(description="Check unique-entry max-age migration closure for active runtime identities.")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml", help="repository catalog path (default: identity/catalog/identities.yaml)")
    ap.add_argument("--catalog", action="append", default=[], help="additional catalog(s) to check; missing paths are skipped")
    ap.add_argument("--include-env-catalog", action="store_true", help="include $IDENTITY_CATALOG when set")
    ap.add_argument("--workspace-runtime-only", action="store_true", help="exclude the repository fixture catalog and check only explicitly provided workspace/runtime catalogs")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    payload = collect_active_runtime_pack_closure(
        repo_root=repo_root,
        repo_catalog_arg=args.repo_catalog,
        raw_catalogs=args.catalog,
        include_env_catalog=bool(args.include_env_catalog),
        workspace_runtime_only=bool(args.workspace_runtime_only),
        caller_anchor=Path.cwd().resolve(),
        caller_start=Path(__file__).resolve(),
        payload_status_key="unique_entry_contract_migration_closure_status",
        error_code=ERR_CONTRACT_INVALID,
        row_evaluator=_evaluate_row,
    )

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if str(payload.get("unique_entry_contract_migration_closure_status", "")).strip().upper() == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
