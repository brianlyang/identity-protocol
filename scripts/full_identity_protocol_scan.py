#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CheckResult:
    rc: int
    ok: bool
    tail: str = ""
    stdout: str = ""
    stderr: str = ""


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> CheckResult:
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=env)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    tail = out.splitlines()[-1] if out else (err.splitlines()[-1] if err else "")
    return CheckResult(rc=p.returncode, ok=p.returncode == 0, tail=tail, stdout=out, stderr=err)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"invalid yaml root: {path}")
    return data


def _catalog_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = _load_yaml(path)
    return [x for x in (data.get("identities") or []) if isinstance(x, dict)]


def _parse_json_safely(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        pass
    lines = raw.splitlines()
    if lines and lines[-1].startswith("overall_release_decision="):
        try:
            return json.loads("\n".join(lines[:-1]))
        except Exception:
            return None
    return None


def _extract_capability_signal(raw: str) -> tuple[str, str]:
    """
    Best-effort parser for capability preflight output.
    Handles mixed stdout with leading [WARN]/[FAIL] lines + trailing JSON payload.
    """
    text = (raw or "").strip()
    if not text:
        return "", ""
    payload: dict[str, Any] | None = _parse_json_safely(text)
    if payload is None:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                payload = json.loads(text[start : end + 1])
            except Exception:
                payload = None
    if not isinstance(payload, dict):
        return "", ""
    status = str(payload.get("capability_activation_status", "")).strip().upper()
    code = str(payload.get("capability_activation_error_code", "")).strip()
    return status, code


def _latest_runtime_report(identity_id: str, report_dir: Path) -> Path | None:
    if not report_dir.exists():
        return None
    rows = [
        p
        for p in report_dir.glob(f"identity-upgrade-exec-{identity_id}-*.json")
        if not p.name.endswith("-patch-plan.json")
    ]
    if not rows:
        return None
    rows.sort(key=lambda p: p.stat().st_mtime)
    return rows[-1]


def _scope_hint_for_row(layer: str, row: dict[str, Any]) -> str:
    profile = str(row.get("profile", "")).strip().lower()
    runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
    if profile == "fixture" or runtime_mode == "demo_only":
        return "SYSTEM"
    if layer == "repo":
        return "SYSTEM"
    return "USER"


def _severity_for_row(row: dict[str, Any]) -> str:
    active = str(row.get("status", "")).lower() == "active"
    profile = str(row.get("profile", "")).lower()
    runtime_mode = str(row.get("runtime_mode", "")).lower()
    is_fixture = profile == "fixture" or runtime_mode == "demo_only"
    checks = row.get("checks", {})
    core_fail = any(
        not checks.get(name, {}).get("ok", False)
        for name in (
            "scope_resolution",
            "scope_isolation",
            "scope_persistence",
            "runtime_contract",
            "identity_home_catalog_alignment",
            "fixture_runtime_boundary",
            "actor_session_binding",
            "no_implicit_switch",
            "cross_actor_isolation",
            "response_stamp_validation",
            "response_stamp_blocker_receipt",
            "writeback_continuity",
            "post_execution_mandatory",
        )
    )
    prompt_fail = (not is_fixture) and any(
        name in checks and not checks.get(name, {}).get("ok", False)
        for name in ("prompt_quality", "prompt_activation", "prompt_lifecycle")
    )
    capability_fail = any(
        name in checks and not checks.get(name, {}).get("ok", False)
        for name in ("capability_activation_preflight", "capability_activation_report")
    )
    tool_vendor_fail = any(
        name in checks and not checks.get(name, {}).get("ok", False)
        for name in (
            "tool_installation",
            "install_provenance",
            "vendor_api_discovery",
            "vendor_api_solution",
            "required_contract_coverage",
        )
    )
    baseline = checks.get("protocol_baseline_freshness") or {}
    baseline_status = str(baseline.get("baseline_status", "")).upper()
    baseline_issue = (not baseline.get("ok", True)) or baseline_status == "FAIL" or (
        baseline_status == "WARN" and not is_fixture
    )
    freshness = checks.get("execution_report_freshness") or {}
    freshness_fail = (not freshness.get("ok", True)) or str(freshness.get("freshness_status", "")).upper() == "FAIL"
    cap_preflight = checks.get("capability_activation_preflight") or {}
    capability_env_blocked = bool(cap_preflight.get("env_auth_blocked", False))
    if capability_env_blocked:
        capability_fail = active and any(
            name in checks and not checks.get(name, {}).get("ok", False)
            for name in ("capability_activation_report",)
        )
    dialogue_fail = any(
        name in checks and not checks.get(name, {}).get("ok", False)
        for name in ("dialogue_content", "dialogue_cross_validation", "dialogue_result_support")
    )
    if active and profile == "runtime" and (core_fail or prompt_fail or capability_fail or dialogue_fail or tool_vendor_fail or freshness_fail):
        return "P0"
    if active and capability_env_blocked and not (core_fail or prompt_fail or dialogue_fail or tool_vendor_fail):
        return "P1"
    if core_fail or prompt_fail or capability_fail or dialogue_fail or tool_vendor_fail or freshness_fail or baseline_issue:
        return "P1"
    return "OK"


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan all configured identities and emit cross-catalog governance status.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--project-catalog", default="")
    ap.add_argument("--global-catalog", default="")
    ap.add_argument("--include-repo-catalog", action="store_true")
    ap.add_argument("--with-docs-contract", action="store_true")
    ap.add_argument(
        "--scan-mode",
        choices=["full", "target"],
        default="full",
        help="full=scan all discovered identities across selected catalogs; target=scan only explicit target identities",
    )
    ap.add_argument(
        "--identity-ids",
        default=os.environ.get("IDENTITY_IDS", ""),
        help="target identities for --scan-mode target (space/comma separated)",
    )
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    repo_catalog = (repo_root / args.repo_catalog).resolve() if not Path(args.repo_catalog).is_absolute() else Path(args.repo_catalog)
    if not repo_catalog.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog}")
        return 2

    project_catalog = Path(args.project_catalog).expanduser().resolve() if args.project_catalog else (repo_root.parent / ".agents/identity/catalog.local.yaml").resolve()
    global_catalog = Path(args.global_catalog).expanduser().resolve() if args.global_catalog else (Path.home() / ".codex/identity/catalog.local.yaml").resolve()

    catalog_list: list[tuple[str, Path]] = []
    if args.include_repo_catalog:
        catalog_list.append(("repo", repo_catalog))
    catalog_list.extend([("project", project_catalog), ("global", global_catalog)])

    target_ids = [x.strip() for x in args.identity_ids.replace(",", " ").split() if x.strip()]
    target_set = set(target_ids)
    if args.scan_mode == "target" and not target_set:
        print("[FAIL] --scan-mode target requires --identity-ids (or IDENTITY_IDS env).")
        return 2
    matched_targets: set[str] = set()

    payload: dict[str, Any] = {
        "repo_root": str(repo_root),
        "repo_catalog": str(repo_catalog),
        "scan_mode": args.scan_mode,
        "target_identities": sorted(target_set),
        "catalogs": [],
        "summary": {"total_identities": 0, "p0": 0, "p1": 0, "ok": 0},
    }

    for layer, catalog in catalog_list:
        rows = _catalog_rows(catalog) if catalog.exists() else []
        layer_out: dict[str, Any] = {"layer": layer, "catalog": str(catalog), "exists": catalog.exists(), "identities": []}
        for row in rows:
            iid = str(row.get("id", "")).strip()
            if not iid:
                continue
            if args.scan_mode == "target" and iid not in target_set:
                continue
            matched_targets.add(iid)
            scan_scope_hint = _scope_hint_for_row(layer, row)
            item: dict[str, Any] = {
                "identity_id": iid,
                "status": row.get("status"),
                "profile": row.get("profile"),
                "runtime_mode": row.get("runtime_mode"),
                "pack_path": row.get("pack_path"),
                "scan_scope_hint": scan_scope_hint,
                "checks": {},
            }
            resolve = _run(
                [
                    "python3",
                    "scripts/resolve_identity_context.py",
                    "resolve",
                    "--identity-id",
                    iid,
                    "--repo-catalog",
                    str(repo_catalog),
                    "--local-catalog",
                    str(catalog),
                    "--scope",
                    scan_scope_hint,
                ],
                cwd=repo_root,
            )
            item["checks"]["resolve"] = {"rc": resolve.rc, "ok": resolve.ok, "tail": resolve.tail}
            resolved_scope = scan_scope_hint
            if resolve.ok:
                data = _parse_json_safely(resolve.stdout) or {}
                item["resolved_scope"] = data.get("resolved_scope")
                item["source_layer"] = data.get("source_layer")
                item["conflict_detected"] = data.get("conflict_detected")
                resolved_scope = str(data.get("resolved_scope", "")).upper() or scan_scope_hint

            is_active_runtime = str(row.get("status", "")).lower() == "active" and str(row.get("profile", "")).lower() == "runtime"
            is_fixture = str(row.get("profile", "")).lower() == "fixture" or str(row.get("runtime_mode", "")).lower() == "demo_only"
            stamp_artifact = f"/tmp/identity-response-stamp-scan-{iid}.json"
            stamp_blocker_receipt = f"/tmp/identity-stamp-blocker-receipt-scan-{iid}.json"
            checks = {
                "scope_resolution": [
                    "python3",
                    "scripts/validate_identity_scope_resolution.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--scope",
                    scan_scope_hint,
                ],
                "scope_isolation": [
                    "python3",
                    "scripts/validate_identity_scope_isolation.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--scope",
                    scan_scope_hint,
                ],
                "scope_persistence": [
                    "python3",
                    "scripts/validate_identity_scope_persistence.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--scope",
                    scan_scope_hint,
                ],
                "runtime_contract": [
                    "python3",
                    "scripts/validate_identity_runtime_contract.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                ],
                "identity_home_catalog_alignment": [
                    "python3",
                    "scripts/validate_identity_home_catalog_alignment.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--json-only",
                ],
                "fixture_runtime_boundary": [
                    "python3",
                    "scripts/validate_fixture_runtime_boundary.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "actor_session_binding": [
                    "python3",
                    "scripts/validate_actor_session_binding.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "no_implicit_switch": [
                    "python3",
                    "scripts/validate_no_implicit_switch.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "cross_actor_isolation": [
                    "python3",
                    "scripts/validate_cross_actor_isolation.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "response_stamp_render": [
                    "python3",
                    "scripts/render_identity_response_stamp.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--view",
                    "external",
                    "--out",
                    stamp_artifact,
                    "--json-only",
                ],
                "response_stamp_validation": [
                    "python3",
                    "scripts/validate_identity_response_stamp.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--stamp-json",
                    stamp_artifact,
                    "--force-check",
                    "--enforce-user-visible-gate",
                    "--blocker-receipt-out",
                    stamp_blocker_receipt,
                ],
                "response_stamp_blocker_receipt": [
                    "python3",
                    "scripts/validate_identity_response_stamp_blocker_receipt.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--force-check",
                    "--receipt",
                    stamp_blocker_receipt,
                ],
                "tool_installation": [
                    "python3",
                    "scripts/validate_identity_tool_installation.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                ],
                "install_provenance": [
                    "python3",
                    "scripts/validate_identity_install_provenance.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                ],
                "vendor_api_discovery": [
                    "python3",
                    "scripts/validate_identity_vendor_api_discovery.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                ],
                "vendor_api_solution": [
                    "python3",
                    "scripts/validate_identity_vendor_api_solution.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                ],
                "required_contract_coverage": [
                    "python3",
                    "scripts/validate_required_contract_coverage.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--json-only",
                ],
                "writeback_continuity": [
                    "python3",
                    "scripts/validate_writeback_continuity.py",
                    "--identity-id",
                    iid,
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "post_execution_mandatory": [
                    "python3",
                    "scripts/validate_post_execution_mandatory.py",
                    "--identity-id",
                    iid,
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "protocol_baseline_freshness": [
                    "python3",
                    "scripts/validate_identity_protocol_baseline_freshness.py",
                    "--identity-id",
                    iid,
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--baseline-policy",
                    "warn",
                    "--json-only",
                ],
            }
            if not is_fixture:
                checks["prompt_quality"] = [
                    "python3",
                    "scripts/validate_identity_prompt_quality.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--scope",
                    resolved_scope,
                ]
            else:
                item["checks"]["prompt_quality"] = {
                    "rc": 0,
                    "ok": True,
                    "tail": f"[OK] prompt quality skipped for fixture/demo identity={iid}",
                    "skipped": True,
                }
            cap_preflight_cmd = [
                "python3",
                "scripts/validate_identity_capability_activation.py",
                "--catalog",
                str(catalog),
                "--repo-catalog",
                str(repo_catalog),
                "--identity-id",
                iid,
            ]
            if is_active_runtime:
                cap_preflight_cmd.append("--require-activated")
            checks["capability_activation_preflight"] = cap_preflight_cmd
            checks["dialogue_content"] = [
                "python3",
                "scripts/validate_identity_dialogue_content.py",
                "--catalog",
                str(catalog),
                "--identity-id",
                iid,
            ]
            checks["dialogue_cross_validation"] = [
                "python3",
                "scripts/validate_identity_dialogue_cross_validation.py",
                "--catalog",
                str(catalog),
                "--identity-id",
                iid,
            ]
            checks["dialogue_result_support"] = [
                "python3",
                "scripts/validate_identity_dialogue_result_support.py",
                "--catalog",
                str(catalog),
                "--identity-id",
                iid,
            ]
            checks["execution_report_freshness"] = [
                "python3",
                "scripts/validate_execution_report_freshness.py",
                "--identity-id",
                iid,
                "--catalog",
                str(catalog),
                "--repo-catalog",
                str(repo_catalog),
                "--execution-report-policy",
                "warn",
                "--json-only",
            ]
            if is_active_runtime:
                runtime_report_dir_path = Path(str(row.get("pack_path", ""))).expanduser().resolve() / "runtime" / "reports"
                runtime_report_dir = str(runtime_report_dir_path)
                checks["session_pointer"] = [
                    "python3",
                    "scripts/validate_identity_session_pointer_consistency.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                ]
                checks["prompt_activation"] = [
                    "python3",
                    "scripts/validate_identity_prompt_activation.py",
                    "--identity-id",
                    iid,
                    "--catalog",
                    str(catalog),
                    "--report-dir",
                    runtime_report_dir,
                ]
                checks["prompt_lifecycle"] = [
                    "python3",
                    "scripts/validate_identity_prompt_lifecycle.py",
                    "--identity-id",
                    iid,
                    "--report-dir",
                    runtime_report_dir,
                ]
                latest_report = _latest_runtime_report(iid, runtime_report_dir_path)
                if latest_report:
                    checks["capability_activation_report"] = [
                        "python3",
                        "scripts/validate_identity_capability_activation.py",
                        "--identity-id",
                        iid,
                        "--report",
                        str(latest_report),
                        "--require-activated",
                    ]
            for name, cmd in checks.items():
                r = _run(cmd, cwd=repo_root)
                check_payload: dict[str, Any] = {"rc": r.rc, "ok": r.ok, "tail": r.tail}
                if name == "capability_activation_preflight":
                    cap_status, cap_code = _extract_capability_signal(r.stdout)
                    if cap_status:
                        check_payload["capability_activation_status"] = cap_status
                    if cap_code:
                        check_payload["capability_activation_error_code"] = cap_code
                    if cap_code == "IP-CAP-003":
                        check_payload["env_auth_blocked"] = True
                if name == "required_contract_coverage":
                    coverage_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "required_contract_total",
                        "required_contract_passed",
                        "required_contract_coverage_rate",
                        "skipped_contract_count",
                        "failed_required_contract_count",
                        "failed_optional_contract_count",
                    ):
                        if k in coverage_doc:
                            check_payload[k] = coverage_doc.get(k)
                if name == "writeback_continuity":
                    writeback_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "writeback_continuity_status",
                        "error_code",
                        "required_contract",
                        "report_selected_path",
                        "writeback_mode",
                        "writeback_status",
                        "upgrade_required",
                        "all_ok",
                        "degrade_reason",
                        "risk_level",
                        "next_recovery_action",
                        "stale_reasons",
                    ):
                        if k in writeback_doc:
                            check_payload[k] = writeback_doc.get(k)
                if name == "post_execution_mandatory":
                    post_exec_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "post_execution_mandatory_status",
                        "error_code",
                        "required_contract",
                        "report_selected_path",
                        "missing_fields",
                        "writeback_mode",
                        "writeback_status",
                        "next_action",
                        "next_recovery_action",
                        "stale_reasons",
                    ):
                        if k in post_exec_doc:
                            check_payload[k] = post_exec_doc.get(k)
                if name == "execution_report_freshness":
                    freshness_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "freshness_status",
                        "freshness_error_code",
                        "report_selected_path",
                        "stale_reasons",
                        "checks",
                    ):
                        if k in freshness_doc:
                            check_payload[k] = freshness_doc.get(k)
                if name == "protocol_baseline_freshness":
                    baseline_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "baseline_status",
                        "baseline_error_code",
                        "report_selected_path",
                        "report_protocol_root",
                        "report_protocol_commit_sha",
                        "current_protocol_head_sha",
                        "lag_commits",
                        "stale_reasons",
                    ):
                        if k in baseline_doc:
                            check_payload[k] = baseline_doc.get(k)
                if name == "identity_home_catalog_alignment":
                    home_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "path_governance_status",
                        "path_error_codes",
                        "identity_home",
                        "identity_home_expected",
                        "identity_home_source",
                        "stale_reasons",
                    ):
                        if k in home_doc:
                            check_payload[k] = home_doc.get(k)
                if name == "fixture_runtime_boundary":
                    boundary_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "path_governance_status",
                        "path_error_codes",
                        "operation",
                        "allow_fixture_runtime",
                        "fixture_audit_receipt",
                        "stale_reasons",
                    ):
                        if k in boundary_doc:
                            check_payload[k] = boundary_doc.get(k)
                if name == "actor_session_binding":
                    actor_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "actor_binding_status",
                        "error_code",
                        "actor_id",
                        "actor_session_path",
                        "bound_identity_id",
                        "catalog_identity_status",
                        "stale_reasons",
                    ):
                        if k in actor_doc:
                            check_payload[k] = actor_doc.get(k)
                if name == "no_implicit_switch":
                    implicit_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "implicit_switch_status",
                        "error_code",
                        "switch_report_path",
                        "switch_id",
                        "actor_id",
                        "run_id",
                        "cross_actor_demotion_detected",
                        "stale_reasons",
                    ):
                        if k in implicit_doc:
                            check_payload[k] = implicit_doc.get(k)
                if name == "cross_actor_isolation":
                    isolation_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "cross_actor_isolation_status",
                        "error_code",
                        "actor_binding_count",
                        "active_identities",
                        "stale_reasons",
                    ):
                        if k in isolation_doc:
                            check_payload[k] = isolation_doc.get(k)
                item["checks"][name] = check_payload

            env = os.environ.copy()
            env["IDENTITY_CATALOG"] = str(catalog)
            three_plane = _run(
                [
                    "python3",
                    "scripts/report_three_plane_status.py",
                    "--identity-id",
                    iid,
                    "--scope",
                    scan_scope_hint,
                    *(["--with-docs-contract"] if args.with_docs_contract else []),
                ],
                cwd=repo_root,
                env=env,
            )
            item["checks"]["three_plane"] = {"rc": three_plane.rc, "ok": three_plane.ok, "tail": three_plane.tail}
            tp = _parse_json_safely(three_plane.stdout)
            if tp:
                item["three_plane"] = {
                    "instance": tp.get("instance_plane_status"),
                    "repo": tp.get("repo_plane_status"),
                    "release": tp.get("release_plane_status"),
                    "overall": tp.get("overall_release_decision"),
                }
            item["severity"] = _severity_for_row(item)
            payload["summary"]["total_identities"] += 1
            if item["severity"] == "P0":
                payload["summary"]["p0"] += 1
            elif item["severity"] == "P1":
                payload["summary"]["p1"] += 1
            else:
                payload["summary"]["ok"] += 1
            layer_out["identities"].append(item)

        payload["catalogs"].append(layer_out)

    if args.scan_mode == "target":
        missing = sorted(target_set - matched_targets)
        payload["missing_target_identities"] = missing
        if missing:
            if args.out:
                out = Path(args.out).expanduser().resolve()
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"[OK] wrote: {out}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            print(f"[FAIL] target identities not found in selected catalogs: {missing}")
            return 2

    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] wrote: {out}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
