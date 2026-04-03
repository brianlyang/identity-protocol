#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from identity_context_continuity_common import (
    CONTEXT_CONTINUITY_CONTRACT_ID,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    artifact_location_status,
    clean_string,
    continuity_contract_required,
    discover_continuity_artifact,
    freshness_indicates_stale,
    load_artifact_doc,
    normalize_ref_rows,
    ref_row_nonempty,
    resolve_pack_task,
    validate_continuity_artifact_doc,
    validate_contract_tuple,
)

ERR_ARTIFACT_MISSING = "IP-ICONT-001"
ERR_CONTRACT_INVALID = "IP-ICONT-002"
ERR_SCHEMA_INVALID = "IP-ICONT-003"
ERR_STALE_OR_OVERRIDE = "IP-ICONT-004"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

def main() -> int:
    ap = argparse.ArgumentParser(description="Validate continuity artifact schema/integrity for v1.6.16.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--artifact", default="")
    ap.add_argument("--artifact-kind", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = clean_string(args.catalog)
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None
    expected_artifact_kind = clean_string(args.artifact_kind)

    try:
        pack_root, task_path, task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=clean_string(args.current_task),
            identity_id=args.identity_id,
        )
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    required_contract, contract_doc, contract_key = continuity_contract_required(task_doc)
    explicit_artifact = clean_string(args.artifact)
    force_validate = bool(explicit_artifact or expected_artifact_kind)
    artifact_path, artifact_discovery_mode = discover_continuity_artifact(
        pack_root=pack_root,
        explicit_artifact=explicit_artifact,
        artifact_kind=expected_artifact_kind,
    )

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "artifact_path": str(artifact_path) if artifact_path is not None else "",
        "artifact_discovery_mode": artifact_discovery_mode,
        "expected_artifact_kind": expected_artifact_kind,
        "required_contract": required_contract,
        "contract_key": contract_key,
        "contract_id": clean_string(contract_doc.get("contract_id")),
        "identity_context_continuity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "artifact_schema_status": STATUS_SKIPPED_NOT_REQUIRED,
        "authority_refs_status": STATUS_SKIPPED_NOT_REQUIRED,
        "receipt_refs_status": STATUS_SKIPPED_NOT_REQUIRED,
        "freshness_status": STATUS_SKIPPED_NOT_REQUIRED,
        "lineage_status": STATUS_SKIPPED_NOT_REQUIRED,
        "artifact_location_status": STATUS_SKIPPED_NOT_REQUIRED,
        "continuity_id": "",
        "artifact_kind": "",
        "generation_reason": "",
        "trigger_class": "",
        "source_identity_id": "",
        "source_layer": "",
        "work_layer": "",
        "authority_refs": [],
        "task_focus_summary": None,
        "completed_since_previous": None,
        "open_blockers": None,
        "next_actions": None,
        "receipt_refs": [],
        "supersedes_ref": None,
        "freshness": None,
        "stale_reasons": [],
        "error_code": "",
        "evidence_ref": str(task_path),
    }

    if not required_contract and not force_validate:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if required_contract:
        contract_issues = validate_contract_tuple(
            contract_doc,
            expected_contract_id=CONTEXT_CONTINUITY_CONTRACT_ID,
            accepted_validator_ids=("scripts/validate_identity_context_continuity.py",),
        )
        if contract_issues:
            payload["identity_context_continuity_status"] = STATUS_FAIL_REQUIRED
            payload["artifact_schema_status"] = STATUS_FAIL_REQUIRED
            payload["authority_refs_status"] = STATUS_FAIL_REQUIRED
            payload["receipt_refs_status"] = STATUS_FAIL_REQUIRED
            payload["freshness_status"] = STATUS_FAIL_REQUIRED
            payload["lineage_status"] = STATUS_FAIL_REQUIRED
            payload["artifact_location_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONTRACT_INVALID
            payload["stale_reasons"] = contract_issues
            _emit(payload, json_only=args.json_only)
            return 1

    if artifact_path is None:
        payload["identity_context_continuity_status"] = STATUS_FAIL_REQUIRED
        payload["artifact_schema_status"] = STATUS_FAIL_REQUIRED
        payload["authority_refs_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_refs_status"] = STATUS_FAIL_REQUIRED
        payload["freshness_status"] = STATUS_FAIL_REQUIRED
        payload["lineage_status"] = STATUS_FAIL_REQUIRED
        payload["artifact_location_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ARTIFACT_MISSING
        payload["stale_reasons"] = ["continuity_artifact_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        artifact_doc = load_artifact_doc(artifact_path)
    except Exception as exc:
        payload["identity_context_continuity_status"] = STATUS_FAIL_REQUIRED
        payload["artifact_schema_status"] = STATUS_FAIL_REQUIRED
        payload["authority_refs_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_refs_status"] = STATUS_FAIL_REQUIRED
        payload["freshness_status"] = STATUS_FAIL_REQUIRED
        payload["lineage_status"] = STATUS_FAIL_REQUIRED
        payload["artifact_location_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SCHEMA_INVALID
        payload["stale_reasons"] = [f"artifact_json_invalid:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    artifact_payload, schema_issues, stale_issues = validate_continuity_artifact_doc(
        artifact_doc=artifact_doc,
        expected_identity_id=args.identity_id,
        expected_artifact_kind=expected_artifact_kind,
    )
    issues = list(schema_issues)
    error_code = ERR_SCHEMA_INVALID if schema_issues else ""
    if stale_issues:
        issues.extend(stale_issues)
        if not error_code:
            error_code = ERR_STALE_OR_OVERRIDE
    payload.update(artifact_payload)
    payload["evidence_ref"] = str(artifact_path)

    location_status, location_issues = artifact_location_status(pack_root=pack_root, artifact_path=artifact_path)
    payload["artifact_location_status"] = location_status
    issues.extend(location_issues)

    if location_status == STATUS_FAIL_REQUIRED and not error_code:
        error_code = ERR_STALE_OR_OVERRIDE

    authority_rows = normalize_ref_rows(payload.get("authority_refs"))
    receipt_rows = normalize_ref_rows(payload.get("receipt_refs"))
    payload["authority_refs_status"] = STATUS_PASS_REQUIRED if authority_rows and all(ref_row_nonempty(row) for row in authority_rows) else STATUS_FAIL_REQUIRED
    payload["receipt_refs_status"] = STATUS_PASS_REQUIRED if receipt_rows and all(ref_row_nonempty(row) for row in receipt_rows) else STATUS_FAIL_REQUIRED
    payload["freshness_status"] = STATUS_FAIL_REQUIRED if freshness_indicates_stale(payload.get("freshness")) else STATUS_PASS_REQUIRED
    payload["lineage_status"] = STATUS_FAIL_REQUIRED if "supersedes_ref_self_cycle" in issues else STATUS_PASS_REQUIRED

    if issues:
        payload["identity_context_continuity_status"] = STATUS_FAIL_REQUIRED
        payload["artifact_schema_status"] = STATUS_FAIL_REQUIRED if error_code == ERR_SCHEMA_INVALID else STATUS_PASS_REQUIRED
        if error_code == ERR_STALE_OR_OVERRIDE:
            payload["freshness_status"] = STATUS_FAIL_REQUIRED if (
                freshness_indicates_stale(payload.get("freshness")) or any(
                    token.startswith("authority_override") or token == "checkpoint_artifact_contains_reentry_only_fields"
                    for token in issues
                )
            ) else payload["freshness_status"]
        payload["error_code"] = error_code or ERR_SCHEMA_INVALID
        payload["stale_reasons"] = issues
        _emit(payload, json_only=args.json_only)
        return 1

    payload["identity_context_continuity_status"] = STATUS_PASS_REQUIRED
    payload["artifact_schema_status"] = STATUS_PASS_REQUIRED
    payload["artifact_location_status"] = location_status
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
