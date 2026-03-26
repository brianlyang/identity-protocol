#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from execution_report_selection_common import (
    collect_reports as collect_execution_reports,
    evaluate_report_candidate,
    select_best_evaluated_candidate,
)
from resolve_identity_context import resolve_identity

ERROR_STALE = "IP-REL-001"


def _iso_from_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _derive_freshness_hint(stale_reasons: list[str]) -> tuple[str, str]:
    reasons = {str(x).strip() for x in (stale_reasons or []) if str(x).strip()}
    if "report_selector_identity_tuple_no_match_candidates" in reasons:
        return (
            "regenerate_identity_scoped_execution_report",
            "auto-selected reports do not match identity tuple; regenerate report for current identity pack",
        )
    if "report_older_than_key_inputs" in reasons:
        return (
            "run_identity_creator_update_then_rerun_validate",
            "key inputs are newer than execution report; run identity_creator.py update before validate",
        )
    if "execution_report_not_found" in reasons:
        return (
            "run_identity_creator_update_to_generate_report",
            "execution report is missing; run identity_creator.py update before validate",
        )
    return (
        "inspect_freshness_stale_reasons_and_refresh_report",
        "execution report freshness drift detected; refresh execution report before strict validate",
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate upgrade execution report freshness and runtime binding.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--report", default="", help="explicit execution report path; when omitted, auto-select best candidate")
    ap.add_argument(
        "--execution-report-policy",
        choices=["strict", "warn"],
        default="strict",
        help="strict: stale/mismatch fails with IP-REL-001; warn: emit warning payload but return 0",
    )
    ap.add_argument("--json-only", action="store_true", help="emit payload only")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    ctx = resolve_identity(
        args.identity_id,
        repo_catalog_path,
        catalog_path,
        allow_conflict=True,
    )
    resolved_pack = Path(str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "")).expanduser().resolve()
    prompt_path = (resolved_pack / "IDENTITY_PROMPT.md").resolve()
    task_path = (resolved_pack / "CURRENT_TASK.json").resolve()
    if not prompt_path.exists():
        print(f"[FAIL] prompt missing for freshness validation: {prompt_path}")
        return 2
    if not task_path.exists():
        print(f"[FAIL] CURRENT_TASK missing for freshness validation: {task_path}")
        return 2

    prompt_sha = _sha256(prompt_path)
    key_inputs = [prompt_path, task_path]
    key_input_latest_mtime = max(p.stat().st_mtime for p in key_inputs)

    if args.report.strip():
        raw_candidates = [Path(args.report).expanduser().resolve()] if Path(args.report).expanduser().resolve().exists() else []
    else:
        raw_candidates = collect_execution_reports(
            resolved_pack,
            args.identity_id,
            include_fallback_roots=False,
            include_generic_upgrade_json=True,
        )
        if not raw_candidates:
            raw_candidates = collect_execution_reports(
                resolved_pack,
                args.identity_id,
                include_fallback_roots=True,
                include_generic_upgrade_json=True,
            )

    evaluated = [
        evaluate_report_candidate(
            p,
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            resolved_pack_path=resolved_pack,
            prompt_path=prompt_path,
            prompt_sha=prompt_sha,
            key_input_latest_mtime=key_input_latest_mtime,
        )
        for p in raw_candidates
    ]

    if not evaluated:
        stale_reasons = ["execution_report_not_found"]
        next_action, hint = _derive_freshness_hint(stale_reasons)
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "resolved_pack_path": str(resolved_pack),
            "execution_report_policy": args.execution_report_policy,
            "selection_mode": "explicit" if args.report.strip() else "auto",
            "report_selected_path": "",
            "candidate_count": 0,
            "freshness_status": "FAIL" if args.execution_report_policy == "strict" else "WARN",
            "freshness_error_code": ERROR_STALE,
            "stale_reasons": stale_reasons,
            "next_action": next_action,
            "hint": hint,
            "checks": {},
            "key_input_paths": [str(p) for p in key_inputs],
            "key_input_latest_mtime_utc": _iso_from_ts(key_input_latest_mtime),
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[FAIL] {ERROR_STALE} execution report not found for identity={args.identity_id}")
            print(f"[HINT] {hint}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if args.execution_report_policy == "strict" else 0

    strict_tuple_candidates = [c for c in evaluated if c.strict_identity_tuple_match]
    if not args.report.strip():
        if not strict_tuple_candidates:
            stale_reasons = [
                "execution_report_not_found",
                "report_selector_identity_tuple_no_match_candidates",
            ]
            next_action, hint = _derive_freshness_hint(stale_reasons)
            payload = {
                "identity_id": args.identity_id,
                "catalog_path": str(catalog_path),
                "resolved_pack_path": str(resolved_pack),
                "execution_report_policy": args.execution_report_policy,
                "selection_mode": "auto",
                "report_selected_path": "",
                "candidate_count": len(evaluated),
                "strict_tuple_candidate_count": 0,
                "freshness_status": "FAIL" if args.execution_report_policy == "strict" else "WARN",
                "freshness_error_code": ERROR_STALE,
                "stale_reasons": stale_reasons,
                "next_action": next_action,
                "hint": hint,
                "checks": {},
                "key_input_paths": [str(p) for p in key_inputs],
                "key_input_latest_mtime_utc": _iso_from_ts(key_input_latest_mtime),
            }
            if args.json_only:
                print(json.dumps(payload, ensure_ascii=False))
            else:
                print(f"[FAIL] {ERROR_STALE} auto-selected reports do not match current identity tuple")
                print(f"[HINT] {hint}")
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1 if args.execution_report_policy == "strict" else 0
        selected = select_best_evaluated_candidate(strict_tuple_candidates)
    else:
        selected = select_best_evaluated_candidate(evaluated)
    checks = {
        "identity_id_match": selected.identity_id_match,
        "catalog_path_match": selected.catalog_path_match,
        "pack_path_match": selected.pack_path_match,
        "prompt_path_match": selected.prompt_path_match,
        "prompt_sha_match": selected.prompt_sha_match,
        "report_newer_than_key_inputs": selected.report_newer_than_key_inputs,
    }
    strict_ok = all(checks.values())
    status = "PASS" if strict_ok else ("FAIL" if args.execution_report_policy == "strict" else "WARN")
    next_action = ""
    hint = ""
    if not strict_ok:
        next_action, hint = _derive_freshness_hint(selected.stale_reasons)
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(resolved_pack),
        "execution_report_policy": args.execution_report_policy,
        "selection_mode": "explicit" if args.report.strip() else "auto",
        "report_selected_path": str(selected.path),
        "candidate_count": len(evaluated),
        "strict_tuple_candidate_count": len(strict_tuple_candidates),
        "report_mtime_utc": _iso_from_ts(selected.path.stat().st_mtime),
        "key_input_paths": [str(p) for p in key_inputs],
        "key_input_latest_mtime_utc": _iso_from_ts(key_input_latest_mtime),
        "checks": checks,
        "freshness_status": status,
        "freshness_error_code": "" if strict_ok else ERROR_STALE,
        "stale_reasons": selected.stale_reasons,
        "next_action": next_action,
        "hint": hint,
    }
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if strict_ok:
            print(
                f"[OK] execution report freshness validated: identity={args.identity_id} "
                f"report={selected.path}"
            )
        else:
            print(
                f"[WARN] {ERROR_STALE} execution report freshness drift detected: identity={args.identity_id} "
                f"report={selected.path}"
            )
            if hint:
                print(f"[HINT] {hint}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if strict_ok:
        return 0
    return 1 if args.execution_report_policy == "strict" else 0


if __name__ == "__main__":
    raise SystemExit(main())
