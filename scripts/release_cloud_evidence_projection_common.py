from __future__ import annotations

from typing import Any, Mapping

from projection_profile_exclusion_scope_common import build_projection_profile_exclusion_payload


def _as_mapping(payload: Mapping[str, Any] | dict[str, Any] | None) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        return payload
    return {}


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _clean_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    return []


def _clean_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _clean_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _clean_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def build_release_cloud_evidence_adapter_projection(
    adapter_payload: Mapping[str, Any] | dict[str, Any] | None,
) -> dict[str, Any]:
    payload = _as_mapping(adapter_payload)
    return {
        "release_cloud_evidence_adapter_status": _clean_str(payload.get("release_cloud_evidence_adapter_status")),
        "adapter_source_kind": _clean_str(payload.get("adapter_source_kind")),
        "adapter_acquisition_mode": _clean_str(payload.get("adapter_acquisition_mode")),
        "adapter_fetch_transport": _clean_str(payload.get("adapter_fetch_transport")),
        "adapter_local_dev_canonical": _clean_bool(payload.get("adapter_local_dev_canonical")),
        "adapter_best_effort_fetch": _clean_bool(payload.get("adapter_best_effort_fetch")),
        "semantic_consumption_mode": _clean_str(payload.get("semantic_consumption_mode")),
        "checks_json_path": _clean_str(payload.get("checks_json_path")),
        "required_gates_run_id": _clean_str(payload.get("required_gates_run_id")),
        "run_url": _clean_str(payload.get("run_url")),
        "required_checks_count": _clean_int(payload.get("required_checks_count")),
        "adapter_http_status": _clean_str(payload.get("adapter_http_status")),
        "github_rate_limit_remaining": _clean_str(payload.get("github_rate_limit_remaining")),
        "github_rate_limit_reset_epoch": _clean_str(payload.get("github_rate_limit_reset_epoch")),
        "stale_reasons": _clean_list(payload.get("stale_reasons")),
    }


def build_projection_profile_excluded_release_cloud_evidence_adapter(
    *,
    profile_id: str,
    execution_mode: str,
    description: str,
    owner_surface: str,
) -> dict[str, Any]:
    return build_projection_profile_exclusion_payload(
        profile_id=profile_id,
        execution_mode=execution_mode,
        description=description,
        excluded_area="release_cloud_evidence_adapter",
        owner_surface=owner_surface,
        extra_fields={
            "release_cloud_evidence_adapter_status": "SKIPPED_NOT_REQUIRED",
            "adapter_source_kind": "",
            "adapter_acquisition_mode": "",
            "adapter_fetch_transport": "",
            "adapter_local_dev_canonical": False,
            "adapter_best_effort_fetch": False,
            "semantic_consumption_mode": "",
            "checks_json_path": "",
            "required_gates_run_id": "",
            "run_url": "",
            "required_checks_count": 0,
            "adapter_http_status": "",
            "github_rate_limit_remaining": "",
            "github_rate_limit_reset_epoch": "",
        },
    )


def build_release_plane_cloud_evidence_summary_projection(
    validator_payload: Mapping[str, Any] | dict[str, Any] | None,
) -> dict[str, Any]:
    payload = _as_mapping(validator_payload)
    return {
        "status": _clean_str(payload.get("release_plane_cloud_evidence_status")),
        "error_code": _clean_str(payload.get("error_code")),
        "release_plane_status": _clean_str(payload.get("release_plane_status")),
        "target_branch": _clean_str(payload.get("target_branch")),
        "release_head_sha": _clean_str(payload.get("release_head_sha")),
        "required_gates_run_id": _clean_str(payload.get("required_gates_run_id")),
        "run_url": _clean_str(payload.get("run_url")),
        "checks_json": _clean_str(payload.get("checks_json")),
        "jobs_json": _clean_str(payload.get("jobs_json")),
        "gh_runs_json": _clean_str(payload.get("gh_runs_json")),
        "evidence_ref": _clean_str(payload.get("evidence_ref")),
        "conditions": _clean_dict(payload.get("conditions")),
        "stale_reasons": _clean_list(payload.get("stale_reasons")),
        "adapter": build_release_cloud_evidence_adapter_projection(payload),
    }
