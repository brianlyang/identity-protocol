#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from identity_context_continuity_common import (
    AUTHORITY_OVERRIDE_KEYS,
    CHECKPOINT_ARTIFACT_KINDS,
    CONTEXT_CONTINUITY_CONTRACT_ID,
    CONTEXT_CONTINUITY_CONTRACT_KEY,
    CONTEXT_CONTINUITY_VALIDATOR_ID,
    CONTINUITY_ARTIFACT_KINDS,
    REENTRY_BRIEF_REL,
    REPORT_ROOT_REL,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    boolish,
    clean_string,
    continuity_contract_required,
    continuity_report_root,
    continuity_state_root,
    discover_continuity_artifact,
    freshness_indicates_stale,
    load_artifact_doc,
    nonempty,
    normalize_ref_rows,
    path_within,
    ref_row_nonempty,
    resolve_pack_task,
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


def _validate_contract(contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if clean_string(contract.get("contract_id")) != CONTEXT_CONTINUITY_CONTRACT_ID:
        issues.append("contract_id_mismatch")
    if clean_string(contract.get("validator")) != CONTEXT_CONTINUITY_VALIDATOR_ID:
        issues.append("validator_mismatch")
    if clean_string(contract.get("fail_mode")).lower() != "fail_required":
        issues.append("fail_mode_not_fail_required")
    return issues


def _field_present(doc: dict[str, Any], field: str) -> bool:
    return field in doc


def _validate_ref_family(field_name: str, value: Any) -> tuple[list[Any], list[str]]:
    rows = normalize_ref_rows(value)
    issues: list[str] = []
    if not rows:
        issues.append(f"{field_name}_missing")
        return rows, issues
    for idx, row in enumerate(rows):
        if not ref_row_nonempty(row):
            issues.append(f"{field_name}_row_invalid:{idx}")
    return rows, issues


def _task_field_present(field_name: str, value: Any) -> list[str]:
    if value is None:
        return [f"{field_name}_missing"]
    if isinstance(value, str) and not value.strip():
        return [f"{field_name}_blank"]
    if isinstance(value, (list, dict)) and field_name == "task_focus_summary" and not value:
        return [f"{field_name}_blank"]
    return []


def _location_status(*, pack_root: Path, artifact_path: Path) -> tuple[str, list[str]]:
    if not path_within(artifact_path, pack_root):
        return "NOT_PACK_SCOPED", []
    if path_within(artifact_path, pack_root / "scripts"):
        return STATUS_FAIL_REQUIRED, ["artifact_under_scripts_surface"]
    if path_within(artifact_path, continuity_report_root(pack_root)):
        return STATUS_PASS_REQUIRED, []
    if path_within(artifact_path, continuity_state_root(pack_root)):
        return STATUS_PASS_REQUIRED, []
    return STATUS_FAIL_REQUIRED, ["artifact_outside_canonical_runtime_family"]


def _validate_artifact(
    *,
    artifact_doc: dict[str, Any],
    expected_identity_id: str,
    expected_artifact_kind: str,
) -> tuple[dict[str, Any], str, list[str]]:
    continuity_id = clean_string(artifact_doc.get("continuity_id"))
    artifact_kind = clean_string(artifact_doc.get("artifact_kind"))
    generation_reason = clean_string(artifact_doc.get("generation_reason"))
    trigger_class = clean_string(artifact_doc.get("trigger_class"))
    source_identity_id = clean_string(artifact_doc.get("source_identity_id"))
    source_layer = clean_string(artifact_doc.get("source_layer"))
    work_layer = clean_string(artifact_doc.get("work_layer"))
    task_focus_summary = artifact_doc.get("task_focus_summary")
    completed_since_previous = artifact_doc.get("completed_since_previous")
    open_blockers = artifact_doc.get("open_blockers")
    next_actions = artifact_doc.get("next_actions")
    supersedes_ref = artifact_doc.get("supersedes_ref")
    freshness = artifact_doc.get("freshness")

    authority_refs, authority_issues = _validate_ref_family("authority_refs", artifact_doc.get("authority_refs"))
    receipt_refs, receipt_issues = _validate_ref_family("receipt_refs", artifact_doc.get("receipt_refs"))

    schema_issues: list[str] = []
    stale_issues: list[str] = []

    if not continuity_id:
        schema_issues.append("continuity_id_missing")
    if artifact_kind not in CONTINUITY_ARTIFACT_KINDS:
        schema_issues.append("artifact_kind_invalid")
    if expected_artifact_kind and artifact_kind != expected_artifact_kind:
        schema_issues.append(f"artifact_kind_mismatch:{expected_artifact_kind}")
    if not generation_reason:
        schema_issues.append("generation_reason_missing")
    if not trigger_class:
        schema_issues.append("trigger_class_missing")
    if not source_identity_id:
        schema_issues.append("source_identity_id_missing")
    elif expected_identity_id and source_identity_id != expected_identity_id:
        schema_issues.append(f"source_identity_id_mismatch:{source_identity_id}")
    if not source_layer:
        schema_issues.append("source_layer_missing")
    if not work_layer:
        schema_issues.append("work_layer_missing")

    schema_issues.extend(authority_issues)
    schema_issues.extend(receipt_issues)
    schema_issues.extend(_task_field_present("task_focus_summary", task_focus_summary))
    schema_issues.extend(_task_field_present("completed_since_previous", completed_since_previous))
    schema_issues.extend(_task_field_present("open_blockers", open_blockers))
    schema_issues.extend(_task_field_present("next_actions", next_actions))

    if not _field_present(artifact_doc, "supersedes_ref"):
        schema_issues.append("supersedes_ref_missing")
    if not _field_present(artifact_doc, "freshness"):
        schema_issues.append("freshness_missing")

    if artifact_kind == "reentry_brief":
        if not nonempty(artifact_doc.get("stable_prefix")):
            schema_issues.append("stable_prefix_missing")
        if not nonempty(artifact_doc.get("dynamic_tail")):
            schema_issues.append("dynamic_tail_missing")
    elif artifact_kind in CHECKPOINT_ARTIFACT_KINDS:
        if "stable_prefix" in artifact_doc or "dynamic_tail" in artifact_doc:
            stale_issues.append("checkpoint_artifact_contains_reentry_only_fields")

    if boolish(artifact_doc.get("authority_override")):
        stale_issues.append("authority_override_attempt")
    for key in AUTHORITY_OVERRIDE_KEYS:
        value = artifact_doc.get(key)
        if key == "authority_override":
            continue
        if nonempty(value):
            stale_issues.append(f"authority_override_key_present:{key}")

    if continuity_id and clean_string(supersedes_ref) == continuity_id:
        stale_issues.append("supersedes_ref_self_cycle")
    if freshness_indicates_stale(freshness):
        stale_issues.append("freshness_indicates_stale")

    normalized_payload: dict[str, Any] = {
        "continuity_id": continuity_id,
        "artifact_kind": artifact_kind,
        "generation_reason": generation_reason,
        "trigger_class": trigger_class,
        "source_identity_id": source_identity_id,
        "source_layer": source_layer,
        "work_layer": work_layer,
        "authority_refs": authority_refs,
        "task_focus_summary": task_focus_summary,
        "completed_since_previous": completed_since_previous,
        "open_blockers": open_blockers,
        "next_actions": next_actions,
        "receipt_refs": receipt_refs,
        "supersedes_ref": supersedes_ref,
        "freshness": freshness,
    }
    if artifact_kind == "reentry_brief":
        normalized_payload["stable_prefix"] = artifact_doc.get("stable_prefix")
        normalized_payload["dynamic_tail"] = artifact_doc.get("dynamic_tail")

    if schema_issues:
        return normalized_payload, ERR_SCHEMA_INVALID, schema_issues
    if stale_issues:
        return normalized_payload, ERR_STALE_OR_OVERRIDE, stale_issues
    return normalized_payload, "", []


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
        contract_issues = _validate_contract(contract_doc)
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

    artifact_payload, error_code, issues = _validate_artifact(
        artifact_doc=artifact_doc,
        expected_identity_id=args.identity_id,
        expected_artifact_kind=expected_artifact_kind,
    )
    payload.update(artifact_payload)
    payload["evidence_ref"] = str(artifact_path)

    location_status, location_issues = _location_status(pack_root=pack_root, artifact_path=artifact_path)
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
