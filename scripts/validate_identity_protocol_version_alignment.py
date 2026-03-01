#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from resolve_identity_context import resolve_identity

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REPORT_ALIGNMENT = "IP-PVA-001"
ERR_BASELINE_ALIGNMENT = "IP-PVA-002"
ERR_PROMPT_ALIGNMENT = "IP-PVA-003"
ERR_BINDING_ALIGNMENT = "IP-PVA-004"

STRICT_OPERATIONS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


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


def _tail(out: str, err: str) -> str:
    merged = "\n".join([x for x in [out.strip(), err.strip()] if x]).strip()
    if not merged:
        return ""
    return merged.splitlines()[-1]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate protocol version alignment as one tuple across report/prompt/task/binding context."
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--execution-report", default="")
    ap.add_argument("--scope", default="")
    ap.add_argument("--operation", choices=sorted(STRICT_OPERATIONS | INSPECTION_OPERATIONS), default="validate")
    ap.add_argument("--alignment-policy", choices=["strict", "warn"], default="strict")
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
            preferred_scope=str(args.scope or ""),
            allow_conflict=True,
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity context: {exc}")
        return 2

    resolved_pack_path = Path(str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "")).expanduser().resolve()
    scope = str(ctx.get("resolved_scope", "")).strip()
    policy = str(args.alignment_policy or "strict").strip().lower()
    operation = str(args.operation or "validate").strip().lower()
    inspection_mode = operation in INSPECTION_OPERATIONS

    fresh_cmd = [
        "python3",
        "scripts/validate_execution_report_freshness.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--execution-report-policy",
        policy,
        "--json-only",
    ]
    if args.execution_report.strip():
        fresh_cmd.extend(["--report", args.execution_report.strip()])
    rc_fresh, out_fresh, err_fresh = _run_capture(fresh_cmd)
    freshness_payload = _parse_json_payload(out_fresh) or {}
    freshness_status = str(freshness_payload.get("freshness_status", "")).strip().upper()
    freshness_code = str(freshness_payload.get("freshness_error_code", "")).strip()
    selected_report = str(freshness_payload.get("report_selected_path", "")).strip()
    if not selected_report and args.execution_report.strip():
        selected_report = str(Path(args.execution_report.strip()).expanduser().resolve())

    baseline_cmd = [
        "python3",
        "scripts/validate_identity_protocol_baseline_freshness.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--baseline-policy",
        policy,
        "--json-only",
    ]
    if selected_report:
        baseline_cmd.extend(["--execution-report", selected_report])
    rc_baseline, out_baseline, err_baseline = _run_capture(baseline_cmd)
    baseline_payload = _parse_json_payload(out_baseline) or {}
    baseline_status = str(baseline_payload.get("baseline_status", "")).strip().upper()
    baseline_code = str(baseline_payload.get("baseline_error_code", "")).strip()
    if not selected_report:
        selected_report = str(baseline_payload.get("report_selected_path", "")).strip()

    rc_prompt = 1
    out_prompt = ""
    err_prompt = ""
    rc_binding = 1
    out_binding = ""
    err_binding = ""
    report_exists = bool(selected_report) and Path(selected_report).expanduser().exists()
    if report_exists:
        prompt_cmd = [
            "python3",
            "scripts/validate_identity_prompt_activation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            str(catalog_path),
            "--repo-catalog",
            str(repo_catalog_path),
            "--report",
            selected_report,
        ]
        if scope:
            prompt_cmd.extend(["--scope", scope])
        rc_prompt, out_prompt, err_prompt = _run_capture(prompt_cmd)

        binding_cmd = [
            "python3",
            "scripts/validate_identity_binding_tuple.py",
            "--identity-id",
            args.identity_id,
            "--report",
            selected_report,
        ]
        rc_binding, out_binding, err_binding = _run_capture(binding_cmd)

    freshness_ok = rc_fresh == 0 and freshness_status == "PASS"
    baseline_ok = rc_baseline == 0 and baseline_status == "PASS"
    prompt_ok = report_exists and rc_prompt == 0
    binding_ok = report_exists and rc_binding == 0

    stale_reasons: list[str] = []
    if not freshness_ok:
        stale_reasons.extend(freshness_payload.get("stale_reasons", []) if isinstance(freshness_payload.get("stale_reasons", []), list) else [])
        if not freshness_status:
            stale_reasons.append("execution_report_freshness_status_missing")
    if not baseline_ok:
        stale_reasons.extend(baseline_payload.get("stale_reasons", []) if isinstance(baseline_payload.get("stale_reasons", []), list) else [])
        if not baseline_status:
            stale_reasons.append("baseline_status_missing")
    if not report_exists:
        stale_reasons.append("alignment_report_missing_for_prompt_binding")
    if report_exists and not prompt_ok:
        stale_reasons.append("prompt_activation_mismatch")
    if report_exists and not binding_ok:
        stale_reasons.append("binding_tuple_mismatch")

    status = STATUS_PASS_REQUIRED
    error_code = ""
    if not freshness_ok:
        error_code = ERR_REPORT_ALIGNMENT
    elif not baseline_ok:
        error_code = ERR_BASELINE_ALIGNMENT
    elif not prompt_ok:
        error_code = ERR_PROMPT_ALIGNMENT
    elif not binding_ok:
        error_code = ERR_BINDING_ALIGNMENT

    if error_code:
        status = STATUS_FAIL_REQUIRED if policy == "strict" and not inspection_mode else STATUS_WARN_NON_BLOCKING

    # de-duplicate while preserving order
    dedup_reasons: list[str] = []
    seen = set()
    for reason in stale_reasons:
        rr = str(reason).strip()
        if not rr or rr in seen:
            continue
        seen.add(rr)
        dedup_reasons.append(rr)

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(resolved_pack_path),
        "operation": operation,
        "alignment_policy": policy,
        "required_contract": True,
        "report_selected_path": str(selected_report).strip(),
        "protocol_version_alignment_status": status,
        "error_code": error_code,
        "tuple_checks": {
            "execution_report_freshness": freshness_ok,
            "protocol_baseline_freshness": baseline_ok,
            "prompt_activation": prompt_ok,
            "binding_tuple": binding_ok,
        },
        "execution_report_freshness": {
            "status": freshness_status,
            "error_code": freshness_code,
            "rc": rc_fresh,
            "tail": _tail(out_fresh, err_fresh),
            "report_selected_path": freshness_payload.get("report_selected_path", ""),
            "stale_reasons": freshness_payload.get("stale_reasons", []),
            "checks": freshness_payload.get("checks", {}),
        },
        "protocol_baseline_freshness": {
            "status": baseline_status,
            "error_code": baseline_code,
            "rc": rc_baseline,
            "tail": _tail(out_baseline, err_baseline),
            "report_selected_path": baseline_payload.get("report_selected_path", ""),
            "report_protocol_root": baseline_payload.get("report_protocol_root", ""),
            "report_protocol_commit_sha": baseline_payload.get("report_protocol_commit_sha", ""),
            "current_protocol_head_sha": baseline_payload.get("current_protocol_head_sha", ""),
            "lag_commits": baseline_payload.get("lag_commits"),
            "stale_reasons": baseline_payload.get("stale_reasons", []),
        },
        "prompt_activation": {
            "rc": rc_prompt,
            "tail": _tail(out_prompt, err_prompt),
        },
        "binding_tuple": {
            "rc": rc_binding,
            "tail": _tail(out_binding, err_binding),
        },
        "stale_reasons": dedup_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if status == STATUS_PASS_REQUIRED:
            print(
                "[OK] protocol version alignment validated: "
                f"identity={args.identity_id} report={payload['report_selected_path']}"
            )
        else:
            print(
                f"[WARN] {error_code} protocol version alignment drift: "
                f"identity={args.identity_id} report={payload['report_selected_path']}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if status == STATUS_FAIL_REQUIRED:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

