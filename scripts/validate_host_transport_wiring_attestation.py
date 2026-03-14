#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
    HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS,
    HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS,
    HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
    HOST_VISIBLE_SURFACE_STATE_FILE,
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


def _parse_csv(value: str) -> list[str]:
    return [token for token in [str(item).strip() for item in str(value or "").split(",")] if token]


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


def _latest_receipt_by_channel(receipts: list[Path]) -> dict[str, Path]:
    by_channel: dict[str, Path] = {}
    for path in sorted(receipts, key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = _load_json(path)
        except Exception:
            continue
        channel = str(payload.get("emit_channel_id", "")).strip()
        if not channel or channel in by_channel:
            continue
        by_channel[channel] = path
    return by_channel


def _pick_host_gateway_contract(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in HOST_GATEWAY_CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node, str(key)
    return {}, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate host transport visible-surface wiring attestation contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--require-live-receipts", action="store_true")
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
        "host_transport_wiring_attestation_live_receipt_required": bool(args.require_live_receipts),
        "host_transport_wiring_attestation_allowed_live_receipt_sources": _parse_csv(
            args.allowed_live_receipt_sources
        ),
        "host_transport_wiring_attestation_live_coverage_status": STATUS_PASS_REQUIRED,
        "host_transport_wiring_attestation_live_covered_channels": [],
        "error_code": "",
        "stale_reasons": [],
    }

    issues: list[str] = []
    host_visible_contract = task.get(HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY)
    if not isinstance(host_visible_contract, dict):
        payload["host_transport_wiring_attestation_status"] = STATUS_FAIL_REQUIRED
        payload["host_transport_wiring_attestation_live_coverage_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MISSING
        payload["stale_reasons"] = ["host_visible_surface_contract_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

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
    payload["host_transport_wiring_attestation_state_file"] = state_file
    payload["host_transport_wiring_attestation_receipt_pattern"] = receipt_pattern

    required_attestation_fields = set(_as_list(host_visible_contract.get("required_attestation_fields")))
    required_pass_status_fields = set(_as_list(host_visible_contract.get("required_pass_status_fields")))
    if not set(HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS).issubset(required_attestation_fields):
        issues.append("host_visible_surface_required_attestation_fields_missing")
    if not set(HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS).issubset(required_pass_status_fields):
        issues.append("host_visible_surface_required_pass_status_fields_missing")

    dispatch_mode_required = str(host_visible_contract.get("host_dispatch_mode_required", "")).strip().lower()
    release_mode_required = str(host_visible_contract.get("host_release_mode_required", "")).strip().lower()
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
        except Exception:
            issues.append("host_visible_surface_live_state_file_invalid")

        receipt_glob_path = _resolve_pack_relative_path(
            pack_path,
            receipt_pattern,
            HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
        )
        if receipt_glob_path.is_file():
            receipt_files = [receipt_glob_path]
        else:
            receipt_files = sorted(pack_path.glob(receipt_pattern), key=lambda item: item.stat().st_mtime)
        if not receipt_files:
            issues.append("host_visible_surface_live_receipts_missing")
            payload["host_transport_wiring_attestation_live_coverage_status"] = STATUS_FAIL_REQUIRED
        else:
            latest_by_channel = _latest_receipt_by_channel(receipt_files)
            covered_channels = sorted(latest_by_channel.keys())
            payload["host_transport_wiring_attestation_live_covered_channels"] = covered_channels
            for channel in sorted(required_channels):
                receipt_path = latest_by_channel.get(channel)
                if receipt_path is None:
                    issues.append(f"host_visible_surface_live_channel_receipt_missing:{channel}")
                    continue
                try:
                    receipt_doc = _load_json(receipt_path)
                except Exception:
                    issues.append(f"host_visible_surface_live_channel_receipt_invalid:{channel}")
                    continue
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
        _emit(payload, json_only=args.json_only)
        return 1

    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
