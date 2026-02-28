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

ERR_MISSING_CLASSIFICATION = "IP-SEM-001"
ERR_MIXED_WITHOUT_SPLIT = "IP-SEM-002"
ERR_NAMESPACE_VIOLATION = "IP-SEM-003"
ERR_DOMAIN_WHITELIST = "IP-SEM-004"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "semantic_routing_guard_contract_v1",
        "semantic_routing_guard_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _feedback_artifacts_present(feedback_root: Path) -> bool:
    if not feedback_root.exists():
        return False
    return any(p.is_file() for p in feedback_root.rglob("*"))


def _collect_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted([p for p in root.rglob("*") if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)


def _outbox_legacy_refs(outbox_dir: Path) -> list[str]:
    if not outbox_dir.exists():
        return []
    refs: list[str] = []
    for p in sorted(outbox_dir.glob("FEEDBACK_BATCH_*")):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r"`([^`]+)`", text):
            token = m.group(1).strip()
            low = token.lower()
            if "vendor-intel/" in low and "protocol-vendor-intel/" not in low and "business-partner-intel/" not in low:
                refs.append(f"{p}:{token}")
    return sorted(set(refs))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol feedback vendor namespace separation contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--feedback-root", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
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
    required = contract_required(contract) if contract else False

    feedback_root = Path(args.feedback_root).expanduser().resolve() if args.feedback_root.strip() else (
        pack_path / "runtime" / "protocol-feedback"
    ).resolve()
    auto_required_signal = False
    if not contract and _feedback_artifacts_present(feedback_root):
        required = True
        auto_required_signal = True
    protocol_vendor_root = (feedback_root / "protocol-vendor-intel").resolve()
    business_partner_root = (feedback_root / "business-partner-intel").resolve()
    legacy_vendor_root = (feedback_root / "vendor-intel").resolve()
    outbox_root = (feedback_root / "outbox-to-protocol").resolve()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "feedback_root": str(feedback_root),
        "protocol_vendor_root": str(protocol_vendor_root),
        "business_partner_root": str(business_partner_root),
        "legacy_vendor_root": str(legacy_vendor_root),
        "vendor_namespace_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "protocol_vendor_file_count": 0,
        "business_partner_file_count": 0,
        "legacy_vendor_file_count": 0,
        "legacy_namespace_refs": [],
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not feedback_root.exists():
        payload["error_code"] = ERR_MISSING_CLASSIFICATION
        payload["stale_reasons"] = ["feedback_root_not_found"]
        if args.operation in INSPECTION_OPERATIONS:
            payload["vendor_namespace_status"] = STATUS_SKIPPED_NOT_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 0
        payload["vendor_namespace_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    protocol_files = _collect_files(protocol_vendor_root)
    business_files = _collect_files(business_partner_root)
    legacy_files = _collect_files(legacy_vendor_root)
    outbox_legacy = _outbox_legacy_refs(outbox_root)

    payload["protocol_vendor_file_count"] = len(protocol_files)
    payload["business_partner_file_count"] = len(business_files)
    payload["legacy_vendor_file_count"] = len(legacy_files)
    payload["legacy_namespace_refs"] = outbox_legacy

    stale_reasons: list[str] = []
    error_code = ""

    require_split = bool(contract.get("require_split_namespaces", True))
    if require_split and len(protocol_files) == 0 and len(business_files) == 0:
        stale_reasons.append("split_namespace_outputs_missing")
        error_code = ERR_DOMAIN_WHITELIST

    if legacy_files:
        stale_reasons.append("legacy_vendor_namespace_has_files")
        error_code = ERR_NAMESPACE_VIOLATION

    if outbox_legacy:
        stale_reasons.append("outbox_references_legacy_vendor_namespace")
        if not error_code:
            error_code = ERR_NAMESPACE_VIOLATION

    if stale_reasons:
        payload["vendor_namespace_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_NAMESPACE_VIOLATION
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["vendor_namespace_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
