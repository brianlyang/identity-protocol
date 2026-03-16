#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from protocol_infra_contract import (
    HOST_VISIBLE_NEXT_HOP_BLOCK_REQUIRED_RATE,
    HOST_VISIBLE_POST_CHECK_DETECTABILITY_REQUIRED_RATE,
    HOST_VISIBLE_PRE_SEND_GATE_MIN_PASS_RATE,
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
ERR_CLOSURE_STEP_FAILED = "IP-HDSTAMP-CLSR-001"
ERR_SEND_TIME_REPLY_REQUIRED = "IP-HDSTAMP-CLSR-002"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def _parse_payload(raw_stdout: str) -> dict[str, Any]:
    text = str(raw_stdout or "").strip()
    if not text:
        return {}
    for line in reversed(text.splitlines()):
        row = line.strip()
        if not row:
            continue
        try:
            payload = json.loads(row)
        except Exception:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _run_json(cmd: list[str]) -> tuple[int, dict[str, Any], str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    payload = _parse_payload(proc.stdout)
    tail = "\n".join(str(proc.stderr or "").splitlines()[-5:]).strip()
    return proc.returncode, payload, tail


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Official host-visible live closure command: "
            "recover post-check state -> live attestation -> send-time gate verification."
        )
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--actor-id", required=True)
    ap.add_argument("--session-id", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument(
        "--operation",
        choices=[
            "activate",
            "update",
            "mutation",
            "readiness",
            "e2e",
            "ci",
            "validate",
            "scan",
            "three-plane",
            "inspection",
            "send-time",
        ],
        default="validate",
    )
    ap.add_argument(
        "--outlet-channel-id",
        default="commentary",
        help="host-visible governed channel to verify at send-time stage",
    )
    ap.add_argument("--reply-file", default="")
    ap.add_argument("--transport-url", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = str(Path(args.catalog).expanduser().resolve())
    repo_catalog_path = str(Path(args.repo_catalog).expanduser().resolve())
    reply_file = str(args.reply_file or "").strip()
    if not reply_file:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": catalog_path,
            "operation": args.operation,
            "host_visible_live_closure_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_SEND_TIME_REPLY_REQUIRED,
            "stale_reasons": ["send_time_reply_file_missing"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    reply_file_path = Path(reply_file).expanduser().resolve()
    if not reply_file_path.exists():
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": catalog_path,
            "operation": args.operation,
            "host_visible_live_closure_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_SEND_TIME_REPLY_REQUIRED,
            "stale_reasons": ["send_time_reply_file_not_found"],
            "reply_file": str(reply_file_path),
        }
        _emit(payload, json_only=args.json_only)
        return 1

    reachability_cmd = [
        sys.executable,
        str((SCRIPT_DIR / "validate_host_transport_reachability.py").resolve()),
        "--catalog",
        catalog_path,
        "--identity-id",
        str(args.identity_id).strip(),
        "--json-only",
    ]
    if str(args.transport_url).strip():
        reachability_cmd.extend(["--transport-url", str(args.transport_url).strip()])
    reachability_rc, reachability_payload, reachability_stderr_tail = _run_json(reachability_cmd)
    reachability_status = str(
        reachability_payload.get("host_transport_reachability_status", "")
    ).strip().upper()
    if reachability_rc != 0 or reachability_status != STATUS_PASS_REQUIRED:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": catalog_path,
            "repo_catalog_path": repo_catalog_path,
            "operation": args.operation,
            "actor_id": args.actor_id,
            "session_id": args.session_id,
            "run_id": args.run_id,
            "reply_file": str(reply_file_path),
            "outlet_channel_id": str(args.outlet_channel_id).strip(),
            "host_visible_live_closure_status": STATUS_FAIL_REQUIRED,
            "error_code": str(reachability_payload.get("error_code", "")).strip() or ERR_CLOSURE_STEP_FAILED,
            "host_visible_metrics": {
                "pre_send_gate_min_pass_rate": float(HOST_VISIBLE_PRE_SEND_GATE_MIN_PASS_RATE),
                "post_check_detectability_required_rate": float(
                    HOST_VISIBLE_POST_CHECK_DETECTABILITY_REQUIRED_RATE
                ),
                "next_hop_block_required_rate": float(HOST_VISIBLE_NEXT_HOP_BLOCK_REQUIRED_RATE),
                "transport_reachability_status": reachability_status or STATUS_FAIL_REQUIRED,
                "pre_send_gate_status": STATUS_SKIPPED_NOT_REQUIRED,
                "post_check_detectability_status": STATUS_SKIPPED_NOT_REQUIRED,
                "next_hop_ready_status": STATUS_FAIL_REQUIRED,
            },
            "steps": {
                "reachability": {
                    "rc": reachability_rc,
                    "status": reachability_status or STATUS_FAIL_REQUIRED,
                    "error_code": str(reachability_payload.get("error_code", "")).strip(),
                    "transport_failure_class": str(
                        reachability_payload.get("transport_failure_class", "")
                    ).strip(),
                    "stderr_tail": reachability_stderr_tail,
                },
                "recovery": {
                    "rc": -1,
                    "status": STATUS_SKIPPED_NOT_REQUIRED,
                    "error_code": "",
                    "stderr_tail": "",
                },
                "attestation": {
                    "rc": -1,
                    "status": STATUS_SKIPPED_NOT_REQUIRED,
                    "error_code": "",
                    "stderr_tail": "",
                },
                "send_time": {
                    "rc": -1,
                    "status": STATUS_SKIPPED_NOT_REQUIRED,
                    "error_code": "",
                    "post_check_blocker_active": False,
                    "stderr_tail": "",
                },
            },
            "stale_reasons": [
                "host_transport_reachability_not_pass",
                *[
                    str(item).strip()
                    for item in (reachability_payload.get("stale_reasons") or [])
                    if str(item).strip()
                ],
            ],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    recovery_cmd = [
        sys.executable,
        str((SCRIPT_DIR / "recover_host_visible_post_check_state.py").resolve()),
        "--catalog",
        catalog_path,
        "--repo-catalog",
        repo_catalog_path,
        "--identity-id",
        str(args.identity_id).strip(),
        "--operation",
        str(args.operation).strip(),
        "--actor-id",
        str(args.actor_id).strip(),
        "--session-id",
        str(args.session_id).strip(),
        "--run-id",
        str(args.run_id).strip(),
        "--receipt-source",
        HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
        "--allowed-live-receipt-sources",
        HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
        "--json-only",
    ]
    recovery_rc, recovery_payload, recovery_stderr_tail = _run_json(recovery_cmd)

    attestation_cmd = [
        sys.executable,
        str((SCRIPT_DIR / "validate_host_transport_wiring_attestation.py").resolve()),
        "--catalog",
        catalog_path,
        "--identity-id",
        str(args.identity_id).strip(),
        "--operation",
        str(args.operation).strip(),
        "--require-live-receipts",
        "--require-actor-id",
        str(args.actor_id).strip(),
        "--require-session-id",
        str(args.session_id).strip(),
        "--require-run-id",
        str(args.run_id).strip(),
        "--allowed-live-receipt-sources",
        HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
        "--json-only",
    ]
    attestation_rc, attestation_payload, attestation_stderr_tail = _run_json(attestation_cmd)

    send_time_cmd = [
        sys.executable,
        str((SCRIPT_DIR / "validate_send_time_reply_gate.py").resolve()),
        "--identity-id",
        str(args.identity_id).strip(),
        "--catalog",
        catalog_path,
        "--repo-catalog",
        repo_catalog_path,
        "--operation",
        "send-time",
        "--actor-id",
        str(args.actor_id).strip(),
        "--session-id",
        str(args.session_id).strip(),
        "--reply-file",
        str(reply_file_path),
        "--force-check",
        "--enforce-send-time-gate",
        "--reply-outlet-guard-applied",
        "--outlet-channel-id",
        str(args.outlet_channel_id).strip(),
        "--json-only",
    ]
    send_time_rc, send_time_payload, send_time_stderr_tail = _run_json(send_time_cmd)

    recovery_status = str(recovery_payload.get("recovery_status", "")).strip().upper()
    attestation_status = str(attestation_payload.get("host_transport_wiring_attestation_status", "")).strip().upper()
    send_time_status = str(send_time_payload.get("send_time_gate_status", "")).strip().upper()
    send_time_post_check_blocker = bool(send_time_payload.get("host_transport_post_check_blocker_active", False))

    stale_reasons: list[str] = []
    if reachability_rc != 0 or reachability_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("host_transport_reachability_not_pass")
    if recovery_rc != 0 or recovery_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("host_visible_recovery_not_pass")
    if attestation_rc != 0 or attestation_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("host_visible_live_attestation_not_pass")
    if send_time_rc != 0 or send_time_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("send_time_gate_not_pass")
    if send_time_post_check_blocker:
        stale_reasons.append("send_time_post_check_blocker_active")

    closure_ok = len(stale_reasons) == 0
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": catalog_path,
        "repo_catalog_path": repo_catalog_path,
        "operation": args.operation,
        "actor_id": args.actor_id,
        "session_id": args.session_id,
        "run_id": args.run_id,
        "reply_file": str(reply_file_path),
        "outlet_channel_id": str(args.outlet_channel_id).strip(),
        "host_visible_live_closure_status": STATUS_PASS_REQUIRED if closure_ok else STATUS_FAIL_REQUIRED,
        "error_code": "" if closure_ok else ERR_CLOSURE_STEP_FAILED,
        "host_visible_metrics": {
            "pre_send_gate_min_pass_rate": float(HOST_VISIBLE_PRE_SEND_GATE_MIN_PASS_RATE),
            "post_check_detectability_required_rate": float(HOST_VISIBLE_POST_CHECK_DETECTABILITY_REQUIRED_RATE),
            "next_hop_block_required_rate": float(HOST_VISIBLE_NEXT_HOP_BLOCK_REQUIRED_RATE),
            "transport_reachability_status": reachability_status,
            "pre_send_gate_status": send_time_status,
            "post_check_detectability_status": attestation_status,
            "next_hop_ready_status": STATUS_PASS_REQUIRED if not send_time_post_check_blocker else STATUS_FAIL_REQUIRED,
        },
        "steps": {
            "reachability": {
                "rc": reachability_rc,
                "status": reachability_status,
                "error_code": str(reachability_payload.get("error_code", "")).strip(),
                "transport_failure_class": str(
                    reachability_payload.get("transport_failure_class", "")
                ).strip(),
                "stderr_tail": reachability_stderr_tail,
            },
            "recovery": {
                "rc": recovery_rc,
                "status": recovery_status,
                "error_code": str(recovery_payload.get("error_code", "")).strip(),
                "stderr_tail": recovery_stderr_tail,
            },
            "attestation": {
                "rc": attestation_rc,
                "status": attestation_status,
                "error_code": str(attestation_payload.get("error_code", "")).strip(),
                "stderr_tail": attestation_stderr_tail,
            },
            "send_time": {
                "rc": send_time_rc,
                "status": send_time_status,
                "error_code": str(send_time_payload.get("error_code", "")).strip(),
                "post_check_blocker_active": send_time_post_check_blocker,
                "stderr_tail": send_time_stderr_tail,
            },
        },
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if closure_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
