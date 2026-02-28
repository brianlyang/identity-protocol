#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task, resolve_report_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_BOUNDARY_VIOLATION = "IP-GOV-BASE-001"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}

DEFAULT_ALLOW_PREFIXES = ("docs/",)
DEFAULT_DENY_PREFIXES = (
    "scripts/",
    ".github/",
    "identity/catalog/",
    "identity/protocol/",
)
DEFAULT_IGNORE_PREFIXES = (
    ".agents/identity/",
    "identity/runtime/",
)
REQUIRED_OVERRIDE_FIELDS = ("approved_by", "ticket_id", "purpose", "scope_paths", "expiry")


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _run_git(args: list[str], *, cwd: Path) -> str:
    p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=str(cwd))
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "git command failed").strip())
    return (p.stdout or "").strip()


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "instance_base_repo_mutation_policy_v1",
        "instance_base_repo_mutation_policy_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _norm_prefixes(raw: Any, default: tuple[str, ...]) -> list[str]:
    if not isinstance(raw, list) or not raw:
        return list(default)
    out: list[str] = []
    for item in raw:
        token = str(item).strip().replace("\\", "/")
        if token:
            out.append(token)
    return out or list(default)


def _matches_any(path: str, patterns: list[str]) -> bool:
    p = path.replace("\\", "/")
    for pat in patterns:
        token = str(pat).strip().replace("\\", "/")
        if not token:
            continue
        if "*" in token or "?" in token or "[" in token:
            if fnmatch.fnmatch(p, token):
                return True
            continue
        if token.endswith("/"):
            if p.startswith(token):
                return True
            continue
        if p == token or p.startswith(f"{token}/"):
            return True
    return False


def _iter_report_artifacts(report_doc: dict[str, Any]) -> list[str]:
    refs: list[str] = []

    writeback = report_doc.get("writeback_paths")
    if isinstance(writeback, list):
        refs.extend(str(x).strip() for x in writeback if str(x).strip())

    for row in report_doc.get("path_policy_violations") or []:
        if isinstance(row, dict):
            p = str(row.get("path", "")).strip()
            if p:
                refs.append(p)

    artifacts = report_doc.get("artifacts")
    if isinstance(artifacts, list):
        for x in artifacts:
            token = str(x).strip()
            if token.endswith("-patch-plan.json"):
                refs.append(token)
    elif isinstance(artifacts, dict):
        token = str(artifacts.get("patch_plan_path", "")).strip()
        if token:
            refs.append(token)

    return [x for x in refs if x]


def _load_patch_surface(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = doc.get("patch_surface")
    if not isinstance(rows, list):
        return []
    out: list[str] = []
    for row in rows:
        token = str(row).strip()
        if token:
            out.append(token)
    return out


def _resolve_candidate_path(raw: str, *, report_path: Path, pack_path: Path) -> Path:
    token = str(raw).strip()
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    # Prefer pack-root relative for report payload fields like RULEBOOK.jsonl / TASK_HISTORY.md.
    by_pack = (pack_path / p).resolve()
    if by_pack.exists():
        return by_pack
    return (report_path.parent / p).resolve()


def _changed_paths_from_git(*, repo_root: Path, base: str, head: str) -> list[str]:
    out = _run_git(["diff", "--name-status", base, head], cwd=repo_root)
    changed: list[str] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        status, rel = parts[0].strip(), parts[1].strip().replace("\\", "/")
        if status == "D":
            continue
        if rel:
            changed.append(rel)
    return changed


def _parse_expiry(raw: str) -> datetime | None:
    token = str(raw or "").strip()
    if not token:
        return None
    if token.endswith("Z"):
        token = token[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(token)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _validate_override_receipt(path: Path, blocked_paths: list[str]) -> tuple[bool, list[str], dict[str, Any]]:
    reasons: list[str] = []
    payload: dict[str, Any] = {}
    if not path.exists():
        return False, ["override_receipt_missing"], payload
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False, ["override_receipt_invalid_json"], payload
    if not isinstance(payload, dict):
        return False, ["override_receipt_not_object"], {}

    missing = [k for k in REQUIRED_OVERRIDE_FIELDS if k not in payload]
    if missing:
        reasons.append(f"override_receipt_missing_fields:{','.join(missing)}")

    scope_paths = payload.get("scope_paths")
    scope_list = [str(x).strip() for x in scope_paths] if isinstance(scope_paths, list) else []
    if not scope_list:
        reasons.append("override_receipt_scope_paths_empty")
    else:
        uncovered = [p for p in blocked_paths if not _matches_any(p, scope_list)]
        if uncovered:
            reasons.append("override_receipt_scope_not_covering_blocked_paths")

    expiry = _parse_expiry(str(payload.get("expiry", "")))
    if expiry is None:
        reasons.append("override_receipt_expiry_invalid")
    elif expiry < datetime.now(timezone.utc):
        reasons.append("override_receipt_expired")

    return not reasons, reasons, payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate instance-to-base-repo mutation boundary (docs allowlist / code denylist).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--report", default="")
    ap.add_argument("--report-glob", default="")
    ap.add_argument("--operation", choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"], default="validate")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    ap.add_argument("--check-git-diff", action="store_true")
    ap.add_argument("--override-receipt", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
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
    auto_required_signal = False

    report_glob = str(args.report_glob or contract.get("report_glob") or f"runtime/reports/identity-upgrade-exec-{args.identity_id}-*.json").strip()
    report_path: Path | None = None
    if args.report.strip():
        report_path = resolve_report_path(report=args.report, pattern=report_glob, pack_root=pack_path)
    elif not args.check_git_diff:
        report_path = resolve_report_path(report="", pattern=report_glob, pack_root=pack_path)
    if (not required) and report_path is not None:
        required = True
        auto_required_signal = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "base_repo_write_boundary_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "report_selected_path": str(report_path) if report_path else "",
        "source_mode": "none",
        "allowlist_prefixes": [],
        "denylist_prefixes": [],
        "ignore_prefixes": [],
        "candidate_paths": [],
        "repo_relative_candidates": [],
        "ignored_paths": [],
        "allowed_paths": [],
        "blocked_paths": [],
        "explicit_deny_hits": [],
        "override_receipt_path": "",
        "override_applied": False,
        "override_receipt_fields": {},
        "stale_reasons": [],
    }

    allowlist = _norm_prefixes(contract.get("allowlist_prefixes"), DEFAULT_ALLOW_PREFIXES)
    denylist = _norm_prefixes(contract.get("denylist_prefixes"), DEFAULT_DENY_PREFIXES)
    ignorelist = _norm_prefixes(contract.get("ignore_prefixes"), DEFAULT_IGNORE_PREFIXES)
    try:
        pack_rel = pack_path.resolve().relative_to(repo_root).as_posix().rstrip("/")
    except Exception:
        pack_rel = ""
    if pack_rel:
        ignorelist.append(f"{pack_rel}/")
    payload["allowlist_prefixes"] = allowlist
    payload["denylist_prefixes"] = denylist
    payload["ignore_prefixes"] = sorted(set(ignorelist))

    repo_rel_candidates: list[str] = []
    raw_candidates: list[str] = []
    source_mode = "none"

    if report_path is not None:
        try:
            report_doc = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            report_doc = {}
        artifacts = _iter_report_artifacts(report_doc)
        patch_surface_rows: list[str] = []
        for token in artifacts:
            if token.endswith("-patch-plan.json"):
                patch_surface_rows.extend(_load_patch_surface(Path(token).expanduser().resolve()))
        artifacts.extend(patch_surface_rows)
        resolved_paths: list[str] = []
        for token in artifacts:
            resolved = _resolve_candidate_path(token, report_path=report_path, pack_path=pack_path)
            resolved_paths.append(str(resolved))
            try:
                rel = resolved.relative_to(repo_root).as_posix()
                repo_rel_candidates.append(rel)
            except Exception:
                continue
        raw_candidates = sorted(set(resolved_paths))
        repo_rel_candidates = sorted(set(repo_rel_candidates))
        source_mode = "report"
    elif args.check_git_diff:
        try:
            base = args.base.strip() or _run_git(["rev-parse", "HEAD~1"], cwd=repo_root)
            head = args.head.strip() or _run_git(["rev-parse", "HEAD"], cwd=repo_root)
            repo_rel_candidates = _changed_paths_from_git(repo_root=repo_root, base=base, head=head)
            source_mode = "git_diff"
        except Exception as exc:
            payload["base_repo_write_boundary_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_BOUNDARY_VIOLATION
            payload["stale_reasons"] = [f"git_diff_failed:{exc}"]
            _emit(payload, json_only=args.json_only)
            return 1

    payload["source_mode"] = source_mode
    payload["candidate_paths"] = raw_candidates
    payload["repo_relative_candidates"] = repo_rel_candidates
    if (not required) and source_mode == "git_diff" and bool(repo_rel_candidates):
        required = True
        auto_required_signal = True
    payload["required_contract"] = required
    payload["auto_required_signal"] = auto_required_signal

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    ignored_paths = [p for p in repo_rel_candidates if _matches_any(p, ignorelist)]
    filtered_candidates = [p for p in repo_rel_candidates if p not in set(ignored_paths)]
    payload["ignored_paths"] = sorted(set(ignored_paths))

    if not filtered_candidates:
        if report_path is None and args.operation in STRICT_OPERATIONS:
            payload["base_repo_write_boundary_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_BOUNDARY_VIOLATION
            payload["stale_reasons"] = ["execution_report_not_found"]
            _emit(payload, json_only=args.json_only)
            return 1
        payload["base_repo_write_boundary_status"] = STATUS_PASS_REQUIRED
        payload["stale_reasons"] = ["no_base_repo_mutation_candidate_after_ignore_filter"]
        _emit(payload, json_only=args.json_only)
        return 0

    allowed = [p for p in filtered_candidates if _matches_any(p, allowlist)]
    blocked: list[str] = []
    explicit_deny_hits: list[str] = []
    for rel in filtered_candidates:
        deny_hit = _matches_any(rel, denylist)
        allow_hit = _matches_any(rel, allowlist)
        if deny_hit:
            explicit_deny_hits.append(rel)
        if deny_hit or (not allow_hit):
            blocked.append(rel)

    payload["allowed_paths"] = sorted(set(allowed))
    payload["blocked_paths"] = sorted(set(blocked))
    payload["explicit_deny_hits"] = sorted(set(explicit_deny_hits))

    if blocked:
        receipt_raw = str(args.override_receipt or contract.get("override_receipt_path", "")).strip()
        if receipt_raw:
            receipt_path = Path(receipt_raw).expanduser()
            if not receipt_path.is_absolute():
                receipt_path = (pack_path / receipt_path).resolve()
            else:
                receipt_path = receipt_path.resolve()
            payload["override_receipt_path"] = str(receipt_path)
            ok, reasons, receipt_doc = _validate_override_receipt(receipt_path, payload["blocked_paths"])
            payload["override_receipt_fields"] = receipt_doc if isinstance(receipt_doc, dict) else {}
            if ok:
                payload["override_applied"] = True
                payload["base_repo_write_boundary_status"] = STATUS_PASS_REQUIRED
                payload["stale_reasons"] = ["override_receipt_applied"]
                _emit(payload, json_only=args.json_only)
                return 0
            payload["stale_reasons"] = reasons
        else:
            payload["stale_reasons"] = ["blocked_paths_without_override"]
        payload["base_repo_write_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_BOUNDARY_VIOLATION
        _emit(payload, json_only=args.json_only)
        return 1

    payload["base_repo_write_boundary_status"] = STATUS_PASS_REQUIRED
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
