#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from identity_runtime_authority_common import (
    STATUS_PASS_REQUIRED,
    validate_runtime_egress_identity_authority,
)
from governed_reply_observability_common import build_headstamp_consistency_projection
from response_stamp_common import (
    ALLOWED_SOURCE_LAYERS,
    ALLOWED_WORK_LAYERS,
    build_operator_machine_verification_payload,
    DEFAULT_MACHINE_VERIFICATION_SOURCE,
    normalize_response_stamp_profile,
    render_machine_verification_line,
    render_operator_headstamp_lines,
    render_external_stamp_with_layer_context,
    render_internal_stamp,
    render_structured_context,
    resolve_layer_intent,
    resolve_disclosure_level,
    resolve_task_response_stamp_profile,
    resolve_stamp_context,
)

def main() -> int:
    ap = argparse.ArgumentParser(description="Render dynamic identity response stamp (external/internal).")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="", help="optional actor session selector (run:<id>) for M:N binding alignment")
    ap.add_argument("--view", choices=["external", "internal", "dual"], default="external")
    ap.add_argument("--disclosure-level", choices=["minimal", "standard", "verbose", "audit"], default="")
    ap.add_argument("--work-layer", default="", help="explicit work layer override (protocol|instance|dual)")
    ap.add_argument("--source-layer", default="", help="explicit source layer override (project|global)")
    ap.add_argument(
        "--layer-intent-text",
        default="",
        help="optional natural-language intent used for auto work/source layer resolution",
    )
    ap.add_argument("--trigger-text", default="", help="optional natural-language stamp level trigger")
    ap.add_argument("--trigger-scope", choices=["once", "session"], default="")
    ap.add_argument(
        "--persist-session-trigger",
        action="store_true",
        help="legacy compatibility switch; session trigger persistence is enabled by default",
    )
    ap.add_argument(
        "--no-persist-session-trigger",
        action="store_true",
        help="disable session-trigger persistence (useful for sandbox dry-runs)",
    )
    ap.add_argument(
        "--machine-payload-json",
        default="",
        help="optional JSON object merged into Machine-Verification rendering",
    )
    ap.add_argument(
        "--machine-payload-file",
        default="",
        help="optional path to JSON object merged into Machine-Verification rendering",
    )
    ap.add_argument(
        "--render-operator-envelope",
        action="store_true",
        help="print Display-Headstamp + Machine-Verification lines instead of raw external/internal stamps",
    )
    ap.add_argument("--out", default="", help="optional path to persist rendered stamp payload JSON")
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
        ctx = resolve_stamp_context(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            actor_id=args.actor_id,
            session_id=args.session_id,
            explicit_catalog=bool(args.catalog.strip()),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve stamp context: {exc}")
        return 1

    authority = validate_runtime_egress_identity_authority(
        catalog_path=catalog_path,
        identity_id=ctx.identity_id,
        actor_id=args.actor_id,
        session_id=str(args.session_id or "").strip(),
    )
    if str(authority.get("identity_authority_status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        payload = {
            "identity_id": ctx.identity_id,
            "catalog_path": str(catalog_path),
            "pack_path": str(ctx.pack_path),
            "view": args.view,
            "session_id": str(args.session_id or "").strip(),
            "work_layer": str(args.work_layer or "").strip().lower() or "instance",
            "source_layer": str(args.source_layer or "").strip().lower() or str(ctx.source_domain or ""),
            "layer_intent_resolution_status": "FAIL_REQUIRED",
            "identity_authority_status": str(authority.get("identity_authority_status", "")).strip(),
            "error_code": str(authority.get("identity_authority_error_code", "")).strip(),
            "stale_reasons": list(authority.get("identity_authority_stale_reasons") or []),
            "identity_authority_next_action": str(authority.get("identity_authority_next_action", "")).strip(),
        }
        payload.update(authority)
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    persist_session_trigger = not bool(args.no_persist_session_trigger)
    disclosure = resolve_disclosure_level(
        ctx,
        explicit_level=args.disclosure_level,
        trigger_text=args.trigger_text,
        trigger_scope=args.trigger_scope,
        persist_session_trigger=persist_session_trigger,
    )
    disclosure_level = str(disclosure.get("disclosure_level", "standard")).strip() or "standard"
    response_stamp_profile = resolve_task_response_stamp_profile(ctx)
    response_stamp_profile = normalize_response_stamp_profile(
        response_stamp_profile,
        disclosure_level=disclosure_level,
    )
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
    external = render_external_stamp_with_layer_context(
        ctx,
        disclosure_level=disclosure_level,
        work_layer=work_layer,
        source_layer=source_layer,
    )
    internal = render_internal_stamp(ctx)
    payload = {
        "identity_id": ctx.identity_id,
        "catalog_path": str(ctx.catalog_path),
        "pack_path": str(ctx.pack_path),
        "view": args.view,
        "disclosure_level": disclosure_level,
        "response_stamp_profile": response_stamp_profile,
        "session_id": str(args.session_id or "").strip(),
        "disclosure_source": disclosure.get("disclosure_source", ""),
        "trigger_applied": bool(disclosure.get("trigger_applied", False)),
        "trigger_scope": disclosure.get("trigger_scope", ""),
        "trigger_text": disclosure.get("trigger_text", ""),
        "trigger_confidence": disclosure.get("trigger_confidence", 0.0),
        "session_profile_path": disclosure.get("session_profile_path", ""),
        "work_layer": work_layer,
        "source_layer": source_layer,
        "layer_intent_resolution_status": "PASS_REQUIRED"
        if work_layer in ALLOWED_WORK_LAYERS and source_layer in ALLOWED_SOURCE_LAYERS
        else "FAIL_REQUIRED",
        "resolved_work_layer": work_layer,
        "resolved_source_layer": source_layer,
        "intent_confidence": intent.get("intent_confidence", 0.0),
        "intent_source": intent.get("intent_source", "default_fallback"),
        "fallback_reason": intent.get("fallback_reason", ""),
        "fallback_reason_raw": intent.get("fallback_reason_raw", intent.get("fallback_reason", "")),
        "fallback_taxonomy_class": intent.get("fallback_taxonomy_class", ""),
        "fallback_taxonomy_version": intent.get("fallback_taxonomy_version", ""),
        "protocol_triggered": bool(intent.get("protocol_triggered", False)),
        "protocol_trigger_reasons": list(intent.get("protocol_trigger_reasons") or []),
        "protocol_trigger_confidence": float(intent.get("protocol_trigger_confidence", 0.0) or 0.0),
        "layer_intent_text": str(args.layer_intent_text or "").strip(),
        "identity_authority_status": str(authority.get("identity_authority_status", "")).strip(),
        "identity_authority_error_code": str(authority.get("identity_authority_error_code", "")).strip(),
        "identity_authority_selected_identity_id": str(
            authority.get("identity_authority_selected_identity_id", "")
        ).strip(),
        "identity_authority_authoritative_identity_id": str(
            authority.get("identity_authority_authoritative_identity_id", "")
        ).strip(),
        "identity_authority_resolution_mode": str(authority.get("identity_authority_resolution_mode", "")).strip(),
        "identity_authority_next_action": str(authority.get("identity_authority_next_action", "")).strip(),
        "identity_authority_stale_reasons": list(authority.get("identity_authority_stale_reasons") or []),
        "external_stamp": external,
        "internal_stamp": internal,
        "identity_context": render_structured_context(
            ctx,
            work_layer=work_layer,
            source_layer=source_layer,
        ),
    }
    payload.update(
        build_headstamp_consistency_projection(
            display_identity_id=ctx.identity_id,
            authoritative_identity_id=str(
                authority.get("identity_authority_authoritative_identity_id", "")
            ).strip()
            or ctx.identity_id,
        )
    )

    machine_payload: dict[str, object] = build_operator_machine_verification_payload(
        payload,
        verification_source=DEFAULT_MACHINE_VERIFICATION_SOURCE,
    )
    if str(args.machine_payload_file or "").strip():
        extra_path = Path(args.machine_payload_file).expanduser().resolve()
        if not extra_path.exists():
            print(
                f"[FAIL] machine payload file not found: {extra_path}"
            )
            return 2
        extra_payload = json.loads(extra_path.read_text(encoding="utf-8"))
        if not isinstance(extra_payload, dict):
            print("[FAIL] machine payload file must contain a JSON object")
            return 2
        machine_payload.update(extra_payload)
    if str(args.machine_payload_json or "").strip():
        try:
            extra_payload = json.loads(str(args.machine_payload_json or "").strip())
        except json.JSONDecodeError as exc:
            print(f"[FAIL] invalid --machine-payload-json: {exc}")
            return 2
        if not isinstance(extra_payload, dict):
            print("[FAIL] --machine-payload-json must decode to a JSON object")
            return 2
        machine_payload.update(extra_payload)

    operator_envelope_lines = render_operator_headstamp_lines(
        ctx,
        disclosure_level=disclosure_level,
        work_layer=work_layer,
        source_layer=source_layer,
        machine_payload=machine_payload,
    )
    payload["machine_verification"] = machine_payload
    payload["machine_verification_line"] = render_machine_verification_line(machine_payload)
    payload["display_headstamp_line"] = operator_envelope_lines[0] if operator_envelope_lines else ""
    payload["operator_envelope_lines"] = operator_envelope_lines
    payload["operator_envelope"] = "\n".join(operator_envelope_lines)

    if args.out.strip():
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    if args.render_operator_envelope:
        for line in operator_envelope_lines:
            print(line)
        return 0

    if args.view in {"external", "dual"}:
        print(external)
    if args.view in {"internal", "dual"}:
        print(internal)
    print(json.dumps({"identity_context": payload["identity_context"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
