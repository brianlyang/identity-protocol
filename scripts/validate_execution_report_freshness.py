#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from resolve_identity_context import resolve_identity


ERROR_STALE = "IP-REL-001"


@dataclass
class CandidateEval:
    path: Path
    identity_id_match: bool
    catalog_path_match: bool
    pack_path_match: bool
    prompt_path_match: bool
    prompt_sha_match: bool
    report_newer_than_key_inputs: bool
    score: int
    stale_reasons: list[str]
    report_data: dict[str, Any]


def _iso_from_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _collect_from_roots(identity_id: str, roots: list[Path]) -> list[Path]:
    rows: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.glob(f"**/identity-upgrade-exec-{identity_id}-*.json"):
            if p.name.endswith("-patch-plan.json"):
                continue
            rows.append(p.resolve())
    return sorted(set(rows), key=lambda p: p.stat().st_mtime, reverse=True)


def _collect_candidates(identity_id: str, preferred_pack: Path | None, report: str) -> list[Path]:
    if report.strip():
        p = Path(report).expanduser().resolve()
        return [p] if p.exists() else []

    preferred_roots: list[Path] = []
    if preferred_pack is not None:
        preferred_roots.append((preferred_pack / "runtime" / "reports").resolve())
        preferred_roots.append((preferred_pack / "runtime").resolve())
    preferred_rows = _collect_from_roots(identity_id, preferred_roots)
    if preferred_rows:
        return preferred_rows

    fallback_roots: list[Path] = [Path("/tmp/identity-upgrade-reports"), Path("/tmp/identity-runtime")]
    identity_home = os.environ.get("IDENTITY_HOME", "").strip()
    if identity_home:
        fallback_roots.append(Path(identity_home).expanduser().resolve())
    return _collect_from_roots(identity_id, fallback_roots)


def _eval_candidate(
    path: Path,
    *,
    identity_id: str,
    catalog_path: Path,
    resolved_pack: Path,
    prompt_path: Path,
    prompt_sha: str,
    key_input_latest_mtime: float,
) -> CandidateEval:
    data = _safe_json(path)
    rid = str(data.get("identity_id", "")).strip()
    report_catalog = str(data.get("catalog_path", "")).strip()
    report_pack = str(data.get("resolved_pack_path", "")).strip()
    report_prompt = str(data.get("identity_prompt_path", "")).strip()
    report_prompt_sha = str(data.get("identity_prompt_sha256", "")).strip()

    identity_id_match = rid == identity_id
    catalog_path_match = bool(report_catalog) and Path(report_catalog).expanduser().resolve() == catalog_path
    if report_pack:
        pack_candidate = Path(report_pack).expanduser().resolve()
    elif report_prompt:
        pack_candidate = Path(report_prompt).expanduser().resolve().parent
    else:
        pack_candidate = None
    pack_path_match = pack_candidate is not None and pack_candidate == resolved_pack
    prompt_path_match = bool(report_prompt) and Path(report_prompt).expanduser().resolve() == prompt_path
    prompt_sha_match = bool(report_prompt_sha) and report_prompt_sha == prompt_sha
    report_newer_than_key_inputs = path.stat().st_mtime >= key_input_latest_mtime

    reasons: list[str] = []
    if not identity_id_match:
        reasons.append("identity_id_mismatch")
    if not catalog_path_match:
        reasons.append("catalog_path_mismatch_or_missing")
    if not pack_path_match:
        reasons.append("pack_path_mismatch_or_missing")
    if not prompt_path_match:
        reasons.append("prompt_path_mismatch_or_missing")
    if not prompt_sha_match:
        reasons.append("prompt_sha_mismatch_or_missing")
    if not report_newer_than_key_inputs:
        reasons.append("report_older_than_key_inputs")

    score = 0
    score += 32 if identity_id_match else 0
    score += 16 if pack_path_match else 0
    score += 8 if prompt_sha_match else 0
    score += 4 if prompt_path_match else 0
    score += 2 if catalog_path_match else 0
    score += 1 if report_newer_than_key_inputs else 0
    score += int(path.stat().st_mtime / 1_000_000_000)  # tie-break by recency

    return CandidateEval(
        path=path,
        identity_id_match=identity_id_match,
        catalog_path_match=catalog_path_match,
        pack_path_match=pack_path_match,
        prompt_path_match=prompt_path_match,
        prompt_sha_match=prompt_sha_match,
        report_newer_than_key_inputs=report_newer_than_key_inputs,
        score=score,
        stale_reasons=reasons,
        report_data=data,
    )


def _select_best(candidates: list[CandidateEval]) -> CandidateEval:
    if not candidates:
        raise RuntimeError("no_execution_report_candidates")
    return sorted(candidates, key=lambda c: c.score, reverse=True)[0]


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

    raw_candidates = _collect_candidates(args.identity_id, resolved_pack, args.report)
    evaluated = [
        _eval_candidate(
            p,
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            resolved_pack=resolved_pack,
            prompt_path=prompt_path,
            prompt_sha=prompt_sha,
            key_input_latest_mtime=key_input_latest_mtime,
        )
        for p in raw_candidates
    ]

    if not evaluated:
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
            "stale_reasons": ["execution_report_not_found"],
            "checks": {},
            "key_input_paths": [str(p) for p in key_inputs],
            "key_input_latest_mtime_utc": _iso_from_ts(key_input_latest_mtime),
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[FAIL] {ERROR_STALE} execution report not found for identity={args.identity_id}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if args.execution_report_policy == "strict" else 0

    selected = _select_best(evaluated)
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
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(resolved_pack),
        "execution_report_policy": args.execution_report_policy,
        "selection_mode": "explicit" if args.report.strip() else "auto",
        "report_selected_path": str(selected.path),
        "candidate_count": len(evaluated),
        "report_mtime_utc": _iso_from_ts(selected.path.stat().st_mtime),
        "key_input_paths": [str(p) for p in key_inputs],
        "key_input_latest_mtime_utc": _iso_from_ts(key_input_latest_mtime),
        "checks": checks,
        "freshness_status": status,
        "freshness_error_code": "" if strict_ok else ERROR_STALE,
        "stale_reasons": selected.stale_reasons,
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
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if strict_ok:
        return 0
    return 1 if args.execution_report_policy == "strict" else 0


if __name__ == "__main__":
    raise SystemExit(main())
