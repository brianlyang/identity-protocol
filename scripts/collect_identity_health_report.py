#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CHECKS: list[tuple[str, list[str]]] = [
    ("scope_resolution", ["python3", "scripts/validate_identity_scope_resolution.py"]),
    ("scope_isolation", ["python3", "scripts/validate_identity_scope_isolation.py"]),
    ("scope_persistence", ["python3", "scripts/validate_identity_scope_persistence.py"]),
    ("state_consistency", ["python3", "scripts/validate_identity_state_consistency.py"]),
    ("instance_isolation", ["python3", "scripts/validate_identity_instance_isolation.py"]),
    ("runtime_contract", ["python3", "scripts/validate_identity_runtime_contract.py"]),
    ("role_binding", ["python3", "scripts/validate_identity_role_binding.py"]),
    ("update_lifecycle", ["python3", "scripts/validate_identity_update_lifecycle.py"]),
    ("install_safety", ["python3", "scripts/validate_identity_install_safety.py"]),
    ("tool_installation", ["python3", "scripts/validate_identity_tool_installation.py"]),
    ("install_provenance", ["python3", "scripts/validate_identity_install_provenance.py"]),
    ("vendor_api_discovery", ["python3", "scripts/validate_identity_vendor_api_discovery.py"]),
    ("vendor_api_solution", ["python3", "scripts/validate_identity_vendor_api_solution.py"]),
    (
        "writeback_continuity",
        [
            "python3",
            "scripts/validate_writeback_continuity.py",
            "--operation",
            "scan",
            "--json-only",
        ],
    ),
    (
        "post_execution_mandatory",
        [
            "python3",
            "scripts/validate_post_execution_mandatory.py",
            "--operation",
            "scan",
            "--json-only",
        ],
    ),
    (
        "protocol_baseline_freshness",
        [
            "python3",
            "scripts/validate_identity_protocol_baseline_freshness.py",
            "--baseline-policy",
            "warn",
            "--json-only",
        ],
    ),
    ("experience_feedback_governance", ["python3", "scripts/validate_identity_experience_feedback_governance.py"]),
    ("capability_arbitration", ["python3", "scripts/validate_identity_capability_arbitration.py"]),
    ("ci_enforcement", ["python3", "scripts/validate_identity_ci_enforcement.py"]),
]

SUGGESTIONS = {
    "scope_resolution": "Run `identity_creator heal --identity-id <id> --apply` to arbitrate duplicate paths and lock canonical scope.",
    "scope_isolation": "Check for cross-identity/shared pack paths, then run scan/adopt/lock.",
    "scope_persistence": "Ensure runtime identities are USER/REPO scoped and fixtures stay SYSTEM-only.",
    "state_consistency": "Run `identity_creator activate` for intended identity to re-sync catalog and META status.",
    "instance_isolation": "Fix CURRENT_TASK path patterns to identity-scoped locations; remove cross-identity fallbacks.",
    "runtime_contract": "Repair CURRENT_TASK contract fields, then rerun validate.",
    "role_binding": "Regenerate role-binding evidence and re-run activation transaction.",
    "update_lifecycle": "Repair patch/replay/required checks in CURRENT_TASK and ensure required evidence files exist.",
    "install_safety": "Generate/refresh install report via identity_installer plan/install/verify.",
    "tool_installation": "Produce tool installation closure report with plan/approval/execution/healthcheck/fallback/rollback refs.",
    "install_provenance": "Generate identity-installer provenance chain reports (plan/dry-run/install/verify).",
    "vendor_api_discovery": "Record vendor/API discovery closure with official contract refs and trust tier/provenance evidence.",
    "vendor_api_solution": "Complete solution option matrix with exactly one selected option and rollback/fallback refs.",
    "writeback_continuity": "Regenerate update execution report and ensure writeback_mode/degrade_reason/risk_level/next_recovery_action satisfy continuity contract.",
    "post_execution_mandatory": "Ensure post-execution mandatory fields and recovery actions are complete in execution report; rerun update and validate.",
    "protocol_baseline_freshness": "Run identity_creator update to regenerate execution report on current protocol baseline commit.",
    "experience_feedback_governance": "Refresh feedback sample/log linkage for target identity only.",
    "capability_arbitration": "Refresh route quality metrics and arbitration sample for current identity.",
    "ci_enforcement": "Align evidence and CI execution metadata with protocol requirements.",
}

ERR_RE = re.compile(r"\b(IP-[A-Z0-9-]+)\b")


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout or "", p.stderr or ""


def _extract_error_code(out: str, err: str) -> str:
    text = f"{out}\n{err}".strip()
    m = ERR_RE.search(text)
    return m.group(1) if m else ""


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect identity health report with actionable recommendations.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="")
    ap.add_argument("--out-dir", default="/tmp/identity-health-reports")
    ap.add_argument("--enforce-pass", action="store_true", help="return non-zero if any check fails")
    args = ap.parse_args()

    catalog = args.catalog.strip() or str((Path.home() / ".codex" / "identity" / "catalog.local.yaml").resolve())

    checks: list[dict[str, Any]] = []
    for name, base in DEFAULT_CHECKS:
        cmd = [*base, "--identity-id", args.identity_id]
        if name == "state_consistency":
            cmd = [*base, "--catalog", catalog]
        elif name == "protocol_baseline_freshness":
            cmd += ["--catalog", catalog, "--repo-catalog", args.repo_catalog]
        elif name in {"writeback_continuity", "post_execution_mandatory"}:
            cmd += ["--catalog", catalog, "--repo-catalog", args.repo_catalog]
        elif name in {"scope_resolution", "scope_isolation", "scope_persistence"}:
            cmd += ["--catalog", catalog, "--repo-catalog", args.repo_catalog]
            if args.scope:
                cmd += ["--scope", args.scope]
        else:
            cmd += ["--catalog", catalog]

        rc, out, err = _run(cmd)
        status = "PASS" if rc == 0 else "FAIL"
        error_code = _extract_error_code(out, err)
        if name == "protocol_baseline_freshness":
            payload = _parse_json_payload(out) or {}
            baseline_status = str(payload.get("baseline_status", "")).strip().upper()
            if baseline_status in {"PASS", "WARN", "FAIL"}:
                status = baseline_status
            baseline_code = str(payload.get("baseline_error_code", "")).strip()
            if baseline_code:
                error_code = baseline_code
        elif name == "writeback_continuity":
            payload = _parse_json_payload(out) or {}
            continuity_status = str(payload.get("writeback_continuity_status", "")).strip().upper()
            if continuity_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif continuity_status == "FAIL_REQUIRED":
                status = "FAIL"
            continuity_code = str(payload.get("error_code", "")).strip()
            if continuity_code:
                error_code = continuity_code
        elif name == "post_execution_mandatory":
            payload = _parse_json_payload(out) or {}
            post_exec_status = str(payload.get("post_execution_mandatory_status", "")).strip().upper()
            if post_exec_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif post_exec_status == "FAIL_REQUIRED":
                status = "FAIL"
            post_exec_code = str(payload.get("error_code", "")).strip()
            if post_exec_code:
                error_code = post_exec_code

        checks.append(
            {
                "name": name,
                "command": cmd,
                "rc": rc,
                "ok": status != "FAIL",
                "status": status,
                "error_code": error_code,
                "stdout": out,
                "stderr": err,
                "suggestion": "" if status == "PASS" else SUGGESTIONS.get(name, "Review validator output and fix failing contract fields."),
            }
        )

    failed = [c for c in checks if str(c.get("status", "")).upper() == "FAIL"]
    warns = [c for c in checks if str(c.get("status", "")).upper() == "WARN"]
    if failed:
        overall = "FAIL"
    elif warns:
        overall = "WARN"
    else:
        overall = "PASS"
    now = datetime.now(timezone.utc)
    report = {
        "report_id": f"identity-health-{args.identity_id}-{int(now.timestamp())}",
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "identity_id": args.identity_id,
        "catalog_path": str(Path(catalog).expanduser().resolve()),
        "scope": args.scope,
        "overall_status": overall,
        "warning_count": len(warns),
        "failed_count": len(failed),
        "checks": checks,
        "recommendations": [
            {
                "check": c["name"],
                "action": c["suggestion"],
                "status": c.get("status"),
                "error_code": c.get("error_code"),
            }
            for c in checks
            if str(c.get("status", "")).upper() in {"FAIL", "WARN"}
        ],
    }

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{report['report_id']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"report={report_path}")
    print(f"overall_status={overall}")
    print(f"warning_count={len(warns)}")
    print(f"failed_count={len(failed)}")
    if failed:
        for c in failed:
            print(f"- fail:{c['name']} -> {c['suggestion']}")
    if warns:
        for c in warns:
            print(f"- warn:{c['name']} -> {c['suggestion']}")

    if args.enforce_pass and failed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
