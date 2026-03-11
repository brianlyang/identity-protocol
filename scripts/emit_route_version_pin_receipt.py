#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, load_yaml, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_FIELDS_MISSING = "IP-PIN-EMIT-001"
ERR_SOURCE_PARSE = "IP-PIN-EMIT-002"
ERR_OUTPUT_BLOCKED = "IP-PIN-EMIT-003"

STRICT_OPERATIONS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation", "scan", "three-plane"}

CONTRACT_KEYS = (
    "route_workflow_version_pinning_contract_v1",
    "route_workflow_version_pinning_contract",
    "rq_021_route_workflow_version_pinning_contract_v1",
)

RECEIPT_NESTED_KEYS = (
    "route_workflow_version_pin_receipt",
    "route_workflow_version_pinning_receipt",
    "route_version_pin_receipt",
    "route_workflow_pin_receipt",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog = load_yaml(catalog_path)
    except Exception:
        return False
    identities = catalog.get("identities") or []
    row = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _nonempty(value: Any) -> str:
    text = str(value or "").strip()
    return text


def _extract_pin_tuple(source: Any) -> dict[str, str]:
    if not isinstance(source, dict):
        return {}

    route_endpoint = _nonempty(source.get("route_endpoint"))
    workflow_id = _nonempty(source.get("workflow_id"))
    workflow_publish_version = _nonempty(source.get("workflow_publish_version"))
    pin_proof_ref = _nonempty(source.get("pin_proof_ref"))

    if route_endpoint and workflow_id and workflow_publish_version:
        return {
            "route_endpoint": route_endpoint,
            "workflow_id": workflow_id,
            "workflow_publish_version": workflow_publish_version,
            "pin_proof_ref": pin_proof_ref,
        }

    for key in RECEIPT_NESTED_KEYS:
        nested = source.get(key)
        if isinstance(nested, dict):
            cand = _extract_pin_tuple(nested)
            if cand:
                return cand

    for key in ("expected_binding", "pin_binding", "default_binding"):
        nested = source.get(key)
        if isinstance(nested, dict):
            cand = _extract_pin_tuple(nested)
            if cand:
                return cand

    for list_key in ("expected_bindings", "pin_bindings", "bindings"):
        nested = source.get(list_key)
        if isinstance(nested, list):
            for item in nested:
                cand = _extract_pin_tuple(item)
                if cand:
                    return cand

    return {}


def _load_pin_source(path_text: str) -> tuple[dict[str, Any], str]:
    path = Path(path_text).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"pin source not found: {path}")

    raw = path.read_text(encoding="utf-8", errors="ignore")
    source: dict[str, Any] = {}
    try:
        doc = json.loads(raw)
        if isinstance(doc, dict):
            source = doc
        elif isinstance(doc, list):
            source = {"bindings": doc}
    except Exception:
        doc = load_yaml(path)
        if isinstance(doc, dict):
            source = doc
        elif isinstance(doc, list):
            source = {"bindings": doc}
    return source, str(path)


def _derive_pin_proof_ref(route_endpoint: str, workflow_id: str, workflow_publish_version: str) -> str:
    seed = f"{route_endpoint}|{workflow_id}|{workflow_publish_version}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()[:16]
    return f"pin://{workflow_id}@{workflow_publish_version}#{digest}"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _default_output_path(*, identity_id: str, pack_path: Path) -> Path:
    runtime_root = os.environ.get("IDENTITY_RUNTIME_OUTPUT_ROOT", "").strip()
    if runtime_root:
        return Path(runtime_root).expanduser().resolve() / "reports" / f"{identity_id}-route-version-pin-receipt.json"
    return pack_path / "runtime" / "reports" / f"{identity_id}-route-version-pin-receipt.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit route/workflow publish-version pin receipt (RQ-021).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--route-endpoint", default="")
    ap.add_argument("--workflow-id", default="")
    ap.add_argument("--workflow-publish-version", default="")
    ap.add_argument("--pin-proof-ref", default="")
    ap.add_argument("--pin-source", default="", help="json/yaml source containing route pin fields")
    ap.add_argument("--out", default="")
    ap.add_argument("--allow-repo-runtime-fallback", action="store_true")
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

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": False,
        "auto_required_signal": False,
        "route_endpoint": "",
        "workflow_id": "",
        "workflow_publish_version": "",
        "pin_proof_ref": "",
        "pin_status": STATUS_SKIPPED_NOT_REQUIRED,
        "pin_error_code": "",
        "error_code": "",
        "receipt_path": "",
        "evidence_ref": "",
        "pin_receipt_hash": "",
        "source_priority": [],
        "stale_reasons": [],
    }

    if _is_fixture_identity(catalog_path, args.identity_id):
        payload["stale_reasons"] = ["fixture_profile_scope"]
        _emit(payload, json_only=args.json_only)
        return 0

    contract = _select_contract(task)
    required = contract_required(contract) if contract else False

    auto_required = any(
        _nonempty(v)
        for v in (
            args.route_endpoint,
            args.workflow_id,
            args.workflow_publish_version,
            args.pin_proof_ref,
            args.pin_source,
            args.out,
        )
    )
    if args.operation in STRICT_OPERATIONS and auto_required:
        required = True

    payload["required_contract"] = required
    payload["auto_required_signal"] = auto_required

    if not required and not auto_required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    source_row: dict[str, str] = {}

    if _nonempty(args.pin_source):
        try:
            src_doc, src_path = _load_pin_source(args.pin_source)
            src_pin = _extract_pin_tuple(src_doc)
            source_row.update(src_pin)
            if src_pin:
                payload["source_priority"].append("source_file")
            payload["evidence_ref"] = src_path
        except Exception:
            payload["pin_status"] = STATUS_FAIL_REQUIRED
            payload["pin_error_code"] = ERR_SOURCE_PARSE
            payload["error_code"] = ERR_SOURCE_PARSE
            payload["stale_reasons"] = ["pin_source_parse_failed"]
            _emit(payload, json_only=args.json_only)
            return 1

    if isinstance(contract, dict) and contract:
        contract_pin = _extract_pin_tuple(contract)
        if contract_pin:
            for k, v in contract_pin.items():
                source_row.setdefault(k, v)
            payload["source_priority"].append("contract_default")

    cli_pin = {
        "route_endpoint": _nonempty(args.route_endpoint),
        "workflow_id": _nonempty(args.workflow_id),
        "workflow_publish_version": _nonempty(args.workflow_publish_version),
        "pin_proof_ref": _nonempty(args.pin_proof_ref),
    }
    if any(cli_pin.values()):
        for k, v in cli_pin.items():
            if v:
                source_row[k] = v
        payload["source_priority"].append("cli")

    route_endpoint = _nonempty(source_row.get("route_endpoint"))
    workflow_id = _nonempty(source_row.get("workflow_id"))
    workflow_publish_version = _nonempty(source_row.get("workflow_publish_version"))
    pin_proof_ref = _nonempty(source_row.get("pin_proof_ref"))

    missing_fields = [
        name
        for name, value in (
            ("route_endpoint", route_endpoint),
            ("workflow_id", workflow_id),
            ("workflow_publish_version", workflow_publish_version),
        )
        if not value
    ]
    if missing_fields:
        payload["pin_status"] = STATUS_FAIL_REQUIRED
        payload["pin_error_code"] = ERR_FIELDS_MISSING
        payload["error_code"] = ERR_FIELDS_MISSING
        payload["stale_reasons"] = [f"missing_{field}" for field in missing_fields]
        _emit(payload, json_only=args.json_only)
        return 1

    if not pin_proof_ref:
        pin_proof_ref = _derive_pin_proof_ref(route_endpoint, workflow_id, workflow_publish_version)

    if _nonempty(args.out):
        out_path = Path(args.out).expanduser().resolve()
    else:
        out_path = _default_output_path(identity_id=args.identity_id, pack_path=pack_path)

    repo_root = Path.cwd().resolve()
    if _is_within(out_path, repo_root) and not args.allow_repo_runtime_fallback:
        payload["route_endpoint"] = route_endpoint
        payload["workflow_id"] = workflow_id
        payload["workflow_publish_version"] = workflow_publish_version
        payload["pin_proof_ref"] = pin_proof_ref
        payload["pin_status"] = STATUS_FAIL_REQUIRED
        payload["pin_error_code"] = ERR_OUTPUT_BLOCKED
        payload["error_code"] = ERR_OUTPUT_BLOCKED
        payload["receipt_path"] = str(out_path)
        payload["stale_reasons"] = ["repo_output_blocked"]
        _emit(payload, json_only=args.json_only)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)

    generated_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = {
        "identity_id": args.identity_id,
        "operation": args.operation,
        "route_endpoint": route_endpoint,
        "workflow_id": workflow_id,
        "workflow_publish_version": workflow_publish_version,
        "pin_proof_ref": pin_proof_ref,
        "generated_at_utc": generated_at_utc,
        "source_priority": payload["source_priority"],
        "pin_status": STATUS_PASS_REQUIRED,
        "pin_error_code": "",
    }
    raw = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    receipt_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    receipt["pin_receipt_hash"] = receipt_hash

    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload.update(
        {
            "route_endpoint": route_endpoint,
            "workflow_id": workflow_id,
            "workflow_publish_version": workflow_publish_version,
            "pin_proof_ref": pin_proof_ref,
            "pin_status": STATUS_PASS_REQUIRED,
            "pin_error_code": "",
            "error_code": "",
            "receipt_path": str(out_path),
            "evidence_ref": str(out_path),
            "pin_receipt_hash": receipt_hash,
            "stale_reasons": [],
        }
    )
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
