#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from protocol_feedback_contract_common import (
    canonical_dirs,
    ensure_index_linkage,
    is_strict_operation,
    rel_to_feedback_root,
    resolve_feedback_root,
    utc_now_z,
    write_json,
)
from response_stamp_common import resolve_layer_intent
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_BOOTSTRAP_READINESS = "IP-PFB-CH-004"
ERR_BOOTSTRAP_UNLINKED = "IP-PFB-CH-005"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_bootstrap_ready_contract_v1",
        "protocol_feedback_bootstrap_ready_contract",
        "protocol_feedback_canonical_reply_channel_contract_v1",
        "protocol_feedback_robustness_contract_v1",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _resolve_protocol_lane(
    *,
    layer_intent_text: str,
    work_layer: str,
    expected_work_layer: str,
    source_layer: str,
    stamp_json: str,
) -> tuple[str, bool, float, str]:
    stamp_doc: dict[str, Any] = {}
    if str(stamp_json or "").strip():
        stamp_doc = _parse_json_payload(Path(stamp_json).expanduser().resolve())
    wl = str(expected_work_layer or "").strip().lower() or str(work_layer or "").strip().lower()
    if not wl:
        wl = str(stamp_doc.get("resolved_work_layer", "")).strip().lower() or str(stamp_doc.get("work_layer", "")).strip().lower()
    protocol_triggered = bool(stamp_doc.get("protocol_triggered", False))
    if not wl:
        intent = resolve_layer_intent(
            explicit_work_layer=work_layer,
            explicit_source_layer=source_layer,
            intent_text=layer_intent_text,
            default_work_layer="instance",
            default_source_layer="global",
        )
        wl = str(intent.get("resolved_work_layer", "")).strip().lower() or "instance"
        protocol_triggered = bool(intent.get("protocol_triggered", False))
        confidence = float(intent.get("intent_confidence", 0.0) or 0.0)
        reason = str(intent.get("fallback_reason", "")).strip()
        return wl, protocol_triggered, confidence, reason
    confidence = float(stamp_doc.get("intent_confidence", 0.0) or 0.0)
    reason = str(stamp_doc.get("fallback_reason", "")).strip()
    return wl, protocol_triggered, confidence, reason


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-feedback bootstrap readiness (with deterministic auto-bootstrap).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--feedback-root", default="")
    ap.add_argument("--stamp-json", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--work-layer", default="")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--auto-bootstrap", action="store_true")
    ap.add_argument("--no-auto-bootstrap", action="store_true")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
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
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required_contract = bool(args.force_check or contract_required(contract))
    strict = is_strict_operation(args.operation)
    auto_bootstrap = not bool(args.no_auto_bootstrap)
    if args.auto_bootstrap:
        auto_bootstrap = True

    resolved_work_layer, protocol_triggered, intent_confidence, fallback_reason = _resolve_protocol_lane(
        layer_intent_text=str(args.layer_intent_text or "").strip(),
        work_layer=str(args.work_layer or "").strip(),
        expected_work_layer=str(args.expected_work_layer or "").strip(),
        source_layer=str(args.source_layer or "").strip(),
        stamp_json=str(args.stamp_json or "").strip(),
    )

    protocol_lane_selected = resolved_work_layer in {"protocol", "dual"} or protocol_triggered
    required = bool(required_contract or protocol_lane_selected)

    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    d = canonical_dirs(feedback_root)
    outbox_dir = d["outbox_dir"]
    evidence_dir = d["evidence_dir"]
    upgrade_dir = d["upgrade_dir"]
    index_path = d["index_path"]
    canonical = [outbox_dir, evidence_dir, upgrade_dir]
    missing_dirs = [str(p) for p in canonical if not p.exists()]

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "auto_required_signal": bool(protocol_lane_selected and not required_contract),
        "strict_operation": strict,
        "resolved_work_layer": resolved_work_layer,
        "protocol_triggered": protocol_triggered,
        "intent_confidence": intent_confidence,
        "fallback_reason": fallback_reason,
        "protocol_lane_selected": protocol_lane_selected,
        "protocol_feedback_bootstrap_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_feedback_bootstrap_mode": "failed",
        "bootstrap_created_paths": [],
        "bootstrap_receipt_path": "",
        "feedback_root": str(feedback_root),
        "missing_required_dirs": missing_dirs,
        "error_code": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not protocol_lane_selected:
        payload["protocol_feedback_bootstrap_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["instance_lane_selected"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not missing_dirs:
        payload["protocol_feedback_bootstrap_status"] = STATUS_PASS_REQUIRED
        payload["protocol_feedback_bootstrap_mode"] = "preexisting"
        payload["stale_reasons"] = []
        _emit(payload, json_only=args.json_only)
        return 0

    if not auto_bootstrap:
        payload["protocol_feedback_bootstrap_status"] = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
        payload["protocol_feedback_bootstrap_mode"] = "failed"
        payload["error_code"] = ERR_BOOTSTRAP_READINESS
        payload["stale_reasons"] = ["protocol_layer_without_bootstrap_readiness", "auto_bootstrap_disabled"]
        _emit(payload, json_only=args.json_only)
        return 1 if strict else 0

    try:
        created_paths: list[str] = []
        for p in canonical:
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                created_paths.append(str(p))
        ts = utc_now_z().replace("-", "").replace(":", "")
        receipt = {
            "event": "protocol_feedback_bootstrap",
            "identity_id": args.identity_id,
            "operation": args.operation,
            "resolved_work_layer": resolved_work_layer,
            "protocol_triggered": protocol_triggered,
            "feedback_root": str(feedback_root),
            "created_paths": [rel_to_feedback_root(Path(p), feedback_root) for p in created_paths],
            "generated_at": utc_now_z(),
        }
        receipt_path = (outbox_dir / f"BOOTSTRAP_RECEIPT_{ts}.json").resolve()
        write_json(receipt_path, receipt)
        rel_receipt = rel_to_feedback_root(receipt_path, feedback_root)
        _, linked = ensure_index_linkage(index_path, [rel_receipt], section_title="Bootstrap receipts")
        if not linked:
            payload["protocol_feedback_bootstrap_status"] = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
            payload["protocol_feedback_bootstrap_mode"] = "failed"
            payload["bootstrap_created_paths"] = created_paths
            payload["bootstrap_receipt_path"] = str(receipt_path)
            payload["error_code"] = ERR_BOOTSTRAP_UNLINKED
            payload["stale_reasons"] = ["bootstrap_receipt_missing_or_unlinked"]
            _emit(payload, json_only=args.json_only)
            return 1 if strict else 0
        payload["protocol_feedback_bootstrap_status"] = STATUS_PASS_REQUIRED
        payload["protocol_feedback_bootstrap_mode"] = "auto_created"
        payload["bootstrap_created_paths"] = created_paths
        payload["bootstrap_receipt_path"] = str(receipt_path)
        payload["missing_required_dirs"] = []
        payload["error_code"] = ""
        payload["stale_reasons"] = []
        _emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        payload["protocol_feedback_bootstrap_status"] = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
        payload["protocol_feedback_bootstrap_mode"] = "failed"
        payload["error_code"] = ERR_BOOTSTRAP_READINESS
        payload["stale_reasons"] = [f"bootstrap_constructor_error:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1 if strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
