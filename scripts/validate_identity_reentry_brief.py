#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from identity_context_continuity_common import (
    REENTRY_BRIEF_CONSUMPTION_CONTRACT_ID,
    REENTRY_BRIEF_VALIDATOR_ID,
    REENTRY_CONSUMPTION_VALIDATOR_ID,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    clean_string,
    discover_continuity_artifact,
    issues_have_prefix,
    load_artifact_doc,
    reentry_contract_required,
    reentry_brief_location_status,
    resolve_pack_task,
    validate_continuity_artifact_doc,
    validate_contract_tuple,
    validate_reentry_brief_sections,
)

ERR_BRIEF_MISSING = "IP-REENTRY-001"
ERR_BRIEF_SCHEMA = "IP-REENTRY-002"
ERR_BRIEF_STALE = "IP-REENTRY-003"
ERR_BRIEF_CONTRACT = "IP-REENTRY-004"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate governed reentry brief structure for v1.6.16.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = clean_string(args.catalog)
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None

    try:
        pack_root, task_path, task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=clean_string(args.current_task),
            identity_id=args.identity_id,
        )
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    required_contract, contract_doc, contract_key = reentry_contract_required(task_doc)
    explicit_brief = clean_string(args.brief)
    force_validate = bool(explicit_brief)
    brief_path, brief_discovery_mode = discover_continuity_artifact(
        pack_root=pack_root,
        explicit_artifact=explicit_brief,
        artifact_kind="reentry_brief",
    )

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "brief_path": str(brief_path) if brief_path is not None else "",
        "brief_discovery_mode": brief_discovery_mode,
        "required_contract": required_contract,
        "contract_key": contract_key,
        "contract_id": clean_string(contract_doc.get("contract_id")),
        "identity_reentry_brief_status": STATUS_SKIPPED_NOT_REQUIRED,
        "brief_schema_status": STATUS_SKIPPED_NOT_REQUIRED,
        "stable_prefix_status": STATUS_SKIPPED_NOT_REQUIRED,
        "dynamic_tail_status": STATUS_SKIPPED_NOT_REQUIRED,
        "authority_refs_status": STATUS_SKIPPED_NOT_REQUIRED,
        "receipt_refs_status": STATUS_SKIPPED_NOT_REQUIRED,
        "freshness_status": STATUS_SKIPPED_NOT_REQUIRED,
        "lineage_status": STATUS_SKIPPED_NOT_REQUIRED,
        "artifact_location_status": STATUS_SKIPPED_NOT_REQUIRED,
        "continuity_id": "",
        "artifact_kind": "",
        "reentry_brief_ref": "",
        "continuity_lineage_ref": "",
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
            expected_contract_id=REENTRY_BRIEF_CONSUMPTION_CONTRACT_ID,
            accepted_validator_ids=(REENTRY_BRIEF_VALIDATOR_ID, REENTRY_CONSUMPTION_VALIDATOR_ID),
        )
        if contract_issues:
            payload["identity_reentry_brief_status"] = STATUS_FAIL_REQUIRED
            payload["brief_schema_status"] = STATUS_FAIL_REQUIRED
            payload["stable_prefix_status"] = STATUS_FAIL_REQUIRED
            payload["dynamic_tail_status"] = STATUS_FAIL_REQUIRED
            payload["authority_refs_status"] = STATUS_FAIL_REQUIRED
            payload["receipt_refs_status"] = STATUS_FAIL_REQUIRED
            payload["freshness_status"] = STATUS_FAIL_REQUIRED
            payload["lineage_status"] = STATUS_FAIL_REQUIRED
            payload["artifact_location_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_BRIEF_CONTRACT
            payload["stale_reasons"] = contract_issues
            _emit(payload, json_only=args.json_only)
            return 1

    if brief_path is None:
        payload["identity_reentry_brief_status"] = STATUS_FAIL_REQUIRED
        payload["brief_schema_status"] = STATUS_FAIL_REQUIRED
        payload["stable_prefix_status"] = STATUS_FAIL_REQUIRED
        payload["dynamic_tail_status"] = STATUS_FAIL_REQUIRED
        payload["authority_refs_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_refs_status"] = STATUS_FAIL_REQUIRED
        payload["freshness_status"] = STATUS_FAIL_REQUIRED
        payload["lineage_status"] = STATUS_FAIL_REQUIRED
        payload["artifact_location_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_BRIEF_MISSING
        payload["stale_reasons"] = ["reentry_brief_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        brief_doc = load_artifact_doc(brief_path)
    except Exception as exc:
        payload["identity_reentry_brief_status"] = STATUS_FAIL_REQUIRED
        payload["brief_schema_status"] = STATUS_FAIL_REQUIRED
        payload["stable_prefix_status"] = STATUS_FAIL_REQUIRED
        payload["dynamic_tail_status"] = STATUS_FAIL_REQUIRED
        payload["authority_refs_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_refs_status"] = STATUS_FAIL_REQUIRED
        payload["freshness_status"] = STATUS_FAIL_REQUIRED
        payload["lineage_status"] = STATUS_FAIL_REQUIRED
        payload["artifact_location_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_BRIEF_SCHEMA
        payload["stale_reasons"] = [f"reentry_brief_invalid_json:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    artifact_payload, schema_issues, stale_issues = validate_continuity_artifact_doc(
        artifact_doc=brief_doc,
        expected_identity_id=args.identity_id,
        expected_artifact_kind="reentry_brief",
    )
    payload.update(artifact_payload)
    payload["reentry_brief_ref"] = str(brief_path)
    payload["evidence_ref"] = str(brief_path)

    section_payload, section_issues = validate_reentry_brief_sections(brief_doc)
    payload.update(section_payload)
    if not payload.get("continuity_lineage_ref") and clean_string(payload.get("supersedes_ref")):
        payload["continuity_lineage_ref"] = clean_string(payload.get("supersedes_ref"))

    location_status, location_issues = reentry_brief_location_status(pack_root=pack_root, brief_path=brief_path)
    payload["artifact_location_status"] = location_status
    payload["authority_refs_status"] = (
        STATUS_FAIL_REQUIRED
        if issues_have_prefix(schema_issues, "authority_refs_missing", "authority_refs_row_invalid")
        else STATUS_PASS_REQUIRED
    )
    payload["receipt_refs_status"] = (
        STATUS_FAIL_REQUIRED
        if issues_have_prefix(schema_issues, "receipt_refs_missing", "receipt_refs_row_invalid")
        else STATUS_PASS_REQUIRED
    )
    payload["lineage_status"] = (
        STATUS_FAIL_REQUIRED
        if (
            not clean_string(payload.get("continuity_lineage_ref"))
            or issues_have_prefix(section_issues, "dynamic_tail_missing_family:lineage")
            or "supersedes_ref_self_cycle" in stale_issues
        )
        else STATUS_PASS_REQUIRED
    )

    stable_prefix = section_payload.get("stable_prefix")
    dynamic_tail = section_payload.get("dynamic_tail")
    payload["stable_prefix_status"] = (
        STATUS_FAIL_REQUIRED
        if (not isinstance(stable_prefix, dict) or issues_have_prefix(section_issues, "stable_prefix_"))
        else STATUS_PASS_REQUIRED
    )
    payload["dynamic_tail_status"] = (
        STATUS_FAIL_REQUIRED
        if (not isinstance(dynamic_tail, dict) or issues_have_prefix(section_issues, "dynamic_tail_"))
        else STATUS_PASS_REQUIRED
    )
    payload["freshness_status"] = (
        STATUS_FAIL_REQUIRED
        if ("freshness_indicates_stale" in stale_issues or "freshness_missing" in schema_issues)
        else STATUS_PASS_REQUIRED
    )

    issues = list(schema_issues)
    issues.extend(stale_issues)
    issues.extend(section_issues)
    issues.extend(location_issues)

    if issues:
        payload["identity_reentry_brief_status"] = STATUS_FAIL_REQUIRED
        payload["brief_schema_status"] = (
            STATUS_FAIL_REQUIRED if (schema_issues or section_issues or location_issues) else STATUS_PASS_REQUIRED
        )
        payload["error_code"] = ERR_BRIEF_STALE if stale_issues else ERR_BRIEF_SCHEMA
        payload["stale_reasons"] = issues
        _emit(payload, json_only=args.json_only)
        return 1

    payload["identity_reentry_brief_status"] = STATUS_PASS_REQUIRED
    payload["brief_schema_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
