#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from protocol_infra_contract import (
    HOST_GATEWAY_CONTRACT_KEYS,
    HOST_GATEWAY_REQUIRED_DISPATCH_MODE,
    HOST_GATEWAY_REQUIRED_RELEASE_MODE,
    HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE,
    HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID,
    HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE,
    HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR,
    HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED,
    HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS,
    HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS,
    HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS,
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
    HOST_VISIBLE_SURFACE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE,
    HOST_VISIBLE_SURFACE_POST_CHECK_SCHEMA_VERSION,
    PRIVILEGE_ESCALATION_ERROR_CODE,
    PRIVILEGE_ESCALATION_REASON_PREFIX,
    PRIVILEGE_ESCALATION_REMEDIATION_HINT,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MISSING = "IP-HDSTAMP-001"
ERR_INVALID = "IP-HDSTAMP-003"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _as_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    token = str(value or "").strip().lower()
    if token in {"1", "true", "yes", "on"}:
        return True
    if token in {"0", "false", "no", "off"}:
        return False
    return bool(default)


def _parse_csv(value: str) -> list[str]:
    return [token for token in [str(item).strip() for item in str(value or "").split(",")] if token]


def _is_privilege_escalation_error(exc: Exception) -> bool:
    if isinstance(exc, PermissionError):
        return True
    if isinstance(exc, OSError) and getattr(exc, "errno", None) in {
        errno.EACCES,
        errno.EPERM,
        errno.EROFS,
    }:
        return True
    return False


def _format_privilege_escalation_reason(*, path: Path, scope: str, exc: Exception) -> str:
    safe_scope = str(scope or "").strip() or "unknown_scope"
    safe_path = str(path.expanduser().resolve())
    safe_exc = type(exc).__name__
    return (
        f"{PRIVILEGE_ESCALATION_REASON_PREFIX}:{safe_scope}:path={safe_path}:error={safe_exc}:"
        f"hint={PRIVILEGE_ESCALATION_REMEDIATION_HINT}:error_code={PRIVILEGE_ESCALATION_ERROR_CODE}"
    )


def _resolve_pack_relative_path(pack_path: Path, raw_path: str, fallback_rel: str) -> Path:
    token = str(raw_path or "").strip()
    if not token:
        return (pack_path / fallback_rel).resolve()
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    if token.startswith("identity/runtime/"):
        return (pack_path / "runtime" / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (pack_path / token).resolve()
    return (pack_path / token).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("json_payload_not_object")
    return data


def _latest_receipt_by_channel(receipts: list[Path]) -> tuple[dict[str, Path], list[str]]:
    by_channel: dict[str, Path] = {}
    issues: list[str] = []
    def _safe_mtime(item: Path) -> float:
        try:
            return float(item.stat().st_mtime)
        except Exception as exc:
            if _is_privilege_escalation_error(exc):
                issues.append(
                    _format_privilege_escalation_reason(
                        path=item,
                        scope="host_visible_live_receipt_stat",
                        exc=exc,
                    )
                )
            else:
                issues.append(f"host_visible_surface_live_channel_receipt_stat_failed:{item.name}")
            return -1.0

    for path in sorted(receipts, key=_safe_mtime, reverse=True):
        try:
            payload = _load_json(path)
        except Exception as exc:
            if _is_privilege_escalation_error(exc):
                issues.append(
                    _format_privilege_escalation_reason(
                        path=path,
                        scope="host_visible_live_receipt_read",
                        exc=exc,
                    )
                )
            else:
                issues.append(
                    f"host_visible_surface_live_channel_receipt_invalid:{path.name}:{type(exc).__name__}"
                )
            continue
        channel = str(payload.get("emit_channel_id", "")).strip()
        if not channel or channel in by_channel:
            continue
        by_channel[channel] = path
    return by_channel, issues


def _pick_host_gateway_contract(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in HOST_GATEWAY_CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node, str(key)
    return {}, ""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_post_check_closure_state(
    *,
    pack_path: Path,
    closure_state_file: str,
    closure_state_doc: dict[str, Any],
) -> tuple[bool, str, str]:
    state_path = _resolve_pack_relative_path(
        pack_path,
        closure_state_file,
        HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    )
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            return False, str(state_path), _format_privilege_escalation_reason(
                path=state_path.parent,
                scope="host_transport_post_check_state_dir_write",
                exc=exc,
            )
        return False, str(state_path), f"host_transport_post_check_state_dir_write_failed:{type(exc).__name__}"

    try:
        state_path.write_text(json.dumps(closure_state_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            return False, str(state_path), _format_privilege_escalation_reason(
                path=state_path,
                scope="host_transport_post_check_state_write",
                exc=exc,
            )
        return False, str(state_path), f"host_transport_post_check_state_write_failed:{type(exc).__name__}"
    return True, str(state_path), ""


def _finalize_with_post_check_state(
    *,
    payload: dict[str, Any],
    pack_path: Path,
    args: argparse.Namespace,
    closure_state_file: str,
    post_check_block_on_active: bool,
) -> int:
    checked_at_utc = _utc_now_iso()
    attestation_status = str(payload.get("host_transport_wiring_attestation_status", "")).strip().upper()
    if attestation_status not in {STATUS_PASS_REQUIRED, STATUS_FAIL_REQUIRED}:
        attestation_status = STATUS_FAIL_REQUIRED
        payload["host_transport_wiring_attestation_status"] = STATUS_FAIL_REQUIRED
    stale_reasons = _as_list(payload.get("stale_reasons"))
    if attestation_status != STATUS_PASS_REQUIRED and not str(payload.get("error_code", "")).strip():
        payload["error_code"] = ERR_INVALID
    blocker_active = bool(post_check_block_on_active) and attestation_status != STATUS_PASS_REQUIRED
    closure_state_doc: dict[str, Any] = {
        "schema_version": HOST_VISIBLE_SURFACE_POST_CHECK_SCHEMA_VERSION,
        "identity_id": str(payload.get("identity_id", "")).strip(),
        "catalog_path": str(payload.get("catalog_path", "")).strip(),
        "pack_path": str(payload.get("pack_path", "")).strip(),
        "task_path": str(payload.get("task_path", "")).strip(),
        "validator": HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR,
        "closure_status": attestation_status,
        "block_on_active": bool(post_check_block_on_active),
        "blocker_active": bool(blocker_active),
        "error_code": str(payload.get("error_code", "")).strip(),
        "stale_reasons": stale_reasons,
        "live_receipt_required": bool(args.require_live_receipts),
        "required_actor_id": str(args.require_actor_id or "").strip(),
        "required_session_id": str(args.require_session_id or "").strip(),
        "required_run_id": str(args.require_run_id or "").strip(),
        "checked_at_utc": checked_at_utc,
    }
    ok, resolved_state_path, write_reason = _write_post_check_closure_state(
        pack_path=pack_path,
        closure_state_file=closure_state_file,
        closure_state_doc=closure_state_doc,
    )

    payload["host_transport_post_check_closure_state_file"] = str(closure_state_file).strip() or HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE
    payload["host_transport_post_check_closure_state_path"] = resolved_state_path
    payload["host_transport_post_check_block_on_active"] = bool(post_check_block_on_active)
    payload["host_transport_post_check_blocker_active"] = bool(blocker_active)
    payload["host_transport_post_check_closure_status"] = attestation_status
    payload["host_transport_post_check_checked_at_utc"] = checked_at_utc
    payload["host_transport_post_check_state_write_status"] = STATUS_PASS_REQUIRED if ok else STATUS_FAIL_REQUIRED

    if not ok:
        if write_reason and write_reason not in stale_reasons:
            stale_reasons.append(write_reason)
        payload["stale_reasons"] = stale_reasons
        payload["host_transport_wiring_attestation_status"] = STATUS_FAIL_REQUIRED
        payload["host_transport_wiring_attestation_live_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["host_transport_post_check_blocker_active"] = True
        payload["host_transport_post_check_closure_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = PRIVILEGE_ESCALATION_ERROR_CODE
        _emit(payload, json_only=args.json_only)
        return 1

    _emit(payload, json_only=args.json_only)
    return 0 if attestation_status == STATUS_PASS_REQUIRED else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate host transport visible-surface wiring attestation contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--require-live-receipts", action="store_true")
    ap.add_argument("--require-actor-id", default="", help="optional expected actor_id for live receipt binding")
    ap.add_argument("--require-session-id", default="", help="optional expected session_id for live receipt binding")
    ap.add_argument("--require-run-id", default="", help="optional expected run_id for live receipt binding")
    ap.add_argument(
        "--allowed-live-receipt-sources",
        default=HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
        help=(
            "comma-separated receipt sources accepted for live coverage "
            f"(default: {HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE}; "
            f"CI may extend with {HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE})"
        ),
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 2

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_path),
        "task_path": str(task_path),
        "host_transport_wiring_attestation_status": STATUS_PASS_REQUIRED,
        "host_transport_wiring_attestation_contract_key": HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
        "host_transport_wiring_attestation_required_channels": [],
        "host_transport_wiring_attestation_state_file": "",
        "host_transport_wiring_attestation_receipt_pattern": "",
        "host_transport_wiring_attestation_runtime_receipt_max_age_seconds": 0,
        "host_transport_wiring_attestation_live_receipt_required": bool(args.require_live_receipts),
        "host_transport_wiring_attestation_allowed_live_receipt_sources": _parse_csv(
            args.allowed_live_receipt_sources
        ),
        "host_transport_wiring_attestation_live_coverage_status": STATUS_PASS_REQUIRED,
        "host_transport_wiring_attestation_live_covered_channels": [],
        "host_transport_wiring_attestation_live_binding_required": False,
        "host_transport_wiring_attestation_required_actor_id": str(args.require_actor_id or "").strip(),
        "host_transport_wiring_attestation_required_session_id": str(args.require_session_id or "").strip(),
        "host_transport_wiring_attestation_required_run_id": str(args.require_run_id or "").strip(),
        "host_transport_wiring_attestation_strict_live_run_binding_required": bool(
            HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED
        ),
        "host_transport_post_check_closure_state_file": HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
        "host_transport_post_check_closure_state_path": "",
        "host_transport_post_check_block_on_active": bool(HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
        "host_transport_post_check_blocker_active": False,
        "host_transport_post_check_closure_status": STATUS_PASS_REQUIRED,
        "host_transport_post_check_checked_at_utc": "",
        "host_transport_post_check_state_write_status": "",
        "error_code": "",
        "stale_reasons": [],
    }

    issues: list[str] = []
    post_check_closure_state_file = HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE
    post_check_block_on_active = bool(HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE)
    host_visible_contract = task.get(HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY)
    if not isinstance(host_visible_contract, dict):
        payload["host_transport_wiring_attestation_status"] = STATUS_FAIL_REQUIRED
        payload["host_transport_wiring_attestation_live_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MISSING
        payload["stale_reasons"] = ["host_visible_surface_contract_missing"]
        return _finalize_with_post_check_state(
            payload=payload,
            pack_path=pack_path,
            args=args,
            closure_state_file=post_check_closure_state_file,
            post_check_block_on_active=post_check_block_on_active,
        )

    if host_visible_contract.get("required") is not True:
        issues.append("host_visible_surface_required_flag_not_true")
    if str(host_visible_contract.get("contract_id", "")).strip() != HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID:
        issues.append("host_visible_surface_contract_id_mismatch")
    if str(host_visible_contract.get("validator", "")).strip() != HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR:
        issues.append("host_visible_surface_validator_mismatch")
    if str(host_visible_contract.get("required_live_probe_delegate", "")).strip() != HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE:
        issues.append("host_visible_surface_live_probe_delegate_mismatch")

    required_channels = set(_as_list(host_visible_contract.get("required_channels")))
    payload["host_transport_wiring_attestation_required_channels"] = sorted(required_channels)
    if not set(HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS).issubset(required_channels):
        issues.append("host_visible_surface_required_channels_missing")

    state_file = str(host_visible_contract.get("runtime_state_file", "")).strip() or HOST_VISIBLE_SURFACE_STATE_FILE
    receipt_pattern = str(host_visible_contract.get("runtime_receipt_pattern", "")).strip() or HOST_VISIBLE_SURFACE_RECEIPT_PATTERN
    post_check_closure_state_file = (
        str(host_visible_contract.get("post_check_closure_state_file", "")).strip()
        or HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE
    )
    post_check_block_on_active = _as_bool(
        host_visible_contract.get("post_check_block_on_active", HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
        default=bool(HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
    )
    payload["host_transport_post_check_closure_state_file"] = post_check_closure_state_file
    payload["host_transport_post_check_block_on_active"] = bool(post_check_block_on_active)
    if not str(host_visible_contract.get("post_check_closure_state_file", "")).strip():
        issues.append("host_visible_surface_post_check_closure_state_file_missing")
    if post_check_block_on_active is not True:
        issues.append("host_visible_surface_post_check_block_on_active_not_true")
    max_age_raw = host_visible_contract.get(
        "runtime_receipt_max_age_seconds",
        HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS,
    )
    try:
        runtime_receipt_max_age_seconds = int(max_age_raw)
    except Exception:
        runtime_receipt_max_age_seconds = 0
    payload["host_transport_wiring_attestation_state_file"] = state_file
    payload["host_transport_wiring_attestation_receipt_pattern"] = receipt_pattern
    payload["host_transport_wiring_attestation_runtime_receipt_max_age_seconds"] = runtime_receipt_max_age_seconds

    required_attestation_fields = set(_as_list(host_visible_contract.get("required_attestation_fields")))
    required_pass_status_fields = set(_as_list(host_visible_contract.get("required_pass_status_fields")))
    if not set(HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS).issubset(required_attestation_fields):
        issues.append("host_visible_surface_required_attestation_fields_missing")
    if not set(HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS).issubset(required_pass_status_fields):
        issues.append("host_visible_surface_required_pass_status_fields_missing")
    if runtime_receipt_max_age_seconds <= 0:
        issues.append("host_visible_surface_runtime_receipt_max_age_seconds_invalid")

    dispatch_mode_required = str(host_visible_contract.get("host_dispatch_mode_required", "")).strip().lower()
    release_mode_required = str(host_visible_contract.get("host_release_mode_required", "")).strip().lower()
    strict_live_run_binding_required = _as_bool(
        host_visible_contract.get(
            "strict_live_run_binding_required",
            HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED,
        ),
        default=bool(HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED),
    )
    payload["host_transport_wiring_attestation_strict_live_run_binding_required"] = bool(
        strict_live_run_binding_required
    )
    if strict_live_run_binding_required is not True:
        issues.append("host_visible_surface_strict_live_run_binding_required_not_true")
    if dispatch_mode_required != HOST_GATEWAY_REQUIRED_DISPATCH_MODE:
        issues.append("host_visible_surface_dispatch_mode_required_mismatch")
    if release_mode_required != HOST_GATEWAY_REQUIRED_RELEASE_MODE:
        issues.append("host_visible_surface_release_mode_required_mismatch")

    state_path = _resolve_pack_relative_path(pack_path, state_file, HOST_VISIBLE_SURFACE_STATE_FILE)
    if not state_path.exists() or not state_path.is_file():
        issues.append("host_visible_surface_state_file_missing")

    host_gateway_contract, host_gateway_key = _pick_host_gateway_contract(task if isinstance(task, dict) else {})
    payload["host_transport_wiring_attestation_host_gateway_contract_key"] = host_gateway_key
    if not isinstance(host_gateway_contract, dict):
        issues.append("host_gateway_contract_missing")
    else:
        if str(host_gateway_contract.get("host_visible_surface_registry_contract_ref", "")).strip() != HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY:
            issues.append("host_gateway_visible_surface_contract_ref_mismatch")
        if str(host_gateway_contract.get("host_dispatch_mode", "")).strip().lower() != HOST_GATEWAY_REQUIRED_DISPATCH_MODE:
            issues.append("host_gateway_dispatch_mode_not_wrapper_only")
        if str(host_gateway_contract.get("host_release_mode", "")).strip().lower() != HOST_GATEWAY_REQUIRED_RELEASE_MODE:
            issues.append("host_gateway_release_mode_not_wrapper_only")

    if args.require_live_receipts:
        required_actor_id = str(args.require_actor_id or "").strip()
        required_session_id = str(args.require_session_id or "").strip()
        required_run_id = str(args.require_run_id or "").strip()
        payload["host_transport_wiring_attestation_live_binding_required"] = bool(
            required_actor_id
            or required_session_id
            or required_run_id
            or strict_live_run_binding_required
        )
        if strict_live_run_binding_required and not required_run_id:
            issues.append("host_visible_surface_live_run_id_required_missing")
        allowed_sources = set(_parse_csv(args.allowed_live_receipt_sources))
        if not allowed_sources:
            allowed_sources = {HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE}
        payload["host_transport_wiring_attestation_allowed_live_receipt_sources"] = sorted(allowed_sources)

        state_doc: dict[str, Any] = {}
        state_channels: dict[str, Any] = {}
        try:
            if state_path.exists() and state_path.is_file():
                state_doc = _load_json(state_path)
                channels_node = state_doc.get("channels")
                state_channels = channels_node if isinstance(channels_node, dict) else {}
            else:
                issues.append("host_visible_surface_live_state_file_missing")
        except Exception as exc:
            if _is_privilege_escalation_error(exc):
                issues.append(
                    _format_privilege_escalation_reason(
                        path=state_path,
                        scope="host_visible_live_state_read",
                        exc=exc,
                    )
                )
            else:
                issues.append("host_visible_surface_live_state_file_invalid")

        receipt_glob_path = _resolve_pack_relative_path(
            pack_path,
            receipt_pattern,
            HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
        )
        if receipt_glob_path.is_file():
            receipt_files = [receipt_glob_path]
        else:
            try:
                receipt_files = sorted(pack_path.glob(receipt_pattern), key=lambda item: item.stat().st_mtime)
            except Exception as exc:
                if _is_privilege_escalation_error(exc):
                    issues.append(
                        _format_privilege_escalation_reason(
                            path=receipt_glob_path.parent,
                            scope="host_visible_live_receipt_glob",
                            exc=exc,
                        )
                    )
                else:
                    issues.append("host_visible_surface_live_receipt_glob_failed")
                receipt_files = []
        if not receipt_files:
            issues.append("host_visible_surface_live_receipts_missing")
            payload["host_transport_wiring_attestation_live_coverage_status"] = STATUS_FAIL_REQUIRED
        else:
            latest_by_channel, latest_scan_issues = _latest_receipt_by_channel(receipt_files)
            issues.extend(latest_scan_issues)
            covered_channels = sorted(latest_by_channel.keys())
            payload["host_transport_wiring_attestation_live_covered_channels"] = covered_channels
            for channel in sorted(required_channels):
                receipt_path = latest_by_channel.get(channel)
                if receipt_path is None:
                    issues.append(f"host_visible_surface_live_channel_receipt_missing:{channel}")
                    continue
                try:
                    receipt_doc = _load_json(receipt_path)
                except Exception as exc:
                    if _is_privilege_escalation_error(exc):
                        issues.append(
                            _format_privilege_escalation_reason(
                                path=receipt_path,
                                scope=f"host_visible_live_channel_receipt_read:{channel}",
                                exc=exc,
                            )
                        )
                    else:
                        issues.append(f"host_visible_surface_live_channel_receipt_invalid:{channel}")
                    continue
                receipt_age_seconds = max(0, int(time.time() - receipt_path.stat().st_mtime))
                if receipt_age_seconds > runtime_receipt_max_age_seconds:
                    issues.append(
                        "host_visible_surface_live_channel_receipt_stale:"
                        f"{channel}:age_seconds={receipt_age_seconds}:max_age_seconds={runtime_receipt_max_age_seconds}"
                    )
                source_value = str(receipt_doc.get(HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD, "")).strip()
                if source_value not in allowed_sources:
                    issues.append(
                        f"host_visible_surface_live_channel_receipt_source_invalid:{channel}:{source_value or 'missing'}"
                    )
                for field in sorted(required_attestation_fields):
                    if field not in receipt_doc:
                        issues.append(f"host_visible_surface_live_channel_attestation_field_missing:{channel}:{field}")
                for field in sorted(required_pass_status_fields):
                    status_value = str(receipt_doc.get(field, "")).strip().upper()
                    if status_value != STATUS_PASS_REQUIRED:
                        issues.append(f"host_visible_surface_live_channel_status_not_pass:{channel}:{field}")
                receipt_actor_id = str(receipt_doc.get("actor_id", "")).strip()
                receipt_session_id = str(receipt_doc.get("session_id", "")).strip()
                receipt_run_id = str(receipt_doc.get("run_id", "")).strip()
                if required_actor_id and receipt_actor_id != required_actor_id:
                    issues.append(
                        "host_visible_surface_live_channel_actor_id_mismatch:"
                        f"{channel}:expected={required_actor_id}:observed={receipt_actor_id or 'missing'}"
                    )
                if required_session_id and receipt_session_id != required_session_id:
                    issues.append(
                        "host_visible_surface_live_channel_session_id_mismatch:"
                        f"{channel}:expected={required_session_id}:observed={receipt_session_id or 'missing'}"
                    )
                if required_run_id and receipt_run_id != required_run_id:
                    issues.append(
                        "host_visible_surface_live_channel_run_id_mismatch:"
                        f"{channel}:expected={required_run_id}:observed={receipt_run_id or 'missing'}"
                    )
                channel_state = state_channels.get(channel)
                if not isinstance(channel_state, dict):
                    issues.append(f"host_visible_surface_live_state_channel_missing:{channel}")
                    continue
                state_last_receipt = str(channel_state.get("last_receipt_path", "")).strip()
                if not state_last_receipt:
                    issues.append(f"host_visible_surface_live_state_channel_receipt_missing:{channel}")
                elif Path(state_last_receipt).resolve() != receipt_path.resolve():
                    issues.append(f"host_visible_surface_live_state_channel_receipt_mismatch:{channel}")
                state_last_status = str(channel_state.get("last_status", "")).strip().upper()
                if state_last_status != STATUS_PASS_REQUIRED:
                    issues.append(f"host_visible_surface_live_state_channel_status_not_pass:{channel}")
                state_last_run_id = str(channel_state.get("last_run_id", "")).strip()
                if state_last_run_id and receipt_run_id and state_last_run_id != receipt_run_id:
                    issues.append(
                        "host_visible_surface_live_state_channel_run_id_receipt_mismatch:"
                        f"{channel}:state={state_last_run_id}:receipt={receipt_run_id}"
                    )
                if required_run_id and state_last_run_id != required_run_id:
                    issues.append(
                        "host_visible_surface_live_state_channel_run_id_mismatch:"
                        f"{channel}:expected={required_run_id}:observed={state_last_run_id or 'missing'}"
                    )
                state_source = str(channel_state.get(HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD, "")).strip()
                if state_source not in allowed_sources:
                    issues.append(
                        f"host_visible_surface_live_state_channel_source_invalid:{channel}:{state_source or 'missing'}"
                    )
            if any(issue.startswith("host_visible_surface_live_") for issue in issues):
                payload["host_transport_wiring_attestation_live_coverage_status"] = STATUS_FAIL_REQUIRED

    if issues:
        payload["host_transport_wiring_attestation_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_INVALID
        payload["stale_reasons"] = issues
    return _finalize_with_post_check_state(
        payload=payload,
        pack_path=pack_path,
        args=args,
        closure_state_file=post_check_closure_state_file,
        post_check_block_on_active=post_check_block_on_active,
    )


if __name__ == "__main__":
    raise SystemExit(main())
