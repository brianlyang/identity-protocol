#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any

import yaml

from resolve_identity_context import collect_protocol_evidence, default_identity_home


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_pack(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path)
        if p.exists():
            return p
    legacy = Path("identity") / identity_id
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"identity pack not found: {identity_id}")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str], log_dir: Path, run_id: str, idx: int) -> dict[str, Any]:
    start = datetime.now(timezone.utc)
    t0 = time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    end = datetime.now(timezone.utc)
    elapsed_ms = int((time() - t0) * 1000)
    log_path = log_dir / f"{run_id}-check-{idx:02d}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_content = (
        f"$ {' '.join(cmd)}\n"
        f"[exit_code] {p.returncode}\n"
        f"[started_at] {start.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"[ended_at] {end.strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
        f"[stdout]\n{p.stdout}\n"
        f"[stderr]\n{p.stderr}\n"
    )
    log_path.write_text(log_content, encoding="utf-8")
    log_sha256 = _sha256_file(log_path)
    return {
        "command": " ".join(cmd),
        "cmd": " ".join(cmd),
        "code": p.returncode,
        "ok": p.returncode == 0,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
        "started_at": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ended_at": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_ms": elapsed_ms,
        "exit_code": p.returncode,
        "log_path": str(log_path),
        "sha256": log_sha256,
    }


def _resolve_git_range() -> tuple[str, str]:
    def _git(cmd: list[str]) -> str:
        p = subprocess.run(["git", *cmd], capture_output=True, text=True)
        return (p.stdout or "").strip() if p.returncode == 0 else ""

    base = os.environ.get("PR_BASE_SHA") or os.environ.get("GITHUB_BASE_SHA") or os.environ.get("PUSH_BEFORE_SHA") or os.environ.get("GITHUB_EVENT_BEFORE") or ""
    head = os.environ.get("PR_HEAD_SHA") or os.environ.get("GITHUB_SHA") or ""
    if not head:
        head = _git(["rev-parse", "HEAD"])
    if not base:
        base = _git(["rev-parse", "HEAD~1"])
    return base or "HEAD~1", head or "HEAD"


def _build_validator_cmd(check: str, identity_id: str, catalog_path: str) -> list[str]:
    if not check.startswith("scripts/"):
        return ["python3", check]
    cmd = ["python3", check]
    if check.endswith("validate_changelog_updated.py"):
        base, head = _resolve_git_range()
        return ["python3", check, "--base", base, "--head", head]
    if check.endswith("validate_identity_self_upgrade_enforcement.py"):
        base, head = _resolve_git_range()
        return ["python3", check, "--identity-id", identity_id, "--base", base, "--head", head]
    if check.endswith("validate_identity_manifest.py") or check.endswith("compile_identity_runtime.py"):
        return cmd
    # most validators are identity scoped
    if "--identity-id" not in check:
        cmd += ["--identity-id", identity_id]
    if check.startswith("scripts/validate_") and "--catalog" not in check:
        cmd += ["--catalog", catalog_path]
    if check.endswith("validate_identity_collab_trigger.py"):
        cmd += ["--self-test"]
    if check.endswith("validate_agent_handoff_contract.py"):
        cmd += ["--self-test"]
    if check.endswith("validate_identity_knowledge_contract.py"):
        cmd += ["--self-test"]
    if check.endswith("validate_identity_experience_feedback.py"):
        cmd += ["--self-test"]
    return cmd


def _needs_upgrade(metrics: dict[str, Any], thresholds: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    misroute = float(metrics.get("misroute_rate", 0))
    replay_fail = max(0.0, 100.0 - float(metrics.get("replay_success_rate", 100.0)))
    first_pass = float(metrics.get("first_pass_success_rate", 100.0))

    if misroute >= float(thresholds.get("misroute_rate_percent", 999)):
        reasons.append(f"misroute_rate {misroute} >= threshold {thresholds.get('misroute_rate_percent')}")
    if replay_fail >= float(thresholds.get("replay_failure_rate_percent", 999)):
        reasons.append(f"replay_failure_rate {replay_fail} >= threshold {thresholds.get('replay_failure_rate_percent')}")
    if (100.0 - first_pass) >= float(thresholds.get("first_pass_success_drop_percent", 999)):
        reasons.append(
            f"first_pass_success_drop {100.0-first_pass} >= threshold {thresholds.get('first_pass_success_drop_percent')}"
        )
    return (len(reasons) > 0), reasons


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _path_allowed(path: str, allowlist: list[str], denylist: list[str]) -> tuple[bool, str]:
    for pat in denylist:
        if fnmatch.fnmatch(path, pat):
            return False, f"denied by pattern: {pat}"
    for pat in allowlist:
        if fnmatch.fnmatch(path, pat):
            return True, f"allowed by pattern: {pat}"
    return False, "not matched by allowlist"


def _append_task_history(history_path: Path, line: str) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(f"\n- {line}\n")


def _resolve_local_runtime_path(raw: str, *, identity_id: str, pack: Path, identity_home: Path) -> Path:
    val = (raw or "").strip()
    if not val:
        return Path("")
    p = Path(val).expanduser()
    if p.is_absolute():
        return p
    token = "{identity_id}"
    if token in val:
        val = val.replace(token, identity_id)
    pref_local = f"identity/runtime/local/{identity_id}/"
    if val.startswith(pref_local):
        return (pack / val[len(pref_local) :]).resolve()
    pref_identity = f"identity/{identity_id}/"
    if val.startswith(pref_identity):
        return (pack / val[len(pref_identity) :]).resolve()
    if val.startswith("identity/runtime/local/"):
        rel = val[len("identity/runtime/local/") :].split("/", 1)
        if rel and rel[0] == identity_id and len(rel) > 1:
            return (pack / rel[1]).resolve()
        # fallback: map under identity_home for non-pack-scoped local runtime artifacts
        return (identity_home / val[len("identity/runtime/local/") :]).resolve()
    return p.resolve()


def _append_writeback_or_defer(
    *,
    rulebook_path: Path,
    history_path: Path,
    rulebook_row: dict[str, Any],
    history_line: str,
    out_dir: Path,
    run_id: str,
    identity_id: str,
    mode: str,
) -> dict[str, Any]:
    completed: list[str] = []
    try:
        _append_jsonl(rulebook_path, rulebook_row)
        completed.append("rulebook")
        _append_task_history(history_path, history_line)
        completed.append("task_history")
        return {
            "status": "WRITTEN",
            "history_contains_run_id": True,
            "deferred_report_path": "",
            "notes": "writeback appended successfully",
            "completed_steps": completed,
            "error": "",
        }
    except (PermissionError, OSError) as exc:
        deferred = {
            "run_id": run_id,
            "identity_id": identity_id,
            "mode": mode,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reason": "permission_or_filesystem_blocked",
            "error": str(exc),
            "completed_steps": completed,
            "intended_writeback": {
                "rulebook_path": str(rulebook_path),
                "rulebook_row": rulebook_row,
                "task_history_path": str(history_path),
                "task_history_line": history_line,
            },
            "operator_action": (
                "rerun with writable runtime root or elevated permission, then "
                "re-append RULEBOOK/TASK_HISTORY and re-run validate_identity_experience_writeback.py"
            ),
        }
        deferred_path = out_dir / f"{run_id}-writeback-deferred.json"
        _write_json(deferred_path, deferred)
        return {
            "status": "DEFERRED_PERMISSION_BLOCKED",
            "history_contains_run_id": "task_history" in completed,
            "deferred_report_path": str(deferred_path),
            "notes": "writeback deferred due to filesystem permission/sandbox constraint",
            "completed_steps": completed,
            "error": str(exc),
        }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Execute identity upgrade cycle using metrics + arbitration thresholds (safe-auto/review-required)."
    )
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--mode", choices=["review-required", "safe-auto"], default="review-required")
    ap.add_argument("--metrics-path", default="", help="optional route metrics artifact path override")
    ap.add_argument("--out-dir", default="identity/runtime/reports")
    ap.add_argument("--protocol-root", default="")
    ap.add_argument("--protocol-mode", choices=["mode_a_shared", "mode_b_standalone"], default="mode_a_shared")
    ap.add_argument(
        "--allow-deferred-writeback",
        action="store_true",
        help="allow process to return success when writeback is deferred by permission/sandbox constraints",
    )
    args = ap.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = f"identity-upgrade-exec-{args.identity_id}-{int(datetime.now(timezone.utc).timestamp())}"
    identity_home = default_identity_home()

    if args.allow_deferred_writeback and os.environ.get("CI"):
        print("[FAIL] --allow-deferred-writeback is forbidden in CI/release environments")
        return 2

    pack = _resolve_pack(Path(args.catalog), args.identity_id)
    current_task_path = pack / "CURRENT_TASK.json"
    task = _load_json(current_task_path)

    arb = task.get("capability_arbitration_contract") or {}
    thresholds = (arb.get("trigger_thresholds") or {}) if isinstance(arb, dict) else {}
    raw_metrics_path = (
        str(args.metrics_path).strip()
        if str(args.metrics_path).strip()
        else str((task.get("route_quality_contract") or {}).get("metrics_output_path", "")).strip()
    )
    if not raw_metrics_path:
        raw_metrics_path = f"{pack}/metrics/{args.identity_id}-route-quality.json"
    metrics_path = _resolve_local_runtime_path(
        raw_metrics_path,
        identity_id=args.identity_id,
        pack=pack,
        identity_home=identity_home,
    )
    if not metrics_path.exists():
        raise FileNotFoundError(f"metrics artifact not found: {metrics_path}")
    metrics = _load_json(metrics_path)

    upgrade_required, reasons = _needs_upgrade(metrics, thresholds)

    safe_auto = ((arb.get("safe_auto_patch_surface") or {}) if isinstance(arb, dict) else {}) or {}
    touched_paths = [
        str(pack / "RULEBOOK.jsonl"),
        str(pack / "TASK_HISTORY.md"),
        f"identity/runtime/logs/arbitration/{args.identity_id}-{run_id}.json",
    ]
    if args.mode == "safe-auto":
        patch_surface = touched_paths
    else:
        patch_surface = [
            str(current_task_path),
            str(pack / "IDENTITY_PROMPT.md"),
            str(pack / "RULEBOOK.jsonl"),
            str(pack / "TASK_HISTORY.md"),
        ]

    # Always produce patch plan (even if no trigger) for audit clarity
    patch_plan = {
        "run_id": run_id,
        "identity_id": args.identity_id,
        "generated_at": now,
        "mode": args.mode,
        "upgrade_required": upgrade_required,
        "trigger_reasons": reasons,
        "patch_surface": patch_surface,
        "planned_actions": [
            "append arbitration decision record",
            "append rulebook learning row",
            "append TASK_HISTORY upgrade note",
            "run required validators and replay checks",
        ],
    }
    protocol = collect_protocol_evidence(args.protocol_root, args.protocol_mode)
    patch_plan.update(
        {
            "protocol_mode": protocol["protocol_mode"],
            "protocol_root": protocol["protocol_root"],
            "protocol_commit_sha": protocol["protocol_commit_sha"],
            "protocol_ref": protocol["protocol_ref"],
            "identity_home": str(identity_home),
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        }
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / f"{run_id}-patch-plan.json"
    _write_json(plan_path, patch_plan)

    actions_taken: list[str] = [f"patch_plan_written:{plan_path}"]
    artifacts = [str(plan_path), str(metrics_path)]
    experience_writeback: dict[str, Any] = {
        "required": bool(upgrade_required),
        "status": "SKIPPED",
        "mode": args.mode,
        "rulebook_path": str(pack / "RULEBOOK.jsonl"),
        "task_history_path": str(pack / "TASK_HISTORY.md"),
        "rule_entry_id": "",
        "history_contains_run_id": False,
        "notes": "",
    }
    writeback_paths = [str(pack / "RULEBOOK.jsonl"), str(pack / "TASK_HISTORY.md")]

    if upgrade_required and args.mode == "safe-auto":
        if safe_auto.get("enforce_path_policy") is True:
            allowlist = [str(x) for x in (safe_auto.get("allowlist") or [])]
            denylist = [str(x) for x in (safe_auto.get("denylist") or [])]
            violations: list[dict[str, str]] = []
            for pth in touched_paths:
                ok, reason = _path_allowed(pth, allowlist, denylist)
                if not ok:
                    violations.append({"path": pth, "reason": reason})
            if violations:
                report = {
                    "run_id": run_id,
                    "identity_id": args.identity_id,
                    "mode": args.mode,
                    "upgrade_required": upgrade_required,
                    "trigger_reasons": reasons,
                    "actions_taken": actions_taken,
                    "checks": [],
                    "artifacts": artifacts,
                    "all_ok": False,
                    "path_policy_violations": violations,
                }
                report_path = out_dir / f"{run_id}.json"
                _write_json(report_path, report)
                print(f"report={report_path}")
                print("upgrade_required=True")
                print("all_ok=False")
                print("next_action=blocked_by_safe_auto_path_policy")
                return 3

        # 1) append arbitration decision record
        decision = {
            "arbitration_id": f"{run_id}-arb",
            "task_id": str(task.get("task_id", "")),
            "identity_id": args.identity_id,
            "conflict_pair": "routing_vs_learning",
            "inputs": {
                "metrics": {
                    "misroute_rate": metrics.get("misroute_rate"),
                    "replay_success_rate": metrics.get("replay_success_rate"),
                    "first_pass_success_rate": metrics.get("first_pass_success_rate"),
                },
                "thresholds": thresholds,
            },
            "decision": "trigger_identity_update_cycle",
            "impact": "force patch/validate/replay cycle",
            "rationale": "; ".join(reasons) if reasons else "threshold trigger",
            "decided_at": now,
        }
        decision_path = Path(f"identity/runtime/logs/arbitration/{args.identity_id}-{run_id}.json")
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(decision_path, {"records": [decision]})
        actions_taken.append("arbitration_record_written")
        artifacts.append(str(decision_path))

        # 2/3) append writeback rows (or defer with explicit evidence when blocked)
        rulebook_path = pack / "RULEBOOK.jsonl"
        history_path = pack / "TASK_HISTORY.md"
        wb = _append_writeback_or_defer(
            rulebook_path=rulebook_path,
            history_path=history_path,
            rulebook_row={
                "rule_id": f"{run_id}-auto-upgrade",
                "type": "negative",
                "trigger": "arbitration_threshold_hit",
                "action": "execute_identity_upgrade_safe_auto",
                "evidence_run_id": run_id,
                "scope": "identity_update_cycle",
                "confidence": 0.75,
                "updated_at": now,
            },
            history_line=f"{now} | auto-upgrade trigger | run_id={run_id} | mode=safe-auto | reasons={'; '.join(reasons)}",
            out_dir=out_dir,
            run_id=run_id,
            identity_id=args.identity_id,
            mode=args.mode,
        )
        if wb["status"] == "WRITTEN":
            actions_taken.append("rulebook_row_appended")
            actions_taken.append("task_history_appended")
        else:
            actions_taken.append("writeback_deferred_permission_blocked")
            deferred_path = str(wb.get("deferred_report_path", ""))
            if deferred_path:
                artifacts.append(deferred_path)
        experience_writeback.update(
            {
                "status": wb["status"],
                "rule_entry_id": f"{run_id}-auto-upgrade",
                "history_contains_run_id": bool(wb.get("history_contains_run_id")),
                "notes": str(wb.get("notes", "")),
                "deferred_report_path": str(wb.get("deferred_report_path", "")),
                "error": str(wb.get("error", "")),
            }
        )

    # Run required validators + replay-equivalent gate checks
    required_checks = (
        task.get("identity_update_lifecycle_contract", {})
        .get("validation_contract", {})
        .get("required_checks", [])
    )
    if not isinstance(required_checks, list) or not required_checks:
        required_checks = [
            "scripts/validate_identity_upgrade_prereq.py",
            "scripts/validate_identity_runtime_contract.py",
            "scripts/validate_identity_update_lifecycle.py",
            "scripts/validate_identity_capability_arbitration.py",
        ]
    check_cmds = [_build_validator_cmd(chk, args.identity_id, args.catalog) for chk in required_checks]
    log_dir = Path(f"identity/runtime/logs/upgrade/{args.identity_id}")
    checks = [_run(cmd, log_dir=log_dir, run_id=run_id, idx=i + 1) for i, cmd in enumerate(check_cmds)]

    all_ok = all(c["ok"] for c in checks)
    if upgrade_required and args.mode == "review-required" and all_ok:
        rulebook_path = pack / "RULEBOOK.jsonl"
        history_path = pack / "TASK_HISTORY.md"
        rule_id = f"{run_id}-review-required-upgrade"
        wb = _append_writeback_or_defer(
            rulebook_path=rulebook_path,
            history_path=history_path,
            rulebook_row={
                "rule_id": rule_id,
                "type": "positive",
                "trigger": "review_required_upgrade_validated",
                "action": "preserve_trigger_patch_validate_replay_chain",
                "evidence_run_id": run_id,
                "scope": "identity_update_cycle",
                "confidence": 0.9,
                "updated_at": now,
            },
            history_line=(
                f"{now} | review-required upgrade validated | run_id={run_id} | mode=review-required "
                f"| checks_passed={len(checks)} | reasons={'; '.join(reasons) if reasons else 'none'}"
            ),
            out_dir=out_dir,
            run_id=run_id,
            identity_id=args.identity_id,
            mode=args.mode,
        )
        if wb["status"] == "WRITTEN":
            actions_taken.append("rulebook_row_appended_review_required")
            actions_taken.append("task_history_appended_review_required")
            artifacts.append(str(rulebook_path))
            artifacts.append(str(history_path))
        else:
            actions_taken.append("writeback_deferred_permission_blocked_review_required")
            deferred_path = str(wb.get("deferred_report_path", ""))
            if deferred_path:
                artifacts.append(deferred_path)
        experience_writeback.update(
            {
                "status": wb["status"],
                "rule_entry_id": rule_id,
                "history_contains_run_id": bool(wb.get("history_contains_run_id")),
                "notes": str(wb.get("notes", "")),
                "deferred_report_path": str(wb.get("deferred_report_path", "")),
                "error": str(wb.get("error", "")),
            }
        )
    elif upgrade_required:
        experience_writeback.update(
            {
                "status": "MISSING",
                "notes": "upgrade was required but writeback not appended (run failed or policy blocked)",
            }
        )
    else:
        experience_writeback.update(
            {
                "required": False,
                "status": "NOT_REQUIRED",
                "notes": "thresholds not triggered; no upgrade writeback required",
            }
        )

    if upgrade_required and str(experience_writeback.get("status", "")) != "WRITTEN":
        writeback_status = str(experience_writeback.get("status", ""))
        checks.append(
            {
                "command": "identity_writeback_enforcement",
                "cmd": "identity_writeback_enforcement",
                "code": 1,
                "ok": False,
                "stdout": "",
                "stderr": (
                    f"writeback enforcement failed: status={writeback_status}; "
                    "runtime writeback not fully committed"
                ),
                "started_at": now,
                "ended_at": now,
                "duration_ms": 0,
                "exit_code": 1,
                "log_path": "",
                "sha256": "",
            }
        )
        all_ok = False if not args.allow_deferred_writeback else all_ok
        if args.allow_deferred_writeback:
            actions_taken.append("writeback_deferred_allowed_by_flag")

    report = {
        "run_id": run_id,
        "identity_id": args.identity_id,
        "generated_at": now,
        "creator_invocation": {
            "tool": "identity-creator",
            "mode": "update",
            "entrypoint": "scripts/execute_identity_upgrade.py",
            "base_contract": "identity_update_lifecycle_contract",
            "run_id": run_id,
        },
        "mode": args.mode,
        "execution_context": {
            "generated_by": "ci" if os.environ.get("CI") else "local",
            "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "github_sha": os.environ.get("GITHUB_SHA", ""),
        },
        "upgrade_required": upgrade_required,
        "trigger_reasons": reasons,
        "actions_taken": actions_taken,
        "checks": checks,
        "check_results": checks,
        "artifacts": artifacts,
        "experience_writeback": experience_writeback,
        "writeback_paths": writeback_paths,
        "writeback_status": str(experience_writeback.get("status", "")),
        "writeback_rule_id": str(experience_writeback.get("rule_entry_id", "")),
        "all_ok": all_ok,
    }
    report.update(
        {
            "protocol_mode": protocol["protocol_mode"],
            "protocol_root": protocol["protocol_root"],
            "protocol_commit_sha": protocol["protocol_commit_sha"],
            "protocol_ref": protocol["protocol_ref"],
            "identity_home": str(identity_home),
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        }
    )
    report_path = out_dir / f"{run_id}.json"
    _write_json(report_path, report)

    print(f"report={report_path}")
    print(f"upgrade_required={upgrade_required}")
    print(f"all_ok={all_ok}")
    if args.mode == "review-required" and upgrade_required:
        print("next_action=review_required: apply patch plan via PR")
    elif args.mode == "safe-auto" and upgrade_required:
        print("next_action=safe_auto_applied_and_validated")
    else:
        print("next_action=no_upgrade_triggered")

    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
