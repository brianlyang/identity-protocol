#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from actor_session_common import load_actor_binding
from response_stamp_common import (
    ALLOWED_SOURCE_LAYERS,
    ALLOWED_WORK_LAYERS,
    blocker_receipt,
    parse_identity_context_stamp,
    resolve_layer_intent,
    resolve_stamp_context,
)
from tool_vendor_governance_common import contract_required, load_json

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REPLY_FIRST_LINE = "IP-ASB-STAMP-SESSION-001"
ERR_INVALID_EXPECTED_SOURCE_LAYER = "IP-SOURCE-LAYER-001"
ERR_RUNTIME_BINDING_MISMATCH = "IP-ASB-STAMP-SESSION-005"
STRICT_LOCK_OPERATIONS = {"activate", "update", "mutation", "readiness", "e2e", "validate"}


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    # Reuse response stamp contract, while allowing explicit first-line contract key.
    for key in (
        "reply_identity_context_first_line_contract_v1",
        "identity_response_stamp_contract",
        "response_stamp_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _resolve_pack_and_task(catalog_path: Path, identity_id: str) -> tuple[Path, Path]:
    import yaml

    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_raw = str((row or {}).get("pack_path", "")).strip()
    if not pack_raw:
        raise FileNotFoundError(f"pack_path missing for identity: {identity_id}")
    pack = Path(pack_raw).expanduser().resolve()
    if not pack.exists():
        raise FileNotFoundError(f"pack_path not found: {pack}")
    task = pack / "CURRENT_TASK.json"
    if not task.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found: {task}")
    return pack, task


def _message_to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                elif isinstance(item.get("content"), str):
                    parts.append(str(item.get("content")))
        return "\n".join([x for x in parts if x]).strip()
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return str(value.get("text"))
        if isinstance(value.get("content"), str):
            return str(value.get("content"))
    return ""


def _extract_reply_samples(reply_log_path: Path) -> list[str]:
    text = reply_log_path.read_text(encoding="utf-8", errors="ignore")
    suffix = reply_log_path.suffix.lower()

    if suffix == ".jsonl":
        out: list[str] = []
        for raw in text.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except Exception:
                continue
            if not isinstance(row, dict):
                continue
            role = str(row.get("role", "")).strip().lower()
            if role and role not in {"assistant", "ai", "model"}:
                continue
            msg = _message_to_text(row.get("content"))
            if not msg:
                msg = _message_to_text(row.get("message"))
            if not msg:
                msg = _message_to_text(row.get("output"))
            if msg:
                out.append(msg)
        return out

    if suffix == ".json":
        try:
            doc = json.loads(text)
        except Exception:
            doc = None
        out: list[str] = []
        if isinstance(doc, dict):
            replies = doc.get("replies")
            if isinstance(replies, list):
                for item in replies:
                    msg = _message_to_text(item)
                    if msg:
                        out.append(msg)
            messages = doc.get("messages")
            if isinstance(messages, list):
                for row in messages:
                    if not isinstance(row, dict):
                        continue
                    role = str(row.get("role", "")).strip().lower()
                    if role and role not in {"assistant", "ai", "model"}:
                        continue
                    msg = _message_to_text(row.get("content"))
                    if msg:
                        out.append(msg)
            if not out:
                msg = _message_to_text(doc.get("content"))
                if msg:
                    out.append(msg)
        elif isinstance(doc, list):
            for item in doc:
                msg = _message_to_text(item)
                if msg:
                    out.append(msg)
        return out

    chunks = [x.strip() for x in text.split("\n---\n") if x.strip()]
    if chunks:
        return chunks
    return [x.strip() for x in text.splitlines() if x.strip()]


def _first_nonempty_line(text: str) -> str:
    for line in str(text or "").splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _emit_blocker(receipt_path: Path, payload: dict[str, Any]) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate that user-visible assistant replies start with Identity-Context first line.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--reply-log", default="", help="assistant reply evidence (.json/.jsonl/.txt)")
    ap.add_argument("--reply-file", default="", help="single reply text file")
    ap.add_argument("--reply-text", default="", help="inline single reply text")
    ap.add_argument("--stamp-json", default="", help="optional rendered stamp payload json (external_stamp field)")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--layer-intent-text", default="", help="optional natural-language intent text for layer auto-resolution")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--enforce-first-line-gate", action="store_true")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "mutation", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
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

    try:
        _, task_path = _resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    force_required = bool(args.force_check or args.enforce_first_line_gate)
    if not force_required and not contract_required(contract):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "required_contract": False,
            "reply_first_line_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "reply_first_line_missing_count": 0,
            "reply_first_line_missing_refs": [],
            "reply_sample_count": 0,
            "blocker_receipt_path": "",
            "stale_reasons": ["contract_not_required"],
        }
        _emit(payload, json_only=args.json_only)
        return 0

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

    reply_samples: list[str] = []
    evidence_ref = ""
    stamp_doc: dict[str, Any] = {}
    if args.reply_log.strip():
        p = Path(args.reply_log).expanduser().resolve()
        if not p.exists():
            print(f"[FAIL] reply log file not found: {p}")
            return 1
        reply_samples = _extract_reply_samples(p)
        evidence_ref = str(p)
    elif args.reply_file.strip():
        p = Path(args.reply_file).expanduser().resolve()
        if not p.exists():
            print(f"[FAIL] reply file not found: {p}")
            return 1
        reply_samples = [p.read_text(encoding="utf-8", errors="ignore")]
        evidence_ref = str(p)
    elif args.reply_text.strip():
        reply_samples = [args.reply_text]
        evidence_ref = "inline:reply_text"
    elif args.stamp_json.strip():
        p = Path(args.stamp_json).expanduser().resolve()
        if not p.exists():
            print(f"[FAIL] stamp json not found: {p}")
            return 1
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[FAIL] invalid stamp json: {p} ({exc})")
            return 1
        if not isinstance(doc, dict):
            print(f"[FAIL] stamp json payload must be object: {p}")
            return 1
        stamp_doc = doc
        stamp_line = str(doc.get("external_stamp", "")).strip()
        reply_samples = [stamp_line] if stamp_line else []
        evidence_ref = str(p)

    first_lines = [_first_nonempty_line(x) for x in reply_samples]
    first_lines = [x for x in first_lines if x]

    missing_refs: list[str] = []
    for idx, line in enumerate(first_lines, start=1):
        if not line.startswith("Identity-Context:"):
            missing_refs.append(f"sample:{idx}")

    stale_reasons: list[str] = []
    error_code = ""

    if args.enforce_first_line_gate and len(first_lines) == 0:
        stale_reasons.append("reply_evidence_missing")
        error_code = ERR_REPLY_FIRST_LINE

    if len(missing_refs) > 0:
        stale_reasons.append("reply_first_line_identity_context_missing")
        if not error_code:
            error_code = ERR_REPLY_FIRST_LINE

    parsed_first: dict[str, Any] = parse_identity_context_stamp(first_lines[0]) if first_lines else {}
    strict_format_enforced = args.operation in STRICT_LOCK_OPERATIONS
    expected_source_layer_input = str(args.expected_source_layer or "").strip().lower()
    expected_source_layer_input_invalid = bool(
        expected_source_layer_input and expected_source_layer_input not in ALLOWED_SOURCE_LAYERS
    )
    expected_source_layer_validation_status = STATUS_PASS_REQUIRED
    expected_source_layer_validation_error_code = ""
    source_layer_downgrade_applied = False
    if expected_source_layer_input_invalid:
        if strict_format_enforced:
            stale_reasons.append("expected_source_layer_invalid_input")
            if not error_code:
                error_code = ERR_INVALID_EXPECTED_SOURCE_LAYER
            expected_source_layer_validation_status = STATUS_FAIL_REQUIRED
            expected_source_layer_validation_error_code = ERR_INVALID_EXPECTED_SOURCE_LAYER
        else:
            expected_source_layer_validation_status = "WARN_NON_BLOCKING"
            expected_source_layer_validation_error_code = ERR_INVALID_EXPECTED_SOURCE_LAYER
            source_layer_downgrade_applied = True

    expected_work_input = str(args.expected_work_layer or "").strip()
    expected_source_input = str(args.expected_source_layer or "").strip()
    intent_text_input = str(args.layer_intent_text or "").strip() or str(stamp_doc.get("layer_intent_text", "")).strip()
    seed_work = expected_work_input
    if not seed_work and not intent_text_input:
        seed_work = str(stamp_doc.get("resolved_work_layer", "")).strip()
    seed_source = expected_source_input
    if not seed_source and not intent_text_input:
        seed_source = str(stamp_doc.get("resolved_source_layer", "")).strip()

    layer_intent = resolve_layer_intent(
        explicit_work_layer=seed_work,
        explicit_source_layer=seed_source,
        intent_text=intent_text_input,
        default_work_layer="instance",
        default_source_layer=ctx.source_domain,
    )
    expected_work_layer = str(layer_intent.get("resolved_work_layer", "")).strip().lower() or "instance"
    expected_source_layer = str(layer_intent.get("resolved_source_layer", "")).strip().lower() or ctx.source_domain
    if expected_work_layer not in ALLOWED_WORK_LAYERS:
        expected_work_layer = "instance"
    if expected_source_layer not in ALLOWED_SOURCE_LAYERS:
        expected_source_layer = ctx.source_domain if ctx.source_domain in ALLOWED_SOURCE_LAYERS else "auto"
    if expected_source_layer_input_invalid and expected_source_layer != expected_source_layer_input:
        source_layer_downgrade_applied = True

    # Optional identity mismatch signal if first line exists and parsable.
    if not error_code and first_lines:
        actual_identity = str(parsed_first.get("identity_id", "")).strip()
        if actual_identity and actual_identity != ctx.identity_id:
            stale_reasons.append("reply_first_line_identity_mismatch")
            error_code = ERR_REPLY_FIRST_LINE

    protocol_triggered = bool(layer_intent.get("protocol_triggered", False))
    protocol_trigger_reasons = list(layer_intent.get("protocol_trigger_reasons") or [])
    has_layer_context = bool(parsed_first.get("_has_layer_context", False)) if first_lines else False
    parsed_work_layer = str(parsed_first.get("work_layer", "")).strip() if parsed_first else ""
    parsed_source_layer = str(parsed_first.get("source_layer", "")).strip() if parsed_first else ""
    if not error_code and first_lines:
        if not has_layer_context:
            if strict_format_enforced:
                stale_reasons.append("reply_first_line_layer_context_tail_missing")
                error_code = ERR_REPLY_FIRST_LINE
            else:
                stale_reasons.append("reply_first_line_layer_context_tail_missing_non_blocking")
        else:
            if parsed_work_layer not in ALLOWED_WORK_LAYERS:
                if strict_format_enforced:
                    stale_reasons.append("reply_first_line_work_layer_invalid")
                    error_code = ERR_REPLY_FIRST_LINE
                else:
                    stale_reasons.append("reply_first_line_work_layer_invalid_non_blocking")
            elif parsed_work_layer != expected_work_layer:
                if strict_format_enforced:
                    stale_reasons.append("reply_first_line_work_layer_mismatch")
                    error_code = ERR_REPLY_FIRST_LINE
                else:
                    stale_reasons.append("reply_first_line_work_layer_mismatch_non_blocking")
            if parsed_source_layer not in ALLOWED_SOURCE_LAYERS:
                if strict_format_enforced and not error_code:
                    stale_reasons.append("reply_first_line_source_layer_invalid")
                    error_code = ERR_REPLY_FIRST_LINE
                elif not strict_format_enforced:
                    stale_reasons.append("reply_first_line_source_layer_invalid_non_blocking")
            elif parsed_source_layer != expected_source_layer:
                if strict_format_enforced and not error_code:
                    stale_reasons.append("reply_first_line_source_layer_mismatch")
                    error_code = ERR_REPLY_FIRST_LINE
                elif not strict_format_enforced:
                    stale_reasons.append("reply_first_line_source_layer_mismatch_non_blocking")

    if expected_work_layer == "protocol" and not protocol_triggered:
        stale_reasons.append("protocol_layer_without_trigger")
        if strict_format_enforced and not error_code:
            error_code = ERR_REPLY_FIRST_LINE

    actor_id_effective = str(ctx.actor_id or "").strip()
    actor_bound_identity = ""
    actor_binding = load_actor_binding(catalog_path, actor_id_effective)
    actor_bound_identity = str(actor_binding.get("identity_id", "")).strip()
    if strict_format_enforced and actor_bound_identity and actor_bound_identity != ctx.identity_id and not error_code:
        stale_reasons.append("actor_bound_identity_mismatch")
        error_code = ERR_RUNTIME_BINDING_MISMATCH

    lock_boundary_enforced = bool(args.enforce_first_line_gate and args.operation in STRICT_LOCK_OPERATIONS)
    parsed_lock_state = ""
    parsed_actor_id = ""
    if not error_code and first_lines:
        parsed_lock_state = str(parsed_first.get("lock", "")).strip()
        parsed_actor_id = str(parsed_first.get("actor_id", "")).strip()
    if strict_format_enforced and parsed_actor_id and parsed_actor_id != actor_id_effective and not error_code:
        stale_reasons.append("reply_first_line_actor_mismatch")
        error_code = ERR_RUNTIME_BINDING_MISMATCH
    if not error_code and lock_boundary_enforced:
        if actor_bound_identity and ctx.lock_state != "LOCK_MATCH":
            stale_reasons.append("actor_binding_lock_not_match")
            error_code = ERR_RUNTIME_BINDING_MISMATCH
        elif parsed_lock_state and parsed_lock_state != "LOCK_MATCH":
            stale_reasons.append("reply_first_line_lock_not_match")
            error_code = ERR_REPLY_FIRST_LINE

    ok = error_code == ""
    receipt_path = (
        Path(args.blocker_receipt_out).expanduser().resolve()
        if args.blocker_receipt_out.strip()
        else Path(f"/tmp/identity-reply-first-line-blocker-receipt-{args.identity_id}.json").resolve()
    )

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": bool(force_required or contract_required(contract)),
        "reply_first_line_status": STATUS_PASS_REQUIRED if ok else STATUS_FAIL_REQUIRED,
        "error_code": error_code,
        "layer_intent_resolution_status": STATUS_PASS_REQUIRED if not error_code else STATUS_FAIL_REQUIRED,
        "resolved_work_layer": expected_work_layer,
        "resolved_source_layer": expected_source_layer,
        "intent_confidence": layer_intent.get("intent_confidence", 0.0),
        "intent_source": layer_intent.get("intent_source", "default_fallback"),
        "fallback_reason": layer_intent.get("fallback_reason", ""),
        "protocol_triggered": protocol_triggered,
        "protocol_trigger_reasons": protocol_trigger_reasons,
        "protocol_trigger_confidence": float(layer_intent.get("protocol_trigger_confidence", 0.0) or 0.0),
        "layer_context_enforced": strict_format_enforced,
        "layer_context_present": has_layer_context,
        "expected_work_layer": expected_work_layer,
        "reply_first_line_work_layer": parsed_work_layer,
        "expected_source_layer_input": expected_source_layer_input,
        "expected_source_layer": expected_source_layer,
        "expected_source_layer_effective": expected_source_layer,
        "expected_source_layer_validation_status": expected_source_layer_validation_status,
        "expected_source_layer_validation_error_code": expected_source_layer_validation_error_code,
        "source_layer_downgrade_applied": source_layer_downgrade_applied,
        "reply_first_line_source_layer": parsed_source_layer,
        "lock_boundary_enforced": lock_boundary_enforced,
        "context_lock_state": ctx.lock_state,
        "expected_actor_id": actor_id_effective,
        "reply_first_line_actor_id": parsed_actor_id,
        "actor_bound_identity_id": actor_bound_identity,
        "expected_lock_state": ctx.lock_state,
        "reply_first_line_lock_state": parsed_lock_state,
        "reply_first_line_missing_count": len(missing_refs),
        "reply_first_line_missing_refs": missing_refs,
        "reply_sample_count": len(first_lines),
        "reply_evidence_ref": evidence_ref,
        "expected_identity_id": ctx.identity_id,
        "blocker_receipt_path": str(receipt_path) if not ok else "",
        "stale_reasons": stale_reasons,
    }

    if not ok:
        first_line_identity = ""
        if first_lines:
            first_line_identity = str(parsed_first.get("identity_id", "")).strip()
        next_action = "emit_identity_context_first_line_then_retry"
        if error_code == ERR_INVALID_EXPECTED_SOURCE_LAYER:
            next_action = "use_valid_expected_source_layer(project|global|env|auto)_then_retry"
        elif error_code == ERR_RUNTIME_BINDING_MISMATCH:
            next_action = "activate_actor_bound_identity_then_retry"
        receipt = blocker_receipt(
            error_code=error_code or ERR_REPLY_FIRST_LINE,
            expected_identity_id=ctx.identity_id,
            actual_identity_id=first_line_identity or "MISSING_STAMP",
            source_domain=ctx.source_domain,
            resolver_ref=f"{catalog_path.parent}/session/actors",
            next_action=next_action,
        )
        _emit_blocker(receipt_path, receipt)
        payload["blocker_receipt"] = receipt
    else:
        if receipt_path.exists():
            try:
                receipt_path.unlink()
            except Exception:
                pass

    _emit(payload, json_only=args.json_only)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
