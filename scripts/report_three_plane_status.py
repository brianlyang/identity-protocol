#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from resolve_identity_context import resolve_identity


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_json(path: str) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"json file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _latest_report(identity_id: str, identity_home: str = "", preferred_pack: str = "") -> Path | None:
    roots: list[Path] = []
    if preferred_pack.strip():
        pack = Path(preferred_pack).expanduser().resolve()
        roots.append(pack / "runtime" / "reports")
        roots.append(pack / "runtime")
    roots.extend(
        [
            Path("/tmp/identity-upgrade-reports"),
            Path("/tmp/identity-runtime"),
        ]
    )
    if identity_home.strip():
        roots.append(Path(identity_home).expanduser().resolve())
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        candidates.extend(root.glob(f"**/identity-upgrade-exec-{identity_id}-*.json"))
    filtered = [p for p in candidates if not p.name.endswith("-patch-plan.json")]
    if not filtered:
        return None
    filtered.sort(key=lambda p: p.stat().st_mtime)
    return filtered[-1]


def _release_plane_status(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if args.checks_json:
        checks_doc = _load_json(args.checks_json)
        raw = checks_doc.get("required_checks_set", [])
        if isinstance(raw, list):
            checks = [x for x in raw if isinstance(x, dict)]

    if not args.required_gates_run_id:
        detail = {
            "conditions": {
                "target_branch_explicit": bool(args.target_branch),
                "release_head_sha_explicit": bool(args.release_head_sha),
                "required_gates_run_id_accessible": False,
                "run_head_matches_release_head": False,
                "required_checks_all_success": False,
                "workflow_file_sha_matches": False,
            },
            "required_checks_set": checks,
        }
        return "NOT_STARTED", detail

    cond = {
        "target_branch_explicit": bool(args.target_branch),
        "release_head_sha_explicit": bool(args.release_head_sha),
        "required_gates_run_id_accessible": bool(args.required_gates_run_id and args.run_url),
        "run_head_matches_release_head": args.run_head_sha == args.release_head_sha and bool(args.run_head_sha),
        "required_checks_all_success": bool(checks) and all(str(x.get("status", "")).lower() == "success" for x in checks),
        "workflow_file_sha_matches": args.run_workflow_file_sha == args.workflow_file_sha and bool(args.workflow_file_sha),
    }
    return ("CLOSED" if all(cond.values()) else "BLOCKED"), {"conditions": cond, "required_checks_set": checks}


def _repo_plane_status(args: argparse.Namespace, resolved: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    checks: dict[str, Any] = {
        "catalog_explicit": bool(args.catalog and Path(args.catalog).exists()),
        "resolved_scope_known": str(resolved.get("resolved_scope", "")).upper() != "UNKNOWN",
        "conflict_detected": bool(resolved.get("conflict_detected", False)),
    }
    if args.with_docs_contract:
        rc, out, err = _run(["python3", "scripts/docs_command_contract_check.py"])
        checks["docs_command_contract"] = {
            "rc": rc,
            "ok": rc == 0,
            "stdout_tail": out.splitlines()[-1] if out else "",
            "stderr_tail": err.splitlines()[-1] if err else "",
        }
    status = "CLOSED"
    if checks["conflict_detected"]:
        status = "BLOCKED"
    if not checks["catalog_explicit"] or not checks["resolved_scope_known"]:
        status = "BLOCKED"
    if args.with_docs_contract and not checks["docs_command_contract"]["ok"]:
        status = "BLOCKED"
    return status, checks


def _instance_plane_status(args: argparse.Namespace, report_path: Path | None) -> tuple[str, dict[str, Any]]:
    if report_path is None:
        return "NOT_STARTED", {"reason": "execution_report_not_found"}

    data = _load_json(str(report_path))
    ew = data.get("experience_writeback") or {}
    mandatory = all(
        k in data
        for k in (
            "permission_state",
            "writeback_status",
            "next_action",
            "skills_used",
            "mcp_tools_used",
            "tool_calls_used",
            "capability_activation_status",
            "capability_activation_error_code",
        )
    ) and isinstance(ew, dict) and (
        "status" in ew and "error_code" in ew
    )
    wb = str(data.get("writeback_status", "")).strip()
    ps = str(data.get("permission_state", "")).strip()
    all_ok = _bool(data.get("all_ok", False))
    err_code = str((ew.get("error_code", "") or data.get("permission_error_code", ""))).strip()
    next_action = str(data.get("next_action", "")).strip()
    cap_status = str(data.get("capability_activation_status", "")).strip().upper()
    cap_error = str(data.get("capability_activation_error_code", "")).strip()
    hard_boundary = err_code.startswith("IP-PATH-") or err_code.startswith("IP-PERM-")

    validators: dict[str, Any] = {}
    # Always validate tuple and writeback linkage to keep evidence machine-checkable.
    rc_tuple, out_tuple, err_tuple = _run(
        ["python3", "scripts/validate_identity_binding_tuple.py", "--identity-id", args.identity_id, "--report", str(report_path)]
    )
    validators["binding_tuple"] = {"rc": rc_tuple, "ok": rc_tuple == 0, "out": out_tuple, "err": err_tuple}

    rc_wb, out_wb, err_wb = _run(
        [
            "python3",
            "scripts/validate_identity_experience_writeback.py",
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--local-catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--execution-report",
            str(report_path),
        ]
    )
    validators["experience_writeback"] = {"rc": rc_wb, "ok": rc_wb == 0, "out": out_wb, "err": err_wb}

    perm_cmd = ["python3", "scripts/validate_identity_permission_state.py", "--identity-id", args.identity_id, "--report", str(report_path), "--ci"]
    if all_ok and wb == "WRITTEN" and ps == "WRITEBACK_WRITTEN":
        perm_cmd.append("--require-written")
    rc_perm, out_perm, err_perm = _run(perm_cmd)
    validators["permission_state"] = {"rc": rc_perm, "ok": rc_perm == 0, "out": out_perm, "err": err_perm}

    rc_prompt, out_prompt, err_prompt = _run(
        [
            "python3",
            "scripts/validate_identity_prompt_activation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--report",
            str(report_path),
        ]
    )
    validators["prompt_activation"] = {"rc": rc_prompt, "ok": rc_prompt == 0, "out": out_prompt, "err": err_prompt}

    rc_prompt_lc, out_prompt_lc, err_prompt_lc = _run(
        [
            "python3",
            "scripts/validate_identity_prompt_lifecycle.py",
            "--identity-id",
            args.identity_id,
            "--report",
            str(report_path),
        ]
    )
    validators["prompt_lifecycle"] = {
        "rc": rc_prompt_lc,
        "ok": rc_prompt_lc == 0,
        "out": out_prompt_lc,
        "err": err_prompt_lc,
    }

    cap_cmd = [
        "python3",
        "scripts/validate_identity_capability_activation.py",
        "--identity-id",
        args.identity_id,
        "--report",
        str(report_path),
    ]
    if all_ok and wb == "WRITTEN" and ps == "WRITEBACK_WRITTEN":
        cap_cmd.append("--require-activated")
    rc_cap, out_cap, err_cap = _run(cap_cmd)
    validators["capability_activation"] = {
        "rc": rc_cap,
        "ok": rc_cap == 0,
        "out": out_cap,
        "err": err_cap,
    }

    detail = {
        "report_path": str(report_path),
        "all_ok": all_ok,
        "writeback_status": wb,
        "permission_state": ps,
        "capability_activation_status": cap_status,
        "capability_activation_error_code": cap_error,
        "next_action": next_action,
        "error_code": err_code,
        "mandatory_fields_complete": bool(mandatory),
        "hard_boundary": hard_boundary,
        "validators": validators,
    }

    validators_all_ok = all(v.get("ok", False) for v in validators.values())
    capability_strict_ok = cap_status in {"ACTIVATED", "NOT_REQUIRED"}
    if all_ok and wb == "WRITTEN" and ps == "WRITEBACK_WRITTEN" and mandatory and validators_all_ok and capability_strict_ok:
        return "CLOSED", detail
    if hard_boundary:
        return "BLOCKED", detail
    if mandatory and next_action and validators_all_ok:
        return "IN_PROGRESS", detail
    return "BLOCKED", detail


def _git_current_branch() -> str:
    rc, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0:
        return out.strip()
    return ""


def _git_head_sha() -> str:
    rc, out, _ = _run(["git", "rev-parse", "HEAD"])
    if rc == 0:
        return out.strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit unified three-plane status for identity governance.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default=os.environ.get("IDENTITY_CATALOG", ""))
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--execution-report", default="")
    ap.add_argument("--with-docs-contract", action="store_true", help="run repo-plane docs contract checker")
    ap.add_argument("--target-branch", default="")
    ap.add_argument("--release-head-sha", default="")
    ap.add_argument("--required-gates-run-id", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--workflow-file-sha", default="")
    ap.add_argument("--run-head-sha", default="")
    ap.add_argument("--run-workflow-file-sha", default="")
    ap.add_argument("--checks-json", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if not args.catalog:
        print("[FAIL] --catalog is required (or export IDENTITY_CATALOG first).")
        return 2
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        resolved = resolve_identity(args.identity_id, repo_catalog_path, catalog_path)
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity context: {exc}")
        return 2

    if not args.target_branch:
        args.target_branch = _git_current_branch()
    if not args.release_head_sha:
        args.release_head_sha = _git_head_sha()

    preferred_pack = str(resolved.get("resolved_pack_path") or resolved.get("pack_path") or "")
    report_path = Path(args.execution_report).expanduser().resolve() if args.execution_report else _latest_report(
        args.identity_id,
        os.environ.get("IDENTITY_HOME", ""),
        preferred_pack,
    )
    instance_status, instance_detail = _instance_plane_status(args, report_path)
    repo_status, repo_detail = _repo_plane_status(args, resolved)
    release_status, release_detail = _release_plane_status(args)

    payload = {
        "target_branch": args.target_branch,
        "release_head_sha": args.release_head_sha,
        "required_gates_run_id": args.required_gates_run_id,
        "run_url": args.run_url,
        "workflow_file_sha": args.workflow_file_sha,
        "required_checks_set": release_detail.get("required_checks_set", []),
        "instance_plane_status": instance_status,
        "repo_plane_status": repo_status,
        "release_plane_status": release_status,
        "identity_context": {
            "identity_id": args.identity_id,
            "source_layer": resolved.get("source_layer"),
            "catalog_path": resolved.get("catalog_path"),
            "pack_path": resolved.get("pack_path"),
            "resolved_scope": resolved.get("resolved_scope"),
            "resolved_pack_path": resolved.get("resolved_pack_path"),
            "conflict_detected": resolved.get("conflict_detected"),
        },
        "instance_plane_detail": instance_detail,
        "repo_plane_detail": repo_detail,
        "release_plane_detail": release_detail,
    }

    overall = "Conditional Go"
    if instance_status == "CLOSED" and repo_status == "CLOSED" and release_status == "CLOSED":
        overall = "Full Go"
    payload["overall_release_decision"] = overall
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] wrote: {out}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"overall_release_decision={overall}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
