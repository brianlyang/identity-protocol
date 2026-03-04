#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actor_session_common import load_actor_binding
from response_stamp_common import (
    ALLOWED_SOURCE_LAYERS,
    ALLOWED_WORK_LAYERS,
    render_external_stamp_with_layer_context,
    resolve_disclosure_level,
    resolve_layer_intent,
    resolve_stamp_context,
)

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ERR_RUNTIME_BINDING_MISMATCH = "IP-ASB-STAMP-SESSION-005"


def _load_body(args: argparse.Namespace) -> str:
    body_text = str(args.body_text or "")
    body_file = str(args.body_file or "").strip()
    if body_file:
        p = Path(body_file).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"body file not found: {p}")
        body_text = p.read_text(encoding="utf-8", errors="ignore")
    text = body_text.strip()
    if not text:
        raise ValueError("reply body is empty; pass --body-text or --body-file")
    return text


def _json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        doc = json.loads(text)
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _emit(payload: dict[str, Any], *, json_only: bool, composed_reply: str) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return
    print(composed_reply.rstrip())
    print("")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Compose governed reply with mandatory first-line Identity-Context stamp, "
            "then run send-time fail-closed gate before output."
        )
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--body-text", default="")
    ap.add_argument("--body-file", default="")
    ap.add_argument("--work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--disclosure-level", choices=["minimal", "standard", "verbose", "audit"], default="standard")
    ap.add_argument("--out-reply-file", default="")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument("--preflight-receipt-out", default="")
    ap.add_argument("--outlet-channel-id", default="governed_adapter_v1")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        body = _load_body(args)
    except Exception as exc:
        print(f"[FAIL] invalid body input: {exc}")
        return 2

    try:
        ctx = resolve_stamp_context(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            actor_id=str(args.actor_id or "").strip(),
            explicit_catalog=bool(str(args.catalog or "").strip()),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity stamp context: {exc}")
        return 1

    actor_id_explicit = str(args.actor_id or "").strip()
    actor_bound_identity = ""
    if actor_id_explicit:
        actor_binding = load_actor_binding(catalog_path, actor_id_explicit)
        actor_bound_identity = str(actor_binding.get("identity_id", "")).strip()

    if actor_id_explicit and actor_bound_identity and actor_bound_identity != str(args.identity_id or "").strip():
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "repo_catalog_path": str(repo_catalog_path),
            "work_layer": "",
            "source_layer": "",
            "protocol_triggered": False,
            "protocol_trigger_reasons": ["actor_binding_lock_mismatch"],
            "intent_source": "strict_actor_binding_guard",
            "intent_confidence": 1.0,
            "fallback_reason": "actor_binding_lock_mismatch",
            "disclosure_level": "standard",
            "send_time_gate_status": "FAIL_REQUIRED",
            "send_time_error_code": ERR_RUNTIME_BINDING_MISMATCH,
            "error_code": ERR_RUNTIME_BINDING_MISMATCH,
            "send_time_rc": 1,
            "reply_first_line_status": "FAIL_REQUIRED",
            "reply_evidence_mode": "none",
            "reply_transport_ref": "",
            "reply_outlet_guard_applied": True,
            "governed_outlet_enforced": False,
            "outlet_channel_id": str(args.outlet_channel_id or "").strip() or "governed_adapter_v1",
            "outlet_preflight_receipt": "",
            "outlet_bypass_detected": True,
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "blocker_receipt_path": "",
            "out_reply_file": str(Path(args.out_reply_file).expanduser().resolve()) if str(args.out_reply_file or "").strip() else "",
            "context_lock_state": str(ctx.lock_state or "").strip(),
            "actor_bound_identity_id": actor_bound_identity,
        }
        out_json = str(args.out_json or "").strip()
        if out_json:
            out_json_path = Path(out_json).expanduser().resolve()
            out_json_path.parent.mkdir(parents=True, exist_ok=True)
            out_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    disclosure = resolve_disclosure_level(ctx, explicit_level=str(args.disclosure_level or "standard"))
    disclosure_level = str(disclosure.get("disclosure_level", "standard")).strip() or "standard"
    intent = resolve_layer_intent(
        explicit_work_layer=str(args.work_layer or "").strip(),
        explicit_source_layer=str(args.source_layer or "").strip(),
        intent_text=str(args.layer_intent_text or "").strip(),
        default_work_layer="instance",
        default_source_layer=ctx.source_domain,
    )
    work_layer = str(intent.get("resolved_work_layer", "")).strip().lower() or "instance"
    source_layer = str(intent.get("resolved_source_layer", "")).strip().lower() or ctx.source_domain
    if work_layer not in ALLOWED_WORK_LAYERS:
        work_layer = "instance"
    if source_layer not in ALLOWED_SOURCE_LAYERS:
        source_layer = "auto"

    stamp_line = render_external_stamp_with_layer_context(
        ctx,
        disclosure_level=disclosure_level,
        work_layer=work_layer,
        source_layer=source_layer,
    )
    composed_reply = f"{stamp_line}\n{body}\n"
    out_reply = str(args.out_reply_file or "").strip()
    out_reply_path = (
        Path(out_reply).expanduser().resolve()
        if out_reply
        else (Path("/tmp") / f"identity-governed-reply-{args.identity_id}.txt").resolve()
    )
    out_reply_path.parent.mkdir(parents=True, exist_ok=True)
    out_reply_path.write_text(composed_reply, encoding="utf-8")
    reply_transport_ref = str(out_reply_path)

    validate_cmd = [
        sys.executable,
        str((SCRIPT_DIR / "validate_send_time_reply_gate.py").resolve()),
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--reply-file",
        str(out_reply_path),
        "--force-check",
        "--enforce-send-time-gate",
        "--reply-outlet-guard-applied",
        "--reply-transport-ref",
        reply_transport_ref,
        "--outlet-channel-id",
        str(args.outlet_channel_id or "").strip() or "governed_adapter_v1",
        "--operation",
        "send-time",
        "--expected-work-layer",
        work_layer,
        "--expected-source-layer",
        source_layer,
        "--json-only",
    ]
    if str(args.actor_id or "").strip():
        validate_cmd += ["--actor-id", str(args.actor_id).strip()]
    if str(args.blocker_receipt_out or "").strip():
        validate_cmd += ["--blocker-receipt-out", str(args.blocker_receipt_out).strip()]
    if str(args.layer_intent_text or "").strip():
        validate_cmd += ["--layer-intent-text", str(args.layer_intent_text).strip()]
    proc = subprocess.run(validate_cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    validate_payload = _json_payload(proc.stdout)

    default_preflight_receipt = (Path("/tmp") / f"identity-governed-outlet-preflight-{args.identity_id}.json").resolve()
    preflight_receipt_path: Path | None = (
        Path(str(args.preflight_receipt_out).strip()).expanduser().resolve()
        if str(args.preflight_receipt_out or "").strip()
        else default_preflight_receipt
    )
    try:
        preflight_receipt_path.parent.mkdir(parents=True, exist_ok=True)
        preflight_receipt = {
            "receipt_type": "governed_outlet_preflight_v1",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "identity_id": args.identity_id,
            "work_layer": work_layer,
            "source_layer": source_layer,
            "send_time_gate_status": str(validate_payload.get("send_time_gate_status", "")),
            "error_code": str(validate_payload.get("error_code", "")),
            "governed_outlet_enforced": bool(validate_payload.get("governed_outlet_enforced", False)),
            "outlet_channel_id": str(validate_payload.get("outlet_channel_id", "")),
            "outlet_bypass_detected": bool(validate_payload.get("outlet_bypass_detected", False)),
            "reply_transport_ref": str(validate_payload.get("reply_transport_ref", "")),
            "reply_evidence_mode": str(validate_payload.get("reply_evidence_mode", "")),
            "blocker_receipt_path": str(validate_payload.get("blocker_receipt_path", "")),
        }
        preflight_receipt_path.write_text(
            json.dumps(preflight_receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        preflight_receipt_path = None

    if proc.returncode != 0 and not out_reply:
        # keep temporary reply evidence for strict fail-closed replay
        pass

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "repo_catalog_path": str(repo_catalog_path),
        "work_layer": work_layer,
        "source_layer": source_layer,
        "protocol_triggered": bool(intent.get("protocol_triggered", False)),
        "protocol_trigger_reasons": list(intent.get("protocol_trigger_reasons") or []),
        "intent_source": str(intent.get("intent_source", "")),
        "intent_confidence": intent.get("intent_confidence"),
        "fallback_reason": str(intent.get("fallback_reason", "")),
        "disclosure_level": disclosure_level,
        "send_time_gate_status": str(validate_payload.get("send_time_gate_status", "")),
        "send_time_error_code": str(validate_payload.get("error_code", "")),
        "error_code": str(validate_payload.get("error_code", "")),
        "send_time_rc": proc.returncode,
        "reply_first_line_status": str(validate_payload.get("reply_first_line_status", "")),
        "reply_evidence_mode": str(validate_payload.get("reply_evidence_mode", "")),
        "reply_transport_ref": str(validate_payload.get("reply_transport_ref", "")),
        "reply_outlet_guard_applied": bool(validate_payload.get("reply_outlet_guard_applied", False)),
        "governed_outlet_enforced": bool(validate_payload.get("governed_outlet_enforced", False)),
        "outlet_channel_id": str(validate_payload.get("outlet_channel_id", str(args.outlet_channel_id or "").strip())),
        "outlet_preflight_receipt": str(preflight_receipt_path) if preflight_receipt_path else "",
        "outlet_bypass_detected": bool(validate_payload.get("outlet_bypass_detected", False)),
        "reply_sample_count": validate_payload.get("reply_sample_count"),
        "reply_first_line_missing_count": validate_payload.get("reply_first_line_missing_count"),
        "blocker_receipt_path": str(validate_payload.get("blocker_receipt_path", "")),
        "out_reply_file": str(out_reply_path),
    }

    out_json = str(args.out_json or "").strip()
    if out_json:
        out_json_path = Path(out_json).expanduser().resolve()
        out_json_path.parent.mkdir(parents=True, exist_ok=True)
        out_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _emit(payload, json_only=args.json_only, composed_reply=composed_reply)
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
