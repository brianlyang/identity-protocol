#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from resolve_identity_context import (
    default_local_catalog_path,
    merged_catalog,
    resolve_local_catalog_path,
    resolve_repo_catalog_path,
)
from runtime_temp_path_common import runtime_temp_root
from tool_vendor_governance_common import (
    build_identity_upgrade_report_selection_projection,
    resolve_identity_upgrade_report_selection,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

ERR_REPORT_NOT_FOUND = "IP-EWB-001"
ERR_REPORT_INVALID = "IP-EWB-002"
ERR_RUN_ID_MISSING = "IP-EWB-003"
ERR_IDENTITY_MISMATCH = "IP-EWB-004"
ERR_RULEBOOK_MISSING = "IP-EWB-005"
ERR_TASK_HISTORY_MISSING = "IP-EWB-006"
ERR_RULEBOOK_LINK_MISSING = "IP-EWB-007"
ERR_TASK_HISTORY_LINK_MISSING = "IP-EWB-008"
ERR_WRITEBACK_OBJECT_MISSING = "IP-EWB-009"
ERR_WRITEBACK_STATUS_INVALID = "IP-EWB-010"
ERR_WRITEBACK_PATHS_INVALID = "IP-EWB-011"
ERR_WRITEBACK_PATH_RESOLUTION_FAILED = "IP-EWB-012"
ERR_WRITEBACK_RULE_ID_MISSING = "IP-EWB-013"

RUNTIME_TEMP_SELECTION_MODE = "runtime_temp_root_latest_report"
RUNTIME_TEMP_AUTHORITY_CLASS = "runtime_temp_root_latest_report"
RUNTIME_TEMP_POINTER_RESOLUTION_MODE = "runtime_temp_root_latest_report"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_pack(identity_id: str, repo_catalog_path: Path, local_catalog_path: Path) -> Path:
    catalog = merged_catalog(repo_catalog_path, local_catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path)
        if p.exists():
            return p.resolve()
    legacy = Path("identity") / identity_id
    if legacy.exists():
        return legacy.resolve()
    raise FileNotFoundError(f"identity pack not found: {identity_id}")


def _latest_runtime_temp_report(identity_id: str) -> Path | None:
    report_dir = (runtime_temp_root() / "identity-upgrade-reports").resolve()
    if not report_dir.exists():
        return None
    rows = sorted(
        [
            p
            for p in report_dir.glob(f"identity-upgrade-exec-{identity_id}-*.json")
            if p.is_file() and not p.name.endswith("-patch-plan.json")
        ],
        key=lambda p: p.stat().st_mtime,
    )
    return rows[-1].resolve() if rows else None


def _resolve_report_selection(identity_id: str, pack_root: Path, explicit_report: str) -> dict[str, Any]:
    resolution = resolve_identity_upgrade_report_selection(
        identity_id,
        pack_root,
        explicit_report=explicit_report,
    )
    payload = build_identity_upgrade_report_selection_projection(
        resolution,
        field_prefix="report",
    )
    selected_report = resolution.selected_report
    if selected_report is None and not str(explicit_report or "").strip():
        temp_report = _latest_runtime_temp_report(identity_id)
        if temp_report is not None:
            report_dir = (runtime_temp_root() / "identity-upgrade-reports").resolve()
            payload.update(
                {
                    "report_selected_path": str(temp_report),
                    "report_selection_mode": RUNTIME_TEMP_SELECTION_MODE,
                    "report_selected_authority_class": RUNTIME_TEMP_AUTHORITY_CLASS,
                    "report_pointer_resolution_mode": RUNTIME_TEMP_POINTER_RESOLUTION_MODE,
                    "report_pointer_path": str(report_dir),
                }
            )
            selected_report = temp_report
    payload["_selected_report_path"] = selected_report
    return payload


def _resolve_writeback_path(raw_path: Any, *, pack_root: Path, report_path: Path) -> tuple[Path | None, list[Path]]:
    raw = str(raw_path or "").strip()
    if not raw:
        return None, []
    p = Path(raw).expanduser()
    candidates: list[Path] = []
    if p.is_absolute():
        candidates.append(p.resolve())
    else:
        report_dir = report_path.parent.resolve()
        runtime_root = report_dir.parent if report_dir.name == "reports" else report_dir
        for base in (pack_root.resolve(), report_dir, runtime_root):
            candidates.append((base / p).resolve())
    dedup: list[Path] = []
    seen: set[str] = set()
    for cand in candidates:
        key = cand.as_posix()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(cand)
    for cand in dedup:
        if cand.exists():
            return cand, dedup
    return None, dedup


def _load_rulebook_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        ln = line.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except Exception:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def _ok_text(payload: dict[str, Any]) -> str:
    return (
        "[OK] experience writeback validation passed\n"
        f"     execution_report={payload.get('report_selected_path', '')}\n"
        f"     run_id={payload.get('report_run_id', '')}\n"
        f"     rulebook_matches={payload.get('rulebook_match_count', 0)}"
    )


def main() -> int:
    script_ref = Path(__file__).resolve()
    ap = argparse.ArgumentParser(description="Validate experience writeback after identity upgrade execution.")
    ap.add_argument("--catalog", default="", help="legacy alias; when set, used as repo catalog path")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--local-catalog", default=str(default_local_catalog_path(start=script_ref)))
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--execution-report", default="")
    ap.add_argument("--report", default="", help="alias of --execution-report")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "repo_catalog_path": "",
        "local_catalog_path": "",
        "resolved_pack_path": "",
        "report_selected_path": "",
        "report_selection_mode": "",
        "report_selected_authority_class": "",
        "report_pointer_resolution_mode": "",
        "report_pointer_path": "",
        "report_run_id": "",
        "producer_readiness": False,
        "experience_writeback_validation_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
        "upgrade_required": False,
        "all_ok": False,
        "writeback_status": "",
        "writeback_rule_id": "",
        "rulebook_path": "",
        "task_history_path": "",
        "rulebook_match_count": 0,
        "task_history_contains_run_id": False,
        "writeback_path_count": 0,
        "resolved_writeback_paths": [],
        "evidence_ref": "",
    }

    try:
        repo_catalog = (
            resolve_repo_catalog_path(args.catalog, start=script_ref)
            if args.catalog
            else resolve_repo_catalog_path(args.repo_catalog, start=script_ref)
        )
        local_catalog = resolve_local_catalog_path(args.local_catalog, start=script_ref)
        pack = _resolve_pack(args.identity_id, repo_catalog, local_catalog)
        payload["repo_catalog_path"] = str(repo_catalog)
        payload["local_catalog_path"] = str(local_catalog)
        payload["resolved_pack_path"] = str(pack)
    except Exception as exc:
        payload["error_code"] = ERR_REPORT_NOT_FOUND
        payload["stale_reasons"] = [f"identity_resolution_failed:{type(exc).__name__}"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] {exc}")
        return 1

    override = str(args.execution_report or args.report or "").strip()
    report_selection = _resolve_report_selection(args.identity_id, pack, override)
    payload.update({k: v for k, v in report_selection.items() if not k.startswith("_")})
    report_path = report_selection.get("_selected_report_path")
    payload["producer_readiness"] = report_path is not None
    if report_path is None:
        payload["error_code"] = ERR_REPORT_NOT_FOUND
        payload["stale_reasons"] = ["execution_report_not_found"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(
                f"[FAIL] no execution report found for identity {args.identity_id}; "
                "provide --execution-report explicitly when reports are generated outside pack/runtime roots"
            )
        return 1

    payload["report_selected_path"] = str(report_path)
    payload["evidence_ref"] = str(report_path)

    try:
        report = _load_json(report_path)
    except Exception as exc:
        payload["error_code"] = ERR_REPORT_INVALID
        payload["stale_reasons"] = [f"execution_report_invalid_json:{type(exc).__name__}"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] invalid execution report json: {report_path}")
        return 1

    run_id = str(report.get("run_id", "")).strip()
    payload["report_run_id"] = run_id
    payload["upgrade_required"] = bool(report.get("upgrade_required"))
    payload["all_ok"] = bool(report.get("all_ok"))
    payload["writeback_status"] = str(report.get("writeback_status", "")).strip()
    payload["writeback_rule_id"] = str(report.get("writeback_rule_id", "")).strip()

    if not run_id:
        payload["error_code"] = ERR_RUN_ID_MISSING
        payload["stale_reasons"] = ["report_run_id_missing"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] report.run_id missing: {report_path}")
        return 1

    if str(report.get("identity_id", "")).strip() != args.identity_id:
        payload["error_code"] = ERR_IDENTITY_MISMATCH
        payload["stale_reasons"] = ["report_identity_id_mismatch"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(
                f"[FAIL] report.identity_id mismatch: expected={args.identity_id}, "
                f"got={report.get('identity_id')}"
            )
        return 1

    upgrade_required = payload["upgrade_required"]
    all_ok = payload["all_ok"]
    if not upgrade_required:
        payload["experience_writeback_validation_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["upgrade_required_false"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[OK] upgrade_required=false; experience writeback not required")
        return 0

    if not all_ok:
        payload["experience_writeback_validation_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["upgrade_required_true_but_all_ok_false"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[OK] upgrade_required=true but all_ok=false; writeback enforcement deferred until successful run")
        return 0

    rulebook_path = pack / "RULEBOOK.jsonl"
    history_path = pack / "TASK_HISTORY.md"
    payload["rulebook_path"] = str(rulebook_path)
    payload["task_history_path"] = str(history_path)

    if not rulebook_path.exists():
        payload["error_code"] = ERR_RULEBOOK_MISSING
        payload["stale_reasons"] = ["rulebook_missing"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] missing RULEBOOK: {rulebook_path}")
        return 1

    if not history_path.exists():
        payload["error_code"] = ERR_TASK_HISTORY_MISSING
        payload["stale_reasons"] = ["task_history_missing"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] missing TASK_HISTORY: {history_path}")
        return 1

    rows = _load_rulebook_rows(rulebook_path)
    matched_rows = [r for r in rows if str(r.get("evidence_run_id", "")).strip() == run_id]
    payload["rulebook_match_count"] = len(matched_rows)
    if not matched_rows:
        payload["error_code"] = ERR_RULEBOOK_LINK_MISSING
        payload["stale_reasons"] = [f"rulebook_missing_run_link:{run_id}"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] RULEBOOK has no row linked to run_id={run_id}")
        return 1

    history_text = history_path.read_text(encoding="utf-8")
    payload["task_history_contains_run_id"] = run_id in history_text
    if not payload["task_history_contains_run_id"]:
        payload["error_code"] = ERR_TASK_HISTORY_LINK_MISSING
        payload["stale_reasons"] = [f"task_history_missing_run_link:{run_id}"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] TASK_HISTORY missing run_id={run_id} entry")
        return 1

    wb = report.get("experience_writeback")
    if not isinstance(wb, dict):
        payload["error_code"] = ERR_WRITEBACK_OBJECT_MISSING
        payload["stale_reasons"] = ["experience_writeback_object_missing"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[FAIL] execution report missing experience_writeback object")
        return 1

    status = str(wb.get("status", "")).strip()
    if status != "WRITTEN":
        payload["error_code"] = ERR_WRITEBACK_STATUS_INVALID
        payload["stale_reasons"] = [f"experience_writeback_status_invalid:{status or '<empty>'}"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] experience_writeback.status must be WRITTEN, got={status!r}")
        return 1

    writeback_paths = report.get("writeback_paths")
    if not isinstance(writeback_paths, list) or len(writeback_paths) < 2:
        payload["error_code"] = ERR_WRITEBACK_PATHS_INVALID
        payload["stale_reasons"] = ["writeback_paths_missing_or_incomplete"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[FAIL] report.writeback_paths must include RULEBOOK and TASK_HISTORY paths")
        return 1

    resolved_writeback_paths: list[str] = []
    for wp in writeback_paths:
        resolved, searched = _resolve_writeback_path(wp, pack_root=pack, report_path=report_path)
        if resolved is None:
            payload["error_code"] = ERR_WRITEBACK_PATH_RESOLUTION_FAILED
            payload["stale_reasons"] = [
                "writeback_path_resolution_failed:"
                + (", ".join(p.as_posix() for p in searched) if searched else "<none>")
            ]
            if args.json_only:
                _emit(payload, json_only=True)
            else:
                searched_hint = ", ".join(p.as_posix() for p in searched) if searched else "<none>"
                print(f"[FAIL] report.writeback_paths item not found: {wp!r}; searched=[{searched_hint}]")
            return 1
        resolved_writeback_paths.append(str(resolved))
    payload["writeback_path_count"] = len(writeback_paths)
    payload["resolved_writeback_paths"] = resolved_writeback_paths

    if str(report.get("writeback_status", "")).strip() != "WRITTEN":
        payload["error_code"] = ERR_WRITEBACK_STATUS_INVALID
        payload["stale_reasons"] = [f"report_writeback_status_invalid:{report.get('writeback_status')!r}"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] report.writeback_status must be WRITTEN, got={report.get('writeback_status')!r}")
        return 1

    if not payload["writeback_rule_id"]:
        payload["error_code"] = ERR_WRITEBACK_RULE_ID_MISSING
        payload["stale_reasons"] = ["writeback_rule_id_missing"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[FAIL] report.writeback_rule_id must be non-empty")
        return 1

    payload["experience_writeback_validation_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    if args.json_only:
        _emit(payload, json_only=True)
    else:
        print(_ok_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
