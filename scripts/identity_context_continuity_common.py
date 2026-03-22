#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

CONTEXT_CONTINUITY_CONTRACT_KEY = "context_continuity_contract_v1"
CONTEXT_CONTINUITY_CONTRACT_ID = "rq_044_identity_context_continuity_artifact_contract_v1"
CONTEXT_CONTINUITY_VALIDATOR_ID = "scripts/validate_identity_context_continuity.py"

REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY = "reentry_brief_consumption_contract_v1"
REENTRY_BRIEF_CONSUMPTION_CONTRACT_ID = "rq_045_identity_reentry_brief_consumption_contract_v1"
REENTRY_BRIEF_VALIDATOR_ID = "scripts/validate_identity_reentry_brief.py"
REENTRY_CONSUMPTION_VALIDATOR_ID = "scripts/validate_identity_reentry_consumption.py"
CONTINUITY_RECEIPT_CONTRACT_ID = "rq_046_identity_context_continuity_receipt_family_contract_v1"
CONTINUITY_RECEIPT_VALIDATOR_ID = "scripts/validate_identity_context_continuity_receipts.py"
CONTINUITY_RECEIPT_KINDS: dict[str, str] = {
    "checkpoint": "instance_continuity_checkpoint_receipt",
    "migration_handoff": "instance_migration_handoff_receipt",
    "reentry_brief": "instance_reentry_brief_receipt",
    "reentry_consumption": "instance_reentry_consumption_receipt",
}

CONTINUITY_ARTIFACT_KINDS: tuple[str, ...] = (
    "rolling_checkpoint",
    "stage_checkpoint",
    "migration_checkpoint",
    "reentry_brief",
)
CHECKPOINT_ARTIFACT_KINDS: tuple[str, ...] = (
    "rolling_checkpoint",
    "stage_checkpoint",
    "migration_checkpoint",
)
STALENESS_TOKENS = frozenset({"stale", "expired", "invalid", "obsolete"})
AUTHORITY_OVERRIDE_KEYS: tuple[str, ...] = (
    "authority_override",
    "override_authority",
    "override_current_task",
    "override_identity_prompt",
    "override_governance_doc",
    "override_review_doc",
    "override_workbook",
    "override_runtime_receipts",
)
REPORT_ROOT_REL = Path("runtime/reports/context-continuity")
STATE_ROOT_REL = Path("runtime/state/context-continuity")
REENTRY_BRIEF_REL = STATE_ROOT_REL / "active-reentry-brief.json"
CHECKPOINT_PATTERN = "continuity-*.json"
REF_KEYS: tuple[str, ...] = (
    "ref",
    "path",
    "uri",
    "id",
    "artifact_ref",
    "receipt_ref",
    "task_ref",
    "governance_ref",
    "review_ref",
)
STABLE_PREFIX_FAMILIES: dict[str, tuple[str, ...]] = {
    "identity": ("identity",),
    "task": ("task",),
    "lane": ("lane",),
    "authority": ("authority",),
    "contract": ("contract",),
}
DYNAMIC_TAIL_FAMILIES: dict[str, tuple[str, ...]] = {
    "lineage": ("lineage", "supersede"),
    "completed": ("completed",),
    "blockers": ("blocker",),
    "next_actions": ("next", "action"),
    "receipt": ("receipt",),
}


def clean_string(value: Any) -> str:
    return str(value or "").strip()


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def resolve_pack_task(
    *,
    catalog_path: Path | None,
    current_task: str,
    identity_id: str,
) -> tuple[Path, Path, dict[str, Any]]:
    if clean_string(current_task):
        task_path = Path(clean_string(current_task)).expanduser().resolve()
        pack_root = task_path.parent.resolve()
        task_doc = load_json(task_path)
        return pack_root, task_path, task_doc
    if catalog_path is None or not catalog_path.exists():
        missing_catalog = catalog_path if catalog_path is not None else "<missing>"
        raise FileNotFoundError(f"catalog not found: {missing_catalog}")
    pack_root, task_path = resolve_pack_and_task(catalog_path, identity_id)
    task_doc = load_json(task_path)
    return pack_root, task_path, task_doc


def _contract_aliases(primary_key: str) -> tuple[str, ...]:
    legacy = primary_key.removesuffix("_v1")
    if legacy == primary_key:
        return (primary_key,)
    return (primary_key, legacy)


def resolve_contract(task_doc: dict[str, Any], primary_key: str) -> tuple[dict[str, Any], str]:
    for key in _contract_aliases(primary_key):
        node = task_doc.get(key)
        if isinstance(node, dict):
            return node, key
    return {}, primary_key


def continuity_contract_required(task_doc: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
    contract, contract_key = resolve_contract(task_doc, CONTEXT_CONTINUITY_CONTRACT_KEY)
    return contract_required(contract), contract, contract_key


def reentry_contract_required(task_doc: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
    contract, contract_key = resolve_contract(task_doc, REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY)
    return contract_required(contract), contract, contract_key


def continuity_report_root(pack_root: Path) -> Path:
    return (pack_root.resolve() / REPORT_ROOT_REL).resolve()


def continuity_state_root(pack_root: Path) -> Path:
    return (pack_root.resolve() / STATE_ROOT_REL).resolve()


def reentry_brief_path(pack_root: Path) -> Path:
    return (pack_root.resolve() / REENTRY_BRIEF_REL).resolve()


def discover_continuity_artifact(
    *,
    pack_root: Path,
    explicit_artifact: str,
    artifact_kind: str,
) -> tuple[Path | None, str]:
    explicit = clean_string(explicit_artifact)
    if explicit:
        path = Path(explicit).expanduser().resolve()
        return (path if path.exists() else None), "explicit_artifact"

    normalized_kind = clean_string(artifact_kind)
    if normalized_kind == "reentry_brief":
        brief = reentry_brief_path(pack_root)
        return (brief if brief.exists() else None), "canonical_reentry_brief"

    report_root = continuity_report_root(pack_root)
    checkpoint_hits = sorted(
        (
            row.resolve()
            for row in report_root.glob(CHECKPOINT_PATTERN)
            if row.is_file()
        ),
        key=lambda path: path.stat().st_mtime,
    )
    if checkpoint_hits:
        return checkpoint_hits[-1], "latest_continuity_report"

    brief = reentry_brief_path(pack_root)
    if brief.exists():
        return brief, "canonical_reentry_brief_fallback"
    return None, "artifact_not_found"


def load_artifact_doc(path: Path) -> dict[str, Any]:
    return load_json(path)


def validate_contract_tuple(
    contract: dict[str, Any],
    *,
    expected_contract_id: str,
    accepted_validator_ids: tuple[str, ...],
) -> list[str]:
    issues: list[str] = []
    if clean_string(contract.get("contract_id")) != expected_contract_id:
        issues.append("contract_id_mismatch")
    validator = clean_string(contract.get("validator"))
    validators = [clean_string(row) for row in contract.get("validators", [])] if isinstance(contract.get("validators"), list) else []
    if validator:
        if accepted_validator_ids and validator not in accepted_validator_ids:
            issues.append("validator_mismatch")
    elif validators:
        if accepted_validator_ids and not all(row in validators for row in accepted_validator_ids if row):
            issues.append("validators_family_incomplete")
    else:
        issues.append("validator_missing")
    if clean_string(contract.get("fail_mode")).lower() != "fail_required":
        issues.append("fail_mode_not_fail_required")
    return issues


def normalize_ref_rows(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (str, dict)):
        return [value]
    return []


def ref_row_nonempty(row: Any) -> bool:
    if isinstance(row, str):
        return bool(row.strip())
    if isinstance(row, dict):
        for key in REF_KEYS:
            if nonempty(row.get(key)):
                return True
        return any(nonempty(value) for value in row.values())
    return False


def ref_row_token(row: Any) -> str:
    if isinstance(row, str):
        return clean_string(row)
    if isinstance(row, dict):
        for key in REF_KEYS:
            token = clean_string(row.get(key))
            if token:
                return token
    return ""


def normalize_token(value: Any) -> str:
    return clean_string(value).lower()


def freshness_indicates_stale(value: Any) -> bool:
    if isinstance(value, str):
        return normalize_token(value) in STALENESS_TOKENS
    if isinstance(value, dict):
        for key in ("status", "freshness_status", "state"):
            token = normalize_token(value.get(key))
            if token in STALENESS_TOKENS:
                return True
    return False


def path_within(path: Path, root: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to(root.expanduser().resolve())
        return True
    except Exception:
        return False


def validate_ref_family(field_name: str, value: Any) -> tuple[list[Any], list[str]]:
    rows = normalize_ref_rows(value)
    issues: list[str] = []
    if not rows:
        issues.append(f"{field_name}_missing")
        return rows, issues
    for idx, row in enumerate(rows):
        if not ref_row_nonempty(row):
            issues.append(f"{field_name}_row_invalid:{idx}")
    return rows, issues


def validate_task_field_presence(field_name: str, value: Any) -> list[str]:
    if value is None:
        return [f"{field_name}_missing"]
    if isinstance(value, str) and not value.strip():
        return [f"{field_name}_blank"]
    if isinstance(value, (list, dict)) and field_name == "task_focus_summary" and not value:
        return [f"{field_name}_blank"]
    return []


def artifact_location_status(*, pack_root: Path, artifact_path: Path) -> tuple[str, list[str]]:
    if not path_within(artifact_path, pack_root):
        return "NOT_PACK_SCOPED", []
    if path_within(artifact_path, pack_root / "scripts"):
        return STATUS_FAIL_REQUIRED, ["artifact_under_scripts_surface"]
    if path_within(artifact_path, continuity_report_root(pack_root)):
        return STATUS_PASS_REQUIRED, []
    if path_within(artifact_path, continuity_state_root(pack_root)):
        return STATUS_PASS_REQUIRED, []
    return STATUS_FAIL_REQUIRED, ["artifact_outside_canonical_runtime_family"]


def reentry_brief_location_status(*, pack_root: Path, brief_path: Path) -> tuple[str, list[str]]:
    base_status, base_issues = artifact_location_status(pack_root=pack_root, artifact_path=brief_path)
    if base_status != STATUS_PASS_REQUIRED:
        return base_status, base_issues
    if not path_within(brief_path, continuity_state_root(pack_root)):
        return STATUS_FAIL_REQUIRED, ["reentry_brief_not_under_state_runtime_family"]
    return STATUS_PASS_REQUIRED, []


def continuity_report_location_status(*, pack_root: Path, report_path: Path) -> tuple[str, list[str]]:
    if not path_within(report_path, pack_root):
        return "NOT_PACK_SCOPED", []
    if path_within(report_path, pack_root / "scripts"):
        return STATUS_FAIL_REQUIRED, ["report_under_scripts_surface"]
    if path_within(report_path, continuity_report_root(pack_root)):
        return STATUS_PASS_REQUIRED, []
    if path_within(report_path, continuity_state_root(pack_root)):
        return STATUS_FAIL_REQUIRED, ["report_under_state_surface"]
    return STATUS_FAIL_REQUIRED, ["report_outside_canonical_runtime_report_family"]


def validate_continuity_artifact_doc(
    *,
    artifact_doc: dict[str, Any],
    expected_identity_id: str,
    expected_artifact_kind: str,
) -> tuple[dict[str, Any], list[str], list[str]]:
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

    authority_refs, authority_issues = validate_ref_family("authority_refs", artifact_doc.get("authority_refs"))
    receipt_refs, receipt_issues = validate_ref_family("receipt_refs", artifact_doc.get("receipt_refs"))

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
    schema_issues.extend(validate_task_field_presence("task_focus_summary", task_focus_summary))
    schema_issues.extend(validate_task_field_presence("completed_since_previous", completed_since_previous))
    schema_issues.extend(validate_task_field_presence("open_blockers", open_blockers))
    schema_issues.extend(validate_task_field_presence("next_actions", next_actions))

    if "supersedes_ref" not in artifact_doc:
        schema_issues.append("supersedes_ref_missing")
    if "freshness" not in artifact_doc:
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
    return normalized_payload, schema_issues, stale_issues


def discover_continuity_report_doc(
    *,
    pack_root: Path,
    explicit_report: str,
    required_fields: tuple[str, ...],
    preferred_receipt_kind: str = "",
    selection_requires_fields: bool = True,
) -> tuple[Path | None, str]:
    explicit = clean_string(explicit_report)
    if explicit:
        path = Path(explicit).expanduser().resolve()
        return (path if path.exists() else None), "explicit_report"

    report_root = continuity_report_root(pack_root)
    if not report_root.exists():
        return None, "report_root_missing"

    hits = sorted(
        (row.resolve() for row in report_root.glob("*.json") if row.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    preferred_kind = clean_string(preferred_receipt_kind)
    fallback_candidate: Path | None = None
    for path in hits:
        try:
            doc = load_json(path)
        except Exception:
            continue
        if preferred_kind:
            receipt_kind = clean_string(doc.get("receipt_kind") or doc.get("receipt_family"))
            if not receipt_kind:
                continue
            if receipt_kind != preferred_kind:
                continue
        if fallback_candidate is None:
            fallback_candidate = path
        if all(nonempty(doc.get(field)) for field in required_fields):
            return path, "latest_matching_report"
    if not selection_requires_fields and fallback_candidate is not None:
        return fallback_candidate, "latest_candidate_report"
    return None, "report_not_found"


def issues_have_prefix(issues: list[str], *prefixes: str) -> bool:
    for issue in issues:
        for prefix in prefixes:
            if issue == prefix or issue.startswith(prefix):
                return True
    return False


def semantic_family_present(container: Any, tokens: tuple[str, ...]) -> bool:
    if not isinstance(container, dict):
        return False
    lowered_tokens = tuple(token.lower() for token in tokens)
    for key, value in container.items():
        key_norm = clean_string(key).lower()
        if not key_norm:
            continue
        if any(token in key_norm for token in lowered_tokens) and nonempty(value):
            return True
    return False


def extract_first_semantic_value(container: Any, tokens: tuple[str, ...]) -> Any:
    if not isinstance(container, dict):
        return None
    lowered_tokens = tuple(token.lower() for token in tokens)
    for key, value in container.items():
        key_norm = clean_string(key).lower()
        if not key_norm:
            continue
        if any(token in key_norm for token in lowered_tokens) and nonempty(value):
            return value
    return None


def validate_reentry_brief_sections(artifact_doc: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    stable_prefix = artifact_doc.get("stable_prefix")
    dynamic_tail = artifact_doc.get("dynamic_tail")
    payload = {
        "stable_prefix": stable_prefix,
        "dynamic_tail": dynamic_tail,
        "continuity_lineage_ref": extract_first_semantic_value(dynamic_tail, DYNAMIC_TAIL_FAMILIES["lineage"]),
    }
    issues: list[str] = []
    if not isinstance(stable_prefix, dict):
        issues.append("stable_prefix_not_object")
    else:
        for family_name, tokens in STABLE_PREFIX_FAMILIES.items():
            if not semantic_family_present(stable_prefix, tokens):
                issues.append(f"stable_prefix_missing_family:{family_name}")
    if not isinstance(dynamic_tail, dict):
        issues.append("dynamic_tail_not_object")
    else:
        for family_name, tokens in DYNAMIC_TAIL_FAMILIES.items():
            if not semantic_family_present(dynamic_tail, tokens):
                issues.append(f"dynamic_tail_missing_family:{family_name}")
    return payload, issues
