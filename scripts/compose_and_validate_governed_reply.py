#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actor_session_common import (
    load_actor_binding,
    load_actor_binding_store,
    resolve_protocol_actor_id,
)
from final_emit_contract_common import (
    FINAL_EMIT_CHANNEL_ID,
    FINAL_EMIT_POLICY_MODE,
    FINAL_EMIT_SCHEMA_ID,
    FINAL_EMIT_SCHEMA_REQUIRED_FIELDS,
)
from governed_reply_observability_common import (
    build_headstamp_consistency_projection,
    build_identity_observability_projection,
    build_sender_consumption_projection,
    classify_headstamp_visibility,
    parse_probe_identity_contexts,
)
from headstamp_error_family_common import ERR_HDSTAMP_ACTOR_LAYER_MISMATCH, inject_legacy_error_fields
from identity_runtime_authority_common import (
    STATUS_PASS_REQUIRED as AUTHORITY_PASS_REQUIRED,
    validate_runtime_egress_identity_authority,
)
from response_stamp_common import (
    ALLOWED_SOURCE_LAYERS,
    ALLOWED_WORK_LAYERS,
    build_operator_machine_verification_payload,
    CONTROLLED_RUNTIME_MACHINE_VERIFICATION_SOURCE,
    parse_identity_context_stamp,
    render_operator_headstamp_lines,
    render_visible_reply_with_operator_envelope,
    render_external_stamp_with_layer_context,
    resolve_disclosure_level,
    resolve_layer_intent,
    resolve_stamp_context,
)
from runtime_temp_path_common import runtime_temp_file

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ERR_RUNTIME_BINDING_MISMATCH = ERR_HDSTAMP_ACTOR_LAYER_MISMATCH
ERR_ACTOR_ENTRY_REQUIRED = "IP-ACTOR-ENTRY-001"
ERR_SESSION_ENTRY_REQUIRED = "IP-ASB-SESSION-ENTRY-001"
STATUS_PASS_REQUIRED = "PASS_REQUIRED"


def _normalize_embedded_identity_context_line(raw_line: str) -> str:
    line = str(raw_line or "").strip()
    if not line:
        return ""

    # Strip common quoted/bullet prefixes to prevent pasted foreign headstamps
    # from being interpreted as executable routing input.
    trimmed = line
    while True:
        changed = False
        for prefix in (">", "-", "*"):
            if trimmed.startswith(prefix):
                trimmed = trimmed[len(prefix) :].lstrip()
                changed = True
        if not changed:
            break

    marker = "Identity-Context:"
    idx = trimmed.find(marker)
    if idx < 0:
        return ""
    return trimmed[idx:].strip()


def _inspect_embedded_identity_context(
    *,
    body_text: str,
    expected_identity_id: str,
) -> dict[str, Any]:
    expected_id = str(expected_identity_id or "").strip()
    refs: list[dict[str, Any]] = []
    identities: set[str] = set()
    foreign_ids: set[str] = set()

    for line_no, raw_line in enumerate(str(body_text or "").splitlines(), start=1):
        normalized = _normalize_embedded_identity_context_line(raw_line)
        if not normalized:
            continue
        parsed = parse_identity_context_stamp(normalized)
        identity_id = str(parsed.get("identity_id", "")).strip()
        actor_id = str(parsed.get("actor_id", "")).strip()
        if identity_id:
            identities.add(identity_id)
            if expected_id and identity_id != expected_id:
                foreign_ids.add(identity_id)
        refs.append(
            {
                "line_no": line_no,
                "identity_id": identity_id,
                "actor_id": actor_id,
                "raw": normalized,
            }
        )

    foreign_detected = bool(foreign_ids)
    guard_reason = "no_embedded_identity_context"
    if refs and foreign_detected:
        guard_reason = "embedded_foreign_identity_context_ignored"
    elif refs:
        guard_reason = "embedded_identity_context_same_identity_ignored"

    return {
        "quoted_identity_context_detected": bool(refs),
        "quoted_identity_context_line_count": len(refs),
        "quoted_identity_context_ids": sorted(identities),
        "quoted_identity_context_foreign_detected": foreign_detected,
        "quoted_identity_context_foreign_ids": sorted(foreign_ids),
        "quoted_identity_context_refs": refs[:8],
        "quoted_identity_context_guard_applied": True,
        "quoted_identity_context_guard_reason": guard_reason,
        "quoted_identity_context_guard_status": STATUS_PASS_REQUIRED,
        "quoted_identity_context_binding_effect": "none",
    }


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


def _resolve_actor_binding_with_target(
    *,
    catalog_path: Path,
    actor_id: str,
    target_identity_id: str,
    session_id: str = "",
) -> tuple[dict[str, Any], dict[str, Any], str]:
    store = load_actor_binding_store(catalog_path, actor_id)
    selected = load_actor_binding(
        catalog_path,
        actor_id,
        identity_id=target_identity_id,
        session_id=session_id,
    )
    selection_mode = "identity_scoped"
    if not selected:
        selection_mode = "identity_scoped_missing"
    return selected, store, selection_mode


def _emit(
    payload: dict[str, Any],
    *,
    json_only: bool,
    visible_reply: str,
    allow_reply_emit: bool,
) -> None:
    payload = inject_legacy_error_fields(payload)
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return
    if allow_reply_emit:
        print(visible_reply.rstrip())
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
    ap.add_argument("--session-id", default="")
    ap.add_argument("--body-text", default="")
    ap.add_argument("--body-file", default="")
    ap.add_argument("--probe-context-json", default="")
    ap.add_argument("--probe-context-file", default="")
    ap.add_argument("--work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--disclosure-level", choices=["minimal", "standard", "verbose", "audit"], default="standard")
    ap.add_argument("--out-reply-file", default="")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument("--preflight-receipt-out", default="")
    ap.add_argument("--final-emit-receipt-out", default="")
    ap.add_argument("--outlet-channel-id", default=FINAL_EMIT_CHANNEL_ID)
    ap.add_argument(
        "--host-visible-shadow-root",
        default="",
        help=(
            "optional shadow root that mirrors host-visible runtime closure-state for isolated "
            "precheck/replay execution without mutating live singleton state"
        ),
    )
    ap.add_argument(
        "--current-surface-native-machine-attested",
        action="store_true",
        help="allow current-surface governed transport attestation for controlled runtime entrypoints",
    )
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

    probe_identity_contexts = parse_probe_identity_contexts(
        probe_context_json=str(args.probe_context_json or "").strip(),
        probe_context_file=str(args.probe_context_file or "").strip(),
    )

    def _project_payload(
        payload: dict[str, Any],
        *,
        effective_bound_identity_id: str = "",
        quoted_guard: dict[str, Any] | None = None,
        actor_id_override: str = "",
        session_id_override: str = "",
    ) -> dict[str, Any]:
        augmented = dict(payload)
        augmented.update(
            build_identity_observability_projection(
                expected_identity_id=str(args.identity_id or "").strip(),
                actor_id=str(actor_id_override or args.actor_id or "").strip(),
                session_id=str(session_id_override or args.session_id or "").strip(),
                effective_bound_identity_id=str(effective_bound_identity_id or "").strip(),
                quoted_identity_context_guard=quoted_guard,
                probe_identity_contexts=probe_identity_contexts,
            )
        )
        augmented.update(
            classify_headstamp_visibility(
                reply_first_line_status=augmented.get("reply_first_line_status", ""),
                send_time_gate_status=augmented.get("send_time_gate_status", ""),
                headstamp_first_line_status=augmented.get("headstamp_first_line_status", ""),
            )
        )
        augmented.update(
            build_sender_consumption_projection(
                out_reply_file=augmented.get("out_reply_file", ""),
                reply_transport_ref=augmented.get("reply_transport_ref", ""),
                reply_emit_allowed=bool(augmented.get("reply_emit_allowed", False)),
            )
        )
        if not str(augmented.get("headstamp_consistency_status", "")).strip():
            augmented.update(
                build_headstamp_consistency_projection(
                    display_identity_id=str(
                        augmented.get(
                            "display_headstamp_identity_id",
                            augmented.get("reply_first_line_identity_id", ""),
                        )
                    ).strip(),
                    authoritative_identity_id=str(
                        augmented.get(
                            "authoritative_identity_id",
                            augmented.get("identity_authority_authoritative_identity_id", ""),
                        )
                    ).strip()
                    or str(args.identity_id or "").strip(),
                    correction_evidence_ref=str(
                        augmented.get("headstamp_correction_evidence_ref", "")
                    ).strip(),
                )
            )
        return augmented

    actor_id_input = str(args.actor_id or "").strip()
    if not actor_id_input:
        payload = _project_payload({
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "repo_catalog_path": str(repo_catalog_path),
            "send_time_gate_status": "FAIL_REQUIRED",
            "send_time_error_code": ERR_ACTOR_ENTRY_REQUIRED,
            "error_code": ERR_ACTOR_ENTRY_REQUIRED,
            "reply_first_line_status": "FAIL_REQUIRED",
            "reply_evidence_mode": "none",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_outlet_guard_applied": False,
            "governed_outlet_enforced": False,
            "outlet_bypass_detected": True,
            "outlet_channel_id": str(args.outlet_channel_id or "").strip() or FINAL_EMIT_CHANNEL_ID,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": FINAL_EMIT_POLICY_MODE,
            "final_emit_schema_id": FINAL_EMIT_SCHEMA_ID,
            "final_emit_schema_status": "FAIL_REQUIRED",
            "final_emit_contract_status": "FAIL_REQUIRED",
            "stale_reasons": ["actor_id_required"],
        })
        out_json = str(args.out_json or "").strip()
        if out_json:
            out_json_path = Path(out_json).expanduser().resolve()
            out_json_path.parent.mkdir(parents=True, exist_ok=True)
            out_json_path.write_text(
                json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(
            json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False)
            if args.json_only
            else json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2)
        )
        return 1
    session_id_input = str(args.session_id or "").strip()
    if not session_id_input:
        payload = _project_payload({
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "repo_catalog_path": str(repo_catalog_path),
            "send_time_gate_status": "FAIL_REQUIRED",
            "send_time_error_code": ERR_SESSION_ENTRY_REQUIRED,
            "error_code": ERR_SESSION_ENTRY_REQUIRED,
            "reply_first_line_status": "FAIL_REQUIRED",
            "reply_evidence_mode": "none",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_outlet_guard_applied": False,
            "governed_outlet_enforced": False,
            "outlet_bypass_detected": True,
            "outlet_channel_id": str(args.outlet_channel_id or "").strip() or FINAL_EMIT_CHANNEL_ID,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": FINAL_EMIT_POLICY_MODE,
            "final_emit_schema_id": FINAL_EMIT_SCHEMA_ID,
            "final_emit_schema_status": "FAIL_REQUIRED",
            "final_emit_contract_status": "FAIL_REQUIRED",
            "stale_reasons": ["session_id_required"],
        }, actor_id_override=actor_id_input)
        out_json = str(args.out_json or "").strip()
        if out_json:
            out_json_path = Path(out_json).expanduser().resolve()
            out_json_path.parent.mkdir(parents=True, exist_ok=True)
            out_json_path.write_text(
                json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(
            json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False)
            if args.json_only
            else json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2)
        )
        return 1

    try:
        body = _load_body(args)
    except Exception as exc:
        print(f"[FAIL] invalid body input: {exc}")
        return 2
    quoted_identity_context_guard = _inspect_embedded_identity_context(
        body_text=body,
        expected_identity_id=str(args.identity_id or "").strip(),
    )

    try:
        ctx = resolve_stamp_context(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            actor_id=actor_id_input,
            session_id=str(args.session_id or "").strip(),
            explicit_catalog=bool(str(args.catalog or "").strip()),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity stamp context: {exc}")
        return 1

    authority = validate_runtime_egress_identity_authority(
        catalog_path=catalog_path,
        identity_id=str(args.identity_id or "").strip(),
        actor_id=actor_id_input,
        session_id=str(args.session_id or "").strip(),
    )
    if str(authority.get("identity_authority_status", "")).strip().upper() != AUTHORITY_PASS_REQUIRED:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "repo_catalog_path": str(repo_catalog_path),
            "send_time_gate_status": "FAIL_REQUIRED",
            "send_time_error_code": str(authority.get("identity_authority_error_code", "")).strip(),
            "error_code": str(authority.get("identity_authority_error_code", "")).strip(),
            "reply_first_line_status": "FAIL_REQUIRED",
            "reply_evidence_mode": "none",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_outlet_guard_applied": True,
            "governed_outlet_enforced": False,
            "outlet_bypass_detected": True,
            "outlet_channel_id": str(args.outlet_channel_id or "").strip() or FINAL_EMIT_CHANNEL_ID,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": FINAL_EMIT_POLICY_MODE,
            "final_emit_schema_id": FINAL_EMIT_SCHEMA_ID,
            "final_emit_schema_status": "FAIL_REQUIRED",
            "final_emit_contract_status": "FAIL_REQUIRED",
            "resolved_actor_id": resolve_protocol_actor_id(actor_id_input),
            "stale_reasons": list(authority.get("identity_authority_stale_reasons") or []),
            "identity_authority_status": str(authority.get("identity_authority_status", "")).strip(),
            "identity_authority_next_action": str(authority.get("identity_authority_next_action", "")).strip(),
        }
        payload.update(authority)
        out_json = str(args.out_json or "").strip()
        if out_json:
            out_json_path = Path(out_json).expanduser().resolve()
            out_json_path.parent.mkdir(parents=True, exist_ok=True)
            out_json_path.write_text(
                json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(
            json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False)
            if args.json_only
            else json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2)
        )
        return 1

    actor_id_effective = resolve_protocol_actor_id(actor_id_input)
    actor_binding, actor_binding_store, actor_binding_selection_mode = _resolve_actor_binding_with_target(
        catalog_path=catalog_path,
        actor_id=actor_id_effective,
        target_identity_id=str(args.identity_id or "").strip(),
        session_id=str(args.session_id or "").strip(),
    )
    actor_bound_identity = str(actor_binding.get("identity_id", "")).strip()
    session_id_effective = session_id_input

    if session_id_effective and not actor_bound_identity:
        payload = _project_payload({
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "repo_catalog_path": str(repo_catalog_path),
            "send_time_gate_status": "FAIL_REQUIRED",
            "send_time_error_code": ERR_RUNTIME_BINDING_MISMATCH,
            "error_code": ERR_RUNTIME_BINDING_MISMATCH,
            "reply_first_line_status": "FAIL_REQUIRED",
            "reply_evidence_mode": "none",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_outlet_guard_applied": True,
            "governed_outlet_enforced": False,
            "outlet_bypass_detected": True,
            "outlet_channel_id": str(args.outlet_channel_id or "").strip() or FINAL_EMIT_CHANNEL_ID,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": FINAL_EMIT_POLICY_MODE,
            "final_emit_schema_id": FINAL_EMIT_SCHEMA_ID,
            "final_emit_schema_status": "FAIL_REQUIRED",
            "final_emit_contract_status": "FAIL_REQUIRED",
            "resolved_actor_id": actor_id_effective,
            "actor_bound_identity_id": actor_bound_identity,
            "actor_binding_selection_mode": actor_binding_selection_mode,
            "actor_binding_key_mode": str(actor_binding_store.get("binding_key_mode", "")),
            "actor_binding_compare_token": str(actor_binding_store.get("compare_token", "")),
            "actor_binding_session_id": str(actor_binding.get("session_id", "")),
            "stale_reasons": ["session_scoped_actor_binding_missing"],
        }, actor_id_override=actor_id_effective, session_id_override=session_id_effective)
        out_json = str(args.out_json or "").strip()
        if out_json:
            out_json_path = Path(out_json).expanduser().resolve()
            out_json_path.parent.mkdir(parents=True, exist_ok=True)
            out_json_path.write_text(
                json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(
            json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False)
            if args.json_only
            else json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2)
        )
        return 1

    if actor_bound_identity and actor_bound_identity != str(args.identity_id or "").strip():
        payload = _project_payload({
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
            "outlet_channel_id": str(args.outlet_channel_id or "").strip() or FINAL_EMIT_CHANNEL_ID,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": FINAL_EMIT_POLICY_MODE,
            "final_emit_schema_id": FINAL_EMIT_SCHEMA_ID,
            "final_emit_schema_status": "FAIL_REQUIRED",
            "final_emit_contract_status": "FAIL_REQUIRED",
            "outlet_preflight_receipt": "",
            "outlet_bypass_detected": True,
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "blocker_receipt_path": "",
            "out_reply_file": str(Path(args.out_reply_file).expanduser().resolve()) if str(args.out_reply_file or "").strip() else "",
            "context_lock_state": str(ctx.lock_state or "").strip(),
            "resolved_actor_id": actor_id_effective,
            "actor_bound_identity_id": actor_bound_identity,
            "actor_binding_selection_mode": actor_binding_selection_mode,
            "actor_binding_key_mode": str(actor_binding_store.get("binding_key_mode", "")),
            "actor_binding_compare_token": str(actor_binding_store.get("compare_token", "")),
            "actor_binding_session_id": str(actor_binding.get("session_id", "")),
        }, effective_bound_identity_id=actor_bound_identity, actor_id_override=actor_id_effective, session_id_override=session_id_effective)
        out_json = str(args.out_json or "").strip()
        if out_json:
            out_json_path = Path(out_json).expanduser().resolve()
            out_json_path.parent.mkdir(parents=True, exist_ok=True)
            out_json_path.write_text(
                json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(
            json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False)
            if args.json_only
            else json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2)
        )
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
        source_layer = "project"

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
        else runtime_temp_file(
            channel="response-stamp",
            operation="compose",
            identity_id=args.identity_id,
            stem=f"identity-governed-reply-{args.identity_id}",
            ext="txt",
        ).resolve()
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
        str(args.outlet_channel_id or "").strip() or FINAL_EMIT_CHANNEL_ID,
        "--final-emit-policy-mode",
        FINAL_EMIT_POLICY_MODE,
        "--final-emit-schema-status",
        "PASS_REQUIRED",
        "--final-emit-schema-id",
        FINAL_EMIT_SCHEMA_ID,
        "--operation",
        "send-time",
        "--expected-work-layer",
        work_layer,
        "--expected-source-layer",
        source_layer,
        "--json-only",
    ]
    if args.current_surface_native_machine_attested:
        validate_cmd.append("--current-surface-native-machine-attested")
    validate_cmd += ["--actor-id", str(actor_id_effective).strip()]
    if str(args.session_id or "").strip():
        validate_cmd += ["--session-id", str(args.session_id).strip()]
    if str(args.blocker_receipt_out or "").strip():
        validate_cmd += ["--blocker-receipt-out", str(args.blocker_receipt_out).strip()]
    if str(args.layer_intent_text or "").strip():
        validate_cmd += ["--layer-intent-text", str(args.layer_intent_text).strip()]
    if str(args.host_visible_shadow_root or "").strip():
        validate_cmd += ["--host-visible-shadow-root", str(args.host_visible_shadow_root).strip()]
    proc = subprocess.run(validate_cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    validate_payload = _json_payload(proc.stdout)

    default_preflight_receipt = runtime_temp_file(
        channel="response-stamp",
        operation="compose",
        identity_id=args.identity_id,
        stem=f"identity-governed-outlet-preflight-{args.identity_id}",
        ext="json",
    ).resolve()
    preflight_receipt_path: Path | None = (
        Path(str(args.preflight_receipt_out).strip()).expanduser().resolve()
        if str(args.preflight_receipt_out or "").strip()
        else default_preflight_receipt
    )
    default_final_emit_receipt = runtime_temp_file(
        channel="response-stamp",
        operation="compose",
        identity_id=args.identity_id,
        stem=f"identity-final-emit-receipt-{args.identity_id}",
        ext="json",
    ).resolve()
    final_emit_receipt_path: Path | None = (
        Path(str(args.final_emit_receipt_out).strip()).expanduser().resolve()
        if str(args.final_emit_receipt_out or "").strip()
        else default_final_emit_receipt
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
            "output_governance_mode": str(validate_payload.get("output_governance_mode", "")).strip(),
            "control_lane_attestation_status": str(
                validate_payload.get("control_lane_attestation_status", "")
            ).strip(),
            "next_hop_admission_status": str(validate_payload.get("next_hop_admission_status", "")).strip(),
            "next_hop_admission_reason": str(validate_payload.get("next_hop_admission_reason", "")).strip(),
            "outlet_channel_id": str(validate_payload.get("outlet_channel_id", "")),
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": str(validate_payload.get("final_emit_policy_mode", FINAL_EMIT_POLICY_MODE)),
            "final_emit_schema_id": str(validate_payload.get("final_emit_schema_id", FINAL_EMIT_SCHEMA_ID)),
            "final_emit_schema_status": str(validate_payload.get("final_emit_schema_status", "PASS_REQUIRED")),
            "final_emit_contract_status": str(validate_payload.get("final_emit_contract_status", "")),
            "outlet_bypass_detected": bool(validate_payload.get("outlet_bypass_detected", False)),
            "reply_transport_ref": str(validate_payload.get("reply_transport_ref", "")),
            "reply_evidence_mode": str(validate_payload.get("reply_evidence_mode", "")),
            "blocker_receipt_path": str(validate_payload.get("blocker_receipt_path", "")),
            "quoted_identity_context_detected": bool(
                quoted_identity_context_guard.get("quoted_identity_context_detected", False)
            ),
            "quoted_identity_context_foreign_detected": bool(
                quoted_identity_context_guard.get("quoted_identity_context_foreign_detected", False)
            ),
            "quoted_identity_context_foreign_ids": list(
                quoted_identity_context_guard.get("quoted_identity_context_foreign_ids") or []
            ),
            "quoted_identity_context_guard_status": str(
                quoted_identity_context_guard.get("quoted_identity_context_guard_status", "")
            ).strip(),
            "quoted_identity_context_binding_effect": str(
                quoted_identity_context_guard.get("quoted_identity_context_binding_effect", "")
            ).strip(),
        }
        preflight_receipt_path.write_text(
            json.dumps(preflight_receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        preflight_receipt_path = None
    try:
        if final_emit_receipt_path is not None:
            final_emit_receipt_path.parent.mkdir(parents=True, exist_ok=True)
            final_emit_receipt = {
                "receipt_type": "final_emit_governed_receipt_v1",
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "identity_id": args.identity_id,
                "actor_id": actor_id_effective,
                "effective_bound_identity_id": actor_bound_identity or str(args.identity_id or "").strip(),
                "effective_bound_actor_id": actor_id_effective,
                "effective_bound_session_id": session_id_effective,
                "work_layer": work_layer,
                "source_layer": source_layer,
                "lock_state": str(ctx.lock_state or "").strip(),
                "run_id": str(validate_payload.get("run_id_binding", "")).strip() or "compose-send-time",
                "headstamp_text": str(stamp_line).strip(),
                "body_text": str(body).strip(),
                "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
                "final_emit_policy_mode": FINAL_EMIT_POLICY_MODE,
                "final_emit_schema_id": FINAL_EMIT_SCHEMA_ID,
                "final_emit_schema_required_fields": list(FINAL_EMIT_SCHEMA_REQUIRED_FIELDS),
                "final_emit_schema_status": "PASS_REQUIRED",
                "final_emit_contract_status": str(validate_payload.get("final_emit_contract_status", "PASS_REQUIRED")),
                "quoted_identity_context_detected": bool(
                    quoted_identity_context_guard.get("quoted_identity_context_detected", False)
                ),
                "quoted_identity_context_foreign_detected": bool(
                    quoted_identity_context_guard.get("quoted_identity_context_foreign_detected", False)
                ),
                "quoted_identity_context_foreign_ids": list(
                    quoted_identity_context_guard.get("quoted_identity_context_foreign_ids") or []
                ),
                "quoted_identity_context_guard_status": str(
                    quoted_identity_context_guard.get("quoted_identity_context_guard_status", "")
                ).strip(),
                "quoted_identity_context_binding_effect": str(
                    quoted_identity_context_guard.get("quoted_identity_context_binding_effect", "")
                ).strip(),
                "quoted_identity_contexts": list(quoted_identity_context_guard.get("quoted_identity_context_refs") or []),
                "probe_identity_contexts": probe_identity_contexts,
            }
            final_emit_receipt_path.write_text(
                json.dumps(final_emit_receipt, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    except Exception:
        final_emit_receipt_path = None

    if proc.returncode != 0 and not out_reply:
        # keep temporary reply evidence for strict fail-closed replay
        pass

    payload = _project_payload({
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
        "send_time_block_stage": str(validate_payload.get("send_time_block_stage", "")).strip(),
        "reply_first_line_status": str(validate_payload.get("reply_first_line_status", "")),
        "reply_first_line_blocked_reason": str(
            validate_payload.get("reply_first_line_blocked_reason", "")
        ).strip(),
        "reply_evidence_mode": str(validate_payload.get("reply_evidence_mode", "")),
        "reply_transport_ref": str(validate_payload.get("reply_transport_ref", "")),
        "reply_transport_binding_issues": list(
            validate_payload.get("reply_transport_binding_issues") or []
        ),
        "governed_reply_transport_lifecycle_phase": str(
            validate_payload.get("governed_reply_transport_lifecycle_phase", "")
        ).strip(),
        "governed_reply_transport_lifecycle_status": str(
            validate_payload.get("governed_reply_transport_lifecycle_status", "")
        ).strip(),
        "governed_reply_transport_lifecycle_reason": str(
            validate_payload.get("governed_reply_transport_lifecycle_reason", "")
        ).strip(),
        "current_surface_transport_attestation_contract_id": str(
            validate_payload.get("current_surface_transport_attestation_contract_id", "")
        ).strip(),
        "current_surface_transport_attestation_status": str(
            validate_payload.get("current_surface_transport_attestation_status", "")
        ).strip(),
        "current_surface_transport_attestation_reason": str(
            validate_payload.get("current_surface_transport_attestation_reason", "")
        ).strip(),
        "current_surface_transport_attestation_mode": str(
            validate_payload.get("current_surface_transport_attestation_mode", "")
        ).strip(),
        "current_surface_native_machine_attested": bool(
            validate_payload.get("current_surface_native_machine_attested", False)
        ),
        "reply_outlet_guard_applied": bool(validate_payload.get("reply_outlet_guard_applied", False)),
        "governed_outlet_enforced": bool(validate_payload.get("governed_outlet_enforced", False)),
        "output_governance_mode": str(validate_payload.get("output_governance_mode", "")).strip(),
        "control_lane_attestation_status": str(
            validate_payload.get("control_lane_attestation_status", "")
        ).strip(),
        "next_hop_admission_status": str(validate_payload.get("next_hop_admission_status", "")).strip(),
        "next_hop_admission_reason": str(validate_payload.get("next_hop_admission_reason", "")).strip(),
        "outlet_channel_id": str(validate_payload.get("outlet_channel_id", str(args.outlet_channel_id or "").strip())),
        "final_emit_channel_id": str(validate_payload.get("final_emit_channel_id", FINAL_EMIT_CHANNEL_ID)),
        "final_emit_policy_mode": str(validate_payload.get("final_emit_policy_mode", FINAL_EMIT_POLICY_MODE)),
        "final_emit_schema_id": str(validate_payload.get("final_emit_schema_id", FINAL_EMIT_SCHEMA_ID)),
        "final_emit_schema_status": str(validate_payload.get("final_emit_schema_status", "")),
        "final_emit_contract_status": str(validate_payload.get("final_emit_contract_status", "")),
        "final_emit_receipt_path": str(final_emit_receipt_path) if final_emit_receipt_path else "",
        "outlet_preflight_receipt": str(preflight_receipt_path) if preflight_receipt_path else "",
        "outlet_bypass_detected": bool(validate_payload.get("outlet_bypass_detected", False)),
        "reply_sample_count": validate_payload.get("reply_sample_count"),
        "reply_first_line_missing_count": validate_payload.get("reply_first_line_missing_count"),
        "reply_first_line_identity_id": str(validate_payload.get("reply_first_line_identity_id", "")).strip(),
        "blocker_receipt_path": str(validate_payload.get("blocker_receipt_path", "")),
        "out_reply_file": str(out_reply_path),
        "actor_binding_selection_mode": actor_binding_selection_mode,
        "actor_binding_key_mode": str(actor_binding_store.get("binding_key_mode", "")),
        "actor_binding_compare_token": str(actor_binding_store.get("compare_token", "")),
        "actor_binding_session_id": str(actor_binding.get("session_id", "")),
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
        "host_transport_post_check_state_file": str(
            validate_payload.get("host_transport_post_check_state_file", "")
        ).strip(),
        "host_transport_post_check_state_path": str(
            validate_payload.get("host_transport_post_check_state_path", "")
        ).strip(),
        "host_transport_post_check_state_status": str(
            validate_payload.get("host_transport_post_check_state_status", "")
        ).strip(),
        "host_transport_post_check_runtime_scope": str(
            validate_payload.get("host_transport_post_check_runtime_scope", "")
        ).strip(),
        "host_transport_post_check_runtime_shadow_root": str(
            validate_payload.get("host_transport_post_check_runtime_shadow_root", "")
        ).strip(),
        "host_transport_post_check_state_live_path": str(
            validate_payload.get("host_transport_post_check_state_live_path", "")
        ).strip(),
        "host_transport_post_check_block_on_active": bool(
            validate_payload.get("host_transport_post_check_block_on_active", False)
        ),
        "host_transport_post_check_blocker_active": bool(
            validate_payload.get("host_transport_post_check_blocker_active", False)
        ),
        "host_transport_post_check_closure_status": str(
            validate_payload.get("host_transport_post_check_closure_status", "")
        ).strip(),
        "host_transport_post_check_error_code": str(
            validate_payload.get("host_transport_post_check_error_code", "")
        ).strip(),
        "display_headstamp_identity_id": str(validate_payload.get("display_headstamp_identity_id", "")).strip(),
        "authoritative_identity_id": str(validate_payload.get("authoritative_identity_id", "")).strip(),
        "headstamp_consistency_status": str(validate_payload.get("headstamp_consistency_status", "")).strip(),
        "headstamp_consistency_mode": str(validate_payload.get("headstamp_consistency_mode", "")).strip(),
        "headstamp_consistency_reason": str(validate_payload.get("headstamp_consistency_reason", "")).strip(),
        "headstamp_correction_from": str(validate_payload.get("headstamp_correction_from", "")).strip(),
        "headstamp_correction_to": str(validate_payload.get("headstamp_correction_to", "")).strip(),
        "headstamp_correction_evidence_ref": str(
            validate_payload.get("headstamp_correction_evidence_ref", "")
        ).strip(),
        "quoted_identity_context_detected": bool(
            quoted_identity_context_guard.get("quoted_identity_context_detected", False)
        ),
        "quoted_identity_context_line_count": int(quoted_identity_context_guard.get("quoted_identity_context_line_count", 0) or 0),
        "quoted_identity_context_ids": list(quoted_identity_context_guard.get("quoted_identity_context_ids") or []),
        "quoted_identity_context_foreign_detected": bool(
            quoted_identity_context_guard.get("quoted_identity_context_foreign_detected", False)
        ),
        "quoted_identity_context_foreign_ids": list(
            quoted_identity_context_guard.get("quoted_identity_context_foreign_ids") or []
        ),
        "quoted_identity_context_refs": list(quoted_identity_context_guard.get("quoted_identity_context_refs") or []),
        "quoted_identity_context_guard_applied": bool(
            quoted_identity_context_guard.get("quoted_identity_context_guard_applied", False)
        ),
        "quoted_identity_context_guard_reason": str(
            quoted_identity_context_guard.get("quoted_identity_context_guard_reason", "")
        ).strip(),
        "quoted_identity_context_guard_status": str(
            quoted_identity_context_guard.get("quoted_identity_context_guard_status", "")
        ).strip(),
        "quoted_identity_context_binding_effect": str(
            quoted_identity_context_guard.get("quoted_identity_context_binding_effect", "")
        ).strip(),
    }, effective_bound_identity_id=actor_bound_identity or str(args.identity_id or "").strip(), quoted_guard=quoted_identity_context_guard, actor_id_override=actor_id_effective, session_id_override=session_id_effective)

    allow_reply_emit = (
        proc.returncode == 0
        and str(payload.get("send_time_gate_status", "")).strip().upper() == "PASS_REQUIRED"
        and str(payload.get("final_emit_contract_status", "")).strip().upper() == "PASS_REQUIRED"
    )
    payload["reply_emit_allowed"] = allow_reply_emit
    payload.update(
        build_sender_consumption_projection(
            out_reply_file=payload.get("out_reply_file", ""),
            reply_transport_ref=payload.get("reply_transport_ref", ""),
            reply_emit_allowed=allow_reply_emit,
        )
    )
    machine_verification_payload = build_operator_machine_verification_payload(
        payload,
        verification_source=CONTROLLED_RUNTIME_MACHINE_VERIFICATION_SOURCE,
        current_surface_native_machine_attested=bool(
            payload.get("current_surface_native_machine_attested", False)
        ),
    )
    operator_envelope_lines = render_operator_headstamp_lines(
        ctx,
        disclosure_level=disclosure_level,
        work_layer=work_layer,
        source_layer=source_layer,
        machine_payload=machine_verification_payload,
    )
    visible_reply = render_visible_reply_with_operator_envelope(
        reply_text=composed_reply,
        operator_envelope_lines=operator_envelope_lines,
    )
    payload["machine_verification"] = machine_verification_payload
    payload["machine_verification_line"] = operator_envelope_lines[1] if len(operator_envelope_lines) > 1 else ""
    payload["display_headstamp_line"] = operator_envelope_lines[0] if operator_envelope_lines else ""
    payload["operator_envelope_lines"] = operator_envelope_lines
    payload["operator_envelope"] = "\n".join(operator_envelope_lines)
    payload["visible_reply"] = visible_reply
    payload["visible_reply_preview"] = visible_reply.splitlines()[:3]

    out_json = str(args.out_json or "").strip()
    if out_json:
        out_json_path = Path(out_json).expanduser().resolve()
        out_json_path.parent.mkdir(parents=True, exist_ok=True)
        out_json_path.write_text(
            json.dumps(inject_legacy_error_fields(payload), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    _emit(
        payload,
        json_only=args.json_only,
        visible_reply=visible_reply,
        allow_reply_emit=allow_reply_emit,
    )
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
