#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"

ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY = "artifact_family_routing_contract_v1"
ARTIFACT_FAMILY_ROUTING_CONTRACT_ID = "rq_052_identity_artifact_family_routing_contract_v1"
ARTIFACT_FAMILY_ROUTING_VALIDATOR_ID = "scripts/validate_identity_artifact_family_routing.py"
ARTIFACT_FAMILY_ROUTING_MATRIX_VERSION = "v1.6.18"

RULEBOOK_REL = Path("RULEBOOK.jsonl")
TASK_HISTORY_REL = Path("TASK_HISTORY.md")
DIALOGUE_RETENTION_REPORT_ROOT_REL = Path("runtime/reports/dialogue-retention")
DIALOGUE_RETENTION_STATE_ROOT_REL = Path("runtime/state/dialogue-retention")
DIALOGUE_GOVERNANCE_REPORT_ROOT_REL = Path("runtime/reports")
EXPERIENCE_RULEBOOK_DIR_REL = Path("runtime/rulebooks")
EXPERIENCE_EXAMPLES_DIR_REL = Path("runtime/examples")
EXPERIENCE_LOGS_DIR_REL = Path("runtime/logs/feedback")
PROTOCOL_FEEDBACK_ROOT_REL = Path("runtime/protocol-feedback")
CONTINUITY_REPORT_ROOT_REL = Path("runtime/reports/context-continuity")
CONTINUITY_STATE_ROOT_REL = Path("runtime/state/context-continuity")
MEMORY_ABSORPTION_ROOT_REL = Path("runtime/memory-absorption")


@dataclass(frozen=True)
class ArtifactFamilyDescriptor:
    name: str
    canonical_paths: tuple[str, ...]
    semantic_owner: str
    payload_class: str
    primary_producer: str
    primary_consumer: str
    optional: bool = False


CANONICAL_FAMILY_MATRIX: tuple[ArtifactFamilyDescriptor, ...] = (
    ArtifactFamilyDescriptor(
        name="pack_rulebook_family",
        canonical_paths=(RULEBOOK_REL.as_posix(),),
        semantic_owner="durable_identity_rulebook",
        payload_class="append_only_rule_rows",
        primary_producer="identity update lifecycle + governed rule writeback",
        primary_consumer="identity update / learning validators and durable pack evolution",
    ),
    ArtifactFamilyDescriptor(
        name="pack_task_history_family",
        canonical_paths=(TASK_HISTORY_REL.as_posix(),),
        semantic_owner="chronological_task_result_writeback",
        payload_class="human_readable_task_history_markdown",
        primary_producer="post-execution governed task writeback",
        primary_consumer="operator audit and pack-local chronology",
    ),
    ArtifactFamilyDescriptor(
        name="runtime_dialogue_retention_family",
        canonical_paths=(
            DIALOGUE_RETENTION_REPORT_ROOT_REL.as_posix(),
            DIALOGUE_RETENTION_STATE_ROOT_REL.as_posix(),
        ),
        semantic_owner="governed_raw_dialogue_truth_mirror",
        payload_class="thread_jsonl_mirror_plus_receipts_and_state",
        primary_producer="shared post-delivery hook + dialogue-retention guard",
        primary_consumer="raw-dialogue audit and bounded downstream analysis",
    ),
    ArtifactFamilyDescriptor(
        name="runtime_dialogue_governance_family",
        canonical_paths=(
            "runtime/reports/dialogue-content-synthesis-<identity-id>-*.json",
            "runtime/reports/dialogue-cross-validation-matrix-<identity-id>-*.json",
            "runtime/reports/dialogue-result-support-<identity-id>-*.json",
        ),
        semantic_owner="dialogue_to_result_justification",
        payload_class="dialogue synthesis and traceability reports",
        primary_producer="dialogue-governance renderers and validators",
        primary_consumer="dialogue-quality review and done-state support",
        optional=True,
    ),
    ArtifactFamilyDescriptor(
        name="runtime_experience_feedback_family",
        canonical_paths=(
            "runtime/rulebooks/positive.jsonl",
            "runtime/rulebooks/negative.jsonl",
            "runtime/examples/*experience-feedback*.json",
            "runtime/logs/feedback/*.json",
        ),
        semantic_owner="replay_backed_learning_deltas",
        payload_class="positive_negative_rule_deltas_and_feedback_logs",
        primary_producer="experience-feedback writeback and replay validation",
        primary_consumer="fourth-loop strengthening and rule promotion",
        optional=True,
    ),
    ArtifactFamilyDescriptor(
        name="runtime_protocol_feedback_family",
        canonical_paths=(PROTOCOL_FEEDBACK_ROOT_REL.as_posix(),),
        semantic_owner="instance_to_protocol_governance_communication",
        payload_class="feedback batches receipts inbox outbox proposals and indexes",
        primary_producer="protocol-feedback emit/inbox/index helpers",
        primary_consumer="protocol remediation audit and governance circulation",
        optional=True,
    ),
    ArtifactFamilyDescriptor(
        name="runtime_continuity_reentry_family",
        canonical_paths=(
            CONTINUITY_REPORT_ROOT_REL.as_posix(),
            CONTINUITY_STATE_ROOT_REL.as_posix(),
        ),
        semantic_owner="bounded_context_continuity_and_reentry_support",
        payload_class="checkpoints reentry brief and continuity receipts",
        primary_producer="v1.6.16 continuity guard and deterministic writers",
        primary_consumer="startup resume recover continuity consumption",
        optional=True,
    ),
    ArtifactFamilyDescriptor(
        name="runtime_memory_absorption_family",
        canonical_paths=(MEMORY_ABSORPTION_ROOT_REL.as_posix(),),
        semantic_owner="quarantine_and_rematerialization_only",
        payload_class="absorbed_legacy_runtime_evidence",
        primary_producer="explicit migration absorption and backfill only",
        primary_consumer="migration backfill and re-materialization only",
        optional=True,
    ),
)


def clean_string(value: Any) -> str:
    return str(value or "").strip()


def resolve_pack_task(*, catalog_path: Path | None, current_task: str, identity_id: str) -> tuple[Path, Path, dict[str, Any]]:
    if clean_string(current_task):
        task_path = Path(clean_string(current_task)).expanduser().resolve()
        if not task_path.is_file():
            raise FileNotFoundError(f"current_task_not_found:{task_path}")
        task_doc = json.loads(task_path.read_text(encoding="utf-8"))
        if not isinstance(task_doc, dict):
            raise RuntimeError(f"json_root_not_object:{task_path}")
        return task_path.parent.resolve(), task_path, task_doc
    if catalog_path is None or not catalog_path.exists():
        missing_catalog = catalog_path if catalog_path is not None else "<missing>"
        raise FileNotFoundError(f"catalog not found: {missing_catalog}")
    pack_root, task_path = resolve_pack_and_task(catalog_path, identity_id)
    task_doc = json.loads(task_path.read_text(encoding="utf-8"))
    if not isinstance(task_doc, dict):
        raise RuntimeError(f"json_root_not_object:{task_path}")
    return pack_root.resolve(), task_path.resolve(), task_doc


def resolve_artifact_family_routing_contract(task_doc: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
    contract_doc = task_doc.get(ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY)
    if not isinstance(contract_doc, dict):
        contract_doc = {}
    return contract_required(contract_doc), contract_doc, ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY


def artifact_family_routing_contract_skeleton() -> dict[str, Any]:
    return {
        "required": True,
        "contract_id": ARTIFACT_FAMILY_ROUTING_CONTRACT_ID,
        "validator": ARTIFACT_FAMILY_ROUTING_VALIDATOR_ID,
        "fail_mode": "fail_required",
        "family_matrix_version": ARTIFACT_FAMILY_ROUTING_MATRIX_VERSION,
        "canonical_runtime_families": [
            path
            for row in CANONICAL_FAMILY_MATRIX
            for path in row.canonical_paths
            if path.startswith("runtime/")
        ],
        "forbid_generic_sink_names": ["memory"],
        "declaration_gate_not_artifact_family": True,
        "family_matrix": [
            {
                "family": row.name,
                "canonical_paths": list(row.canonical_paths),
                "semantic_owner": row.semantic_owner,
                "payload_class": row.payload_class,
                "primary_producer": row.primary_producer,
                "primary_consumer": row.primary_consumer,
                "optional": bool(row.optional),
            }
            for row in CANONICAL_FAMILY_MATRIX
        ],
        "forbidden_conflations": [
            {
                "left": "pack_rulebook_family",
                "right": "runtime_experience_feedback_family",
                "reason": "RULEBOOK.jsonl is not the runtime learning rulebook family",
            },
            {
                "left": "pack_task_history_family",
                "right": "runtime_continuity_reentry_family",
                "reason": "TASK_HISTORY.md is chronology, not continuity or reentry state",
            },
            {
                "left": "runtime_dialogue_retention_family",
                "right": "runtime_dialogue_governance_family",
                "reason": "raw dialogue mirror is not synthesized dialogue governance",
            },
            {
                "left": "runtime_dialogue_retention_family",
                "right": "runtime_continuity_reentry_family",
                "reason": "raw dialogue mirror is not continuity checkpoint or reentry state",
            },
            {
                "left": "runtime_protocol_feedback_family",
                "right": "runtime_experience_feedback_family",
                "reason": "protocol-feedback is governance communication, not learning sink",
            },
            {
                "left": "runtime_memory_absorption_family",
                "right": "active_success_path",
                "reason": "memory-absorption stays quarantine / re-materialization only",
            },
        ],
    }


def family_roots(pack_root: Path) -> dict[str, tuple[Path, ...]]:
    return {
        "pack_rulebook_family": ((pack_root / RULEBOOK_REL).resolve(),),
        "pack_task_history_family": ((pack_root / TASK_HISTORY_REL).resolve(),),
        "runtime_dialogue_retention_family": (
            (pack_root / DIALOGUE_RETENTION_REPORT_ROOT_REL).resolve(),
            (pack_root / DIALOGUE_RETENTION_STATE_ROOT_REL).resolve(),
        ),
        "runtime_dialogue_governance_family": ((pack_root / DIALOGUE_GOVERNANCE_REPORT_ROOT_REL).resolve(),),
        "runtime_experience_feedback_family": (
            (pack_root / EXPERIENCE_RULEBOOK_DIR_REL).resolve(),
            (pack_root / EXPERIENCE_EXAMPLES_DIR_REL).resolve(),
            (pack_root / EXPERIENCE_LOGS_DIR_REL).resolve(),
        ),
        "runtime_protocol_feedback_family": ((pack_root / PROTOCOL_FEEDBACK_ROOT_REL).resolve(),),
        "runtime_continuity_reentry_family": (
            (pack_root / CONTINUITY_REPORT_ROOT_REL).resolve(),
            (pack_root / CONTINUITY_STATE_ROOT_REL).resolve(),
        ),
        "runtime_memory_absorption_family": ((pack_root / MEMORY_ABSORPTION_ROOT_REL).resolve(),),
    }


def path_under(root: Path, candidate: Path) -> bool:
    try:
        candidate.expanduser().resolve().relative_to(root.expanduser().resolve())
        return True
    except Exception:
        return False


def _substitute_identity_tokens(raw: str, identity_id: str) -> str:
    text = clean_string(raw).replace("<identity-id>", identity_id)
    text = text.replace("${IDENTITY_ID}", identity_id)
    text = text.replace("${identity_id}", identity_id)
    return text


def _pattern_anchor_text(raw: str) -> str:
    token = clean_string(raw)
    if not token:
        return ""
    indices = [token.find(ch) for ch in ("*", "?", "[") if token.find(ch) >= 0]
    if not indices:
        return token
    prefix = token[: min(indices)]
    if not prefix:
        return ""
    if prefix.endswith("/"):
        return prefix.rstrip("/")
    return str(Path(prefix).parent)


def resolve_pack_path(pack_root: Path, identity_id: str, raw: str) -> Path | None:
    token = _pattern_anchor_text(_substitute_identity_tokens(raw, identity_id))
    if not token:
        return None
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    normalized = token.replace("\\", "/")
    pack_prefixes = (
        f"identity/packs/{identity_id}/",
        "identity/packs/<identity-id>/",
        "identity/packs/${IDENTITY_ID}/",
    )
    for prefix in pack_prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            return (pack_root / normalized).resolve()
    runtime_prefixes = (
        f"identity/runtime/{identity_id}/",
        "identity/runtime/",
    )
    for prefix in runtime_prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            return (pack_root / "runtime" / normalized).resolve()
    return (pack_root / normalized).resolve()


def any_payload_under(root: Path) -> bool:
    if not root.exists():
        return False
    if root.is_file():
        return True
    for child in root.rglob("*"):
        if child.is_file():
            return True
    return False
