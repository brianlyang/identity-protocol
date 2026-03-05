#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import (
    LEGACY_BINDING_KEY_MODE,
    actor_session_path,
    load_actor_binding_store,
    normalize_actor_binding_store,
    resolve_actor_id,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

STRICT_OPS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPS = {"scan", "three-plane", "inspection"}

ERR_MB_001 = "IP-ASB-MB-001"
ERR_MB_002 = "IP-ASB-MB-002"
ERR_MB_003 = "IP-ASB-MB-003"
ERR_MB_004 = "IP-ASB-MB-004"
ERR_MB_005 = "IP-ASB-MB-005"
ERR_MB_006 = "IP-ASB-MB-006"

RECEIPT_REQUIRED_FIELDS = (
    "from_binding_ref",
    "to_binding_ref",
    "actor_id",
    "session_id",
    "run_id",
    "switch_reason",
    "approved_by",
    "applied_at",
)


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {}


def _identity_row(catalog_path: Path, identity_id: str) -> dict[str, Any] | None:
    if not identity_id:
        return None
    rows = [x for x in (_load_catalog(catalog_path).get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)


def _is_fixture_identity(row: dict[str, Any] | None) -> bool:
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _latest_receipt(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    if not receipts:
        return {}
    return receipts[-1]


def _finalize_status(
    *,
    operation: str,
    status: str,
    stale_reasons: list[str],
    error_code: str,
) -> tuple[str, str]:
    if status == STATUS_FAIL_REQUIRED and operation in INSPECTION_OPS:
        return STATUS_WARN_NON_BLOCKING, error_code
    if status == STATUS_PASS_REQUIRED and stale_reasons and operation in INSPECTION_OPS:
        return STATUS_WARN_NON_BLOCKING, error_code
    return status, error_code


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate same-actor multi-session binding concurrency contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--actor-session-json", default="", help="optional direct actor session payload for replay")
    ap.add_argument("--expected-compare-token", default="", help="optional expected compare token for CAS replay")
    ap.add_argument(
        "--operation",
        choices=sorted(STRICT_OPS | INSPECTION_OPS),
        default="validate",
        help="strict operations fail-closed, inspection operations downgrade to warning",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    actor_id = resolve_actor_id(args.actor_id)
    actor_path = actor_session_path(catalog_path, actor_id)
    identity_id = str(args.identity_id or "").strip()
    fixture_mode = _is_fixture_identity(_identity_row(catalog_path, identity_id))

    raw_payload: dict[str, Any] = {}
    if args.actor_session_json.strip():
        raw_path = Path(args.actor_session_json).expanduser().resolve()
        raw_payload = _load_json(raw_path)
        if raw_payload:
            actor_path = raw_path
    else:
        raw_payload = _load_json(actor_path)

    store = (
        normalize_actor_binding_store(
            data=raw_payload,
            actor_id=actor_id,
            catalog_path=catalog_path,
            actor_session_file=actor_path,
        )
        if raw_payload
        else load_actor_binding_store(catalog_path, actor_id)
    )
    bindings = [x for x in (store.get("bindings") or []) if isinstance(x, dict)]
    receipts = [x for x in (store.get("rebind_receipts") or []) if isinstance(x, dict)]

    binding_key_mode = str(store.get("binding_key_mode", "")).strip()
    compare_token = str(store.get("compare_token", "")).strip()
    try:
        binding_version = int(store.get("binding_version", 0))
    except Exception:
        binding_version = 0
    session_entry_count = int(store.get("session_entry_count", len(bindings)) or 0)
    stale_reasons = [str(x).strip() for x in (store.get("stale_reasons") or []) if str(x).strip()]
    error_code = ""
    status = STATUS_PASS_REQUIRED
    cas_checked = bool(compare_token and session_entry_count > 0)
    cas_conflict_detected = False
    non_activation_mutation_detected = False
    dropped_peer_session_count = 0
    rebind_receipt_status = STATUS_PASS_REQUIRED
    operation = str(args.operation or "validate").strip().lower()

    if fixture_mode:
        status = STATUS_SKIPPED_NOT_REQUIRED
        stale_reasons.append("fixture_profile_scope")

    if not actor_path.exists() and not raw_payload:
        status = STATUS_SKIPPED_NOT_REQUIRED
        stale_reasons.append("actor_binding_store_missing")

    if status == STATUS_PASS_REQUIRED and session_entry_count <= 0:
        status = STATUS_SKIPPED_NOT_REQUIRED
        stale_reasons.append("actor_binding_entries_missing")

    if status == STATUS_PASS_REQUIRED and binding_key_mode == LEGACY_BINDING_KEY_MODE:
        error_code = ERR_MB_001
        status = STATUS_FAIL_REQUIRED
        stale_reasons.append("single_record_overwrite_shape_detected")

    if status == STATUS_PASS_REQUIRED and (
        (not compare_token)
        or (binding_version < 0)
        or ("compare_token_missing" in stale_reasons)
        or ("binding_version_missing" in stale_reasons)
    ):
        error_code = ERR_MB_002
        status = STATUS_FAIL_REQUIRED
        stale_reasons.append("compare_token_missing_or_invalid")

    expected_compare = str(args.expected_compare_token or "").strip()
    if status == STATUS_PASS_REQUIRED and expected_compare and compare_token and expected_compare != compare_token:
        error_code = ERR_MB_003
        status = STATUS_FAIL_REQUIRED
        stale_reasons.append("compare_token_conflict")
        cas_conflict_detected = True

    last_mutation = store.get("last_mutation") if isinstance(store.get("last_mutation"), dict) else {}
    if status == STATUS_PASS_REQUIRED and last_mutation:
        lane = str(last_mutation.get("mutation_lane", "")).strip().lower()
        override_receipt = str(last_mutation.get("governance_override_receipt", "")).strip()
        if lane and lane != "activate" and not override_receipt:
            error_code = ERR_MB_004
            status = STATUS_FAIL_REQUIRED
            stale_reasons.append("non_activation_mutation_without_override")
            non_activation_mutation_detected = True
        before = str(last_mutation.get("compare_token_before", "")).strip()
        after = str(last_mutation.get("compare_token_after", "")).strip()
        if before and after and before == after:
            error_code = ERR_MB_003
            status = STATUS_FAIL_REQUIRED
            stale_reasons.append("compare_token_not_incremented")
            cas_conflict_detected = True
        if bool(last_mutation.get("cas_conflict_detected")):
            error_code = ERR_MB_003
            status = STATUS_FAIL_REQUIRED
            stale_reasons.append("cas_conflict_detected")
            cas_conflict_detected = True
        dropped = last_mutation.get("dropped_peer_sessions")
        if isinstance(dropped, list):
            dropped_peer_session_count = len([x for x in dropped if str(x).strip()])
            if dropped_peer_session_count > 0:
                error_code = ERR_MB_006
                status = STATUS_FAIL_REQUIRED
                stale_reasons.append("peer_sessions_dropped")

    if status == STATUS_PASS_REQUIRED:
        latest_receipt = _latest_receipt(receipts)
        missing_receipt_fields = [
            k for k in RECEIPT_REQUIRED_FIELDS if not str(latest_receipt.get(k, "")).strip()
        ]
        if not receipts or missing_receipt_fields:
            error_code = ERR_MB_005
            status = STATUS_FAIL_REQUIRED
            rebind_receipt_status = STATUS_FAIL_REQUIRED
            stale_reasons.append(
                "rebind_receipt_missing_or_incomplete"
                if not missing_receipt_fields
                else f"rebind_receipt_missing_fields:{','.join(missing_receipt_fields)}"
            )

    if status == STATUS_PASS_REQUIRED:
        # session_id uniqueness contract check
        session_ids = [str(x.get("session_id", "")).strip() for x in bindings if str(x.get("session_id", "")).strip()]
        if len(session_ids) != len(set(session_ids)):
            error_code = ERR_MB_001
            status = STATUS_FAIL_REQUIRED
            stale_reasons.append("duplicate_session_id_entries")

    status, error_code = _finalize_status(
        operation=operation,
        status=status,
        stale_reasons=stale_reasons,
        error_code=error_code,
    )
    if status == STATUS_WARN_NON_BLOCKING and rebind_receipt_status == STATUS_FAIL_REQUIRED:
        rebind_receipt_status = STATUS_WARN_NON_BLOCKING

    payload = {
        "identity_id": identity_id,
        "catalog_path": str(catalog_path),
        "actor_id": actor_id,
        "operation": operation,
        "actor_session_path": str(actor_path),
        "actor_session_multibinding_status": status,
        "error_code": error_code,
        "binding_key_mode": binding_key_mode,
        "session_entry_count": session_entry_count,
        "cas_checked": cas_checked,
        "cas_conflict_detected": cas_conflict_detected,
        "non_activation_mutation_detected": non_activation_mutation_detected,
        "rebind_receipt_status": rebind_receipt_status,
        "dropped_peer_session_count": dropped_peer_session_count,
        "compare_token": compare_token,
        "binding_version": binding_version,
        "stale_reasons": sorted(set(stale_reasons)),
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if status in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED, STATUS_WARN_NON_BLOCKING}:
            print(
                "[OK] actor session multibinding concurrency validated: "
                f"actor={actor_id} status={status} path={actor_path}"
            )
        else:
            print(
                f"[FAIL] {error_code or ERR_MB_001} actor session multibinding concurrency validation failed: "
                f"actor={actor_id} path={actor_path}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if status in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED, STATUS_WARN_NON_BLOCKING} else 1


if __name__ == "__main__":
    raise SystemExit(main())
