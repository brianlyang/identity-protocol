#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROJECT_IDENTITY_HOME="$(cd "${REPO_ROOT}/.." && pwd)/.identity"
PROBE_ROOT_BASE="${PROJECT_IDENTITY_HOME}/_probe"
mkdir -p "${PROBE_ROOT_BASE}"
TMP_ROOT="$(mktemp -d "${PROBE_ROOT_BASE}/terminal-truth-boundary-outer-surface.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

PYTHONPATH="${REPO_ROOT}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
python3 - "${REPO_ROOT}" "${TMP_ROOT}" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

repo_root = Path(sys.argv[1]).resolve()
tmp_root = Path(sys.argv[2]).resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from actor_session_common import actor_session_path, normalize_actor_binding_store, write_actor_binding_store
from blocker_taxonomy_common import BLOCKER_ALIAS_MAP_VERSION, CANONICAL_BLOCKER_TYPES
from create_identity_pack import _collaboration_trigger_contract_skeleton
from terminal_truth_cleanliness_common import terminal_truth_cleanliness_contract_skeleton

actor_id = "assistant:codex"
catalog_path = (tmp_root / "catalog.local.yaml").resolve()
repo_catalog_path = (repo_root / "identity/catalog/identities.yaml").resolve()
protocol_commit_sha = (
    subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
)
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

identity_specs = {
    "clean": {
        "identity_id": "terminal-truth-boundary-clean-e2e",
        "session_id": "run:terminal-truth-boundary-clean-e2e",
        "mode": "safe-auto",
        "next_action": "no_upgrade_triggered",
        "is_terminal_clean": True,
        "publishable": True,
        "canonical_result_eligible": True,
        "terminal_truth_class": "clean_terminal_truth",
        "terminal_state_class": "completed_clean",
        "negative_feedback_class": "",
        "boundary_health_class": "repair_green_terminal_truth_clean",
        "admission_lane_projection": "NOT_BLOCKED_BY_TERMINAL_TRUTH",
        "terminal_truth_observation_status": "PASS_REQUIRED",
        "experience_writeback_validation_status": "SKIPPED_NOT_REQUIRED",
        "repair_success_not_clean_terminal_truth": False,
        "report_suffix": "clean",
    },
    "review": {
        "identity_id": "terminal-truth-boundary-review-e2e",
        "session_id": "run:terminal-truth-boundary-review-e2e",
        "mode": "review-required",
        "next_action": "review_required_followup",
        "is_terminal_clean": False,
        "publishable": False,
        "canonical_result_eligible": False,
        "terminal_truth_class": "review_required_execution_closure",
        "terminal_state_class": "review_pending",
        "negative_feedback_class": "review_required",
        "boundary_health_class": "repair_green_terminal_truth_blocked",
        "admission_lane_projection": "BLOCKED_BY_TERMINAL_TRUTH",
        "terminal_truth_observation_status": "FAIL_REQUIRED",
        "experience_writeback_validation_status": "SKIPPED_NOT_REQUIRED",
        "repair_success_not_clean_terminal_truth": True,
        "report_suffix": "review-required",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_identity(spec: dict[str, object]) -> dict[str, str]:
    identity_id = str(spec["identity_id"])
    pack_path = (tmp_root / identity_id).resolve()
    reports_dir = pack_path / "runtime" / "reports"
    state_dir = pack_path / "runtime" / "state"
    reports_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    rulebook_path = (pack_path / "RULEBOOK.jsonl").resolve()
    task_history_path = (pack_path / "TASK_HISTORY.md").resolve()
    prompt_contract_path = (state_dir / "prompt_contract.json").resolve()
    prompt_path = (pack_path / "IDENTITY_PROMPT.md").resolve()
    outlet_preflight_path = (reports_dir / "outlet-preflight.json").resolve()

    canonical_blockers = list(CANONICAL_BLOCKER_TYPES)
    task_doc = {
        "task_id": f"{identity_id}_task",
        "objective": {"status": "active"},
        "gates": {
            "identity_update_gate": "required",
            "collaboration_trigger_gate": "required",
        },
        "post_execution_mandatory": [
            "append task outcome into TASK_HISTORY.md",
            "update objective.status",
        ],
        "capability_orchestration_contract": {
            "required": True,
            "preflight_requirements": [],
            "task_type_routes": {
                "instance_delivery": {
                    "pipeline": ["observe_context", "emit"],
                    "primary_skills": [],
                    "fallback_skills": [],
                    "required_mcp": [],
                    "primary_instance_scripts": [],
                    "fallback_instance_scripts": [],
                    "script_receipt_pattern": "",
                    "allowed_execution_lanes": [],
                    "lane_admission_policy": {},
                    "lane_receipt_pattern": "",
                    "lane_block_on_fallback": False,
                    "direct_tool_entry_policy": {},
                }
            },
        },
        "writeback_continuity_contract_v1": {"required": True},
        "identity_terminal_truth_cleanliness_contract_v1": terminal_truth_cleanliness_contract_skeleton(),
        "blocker_taxonomy_contract": {
            "required": True,
            "required_blocker_types": canonical_blockers,
            "blocker_alias_map_version": BLOCKER_ALIAS_MAP_VERSION,
            "blocker_classification_required_fields": [
                "blocker_type",
                "source",
                "detected_at",
                "requires_human_collab",
                "next_action",
            ],
            "fail_action": "block_merge_and_reenter_collaboration_update",
        },
        "collaboration_trigger_contract": _collaboration_trigger_contract_skeleton(),
        "escalation_policy": {
            "human_collab_blockers": canonical_blockers,
        },
    }
    task_doc["collaboration_trigger_contract"]["trigger_conditions"] = canonical_blockers

    rulebook_path.write_text("", encoding="utf-8")
    task_history_path.write_text("# Task History\n", encoding="utf-8")
    prompt_contract_path.write_text("{}\n", encoding="utf-8")
    prompt_path.write_text(
        "\n".join(
            [
                f"# {identity_id}",
                "",
                "Identity-Context: synthetic-probe",
                "Machine-Verification: synthetic-probe",
                "",
                "This prompt exists only to drive terminal-truth outer-surface e2e probes.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_path / "CURRENT_TASK.json").write_text(
        json.dumps(task_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    outlet_preflight_path.write_text(
        json.dumps({"status": "PASS_REQUIRED", "identity_id": identity_id}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    prompt_sha = _sha256(prompt_path)
    report_doc = {
        "identity_id": identity_id,
        "generated_at": now,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "identity_prompt_path": str(prompt_path),
        "identity_prompt_sha256": prompt_sha,
        "protocol_commit_sha": protocol_commit_sha,
        "protocol_head_sha_at_run_start": protocol_commit_sha,
        "all_ok": True,
        "upgrade_required": False,
        "permission_state": "PRECHECK",
        "writeback_status": "NOT_REQUIRED",
        "writeback_mode": "STRICT_WRITEBACK",
        "next_recovery_action": "",
        "phase_a_refresh_applied": False,
        "phase_b_strict_revalidate_status": "PASS_REQUIRED",
        "phase_transition_reason": "",
        "phase_transition_error_code": "",
        "governed_outlet_enforced": True,
        "outlet_channel_id": "final_emit_governed",
        "outlet_preflight_receipt": str(outlet_preflight_path),
        "outlet_bypass_detected": False,
        "final_emit_channel_id": "final_emit_governed",
        "final_emit_policy_mode": "tool_choice_required",
        "final_emit_schema_id": "hud_headstamp_final_emit_schema_v1",
        "final_emit_schema_status": "PASS_REQUIRED",
        "final_emit_contract_status": "PASS_REQUIRED",
        "experience_writeback": {
            "required": False,
            "status": "NOT_REQUIRED",
            "error_code": "",
            "mode": "safe-auto",
        },
        "writeback_paths": [
            str(rulebook_path),
            str(task_history_path),
            str(prompt_contract_path),
        ],
        "writeback_rule_id": "",
        "artifacts": [],
        "run_id": f"identity-upgrade-exec-{identity_id}-{spec['report_suffix']}",
        "mode": str(spec["mode"]),
        "next_action": str(spec["next_action"]),
        "is_terminal_clean": bool(spec["is_terminal_clean"]),
        "publishable": bool(spec["publishable"]),
        "canonical_result_eligible": bool(spec["canonical_result_eligible"]),
        "terminal_truth_class": str(spec["terminal_truth_class"]),
        "terminal_state_class": str(spec["terminal_state_class"]),
        "negative_feedback_class": str(spec["negative_feedback_class"]),
    }
    report_path = (reports_dir / f"identity-upgrade-exec-{identity_id}-{spec['report_suffix']}.json").resolve()
    report_path.write_text(json.dumps(report_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "identity_id": identity_id,
        "pack_path": str(pack_path),
        "report_path": str(report_path),
        "session_id": str(spec["session_id"]),
    }


seeded = [_seed_identity(spec) for spec in identity_specs.values()]
catalog_doc = {
    "identities": [
        {
            "id": row["identity_id"],
            "pack_path": row["pack_path"],
            "scope": "USER",
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "auto",
        }
        for row in seeded
    ]
}
catalog_path.write_text(yaml.safe_dump(catalog_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")

session_id_map_path = (tmp_root / "session-id-map.json").resolve()
session_id_map_path.write_text(
    json.dumps({row["identity_id"]: row["session_id"] for row in seeded}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

actor_store_path = actor_session_path(catalog_path, actor_id)
raw_store = {
    "schema_version": "actor_session_multibinding_v1",
    "actor_id": actor_id,
    "catalog_path": str(catalog_path),
    "binding_key_mode": "actor_id+identity_id+session_id",
    "binding_version": len(seeded),
    "compare_token": str(len(seeded)),
    "bindings": [
        {
            "actor_id": actor_id,
            "identity_id": row["identity_id"],
            "session_id": row["session_id"],
            "catalog_path": str(catalog_path),
            "status": "active",
            "bound_at": now,
            "updated_at": now,
            "binding_ref": f"{actor_id}:{row['identity_id']}:{row['session_id']}:v{idx}",
            "binding_version": idx,
            "compare_token": str(idx),
        }
        for idx, row in enumerate(seeded, start=1)
    ],
    "updated_at": now,
}
normalized_store = normalize_actor_binding_store(
    data=raw_store,
    actor_id=actor_id,
    catalog_path=catalog_path,
    actor_session_file=actor_store_path,
)
write_actor_binding_store(actor_store_path, normalized_store)

env = dict(os.environ)
env["IDENTITY_CATALOG"] = str(catalog_path)


def _run(cmd: list[str], *, allow_nonzero: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
    )
    if not allow_nonzero and proc.returncode != 0:
        raise AssertionError(
            f"command_failed rc={proc.returncode} cmd={' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_projection(surface: str, payload: dict, spec: dict[str, object]) -> None:
    assert payload["terminal_truth_boundary_projection_status"] == "PASS_REQUIRED", (surface, payload)
    assert payload["repair_lane_status"] == "PASS_REQUIRED", (surface, payload)
    assert payload["experience_writeback_validation_status"] == spec["experience_writeback_validation_status"], (
        surface,
        payload,
    )
    assert payload["terminal_truth_observation_status"] == spec["terminal_truth_observation_status"], (surface, payload)
    assert payload["admission_lane_projection"] == spec["admission_lane_projection"], (surface, payload)
    assert payload["boundary_health_class"] == spec["boundary_health_class"], (surface, payload)
    assert payload["repair_success_not_clean_terminal_truth"] is spec["repair_success_not_clean_terminal_truth"], (
        surface,
        payload,
    )
    assert payload["terminal_truth_class"] == spec["terminal_truth_class"], (surface, payload)
    assert payload["terminal_state_class"] == spec["terminal_state_class"], (surface, payload)


three_plane_out: dict[str, str] = {}
readiness_out: dict[str, str] = {}
report_paths_by_identity = {row["identity_id"]: row["report_path"] for row in seeded}
specs_by_identity = {row["identity_id"]: next(spec for spec in identity_specs.values() if spec["identity_id"] == row["identity_id"]) for row in seeded}

for row in seeded:
    identity_id = row["identity_id"]
    session_id = row["session_id"]
    report_path = Path(row["report_path"]).resolve()
    spec = specs_by_identity[identity_id]

    tp_out = (tmp_root / f"three-plane-{identity_id}.json").resolve()
    three_plane_out[identity_id] = str(tp_out)
    _run(
        [
            "python3",
            "scripts/report_three_plane_status.py",
            "--projection-profile",
            "terminal_truth_boundary_projection",
            "--identity-id",
            identity_id,
            "--catalog",
            str(catalog_path),
            "--repo-catalog",
            str(repo_catalog_path),
            "--execution-report",
            str(report_path),
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--out",
            str(tp_out),
        ]
    )
    tp_payload = _load_json(tp_out)
    assert tp_payload["projection_profile"] == "terminal_truth_boundary_projection", (identity_id, tp_payload)
    assert tp_payload["projection_profile_execution_mode"] == "projection_only", (identity_id, tp_payload)
    assert tp_payload["projection_excluded_areas"] == [
        "repo_plane",
        "release_plane",
        "release_cloud_evidence_adapter",
        "required_gate_bundle_projection",
        "health_report_experience_writeback_closure",
        "current_chat_surface_exclusion",
        "m2m_projection",
        "tuple_context_projection",
        "governance_closure_axes",
    ], (identity_id, tp_payload)
    assert tp_payload["instance_plane_status"] == "PROJECTION_ONLY", (identity_id, tp_payload)
    assert tp_payload["repo_plane_status"] == "SKIPPED_NOT_REQUIRED", (identity_id, tp_payload)
    assert tp_payload["release_plane_status"] == "SKIPPED_NOT_REQUIRED", (identity_id, tp_payload)
    assert tp_payload["overall_release_decision"] == "Projection Only", (identity_id, tp_payload)
    assert tp_payload["repo_plane_detail"]["projection_skip_scope_class"] == "bounded_projection_profile_exclusion", (
        identity_id,
        tp_payload["repo_plane_detail"],
    )
    assert tp_payload["release_plane_detail"]["projection_skip_scope_reason"] == "projection_profile_out_of_scope", (
        identity_id,
        tp_payload["release_plane_detail"],
    )
    assert tp_payload["release_cloud_evidence_adapter"]["release_cloud_evidence_adapter_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        tp_payload["release_cloud_evidence_adapter"],
    )
    assert tp_payload["release_cloud_evidence_adapter"]["projection_skip_scope_class"] == "bounded_projection_profile_exclusion", (
        identity_id,
        tp_payload["release_cloud_evidence_adapter"],
    )
    assert tp_payload["current_chat_surface_exclusion"]["projection_skip_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        tp_payload["current_chat_surface_exclusion"],
    )
    assert tp_payload["current_chat_surface_exclusion"]["projection_excluded_area"] == "current_chat_surface_exclusion", (
        identity_id,
        tp_payload["current_chat_surface_exclusion"],
    )
    assert tp_payload["required_gate_bundle_target_projection"]["projection_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        tp_payload["required_gate_bundle_target_projection"],
    )
    assert tp_payload["required_gate_bundle_target_projection"]["scope_class"] == "bounded_projection_profile_exclusion", (
        identity_id,
        tp_payload["required_gate_bundle_target_projection"],
    )
    assert tp_payload["health_report_experience_writeback_closure"]["projection_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        tp_payload["health_report_experience_writeback_closure"],
    )
    assert tp_payload["health_report_experience_writeback_closure"]["projection_excluded_area"] == "health_report_experience_writeback_closure", (
        identity_id,
        tp_payload["health_report_experience_writeback_closure"],
    )
    _assert_projection(f"three-plane:{identity_id}:top", tp_payload["terminal_truth_boundary_projection"], spec)
    instance_projection = (tp_payload.get("instance_plane_detail") or {}).get("terminal_truth_boundary_projection") or {}
    _assert_projection(f"three-plane:{identity_id}:instance", instance_projection, spec)

    readiness_out_path = (tmp_root / f"release-readiness-{identity_id}.json").resolve()
    readiness_out[identity_id] = str(readiness_out_path)
    rr_proc = _run(
        [
            "python3",
            "scripts/release_readiness_check.py",
            "--identity-id",
            identity_id,
            "--catalog",
            str(catalog_path),
            "--execution-report",
            str(report_path),
            "--check-name",
            "scripts/ci/run_terminal_truth_boundary_projection_probes_ci.sh",
            "--summary-out",
            str(readiness_out_path),
        ],
        allow_nonzero=True,
    )
    assert rr_proc.returncode in {0, 1, 2}, (identity_id, rr_proc.returncode)
    readiness_payload = _load_json(readiness_out_path)
    _assert_projection(
        f"release-readiness:{identity_id}:projection",
        readiness_payload["terminal_truth_boundary_projection"],
        spec,
    )
    one_look = readiness_payload.get("one_look") or {}
    assert one_look["terminal_truth_boundary_projection_status"] == "PASS_REQUIRED", (identity_id, one_look)
    assert one_look["repair_lane_status"] == "PASS_REQUIRED", (identity_id, one_look)
    assert one_look["experience_writeback_validation_status"] == spec["experience_writeback_validation_status"], (
        identity_id,
        one_look,
    )
    assert one_look["terminal_truth_observation_status"] == spec["terminal_truth_observation_status"], (
        identity_id,
        one_look,
    )
    assert one_look["admission_lane_projection"] == spec["admission_lane_projection"], (identity_id, one_look)
    assert one_look["repair_success_not_clean_terminal_truth"] is spec["repair_success_not_clean_terminal_truth"], (
        identity_id,
        one_look,
    )
    assert one_look["terminal_truth_class"] == spec["terminal_truth_class"], (identity_id, one_look)
    assert one_look["terminal_state_class"] == spec["terminal_state_class"], (identity_id, one_look)

full_scan_out = (tmp_root / "full-identity-protocol-scan.json").resolve()
_run(
    [
        "python3",
        "scripts/full_identity_protocol_scan.py",
        "--repo-root",
        str(repo_root),
        "--repo-catalog",
        str(repo_catalog_path),
        "--project-catalog",
        str(catalog_path),
        "--projection-profile",
        "terminal_truth_boundary_projection",
        "--scan-mode",
        "target",
        "--identity-ids",
        ",".join(row["identity_id"] for row in seeded),
        "--target-source-layer",
        "project",
        "--actor-id",
        actor_id,
        "--session-id-map-file",
        str(session_id_map_path),
        "--out",
        str(full_scan_out),
    ]
)
full_scan_payload = _load_json(full_scan_out)
assert full_scan_payload["projection_profile"] == "terminal_truth_boundary_projection", full_scan_payload
assert full_scan_payload["projection_profile_execution_mode"] == "projection_only", full_scan_payload
assert full_scan_payload["projection_excluded_areas"] == [
    "release_cloud_evidence_adapter",
    "host_visible_post_check_metrics",
    "health_report_experience_writeback_closure",
], full_scan_payload
release_adapter = full_scan_payload.get("release_cloud_evidence_adapter") or {}
assert release_adapter["release_cloud_evidence_adapter_status"] == "SKIPPED_NOT_REQUIRED", release_adapter
assert release_adapter["projection_skip_scope_class"] == "bounded_projection_profile_exclusion", release_adapter
assert release_adapter["stale_reasons"] == [], release_adapter
host_visible_metrics = full_scan_payload.get("host_visible_post_check_metrics") or {}
assert host_visible_metrics["host_visible_post_check_metrics_status"] == "SKIPPED_NOT_REQUIRED", host_visible_metrics
assert host_visible_metrics["projection_skip_scope_class"] == "bounded_projection_profile_exclusion", host_visible_metrics
assert host_visible_metrics["stale_reasons"] == [], host_visible_metrics
assert full_scan_payload["chat_egress_uniqueness_status"] == "SKIPPED_NOT_REQUIRED", full_scan_payload
summary_boundary = full_scan_payload.get("summary_terminal_truth_boundary") or {}
assert summary_boundary["total_identities"] == 2, summary_boundary
assert summary_boundary["projection_pass"] == 2, summary_boundary
assert summary_boundary["projection_fail"] == 0, summary_boundary
assert summary_boundary["not_applicable"] == 0, summary_boundary
assert summary_boundary["blocked_by_terminal_truth"] == 1, summary_boundary
assert summary_boundary["repair_green_terminal_truth_blocked"] == 1, summary_boundary
assert summary_boundary["repair_green_terminal_truth_clean"] == 1, summary_boundary
assert summary_boundary["blocked_identity_ids"] == [identity_specs["review"]["identity_id"]], summary_boundary
required_gate_summary = full_scan_payload.get("summary_required_gate_bundle_projection") or {}
assert required_gate_summary["projection_fail"] == 0, required_gate_summary
assert required_gate_summary["projection_skipped_not_required"] == 2, required_gate_summary
assert required_gate_summary["projection_scope_classes"] == ["bounded_projection_profile_exclusion"], required_gate_summary
assert required_gate_summary["projection_scope_reasons"] == ["projection_profile_out_of_scope"], required_gate_summary
health_summary = full_scan_payload.get("summary_health_report_experience_writeback_closure") or {}
assert health_summary["total_identities"] == 2, health_summary
assert health_summary["projection_pass"] == 0, health_summary
assert health_summary["projection_fail"] == 0, health_summary
assert health_summary["projection_skipped_not_required"] == 2, health_summary
assert health_summary["projection_scope_excluded_identity_ids"] == [row["identity_id"] for row in seeded], health_summary
assert health_summary["projection_scope_classes"] == ["bounded_projection_profile_exclusion"], health_summary
assert health_summary["projection_scope_reasons"] == ["projection_profile_out_of_scope"], health_summary
assert health_summary["projection_stale_reasons"] == [], health_summary

rows_by_identity: dict[str, dict] = {}
for catalog_row in full_scan_payload.get("catalogs") or []:
    for identity_row in catalog_row.get("identities") or []:
        identity_id = str(identity_row.get("identity_id", "")).strip()
        if identity_id:
            rows_by_identity[identity_id] = identity_row

assert set(rows_by_identity) >= {row["identity_id"] for row in seeded}, rows_by_identity.keys()
for row in seeded:
    identity_id = row["identity_id"]
    spec = specs_by_identity[identity_id]
    identity_row = rows_by_identity[identity_id]
    projection = identity_row.get("three_plane_terminal_truth_boundary_projection") or {}
    _assert_projection(f"full-scan:{identity_id}:row", projection, spec)
    three_plane_summary = identity_row.get("three_plane") or {}
    assert three_plane_summary["terminal_truth_boundary_projection_status"] == "PASS_REQUIRED", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["terminal_truth_boundary_health_class"] == spec["boundary_health_class"], (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["admission_lane_projection"] == spec["admission_lane_projection"], (
        identity_id,
        three_plane_summary,
    )
    assert identity_row["check_matrix_mode"] == "projection_only", (identity_id, identity_row)
    assert identity_row["scan_projection_profile"] == "terminal_truth_boundary_projection", (identity_id, identity_row)
    health_projection = identity_row.get("three_plane_health_report_experience_writeback_closure") or {}
    assert health_projection["projection_status"] == "SKIPPED_NOT_REQUIRED", (identity_id, health_projection)
    assert health_projection["projection_excluded_area"] == "health_report_experience_writeback_closure", (
        identity_id,
        health_projection,
    )
    assert health_projection["projection_skip_scope_class"] == "bounded_projection_profile_exclusion", (
        identity_id,
        health_projection,
    )
    assert health_projection["validation_status"] == "SKIPPED_NOT_REQUIRED", (identity_id, health_projection)
    assert three_plane_summary["health_report_experience_writeback_projection_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["health_report_contract_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["health_report_experience_writeback_validation_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["health_report_selected_path_matches_execution_report"] is False, (
        identity_id,
        three_plane_summary,
    )
    required_gate_projection = identity_row.get("three_plane_required_gate_bundle_target_projection") or {}
    assert required_gate_projection["projection_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        required_gate_projection,
    )
    assert required_gate_projection["scope_class"] == "bounded_projection_profile_exclusion", (
        identity_id,
        required_gate_projection,
    )
    assert three_plane_summary["required_gate_bundle_projection_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_scope_class"] == "bounded_projection_profile_exclusion", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_scope_reason"] == "projection_profile_out_of_scope", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_actor_id"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_resolved_work_layer"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_resolved_source_layer"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_lock_state"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_run_id_binding"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_report_selected_path"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_report_selection_mode"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_report_authority_class"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_report_pointer_resolution_mode"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_report_pointer_path"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_missing_mapping_requirements"] == [], (
        identity_id,
        three_plane_summary,
    )
    shadow_projection = identity_row.get("three_plane_required_gate_bundle_target_projection_shadow") or {}
    assert shadow_projection["projection_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        shadow_projection,
    )
    assert shadow_projection["scope_class"] == "bounded_projection_profile_exclusion", (
        identity_id,
        shadow_projection,
    )
    assert three_plane_summary["required_gate_bundle_shadow_projection_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_scope_class"] == "bounded_projection_profile_exclusion", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_scope_reason"] == "projection_profile_out_of_scope", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_actor_id"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_resolved_work_layer"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_resolved_source_layer"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_lock_state"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_run_id_binding"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_report_selected_path"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_report_selection_mode"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_report_authority_class"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_report_pointer_resolution_mode"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_report_pointer_path"] == "", (
        identity_id,
        three_plane_summary,
    )
    assert three_plane_summary["required_gate_bundle_shadow_missing_mapping_requirements"] == [], (
        identity_id,
        three_plane_summary,
    )
    current_chat_projection = identity_row.get("current_chat_surface_projection") or {}
    assert current_chat_projection["projection_skip_status"] == "SKIPPED_NOT_REQUIRED", (
        identity_id,
        current_chat_projection,
    )
    assert current_chat_projection["projection_skip_scope_reason"] == "projection_profile_out_of_scope", (
        identity_id,
        current_chat_projection,
    )

print(
    json.dumps(
        {
            "terminal_truth_boundary_outer_surface_e2e_probe_status": "PASS_REQUIRED",
            "catalog_path": str(catalog_path),
            "seeded_identity_ids": [row["identity_id"] for row in seeded],
            "three_plane_outputs": three_plane_out,
            "release_readiness_outputs": readiness_out,
            "full_scan_output": str(full_scan_out),
            "summary_terminal_truth_boundary": summary_boundary,
            "summary_health_report_experience_writeback_closure": health_summary,
        },
        ensure_ascii=False,
        indent=2,
    )
)
PY

echo "[PASS] terminal truth boundary outer-surface e2e probes passed"
