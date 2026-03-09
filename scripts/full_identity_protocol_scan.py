#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from actor_session_common import load_actor_binding, resolve_actor_id
from response_stamp_common import DEFAULT_WORK_LAYER, resolve_layer_intent
from runtime_temp_path_common import named_temp_root, runtime_temp_file

LOCK_PROTOCOL_PREFIX = "SESSION_LANE_LOCK_PROTOCOL_"
LOCK_EXIT_PREFIX = "SESSION_LANE_LOCK_EXIT_"
IP_ERROR_CODE_RE = re.compile(r"\b(IP-[A-Z0-9-]+)\b")

M2M_CHECK_NAMES: set[str] = {
    "actor_session_binding",
    "actor_session_multibinding_concurrency",
    "no_implicit_switch",
    "cross_actor_isolation",
    "response_stamp_validation",
    "reply_identity_context_first_line",
    "send_time_reply_gate",
    "headstamp_recurrence_closure",
    "execution_reply_identity_coherence",
    "required_gate_tuple_parity",
    "execution_target_tuple_isolation",
}
BUNDLE_GATE_CHECK_NAMES: set[str] = {
    "required_gate_bundle_runner",
    "required_gate_bundle_runner_shadow",
}
CAPABILITY_CHECK_NAMES: set[str] = {
    "capability_activation_preflight",
    "capability_activation_report",
    "prompt_bootstrap_capability",
    "prompt_capability_matrix",
    "prompt_kernel_executable_coupling",
}
RELEASE_ENV_CHECK_NAMES: set[str] = {
    "release_plane_cloud_evidence",
    "run_id_report_selection",
    "outlet_regression_matrix",
}
BASELINE_CHECK_NAMES: set[str] = {
    "session_refresh_status",
    "execution_report_freshness",
    "protocol_baseline_freshness",
    "protocol_version_alignment",
}
PROTOCOL_FEEDBACK_OBS_CHECK_NAMES: set[str] = {
    "protocol_feedback_sidecar",
    "protocol_feedback_reply_channel",
    "protocol_feedback_bootstrap_ready",
}
CHECK_ERROR_CODE_KEYS: tuple[str, ...] = (
    "error_code",
    "sidecar_error_code",
    "capability_activation_error_code",
    "pin_error_code",
    "baseline_error_code",
    "freshness_error_code",
    "normalization_error_code",
    "semantic_convergence_error_code",
)


@dataclass
class CheckResult:
    rc: int
    ok: bool
    tail: str = ""
    stdout: str = ""
    stderr: str = ""


def _resolve_applied_gate_set(*, layer_intent_text: str, expected_work_layer: str, expected_source_layer: str) -> str:
    resolved = resolve_layer_intent(
        explicit_work_layer=str(expected_work_layer or "").strip(),
        explicit_source_layer=str(expected_source_layer or "").strip(),
        intent_text=str(layer_intent_text or "").strip(),
        default_work_layer=DEFAULT_WORK_LAYER,
        default_source_layer="project",
    )
    work_layer = str(resolved.get("resolved_work_layer", DEFAULT_WORK_LAYER)).strip().lower() or DEFAULT_WORK_LAYER
    if work_layer == "protocol":
        return "protocol_required_checks"
    if work_layer == "instance":
        return "instance_required_checks"
    return "dual_unroutable"


def _safe_json_file(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _latest_lane_receipt(*, outbox_dir: Path, prefix: str, identity_id: str) -> Path | None:
    if not outbox_dir.exists():
        return None
    rows = sorted(outbox_dir.glob(f"{prefix}*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in rows:
        doc = _safe_json_file(p)
        rid = str(doc.get("identity_id", "")).strip()
        if rid and rid != identity_id:
            continue
        return p.resolve()
    return None


def _detect_session_lane_lock(
    *,
    catalog_path: Path,
    identity_id: str,
    actor_id: str,
    session_id: str,
    resolved_pack_path: Path | None,
) -> str:
    try:
        binding = load_actor_binding(
            catalog_path,
            actor_id,
            identity_id=identity_id,
            session_id=session_id,
        )
    except Exception:
        binding = {}
    for key in ("session_lane_lock", "lane_lock", "work_layer_lock"):
        token = str(binding.get(key, "")).strip().lower()
        if token in {"protocol", "instance"}:
            return token

    if resolved_pack_path is None:
        return ""
    outbox_dir = (resolved_pack_path / "runtime" / "protocol-feedback" / "outbox-to-protocol").resolve()
    lock_protocol = _latest_lane_receipt(outbox_dir=outbox_dir, prefix=LOCK_PROTOCOL_PREFIX, identity_id=identity_id)
    lock_exit = _latest_lane_receipt(outbox_dir=outbox_dir, prefix=LOCK_EXIT_PREFIX, identity_id=identity_id)
    if lock_protocol is None:
        return ""
    protocol_mtime = lock_protocol.stat().st_mtime
    exit_mtime = lock_exit.stat().st_mtime if lock_exit is not None else -1.0
    if exit_mtime > protocol_mtime:
        return ""
    return "protocol"


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


def _extract_check_error_code(entry: dict[str, Any]) -> str:
    for key in CHECK_ERROR_CODE_KEYS:
        token = str(entry.get(key, "")).strip()
        if token:
            return token
    for blob_key in ("tail", "stdout", "stderr"):
        blob = str(entry.get(blob_key, "") or "")
        m = IP_ERROR_CODE_RE.search(blob)
        if m:
            return str(m.group(1) or "").strip()
    return ""


def _is_m2m_error_code(error_code: str) -> bool:
    token = str(error_code or "").strip().upper()
    if not token:
        return False
    return token.startswith("IP-ASB-") or token.startswith("IP-ACTOR-") or token.startswith("IP-FE-")


def _is_m2m_failed_check(*, check_name: str, error_code: str) -> bool:
    if check_name in BUNDLE_GATE_CHECK_NAMES and not _is_m2m_error_code(error_code):
        return False
    return check_name in M2M_CHECK_NAMES or _is_m2m_error_code(error_code)


def _classify_m2m_projection(*, checks: dict[str, Any]) -> dict[str, Any]:
    failed: list[dict[str, str]] = []
    for name, raw in (checks or {}).items():
        entry = raw if isinstance(raw, dict) else {}
        if bool(entry.get("ok", False)):
            continue
        failed.append(
            {
                "check": str(name),
                "error_code": _extract_check_error_code(entry),
            }
        )
    m2m_failed = [
        row
        for row in failed
        if _is_m2m_failed_check(
            check_name=str(row.get("check", "")),
            error_code=str(row.get("error_code", "")),
        )
    ]
    non_m2m_failed = [row for row in failed if row not in m2m_failed]

    non_m2m_scope: list[str] = []
    if any(
        row["check"] in CAPABILITY_CHECK_NAMES or str(row.get("error_code", "")).upper().startswith("IP-CAP-")
        for row in non_m2m_failed
    ):
        non_m2m_scope.append("instance_capability")
    if any(row["check"] in RELEASE_ENV_CHECK_NAMES for row in non_m2m_failed):
        non_m2m_scope.append("release_env")
    if any(
        row["check"] in BASELINE_CHECK_NAMES or str(row.get("error_code", "")).upper().startswith("IP-PBL-")
        for row in non_m2m_failed
    ):
        non_m2m_scope.append("baseline_refresh")
    if any(row["check"] in PROTOCOL_FEEDBACK_OBS_CHECK_NAMES for row in non_m2m_failed):
        non_m2m_scope.append("protocol_feedback_observability")
    if non_m2m_failed and not non_m2m_scope:
        non_m2m_scope.append("other")

    return {
        "m2m_binding_closure_status": "PASS" if not m2m_failed else "FAIL",
        "m2m_failure_scope": "protocol_m2m" if m2m_failed else "",
        "m2m_failed_check_count": len(m2m_failed),
        "m2m_failed_checks": m2m_failed,
        "m2m_failure_reasons": [f"{row['check']}:{row.get('error_code') or 'UNKNOWN'}" for row in m2m_failed],
        "non_m2m_failed_check_count": len(non_m2m_failed),
        "non_m2m_failed_checks": non_m2m_failed,
        "non_m2m_failure_scope": sorted(set(non_m2m_scope)),
        "non_m2m_failure_reasons": [
            f"{row['check']}:{row.get('error_code') or 'UNKNOWN'}"
            for row in non_m2m_failed
        ],
        "failed_check_count_total": len(failed),
    }


def _replace_activation_policy(cmd: list[str], policy: str) -> list[str]:
    out = list(cmd)
    if "--activation-policy" in out:
        idx = out.index("--activation-policy")
        if idx + 1 < len(out):
            out[idx + 1] = policy
            return out
    out.extend(["--activation-policy", policy])
    return out


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


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _infer_target_source_layer_from_env(*, project_catalog: Path, global_catalog: Path) -> str:
    token = os.environ.get("IDENTITY_CATALOG", "").strip()
    if not token:
        return ""
    try:
        env_catalog = Path(token).expanduser().resolve()
    except Exception:
        return ""
    if env_catalog == project_catalog.resolve() or _within(env_catalog, project_catalog.parent):
        return "project"
    if env_catalog == global_catalog.resolve() or _within(env_catalog, global_catalog.parent):
        return "global"
    return ""


def _resolve_effective_scan_session_id(
    *,
    catalog_path: Path,
    actor_id: str,
    identity_id: str,
    requested_session_id: str,
) -> tuple[str, str, bool]:
    requested = str(requested_session_id or "").strip()
    if requested:
        exact = load_actor_binding(
            catalog_path,
            actor_id,
            identity_id=identity_id,
            session_id=requested,
        )
        if exact:
            return requested, "requested_bound", True

    identity_scoped = load_actor_binding(
        catalog_path,
        actor_id,
        identity_id=identity_id,
        session_id="",
    )
    fallback_session_id = str(identity_scoped.get("session_id", "")).strip()
    if fallback_session_id:
        if requested:
            return fallback_session_id, "requested_unbound_fallback_identity_scoped", False
        return fallback_session_id, "identity_scoped_latest", True

    if requested:
        return requested, "requested_unbound_no_fallback", False
    return "", "missing", False


def _scope_hint_for_row(layer: str, row: dict[str, Any]) -> str:
    profile = str(row.get("profile", "")).strip().lower()
    runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
    if profile == "fixture" or runtime_mode == "demo_only":
        return "SYSTEM"
    if layer == "repo_metadata":
        return "SYSTEM"
    return "USER"


def _severity_for_row(row: dict[str, Any]) -> str:
    active = str(row.get("status", "")).lower() == "active"
    profile = str(row.get("profile", "")).lower()
    runtime_mode = str(row.get("runtime_mode", "")).lower()
    is_fixture = profile == "fixture" or runtime_mode == "demo_only"
    # Fixture/demo identities and inactive rows are visibility-only in scan output.
    # Keep their detailed check payloads for audit, but do not let them block
    # release readiness summary (prevents false non-green caused by demo lanes).
    if (not active) or is_fixture:
        return "OK"
    checks = row.get("checks", {})
    core_fail = any(
        not checks.get(name, {}).get("ok", False)
        for name in (
            "scope_resolution",
            "scope_isolation",
            "scope_persistence",
            "runtime_mode_guard",
            "runtime_contract",
            "identity_home_catalog_alignment",
            "fixture_runtime_boundary",
            "actor_session_binding",
            "actor_session_multibinding_concurrency",
            "no_implicit_switch",
            "cross_actor_isolation",
            "session_refresh_status",
            "response_stamp_validation",
            "response_stamp_blocker_receipt",
            "reply_identity_context_first_line",
            "layer_intent_resolution",
            "send_time_reply_gate",
            "headstamp_recurrence_closure",
            "execution_reply_identity_coherence",
            "writeback_continuity",
            "post_execution_mandatory",
            "semantic_routing_guard",
            "instance_protocol_split_receipt",
            "protocol_vendor_semantic_isolation",
            "external_source_trust_chain",
            "protocol_data_sanitization_boundary",
            "platform_optimization_discovery_trigger",
            "discovery_requiredization",
            "vibe_coding_feeding_pack",
            "capability_fit_optimization",
            "capability_composition_before_discovery",
            "capability_fit_review_freshness",
            "capability_fit_roundtable_evidence",
            "capability_fit_review_trigger",
            "capability_fit_matrix_builder",
            "vendor_namespace_separation",
            "work_layer_gate_set_routing",
            "protocol_feedback_reply_channel",
            "protocol_feedback_bootstrap_ready",
            "protocol_entry_candidate_bridge",
            "protocol_inquiry_followup_chain",
            "protocol_feedback_sidecar",
            "instance_base_repo_write_boundary",
            "protocol_feedback_ssot_archival",
            "protocol_version_alignment",
            "required_gate_bundle_runner",
            "required_gate_bundle_runner_shadow",
            "required_gate_recurrence_escalator",
            "required_gate_tuple_parity",
            "cross_verification_tracks",
            "intake_evidence_quorum",
            "route_version_pinning",
            "fallback_taxonomy_normalization",
            "dedup_monotonicity",
            "cross_workflow_schema",
            "skill_path_integrity",
            "execution_target_tuple_isolation",
            "multimodal_plugin_enforcement",
            "e2e_hermetic_runtime_import",
        )
    )
    prompt_fail = (not is_fixture) and any(
        name in checks and not checks.get(name, {}).get("ok", False)
        for name in ("prompt_quality", "prompt_activation", "prompt_lifecycle")
    )
    capability_check_names = ("capability_activation_preflight", "capability_activation_report")
    capability_fail_non_env = any(
        name in checks
        and not checks.get(name, {}).get("ok", False)
        and not bool(checks.get(name, {}).get("env_auth_blocked", False))
        for name in capability_check_names
    )
    capability_fail_env_only = any(
        name in checks
        and not checks.get(name, {}).get("ok", False)
        and bool(checks.get(name, {}).get("env_auth_blocked", False))
        for name in capability_check_names
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
    fit_review = checks.get("capability_fit_review_freshness") or {}
    fit_review_status = str(fit_review.get("capability_fit_review_freshness_status", "")).upper()
    fit_review_issue = fit_review_status == "WARN_NON_BLOCKING" or (
        str(fit_review.get("review_freshness_status", "")).upper() == "WARN_STALE_OPTIMIZATION_REVIEW"
    )
    fit_trigger = checks.get("capability_fit_review_trigger") or {}
    fit_trigger_status = str(fit_trigger.get("capability_fit_review_trigger_status", "")).upper()
    fit_trigger_issue = fit_trigger_status in {"WARN_NON_BLOCKING", "TRIGGERED_NON_BLOCKING"}
    fit_builder = checks.get("capability_fit_matrix_builder") or {}
    fit_builder_status = str(fit_builder.get("capability_fit_matrix_builder_status", "")).upper()
    fit_builder_issue = fit_builder_status == "WARN_NON_BLOCKING"
    freshness = checks.get("execution_report_freshness") or {}
    freshness_fail = (not freshness.get("ok", True)) or str(freshness.get("freshness_status", "")).upper() == "FAIL"
    capability_env_blocked = capability_fail_env_only and not capability_fail_non_env
    dialogue_fail = any(
        name in checks and not checks.get(name, {}).get("ok", False)
        for name in ("dialogue_content", "dialogue_cross_validation", "dialogue_result_support")
    )
    if active and profile == "runtime" and (
        core_fail or prompt_fail or capability_fail_non_env or dialogue_fail or tool_vendor_fail or freshness_fail
    ):
        return "P0"
    if active and capability_env_blocked and not (
        core_fail or prompt_fail or dialogue_fail or tool_vendor_fail or freshness_fail
    ):
        return "P1"
    if (
        core_fail
        or prompt_fail
        or capability_fail_non_env
        or capability_fail_env_only
        or dialogue_fail
        or tool_vendor_fail
        or freshness_fail
        or baseline_issue
        or fit_review_issue
        or fit_trigger_issue
        or fit_builder_issue
    ):
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
    ap.add_argument(
        "--target-source-layer",
        choices=["auto", "project", "global", "both"],
        default="auto",
        help=(
            "target-mode catalog scope: auto=prefer expected-source-layer/env-bound runtime layer; "
            "project/global=single layer only; both=scan both project+global."
        ),
    )
    ap.add_argument("--layer-intent-text", default="", help="optional natural-language layer intent passed to stamp render/reply gates")
    ap.add_argument("--expected-work-layer", default="", help="optional expected work_layer override for strict reply gates")
    ap.add_argument("--expected-source-layer", default="", help="optional expected source_layer override for strict reply gates")
    ap.add_argument(
        "--actor-id",
        default="",
        help=(
            "explicit actor id for strict governed-outlet/headstamp recurrence closure checks. "
            "required for strict full-scan execution (no implicit fallback)."
        ),
    )
    ap.add_argument(
        "--session-id",
        default="",
        help="explicit actor session id for strict full-scan execution (e.g., run:<run_id>)",
    )
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    repo_catalog = (repo_root / args.repo_catalog).resolve() if not Path(args.repo_catalog).is_absolute() else Path(args.repo_catalog)
    if not repo_catalog.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog}")
        return 2

    if args.project_catalog:
        project_catalog = Path(args.project_catalog).expanduser().resolve()
    else:
        project_catalog = (
            (repo_root.parent / ".identity" / "catalog.local.yaml").resolve()
            if repo_root.name == "identity-protocol-local"
            else (repo_root / ".identity" / "catalog.local.yaml").resolve()
        )
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
    global_catalog = (
        Path(args.global_catalog).expanduser().resolve()
        if args.global_catalog
        else (codex_home / ".identity" / "catalog.local.yaml").resolve()
    )

    target_ids = [x.strip() for x in args.identity_ids.replace(",", " ").split() if x.strip()]
    target_set = set(target_ids)
    layer_intent_text = args.layer_intent_text.strip()
    expected_work_layer = args.expected_work_layer.strip().lower()
    expected_source_layer = args.expected_source_layer.strip().lower()
    target_source_layer_mode = str(args.target_source_layer or "auto").strip().lower() or "auto"
    actor_id_input = str(args.actor_id or "").strip()
    if not actor_id_input:
        print("[FAIL] IP-ACTOR-ENTRY-001 explicit --actor-id is required for strict full-scan execution")
        return 1
    session_id_input = str(args.session_id or "").strip()
    if not session_id_input:
        print("[FAIL] IP-ASB-SESSION-ENTRY-001 explicit --session-id is required for strict full-scan execution")
        return 1
    actor_id = resolve_actor_id(actor_id_input)
    if args.scan_mode == "target" and not target_set:
        print("[FAIL] --scan-mode target requires --identity-ids (or IDENTITY_IDS env).")
        return 2
    matched_targets: set[str] = set()

    runtime_catalogs: list[tuple[str, Path]] = [("project", project_catalog), ("global", global_catalog)]
    effective_target_source_layer = ""
    if target_source_layer_mode in {"project", "global"}:
        effective_target_source_layer = target_source_layer_mode
    elif target_source_layer_mode == "both":
        effective_target_source_layer = "both"
    else:
        if expected_source_layer in {"project", "global"}:
            effective_target_source_layer = expected_source_layer
        else:
            inferred = _infer_target_source_layer_from_env(
                project_catalog=project_catalog,
                global_catalog=global_catalog,
            )
            effective_target_source_layer = inferred or "project"
    if effective_target_source_layer in {"project", "global"}:
        runtime_catalogs = [(layer, path) for layer, path in runtime_catalogs if layer == effective_target_source_layer]

    catalog_list: list[tuple[str, Path]] = []
    if args.include_repo_catalog:
        catalog_list.append(("repo_metadata", repo_catalog))
    catalog_list.extend(runtime_catalogs)

    payload: dict[str, Any] = {
        "repo_root": str(repo_root),
        "repo_catalog": str(repo_catalog),
        "scan_mode": args.scan_mode,
        "target_identities": sorted(target_set),
        "target_source_layer_mode": target_source_layer_mode,
        "target_source_layer_effective": effective_target_source_layer,
        "catalogs": [],
        "summary": {"total_identities": 0, "p0": 0, "p1": 0, "ok": 0},
        "summary_m2m": {"total_identities": 0, "pass": 0, "fail": 0},
    }
    target_severity_map: dict[str, str] = {}
    target_m2m_map: dict[str, str] = {}

    def _update_target_severity(identity_id: str, severity: str) -> None:
        if args.scan_mode != "target":
            return
        normalized = str(severity or "OK").strip().upper() or "OK"
        rank = {"P0": 2, "P1": 1, "OK": 0}
        current = target_severity_map.get(identity_id, "OK")
        if rank.get(normalized, 0) >= rank.get(current, 0):
            target_severity_map[identity_id] = normalized

    def _update_target_m2m(identity_id: str, m2m_status: str) -> None:
        if args.scan_mode != "target":
            return
        normalized = str(m2m_status or "PASS").strip().upper() or "PASS"
        current = target_m2m_map.get(identity_id, "PASS")
        if normalized == "FAIL" or current == "FAIL":
            target_m2m_map[identity_id] = "FAIL"
        else:
            target_m2m_map[identity_id] = "PASS"

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
            resolved_pack_path: Path | None = None
            if resolve.ok:
                data = _parse_json_safely(resolve.stdout) or {}
                item["resolved_scope"] = data.get("resolved_scope")
                item["source_layer"] = data.get("source_layer")
                item["conflict_detected"] = data.get("conflict_detected")
                resolved_pack_token = str(data.get("resolved_pack_path") or data.get("pack_path") or "").strip()
                if resolved_pack_token:
                    try:
                        resolved_pack_path = Path(resolved_pack_token).expanduser().resolve()
                        item["resolved_pack_path"] = str(resolved_pack_path)
                    except Exception:
                        resolved_pack_path = None
                resolved_scope = str(data.get("resolved_scope", "")).upper() or scan_scope_hint
            if resolved_pack_path is None:
                fallback_pack = str(row.get("pack_path", "")).strip()
                if fallback_pack:
                    try:
                        resolved_pack_path = Path(fallback_pack).expanduser().resolve()
                    except Exception:
                        resolved_pack_path = None

            effective_source_layer = expected_source_layer or ("global" if layer == "global" else "project")
            lane_lock_hint = _detect_session_lane_lock(
                catalog_path=catalog,
                identity_id=iid,
                actor_id=actor_id,
                session_id=session_id_input,
                resolved_pack_path=resolved_pack_path,
            )
            effective_work_layer = expected_work_layer
            if not effective_work_layer:
                inferred = resolve_layer_intent(
                    explicit_work_layer="",
                    explicit_source_layer=effective_source_layer,
                    intent_text=layer_intent_text,
                    default_work_layer=DEFAULT_WORK_LAYER,
                    default_source_layer=effective_source_layer,
                )
                effective_work_layer = (
                    str(inferred.get("resolved_work_layer", DEFAULT_WORK_LAYER)).strip().lower() or DEFAULT_WORK_LAYER
                )
            if not expected_work_layer and lane_lock_hint in {"protocol", "instance"}:
                effective_work_layer = lane_lock_hint
            if effective_work_layer not in {"protocol", "instance", "dual"}:
                effective_work_layer = DEFAULT_WORK_LAYER

            lane_applied_gate_set = _resolve_applied_gate_set(
                layer_intent_text=layer_intent_text,
                expected_work_layer=effective_work_layer,
                expected_source_layer=effective_source_layer,
            )
            item["effective_expected_work_layer"] = effective_work_layer
            item["effective_expected_source_layer"] = effective_source_layer
            if lane_lock_hint:
                item["detected_session_lane_lock"] = lane_lock_hint

            mode_guard_cmd = [
                "python3",
                "scripts/validate_identity_runtime_mode_guard.py",
                "--identity-id",
                iid,
                "--catalog",
                str(catalog),
                "--repo-catalog",
                str(repo_catalog),
                "--expect-mode",
                "auto",
                "--operation",
                "scan",
            ]
            if str(scan_scope_hint or "").strip():
                mode_guard_cmd.extend(["--scope", str(scan_scope_hint).strip()])
            mode_guard = _run(mode_guard_cmd, cwd=repo_root)
            item["checks"]["runtime_mode_guard"] = {
                "rc": mode_guard.rc,
                "ok": mode_guard.ok,
                "tail": mode_guard.tail,
            }
            if not mode_guard.ok:
                item["runtime_mode_guard_blocked"] = True
                mode_guard_raw = "\n".join(x for x in (mode_guard.stdout, mode_guard.stderr, mode_guard.tail) if x).upper()
                env_catalog_mismatch = "IP-ENV-003" in mode_guard_raw
                if env_catalog_mismatch and args.scan_mode == "full" and target_source_layer_mode == "auto":
                    item["runtime_mode_guard_env_catalog_mismatch"] = True
                    item["severity"] = "P1"
                else:
                    item["severity"] = _severity_for_row(item)
                item["m2m_projection"] = _classify_m2m_projection(checks=item.get("checks", {}))
                payload["summary_m2m"]["total_identities"] += 1
                current_m2m = str(item["m2m_projection"].get("m2m_binding_closure_status", "")).upper()
                if current_m2m == "PASS":
                    payload["summary_m2m"]["pass"] += 1
                else:
                    payload["summary_m2m"]["fail"] += 1
                _update_target_m2m(iid, current_m2m)
                _update_target_severity(iid, str(item["severity"]))
                payload["summary"]["total_identities"] += 1
                if item["severity"] == "P0":
                    payload["summary"]["p0"] += 1
                elif item["severity"] == "P1":
                    payload["summary"]["p1"] += 1
                else:
                    payload["summary"]["ok"] += 1
                layer_out["identities"].append(item)
                continue

            scan_session_id, session_resolution_mode, requested_session_bound = _resolve_effective_scan_session_id(
                catalog_path=catalog,
                actor_id=actor_id,
                identity_id=iid,
                requested_session_id=session_id_input,
            )
            if not scan_session_id:
                scan_session_id = session_id_input
            item["session_id_requested"] = session_id_input
            item["session_id_effective"] = scan_session_id
            item["session_id_resolution_mode"] = session_resolution_mode
            item["session_id_requested_bound"] = requested_session_bound

            is_active_runtime = str(row.get("status", "")).lower() == "active" and str(row.get("profile", "")).lower() == "runtime"
            is_fixture = str(row.get("profile", "")).lower() == "fixture" or str(row.get("runtime_mode", "")).lower() == "demo_only"
            stamp_artifact = str(
                runtime_temp_file(
                    channel="response-stamp",
                    operation="scan",
                    identity_id=iid,
                    stem=f"identity-response-stamp-scan-{iid}",
                    ext="json",
                )
            )
            stamp_blocker_receipt = str(
                runtime_temp_file(
                    channel="response-stamp",
                    operation="scan",
                    identity_id=iid,
                    stem=f"identity-stamp-blocker-receipt-scan-{iid}",
                    ext="json",
                )
            )
            reply_first_line_blocker_receipt = str(
                runtime_temp_file(
                    channel="response-stamp",
                    operation="scan",
                    identity_id=iid,
                    stem=f"identity-reply-first-line-blocker-receipt-scan-{iid}",
                    ext="json",
                )
            )
            send_time_reply_file = str(
                runtime_temp_file(
                    channel="response-stamp",
                    operation="scan",
                    identity_id=iid,
                    stem=f"identity-send-time-reply-scan-{iid}",
                    ext="txt",
                )
            )
            send_time_reply_gate_blocker_receipt = str(
                runtime_temp_file(
                    channel="response-stamp",
                    operation="scan",
                    identity_id=iid,
                    stem=f"identity-send-time-reply-gate-blocker-receipt-scan-{iid}",
                    ext="json",
                )
            )
            execution_reply_coherence_blocker_receipt = str(
                runtime_temp_file(
                    channel="response-stamp",
                    operation="scan",
                    identity_id=iid,
                    stem=f"identity-execution-reply-coherence-blocker-receipt-scan-{iid}",
                    ext="json",
                )
            )
            required_gate_bundle_run_id = f"scan-{layer}-{iid}"
            required_gate_bundle_receipt = str(
                runtime_temp_file(
                    channel="required-gate-bundle",
                    operation="scan",
                    identity_id=iid,
                    run_token=layer,
                    stem=f"required-gate-bundle-scan-{layer}-{iid}",
                    ext="json",
                )
            )
            required_gate_bundle_receipt_probe = str(
                runtime_temp_file(
                    channel="required-gate-bundle",
                    operation="validate",
                    identity_id=iid,
                    run_token=f"{layer}-validate-probe",
                    stem=f"required-gate-bundle-scan-validate-probe-{layer}-{iid}",
                    ext="json",
                )
            )
            vibe_pack_out_root = str(named_temp_root("vibe-coding-feeding-packs"))
            capability_fit_out_root = str(named_temp_root("capability-fit-matrices"))
            current_round_anchor_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
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
                    "--identity-home",
                    str(catalog.parent.resolve()),
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
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "actor_session_multibinding_concurrency": [
                    "python3",
                    "scripts/validate_actor_session_multibinding_concurrency.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
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
                "session_refresh_status": [
                    "python3",
                    "scripts/validate_identity_session_refresh_status.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--actor-id",
                    actor_id,
                    "--operation",
                    "scan",
                    "--baseline-policy",
                    "warn",
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
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--view",
                    "external",
                    "--disclosure-level",
                    "standard",
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
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--stamp-json",
                    stamp_artifact,
                    "--force-check",
                    "--enforce-user-visible-gate",
                    "--operation",
                    "scan",
                    "--blocker-receipt-out",
                    stamp_blocker_receipt,
                    "--json-only",
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
                    "--json-only",
                ],
                "reply_identity_context_first_line": [
                    "python3",
                    "scripts/validate_reply_identity_context_first_line.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--stamp-json",
                    stamp_artifact,
                    "--force-check",
                    "--enforce-first-line-gate",
                    "--operation",
                    "scan",
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--blocker-receipt-out",
                    reply_first_line_blocker_receipt,
                    "--json-only",
                ],
                "layer_intent_resolution": [
                    "python3",
                    "scripts/validate_layer_intent_resolution.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--stamp-json",
                    stamp_artifact,
                    "--force-check",
                    "--enforce-layer-intent-gate",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "send_time_reply_gate": [
                    "python3",
                    "scripts/final_emit_governed.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--body-text",
                    "SCAN_SEND_TIME_REPLY_BODY",
                    "--out-reply-file",
                    send_time_reply_file,
                    "--blocker-receipt-out",
                    send_time_reply_gate_blocker_receipt,
                    "--outlet-channel-id",
                    "final_emit_governed",
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--json-only",
                ],
                "send_time_reply_gate_validate": [
                    "python3",
                    "scripts/validate_send_time_reply_gate.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--reply-file",
                    send_time_reply_file,
                    "--force-check",
                    "--enforce-send-time-gate",
                    "--reply-outlet-guard-applied",
                    "--outlet-channel-id",
                    "final_emit_governed",
                    "--reply-transport-ref",
                    send_time_reply_file,
                    "--operation",
                    "scan",
                    "--blocker-receipt-out",
                    send_time_reply_gate_blocker_receipt,
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--json-only",
                ],
                "headstamp_recurrence_closure": [
                    "python3",
                    "scripts/validate_headstamp_recurrence_closure.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--json-only",
                ],
                "execution_reply_identity_coherence": [
                    "python3",
                    "scripts/validate_execution_reply_identity_coherence.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--stamp-json",
                    stamp_artifact,
                    "--force-check",
                    "--enforce-coherence-gate",
                    "--operation",
                    "scan",
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--blocker-receipt-out",
                    execution_reply_coherence_blocker_receipt,
                    "--json-only",
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
                "semantic_routing_guard": [
                    "python3",
                    "scripts/validate_semantic_routing_guard.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "instance_protocol_split_receipt": [
                    "python3",
                    "scripts/validate_instance_protocol_split_receipt.py",
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
                "protocol_vendor_semantic_isolation": [
                    "python3",
                    "scripts/validate_protocol_vendor_semantic_isolation.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "external_source_trust_chain": [
                    "python3",
                    "scripts/validate_external_source_trust_chain.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "protocol_data_sanitization_boundary": [
                    "python3",
                    "scripts/validate_protocol_data_sanitization_boundary.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "platform_optimization_discovery_trigger": [
                    "python3",
                    "scripts/trigger_platform_optimization_discovery.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "discovery_requiredization": [
                    "python3",
                    "scripts/validate_discovery_requiredization.py",
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
                "vibe_coding_feeding_pack": [
                    "python3",
                    "scripts/build_vibe_coding_feeding_pack.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--out-root",
                    vibe_pack_out_root,
                    "--json-only",
                ],
                "capability_fit_optimization": [
                    "python3",
                    "scripts/validate_identity_capability_fit_optimization.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "capability_composition_before_discovery": [
                    "python3",
                    "scripts/validate_capability_composition_before_discovery.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "capability_fit_review_freshness": [
                    "python3",
                    "scripts/validate_capability_fit_review_freshness.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "capability_fit_roundtable_evidence": [
                    "python3",
                    "scripts/validate_capability_fit_roundtable_evidence.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "capability_fit_review_trigger": [
                    "python3",
                    "scripts/trigger_capability_fit_review.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "capability_fit_matrix_builder": [
                    "python3",
                    "scripts/build_capability_fit_matrix.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--out-root",
                    capability_fit_out_root,
                    "--json-only",
                ],
                "vendor_namespace_separation": [
                    "python3",
                    "scripts/validate_vendor_namespace_separation.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "work_layer_gate_set_routing": [
                    "python3",
                    "scripts/validate_work_layer_gate_set_routing.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--applied-gate-set",
                    lane_applied_gate_set,
                    "--force-check",
                    "--json-only",
                ],
                "protocol_feedback_reply_channel": [
                    "python3",
                    "scripts/validate_protocol_feedback_reply_channel.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--force-check",
                    "--json-only",
                ],
                "protocol_feedback_bootstrap_ready": [
                    "python3",
                    "scripts/validate_protocol_feedback_bootstrap_ready.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--force-check",
                    "--json-only",
                ],
                "protocol_entry_candidate_bridge": [
                    "python3",
                    "scripts/validate_protocol_entry_candidate_bridge.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--force-check",
                    "--json-only",
                ],
                "protocol_inquiry_followup_chain": [
                    "python3",
                    "scripts/validate_protocol_inquiry_followup_chain.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--force-check",
                    "--json-only",
                ],
                "protocol_feedback_sidecar": [
                    "python3",
                    "scripts/validate_protocol_feedback_sidecar_contract.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--current-round-anchor-utc",
                    current_round_anchor_utc,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "instance_base_repo_write_boundary": [
                    "python3",
                    "scripts/validate_instance_base_repo_write_boundary.py",
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
                "protocol_feedback_ssot_archival": [
                    "python3",
                    "scripts/validate_protocol_feedback_ssot_archival.py",
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
                "required_contract_coverage": [
                    "python3",
                    "scripts/validate_required_contract_coverage.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--json-only",
                ],
                "unlock_formula_automation": [
                    "python3",
                    "scripts/validate_unlock_formula.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "release_plane_cloud_evidence": [
                    "python3",
                    "scripts/validate_release_plane_cloud_evidence.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "cross_cwd_absolute_input": [
                    "python3",
                    "scripts/validate_cross_cwd_absolute_input.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog.resolve()),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "run_id_report_selection": [
                    "python3",
                    "scripts/validate_run_id_report_selection.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "phase_bootstrap_before_strict": [
                    "python3",
                    "scripts/validate_phase_bootstrap_before_strict.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "tmp_collision_safety": [
                    "python3",
                    "scripts/validate_tmp_collision_safety.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "handoff_collab_freshness_rotation": [
                    "python3",
                    "scripts/validate_handoff_collab_freshness_rotation.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "protocol_feedback_atomic_emit": [
                    "python3",
                    "scripts/validate_protocol_feedback_atomic_emit.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "capability_boundary_classification": [
                    "python3",
                    "scripts/validate_capability_boundary_classification.py",
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
                "promotion_evidence_pipeline": [
                    "python3",
                    "scripts/validate_promotion_pipeline.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "outlet_regression_matrix": [
                    "python3",
                    "scripts/validate_outlet_matrix.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "sidecar_cwd_parity": [
                    "python3",
                    "scripts/validate_sidecar_cwd_parity.py",
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
                "docs_bridge_consistency": [
                    "python3",
                    "scripts/validate_docs_bridge_consistency.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "contract_mapping_coverage": [
                    "python3",
                    "scripts/validate_contract_mapping_coverage.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "prompt_bootstrap_capability": [
                    "python3",
                    "scripts/validate_prompt_bootstrap_capability.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "prompt_capability_matrix": [
                    "python3",
                    "scripts/validate_prompt_capability_matrix.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "refresh_strict_business_interference": [
                    "python3",
                    "scripts/validate_refresh_strict_business_interference.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "kernel_ssot_source": [
                    "python3",
                    "scripts/validate_kernel_ssot_source.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "prompt_derivation_conformance": [
                    "python3",
                    "scripts/validate_prompt_derivation_conformance.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "semantic_convergence": [
                    "python3",
                    "scripts/validate_semantic_convergence.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "prompt_kernel_executable_coupling": [
                    "python3",
                    "scripts/validate_prompt_kernel_executable_coupling.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "required_gate_bundle_runner": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--surface-label",
                    f"full_scan_{layer}",
                    "--operation",
                    "scan",
                    "--out",
                    required_gate_bundle_receipt,
                    "--json-only",
                ],
                "required_gate_bundle_runner_shadow": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--surface-label",
                    f"full_scan_{layer}_validate_probe",
                    "--operation",
                    "scan",
                    "--out",
                    required_gate_bundle_receipt_probe,
                    "--json-only",
                ],
                "required_gate_recurrence_escalator": [
                    "python3",
                    "scripts/validate_required_gate_recurrence_escalator.py",
                    "--identity-id",
                    iid,
                    "--surface",
                    "full_scan",
                    "--operation",
                    "scan",
                    "--receipt",
                    required_gate_bundle_receipt,
                    "--enforce-blocking",
                    "--json-only",
                ],
                "required_gate_tuple_parity": [
                    "python3",
                    "scripts/validate_required_gate_tuple_parity.py",
                    "--receipt",
                    required_gate_bundle_receipt,
                    "--receipt",
                    required_gate_bundle_receipt_probe,
                    "--require-distinct-surface-labels",
                    "--json-only",
                ],
                "cross_verification_tracks": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--target-name",
                    "cross_verification_tracks",
                    "--surface-label",
                    f"full_scan_{layer}_target_probe",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "intake_evidence_quorum": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--target-name",
                    "intake_evidence_quorum",
                    "--surface-label",
                    f"full_scan_{layer}_target_probe",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "route_version_pinning": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--target-name",
                    "route_version_pinning",
                    "--surface-label",
                    f"full_scan_{layer}_target_probe",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "fallback_taxonomy_normalization": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--target-name",
                    "fallback_taxonomy_normalization",
                    "--surface-label",
                    f"full_scan_{layer}_target_probe",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "dedup_monotonicity": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--target-name",
                    "dedup_monotonicity",
                    "--surface-label",
                    f"full_scan_{layer}_target_probe",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "cross_workflow_schema": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--target-name",
                    "cross_workflow_schema",
                    "--surface-label",
                    f"full_scan_{layer}_target_probe",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "skill_path_integrity": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--target-name",
                    "skill_path_integrity",
                    "--surface-label",
                    f"full_scan_{layer}_target_probe",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "execution_target_tuple_isolation": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--target-name",
                    "execution_target_tuple_isolation",
                    "--surface-label",
                    f"full_scan_{layer}_target_probe",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "multimodal_plugin_enforcement": [
                    "python3",
                    "scripts/required_gate_bundle_runner.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--run-id",
                    required_gate_bundle_run_id,
                    "--send-time-gate-status",
                    "NOT_APPLICABLE",
                    "--outlet-bypass-detected",
                    "false",
                    "--final-emit-contract-status",
                    "NOT_APPLICABLE",
                    "--final-emit-policy-mode",
                    "tool_choice_required",
                    "--final-emit-schema-status",
                    "NOT_APPLICABLE",
                    "--actor-id",
                    actor_id,
                    "--resolved-work-layer",
                    effective_work_layer,
                    "--resolved-source-layer",
                    effective_source_layer,
                    "--lock-state",
                    "LOCK_MATCH",
                    "--target-name",
                    "multimodal_plugin_enforcement",
                    "--surface-label",
                    f"full_scan_{layer}_target_probe",
                    "--operation",
                    "scan",
                    "--json-only",
                ],
                "replay_archive_contract": [
                    "python3",
                    "scripts/validate_replay_archive_contract.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--operation",
                    "scan",
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
                "protocol_version_alignment": [
                    "python3",
                    "scripts/validate_identity_protocol_version_alignment.py",
                    "--identity-id",
                    iid,
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--operation",
                    "scan",
                    "--alignment-policy",
                    "warn",
                    "--json-only",
                ],
                "e2e_hermetic_runtime_import": [
                    "python3",
                    "scripts/validate_e2e_hermetic_runtime_import.py",
                    "--operation",
                    "scan",
                    "--pythonpath-bootstrap-mode",
                    "internal_bootstrap",
                    "--json-only",
                ],
            }
            if layer_intent_text:
                for key in (
                    "response_stamp_render",
                    "send_time_reply_gate",
                    "layer_intent_resolution",
                    "reply_identity_context_first_line",
                    "send_time_reply_gate_validate",
                    "execution_reply_identity_coherence",
                    "protocol_feedback_bootstrap_ready",
                    "protocol_entry_candidate_bridge",
                    "protocol_inquiry_followup_chain",
                    "work_layer_gate_set_routing",
                ):
                    checks[key].extend(["--layer-intent-text", layer_intent_text])
            if effective_work_layer:
                checks["response_stamp_render"].extend(["--work-layer", effective_work_layer])
                for key in (
                    "layer_intent_resolution",
                    "reply_identity_context_first_line",
                    "send_time_reply_gate_validate",
                    "execution_reply_identity_coherence",
                    "protocol_feedback_bootstrap_ready",
                    "protocol_entry_candidate_bridge",
                    "protocol_inquiry_followup_chain",
                    "work_layer_gate_set_routing",
                ):
                    checks[key].extend(["--expected-work-layer", effective_work_layer])
                checks["send_time_reply_gate"].extend(["--work-layer", effective_work_layer])
            if effective_source_layer:
                checks["response_stamp_render"].extend(["--source-layer", effective_source_layer])
                for key in (
                    "layer_intent_resolution",
                    "reply_identity_context_first_line",
                    "send_time_reply_gate_validate",
                    "execution_reply_identity_coherence",
                ):
                    checks[key].extend(["--expected-source-layer", effective_source_layer])
                checks["send_time_reply_gate"].extend(["--source-layer", effective_source_layer])
                for key in (
                    "protocol_feedback_bootstrap_ready",
                    "protocol_entry_candidate_bridge",
                    "protocol_inquiry_followup_chain",
                    "work_layer_gate_set_routing",
                ):
                    checks[key].extend(["--source-layer", effective_source_layer])
            for key in (
                "response_stamp_render",
                "reply_identity_context_first_line",
                "send_time_reply_gate_validate",
                "execution_reply_identity_coherence",
            ):
                cmd = checks.get(key)
                if isinstance(cmd, list) and "--actor-id" not in cmd:
                    cmd.extend(["--actor-id", actor_id])
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
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
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
                    cap_report_cmd = [
                        "python3",
                        "scripts/validate_identity_capability_activation.py",
                        "--identity-id",
                        iid,
                        "--report",
                        str(latest_report),
                    ]
                    report_meta: dict[str, Any] = {}
                    try:
                        loaded = json.loads(latest_report.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            report_meta = loaded
                    except Exception:
                        report_meta = {}
                    report_all_ok = bool(report_meta.get("all_ok"))
                    report_writeback_status = str(report_meta.get("writeback_status", "")).strip().upper()
                    report_permission_state = str(report_meta.get("permission_state", "")).strip().upper()
                    if report_all_ok and report_writeback_status == "WRITTEN" and report_permission_state == "WRITEBACK_WRITTEN":
                        cap_report_cmd.append("--require-activated")
                    checks["capability_activation_report"] = cap_report_cmd
                    sidecar_cmd = checks.get("protocol_feedback_sidecar")
                    if isinstance(sidecar_cmd, list):
                        if "--report" not in sidecar_cmd:
                            sidecar_cmd.extend(["--report", str(latest_report)])
                        report_run_id = str(report_meta.get("run_id", "")).strip()
                        if report_run_id and "--run-id" not in sidecar_cmd:
                            sidecar_cmd.extend(["--run-id", report_run_id])
                    mm_cmd = checks.get("multimodal_plugin_enforcement")
                    if isinstance(mm_cmd, list) and "--report-selected-path" not in mm_cmd:
                        mm_cmd.extend(["--report-selected-path", str(latest_report)])
            for name, cmd in checks.items():
                r = _run(cmd, cwd=repo_root)
                check_payload: dict[str, Any] = {"rc": r.rc, "ok": r.ok, "tail": r.tail}
                if name in {"capability_activation_preflight", "capability_activation_report"}:
                    cap_status, cap_code = _extract_capability_signal(r.stdout)
                    if cap_status:
                        check_payload["capability_activation_status"] = cap_status
                    if cap_code:
                        check_payload["capability_activation_error_code"] = cap_code
                    if cap_code == "IP-CAP-003":
                        check_payload["env_auth_blocked"] = True
                    if name == "capability_activation_preflight" and r.rc != 0 and cap_code == "IP-CAP-003":
                        fallback_cmd = _replace_activation_policy(cmd, "route-any-ready")
                        fallback = _run(fallback_cmd, cwd=repo_root)
                        fb_status, fb_code = _extract_capability_signal(fallback.stdout)
                        check_payload["capability_activation_fallback_attempted"] = True
                        check_payload["capability_activation_fallback_policy"] = "route-any-ready"
                        check_payload["capability_activation_fallback_rc"] = fallback.rc
                        check_payload["capability_activation_fallback_tail"] = fallback.tail
                        if fb_status:
                            check_payload["capability_activation_fallback_status"] = fb_status
                        if fb_code:
                            check_payload["capability_activation_fallback_error_code"] = fb_code
                        if fallback.ok:
                            check_payload["rc"] = 0
                            check_payload["ok"] = True
                            check_payload["tail"] = fallback.tail
                            check_payload["capability_activation_status"] = fb_status or "ACTIVATED"
                            check_payload["capability_activation_error_code"] = fb_code
                            check_payload["capability_activation_policy_effective"] = "route-any-ready"
                if name == "required_contract_coverage":
                    coverage_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "required_contract_total",
                        "required_contract_passed",
                        "required_contract_coverage_rate",
                        "discovery_required_total",
                        "discovery_required_passed",
                        "discovery_required_coverage_rate",
                        "discovery_required_gate_failed",
                        "skipped_contract_count",
                        "failed_required_contract_count",
                        "failed_optional_contract_count",
                    ):
                        if k in coverage_doc:
                            check_payload[k] = coverage_doc.get(k)
                if name == "unlock_formula_automation":
                    unlock_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "unlock_formula_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "unlock_allowed",
                        "decision_gates",
                        "p0_total",
                        "p0_done",
                        "p0_not_done_refs",
                        "audit_signoff_status",
                        "env_blockers",
                        "protocol_blockers",
                        "formula_input_digest",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in unlock_doc:
                            check_payload[k] = unlock_doc.get(k)
                if name == "release_plane_cloud_evidence":
                    release_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "release_plane_cloud_evidence_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "release_plane_status",
                        "conditions",
                        "target_branch",
                        "release_head_sha",
                        "required_gates_run_id",
                        "run_url",
                        "workflow_file_sha",
                        "run_head_sha",
                        "run_workflow_file_sha",
                        "checks_json",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in release_doc:
                            check_payload[k] = release_doc.get(k)
                if name == "cross_cwd_absolute_input":
                    cross_cwd_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "cross_cwd_absolute_input_status",
                        "cwd_parity_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "repo_catalog_input",
                        "repo_catalog_is_absolute",
                        "repo_cwd_resolved_repo_catalog",
                        "tmp_cwd_resolved_repo_catalog",
                        "repo_catalog_exists",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in cross_cwd_doc:
                            check_payload[k] = cross_cwd_doc.get(k)
                if name == "run_id_report_selection":
                    run_selector_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "run_id_report_selection_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "run_id",
                        "selection_strategy",
                        "report_selected_path",
                        "candidate_count",
                        "candidate_paths",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in run_selector_doc:
                            check_payload[k] = run_selector_doc.get(k)
                if name == "phase_bootstrap_before_strict":
                    phase_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "phase_bootstrap_before_strict_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "report_path",
                        "phase_a_refresh_applied",
                        "phase_b_strict_revalidate_status",
                        "phase_trace_status",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in phase_doc:
                            check_payload[k] = phase_doc.get(k)
                if name == "tmp_collision_safety":
                    tmp_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "tmp_collision_safety_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "tmp_root",
                        "generated_paths",
                        "collision_count",
                        "unique_path_count",
                        "path_scope_guard_status",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in tmp_doc:
                            check_payload[k] = tmp_doc.get(k)
                if name == "handoff_collab_freshness_rotation":
                    fresh_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "handoff_collab_freshness_rotation_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "rotation_applied",
                        "freshness_age_days",
                        "rotation_receipt_ref",
                        "freshness_status",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in fresh_doc:
                            check_payload[k] = fresh_doc.get(k)
                if name == "protocol_feedback_atomic_emit":
                    atomic_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "protocol_feedback_atomic_emit_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "transaction_id",
                        "batch_ref",
                        "index_ref",
                        "receipt_ref",
                        "receipt_path",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in atomic_doc:
                            check_payload[k] = atomic_doc.get(k)
                if name == "capability_boundary_classification":
                    cap_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "capability_boundary_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "boundary_classification",
                        "classification_source",
                        "capability_activation_status",
                        "capability_activation_error_code",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in cap_doc:
                            check_payload[k] = cap_doc.get(k)
                if name == "promotion_evidence_pipeline":
                    promo_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "promotion_pipeline_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "decision_hash",
                        "input_hash",
                        "reviewer_role",
                        "reviewer_signature_ref",
                        "evidence_bundle_refs",
                        "receipt_path",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in promo_doc:
                            check_payload[k] = promo_doc.get(k)
                if name == "outlet_regression_matrix":
                    outlet_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "outlet_matrix_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "matrix_positive_status",
                        "matrix_negative_status",
                        "cross_cwd_parity_status",
                        "send_time_gate_status",
                        "governed_outlet_enforced",
                        "outlet_channel_id",
                        "outlet_bypass_detected",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in outlet_doc:
                            check_payload[k] = outlet_doc.get(k)
                if name == "sidecar_cwd_parity":
                    sidecar_cwd_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "sidecar_cwd_parity_status",
                        "cwd_parity_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "passthrough_digest",
                        "root_digest",
                        "temp_digest",
                        "sidecar_contract_status",
                        "sidecar_error_code",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in sidecar_cwd_doc:
                            check_payload[k] = sidecar_cwd_doc.get(k)
                if name == "docs_bridge_consistency":
                    bridge_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "bridge_consistency_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "contradiction_pairs",
                        "governance_anchor_refs",
                        "review_anchor_refs",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in bridge_doc:
                            check_payload[k] = bridge_doc.get(k)
                if name == "contract_mapping_coverage":
                    map_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "contract_mapping_coverage_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "total_requirements",
                        "p0_total",
                        "mapped_total",
                        "p0_mapped",
                        "coverage_rate",
                        "p0_coverage_rate",
                        "orphan_count",
                        "unmapped_p0_requirements",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in map_doc:
                            check_payload[k] = map_doc.get(k)
                if name == "prompt_bootstrap_capability":
                    prompt_bootstrap_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "prompt_bootstrap_contract_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "capability_driver_required_total",
                        "capability_driver_present_total",
                        "capability_driver_coverage_rate",
                        "missing_capability_drivers",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in prompt_bootstrap_doc:
                            check_payload[k] = prompt_bootstrap_doc.get(k)
                if name == "prompt_capability_matrix":
                    prompt_matrix_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "prompt_capability_matrix_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "capability_driver_required_total",
                        "capability_driver_present_total",
                        "capability_driver_coverage_rate",
                        "missing_capability_drivers",
                        "discovery_requiredized_all",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in prompt_matrix_doc:
                            check_payload[k] = prompt_matrix_doc.get(k)
                if name == "refresh_strict_business_interference":
                    interference_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "refresh_strict_business_interference_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "refresh_receipt_ref",
                        "strict_receipt_ref",
                        "refresh_status",
                        "strict_status",
                        "interference_row_count_refresh",
                        "interference_row_count_strict",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in interference_doc:
                            check_payload[k] = interference_doc.get(k)
                if name == "kernel_ssot_source":
                    ssot_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "kernel_ssot_source_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "canonical_source_paths",
                        "missing_source_paths",
                        "ssot_validator_rc",
                        "ssot_validator_tail",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in ssot_doc:
                            check_payload[k] = ssot_doc.get(k)
                if name == "prompt_derivation_conformance":
                    derivation_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "prompt_derivation_conformance_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "kernel_contract_version",
                        "kernel_contract_digest",
                        "derived_from_contract_ids",
                        "overlay_digest",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in derivation_doc:
                            check_payload[k] = derivation_doc.get(k)
                if name == "semantic_convergence":
                    semantic_conv_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "semantic_convergence_status",
                        "semantic_convergence_error_code",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "lineage_ref",
                        "semantic_tuple_update",
                        "semantic_tuple_three_plane",
                        "semantic_tuple_full_scan",
                        "mismatch_count",
                        "mismatch_fields",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in semantic_conv_doc:
                            check_payload[k] = semantic_conv_doc.get(k)
                if name == "prompt_kernel_executable_coupling":
                    coupling_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "prompt_kernel_executable_coupling_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "kernel_contract_ref",
                        "validator_ref",
                        "actor_context_explicit",
                        "routing_validator_rc",
                        "routing_validator_tail",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in coupling_doc:
                            check_payload[k] = coupling_doc.get(k)
                if name == "required_gate_bundle_runner":
                    bundle_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "bundle_contract_id",
                        "bundle_key",
                        "bundle_status",
                        "error_code",
                        "identity_id",
                        "catalog_path",
                        "operation",
                        "contract_mapping",
                        "mapping_errors",
                        "missing_targets",
                        "surface_label",
                        "actor_id",
                        "resolved_work_layer",
                        "resolved_source_layer",
                        "lock_state",
                        "run_id_binding",
                        "report_selected_path",
                        "required_contract",
                        "failed_required_contract_count",
                        "row_contract_error_count",
                        "send_time_gate_status",
                        "outlet_bypass_detected",
                        "final_emit_contract_status",
                        "final_emit_policy_mode",
                        "final_emit_schema_status",
                        "results",
                    ):
                        if k in bundle_doc:
                            check_payload[k] = bundle_doc.get(k)
                    if "bundle_status" in bundle_doc:
                        check_payload["required_gate_bundle_runner_status"] = bundle_doc.get("bundle_status")
                if name == "required_gate_bundle_runner_shadow":
                    bundle_shadow_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "bundle_contract_id",
                        "bundle_key",
                        "bundle_status",
                        "error_code",
                        "identity_id",
                        "catalog_path",
                        "operation",
                        "contract_mapping",
                        "mapping_errors",
                        "missing_targets",
                        "surface_label",
                        "actor_id",
                        "resolved_work_layer",
                        "resolved_source_layer",
                        "lock_state",
                        "run_id_binding",
                        "report_selected_path",
                        "required_contract",
                        "failed_required_contract_count",
                        "row_contract_error_count",
                        "send_time_gate_status",
                        "outlet_bypass_detected",
                        "final_emit_contract_status",
                        "final_emit_policy_mode",
                        "final_emit_schema_status",
                        "results",
                    ):
                        if k in bundle_shadow_doc:
                            check_payload[k] = bundle_shadow_doc.get(k)
                    if "bundle_status" in bundle_shadow_doc:
                        check_payload["required_gate_bundle_runner_shadow_status"] = bundle_shadow_doc.get("bundle_status")
                if name == "required_gate_recurrence_escalator":
                    rec_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "required_gate_recurrence_status",
                        "error_code",
                        "escalation_level",
                        "identity_id",
                        "surface",
                        "operation",
                        "receipt_path",
                        "state_path",
                        "new_event_count",
                        "tracked_event_count",
                        "l1_error_families",
                        "l2_error_families",
                        "l3_error_families",
                        "family_metrics",
                        "stale_reasons",
                    ):
                        if k in rec_doc:
                            check_payload[k] = rec_doc.get(k)
                if name == "required_gate_tuple_parity":
                    parity_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "required_gate_tuple_parity_status",
                        "error_code",
                        "tuple_fields",
                        "core_tuple_fields",
                        "conditional_tuple_fields",
                        "receipts_checked",
                        "surface_labels_checked",
                        "min_receipts",
                        "require_distinct_surface_labels",
                        "require_distinct_operations",
                        "operations_checked",
                        "missing_operations",
                        "duplicate_operations",
                        "parity_contract_reasons",
                        "missing_surface_labels",
                        "duplicate_surface_labels",
                        "load_errors",
                        "missing_fields",
                        "mismatches",
                        "stale_reasons",
                    ):
                        if k in parity_doc:
                            check_payload[k] = parity_doc.get(k)
                if name == "cross_verification_tracks":
                    cross_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "cross_verification_tracks_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "cross_verification_bundle_id",
                        "source_url_set",
                        "reference_timestamp_utc",
                        "conflict_reconciliation_note",
                        "missing_tracks",
                        "missing_metadata_fields",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in cross_doc:
                            check_payload[k] = cross_doc.get(k)
                if name == "intake_evidence_quorum":
                    quorum_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "intake_evidence_quorum_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "cross_verification_bundle_id",
                        "source_url_set",
                        "reference_timestamp_utc",
                        "conflict_reconciliation_note",
                        "missing_tracks",
                        "missing_metadata_fields",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in quorum_doc:
                            check_payload[k] = quorum_doc.get(k)
                if name == "route_version_pinning":
                    pin_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "pin_status",
                        "pin_error_code",
                        "required_contract",
                        "auto_required_signal",
                        "route_endpoint",
                        "workflow_id",
                        "workflow_publish_version",
                        "pin_proof_ref",
                        "expected_route_endpoint",
                        "expected_workflow_id",
                        "expected_workflow_publish_version",
                        "mismatch_fields",
                        "receipt_path",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in pin_doc:
                            check_payload[k] = pin_doc.get(k)
                if name == "fallback_taxonomy_normalization":
                    fn_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "fallback_taxonomy_normalization_status",
                        "normalization_error_code",
                        "required_contract",
                        "auto_required_signal",
                        "taxonomy_version",
                        "fallback_reason_row_count",
                        "fallback_reason_rows",
                        "unmapped_fallback_reasons",
                        "blocker_taxonomy_namespace_preserved",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in fn_doc:
                            check_payload[k] = fn_doc.get(k)
                if name == "dedup_monotonicity":
                    dedup_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "monotonicity_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "run_id",
                        "parallel_claims_requested",
                        "claim_rows_total",
                        "grouped_run_count",
                        "candidate_count",
                        "earliest_claim_ts",
                        "stable_tiebreaker",
                        "winner_id",
                        "winner_reason",
                        "tie_candidate_count",
                        "claims_path",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in dedup_doc:
                            check_payload[k] = dedup_doc.get(k)
                if name == "cross_workflow_schema":
                    xwf_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "cross_workflow_schema_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "run_id",
                        "route_action",
                        "quality_meta_state",
                        "dedup_state",
                        "evidence_hash",
                        "schema_version",
                        "hash_consistency_status",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in xwf_doc:
                            check_payload[k] = xwf_doc.get(k)
                if name == "skill_path_integrity":
                    spath_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "path_integrity_status",
                        "path_integrity_error_code",
                        "required_contract",
                        "auto_required_signal",
                        "layout_mode",
                        "active_repo_root",
                        "active_runtime_root",
                        "required_skills",
                        "missing_skill_paths",
                        "out_of_layout_skill_paths",
                        "allowed_skill_roots",
                        "skill_path_rows",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in spath_doc:
                            check_payload[k] = spath_doc.get(k)
                if name == "execution_target_tuple_isolation":
                    xtuple_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "execution_target_tuple_isolation_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "execution_target_kind",
                        "execution_target_key",
                        "execution_target_ref",
                        "route_conflict_status",
                        "route_conflict_error_code",
                        "conflict_key_mode",
                        "override_non_bypass_status",
                        "process_call_support_status",
                        "tuple_fields_present",
                        "tuple_fields_missing",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in xtuple_doc:
                            check_payload[k] = xtuple_doc.get(k)
                if name == "multimodal_plugin_enforcement":
                    mm_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "multimodal_plugin_enforcement_status",
                        "multimodal_runtime_evidence_status",
                        "multimodal_preflight_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "plugin_registry_status",
                        "plugin_naming_status",
                        "plugin_schema_status",
                        "plugin_threshold_status",
                        "plugin_path_status",
                        "plugin_copy_policy_status",
                        "provider_config_status",
                        "provider_profile_id",
                        "plugin_contract_owner",
                        "plugin_resolution_mode",
                        "report_selected_path",
                        "runtime_report_path",
                        "runtime_report_run_id",
                        "multimodal_calls",
                        "multimodal_resolved",
                        "multimodal_unresolved",
                        "multimodal_errors",
                        "multimodal_retry_calls",
                        "runtime_gate_mode",
                        "runtime_gate_required_confidence",
                        "multimodal_runtime_evidence_refs",
                        "forbidden_copy_refs",
                        "stale_reasons",
                        "evidence_ref",
                    ):
                        if k in mm_doc:
                            check_payload[k] = mm_doc.get(k)
                if name == "replay_archive_contract":
                    replay_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "replay_archive_contract_status",
                        "error_code",
                        "replay_case_total",
                        "replay_case_passed",
                        "replay_case_failed",
                        "stale_reasons",
                        "evidence_ref",
                        "out_path",
                    ):
                        if k in replay_doc:
                            check_payload[k] = replay_doc.get(k)
                if name == "semantic_routing_guard":
                    semantic_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "semantic_routing_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "feedback_batch_path",
                        "intent_domain",
                        "intent_confidence",
                        "classifier_reason",
                        "legacy_namespace_refs",
                        "stale_reasons",
                    ):
                        if k in semantic_doc:
                            check_payload[k] = semantic_doc.get(k)
                if name == "instance_protocol_split_receipt":
                    split_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "instance_protocol_split_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "receipt_path",
                        "split_notice",
                        "instance_actions_ref",
                        "protocol_actions_ref",
                        "feedback_triggered",
                        "evidence_index_ref",
                        "feedback_paths",
                        "trigger_conditions",
                        "alias_fields_used",
                        "stale_reasons",
                    ):
                        if k in split_doc:
                            check_payload[k] = split_doc.get(k)
                if name == "work_layer_gate_set_routing":
                    lane_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "work_layer_gate_set_routing_status",
                        "error_code",
                        "work_layer",
                        "source_layer",
                        "applied_gate_set",
                        "protocol_context_detected",
                        "protocol_context_reasons",
                        "session_lane_lock",
                        "session_lane_lock_source",
                        "session_lane_lock_receipt",
                        "session_lane_lock_exit_receipt",
                        "lane_resolution_decision",
                        "lane_resolution_blocked",
                        "lane_resolution_error_code",
                        "lane_transition_reason",
                        "protocol_feedback_triggered",
                        "protocol_feedback_paths",
                        "pending_receipt_path",
                        "lane_lock_receipt_path",
                        "protocol_relevant_diff_detected",
                        "protocol_relevant_files",
                        "stale_reasons",
                    ):
                        if k in lane_doc:
                            check_payload[k] = lane_doc.get(k)
                if name == "discovery_requiredization":
                    dreq_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "discovery_requiredization_status",
                        "error_code",
                        "required_contract",
                        "required_contract_declared",
                        "auto_required_signal",
                        "requiredization_triggered",
                        "trigger_classes",
                        "window_rounds",
                        "feedback_batches",
                        "trigger_condition_flags",
                        "discovery_contract_required_state",
                        "requiredized_all_discovery_contracts",
                        "requiredization_receipt_path",
                        "requiredization_receipt_linked",
                        "evidence_index_path",
                        "ci_required_validators_missing",
                        "discovery_required_total",
                        "discovery_required_passed",
                        "discovery_required_coverage_rate",
                        "stale_reasons",
                    ):
                        if k in dreq_doc:
                            check_payload[k] = dreq_doc.get(k)
                if name == "protocol_vendor_semantic_isolation":
                    semantic_iso_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "protocol_vendor_semantic_isolation_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "feedback_batch_path",
                        "intent_domain",
                        "intent_confidence",
                        "intent_domain_before",
                        "intent_domain_after",
                        "switch_receipt_required",
                        "switch_receipt_present",
                        "switch_receipt_fields",
                        "protocol_vendor_refs",
                        "business_partner_refs",
                        "stale_reasons",
                    ):
                        if k in semantic_iso_doc:
                            check_payload[k] = semantic_iso_doc.get(k)
                if name == "external_source_trust_chain":
                    src_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "external_source_trust_chain_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "feedback_batch_path",
                        "allowed_trust_tiers",
                        "conclusion_required_tiers",
                        "source_row_count",
                        "conclusion_source_count",
                        "candidate_source_count",
                        "unknown_in_conclusion_refs",
                        "missing_tier_refs",
                        "missing_trace_refs",
                        "unknown_candidate_without_downgrade",
                        "stale_reasons",
                    ):
                        if k in src_doc:
                            check_payload[k] = src_doc.get(k)
                if name == "protocol_data_sanitization_boundary":
                    dsn_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "protocol_data_sanitization_boundary_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "feedback_batch_path",
                        "forbidden_key_hits",
                        "sensitive_pattern_hits",
                        "violation_count",
                        "stale_reasons",
                    ):
                        if k in dsn_doc:
                            check_payload[k] = dsn_doc.get(k)
                if name == "platform_optimization_discovery_trigger":
                    opt_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "platform_optimization_discovery_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "triggered",
                        "trigger_reason",
                        "discovery_scope",
                        "official_doc_retrieval_set",
                        "cross_validation_summary",
                        "upgrade_proposal_ref",
                        "feedback_batches",
                        "stale_reasons",
                    ):
                        if k in opt_doc:
                            check_payload[k] = opt_doc.get(k)
                if name == "vibe_coding_feeding_pack":
                    pack_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "vibe_coding_feeding_pack_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "pack_root",
                        "pack_id",
                        "pack_files",
                        "feedback_batch_path",
                        "feedback_batch_sha256",
                        "evidence_index_path",
                        "evidence_index_linked",
                        "deterministic_manifest_sha256",
                        "sanitization_check_passed",
                        "stale_reasons",
                    ):
                        if k in pack_doc:
                            check_payload[k] = pack_doc.get(k)
                if name == "capability_fit_optimization":
                    fit_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "capability_fit_optimization_status",
                        "error_code",
                        "required_contract",
                        "fit_matrix_path",
                        "matrix_candidate_count",
                        "selected_candidate_count",
                        "selected_candidate_ids",
                        "missing_required_fields",
                        "selected_missing_fields",
                        "next_review_at",
                        "review_interval_days",
                        "review_freshness_status",
                        "stale_reasons",
                    ):
                        if k in fit_doc:
                            check_payload[k] = fit_doc.get(k)
                if name == "capability_composition_before_discovery":
                    comp_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "compose_before_discovery_status",
                        "error_code",
                        "required_contract",
                        "fit_matrix_path",
                        "existing_composition_candidate_count",
                        "selected_candidate_type",
                        "decision_basis",
                        "stale_reasons",
                    ):
                        if k in comp_doc:
                            check_payload[k] = comp_doc.get(k)
                if name == "capability_fit_review_freshness":
                    fresh_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "capability_fit_review_freshness_status",
                        "error_code",
                        "required_contract",
                        "fit_matrix_path",
                        "selected_candidate_id",
                        "selected_candidate_type",
                        "next_review_at",
                        "review_interval_days",
                        "review_freshness_status",
                        "overdue_by_days",
                        "stale_reasons",
                    ):
                        if k in fresh_doc:
                            check_payload[k] = fresh_doc.get(k)
                if name == "capability_fit_roundtable_evidence":
                    round_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "capability_fit_roundtable_status",
                        "error_code",
                        "required_contract",
                        "fit_matrix_path",
                        "roundtable_evidence_path",
                        "selected_candidate_id",
                        "selected_candidate_type",
                        "roundtable_required",
                        "facts_count",
                        "inferences_count",
                        "selected_fact_refs",
                        "stale_reasons",
                    ):
                        if k in round_doc:
                            check_payload[k] = round_doc.get(k)
                if name == "capability_fit_review_trigger":
                    trig_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "capability_fit_review_trigger_status",
                        "error_code",
                        "required_contract",
                        "triggered",
                        "trigger_reason",
                        "fit_matrix_path",
                        "selected_candidate_id",
                        "selected_candidate_type",
                        "review_freshness_status",
                        "roundtable_required",
                        "roundtable_evidence_path",
                        "stale_reasons",
                    ):
                        if k in trig_doc:
                            check_payload[k] = trig_doc.get(k)
                if name == "capability_fit_matrix_builder":
                    builder_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "capability_fit_matrix_builder_status",
                        "error_code",
                        "required_contract",
                        "matrix_path",
                        "matrix_candidate_count",
                        "selected_candidate_count",
                        "selected_candidate_id",
                        "selected_candidate_type",
                        "inventory_snapshot_path",
                        "external_candidate_source_path",
                        "stale_reasons",
                    ):
                        if k in builder_doc:
                            check_payload[k] = builder_doc.get(k)
                if name == "vendor_namespace_separation":
                    namespace_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "vendor_namespace_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "feedback_root",
                        "protocol_vendor_file_count",
                        "business_partner_file_count",
                        "legacy_vendor_file_count",
                        "legacy_namespace_refs",
                        "stale_reasons",
                    ):
                        if k in namespace_doc:
                            check_payload[k] = namespace_doc.get(k)
                if name == "protocol_feedback_sidecar":
                    sidecar_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "sidecar_contract_status",
                        "sidecar_error_code",
                        "required_contract",
                        "auto_required_signal",
                        "requiredization_scope_decision",
                        "requiredization_scope_reason",
                        "requiredization_current_round_linked",
                        "current_round_anchor_utc",
                        "activity_correlation_status",
                        "activity_correlation_key",
                        "activity_unscoped_count",
                        "activity_ignored_missing_correlation_key_refs",
                        "activity_ignored_missing_anchor_refs",
                        "activity_ignored_pre_round_refs",
                        "enforce_blocking",
                        "escalation_required",
                        "escalation_decision",
                        "observability_escalation_required",
                        "observability_alert_level",
                        "observability_escalation_reason",
                        "blocking_error_codes",
                        "p0_violations",
                        "track_a",
                        "track_b",
                        "stale_reasons",
                    ):
                        if k in sidecar_doc:
                            check_payload[k] = sidecar_doc.get(k)
                if name == "instance_base_repo_write_boundary":
                    base_boundary_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "base_repo_write_boundary_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "report_selected_path",
                        "source_mode",
                        "allowlist_prefixes",
                        "denylist_prefixes",
                        "repo_relative_candidates",
                        "allowed_paths",
                        "blocked_paths",
                        "explicit_deny_hits",
                        "override_receipt_path",
                        "override_applied",
                        "stale_reasons",
                    ):
                        if k in base_boundary_doc:
                            check_payload[k] = base_boundary_doc.get(k)
                if name == "protocol_feedback_ssot_archival":
                    archival_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "feedback_ssot_archival_status",
                        "error_code",
                        "required_contract",
                        "auto_required_signal",
                        "feedback_root",
                        "outbox_dir",
                        "evidence_index_path",
                        "batch_file_count",
                        "batch_files",
                        "index_linked_batches",
                        "index_unlinked_batches",
                        "mirror_candidate_refs",
                        "stale_reasons",
                    ):
                        if k in archival_doc:
                            check_payload[k] = archival_doc.get(k)
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
                        "protocol_head_sha_at_run_start",
                        "baseline_reference_mode",
                        "current_protocol_head_sha",
                        "head_drift_detected",
                        "lag_commits",
                        "stale_reasons",
                    ):
                        if k in baseline_doc:
                            check_payload[k] = baseline_doc.get(k)
                if name == "protocol_version_alignment":
                    align_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "protocol_version_alignment_status",
                        "error_code",
                        "required_contract",
                        "operation",
                        "alignment_policy",
                        "report_selected_path",
                        "tuple_checks",
                        "stale_reasons",
                    ):
                        if k in align_doc:
                            check_payload[k] = align_doc.get(k)
                if name == "e2e_hermetic_runtime_import":
                    herm_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "e2e_hermetic_runtime_status",
                        "pythonpath_bootstrap_mode",
                        "import_preflight_status",
                        "import_preflight_error_code",
                        "missing_modules",
                        "stale_reasons",
                    ):
                        if k in herm_doc:
                            check_payload[k] = herm_doc.get(k)
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
                if name == "actor_session_multibinding_concurrency":
                    mb_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "actor_session_multibinding_status",
                        "error_code",
                        "binding_key_mode",
                        "session_entry_count",
                        "cas_checked",
                        "cas_conflict_detected",
                        "non_activation_mutation_detected",
                        "rebind_receipt_status",
                        "dropped_peer_session_count",
                        "stale_reasons",
                    ):
                        if k in mb_doc:
                            check_payload[k] = mb_doc.get(k)
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
                if name == "session_refresh_status":
                    refresh_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "session_refresh_status",
                        "error_code",
                        "actor_id",
                        "lease_status",
                        "pointer_consistency",
                        "risk_flags",
                        "next_action",
                        "baseline_status",
                        "baseline_error_code",
                        "report_protocol_commit_sha",
                        "protocol_head_sha_at_run_start",
                        "baseline_reference_mode",
                        "current_protocol_head_sha",
                        "head_drift_detected",
                        "lag_commits",
                        "report_selected_path",
                        "stale_reasons",
                    ):
                        if k in refresh_doc:
                            check_payload[k] = refresh_doc.get(k)
                if name == "response_stamp_validation":
                    stamp_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "stamp_status",
                        "error_code",
                        "stale_reasons",
                        "blocker_receipt_path",
                        "reply_sample_count",
                        "reply_stamp_missing_count",
                        "reply_stamp_missing_refs",
                    ):
                        if k in stamp_doc:
                            check_payload[k] = stamp_doc.get(k)
                if name == "response_stamp_blocker_receipt":
                    receipt_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "receipt_status",
                        "error_code",
                        "stale_reasons",
                    ):
                        if k in receipt_doc:
                            check_payload[k] = receipt_doc.get(k)
                if name == "reply_identity_context_first_line":
                    reply_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "reply_first_line_status",
                        "error_code",
                        "reply_first_line_missing_count",
                        "reply_first_line_missing_refs",
                        "reply_sample_count",
                        "reply_evidence_ref",
                        "blocker_receipt_path",
                        "stale_reasons",
                    ):
                        if k in reply_doc:
                            check_payload[k] = reply_doc.get(k)
                if name == "send_time_reply_gate":
                    send_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "send_time_gate_status",
                        "error_code",
                        "governed_outlet_enforced",
                        "outlet_channel_id",
                        "final_emit_channel_id",
                        "final_emit_policy_mode",
                        "final_emit_schema_id",
                        "final_emit_schema_status",
                        "final_emit_contract_status",
                        "outlet_preflight_receipt",
                        "outlet_bypass_detected",
                        "reply_evidence_mode",
                        "reply_evidence_ref",
                        "reply_sample_count",
                        "reply_first_line_missing_count",
                        "reply_first_line_missing_refs",
                        "blocker_receipt_path",
                        "stale_reasons",
                    ):
                        if k in send_doc:
                            check_payload[k] = send_doc.get(k)
                if name == "execution_reply_identity_coherence":
                    coherence_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "coherence_status",
                        "coherence_decision",
                        "error_code",
                        "command_catalog_ref",
                        "resolved_catalog_ref",
                        "reply_catalog_ref",
                        "command_identity_id",
                        "resolved_identity_id",
                        "reply_identity_id",
                        "command_actor_id",
                        "resolved_actor_id",
                        "reply_actor_id",
                        "mismatch_fields",
                        "reply_evidence_ref",
                        "blocker_receipt_path",
                        "stale_reasons",
                    ):
                        if k in coherence_doc:
                            check_payload[k] = coherence_doc.get(k)
                if name == "headstamp_recurrence_closure":
                    hs_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "headstamp_recurrence_closure_status",
                        "static_wiring_status",
                        "dynamic_replay_status",
                        "error_code",
                        "missing_wiring_items",
                        "dynamic_cases",
                        "stale_reasons",
                    ):
                        if k in hs_doc:
                            check_payload[k] = hs_doc.get(k)
                if name == "protocol_feedback_reply_channel":
                    channel_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "protocol_feedback_reply_channel_status",
                        "error_code",
                        "primary_channel_root",
                        "protocol_feedback_activity_detected",
                        "protocol_feedback_activity_refs",
                        "non_standard_primary_refs",
                        "mirror_reference_refs",
                        "split_receipt_requiredized",
                        "split_receipt_status",
                        "split_receipt_error_code",
                        "stale_reasons",
                    ):
                        if k in channel_doc:
                            check_payload[k] = channel_doc.get(k)
                if name == "protocol_feedback_bootstrap_ready":
                    boot_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "protocol_feedback_bootstrap_status",
                        "protocol_feedback_bootstrap_mode",
                        "bootstrap_created_paths",
                        "bootstrap_receipt_path",
                        "resolved_work_layer",
                        "protocol_triggered",
                        "protocol_lane_selected",
                        "error_code",
                        "stale_reasons",
                    ):
                        if k in boot_doc:
                            check_payload[k] = boot_doc.get(k)
                if name == "protocol_entry_candidate_bridge":
                    candidate_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "protocol_entry_candidate_status",
                        "protocol_entry_decision",
                        "candidate_reason",
                        "candidate_confidence",
                        "clarification_required",
                        "clarification_questions",
                        "candidate_seed_outbox_ref",
                        "candidate_seed_index_ref",
                        "candidate_promotion_status",
                        "error_code",
                        "stale_reasons",
                    ):
                        if k in candidate_doc:
                            check_payload[k] = candidate_doc.get(k)
                if name == "protocol_inquiry_followup_chain":
                    inquiry_doc = _parse_json_safely(r.stdout) or {}
                    for k in (
                        "protocol_inquiry_followup_chain_status",
                        "inquiry_state",
                        "followup_question_set",
                        "signal_origin",
                        "sanitization_paraphrase_ref",
                        "protocol_feedback_seed_ref",
                        "protocol_feedback_index_ref",
                        "followup_round_count",
                        "max_followup_rounds",
                        "evidence_ttl_hours",
                        "inquiry_requiredization_triggered",
                        "inquiry_requiredization_receipt_path",
                        "error_code",
                        "stale_reasons",
                    ):
                        if k in inquiry_doc:
                            check_payload[k] = inquiry_doc.get(k)
                item["checks"][name] = check_payload

            env = os.environ.copy()
            env["IDENTITY_CATALOG"] = str(catalog)
            three_plane = _run(
                [
                    "python3",
                    "scripts/report_three_plane_status.py",
                    "--identity-id",
                    iid,
                    "--actor-id",
                    actor_id,
                    "--session-id",
                    scan_session_id,
                    "--scope",
                    scan_scope_hint,
                    *(["--layer-intent-text", layer_intent_text] if layer_intent_text else []),
                    *(["--expected-work-layer", effective_work_layer] if effective_work_layer else []),
                    *(["--expected-source-layer", effective_source_layer] if effective_source_layer else []),
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
                if isinstance(tp.get("m2m_projection"), dict):
                    item["m2m_projection"] = tp.get("m2m_projection")
            if "m2m_projection" not in item:
                item["m2m_projection"] = _classify_m2m_projection(checks=item.get("checks", {}))
            payload["summary_m2m"]["total_identities"] += 1
            current_m2m = str(item["m2m_projection"].get("m2m_binding_closure_status", "")).upper()
            if current_m2m == "PASS":
                payload["summary_m2m"]["pass"] += 1
            else:
                payload["summary_m2m"]["fail"] += 1
            _update_target_m2m(iid, current_m2m)
            item["severity"] = _severity_for_row(item)
            _update_target_severity(iid, str(item["severity"]))
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
        payload["summary_unique_targets"] = {
            "total_identities": len(target_severity_map),
            "p0": sum(1 for severity in target_severity_map.values() if str(severity).upper() == "P0"),
            "p1": sum(1 for severity in target_severity_map.values() if str(severity).upper() == "P1"),
            "ok": sum(1 for severity in target_severity_map.values() if str(severity).upper() == "OK"),
        }
        payload["summary_unique_targets_m2m"] = {
            "total_identities": len(target_m2m_map),
            "pass": sum(1 for status in target_m2m_map.values() if str(status).upper() == "PASS"),
            "fail": sum(1 for status in target_m2m_map.values() if str(status).upper() == "FAIL"),
        }
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
