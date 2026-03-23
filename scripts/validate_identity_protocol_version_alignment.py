#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from resolve_identity_context import resolve_identity
from version_baseline_common import (
    REQUIRED_AGENT_IDENTITY_FIELDS,
    REQUIRED_CATALOG_FIELDS,
    REQUIRED_META_FIELDS,
    REQUIRED_SCAFFOLD_METADATA_FIELDS,
    resolve_version_baseline,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REPORT_ALIGNMENT = "IP-PVA-001"
ERR_BASELINE_ALIGNMENT = "IP-PVA-002"
ERR_PROMPT_ALIGNMENT = "IP-PVA-003"
ERR_BINDING_ALIGNMENT = "IP-PVA-004"
ERR_SCAFFOLD_BASELINE_ALIGNMENT = ERR_BASELINE_ALIGNMENT

STRICT_UPDATE_REFRESH_ALLOWED_REASONS = frozenset(
    {
        "prompt_sha_mismatch_or_missing",
        "report_older_than_key_inputs",
        "prompt_activation_mismatch",
        "live_head_drift_non_blocking",
    }
)
STRICT_UPDATE_FRESHNESS_ALLOWED_REASONS = frozenset(
    {
        "prompt_sha_mismatch_or_missing",
        "report_older_than_key_inputs",
    }
)

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


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _safe_load_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _task_snapshot(task_doc: dict[str, Any]) -> dict[str, dict[str, str]]:
    agent = task_doc.get("agent_identity") if isinstance(task_doc.get("agent_identity"), dict) else {}
    scaffold = task_doc.get("scaffold_metadata") if isinstance(task_doc.get("scaffold_metadata"), dict) else {}
    return {
        "agent_identity": {
            field: str(agent.get(field, "")).strip()
            for field in REQUIRED_AGENT_IDENTITY_FIELDS
        },
        "scaffold_metadata": {
            field: str(scaffold.get(field, "")).strip()
            for field in REQUIRED_SCAFFOLD_METADATA_FIELDS
        },
    }


def _meta_snapshot(meta_doc: dict[str, Any]) -> dict[str, str]:
    return {field: str(meta_doc.get(field, "")).strip() for field in REQUIRED_META_FIELDS}


def _catalog_snapshot(catalog_row: dict[str, Any]) -> dict[str, str]:
    return {field: str(catalog_row.get(field, "")).strip() for field in REQUIRED_CATALOG_FIELDS}


def _derive_strict_update_refreshability(
    *,
    error_code: str,
    freshness_ok: bool,
    baseline_ok: bool,
    scaffold_baseline_ok: bool,
    binding_ok: bool,
    freshness_payload: dict[str, Any],
    stale_reasons: list[str],
) -> tuple[bool, str]:
    freshness_stale_reasons = freshness_payload.get("stale_reasons", [])
    if not isinstance(freshness_stale_reasons, list):
        freshness_stale_reasons = []
    freshness_reason_set = {str(reason).strip() for reason in freshness_stale_reasons if str(reason).strip()}
    stale_reason_set = {str(reason).strip() for reason in stale_reasons if str(reason).strip()}
    refreshable = (
        error_code == ERR_REPORT_ALIGNMENT
        and not freshness_ok
        and baseline_ok
        and scaffold_baseline_ok
        and binding_ok
        and "report_older_than_key_inputs" in freshness_reason_set
        and freshness_reason_set.issubset(STRICT_UPDATE_FRESHNESS_ALLOWED_REASONS)
        and stale_reason_set.issubset(STRICT_UPDATE_REFRESH_ALLOWED_REASONS)
    )
    if refreshable:
        return True, "stale_execution_report_projection"
    return False, ""


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
    repo_root = Path(__file__).resolve().parents[1]

    baseline_state = resolve_version_baseline(repo_root=repo_root)
    version_baseline_ok = bool(baseline_state.get("ok"))
    version_baseline_error = str(baseline_state.get("error", "")).strip()

    task_path = (resolved_pack_path / "CURRENT_TASK.json").resolve()
    meta_path = (resolved_pack_path / "META.yaml").resolve()
    task_doc = _safe_load_json(task_path) if task_path.exists() else {}
    meta_doc = _safe_load_yaml(meta_path) if meta_path.exists() else {}
    catalog_doc = _safe_load_yaml(catalog_path)
    catalog_rows = catalog_doc.get("identities")
    catalog_rows = catalog_rows if isinstance(catalog_rows, list) else []
    catalog_row = next(
        (
            row
            for row in catalog_rows
            if isinstance(row, dict) and str(row.get("id", "")).strip() == str(args.identity_id or "").strip()
        ),
        {},
    )

    task_snapshot = _task_snapshot(task_doc)
    meta_snapshot = _meta_snapshot(meta_doc)
    catalog_snapshot = _catalog_snapshot(catalog_row if isinstance(catalog_row, dict) else {})

    baseline_task_agent = dict(baseline_state.get("agent_identity") or {})
    baseline_task_scaffold = dict(baseline_state.get("scaffold_metadata") or {})
    baseline_meta = dict(baseline_state.get("meta") or {})
    baseline_catalog = dict(baseline_state.get("catalog") or {})
    baseline_missing_fields = [
        str(x).strip()
        for x in (baseline_state.get("missing_fields") or [])
        if str(x).strip()
    ]

    version_mismatches: list[dict[str, str]] = []
    version_stale_reasons: list[str] = []

    if not task_path.exists():
        version_stale_reasons.append("current_task_missing")
    if not meta_path.exists():
        version_stale_reasons.append("meta_file_missing")
    if not isinstance(catalog_row, dict) or not catalog_row:
        version_stale_reasons.append("catalog_identity_row_missing")

    if not version_baseline_ok:
        if version_baseline_error:
            version_stale_reasons.append(f"version_baseline_resolution_failed:{version_baseline_error}")
        else:
            version_stale_reasons.append("version_baseline_resolution_failed")
        if baseline_missing_fields:
            version_stale_reasons.append(
                "version_baseline_required_fields_missing:" + ",".join(sorted(set(baseline_missing_fields)))
            )
    else:
        for field in REQUIRED_AGENT_IDENTITY_FIELDS:
            expected = str(baseline_task_agent.get(field, "")).strip()
            observed = str(((task_snapshot.get("agent_identity") or {}).get(field)) or "").strip()
            if expected and observed != expected:
                version_mismatches.append(
                    {
                        "field": f"task.agent_identity.{field}",
                        "expected": expected,
                        "observed": observed,
                    }
                )
        for field in REQUIRED_SCAFFOLD_METADATA_FIELDS:
            expected = str(baseline_task_scaffold.get(field, "")).strip()
            observed = str(((task_snapshot.get("scaffold_metadata") or {}).get(field)) or "").strip()
            if expected and observed != expected:
                version_mismatches.append(
                    {
                        "field": f"task.scaffold_metadata.{field}",
                        "expected": expected,
                        "observed": observed,
                    }
                )
        for field in REQUIRED_META_FIELDS:
            expected = str(baseline_meta.get(field, "")).strip()
            observed = str(meta_snapshot.get(field, "")).strip()
            if expected and observed != expected:
                version_mismatches.append(
                    {
                        "field": f"meta.{field}",
                        "expected": expected,
                        "observed": observed,
                    }
                )
        for field in REQUIRED_CATALOG_FIELDS:
            expected = str(baseline_catalog.get(field, "")).strip()
            observed = str(catalog_snapshot.get(field, "")).strip()
            if expected and observed != expected:
                version_mismatches.append(
                    {
                        "field": f"catalog.{field}",
                        "expected": expected,
                        "observed": observed,
                    }
                )

    scaffold_baseline_ok = version_baseline_ok and not version_mismatches and not version_stale_reasons

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
    if not scaffold_baseline_ok:
        stale_reasons.extend(version_stale_reasons)
        if version_mismatches:
            stale_reasons.append("scaffold_version_baseline_mismatch")

    status = STATUS_PASS_REQUIRED
    error_code = ""
    next_action = ""
    hint = ""
    if not freshness_ok:
        error_code = ERR_REPORT_ALIGNMENT
        next_action = str(freshness_payload.get("next_action", "")).strip()
        hint = str(freshness_payload.get("hint", "")).strip()
    elif not baseline_ok:
        error_code = ERR_BASELINE_ALIGNMENT
    elif not scaffold_baseline_ok:
        error_code = ERR_SCAFFOLD_BASELINE_ALIGNMENT
        next_action = "run_repair_contract_backfill_apply"
        hint = "python3 scripts/repair_contract_backfill.py --catalog <catalog> --identity-id <id> --apply --json-only"
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

    strict_update_refresh_allowed, strict_update_refresh_mode = _derive_strict_update_refreshability(
        error_code=error_code,
        freshness_ok=freshness_ok,
        baseline_ok=baseline_ok,
        scaffold_baseline_ok=scaffold_baseline_ok,
        binding_ok=binding_ok,
        freshness_payload=freshness_payload,
        stale_reasons=dedup_reasons,
    )

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
        "strict_update_refresh_allowed": strict_update_refresh_allowed,
        "strict_update_refresh_mode": strict_update_refresh_mode,
        "tuple_checks": {
            "execution_report_freshness": freshness_ok,
            "protocol_baseline_freshness": baseline_ok,
            "scaffold_version_baseline_alignment": scaffold_baseline_ok,
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
            "next_action": freshness_payload.get("next_action", ""),
            "hint": freshness_payload.get("hint", ""),
        },
        "protocol_baseline_freshness": {
            "status": baseline_status,
            "error_code": baseline_code,
            "rc": rc_baseline,
            "tail": _tail(out_baseline, err_baseline),
            "report_selected_path": baseline_payload.get("report_selected_path", ""),
            "report_protocol_root": baseline_payload.get("report_protocol_root", ""),
            "report_protocol_commit_sha": baseline_payload.get("report_protocol_commit_sha", ""),
            "protocol_head_sha_at_run_start": baseline_payload.get("protocol_head_sha_at_run_start", ""),
            "baseline_reference_mode": baseline_payload.get("baseline_reference_mode", ""),
            "current_protocol_head_sha": baseline_payload.get("current_protocol_head_sha", ""),
            "head_drift_detected": baseline_payload.get("head_drift_detected", False),
            "lag_commits": baseline_payload.get("lag_commits"),
            "stale_reasons": baseline_payload.get("stale_reasons", []),
        },
        "scaffold_version_baseline_alignment": {
            "status": STATUS_PASS_REQUIRED if scaffold_baseline_ok else STATUS_FAIL_REQUIRED,
            "error_code": "" if scaffold_baseline_ok else ERR_SCAFFOLD_BASELINE_ALIGNMENT,
            "entry_file": str(baseline_state.get("entry_path", "")),
            "resolved_file": str(baseline_state.get("resolved_path", "")),
            "stream_version": str(baseline_state.get("stream_version", "")),
            "baseline_ok": version_baseline_ok,
            "baseline_error": version_baseline_error,
            "baseline_missing_fields": baseline_missing_fields,
            "task_path": str(task_path),
            "meta_path": str(meta_path),
            "task_snapshot": task_snapshot,
            "catalog_snapshot": catalog_snapshot,
            "meta_snapshot": meta_snapshot,
            "mismatches": version_mismatches,
            "stale_reasons": version_stale_reasons,
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
        "next_action": next_action,
        "hint": hint,
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
            if hint:
                print(f"[HINT] {hint}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if status == STATUS_FAIL_REQUIRED:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
