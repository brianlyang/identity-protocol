#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from response_stamp_common import (
    ALLOWED_SOURCE_LAYERS,
    ALLOWED_WORK_LAYERS,
    render_external_stamp_with_layer_context,
    render_internal_stamp,
    render_structured_context,
    resolve_layer_intent,
    resolve_disclosure_level,
    resolve_stamp_context,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render dynamic identity response stamp (external/internal).")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--view", choices=["external", "internal", "dual"], default="external")
    ap.add_argument("--disclosure-level", choices=["minimal", "standard", "verbose", "audit"], default="")
    ap.add_argument("--work-layer", default="", help="explicit work layer override (protocol|instance|dual)")
    ap.add_argument("--source-layer", default="", help="explicit source layer override (project|global|env|auto)")
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
            explicit_catalog=bool(args.catalog.strip()),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve stamp context: {exc}")
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
        "protocol_triggered": bool(intent.get("protocol_triggered", False)),
        "protocol_trigger_reasons": list(intent.get("protocol_trigger_reasons") or []),
        "protocol_trigger_confidence": float(intent.get("protocol_trigger_confidence", 0.0) or 0.0),
        "layer_intent_text": str(args.layer_intent_text or "").strip(),
        "external_stamp": external,
        "internal_stamp": internal,
        "identity_context": render_structured_context(
            ctx,
            work_layer=work_layer,
            source_layer=source_layer,
        ),
    }

    if args.out.strip():
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    if args.view in {"external", "dual"}:
        print(external)
    if args.view in {"internal", "dual"}:
        print(internal)
    print(json.dumps({"identity_context": payload["identity_context"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
