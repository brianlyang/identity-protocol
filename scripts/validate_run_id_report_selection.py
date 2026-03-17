#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REPORT_NOT_FOUND = "IP-RSEL-001"
ERR_RUN_ID_NO_MATCH = "IP-RSEL-002"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "run_id_report_selection_contract_v1",
        "run_id_report_selection_contract",
        "rq_009_run_id_anchored_report_selection_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _candidate_report_roots(pack_path: Path) -> list[Path]:
    roots: list[Path] = []
    roots.append((pack_path / "runtime" / "reports").resolve())
    roots.append((pack_path / "runtime").resolve())
    for parent in [pack_path.resolve(), *pack_path.resolve().parents]:
        candidate = (parent / "resource" / "reports").resolve()
        roots.append(candidate)
        if candidate.exists():
            break
    dedup: dict[str, Path] = {}
    for root in roots:
        dedup[root.as_posix()] = root
    return list(dedup.values())


def _collect_reports(pack_path: Path, identity_id: str) -> list[Path]:
    rows: list[Path] = []
    pattern = f"**/identity-upgrade-exec-{identity_id}-*.json"
    for root in _candidate_report_roots(pack_path):
        if not root.exists():
            continue
        for p in root.glob(pattern):
            if p.is_file() and not p.name.endswith("-patch-plan.json"):
                rows.append(p.resolve())
    unique: dict[str, Path] = {p.as_posix(): p for p in rows}
    return sorted(unique.values(), key=lambda p: p.stat().st_mtime)


def _report_run_id(path: Path) -> str:
    try:
        data = load_json(path)
    except Exception:
        data = {}
    run_id = str(data.get("run_id", "")).strip()
    if run_id:
        return run_id
    if path.name.startswith("identity-upgrade-exec-") and path.name.endswith(".json") and not path.name.endswith("-patch-plan.json"):
        return path.stem
    return ""


def _select_report(*, explicit_report: str, run_id: str, reports: list[Path]) -> tuple[Path | None, str]:
    if explicit_report.strip():
        p = Path(explicit_report).expanduser().resolve()
        if p.exists() and p.is_file():
            return p, "explicit_report"
        return None, "explicit_report_missing"

    if run_id.strip():
        run_hits = [p for p in reports if run_id in p.name or _report_run_id(p) == run_id]
        if run_hits:
            return sorted(run_hits, key=lambda p: p.stat().st_mtime)[-1], "run_id_bound"
        return None, "run_id_not_found"

    if not reports:
        return None, "no_reports"
    return reports[-1], "mtime_fallback"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate run-id anchored report selection contract (RQ-009).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--report", default="")
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

    run_id = str(args.run_id or contract.get("run_id", "")).strip()
    explicit_report = str(args.report or "").strip()
    reports = _collect_reports(pack_path, args.identity_id)
    selected_report, selection_strategy = _select_report(explicit_report=explicit_report, run_id=run_id, reports=reports)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": bool(reports),
        "requiredization_current_round_linked": False,
        "run_id_report_selection_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "run_id": run_id,
        "selection_strategy": selection_strategy,
        "report_selected_path": str(selected_report) if selected_report else "",
        "candidate_count": len(reports),
        "candidate_paths": [str(p) for p in reports[-10:]],
        "evidence_ref": str(selected_report) if selected_report else "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if selected_report is None:
        if args.operation in INSPECTION_OPERATIONS:
            if selection_strategy == "run_id_not_found":
                payload["stale_reasons"] = ["required_contract_not_applicable_current_round_unlinked"]
                _emit(payload, json_only=args.json_only)
                return 0
            if selection_strategy in {"no_reports"}:
                payload["stale_reasons"] = ["required_contract_not_applicable_no_reports"]
                _emit(payload, json_only=args.json_only)
                return 0
            if not run_id and not explicit_report:
                payload["stale_reasons"] = ["required_contract_not_applicable_no_current_round_evidence_source"]
                _emit(payload, json_only=args.json_only)
                return 0
        if selection_strategy in {"no_reports"} and args.operation in INSPECTION_OPERATIONS:
            payload["stale_reasons"] = ["required_contract_not_applicable_no_reports"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["run_id_report_selection_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RUN_ID_NO_MATCH if selection_strategy == "run_id_not_found" else ERR_REPORT_NOT_FOUND
        payload["stale_reasons"] = [selection_strategy]
        _emit(payload, json_only=args.json_only)
        return 1

    if explicit_report:
        payload["requiredization_current_round_linked"] = True
    elif run_id and selection_strategy == "run_id_bound":
        payload["requiredization_current_round_linked"] = True
    elif args.operation in INSPECTION_OPERATIONS:
        payload["stale_reasons"] = ["required_contract_not_applicable_no_current_round_evidence_source"]
        _emit(payload, json_only=args.json_only)
        return 0

    payload["run_id_report_selection_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
