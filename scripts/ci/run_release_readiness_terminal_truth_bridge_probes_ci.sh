#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}"

source "${ROOT}/scripts/probe_fixture_shell_common.sh"
source "${ROOT}/scripts/ci/probe_repo_mirror_common.sh"

run_shadow_validator() {
  local shadow_root="$1"
  local output_path="$2"
  PYTHONPATH="${shadow_root}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 "${shadow_root}/scripts/validate_release_readiness_terminal_truth_bridge.py" \
      --repo-root "${shadow_root}" \
      --json-only >"${output_path}"
}

restore_shadow_file() {
  local shadow_root="$1"
  local rel_path="$2"
  mkdir -p "$(dirname "${shadow_root}/${rel_path}")"
  cp "${ROOT}/${rel_path}" "${shadow_root}/${rel_path}"
}

POSITIVE_JSON="/tmp/release-readiness-terminal-truth-bridge-positive.json"
echo "[INFO] positive: release-readiness terminal-truth bridge validator"
python3 scripts/validate_release_readiness_terminal_truth_bridge.py --json-only >"${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
from __future__ import annotations

import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["release_readiness_terminal_truth_bridge_status"] == "PASS_REQUIRED", payload
assert payload["stale_reasons"] == [], payload
PY

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/release-readiness-terminal-truth-bridge-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT
probe_mirror_repo "${ROOT}" "${TMP_ROOT}"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_terminal_truth_bridge_common.py"
# expected fail-close: terminal_truth_bridge_case_markers_drift
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_terminal_truth_bridge_common.py" \
  'terminal_truth_bridge_case=review_required_execution_closure' \
  'terminal_truth_bridge_case=review_required_execution'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-terminal-truth-bridge-negative-common.json; then
  echo "[FAIL] terminal-truth bridge common drift unexpectedly passed"
  exit 1
fi
echo "[PASS] terminal-truth bridge common drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_probe:scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  '["bash", "scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh"],' \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-terminal-truth-bridge-negative-post-closure.json; then
  echo "[FAIL] missing terminal-truth bridge probe command unexpectedly passed"
  exit 1
fi
echo "[PASS] missing terminal-truth bridge probe command fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"
# expected fail-close: summary_binding_probe_missing_token:release_readiness_terminal_truth_bridge_probe
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_release_readiness_summary_binding_probes_ci.sh" \
  'release_readiness_terminal_truth_bridge_probe' \
  'release_readiness_terminal_truth_bridge'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-terminal-truth-bridge-negative-summary-binding.json; then
  echo "[FAIL] summary binding terminal-truth bridge absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] summary binding terminal-truth bridge absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "docs/release/identity-v1.6x-release-closure-summary.md"
# expected fail-close: summary_doc_missing_terminal_truth_bridge_marker:terminal_truth_bridge_surface=...
mutate_probe_literal \
  "${TMP_ROOT}/docs/release/identity-v1.6x-release-closure-summary.md" \
  'terminal_truth_bridge_surface=' \
  'terminal_truth_bridge_surface_missing='
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-terminal-truth-bridge-negative-doc.json; then
  echo "[FAIL] release summary terminal-truth bridge marker drift unexpectedly passed"
  exit 1
fi
echo "[PASS] release summary terminal-truth bridge marker drift fail-closed as expected"

PROJECT_IDENTITY_HOME="$(cd "${ROOT}/.." && pwd)/.identity"
PROBE_ROOT_BASE="${PROJECT_IDENTITY_HOME}/_probe"
mkdir -p "${PROBE_ROOT_BASE}"
E2E_ROOT="$(mktemp -d "${PROBE_ROOT_BASE}/release-readiness-terminal-truth-bridge.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}" "${E2E_ROOT}"' EXIT

PYTHONPATH="${ROOT}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
python3 - "${ROOT}" "${E2E_ROOT}" "${POSITIVE_JSON}" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
e2e_root = Path(sys.argv[2]).resolve()
positive_validator_output = str(Path(sys.argv[3]).resolve())
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from blocker_taxonomy_common import BLOCKER_ALIAS_MAP_VERSION, CANONICAL_BLOCKER_TYPES
from create_identity_pack import _collaboration_trigger_contract_skeleton
from release_readiness_terminal_truth_bridge_common import (
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    build_release_readiness_terminal_truth_bridge_projection,
)
from terminal_truth_cleanliness_common import terminal_truth_cleanliness_contract_skeleton

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
canonical_blockers = list(CANONICAL_BLOCKER_TYPES)
catalog_path = (e2e_root / "catalog.local.yaml").resolve()

def _report_base(*, identity_id: str, pack_path: Path, prompt_path: Path, prompt_sha: str, outlet_path: Path) -> dict[str, object]:
    return {
        "identity_id": identity_id,
        "generated_at": now,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "identity_prompt_path": str(prompt_path),
        "identity_prompt_sha256": prompt_sha,
        "protocol_commit_sha": protocol_commit_sha,
        "protocol_head_sha_at_run_start": protocol_commit_sha,
        "all_ok": True,
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
        "outlet_preflight_receipt": str(outlet_path),
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
            str((pack_path / "RULEBOOK.jsonl").resolve()),
            str((pack_path / "TASK_HISTORY.md").resolve()),
            str((pack_path / "runtime" / "state" / "prompt_contract.json").resolve()),
        ],
        "writeback_rule_id": "",
        "artifacts": [],
        "skills_used": [],
        "mcp_tools_used": [],
        "tool_calls_used": [],
        "active_skills": [],
        "mcp_servers_checked": [],
        "tool_routes": [],
        "capability_activation_status": "PASS_REQUIRED",
        "capability_activation_error_code": "",
        "capability_contract_required": True,
        "route_scope": "identity_pack",
        "route_scope_mode": "pack_local",
        "route_ids": ["default"],
        "route_selection_cardinality": 1,
        "declared_dependency_projection": [],
        "observed_dependency_projection": [],
        "dependency_gap_reasons": [],
        "undeclared_usage_detected": False,
        "undeclared_usage_rows": [],
        "missing_declared_dependency_detected": False,
        "missing_declared_dependency_rows": [],
    }


def _seed_identity(spec: dict[str, object]) -> dict[str, str]:
    identity_id = str(spec["identity_id"])
    pack_path = (e2e_root / identity_id).resolve()
    reports_dir = pack_path / "runtime" / "reports"
    state_dir = pack_path / "runtime" / "state"
    reports_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    rulebook_path = (pack_path / "RULEBOOK.jsonl").resolve()
    task_history_path = (pack_path / "TASK_HISTORY.md").resolve()
    prompt_contract_path = (state_dir / "prompt_contract.json").resolve()
    prompt_path = (pack_path / "IDENTITY_PROMPT.md").resolve()
    outlet_preflight_path = (reports_dir / "outlet-preflight.json").resolve()

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
                "This prompt exists only to drive release-readiness terminal-truth bridge probes.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    outlet_preflight_path.write_text(
        json.dumps({"status": "PASS_REQUIRED", "identity_id": identity_id}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

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
    (pack_path / "CURRENT_TASK.json").write_text(
        json.dumps(task_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    prompt_sha = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    report_doc = _report_base(
        identity_id=identity_id,
        pack_path=pack_path,
        prompt_path=prompt_path,
        prompt_sha=prompt_sha,
        outlet_path=outlet_preflight_path,
    )
    report_doc.update(
        {
            "run_id": str(spec["run_id"]),
            "mode": str(spec["mode"]),
            "next_action": str(spec["next_action"]),
            "is_terminal_clean": bool(spec["is_terminal_clean"]),
            "publishable": bool(spec["publishable"]),
            "canonical_result_eligible": bool(spec["canonical_result_eligible"]),
            "terminal_truth_class": str(spec["terminal_truth_class"]),
            "terminal_state_class": str(spec["terminal_state_class"]),
            "negative_feedback_class": str(spec["negative_feedback_class"]),
            "upgrade_required": bool(spec.get("upgrade_required", False)),
        }
    )
    if report_doc["upgrade_required"]:
        report_doc["writeback_status"] = "WRITTEN"
        report_doc["experience_writeback"] = {
            "required": True,
            "status": "WRITTEN",
            "error_code": "",
            "mode": str(spec["mode"]),
        }
    report_path = (reports_dir / f"identity-upgrade-exec-{identity_id}-{spec['report_suffix']}.json").resolve()
    report_path.write_text(json.dumps(report_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (state_dir / "active_execution_report.json").write_text(
        json.dumps(
            {
                "run_id": str(spec["run_id"]),
                "report_path": str(report_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "identity_id": identity_id,
        "report_path": str(report_path),
        "run_id": str(spec["run_id"]),
        "case_name": str(spec["case_name"]),
        "repair_before_release_readiness": "true"
        if bool(spec.get("repair_before_release_readiness", False))
        else "false",
    }


identity_specs = (
    {
        "case_name": "clean_terminal_truth",
        "identity_id": "release-readiness-terminal-truth-bridge-clean-e2e",
        "report_suffix": "clean",
        "run_id": "identity-upgrade-exec-release-readiness-terminal-truth-bridge-clean-e2e-clean",
        "mode": "safe-auto",
        "next_action": "no_upgrade_triggered",
        "is_terminal_clean": True,
        "publishable": True,
        "canonical_result_eligible": True,
        "terminal_truth_class": "clean_terminal_truth",
        "terminal_state_class": "completed_clean",
        "negative_feedback_class": "",
        "upgrade_required": False,
    },
    {
        "case_name": "review_required_execution_closure",
        "identity_id": "release-readiness-terminal-truth-bridge-review-e2e",
        "report_suffix": "review-required",
        "run_id": "identity-upgrade-exec-release-readiness-terminal-truth-bridge-review-e2e-review-required",
        "mode": "review-required",
        "next_action": "review_required_followup",
        "is_terminal_clean": False,
        "publishable": False,
        "canonical_result_eligible": False,
        "terminal_truth_class": "review_required_execution_closure",
        "terminal_state_class": "review_pending",
        "negative_feedback_class": "review_required",
        "upgrade_required": False,
        "repair_before_release_readiness": True,
    },
)

seeded = [_seed_identity(spec) for spec in identity_specs]
catalog_doc = {
    "identities": [
        {
            "id": row["identity_id"],
            "pack_path": str((e2e_root / row["identity_id"]).resolve()),
            "scope": "USER",
            "status": "active",
            "profile": "runtime",
        }
        for row in seeded
    ]
}
catalog_path.write_text(
    json.dumps(catalog_doc, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

env = dict(os.environ)
env["IDENTITY_CATALOG"] = str(catalog_path)


def _run_release_readiness(row: dict[str, str]) -> tuple[int, dict[str, object], dict[str, object]]:
    if row.get("repair_before_release_readiness") == "true":
        repair_proc = subprocess.run(
            [
                "python3",
                "scripts/repair_identity_post_execution_mandatory.py",
                "--catalog",
                str(catalog_path),
                "--repo-catalog",
                str(catalog_path),
                "--identity-id",
                row["identity_id"],
                "--report",
                row["report_path"],
                "--apply",
                "--json-only",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
        )
        if repair_proc.returncode != 0:
            raise AssertionError(
                f"repair_failed case={row['case_name']} rc={repair_proc.returncode}\nSTDOUT:\n{repair_proc.stdout}\nSTDERR:\n{repair_proc.stderr}"
            )
        repair_payload = json.loads(repair_proc.stdout)
        if repair_payload.get("post_execution_report_repair_status") != STATUS_PASS_REQUIRED:
            raise AssertionError(
                f"repair_status_not_green case={row['case_name']} payload={repair_payload}"
            )
        if repair_payload.get("repair_blocking_status") != STATUS_PASS_REQUIRED:
            raise AssertionError(
                f"repair_blocking_not_green case={row['case_name']} payload={repair_payload}"
            )
        if repair_payload.get("post_execution_validation_status_after") != STATUS_PASS_REQUIRED:
            raise AssertionError(
                f"repair_postexec_not_green case={row['case_name']} payload={repair_payload}"
            )
        if repair_payload.get("writeback_continuity_status_after") != STATUS_PASS_REQUIRED:
            raise AssertionError(
                f"repair_writeback_not_green case={row['case_name']} payload={repair_payload}"
            )

    summary_path = (e2e_root / f"summary-{row['identity_id']}.json").resolve()
    proc = subprocess.run(
        [
            "python3",
            "scripts/release_readiness_check.py",
            "--identity-id",
            row["identity_id"],
            "--catalog",
            str(catalog_path),
            "--execution-report",
            row["report_path"],
            "--check-name",
            "scripts/validate_terminal_truth_cleanliness.py",
            "--summary-out",
            str(summary_path),
        ],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
    )
    if not summary_path.exists():
        raise AssertionError(
            f"summary_missing case={row['case_name']} rc={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    bridge = build_release_readiness_terminal_truth_bridge_projection(summary)
    return proc.returncode, summary, bridge


results: list[dict[str, object]] = []
for row in seeded:
    rc, summary, bridge = _run_release_readiness(row)
    case_name = row["case_name"]
    if case_name == "clean_terminal_truth":
        assert rc == 0, (case_name, rc, summary)
        assert summary["release_readiness_status"] == STATUS_PASS_REQUIRED, summary
        assert bridge["terminal_truth_bridge_status"] == STATUS_PASS_REQUIRED, bridge
        assert bridge["review_veto_semantics_alignment_status"] == STATUS_SKIPPED_NOT_REQUIRED, bridge
        assert bridge["admission_lane_projection"] == "NOT_BLOCKED_BY_TERMINAL_TRUTH", bridge
        assert bridge["boundary_publishable"] is True, bridge
        assert bridge["active_runtime_publishable"] is True, bridge
    elif case_name == "review_required_execution_closure":
        assert rc == 1, (case_name, rc, summary)
        assert summary["release_readiness_status"] == "FAIL_REQUIRED", summary
        assert bridge["terminal_truth_bridge_status"] == STATUS_PASS_REQUIRED, bridge
        assert bridge["review_veto_semantics_alignment_status"] == STATUS_PASS_REQUIRED, bridge
        assert bridge["repair_success_not_clean_terminal_truth"] is True, bridge
        assert bridge["admission_lane_projection"] == "BLOCKED_BY_TERMINAL_TRUTH", bridge
        assert bridge["active_runtime_negative_feedback_class"] == "review_required", bridge
        assert bridge["active_runtime_next_state_after_veto"] == "review_pending", bridge
    else:
        raise AssertionError(f"unexpected_case:{case_name}")
    results.append(
        {
            "case_name": case_name,
            "identity_id": row["identity_id"],
            "bridge_status": bridge["terminal_truth_bridge_status"],
            "release_readiness_status": summary["release_readiness_status"],
        }
    )

print(
    json.dumps(
        {
            "release_readiness_terminal_truth_bridge_probe_status": STATUS_PASS_REQUIRED,
            "positive_validator_output": positive_validator_output,
            "bridge_case_count": len(results),
            "bridge_cases": [row["case_name"] for row in results],
            "seeded_identity_ids": [row["identity_id"] for row in results],
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] release-readiness terminal-truth bridge probes passed"
