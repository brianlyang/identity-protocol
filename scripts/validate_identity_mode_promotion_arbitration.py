#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from resolve_identity_context import (
    default_local_catalog_path,
    resolve_identity,
    resolve_local_catalog_path,
    resolve_repo_catalog_path,
)
from tool_vendor_governance_common import (
    build_identity_upgrade_report_selection_projection,
    resolve_identity_upgrade_report_selection,
)

HIGH_IMPACT = {"CURRENT_TASK.json", "IDENTITY_PROMPT.md", "RULEBOOK.jsonl"}
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

ERR_REPORT_MISSING = "IP-MPA-001"
ERR_REPORT_PARSE_FAILED = "IP-MPA-002"
ERR_PROTOCOL_MODE_INVALID = "IP-MPA-003"
ERR_MODE_A_NOT_ALL_OK = "IP-MPA-004"
ERR_ARBITRATION_NOTE_MISSING = "IP-MPA-005"
ERR_MODE_A_REPLAY_MISSING = "IP-MPA-006"
ERR_MODE_A_REPLAY_NOT_FOUND = "IP-MPA-007"
ERR_MODE_A_REPLAY_INVALID = "IP-MPA-008"
ERR_RUNTIME_CONTEXT_UNRESOLVED = "IP-MPA-009"


def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip()


def _changed(base: str, head: str) -> list[str]:
    rc, out = _run(["git", "diff", "--name-only", f"{base}..{head}"])
    if rc != 0:
        return []
    return [x.strip() for x in out.splitlines() if x.strip()]


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_runtime_context(
    identity_id: str,
    *,
    repo_catalog_token: str,
    local_catalog_token: str,
    start: Path,
) -> tuple[Path, Path, Path, dict[str, Any]]:
    repo_catalog = resolve_repo_catalog_path(repo_catalog_token, start=start)
    local_catalog = resolve_local_catalog_path(local_catalog_token, start=start)
    ctx = resolve_identity(identity_id, repo_catalog, local_catalog, allow_conflict=True)
    pack_raw = str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "").strip()
    if not pack_raw:
        raise FileNotFoundError(f"resolved_pack_path missing for identity: {identity_id}")
    pack_root = Path(pack_raw).expanduser().resolve()
    return repo_catalog, local_catalog, pack_root, ctx


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
    payload["_selected_report_path"] = resolution.selected_report
    return payload


def _resolve_report_artifact_path(raw_path: str, *, selected_report_path: Path, pack_root: Path) -> Path:
    token = str(raw_path or "").strip()
    if not token:
        return Path()
    raw = Path(token).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    candidates = [
        (selected_report_path.parent / raw).resolve(),
        (pack_root / raw).resolve(),
    ]
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.as_posix()
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate
    return candidates[0]


def _is_high_impact(identity_id: str, files: list[str]) -> bool:
    prefixes = [
        f"identity/{identity_id}/",
        f"identity/packs/{identity_id}/",
        f".identity/{identity_id}/",
        f".identity/packs/{identity_id}/",
    ]
    for f in files:
        for pref in prefixes:
            if f.startswith(pref) and Path(f).name in HIGH_IMPACT:
                return True
    return False


def main() -> int:
    script_ref = Path(__file__).resolve()
    ap = argparse.ArgumentParser(description="Validate mode-B promotion arbitration for high-impact identity changes")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="", help="legacy alias; when set, used as repo catalog path")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--local-catalog", default=str(default_local_catalog_path(start=script_ref)))
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--report", default="", help="optional explicit upgrade execution report")
    ap.add_argument("--changed-file", action="append", default=[], help="optional explicit changed-file entries for deterministic probing")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "base": "",
        "head": str(args.head or "").strip() or "HEAD",
        "changed_file_source": "",
        "changed_file_count": 0,
        "changed_files": [],
        "high_impact_change_detected": False,
        "repo_catalog_path": "",
        "local_catalog_path": "",
        "resolved_pack_path": "",
        "resolved_source_layer": "",
        "resolved_scope": "",
        "report_selected_path": "",
        "report_selection_mode": "",
        "report_selected_authority_class": "",
        "report_pointer_resolution_mode": "",
        "report_pointer_path": "",
        "producer_protocol_mode": "",
        "producer_all_ok": False,
        "arbitration_note_id": "",
        "mode_a_replay_report": "",
        "mode_a_replay_report_resolved_path": "",
        "mode_promotion_arbitration_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
    }

    base = args.base.strip()
    explicit_changed_files = [str(item or "").strip() for item in (args.changed_file or []) if str(item or "").strip()]
    if explicit_changed_files:
        files = explicit_changed_files
        payload["changed_file_source"] = "explicit_changed_files"
    else:
        if not base:
            rc, out = _run(["git", "rev-parse", "HEAD~1"])
            if rc != 0:
                if args.json_only:
                    payload["mode_promotion_arbitration_status"] = STATUS_SKIPPED_NOT_REQUIRED
                    payload["changed_file_source"] = "git_diff"
                    payload["stale_reasons"] = ["base_commit_unresolved"]
                    _emit(payload, json_only=True)
                else:
                    print("[WARN] cannot resolve base; skip promotion arbitration check")
                return 0
            base = out
        files = _changed(base, args.head)
        payload["changed_file_source"] = "git_diff"
    payload["base"] = base
    payload["changed_files"] = files
    payload["changed_file_count"] = len(files)

    if not files:
        payload["mode_promotion_arbitration_status"] = STATUS_SKIPPED_NOT_REQUIRED
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[OK] no changed files; promotion arbitration skipped")
        return 0

    payload["high_impact_change_detected"] = _is_high_impact(args.identity_id, files)
    if not payload["high_impact_change_detected"]:
        payload["mode_promotion_arbitration_status"] = STATUS_SKIPPED_NOT_REQUIRED
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[OK] no high-impact identity-core changes; mode promotion arbitration pass")
        return 0

    repo_catalog_token = str(args.catalog or "").strip() or str(args.repo_catalog or "").strip()
    try:
        repo_catalog, local_catalog, pack_root, ctx = _resolve_runtime_context(
            args.identity_id,
            repo_catalog_token=repo_catalog_token,
            local_catalog_token=str(args.local_catalog or "").strip(),
            start=script_ref,
        )
        payload["repo_catalog_path"] = str(repo_catalog)
        payload["local_catalog_path"] = str(local_catalog)
        payload["resolved_pack_path"] = str(pack_root)
        payload["resolved_source_layer"] = str(ctx.get("source_layer", "")).strip()
        payload["resolved_scope"] = str(ctx.get("resolved_scope", "")).strip()
    except Exception as exc:
        payload["error_code"] = ERR_RUNTIME_CONTEXT_UNRESOLVED
        payload["stale_reasons"] = [str(exc)]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] unable to resolve runtime identity context: {exc}")
        return 1

    selection_payload = _resolve_report_selection(args.identity_id, pack_root, str(args.report or "").strip())
    payload.update(
        {
            key: value
            for key, value in selection_payload.items()
            if key != "_selected_report_path"
        }
    )
    report = selection_payload.get("_selected_report_path")
    report_path = report if isinstance(report, Path) else None
    if report_path is None or not report_path.exists():
        payload["error_code"] = ERR_REPORT_MISSING
        payload["stale_reasons"] = ["selected_upgrade_execution_report_missing"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[FAIL] high-impact changes require upgrade execution report evidence")
        return 1

    try:
        row = _load(report_path)
    except Exception as exc:
        payload["error_code"] = ERR_REPORT_PARSE_FAILED
        payload["stale_reasons"] = [str(exc)]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] unable to parse upgrade execution report: {report_path}")
        return 1

    payload["producer_protocol_mode"] = str(row.get("protocol_mode", "")).strip()
    payload["producer_all_ok"] = bool(row.get("all_ok"))

    mode = payload["producer_protocol_mode"]
    all_ok = payload["producer_all_ok"]

    if mode == "mode_a_shared":
        if not all_ok:
            payload["error_code"] = ERR_MODE_A_NOT_ALL_OK
            payload["stale_reasons"] = ["mode_a_shared_report_not_all_ok"]
            if args.json_only:
                _emit(payload, json_only=True)
            else:
                print(f"[FAIL] mode_a_shared report must be all_ok=true for promotion: {report_path}")
            return 1
        payload["mode_promotion_arbitration_status"] = STATUS_PASS_REQUIRED
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[OK] high-impact changes covered by mode_a_shared replay PASS: {report_path}")
        return 0

    if mode != "mode_b_standalone":
        payload["error_code"] = ERR_PROTOCOL_MODE_INVALID
        payload["stale_reasons"] = [f"invalid_protocol_mode:{mode!r}"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] invalid protocol_mode for promotion evidence: {mode!r}")
        return 1

    note = str(row.get("arbitration_note_id", "")).strip()
    mode_a_replay = str(row.get("mode_a_replay_report", "")).strip()
    payload["arbitration_note_id"] = note
    payload["mode_a_replay_report"] = mode_a_replay
    if not note:
        payload["error_code"] = ERR_ARBITRATION_NOTE_MISSING
        payload["stale_reasons"] = ["mode_b_arbitration_note_missing"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[FAIL] mode_b promotion requires arbitration_note_id")
        return 1
    if not mode_a_replay:
        payload["error_code"] = ERR_MODE_A_REPLAY_MISSING
        payload["stale_reasons"] = ["mode_b_mode_a_replay_missing"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[FAIL] mode_b promotion requires mode_a_replay_report")
        return 1

    replay_path = _resolve_report_artifact_path(
        mode_a_replay,
        selected_report_path=report_path,
        pack_root=pack_root,
    )
    payload["mode_a_replay_report_resolved_path"] = str(replay_path)
    if not replay_path.exists():
        payload["error_code"] = ERR_MODE_A_REPLAY_NOT_FOUND
        payload["stale_reasons"] = ["mode_a_replay_report_not_found"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print(f"[FAIL] mode_a_replay_report not found: {replay_path}")
        return 1
    replay = _load(replay_path)
    if str(replay.get("protocol_mode", "")).strip() != "mode_a_shared" or not bool(replay.get("all_ok")):
        payload["error_code"] = ERR_MODE_A_REPLAY_INVALID
        payload["stale_reasons"] = ["mode_a_replay_report_not_mode_a_shared_all_ok"]
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            print("[FAIL] mode_a_replay_report must be mode_a_shared with all_ok=true")
        return 1

    payload["mode_promotion_arbitration_status"] = STATUS_PASS_REQUIRED
    if args.json_only:
        _emit(payload, json_only=True)
    else:
        print("[OK] mode_b promotion arbitration validated with mode_a replay evidence")
        print(f"     execution_report={report_path}")
        print(f"     arbitration_note_id={note}")
        print(f"     mode_a_replay_report={replay_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
