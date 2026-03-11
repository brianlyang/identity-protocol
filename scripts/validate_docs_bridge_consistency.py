#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_DOC_MISSING = "IP-DBRIDGE-001"
ERR_CONTRADICTION_FOUND = "IP-DBRIDGE-002"

PENDING_TOKEN = re.compile(r"\bimplementation pending\b|\brequires implementation\b", flags=re.IGNORECASE)
LANDED_TOKEN = re.compile(r"\bimplementation landed\b|\blanding update\b|\bvalidator landed\b", flags=re.IGNORECASE)
RQ_TOKEN = re.compile(r"ASB16-RQ-\d{3}")


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "docs_bridge_consistency_contract_v1",
        "docs_bridge_consistency_contract",
        "rq_008_docs_bridge_consistency_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _anchor_refs(text: str, *, limit: int = 24) -> list[str]:
    refs: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            refs.append(stripped[4:].strip())
            if len(refs) >= limit:
                break
    return refs


def _collect_contradictions(*, governance_text: str, review_text: str) -> list[str]:
    contradictions: list[str] = []
    merged_lines = governance_text.splitlines() + review_text.splitlines()
    indexed: dict[str, dict[str, bool]] = {}
    for line in merged_lines:
        ids = set(RQ_TOKEN.findall(line))
        if not ids:
            continue
        pending = bool(PENDING_TOKEN.search(line))
        landed = bool(LANDED_TOKEN.search(line))
        if not pending and not landed:
            continue
        for rq in sorted(ids):
            row = indexed.setdefault(rq, {"pending": False, "landed": False})
            row["pending"] = row["pending"] or pending
            row["landed"] = row["landed"] or landed
    for rq, flags in sorted(indexed.items()):
        if flags.get("pending") and flags.get("landed"):
            contradictions.append(f"{rq}:pending_vs_landed")
    return contradictions


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate governance/review docs bridge consistency contract (RQ-008).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--governance-doc", default="docs/governance/identity-actor-session-binding-governance-v1.6.0.md")
    ap.add_argument("--review-doc", default="docs/review/protocol-remediation-audit-ledger-v1.6.md")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required = contract_required(contract)
    if args.force_required:
        required = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in {"update", "readiness", "e2e", "ci", "validate"}),
        "producer_readiness": False,
        "requiredization_current_round_linked": bool(required),
        "bridge_consistency_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "contradiction_pairs": [],
        "governance_anchor_refs": [],
        "review_anchor_refs": [],
        "governance_doc_path": "",
        "review_doc_path": "",
        "stale_reasons": [],
        "evidence_ref": "",
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    governance_doc_path = Path(args.governance_doc).expanduser().resolve()
    review_doc_path = Path(args.review_doc).expanduser().resolve()
    payload["governance_doc_path"] = str(governance_doc_path)
    payload["review_doc_path"] = str(review_doc_path)
    payload["evidence_ref"] = str(governance_doc_path)

    if not governance_doc_path.exists() or not review_doc_path.exists():
        payload["bridge_consistency_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_DOC_MISSING
        reasons = []
        if not governance_doc_path.exists():
            reasons.append("governance_doc_missing")
        if not review_doc_path.exists():
            reasons.append("review_doc_missing")
        payload["stale_reasons"] = reasons
        _emit(payload, json_only=args.json_only)
        return 1

    governance_text = governance_doc_path.read_text(encoding="utf-8", errors="ignore")
    review_text = review_doc_path.read_text(encoding="utf-8", errors="ignore")
    payload["producer_readiness"] = bool(governance_text.strip()) and bool(review_text.strip())
    payload["governance_anchor_refs"] = _anchor_refs(governance_text)
    payload["review_anchor_refs"] = _anchor_refs(review_text)

    contradictions = _collect_contradictions(governance_text=governance_text, review_text=review_text)
    payload["contradiction_pairs"] = contradictions
    if contradictions:
        payload["bridge_consistency_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRADICTION_FOUND
        payload["stale_reasons"] = ["governance_review_contradiction_detected"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["bridge_consistency_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
