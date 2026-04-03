#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from protocol_infra_contract import (
    HOST_TRANSPORT_REACHABILITY_ERROR_CODE,
    HOST_TRANSPORT_REACHABILITY_REASON_PREFIX,
    HOST_TRANSPORT_REACHABILITY_TIMEOUT_SECONDS,
    HOST_TRANSPORT_REACHABILITY_TIMEOUT_FIELD,
    HOST_TRANSPORT_REACHABILITY_URL_FIELD,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _reason(failure_class: str) -> str:
    token = str(failure_class or "").strip() or "unknown"
    return f"{HOST_TRANSPORT_REACHABILITY_REASON_PREFIX}:{token}"


def _safe_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except Exception:
        return int(default)
    if parsed <= 0:
        return int(default)
    return parsed


def _classify_exception(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, urllib.error.HTTPError):
        return "http_status_mismatch", f"http_status={int(exc.code)}"
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            return "connect_timeout", type(reason).__name__
        message = str(reason or "").strip().lower()
        if "connection refused" in message:
            return "connection_refused", message
        if "timed out" in message or "timeout" in message:
            return "connect_timeout", message
        if "network is unreachable" in message:
            return "network_unreachable", message
        if "name or service not known" in message or "nodename nor servname provided" in message:
            return "dns_resolution_failed", message
        if "socket" in message:
            return "localhost_socket_unreachable", message
        return "transport_unavailable", message or type(reason).__name__
    if isinstance(exc, TimeoutError):
        return "connect_timeout", type(exc).__name__
    return "transport_unavailable", type(exc).__name__


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate host transport reachability as a first-class protocol surface.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--transport-url", default="")
    ap.add_argument("--timeout-seconds", type=int, default=HOST_TRANSPORT_REACHABILITY_TIMEOUT_SECONDS)
    ap.add_argument("--expect-status", type=int, default=200)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    transport_url = str(args.transport_url or "").strip()
    timeout_seconds = _safe_positive_int(
        args.timeout_seconds,
        HOST_TRANSPORT_REACHABILITY_TIMEOUT_SECONDS,
    )
    expect_status = int(args.expect_status or 200)

    if not transport_url and str(args.catalog or "").strip() and str(args.identity_id or "").strip():
        catalog_path = Path(str(args.catalog).strip()).expanduser().resolve()
        try:
            _pack_path, task_path = resolve_pack_and_task(catalog_path, str(args.identity_id).strip())
            task = load_json(task_path)
            contract = task.get(HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY)
            if isinstance(contract, dict):
                transport_url = str(contract.get(HOST_TRANSPORT_REACHABILITY_URL_FIELD, "")).strip()
                timeout_seconds = _safe_positive_int(
                    contract.get(HOST_TRANSPORT_REACHABILITY_TIMEOUT_FIELD, timeout_seconds),
                    timeout_seconds,
                )
        except Exception:
            transport_url = transport_url

    payload: dict[str, Any] = {
        "host_transport_reachability_status": STATUS_FAIL_REQUIRED,
        "transport_reachability_status": STATUS_FAIL_REQUIRED,
        "transport_url": transport_url,
        "transport_timeout_seconds": timeout_seconds,
        "transport_expected_http_status": expect_status,
        "transport_http_status": 0,
        "transport_failure_class": "",
        "transport_failure_detail": "",
        "error_code": "",
        "stale_reasons": [],
    }

    if not transport_url:
        payload["transport_failure_class"] = "transport_url_missing"
        payload["transport_failure_detail"] = HOST_TRANSPORT_REACHABILITY_URL_FIELD
        payload["error_code"] = HOST_TRANSPORT_REACHABILITY_ERROR_CODE
        payload["stale_reasons"] = [_reason("transport_url_missing")]
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        with urllib.request.urlopen(transport_url, timeout=timeout_seconds) as response:
            http_status = int(getattr(response, "status", 0) or response.getcode() or 0)
            payload["transport_http_status"] = http_status
            if http_status != expect_status:
                payload["transport_failure_class"] = "http_status_mismatch"
                payload["transport_failure_detail"] = f"http_status={http_status}"
                payload["error_code"] = HOST_TRANSPORT_REACHABILITY_ERROR_CODE
                payload["stale_reasons"] = [_reason("http_status_mismatch")]
                _emit(payload, json_only=args.json_only)
                return 1
    except Exception as exc:
        failure_class, detail = _classify_exception(exc)
        payload["transport_failure_class"] = failure_class
        payload["transport_failure_detail"] = detail
        payload["error_code"] = HOST_TRANSPORT_REACHABILITY_ERROR_CODE
        payload["stale_reasons"] = [_reason(failure_class)]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["host_transport_reachability_status"] = STATUS_PASS_REQUIRED
    payload["transport_reachability_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
