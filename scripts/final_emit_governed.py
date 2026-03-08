#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from final_emit_contract_common import FINAL_EMIT_CHANNEL_ID

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_BODY_EMPTY = "IP-FE-001"
ERR_COMPOSE_RUNTIME = "IP-FE-002"
ERR_COMPOSE_JSON_MISSING = "IP-FE-003"
ERR_EGRESS_CONTRACT_FAILED = "IP-FE-004"
ERR_REPLY_FILE_MISSING = "IP-FE-005"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        doc = json.loads(text)
        return doc if isinstance(doc, dict) else None
    except Exception:
        return None


def _resolve_body(args: argparse.Namespace) -> tuple[str, str]:
    body_text = str(args.body_text or "")
    if str(args.body_file or "").strip():
        body_file = Path(str(args.body_file).strip()).expanduser().resolve()
        if not body_file.exists():
            raise FileNotFoundError(f"body file not found: {body_file}")
        body_text = body_file.read_text(encoding="utf-8", errors="ignore")
    elif args.stdin_body:
        body_text = sys.stdin.read()
    normalized = str(body_text or "").strip()
    if not normalized:
        raise ValueError("empty body")
    return normalized, "stdin" if args.stdin_body else ("body_file" if str(args.body_file or "").strip() else "body_text")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Final egress single-entry wrapper. "
            "Always routes through compose_and_validate_governed_reply and emits reply only when contracts pass."
        )
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", required=True)
    ap.add_argument("--body-text", default="")
    ap.add_argument("--body-file", default="")
    ap.add_argument("--stdin-body", action="store_true")
    ap.add_argument("--work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--out-reply-file", default="")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        body, body_mode = _resolve_body(args)
    except Exception as exc:
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_BODY_EMPTY,
            "stale_reasons": [f"body_invalid:{exc}"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    compose_cmd = [
        sys.executable,
        str((SCRIPT_DIR / "compose_and_validate_governed_reply.py").resolve()),
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(Path(args.catalog).expanduser().resolve()),
        "--repo-catalog",
        str(Path(args.repo_catalog).expanduser().resolve()),
        "--actor-id",
        str(args.actor_id).strip(),
        "--body-text",
        body,
        "--outlet-channel-id",
        FINAL_EMIT_CHANNEL_ID,
        "--json-only",
    ]
    if str(args.work_layer or "").strip():
        compose_cmd += ["--work-layer", str(args.work_layer).strip()]
    if str(args.source_layer or "").strip():
        compose_cmd += ["--source-layer", str(args.source_layer).strip()]
    if str(args.layer_intent_text or "").strip():
        compose_cmd += ["--layer-intent-text", str(args.layer_intent_text).strip()]
    if str(args.out_reply_file or "").strip():
        compose_cmd += ["--out-reply-file", str(args.out_reply_file).strip()]
    if str(args.out_json or "").strip():
        compose_cmd += ["--out-json", str(args.out_json).strip()]
    if str(args.blocker_receipt_out or "").strip():
        compose_cmd += ["--blocker-receipt-out", str(args.blocker_receipt_out).strip()]

    proc = subprocess.run(compose_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    compose_payload = _parse_json_payload(proc.stdout or "")
    if proc.returncode != 0 and compose_payload is None:
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_COMPOSE_RUNTIME,
            "compose_rc": proc.returncode,
            "stderr_tail": (proc.stderr or "").strip().splitlines()[-1] if (proc.stderr or "").strip() else "",
        }
        _emit(payload, json_only=args.json_only)
        return 1
    if compose_payload is None:
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_COMPOSE_JSON_MISSING,
            "compose_rc": proc.returncode,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    send_time_status = str(compose_payload.get("send_time_gate_status", "")).strip().upper()
    final_emit_status = str(compose_payload.get("final_emit_contract_status", "")).strip().upper()
    emit_allowed = bool(compose_payload.get("reply_emit_allowed", False))
    out_reply_file = str(compose_payload.get("out_reply_file", "")).strip()
    pass_contract = (
        proc.returncode == 0
        and send_time_status == STATUS_PASS_REQUIRED
        and final_emit_status == STATUS_PASS_REQUIRED
        and emit_allowed
    )

    payload: dict[str, Any] = {
        "final_emit_guard_status": STATUS_PASS_REQUIRED if pass_contract else STATUS_FAIL_REQUIRED,
        "error_code": "" if pass_contract else ERR_EGRESS_CONTRACT_FAILED,
        "compose_rc": proc.returncode,
        "body_mode": body_mode,
        "send_time_gate_status": send_time_status,
        "final_emit_contract_status": final_emit_status,
        "reply_emit_allowed": emit_allowed,
        "out_reply_file": out_reply_file,
        "identity_id": str(compose_payload.get("identity_id", "")),
        "outlet_channel_id": str(compose_payload.get("outlet_channel_id", "")),
    }
    if not pass_contract:
        payload["stale_reasons"] = ["egress_contract_not_pass"]
        _emit(payload, json_only=args.json_only)
        return 1

    reply_path = Path(out_reply_file).expanduser().resolve()
    if not reply_path.exists():
        payload["final_emit_guard_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REPLY_FILE_MISSING
        payload["stale_reasons"] = ["reply_file_missing_after_compose_pass"]
        _emit(payload, json_only=args.json_only)
        return 1

    reply_text = reply_path.read_text(encoding="utf-8", errors="ignore")
    if args.json_only:
        payload["reply_preview"] = reply_text.splitlines()[:2]
        _emit(payload, json_only=True)
    else:
        print(reply_text.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
