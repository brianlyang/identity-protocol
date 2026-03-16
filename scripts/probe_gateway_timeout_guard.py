#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

from gateway_wrapper_enforcement import run_gateway_wrapped_command
from protocol_infra_contract import (
    CTX_TOOL_TIMEOUT_ERROR_CODE,
    CTX_TOOL_TIMEOUT_MARKER,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
DEFAULT_TIMEOUT_SECONDS = 1
DEFAULT_SLEEP_SECONDS = 2
DEFAULT_TIMEOUT_ENV = "IDENTITY_PROTOCOL_GATEWAY_CMD_TIMEOUT_SECONDS"


def _parse_payload(blob: str) -> dict[str, Any]:
    text = str(blob or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue
        if isinstance(data, dict):
            return data
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe gateway wrapper subprocess timeout fail-close behavior.")
    ap.add_argument("--protocol-root", default="", help="Protocol repository root (defaults to script parent).")
    ap.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    ap.add_argument("--sleep-seconds", type=int, default=DEFAULT_SLEEP_SECONDS)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    protocol_root = (
        Path(args.protocol_root).expanduser().resolve()
        if str(args.protocol_root or "").strip()
        else script_dir.parent.resolve()
    )
    timeout_seconds = int(args.timeout_seconds) if int(args.timeout_seconds) > 0 else DEFAULT_TIMEOUT_SECONDS
    sleep_seconds = int(args.sleep_seconds) if int(args.sleep_seconds) > 0 else DEFAULT_SLEEP_SECONDS

    cmd = [
        sys.executable,
        "-c",
        f"import time; time.sleep({sleep_seconds}); print('late-timeout-probe')",
    ]
    child_env = dict(os.environ)
    child_env[DEFAULT_TIMEOUT_ENV] = str(timeout_seconds)

    wrapper_stdout_io = io.StringIO()
    with contextlib.redirect_stdout(wrapper_stdout_io):
        rc, out, err = run_gateway_wrapped_command(
            cmd=cmd,
            protocol_root=protocol_root,
            passthrough_cwd=protocol_root,
            passthrough_env=child_env,
        )
    wrapper_stdout = wrapper_stdout_io.getvalue()

    payload = _parse_payload(out)
    if not payload:
        payload = _parse_payload(wrapper_stdout)
    stale_reasons = [
        str(item).strip()
        for item in (payload.get("stale_reasons") or [])
        if str(item).strip()
    ]
    marker_present = bool(
        str(payload.get("context_timeout_marker", "")).strip() == CTX_TOOL_TIMEOUT_MARKER
        or CTX_TOOL_TIMEOUT_MARKER in "\n".join(stale_reasons)
        or CTX_TOOL_TIMEOUT_MARKER in str(wrapper_stdout)
        or CTX_TOOL_TIMEOUT_MARKER in str(err or "")
    )
    error_code = str(payload.get("error_code", "")).strip()
    status = (
        STATUS_PASS_REQUIRED
        if rc != 0 and marker_present and error_code == CTX_TOOL_TIMEOUT_ERROR_CODE
        else STATUS_FAIL_REQUIRED
    )
    out_payload = {
        "gateway_timeout_guard_probe_status": status,
        "gateway_timeout_guard_probe_expected_error_code": CTX_TOOL_TIMEOUT_ERROR_CODE,
        "gateway_timeout_guard_probe_observed_error_code": error_code,
        "gateway_timeout_guard_probe_marker_present": marker_present,
        "gateway_timeout_guard_probe_return_code": int(rc),
        "gateway_timeout_guard_probe_timeout_seconds": timeout_seconds,
        "gateway_timeout_guard_probe_stale_reasons": stale_reasons,
        "gateway_timeout_guard_probe_payload_status": str(payload.get("gateway_wrapper_status", "")).strip().upper(),
    }

    print(json.dumps(out_payload, ensure_ascii=False))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())

