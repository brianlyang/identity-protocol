#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from response_stamp_common import (
    ALLOWED_SOURCE_LAYERS,
    ALLOWED_WORK_LAYERS,
    render_external_stamp_with_layer_context,
    resolve_disclosure_level,
    resolve_layer_intent,
    resolve_stamp_context,
)


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
    reply_transport_ref = (
        str(Path(out_reply).expanduser().resolve()) if out_reply else "inline:governed_reply_compose"
    )

    validate_cmd = [
        sys.executable,
        "scripts/validate_send_time_reply_gate.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--reply-text",
        composed_reply,
        "--force-check",
        "--enforce-send-time-gate",
        "--reply-outlet-guard-applied",
        "--reply-transport-ref",
        reply_transport_ref,
        "--operation",
        "send-time",
        "--expected-work-layer",
        work_layer,
        "--expected-source-layer",
        source_layer,
        "--json-only",
    ]
    if str(args.blocker_receipt_out or "").strip():
        validate_cmd += ["--blocker-receipt-out", str(args.blocker_receipt_out).strip()]
    if str(args.layer_intent_text or "").strip():
        validate_cmd += ["--layer-intent-text", str(args.layer_intent_text).strip()]
    proc = subprocess.run(validate_cmd, capture_output=True, text=True)
    validate_payload = _json_payload(proc.stdout)

    if proc.returncode == 0 and out_reply:
        out_reply_path = Path(out_reply).expanduser().resolve()
        out_reply_path.parent.mkdir(parents=True, exist_ok=True)
        out_reply_path.write_text(composed_reply, encoding="utf-8")
    else:
        out_reply_path = Path(out_reply).expanduser().resolve() if out_reply else None

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
        "reply_sample_count": validate_payload.get("reply_sample_count"),
        "reply_first_line_missing_count": validate_payload.get("reply_first_line_missing_count"),
        "blocker_receipt_path": str(validate_payload.get("blocker_receipt_path", "")),
        "out_reply_file": str(out_reply_path) if out_reply and out_reply_path else "",
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
