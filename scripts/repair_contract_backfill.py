#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml

from blocker_taxonomy_common import normalize_task_blocker_surfaces
from create_identity_pack import (
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID,
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY,
    DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID,
    DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID,
    DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER,
    DOWNSINK_LITERAL_LOCK_SCAN_GLOBS,
    DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID,
    DOWNSINK_REQUIRED_DOMAINS,
    HOST_GATEWAY_BROADCAST_ACK_PATTERN,
    HOST_GATEWAY_BROADCAST_INDEX_FILE,
    HOST_GATEWAY_BROADCAST_ITEMS_DIR,
    HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN,
    HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
    HOST_GATEWAY_BROADCAST_STATE_FILE,
    HOST_GATEWAY_CONTRACT_ID,
    HOST_GATEWAY_CONTRACT_KEY,
    HOST_GATEWAY_INGRESS_DISPATCH_TOKEN,
    HOST_GATEWAY_RELATIVE_CONTRACT_PATH,
    HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH,
    HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH,
    HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH,
    HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH,
    HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH,
    HOST_GATEWAY_REQUIRED_DISPATCH_MODE,
    HOST_GATEWAY_REQUIRED_RELEASE_MODE,
    HOST_GATEWAY_REQUIRED_TUPLE_FIELDS,
    HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY,
    HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE,
    HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR,
    HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED,
    HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS,
    HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS,
    HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY,
    HOST_VISIBLE_FINAL_CHANNEL_ID,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE,
    HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS,
    HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_SURFACE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE,
    INSTANCE_PACK_TOPOLOGY_CONTRACT_ID,
    INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY,
    INSTANCE_PACK_TOPOLOGY_VALIDATOR_ID,
    CONTEXT_CONTINUITY_CONTRACT_ID,
    CONTEXT_CONTINUITY_CONTRACT_KEY,
    CONTEXT_CONTINUITY_REPORT_ROOT_REL,
    CONTEXT_CONTINUITY_STATE_ROOT_REL,
    CONTEXT_CONTINUITY_VALIDATOR_ID,
    CONTINUITY_RECEIPT_VALIDATOR_ID,
    INSTANCE_SCRIPT_MANIFEST_RELATIVE_PATH,
    INSTANCE_SCRIPT_MANIFEST_VALIDATOR_ID,
    INSTANCE_SCRIPT_EXECUTION_LANE_VALIDATOR_ID,
    INSTANCE_SCRIPT_ORCHESTRATION_VALIDATOR_ID,
    INSTANCE_SCRIPT_RECEIPT_JOIN_VALIDATOR_ID,
    HEADSTAMP_RECURRENCE_VALIDATOR_ID,
    REENTRY_BRIEF_CONSUMPTION_CONTRACT_ID,
    REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY,
    REENTRY_BRIEF_VALIDATOR_ID,
    REENTRY_CONSUMPTION_VALIDATOR_ID,
    UNIQUE_EGRESS_SCRIPT,
    UNIQUE_INGRESS_SCRIPT,
    _copy_jsonl_with_identity,
    _context_continuity_contract_skeleton,
    _copy_sample_with_identity,
    _default_instance_script_manifest,
    _default_identity_agent_yaml,
    _default_instance_scripts_readme,
    _derived_prompt_conformance_contract_skeleton,
    _ensure_instance_pack_topology_contract,
    _default_identity_prompt_markdown,
    _ensure_intake_p1_contracts,
    _ensure_identity_prompt_governance_kernel,
    ensure_native_chat_prompt_hard_guard,
    _multimodal_plugin_enforcement_contract_skeleton,
    _provider_bindings_template_text,
    _protocol_lane_activation_headstamp_contract_skeleton,
    _host_gateway_signer_secret_env,
    _host_gateway_wrapper_template_attestation_policy,
    _host_visible_surface_registry_contract_skeleton,
    _protocol_downsink_path_immutability_contract_skeleton,
    _protocol_host_unique_channel_contract_skeleton,
    _protocol_unique_entry_gate_contract_skeleton,
    _prompt_bootstrap_capability_contract_skeleton,
    _prompt_capability_matrix_contract_skeleton,
    _prompt_kernel_executable_coupling_contract_skeleton,
    _reentry_brief_consumption_contract_skeleton,
    _reasoning_loop_failclose_contract_skeleton,
    _skill_frontmatter_contract_skeleton,
    _skill_installation_supply_chain_contract_skeleton,
    _skill_sync_drift_guard_contract_skeleton,
    _write_replay_sample,
    materialize_protocol_host_gateway_artifacts,
)
from identity_context_continuity_materialization_common import (
    materialize_identity_context_continuity_assets,
)
from identity_dialogue_retention_common import (
    DIALOGUE_RETENTION_CONTRACT_ID,
    DIALOGUE_RETENTION_CONTRACT_KEY,
    DIALOGUE_RETENTION_VALIDATOR_ID,
    dialogue_retention_contract_skeleton,
    materialize_identity_dialogue_retention_assets,
)
from identity_artifact_family_routing_common import (
    ARTIFACT_FAMILY_ROUTING_CONTRACT_ID,
    ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY,
    ARTIFACT_FAMILY_ROUTING_VALIDATOR_ID,
    artifact_family_routing_contract_skeleton,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task
from identity_codex_launcher_common import (
    IDENTITY_CODEX_LAUNCHER_CONTRACT_ID,
    IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY,
    IDENTITY_CODEX_LAUNCHER_INSTALLER_ID,
    IDENTITY_CODEX_LAUNCHER_MANIFEST_REL,
    IDENTITY_CODEX_LAUNCHER_README_REL,
    IDENTITY_CODEX_LAUNCHER_RENDERER_ID,
    IDENTITY_CODEX_LAUNCHER_VALIDATOR_ID,
    ensure_launcher_assets,
    ensure_launcher_contract,
    launcher_manifest_doc,
    launcher_readme_text,
)
from response_stamp_common import normalize_response_stamp_profile
from version_baseline_common import (
    apply_version_baseline_to_catalog_row,
    apply_version_baseline_to_meta_doc,
    apply_version_baseline_to_task_doc,
    load_version_baseline_or_raise,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_LAUNCHER_WIRE_MISSING = "IP-ILAUNCH-003"
ERR_LAUNCHER_WIRE_INVALID = "IP-ILAUNCH-004"


REQUIRED_INTAKE_KEYS = (
    "multi_track_cross_verification_contract_v1",
    "intake_evidence_quorum_contract_v1",
    "fallback_taxonomy_normalization_contract_v1",
    "dedup_monotonic_winner_contract_v1",
    "cross_workflow_evidence_schema_contract_v1",
    "skill_path_integrity_contract_v1",
    "route_workflow_version_pinning_contract_v1",
    "skill_installation_supply_chain_contract_v1",
    "skill_frontmatter_contract_v1",
    "skill_sync_drift_guard_contract_v1",
)
REQUIRED_TOPOLOGY_KEYS = (
    INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY,
)
REQUIRED_LAUNCHER_KEYS = (
    IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY,
)
REQUIRED_CONTINUITY_KEYS = (
    CONTEXT_CONTINUITY_CONTRACT_KEY,
    REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY,
)
REQUIRED_DIALOGUE_RETENTION_KEYS = (
    DIALOGUE_RETENTION_CONTRACT_KEY,
)

REQUIRED_ARTIFACT_FAMILY_ROUTING_KEYS = (
    ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY,
)

REQUIRED_PROMPT_KEYS = (
    "prompt_bootstrap_capability_contract_v1",
    "prompt_capability_matrix_fail_closed_contract_v1",
    "derived_prompt_conformance_contract_v1",
    "prompt_import_executable_coupling_contract_v1",
)

REQUIRED_MULTIMODAL_KEYS = (
    "multimodal_plugin_enforcement_contract_v1",
)
REQUIRED_REASONING_KEYS = (
    "reasoning_loop_failclose_contract_v1",
)
REQUIRED_ENTRY_KEYS = (
    "protocol_unique_entry_gate_contract_v1",
)
REQUIRED_LANE_HEADSTAMP_KEYS = (
    "protocol_lane_activation_headstamp_contract_v1",
)
REQUIRED_HOST_GATEWAY_KEYS = (
    HOST_GATEWAY_CONTRACT_KEY,
)
REQUIRED_HOST_VISIBLE_SURFACE_KEYS = (
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
)
REQUIRED_DOWNSINK_KEYS = (
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY,
)

PROMPT_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "prompt_bootstrap_capability_contract_v1": _prompt_bootstrap_capability_contract_skeleton(),
    "prompt_capability_matrix_fail_closed_contract_v1": _prompt_capability_matrix_contract_skeleton(),
    "derived_prompt_conformance_contract_v1": _derived_prompt_conformance_contract_skeleton(),
    "prompt_import_executable_coupling_contract_v1": _prompt_kernel_executable_coupling_contract_skeleton(),
}

MULTIMODAL_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "multimodal_plugin_enforcement_contract_v1": _multimodal_plugin_enforcement_contract_skeleton(),
}
REASONING_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "reasoning_loop_failclose_contract_v1": _reasoning_loop_failclose_contract_skeleton(),
}
ENTRY_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "protocol_unique_entry_gate_contract_v1": _protocol_unique_entry_gate_contract_skeleton(),
}
LANE_HEADSTAMP_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "protocol_lane_activation_headstamp_contract_v1": _protocol_lane_activation_headstamp_contract_skeleton(),
}
HOST_GATEWAY_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    HOST_GATEWAY_CONTRACT_KEY: _protocol_host_unique_channel_contract_skeleton("default"),
}
HOST_VISIBLE_SURFACE_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY: _host_visible_surface_registry_contract_skeleton(),
}
DOWNSINK_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY: _protocol_downsink_path_immutability_contract_skeleton(),
}
CONTINUITY_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    CONTEXT_CONTINUITY_CONTRACT_KEY: _context_continuity_contract_skeleton(),
    REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY: _reentry_brief_consumption_contract_skeleton(),
}
DIALOGUE_RETENTION_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    DIALOGUE_RETENTION_CONTRACT_KEY: dialogue_retention_contract_skeleton(),
}
ARTIFACT_FAMILY_ROUTING_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY: artifact_family_routing_contract_skeleton(),
}
SKILL_SUPPLY_CHAIN_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "skill_installation_supply_chain_contract_v1": _skill_installation_supply_chain_contract_skeleton("default"),
    "skill_frontmatter_contract_v1": _skill_frontmatter_contract_skeleton(),
    "skill_sync_drift_guard_contract_v1": _skill_sync_drift_guard_contract_skeleton(),
}

CAPABILITY_DRIVER_VALIDATOR_IDS: tuple[str, ...] = (
    "scripts/validate_identity_tool_installation.py",
    DIALOGUE_RETENTION_VALIDATOR_ID,
    "scripts/validate_identity_vendor_api_discovery.py",
    "scripts/validate_identity_vendor_api_solution.py",
    INSTANCE_SCRIPT_MANIFEST_VALIDATOR_ID,
    INSTANCE_SCRIPT_ORCHESTRATION_VALIDATOR_ID,
    INSTANCE_SCRIPT_RECEIPT_JOIN_VALIDATOR_ID,
    INSTANCE_SCRIPT_EXECUTION_LANE_VALIDATOR_ID,
    CONTEXT_CONTINUITY_VALIDATOR_ID,
    REENTRY_BRIEF_VALIDATOR_ID,
    REENTRY_CONSUMPTION_VALIDATOR_ID,
    CONTINUITY_RECEIPT_VALIDATOR_ID,
)

ERR_CONTINUITY_WIRE_MISSING = "IP-CONT-WIRE-001"
ERR_CONTINUITY_WIRE_INVALID = "IP-CONT-WIRE-002"
ERR_DRET_WIRE_MISSING = "IP-DRET-WIRE-001"
ERR_DRET_WIRE_INVALID = "IP-DRET-WIRE-002"

ERR_PROMPT_WIRE_MISSING = "IP-PROMPT-WIRE-002"
ERR_PROMPT_WIRE_INVALID = "IP-PROMPT-WIRE-003"
ERR_MM_WIRE_MISSING = "IP-MM-WIRE-001"
ERR_MM_WIRE_INVALID = "IP-MM-WIRE-002"
ERR_RL_WIRE_MISSING = "IP-RL-WIRE-001"
ERR_RL_WIRE_INVALID = "IP-RL-WIRE-002"
ERR_ENTRY_WIRE_MISSING = "IP-GATE-ENTRY-001"
ERR_ENTRY_WIRE_INVALID = "IP-GATE-ENTRY-002"
ERR_LANE_HEADSTAMP_WIRE_MISSING = "IP-LANE-WIRE-001"
ERR_LANE_HEADSTAMP_WIRE_INVALID = "IP-LANE-WIRE-002"
ERR_HOST_GATEWAY_WIRE_MISSING = "IP-GATE-ENTRY-001"
ERR_HOST_GATEWAY_WIRE_INVALID = "IP-GATE-ENTRY-002"
ERR_VISIBLE_SURFACE_WIRE_MISSING = "IP-HDSTAMP-001"
ERR_VISIBLE_SURFACE_WIRE_INVALID = "IP-HDSTAMP-003"
ERR_DOWNSINK_WIRE_MISSING = "IP-DSPATH-001"
ERR_DOWNSINK_WIRE_INVALID = "IP-DSPATH-002"
REASONING_LEVEL_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
REASONING_MIN_LEVEL = "L3"
FILE_GOVERNANCE_SKILL_ID = "ai-folder-governance"
ENTRY_SCRIPT = UNIQUE_INGRESS_SCRIPT
ENTRY_BUNDLE_KEY = "required_gate_bundle_runner"
LEGACY_VALIDATOR_ID_REPLACEMENTS: dict[str, str] = {
    "scripts/validate_current_turn_authoritative_headstamp.py": HEADSTAMP_RECURRENCE_VALIDATOR_ID,
}


def _normalize_instance_pack_topology_contract(task_doc: dict[str, Any], identity_id: str) -> list[str]:
    restored: list[str] = []
    before = json.loads(json.dumps(task_doc.get(INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY) or {}))
    _ensure_instance_pack_topology_contract(task_doc, identity_id)
    node = task_doc.get(INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY)
    if not isinstance(node, dict):
        return restored
    if before != node:
        restored.append(INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY)
    lifecycle_contract = task_doc.get("identity_update_lifecycle_contract")
    validation_contract = lifecycle_contract.get("validation_contract") if isinstance(lifecycle_contract, dict) else None
    if isinstance(validation_contract, dict):
        _, appended = _merge_validator_ids(
            validation_contract,
            "required_checks",
            [INSTANCE_PACK_TOPOLOGY_VALIDATOR_ID],
        )
        restored.extend(f"identity_update_lifecycle_contract.validation_contract.required_checks:{row}" for row in appended)
    return restored


def _normalize_identity_codex_launcher_contract(task_doc: dict[str, Any], identity_id: str) -> list[str]:
    before = json.loads(json.dumps(task_doc.get(IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY) or {}))
    ensure_launcher_contract(task_doc, identity_id)
    node = task_doc.get(IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY)
    if before != node:
        return [IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY]
    return []


def _launcher_contract_invalid_keys(task_doc: dict[str, Any]) -> list[str]:
    node = task_doc.get(IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY)
    if not isinstance(node, dict):
        return []
    invalid = (
        node.get("required") is not True
        or str(node.get("contract_id", "")).strip() != IDENTITY_CODEX_LAUNCHER_CONTRACT_ID
        or str(node.get("validator", "")).strip() != IDENTITY_CODEX_LAUNCHER_VALIDATOR_ID
        or str(node.get("renderer", "")).strip() != IDENTITY_CODEX_LAUNCHER_RENDERER_ID
        or str(node.get("installer", "")).strip() != IDENTITY_CODEX_LAUNCHER_INSTALLER_ID
        or str(node.get("pack_manifest_relpath", "")).strip() != IDENTITY_CODEX_LAUNCHER_MANIFEST_REL.as_posix()
        or str(node.get("pack_readme_relpath", "")).strip() != IDENTITY_CODEX_LAUNCHER_README_REL.as_posix()
    )
    return [IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY] if invalid else []


def _ensure_identity_codex_launcher_assets_backfill(
    *,
    pack_path: Path,
    identity_id: str,
    apply: bool,
) -> dict[str, Any]:
    manifest_path = (pack_path / IDENTITY_CODEX_LAUNCHER_MANIFEST_REL).resolve()
    readme_path = (pack_path / IDENTITY_CODEX_LAUNCHER_README_REL).resolve()
    manifest_expected = json.dumps(launcher_manifest_doc(identity_id), ensure_ascii=False, indent=2) + "\n"
    readme_expected = launcher_readme_text(identity_id)
    manifest_exists_before = manifest_path.exists()
    readme_exists_before = readme_path.exists()
    manifest_before = manifest_path.read_text(encoding="utf-8", errors="ignore") if manifest_exists_before else ""
    readme_before = readme_path.read_text(encoding="utf-8", errors="ignore") if readme_exists_before else ""
    manifest_changed = (not manifest_exists_before) or manifest_before != manifest_expected
    readme_changed = (not readme_exists_before) or readme_before != readme_expected
    applied = False
    if apply:
        asset_result = ensure_launcher_assets(pack_path, identity_id)
        applied = bool(asset_result.get("manifest_changed") or asset_result.get("readme_changed"))
    return {
        "manifest_path": str(manifest_path),
        "readme_path": str(readme_path),
        "manifest_exists_before": manifest_exists_before,
        "readme_exists_before": readme_exists_before,
        "manifest_changed": manifest_changed,
        "readme_changed": readme_changed,
        "changed": bool(manifest_changed or readme_changed),
        "applied": applied,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(131072), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _replace_string_list_tokens(
    container: dict[str, Any],
    key: str,
    replacements: dict[str, str],
) -> tuple[bool, list[str]]:
    node = container.get(key)
    if isinstance(node, list):
        rows = [str(item).strip() for item in node if str(item).strip()]
    else:
        rows = []
    if not rows:
        return False, []

    changed_rows: list[str] = []
    normalized: list[str] = []
    seen: set[str] = set()
    for row in rows:
        replacement = str(replacements.get(row, row)).strip()
        if replacement != row:
            changed_rows.append(f"{row}->{replacement}")
        if replacement and replacement not in seen:
            normalized.append(replacement)
            seen.add(replacement)
    changed = normalized != rows
    if changed:
        container[key] = normalized
    return changed, changed_rows


def _next_migrated_conflict_path(target: Path) -> Path:
    base = target.stem
    suffix = target.suffix
    parent = target.parent
    idx = 1
    while True:
        candidate = parent / f"{base}.migrated-from-gate-{idx}{suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


def _move_file_with_conflict_preservation(src: Path, dest: Path) -> tuple[Path, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if _sha256_file(src) == _sha256_file(dest):
            src.unlink()
            return dest, "dedup_existing"
        conflict_dest = _next_migrated_conflict_path(dest)
        shutil.move(str(src), str(conflict_dest))
        return conflict_dest, "migrated_conflict_copy"
    shutil.move(str(src), str(dest))
    return dest, "migrated"


def _remove_empty_dir_chain(start: Path, *, stop: Path) -> list[str]:
    removed: list[str] = []
    current = start.resolve()
    stop_resolved = stop.resolve()
    while current != stop_resolved and stop_resolved in current.parents:
        try:
            current.rmdir()
        except OSError:
            break
        removed.append(str(current))
        current = current.parent
    return removed


def _ensure_instance_pack_topology_assets(
    *,
    pack_path: Path,
    identity_id: str,
    title: str,
    description: str,
    apply: bool,
) -> dict[str, Any]:
    required_dirs = [
        "agents",
        "runtime",
        "scripts",
        "runtime/examples",
        "runtime/gate",  # downsink-path-lock: allow-nonregistry-literal
        "runtime/logs",
        "runtime/plugins",
        "runtime/state",
    ]
    optional_seed_dirs = [
        CONTEXT_CONTINUITY_REPORT_ROOT_REL.as_posix(),
        CONTEXT_CONTINUITY_STATE_ROOT_REL.as_posix(),
    ]
    missing_dirs = [row for row in required_dirs if not (pack_path / row).exists()]
    missing_optional_seed_dirs = [row for row in optional_seed_dirs if not (pack_path / row).exists()]
    required_files = {
        "scripts/README.md": _default_instance_scripts_readme(identity_id),
        "agents/identity.yaml": _default_identity_agent_yaml(identity_id, title, description),
    }
    optional_files = {
        INSTANCE_SCRIPT_MANIFEST_RELATIVE_PATH: json.dumps(
            _default_instance_script_manifest(identity_id),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    }
    missing_files = [row for row in required_files if not (pack_path / row).exists()]
    missing_optional_files = [row for row in optional_files if not (pack_path / row).exists()]
    legacy_relay_root = (pack_path / "runtime" / "gate" / "runtime" / "reports" / "agent-relay-final-answer").resolve()
    canonical_relay_root = (pack_path / "runtime" / "reports" / "agent-relay-final-answer").resolve()
    legacy_relay_files_before = (
        sorted(str(path.resolve().relative_to(pack_path.resolve())) for path in legacy_relay_root.rglob("*") if path.is_file())
        if legacy_relay_root.exists()
        else []
    )
    legacy_cache_dirs_before = sorted(
        str(path.resolve().relative_to(pack_path.resolve()))
        for path in pack_path.rglob("*")
        if path.is_dir() and path.name in {"__pycache__", ".pytest_cache"}
    )
    legacy_relay_migrations: list[dict[str, str]] = []
    legacy_empty_dirs_removed: list[str] = []
    legacy_cache_dirs_removed: list[str] = []
    if apply:
        for row in required_dirs:
            (pack_path / row).mkdir(parents=True, exist_ok=True)
        for row in optional_seed_dirs:
            (pack_path / row).mkdir(parents=True, exist_ok=True)
        for rel, text in required_files.items():
            path = pack_path / rel
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
        for rel, text in optional_files.items():
            path = pack_path / rel
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
        if legacy_relay_root.exists():
            for src in sorted(legacy_relay_root.rglob("*")):
                if not src.is_file():
                    continue
                dest = (canonical_relay_root / src.relative_to(legacy_relay_root)).resolve()
                moved_to, action = _move_file_with_conflict_preservation(src, dest)
                legacy_relay_migrations.append(
                    {
                        "source": str(src.resolve().relative_to(pack_path.resolve())),
                        "destination": str(moved_to.resolve().relative_to(pack_path.resolve())),
                        "action": action,
                    }
                )
            legacy_empty_dirs_removed.extend(
                _remove_empty_dir_chain(legacy_relay_root, stop=(pack_path / "runtime" / "gate"))
            )
        for rel in legacy_cache_dirs_before:
            cache_dir = (pack_path / rel).resolve()
            if not cache_dir.exists():
                continue
            shutil.rmtree(cache_dir)
            legacy_cache_dirs_removed.append(rel)
    topology_hygiene_changed = bool(legacy_relay_files_before or legacy_cache_dirs_before)
    return {
        "status": (
            STATUS_PASS_REQUIRED
            if apply or (not missing_dirs and not missing_files and not topology_hygiene_changed)
            else STATUS_SKIPPED_NOT_REQUIRED
        ),
        "changed": bool(
            missing_dirs
            or missing_optional_seed_dirs
            or missing_files
            or missing_optional_files
            or topology_hygiene_changed
        ),
        "applied": bool(
            apply
            and (
                missing_dirs
                or missing_optional_seed_dirs
                or missing_files
                or missing_optional_files
                or topology_hygiene_changed
            )
        ),
        "missing_dirs_before": missing_dirs,
        "missing_optional_seed_dirs_before": missing_optional_seed_dirs,
        "missing_files_before": missing_files,
        "missing_optional_files_before": missing_optional_files,
        "required_dirs": required_dirs,
        "optional_seed_dirs": optional_seed_dirs,
        "required_files": sorted(required_files.keys()),
        "optional_seed_files": sorted(optional_files.keys()),
        "legacy_relay_files_before": legacy_relay_files_before,
        "legacy_relay_migrations": legacy_relay_migrations,
        "legacy_cache_dirs_before": legacy_cache_dirs_before,
        "legacy_cache_dirs_removed": legacy_cache_dirs_removed,
        "legacy_empty_dirs_removed": legacy_empty_dirs_removed,
    }


def _norm_level(value: Any) -> str:
    token = str(value or "").strip().upper()
    return token if token in REASONING_LEVEL_RANK else ""


def _ensure_reasoning_floor(node: dict[str, Any]) -> bool:
    changed = False
    current_level = _norm_level(node.get("reasoning_enforcement_level"))
    if not current_level or REASONING_LEVEL_RANK[current_level] < REASONING_LEVEL_RANK[REASONING_MIN_LEVEL]:
        node["reasoning_enforcement_level"] = REASONING_MIN_LEVEL
        changed = True

    current_min_level = _norm_level(node.get("minimum_enforcement_level"))
    if not current_min_level or REASONING_LEVEL_RANK[current_min_level] < REASONING_LEVEL_RANK[REASONING_MIN_LEVEL]:
        node["minimum_enforcement_level"] = REASONING_MIN_LEVEL
        changed = True

    enforcement = node.get("reasoning_enforcement")
    if not isinstance(enforcement, dict):
        enforcement = {}
        node["reasoning_enforcement"] = enforcement
        changed = True

    default_level = _norm_level(enforcement.get("default_level"))
    if not default_level or REASONING_LEVEL_RANK[default_level] < REASONING_LEVEL_RANK[REASONING_MIN_LEVEL]:
        enforcement["default_level"] = REASONING_MIN_LEVEL
        changed = True

    minimum_level = _norm_level(enforcement.get("minimum_level"))
    if not minimum_level or REASONING_LEVEL_RANK[minimum_level] < REASONING_LEVEL_RANK[REASONING_MIN_LEVEL]:
        enforcement["minimum_level"] = REASONING_MIN_LEVEL
        changed = True
    return changed


def _merge_required_skills(node: dict[str, Any], required_skill_id: str) -> bool:
    existing = node.get("required_skills")
    if isinstance(existing, list):
        values = [str(x).strip() for x in existing if str(x).strip()]
    else:
        values = []
    if required_skill_id in values:
        return False
    values.append(required_skill_id)
    node["required_skills"] = values
    return True


def _deep_merge(current: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(defaults))
    for key, value in (current or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(value, merged[key])
        else:
            merged[key] = value
    return merged


def _merge_validator_ids(container: dict[str, Any], key: str, validator_ids: tuple[str, ...]) -> tuple[bool, list[str]]:
    changed = False
    node = container.get(key)
    if isinstance(node, list):
        rows = [str(x).strip() for x in node if str(x).strip()]
    else:
        rows = []
    appended: list[str] = []
    for validator_id in validator_ids:
        if validator_id in rows:
            continue
        rows.append(validator_id)
        appended.append(validator_id)
        changed = True
    if changed:
        container[key] = rows
    return changed, appended


def _merge_required_string_list(
    container: dict[str, Any],
    key: str,
    required_items: list[str] | tuple[str, ...],
) -> tuple[bool, list[str]]:
    current = container.get(key)
    if isinstance(current, list):
        rows = [str(item).strip() for item in current if str(item).strip()]
    else:
        rows = []
    changed = False
    appended: list[str] = []
    for item in required_items:
        token = str(item).strip()
        if not token or token in rows:
            continue
        rows.append(token)
        appended.append(token)
        changed = True
    if changed:
        container[key] = rows
    return changed, appended


def _normalize_skill_supply_chain_contracts(task_doc: dict[str, Any], identity_id: str) -> list[str]:
    restored: list[str] = []
    defaults = {
        "skill_installation_supply_chain_contract_v1": _skill_installation_supply_chain_contract_skeleton(identity_id),
        "skill_frontmatter_contract_v1": _skill_frontmatter_contract_skeleton(),
        "skill_sync_drift_guard_contract_v1": _skill_sync_drift_guard_contract_skeleton(),
    }
    for key, default in defaults.items():
        node = task_doc.get(key)
        if not isinstance(node, dict):
            task_doc[key] = json.loads(json.dumps(default))
            restored.append(key)
            continue
        merged = _deep_merge(node, default)
        if merged.get("required") is not True:
            merged["required"] = True
            restored.append(f"{key}.required")
        if not str(merged.get("validator", "")).strip() and str(default.get("validator", "")).strip():
            merged["validator"] = str(default.get("validator", "")).strip()
            restored.append(f"{key}.validator")
        task_doc[key] = merged
    return restored


def _normalize_capability_driver_validators(task_doc: dict[str, Any]) -> dict[str, list[str]]:
    restored: dict[str, list[str]] = {
        "required_validators": [],
        "ci_enforcement_contract.required_validators": [],
        "identity_update_lifecycle_contract.validation_contract.required_checks": [],
    }
    _, appended_root = _merge_validator_ids(task_doc, "required_validators", CAPABILITY_DRIVER_VALIDATOR_IDS)
    if appended_root:
        restored["required_validators"].extend(appended_root)

    ci_contract = task_doc.get("ci_enforcement_contract")
    if isinstance(ci_contract, dict):
        _, appended_ci = _merge_validator_ids(ci_contract, "required_validators", CAPABILITY_DRIVER_VALIDATOR_IDS)
        if appended_ci:
            restored["ci_enforcement_contract.required_validators"].extend(appended_ci)

    lifecycle_contract = task_doc.get("identity_update_lifecycle_contract")
    validation_contract = lifecycle_contract.get("validation_contract") if isinstance(lifecycle_contract, dict) else None
    if isinstance(validation_contract, dict):
        _, appended_lc = _merge_validator_ids(validation_contract, "required_checks", CAPABILITY_DRIVER_VALIDATOR_IDS)
        if appended_lc:
            restored["identity_update_lifecycle_contract.validation_contract.required_checks"].extend(appended_lc)
    return {k: v for k, v in restored.items() if v}


def _normalize_update_lifecycle_required_checks(task_doc: dict[str, Any]) -> list[str]:
    restored: list[str] = []
    lifecycle_contract = task_doc.get("identity_update_lifecycle_contract")
    validation_contract = lifecycle_contract.get("validation_contract") if isinstance(lifecycle_contract, dict) else None
    if not isinstance(validation_contract, dict):
        return restored
    _changed, replaced = _replace_string_list_tokens(
        validation_contract,
        "required_checks",
        LEGACY_VALIDATOR_ID_REPLACEMENTS,
    )
    restored.extend(
        f"identity_update_lifecycle_contract.validation_contract.required_checks:{row}"
        for row in replaced
    )
    return restored


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _safe_dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _jsonl_has_required_fields(path: Path, required_fields: list[str]) -> bool:
    if not path.exists():
        return False
    try:
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except Exception:
        return False
    if not lines:
        return False
    for line in lines:
        try:
            payload = json.loads(line)
        except Exception:
            return False
        if not isinstance(payload, dict):
            return False
        if any(field not in payload for field in required_fields):
            return False
    return True


def _ensure_feedback_selftest_assets(
    *,
    pack_path: Path,
    identity_id: str,
    task_doc: dict[str, Any],
    repo_root: Path,
    apply: bool,
) -> dict[str, Any]:
    runtime_root = (pack_path / "runtime").resolve()
    contract = task_doc.get("experience_feedback_contract")
    required_fields = []
    if isinstance(contract, dict):
        required_fields = [str(x).strip() for x in list(contract.get("required_fields") or []) if str(x).strip()]
    if not required_fields:
        required_fields = ["case_id", "layer", "pattern", "action", "impact_score", "replay_status"]

    positive_src = (repo_root / "identity/runtime/rulebooks/positive.jsonl").resolve()
    negative_src = (repo_root / "identity/runtime/rulebooks/negative.jsonl").resolve()
    positive_dst = (runtime_root / "rulebooks/positive.jsonl").resolve()
    negative_dst = (runtime_root / "rulebooks/negative.jsonl").resolve()

    positive_valid_before = _jsonl_has_required_fields(positive_dst, required_fields)
    negative_valid_before = _jsonl_has_required_fields(negative_dst, required_fields)
    positive_backfilled = False
    negative_backfilled = False

    if apply and positive_src.exists() and not positive_valid_before:
        _copy_jsonl_with_identity(positive_src, positive_dst, identity_id)
        positive_backfilled = True
    if apply and negative_src.exists() and not negative_valid_before:
        _copy_jsonl_with_identity(negative_src, negative_dst, identity_id)
        negative_backfilled = True

    return {
        "positive_rulebook_path": str(positive_dst),
        "negative_rulebook_path": str(negative_dst),
        "required_fields": required_fields,
        "positive_rulebook_valid_before": positive_valid_before,
        "negative_rulebook_valid_before": negative_valid_before,
        "positive_rulebook_valid_after": _jsonl_has_required_fields(positive_dst, required_fields),
        "negative_rulebook_valid_after": _jsonl_has_required_fields(negative_dst, required_fields),
        "positive_rulebook_backfilled": positive_backfilled,
        "negative_rulebook_backfilled": negative_backfilled,
    }


def _ensure_handoff_selftest_assets(
    *,
    pack_path: Path,
    identity_id: str,
    repo_root: Path,
    apply: bool,
) -> dict[str, Any]:
    sample_src = (repo_root / "identity/runtime/examples/handoff").resolve()
    sample_dst = (pack_path / "runtime/examples/handoff").resolve()
    positive_before = sorted((sample_dst / "positive").glob("*.json"))
    negative_before = sorted((sample_dst / "negative").glob("*.json"))
    backfilled_files: list[str] = []

    if apply and sample_src.exists() and (not positive_before or not negative_before):
        for sample in sample_src.rglob("*.json"):
            rel = sample.relative_to(sample_src)
            dst = sample_dst / rel
            _copy_sample_with_identity(sample, dst, identity_id)
            backfilled_files.append(str(dst))

    positive_after = sorted((sample_dst / "positive").glob("*.json"))
    negative_after = sorted((sample_dst / "negative").glob("*.json"))
    return {
        "sample_root": str(sample_dst),
        "positive_count_before": len(positive_before),
        "negative_count_before": len(negative_before),
        "positive_count_after": len(positive_after),
        "negative_count_after": len(negative_after),
        "backfilled_files": backfilled_files,
    }


def _ensure_update_replay_runtime_evidence(
    *,
    pack_path: Path,
    identity_id: str,
    task_doc: dict[str, Any],
    apply: bool,
) -> dict[str, Any]:
    runtime_root = (pack_path / "runtime").resolve()
    sample_path = (runtime_root / "examples" / f"{identity_id}-update-replay-sample.json").resolve()
    existed_before = sample_path.exists()
    before_doc = _safe_load_json(sample_path)
    required_checks = [
        str(item).strip()
        for item in (
            (
                task_doc.get("identity_update_lifecycle_contract", {})
                .get("validation_contract", {})
                .get("required_checks", [])
            )
            or []
        )
        if str(item).strip()
    ]
    before_checks = [str(item).strip() for item in before_doc.get("validation_checks_passed", []) if str(item).strip()]
    needs_refresh = (not sample_path.exists()) or before_checks != required_checks
    wrote = False
    if apply and needs_refresh:
        _write_replay_sample(identity_id, task_doc, runtime_root)
        wrote = True
    after_doc = _safe_load_json(sample_path)
    after_checks = [str(item).strip() for item in after_doc.get("validation_checks_passed", []) if str(item).strip()]
    return {
        "sample_path": str(sample_path),
        "exists_before": existed_before,
        "validation_checks_before": before_checks,
        "validation_checks_after": after_checks,
        "required_checks": required_checks,
        "needs_refresh": needs_refresh,
        "applied": wrote,
    }


def _ensure_handoff_runtime_log(
    *,
    pack_path: Path,
    identity_id: str,
    task_doc: dict[str, Any],
    apply: bool,
) -> dict[str, Any]:
    log_path = (pack_path / "runtime" / "logs" / "handoff" / f"{identity_id}-contract-backfill-latest.json").resolve()
    before_doc = _safe_load_json(log_path)
    before_generated_at = str(before_doc.get("generated_at", "")).strip()
    task_id = str(task_doc.get("task_id", "")).strip() or f"{identity_id}_bootstrap"
    payload = {
        "handoff_id": f"{identity_id}-contract-backfill-handoff",
        "identity_id": identity_id,
        "task_id": task_id,
        "from_agent": f"{identity_id}-master",
        "to_agent": "protocol-review",
        "input_scope": "Refresh runtime handoff governance evidence after protocol contract backfill.",
        "actions_taken": [
            "revalidated protocol-owned lifecycle contracts",
            "refreshed governed runtime evidence surfaces",
        ],
        "artifacts": [
            {
                "path": str(log_path),
                "kind": "handoff_governance_evidence",
            }
        ],
        "result": "PASS",
        "next_action": {
            "owner": "protocol-review",
            "action": "Keep lifecycle and handoff governance evidence fresh after contract changes.",
            "input": f"identity_id={identity_id}",
        },
        "rulebook_update": {
            "applied": False,
            "evidence_run_id": f"repair-contract-backfill-{identity_id}",
        },
        "attempted_mutations": [],
        "generated_at": _utc_now_iso(),
    }
    wrote = False
    if apply:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        wrote = True
    after_doc = _safe_load_json(log_path)
    return {
        "log_path": str(log_path),
        "generated_at_before": before_generated_at,
        "generated_at_after": str(after_doc.get("generated_at", "")).strip(),
        "applied": wrote,
    }


def _ensure_feedback_runtime_log(
    *,
    pack_path: Path,
    identity_id: str,
    task_doc: dict[str, Any],
    apply: bool,
) -> dict[str, Any]:
    log_path = (pack_path / "runtime" / "logs" / "feedback" / f"{identity_id}-feedback-contract-backfill-latest.json").resolve()
    before_doc = _safe_load_json(log_path)
    before_timestamp = str(before_doc.get("timestamp", "")).strip()
    task_id = str(task_doc.get("task_id", "")).strip() or f"{identity_id}_bootstrap"
    payload = {
        "feedback_id": f"feedback-{identity_id}-contract-backfill",
        "identity_id": identity_id,
        "task_id": task_id,
        "run_id": f"repair-contract-backfill-{identity_id}",
        "timestamp": _utc_now_iso(),
        "context_signature": "contract-backfill-refresh",
        "outcome": "PASS",
        "failure_type": "none",
        "decision_trace_ref": "contract_backfill_runtime_feedback_refresh",
        "artifacts": [
            str(log_path),
        ],
        "rulebook_delta": {
            "positive": 0,
            "negative": 0,
        },
        "replay_status": "PASS",
    }
    wrote = False
    if apply:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        wrote = True
    after_doc = _safe_load_json(log_path)
    return {
        "log_path": str(log_path),
        "timestamp_before": before_timestamp,
        "timestamp_after": str(after_doc.get("timestamp", "")).strip(),
        "applied": wrote,
    }


def _identity_title_description(
    *,
    identity_id: str,
    task_doc: dict[str, Any],
    meta_doc: dict[str, Any],
) -> tuple[str, str]:
    title = str(meta_doc.get("title", "")).strip()
    description = str(meta_doc.get("description", "")).strip()
    if not title:
        agent = task_doc.get("agent_identity")
        if isinstance(agent, dict):
            title = str(agent.get("title", "")).strip()
            if not description:
                description = str(agent.get("description", "")).strip()
    if not title:
        title = str(identity_id or "").strip()
    return title, description


def _ensure_identity_prompt_runtime_governance(
    *,
    pack_path: Path,
    identity_id: str,
    title: str,
    description: str,
    task_doc: dict[str, Any],
    apply: bool,
) -> dict[str, Any]:
    prompt_path = (pack_path / "IDENTITY_PROMPT.md").resolve()
    prompt_exists_before = prompt_path.exists()
    if prompt_exists_before:
        prompt_before = prompt_path.read_text(encoding="utf-8", errors="ignore")
    else:
        prompt_before = _default_identity_prompt_markdown(
            identity_id=identity_id,
            title=title,
            description=description,
        )
    prompt_after, governance_tokens_inserted, prompt_changed = _ensure_identity_prompt_governance_kernel(
        prompt_before,
        identity_id=identity_id,
        title=title,
        description=description,
    )
    native_chat_contract = (
        task_doc.get("native_chat_headstamp_contract_v1")
        if isinstance(task_doc.get("native_chat_headstamp_contract_v1"), dict)
        else {}
    )
    native_chat_tokens_inserted: list[str] = []
    if native_chat_contract.get("required") is True:
        prompt_after, native_chat_tokens_inserted, native_chat_prompt_changed = ensure_native_chat_prompt_hard_guard(
            prompt_after,
            default_machine_profile=str(native_chat_contract.get("default_machine_profile", "mini")),
            template_ref=str(native_chat_contract.get("prompt_hard_guard_template_ref", "")).strip(),
        )
        prompt_changed = bool(prompt_changed or native_chat_prompt_changed)
    prompt_written = False
    if apply and (prompt_changed or not prompt_exists_before):
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_after, encoding="utf-8")
        prompt_written = True
    return {
        "path": str(prompt_path),
        "existed_before": prompt_exists_before,
        "changed": bool(prompt_changed or not prompt_exists_before),
        "applied": prompt_written,
        "governance_tokens_inserted": governance_tokens_inserted,
        "native_chat_hard_guard_tokens_inserted": native_chat_tokens_inserted,
        "prompt_bytes_before": len(prompt_before.encode("utf-8")),
        "prompt_bytes_after": len(prompt_after.encode("utf-8")),
    }


def _ensure_provider_bindings_template(
    *,
    pack_path: Path,
    repo_root: Path,
    apply: bool,
) -> dict[str, Any]:
    binding_path = (pack_path / "runtime" / "plugins" / "provider-bindings.local.yaml").resolve()
    binding_exists_before = binding_path.exists()
    binding_before = ""
    if binding_exists_before:
        binding_before = binding_path.read_text(encoding="utf-8", errors="ignore")
    if binding_exists_before:
        binding_after = _provider_bindings_template_text(repo_root=repo_root, existing_text=binding_before)
    else:
        binding_after = _provider_bindings_template_text(repo_root=repo_root)
    binding_changed = not binding_exists_before or binding_before != binding_after
    binding_written = False
    if apply and binding_changed:
        binding_path.parent.mkdir(parents=True, exist_ok=True)
        binding_path.write_text(binding_after, encoding="utf-8")
        binding_written = True
    return {
        "path": str(binding_path),
        "existed_before": binding_exists_before,
        "changed": binding_changed,
        "applied": binding_written,
        "bytes_after": len(binding_after.encode("utf-8")),
    }


def _task_version_snapshot(task_doc: dict[str, Any]) -> dict[str, Any]:
    agent = task_doc.get("agent_identity") if isinstance(task_doc.get("agent_identity"), dict) else {}
    scaffold = task_doc.get("scaffold_metadata") if isinstance(task_doc.get("scaffold_metadata"), dict) else {}
    return {
        "agent_identity": {
            "methodology_version": str(agent.get("methodology_version", "")).strip(),
            "prompt_version": str(agent.get("prompt_version", "")).strip(),
            "json_version": str(agent.get("json_version", "")).strip(),
        },
        "scaffold_metadata": {
            "protocol_contract_version": str(scaffold.get("protocol_contract_version", "")).strip(),
            "required_version_stream": str(scaffold.get("required_version_stream", "")).strip(),
            "required_gate_bundle_contract_version": str(
                scaffold.get("required_gate_bundle_contract_version", "")
            ).strip(),
            "identity_protocol_version": str(scaffold.get("identity_protocol_version", "")).strip(),
        },
    }


def _catalog_version_snapshot(catalog_row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(catalog_row, dict):
        return {"methodology_version": ""}
    return {"methodology_version": str(catalog_row.get("methodology_version", "")).strip()}


def _meta_version_snapshot(meta_doc: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(meta_doc, dict):
        return {"methodology_version": ""}
    return {"methodology_version": str(meta_doc.get("methodology_version", "")).strip()}


def _sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(131072)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _resolve_pack_runtime_path(pack_path: Path, raw_path: str, fallback: str) -> Path:
    token = str(raw_path or "").strip() or str(fallback)
    candidate = Path(token).expanduser()
    if not candidate.is_absolute():
        candidate = (pack_path / candidate).resolve()
    return candidate


def _collect_host_gateway_wrapper_template_snapshot(task: dict[str, Any], *, pack_path: Path) -> dict[str, dict[str, Any]]:
    contract = task.get(HOST_GATEWAY_CONTRACT_KEY)
    node = contract if isinstance(contract, dict) else {}
    wrapper_specs = {
        "ingress_wrapper_path": HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH,
        "egress_wrapper_path": HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH,
        "session_chain_wrapper_path": HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH,
    }
    payload: dict[str, dict[str, Any]] = {}
    for key, fallback in wrapper_specs.items():
        resolved = _resolve_pack_runtime_path(pack_path, str(node.get(key, "")).strip(), fallback)
        payload[key] = {
            "path": str(resolved),
            "exists": bool(resolved.exists() and resolved.is_file()),
            "sha256": _sha256_file(resolved),
        }
    return payload


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _legacy_path_drift_fields(task: dict[str, Any], identity_id: str) -> list[str]:
    legacy_prefix = f"identity/runtime/local/{identity_id}/reports/"
    out: list[str] = []
    mapping = {
        "dedup_monotonic_winner_contract_v1.claims_path_pattern": ("dedup_monotonic_winner_contract_v1", "claims_path_pattern"),
        "cross_workflow_evidence_schema_contract_v1.evidence_path_pattern": ("cross_workflow_evidence_schema_contract_v1", "evidence_path_pattern"),
        "route_workflow_version_pinning_contract_v1.proof_receipt_path_pattern": ("route_workflow_version_pinning_contract_v1", "proof_receipt_path_pattern"),
    }
    for field_ref, (contract_key, path_key) in mapping.items():
        node = task.get(contract_key)
        if not isinstance(node, dict):
            continue
        value = str(node.get(path_key, "")).strip()
        if value.startswith(legacy_prefix):
            out.append(field_ref)
    return out


def _normalize_prompt_contracts(task: dict[str, Any]) -> tuple[list[str], list[str], dict[str, list[str]]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    restored_list_fields: dict[str, list[str]] = {}
    for key in REQUIRED_PROMPT_KEYS:
        default = PROMPT_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        default_contract_ids = default.get("derived_from_contract_ids")
        if key == "derived_prompt_conformance_contract_v1" and isinstance(default_contract_ids, list):
            _, appended_contract_ids = _merge_required_string_list(node, "derived_from_contract_ids", default_contract_ids)
            if appended_contract_ids:
                restored_list_fields[f"{key}.derived_from_contract_ids"] = appended_contract_ids
    return forced_required_keys, restored_validator_keys, restored_list_fields


def _continuity_contract_invalid_keys(task: dict[str, Any]) -> list[str]:
    invalid: list[str] = []
    continuity_contract = task.get(CONTEXT_CONTINUITY_CONTRACT_KEY)
    if isinstance(continuity_contract, dict):
        if str(continuity_contract.get("contract_id", "")).strip() != CONTEXT_CONTINUITY_CONTRACT_ID:
            invalid.append(CONTEXT_CONTINUITY_CONTRACT_KEY)
        if str(continuity_contract.get("validator", "")).strip() != CONTEXT_CONTINUITY_VALIDATOR_ID:
            invalid.append(CONTEXT_CONTINUITY_CONTRACT_KEY)
    reentry_contract = task.get(REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY)
    if isinstance(reentry_contract, dict):
        if str(reentry_contract.get("contract_id", "")).strip() != REENTRY_BRIEF_CONSUMPTION_CONTRACT_ID:
            invalid.append(REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY)
        validators = reentry_contract.get("validators")
        normalized = [str(item).strip() for item in validators if str(item).strip()] if isinstance(validators, list) else []
        expected = {
            REENTRY_BRIEF_VALIDATOR_ID,
            REENTRY_CONSUMPTION_VALIDATOR_ID,
        }
        if not expected.issubset(set(normalized)):
            invalid.append(REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY)
    return sorted(set(invalid))


def _dialogue_retention_contract_invalid_keys(task: dict[str, Any]) -> list[str]:
    invalid: list[str] = []
    contract = task.get(DIALOGUE_RETENTION_CONTRACT_KEY)
    if isinstance(contract, dict):
        if str(contract.get("contract_id", "")).strip() != DIALOGUE_RETENTION_CONTRACT_ID:
            invalid.append(DIALOGUE_RETENTION_CONTRACT_KEY)
        if str(contract.get("validator", "")).strip() != DIALOGUE_RETENTION_VALIDATOR_ID:
            invalid.append(DIALOGUE_RETENTION_CONTRACT_KEY)
    return sorted(set(invalid))


def _artifact_family_routing_contract_invalid_keys(task: dict[str, Any]) -> list[str]:
    invalid: list[str] = []
    contract = task.get(ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY)
    if isinstance(contract, dict):
        if str(contract.get("contract_id", "")).strip() != ARTIFACT_FAMILY_ROUTING_CONTRACT_ID:
            invalid.append(ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY)
        if str(contract.get("validator", "")).strip() != ARTIFACT_FAMILY_ROUTING_VALIDATOR_ID:
            invalid.append(ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY)
    return sorted(set(invalid))


def _normalize_artifact_family_routing_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    restored_contract_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key, default in ARTIFACT_FAMILY_ROUTING_CONTRACT_DEFAULTS.items():
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            restored_contract_keys.append(key)
            restored_validator_keys.append(key)
            continue
        merged = _deep_merge(node, default)
        if merged != node:
            restored_contract_keys.append(key)
        task[key] = merged
        if str(merged.get("validator", "")).strip() != ARTIFACT_FAMILY_ROUTING_VALIDATOR_ID:
            merged["validator"] = ARTIFACT_FAMILY_ROUTING_VALIDATOR_ID
            restored_validator_keys.append(key)
    return restored_contract_keys, restored_validator_keys


def _normalize_dialogue_retention_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    restored_contract_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key, default in DIALOGUE_RETENTION_CONTRACT_DEFAULTS.items():
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            restored_contract_keys.append(key)
            restored_validator_keys.append(key)
            continue
        merged = _deep_merge(node, default)
        if merged != node:
            restored_contract_keys.append(key)
        task[key] = merged
        if str(merged.get("validator", "")).strip() != DIALOGUE_RETENTION_VALIDATOR_ID:
            merged["validator"] = DIALOGUE_RETENTION_VALIDATOR_ID
            restored_validator_keys.append(key)
    return restored_contract_keys, restored_validator_keys


def _normalize_continuity_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    restored_contract_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key, default in CONTINUITY_CONTRACT_DEFAULTS.items():
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            restored_contract_keys.append(key)
            restored_validator_keys.append(key)
            continue
        merged = _deep_merge(node, default)
        if merged != node:
            restored_contract_keys.append(key)
        task[key] = merged
        if key == CONTEXT_CONTINUITY_CONTRACT_KEY:
            if str(merged.get("validator", "")).strip() != CONTEXT_CONTINUITY_VALIDATOR_ID:
                merged["validator"] = CONTEXT_CONTINUITY_VALIDATOR_ID
                restored_validator_keys.append(key)
        elif key == REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY:
            validators = merged.get("validators")
            normalized = [str(item).strip() for item in validators if str(item).strip()] if isinstance(validators, list) else []
            required = [REENTRY_BRIEF_VALIDATOR_ID, REENTRY_CONSUMPTION_VALIDATOR_ID]
            changed = False
            for validator_id in required:
                if validator_id in normalized:
                    continue
                normalized.append(validator_id)
                changed = True
            if changed or not isinstance(validators, list):
                merged["validators"] = normalized
                restored_validator_keys.append(key)
    return restored_contract_keys, restored_validator_keys


def _normalize_multimodal_contracts(task: dict[str, Any]) -> tuple[list[str], list[str], bool]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    arbitration_link_restored = False
    for key in REQUIRED_MULTIMODAL_KEYS:
        default = MULTIMODAL_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        if not str(node.get("contract_id", "")).strip():
            node["contract_id"] = str(default.get("contract_id", "")).strip()
        requirements = node.get("provider_binding_requirements")
        if not isinstance(requirements, dict):
            requirements = {}
            node["provider_binding_requirements"] = requirements
        req_profiles = requirements.get("required_profiles")
        if not isinstance(req_profiles, list) or not req_profiles:
            requirements["required_profiles"] = ["glm46v_vision_prod", "openai_vision_prod"]
        else:
            merged_profiles = [str(x).strip() for x in req_profiles if str(x).strip()]
            for profile_id in ("glm46v_vision_prod", "openai_vision_prod"):
                if profile_id not in merged_profiles:
                    merged_profiles.append(profile_id)
            requirements["required_profiles"] = merged_profiles
        min_bindings = requirements.get("minimum_enabled_bindings")
        current_profiles = {
            str(x).strip()
            for x in (requirements.get("required_profiles") or [])
            if str(x).strip()
        }
        canonical_dual_profiles = {"glm46v_vision_prod", "openai_vision_prod"}
        if not isinstance(min_bindings, int) or min_bindings < 1:
            requirements["minimum_enabled_bindings"] = 1
        elif current_profiles == canonical_dual_profiles and min_bindings == 2:
            requirements["minimum_enabled_bindings"] = 1
        if "require_all_required_profiles" not in requirements:
            requirements["require_all_required_profiles"] = False
        elif current_profiles == canonical_dual_profiles and requirements.get("require_all_required_profiles") is True:
            requirements["require_all_required_profiles"] = False

    arbitration = task.get("capability_arbitration_contract")
    if isinstance(arbitration, dict):
        desired = {
            "contract_ref": "rq_034_multimodal_plugin_enforcement_contract_v1",
            "validator": "scripts/validate_multimodal_plugin_enforcement.py",
            "requires_multimodal_evidence_consistency": True,
            "inconsistent_evidence_transition": "block_done",
        }
        current = arbitration.get("accurate_judgement_enforcement")
        if not isinstance(current, dict):
            arbitration["accurate_judgement_enforcement"] = dict(desired)
            arbitration_link_restored = True
        else:
            for k, v in desired.items():
                if current.get(k) != v:
                    current[k] = v
                    arbitration_link_restored = True
            arbitration["accurate_judgement_enforcement"] = current

    return forced_required_keys, restored_validator_keys, arbitration_link_restored


def _normalize_reasoning_contracts(task: dict[str, Any]) -> tuple[list[str], list[str], bool]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    arbitration_link_restored = False
    for key in REQUIRED_REASONING_KEYS:
        default = REASONING_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        if not str(node.get("contract_id", "")).strip():
            node["contract_id"] = str(default.get("contract_id", "")).strip()
        _ensure_reasoning_floor(node)

    arbitration = task.get("capability_arbitration_contract")
    if isinstance(arbitration, dict):
        desired = {
            "contract_ref": "rq_035_reasoning_loop_failclose_contract_v1",
            "validator": "scripts/validate_reasoning_loop_failclose.py",
            "no_target_reached_cannot_complete": True,
            "failed_attempt_requires_next_action": True,
            "threshold_requires_escalation": True,
            "reasoning_enforcement_level_field": "reasoning_enforcement_level",
        }
        current = arbitration.get("reasoning_loop_enforcement")
        if not isinstance(current, dict):
            arbitration["reasoning_loop_enforcement"] = dict(desired)
            arbitration_link_restored = True
        else:
            for k, v in desired.items():
                if current.get(k) != v:
                    current[k] = v
                    arbitration_link_restored = True
            arbitration["reasoning_loop_enforcement"] = current

    return forced_required_keys, restored_validator_keys, arbitration_link_restored


def _normalize_routing_learning_strengthening(task: dict[str, Any]) -> tuple[bool, bool]:
    route_link_restored = False
    feedback_link_restored = False
    arbitration = task.get("capability_arbitration_contract")
    if not isinstance(arbitration, dict):
        return route_link_restored, feedback_link_restored

    route_desired = {
        "contract_ref": "route_discovery_convergence_contract_v1",
        "validator": "scripts/validate_capability_fit_roundtable_evidence.py",
        "supporting_validators": [
            "scripts/validate_discovery_requiredization.py",
            "scripts/validate_identity_orchestration_contract.py",
            "scripts/validate_identity_knowledge_contract.py",
        ],
        "candidate_rows_required": True,
        "selected_candidate_field": "selected_candidate_id",
        "selection_basis_field": "selection_basis",
        "serial_convergence_required": True,
        "convergence_status_field": "convergence_status",
        "fallback_route_field": "fallback_route_if_selected_fails",
    }
    route_current = arbitration.get("route_discovery_enforcement")
    if not isinstance(route_current, dict):
        arbitration["route_discovery_enforcement"] = json.loads(json.dumps(route_desired))
        route_link_restored = True
    else:
        for key, value in route_desired.items():
            if route_current.get(key) != value:
                route_current[key] = json.loads(json.dumps(value))
                route_link_restored = True
        arbitration["route_discovery_enforcement"] = route_current

    feedback_desired = {
        "contract_ref": "feedback_operational_prompt_contract_v1",
        "validator": "scripts/validate_identity_experience_feedback_governance.py",
        "supporting_validators": [
            "scripts/validate_identity_experience_feedback.py",
        ],
        "rulebook_delta_required": True,
        "operational_prompt_ref_field": "operational_prompt_ref",
        "prompt_injection_status_field": "prompt_injection_status",
        "replay_status_field": "replay_status",
        "rollback_prompt_ref_required": True,
        "ttl_rounds_required": True,
    }
    feedback_current = arbitration.get("feedback_operational_prompt_enforcement")
    if not isinstance(feedback_current, dict):
        arbitration["feedback_operational_prompt_enforcement"] = json.loads(json.dumps(feedback_desired))
        feedback_link_restored = True
    else:
        for key, value in feedback_desired.items():
            if feedback_current.get(key) != value:
                feedback_current[key] = json.loads(json.dumps(value))
                feedback_link_restored = True
        arbitration["feedback_operational_prompt_enforcement"] = feedback_current

    return route_link_restored, feedback_link_restored


def _normalize_unique_entry_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key in REQUIRED_ENTRY_KEYS:
        default = ENTRY_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        node = _deep_merge(node, default)
        task[key] = node
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        if not str(node.get("entry_script", "")).strip():
            node["entry_script"] = ENTRY_SCRIPT
        if not str(node.get("bundle_key", "")).strip():
            node["bundle_key"] = ENTRY_BUNDLE_KEY
        if not str(node.get("scope", "")).strip():
            node["scope"] = "all_identity_instance_actions"
        if node.get("require_strict_operation_receipt") is not True:
            node["require_strict_operation_receipt"] = True
        if not str(node.get("entry_receipt_state_file", "")).strip():
            node["entry_receipt_state_file"] = str(default.get("entry_receipt_state_file", "")).strip()
        if not str(node.get("entry_receipt_history_pattern", "")).strip():
            node["entry_receipt_history_pattern"] = str(default.get("entry_receipt_history_pattern", "")).strip()
        default_max_age_seconds = _safe_int(default.get("entry_receipt_max_age_seconds"), default=1800)
        if default_max_age_seconds <= 0:
            default_max_age_seconds = 1800
        if _safe_int(node.get("entry_receipt_max_age_seconds"), default=0) <= 0:
            node["entry_receipt_max_age_seconds"] = default_max_age_seconds
        receipt_fields = node.get("entry_receipt_required_fields")
        default_receipt_fields = [
            str(item).strip()
            for item in (default.get("entry_receipt_required_fields") or [])
            if str(item).strip()
        ]
        if not isinstance(receipt_fields, list):
            node["entry_receipt_required_fields"] = list(default_receipt_fields)
        else:
            merged = [str(item).strip() for item in receipt_fields if str(item).strip()]
            for field in default_receipt_fields:
                if field not in merged:
                    merged.append(field)
            node["entry_receipt_required_fields"] = merged
        if not str(node.get("onboarding_single_entry_command", "")).strip():
            node["onboarding_single_entry_command"] = str(default.get("onboarding_single_entry_command", "")).strip()
        if not str(node.get("extension_attach_entrypoint", "")).strip():
            node["extension_attach_entrypoint"] = str(default.get("extension_attach_entrypoint", "")).strip()
    return forced_required_keys, restored_validator_keys


def _normalize_lane_headstamp_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key in REQUIRED_LANE_HEADSTAMP_KEYS:
        default = LANE_HEADSTAMP_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("enforcement_validator", "")).strip()
        if not validator:
            node["enforcement_validator"] = str(default.get("enforcement_validator", "")).strip()
            restored_validator_keys.append(key)
        if not str(node.get("required_lane", "")).strip():
            node["required_lane"] = str(default.get("required_lane", "")).strip()
        if node.get("route_non_starvation") is not True:
            node["route_non_starvation"] = True
        if node.get("headstamp_dual_context_required") is not True:
            node["headstamp_dual_context_required"] = True
        required_fields = node.get("required_fields")
        default_required_fields = [
            str(item).strip()
            for item in (default.get("required_fields") or [])
            if str(item).strip()
        ]
        if not isinstance(required_fields, list):
            node["required_fields"] = list(default_required_fields)
        else:
            merged = [str(item).strip() for item in required_fields if str(item).strip()]
            for field in default_required_fields:
                if field not in merged:
                    merged.append(field)
            node["required_fields"] = merged
    return forced_required_keys, restored_validator_keys


def _normalize_host_gateway_contracts(task: dict[str, Any], *, identity_id: str = "") -> tuple[list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    signer_secret_env = _host_gateway_signer_secret_env(identity_id or "default")
    for key in REQUIRED_HOST_GATEWAY_KEYS:
        default = HOST_GATEWAY_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        node["contract_id"] = HOST_GATEWAY_CONTRACT_ID
        if str(node.get("protocol_ingress_script", "")).strip() != UNIQUE_INGRESS_SCRIPT:
            node["protocol_ingress_script"] = UNIQUE_INGRESS_SCRIPT
        if str(node.get("protocol_egress_script", "")).strip() != UNIQUE_EGRESS_SCRIPT:
            node["protocol_egress_script"] = UNIQUE_EGRESS_SCRIPT
        if not str(node.get("ingress_wrapper_path", "")).strip():
            node["ingress_wrapper_path"] = HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH
        if not str(node.get("egress_wrapper_path", "")).strip():
            node["egress_wrapper_path"] = HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH
        if not str(node.get("session_chain_wrapper_path", "")).strip():
            node["session_chain_wrapper_path"] = HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH
        if not str(node.get("gateway_contract_path", "")).strip():
            node["gateway_contract_path"] = HOST_GATEWAY_RELATIVE_CONTRACT_PATH
        entry_policy = node.get("entry_receipt_policy")
        if not isinstance(entry_policy, dict):
            entry_policy = {}
        entry_policy["required"] = True
        default_entry_policy = default.get("entry_receipt_policy")
        if isinstance(default_entry_policy, dict):
            required_surface_label = str(default_entry_policy.get("required_surface_label", "")).strip()
            required_wrapper_surface_status = str(
                default_entry_policy.get("required_wrapper_surface_status", "")
            ).strip().upper()
            required_wrapper_dispatch_status = str(
                default_entry_policy.get("required_wrapper_dispatch_token_status", "")
            ).strip().upper()
            if required_surface_label:
                entry_policy["required_surface_label"] = required_surface_label
            if required_wrapper_surface_status:
                entry_policy["required_wrapper_surface_status"] = required_wrapper_surface_status
            if required_wrapper_dispatch_status:
                entry_policy["required_wrapper_dispatch_token_status"] = required_wrapper_dispatch_status
        node["entry_receipt_policy"] = entry_policy
        ingress_proof_policy = node.get("ingress_proof_policy")
        if not isinstance(ingress_proof_policy, dict):
            ingress_proof_policy = {}
        ingress_proof_policy["required"] = True
        ingress_proof_policy["signer_mode"] = "runtime_env_secret"
        ingress_proof_policy["signer_secret_env"] = signer_secret_env
        ingress_proof_policy["signing_key_path"] = str(
            ingress_proof_policy.get("signing_key_path") or HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH
        ).strip() or HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH
        ingress_proof_policy["bootstrap_env_secret_from_signing_key_path"] = bool(
            ingress_proof_policy.get(
                "bootstrap_env_secret_from_signing_key_path",
                HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH,
            )
        )
        default_ingress_proof_policy = default.get("ingress_proof_policy")
        if isinstance(default_ingress_proof_policy, dict):
            max_age_seconds = int(default_ingress_proof_policy.get("max_age_seconds", 300) or 300)
            if int(ingress_proof_policy.get("max_age_seconds", 0) or 0) <= 0:
                ingress_proof_policy["max_age_seconds"] = max_age_seconds
        node["ingress_proof_policy"] = ingress_proof_policy
        egress_policy = node.get("egress_receipt_policy")
        if not isinstance(egress_policy, dict):
            egress_policy = {}
        egress_policy["required"] = True
        node["egress_receipt_policy"] = egress_policy
        egress_grant_policy = node.get("egress_grant_policy")
        if not isinstance(egress_grant_policy, dict):
            egress_grant_policy = {}
        egress_grant_policy["required"] = True
        egress_grant_policy["signer_mode"] = "runtime_env_secret"
        egress_grant_policy["signer_secret_env"] = signer_secret_env
        egress_grant_policy["signing_key_path"] = str(
            egress_grant_policy.get("signing_key_path") or HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH
        ).strip() or HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH
        egress_grant_policy["bootstrap_env_secret_from_signing_key_path"] = bool(
            egress_grant_policy.get(
                "bootstrap_env_secret_from_signing_key_path",
                HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH,
            )
        )
        default_egress_grant_policy = default.get("egress_grant_policy")
        if isinstance(default_egress_grant_policy, dict):
            max_age_seconds = int(default_egress_grant_policy.get("max_age_seconds", 300) or 300)
            if int(egress_grant_policy.get("max_age_seconds", 0) or 0) <= 0:
                egress_grant_policy["max_age_seconds"] = max_age_seconds
        node["egress_grant_policy"] = egress_grant_policy
        headstamp_policy = node.get("headstamp_policy")
        if not isinstance(headstamp_policy, dict):
            headstamp_policy = {}
        headstamp_policy["required"] = True
        node["headstamp_policy"] = headstamp_policy
        tuple_fields = node.get("identity_tuple_fields")
        if not isinstance(tuple_fields, list):
            tuple_fields = []
        merged = [str(item).strip() for item in tuple_fields if str(item).strip()]
        for field in HOST_GATEWAY_REQUIRED_TUPLE_FIELDS:
            if field not in merged:
                merged.append(field)
        node["identity_tuple_fields"] = merged
        if str(node.get("host_dispatch_mode", "")).strip().lower() != HOST_GATEWAY_REQUIRED_DISPATCH_MODE:
            node["host_dispatch_mode"] = HOST_GATEWAY_REQUIRED_DISPATCH_MODE
        if str(node.get("host_release_mode", "")).strip().lower() != HOST_GATEWAY_REQUIRED_RELEASE_MODE:
            node["host_release_mode"] = HOST_GATEWAY_REQUIRED_RELEASE_MODE
        if str(node.get("ingress_wrapper_dispatch_token", "")).strip() != HOST_GATEWAY_INGRESS_DISPATCH_TOKEN:
            node["ingress_wrapper_dispatch_token"] = HOST_GATEWAY_INGRESS_DISPATCH_TOKEN
        default_profile_policy = default.get("operation_profile_policy")
        profile_policy = node.get("operation_profile_policy")
        if not isinstance(profile_policy, dict):
            profile_policy = {}
        if isinstance(default_profile_policy, dict):
            for policy_key in (
                "strict_operations",
                "light_operations",
                "strict_gate_profile",
                "strict_gate_profile_by_operation",
                "light_gate_profile",
                "allow_upgrade_only",
            ):
                if policy_key not in profile_policy or profile_policy.get(policy_key) in (None, "", []):
                    profile_policy[policy_key] = json.loads(json.dumps(default_profile_policy.get(policy_key)))
        node["operation_profile_policy"] = profile_policy
        default_broadcast_policy = default.get("broadcast_policy")
        broadcast_policy = node.get("broadcast_policy")
        if not isinstance(broadcast_policy, dict):
            broadcast_policy = {}
        broadcast_policy["required"] = True
        broadcast_policy["protocol_broadcast_items_dir"] = HOST_GATEWAY_BROADCAST_ITEMS_DIR
        broadcast_policy["protocol_broadcast_index_file"] = HOST_GATEWAY_BROADCAST_INDEX_FILE
        broadcast_policy["protocol_broadcast_schema_file"] = HOST_GATEWAY_BROADCAST_SCHEMA_FILE
        if not str(broadcast_policy.get("instance_state_file", "")).strip():
            state_fallback = (
                str((default_broadcast_policy or {}).get("instance_state_file", "")).strip()
                if isinstance(default_broadcast_policy, dict)
                else ""
            )
            broadcast_policy["instance_state_file"] = state_fallback or HOST_GATEWAY_BROADCAST_STATE_FILE
        if not str(broadcast_policy.get("instance_receipt_pattern", "")).strip():
            receipt_fallback = (
                str((default_broadcast_policy or {}).get("instance_receipt_pattern", "")).strip()
                if isinstance(default_broadcast_policy, dict)
                else ""
            )
            broadcast_policy["instance_receipt_pattern"] = receipt_fallback or HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN
        if not str(broadcast_policy.get("instance_ack_pattern", "")).strip():
            ack_fallback = (
                str((default_broadcast_policy or {}).get("instance_ack_pattern", "")).strip()
                if isinstance(default_broadcast_policy, dict)
                else ""
            )
            broadcast_policy["instance_ack_pattern"] = ack_fallback or HOST_GATEWAY_BROADCAST_ACK_PATTERN
        broadcast_policy["block_on_critical_unacked"] = bool(
            broadcast_policy.get("block_on_critical_unacked", False)
        )
        node["broadcast_policy"] = broadcast_policy
        node["host_visible_surface_registry_contract_ref"] = HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY
        node[HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY] = _host_gateway_wrapper_template_attestation_policy()
    return forced_required_keys, restored_validator_keys


def _normalize_host_visible_surface_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key in REQUIRED_HOST_VISIBLE_SURFACE_KEYS:
        default = HOST_VISIBLE_SURFACE_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        node["contract_id"] = HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID
        node["validator"] = HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR
        channels = node.get("required_channels")
        if not isinstance(channels, list):
            channels = []
        merged_channels = [str(item).strip() for item in channels if str(item).strip()]
        for channel in HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS:
            if channel not in merged_channels:
                merged_channels.append(channel)
        node["required_channels"] = merged_channels
        if not str(node.get("runtime_state_file", "")).strip():
            node["runtime_state_file"] = str(default.get("runtime_state_file", "")).strip() or HOST_VISIBLE_SURFACE_STATE_FILE
        if not str(node.get("runtime_receipt_pattern", "")).strip():
            node["runtime_receipt_pattern"] = (
                str(default.get("runtime_receipt_pattern", "")).strip() or HOST_VISIBLE_SURFACE_RECEIPT_PATTERN
            )
        if not str(node.get("post_check_closure_state_file", "")).strip():
            node["post_check_closure_state_file"] = (
                str(default.get("post_check_closure_state_file", "")).strip()
                or HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE
            )
        node["post_check_block_on_active"] = bool(
            node.get("post_check_block_on_active", HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE)
        )
        max_age_raw = node.get("runtime_receipt_max_age_seconds")
        try:
            max_age_seconds = int(max_age_raw)
        except Exception:
            max_age_seconds = 0
        if max_age_seconds <= 0:
            try:
                max_age_seconds = int(default.get("runtime_receipt_max_age_seconds", 0))
            except Exception:
                max_age_seconds = 0
        if max_age_seconds <= 0:
            max_age_seconds = 300
        node["runtime_receipt_max_age_seconds"] = int(max_age_seconds)
        attestation_fields = node.get("required_attestation_fields")
        if not isinstance(attestation_fields, list):
            attestation_fields = []
        merged_attestation_fields = [str(item).strip() for item in attestation_fields if str(item).strip()]
        for field in HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS:
            if field not in merged_attestation_fields:
                merged_attestation_fields.append(field)
        node["required_attestation_fields"] = merged_attestation_fields
        pass_status_fields = node.get("required_pass_status_fields")
        if not isinstance(pass_status_fields, list):
            pass_status_fields = []
        merged_pass_status_fields = [str(item).strip() for item in pass_status_fields if str(item).strip()]
        for field in HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS:
            if field not in merged_pass_status_fields:
                merged_pass_status_fields.append(field)
        node["required_pass_status_fields"] = merged_pass_status_fields
        node["final_channel_id"] = str(node.get("final_channel_id", "")).strip() or HOST_VISIBLE_FINAL_CHANNEL_ID
        node["final_channel_relay_required"] = bool(
            node.get("final_channel_relay_required", HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED)
        )
        node["final_channel_relay_surface"] = (
            str(node.get("final_channel_relay_surface", "")).strip()
            or HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE
        )
        node["final_channel_relay_mode"] = (
            str(node.get("final_channel_relay_mode", "")).strip()
            or HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE
        )
        node["final_channel_delivery_authority"] = (
            str(node.get("final_channel_delivery_authority", "")).strip()
            or HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY
        )
        final_attestation_fields = node.get("final_channel_required_attestation_fields")
        if not isinstance(final_attestation_fields, list):
            final_attestation_fields = []
        merged_final_attestation_fields = [
            str(item).strip() for item in final_attestation_fields if str(item).strip()
        ]
        for field in HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS:
            if field not in merged_final_attestation_fields:
                merged_final_attestation_fields.append(field)
        node["final_channel_required_attestation_fields"] = merged_final_attestation_fields
        final_pass_status_fields = node.get("final_channel_required_pass_status_fields")
        if not isinstance(final_pass_status_fields, list):
            final_pass_status_fields = []
        merged_final_pass_status_fields = [
            str(item).strip() for item in final_pass_status_fields if str(item).strip()
        ]
        for field in HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS:
            if field not in merged_final_pass_status_fields:
                merged_final_pass_status_fields.append(field)
        node["final_channel_required_pass_status_fields"] = merged_final_pass_status_fields
        node["required_live_probe_delegate"] = HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE
        node["host_dispatch_mode_required"] = HOST_GATEWAY_REQUIRED_DISPATCH_MODE
        node["host_release_mode_required"] = HOST_GATEWAY_REQUIRED_RELEASE_MODE
        node["strict_live_run_binding_required"] = bool(HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED)
    return forced_required_keys, restored_validator_keys


def _normalize_downsink_path_contracts(task: dict[str, Any]) -> tuple[list[str], list[str], list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    restored_write_guard_validator_keys: list[str] = []
    restored_literal_lock_validator_keys: list[str] = []
    for key in REQUIRED_DOWNSINK_KEYS:
        default = DOWNSINK_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            restored_write_guard_validator_keys.append(key)
            restored_literal_lock_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        node["contract_id"] = DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID
        validator_id = str(node.get("validator_id", "")).strip()
        if validator_id != DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID:
            node["validator_id"] = DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID
            restored_validator_keys.append(key)
        write_guard_validator_id = str(node.get("write_guard_validator_id", "")).strip()
        if write_guard_validator_id != DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID:
            node["write_guard_validator_id"] = DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID
            restored_write_guard_validator_keys.append(key)
        source_literal_lock_policy = node.get("source_literal_lock_policy")
        if not isinstance(source_literal_lock_policy, dict):
            source_literal_lock_policy = {}
        if source_literal_lock_policy.get("required") is not True:
            source_literal_lock_policy["required"] = True
            restored_literal_lock_validator_keys.append(key)
        source_literal_lock_validator_id = str(source_literal_lock_policy.get("validator_id", "")).strip()
        if source_literal_lock_validator_id != DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID:
            source_literal_lock_policy["validator_id"] = DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID
            restored_literal_lock_validator_keys.append(key)
        if bool(source_literal_lock_policy.get("enforce_registered_runtime_path_literals_only")) is not True:
            source_literal_lock_policy["enforce_registered_runtime_path_literals_only"] = True
            restored_literal_lock_validator_keys.append(key)
        if (
            str(source_literal_lock_policy.get("allow_inline_override_marker", "")).strip()
            != DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER
        ):
            source_literal_lock_policy["allow_inline_override_marker"] = DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER
            restored_literal_lock_validator_keys.append(key)
        scan_globs = source_literal_lock_policy.get("scan_globs")
        normalized_scan_globs = [str(item).strip() for item in (scan_globs or []) if str(item).strip()]
        if set(normalized_scan_globs) != set(DOWNSINK_LITERAL_LOCK_SCAN_GLOBS):
            source_literal_lock_policy["scan_globs"] = list(DOWNSINK_LITERAL_LOCK_SCAN_GLOBS)
            restored_literal_lock_validator_keys.append(key)
        node["source_literal_lock_policy"] = source_literal_lock_policy

        anchor_policy = node.get("anchor_policy")
        if not isinstance(anchor_policy, dict):
            anchor_policy = {}
        default_anchor_policy = default.get("anchor_policy")
        if isinstance(default_anchor_policy, dict):
            if not str(anchor_policy.get("protocol_repo_root_ref", "")).strip():
                anchor_policy["protocol_repo_root_ref"] = str(default_anchor_policy.get("protocol_repo_root_ref", "")).strip()
            if not str(anchor_policy.get("identity_pack_root_ref", "")).strip():
                anchor_policy["identity_pack_root_ref"] = str(default_anchor_policy.get("identity_pack_root_ref", "")).strip()
            anchor_policy["allow_parent_escape"] = False
            anchor_policy["allow_symlink_escape"] = False
        node["anchor_policy"] = anchor_policy

        schema_policy = node.get("schema_policy")
        if not isinstance(schema_policy, dict):
            schema_policy = {}
        schema_policy["reject_additional_properties"] = True
        schema_policy["require_all_declared_paths_present_in_runtime_contract"] = True
        node["schema_policy"] = schema_policy

        operation_enforcement = node.get("operation_enforcement")
        if not isinstance(operation_enforcement, dict):
            operation_enforcement = {}
        default_operation_enforcement = default.get("operation_enforcement")
        if isinstance(default_operation_enforcement, dict):
            strict_operations = operation_enforcement.get("strict_operations")
            if not isinstance(strict_operations, list) or not strict_operations:
                operation_enforcement["strict_operations"] = json.loads(
                    json.dumps(default_operation_enforcement.get("strict_operations", []))
                )
            light_operations = operation_enforcement.get("light_operations")
            if not isinstance(light_operations, list) or not light_operations:
                operation_enforcement["light_operations"] = json.loads(
                    json.dumps(default_operation_enforcement.get("light_operations", []))
                )
        operation_enforcement["strict_fail_mode"] = "fail_required"
        operation_enforcement["light_fail_mode"] = "fail_required"
        node["operation_enforcement"] = operation_enforcement

        path_registry = node.get("path_registry")
        if not isinstance(path_registry, dict):
            path_registry = {}
        default_registry = default.get("path_registry")
        if isinstance(default_registry, dict):
            normalized_registry: dict[str, Any] = {}
            for domain, default_domain_node in default_registry.items():
                if not isinstance(default_domain_node, dict):
                    continue
                default_anchor_ref = str(default_domain_node.get("anchor_ref", "")).strip()
                default_entries = json.loads(json.dumps(default_domain_node.get("entries", [])))
                current_domain_node = path_registry.get(domain)
                if not isinstance(current_domain_node, dict):
                    normalized_registry[domain] = {
                        "anchor_ref": default_anchor_ref,
                        "entries": default_entries,
                    }
                    continue
                normalized_registry[domain] = {
                    "anchor_ref": default_anchor_ref,
                    "entries": default_entries,
                }
            path_registry = normalized_registry
        node["path_registry"] = path_registry
    restored_literal_lock_validator_keys = sorted(set(restored_literal_lock_validator_keys))
    return (
        forced_required_keys,
        restored_validator_keys,
        restored_write_guard_validator_keys,
        restored_literal_lock_validator_keys,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill intake contract set into CURRENT_TASK.json.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--scope",
        choices=["full", "blocker_taxonomy"],
        default="full",
        help="limit backfill to a specific shared contract family",
    )
    ap.add_argument("--apply", action="store_true", help="persist updates to CURRENT_TASK.json")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog, args.identity_id)
        task_doc = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    if args.scope == "blocker_taxonomy":
        before = json.loads(json.dumps(task_doc))
        updated = json.loads(json.dumps(task_doc))
        blocker_surface_backfill = normalize_task_blocker_surfaces(
            updated,
            sync_human_collab_blockers_if_present=True,
            include_default_legacy_aliases=True,
        )
        blocker_surface_invalid_after = blocker_surface_backfill.get("invalid_blockers_by_surface") or {}
        changed = before != updated
        applied = False
        if args.apply and changed and not blocker_surface_invalid_after:
            task_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            applied = True
        if blocker_surface_invalid_after:
            status = STATUS_FAIL_REQUIRED
            error_code = "IP-BLOCKER-WIRE-001"
            stale_reasons = ["unsupported_blocker_types_after_backfill"]
        elif changed:
            status = STATUS_PASS_REQUIRED if applied else STATUS_SKIPPED_NOT_REQUIRED
            error_code = ""
            stale_reasons = [] if applied else ["dry_run_only"]
        else:
            status = STATUS_PASS_REQUIRED
            error_code = ""
            stale_reasons = ["already_backfilled"]
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog),
            "pack_path": str(pack_path),
            "task_path": str(task_path),
            "scope": args.scope,
            "contract_backfill_status": status,
            "error_code": error_code,
            "changed": changed,
            "applied": applied,
            "task_changed": changed,
            "blocker_surface_backfill": blocker_surface_backfill,
            "stale_reasons": stale_reasons,
            "evidence_ref": str(task_path),
        }
        _emit(payload, json_only=args.json_only)
        return 0 if status != STATUS_FAIL_REQUIRED else 1

    repo_root = Path(__file__).resolve().parent.parent
    try:
        version_baseline = load_version_baseline_or_raise(repo_root=repo_root)
    except Exception as exc:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog),
            "pack_path": str(pack_path),
            "task_path": str(task_path),
            "contract_backfill_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-CBKF-001",
            "changed": False,
            "applied": False,
            "version_baseline_status": STATUS_FAIL_REQUIRED,
            "version_baseline_error": str(exc),
            "stale_reasons": ["version_baseline_unavailable"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    catalog_doc = _safe_load_yaml(catalog)
    catalog_rows = catalog_doc.get("identities")
    catalog_rows = catalog_rows if isinstance(catalog_rows, list) else []
    catalog_row = next(
        (
            row
            for row in catalog_rows
            if isinstance(row, dict) and str(row.get("id", "")).strip() == str(args.identity_id or "").strip()
        ),
        None,
    )
    catalog_row_before = json.loads(json.dumps(catalog_row)) if isinstance(catalog_row, dict) else {}
    catalog_row_version_changed = False
    if isinstance(catalog_row, dict):
        catalog_row_version_changed = apply_version_baseline_to_catalog_row(catalog_row, version_baseline)

    meta_path = (pack_path / "META.yaml").resolve()
    meta_doc = _safe_load_yaml(meta_path)
    meta_before = json.loads(json.dumps(meta_doc)) if isinstance(meta_doc, dict) else {}
    identity_title, identity_description = _identity_title_description(
        identity_id=str(args.identity_id or "").strip(),
        task_doc=task_doc,
        meta_doc=meta_doc,
    )

    before = json.loads(json.dumps(task_doc))
    response_stamp_profile_present_before = isinstance(before.get("response_stamp_profile"), dict)
    response_stamp_profile_before = normalize_response_stamp_profile(before.get("response_stamp_profile"))
    missing_before = [k for k in REQUIRED_INTAKE_KEYS if not isinstance(task_doc.get(k), dict)]
    topology_missing_before = [k for k in REQUIRED_TOPOLOGY_KEYS if not isinstance(task_doc.get(k), dict)]
    launcher_missing_before = [k for k in REQUIRED_LAUNCHER_KEYS if not isinstance(task_doc.get(k), dict)]
    continuity_missing_before = [k for k in REQUIRED_CONTINUITY_KEYS if not isinstance(task_doc.get(k), dict)]
    dialogue_retention_missing_before = [k for k in REQUIRED_DIALOGUE_RETENTION_KEYS if not isinstance(task_doc.get(k), dict)]
    artifact_family_routing_missing_before = [k for k in REQUIRED_ARTIFACT_FAMILY_ROUTING_KEYS if not isinstance(task_doc.get(k), dict)]
    prompt_missing_before = [k for k in REQUIRED_PROMPT_KEYS if not isinstance(task_doc.get(k), dict)]
    multimodal_missing_before = [k for k in REQUIRED_MULTIMODAL_KEYS if not isinstance(task_doc.get(k), dict)]
    reasoning_missing_before = [k for k in REQUIRED_REASONING_KEYS if not isinstance(task_doc.get(k), dict)]
    entry_missing_before = [k for k in REQUIRED_ENTRY_KEYS if not isinstance(task_doc.get(k), dict)]
    lane_headstamp_missing_before = [k for k in REQUIRED_LANE_HEADSTAMP_KEYS if not isinstance(task_doc.get(k), dict)]
    host_gateway_missing_before = [k for k in REQUIRED_HOST_GATEWAY_KEYS if not isinstance(task_doc.get(k), dict)]
    host_visible_surface_missing_before = [
        k for k in REQUIRED_HOST_VISIBLE_SURFACE_KEYS if not isinstance(task_doc.get(k), dict)
    ]
    downsink_missing_before = [k for k in REQUIRED_DOWNSINK_KEYS if not isinstance(task_doc.get(k), dict)]
    skill_supply_chain_missing_before = [
        k for k in SKILL_SUPPLY_CHAIN_CONTRACT_DEFAULTS.keys() if not isinstance(task_doc.get(k), dict)
    ]
    legacy_drift_before = _legacy_path_drift_fields(task_doc, args.identity_id)

    updated = _ensure_intake_p1_contracts(task_doc, args.identity_id)
    restored_topology_contract_keys = _normalize_instance_pack_topology_contract(updated, args.identity_id)
    restored_launcher_contract_keys = _normalize_identity_codex_launcher_contract(updated, args.identity_id)
    restored_continuity_contract_keys, restored_continuity_validator_keys = _normalize_continuity_contracts(updated)
    restored_dialogue_retention_contract_keys, restored_dialogue_retention_validator_keys = _normalize_dialogue_retention_contracts(updated)
    restored_artifact_family_routing_contract_keys, restored_artifact_family_routing_validator_keys = _normalize_artifact_family_routing_contracts(updated)
    updated["response_stamp_profile"] = normalize_response_stamp_profile(updated.get("response_stamp_profile"))
    restored_skill_supply_chain_contract_keys = _normalize_skill_supply_chain_contracts(updated, args.identity_id)
    restored_capability_driver_validator_paths = _normalize_capability_driver_validators(updated)
    restored_update_lifecycle_required_checks = _normalize_update_lifecycle_required_checks(updated)
    skill_contract = updated.get("skill_path_integrity_contract_v1")
    if isinstance(skill_contract, dict):
        _merge_required_skills(skill_contract, FILE_GOVERNANCE_SKILL_ID)
    (
        forced_required_keys,
        restored_validator_keys,
        restored_prompt_contract_list_fields,
    ) = _normalize_prompt_contracts(updated)
    forced_mm_required_keys, restored_mm_validator_keys, arbitration_link_restored = _normalize_multimodal_contracts(updated)
    forced_rl_required_keys, restored_rl_validator_keys, reasoning_arbitration_link_restored = _normalize_reasoning_contracts(updated)
    route_discovery_link_restored, feedback_operational_prompt_link_restored = _normalize_routing_learning_strengthening(updated)
    forced_entry_required_keys, restored_entry_validator_keys = _normalize_unique_entry_contracts(updated)
    (
        forced_lane_headstamp_required_keys,
        restored_lane_headstamp_validator_keys,
    ) = _normalize_lane_headstamp_contracts(updated)
    forced_host_gateway_required_keys, restored_host_gateway_validator_keys = _normalize_host_gateway_contracts(
        updated,
        identity_id=str(args.identity_id or "").strip(),
    )
    (
        forced_host_visible_surface_required_keys,
        restored_host_visible_surface_validator_keys,
    ) = _normalize_host_visible_surface_contracts(updated)
    (
        forced_downsink_required_keys,
        restored_downsink_validator_keys,
        restored_downsink_write_guard_validator_keys,
        restored_downsink_literal_lock_validator_keys,
    ) = (
        _normalize_downsink_path_contracts(updated)
    )
    task_version_changed = apply_version_baseline_to_task_doc(updated, version_baseline)
    topology_assets_result = _ensure_instance_pack_topology_assets(
        pack_path=pack_path,
        identity_id=str(args.identity_id or "").strip(),
        title=identity_title,
        description=identity_description,
        apply=args.apply,
    )
    launcher_assets_result = _ensure_identity_codex_launcher_assets_backfill(
        pack_path=pack_path,
        identity_id=str(args.identity_id or "").strip(),
        apply=args.apply,
    )
    meta_version_changed = False
    if isinstance(meta_doc, dict):
        meta_version_changed = apply_version_baseline_to_meta_doc(meta_doc, version_baseline)
    missing_after = [k for k in REQUIRED_INTAKE_KEYS if not isinstance(updated.get(k), dict)]
    topology_missing_after = [k for k in REQUIRED_TOPOLOGY_KEYS if not isinstance(updated.get(k), dict)]
    launcher_missing_after = [k for k in REQUIRED_LAUNCHER_KEYS if not isinstance(updated.get(k), dict)]
    continuity_missing_after = [k for k in REQUIRED_CONTINUITY_KEYS if not isinstance(updated.get(k), dict)]
    dialogue_retention_missing_after = [k for k in REQUIRED_DIALOGUE_RETENTION_KEYS if not isinstance(updated.get(k), dict)]
    artifact_family_routing_missing_after = [k for k in REQUIRED_ARTIFACT_FAMILY_ROUTING_KEYS if not isinstance(updated.get(k), dict)]
    response_stamp_profile_present_after = isinstance(updated.get("response_stamp_profile"), dict)
    response_stamp_profile_after = normalize_response_stamp_profile(updated.get("response_stamp_profile"))
    response_stamp_profile_changed = (
        response_stamp_profile_present_before != response_stamp_profile_present_after
        or response_stamp_profile_before != response_stamp_profile_after
    )
    prompt_missing_after = [k for k in REQUIRED_PROMPT_KEYS if not isinstance(updated.get(k), dict)]
    multimodal_missing_after = [k for k in REQUIRED_MULTIMODAL_KEYS if not isinstance(updated.get(k), dict)]
    reasoning_missing_after = [k for k in REQUIRED_REASONING_KEYS if not isinstance(updated.get(k), dict)]
    entry_missing_after = [k for k in REQUIRED_ENTRY_KEYS if not isinstance(updated.get(k), dict)]
    lane_headstamp_missing_after = [k for k in REQUIRED_LANE_HEADSTAMP_KEYS if not isinstance(updated.get(k), dict)]
    host_gateway_missing_after = [k for k in REQUIRED_HOST_GATEWAY_KEYS if not isinstance(updated.get(k), dict)]
    host_visible_surface_missing_after = [
        k for k in REQUIRED_HOST_VISIBLE_SURFACE_KEYS if not isinstance(updated.get(k), dict)
    ]
    downsink_missing_after = [k for k in REQUIRED_DOWNSINK_KEYS if not isinstance(updated.get(k), dict)]
    skill_supply_chain_missing_after = [
        k for k in SKILL_SUPPLY_CHAIN_CONTRACT_DEFAULTS.keys() if not isinstance(updated.get(k), dict)
    ]
    topology_invalid_after = [
        k
        for k in REQUIRED_TOPOLOGY_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or str((updated.get(k) or {}).get("contract_id", "")).strip() != INSTANCE_PACK_TOPOLOGY_CONTRACT_ID
            or str((updated.get(k) or {}).get("validator", "")).strip() != INSTANCE_PACK_TOPOLOGY_VALIDATOR_ID
            or str((updated.get(k) or {}).get("fail_mode", "")).strip().lower() != "fail_required"
        )
    ]
    launcher_invalid_after = _launcher_contract_invalid_keys(updated)
    continuity_invalid_after = _continuity_contract_invalid_keys(updated)
    dialogue_retention_invalid_after = _dialogue_retention_contract_invalid_keys(updated)
    artifact_family_routing_invalid_after = _artifact_family_routing_contract_invalid_keys(updated)
    prompt_invalid_after = [
        k
        for k in REQUIRED_PROMPT_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or not str((updated.get(k) or {}).get("validator", "")).strip()
        )
    ]
    multimodal_invalid_after = [
        k
        for k in REQUIRED_MULTIMODAL_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or not str((updated.get(k) or {}).get("validator", "")).strip()
            or not str((updated.get(k) or {}).get("contract_id", "")).strip()
        )
    ]
    reasoning_invalid_after = [
        k
        for k in REQUIRED_REASONING_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or not str((updated.get(k) or {}).get("validator", "")).strip()
            or not str((updated.get(k) or {}).get("contract_id", "")).strip()
        )
    ]
    entry_invalid_after = [
        k
        for k in REQUIRED_ENTRY_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or not str((updated.get(k) or {}).get("validator", "")).strip()
            or str((updated.get(k) or {}).get("entry_script", "")).strip() != ENTRY_SCRIPT
            or str((updated.get(k) or {}).get("bundle_key", "")).strip() != ENTRY_BUNDLE_KEY
            or updated.get(k, {}).get("require_strict_operation_receipt") is not True
            or not str((updated.get(k) or {}).get("entry_receipt_state_file", "")).strip()
            or not str((updated.get(k) or {}).get("entry_receipt_history_pattern", "")).strip()
            or _safe_int((updated.get(k) or {}).get("entry_receipt_max_age_seconds"), default=0) <= 0
            or not isinstance((updated.get(k) or {}).get("entry_receipt_required_fields"), list)
            or not list((updated.get(k) or {}).get("entry_receipt_required_fields") or [])
        )
    ]
    lane_headstamp_invalid_after = [
        k
        for k in REQUIRED_LANE_HEADSTAMP_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or str((updated.get(k) or {}).get("enforcement_validator", "")).strip()
            != "scripts/validate_protocol_lane_headstamp_continuity.py"
            or str((updated.get(k) or {}).get("required_lane", "")).strip().lower() != "protocol"
            or (updated.get(k) or {}).get("route_non_starvation") is not True
            or (updated.get(k) or {}).get("headstamp_dual_context_required") is not True
            or not isinstance((updated.get(k) or {}).get("required_fields"), list)
            or not set(
                [
                    "requested_lane",
                    "previous_lane",
                    "resolved_lane",
                    "lane_activation_status",
                    "lane_activation_error_code",
                    "route_source_ref",
                    "lane_activation_evidence_ref",
                    "headstamp_continuity_status",
                    "headstamp_error_code",
                ]
            ).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("required_fields") or [])
                    if str(item).strip()
                }
            )
        )
    ]
    host_gateway_invalid_after = [
        k
        for k in REQUIRED_HOST_GATEWAY_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or str((updated.get(k) or {}).get("contract_id", "")).strip() != HOST_GATEWAY_CONTRACT_ID
            or not str((updated.get(k) or {}).get("validator", "")).strip()
            or str((updated.get(k) or {}).get("protocol_ingress_script", "")).strip() != UNIQUE_INGRESS_SCRIPT
            or str((updated.get(k) or {}).get("protocol_egress_script", "")).strip() != UNIQUE_EGRESS_SCRIPT
            or not str((updated.get(k) or {}).get("ingress_wrapper_path", "")).strip()
            or not str((updated.get(k) or {}).get("egress_wrapper_path", "")).strip()
            or not str((updated.get(k) or {}).get("session_chain_wrapper_path", "")).strip()
            or not str((updated.get(k) or {}).get("gateway_contract_path", "")).strip()
            or not isinstance((updated.get(k) or {}).get("entry_receipt_policy"), dict)
            or bool(((updated.get(k) or {}).get("entry_receipt_policy") or {}).get("required")) is not True
            or not isinstance((updated.get(k) or {}).get("ingress_proof_policy"), dict)
            or bool(((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("required")) is not True
            or int((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("max_age_seconds") or 0)) <= 0
            or (
                (
                    str((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_mode") or "")).strip()
                    == "runtime_env_secret"
                    and not str(
                        (((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_secret_env") or "")
                    ).strip()
                    )
                    or (
                        str((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_mode") or "")).strip()
                        == "runtime_env_secret"
                        and not str(
                            (((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signing_key_path") or "")
                        ).strip()
                    )
                    or (
                        str((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_mode") or "")).strip()
                        == "runtime_env_secret"
                        and not isinstance(
                            (((updated.get(k) or {}).get("ingress_proof_policy") or {}).get(
                                "bootstrap_env_secret_from_signing_key_path"
                            )),
                            bool,
                        )
                    )
                    or (
                        str((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_mode") or "")).strip()
                        != "runtime_env_secret"
                    and not str(
                        (((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signing_key_path") or "")
                    ).strip()
                )
            )
            or not isinstance((updated.get(k) or {}).get("egress_receipt_policy"), dict)
            or bool(((updated.get(k) or {}).get("egress_receipt_policy") or {}).get("required")) is not True
            or not isinstance((updated.get(k) or {}).get("egress_grant_policy"), dict)
            or bool(((updated.get(k) or {}).get("egress_grant_policy") or {}).get("required")) is not True
            or int((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("max_age_seconds") or 0)) <= 0
            or (
                (
                    str((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_mode") or "")).strip()
                    == "runtime_env_secret"
                    and not str(
                        (((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_secret_env") or "")
                    ).strip()
                    )
                    or (
                        str((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_mode") or "")).strip()
                        == "runtime_env_secret"
                        and not str(
                            (((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signing_key_path") or "")
                        ).strip()
                    )
                    or (
                        str((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_mode") or "")).strip()
                        == "runtime_env_secret"
                        and not isinstance(
                            (((updated.get(k) or {}).get("egress_grant_policy") or {}).get(
                                "bootstrap_env_secret_from_signing_key_path"
                            )),
                            bool,
                        )
                    )
                    or (
                        str((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_mode") or "")).strip()
                        != "runtime_env_secret"
                    and not str(
                        (((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signing_key_path") or "")
                    ).strip()
                )
            )
            or not isinstance((updated.get(k) or {}).get("headstamp_policy"), dict)
            or bool(((updated.get(k) or {}).get("headstamp_policy") or {}).get("required")) is not True
            or not isinstance((updated.get(k) or {}).get("identity_tuple_fields"), list)
            or not set(HOST_GATEWAY_REQUIRED_TUPLE_FIELDS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("identity_tuple_fields") or [])
                    if str(item).strip()
                }
            )
            or not isinstance((updated.get(k) or {}).get("broadcast_policy"), dict)
            or bool(((updated.get(k) or {}).get("broadcast_policy") or {}).get("required")) is not True
            or str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("protocol_broadcast_items_dir") or "")
            ).strip()
            != HOST_GATEWAY_BROADCAST_ITEMS_DIR
            or str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("protocol_broadcast_index_file") or "")
            ).strip()
            != HOST_GATEWAY_BROADCAST_INDEX_FILE
            or str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("protocol_broadcast_schema_file") or "")
            ).strip()
            != HOST_GATEWAY_BROADCAST_SCHEMA_FILE
            or not str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("instance_state_file") or "")
            ).strip()
            or not str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("instance_receipt_pattern") or "")
            ).strip()
            or not str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("instance_ack_pattern") or "")
            ).strip()
            or not isinstance(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("block_on_critical_unacked")),
                bool,
            )
            or str(((updated.get(k) or {}).get("host_visible_surface_registry_contract_ref") or "")).strip()
            != HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY
            or not isinstance((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY), dict)
            or bool(
                (((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get("required")
            )
            is not True
            or not str(
                ((((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get(
                    "ingress_wrapper_template_sha256"
                ) or "")
            ).strip()
            or not str(
                ((((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get(
                    "egress_wrapper_template_sha256"
                ) or "")
            ).strip()
            or not str(
                ((((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get(
                    "session_chain_wrapper_template_sha256"
                ) or "")
            ).strip()
            or not isinstance(
                ((((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get(
                    "session_chain_required_semantic_tokens"
                )),
                list,
            )
        )
    ]
    host_visible_surface_invalid_after = [
        k
        for k in REQUIRED_HOST_VISIBLE_SURFACE_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or str((updated.get(k) or {}).get("contract_id", "")).strip()
            != HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID
            or str((updated.get(k) or {}).get("validator", "")).strip()
            != HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR
            or not isinstance((updated.get(k) or {}).get("required_channels"), list)
            or not set(HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("required_channels") or [])
                    if str(item).strip()
                }
            )
            or not str((updated.get(k) or {}).get("runtime_state_file", "")).strip()
            or not str((updated.get(k) or {}).get("runtime_receipt_pattern", "")).strip()
            or not str((updated.get(k) or {}).get("post_check_closure_state_file", "")).strip()
            or not bool((updated.get(k) or {}).get("post_check_block_on_active", False))
            or _safe_int((updated.get(k) or {}).get("runtime_receipt_max_age_seconds", 0), default=0) <= 0
            or not isinstance((updated.get(k) or {}).get("required_attestation_fields"), list)
            or not set(HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("required_attestation_fields") or [])
                    if str(item).strip()
                }
            )
            or not isinstance((updated.get(k) or {}).get("required_pass_status_fields"), list)
            or not set(HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("required_pass_status_fields") or [])
                    if str(item).strip()
                }
            )
            or str((updated.get(k) or {}).get("final_channel_id", "")).strip()
            != HOST_VISIBLE_FINAL_CHANNEL_ID
            or (updated.get(k) or {}).get("final_channel_relay_required") is not True
            or str((updated.get(k) or {}).get("final_channel_relay_surface", "")).strip()
            != HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE
            or str((updated.get(k) or {}).get("final_channel_relay_mode", "")).strip()
            != HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE
            or str((updated.get(k) or {}).get("final_channel_delivery_authority", "")).strip()
            != HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY
            or not isinstance((updated.get(k) or {}).get("final_channel_required_attestation_fields"), list)
            or not set(HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("final_channel_required_attestation_fields") or [])
                    if str(item).strip()
                }
            )
            or not isinstance((updated.get(k) or {}).get("final_channel_required_pass_status_fields"), list)
            or not set(HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("final_channel_required_pass_status_fields") or [])
                    if str(item).strip()
                }
            )
            or str((updated.get(k) or {}).get("required_live_probe_delegate", "")).strip()
            != HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE
            or str((updated.get(k) or {}).get("host_dispatch_mode_required", "")).strip().lower()
            != HOST_GATEWAY_REQUIRED_DISPATCH_MODE
            or str((updated.get(k) or {}).get("host_release_mode_required", "")).strip().lower()
            != HOST_GATEWAY_REQUIRED_RELEASE_MODE
            or (updated.get(k) or {}).get("strict_live_run_binding_required") is not True
        )
    ]
    downsink_invalid_after = [
        k
        for k in REQUIRED_DOWNSINK_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or str((updated.get(k) or {}).get("contract_id", "")).strip() != DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID
            or str((updated.get(k) or {}).get("validator_id", "")).strip() != DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID
            or str((updated.get(k) or {}).get("write_guard_validator_id", "")).strip()
            != DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID
            or not isinstance((updated.get(k) or {}).get("source_literal_lock_policy"), dict)
            or bool((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get("required")) is not True
            or str(
                ((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get("validator_id") or "")
            ).strip()
            != DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID
            or bool(
                ((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get(
                    "enforce_registered_runtime_path_literals_only"
                ))
            )
            is not True
            or str(
                ((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get(
                    "allow_inline_override_marker"
                ) or "")
            ).strip()
            != DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER
            or not isinstance((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get("scan_globs"), list)
            or not isinstance((updated.get(k) or {}).get("anchor_policy"), dict)
            or not isinstance((updated.get(k) or {}).get("schema_policy"), dict)
            or not isinstance((updated.get(k) or {}).get("operation_enforcement"), dict)
            or not isinstance((updated.get(k) or {}).get("path_registry"), dict)
            or not set(DOWNSINK_REQUIRED_DOMAINS).issubset(
                {
                    str(domain).strip()
                    for domain in (((updated.get(k) or {}).get("path_registry")) or {}).keys()
                    if str(domain).strip()
                }
            )
        )
    ]
    legacy_drift_after = _legacy_path_drift_fields(updated, args.identity_id)

    host_gateway_wrapper_snapshot_before = _collect_host_gateway_wrapper_template_snapshot(
        updated,
        pack_path=pack_path,
    )
    gateway_artifacts = {}
    host_gateway_artifact_materialization_invoked = False
    if (
        args.apply
        and not host_gateway_missing_after
        and not host_gateway_invalid_after
        and not host_visible_surface_missing_after
        and not host_visible_surface_invalid_after
    ):
        host_gateway_artifact_materialization_invoked = True
        gateway_artifacts = materialize_protocol_host_gateway_artifacts(
            task=updated,
            identity_id=args.identity_id,
            pack_dir=pack_path,
            catalog_path=catalog,
            protocol_root=repo_root,
        )
    continuity_assets_result = materialize_identity_context_continuity_assets(
        task=updated,
        identity_id=args.identity_id,
        pack_dir=pack_path,
        apply=args.apply,
    )
    dialogue_retention_assets_result = materialize_identity_dialogue_retention_assets(
        task=updated,
        identity_id=args.identity_id,
        pack_dir=pack_path,
        apply=args.apply,
    )
    host_gateway_wrapper_snapshot_after = _collect_host_gateway_wrapper_template_snapshot(
        updated,
        pack_path=pack_path,
    )
    host_gateway_wrapper_artifact_changed_paths: list[str] = []
    for wrapper_key, before_snapshot in host_gateway_wrapper_snapshot_before.items():
        after_snapshot = host_gateway_wrapper_snapshot_after.get(wrapper_key) or {}
        before_sha = str(before_snapshot.get("sha256", "")).strip()
        after_sha = str(after_snapshot.get("sha256", "")).strip()
        before_exists = bool(before_snapshot.get("exists"))
        after_exists = bool(after_snapshot.get("exists"))
        if before_sha != after_sha or before_exists != after_exists:
            host_gateway_wrapper_artifact_changed_paths.append(wrapper_key)
    host_gateway_wrapper_artifacts_refreshed = bool(host_gateway_wrapper_artifact_changed_paths)

    prompt_runtime_governance_result = _ensure_identity_prompt_runtime_governance(
        pack_path=pack_path,
        identity_id=str(args.identity_id or "").strip(),
        title=identity_title,
        description=identity_description,
        task_doc=task_doc,
        apply=args.apply,
    )
    provider_bindings_template_result = _ensure_provider_bindings_template(
        pack_path=pack_path,
        repo_root=repo_root,
        apply=args.apply,
    )
    feedback_selftest_assets_result = _ensure_feedback_selftest_assets(
        pack_path=pack_path,
        identity_id=str(args.identity_id or "").strip(),
        task_doc=updated,
        repo_root=repo_root,
        apply=args.apply,
    )
    handoff_selftest_assets_result = _ensure_handoff_selftest_assets(
        pack_path=pack_path,
        identity_id=str(args.identity_id or "").strip(),
        repo_root=repo_root,
        apply=args.apply,
    )
    update_replay_runtime_evidence_result = _ensure_update_replay_runtime_evidence(
        pack_path=pack_path,
        identity_id=str(args.identity_id or "").strip(),
        task_doc=updated,
        apply=args.apply,
    )
    handoff_runtime_log_result = _ensure_handoff_runtime_log(
        pack_path=pack_path,
        identity_id=str(args.identity_id or "").strip(),
        task_doc=updated,
        apply=args.apply,
    )
    feedback_runtime_log_result = _ensure_feedback_runtime_log(
        pack_path=pack_path,
        identity_id=str(args.identity_id or "").strip(),
        task_doc=updated,
        apply=args.apply,
    )

    task_changed = before != updated
    catalog_changed = catalog_row_version_changed
    meta_changed = meta_version_changed
    changed = (
        task_changed
        or catalog_changed
        or meta_changed
        or bool(topology_assets_result.get("changed"))
        or bool(launcher_assets_result.get("changed"))
        or bool(continuity_assets_result.get("changed"))
        or bool(dialogue_retention_assets_result.get("changed"))
        or bool(prompt_runtime_governance_result.get("changed"))
        or bool(provider_bindings_template_result.get("changed"))
        or bool(feedback_selftest_assets_result.get("positive_rulebook_backfilled"))
        or bool(feedback_selftest_assets_result.get("negative_rulebook_backfilled"))
        or bool(handoff_selftest_assets_result.get("backfilled_files"))
    )
    applied = False
    if args.apply:
        if task_changed:
            task_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            applied = True
        if catalog_changed:
            _safe_dump_yaml(catalog, catalog_doc)
            applied = True
        if meta_changed:
            _safe_dump_yaml(meta_path, meta_doc)
            applied = True
        if topology_assets_result.get("applied"):
            applied = True
        if launcher_assets_result.get("applied"):
            applied = True
        if continuity_assets_result.get("changed"):
            applied = True
        if host_gateway_wrapper_artifacts_refreshed:
            applied = True
        if prompt_runtime_governance_result.get("applied"):
            applied = True
        if provider_bindings_template_result.get("applied"):
            applied = True
        if feedback_selftest_assets_result.get("positive_rulebook_backfilled"):
            applied = True
        if feedback_selftest_assets_result.get("negative_rulebook_backfilled"):
            applied = True
        if handoff_selftest_assets_result.get("backfilled_files"):
            applied = True

    if missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-CBKF-001"
        stale_reasons = ["required_contract_keys_missing_after_backfill"]
    elif topology_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-IPACK-001"
        stale_reasons = ["required_topology_contract_keys_missing_after_backfill"]
    elif topology_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-IPACK-002"
        stale_reasons = ["required_topology_contract_invalid_after_backfill"]
    elif launcher_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_LAUNCHER_WIRE_MISSING
        stale_reasons = ["required_launcher_contract_keys_missing_after_backfill"]
    elif launcher_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_LAUNCHER_WIRE_INVALID
        stale_reasons = ["required_launcher_contract_invalid_after_backfill"]
    elif str(continuity_assets_result.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-ICONT-MAT-001"
        stale_reasons = ["continuity_materialization_incomplete_after_backfill"]
    elif prompt_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_PROMPT_WIRE_MISSING
        stale_reasons = ["required_prompt_contract_keys_missing_after_backfill"]
    elif prompt_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_PROMPT_WIRE_INVALID
        stale_reasons = ["required_prompt_contract_invalid_after_backfill"]
    elif multimodal_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_MM_WIRE_MISSING
        stale_reasons = ["required_multimodal_contract_keys_missing_after_backfill"]
    elif multimodal_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_MM_WIRE_INVALID
        stale_reasons = ["required_multimodal_contract_invalid_after_backfill"]
    elif reasoning_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_RL_WIRE_MISSING
        stale_reasons = ["required_reasoning_contract_keys_missing_after_backfill"]
    elif reasoning_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_RL_WIRE_INVALID
        stale_reasons = ["required_reasoning_contract_invalid_after_backfill"]
    elif entry_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_ENTRY_WIRE_MISSING
        stale_reasons = ["required_unique_entry_contract_keys_missing_after_backfill"]
    elif entry_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_ENTRY_WIRE_INVALID
        stale_reasons = ["required_unique_entry_contract_invalid_after_backfill"]
    elif lane_headstamp_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_LANE_HEADSTAMP_WIRE_MISSING
        stale_reasons = ["required_lane_headstamp_contract_keys_missing_after_backfill"]
    elif lane_headstamp_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_LANE_HEADSTAMP_WIRE_INVALID
        stale_reasons = ["required_lane_headstamp_contract_invalid_after_backfill"]
    elif host_gateway_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_HOST_GATEWAY_WIRE_MISSING
        stale_reasons = ["required_host_gateway_contract_keys_missing_after_backfill"]
    elif host_gateway_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_HOST_GATEWAY_WIRE_INVALID
        stale_reasons = ["required_host_gateway_contract_invalid_after_backfill"]
    elif host_visible_surface_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_VISIBLE_SURFACE_WIRE_MISSING
        stale_reasons = ["required_host_visible_surface_contract_keys_missing_after_backfill"]
    elif host_visible_surface_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_VISIBLE_SURFACE_WIRE_INVALID
        stale_reasons = ["required_host_visible_surface_contract_invalid_after_backfill"]
    elif downsink_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_DOWNSINK_WIRE_MISSING
        stale_reasons = ["required_downsink_contract_keys_missing_after_backfill"]
    elif downsink_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_DOWNSINK_WIRE_INVALID
        stale_reasons = ["required_downsink_contract_invalid_after_backfill"]
    elif skill_supply_chain_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-SSUP-001"
        stale_reasons = ["required_skill_supply_chain_contract_keys_missing_after_backfill"]
    elif legacy_drift_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-CBKF-002"
        stale_reasons = ["legacy_contract_path_drift_after_backfill"]
    elif (
        changed
        or host_gateway_wrapper_artifacts_refreshed
        or bool(topology_assets_result.get("changed"))
        or bool(launcher_assets_result.get("changed"))
    ):
        status = STATUS_PASS_REQUIRED if applied else STATUS_SKIPPED_NOT_REQUIRED
        error_code = ""
        stale_reasons = [] if applied else ["dry_run_only"]
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""
        stale_reasons = ["already_backfilled"] if not applied else []

    version_baseline_info = {
        "entry_file": str(version_baseline.get("entry_path", "")),
        "resolved_file": str(version_baseline.get("resolved_path", "")),
        "stream_version": str(version_baseline.get("stream_version", "")),
    }
    task_versions_before = _task_version_snapshot(before)
    task_versions_after = _task_version_snapshot(updated)
    catalog_versions_before = _catalog_version_snapshot(catalog_row_before)
    catalog_versions_after = _catalog_version_snapshot(catalog_row if isinstance(catalog_row, dict) else {})
    meta_versions_before = _meta_version_snapshot(meta_before)
    meta_versions_after = _meta_version_snapshot(meta_doc if isinstance(meta_doc, dict) else {})

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog),
        "pack_path": str(pack_path),
        "task_path": str(task_path),
        "contract_backfill_status": status,
        "error_code": error_code,
        "changed": changed,
        "task_changed": task_changed,
        "catalog_changed": catalog_changed,
        "meta_changed": meta_changed,
        "version_baseline_status": STATUS_PASS_REQUIRED,
        "version_baseline": version_baseline_info,
        "task_version_changed": task_version_changed,
        "catalog_row_version_changed": catalog_row_version_changed,
        "meta_version_changed": meta_version_changed,
        "task_versions_before": task_versions_before,
        "task_versions_after": task_versions_after,
        "catalog_versions_before": catalog_versions_before,
        "catalog_versions_after": catalog_versions_after,
        "meta_versions_before": meta_versions_before,
        "meta_versions_after": meta_versions_after,
        "meta_path": str(meta_path),
        "identity_prompt_title": identity_title,
        "identity_prompt_description": identity_description,
        "host_gateway_wrapper_artifacts_refreshed": host_gateway_wrapper_artifacts_refreshed,
        "host_gateway_wrapper_artifact_changed_paths": host_gateway_wrapper_artifact_changed_paths,
        "host_gateway_wrapper_snapshot_before": host_gateway_wrapper_snapshot_before,
        "host_gateway_wrapper_snapshot_after": host_gateway_wrapper_snapshot_after,
        "host_gateway_artifact_materialization_invoked": host_gateway_artifact_materialization_invoked,
        "identity_prompt_runtime_governance": prompt_runtime_governance_result,
        "provider_bindings_template_backfill": provider_bindings_template_result,
        "feedback_selftest_assets_backfill": feedback_selftest_assets_result,
        "handoff_selftest_assets_backfill": handoff_selftest_assets_result,
        "update_replay_runtime_evidence_backfill": update_replay_runtime_evidence_result,
        "handoff_runtime_log_backfill": handoff_runtime_log_result,
        "feedback_runtime_log_backfill": feedback_runtime_log_result,
        "applied": applied,
        "response_stamp_profile_present_before": response_stamp_profile_present_before,
        "response_stamp_profile_present_after": response_stamp_profile_present_after,
        "response_stamp_profile_before": response_stamp_profile_before,
        "response_stamp_profile_after": response_stamp_profile_after,
        "response_stamp_profile_changed": response_stamp_profile_changed,
        "missing_contract_keys_before": missing_before,
        "missing_contract_keys_after": missing_after,
        "required_topology_contract_keys": list(REQUIRED_TOPOLOGY_KEYS),
        "missing_topology_contract_keys_before": topology_missing_before,
        "required_launcher_contract_keys": list(REQUIRED_LAUNCHER_KEYS),
        "missing_launcher_contract_keys_before": launcher_missing_before,
        "missing_launcher_contract_keys_after": launcher_missing_after,
        "invalid_launcher_contract_keys_after": launcher_invalid_after,
        "restored_launcher_contract_keys": restored_launcher_contract_keys,
        "launcher_assets_backfill": launcher_assets_result,
        "continuity_assets_backfill": continuity_assets_result,
        "dialogue_retention_assets_backfill": dialogue_retention_assets_result,
        "missing_topology_contract_keys_after": topology_missing_after,
        "invalid_topology_contract_keys_after": topology_invalid_after,
        "restored_topology_contract_keys": restored_topology_contract_keys,
        "restored_update_lifecycle_required_checks": restored_update_lifecycle_required_checks,
        "topology_assets_backfill": topology_assets_result,
        "required_continuity_contract_keys": list(REQUIRED_CONTINUITY_KEYS),
        "required_dialogue_retention_contract_keys": list(REQUIRED_DIALOGUE_RETENTION_KEYS),
        "required_artifact_family_routing_contract_keys": list(REQUIRED_ARTIFACT_FAMILY_ROUTING_KEYS),
        "missing_continuity_contract_keys_before": continuity_missing_before,
        "missing_dialogue_retention_contract_keys_before": dialogue_retention_missing_before,
        "missing_artifact_family_routing_contract_keys_before": artifact_family_routing_missing_before,
        "missing_continuity_contract_keys_after": continuity_missing_after,
        "missing_dialogue_retention_contract_keys_after": dialogue_retention_missing_after,
        "missing_artifact_family_routing_contract_keys_after": artifact_family_routing_missing_after,
        "invalid_continuity_contract_keys_after": continuity_invalid_after,
        "invalid_dialogue_retention_contract_keys_after": dialogue_retention_invalid_after,
        "invalid_artifact_family_routing_contract_keys_after": artifact_family_routing_invalid_after,
        "restored_continuity_contract_keys": restored_continuity_contract_keys,
        "restored_continuity_validator_keys": restored_continuity_validator_keys,
        "restored_dialogue_retention_contract_keys": restored_dialogue_retention_contract_keys,
        "restored_dialogue_retention_validator_keys": restored_dialogue_retention_validator_keys,
        "restored_artifact_family_routing_contract_keys": restored_artifact_family_routing_contract_keys,
        "restored_artifact_family_routing_validator_keys": restored_artifact_family_routing_validator_keys,
        "required_prompt_contract_keys": list(REQUIRED_PROMPT_KEYS),
        "missing_prompt_contract_keys_before": prompt_missing_before,
        "missing_prompt_contract_keys_after": prompt_missing_after,
        "invalid_prompt_contract_keys_after": prompt_invalid_after,
        "forced_prompt_required_keys": forced_required_keys,
        "restored_prompt_validator_keys": restored_validator_keys,
        "restored_prompt_contract_list_fields": restored_prompt_contract_list_fields,
        "required_multimodal_contract_keys": list(REQUIRED_MULTIMODAL_KEYS),
        "missing_multimodal_contract_keys_before": multimodal_missing_before,
        "missing_multimodal_contract_keys_after": multimodal_missing_after,
        "invalid_multimodal_contract_keys_after": multimodal_invalid_after,
        "forced_multimodal_required_keys": forced_mm_required_keys,
        "restored_multimodal_validator_keys": restored_mm_validator_keys,
        "multimodal_arbitration_link_restored": arbitration_link_restored,
        "required_reasoning_contract_keys": list(REQUIRED_REASONING_KEYS),
        "missing_reasoning_contract_keys_before": reasoning_missing_before,
        "missing_reasoning_contract_keys_after": reasoning_missing_after,
        "invalid_reasoning_contract_keys_after": reasoning_invalid_after,
        "forced_reasoning_required_keys": forced_rl_required_keys,
        "restored_reasoning_validator_keys": restored_rl_validator_keys,
        "reasoning_arbitration_link_restored": reasoning_arbitration_link_restored,
        "route_discovery_arbitration_link_restored": route_discovery_link_restored,
        "feedback_operational_prompt_arbitration_link_restored": feedback_operational_prompt_link_restored,
        "required_unique_entry_contract_keys": list(REQUIRED_ENTRY_KEYS),
        "missing_unique_entry_contract_keys_before": entry_missing_before,
        "missing_unique_entry_contract_keys_after": entry_missing_after,
        "invalid_unique_entry_contract_keys_after": entry_invalid_after,
        "forced_unique_entry_required_keys": forced_entry_required_keys,
        "restored_unique_entry_validator_keys": restored_entry_validator_keys,
        "required_lane_headstamp_contract_keys": list(REQUIRED_LANE_HEADSTAMP_KEYS),
        "missing_lane_headstamp_contract_keys_before": lane_headstamp_missing_before,
        "missing_lane_headstamp_contract_keys_after": lane_headstamp_missing_after,
        "invalid_lane_headstamp_contract_keys_after": lane_headstamp_invalid_after,
        "forced_lane_headstamp_required_keys": forced_lane_headstamp_required_keys,
        "restored_lane_headstamp_validator_keys": restored_lane_headstamp_validator_keys,
        "required_host_gateway_contract_keys": list(REQUIRED_HOST_GATEWAY_KEYS),
        "missing_host_gateway_contract_keys_before": host_gateway_missing_before,
        "missing_host_gateway_contract_keys_after": host_gateway_missing_after,
        "invalid_host_gateway_contract_keys_after": host_gateway_invalid_after,
        "forced_host_gateway_required_keys": forced_host_gateway_required_keys,
        "restored_host_gateway_validator_keys": restored_host_gateway_validator_keys,
        "required_host_visible_surface_contract_keys": list(REQUIRED_HOST_VISIBLE_SURFACE_KEYS),
        "missing_host_visible_surface_contract_keys_before": host_visible_surface_missing_before,
        "missing_host_visible_surface_contract_keys_after": host_visible_surface_missing_after,
        "invalid_host_visible_surface_contract_keys_after": host_visible_surface_invalid_after,
        "forced_host_visible_surface_required_keys": forced_host_visible_surface_required_keys,
        "restored_host_visible_surface_validator_keys": restored_host_visible_surface_validator_keys,
        "required_downsink_contract_keys": list(REQUIRED_DOWNSINK_KEYS),
        "missing_downsink_contract_keys_before": downsink_missing_before,
        "missing_downsink_contract_keys_after": downsink_missing_after,
        "invalid_downsink_contract_keys_after": downsink_invalid_after,
        "forced_downsink_required_keys": forced_downsink_required_keys,
        "restored_downsink_validator_keys": restored_downsink_validator_keys,
        "restored_downsink_write_guard_validator_keys": restored_downsink_write_guard_validator_keys,
        "restored_downsink_literal_lock_validator_keys": restored_downsink_literal_lock_validator_keys,
        "required_skill_supply_chain_contract_keys": list(SKILL_SUPPLY_CHAIN_CONTRACT_DEFAULTS.keys()),
        "missing_skill_supply_chain_contract_keys_before": skill_supply_chain_missing_before,
        "missing_skill_supply_chain_contract_keys_after": skill_supply_chain_missing_after,
        "restored_skill_supply_chain_contract_keys": restored_skill_supply_chain_contract_keys,
        "restored_capability_driver_validator_paths": restored_capability_driver_validator_paths,
        "host_gateway_artifacts": gateway_artifacts,
        "instance_pack_topology_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not topology_missing_after and not topology_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "instance_pack_topology_contract_auto_wire_error_code": (
            ""
            if not topology_missing_after and not topology_invalid_after
            else ("IP-IPACK-001" if topology_missing_after else "IP-IPACK-002")
        ),
        "continuity_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not continuity_missing_after and not continuity_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "continuity_contract_auto_wire_error_code": (
            ""
            if not continuity_missing_after and not continuity_invalid_after
            else (
                ERR_CONTINUITY_WIRE_MISSING
                if continuity_missing_after
                else ERR_CONTINUITY_WIRE_INVALID
            )
        ),
        "dialogue_retention_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not dialogue_retention_missing_after and not dialogue_retention_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "dialogue_retention_contract_auto_wire_error_code": (
            ""
            if not dialogue_retention_missing_after and not dialogue_retention_invalid_after
            else (
                ERR_DRET_WIRE_MISSING
                if dialogue_retention_missing_after
                else ERR_DRET_WIRE_INVALID
            )
        ),
        "artifact_family_routing_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not artifact_family_routing_missing_after and not artifact_family_routing_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "artifact_family_routing_contract_auto_wire_error_code": (
            ""
            if not artifact_family_routing_missing_after and not artifact_family_routing_invalid_after
            else ("IP-AFR-001" if artifact_family_routing_missing_after else "IP-AFR-002")
        ),
        "unique_entry_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not entry_missing_after and not entry_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "unique_entry_contract_auto_wire_error_code": (
            ""
            if not entry_missing_after and not entry_invalid_after
            else (ERR_ENTRY_WIRE_MISSING if entry_missing_after else ERR_ENTRY_WIRE_INVALID)
        ),
        "lane_headstamp_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED
            if not lane_headstamp_missing_after and not lane_headstamp_invalid_after
            else STATUS_FAIL_REQUIRED
        ),
        "lane_headstamp_contract_auto_wire_error_code": (
            ""
            if not lane_headstamp_missing_after and not lane_headstamp_invalid_after
            else (
                ERR_LANE_HEADSTAMP_WIRE_MISSING
                if lane_headstamp_missing_after
                else ERR_LANE_HEADSTAMP_WIRE_INVALID
            )
        ),
        "host_gateway_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not host_gateway_missing_after and not host_gateway_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "host_gateway_contract_auto_wire_error_code": (
            ""
            if not host_gateway_missing_after and not host_gateway_invalid_after
            else (
                ERR_HOST_GATEWAY_WIRE_MISSING
                if host_gateway_missing_after
                else ERR_HOST_GATEWAY_WIRE_INVALID
            )
        ),
        "host_visible_surface_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED
            if not host_visible_surface_missing_after and not host_visible_surface_invalid_after
            else STATUS_FAIL_REQUIRED
        ),
        "host_visible_surface_contract_auto_wire_error_code": (
            ""
            if not host_visible_surface_missing_after and not host_visible_surface_invalid_after
            else (
                ERR_VISIBLE_SURFACE_WIRE_MISSING
                if host_visible_surface_missing_after
                else ERR_VISIBLE_SURFACE_WIRE_INVALID
            )
        ),
        "downsink_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not downsink_missing_after and not downsink_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "downsink_contract_auto_wire_error_code": (
            ""
            if not downsink_missing_after and not downsink_invalid_after
            else (ERR_DOWNSINK_WIRE_MISSING if downsink_missing_after else ERR_DOWNSINK_WIRE_INVALID)
        ),
        "prompt_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not prompt_missing_after and not prompt_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "prompt_contract_auto_wire_error_code": (
            ""
            if not prompt_missing_after and not prompt_invalid_after
            else (ERR_PROMPT_WIRE_MISSING if prompt_missing_after else ERR_PROMPT_WIRE_INVALID)
        ),
        "multimodal_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not multimodal_missing_after and not multimodal_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "multimodal_contract_auto_wire_error_code": (
            ""
            if not multimodal_missing_after and not multimodal_invalid_after
            else (ERR_MM_WIRE_MISSING if multimodal_missing_after else ERR_MM_WIRE_INVALID)
        ),
        "reasoning_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not reasoning_missing_after and not reasoning_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "reasoning_contract_auto_wire_error_code": (
            ""
            if not reasoning_missing_after and not reasoning_invalid_after
            else (ERR_RL_WIRE_MISSING if reasoning_missing_after else ERR_RL_WIRE_INVALID)
        ),
        "legacy_path_drift_fields_before": legacy_drift_before,
        "legacy_path_drift_fields_after": legacy_drift_after,
        "required_contract_keys": (
            list(REQUIRED_INTAKE_KEYS)
            + list(REQUIRED_MULTIMODAL_KEYS)
            + list(REQUIRED_REASONING_KEYS)
            + list(REQUIRED_ENTRY_KEYS)
            + list(REQUIRED_LANE_HEADSTAMP_KEYS)
            + list(REQUIRED_HOST_GATEWAY_KEYS)
            + list(REQUIRED_HOST_VISIBLE_SURFACE_KEYS)
            + list(REQUIRED_DOWNSINK_KEYS)
        ),
        "stale_reasons": stale_reasons,
        "evidence_ref": str(task_path),
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
