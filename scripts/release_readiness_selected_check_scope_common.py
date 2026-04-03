#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"

SELECTED_CHECK_SCOPE_CLASS_TARGETED_SUBSET = "bounded_targeted_subset_exclusion"
SELECTED_CHECK_SCOPE_REASON_TARGETED_SUBSET = "selected_check_out_of_scope_for_targeted_subset"
RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_FIELDS: tuple[str, ...] = (
    "selected_check_scope_projection_status",
    "selected_check_scope_class",
    "selected_check_scope_reason",
    "selected_check_scope_excluded_summary_key_count",
    "selected_check_scope_excluded_summary_keys",
)
RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_PROJECTION_MARKER = (
    "release_readiness_selected_check_scope_projection="
    + "|".join(
        f"one_look.{field}"
        for field in RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_FIELDS
    )
)

RELEASE_READINESS_SELECTED_CHECK_SCOPE_TARGETED_SUBSET_MARKER = (
    "targeted_subset_selected_check_scope="
    "selected_check_scope_projection_status=PASS_REQUIRED|"
    "selected_check_scope_class=bounded_targeted_subset_exclusion|"
    "selected_check_scope_reason=selected_check_out_of_scope_for_targeted_subset|"
    "selected_check_scope_excluded_summary_key_count"
)
RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_TARGETED_SUBSET_MARKER,
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_PROJECTION_MARKER,
    *(
        f"one_look.{field}"
        for field in RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_FIELDS
    ),
)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _default_keep_field_value(field_name: str) -> Any:
    if field_name.endswith("_status"):
        return STATUS_SKIPPED_NOT_REQUIRED
    if field_name.endswith("_count"):
        return 0
    if (
        field_name.startswith("is_")
        or field_name.startswith("has_")
        or field_name.startswith("allow_")
        or field_name.endswith("_ready")
        or field_name.endswith("_safe")
        or field_name.endswith("_canonical")
    ):
        return False
    return None


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def selected_check_scope_projection_is_targeted_subset(summary: dict[str, Any]) -> bool:
    if not isinstance(summary, dict):
        return False
    selected_check_mode = _clean_str(summary.get("selected_check_mode")).lower()
    return selected_check_mode == "targeted_subset"


def build_release_readiness_selected_check_scope_one_look_projection(
    projection: dict[str, Any] | None,
) -> dict[str, Any]:
    source = projection if isinstance(projection, dict) else {}
    return {
        "selected_check_scope_projection_status": _clean_str(
            source.get("status")
        ).upper()
        or STATUS_UNKNOWN,
        "selected_check_scope_class": _clean_str(source.get("scope_class")),
        "selected_check_scope_reason": _clean_str(source.get("scope_reason")),
        "selected_check_scope_excluded_summary_key_count": _safe_int(
            source.get("excluded_summary_key_count")
        ),
        "selected_check_scope_excluded_summary_keys": _clean_list(
            source.get("excluded_summary_keys")
        ),
    }


def apply_release_readiness_selected_check_scope_one_look(
    summary: dict[str, Any],
    one_look: dict[str, Any],
) -> None:
    if not isinstance(one_look, dict):
        return
    summary_payload = summary if isinstance(summary, dict) else {}
    projection = summary_payload.get("selected_check_scope_projection") or {}
    one_look.update(
        build_release_readiness_selected_check_scope_one_look_projection(projection)
    )


def build_scope_excluded_selected_check_summary(
    summary_key: str,
    owner_script: str,
    *,
    keep_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "status": STATUS_SKIPPED_NOT_REQUIRED,
        "rc": 0,
        "error_code": "",
        "scope_class": SELECTED_CHECK_SCOPE_CLASS_TARGETED_SUBSET,
        "scope_reason": SELECTED_CHECK_SCOPE_REASON_TARGETED_SUBSET,
        "scope_mode": "selected_check_bounded",
        "summary_key": _clean_str(summary_key),
        "owner_script": _clean_str(owner_script),
        "selected_check_scope_excluded": True,
    }
    if _clean_str(summary_key) == "release_plane_cloud_evidence":
        item["conditions"] = {"required_checks_status": STATUS_SKIPPED_NOT_REQUIRED}
        item["adapter"] = {"release_cloud_evidence_adapter_status": STATUS_SKIPPED_NOT_REQUIRED}
    for field_name in keep_fields:
        default_value = _default_keep_field_value(field_name)
        if default_value is not None:
            item[field_name] = default_value
    return item


def materialize_targeted_subset_selected_check_scope_exclusions(
    summary: dict[str, Any],
    *,
    summary_capture_scripts: dict[str, str],
    structured_summary_capture_specs: dict[str, dict[str, tuple[str, ...]]],
) -> None:
    if not isinstance(summary, dict):
        return

    if not selected_check_scope_projection_is_targeted_subset(summary):
        summary["selected_check_scope_projection"] = {
            "status": STATUS_SKIPPED_NOT_REQUIRED,
            "scope_class": "",
            "scope_reason": "",
            "excluded_summary_key_count": 0,
            "excluded_summary_keys": [],
            "excluded_owner_scripts": [],
        }
        return

    selected_check_names = set(_clean_list(summary.get("selected_check_names")))
    excluded_summary_keys: list[str] = []
    excluded_owner_scripts: list[str] = []

    for owner_script, summary_key in summary_capture_scripts.items():
        if owner_script in selected_check_names:
            continue
        excluded_summary_keys.append(summary_key)
        excluded_owner_scripts.append(owner_script)
        existing_payload = summary.get(summary_key) or {}
        existing_status = ""
        if isinstance(existing_payload, dict):
            existing_status = _clean_str(existing_payload.get("status")).upper()
        if existing_status and existing_status != STATUS_UNKNOWN:
            continue
        keep_fields = tuple(structured_summary_capture_specs.get(summary_key, {}).get("keep_fields", ()))
        scope_excluded_payload = build_scope_excluded_selected_check_summary(
            summary_key,
            owner_script,
            keep_fields=keep_fields,
        )
        summary[summary_key] = scope_excluded_payload
        if summary_key == "release_plane_cloud_evidence":
            release_adapter = summary.get("release_cloud_evidence_adapter") or {}
            release_adapter_status = ""
            if isinstance(release_adapter, dict):
                release_adapter_status = _clean_str(
                    release_adapter.get("release_cloud_evidence_adapter_status")
                ).upper()
            if not release_adapter_status or release_adapter_status == STATUS_UNKNOWN:
                summary["release_cloud_evidence_adapter"] = dict(
                    scope_excluded_payload.get("adapter") or {}
                )

    summary["selected_check_scope_projection"] = {
        "status": STATUS_PASS_REQUIRED,
        "scope_class": SELECTED_CHECK_SCOPE_CLASS_TARGETED_SUBSET,
        "scope_reason": SELECTED_CHECK_SCOPE_REASON_TARGETED_SUBSET,
        "excluded_summary_key_count": len(excluded_summary_keys),
        "excluded_summary_keys": excluded_summary_keys,
        "excluded_owner_scripts": excluded_owner_scripts,
    }
