#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from identity_context_continuity_common import (
    REENTRY_BRIEF_CONSUMPTION_CONTRACT_ID,
    REENTRY_BRIEF_REL,
    REENTRY_BRIEF_VALIDATOR_ID,
    REENTRY_CONSUMPTION_VALIDATOR_ID,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    clean_string,
    continuity_report_location_status,
    discover_continuity_artifact,
    discover_continuity_report_doc,
    issues_have_prefix,
    load_artifact_doc,
    nonempty,
    reentry_contract_required,
    reentry_brief_location_status,
    resolve_pack_task,
    validate_continuity_artifact_doc,
    validate_contract_tuple,
    validate_reentry_brief_sections,
)

ERR_CONSUMPTION_MISSING = "IP-REENTRY-001"
ERR_CONSUMPTION_PREREQ = "IP-REENTRY-002"
ERR_CONSUMPTION_INVALID = "IP-REENTRY-003"
ERR_CONSUMPTION_CONTRACT = "IP-REENTRY-004"

REQUIRED_RECEIPT_FIELDS: tuple[str, ...] = (
    "identity_reentry_brief_status",
    "startup_consumption_status",
    "reentry_brief_ref",
    "continuity_lineage_ref",
    "authority_resolution_status",
    "tuple_bootstrap_preserved",
    "launcher_bind_status",
    "consumption_outcome",
)
PASS_TOKENS = {"PASS_REQUIRED", "PASS", "READY"}
BAD_OUTCOME_TOKENS = ("raw_transcript", "operator", "narrative_only", "ungoverned")
EXPECTED_RECEIPT_KIND = "instance_reentry_consumption_receipt"
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = REPO_ROOT.parent


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _status_pass(value: Any) -> bool:
    return clean_string(value).upper() in PASS_TOKENS


def _bool_or_status_pass(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _status_pass(value)


def _looks_like_path(token: str) -> bool:
    return "/" in token or token.endswith(".json") or token.startswith(".")


def _resolve_local_reference(token: str, *, pack_root: Path) -> Path | None:
    text = clean_string(token)
    if not text:
        return None
    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
        return resolved if resolved.exists() else None
    for base in (pack_root, REPO_ROOT, WORKSPACE_ROOT):
        resolved = (base / candidate).resolve()
        if resolved.exists():
            return resolved
    return None


def _read_receipt(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _field_missing(doc: dict[str, Any], field: str) -> bool:
    return field not in doc or not nonempty(doc.get(field))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate governed startup consumption of reentry briefs for v1.6.16.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--receipt", default="")
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
    explicit_receipt = clean_string(args.receipt)
    force_validate = bool(explicit_brief or explicit_receipt)

    brief_path, brief_mode = discover_continuity_artifact(
        pack_root=pack_root,
        explicit_artifact=explicit_brief,
        artifact_kind="reentry_brief",
    )
    receipt_path, receipt_mode = discover_continuity_report_doc(
        pack_root=pack_root,
        explicit_report=explicit_receipt,
        required_fields=REQUIRED_RECEIPT_FIELDS,
        preferred_receipt_kind=EXPECTED_RECEIPT_KIND,
        selection_requires_fields=False,
    )

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "brief_path": str(brief_path) if brief_path is not None else "",
        "brief_discovery_mode": brief_mode,
        "receipt_path": str(receipt_path) if receipt_path is not None else "",
        "receipt_discovery_mode": receipt_mode,
        "required_contract": required_contract,
        "contract_key": contract_key,
        "contract_id": clean_string(contract_doc.get("contract_id")),
        "identity_reentry_consumption_status": STATUS_SKIPPED_NOT_REQUIRED,
        "identity_reentry_brief_status": STATUS_SKIPPED_NOT_REQUIRED,
        "startup_consumption_status": STATUS_SKIPPED_NOT_REQUIRED,
        "authority_resolution_status": STATUS_SKIPPED_NOT_REQUIRED,
        "tuple_bootstrap_preserved": False,
        "launcher_bind_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reentry_brief_ref": "",
        "continuity_lineage_ref": "",
        "consumption_outcome": "",
        "brief_schema_status": STATUS_SKIPPED_NOT_REQUIRED,
        "brief_location_status": STATUS_SKIPPED_NOT_REQUIRED,
        "receipt_evidence_status": STATUS_SKIPPED_NOT_REQUIRED,
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
            payload["identity_reentry_consumption_status"] = STATUS_FAIL_REQUIRED
            payload["identity_reentry_brief_status"] = STATUS_FAIL_REQUIRED
            payload["startup_consumption_status"] = STATUS_FAIL_REQUIRED
            payload["authority_resolution_status"] = STATUS_FAIL_REQUIRED
            payload["launcher_bind_status"] = STATUS_FAIL_REQUIRED
            payload["brief_schema_status"] = STATUS_FAIL_REQUIRED
            payload["brief_location_status"] = STATUS_FAIL_REQUIRED
            payload["receipt_evidence_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONSUMPTION_CONTRACT
            payload["stale_reasons"] = contract_issues
            _emit(payload, json_only=args.json_only)
            return 1

    if brief_path is None:
        payload["identity_reentry_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["identity_reentry_brief_status"] = STATUS_FAIL_REQUIRED
        payload["startup_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["authority_resolution_status"] = STATUS_FAIL_REQUIRED
        payload["launcher_bind_status"] = STATUS_FAIL_REQUIRED
        payload["brief_schema_status"] = STATUS_FAIL_REQUIRED
        payload["brief_location_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONSUMPTION_MISSING
        payload["stale_reasons"] = ["reentry_brief_not_found_for_consumption"]
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        brief_doc = load_artifact_doc(brief_path)
    except Exception as exc:
        payload["identity_reentry_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["identity_reentry_brief_status"] = STATUS_FAIL_REQUIRED
        payload["startup_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["authority_resolution_status"] = STATUS_FAIL_REQUIRED
        payload["launcher_bind_status"] = STATUS_FAIL_REQUIRED
        payload["brief_schema_status"] = STATUS_FAIL_REQUIRED
        payload["brief_location_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONSUMPTION_PREREQ
        payload["stale_reasons"] = [f"reentry_brief_invalid_json:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    brief_payload, brief_schema_issues, brief_stale_issues = validate_continuity_artifact_doc(
        artifact_doc=brief_doc,
        expected_identity_id=args.identity_id,
        expected_artifact_kind="reentry_brief",
    )
    section_payload, section_issues = validate_reentry_brief_sections(brief_doc)
    brief_location_status, brief_location_issues = reentry_brief_location_status(pack_root=pack_root, brief_path=brief_path)
    payload["brief_schema_status"] = STATUS_FAIL_REQUIRED if brief_schema_issues or section_issues else STATUS_PASS_REQUIRED
    payload["brief_location_status"] = brief_location_status
    payload["identity_reentry_brief_status"] = STATUS_FAIL_REQUIRED if (brief_schema_issues or brief_stale_issues or section_issues or brief_location_issues) else STATUS_PASS_REQUIRED

    if brief_schema_issues or brief_stale_issues or section_issues or brief_location_issues:
        issues = list(brief_schema_issues) + list(brief_stale_issues) + list(section_issues) + list(brief_location_issues)
        payload.update(brief_payload)
        payload.update(section_payload)
        payload["reentry_brief_ref"] = str(brief_path)
        payload["continuity_lineage_ref"] = clean_string(section_payload.get("continuity_lineage_ref") or brief_payload.get("supersedes_ref"))
        payload["identity_reentry_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["startup_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["authority_resolution_status"] = STATUS_FAIL_REQUIRED
        payload["launcher_bind_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONSUMPTION_PREREQ
        payload["stale_reasons"] = issues
        payload["evidence_ref"] = str(brief_path)
        _emit(payload, json_only=args.json_only)
        return 1

    if receipt_path is None:
        payload.update(brief_payload)
        payload.update(section_payload)
        payload["reentry_brief_ref"] = str(brief_path)
        payload["continuity_lineage_ref"] = clean_string(section_payload.get("continuity_lineage_ref") or brief_payload.get("supersedes_ref"))
        payload["identity_reentry_brief_status"] = STATUS_PASS_REQUIRED
        payload["identity_reentry_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["startup_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["authority_resolution_status"] = STATUS_FAIL_REQUIRED
        payload["launcher_bind_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONSUMPTION_MISSING
        payload["stale_reasons"] = ["reentry_consumption_receipt_not_found"]
        payload["evidence_ref"] = str(brief_path)
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        receipt_doc = _read_receipt(receipt_path)
        if not isinstance(receipt_doc, dict):
            raise ValueError("receipt_root_not_object")
    except Exception as exc:
        payload["identity_reentry_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["identity_reentry_brief_status"] = STATUS_PASS_REQUIRED
        payload["startup_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["authority_resolution_status"] = STATUS_FAIL_REQUIRED
        payload["launcher_bind_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONSUMPTION_INVALID
        payload["stale_reasons"] = [f"reentry_consumption_receipt_invalid:{exc}"]
        payload["evidence_ref"] = str(receipt_path)
        _emit(payload, json_only=args.json_only)
        return 1

    issues: list[str] = []
    missing_fields: set[str] = set()
    for field in REQUIRED_RECEIPT_FIELDS:
        if _field_missing(receipt_doc, field):
            issues.append(f"missing_required_receipt_field:{field}")
            missing_fields.add(field)

    payload["reentry_brief_ref"] = clean_string(receipt_doc.get("reentry_brief_ref"))
    payload["continuity_lineage_ref"] = clean_string(receipt_doc.get("continuity_lineage_ref"))
    payload["consumption_outcome"] = clean_string(receipt_doc.get("consumption_outcome"))

    receipt_kind = clean_string(receipt_doc.get("receipt_kind") or receipt_doc.get("receipt_family"))
    if not receipt_kind:
        issues.append("receipt_kind_missing")
    elif receipt_kind != EXPECTED_RECEIPT_KIND:
        issues.append(f"receipt_kind_mismatch:{receipt_kind}")

    receipt_location_status, receipt_location_issues = continuity_report_location_status(
        pack_root=pack_root,
        report_path=receipt_path,
    )
    if receipt_location_status != STATUS_PASS_REQUIRED:
        issues.extend(receipt_location_issues)

    if "identity_reentry_brief_status" not in missing_fields and not _status_pass(receipt_doc.get("identity_reentry_brief_status")):
        issues.append("identity_reentry_brief_status_not_pass")
    if "startup_consumption_status" not in missing_fields and not _status_pass(receipt_doc.get("startup_consumption_status")):
        issues.append("startup_consumption_status_not_pass")
    if "authority_resolution_status" not in missing_fields and not _status_pass(receipt_doc.get("authority_resolution_status")):
        issues.append("authority_resolution_status_not_pass")
    if "launcher_bind_status" not in missing_fields and not _status_pass(receipt_doc.get("launcher_bind_status")):
        issues.append("launcher_bind_status_not_pass")
    if "tuple_bootstrap_preserved" not in missing_fields and not _bool_or_status_pass(receipt_doc.get("tuple_bootstrap_preserved")):
        issues.append("tuple_bootstrap_not_preserved")
    if "consumption_outcome" not in missing_fields and any(
        token in clean_string(receipt_doc.get("consumption_outcome")).lower() for token in BAD_OUTCOME_TOKENS
    ):
        issues.append("consumption_outcome_non_governed")

    brief_ref_token = clean_string(receipt_doc.get("reentry_brief_ref"))
    if brief_ref_token:
        resolved_brief_ref = _resolve_local_reference(brief_ref_token, pack_root=pack_root)
        if resolved_brief_ref is not None:
            if resolved_brief_ref != brief_path.resolve():
                issues.append("reentry_brief_ref_mismatch")
        elif clean_string(brief_ref_token) not in {
            str(REENTRY_BRIEF_REL.as_posix()),
            brief_path.name,
            str(brief_path.resolve()),
        }:
            issues.append("reentry_brief_ref_unresolved")

    lineage_token = clean_string(receipt_doc.get("continuity_lineage_ref"))
    if lineage_token:
        resolved_lineage_ref = _resolve_local_reference(lineage_token, pack_root=pack_root)
        if resolved_lineage_ref is None and _looks_like_path(lineage_token):
            issues.append("continuity_lineage_ref_unresolved")
    else:
        issues.append("continuity_lineage_ref_missing")

    payload["tuple_bootstrap_preserved"] = bool(_bool_or_status_pass(receipt_doc.get("tuple_bootstrap_preserved")))
    payload["identity_reentry_brief_status"] = STATUS_PASS_REQUIRED if _status_pass(receipt_doc.get("identity_reentry_brief_status")) else STATUS_FAIL_REQUIRED
    payload["startup_consumption_status"] = STATUS_PASS_REQUIRED if _status_pass(receipt_doc.get("startup_consumption_status")) else STATUS_FAIL_REQUIRED
    payload["authority_resolution_status"] = STATUS_PASS_REQUIRED if _status_pass(receipt_doc.get("authority_resolution_status")) else STATUS_FAIL_REQUIRED
    payload["launcher_bind_status"] = STATUS_PASS_REQUIRED if _status_pass(receipt_doc.get("launcher_bind_status")) else STATUS_FAIL_REQUIRED
    payload["receipt_evidence_status"] = STATUS_FAIL_REQUIRED if issues else STATUS_PASS_REQUIRED
    payload["brief_schema_status"] = STATUS_FAIL_REQUIRED if (brief_schema_issues or section_issues) else STATUS_PASS_REQUIRED
    payload["brief_location_status"] = brief_location_status
    payload["evidence_ref"] = str(receipt_path)

    if issues:
        payload["identity_reentry_consumption_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONSUMPTION_INVALID
        payload["stale_reasons"] = issues
        if issues_have_prefix(issues, "missing_required_receipt_field:authority_resolution_status", "authority_resolution_status_not_pass"):
            payload["authority_resolution_status"] = STATUS_FAIL_REQUIRED
        if issues_have_prefix(issues, "missing_required_receipt_field:launcher_bind_status", "launcher_bind_status_not_pass"):
            payload["launcher_bind_status"] = STATUS_FAIL_REQUIRED
        if issues_have_prefix(issues, "missing_required_receipt_field:startup_consumption_status", "startup_consumption_status_not_pass"):
            payload["startup_consumption_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    payload["identity_reentry_consumption_status"] = STATUS_PASS_REQUIRED
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
