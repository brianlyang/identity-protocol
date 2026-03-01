#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ERR_SEND_TIME_GATE = "IP-ASB-STAMP-SESSION-001"
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"


def _parse_json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        doc = json.loads(text)
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def _read_stamp_line(stamp_json_path: Path) -> str:
    doc = _parse_json_payload(stamp_json_path.read_text(encoding="utf-8"))
    return str(doc.get("external_stamp", "")).strip()


def _reply_text_from_args(args: argparse.Namespace) -> tuple[str, str]:
    """
    Returns (reply_text, evidence_mode).
    """
    if str(args.reply_text or "").strip():
        return str(args.reply_text).strip(), "reply_text"

    if str(args.reply_file or "").strip():
        p = Path(str(args.reply_file)).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"reply file not found: {p}")
        return p.read_text(encoding="utf-8", errors="ignore"), "reply_file"

    if str(args.reply_log or "").strip():
        p = Path(str(args.reply_log)).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"reply log not found: {p}")
        # pass-through mode; validator will parse the log directly.
        return "", "reply_log"

    if str(args.stamp_json or "").strip():
        p = Path(str(args.stamp_json)).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"stamp json not found: {p}")
        stamp_line = _read_stamp_line(p)
        if not stamp_line:
            return "", "stamp_json"
        business_line = str(args.business_line or "").strip() or "SEND_TIME_GATE_PROBE_BODY"
        return f"{stamp_line}\n{business_line}\n", "stamp_json_composed_reply"

    return "", "missing"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Unified send-time gate for governed user-visible reply channel. "
            "Fails closed on missing first-line Identity-Context and emits blocker receipt."
        )
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--reply-text", default="")
    ap.add_argument("--reply-file", default="")
    ap.add_argument("--reply-log", default="")
    ap.add_argument("--stamp-json", default="", help="optional fallback to compose send-time reply from external_stamp")
    ap.add_argument("--business-line", default="SEND_TIME_GATE_PROBE_BODY")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--enforce-send-time-gate", action="store_true")
    ap.add_argument("--blocker-receipt-out", default="")
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
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        reply_text, evidence_mode = _reply_text_from_args(args)
    except Exception as exc:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
            "operation": args.operation,
            "send_time_gate_status": STATUS_FAIL_REQUIRED if args.enforce_send_time_gate else STATUS_WARN_NON_BLOCKING,
            "error_code": ERR_SEND_TIME_GATE,
            "reply_evidence_mode": "invalid_input",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["input:missing_or_invalid"],
            "blocker_receipt_path": "",
            "stale_reasons": [f"send_time_input_invalid:{exc}"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    op_for_validator = "validate" if args.operation == "send-time" else args.operation
    cmd = [
        sys.executable,
        "scripts/validate_reply_identity_context_first_line.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        op_for_validator,
        "--json-only",
    ]
    if str(args.actor_id or "").strip():
        cmd.extend(["--actor-id", str(args.actor_id).strip()])
    if args.force_check:
        cmd.append("--force-check")
    if args.enforce_send_time_gate:
        cmd.append("--enforce-first-line-gate")
    if str(args.blocker_receipt_out or "").strip():
        cmd.extend(["--blocker-receipt-out", str(args.blocker_receipt_out).strip()])
    if evidence_mode == "reply_log":
        cmd.extend(["--reply-log", str(args.reply_log).strip()])
    elif reply_text:
        cmd.extend(["--reply-text", reply_text])

    p = subprocess.run(cmd, capture_output=True, text=True)
    validator_payload = _parse_json_payload(p.stdout)

    first_line_status = str(validator_payload.get("reply_first_line_status", "")).strip() or (
        STATUS_PASS_REQUIRED if p.returncode == 0 else STATUS_FAIL_REQUIRED
    )
    error_code = str(validator_payload.get("error_code", "")).strip()
    if p.returncode != 0 and not error_code:
        error_code = ERR_SEND_TIME_GATE

    send_time_status = first_line_status
    if send_time_status not in {
        STATUS_PASS_REQUIRED,
        STATUS_FAIL_REQUIRED,
        STATUS_SKIPPED_NOT_REQUIRED,
        STATUS_WARN_NON_BLOCKING,
    }:
        send_time_status = STATUS_PASS_REQUIRED if p.returncode == 0 else STATUS_FAIL_REQUIRED

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        "operation": args.operation,
        "validator_operation": op_for_validator,
        "send_time_gate_enforced": bool(args.enforce_send_time_gate),
        "required_contract": bool(validator_payload.get("required_contract", False)),
        "send_time_gate_status": send_time_status,
        "error_code": error_code,
        "reply_first_line_status": first_line_status,
        "reply_evidence_mode": evidence_mode,
        "reply_evidence_ref": validator_payload.get("reply_evidence_ref", ""),
        "reply_sample_count": validator_payload.get("reply_sample_count", 0),
        "reply_first_line_missing_count": validator_payload.get("reply_first_line_missing_count", 0),
        "reply_first_line_missing_refs": validator_payload.get("reply_first_line_missing_refs", []),
        "expected_identity_id": validator_payload.get("expected_identity_id", ""),
        "reply_first_line_work_layer": validator_payload.get("reply_first_line_work_layer", ""),
        "reply_first_line_source_layer": validator_payload.get("reply_first_line_source_layer", ""),
        "blocker_receipt_path": validator_payload.get("blocker_receipt_path", ""),
        "stale_reasons": validator_payload.get("stale_reasons", []),
        "upstream_validator_rc": p.returncode,
    }
    if "blocker_receipt" in validator_payload:
        payload["blocker_receipt"] = validator_payload.get("blocker_receipt")

    _emit(payload, json_only=args.json_only)
    return 1 if p.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())

