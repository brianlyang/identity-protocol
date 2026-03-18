#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from actor_session_common import (
    list_session_primary_conflicts,
    load_actor_binding,
    load_actor_binding_store,
    resolve_protocol_actor_id,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
AUTHORITY_CONSUMER_EXEMPT = True  # Provider module; not a direct authority-consuming surface.

ERR_IDENTITY_AUTHORITY_VIOLATION = "IP-IAUTH-001"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data

def _identity_row(rows: list[dict[str, Any]], identity_id: str) -> dict[str, Any] | None:
    target = str(identity_id or "").strip()
    if not target:
        return None
    return next((row for row in rows if str(row.get("id", "")).strip() == target), None)


def _identity_runtime_meta(row: dict[str, Any] | None) -> dict[str, Any]:
    node = row if isinstance(row, dict) else {}
    status = str(node.get("status", "")).strip().lower()
    profile = str(node.get("profile", "")).strip().lower()
    runtime_mode = str(node.get("runtime_mode", "")).strip().lower()
    runtime_eligible = bool(
        status == "active"
        and profile != "fixture"
        and runtime_mode != "demo_only"
    )
    stale_reasons: list[str] = []
    if status != "active":
        stale_reasons.append(f"identity_status_not_active:{status or 'missing'}")
    if profile == "fixture":
        stale_reasons.append("identity_profile_fixture")
    if runtime_mode == "demo_only":
        stale_reasons.append("identity_runtime_mode_demo_only")
    return {
        "status": status,
        "profile": profile,
        "runtime_mode": runtime_mode,
        "runtime_eligible": runtime_eligible,
        "stale_reasons": stale_reasons,
    }


def _resolve_authoritative_identity(
    *,
    catalog_path: Path,
    actor_id: str,
    session_id: str,
) -> tuple[str, str, dict[str, Any]]:
    actor = resolve_protocol_actor_id(actor_id)
    sid = str(session_id or "").strip()
    if not actor:
        return "", "actor_context_missing", {}

    if not sid:
        store = load_actor_binding_store(catalog_path, actor)
        return "", "actor_binding_session_context_missing", {
            "actor_id": actor,
            "session_id": "",
            "actor_session_path": str(store.get("actor_session_path", "")).strip(),
        }

    binding = load_actor_binding(catalog_path, actor, session_id=sid)
    identity_id = str(binding.get("identity_id", "")).strip()
    if identity_id:
        return identity_id, "actor_binding_session_scoped", binding
    store = load_actor_binding_store(catalog_path, actor)
    conflicts = list_session_primary_conflicts(store, session_id=sid)
    if conflicts:
        return "", "actor_binding_session_primary_conflict", conflicts[0]
    return "", "actor_binding_session_binding_missing", {
        "actor_id": actor,
        "session_id": sid,
        "actor_session_path": str(store.get("actor_session_path", "")).strip(),
    }


def validate_runtime_egress_identity_authority(
    *,
    catalog_path: Path,
    identity_id: str,
    actor_id: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    target_identity_id = str(identity_id or "").strip()
    actor_raw = str(actor_id or "").strip()
    actor = resolve_protocol_actor_id(actor_raw)
    actor_resolution_mode = "explicit" if actor_raw else ("env" if actor else "missing")
    sid = str(session_id or "").strip()

    payload: dict[str, Any] = {
        "identity_authority_status": STATUS_PASS_REQUIRED,
        "identity_authority_error_code": "",
        "identity_authority_selected_identity_id": target_identity_id,
        "identity_authority_authoritative_identity_id": "",
        "identity_authority_resolution_mode": "",
        "identity_authority_selected_status": "",
        "identity_authority_selected_profile": "",
        "identity_authority_selected_runtime_mode": "",
        "identity_authority_selected_runtime_eligible": False,
        "identity_authority_authoritative_status": "",
        "identity_authority_authoritative_profile": "",
        "identity_authority_authoritative_runtime_mode": "",
        "identity_authority_authoritative_runtime_eligible": False,
        "identity_authority_actor_id": actor,
        "identity_authority_actor_resolution_mode": actor_resolution_mode,
        "identity_authority_session_id": sid,
        "identity_authority_stale_reasons": [],
        "identity_authority_next_action": "",
    }

    if not target_identity_id:
        payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
        payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
        payload["identity_authority_stale_reasons"] = ["identity_id_missing"]
        payload["identity_authority_next_action"] = "provide_runtime_identity_id_then_retry"
        return payload

    catalog_doc = _load_yaml(catalog_path)
    rows = [row for row in (catalog_doc.get("identities") or []) if isinstance(row, dict)]
    selected_row = _identity_row(rows, target_identity_id)
    if not selected_row:
        payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
        payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
        payload["identity_authority_stale_reasons"] = [f"identity_not_found_in_catalog:{target_identity_id}"]
        payload["identity_authority_next_action"] = "use_catalog_runtime_identity_then_retry"
        return payload

    selected_meta = _identity_runtime_meta(selected_row)
    payload["identity_authority_selected_status"] = str(selected_meta.get("status", "")).strip()
    payload["identity_authority_selected_profile"] = str(selected_meta.get("profile", "")).strip()
    payload["identity_authority_selected_runtime_mode"] = str(selected_meta.get("runtime_mode", "")).strip()
    payload["identity_authority_selected_runtime_eligible"] = bool(selected_meta.get("runtime_eligible", False))

    authoritative_identity_id, resolution_mode, authority_doc = _resolve_authoritative_identity(
        catalog_path=catalog_path,
        actor_id=actor,
        session_id=sid,
    )
    payload["identity_authority_authoritative_identity_id"] = authoritative_identity_id
    payload["identity_authority_resolution_mode"] = resolution_mode

    if resolution_mode == "actor_binding_session_primary_conflict":
        conflict_session_id = str(authority_doc.get("session_id", "")).strip() or sid
        conflict_identity_ids = [
            str(item).strip()
            for item in (authority_doc.get("identity_ids") or [])
            if str(item).strip()
        ]
        payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
        payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
        payload["identity_authority_stale_reasons"] = [
            "session_primary_identity_conflict:"
            f"session_id={conflict_session_id or 'missing'}:"
            f"identities={','.join(sorted(conflict_identity_ids)) or 'missing'}"
        ]
        payload["identity_authority_next_action"] = "repair_session_primary_conflict_then_retry"
        return payload

    if resolution_mode == "actor_binding_session_binding_missing":
        payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
        payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
        payload["identity_authority_stale_reasons"] = [
            "session_primary_identity_missing:"
            f"actor_id={actor or 'missing'}:"
            f"session_id={sid or 'missing'}"
        ]
        payload["identity_authority_next_action"] = "bind_session_primary_identity_then_retry"
        return payload

    if resolution_mode == "actor_binding_session_context_missing":
        payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
        payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
        payload["identity_authority_stale_reasons"] = [
            f"session_context_missing:actor_id={actor or 'missing'}"
        ]
        payload["identity_authority_next_action"] = "pass_session_id_then_retry"
        return payload

    if resolution_mode == "actor_context_missing":
        payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
        payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
        payload["identity_authority_stale_reasons"] = ["actor_context_missing", "authoritative_identity_unresolved"]
        payload["identity_authority_next_action"] = "pass_actor_id_or_set_CODEX_ACTOR_ID_then_retry"
        return payload

    if resolution_mode == "authority_unresolved":
        payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
        payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
        stale_reasons = ["authoritative_identity_unresolved"]
        next_action = "provide_runtime_authority_context_then_retry"
        if actor_resolution_mode == "missing":
            stale_reasons.insert(0, "actor_context_missing")
            next_action = "pass_actor_id_or_set_CODEX_ACTOR_ID_then_retry"
        payload["identity_authority_stale_reasons"] = stale_reasons
        payload["identity_authority_next_action"] = next_action
        return payload

    if authoritative_identity_id:
        authoritative_row = _identity_row(rows, authoritative_identity_id)
        authoritative_meta = _identity_runtime_meta(authoritative_row)
        payload["identity_authority_authoritative_status"] = str(authoritative_meta.get("status", "")).strip()
        payload["identity_authority_authoritative_profile"] = str(authoritative_meta.get("profile", "")).strip()
        payload["identity_authority_authoritative_runtime_mode"] = str(
            authoritative_meta.get("runtime_mode", "")
        ).strip()
        payload["identity_authority_authoritative_runtime_eligible"] = bool(
            authoritative_meta.get("runtime_eligible", False)
        )

        if authoritative_row is None:
            payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
            payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
            payload["identity_authority_stale_reasons"] = [
                f"authoritative_identity_not_found_in_catalog:{authoritative_identity_id}",
            ]
            payload["identity_authority_next_action"] = "repair_authoritative_identity_binding_then_retry"
            return payload

        if not bool(authoritative_meta.get("runtime_eligible", False)):
            payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
            payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
            authority_reasons = [
                f"authoritative_identity_not_runtime_eligible:{authoritative_identity_id}",
                *[
                    f"authoritative_{reason}"
                    for reason in authoritative_meta.get("stale_reasons", [])
                    if str(reason).strip()
                ],
            ]
            payload["identity_authority_stale_reasons"] = authority_reasons
            payload["identity_authority_next_action"] = "repair_session_primary_runtime_identity_then_retry"
            return payload

    if not bool(selected_meta.get("runtime_eligible", False)):
        payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
        payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
        payload["identity_authority_stale_reasons"] = [
            f"selected_identity_not_runtime_eligible:{target_identity_id}",
            *[
                f"selected_{reason}"
                for reason in selected_meta.get("stale_reasons", [])
                if str(reason).strip()
            ],
        ]
        payload["identity_authority_next_action"] = "select_active_runtime_identity_then_retry"
        return payload

    if authoritative_identity_id and authoritative_identity_id != target_identity_id:
        payload["identity_authority_status"] = STATUS_FAIL_REQUIRED
        payload["identity_authority_error_code"] = ERR_IDENTITY_AUTHORITY_VIOLATION
        payload["identity_authority_stale_reasons"] = [
            f"identity_authority_mismatch:selected={target_identity_id}:authoritative={authoritative_identity_id}:source={resolution_mode}",
        ]
        if resolution_mode.startswith("actor_binding"):
            payload["identity_authority_next_action"] = "use_session_primary_identity_or_run_gated_switch_then_retry"
        elif resolution_mode.startswith("legacy_"):
            payload["identity_authority_next_action"] = "align_canonical_runtime_identity_then_retry"
        else:
            payload["identity_authority_next_action"] = "provide_runtime_authority_context_then_retry"
        return payload

    return payload
