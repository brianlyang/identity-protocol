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
