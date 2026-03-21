#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, path_within, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

INSTANCE_SCRIPT_MANIFEST_REL = Path("scripts/INSTANCE_SCRIPT_MANIFEST.json")
INSTANCE_SCRIPT_ROUTE_FIELDS: tuple[str, ...] = (
    "primary_instance_scripts",
    "fallback_instance_scripts",
    "script_preconditions",
    "script_receipt_pattern",
)
PRECONDITION_FIELDS: tuple[str, ...] = (
    "identity_lock",
    "work_layer",
    "source_layer",
    "required_contracts",
    "gate_policies",
)
TOKEN_RE = re.compile(r"^[a-z][a-z0-9_:-]*$")


def clean_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        token = value.strip()
        return [token] if token else []
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        token = str(item).strip()
        if token:
            out.append(token)
    return out


def normalize_source_layer(catalog_path: Path | None) -> str:
    if catalog_path is None:
        return "project"
    token = catalog_path.expanduser().resolve().as_posix()
    return "global" if "/.codex/.identity/" in token else "project"


def resolve_pack_task(
    *,
    catalog_path: Path | None,
    current_task: str,
    identity_id: str,
) -> tuple[Path, Path, dict[str, Any]]:
    task_raw = str(current_task or "").strip()
    if task_raw:
        task_path = Path(task_raw).expanduser().resolve()
        pack_root = task_path.parent.resolve()
        task_doc = load_json(task_path)
        return pack_root, task_path, task_doc
    if catalog_path is None or not catalog_path.exists():
        missing_catalog = catalog_path if catalog_path is not None else "<missing>"
        raise FileNotFoundError(f"catalog not found: {missing_catalog}")
    pack_root, task_path = resolve_pack_and_task(catalog_path, identity_id)
    task_doc = load_json(task_path)
    return pack_root, task_path, task_doc


def task_type_routes(task_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    contract = task_doc.get("capability_orchestration_contract")
    if not isinstance(contract, dict):
        return {}
    routes = contract.get("task_type_routes")
    if not isinstance(routes, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for name, row in routes.items():
        if not isinstance(row, dict):
            continue
        token = str(name).strip()
        if token:
            out[token] = row
    return out


def route_uses_instance_scripts(route_doc: dict[str, Any]) -> bool:
    if not isinstance(route_doc, dict):
        return False
    return any(field in route_doc for field in INSTANCE_SCRIPT_ROUTE_FIELDS)


def orchestration_required(task_doc: dict[str, Any]) -> bool:
    return any(route_uses_instance_scripts(route_doc) for route_doc in task_type_routes(task_doc).values())


def resolve_manifest_path(pack_root: Path) -> Path:
    return (pack_root / INSTANCE_SCRIPT_MANIFEST_REL).resolve()


def load_manifest_doc(pack_root: Path) -> tuple[Path, dict[str, Any] | None]:
    manifest_path = resolve_manifest_path(pack_root)
    if not manifest_path.exists():
        return manifest_path, None
    return manifest_path, load_json(manifest_path)


def manifest_required(task_doc: dict[str, Any], pack_root: Path) -> bool:
    manifest_path = resolve_manifest_path(pack_root)
    return manifest_path.exists() or orchestration_required(task_doc)


def _path_has_parent_escape(token: str) -> bool:
    try:
        return ".." in PurePosixPath(token).parts
    except Exception:
        return True


def validate_receipt_pattern(pattern: str) -> list[str]:
    token = str(pattern or "").strip()
    issues: list[str] = []
    if not token:
        return ["receipt_pattern_missing"]
    if Path(token).is_absolute():
        issues.append("receipt_pattern_absolute_forbidden")
        return issues
    if _path_has_parent_escape(token):
        issues.append("receipt_pattern_parent_escape_forbidden")
    if not token.startswith("runtime/"):
        issues.append("receipt_pattern_not_runtime_relative")
    if token.startswith("scripts/"):
        issues.append("receipt_pattern_under_scripts_forbidden")
    if not any(ch in token for ch in "*?["):
        issues.append("receipt_pattern_glob_missing")
    return issues


def _normalize_manifest_entries(raw_entries: Any) -> tuple[list[dict[str, Any]], list[str]]:
    issues: list[str] = []
    normalized: list[dict[str, Any]] = []
    if isinstance(raw_entries, dict):
        for key, value in raw_entries.items():
            if not isinstance(value, dict):
                issues.append(f"manifest_entry_not_object:{key}")
                continue
            row = dict(value)
            row.setdefault("script_id", str(key).strip())
            if str(row.get("script_id", "")).strip() != str(key).strip():
                issues.append(f"manifest_key_script_id_mismatch:{key}")
            normalized.append(row)
        return normalized, issues
    if isinstance(raw_entries, list):
        for idx, value in enumerate(raw_entries):
            if not isinstance(value, dict):
                issues.append(f"manifest_entry_not_object:index={idx}")
                continue
            normalized.append(dict(value))
        return normalized, issues
    issues.append("manifest_scripts_collection_missing")
    return normalized, issues


def validate_manifest_doc(
    *,
    manifest_doc: dict[str, Any],
    manifest_path: Path,
    pack_root: Path,
    identity_id: str,
) -> dict[str, Any]:
    issues: list[str] = []
    entry_rows: list[dict[str, Any]] = []
    if str(manifest_doc.get("manifest_version", "")).strip() != "v1":
        issues.append("manifest_version_mismatch")
    manifest_identity_id = str(manifest_doc.get("identity_id", "")).strip()
    if manifest_identity_id and manifest_identity_id != identity_id:
        issues.append("manifest_identity_id_mismatch")

    raw_entries = manifest_doc.get("scripts")
    entries, entry_issues = _normalize_manifest_entries(raw_entries)
    issues.extend(entry_issues)
    seen_ids: set[str] = set()
    scripts_root = (pack_root / "scripts").resolve()

    for entry in entries:
        script_id = str(entry.get("script_id", "")).strip()
        row_issues: list[str] = []
        if not script_id:
            row_issues.append("script_id_missing")
        elif script_id in seen_ids:
            row_issues.append("script_id_duplicate")
        elif not TOKEN_RE.match(script_id):
            row_issues.append("script_id_not_machine_token")
        seen_ids.add(script_id)

        entry_relpath = str(entry.get("entry_relpath", "")).strip()
        resolved_path = Path()
        if not entry_relpath:
            row_issues.append("entry_relpath_missing")
        elif Path(entry_relpath).is_absolute():
            row_issues.append("entry_relpath_absolute_forbidden")
        elif _path_has_parent_escape(entry_relpath):
            row_issues.append("entry_relpath_parent_escape_forbidden")
        elif not entry_relpath.startswith("scripts/"):
            row_issues.append("entry_relpath_not_pack_scripts")
        else:
            resolved_path = (pack_root / entry_relpath).resolve()
            if not path_within(resolved_path, scripts_root):
                row_issues.append("entry_relpath_outside_pack_scripts")
            elif not resolved_path.is_file():
                row_issues.append("entry_target_missing")

        script_kind = str(entry.get("script_kind", "")).strip()
        if not script_kind:
            row_issues.append("script_kind_missing")
        elif not TOKEN_RE.match(script_kind):
            row_issues.append("script_kind_not_machine_token")

        default_receipt_pattern = str(entry.get("default_receipt_pattern", "")).strip()
        row_issues.extend(validate_receipt_pattern(default_receipt_pattern))

        entry_rows.append(
            {
                "script_id": script_id,
                "entry_relpath": entry_relpath,
                "resolved_path": str(resolved_path) if str(resolved_path) else "",
                "script_kind": script_kind,
                "default_receipt_pattern": default_receipt_pattern,
                "entry_status": STATUS_FAIL_REQUIRED if row_issues else STATUS_PASS_REQUIRED,
                "stale_reasons": row_issues,
            }
        )
        issues.extend(f"{script_id or '<missing>'}:{reason}" for reason in row_issues)

    manifest_index = {
        str(row.get("script_id", "")).strip(): row
        for row in entry_rows
        if str(row.get("script_id", "")).strip()
    }
    status = STATUS_PASS_REQUIRED if not issues else STATUS_FAIL_REQUIRED
    return {
        "status": status,
        "manifest_path": str(manifest_path),
        "manifest_script_count": len(entry_rows),
        "manifest_entries": entry_rows,
        "manifest_index": manifest_index,
        "stale_reasons": issues,
    }


def _precondition_tokens(value: Any) -> list[str]:
    if isinstance(value, (str, list)):
        return clean_string_list(value)
    return []


def evaluate_script_preconditions(
    *,
    preconditions: Any,
    identity_id: str,
    work_layer: str,
    source_layer: str,
    task_doc: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(preconditions, dict):
        return {
            "status": STATUS_FAIL_REQUIRED,
            "stale_reasons": ["script_preconditions_not_object"],
        }

    issues: list[str] = []
    identity_locks = _precondition_tokens(preconditions.get("identity_lock"))
    if identity_locks and identity_id not in identity_locks:
        issues.append("identity_lock_mismatch")

    work_layers = _precondition_tokens(preconditions.get("work_layer"))
    if work_layers and work_layer not in work_layers:
        issues.append("work_layer_mismatch")

    source_layers = _precondition_tokens(preconditions.get("source_layer"))
    if source_layers and source_layer not in source_layers:
        issues.append("source_layer_mismatch")

    required_contracts = preconditions.get("required_contracts")
    if required_contracts not in (None, ""):
        contract_tokens = clean_string_list(required_contracts)
        if not contract_tokens:
            issues.append("required_contracts_invalid")
        for contract_key in contract_tokens:
            contract_node = task_doc.get(contract_key)
            if not isinstance(contract_node, dict):
                issues.append(f"required_contract_missing:{contract_key}")
                continue
            if not contract_required(contract_node):
                issues.append(f"required_contract_not_required:{contract_key}")

    gate_policies = preconditions.get("gate_policies")
    if gate_policies not in (None, ""):
        if isinstance(gate_policies, dict):
            if not all(str(key).strip() for key in gate_policies.keys()):
                issues.append("gate_policies_key_invalid")
        elif isinstance(gate_policies, list):
            if not all(str(item).strip() for item in gate_policies):
                issues.append("gate_policies_value_invalid")
        else:
            issues.append("gate_policies_invalid")

    return {
        "status": STATUS_PASS_REQUIRED if not issues else STATUS_FAIL_REQUIRED,
        "stale_reasons": issues,
        "evaluated_fields": sorted(key for key in PRECONDITION_FIELDS if key in preconditions),
    }


def build_route_orchestration_matrix(
    *,
    task_doc: dict[str, Any],
    manifest_validation: dict[str, Any],
    identity_id: str,
    work_layer: str,
    source_layer: str,
) -> dict[str, Any]:
    routes = task_type_routes(task_doc)
    manifest_index = dict(manifest_validation.get("manifest_index") or {})
    route_rows: list[dict[str, Any]] = []
    stale_reasons: list[str] = []
    adopted_count = 0
    ready_count = 0

    for route_name, route_doc in routes.items():
        adopted = route_uses_instance_scripts(route_doc)
        row: dict[str, Any] = {
            "route": route_name,
            "adopted": adopted,
            "route_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
            "script_preconditions_status": STATUS_SKIPPED_NOT_REQUIRED,
            "manifest_binding_status": STATUS_SKIPPED_NOT_REQUIRED,
            "route_ready": False,
            "diagnostic_label": "not_required",
            "primary_instance_scripts": [],
            "fallback_instance_scripts": [],
            "resolved_script_ids": [],
            "missing_script_ids": [],
            "script_receipt_pattern": "",
            "stale_reasons": [],
        }
        if not adopted:
            route_rows.append(row)
            continue

        adopted_count += 1
        missing_fields = [field for field in INSTANCE_SCRIPT_ROUTE_FIELDS if field not in route_doc]
        primary_scripts = clean_string_list(route_doc.get("primary_instance_scripts"))
        fallback_scripts = clean_string_list(route_doc.get("fallback_instance_scripts"))
        row["primary_instance_scripts"] = primary_scripts
        row["fallback_instance_scripts"] = fallback_scripts
        route_receipt_pattern = str(route_doc.get("script_receipt_pattern", "")).strip()
        row["script_receipt_pattern"] = route_receipt_pattern

        route_issues: list[str] = []
        if missing_fields:
            route_issues.extend(f"missing_field:{field}" for field in missing_fields)
        if not primary_scripts:
            route_issues.append("primary_instance_scripts_empty")
        receipt_issues = validate_receipt_pattern(route_receipt_pattern)
        route_issues.extend(receipt_issues)

        if route_issues:
            row["route_contract_status"] = STATUS_FAIL_REQUIRED
            row["diagnostic_label"] = "route_contract_missing"
            row["stale_reasons"].extend(route_issues)
            stale_reasons.extend(f"{route_name}:{reason}" for reason in route_issues)
            route_rows.append(row)
            continue

        row["route_contract_status"] = STATUS_PASS_REQUIRED

        required_script_ids = primary_scripts + fallback_scripts
        missing_script_ids = [script_id for script_id in required_script_ids if script_id not in manifest_index]
        resolved_script_ids = [script_id for script_id in required_script_ids if script_id in manifest_index]
        row["resolved_script_ids"] = resolved_script_ids
        row["missing_script_ids"] = missing_script_ids
        if missing_script_ids:
            row["manifest_binding_status"] = STATUS_FAIL_REQUIRED
            row["diagnostic_label"] = "manifest_binding_missing"
            row["stale_reasons"].extend(f"missing_script_id:{script_id}" for script_id in missing_script_ids)
            stale_reasons.extend(f"{route_name}:missing_script_id:{script_id}" for script_id in missing_script_ids)
            route_rows.append(row)
            continue

        row["manifest_binding_status"] = STATUS_PASS_REQUIRED

        precondition_result = evaluate_script_preconditions(
            preconditions=route_doc.get("script_preconditions"),
            identity_id=identity_id,
            work_layer=work_layer,
            source_layer=source_layer,
            task_doc=task_doc,
        )
        row["script_preconditions_status"] = precondition_result["status"]
        row["precondition_evaluated_fields"] = precondition_result.get("evaluated_fields", [])
        if precondition_result["status"] != STATUS_PASS_REQUIRED:
            row["diagnostic_label"] = "script_precondition_blocked"
            row["stale_reasons"].extend(precondition_result.get("stale_reasons", []))
            stale_reasons.extend(
                f"{route_name}:{reason}" for reason in precondition_result.get("stale_reasons", [])
            )
            route_rows.append(row)
            continue

        row["diagnostic_label"] = "ready"
        row["route_ready"] = True
        ready_count += 1
        route_rows.append(row)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    if adopted_count == 0:
        status = STATUS_SKIPPED_NOT_REQUIRED
    return {
        "status": status,
        "route_total_count": len(route_rows),
        "route_adopted_count": adopted_count,
        "route_ready_count": ready_count,
        "route_rows": route_rows,
        "stale_reasons": stale_reasons,
    }
