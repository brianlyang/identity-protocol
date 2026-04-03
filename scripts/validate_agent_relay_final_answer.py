#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_relay_final_answer_common import (
    DEFAULT_TEMPLATE,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    extract_source_text,
    first_nonempty_line,
    load_json,
    normalize_source_text,
    parse_identity_context_fields,
    preview,
    resolve_path,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate governed outer-agent relay receipts for identity final answers.")
    ap.add_argument("--receipt", required=True, help="relay receipt json path")
    ap.add_argument("--template", default=DEFAULT_TEMPLATE, help="contract template path")
    ap.add_argument("--source-artifact", default="", help="optional source artifact override path")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    template_path = resolve_path(args.template, repo_root=repo_root)
    receipt_path = resolve_path(args.receipt, repo_root=repo_root)
    try:
        template = load_json(template_path)
        receipt = load_json(receipt_path)
    except Exception as exc:
        payload = {
            "agent_relay_final_answer_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-RELAY-001",
            "stale_reasons": [f"receipt_or_template_invalid:{exc}"],
            "template_path": str(template_path),
            "receipt_path": str(receipt_path),
        }
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    error_codes = template.get("error_codes") if isinstance(template.get("error_codes"), dict) else {}
    err_missing = str(error_codes.get("missing_or_invalid_receipt", "IP-RELAY-001")).strip()
    err_source = str(error_codes.get("source_artifact_unavailable", "IP-RELAY-002")).strip()
    err_exact = str(error_codes.get("exact_relay_mismatch", "IP-RELAY-003")).strip()
    err_summary = str(error_codes.get("summary_impersonates_governed_output", "IP-RELAY-004")).strip()
    err_mode = str(error_codes.get("invalid_relay_mode", "IP-RELAY-005")).strip()
    err_identity = str(error_codes.get("source_identity_mismatch", "IP-RELAY-006")).strip()
    err_ts = str(error_codes.get("source_snapshot_ts_mismatch", "IP-RELAY-007")).strip()

    relay_mode = str(receipt.get("relay_mode", "")).strip()
    relay_surface = str(receipt.get("relay_surface", "")).strip()
    target_identity_id = str(receipt.get("target_identity_id", "")).strip()
    relay_text = normalize_source_text(str(receipt.get("relay_text", "")))
    delivery_authority = str(receipt.get("delivery_authority", "")).strip()
    source_snapshot_ts = str(receipt.get("source_snapshot_ts", "")).strip()

    mode_doc = template.get("relay_modes") if isinstance(template.get("relay_modes"), dict) else {}
    mode_cfg = mode_doc.get(relay_mode) if isinstance(mode_doc.get(relay_mode), dict) else {}
    common_required = [str(x).strip() for x in (template.get("required_common_fields") or []) if str(x).strip()]
    required_fields = [str(x).strip() for x in (mode_cfg.get("required_fields") or common_required) if str(x).strip()]
    missing_fields = [field for field in required_fields if not str(receipt.get(field, "")).strip()]
    stale_reasons: list[str] = []
    error_code = ""

    if str(receipt.get("schema_version", "")).strip() != str(template.get("receipt_schema_version", "")).strip():
        missing_fields.append("schema_version")
    if relay_surface != str(template.get("surface_id", "")).strip():
        missing_fields.append("relay_surface")
    if not mode_cfg:
        stale_reasons.append(f"relay_mode_invalid:{relay_mode or 'missing'}")
        error_code = err_mode

    source_artifact_raw = str(args.source_artifact or receipt.get("source_artifact", "")).strip()
    source_artifact_path = resolve_path(source_artifact_raw, repo_root=repo_root) if source_artifact_raw else Path()
    source_text = ""
    source_identity_id = ""
    source_generated_at = ""
    source_kind = ""
    if source_artifact_raw:
        source_text, source_identity_id, source_generated_at, source_kind = extract_source_text(
            source_artifact_path,
            target_identity_id=target_identity_id,
        )
        if not source_text:
            stale_reasons.append("source_artifact_unreadable_or_empty")
            if not error_code:
                error_code = err_source
    else:
        stale_reasons.append("source_artifact_missing")
        if not error_code:
            error_code = err_missing

    if missing_fields:
        stale_reasons.append("missing_required_fields:" + ",".join(sorted(set(missing_fields))))
        if not error_code:
            error_code = err_missing

    detected_identity = source_identity_id
    if not detected_identity and source_text:
        detected_identity = parse_identity_context_fields(first_nonempty_line(source_text)).get("identity_id", "")
    if target_identity_id and detected_identity and target_identity_id != detected_identity:
        stale_reasons.append(f"source_identity_mismatch:{target_identity_id}!={detected_identity}")
        if not error_code:
            error_code = err_identity

    if source_generated_at and source_snapshot_ts and source_generated_at != source_snapshot_ts:
        stale_reasons.append(f"source_snapshot_ts_mismatch:{source_snapshot_ts}!={source_generated_at}")
        if not error_code:
            error_code = err_ts

    forbidden_prefixes = [
        str(x).strip() for x in (template.get("summary_forbidden_prefixes") or []) if str(x).strip()
    ]
    allowed_source_artifact_kinds = {
        str(x).strip() for x in (template.get("allowed_source_artifact_kinds") or []) if str(x).strip()
    }
    if source_kind and allowed_source_artifact_kinds and source_kind not in allowed_source_artifact_kinds:
        stale_reasons.append(f"source_artifact_kind_not_allowed:{source_kind}")
        if not error_code:
            error_code = err_source
    first_line = first_nonempty_line(relay_text)
    relay_output_classification = str(mode_cfg.get("delivery_authority", "")).strip() if mode_cfg else ""
    if relay_mode == "exact":
        if delivery_authority != str(mode_cfg.get("delivery_authority", "")).strip():
            stale_reasons.append("exact_delivery_authority_invalid")
            if not error_code:
                error_code = err_exact
        if source_text and relay_text != source_text:
            stale_reasons.append("exact_relay_text_mismatch")
            if not error_code:
                error_code = err_exact
    elif relay_mode == "summary":
        if delivery_authority != str(mode_cfg.get("delivery_authority", "")).strip():
            stale_reasons.append("summary_delivery_authority_invalid")
            if not error_code:
                error_code = err_summary
        if any(first_line.startswith(prefix) for prefix in forbidden_prefixes):
            stale_reasons.append("summary_impersonates_governed_output")
            if not error_code:
                error_code = err_summary
    elif not error_code:
        error_code = err_mode

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload = {
        "agent_relay_final_answer_status": status,
        "error_code": error_code,
        "template_path": str(template_path),
        "receipt_path": str(receipt_path),
        "relay_surface": relay_surface,
        "relay_mode": relay_mode,
        "target_identity_id": target_identity_id,
        "question_tag": str(receipt.get("question_tag", "")).strip(),
        "relay_output_classification": relay_output_classification,
        "delivery_authority": delivery_authority,
        "source_artifact": str(source_artifact_path) if source_artifact_raw else "",
        "source_artifact_exists": bool(source_artifact_raw and source_artifact_path.exists()),
        "source_artifact_kind": source_kind,
        "source_identity_id": detected_identity,
        "source_snapshot_ts": source_snapshot_ts,
        "source_artifact_generated_at": source_generated_at,
        "relay_text_preview": preview(relay_text),
        "source_text_preview": preview(source_text),
        "summary_forbidden_prefixes": forbidden_prefixes,
        "stale_reasons": stale_reasons,
    }
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
