#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from agent_relay_final_answer_common import (
    DEFAULT_TEMPLATE,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    build_receipt,
    default_delivery_authority,
    extract_source_text,
    first_nonempty_line,
    load_json,
    normalize_source_text,
    parse_identity_context_fields,
    preview,
    resolve_path,
)


def _build_error_payload(
    *,
    error_code: str,
    stale_reasons: list[str],
    source_artifact_path: Path,
    relay_mode: str,
    target_identity_id: str,
    question_tag: str,
    relay_output_classification: str,
) -> dict[str, object]:
    return {
        "build_status": STATUS_FAIL_REQUIRED,
        "error_code": error_code,
        "stale_reasons": stale_reasons,
        "source_artifact": str(source_artifact_path) if str(source_artifact_path) else "",
        "relay_mode": relay_mode,
        "target_identity_id": target_identity_id,
        "question_tag": question_tag,
        "relay_output_classification": relay_output_classification,
    }


def _run_validator(*, repo_root: Path, receipt_path: Path) -> tuple[int, dict[str, object]]:
    validator_path = repo_root / "scripts" / "validate_agent_relay_final_answer.py"
    completed = subprocess.run(
        [
            str(sys.executable or "python3"),
            str(validator_path),
            "--receipt",
            str(receipt_path),
            "--json-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = str(completed.stdout or "").strip()
    if not stdout:
        payload: dict[str, object] = {
            "agent_relay_final_answer_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-RELAY-001",
            "stale_reasons": ["validator_stdout_empty"],
        }
    else:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = {
                "agent_relay_final_answer_status": STATUS_FAIL_REQUIRED,
                "error_code": "IP-RELAY-001",
                "stale_reasons": ["validator_stdout_not_json"],
                "validator_stdout_preview": stdout[:500],
            }
    payload["validator_exit_code"] = completed.returncode
    payload["validator_stderr"] = str(completed.stderr or "").strip()
    return completed.returncode, payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Build canonical relay receipts for governed outer-agent final-answer delivery.")
    ap.add_argument("--mode", "--relay-mode", dest="relay_mode", default="exact")
    ap.add_argument("--target-identity-id", default="")
    ap.add_argument("--question-tag", required=True)
    ap.add_argument("--source-artifact", required=True)
    ap.add_argument("--summary-text", default="")
    ap.add_argument("--relay-text", default="")
    ap.add_argument("--relay-text-file", default="")
    ap.add_argument("--delivery-authority", default="")
    ap.add_argument("--source-snapshot-ts", default="")
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--output", required=True)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--validation-output", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    template_path = resolve_path(args.template, repo_root=repo_root)
    source_artifact_path = resolve_path(args.source_artifact, repo_root=repo_root)
    output_path = resolve_path(args.output, repo_root=repo_root)
    validation_output_path = resolve_path(args.validation_output, repo_root=repo_root) if args.validation_output else Path()
    try:
        template = load_json(template_path)
    except Exception as exc:
        payload = {
            "build_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-RELAY-001",
            "stale_reasons": [f"template_invalid:{exc}"],
            "template_path": str(template_path),
            "source_artifact": str(source_artifact_path),
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

    relay_mode = str(args.relay_mode or "").strip()
    mode_doc = template.get("relay_modes") if isinstance(template.get("relay_modes"), dict) else {}
    mode_cfg = mode_doc.get(relay_mode) if isinstance(mode_doc.get(relay_mode), dict) else {}
    relay_output_classification = str(mode_cfg.get("delivery_authority", "")).strip() if mode_cfg else ""
    if not mode_cfg:
        payload = _build_error_payload(
            error_code=err_mode,
            stale_reasons=[f"relay_mode_invalid:{relay_mode or 'missing'}"],
            source_artifact_path=source_artifact_path,
            relay_mode=relay_mode,
            target_identity_id=str(args.target_identity_id or "").strip(),
            question_tag=str(args.question_tag or "").strip(),
            relay_output_classification=relay_output_classification,
        )
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    source_text, source_identity_id, source_generated_at, source_kind = extract_source_text(
        source_artifact_path,
        target_identity_id=str(args.target_identity_id or "").strip(),
    )
    if not source_text:
        payload = _build_error_payload(
            error_code=err_source,
            stale_reasons=["source_artifact_unreadable_or_empty"],
            source_artifact_path=source_artifact_path,
            relay_mode=relay_mode,
            target_identity_id=str(args.target_identity_id or "").strip(),
            question_tag=str(args.question_tag or "").strip(),
            relay_output_classification=relay_output_classification,
        )
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    allowed_source_artifact_kinds = {
        str(item).strip() for item in (template.get("allowed_source_artifact_kinds") or []) if str(item).strip()
    }
    if source_kind and allowed_source_artifact_kinds and source_kind not in allowed_source_artifact_kinds:
        payload = _build_error_payload(
            error_code=err_source,
            stale_reasons=[f"source_artifact_kind_not_allowed:{source_kind}"],
            source_artifact_path=source_artifact_path,
            relay_mode=relay_mode,
            target_identity_id=str(args.target_identity_id or "").strip(),
            question_tag=str(args.question_tag or "").strip(),
            relay_output_classification=relay_output_classification,
        )
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    detected_identity = str(source_identity_id or "").strip()
    if not detected_identity:
        detected_identity = parse_identity_context_fields(first_nonempty_line(source_text)).get("identity_id", "")
    target_identity_id = str(args.target_identity_id or "").strip() or detected_identity
    if not target_identity_id:
        payload = _build_error_payload(
            error_code=err_missing,
            stale_reasons=["target_identity_id_missing"],
            source_artifact_path=source_artifact_path,
            relay_mode=relay_mode,
            target_identity_id="",
            question_tag=str(args.question_tag or "").strip(),
            relay_output_classification=relay_output_classification,
        )
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if detected_identity and target_identity_id != detected_identity:
        payload = _build_error_payload(
            error_code=err_identity,
            stale_reasons=[f"source_identity_mismatch:{target_identity_id}!={detected_identity}"],
            source_artifact_path=source_artifact_path,
            relay_mode=relay_mode,
            target_identity_id=target_identity_id,
            question_tag=str(args.question_tag or "").strip(),
            relay_output_classification=relay_output_classification,
        )
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    source_snapshot_ts = str(args.source_snapshot_ts or "").strip() or str(source_generated_at or "").strip()
    if source_generated_at and source_snapshot_ts and source_generated_at != source_snapshot_ts:
        payload = _build_error_payload(
            error_code=err_ts,
            stale_reasons=[f"source_snapshot_ts_mismatch:{source_snapshot_ts}!={source_generated_at}"],
            source_artifact_path=source_artifact_path,
            relay_mode=relay_mode,
            target_identity_id=target_identity_id,
            question_tag=str(args.question_tag or "").strip(),
            relay_output_classification=relay_output_classification,
        )
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    delivery_authority = str(args.delivery_authority or "").strip() or default_delivery_authority(relay_mode)
    expected_delivery_authority = str(mode_cfg.get("delivery_authority", "")).strip()
    if delivery_authority != expected_delivery_authority:
        error_code = err_exact if relay_mode == "exact" else err_summary
        payload = _build_error_payload(
            error_code=error_code,
            stale_reasons=[f"delivery_authority_invalid:{delivery_authority or 'missing'}!={expected_delivery_authority}"],
            source_artifact_path=source_artifact_path,
            relay_mode=relay_mode,
            target_identity_id=target_identity_id,
            question_tag=str(args.question_tag or "").strip(),
            relay_output_classification=relay_output_classification,
        )
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    manual_text = ""
    if args.relay_text_file:
        manual_text = Path(args.relay_text_file).read_text(encoding="utf-8")
    elif relay_mode == "summary" and args.summary_text:
        manual_text = args.summary_text
    elif args.relay_text:
        manual_text = args.relay_text
    manual_text = normalize_source_text(manual_text)

    forbidden_prefixes = [
        str(item).strip() for item in (template.get("summary_forbidden_prefixes") or []) if str(item).strip()
    ]
    if relay_mode == "exact":
        if manual_text and manual_text != source_text:
            payload = _build_error_payload(
                error_code=err_exact,
                stale_reasons=["exact_relay_text_mismatch"],
                source_artifact_path=source_artifact_path,
                relay_mode=relay_mode,
                target_identity_id=target_identity_id,
                question_tag=str(args.question_tag or "").strip(),
                relay_output_classification=relay_output_classification,
            )
            print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
        relay_text = source_text
    else:
        relay_text = manual_text
        if not relay_text:
            payload = _build_error_payload(
                error_code=err_missing,
                stale_reasons=["summary_text_missing"],
                source_artifact_path=source_artifact_path,
                relay_mode=relay_mode,
                target_identity_id=target_identity_id,
                question_tag=str(args.question_tag or "").strip(),
                relay_output_classification=relay_output_classification,
            )
            print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
        if any(first_nonempty_line(relay_text).startswith(prefix) for prefix in forbidden_prefixes):
            payload = _build_error_payload(
                error_code=err_summary,
                stale_reasons=["summary_impersonates_governed_output"],
                source_artifact_path=source_artifact_path,
                relay_mode=relay_mode,
                target_identity_id=target_identity_id,
                question_tag=str(args.question_tag or "").strip(),
                relay_output_classification=relay_output_classification,
            )
            print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
            return 1

    receipt = build_receipt(
        target_identity_id=target_identity_id,
        question_tag=str(args.question_tag or "").strip(),
        source_artifact=source_artifact_path,
        relay_text=relay_text,
        relay_mode=relay_mode,
        relay_surface=str(template.get("surface_id", "")).strip(),
        delivery_authority=delivery_authority,
        source_snapshot_ts=source_snapshot_ts,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload: dict[str, object] = {
        "build_status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
        "receipt_path": str(output_path),
        "template_path": str(template_path),
        "relay_surface": receipt["relay_surface"],
        "relay_mode": receipt["relay_mode"],
        "target_identity_id": receipt["target_identity_id"],
        "question_tag": receipt["question_tag"],
        "delivery_authority": receipt["delivery_authority"],
        "relay_output_classification": relay_output_classification,
        "source_artifact": receipt["source_artifact"],
        "source_artifact_kind": source_kind,
        "source_identity_id": detected_identity,
        "source_snapshot_ts": receipt["source_snapshot_ts"],
        "source_artifact_generated_at": source_generated_at,
        "relay_text_preview": preview(receipt["relay_text"]),
        "source_text_preview": preview(source_text),
        "validation_attempted": bool(args.validate),
    }

    exit_code = 0
    if args.validate:
        exit_code, validation_payload = _run_validator(
            repo_root=repo_root,
            receipt_path=output_path,
        )
        payload["agent_relay_final_answer_status"] = validation_payload.get("agent_relay_final_answer_status", "")
        payload["validation_error_code"] = validation_payload.get("error_code", "")
        if validation_output_path:
            validation_output_path.parent.mkdir(parents=True, exist_ok=True)
            validation_output_path.write_text(
                json.dumps(validation_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            payload["validation_output_path"] = str(validation_output_path)

    print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
