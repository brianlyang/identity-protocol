#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from actor_session_common import (
    list_session_primary_conflicts,
    load_actor_binding,
    load_actor_binding_store,
    resolve_required_protocol_actor_id,
)
from identity_runtime_authority_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    validate_runtime_egress_identity_authority,
)
from resolve_identity_context import default_local_catalog_path

ERR_RUNTIME_AUTHORITY_RESOLVE = "IP-AUTH-RESOLVE-001"
SCRIPT_DIR = Path(__file__).resolve().parent
AUTHORITY_CONSUMER_EXEMPT = True  # Resolver utility; not a direct reply/headstamp consumer.


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _fail_payload(
    *,
    catalog_path: Path,
    actor_id: str,
    session_id: str,
    requested_identity_id: str,
    resolution_mode: str,
    stale_reasons: list[str],
    next_action: str,
    conflict: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "runtime_authoritative_identity_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_RUNTIME_AUTHORITY_RESOLVE,
        "catalog_path": str(catalog_path),
        "actor_id": actor_id,
        "session_id": session_id,
        "requested_identity_id": requested_identity_id,
        "authoritative_identity_id": "",
        "resolution_mode": resolution_mode,
        "stale_reasons": stale_reasons,
        "next_action": next_action,
    }
    if conflict:
        payload["session_primary_conflict"] = conflict
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Resolve the current session-primary runtime identity and fail-close when only compatibility projection is available."
    )
    ap.add_argument("--catalog", default=str(default_local_catalog_path(start=SCRIPT_DIR)))
    ap.add_argument("--actor-id", default="", help="explicit actor id; falls back to CODEX_ACTOR_ID")
    ap.add_argument("--session-id", default="", help="required session-primary selector (run:<id>)")
    ap.add_argument(
        "--identity-id",
        default="",
        help="optional expected identity id; when provided it must match the session-primary authoritative identity",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    requested_identity_id = str(args.identity_id or "").strip()
    session_id = str(args.session_id or "").strip()

    try:
        actor_id = resolve_required_protocol_actor_id(str(args.actor_id or "").strip())
    except ValueError:
        payload = _fail_payload(
            catalog_path=catalog_path,
            actor_id="",
            session_id=session_id,
            requested_identity_id=requested_identity_id,
            resolution_mode="actor_context_missing",
            stale_reasons=["actor_context_missing", "authoritative_identity_unresolved"],
            next_action="pass_actor_id_or_set_CODEX_ACTOR_ID_then_retry",
        )
        _emit(payload, json_only=args.json_only)
        return 1

    if not session_id:
        payload = _fail_payload(
            catalog_path=catalog_path,
            actor_id=actor_id,
            session_id="",
            requested_identity_id=requested_identity_id,
            resolution_mode="session_context_missing",
            stale_reasons=[f"session_context_missing:actor_id={actor_id}"],
            next_action="pass_session_id_or_set_CODEX_SESSION_ID_then_retry",
        )
        _emit(payload, json_only=args.json_only)
        return 1

    binding = load_actor_binding(catalog_path, actor_id, session_id=session_id)
    authoritative_identity_id = str(binding.get("identity_id", "")).strip()
    if not authoritative_identity_id:
        store = load_actor_binding_store(catalog_path, actor_id)
        conflicts = list_session_primary_conflicts(store, session_id=session_id)
        if conflicts:
            conflict = conflicts[0]
            payload = _fail_payload(
                catalog_path=catalog_path,
                actor_id=actor_id,
                session_id=session_id,
                requested_identity_id=requested_identity_id,
                resolution_mode="actor_binding_session_primary_conflict",
                stale_reasons=[
                    "session_primary_identity_conflict:"
                    f"session_id={session_id}:"
                    f"identities={','.join(str(x).strip() for x in (conflict.get('identity_ids') or []) if str(x).strip()) or 'missing'}"
                ],
                next_action="repair_session_primary_conflict_then_retry",
                conflict=conflict,
            )
            _emit(payload, json_only=args.json_only)
            return 1

        payload = _fail_payload(
            catalog_path=catalog_path,
            actor_id=actor_id,
            session_id=session_id,
            requested_identity_id=requested_identity_id,
            resolution_mode="actor_binding_session_binding_missing",
            stale_reasons=[f"session_primary_identity_missing:actor_id={actor_id}:session_id={session_id}"],
            next_action="bind_session_primary_identity_then_retry",
        )
        _emit(payload, json_only=args.json_only)
        return 1

    selected_identity_id = requested_identity_id or authoritative_identity_id
    authority_payload = validate_runtime_egress_identity_authority(
        catalog_path=catalog_path,
        identity_id=selected_identity_id,
        actor_id=actor_id,
        session_id=session_id,
    )
    payload: dict[str, Any] = {
        "runtime_authoritative_identity_status": str(
            authority_payload.get("identity_authority_status", STATUS_FAIL_REQUIRED)
        ).strip(),
        "error_code": str(authority_payload.get("identity_authority_error_code", "")).strip(),
        "catalog_path": str(catalog_path),
        "actor_id": actor_id,
        "session_id": session_id,
        "requested_identity_id": requested_identity_id,
        "selected_identity_id": selected_identity_id,
        "authoritative_identity_id": authoritative_identity_id,
        "resolution_mode": str(authority_payload.get("identity_authority_resolution_mode", "")).strip(),
        "stale_reasons": list(authority_payload.get("identity_authority_stale_reasons", []) or []),
        "next_action": str(authority_payload.get("identity_authority_next_action", "")).strip(),
        "identity_authority_payload": authority_payload,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if payload["runtime_authoritative_identity_status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
