#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

ERR_HDSTAMP_MISSING_OR_MALFORMED = "IP-HDSTAMP-001"
ERR_HDSTAMP_ACTOR_LAYER_MISMATCH = "IP-HDSTAMP-002"
ERR_HDSTAMP_RECEIPT_MISSING = "IP-HDSTAMP-003"
ERR_HDSTAMP_REPLY_EVIDENCE_MISSING = "IP-HDSTAMP-004"

LEGACY_ERROR_ALIAS_MODE_ACTIVE_CANONICAL_ONLY = "active_canonical_only"
LEGACY_ERROR_ALIAS_MODE_REPLAY_MIGRATION = "replay_migration"

# Legacy/compatibility aliases kept for replay migration and historical receipts.
LEGACY_ERR_SEND_TIME_GATE = "IP-ASB-STAMP-SESSION-001"
LEGACY_ERR_SYNTHETIC_EVIDENCE = "IP-ASB-STAMP-SESSION-002"
LEGACY_ERR_OUTLET_GUARD_MISSING = "IP-ASB-STAMP-SESSION-003"
LEGACY_ERR_NON_GOVERNED_OUTLET = "IP-ASB-STAMP-SESSION-004"
LEGACY_ERR_RUNTIME_BINDING_MISMATCH = "IP-ASB-STAMP-SESSION-005"
LEGACY_ERR_FINAL_EMIT_CHANNEL_REQUIRED = "IP-ASB-STAMP-SESSION-006"
LEGACY_ERR_FINAL_EMIT_SCHEMA_REQUIRED = "IP-ASB-STAMP-SESSION-007"

LEGACY_ERR_FINAL_EMIT_BODY_EMPTY = "IP-FE-001"
LEGACY_ERR_FINAL_EMIT_COMPOSE_RUNTIME = "IP-FE-002"
LEGACY_ERR_FINAL_EMIT_COMPOSE_JSON_MISSING = "IP-FE-003"
LEGACY_ERR_FINAL_EMIT_CONTRACT_FAILED = "IP-FE-004"
LEGACY_ERR_FINAL_EMIT_REPLY_FILE_MISSING = "IP-FE-005"
LEGACY_ERR_FINAL_EMIT_CONTEXT_RESOLVE = "IP-FE-006"
LEGACY_ERR_FINAL_EMIT_IDENTITY_RESOLVE = "IP-FE-007"


LEGACY_HEADSTAMP_ERROR_MAP: dict[str, str] = {
    # send-time gate legacy family
    LEGACY_ERR_SEND_TIME_GATE: ERR_HDSTAMP_MISSING_OR_MALFORMED,
    LEGACY_ERR_SYNTHETIC_EVIDENCE: ERR_HDSTAMP_RECEIPT_MISSING,
    LEGACY_ERR_OUTLET_GUARD_MISSING: ERR_HDSTAMP_RECEIPT_MISSING,
    LEGACY_ERR_NON_GOVERNED_OUTLET: ERR_HDSTAMP_RECEIPT_MISSING,
    LEGACY_ERR_RUNTIME_BINDING_MISMATCH: ERR_HDSTAMP_ACTOR_LAYER_MISMATCH,
    LEGACY_ERR_FINAL_EMIT_CHANNEL_REQUIRED: ERR_HDSTAMP_RECEIPT_MISSING,
    LEGACY_ERR_FINAL_EMIT_SCHEMA_REQUIRED: ERR_HDSTAMP_RECEIPT_MISSING,
    # final emit wrapper legacy family
    LEGACY_ERR_FINAL_EMIT_BODY_EMPTY: ERR_HDSTAMP_MISSING_OR_MALFORMED,
    LEGACY_ERR_FINAL_EMIT_COMPOSE_RUNTIME: ERR_HDSTAMP_RECEIPT_MISSING,
    LEGACY_ERR_FINAL_EMIT_COMPOSE_JSON_MISSING: ERR_HDSTAMP_RECEIPT_MISSING,
    LEGACY_ERR_FINAL_EMIT_CONTRACT_FAILED: ERR_HDSTAMP_RECEIPT_MISSING,
    LEGACY_ERR_FINAL_EMIT_REPLY_FILE_MISSING: ERR_HDSTAMP_RECEIPT_MISSING,
    LEGACY_ERR_FINAL_EMIT_CONTEXT_RESOLVE: ERR_HDSTAMP_ACTOR_LAYER_MISMATCH,
    LEGACY_ERR_FINAL_EMIT_IDENTITY_RESOLVE: ERR_HDSTAMP_ACTOR_LAYER_MISMATCH,
}


def canonicalize_headstamp_error_code(error_code: str) -> tuple[str, str]:
    token = str(error_code or "").strip()
    if not token:
        return "", ""
    if token in {
        ERR_HDSTAMP_MISSING_OR_MALFORMED,
        ERR_HDSTAMP_ACTOR_LAYER_MISMATCH,
        ERR_HDSTAMP_RECEIPT_MISSING,
        ERR_HDSTAMP_REPLY_EVIDENCE_MISSING,
    }:
        return token, ""
    mapped = LEGACY_HEADSTAMP_ERROR_MAP.get(token, "")
    if mapped:
        return mapped, token
    return token, ""


def inject_legacy_error_fields(
    payload: dict[str, Any],
    *,
    legacy_error_code: str = "",
    alias_mode: str = LEGACY_ERROR_ALIAS_MODE_ACTIVE_CANONICAL_ONLY,
) -> dict[str, Any]:
    """
    Standardize payload error fields:
    - payload.error_code always carries canonical family when mapping exists.
    - active/runtime/control-plane payloads stay canonical-only by default.
    - replay/migration callers must opt in explicitly before alias fields are re-projected.
    """
    out = dict(payload or {})
    raw_code = str(out.get("error_code", "")).strip()
    mapped_code, mapped_legacy = canonicalize_headstamp_error_code(raw_code)
    final_code = str(mapped_code or raw_code).strip()
    final_legacy = str(legacy_error_code or mapped_legacy).strip()
    mode = str(alias_mode or "").strip() or LEGACY_ERROR_ALIAS_MODE_ACTIVE_CANONICAL_ONLY
    if mode not in {
        LEGACY_ERROR_ALIAS_MODE_ACTIVE_CANONICAL_ONLY,
        LEGACY_ERROR_ALIAS_MODE_REPLAY_MIGRATION,
    }:
        mode = LEGACY_ERROR_ALIAS_MODE_ACTIVE_CANONICAL_ONLY
    out["error_code"] = final_code
    if mode == LEGACY_ERROR_ALIAS_MODE_REPLAY_MIGRATION and final_legacy and final_legacy != final_code:
        out["legacy_error_code"] = final_legacy
        out["compat_error_code"] = final_legacy
    else:
        out.pop("legacy_error_code", None)
        out.pop("compat_error_code", None)
    return out
