#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import resolve_actor_id
from response_stamp_common import DEFAULT_WORK_LAYER, resolve_layer_intent

PROTOCOL_PUBLISH_SCRIPTS = {
    "scripts/validate_changelog_updated.py",
    "scripts/validate_protocol_handoff_coupling.py",
    "scripts/validate_release_metadata_sync.py",
    "scripts/validate_release_freeze_boundary.py",
}


def _run(cmd: list[str]) -> int:
    print(f"[RUN] {' '.join(cmd)}")
    p = subprocess.run(cmd)
    if p.returncode != 0:
        print(f"[FAIL] command failed ({p.returncode}): {' '.join(cmd)}")
        return p.returncode
    return 0


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    print(f"[RUN] {' '.join(cmd)}")
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    if p.returncode != 0:
        print(f"[FAIL] command failed ({p.returncode}): {' '.join(cmd)}")
    return p.returncode, out, err


def _replace_activation_policy(cmd: list[str], policy: str) -> list[str]:
    out = list(cmd)
    if "--activation-policy" in out:
        idx = out.index("--activation-policy")
        if idx + 1 < len(out):
            out[idx + 1] = policy
            return out
    out.extend(["--activation-policy", policy])
    return out


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _boolish(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _git_rev(expr: str) -> str:
    p = subprocess.run(["git", "rev-parse", expr], check=True, capture_output=True, text=True)
    return p.stdout.strip()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _resolve_pack_path(catalog_path: str, identity_id: str) -> Path | None:
    p = Path(catalog_path).expanduser().resolve()
    if not p.exists():
        return None
    try:
        doc = _load_yaml(p)
    except Exception:
        return None
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        return None
    pack_raw = str((row or {}).get("pack_path", "")).strip()
    if not pack_raw:
        return None
    pack = Path(pack_raw).expanduser().resolve()
    return pack if pack.exists() else None


def _resolve_lane_context(*, layer_intent_text: str, expected_work_layer: str, expected_source_layer: str) -> dict[str, str]:
    resolved = resolve_layer_intent(
        explicit_work_layer=str(expected_work_layer or "").strip(),
        explicit_source_layer=str(expected_source_layer or "").strip(),
        intent_text=str(layer_intent_text or "").strip(),
        default_work_layer=DEFAULT_WORK_LAYER,
        default_source_layer="global",
    )
    work_layer = str(resolved.get("resolved_work_layer", DEFAULT_WORK_LAYER)).strip().lower() or DEFAULT_WORK_LAYER
    source_layer = str(resolved.get("resolved_source_layer", "global")).strip().lower() or "global"
    if work_layer == "instance":
        applied_gate_set = "instance_required_checks"
    elif work_layer == "protocol":
        applied_gate_set = "protocol_required_checks"
    else:
        applied_gate_set = "dual_unroutable"
    return {
        "work_layer": work_layer,
        "source_layer": source_layer,
        "applied_gate_set": applied_gate_set,
    }


def _route_release_seq_for_lane(seq: list[list[str]], *, work_layer: str) -> tuple[list[list[str]], list[str]]:
    if work_layer != "instance":
        return seq, []
    filtered: list[list[str]] = []
    skipped: list[str] = []
    for cmd in seq:
        script = cmd[1] if len(cmd) >= 2 else ""
        if script in PROTOCOL_PUBLISH_SCRIPTS:
            skipped.append(script)
            continue
        filtered.append(cmd)
    return filtered, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description="Run release-readiness validators in a deterministic order.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--scope", default="", help="explicit scope arbitration (REPO/USER/ADMIN/SYSTEM)")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    ap.add_argument(
        "--execution-report",
        default="",
        help="optional identity upgrade execution report path; when provided, enforce experience writeback linkage",
    )
    ap.add_argument(
        "--upgrade-report-dir",
        default="",
        help="optional explicit directory to search for auto-generated execution report",
    )
    ap.add_argument(
        "--catalog",
        default="",
        help="catalog path override. required unless IDENTITY_CATALOG is set.",
    )
    ap.add_argument(
        "--capability-activation-policy",
        choices=["strict-union", "route-any-ready"],
        default="strict-union",
        help=(
            "capability evaluation policy used by preflight and auto-generated update report. "
            "strict-union requires all declared route capabilities; route-any-ready allows progress when at least one route is ready."
        ),
    )
    ap.add_argument(
        "--execution-report-policy",
        choices=["strict", "warn"],
        default="strict",
        help=(
            "freshness policy for execution report binding preflight. "
            "strict fails early with IP-REL-001 on stale/mismatch reports; warn logs drift but continues."
        ),
    )
    ap.add_argument(
        "--baseline-policy",
        choices=["strict", "warn"],
        default="strict",
        help=(
            "protocol baseline freshness policy for execution report protocol_commit_sha vs current protocol HEAD. "
            "strict fails with IP-PBL-001 on stale baseline; warn logs drift but continues."
        ),
    )
    ap.add_argument(
        "--min-required-contract-coverage",
        type=float,
        default=-1.0,
        help=(
            "optional minimum required-contract coverage percentage (0-100) for tool/vendor closures. "
            "default disabled."
        ),
    )
    ap.add_argument(
        "--min-discovery-required-coverage",
        type=float,
        default=-1.0,
        help=(
            "optional minimum required-contract coverage percentage (0-100) for discovery subset "
            "(tool_installation/vendor_api_discovery/vendor_api_solution). default disabled."
        ),
    )
    ap.add_argument("--layer-intent-text", default="", help="optional natural-language layer intent for stamp render/validators")
    ap.add_argument("--expected-work-layer", default="", help="optional expected work_layer override for strict reply gates")
    ap.add_argument("--expected-source-layer", default="", help="optional expected source_layer override for strict reply gates")
    ap.add_argument(
        "--actor-id",
        default=os.environ.get("CODEX_ACTOR_ID", "assistant:codex"),
        help=(
            "explicit actor id for strict governed-outlet/headstamp recurrence closure checks. "
            "Defaults to CODEX_ACTOR_ID; falls back to assistant:codex."
        ),
    )
    args = ap.parse_args()

    base = args.base.strip() or _git_rev("HEAD~1")
    head = args.head.strip() or _git_rev("HEAD")
    identity_id = args.identity_id.strip()
    scope = args.scope.strip().upper()
    layer_intent_text = args.layer_intent_text.strip()
    expected_work_layer = args.expected_work_layer.strip().lower()
    expected_source_layer = args.expected_source_layer.strip().lower()
    actor_id = resolve_actor_id(str(args.actor_id or "").strip())
    lane_ctx = _resolve_lane_context(
        layer_intent_text=layer_intent_text,
        expected_work_layer=expected_work_layer,
        expected_source_layer=expected_source_layer,
    )
    routed_work_layer = str(lane_ctx.get("work_layer", DEFAULT_WORK_LAYER))
    routed_source_layer = str(lane_ctx.get("source_layer", "global"))
    routed_applied_gate_set = str(lane_ctx.get("applied_gate_set", "instance_required_checks"))
    if not expected_source_layer:
        expected_source_layer = routed_source_layer
    print(
        f"[INFO] lane routing: work_layer={routed_work_layer} "
        f"source_layer={routed_source_layer} applied_gate_set={routed_applied_gate_set}"
    )
    explicit_catalog = args.catalog.strip()
    env_catalog = os.environ.get("IDENTITY_CATALOG", "").strip()
    catalog = explicit_catalog or env_catalog
    stamp_artifact = f"/tmp/identity-response-stamp-{identity_id}.json"
    stamp_blocker_receipt = f"/tmp/identity-stamp-blocker-receipt-{identity_id}.json"
    reply_first_line_blocker_receipt = f"/tmp/identity-reply-first-line-blocker-receipt-{identity_id}.json"
    send_time_reply_file = f"/tmp/identity-send-time-reply-{identity_id}.txt"
    send_time_reply_gate_blocker_receipt = (
        f"/tmp/identity-send-time-reply-gate-blocker-receipt-{identity_id}.json"
    )
    execution_reply_coherence_blocker_receipt = (
        f"/tmp/identity-execution-reply-coherence-blocker-receipt-{identity_id}.json"
    )
    if not catalog:
        print("[FAIL] catalog is required (implicit fallback disabled).")
        print("       pass --catalog <path> or set IDENTITY_CATALOG after mode selection.")
        print("       recommended: source ./scripts/identity_runtime_select.sh project")
        return 2
    if not Path(catalog).expanduser().exists():
        print(f"[FAIL] catalog path does not exist: {catalog}")
        return 2
    guard_cmd = [
        "python3",
        "scripts/validate_identity_runtime_mode_guard.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--expect-mode",
        "auto",
    ]
    if scope:
        guard_cmd.extend(["--scope", scope])
    rc_guard = _run(guard_cmd)
    if rc_guard != 0:
        return rc_guard

    path_pack_cmd = [
        "python3",
        "scripts/validate_identity_pack_path_canonical.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--json-only",
    ]
    rc_pack, out_pack, _ = _run_capture(path_pack_cmd)
    pack_payload = _parse_json_payload(out_pack) or {}
    path_status = str(pack_payload.get("path_governance_status", "")).strip().upper() or "UNKNOWN"
    path_codes = pack_payload.get("path_error_codes", [])
    if not isinstance(path_codes, list):
        path_codes = [str(path_codes)]
    print(
        "[INFO] pack path canonical preflight: "
        f"status={path_status} error_codes={','.join(str(x) for x in path_codes if str(x).strip()) or '-'} "
        f"identity={identity_id}"
    )
    if rc_pack != 0:
        return rc_pack

    home_alignment_cmd = [
        "python3",
        "scripts/validate_identity_home_catalog_alignment.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--identity-home",
        str(Path(catalog).expanduser().resolve().parent),
        "--json-only",
    ]
    rc_home_align, out_home_align, _ = _run_capture(home_alignment_cmd)
    home_align_payload = _parse_json_payload(out_home_align) or {}
    home_align_status = str(home_align_payload.get("path_governance_status", "")).strip().upper() or "UNKNOWN"
    home_align_codes = home_align_payload.get("path_error_codes", [])
    if not isinstance(home_align_codes, list):
        home_align_codes = [str(home_align_codes)]
    print(
        "[INFO] identity home/catalog alignment preflight: "
        f"status={home_align_status} error_codes={','.join(str(x) for x in home_align_codes if str(x).strip()) or '-'} "
        f"identity={identity_id}"
    )
    if rc_home_align != 0:
        return rc_home_align

    fixture_boundary_cmd = [
        "python3",
        "scripts/validate_fixture_runtime_boundary.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--operation",
        "readiness",
        "--json-only",
    ]
    rc_fixture_boundary, out_fixture_boundary, _ = _run_capture(fixture_boundary_cmd)
    fixture_boundary_payload = _parse_json_payload(out_fixture_boundary) or {}
    fixture_boundary_status = (
        str(fixture_boundary_payload.get("path_governance_status", "")).strip().upper() or "UNKNOWN"
    )
    fixture_boundary_codes = fixture_boundary_payload.get("path_error_codes", [])
    if not isinstance(fixture_boundary_codes, list):
        fixture_boundary_codes = [str(fixture_boundary_codes)]
    print(
        "[INFO] fixture/runtime boundary preflight: "
        f"status={fixture_boundary_status} error_codes={','.join(str(x) for x in fixture_boundary_codes if str(x).strip()) or '-'} "
        f"identity={identity_id}"
    )
    if rc_fixture_boundary != 0:
        return rc_fixture_boundary

    seq: list[list[str]] = [
        ["python3", "scripts/validate_identity_protocol.py"],
        ["python3", "scripts/validate_identity_local_persistence.py"],
        ["python3", "scripts/validate_identity_creation_boundary.py"],
        [
            "python3",
            "scripts/validate_identity_scope_resolution.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_scope_isolation.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_scope_persistence.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
        ],
        ["python3", "scripts/validate_identity_state_consistency.py", "--catalog", catalog],
        ["python3", "scripts/validate_identity_session_pointer_consistency.py", "--catalog", catalog],
        [
            "python3",
            "scripts/validate_actor_session_binding.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_no_implicit_switch.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_cross_actor_isolation.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_actor_session_multibinding_concurrency.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_session_refresh_status.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--baseline-policy",
            args.baseline_policy,
        ],
        ["python3", "scripts/validate_audit_snapshot_index.py"],
        ["python3", "scripts/validate_protocol_ssot_source.py"],
        [
            "python3",
            "scripts/validate_e2e_hermetic_runtime_import.py",
            "--operation",
            "readiness",
            "--pythonpath-bootstrap-mode",
            "internal_bootstrap",
            "--json-only",
        ],
        ["python3", "scripts/validate_changelog_updated.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_protocol_handoff_coupling.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_release_metadata_sync.py"],
        ["python3", "scripts/validate_release_freeze_boundary.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_release_workspace_cleanliness.py"],
        ["python3", "scripts/validate_identity_instance_isolation.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_runtime_contract.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_role_binding.py", "--catalog", catalog, "--identity-id", identity_id],
        [
            "python3",
            "scripts/render_identity_response_stamp.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--view",
            "external",
            "--disclosure-level",
            "standard",
            "--out",
            stamp_artifact,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_response_stamp.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-user-visible-gate",
            "--operation",
            "readiness",
            "--blocker-receipt-out",
            stamp_blocker_receipt,
        ],
        [
            "python3",
            "scripts/validate_layer_intent_resolution.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-layer-intent-gate",
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_response_stamp_blocker_receipt.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--force-check",
            "--receipt",
            stamp_blocker_receipt,
        ],
        [
            "python3",
            "scripts/validate_reply_identity_context_first_line.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-first-line-gate",
            "--operation",
            "readiness",
            "--blocker-receipt-out",
            reply_first_line_blocker_receipt,
        ],
        [
            "python3",
            "scripts/compose_and_validate_governed_reply.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--body-text",
            "READINESS_SEND_TIME_REPLY_BODY",
            "--out-reply-file",
            send_time_reply_file,
            "--blocker-receipt-out",
            send_time_reply_gate_blocker_receipt,
            "--outlet-channel-id",
            "governed_adapter_v1",
            "--actor-id",
            actor_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_send_time_reply_gate.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--reply-file",
            send_time_reply_file,
            "--force-check",
            "--enforce-send-time-gate",
            "--reply-outlet-guard-applied",
            "--outlet-channel-id",
            "governed_adapter_v1",
            "--reply-transport-ref",
            send_time_reply_file,
            "--operation",
            "readiness",
            "--blocker-receipt-out",
            send_time_reply_gate_blocker_receipt,
            "--actor-id",
            actor_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_response_stamp_blocker_receipt.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--force-check",
            "--receipt",
            send_time_reply_gate_blocker_receipt,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_headstamp_recurrence_closure.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--actor-id",
            actor_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_response_stamp_blocker_receipt.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--force-check",
            "--receipt",
            reply_first_line_blocker_receipt,
        ],
        [
            "python3",
            "scripts/validate_execution_reply_identity_coherence.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-coherence-gate",
            "--operation",
            "readiness",
            "--blocker-receipt-out",
            execution_reply_coherence_blocker_receipt,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_response_stamp_blocker_receipt.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--force-check",
            "--receipt",
            execution_reply_coherence_blocker_receipt,
            "--json-only",
        ],
        # scope must come from bound runtime/catalog resolution (single source of truth).
        ["python3", "scripts/validate_identity_prompt_quality.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_update_lifecycle.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_install_safety.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_install_provenance.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_tool_installation.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_vendor_api_discovery.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_vendor_api_solution.py", "--catalog", catalog, "--identity-id", identity_id],
        [
            "python3",
            "scripts/validate_semantic_routing_guard.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_instance_protocol_split_receipt.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_work_layer_gate_set_routing.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--base",
            base,
            "--head",
            head,
            "--applied-gate-set",
            routed_applied_gate_set,
            "--force-check",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_protocol_vendor_semantic_isolation.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_external_source_trust_chain.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_protocol_data_sanitization_boundary.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/trigger_platform_optimization_discovery.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_discovery_requiredization.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/build_vibe_coding_feeding_pack.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--out-root",
            "/tmp/vibe-coding-feeding-packs",
        ],
        [
            "python3",
            "scripts/validate_identity_capability_fit_optimization.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_capability_composition_before_discovery.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_capability_fit_review_freshness.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_capability_fit_roundtable_evidence.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/trigger_capability_fit_review.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/build_capability_fit_matrix.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--out-root",
            "/tmp/capability-fit-matrices",
        ],
        [
            "python3",
            "scripts/validate_vendor_namespace_separation.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_required_contract_coverage.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_identity_capability_activation.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--activation-policy",
            args.capability_activation_policy,
        ],
        [
            "python3",
            "scripts/validate_identity_dialogue_content.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_dialogue_cross_validation.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_dialogue_result_support.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_self_upgrade_enforcement.py",
            "--identity-id",
            identity_id,
            "--base",
            base,
            "--head",
            head,
            "--catalog",
            catalog,
        ],
        ["python3", "scripts/validate_identity_ci_enforcement.py", "--catalog", catalog, "--identity-id", identity_id],
    ]
    if scope:
        for cmd in seq:
            if len(cmd) < 2:
                continue
            script = cmd[1]
            if script in {
                "scripts/validate_identity_scope_resolution.py",
                "scripts/validate_identity_scope_isolation.py",
                "scripts/validate_identity_scope_persistence.py",
                "scripts/collect_identity_health_report.py",
            }:
                cmd.extend(["--scope", scope])
    if args.min_required_contract_coverage >= 0.0:
        for cmd in seq:
            if len(cmd) >= 2 and cmd[1] == "scripts/validate_required_contract_coverage.py":
                cmd.extend(["--min-required-contract-coverage", str(args.min_required_contract_coverage)])
                break
    if args.min_discovery_required_coverage >= 0.0:
        for cmd in seq:
            if len(cmd) >= 2 and cmd[1] == "scripts/validate_required_contract_coverage.py":
                cmd.extend(["--min-discovery-required-coverage", str(args.min_discovery_required_coverage)])
                break
    execution_report = args.execution_report.strip()
    if not execution_report:
        gen_cmd = [
            "python3",
            "scripts/identity_creator.py",
            "update",
            "--identity-id",
            identity_id,
            "--mode",
            "review-required",
            "--catalog",
            catalog,
            "--capability-activation-policy",
            args.capability_activation_policy,
            "--baseline-policy",
            args.baseline_policy,
        ]
        if scope:
            gen_cmd.extend(["--scope", scope])
        if layer_intent_text:
            gen_cmd.extend(["--layer-intent-text", layer_intent_text])
        if expected_work_layer:
            gen_cmd.extend(["--expected-work-layer", expected_work_layer])
        if expected_source_layer:
            gen_cmd.extend(["--expected-source-layer", expected_source_layer])
        rc = _run(gen_cmd)
        if rc != 0:
            return rc
        roots: list[Path] = []
        if args.upgrade_report_dir.strip():
            roots.append(Path(args.upgrade_report_dir.strip()).expanduser().resolve())
        pack_path = _resolve_pack_path(catalog, identity_id)
        if pack_path is not None:
            roots.append((pack_path / "runtime" / "reports").resolve())
            roots.append((pack_path / "runtime").resolve())
        roots.append(Path("/tmp/identity-upgrade-reports"))
        roots.append(Path("/tmp/identity-runtime"))
        if os.environ.get("IDENTITY_HOME", "").strip():
            roots.append(Path(os.environ["IDENTITY_HOME"]).expanduser().resolve())
        candidates: list[Path] = []
        for root in roots:
            if not root.exists():
                continue
            for p in glob.glob(str(root / "**" / f"identity-upgrade-exec-{identity_id}-*.json"), recursive=True):
                pp = Path(p)
                if pp.name.endswith("-patch-plan.json"):
                    continue
                candidates.append(pp)
        prompt_sha = ""
        if pack_path is not None:
            prompt_path = pack_path / "IDENTITY_PROMPT.md"
            if prompt_path.exists():
                try:
                    prompt_sha = _sha256(prompt_path)
                except Exception:
                    prompt_sha = ""

        def _candidate_key(path: Path) -> tuple[int, float]:
            if not prompt_sha:
                return (0, path.stat().st_mtime)
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                report_sha = str(data.get("identity_prompt_sha256", "")).strip()
            except Exception:
                report_sha = ""
            return (1 if report_sha and report_sha == prompt_sha else 0, path.stat().st_mtime)

        candidates = sorted(candidates, key=_candidate_key)
        if not candidates:
            print(
                "[FAIL] writeback validation requires execution report, but auto-generation produced none: "
                f"searched_roots={','.join(str(r) for r in roots)} pattern=identity-upgrade-exec-{identity_id}-*.json"
            )
            return 2
        execution_report = str(candidates[-1])
        print(f"[INFO] auto-generated execution report: {execution_report}")

    freshness_cmd = [
        "python3",
        "scripts/validate_execution_report_freshness.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--report",
        execution_report,
        "--execution-report-policy",
        args.execution_report_policy,
        "--json-only",
    ]
    rc_fresh, out_fresh, _ = _run_capture(freshness_cmd)
    freshness_payload = _parse_json_payload(out_fresh) or {}
    freshness_status = str(freshness_payload.get("freshness_status", "")).strip().upper() or "UNKNOWN"
    freshness_code = str(freshness_payload.get("freshness_error_code", "")).strip() or "-"
    selected_report = str(freshness_payload.get("report_selected_path", "")).strip()
    if selected_report and Path(selected_report).exists():
        execution_report = selected_report
    print(
        "[INFO] execution report freshness preflight: "
        f"status={freshness_status} error_code={freshness_code} report={execution_report}"
    )
    if rc_fresh != 0:
        return rc_fresh

    report_path_cmd = [
        "python3",
        "scripts/validate_identity_execution_report_path_contract.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--report",
        execution_report,
        "--json-only",
    ]
    rc_report_path, out_report_path, _ = _run_capture(report_path_cmd)
    report_path_payload = _parse_json_payload(out_report_path) or {}
    report_path_status = str(report_path_payload.get("path_governance_status", "")).strip().upper() or "UNKNOWN"
    report_path_codes = report_path_payload.get("path_error_codes", [])
    if not isinstance(report_path_codes, list):
        report_path_codes = [str(report_path_codes)]
    print(
        "[INFO] execution report path preflight: "
        f"status={report_path_status} error_codes={','.join(str(x) for x in report_path_codes if str(x).strip()) or '-'} "
        f"report={execution_report}"
    )
    if rc_report_path != 0:
        return rc_report_path

    baseline_cmd = [
        "python3",
        "scripts/validate_identity_protocol_baseline_freshness.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--execution-report",
        execution_report,
        "--baseline-policy",
        args.baseline_policy,
        "--json-only",
    ]
    rc_baseline, out_baseline, _ = _run_capture(baseline_cmd)
    baseline_payload = _parse_json_payload(out_baseline) or {}
    baseline_status = str(baseline_payload.get("baseline_status", "")).strip().upper() or "UNKNOWN"
    baseline_code = str(baseline_payload.get("baseline_error_code", "")).strip() or "-"
    selected_report = str(baseline_payload.get("report_selected_path", "")).strip()
    if selected_report and Path(selected_report).exists():
        execution_report = selected_report
    print(
        "[INFO] protocol baseline freshness preflight: "
        f"status={baseline_status} error_code={baseline_code} report={execution_report}"
    )
    if rc_baseline != 0:
        return rc_baseline

    version_alignment_cmd = [
        "python3",
        "scripts/validate_identity_protocol_version_alignment.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--execution-report",
        execution_report,
        "--operation",
        "readiness",
        "--alignment-policy",
        args.baseline_policy,
        "--json-only",
    ]
    if scope:
        version_alignment_cmd.extend(["--scope", scope])
    rc_align, out_align, _ = _run_capture(version_alignment_cmd)
    align_payload = _parse_json_payload(out_align) or {}
    align_status = str(align_payload.get("protocol_version_alignment_status", "")).strip().upper() or "UNKNOWN"
    align_code = str(align_payload.get("error_code", "")).strip() or "-"
    print(
        "[INFO] protocol version alignment preflight: "
        f"status={align_status} error_code={align_code} report={execution_report}"
    )
    if rc_align != 0:
        return rc_align

    seq.append(
        [
            "python3",
            "scripts/validate_writeback_continuity.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--report",
            execution_report,
            "--operation",
            "readiness",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_post_execution_mandatory.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--report",
            execution_report,
            "--operation",
            "readiness",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/collect_identity_health_report.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--operation",
            "readiness",
            "--execution-report",
            execution_report,
            "--out-dir",
            "/tmp/identity-health-reports",
            "--enforce-pass",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_health_contract.py",
            "--identity-id",
            identity_id,
            "--report-dir",
            "/tmp/identity-health-reports",
            "--require-pass",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_actor_health_profile.py",
            "--identity-id",
            identity_id,
            "--report-dir",
            "/tmp/identity-health-reports",
            "--execution-report",
            execution_report,
            "--operation",
            "readiness",
            "--enforce-bound-report",
            "--json-only",
        ]
    )
    if scope:
        seq[-3].extend(["--scope", scope])
    seq.append(
        [
            "python3",
            "scripts/validate_protocol_feedback_reply_channel.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--operation",
            "readiness",
            "--force-check",
            "--json-only",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_protocol_feedback_bootstrap_ready.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--operation",
            "readiness",
            "--force-check",
            "--json-only",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_protocol_entry_candidate_bridge.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--operation",
            "readiness",
            "--force-check",
            "--json-only",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_protocol_inquiry_followup_chain.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--operation",
            "readiness",
            "--force-check",
            "--json-only",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_protocol_feedback_sidecar_contract.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--report",
            execution_report,
            "--operation",
            "readiness",
            "--enforce-blocking",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_instance_base_repo_write_boundary.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--report",
            execution_report,
            "--operation",
            "readiness",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_protocol_feedback_ssot_archival.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--operation",
            "readiness",
        ]
    )

    seq.append(
        [
            "python3",
            "scripts/validate_identity_protocol_root_evidence.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_mode_promotion_arbitration.py",
            "--identity-id",
            identity_id,
            "--base",
            base,
            "--head",
            head,
            "--report",
            execution_report,
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_experience_writeback.py",
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--local-catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--execution-report",
            execution_report,
        ]
    )
    report_meta: dict[str, Any] = {}
    try:
        report_meta = json.loads(Path(execution_report).read_text(encoding="utf-8"))
    except Exception:
        report_meta = {}
    permission_cmd = [
        "python3",
        "scripts/validate_identity_permission_state.py",
        "--identity-id",
        identity_id,
        "--report",
        execution_report,
    ]
    report_all_ok = _boolish(report_meta.get("all_ok"))
    report_writeback_status = str(report_meta.get("writeback_status", "")).strip().upper()
    report_permission_state = str(report_meta.get("permission_state", "")).strip().upper()
    if report_all_ok and report_writeback_status == "WRITTEN" and report_permission_state == "WRITEBACK_WRITTEN":
        permission_cmd.append("--require-written")
    seq.append(permission_cmd)
    seq.append(
        [
            "python3",
            "scripts/validate_identity_binding_tuple.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_capability_activation.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
            "--require-activated",
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_prompt_activation.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--report",
            execution_report,
        ]
    )
    seq.append(
        [
            "python3",
            "scripts/validate_identity_prompt_lifecycle.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
        ]
    )

    seq, skipped_protocol_publish_checks = _route_release_seq_for_lane(seq, work_layer=routed_work_layer)
    if skipped_protocol_publish_checks:
        print(
            "[INFO] instance lane active; skipped protocol publish gates: "
            + ", ".join(skipped_protocol_publish_checks)
        )

    if layer_intent_text:
        for cmd in seq:
            if len(cmd) < 2:
                continue
            script = cmd[1]
            if script in {
                "scripts/render_identity_response_stamp.py",
                "scripts/compose_and_validate_governed_reply.py",
                "scripts/validate_layer_intent_resolution.py",
                "scripts/validate_reply_identity_context_first_line.py",
                "scripts/validate_send_time_reply_gate.py",
                "scripts/validate_execution_reply_identity_coherence.py",
                "scripts/validate_work_layer_gate_set_routing.py",
                "scripts/validate_protocol_feedback_bootstrap_ready.py",
                "scripts/validate_protocol_entry_candidate_bridge.py",
                "scripts/validate_protocol_inquiry_followup_chain.py",
            } and "--layer-intent-text" not in cmd:
                cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        for cmd in seq:
            if len(cmd) < 2:
                continue
            if cmd[1] in {
                "scripts/validate_layer_intent_resolution.py",
                "scripts/validate_reply_identity_context_first_line.py",
                "scripts/validate_send_time_reply_gate.py",
                "scripts/validate_execution_reply_identity_coherence.py",
                "scripts/validate_work_layer_gate_set_routing.py",
                "scripts/validate_protocol_feedback_bootstrap_ready.py",
                "scripts/validate_protocol_entry_candidate_bridge.py",
                "scripts/validate_protocol_inquiry_followup_chain.py",
            } and "--expected-work-layer" not in cmd:
                cmd.extend(["--expected-work-layer", expected_work_layer])
            if (
                cmd[1] == "scripts/compose_and_validate_governed_reply.py"
                and "--work-layer" not in cmd
            ):
                cmd.extend(["--work-layer", expected_work_layer])
    if expected_source_layer:
        for cmd in seq:
            if len(cmd) < 2:
                continue
            if (
                cmd[1] == "scripts/compose_and_validate_governed_reply.py"
                and "--source-layer" not in cmd
            ):
                cmd.extend(["--source-layer", expected_source_layer])
            if cmd[1] in {
                "scripts/validate_layer_intent_resolution.py",
                "scripts/validate_reply_identity_context_first_line.py",
                "scripts/validate_send_time_reply_gate.py",
                "scripts/validate_execution_reply_identity_coherence.py",
            } and "--expected-source-layer" not in cmd:
                cmd.extend(["--expected-source-layer", expected_source_layer])
            if cmd[1] in {
                "scripts/validate_protocol_feedback_bootstrap_ready.py",
                "scripts/validate_protocol_entry_candidate_bridge.py",
                "scripts/validate_protocol_inquiry_followup_chain.py",
                "scripts/validate_work_layer_gate_set_routing.py",
            } and "--source-layer" not in cmd:
                cmd.extend(["--source-layer", expected_source_layer])

    for cmd in seq:
        is_capability_validator = len(cmd) >= 2 and cmd[1] == "scripts/validate_identity_capability_activation.py"
        if not is_capability_validator:
            rc = _run(cmd)
            if rc != 0:
                return rc
            continue

        rc, out, _ = _run_capture(cmd)
        if rc == 0:
            continue

        payload = _parse_json_payload(out) or {}
        cap_error_code = str(payload.get("capability_activation_error_code", "")).strip()
        if str(args.capability_activation_policy or "").strip().lower() == "strict-union" and cap_error_code == "IP-CAP-003":
            print(
                "[WARN] capability activation strict-union blocked by env/auth boundary (IP-CAP-003); "
                "retrying route-any-ready fallback for readiness flow"
            )
            fallback_cmd = _replace_activation_policy(cmd, "route-any-ready")
            rc_fb = _run(fallback_cmd)
            if rc_fb == 0:
                continue
            return rc_fb
        return rc

    print("[OK] release readiness checks PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"[FAIL] subprocess error: {exc}", file=sys.stderr)
        raise SystemExit(2)
