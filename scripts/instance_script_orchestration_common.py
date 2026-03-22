#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, path_within, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROUTE_SCOPE_ROUTE_SCOPED = "route_scoped"
ROUTE_SCOPE_AGGREGATE = "aggregate"
ROUTE_SELECTION_CARDINALITY_ZERO = "zero_route"
ROUTE_SELECTION_CARDINALITY_SINGLE = "single_route"
ROUTE_SELECTION_CARDINALITY_MULTI = "multi_route"
SEMANTIC_ANCHOR_FIELDS: tuple[str, ...] = (
    "semantic_anchor_ref",
    "semantic_anchor_schema_id",
    "semantic_anchor_source",
    "semantic_anchor_revision",
    "semantic_anchor_digest",
    "semantic_anchor_status",
)
OUTCOME_SENTINEL_FIELDS: tuple[str, ...] = (
    "outcome_sentinel_ref",
    "outcome_sentinel_schema_id",
    "outcome_sentinel_status",
)

INSTANCE_SCRIPT_MANIFEST_REL = Path("scripts/INSTANCE_SCRIPT_MANIFEST.json")
INSTANCE_SCRIPT_RECEIPT_FAMILIES: tuple[str, ...] = (
    "instance_script_admission_receipt",
    "instance_script_execution_receipt",
    "instance_script_emit_receipt",
    "instance_script_recovery_receipt",
)
INSTANCE_SCRIPT_RECEIPT_PROVENANCE_FIELDS: tuple[str, ...] = (
    "route_selected",
    "skills_used",
    "mcp_tools_used",
    "actions_taken",
    "result",
    "artifacts",
)
INSTANCE_SCRIPT_ROUTE_FIELDS: tuple[str, ...] = (
    "primary_instance_scripts",
    "fallback_instance_scripts",
    "script_preconditions",
    "script_receipt_pattern",
)
INSTANCE_SCRIPT_EXECUTION_LANE_ROUTE_FIELDS: tuple[str, ...] = (
    "allowed_execution_lanes",
    "lane_admission_policy",
    "lane_receipt_pattern",
    "lane_block_on_fallback",
)
INSTANCE_SCRIPT_ADMISSION_RECEIPT_FAMILY = "instance_script_admission_receipt"
INSTANCE_SCRIPT_EXECUTION_LANE_RECEIPT_FIELDS: tuple[str, ...] = (
    "route_selected",
    "script_id",
    "lane_id",
    "lane_class",
    "lane_source",
    "lane_endpoint_class",
    "lane_admission_status",
    "fallback_used",
)
PRECONDITION_FIELDS: tuple[str, ...] = (
    "identity_lock",
    "work_layer",
    "source_layer",
    "required_contracts",
    "gate_policies",
)
ALLOWED_LANE_ADMISSION_POLICY_MODES = frozenset(
    {
        "declared_lane_only",
        "declared_lane_with_controlled_fallback",
    }
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


def unique_string_list(value: Any) -> list[str]:
    tokens = clean_string_list(value)
    deduped: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        deduped.append(token)
    return deduped


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_route_scope_projection(
    *,
    route_scope: str,
    route_activation_strategy: str = "",
    route_ready_count: int | None = None,
    route_total_count: int | None = None,
) -> dict[str, Any]:
    route_scope_token = str(route_scope or "").strip() or ROUTE_SCOPE_AGGREGATE
    ready_count = _safe_int(route_ready_count, 0) if route_ready_count is not None else 0
    total_count = _safe_int(route_total_count, 0) if route_total_count is not None else 0
    if route_scope_token == ROUTE_SCOPE_ROUTE_SCOPED:
        cardinality = ROUTE_SELECTION_CARDINALITY_SINGLE
    elif ready_count <= 0:
        cardinality = ROUTE_SELECTION_CARDINALITY_ZERO
    elif ready_count == 1:
        cardinality = ROUTE_SELECTION_CARDINALITY_SINGLE
    else:
        cardinality = ROUTE_SELECTION_CARDINALITY_MULTI
    payload: dict[str, Any] = {
        "route_scope": route_scope_token,
        "route_selection_cardinality": cardinality,
    }
    if str(route_activation_strategy or "").strip():
        payload["route_activation_strategy"] = str(route_activation_strategy).strip()
    if route_ready_count is not None:
        payload["route_ready_count"] = ready_count
    if route_total_count is not None:
        payload["route_total_count"] = total_count
    return payload


def _declared_lane_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    lane_ids: list[str] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        lane_id = str(row.get("lane_id", "")).strip()
        if lane_id:
            lane_ids.append(lane_id)
    return unique_string_list(lane_ids)


def build_declared_dependency_projection(
    *,
    route_name: str = "",
    primary_skills: Any = None,
    fallback_skills: Any = None,
    required_mcp: Any = None,
    primary_instance_scripts: Any = None,
    fallback_instance_scripts: Any = None,
    allowed_execution_lane_ids: Any = None,
    route_scope: str = ROUTE_SCOPE_ROUTE_SCOPED,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "route_scope": str(route_scope or "").strip() or ROUTE_SCOPE_ROUTE_SCOPED,
        "declared_primary_skills": unique_string_list(primary_skills or []),
        "declared_fallback_skills": unique_string_list(fallback_skills or []),
        "declared_required_mcp": unique_string_list(required_mcp or []),
        "declared_primary_instance_scripts": unique_string_list(primary_instance_scripts or []),
        "declared_fallback_instance_scripts": unique_string_list(fallback_instance_scripts or []),
        "declared_allowed_execution_lane_ids": unique_string_list(allowed_execution_lane_ids or []),
    }
    route_token = str(route_name or "").strip()
    if route_token:
        payload["route"] = route_token
    return payload


def build_observed_dependency_projection(
    *,
    route_name: str = "",
    observed_skills: Any = None,
    observed_mcp_tools: Any = None,
    observed_instance_scripts: Any = None,
    observed_execution_lane_ids: Any = None,
    observed_receipt_family: str = "",
    observed_route_ready: bool | None = None,
    route_scope: str = ROUTE_SCOPE_ROUTE_SCOPED,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "route_scope": str(route_scope or "").strip() or ROUTE_SCOPE_ROUTE_SCOPED,
        "observed_skills": unique_string_list(observed_skills or []),
        "observed_mcp_tools": unique_string_list(observed_mcp_tools or []),
        "observed_instance_scripts": unique_string_list(observed_instance_scripts or []),
        "observed_execution_lane_ids": unique_string_list(observed_execution_lane_ids or []),
    }
    route_token = str(route_name or "").strip()
    if route_token:
        payload["route"] = route_token
    if str(observed_receipt_family or "").strip():
        payload["observed_receipt_family"] = str(observed_receipt_family).strip()
    if observed_route_ready is not None:
        payload["observed_route_ready"] = bool(observed_route_ready)
    return payload


def normalize_dependency_gap_reasons(value: Any) -> list[str]:
    if isinstance(value, list):
        return unique_string_list(value)
    return []


def _extract_optional_projection_fields(source: Any, *, fields: tuple[str, ...]) -> dict[str, str]:
    if not isinstance(source, dict):
        return {}
    payload: dict[str, str] = {}
    for field in fields:
        token = str(source.get(field, "")).strip()
        if token:
            payload[field] = token
    return payload


def normalize_optional_projection_fields(
    source: Any,
    *,
    fields: tuple[str, ...],
    family_name: str,
) -> tuple[dict[str, str], list[str]]:
    payload = _extract_optional_projection_fields(source, fields=fields)
    if not payload:
        return {}, []
    missing = [field for field in fields if field not in payload]
    if missing:
        return payload, [f"{family_name}_missing:{field}" for field in missing]
    return payload, []


def compare_optional_projection_fields(
    *,
    declared: dict[str, str],
    observed: dict[str, str],
    fields: tuple[str, ...],
    family_name: str,
) -> list[str]:
    issues: list[str] = []
    if declared and not observed:
        return [f"{family_name}_declared_not_observed"]
    if not declared or not observed:
        return issues
    for field in fields:
        if declared.get(field) != observed.get(field):
            issues.append(f"{family_name}_field_mismatch:{field}")
    return issues


def optional_projection_field_families() -> tuple[tuple[str, tuple[str, ...]], ...]:
    return (
        ("semantic_anchor", SEMANTIC_ANCHOR_FIELDS),
        ("outcome_sentinel", OUTCOME_SENTINEL_FIELDS),
    )


def copy_optional_projection_fields(source: dict[str, Any]) -> dict[str, str]:
    payload: dict[str, str] = {}
    for _, fields in optional_projection_field_families():
        payload.update(_extract_optional_projection_fields(source, fields=fields))
    return payload


def validate_optional_projection_payload(source: Any) -> list[str]:
    issues: list[str] = []
    for family_name, fields in optional_projection_field_families():
        _, family_issues = normalize_optional_projection_fields(
            source,
            fields=fields,
            family_name=family_name,
        )
        issues.extend(family_issues)
    return issues


def promote_uniform_optional_projection(
    route_rows: list[dict[str, Any]],
    *,
    fields: tuple[str, ...],
    family_name: str,
) -> tuple[dict[str, str], int]:
    unique_rows: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    for row in route_rows:
        payload, issues = normalize_optional_projection_fields(
            row,
            fields=fields,
            family_name=family_name,
        )
        if issues or not payload:
            continue
        key = tuple(payload[field] for field in fields)
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(payload)
    if len(unique_rows) == 1:
        return unique_rows[0], len(unique_rows)
    return {}, len(unique_rows)


def summarize_optional_projection_families(
    rows: list[dict[str, Any]],
    *,
    ambiguity_scope: str,
) -> tuple[dict[str, str], list[str]]:
    payload: dict[str, str] = {}
    reasons: list[str] = []
    for family_name, fields in optional_projection_field_families():
        promoted_payload, unique_count = promote_uniform_optional_projection(
            rows,
            fields=fields,
            family_name=family_name,
        )
        if promoted_payload:
            payload.update(promoted_payload)
            continue
        if unique_count > 1:
            reasons.append(f"{family_name}_projection_{ambiguity_scope}_ambiguous")
    return payload, reasons


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


def route_uses_execution_lanes(route_doc: dict[str, Any]) -> bool:
    if not isinstance(route_doc, dict):
        return False
    return any(field in route_doc for field in INSTANCE_SCRIPT_EXECUTION_LANE_ROUTE_FIELDS)


def orchestration_required(task_doc: dict[str, Any]) -> bool:
    return any(route_uses_instance_scripts(route_doc) for route_doc in task_type_routes(task_doc).values())


def execution_lane_required(task_doc: dict[str, Any]) -> bool:
    return any(route_uses_execution_lanes(route_doc) for route_doc in task_type_routes(task_doc).values())


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


def route_evidence_schema_fields(task_doc: dict[str, Any]) -> list[str]:
    contract = task_doc.get("capability_orchestration_contract")
    declared = clean_string_list(contract.get("evidence_schema_fields")) if isinstance(contract, dict) else []
    merged: list[str] = []
    for token in [*INSTANCE_SCRIPT_RECEIPT_PROVENANCE_FIELDS, *declared]:
        if token and token not in merged:
            merged.append(token)
    return merged


def build_aggregate_dependency_projection(
    *,
    tool_routes: list[dict[str, Any]],
    route_activation_matrix: list[dict[str, Any]],
    active_skills: list[str],
    mcp_tools_used: list[str],
    route_activation_strategy: str,
    route_ready_count: int,
) -> dict[str, Any]:
    route_index = {
        str(row.get("route", "")).strip(): row
        for row in route_activation_matrix
        if isinstance(row, dict) and str(row.get("route", "")).strip()
    }
    declared_route_rows: list[dict[str, Any]] = []
    observed_route_rows: list[dict[str, Any]] = []
    dependency_gap_reasons: list[str] = []

    aggregate_declared_primary_skills: list[str] = []
    aggregate_declared_fallback_skills: list[str] = []
    aggregate_declared_required_mcp: list[str] = []
    aggregate_declared_primary_instance_scripts: list[str] = []
    aggregate_declared_fallback_instance_scripts: list[str] = []
    aggregate_declared_allowed_execution_lane_ids: list[str] = []
    aggregate_observed_instance_scripts: list[str] = []
    aggregate_observed_execution_lane_ids: list[str] = []
    observed_ready_routes: list[str] = []

    active_skill_set = set(unique_string_list(active_skills))
    active_mcp_set = set(unique_string_list(mcp_tools_used))

    for route_row in tool_routes:
        if not isinstance(route_row, dict):
            continue
        route_name = str(route_row.get("route", "")).strip()
        if not route_name:
            continue
        declared_primary_skills = unique_string_list(route_row.get("primary_skills") or [])
        declared_fallback_skills = unique_string_list(route_row.get("fallback_skills") or [])
        declared_required_mcp = unique_string_list(route_row.get("required_mcp") or [])
        declared_primary_instance_scripts = unique_string_list(route_row.get("primary_instance_scripts") or [])
        declared_fallback_instance_scripts = unique_string_list(route_row.get("fallback_instance_scripts") or [])
        declared_allowed_execution_lane_ids = _declared_lane_ids(route_row.get("allowed_execution_lanes") or [])
        declared_projection = build_declared_dependency_projection(
            route_name=route_name,
            primary_skills=declared_primary_skills,
            fallback_skills=declared_fallback_skills,
            required_mcp=declared_required_mcp,
            primary_instance_scripts=declared_primary_instance_scripts,
            fallback_instance_scripts=declared_fallback_instance_scripts,
            allowed_execution_lane_ids=declared_allowed_execution_lane_ids,
            route_scope=ROUTE_SCOPE_AGGREGATE,
        )
        declared_semantic_anchor, declared_semantic_anchor_issues = normalize_optional_projection_fields(
            route_row,
            fields=SEMANTIC_ANCHOR_FIELDS,
            family_name="semantic_anchor_declared",
        )
        declared_outcome_sentinel, declared_outcome_sentinel_issues = normalize_optional_projection_fields(
            route_row,
            fields=OUTCOME_SENTINEL_FIELDS,
            family_name="outcome_sentinel_declared",
        )
        declared_projection.update(declared_semantic_anchor)
        declared_projection.update(declared_outcome_sentinel)
        declared_route_rows.append(declared_projection)
        aggregate_declared_primary_skills.extend(declared_primary_skills)
        aggregate_declared_fallback_skills.extend(declared_fallback_skills)
        aggregate_declared_required_mcp.extend(declared_required_mcp)
        aggregate_declared_primary_instance_scripts.extend(declared_primary_instance_scripts)
        aggregate_declared_fallback_instance_scripts.extend(declared_fallback_instance_scripts)
        aggregate_declared_allowed_execution_lane_ids.extend(declared_allowed_execution_lane_ids)

        activation_row = route_index.get(route_name, {})
        route_missing_skills = unique_string_list(activation_row.get("missing_skills") or [])
        route_missing_mcp = unique_string_list(activation_row.get("missing_mcp") or [])
        route_missing_script_ids = unique_string_list(activation_row.get("missing_script_ids") or [])
        route_observed_execution_lane_ids = unique_string_list(
            [
                str(row.get("observed_lane_id", "")).strip()
                for row in (activation_row.get("execution_lane_rows") or [])
                if isinstance(row, dict)
                and str(row.get("lane_receipt_validation_status", "")).strip() == STATUS_PASS_REQUIRED
                and str(row.get("observed_lane_id", "")).strip()
            ]
        )
        route_observed_instance_scripts = unique_string_list(
            activation_row.get("resolved_script_ids") or []
        )
        observed_projection = build_observed_dependency_projection(
            route_name=route_name,
            observed_skills=[token for token in declared_primary_skills + declared_fallback_skills if token in active_skill_set],
            observed_mcp_tools=[token for token in declared_required_mcp if token in active_mcp_set],
            observed_instance_scripts=route_observed_instance_scripts,
            observed_execution_lane_ids=route_observed_execution_lane_ids,
            observed_route_ready=bool(activation_row.get("ready")),
            route_scope=ROUTE_SCOPE_AGGREGATE,
        )
        observed_semantic_anchor, observed_semantic_anchor_issues = normalize_optional_projection_fields(
            activation_row,
            fields=SEMANTIC_ANCHOR_FIELDS,
            family_name="semantic_anchor",
        )
        observed_outcome_sentinel, observed_outcome_sentinel_issues = normalize_optional_projection_fields(
            activation_row,
            fields=OUTCOME_SENTINEL_FIELDS,
            family_name="outcome_sentinel",
        )
        observed_projection.update(observed_semantic_anchor)
        observed_projection.update(observed_outcome_sentinel)
        observed_route_rows.append(observed_projection)
        aggregate_observed_instance_scripts.extend(route_observed_instance_scripts)
        aggregate_observed_execution_lane_ids.extend(route_observed_execution_lane_ids)
        if bool(activation_row.get("ready")):
            observed_ready_routes.append(route_name)

        dependency_gap_reasons.extend(
            f"{route_name}:{reason}" for reason in declared_semantic_anchor_issues
        )
        dependency_gap_reasons.extend(
            f"{route_name}:{reason}" for reason in observed_semantic_anchor_issues
        )
        dependency_gap_reasons.extend(
            f"{route_name}:{reason}"
            for reason in compare_optional_projection_fields(
                declared=declared_semantic_anchor,
                observed=observed_semantic_anchor,
                fields=SEMANTIC_ANCHOR_FIELDS,
                family_name="semantic_anchor",
            )
        )
        dependency_gap_reasons.extend(
            f"{route_name}:{reason}" for reason in declared_outcome_sentinel_issues
        )
        dependency_gap_reasons.extend(
            f"{route_name}:{reason}" for reason in observed_outcome_sentinel_issues
        )
        dependency_gap_reasons.extend(
            f"{route_name}:{reason}"
            for reason in compare_optional_projection_fields(
                declared=declared_outcome_sentinel,
                observed=observed_outcome_sentinel,
                fields=OUTCOME_SENTINEL_FIELDS,
                family_name="outcome_sentinel",
            )
        )
        dependency_gap_reasons.extend(
            f"{route_name}:{reason}"
            for reason in unique_string_list(activation_row.get("optional_projection_reasons") or [])
        )

        dependency_gap_reasons.extend(
            f"{route_name}:declared_skill_unavailable:{token}" for token in route_missing_skills
        )
        dependency_gap_reasons.extend(
            f"{route_name}:declared_required_mcp_unavailable:{token}" for token in route_missing_mcp
        )
        dependency_gap_reasons.extend(
            f"{route_name}:declared_instance_script_unresolved:{token}" for token in route_missing_script_ids
        )
        if bool(activation_row.get("uses_execution_lanes")) and str(
            activation_row.get("execution_lane_contract_status", "")
        ).strip() == STATUS_FAIL_REQUIRED:
            dependency_gap_reasons.append(f"{route_name}:declared_execution_lane_contract_not_ready")
        if bool(activation_row.get("uses_execution_lanes")) and str(
            activation_row.get("execution_lane_receipt_status", "")
        ).strip() == STATUS_FAIL_REQUIRED:
            dependency_gap_reasons.append(f"{route_name}:declared_execution_lane_receipt_not_ready")

    declared_dependency_projection = {
        "route_scope": ROUTE_SCOPE_AGGREGATE,
        "declared_route_count": len(declared_route_rows),
        "declared_route_rows": declared_route_rows,
        "declared_primary_skills": unique_string_list(aggregate_declared_primary_skills),
        "declared_fallback_skills": unique_string_list(aggregate_declared_fallback_skills),
        "declared_required_mcp": unique_string_list(aggregate_declared_required_mcp),
        "declared_primary_instance_scripts": unique_string_list(aggregate_declared_primary_instance_scripts),
        "declared_fallback_instance_scripts": unique_string_list(aggregate_declared_fallback_instance_scripts),
        "declared_allowed_execution_lane_ids": unique_string_list(aggregate_declared_allowed_execution_lane_ids),
    }
    observed_dependency_projection = {
        "route_scope": ROUTE_SCOPE_AGGREGATE,
        "observed_route_count": len(observed_route_rows),
        "observed_route_rows": observed_route_rows,
        "observed_skills": unique_string_list(active_skills),
        "observed_mcp_tools": unique_string_list(mcp_tools_used),
        "observed_instance_scripts": unique_string_list(aggregate_observed_instance_scripts),
        "observed_execution_lane_ids": unique_string_list(aggregate_observed_execution_lane_ids),
        "observed_ready_routes": unique_string_list(observed_ready_routes),
    }
    payload = build_route_scope_projection(
        route_scope=ROUTE_SCOPE_AGGREGATE,
        route_activation_strategy=route_activation_strategy,
        route_ready_count=route_ready_count,
        route_total_count=len(route_activation_matrix),
    )
    payload["declared_dependency_projection"] = declared_dependency_projection
    payload["observed_dependency_projection"] = observed_dependency_projection
    promoted_optional_projection, optional_projection_reasons = summarize_optional_projection_families(
        observed_route_rows,
        ambiguity_scope="route_aggregation",
    )
    payload.update(promoted_optional_projection)
    dependency_gap_reasons.extend(optional_projection_reasons)

    payload["dependency_gap_reasons"] = normalize_dependency_gap_reasons(dependency_gap_reasons)
    return payload


def expected_receipt_family(*, receipt_pattern: str, script_kind: str) -> str:
    pattern_token = str(receipt_pattern or "").strip().lower()
    kind_token = str(script_kind or "").strip().lower()
    if "instance-script-emit" in pattern_token or kind_token in {"emit", "emitter"} or "emitter" in kind_token:
        return "instance_script_emit_receipt"
    if "instance-script-recovery" in pattern_token or "recovery" in kind_token:
        return "instance_script_recovery_receipt"
    if "instance-script-admission" in pattern_token or "admission" in kind_token or kind_token.startswith("entry"):
        return "instance_script_admission_receipt"
    return "instance_script_execution_receipt"


def _resolve_receipt_paths(
    *,
    pack_root: Path,
    receipt_pattern: str,
    route_name: str,
    script_id: str,
    receipt_override: str = "",
) -> tuple[list[Path], list[str]]:
    override = str(receipt_override or "").strip()
    if override:
        return [Path(override).expanduser().resolve()], []
    token = str(receipt_pattern or "").strip()
    if not token:
        return [], ["receipt_pattern_missing"]
    try:
        hits = [path.resolve() for path in pack_root.glob(token) if path.is_file()]
    except Exception as exc:
        return [], [f"receipt_glob_failed:{type(exc).__name__}:{exc}"]
    route_token = str(route_name or "").strip()
    script_token = str(script_id or "").strip()
    filtered = [
        path
        for path in hits
        if route_token in path.name and script_token in path.name
    ]
    return sorted(filtered, key=lambda item: item.stat().st_mtime, reverse=True), []


def _validate_string_list_field(value: Any, *, field_name: str) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    if not isinstance(value, list):
        return [], [f"{field_name}_not_list"]
    tokens = clean_string_list(value)
    if len(tokens) != len(value):
        issues.append(f"{field_name}_contains_blank_or_non_string")
    return tokens, issues


def _validate_machine_token_field(value: Any, *, field_name: str) -> tuple[str, list[str]]:
    token = str(value or "").strip()
    if not token:
        return "", [f"{field_name}_missing"]
    if not TOKEN_RE.match(token):
        return token, [f"{field_name}_not_machine_token:{token}"]
    return token, []


def _normalize_allowed_execution_lanes(value: Any) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(value, list):
        return [], ["allowed_execution_lanes_not_list"]
    lanes: list[dict[str, Any]] = []
    issues: list[str] = []
    seen_lane_ids: set[str] = set()
    for idx, row in enumerate(value):
        if not isinstance(row, dict):
            issues.append(f"allowed_execution_lanes_row_not_object:index={idx}")
            continue
        lane_row_issues: list[str] = []
        lane_id, lane_id_issues = _validate_machine_token_field(row.get("lane_id"), field_name="lane_id")
        lane_row_issues.extend(lane_id_issues)
        lane_class, lane_class_issues = _validate_machine_token_field(
            row.get("lane_class"),
            field_name="lane_class",
        )
        lane_row_issues.extend(lane_class_issues)
        lane_source, lane_source_issues = _validate_machine_token_field(
            row.get("lane_source"),
            field_name="lane_source",
        )
        lane_row_issues.extend(lane_source_issues)
        endpoint_class, endpoint_class_issues = _validate_machine_token_field(
            row.get("endpoint_class"),
            field_name="endpoint_class",
        )
        lane_row_issues.extend(endpoint_class_issues)
        if lane_id:
            if lane_id in seen_lane_ids:
                lane_row_issues.append(f"lane_id_duplicate:{lane_id}")
            seen_lane_ids.add(lane_id)
        lanes.append(
            {
                "lane_id": lane_id,
                "lane_class": lane_class,
                "lane_source": lane_source,
                "endpoint_class": endpoint_class,
                "lane_status": STATUS_FAIL_REQUIRED if lane_row_issues else STATUS_PASS_REQUIRED,
                "stale_reasons": lane_row_issues,
            }
        )
        issues.extend(f"allowed_execution_lanes[{idx}]:{reason}" for reason in lane_row_issues)
    if not lanes:
        issues.append("allowed_execution_lanes_empty")
    return lanes, issues


def _normalize_lane_admission_policy(value: Any) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(value, dict):
        return {}, ["lane_admission_policy_not_object"]
    issues: list[str] = []
    mode = str(value.get("mode", "")).strip()
    if mode not in ALLOWED_LANE_ADMISSION_POLICY_MODES:
        issues.append(f"lane_admission_policy_mode_invalid:{mode or 'missing'}")
    require_pass_status = value.get("require_pass_status")
    if not isinstance(require_pass_status, bool):
        issues.append("lane_admission_policy_require_pass_status_not_bool")
    return {
        "mode": mode,
        "require_pass_status": bool(require_pass_status) if isinstance(require_pass_status, bool) else False,
    }, issues


def validate_route_execution_lane_contract(route_doc: dict[str, Any]) -> dict[str, Any]:
    if not route_uses_execution_lanes(route_doc):
        return {
            "status": STATUS_SKIPPED_NOT_REQUIRED,
            "lane_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
            "allowed_execution_lanes": [],
            "lane_admission_policy": {},
            "lane_receipt_pattern": "",
            "lane_block_on_fallback": False,
            "stale_reasons": [],
        }

    issues: list[str] = []
    missing_fields = [
        field for field in INSTANCE_SCRIPT_EXECUTION_LANE_ROUTE_FIELDS if field not in route_doc
    ]
    issues.extend(f"missing_field:{field}" for field in missing_fields)

    allowed_execution_lanes, lane_issues = _normalize_allowed_execution_lanes(
        route_doc.get("allowed_execution_lanes")
    )
    issues.extend(lane_issues)

    lane_admission_policy, policy_issues = _normalize_lane_admission_policy(
        route_doc.get("lane_admission_policy")
    )
    issues.extend(policy_issues)

    lane_receipt_pattern = str(route_doc.get("lane_receipt_pattern", "")).strip()
    issues.extend(validate_receipt_pattern(lane_receipt_pattern))

    lane_block_on_fallback = route_doc.get("lane_block_on_fallback")
    if not isinstance(lane_block_on_fallback, bool):
        issues.append("lane_block_on_fallback_not_bool")

    status = STATUS_PASS_REQUIRED if not issues else STATUS_FAIL_REQUIRED
    return {
        "status": status,
        "lane_contract_status": status,
        "allowed_execution_lanes": allowed_execution_lanes,
        "lane_admission_policy": lane_admission_policy,
        "lane_receipt_pattern": lane_receipt_pattern,
        "lane_block_on_fallback": bool(lane_block_on_fallback) if isinstance(lane_block_on_fallback, bool) else False,
        "stale_reasons": issues,
    }


def validate_route_script_receipt_doc(
    *,
    receipt_doc: dict[str, Any],
    receipt_path: Path,
    pack_root: Path,
    identity_id: str,
    route_name: str,
    script_id: str,
    route_doc: dict[str, Any],
    manifest_entry: dict[str, Any],
    expected_pattern: str,
    allow_external_receipt: bool = False,
) -> dict[str, Any]:
    issues: list[str] = []
    route_scope_projection = build_route_scope_projection(
        route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
        route_ready_count=1,
        route_total_count=1,
    )
    declared_dependency_projection = build_declared_dependency_projection(
        route_name=route_name,
        primary_skills=route_doc.get("primary_skills"),
        fallback_skills=route_doc.get("fallback_skills"),
        required_mcp=route_doc.get("required_mcp"),
        primary_instance_scripts=route_doc.get("primary_instance_scripts"),
        fallback_instance_scripts=route_doc.get("fallback_instance_scripts"),
        allowed_execution_lane_ids=_declared_lane_ids(route_doc.get("allowed_execution_lanes") or []),
        route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
    )
    if str(receipt_doc.get("schema_version", "")).strip() != "v1":
        issues.append("receipt_schema_version_invalid")
    receipt_family = str(receipt_doc.get("receipt_family", "")).strip()
    if receipt_family not in INSTANCE_SCRIPT_RECEIPT_FAMILIES:
        issues.append(f"receipt_family_invalid:{receipt_family or 'missing'}")
    expected_family = expected_receipt_family(
        receipt_pattern=expected_pattern,
        script_kind=str(manifest_entry.get("script_kind", "")).strip(),
    )
    if receipt_family and receipt_family in INSTANCE_SCRIPT_RECEIPT_FAMILIES and receipt_family != expected_family:
        issues.append(f"receipt_family_mismatch:{expected_family}!={receipt_family}")
    if str(receipt_doc.get("identity_id", "")).strip() != str(identity_id or "").strip():
        issues.append("receipt_identity_id_mismatch")
    if str(receipt_doc.get("route_selected", "")).strip() != str(route_name or "").strip():
        issues.append("receipt_route_selected_mismatch")
    if str(receipt_doc.get("script_id", "")).strip() != str(script_id or "").strip():
        issues.append("receipt_script_id_mismatch")
    manifest_script_kind = str(manifest_entry.get("script_kind", "")).strip()
    if str(receipt_doc.get("script_kind", "")).strip() != manifest_script_kind:
        issues.append("receipt_script_kind_mismatch")
    if str(receipt_doc.get("script_receipt_pattern", "")).strip() != str(expected_pattern or "").strip():
        issues.append("receipt_pattern_mismatch")

    if not allow_external_receipt:
        runtime_root = (pack_root / "runtime").resolve()
        if not path_within(receipt_path, runtime_root):
            issues.append("receipt_path_outside_runtime_root")

    required_skills = {
        *clean_string_list(route_doc.get("primary_skills")),
        *clean_string_list(route_doc.get("fallback_skills")),
    }
    required_mcp = set(clean_string_list(route_doc.get("required_mcp")))

    skills_used, skill_issues = _validate_string_list_field(receipt_doc.get("skills_used"), field_name="skills_used")
    issues.extend(skill_issues)
    if required_skills and not skills_used:
        issues.append("skills_used_empty_for_declared_route")
    undeclared_skills = [token for token in skills_used if token not in required_skills]
    if undeclared_skills:
        issues.append("skills_used_undeclared:" + ",".join(sorted(set(undeclared_skills))))

    mcp_tools_used, mcp_issues = _validate_string_list_field(
        receipt_doc.get("mcp_tools_used"),
        field_name="mcp_tools_used",
    )
    issues.extend(mcp_issues)
    if required_mcp and not mcp_tools_used:
        issues.append("mcp_tools_used_empty_for_declared_route")
    undeclared_mcp = [token for token in mcp_tools_used if token not in required_mcp]
    if undeclared_mcp:
        issues.append("mcp_tools_used_undeclared:" + ",".join(sorted(set(undeclared_mcp))))

    actions_taken, action_issues = _validate_string_list_field(
        receipt_doc.get("actions_taken"),
        field_name="actions_taken",
    )
    issues.extend(action_issues)
    if not actions_taken:
        issues.append("actions_taken_empty")

    result_token = str(receipt_doc.get("result", "")).strip()
    if not result_token:
        issues.append("result_missing")
    elif result_token != STATUS_PASS_REQUIRED:
        issues.append(f"result_not_pass_required:{result_token}")

    artifacts = receipt_doc.get("artifacts")
    if isinstance(artifacts, dict):
        if not artifacts:
            issues.append("artifacts_empty")
    elif isinstance(artifacts, list):
        if not clean_string_list(artifacts):
            issues.append("artifacts_empty")
    else:
        issues.append("artifacts_not_machine_visible")

    missing_minimum_fields = [
        field
        for field in INSTANCE_SCRIPT_RECEIPT_PROVENANCE_FIELDS
        if field not in receipt_doc
    ]
    if missing_minimum_fields:
        issues.append("missing_provenance_fields:" + ",".join(sorted(set(missing_minimum_fields))))

    observed_dependency_projection = build_observed_dependency_projection(
        route_name=route_name,
        observed_skills=skills_used,
        observed_mcp_tools=mcp_tools_used,
        observed_instance_scripts=[script_id],
        observed_receipt_family=receipt_family,
        observed_route_ready=not issues,
        route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
    )
    dependency_gap_reasons: list[str] = []
    if required_skills and not skills_used:
        dependency_gap_reasons.append("declared_skills_not_observed")
    dependency_gap_reasons.extend(
        f"undeclared_observed_skill:{token}" for token in sorted(set(undeclared_skills))
    )
    if required_mcp and not mcp_tools_used:
        dependency_gap_reasons.append("declared_required_mcp_not_observed")
    dependency_gap_reasons.extend(
        f"undeclared_observed_mcp_tool:{token}" for token in sorted(set(undeclared_mcp))
    )

    declared_semantic_anchor, declared_semantic_anchor_issues = normalize_optional_projection_fields(
        route_doc,
        fields=SEMANTIC_ANCHOR_FIELDS,
        family_name="semantic_anchor_declared",
    )
    observed_semantic_anchor, observed_semantic_anchor_issues = normalize_optional_projection_fields(
        receipt_doc,
        fields=SEMANTIC_ANCHOR_FIELDS,
        family_name="semantic_anchor",
    )
    issues.extend(declared_semantic_anchor_issues)
    issues.extend(observed_semantic_anchor_issues)
    dependency_gap_reasons.extend(
        compare_optional_projection_fields(
            declared=declared_semantic_anchor,
            observed=observed_semantic_anchor,
            fields=SEMANTIC_ANCHOR_FIELDS,
            family_name="semantic_anchor",
        )
    )

    declared_outcome_sentinel, declared_outcome_sentinel_issues = normalize_optional_projection_fields(
        route_doc,
        fields=OUTCOME_SENTINEL_FIELDS,
        family_name="outcome_sentinel_declared",
    )
    observed_outcome_sentinel, observed_outcome_sentinel_issues = normalize_optional_projection_fields(
        receipt_doc,
        fields=OUTCOME_SENTINEL_FIELDS,
        family_name="outcome_sentinel",
    )
    issues.extend(declared_outcome_sentinel_issues)
    issues.extend(observed_outcome_sentinel_issues)
    dependency_gap_reasons.extend(
        compare_optional_projection_fields(
            declared=declared_outcome_sentinel,
            observed=observed_outcome_sentinel,
            fields=OUTCOME_SENTINEL_FIELDS,
            family_name="outcome_sentinel",
        )
    )
    payload = {
        "status": STATUS_PASS_REQUIRED if not issues else STATUS_FAIL_REQUIRED,
        "receipt_family": receipt_family,
        "expected_receipt_family": expected_family,
        "stale_reasons": issues,
        **route_scope_projection,
        "declared_dependency_projection": declared_dependency_projection,
        "observed_dependency_projection": observed_dependency_projection,
        "dependency_gap_reasons": normalize_dependency_gap_reasons(dependency_gap_reasons),
    }
    payload.update(observed_semantic_anchor)
    payload.update(observed_outcome_sentinel)
    return payload


def validate_route_execution_lane_receipt_doc(
    *,
    receipt_doc: dict[str, Any],
    receipt_path: Path,
    pack_root: Path,
    identity_id: str,
    route_name: str,
    script_id: str,
    lane_contract: dict[str, Any],
    allow_external_receipt: bool = False,
) -> dict[str, Any]:
    issues: list[str] = []
    if str(receipt_doc.get("schema_version", "")).strip() != "v1":
        issues.append("lane_receipt_schema_version_invalid")
    receipt_family = str(receipt_doc.get("receipt_family", "")).strip()
    if receipt_family != INSTANCE_SCRIPT_ADMISSION_RECEIPT_FAMILY:
        issues.append(
            "lane_receipt_family_invalid:"
            f"{receipt_family or 'missing'}!={INSTANCE_SCRIPT_ADMISSION_RECEIPT_FAMILY}"
        )
    if str(receipt_doc.get("identity_id", "")).strip() != str(identity_id or "").strip():
        issues.append("lane_receipt_identity_id_mismatch")
    if str(receipt_doc.get("route_selected", "")).strip() != str(route_name or "").strip():
        issues.append("lane_receipt_route_selected_mismatch")
    if str(receipt_doc.get("script_id", "")).strip() != str(script_id or "").strip():
        issues.append("lane_receipt_script_id_mismatch")

    if not allow_external_receipt:
        runtime_root = (pack_root / "runtime").resolve()
        if not path_within(receipt_path, runtime_root):
            issues.append("lane_receipt_path_outside_runtime_root")

    lane_id, lane_id_issues = _validate_machine_token_field(receipt_doc.get("lane_id"), field_name="lane_id")
    issues.extend("lane_receipt_" + reason for reason in lane_id_issues)
    lane_class, lane_class_issues = _validate_machine_token_field(
        receipt_doc.get("lane_class"),
        field_name="lane_class",
    )
    issues.extend("lane_receipt_" + reason for reason in lane_class_issues)
    lane_source, lane_source_issues = _validate_machine_token_field(
        receipt_doc.get("lane_source"),
        field_name="lane_source",
    )
    issues.extend("lane_receipt_" + reason for reason in lane_source_issues)
    lane_endpoint_class, lane_endpoint_class_issues = _validate_machine_token_field(
        receipt_doc.get("lane_endpoint_class"),
        field_name="lane_endpoint_class",
    )
    issues.extend("lane_receipt_" + reason for reason in lane_endpoint_class_issues)

    lane_admission_status = str(receipt_doc.get("lane_admission_status", "")).strip()
    if not lane_admission_status:
        issues.append("lane_receipt_lane_admission_status_missing")

    fallback_used = receipt_doc.get("fallback_used")
    if not isinstance(fallback_used, bool):
        issues.append("lane_receipt_fallback_used_not_bool")

    declared_lanes = {
        str(row.get("lane_id", "")).strip(): row
        for row in (lane_contract.get("allowed_execution_lanes") or [])
        if str(row.get("lane_id", "")).strip()
    }
    declared_lane = declared_lanes.get(lane_id) if lane_id else None
    if lane_id and declared_lane is None:
        issues.append(f"lane_receipt_lane_id_undeclared:{lane_id}")
    elif declared_lane is not None:
        if lane_class and lane_class != str(declared_lane.get("lane_class", "")).strip():
            issues.append("lane_receipt_lane_class_mismatch")
        if lane_source and lane_source != str(declared_lane.get("lane_source", "")).strip():
            issues.append("lane_receipt_lane_source_mismatch")
        if lane_endpoint_class and lane_endpoint_class != str(declared_lane.get("endpoint_class", "")).strip():
            issues.append("lane_receipt_lane_endpoint_class_mismatch")

    lane_policy = lane_contract.get("lane_admission_policy") or {}
    if (
        isinstance(lane_policy, dict)
        and bool(lane_policy.get("require_pass_status"))
        and lane_admission_status != STATUS_PASS_REQUIRED
    ):
        issues.append(f"lane_receipt_lane_admission_status_not_pass_required:{lane_admission_status}")

    if lane_contract.get("lane_block_on_fallback") is True and fallback_used is True:
        issues.append("lane_receipt_fallback_blocked")

    missing_minimum_fields = [
        field for field in INSTANCE_SCRIPT_EXECUTION_LANE_RECEIPT_FIELDS if field not in receipt_doc
    ]
    if missing_minimum_fields:
        issues.append("lane_receipt_missing_fields:" + ",".join(sorted(set(missing_minimum_fields))))

    return {
        "status": STATUS_PASS_REQUIRED if not issues else STATUS_FAIL_REQUIRED,
        "receipt_family": receipt_family,
        "lane_id": lane_id,
        "lane_class": lane_class,
        "lane_source": lane_source,
        "lane_endpoint_class": lane_endpoint_class,
        "lane_admission_status": lane_admission_status,
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


def build_route_receipt_join_matrix(
    *,
    pack_root: Path,
    task_doc: dict[str, Any],
    manifest_validation: dict[str, Any],
    route_validation: dict[str, Any],
    identity_id: str,
    require_observed: bool = False,
    receipt_override: str = "",
    target_route: str = "",
    target_script_id: str = "",
) -> dict[str, Any]:
    manifest_index = dict(manifest_validation.get("manifest_index") or {})
    routes = task_type_routes(task_doc)
    target_route_token = str(target_route or "").strip()
    target_script_token = str(target_script_id or "").strip()
    route_rows: list[dict[str, Any]] = []
    blocking_reasons: list[str] = []
    observed_count = 0
    checked_count = 0

    for route_row in route_validation.get("route_rows") or []:
        if not isinstance(route_row, dict):
            continue
        route_name = str(route_row.get("route", "")).strip()
        if not route_name or not bool(route_row.get("adopted")):
            continue
        if target_route_token and route_name != target_route_token:
            continue
        route_doc = routes.get(route_name) or {}
        if route_row.get("route_ready") is not True:
            row_copy = dict(route_row)
            row_copy["receipt_validation_status"] = STATUS_SKIPPED_NOT_REQUIRED
            row_copy["diagnostic_label"] = "orchestration_not_ready"
            row_copy["receipt_observed_count"] = 0
            row_copy.update(
                build_route_scope_projection(
                    route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
                    route_ready_count=1,
                    route_total_count=1,
                )
            )
            row_copy["declared_dependency_projection"] = build_declared_dependency_projection(
                route_name=route_name,
                primary_skills=route_doc.get("primary_skills"),
                fallback_skills=route_doc.get("fallback_skills"),
                required_mcp=route_doc.get("required_mcp"),
                primary_instance_scripts=route_doc.get("primary_instance_scripts"),
                fallback_instance_scripts=route_doc.get("fallback_instance_scripts"),
                allowed_execution_lane_ids=_declared_lane_ids(route_doc.get("allowed_execution_lanes") or []),
                route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
            )
            row_copy["observed_dependency_projection"] = build_observed_dependency_projection(
                route_name=route_name,
                route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
            )
            row_copy["dependency_gap_reasons"] = ["route_orchestration_not_ready"]
            route_rows.append(row_copy)
            continue
        route_scope_projection = build_route_scope_projection(
            route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
            route_ready_count=1,
            route_total_count=1,
        )
        declared_dependency_projection = build_declared_dependency_projection(
            route_name=route_name,
            primary_skills=route_doc.get("primary_skills"),
            fallback_skills=route_doc.get("fallback_skills"),
            required_mcp=route_doc.get("required_mcp"),
            primary_instance_scripts=route_doc.get("primary_instance_scripts"),
            fallback_instance_scripts=route_doc.get("fallback_instance_scripts"),
            allowed_execution_lane_ids=_declared_lane_ids(route_doc.get("allowed_execution_lanes") or []),
            route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
        )
        resolved_script_ids = [
            str(token).strip()
            for token in (route_row.get("resolved_script_ids") or [])
            if str(token).strip()
        ]
        for script_id in resolved_script_ids:
            if target_script_token and script_id != target_script_token:
                continue
            checked_count += 1
            manifest_entry = dict(manifest_index.get(script_id) or {})
            receipt_pattern = str(route_doc.get("script_receipt_pattern", "")).strip() or str(
                manifest_entry.get("default_receipt_pattern", "")
            ).strip()
            row: dict[str, Any] = {
                "route": route_name,
                "script_id": script_id,
                "script_kind": str(manifest_entry.get("script_kind", "")).strip(),
                "receipt_pattern": receipt_pattern,
                "receipt_validation_status": STATUS_SKIPPED_NOT_REQUIRED,
                "diagnostic_label": "receipt_not_observed_yet",
                "receipt_observed_count": 0,
                "latest_receipt_path": "",
                "required_provenance_fields": route_evidence_schema_fields(task_doc),
                "stale_reasons": [],
                **route_scope_projection,
                "declared_dependency_projection": declared_dependency_projection,
                "observed_dependency_projection": build_observed_dependency_projection(
                    route_name=route_name,
                    observed_instance_scripts=[script_id],
                    route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
                ),
                "dependency_gap_reasons": [],
            }
            receipt_paths, path_issues = _resolve_receipt_paths(
                pack_root=pack_root,
                receipt_pattern=receipt_pattern,
                route_name=route_name,
                script_id=script_id,
                receipt_override=receipt_override,
            )
            if path_issues:
                row["receipt_validation_status"] = STATUS_FAIL_REQUIRED
                row["diagnostic_label"] = "receipt_glob_failed"
                row["stale_reasons"] = list(path_issues)
                blocking_reasons.extend(f"{route_name}:{script_id}:{reason}" for reason in path_issues)
                route_rows.append(row)
                continue
            row["receipt_observed_count"] = len(receipt_paths)
            if not receipt_paths:
                if require_observed:
                    row["receipt_validation_status"] = STATUS_FAIL_REQUIRED
                    row["diagnostic_label"] = "receipt_missing"
                    row["stale_reasons"] = ["receipt_not_observed"]
                    row["dependency_gap_reasons"] = ["route_receipt_not_observed"]
                    blocking_reasons.append(f"{route_name}:{script_id}:receipt_not_observed")
                route_rows.append(row)
                continue

            observed_count += 1
            latest_receipt = receipt_paths[0]
            row["latest_receipt_path"] = str(latest_receipt)
            try:
                receipt_doc = load_json(latest_receipt)
            except Exception as exc:
                row["receipt_validation_status"] = STATUS_FAIL_REQUIRED
                row["diagnostic_label"] = "receipt_invalid_json"
                row["stale_reasons"] = [f"receipt_invalid_json:{exc}"]
                blocking_reasons.append(f"{route_name}:{script_id}:receipt_invalid_json")
                route_rows.append(row)
                continue

            validation = validate_route_script_receipt_doc(
                receipt_doc=receipt_doc,
                receipt_path=latest_receipt,
                pack_root=pack_root,
                identity_id=identity_id,
                route_name=route_name,
                script_id=script_id,
                route_doc=route_doc,
                manifest_entry=manifest_entry,
                expected_pattern=receipt_pattern,
                allow_external_receipt=bool(str(receipt_override or "").strip()),
            )
            row["receipt_validation_status"] = str(validation.get("status", "")).strip() or STATUS_FAIL_REQUIRED
            row["expected_receipt_family"] = str(validation.get("expected_receipt_family", "")).strip()
            row["observed_receipt_family"] = str(validation.get("receipt_family", "")).strip()
            row["stale_reasons"] = list(validation.get("stale_reasons") or [])
            row["declared_dependency_projection"] = dict(
                validation.get("declared_dependency_projection") or declared_dependency_projection
            )
            row["observed_dependency_projection"] = dict(
                validation.get("observed_dependency_projection")
                or build_observed_dependency_projection(
                    route_name=route_name,
                    observed_instance_scripts=[script_id],
                    observed_receipt_family=str(validation.get("receipt_family", "")).strip(),
                    observed_route_ready=False,
                    route_scope=ROUTE_SCOPE_ROUTE_SCOPED,
                )
            )
            row["dependency_gap_reasons"] = list(validation.get("dependency_gap_reasons") or [])
            row.update(copy_optional_projection_fields(validation))
            row["diagnostic_label"] = "ready" if row["receipt_validation_status"] == STATUS_PASS_REQUIRED else "receipt_invalid"
            if row["receipt_validation_status"] != STATUS_PASS_REQUIRED:
                blocking_reasons.extend(f"{route_name}:{script_id}:{reason}" for reason in row["stale_reasons"])
            route_rows.append(row)

    status = STATUS_PASS_REQUIRED if not blocking_reasons else STATUS_FAIL_REQUIRED
    if checked_count == 0:
        status = STATUS_SKIPPED_NOT_REQUIRED
    return {
        "status": status,
        "route_total_count": len(route_rows),
        "route_checked_count": checked_count,
        "route_observed_count": observed_count,
        "route_rows": route_rows,
        "stale_reasons": blocking_reasons,
    }


def build_route_execution_lane_matrix(
    *,
    pack_root: Path,
    task_doc: dict[str, Any],
    manifest_validation: dict[str, Any],
    route_validation: dict[str, Any],
    identity_id: str,
    require_observed: bool = False,
    receipt_override: str = "",
    target_route: str = "",
    target_script_id: str = "",
) -> dict[str, Any]:
    routes = task_type_routes(task_doc)
    target_route_token = str(target_route or "").strip()
    target_script_token = str(target_script_id or "").strip()
    route_rows: list[dict[str, Any]] = []
    blocking_reasons: list[str] = []
    observed_count = 0
    checked_count = 0

    for route_row in route_validation.get("route_rows") or []:
        if not isinstance(route_row, dict):
            continue
        route_name = str(route_row.get("route", "")).strip()
        if not route_name or not bool(route_row.get("adopted")):
            continue
        if target_route_token and route_name != target_route_token:
            continue
        route_doc = routes.get(route_name) or {}
        resolved_script_ids = [
            str(token).strip()
            for token in (route_row.get("resolved_script_ids") or [])
            if str(token).strip()
        ]
        if route_row.get("route_ready") is not True:
            for script_id in resolved_script_ids or [""]:
                if target_script_token and script_id and script_id != target_script_token:
                    continue
                row_copy = {
                    "route": route_name,
                    "script_id": script_id,
                    "lane_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
                    "lane_receipt_validation_status": STATUS_SKIPPED_NOT_REQUIRED,
                    "diagnostic_label": "orchestration_not_ready",
                    "receipt_observed_count": 0,
                    "latest_lane_receipt_path": "",
                    "allowed_execution_lanes": [],
                    "lane_admission_policy": {},
                    "lane_receipt_pattern": "",
                    "lane_block_on_fallback": False,
                    "stale_reasons": [],
                }
                route_rows.append(row_copy)
            continue

        for script_id in resolved_script_ids:
            if target_script_token and script_id != target_script_token:
                continue
            row: dict[str, Any] = {
                "route": route_name,
                "script_id": script_id,
                "lane_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
                "lane_receipt_validation_status": STATUS_SKIPPED_NOT_REQUIRED,
                "diagnostic_label": "lane_contract_not_required",
                "receipt_observed_count": 0,
                "latest_lane_receipt_path": "",
                "allowed_execution_lanes": [],
                "lane_admission_policy": {},
                "lane_receipt_pattern": "",
                "lane_block_on_fallback": False,
                "stale_reasons": [],
            }
            if not route_uses_execution_lanes(route_doc):
                route_rows.append(row)
                continue

            checked_count += 1
            lane_contract = validate_route_execution_lane_contract(route_doc)
            row["lane_contract_status"] = str(
                lane_contract.get("lane_contract_status", STATUS_FAIL_REQUIRED)
            ).strip() or STATUS_FAIL_REQUIRED
            row["allowed_execution_lanes"] = list(lane_contract.get("allowed_execution_lanes") or [])
            row["lane_admission_policy"] = dict(lane_contract.get("lane_admission_policy") or {})
            row["lane_receipt_pattern"] = str(lane_contract.get("lane_receipt_pattern", "")).strip()
            row["lane_block_on_fallback"] = bool(lane_contract.get("lane_block_on_fallback"))
            if row["lane_contract_status"] != STATUS_PASS_REQUIRED:
                row["lane_receipt_validation_status"] = STATUS_FAIL_REQUIRED
                row["diagnostic_label"] = "lane_contract_invalid"
                row["stale_reasons"] = list(lane_contract.get("stale_reasons") or [])
                blocking_reasons.extend(f"{route_name}:{script_id}:{reason}" for reason in row["stale_reasons"])
                route_rows.append(row)
                continue

            receipt_paths, path_issues = _resolve_receipt_paths(
                pack_root=pack_root,
                receipt_pattern=row["lane_receipt_pattern"],
                route_name=route_name,
                script_id=script_id,
                receipt_override=receipt_override,
            )
            if path_issues:
                row["lane_receipt_validation_status"] = STATUS_FAIL_REQUIRED
                row["diagnostic_label"] = "lane_receipt_glob_failed"
                row["stale_reasons"] = list(path_issues)
                blocking_reasons.extend(f"{route_name}:{script_id}:{reason}" for reason in row["stale_reasons"])
                route_rows.append(row)
                continue
            row["receipt_observed_count"] = len(receipt_paths)
            if not receipt_paths:
                if require_observed:
                    row["lane_receipt_validation_status"] = STATUS_FAIL_REQUIRED
                    row["diagnostic_label"] = "lane_receipt_missing"
                    row["stale_reasons"] = ["lane_receipt_not_observed"]
                    blocking_reasons.append(f"{route_name}:{script_id}:lane_receipt_not_observed")
                else:
                    row["diagnostic_label"] = "lane_receipt_not_observed_yet"
                route_rows.append(row)
                continue

            observed_count += 1
            latest_receipt = receipt_paths[0]
            row["latest_lane_receipt_path"] = str(latest_receipt)
            try:
                receipt_doc = load_json(latest_receipt)
            except Exception as exc:
                row["lane_receipt_validation_status"] = STATUS_FAIL_REQUIRED
                row["diagnostic_label"] = "lane_receipt_invalid_json"
                row["stale_reasons"] = [f"lane_receipt_invalid_json:{exc}"]
                blocking_reasons.append(f"{route_name}:{script_id}:lane_receipt_invalid_json")
                route_rows.append(row)
                continue

            validation = validate_route_execution_lane_receipt_doc(
                receipt_doc=receipt_doc,
                receipt_path=latest_receipt,
                pack_root=pack_root,
                identity_id=identity_id,
                route_name=route_name,
                script_id=script_id,
                lane_contract=lane_contract,
                allow_external_receipt=bool(str(receipt_override or "").strip()),
            )
            row["lane_receipt_validation_status"] = str(
                validation.get("status", STATUS_FAIL_REQUIRED)
            ).strip() or STATUS_FAIL_REQUIRED
            row["observed_lane_id"] = str(validation.get("lane_id", "")).strip()
            row["observed_lane_class"] = str(validation.get("lane_class", "")).strip()
            row["observed_lane_source"] = str(validation.get("lane_source", "")).strip()
            row["observed_lane_endpoint_class"] = str(validation.get("lane_endpoint_class", "")).strip()
            row["observed_lane_admission_status"] = str(
                validation.get("lane_admission_status", "")
            ).strip()
            row["observed_receipt_family"] = str(validation.get("receipt_family", "")).strip()
            row["stale_reasons"] = list(validation.get("stale_reasons") or [])
            row["diagnostic_label"] = (
                "ready" if row["lane_receipt_validation_status"] == STATUS_PASS_REQUIRED else "lane_receipt_invalid"
            )
            if row["lane_receipt_validation_status"] != STATUS_PASS_REQUIRED:
                blocking_reasons.extend(f"{route_name}:{script_id}:{reason}" for reason in row["stale_reasons"])
            route_rows.append(row)

    status = STATUS_PASS_REQUIRED if not blocking_reasons else STATUS_FAIL_REQUIRED
    if checked_count == 0:
        status = STATUS_SKIPPED_NOT_REQUIRED
    return {
        "status": status,
        "route_total_count": len(route_rows),
        "route_checked_count": checked_count,
        "route_observed_count": observed_count,
        "route_rows": route_rows,
        "stale_reasons": blocking_reasons,
    }
