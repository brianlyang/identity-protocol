from __future__ import annotations

from typing import Any, Iterable

BLOCKER_ALIAS_MAP_VERSION = "v1"

CANONICAL_BLOCKER_TYPES: tuple[str, ...] = (
    "auth_login_required",
    "anti_automation_challenge_required",
    "session_reauthentication_required",
    "manual_verification_required",
)
CANONICAL_BLOCKER_TYPE_SET = frozenset(CANONICAL_BLOCKER_TYPES)

LEGACY_BLOCKER_ALIAS_MAP: dict[str, str] = {
    "login_required": "auth_login_required",
    "captcha_required": "anti_automation_challenge_required",
    "session_expired": "session_reauthentication_required",
}


def canonical_blocker_types_list() -> list[str]:
    return list(CANONICAL_BLOCKER_TYPES)


def build_blocker_alias_map(
    *raw_maps: Any,
    include_default_legacy_aliases: bool = False,
) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    if include_default_legacy_aliases:
        alias_map.update(LEGACY_BLOCKER_ALIAS_MAP)
    for raw_map in raw_maps:
        if not isinstance(raw_map, dict):
            continue
        for raw_key, raw_value in raw_map.items():
            key = str(raw_key or "").strip()
            value = str(raw_value or "").strip()
            if key and value in CANONICAL_BLOCKER_TYPE_SET:
                alias_map[key] = value
    return alias_map


def canonicalize_blocker(
    raw: Any,
    *,
    alias_map: dict[str, str] | None = None,
) -> tuple[str, str]:
    value = str(raw or "").strip()
    if not value:
        return "", "empty"
    if value in CANONICAL_BLOCKER_TYPE_SET:
        return value, "canonical"
    mapped = (alias_map or {}).get(value, "")
    if mapped in CANONICAL_BLOCKER_TYPE_SET:
        return mapped, "legacy_alias_bridge"
    return "", "invalid"


def normalize_blocker_membership(
    values: Iterable[Any],
    *,
    alias_map: dict[str, str] | None = None,
) -> tuple[set[str], list[str], list[str]]:
    canonical: set[str] = set()
    alias_hits: list[str] = []
    invalid: list[str] = []
    for raw in values:
        normalized, mode = canonicalize_blocker(raw, alias_map=alias_map)
        if mode == "canonical":
            canonical.add(normalized)
        elif mode == "legacy_alias_bridge":
            canonical.add(normalized)
            alias_hits.append(str(raw))
        elif mode == "invalid":
            invalid.append(str(raw))
    return canonical, sorted(set(alias_hits)), sorted(set(invalid))


def normalize_blocker_sequence(
    values: Any,
    *,
    alias_map: dict[str, str] | None = None,
) -> tuple[list[str], list[str], list[str]]:
    rows = values if isinstance(values, (list, tuple, set)) else []
    normalized_set, alias_hits, invalid = normalize_blocker_membership(rows, alias_map=alias_map)
    normalized = [token for token in CANONICAL_BLOCKER_TYPES if token in normalized_set]
    return normalized, alias_hits, invalid


def normalize_task_blocker_surfaces(
    task: dict[str, Any],
    *,
    sync_human_collab_blockers_if_present: bool = True,
    include_default_legacy_aliases: bool = True,
) -> dict[str, Any]:
    taxonomy = task.get("blocker_taxonomy_contract")
    collab = task.get("collaboration_trigger_contract")
    escalation = task.get("escalation_policy")
    gates = task.get("gates")
    collaboration_gate_required = (
        isinstance(gates, dict) and str(gates.get("collaboration_trigger_gate", "")).strip() == "required"
    )
    surface_contract_present = (
        isinstance(taxonomy, dict)
        or isinstance(collab, dict)
        or (isinstance(escalation, dict) and "human_collab_blockers" in escalation)
    )
    applicable = collaboration_gate_required or surface_contract_present
    alias_map = build_blocker_alias_map(
        taxonomy.get("legacy_alias_bridge") if isinstance(taxonomy, dict) else None,
        collab.get("legacy_alias_bridge") if isinstance(collab, dict) else None,
        include_default_legacy_aliases=include_default_legacy_aliases,
    )
    canonical_list = canonical_blocker_types_list()
    report: dict[str, Any] = {
        "blocker_alias_map_version": BLOCKER_ALIAS_MAP_VERSION,
        "canonical_blocker_types": canonical_list,
        "applicable": applicable,
        "applicability_reason": (
            "collaboration_trigger_gate_required"
            if collaboration_gate_required
            else ("surface_contract_present" if surface_contract_present else "contract_not_required")
        ),
        "restored_surface_fields": [],
        "restored_version_fields": [],
        "missing_surfaces": [],
        "alias_hits_by_surface": {},
        "invalid_blockers_by_surface": {},
    }
    if not applicable:
        return report

    def _normalize_surface(
        node: Any,
        field: str,
        surface_name: str,
        *,
        required: bool,
    ) -> None:
        if not isinstance(node, dict):
            if required:
                report["missing_surfaces"].append(surface_name)
            return
        normalized, alias_hits, invalid = normalize_blocker_sequence(node.get(field), alias_map=alias_map)
        if alias_hits:
            report["alias_hits_by_surface"][surface_name] = alias_hits
        if invalid:
            report["invalid_blockers_by_surface"][surface_name] = invalid
            return
        if node.get(field) != canonical_list:
            node[field] = list(canonical_list)
            report["restored_surface_fields"].append(surface_name)

    _normalize_surface(
        taxonomy,
        "required_blocker_types",
        "blocker_taxonomy_contract.required_blocker_types",
        required=True,
    )
    if isinstance(taxonomy, dict) and str(taxonomy.get("blocker_alias_map_version", "")).strip() != BLOCKER_ALIAS_MAP_VERSION:
        taxonomy["blocker_alias_map_version"] = BLOCKER_ALIAS_MAP_VERSION
        report["restored_version_fields"].append("blocker_taxonomy_contract.blocker_alias_map_version")

    _normalize_surface(
        collab,
        "trigger_conditions",
        "collaboration_trigger_contract.trigger_conditions",
        required=True,
    )

    if sync_human_collab_blockers_if_present and isinstance(escalation, dict) and "human_collab_blockers" in escalation:
        _normalize_surface(
            escalation,
            "human_collab_blockers",
            "escalation_policy.human_collab_blockers",
            required=False,
        )

    return report
