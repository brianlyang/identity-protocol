#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
import subprocess
from pathlib import Path
from typing import Any

from blocker_taxonomy_common import CANONICAL_BLOCKER_TYPES
from create_identity_pack import (
    _agent_handoff_contract_skeleton,
    _collaboration_trigger_contract_skeleton,
    _identity_communication_transport_contract_skeleton,
)
from identity_broadcast_delivery_common import resolve_pack_runtime_path
from tool_vendor_governance_common import contract_required

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

ERR_COMMUNICATION_CONTRACT_MISSING = "IP-COMM-001"
ERR_COMMUNICATION_RUNTIME_ROOTS = "IP-COMM-002"
ERR_COMMUNICATION_COMPONENT_FAILURE = "IP-COMM-003"

COMMUNICATION_CONTRACT_KEYS: tuple[str, ...] = (
    "identity_communication_transport_contract_v1",
    "identity_communication_transport_contract",
)

REPLY_CONTRACT_KEY = "protocol_feedback_canonical_reply_channel_contract_v1"
INBOX_CONTRACT_KEY = "protocol_feedback_canonical_inbox_channel_contract_v1"
ATOMIC_CONTRACT_KEY = "protocol_feedback_atomic_emit_contract_v1"
HANDOFF_CONTRACT_KEY = "agent_handoff_contract"
COLLAB_CONTRACT_KEY = "collaboration_trigger_contract"
BROADCAST_CONTRACT_KEY = "identity_broadcast_delivery_contract_v1"


def _parse_json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        payload = json.loads(text[start : end + 1])
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _select_contract(task_doc: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in COMMUNICATION_CONTRACT_KEYS:
        node = task_doc.get(key)
        if isinstance(node, dict):
            return node, key
    return {}, COMMUNICATION_CONTRACT_KEYS[0]


def _normalize_required_runtime_roots(contract: dict[str, Any]) -> list[str]:
    rows = contract.get("required_runtime_roots")
    if not isinstance(rows, list):
        rows = _identity_communication_transport_contract_skeleton().get("required_runtime_roots", [])
    return [str(item).strip() for item in rows if str(item).strip()]


def _runtime_root_rows(*, pack_path: Path, contract: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for raw in _normalize_required_runtime_roots(contract):
        resolved = resolve_pack_runtime_path(pack_path, raw, raw)
        exists = resolved.exists()
        rows.append(
            {
                "declared_root": raw,
                "resolved_root": str(resolved),
                "exists": exists,
                "kind": "dir" if resolved.is_dir() else "file" if resolved.is_file() else "missing",
            }
        )
        if not exists:
            missing.append(raw)
    return rows, missing


def _run_subprocess_json(*, repo_root: Path, cmd: list[str]) -> tuple[int, dict[str, Any], str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_root), check=False)
    stdout = str(proc.stdout or "")
    payload = _parse_json_payload(stdout)
    return proc.returncode, payload, stdout


def _glob_pack_matches(*, pack_path: Path, pattern: str, identity_id: str) -> list[Path]:
    token = str(pattern or "").strip()
    if not token:
        return []
    p = Path(token).expanduser()
    if p.is_absolute():
        hits = [Path(x).expanduser().resolve() for x in glob.glob(str(p))]
    else:
        hits = [x.resolve() for x in pack_path.glob(token)]
        if not hits and token.startswith("identity/runtime/"):
            hits = [x.resolve() for x in pack_path.glob(token[len("identity/") :])]
    if not hits:
        return []
    token_dash = identity_id
    token_us = identity_id.replace("-", "_")
    scoped = [path for path in hits if token_dash in path.name or token_us in path.name]
    return sorted(scoped or hits)


def _sample_family_counts(sample_root: Path) -> tuple[int, int]:
    positive = len(list((sample_root / "positive").glob("*.json")))
    negative = len(list((sample_root / "negative").glob("*.json")))
    return positive, negative


def _validate_handoff_component(*, task_doc: dict[str, Any], pack_path: Path, identity_id: str) -> dict[str, Any]:
    stale_reasons: list[str] = []
    contract = task_doc.get(HANDOFF_CONTRACT_KEY)
    skeleton = _agent_handoff_contract_skeleton()
    log_pattern = ""
    live_log_count = 0
    sample_root = (pack_path / "runtime/examples/handoff").resolve()
    positive_count, negative_count = _sample_family_counts(sample_root)
    if not isinstance(contract, dict) or contract.get("required") is not True:
        stale_reasons.append("agent_handoff_contract_missing_or_not_required")
    else:
        log_pattern = str(contract.get("handoff_log_path_pattern", "")).strip()
        if str(contract.get("validator", "")).strip() != "scripts/validate_agent_handoff_contract.py":
            stale_reasons.append("agent_handoff_validator_mismatch")
        if not log_pattern:
            stale_reasons.append("agent_handoff_log_pattern_missing")
        required_fields = {str(item).strip() for item in (contract.get("required_fields") or []) if str(item).strip()}
        if not set(skeleton.get("required_fields", [])).issubset(required_fields):
            stale_reasons.append("agent_handoff_required_fields_incomplete")
    if not (pack_path / "runtime/logs/handoff").exists():
        stale_reasons.append("handoff_runtime_root_missing")
    if positive_count <= 0 or negative_count <= 0:
        stale_reasons.append("handoff_sample_family_incomplete")
    if log_pattern:
        live_log_count = len(_glob_pack_matches(pack_path=pack_path, pattern=log_pattern, identity_id=identity_id))
    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    return {
        "component": "handoff_transport",
        "contract_key": HANDOFF_CONTRACT_KEY,
        "status": status,
        "validator": "scripts/validate_agent_handoff_contract.py",
        "live_log_count": live_log_count,
        "sample_positive_count": positive_count,
        "sample_negative_count": negative_count,
        "sample_root": str(sample_root),
        "stale_reasons": stale_reasons,
    }


def _validate_collaboration_component(*, task_doc: dict[str, Any], pack_path: Path, identity_id: str) -> dict[str, Any]:
    stale_reasons: list[str] = []
    contract = task_doc.get(COLLAB_CONTRACT_KEY)
    pattern = ""
    live_log_count = 0
    sample_root = (pack_path / "runtime/examples/collaboration-trigger").resolve()
    positive_count, negative_count = _sample_family_counts(sample_root)
    if not isinstance(contract, dict) or contract.get("required") is not True:
        stale_reasons.append("collaboration_trigger_contract_missing_or_not_required")
    else:
        pattern = str(contract.get("evidence_log_path_pattern", "")).strip()
        if str(contract.get("validator", "")).strip() != "scripts/validate_identity_collab_trigger.py":
            stale_reasons.append("collaboration_trigger_validator_mismatch")
        if not pattern:
            stale_reasons.append("collaboration_trigger_log_pattern_missing")
        trigger_conditions = {str(item).strip() for item in (contract.get("trigger_conditions") or []) if str(item).strip()}
        if not set(CANONICAL_BLOCKER_TYPES).issubset(trigger_conditions):
            stale_reasons.append("collaboration_trigger_conditions_incomplete")
        receipt_fields = {str(item).strip() for item in (contract.get("receipt_required_fields") or []) if str(item).strip()}
        if not {"event_id", "blocker_type", "notified_at", "channel", "dedupe_key", "status"}.issubset(receipt_fields):
            stale_reasons.append("collaboration_receipt_fields_incomplete")
    if not (pack_path / "runtime/logs/collaboration").exists():
        stale_reasons.append("collaboration_runtime_root_missing")
    if positive_count <= 0 or negative_count <= 0:
        stale_reasons.append("collaboration_sample_family_incomplete")
    if pattern:
        live_log_count = len(_glob_pack_matches(pack_path=pack_path, pattern=pattern, identity_id=identity_id))
    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    return {
        "component": "collaboration_transport",
        "contract_key": COLLAB_CONTRACT_KEY,
        "status": status,
        "validator": "scripts/validate_identity_collab_trigger.py",
        "live_log_count": live_log_count,
        "sample_positive_count": positive_count,
        "sample_negative_count": negative_count,
        "sample_root": str(sample_root),
        "stale_reasons": stale_reasons,
    }


def _validate_reply_component(
    *,
    repo_root: Path,
    catalog_path: Path,
    repo_catalog_path: Path,
    task_doc: dict[str, Any],
    identity_id: str,
) -> dict[str, Any]:
    stale_reasons: list[str] = []
    contract = task_doc.get(REPLY_CONTRACT_KEY)
    if not isinstance(contract, dict) or contract.get("required") is not True:
        stale_reasons.append("protocol_feedback_reply_contract_missing_or_not_required")
    else:
        if str(contract.get("outbox_dir", "")).strip() != "runtime/protocol-feedback/outbox-to-protocol":
            stale_reasons.append("protocol_feedback_reply_outbox_dir_mismatch")
        if str(contract.get("primary_outbox_glob", "")).strip() != "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md":
            stale_reasons.append("protocol_feedback_reply_glob_mismatch")
        if str(contract.get("required_index_path", "")).strip() != "runtime/protocol-feedback/evidence-index/INDEX.md":
            stale_reasons.append("protocol_feedback_reply_index_path_mismatch")
        if str(contract.get("enforcement_validator", "")).strip() != "scripts/validate_protocol_feedback_reply_channel.py":
            stale_reasons.append("protocol_feedback_reply_validator_mismatch")
    rc = -1
    payload: dict[str, Any] = {}
    if not stale_reasons:
        rc, payload, _stdout = _run_subprocess_json(
            repo_root=repo_root,
            cmd=[
                "python3",
                "scripts/validate_protocol_feedback_reply_channel.py",
                "--catalog",
                str(catalog_path),
                "--repo-catalog",
                str(repo_catalog_path),
                "--identity-id",
                str(identity_id or "").strip(),
                "--operation",
                "scan",
                "--force-check",
                "--json-only",
            ],
        )
        if rc != 0 or str(payload.get("protocol_feedback_reply_channel_status", "")).strip().upper() == STATUS_FAIL_REQUIRED:
            stale_reasons.extend(
                [str(item).strip() for item in (payload.get("stale_reasons") or []) if str(item).strip()]
                or ["protocol_feedback_reply_validator_failed"]
            )
    return {
        "component": "protocol_feedback_reply_transport",
        "contract_key": REPLY_CONTRACT_KEY,
        "status": STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED,
        "validator": "scripts/validate_protocol_feedback_reply_channel.py",
        "validator_rc": rc,
        "validator_status": str(payload.get("protocol_feedback_reply_channel_status", "")).strip().upper(),
        "stale_reasons": stale_reasons,
        "evidence_ref": str(payload.get("evidence_ref", "")).strip(),
    }


def _validate_inbox_component(
    *,
    repo_root: Path,
    catalog_path: Path,
    task_doc: dict[str, Any],
    identity_id: str,
) -> dict[str, Any]:
    stale_reasons: list[str] = []
    contract = task_doc.get(INBOX_CONTRACT_KEY)
    if not isinstance(contract, dict) or contract.get("required") is not True:
        stale_reasons.append("protocol_feedback_inbox_contract_missing_or_not_required")
    else:
        if str(contract.get("inbox_dir", "")).strip() != "runtime/protocol-feedback/inbox-from-protocol":
            stale_reasons.append("protocol_feedback_inbox_dir_mismatch")
        if str(contract.get("primary_inbox_glob", "")).strip() != "runtime/protocol-feedback/inbox-from-protocol/PROTOCOL_INBOX_*.md":
            stale_reasons.append("protocol_feedback_inbox_glob_mismatch")
        if str(contract.get("required_index_path", "")).strip() != "runtime/protocol-feedback/evidence-index/INDEX.md":
            stale_reasons.append("protocol_feedback_inbox_index_path_mismatch")
        if str(contract.get("enforcement_validator", "")).strip() != "scripts/validate_protocol_feedback_inbox_channel.py":
            stale_reasons.append("protocol_feedback_inbox_validator_mismatch")
    rc = -1
    payload: dict[str, Any] = {}
    if not stale_reasons:
        rc, payload, _stdout = _run_subprocess_json(
            repo_root=repo_root,
            cmd=[
                "python3",
                "scripts/validate_protocol_feedback_inbox_channel.py",
                "--catalog",
                str(catalog_path),
                "--identity-id",
                str(identity_id or "").strip(),
                "--operation",
                "scan",
                "--force-check",
                "--json-only",
            ],
        )
        if rc != 0 or str(payload.get("protocol_feedback_inbox_channel_status", "")).strip().upper() == STATUS_FAIL_REQUIRED:
            stale_reasons.extend(
                [str(item).strip() for item in (payload.get("stale_reasons") or []) if str(item).strip()]
                or ["protocol_feedback_inbox_validator_failed"]
            )
    return {
        "component": "protocol_feedback_inbox_transport",
        "contract_key": INBOX_CONTRACT_KEY,
        "status": STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED,
        "validator": "scripts/validate_protocol_feedback_inbox_channel.py",
        "validator_rc": rc,
        "validator_status": str(payload.get("protocol_feedback_inbox_channel_status", "")).strip().upper(),
        "stale_reasons": stale_reasons,
        "evidence_ref": str(payload.get("evidence_ref", "")).strip(),
    }


def _validate_atomic_component(
    *,
    repo_root: Path,
    catalog_path: Path,
    task_doc: dict[str, Any],
    identity_id: str,
) -> dict[str, Any]:
    stale_reasons: list[str] = []
    contract = task_doc.get(ATOMIC_CONTRACT_KEY)
    if not isinstance(contract, dict) or contract.get("required") is not True:
        stale_reasons.append("protocol_feedback_atomic_contract_missing_or_not_required")
    else:
        if str(contract.get("validator", "")).strip() != "scripts/validate_protocol_feedback_atomic_emit.py":
            stale_reasons.append("protocol_feedback_atomic_validator_mismatch")
        if not str(contract.get("receipt_path_pattern", "")).strip():
            stale_reasons.append("protocol_feedback_atomic_receipt_pattern_missing")
    rc = -1
    payload: dict[str, Any] = {}
    if not stale_reasons:
        rc, payload, _stdout = _run_subprocess_json(
            repo_root=repo_root,
            cmd=[
                "python3",
                "scripts/validate_protocol_feedback_atomic_emit.py",
                "--catalog",
                str(catalog_path),
                "--identity-id",
                str(identity_id or "").strip(),
                "--operation",
                "scan",
                "--force-required",
                "--json-only",
            ],
        )
        atomic_status = str(payload.get("protocol_feedback_atomic_emit_status", "")).strip().upper()
        if rc != 0 or atomic_status != STATUS_PASS_REQUIRED:
            stale_reasons.extend(
                [str(item).strip() for item in (payload.get("stale_reasons") or []) if str(item).strip()]
                or ["protocol_feedback_atomic_validator_failed"]
            )
    return {
        "component": "protocol_feedback_atomic_transport",
        "contract_key": ATOMIC_CONTRACT_KEY,
        "status": STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED,
        "validator": "scripts/validate_protocol_feedback_atomic_emit.py",
        "validator_rc": rc,
        "validator_status": str(payload.get("protocol_feedback_atomic_emit_status", "")).strip().upper(),
        "stale_reasons": stale_reasons,
        "evidence_ref": str(payload.get("evidence_ref", "")).strip(),
    }


def _validate_broadcast_component(
    *,
    repo_root: Path,
    catalog_path: Path,
    task_doc: dict[str, Any],
    identity_id: str,
) -> dict[str, Any]:
    stale_reasons: list[str] = []
    contract = task_doc.get(BROADCAST_CONTRACT_KEY)
    if not isinstance(contract, dict) or contract.get("required") is not True:
        stale_reasons.append("identity_broadcast_delivery_contract_missing_or_not_required")
    rc = -1
    payload: dict[str, Any] = {}
    if not stale_reasons:
        rc, payload, _stdout = _run_subprocess_json(
            repo_root=repo_root,
            cmd=[
                "python3",
                "scripts/validate_identity_broadcast_delivery.py",
                "--catalog",
                str(catalog_path),
                "--identity-id",
                str(identity_id or "").strip(),
                "--operation",
                "scan",
                "--json-only",
            ],
        )
        if rc != 0 or str(payload.get("identity_broadcast_delivery_status", "")).strip().upper() != STATUS_PASS_REQUIRED:
            stale_reasons.extend(
                [str(item).strip() for item in (payload.get("stale_reasons") or []) if str(item).strip()]
                or ["identity_broadcast_delivery_validator_failed"]
            )
    return {
        "component": "broadcast_transport",
        "contract_key": BROADCAST_CONTRACT_KEY,
        "status": STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED,
        "validator": "scripts/validate_identity_broadcast_delivery.py",
        "validator_rc": rc,
        "validator_status": str(payload.get("identity_broadcast_delivery_status", "")).strip().upper(),
        "stale_reasons": stale_reasons,
        "evidence_ref": str(payload.get("broadcast_receipt_path", "") or payload.get("broadcast_state_file", "")).strip(),
        "broadcast_visible_count": int(payload.get("broadcast_visible_count", 0) or 0),
        "broadcast_pending_ack_count": int(payload.get("broadcast_pending_ack_count", 0) or 0),
        "broadcast_critical_unacked_count": int(payload.get("broadcast_critical_unacked_count", 0) or 0),
    }


def collect_identity_communication_transport_projection(
    *,
    task_doc: dict[str, Any],
    pack_path: Path,
    identity_id: str,
    catalog_path: Path,
    repo_root: Path,
    repo_catalog_path: Path,
) -> dict[str, Any]:
    contract, contract_key = _select_contract(task_doc)
    required_contract = contract_required(contract)
    payload: dict[str, Any] = {
        "identity_communication_transport_status": STATUS_FAIL_REQUIRED,
        "communication_contract_status": STATUS_FAIL_REQUIRED,
        "communication_runtime_roots_status": STATUS_FAIL_REQUIRED,
        "handoff_transport_status": STATUS_FAIL_REQUIRED,
        "collaboration_transport_status": STATUS_FAIL_REQUIRED,
        "protocol_feedback_reply_transport_status": STATUS_FAIL_REQUIRED,
        "protocol_feedback_inbox_transport_status": STATUS_FAIL_REQUIRED,
        "protocol_feedback_atomic_transport_status": STATUS_FAIL_REQUIRED,
        "broadcast_transport_status": STATUS_FAIL_REQUIRED,
        "identity_id": str(identity_id or "").strip(),
        "required_contract": bool(required_contract),
        "contract_key": contract_key,
        "error_code": ERR_COMMUNICATION_CONTRACT_MISSING,
        "stale_reasons": [],
        "transport_rows": [],
        "runtime_root_rows": [],
        "missing_runtime_roots": [],
        "evidence_ref": str(pack_path / "CURRENT_TASK.json"),
    }

    if not isinstance(contract, dict) or required_contract is not True:
        payload["stale_reasons"] = ["identity_communication_transport_contract_missing_or_not_required"]
        return payload

    contract_stale_reasons: list[str] = []
    if str(contract.get("validator", "")).strip() != "scripts/validate_identity_communication_transport.py":
        contract_stale_reasons.append("identity_communication_transport_validator_mismatch")
    if str(contract.get("convergence_executor", "")).strip() != "scripts/run_identity_communication_transport.py":
        contract_stale_reasons.append("identity_communication_transport_convergence_executor_mismatch")
    if str(contract.get("migration_closure_checker", "")).strip() != "scripts/check_identity_communication_transport_closure.py":
        contract_stale_reasons.append("identity_communication_transport_migration_checker_mismatch")
    required_component_contract_keys = {
        str(item).strip()
        for item in (_identity_communication_transport_contract_skeleton().get("required_component_contract_keys", []) or [])
        if str(item).strip()
    }
    declared_component_contract_keys = {
        str(item).strip()
        for item in (contract.get("required_component_contract_keys") or [])
        if str(item).strip()
    }
    if not required_component_contract_keys.issubset(declared_component_contract_keys):
        contract_stale_reasons.append("identity_communication_transport_component_contract_keys_incomplete")
    required_live_bootstrap_steps = {
        str(item).strip()
        for item in (_identity_communication_transport_contract_skeleton().get("required_live_bootstrap_steps", []) or [])
        if str(item).strip()
    }
    declared_live_bootstrap_steps = {
        str(item).strip()
        for item in (contract.get("required_live_bootstrap_steps") or [])
        if str(item).strip()
    }
    if not required_live_bootstrap_steps.issubset(declared_live_bootstrap_steps):
        contract_stale_reasons.append("identity_communication_transport_live_bootstrap_steps_incomplete")

    if contract_stale_reasons:
        payload["stale_reasons"] = contract_stale_reasons
        return payload

    payload["communication_contract_status"] = STATUS_PASS_REQUIRED

    runtime_root_rows, missing_runtime_roots = _runtime_root_rows(pack_path=pack_path, contract=contract)
    payload["runtime_root_rows"] = runtime_root_rows
    payload["missing_runtime_roots"] = missing_runtime_roots
    if not missing_runtime_roots:
        payload["communication_runtime_roots_status"] = STATUS_PASS_REQUIRED

    rows = [
        _validate_handoff_component(task_doc=task_doc, pack_path=pack_path, identity_id=identity_id),
        _validate_collaboration_component(task_doc=task_doc, pack_path=pack_path, identity_id=identity_id),
        _validate_reply_component(
            repo_root=repo_root,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            task_doc=task_doc,
            identity_id=identity_id,
        ),
        _validate_inbox_component(
            repo_root=repo_root,
            catalog_path=catalog_path,
            task_doc=task_doc,
            identity_id=identity_id,
        ),
        _validate_atomic_component(
            repo_root=repo_root,
            catalog_path=catalog_path,
            task_doc=task_doc,
            identity_id=identity_id,
        ),
        _validate_broadcast_component(
            repo_root=repo_root,
            catalog_path=catalog_path,
            task_doc=task_doc,
            identity_id=identity_id,
        ),
    ]
    payload["transport_rows"] = rows
    status_by_component = {str(row.get("component")): str(row.get("status", "")).strip().upper() for row in rows}
    payload["handoff_transport_status"] = status_by_component.get("handoff_transport", STATUS_FAIL_REQUIRED)
    payload["collaboration_transport_status"] = status_by_component.get("collaboration_transport", STATUS_FAIL_REQUIRED)
    payload["protocol_feedback_reply_transport_status"] = status_by_component.get(
        "protocol_feedback_reply_transport", STATUS_FAIL_REQUIRED
    )
    payload["protocol_feedback_inbox_transport_status"] = status_by_component.get(
        "protocol_feedback_inbox_transport", STATUS_FAIL_REQUIRED
    )
    payload["protocol_feedback_atomic_transport_status"] = status_by_component.get(
        "protocol_feedback_atomic_transport", STATUS_FAIL_REQUIRED
    )
    payload["broadcast_transport_status"] = status_by_component.get("broadcast_transport", STATUS_FAIL_REQUIRED)

    stale_reasons: list[str] = []
    if missing_runtime_roots:
        stale_reasons.extend(f"missing_runtime_root:{item}" for item in missing_runtime_roots)
    for row in rows:
        if str(row.get("status", "")).strip().upper() == STATUS_PASS_REQUIRED:
            continue
        component = str(row.get("component", "")).strip() or "component"
        row_reasons = [str(item).strip() for item in (row.get("stale_reasons") or []) if str(item).strip()]
        if row_reasons:
            stale_reasons.extend(f"{component}:{reason}" for reason in row_reasons)
        else:
            stale_reasons.append(f"{component}:failed")

    payload["stale_reasons"] = stale_reasons
    if not stale_reasons and payload["communication_runtime_roots_status"] == STATUS_PASS_REQUIRED:
        payload["identity_communication_transport_status"] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""
        return payload

    payload["error_code"] = (
        ERR_COMMUNICATION_RUNTIME_ROOTS
        if missing_runtime_roots
        else ERR_COMMUNICATION_COMPONENT_FAILURE
    )
    return payload
