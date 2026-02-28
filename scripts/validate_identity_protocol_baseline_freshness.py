#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from resolve_identity_context import resolve_identity

ERR_BASELINE_STALE = "IP-PBL-001"
ERR_REPORT_INVALID = "IP-PBL-002"
ERR_SHA_INVALID = "IP-PBL-003"
ERR_PROTOCOL_ROOT_UNAVAILABLE = "IP-PBL-004"

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass
class BaselineResult:
    status: str
    error_code: str
    stale_reasons: list[str]
    lag_commits: int | None
    current_head_sha: str


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


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


def _collect_reports(identity_id: str, resolved_pack_path: Path, explicit_report: str) -> list[Path]:
    if explicit_report.strip():
        rp = Path(explicit_report).expanduser().resolve()
        return [rp] if rp.exists() else []

    preferred_roots: list[Path] = [
        (resolved_pack_path / "runtime" / "reports").resolve(),
        (resolved_pack_path / "runtime").resolve(),
    ]
    preferred = _collect_from_roots(identity_id, preferred_roots)
    if preferred:
        return preferred

    fallback_roots: list[Path] = [
        Path("/tmp/identity-upgrade-reports"),
        Path("/tmp/identity-runtime"),
    ]
    identity_home = os.environ.get("IDENTITY_HOME", "").strip()
    if identity_home:
        fallback_roots.append(Path(identity_home).expanduser().resolve())
    return _collect_from_roots(identity_id, fallback_roots)


def _resolve_current_head(protocol_root: Path) -> tuple[str, str]:
    rc, out, _ = _run(["git", "-C", str(protocol_root), "rev-parse", "HEAD"])
    if rc != 0:
        return "", ERR_PROTOCOL_ROOT_UNAVAILABLE
    head = out.strip().lower()
    if not SHA40_RE.fullmatch(head):
        return "", ERR_PROTOCOL_ROOT_UNAVAILABLE
    return head, ""


def _resolve_lag_commits(protocol_root: Path, old_sha: str, new_sha: str) -> int | None:
    rc_anc, _, _ = _run(["git", "-C", str(protocol_root), "merge-base", "--is-ancestor", old_sha, new_sha])
    if rc_anc == 0:
        rc_count, out, _ = _run(["git", "-C", str(protocol_root), "rev-list", "--count", f"{old_sha}..{new_sha}"])
        if rc_count == 0 and out.strip().isdigit():
            return int(out.strip())
    return None


def _evaluate(
    report_data: dict[str, Any],
    *,
    baseline_policy: str,
) -> BaselineResult:
    stale_reasons: list[str] = []
    report_root_raw = str(report_data.get("protocol_root", "")).strip()
    report_sha = str(report_data.get("protocol_commit_sha", "")).strip().lower()

    if not report_root_raw:
        status = "FAIL" if baseline_policy == "strict" else "WARN"
        return BaselineResult(
            status=status,
            error_code=ERR_REPORT_INVALID,
            stale_reasons=["report_protocol_root_missing"],
            lag_commits=None,
            current_head_sha="",
        )

    protocol_root = Path(report_root_raw).expanduser().resolve()
    if not protocol_root.exists():
        status = "FAIL" if baseline_policy == "strict" else "WARN"
        return BaselineResult(
            status=status,
            error_code=ERR_PROTOCOL_ROOT_UNAVAILABLE,
            stale_reasons=["report_protocol_root_not_found"],
            lag_commits=None,
            current_head_sha="",
        )

    if not SHA40_RE.fullmatch(report_sha):
        status = "FAIL" if baseline_policy == "strict" else "WARN"
        return BaselineResult(
            status=status,
            error_code=ERR_SHA_INVALID,
            stale_reasons=["report_protocol_commit_sha_invalid"],
            lag_commits=None,
            current_head_sha="",
        )

    current_head_sha, head_err = _resolve_current_head(protocol_root)
    if head_err:
        status = "FAIL" if baseline_policy == "strict" else "WARN"
        return BaselineResult(
            status=status,
            error_code=head_err,
            stale_reasons=["current_protocol_head_unavailable"],
            lag_commits=None,
            current_head_sha="",
        )

    if report_sha == current_head_sha:
        return BaselineResult(
            status="PASS",
            error_code="",
            stale_reasons=[],
            lag_commits=0,
            current_head_sha=current_head_sha,
        )

    stale_reasons.append("protocol_commit_sha_mismatch")
    lag = _resolve_lag_commits(protocol_root, report_sha, current_head_sha)
    status = "FAIL" if baseline_policy == "strict" else "WARN"
    return BaselineResult(
        status=status,
        error_code=ERR_BASELINE_STALE,
        stale_reasons=stale_reasons,
        lag_commits=lag,
        current_head_sha=current_head_sha,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol baseline freshness for identity execution report.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--execution-report", default="")
    ap.add_argument("--baseline-policy", choices=["strict", "warn"], default="warn")
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
        ctx = resolve_identity(
            args.identity_id,
            repo_catalog_path,
            catalog_path,
            allow_conflict=True,
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity context: {exc}")
        return 2

    resolved_pack_path = Path(str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "")).expanduser().resolve()
    reports = _collect_reports(args.identity_id, resolved_pack_path, args.execution_report)
    if not reports:
        status = "FAIL" if args.baseline_policy == "strict" else "WARN"
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "resolved_pack_path": str(resolved_pack_path),
            "report_selected_path": "",
            "report_protocol_root": "",
            "report_protocol_commit_sha": "",
            "current_protocol_head_sha": "",
            "baseline_status": status,
            "baseline_error_code": ERR_REPORT_INVALID,
            "lag_commits": None,
            "stale_reasons": ["execution_report_not_found"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[WARN] {ERR_REPORT_INVALID} execution report not found for identity={args.identity_id}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if args.baseline_policy == "strict" else 0

    selected = reports[0]
    report_data = _safe_json(selected)
    if not report_data:
        status = "FAIL" if args.baseline_policy == "strict" else "WARN"
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "resolved_pack_path": str(resolved_pack_path),
            "report_selected_path": str(selected),
            "report_protocol_root": "",
            "report_protocol_commit_sha": "",
            "current_protocol_head_sha": "",
            "baseline_status": status,
            "baseline_error_code": ERR_REPORT_INVALID,
            "lag_commits": None,
            "stale_reasons": ["execution_report_invalid_json"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[WARN] {ERR_REPORT_INVALID} invalid execution report json: {selected}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if args.baseline_policy == "strict" else 0

    result = _evaluate(report_data, baseline_policy=args.baseline_policy)
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(resolved_pack_path),
        "report_selected_path": str(selected),
        "report_protocol_root": str(report_data.get("protocol_root", "")).strip(),
        "report_protocol_commit_sha": str(report_data.get("protocol_commit_sha", "")).strip().lower(),
        "current_protocol_head_sha": result.current_head_sha,
        "baseline_status": result.status,
        "baseline_error_code": result.error_code,
        "lag_commits": result.lag_commits,
        "stale_reasons": result.stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if result.status == "PASS":
            print(
                "[OK] protocol baseline freshness validated: "
                f"identity={args.identity_id} report={selected}"
            )
        else:
            print(
                f"[WARN] {result.error_code} protocol baseline stale: "
                f"identity={args.identity_id} report={selected}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if result.status == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
