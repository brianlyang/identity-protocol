#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, load_yaml, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_RECEIPT_MISSING = "IP-PIN-001"
ERR_RECEIPT_FIELDS_MISSING = "IP-PIN-002"
ERR_PIN_MISMATCH = "IP-PIN-003"
ERR_EXPECTED_BINDING_MISSING = "IP-PIN-004"
ERR_RECEIPT_PARSE = "IP-PIN-005"

STRICT_OPERATIONS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation", "scan", "three-plane"}

CONTRACT_KEYS = (
    "route_workflow_version_pinning_contract_v1",
    "route_workflow_version_pinning_contract",
    "rq_021_route_workflow_version_pinning_contract_v1",
)

NESTED_KEYS = (
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
    return str(value or "").strip()


def _extract_pin_tuple(source: Any) -> dict[str, str]:
    if not isinstance(source, dict):
        return {}

    row = {
        "route_endpoint": _nonempty(source.get("route_endpoint")),
        "workflow_id": _nonempty(source.get("workflow_id")),
        "workflow_publish_version": _nonempty(source.get("workflow_publish_version")),
        "pin_proof_ref": _nonempty(source.get("pin_proof_ref")),
    }
    if row["route_endpoint"] and row["workflow_id"] and row["workflow_publish_version"]:
        return row

    for key in NESTED_KEYS:
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

    for key in ("expected_bindings", "pin_bindings", "bindings"):
        nested = source.get(key)
        if isinstance(nested, list):
            for item in nested:
                cand = _extract_pin_tuple(item)
                if cand:
                    return cand
    return {}


def _load_json_or_yaml(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    try:
        return json.loads(raw)
    except Exception:
        return load_yaml(path)


def _candidate_receipt_paths(*, identity_id: str, pack_path: Path) -> list[Path]:
    rows: list[Path] = []

    runtime_root = os.environ.get("IDENTITY_RUNTIME_OUTPUT_ROOT", "").strip()
    candidate_roots: list[Path] = []
    if runtime_root:
        candidate_roots.append(Path(runtime_root).expanduser().resolve() / "reports")
    candidate_roots.append((pack_path / "runtime" / "reports").resolve())
    candidate_roots.append((pack_path / "runtime").resolve())

    for parent in [pack_path.resolve(), *pack_path.resolve().parents]:
        candidate = (parent / "resource" / "reports").resolve()
        candidate_roots.append(candidate)
        if candidate.exists():
            break

    seen: set[str] = set()
    for root in candidate_roots:
        key = root.as_posix()
        if key in seen:
            continue
        seen.add(key)
        if not root.exists():
            continue
        patterns = [
            f"**/{identity_id}-route-version-pin-receipt*.json",
            f"**/*route-version-pin-receipt*{identity_id}*.json",
            "**/*route-version-pin-receipt*.json",
        ]
        for pat in patterns:
            rows.extend(p for p in root.glob(pat) if p.is_file())

    dedup: dict[str, Path] = {p.resolve().as_posix(): p.resolve() for p in rows}
    ordered = sorted(dedup.values(), key=lambda p: p.stat().st_mtime)
    return ordered


def _select_receipt_path(*, explicit_receipt: str, identity_id: str, pack_path: Path) -> Path | None:
    if _nonempty(explicit_receipt):
        p = Path(explicit_receipt).expanduser().resolve()
        return p if p.exists() and p.is_file() else None
    rows = _candidate_receipt_paths(identity_id=identity_id, pack_path=pack_path)
    if not rows:
        return None
    return rows[-1]


def _extract_expected_binding(*, args: argparse.Namespace, contract: dict[str, Any], actual: dict[str, str]) -> tuple[dict[str, str], str]:
    from_args = {
        "route_endpoint": _nonempty(args.expected_route_endpoint),
        "workflow_id": _nonempty(args.expected_workflow_id),
        "workflow_publish_version": _nonempty(args.expected_workflow_publish_version),
    }
    if any(from_args.values()):
        return from_args, "cli_expected"

    if _nonempty(args.expected_source):
        path = Path(args.expected_source).expanduser().resolve()
        if path.exists() and path.is_file():
            doc = _load_json_or_yaml(path)
            if isinstance(doc, list):
                for item in doc:
                    cand = _extract_pin_tuple(item)
                    if not cand:
                        continue
                    if actual and cand.get("route_endpoint") == actual.get("route_endpoint"):
                        return {
                            "route_endpoint": cand.get("route_endpoint", ""),
                            "workflow_id": cand.get("workflow_id", ""),
                            "workflow_publish_version": cand.get("workflow_publish_version", ""),
                        }, "expected_source"
                if doc:
                    cand = _extract_pin_tuple(doc[0])
                    if cand:
                        return {
                            "route_endpoint": cand.get("route_endpoint", ""),
                            "workflow_id": cand.get("workflow_id", ""),
                            "workflow_publish_version": cand.get("workflow_publish_version", ""),
                        }, "expected_source"
            elif isinstance(doc, dict):
                cand = _extract_pin_tuple(doc)
                if cand:
                    return {
                        "route_endpoint": cand.get("route_endpoint", ""),
                        "workflow_id": cand.get("workflow_id", ""),
                        "workflow_publish_version": cand.get("workflow_publish_version", ""),
                    }, "expected_source"

    cand = _extract_pin_tuple(contract)
    if cand:
        return {
            "route_endpoint": cand.get("route_endpoint", ""),
            "workflow_id": cand.get("workflow_id", ""),
            "workflow_publish_version": cand.get("workflow_publish_version", ""),
        }, "contract_default"

    for list_key in ("expected_bindings", "pin_bindings", "bindings"):
        rows = contract.get(list_key)
        if isinstance(rows, list):
            chosen = None
            for item in rows:
                cand = _extract_pin_tuple(item)
                if not cand:
                    continue
                if actual and cand.get("route_endpoint") == actual.get("route_endpoint"):
                    chosen = cand
                    break
                if chosen is None:
                    chosen = cand
            if chosen:
                return {
                    "route_endpoint": chosen.get("route_endpoint", ""),
                    "workflow_id": chosen.get("workflow_id", ""),
                    "workflow_publish_version": chosen.get("workflow_publish_version", ""),
                }, "contract_list"

    return {}, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate route/workflow publish-version pinning receipt (RQ-021).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--receipt", default="")
    ap.add_argument("--expected-route-endpoint", default="")
    ap.add_argument("--expected-workflow-id", default="")
    ap.add_argument("--expected-workflow-publish-version", default="")
    ap.add_argument("--expected-source", default="", help="json/yaml expected pin source")
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
        "receipt_path": "",
        "evidence_ref": "",
        "route_endpoint": "",
        "workflow_id": "",
        "workflow_publish_version": "",
        "pin_proof_ref": "",
        "expected_route_endpoint": "",
        "expected_workflow_id": "",
        "expected_workflow_publish_version": "",
        "expected_binding_source": "",
        "pin_status": STATUS_SKIPPED_NOT_REQUIRED,
        "pin_error_code": "",
        "error_code": "",
        "mismatch_fields": [],
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
            args.receipt,
            args.expected_route_endpoint,
            args.expected_workflow_id,
            args.expected_workflow_publish_version,
            args.expected_source,
        )
    )
    if auto_required and args.operation in STRICT_OPERATIONS:
        required = True

    payload["required_contract"] = required
    payload["auto_required_signal"] = auto_required

    if not required and not auto_required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    receipt_path = _select_receipt_path(explicit_receipt=args.receipt, identity_id=args.identity_id, pack_path=pack_path)
    if receipt_path is None:
        payload["pin_status"] = STATUS_FAIL_REQUIRED
        payload["pin_error_code"] = ERR_RECEIPT_MISSING
        payload["error_code"] = ERR_RECEIPT_MISSING
        payload["stale_reasons"] = ["pin_receipt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["receipt_path"] = str(receipt_path)
    payload["evidence_ref"] = str(receipt_path)

    try:
        receipt_doc = _load_json_or_yaml(receipt_path)
    except Exception:
        payload["pin_status"] = STATUS_FAIL_REQUIRED
        payload["pin_error_code"] = ERR_RECEIPT_PARSE
        payload["error_code"] = ERR_RECEIPT_PARSE
        payload["stale_reasons"] = ["pin_receipt_parse_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    actual = _extract_pin_tuple(receipt_doc)
    payload["route_endpoint"] = actual.get("route_endpoint", "")
    payload["workflow_id"] = actual.get("workflow_id", "")
    payload["workflow_publish_version"] = actual.get("workflow_publish_version", "")
    payload["pin_proof_ref"] = actual.get("pin_proof_ref", "")

    missing_receipt_fields = [
        name
        for name in ("route_endpoint", "workflow_id", "workflow_publish_version", "pin_proof_ref")
        if not _nonempty(payload.get(name))
    ]
    if missing_receipt_fields:
        payload["pin_status"] = STATUS_FAIL_REQUIRED
        payload["pin_error_code"] = ERR_RECEIPT_FIELDS_MISSING
        payload["error_code"] = ERR_RECEIPT_FIELDS_MISSING
        payload["stale_reasons"] = [f"missing_{x}" for x in missing_receipt_fields]
        _emit(payload, json_only=args.json_only)
        return 1

    expected, expected_source = _extract_expected_binding(args=args, contract=contract, actual=actual)
    payload["expected_route_endpoint"] = expected.get("route_endpoint", "")
    payload["expected_workflow_id"] = expected.get("workflow_id", "")
    payload["expected_workflow_publish_version"] = expected.get("workflow_publish_version", "")
    payload["expected_binding_source"] = expected_source

    if not any(_nonempty(v) for v in expected.values()):
        payload["pin_status"] = STATUS_FAIL_REQUIRED
        payload["pin_error_code"] = ERR_EXPECTED_BINDING_MISSING
        payload["error_code"] = ERR_EXPECTED_BINDING_MISSING
        payload["stale_reasons"] = ["expected_binding_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    mismatches: list[str] = []
    for key in ("route_endpoint", "workflow_id", "workflow_publish_version"):
        exp = _nonempty(expected.get(key))
        act = _nonempty(actual.get(key))
        if exp and act != exp:
            mismatches.append(key)

    payload["mismatch_fields"] = mismatches
    if mismatches:
        payload["pin_status"] = STATUS_FAIL_REQUIRED
        payload["pin_error_code"] = ERR_PIN_MISMATCH
        payload["error_code"] = ERR_PIN_MISMATCH
        payload["stale_reasons"] = [f"mismatch_{x}" for x in mismatches]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["pin_status"] = STATUS_PASS_REQUIRED
    payload["pin_error_code"] = ""
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
