#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
    "experience_feedback_governance": "Refresh feedback sample/log linkage for target identity only.",
    "capability_arbitration": "Refresh route quality metrics and arbitration sample for current identity.",
    "ci_enforcement": "Align evidence and CI execution metadata with protocol requirements.",
}


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout or "", p.stderr or ""


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
        elif name in {"scope_resolution", "scope_isolation", "scope_persistence"}:
            cmd += ["--catalog", catalog, "--repo-catalog", args.repo_catalog]
            if args.scope:
                cmd += ["--scope", args.scope]
        else:
            cmd += ["--catalog", catalog]

        rc, out, err = _run(cmd)
        checks.append(
            {
                "name": name,
                "command": cmd,
                "rc": rc,
                "ok": rc == 0,
                "stdout": out,
                "stderr": err,
                "suggestion": "" if rc == 0 else SUGGESTIONS.get(name, "Review validator output and fix failing contract fields."),
            }
        )

    failed = [c for c in checks if not c["ok"]]
    overall = "PASS" if not failed else "FAIL"
    now = datetime.now(timezone.utc)
    report = {
        "report_id": f"identity-health-{args.identity_id}-{int(now.timestamp())}",
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "identity_id": args.identity_id,
        "catalog_path": str(Path(catalog).expanduser().resolve()),
        "scope": args.scope,
        "overall_status": overall,
        "failed_count": len(failed),
        "checks": checks,
        "recommendations": [
            {
                "check": c["name"],
                "action": c["suggestion"],
            }
            for c in failed
        ],
    }

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{report['report_id']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"report={report_path}")
    print(f"overall_status={overall}")
    print(f"failed_count={len(failed)}")
    if failed:
        for c in failed:
            print(f"- fail:{c['name']} -> {c['suggestion']}")

    if args.enforce_pass and failed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
