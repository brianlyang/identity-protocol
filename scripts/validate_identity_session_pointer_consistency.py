#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import (
    ACTOR_GLOBAL_LAST_MUTATION_PROJECTION_SCOPE,
    AUTHORITATIVE_BINDING_RULE,
    COMPATIBILITY_PROJECTION_STATUS_AVAILABLE,
    COMPATIBILITY_PROJECTION_STATUS_SUPPRESSED_MULTI_IDENTITY,
    COMPATIBILITY_PROJECTION_STATUS_UNAVAILABLE,
    load_actor_binding,
    resolve_actor_id,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json root must be object: {path}")
    return data


def _default_canonical_out(catalog_path: Path) -> Path:
    return (catalog_path.parent / "session" / "active_identity.json").resolve()


def _default_mirror_out(catalog_path: Path) -> Path:
    return (catalog_path.parent / "session" / "mirror" / "current.json").resolve()


def _validate_pointer(
    *,
    pointer_path: Path,
    pointer_name: str,
    catalog_path: Path,
    active_identity_id: str,
    active_pack_path: str,
    require_compatibility_metadata: bool = False,
) -> tuple[bool, str, dict[str, Any]]:
    if not pointer_path.exists():
        return False, f"{pointer_name}_missing:{pointer_path}", {}
    try:
        payload = _load_json(pointer_path)
    except Exception as exc:
        return False, f"{pointer_name}_invalid_json:{exc}", {}

    projection_status = str(payload.get("compatibility_projection_status", "")).strip()
    if projection_status == COMPATIBILITY_PROJECTION_STATUS_SUPPRESSED_MULTI_IDENTITY:
        if require_compatibility_metadata:
            if str(payload.get("authority_role", "")).strip() != "compatibility_mirror":
                return False, f"{pointer_name}_authority_role_missing_or_invalid", payload
            if str(payload.get("authoritative_binding_rule", "")).strip() != AUTHORITATIVE_BINDING_RULE:
                return False, f"{pointer_name}_authoritative_binding_rule_missing_or_invalid", payload
            if payload.get("authoritative_decision_allowed") is not False:
                return False, f"{pointer_name}_authoritative_decision_allowed_not_false", payload
        return False, f"{pointer_name}_projection_suppressed_multi_identity", payload

    pointer_identity_id = str(payload.get("identity_id", "")).strip()
    if pointer_identity_id != active_identity_id:
        return (
            False,
            f"{pointer_name}_identity_mismatch:pointer={pointer_identity_id} active={active_identity_id}",
            payload,
        )

    pointer_status = str(payload.get("status", "")).strip().lower()
    if pointer_status != "active":
        return False, f"{pointer_name}_status_not_active:{pointer_status}", payload

    pointer_catalog = str(payload.get("catalog_path", "")).strip()
    if pointer_catalog:
        try:
            pointer_catalog_path = Path(pointer_catalog).expanduser().resolve()
        except Exception:
            pointer_catalog_path = Path(pointer_catalog)
        if pointer_catalog_path != catalog_path:
            return (
                False,
                f"{pointer_name}_catalog_mismatch:pointer={pointer_catalog_path} expected={catalog_path}",
                payload,
            )

    pointer_pack = str(payload.get("pack_path", "")).strip()
    if pointer_pack and active_pack_path and pointer_pack != active_pack_path:
        return (
            False,
            f"{pointer_name}_pack_mismatch:pointer={pointer_pack} expected={active_pack_path}",
            payload,
        )

    if require_compatibility_metadata:
        if str(payload.get("authority_role", "")).strip() != "compatibility_mirror":
            return False, f"{pointer_name}_authority_role_missing_or_invalid", payload
        if str(payload.get("authoritative_binding_rule", "")).strip() != AUTHORITATIVE_BINDING_RULE:
            return False, f"{pointer_name}_authoritative_binding_rule_missing_or_invalid", payload
        if payload.get("authoritative_decision_allowed") is not False:
            return False, f"{pointer_name}_authoritative_decision_allowed_not_false", payload
        if not str(payload.get("authoritative_binding_store_root", "")).strip():
            return False, f"{pointer_name}_authoritative_binding_store_root_missing", payload
        if not str(payload.get("pointer_semantics_version", "")).strip():
            return False, f"{pointer_name}_pointer_semantics_version_missing", payload

    return True, "ok", payload


def _validate_compatibility_projection_exception(
    *,
    payload: dict[str, Any],
    expected_identity_id: str,
    actor_id: str,
    session_id: str,
) -> tuple[bool, str]:
    projection_status = str(payload.get("compatibility_projection_status", "")).strip()
    if projection_status == COMPATIBILITY_PROJECTION_STATUS_SUPPRESSED_MULTI_IDENTITY:
        if str(payload.get("authority_role", "")).strip() != "compatibility_mirror":
            return False, "compatibility_projection_authority_role_invalid"
        if payload.get("authoritative_decision_allowed") is not False:
            return False, "compatibility_projection_decision_flag_invalid"
        if str(payload.get("compatibility_projection_reason", "")).strip() != "multiple_session_primary_identity_ids":
            return False, "compatibility_projection_reason_invalid"
        candidate_ids = [
            str(item).strip()
            for item in (payload.get("compatibility_projection_candidate_identity_ids") or [])
            if str(item).strip()
        ]
        if expected_identity_id not in candidate_ids:
            return False, "compatibility_projection_candidates_missing_expected_identity"
        return True, "compatibility_projection_suppressed_multi_identity"
    if projection_status == COMPATIBILITY_PROJECTION_STATUS_UNAVAILABLE:
        if str(payload.get("authority_role", "")).strip() != "compatibility_mirror":
            return False, "compatibility_projection_authority_role_invalid"
        if payload.get("authoritative_decision_allowed") is not False:
            return False, "compatibility_projection_decision_flag_invalid"
        if str(payload.get("identity_id", "")).strip():
            return False, "compatibility_projection_identity_expected_empty"
        return True, "compatibility_projection_unavailable_by_policy"
    if projection_status == COMPATIBILITY_PROJECTION_STATUS_AVAILABLE:
        return False, "compatibility_projection_available_diagnostic_only"

    pointer_identity_id = str(payload.get("identity_id", "")).strip()
    if not pointer_identity_id:
        return False, "compatibility_projection_identity_missing"
    if pointer_identity_id == expected_identity_id:
        return False, "compatibility_projection_drift_not_needed"
    if str(payload.get("authority_role", "")).strip() != "compatibility_mirror":
        return False, "compatibility_projection_authority_role_invalid"
    if payload.get("authoritative_decision_allowed") is not False:
        return False, "compatibility_projection_decision_flag_invalid"
    if str(payload.get("compatibility_projection_scope", "")).strip() != ACTOR_GLOBAL_LAST_MUTATION_PROJECTION_SCOPE:
        return False, "compatibility_projection_scope_invalid"
    if str(payload.get("compatibility_projection_role", "")).strip() != "compatibility_projection":
        return False, "compatibility_projection_role_invalid"
    if str(payload.get("compatibility_projection_actor_id", "")).strip() != actor_id:
        return False, "compatibility_projection_actor_mismatch"
    if str(payload.get("compatibility_projection_identity_id", "")).strip() != pointer_identity_id:
        return False, "compatibility_projection_identity_mismatch"
    projection_session_id = str(payload.get("compatibility_projection_session_id", "")).strip()
    if not projection_session_id:
        return False, "compatibility_projection_session_missing"
    if projection_session_id == session_id:
        return False, "compatibility_projection_not_cross_session"
    if not str(payload.get("compatibility_projection_binding_ref", "")).strip():
        return False, "compatibility_projection_binding_ref_missing"
    return True, "compatibility_projection_cross_session_drift"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate session pointer consistency under actor-scoped binding (multi-active aware)."
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", default="", help="optional: require this identity to be current active")
    ap.add_argument("--actor-id", default="", help="optional actor id for actor-scoped expected identity resolution")
    ap.add_argument("--session-id", default="", help="optional actor session selector (run:<id>) for strict M:N binding checks")
    ap.add_argument(
        "--canonical-out",
        default="",
        help="canonical session pointer path (default: <catalog_dir>/session/active_identity.json)",
    )
    ap.add_argument(
        "--mirror-out",
        default="",
        help=(
            "mirror pointer path; default: <catalog_dir>/session/mirror/current.json. "
            "empty disables mirror check"
        ),
    )
    ap.add_argument(
        "--legacy-mirror-out",
        default="",
        help=(
            "optional legacy mirror pointer path (for compatibility only, e.g. /tmp/identity-session/current.json). "
            "empty disables legacy mirror check"
        ),
    )
    ap.add_argument(
        "--require-mirror",
        action="store_true",
        help="fail if mirror/legacy-mirror pointer is missing or inconsistent (default: warning-only)",
    )
    ap.add_argument(
        "--strict-session-primary",
        action="store_true",
        help=(
            "enforce session-primary semantics for strict lanes: "
            "canonical/mirror identity mismatches and missing mirror become fail-close even under multi-active."
        ),
    )
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 1

    data = _load_yaml(catalog_path)
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    active_rows = [x for x in rows if str(x.get("status", "")).strip().lower() == "active"]
    active_ids = [str(x.get("id", "")).strip() for x in active_rows if str(x.get("id", "")).strip()]
    actor_id = resolve_actor_id(args.actor_id)
    session_id = str(args.session_id or "").strip()
    expected_identity_id = str(args.identity_id or "").strip()
    actor_binding = load_actor_binding(
        catalog_path,
        actor_id,
        identity_id=expected_identity_id,
        session_id=session_id,
    )
    bound_identity_id = str(actor_binding.get("identity_id", "")).strip()
    if not expected_identity_id:
        if bound_identity_id:
            expected_identity_id = bound_identity_id
        else:
            fallback_binding = load_actor_binding(catalog_path, actor_id, session_id=session_id)
            bound_identity_id = str(fallback_binding.get("identity_id", "")).strip()
            if bound_identity_id:
                expected_identity_id = bound_identity_id
        if not expected_identity_id and len(active_rows) == 1:
            expected_identity_id = str(active_rows[0].get("id", "")).strip()
    if not expected_identity_id:
        print(
            "[FAIL] expected identity is ambiguous under multi-active catalog; "
            f"active_identities={active_ids}. Pass --identity-id or --actor-id with actor binding."
        )
        return 1

    expected_row = next((x for x in rows if str(x.get("id", "")).strip() == expected_identity_id), None)
    if not expected_row:
        print(f"[FAIL] expected identity not found in catalog: {expected_identity_id}")
        return 1
    expected_status = str(expected_row.get("status", "")).strip().lower()
    if expected_status != "active":
        print(f"[FAIL] expected identity is not active: identity={expected_identity_id} status={expected_status}")
        return 1
    expected_pack_path = str(expected_row.get("pack_path", "")).strip()

    if args.identity_id.strip() and bound_identity_id and bound_identity_id != expected_identity_id:
        print(
            "[WARN] actor binding targets a different identity than requested identity: "
            f"actor={actor_id} bound={bound_identity_id} requested={expected_identity_id}"
        )

    canonical_out = (
        Path(args.canonical_out).expanduser().resolve()
        if args.canonical_out.strip()
        else _default_canonical_out(catalog_path)
    )
    require_mirror_effective = bool(args.require_mirror or args.strict_session_primary)
    compatibility_projection_drift_detected = False
    compatibility_projection_payload: dict[str, Any] = {}
    compatibility_projection_drift_check_enabled = bool(
        args.strict_session_primary and actor_id and session_id
    )

    ok, reason, pointer_payload = _validate_pointer(
        pointer_path=canonical_out,
        pointer_name="canonical",
        catalog_path=catalog_path,
        active_identity_id=expected_identity_id,
        active_pack_path=expected_pack_path,
        require_compatibility_metadata=bool(args.strict_session_primary),
    )
    if not ok:
        allow_compatibility_projection_drift = False
        if (
            compatibility_projection_drift_check_enabled
            and (
                reason.startswith("canonical_identity_mismatch:")
                or reason == "canonical_projection_suppressed_multi_identity"
            )
        ):
            allow_compatibility_projection_drift, drift_reason = _validate_compatibility_projection_exception(
                payload=pointer_payload,
                expected_identity_id=expected_identity_id,
                actor_id=actor_id,
                session_id=session_id,
            )
            if allow_compatibility_projection_drift:
                compatibility_projection_drift_detected = True
                compatibility_projection_payload = dict(pointer_payload)
                print(f"[INFO] canonical compatibility projection drift acknowledged: {drift_reason}")
        allow_multi_active_identity_mismatch = (
            (not args.strict_session_primary)
            and len(active_rows) > 1
            and reason.startswith("canonical_identity_mismatch:")
        )
        if allow_compatibility_projection_drift:
            pass
        elif allow_multi_active_identity_mismatch:
            print(f"[WARN] {reason} (allowed under actor-scoped multi-active model)")
        else:
            print(f"[FAIL] {reason}")
            return 1

    mirror_targets: list[Path] = []
    mirror_raw = args.mirror_out.strip()
    if mirror_raw:
        mirror_targets.append(Path(mirror_raw).expanduser().resolve())
    else:
        mirror_targets.append(_default_mirror_out(catalog_path))
    legacy_mirror_raw = args.legacy_mirror_out.strip()
    if legacy_mirror_raw:
        mirror_targets.append(Path(legacy_mirror_raw).expanduser().resolve())

    seen: set[str] = set()
    dedup_targets: list[Path] = []
    for t in mirror_targets:
        k = str(t)
        if k in seen:
            continue
        seen.add(k)
        dedup_targets.append(t)

    for i, mirror_out in enumerate(dedup_targets, start=1):
        pointer_name = "mirror" if i == 1 else f"mirror_{i}"
        if mirror_out.exists():
            ok, reason, pointer_payload = _validate_pointer(
                pointer_path=mirror_out,
                pointer_name=pointer_name,
                catalog_path=catalog_path,
                active_identity_id=expected_identity_id,
                active_pack_path=expected_pack_path,
                require_compatibility_metadata=bool(args.strict_session_primary),
            )
            if not ok:
                allow_compatibility_projection_drift = False
                if (
                    compatibility_projection_drift_check_enabled
                    and (
                        reason.startswith(f"{pointer_name}_identity_mismatch:")
                        or reason == f"{pointer_name}_projection_suppressed_multi_identity"
                    )
                ):
                    allow_compatibility_projection_drift, drift_reason = _validate_compatibility_projection_exception(
                        payload=pointer_payload,
                        expected_identity_id=expected_identity_id,
                        actor_id=actor_id,
                        session_id=session_id,
                    )
                    if allow_compatibility_projection_drift:
                        compatibility_projection_drift_detected = True
                        if not compatibility_projection_payload:
                            compatibility_projection_payload = dict(pointer_payload)
                        print(f"[INFO] {pointer_name} compatibility projection drift acknowledged: {drift_reason}")
                allow_multi_active_identity_mismatch = (
                    (not args.strict_session_primary)
                    and len(active_rows) > 1
                    and reason.startswith(f"{pointer_name}_identity_mismatch:")
                )
                if allow_compatibility_projection_drift:
                    continue
                if allow_multi_active_identity_mismatch and not require_mirror_effective:
                    print(f"[WARN] {reason} (allowed under actor-scoped multi-active model)")
                    continue
                if require_mirror_effective:
                    print(f"[FAIL] {reason}")
                    return 1
                print(f"[WARN] {reason}")
                continue
            print(f"[OK] {pointer_name} pointer aligned: {mirror_out}")
            continue
        if require_mirror_effective:
            print(f"[FAIL] {pointer_name}_missing:{mirror_out}")
            return 1
        print(f"[WARN] {pointer_name} pointer not found (allowed): {mirror_out}")

    print(
        "[OK] session pointer consistency validated: "
        f"expected_identity={expected_identity_id} actor={actor_id} "
        f"session_id={session_id or '<auto>'} "
        f"active_count={len(active_rows)} catalog={catalog_path} canonical={canonical_out} "
        f"compatibility_projection_drift={'yes' if compatibility_projection_drift_detected else 'no'} "
        f"projection_status={str(compatibility_projection_payload.get('compatibility_projection_status', '')).strip() or '<none>'} "
        f"projection_session={str(compatibility_projection_payload.get('compatibility_projection_session_id', '')).strip() or '<none>'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
