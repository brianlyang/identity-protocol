from __future__ import annotations

from typing import Any, Mapping


CAPABILITY_ACTIVATION_REPORT_REQUIRED_FIELDS: tuple[str, ...] = (
    "skills_used",
    "mcp_tools_used",
    "tool_calls_used",
    "active_skills",
    "mcp_servers_checked",
    "tool_routes",
    "capability_activation_status",
    "capability_activation_error_code",
    "capability_contract_required",
    "route_scope",
    "route_scope_mode",
    "route_ids",
    "route_selection_cardinality",
    "declared_dependency_projection",
    "observed_dependency_projection",
    "dependency_gap_reasons",
    "undeclared_usage_detected",
    "undeclared_usage_rows",
    "missing_declared_dependency_detected",
    "missing_declared_dependency_rows",
)

CAPABILITY_ACTIVATION_REPORT_OPTIONAL_FIELDS: tuple[str, ...] = (
    "capability_activation_notes",
    "route_script_rows",
    "route_receipt_join_status",
    "route_receipt_join_stale_reasons",
    "route_receipt_rows",
    "route_execution_lane_rows",
    "route_activation_matrix",
    "instance_script_manifest_required",
    "instance_script_manifest_status",
    "instance_script_manifest_stale_reasons",
    "instance_script_orchestration_required",
    "instance_script_orchestration_status",
    "instance_script_orchestration_stale_reasons",
    "instance_script_execution_lane_required",
    "instance_script_execution_lane_status",
    "instance_script_execution_lane_stale_reasons",
    "capability_activation_policy_requested",
    "capability_activation_policy_effective",
    "capability_activation_fallback_attempted",
    "capability_activation_fallback_policy",
    "capability_activation_fallback_rc",
    "capability_activation_initial_status",
    "capability_activation_initial_error_code",
    "capability_activation_fallback_stdout_tail",
    "capability_activation_fallback_stderr_tail",
    "capability_activation_validator_rc",
    "capability_activation_validator_stdout_tail",
    "capability_activation_validator_stderr_tail",
    "capability_activation_report_path",
)


def _clean_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _normalized_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def build_capability_activation_report_projection(
    capability_contract: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(capability_contract or {})
    projection: dict[str, Any] = {
        "skills_used": _clean_string_list(payload.get("skills_used")),
        "mcp_tools_used": _clean_string_list(payload.get("mcp_tools_used")),
        "tool_calls_used": _clean_string_list(payload.get("tool_calls_used")),
        "active_skills": _clean_string_list(payload.get("active_skills")),
        "mcp_servers_checked": list(payload.get("mcp_servers_checked") or [])
        if isinstance(payload.get("mcp_servers_checked"), list)
        else [],
        "tool_routes": list(payload.get("tool_routes") or [])
        if isinstance(payload.get("tool_routes"), list)
        else [],
        "capability_activation_status": str(payload.get("capability_activation_status", "UNKNOWN")),
        "capability_activation_error_code": str(payload.get("capability_activation_error_code", "")),
        "capability_contract_required": bool(
            payload.get("capability_contract_required", payload.get("required", True))
        ),
        "route_scope": str(payload.get("route_scope", "")),
        "route_scope_mode": str(payload.get("route_scope_mode", "")),
        "route_ids": _clean_string_list(payload.get("route_ids")),
        "route_selection_cardinality": str(payload.get("route_selection_cardinality", "")),
        "declared_dependency_projection": _normalized_dict(
            payload.get("declared_dependency_projection")
        ),
        "observed_dependency_projection": _normalized_dict(
            payload.get("observed_dependency_projection")
        ),
        "dependency_gap_reasons": _clean_string_list(payload.get("dependency_gap_reasons")),
        "undeclared_usage_detected": bool(payload.get("undeclared_usage_detected", False)),
        "undeclared_usage_rows": _clean_string_list(payload.get("undeclared_usage_rows")),
        "missing_declared_dependency_detected": bool(
            payload.get("missing_declared_dependency_detected", False)
        ),
        "missing_declared_dependency_rows": _clean_string_list(
            payload.get("missing_declared_dependency_rows")
        ),
    }
    for field in CAPABILITY_ACTIVATION_REPORT_OPTIONAL_FIELDS:
        if field in payload:
            value = payload.get(field)
            if field.endswith("_rows") or field.endswith("_matrix") or field.endswith("_reasons") or field.endswith("_notes"):
                if isinstance(value, list):
                    projection[field] = list(value)
                else:
                    projection[field] = []
            elif field.endswith("_required") or field.endswith("_attempted"):
                projection[field] = bool(value)
            elif field.endswith("_path") or field.endswith("_status") or field.endswith("_policy") or field.endswith("_error_code") or field.endswith("_tail") or field.endswith("_initial_status") or field.endswith("_initial_error_code"):
                projection[field] = str(value or "")
            elif field.endswith("_rc"):
                projection[field] = value
            else:
                projection[field] = value
    return projection
