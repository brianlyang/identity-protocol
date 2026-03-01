#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from response_stamp_common import (
    ALLOWED_SOURCE_LAYERS,
    ALLOWED_WORK_LAYERS,
    blocker_receipt,
    infer_disclosure_level_from_stamp_fields,
    parse_identity_context_stamp,
    resolve_layer_intent,
    resolve_stamp_context,
)
from tool_vendor_governance_common import contract_required, load_json

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_TUPLE_MISMATCH = "IP-ASB-CTX-001"
ERR_REPLY_TUPLE_MISSING = "IP-ASB-CTX-002"
ERR_DUAL_CATALOG_AMBIGUITY = "IP-ASB-CTX-003"

STRICT_OPERATIONS = {"activate", "update", "mutation", "readiness", "e2e", "validate"}


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "execution_reply_identity_coherence_contract_v1",
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


def _lane_ambiguity(expected_source: str, reply_source: str) -> bool:
    lanes = {"project", "global"}
    return expected_source in lanes and reply_source in lanes and expected_source != reply_source


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate execution command tuple vs reply identity-context tuple coherence.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--reply-log", default="")
    ap.add_argument("--reply-file", default="")
    ap.add_argument("--reply-text", default="")
    ap.add_argument("--stamp-line", default="")
    ap.add_argument("--stamp-json", default="")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--layer-intent-text", default="", help="optional natural-language intent text for layer resolution")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--enforce-coherence-gate", action="store_true")
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
    force_required = bool(args.force_check or args.enforce_coherence_gate)
    if not force_required and not contract_required(contract):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "required_contract": False,
            "coherence_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "coherence_decision": "SKIPPED",
            "command_catalog_ref": "",
            "resolved_catalog_ref": "",
            "reply_catalog_ref": "",
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
    elif args.stamp_line.strip():
        reply_samples = [args.stamp_line]
        evidence_ref = "inline:stamp_line"
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
        line = str(doc.get("external_stamp", "")).strip()
        reply_samples = [line] if line else []
        evidence_ref = str(p)

    first_line = ""
    if reply_samples:
        first_line = _first_nonempty_line(reply_samples[0])
    parsed = parse_identity_context_stamp(first_line)
    layer_intent = resolve_layer_intent(
        explicit_work_layer=str(args.expected_work_layer or "").strip()
        or str(stamp_doc.get("resolved_work_layer", "")).strip(),
        explicit_source_layer=str(args.expected_source_layer or "").strip()
        or str(stamp_doc.get("resolved_source_layer", "")).strip(),
        intent_text=str(args.layer_intent_text or "").strip()
        or str(stamp_doc.get("layer_intent_text", "")).strip(),
        default_work_layer="protocol",
        default_source_layer=ctx.source_domain,
    )
    expected_work_layer = str(layer_intent.get("resolved_work_layer", "")).strip().lower() or "protocol"
    expected_source_layer = str(layer_intent.get("resolved_source_layer", "")).strip().lower() or ctx.source_domain
    if expected_work_layer not in ALLOWED_WORK_LAYERS:
        expected_work_layer = "protocol"
    if expected_source_layer not in ALLOWED_SOURCE_LAYERS:
        expected_source_layer = ctx.source_domain if ctx.source_domain in ALLOWED_SOURCE_LAYERS else "auto"

    strict_operation = args.operation in STRICT_OPERATIONS
    lock_boundary_enforced = bool(args.enforce_coherence_gate and strict_operation)
    strict_format_enforced = strict_operation

    mismatch_fields: list[str] = []
    stale_reasons: list[str] = []
    error_code = ""
    coherence_decision = "PASS"

    if not first_line:
        coherence_decision = "MISSING_REPLY_TUPLE"
        stale_reasons.append("reply_tuple_evidence_missing")
        error_code = ERR_REPLY_TUPLE_MISSING
    elif not parsed:
        coherence_decision = "MISSING_REPLY_TUPLE"
        stale_reasons.append("reply_first_line_not_identity_context")
        error_code = ERR_REPLY_TUPLE_MISSING
    else:
        reply_source_layer = str(parsed.get("source_layer", "")).strip()
        reply_work_layer = str(parsed.get("work_layer", "")).strip()
        disclosure_level = infer_disclosure_level_from_stamp_fields(parsed)
        require_ref_tuple = disclosure_level in {"standard", "verbose", "audit"}
        checks = {
            "identity_id": (str(parsed.get("identity_id", "")).strip(), ctx.identity_id),
            "actor_id": (str(parsed.get("actor_id", "")).strip(), ctx.actor_id),
            "scope": (str(parsed.get("scope", "")).strip(), ctx.resolved_scope),
            "source": (str(parsed.get("source", "")).strip(), ctx.source_domain),
            "source_layer": (reply_source_layer, expected_source_layer),
            "work_layer": (reply_work_layer, expected_work_layer),
        }
        if require_ref_tuple or str(parsed.get("catalog_ref", "")).strip():
            checks["catalog_ref"] = (str(parsed.get("catalog_ref", "")).strip(), ctx.catalog_ref)
        if require_ref_tuple or str(parsed.get("pack_ref", "")).strip():
            checks["pack_ref"] = (str(parsed.get("pack_ref", "")).strip(), ctx.pack_ref)
        for field, (actual, expected) in checks.items():
            if actual != expected:
                mismatch_fields.append(field)
        required_tuple_fields = ["identity_id", "actor_id", "source", "work_layer", "source_layer"]
        if require_ref_tuple:
            required_tuple_fields.extend(["catalog_ref", "pack_ref"])
        missing_tuple_fields = [field for field in required_tuple_fields if not str(parsed.get(field, "")).strip()]
        if not bool(parsed.get("_has_layer_context", False)):
            stale_reasons.append("layer_context_tail_missing")
            if "work_layer" not in missing_tuple_fields:
                missing_tuple_fields.append("work_layer")
            if "source_layer" not in missing_tuple_fields:
                missing_tuple_fields.append("source_layer")
        if reply_work_layer and reply_work_layer not in ALLOWED_WORK_LAYERS:
            stale_reasons.append("work_layer_invalid")
            if "work_layer" not in mismatch_fields:
                mismatch_fields.append("work_layer")
        if reply_source_layer and reply_source_layer not in ALLOWED_SOURCE_LAYERS:
            stale_reasons.append("source_layer_invalid")
            if "source_layer" not in mismatch_fields:
                mismatch_fields.append("source_layer")
        if mismatch_fields:
            coherence_decision = "MISMATCH"
            stale_reasons.append("tuple_mismatch:" + ",".join(mismatch_fields))
            if missing_tuple_fields:
                stale_reasons.append("reply_tuple_fields_missing:" + ",".join(missing_tuple_fields))
                error_code = ERR_REPLY_TUPLE_MISSING
            elif _lane_ambiguity(ctx.source_domain, str(parsed.get("source", "")).strip()):
                error_code = ERR_DUAL_CATALOG_AMBIGUITY
            else:
                error_code = ERR_TUPLE_MISMATCH

    reply_lock_state = str(parsed.get("lock", "")).strip() if parsed else ""
    if not error_code and lock_boundary_enforced:
        if ctx.lock_state != "LOCK_MATCH":
            coherence_decision = "LOCK_MISMATCH"
            stale_reasons.append("actor_binding_lock_not_match")
            error_code = ERR_DUAL_CATALOG_AMBIGUITY
        elif reply_lock_state and reply_lock_state != "LOCK_MATCH":
            coherence_decision = "LOCK_MISMATCH"
            stale_reasons.append("reply_tuple_lock_not_match")
            error_code = ERR_DUAL_CATALOG_AMBIGUITY

    receipt_path = (
        Path(args.blocker_receipt_out).expanduser().resolve()
        if args.blocker_receipt_out.strip()
        else Path(f"/tmp/identity-execution-reply-coherence-blocker-receipt-{args.identity_id}.json").resolve()
    )

    required_contract = bool(force_required or contract_required(contract))
    strict_fail = bool(error_code) and strict_operation and required_contract
    warn_non_blocking = bool(error_code) and not strict_operation

    coherence_status = STATUS_PASS_REQUIRED
    if strict_fail:
        coherence_status = STATUS_FAIL_REQUIRED
    elif warn_non_blocking:
        coherence_status = STATUS_WARN_NON_BLOCKING

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "layer_intent_resolution_status": STATUS_PASS_REQUIRED if not error_code else STATUS_FAIL_REQUIRED,
        "resolved_work_layer": expected_work_layer,
        "resolved_source_layer": expected_source_layer,
        "intent_confidence": layer_intent.get("intent_confidence", 0.0),
        "intent_source": layer_intent.get("intent_source", "default_fallback"),
        "fallback_reason": layer_intent.get("fallback_reason", ""),
        "coherence_status": coherence_status,
        "error_code": error_code,
        "coherence_decision": coherence_decision,
        "strict_operation": strict_operation,
        "strict_format_enforced": strict_format_enforced,
        "lock_boundary_enforced": lock_boundary_enforced,
        "expected_lock_state": ctx.lock_state,
        "reply_lock_state": reply_lock_state,
        "command_identity_id": args.identity_id,
        "resolved_identity_id": ctx.identity_id,
        "reply_identity_id": str(parsed.get("identity_id", "")).strip() if parsed else "",
        "command_actor_id": str(args.actor_id).strip() or ctx.actor_id,
        "resolved_actor_id": ctx.actor_id,
        "reply_actor_id": str(parsed.get("actor_id", "")).strip() if parsed else "",
        "command_catalog_ref": ctx.catalog_ref,
        "resolved_catalog_ref": ctx.catalog_ref,
        "reply_catalog_ref": str(parsed.get("catalog_ref", "")).strip() if parsed else "",
        "command_pack_ref": ctx.pack_ref,
        "resolved_pack_ref": ctx.pack_ref,
        "reply_pack_ref": str(parsed.get("pack_ref", "")).strip() if parsed else "",
        "command_source": ctx.source_domain,
        "reply_source": str(parsed.get("source", "")).strip() if parsed else "",
        "command_work_layer": expected_work_layer,
        "reply_work_layer": str(parsed.get("work_layer", "")).strip() if parsed else "",
        "command_source_layer": expected_source_layer,
        "reply_source_layer": str(parsed.get("source_layer", "")).strip() if parsed else "",
        "reply_layer_context_present": bool(parsed.get("_has_layer_context", False)) if parsed else False,
        "reply_evidence_ref": evidence_ref,
        "reply_first_line": first_line,
        "mismatch_fields": mismatch_fields,
        "blocker_receipt_path": str(receipt_path) if strict_fail else "",
        "stale_reasons": stale_reasons,
    }

    if strict_fail:
        receipt = blocker_receipt(
            error_code=error_code,
            expected_identity_id=ctx.identity_id,
            actual_identity_id=str(parsed.get("identity_id", "")).strip() or "MISSING_STAMP",
            source_domain=str(parsed.get("source", "")).strip() or ctx.source_domain,
            resolver_ref=f"{catalog_path.parent}/session/actors",
            next_action="re_resolve_identity_lane_then_retry",
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
    return 1 if strict_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
