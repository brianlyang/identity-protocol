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
        "actor_session_binding",
        [
            "python3",
            "scripts/validate_actor_session_binding.py",
            "--operation",
            "scan",
            "--json-only",
        ],
    ),
    (
        "implicit_switch_guard",
        [
            "python3",
            "scripts/validate_no_implicit_switch.py",
            "--operation",
            "scan",
            "--json-only",
        ],
    ),
    (
        "cross_actor_isolation",
        [
            "python3",
            "scripts/validate_cross_actor_isolation.py",
            "--operation",
            "scan",
            "--json-only",
        ],
    ),
    (
        "pointer_drift_guard",
        [
            "python3",
            "scripts/validate_identity_session_pointer_consistency.py",
            "--require-mirror",
        ],
    ),
    (
        "session_refresh_status",
        [
            "python3",
            "scripts/validate_identity_session_refresh_status.py",
            "--operation",
            "scan",
            "--baseline-policy",
            "warn",
            "--json-only",
        ],
    ),
    (
        "semantic_routing_guard",
        [
            "python3",
            "scripts/validate_semantic_routing_guard.py",
            "--operation",
            "scan",
            "--json-only",
        ],
    ),
    (
        "vendor_namespace_separation",
        [
            "python3",
            "scripts/validate_vendor_namespace_separation.py",
            "--operation",
            "scan",
            "--json-only",
        ],
    ),
    (
        "protocol_feedback_sidecar",
        [
            "python3",
            "scripts/validate_protocol_feedback_sidecar_contract.py",
            "--operation",
            "scan",
            "--json-only",
        ],
    ),
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
    (
        "protocol_version_alignment",
        [
            "python3",
            "scripts/validate_identity_protocol_version_alignment.py",
            "--operation",
            "scan",
            "--alignment-policy",
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
    "actor_session_binding": "Run `validate_actor_session_binding --operation validate` and repair actor binding tuples for current actor/session.",
    "implicit_switch_guard": "Run `validate_no_implicit_switch --operation validate` and reconcile unexpected switch reports/identity drift.",
    "cross_actor_isolation": "Run `validate_cross_actor_isolation --operation validate` and eliminate cross-actor identity contamination before closure.",
    "pointer_drift_guard": "Run `validate_identity_session_pointer_consistency --require-mirror` and fix canonical/mirror pointer drift.",
    "session_refresh_status": "Run refresh_identity_session_status and repair actor binding/session pointer drift before re-validating health.",
    "semantic_routing_guard": "Add semantic_routing_guard_contract_v1 evidence and ensure intent_domain/intent_confidence/classifier_reason are present in feedback batches.",
    "vendor_namespace_separation": "Split protocol feedback artifacts into protocol-vendor-intel and business-partner-intel namespaces; eliminate legacy vendor-intel default writes.",
    "protocol_feedback_sidecar": "Align protocol_feedback_sidecar_contract_v1 (default non-blocking + auditable P0 escalation); resolve blocking IP-WRB/IP-SEM violations before strict gates.",
    "writeback_continuity": "Regenerate update execution report and ensure writeback_mode/degrade_reason/risk_level/next_recovery_action satisfy continuity contract.",
    "post_execution_mandatory": "Ensure post-execution mandatory fields and recovery actions are complete in execution report; rerun update and validate.",
    "protocol_baseline_freshness": "Run identity_creator update to regenerate execution report on current protocol baseline commit.",
    "protocol_version_alignment": "Run identity_creator update (or refresh execution report) and resolve prompt/binding tuple mismatches before release closure.",
    "experience_feedback_governance": "Refresh feedback sample/log linkage for target identity only.",
    "capability_arbitration": "Refresh route quality metrics and arbitration sample for current identity.",
    "ci_enforcement": "Align evidence and CI execution metadata with protocol requirements.",
}

ERR_RE = re.compile(r"\b(IP-[A-Z0-9-]+)\b")
ACTOR_RISK_FIELDS = (
    "actor_binding_integrity",
    "actor_lease_freshness",
    "implicit_switch_guard",
    "pointer_drift_guard",
)


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout or "", p.stderr or ""


def _extract_error_code(out: str, err: str) -> str:
    text = f"{out}\n{err}".strip()
    m = ERR_RE.search(text)
    return m.group(1) if m else ""


def _override_operation(cmd: list[str], operation: str) -> list[str]:
    if not operation:
        return cmd
    out = list(cmd)
    if "--operation" in out:
        idx = out.index("--operation")
        if idx + 1 < len(out):
            out[idx + 1] = operation
            return out
    out.extend(["--operation", operation])
    return out


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
    ap.add_argument(
        "--operation",
        default="scan",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
    )
    ap.add_argument("--execution-report", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--out-dir", default="/tmp/identity-health-reports")
    ap.add_argument("--enforce-pass", action="store_true", help="return non-zero if any check fails")
    args = ap.parse_args()

    catalog = args.catalog.strip() or str((Path.home() / ".codex" / "identity" / "catalog.local.yaml").resolve())
    execution_report = str(args.execution_report or "").strip()
    actor_id = str(args.actor_id or "").strip()

    checks: list[dict[str, Any]] = []
    for name, base in DEFAULT_CHECKS:
        cmd = [*base, "--identity-id", args.identity_id]
        cmd = _override_operation(cmd, args.operation if name not in {"state_consistency"} else "")
        if name == "state_consistency":
            cmd = [*base, "--catalog", catalog]
        elif name in {"protocol_baseline_freshness", "protocol_version_alignment"}:
            cmd += ["--catalog", catalog, "--repo-catalog", args.repo_catalog]
            if execution_report:
                cmd += ["--execution-report", execution_report]
        elif name in {"semantic_routing_guard", "vendor_namespace_separation"}:
            cmd += ["--catalog", catalog]
        elif name == "protocol_feedback_sidecar":
            cmd += ["--catalog", catalog, "--repo-catalog", args.repo_catalog]
            if execution_report:
                cmd += ["--report", execution_report]
        elif name in {"writeback_continuity", "post_execution_mandatory"}:
            cmd += ["--catalog", catalog, "--repo-catalog", args.repo_catalog]
            if execution_report:
                cmd += ["--report", execution_report]
        elif name in {"scope_resolution", "scope_isolation", "scope_persistence"}:
            cmd += ["--catalog", catalog, "--repo-catalog", args.repo_catalog]
            if args.scope:
                cmd += ["--scope", args.scope]
        else:
            cmd += ["--catalog", catalog]
        if name == "session_refresh_status":
            if execution_report:
                cmd += ["--execution-report", execution_report]
            if actor_id:
                cmd += ["--actor-id", actor_id]
        if name == "actor_session_binding" and actor_id:
            cmd += ["--actor-id", actor_id]
        if name == "pointer_drift_guard" and actor_id:
            cmd += ["--actor-id", actor_id]

        rc, out, err = _run(cmd)
        status = "PASS" if rc == 0 else "FAIL"
        error_code = _extract_error_code(out, err)
        payload = _parse_json_payload(out) or {}
        if name == "protocol_baseline_freshness":
            baseline_status = str(payload.get("baseline_status", "")).strip().upper()
            if baseline_status in {"PASS", "WARN", "FAIL"}:
                status = baseline_status
            baseline_code = str(payload.get("baseline_error_code", "")).strip()
            if baseline_code:
                error_code = baseline_code
        elif name == "protocol_version_alignment":
            align_status = str(payload.get("protocol_version_alignment_status", "")).strip().upper()
            if align_status == "PASS_REQUIRED":
                status = "PASS"
            elif align_status == "WARN_NON_BLOCKING":
                status = "WARN"
            elif align_status == "FAIL_REQUIRED":
                status = "FAIL"
            align_code = str(payload.get("error_code", "")).strip()
            if align_code:
                error_code = align_code
        elif name == "semantic_routing_guard":
            sem_status = str(payload.get("semantic_routing_status", "")).strip().upper()
            if sem_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif sem_status == "FAIL_REQUIRED":
                status = "FAIL"
            sem_code = str(payload.get("error_code", "")).strip()
            if sem_code:
                error_code = sem_code
        elif name == "vendor_namespace_separation":
            ns_status = str(payload.get("vendor_namespace_status", "")).strip().upper()
            if ns_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif ns_status == "FAIL_REQUIRED":
                status = "FAIL"
            ns_code = str(payload.get("error_code", "")).strip()
            if ns_code:
                error_code = ns_code
        elif name == "protocol_feedback_sidecar":
            sidecar_status = str(payload.get("sidecar_contract_status", "")).strip().upper()
            if sidecar_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif sidecar_status == "WARN_NON_BLOCKING":
                status = "WARN"
            elif sidecar_status == "FAIL_REQUIRED":
                status = "FAIL"
            sidecar_code = str(payload.get("sidecar_error_code", "")).strip()
            if sidecar_code:
                error_code = sidecar_code
        elif name == "session_refresh_status":
            refresh_status = str(payload.get("session_refresh_status", "")).strip().upper()
            if refresh_status == "PASS_REQUIRED":
                status = "PASS"
            elif refresh_status == "WARN_NON_BLOCKING":
                status = "WARN"
            elif refresh_status == "FAIL_REQUIRED":
                status = "FAIL"
            refresh_code = str(payload.get("error_code", "")).strip()
            if refresh_code:
                error_code = refresh_code
        elif name == "writeback_continuity":
            continuity_status = str(payload.get("writeback_continuity_status", "")).strip().upper()
            if continuity_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif continuity_status == "FAIL_REQUIRED":
                status = "FAIL"
            continuity_code = str(payload.get("error_code", "")).strip()
            if continuity_code:
                error_code = continuity_code
        elif name == "post_execution_mandatory":
            post_exec_status = str(payload.get("post_execution_mandatory_status", "")).strip().upper()
            if post_exec_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif post_exec_status == "FAIL_REQUIRED":
                status = "FAIL"
            post_exec_code = str(payload.get("error_code", "")).strip()
            if post_exec_code:
                error_code = post_exec_code
        elif name == "actor_session_binding":
            asb_status = str(payload.get("actor_binding_status", "")).strip().upper()
            if asb_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif asb_status == "WARN_NON_BLOCKING":
                status = "WARN"
            elif asb_status == "FAIL_REQUIRED":
                status = "FAIL"
            asb_code = str(payload.get("error_code", "")).strip()
            if asb_code:
                error_code = asb_code
        elif name == "implicit_switch_guard":
            imp_status = str(payload.get("implicit_switch_status", "")).strip().upper()
            if imp_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif imp_status == "WARN_NON_BLOCKING":
                status = "WARN"
            elif imp_status == "FAIL_REQUIRED":
                status = "FAIL"
            imp_code = str(payload.get("error_code", "")).strip()
            if imp_code:
                error_code = imp_code
        elif name == "cross_actor_isolation":
            x_status = str(payload.get("cross_actor_isolation_status", "")).strip().upper()
            if x_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
                status = "PASS"
            elif x_status == "WARN_NON_BLOCKING":
                status = "WARN"
            elif x_status == "FAIL_REQUIRED":
                status = "FAIL"
            x_code = str(payload.get("error_code", "")).strip()
            if x_code:
                error_code = x_code

        suggestion = "" if status == "PASS" else SUGGESTIONS.get(name, "Review validator output and fix failing contract fields.")
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
                "suggestion": suggestion,
                "payload": payload if payload else {},
            }
        )

    failed = [c for c in checks if str(c.get("status", "")).upper() == "FAIL"]
    warns = [c for c in checks if str(c.get("status", "")).upper() == "WARN"]

    by_name = {str(c.get("name")): c for c in checks}

    def _actor_field(check_name: str, *, default_code: str = "", extra: dict[str, Any] | None = None) -> dict[str, Any]:
        row = by_name.get(check_name) or {}
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        status = str(row.get("status", ""))
        error_code = str(row.get("error_code", "")).strip()
        if not error_code and status.strip().upper() in {"WARN", "FAIL"}:
            error_code = default_code
        out = {
            "status": status,
            "error_code": error_code,
            "suggestion": str(row.get("suggestion", "")),
        }
        if payload:
            out["payload"] = payload
        if extra:
            out.update(extra)
        return out

    session_payload = by_name.get("session_refresh_status", {}).get("payload")
    if not isinstance(session_payload, dict):
        session_payload = {}
    actor_binding_integrity = _actor_field("actor_session_binding", default_code="IP-ASB-BIND-001")
    actor_lease_freshness = _actor_field(
        "session_refresh_status",
        default_code="IP-ASB-LEASE-001",
        extra={
            "lease_status": str(session_payload.get("lease_status", "")),
            "pointer_consistency": str(session_payload.get("pointer_consistency", "")),
            "risk_flags": list(session_payload.get("risk_flags") or []),
        },
    )
    implicit_switch_guard = _actor_field("implicit_switch_guard", default_code="IP-ASB-SWITCH-001")
    pointer_drift_guard = _actor_field("pointer_drift_guard", default_code="IP-ASB-POINTER-001")

    actor_risk_required_count = len(ACTOR_RISK_FIELDS)
    actor_risk_present_count = sum(
        1
        for row in (
            actor_binding_integrity,
            actor_lease_freshness,
            implicit_switch_guard,
            pointer_drift_guard,
        )
        if str(row.get("status", "")).strip().upper() in {"PASS", "WARN", "FAIL"}
    )
    actor_risk_coverage_rate = round(
        (actor_risk_present_count / actor_risk_required_count) * 100.0, 2
    ) if actor_risk_required_count else 0.0
    actor_risk_profile_complete = actor_risk_coverage_rate >= 100.0

    if not actor_risk_profile_complete:
        failed.append(
            {
                "name": "actor_risk_profile_coverage",
                "status": "FAIL",
                "suggestion": "Ensure actor-risk profile exports all mandatory fields (binding/lease/implicit-switch/pointer).",
                "error_code": "IP-HLT-001",
            }
        )

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
        "operation": args.operation,
        "execution_report_ref": execution_report,
        "report_binding_mode": "explicit_report" if execution_report else "latest_report",
        "overall_status": overall,
        "warning_count": len(warns),
        "failed_count": len(failed),
        "actor_binding_integrity": actor_binding_integrity,
        "actor_lease_freshness": actor_lease_freshness,
        "implicit_switch_guard": implicit_switch_guard,
        "pointer_drift_guard": pointer_drift_guard,
        "actor_risk_required_count": actor_risk_required_count,
        "actor_risk_present_count": actor_risk_present_count,
        "actor_risk_coverage_rate": actor_risk_coverage_rate,
        "actor_risk_profile_complete": actor_risk_profile_complete,
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
