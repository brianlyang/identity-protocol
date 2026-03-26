#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-${REPO_ROOT}}/.tmp-runtime}}"
WORK_ROOT="${MONOTONIC_PROBE_WORK_ROOT:-${TMP_ROOT_BASE%/}/identity-monotonic-floor-probes}"
FIXTURE_ROOT="${WORK_ROOT}/fixtures"
FIXTURE_MANIFEST_PATH="${WORK_ROOT}/fixture_paths.monotonic_floor_probes.json"
RESULT_ROOT="${WORK_ROOT}/results"
MANIFEST_PATH="${WORK_ROOT}/manifest.monotonic_floor_probes.json"

mkdir -p "${FIXTURE_ROOT}" "${RESULT_ROOT}"

python3 - <<'PY' "${FIXTURE_ROOT}" "${FIXTURE_MANIFEST_PATH}"
from __future__ import annotations

import json
from pathlib import Path
import hashlib
import yaml
import sys

fixture_root = Path(sys.argv[1]).resolve()
fixture_manifest_path = Path(sys.argv[2]).resolve()
fixture_root.mkdir(parents=True, exist_ok=True)

identity_root = fixture_root / "identity"
probe_floor_pack = identity_root / "probe-floor"
probe_mm_pack = identity_root / "probe-mm"

(probe_floor_pack / "runtime").mkdir(parents=True, exist_ok=True)
(probe_mm_pack / "runtime" / "plugins").mkdir(parents=True, exist_ok=True)
(probe_mm_pack / "runtime" / "reports").mkdir(parents=True, exist_ok=True)

catalog = {
    "default_identity": "probe-floor",
    "identities": [
        {
            "id": "probe-floor",
            "status": "active",
            "pack_path": str(probe_floor_pack),
        },
        {
            "id": "probe-mm",
            "status": "active",
            "pack_path": str(probe_mm_pack),
        },
    ],
}

reasoning_contract_floor = {
    "required": True,
    "contract_id": "rq_035_reasoning_loop_failclose_contract_v1",
    "plugin_id": "reasoning-loop-enforcement",
    "validator": "scripts/validate_reasoning_loop_failclose.py",
    "plugin_registry_path": "identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml",
    "contract_file": "identity/protocol/plugins/reasoning-loop-enforcement/plugin.contract.yaml",
    "reasoning_enforcement_level": "L0",
    "strict_run_id_binding": True,
    "runtime_report_selection_mode": "prefer_run_id",
}

reasoning_contract_mm = dict(reasoning_contract_floor)
reasoning_contract_mm["reasoning_enforcement_level"] = "L1"

multimodal_contract = {
    "required": True,
    "contract_id": "rq_034_multimodal_plugin_enforcement_contract_v1",
    "validator": "scripts/validate_multimodal_plugin_enforcement.py",
    "plugin_registry_path": "identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml",
    "provider_profiles_path": "identity/protocol/plugins/PROVIDER_PROFILES.current.yaml",
    "provider_binding_path_pattern": "runtime/plugins/provider-bindings.local.yaml",
}

probe_gateway_contract = {
    "required": True,
    "contract_id": "protocol_host_unique_channel_contract_v1",
    "ingress_wrapper_path": "runtime/gate/protocol_ingress_wrapper.py",
    "ingress_wrapper_dispatch_token": "probe_mm_wrapper_dispatch_v1",
    "host_dispatch_mode": "advisory",
    "host_release_mode": "advisory",
    "entry_receipt_policy": {
        "required_surface_label": "host_ingress_wrapper",
        "required_wrapper_surface_status": "PASS_REQUIRED",
        "required_wrapper_dispatch_token_status": "PASS_REQUIRED",
    },
    "operation_profile_policy": {
        "strict_operations": [
            "activate",
            "update",
            "validate",
            "readiness",
            "e2e",
            "ci",
            "three-plane",
            "mutation",
        ],
        "light_operations": ["scan", "inspection"],
        "strict_gate_profile": "strict_full",
        "light_gate_profile": "inspection_targeted",
        "allow_upgrade_only": True,
    },
}

outlet_contract = {
    "required": True,
    "contract_id": "rq_004_outlet_matrix_contract_v1",
    "validator": "scripts/validate_outlet_matrix.py",
}

promotion_contract = {
    "required": True,
    "contract_id": "rq_003_promotion_evidence_pipeline_contract_v1",
    "validator": "scripts/validate_promotion_pipeline.py",
}

phase_contract = {
    "required": True,
    "contract_id": "rq_010_phase_a_bootstrap_before_strict_contract_v1",
    "validator": "scripts/validate_phase_bootstrap_before_strict.py",
}

fallback_contract = {
    "required": True,
    "contract_id": "rq_022_fallback_taxonomy_normalization_contract_v1",
    "validator": "scripts/validate_fallback_taxonomy_normalization.py",
}

xwf_contract = {
    "required": True,
    "contract_id": "rq_019_cross_workflow_evidence_schema_contract_v1",
    "validator": "scripts/validate_cross_workflow_schema.py",
    "evidence_path_pattern": "runtime/reports/identity-upgrade-exec-probe-mm-*.json",
}


def compute_promotion_decision_hash(doc: dict[str, object]) -> str:
    base = {
        "identity_id": str(doc.get("identity_id", "")),
        "report_path": str(doc.get("report_path", "")),
        "all_ok": bool(doc.get("all_ok", False)),
        "writeback_status": str(doc.get("writeback_status", "")),
        "permission_state": str(doc.get("permission_state", "")),
        "error_code": str(doc.get("error_code", "")),
        "protocol_mode": str(doc.get("protocol_mode", "")),
    }
    return hashlib.sha256(
        json.dumps(base, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def build_probe_runtime_report_path(pack_root: Path, identity_id: str, report_role: str) -> Path:
    return (
        pack_root
        / "runtime"
        / "reports"
        / f"identity-upgrade-exec-{identity_id}-{report_role}.json"
    )

(probe_floor_pack / "CURRENT_TASK.json").write_text(
    json.dumps(
        {
            "reasoning_loop_failclose_contract_v1": reasoning_contract_floor,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

(probe_mm_pack / "CURRENT_TASK.json").write_text(
    json.dumps(
        {
            "protocol_host_unique_channel_contract_v1": probe_gateway_contract,
            "multimodal_plugin_enforcement_contract_v1": multimodal_contract,
            "outlet_regression_matrix_contract_v1": outlet_contract,
            "status_promotion_evidence_contract_v1": promotion_contract,
            "phase_bootstrap_before_strict_contract_v1": phase_contract,
            "fallback_taxonomy_normalization_contract_v1": fallback_contract,
            "cross_workflow_evidence_schema_contract_v1": xwf_contract,
            "reasoning_loop_failclose_contract_v1": reasoning_contract_mm,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

(probe_mm_pack / "runtime" / "plugins" / "provider-bindings.local.yaml").write_text(
    yaml.safe_dump(
        {
            "bindings": [
                {
                    "plugin_id": "multimodal-vision-enforcement",
                    "provider_profile_id": "glm46v_vision_prod",
                    "credential_ref": "vault:dummy/credential",
                    "enabled": True,
                },
                {
                    "plugin_id": "multimodal-vision-enforcement",
                    "provider_profile_id": "openai_vision_prod",
                    "credential_ref": "vault:dummy/openai_credential",
                    "enabled": True,
                }
            ]
        },
        sort_keys=False,
        allow_unicode=True,
    ),
    encoding="utf-8",
)

pointer_report_path = build_probe_runtime_report_path(
    probe_mm_pack,
    "probe-mm",
    "pointer-selected-upgrade-report",
)
explicit_report_path = build_probe_runtime_report_path(
    probe_mm_pack,
    "probe-mm",
    "explicit-override-upgrade-report",
)
explicit_receipt_path = (
    probe_mm_pack / "runtime" / "reports" / "promotion-evidence-explicit-receipt.json"
)

pointer_report_doc = {
    "identity_id": "probe-mm",
    "report_path": str(pointer_report_path),
    "all_ok": True,
    "upgrade_required": True,
    "writeback_status": "WRITTEN",
    "writeback_rule_id": "probe-mm-ewb-pointer-rule",
    "writeback_paths": ["RULEBOOK.jsonl", "TASK_HISTORY.md"],
    "experience_writeback": {
        "status": "WRITTEN",
        "error_code": "",
    },
    "permission_state": "PASS_REQUIRED",
    "protocol_mode": "strict",
    "input_hash": "probe-mm-promotion-input-pointer",
    "reviewer_role": "protocol_auditor",
    "reviewer_signature_ref": "runtime/reports/promotion/pointer-review.sig",
    "evidence_bundle_refs": ["runtime/reports/promotion/pointer-evidence.json"],
    "run_id": "identity-upgrade-exec-probe-mm-old",
    "check_results": [],
    "multimodal_runtime_evidence_status": "SKIPPED_NOT_REQUIRED",
    "runtime_stage_deferred": True,
    "runtime_stage_deferred_reason": "legacy_report_missing_runtime_stage_pre_execution",
    "route_action": "pointer_selected_validation_path",
    "dedup_state": "pointer_selected_stable_winner",
    "schema_version": "v1",
    "send_time_gate_status": "PASS_REQUIRED",
    "governed_outlet_enforced": True,
    "outlet_bypass_detected": False,
    "outlet_channel_id": "final_emit_governed",
    "final_emit_channel_id": "final_emit_governed",
    "final_emit_policy_mode": "tool_choice_required",
    "final_emit_schema_id": "protocol.final_emit.v1",
    "final_emit_schema_status": "PASS_REQUIRED",
    "final_emit_contract_status": "PASS_REQUIRED",
    "blocker_receipt_path": "",
    "outlet_preflight_receipt": "runtime/receipts/outlet-preflight-pointer.json",
}

explicit_report_doc = {
    "identity_id": "probe-mm",
    "report_path": str(explicit_report_path),
    "all_ok": True,
    "upgrade_required": True,
    "writeback_status": "WRITTEN",
    "writeback_rule_id": "probe-mm-ewb-explicit-rule",
    "writeback_paths": ["RULEBOOK.jsonl", "TASK_HISTORY.md"],
    "experience_writeback": {
        "status": "WRITTEN",
        "error_code": "",
    },
    "permission_state": "PASS_REQUIRED",
    "protocol_mode": "strict",
    "input_hash": "probe-mm-promotion-input-explicit-report",
    "reviewer_role": "protocol_auditor",
    "reviewer_signature_ref": "runtime/reports/promotion/explicit-report-review.sig",
    "evidence_bundle_refs": ["runtime/reports/promotion/explicit-report-evidence.json"],
    "phase_a_refresh_applied": True,
    "phase_b_strict_revalidate_status": "PASS_REQUIRED",
    "run_id": "identity-upgrade-exec-probe-mm-explicit",
    "route_action": "explicit_override_validation_path",
    "dedup_state": "explicit_override_stable_winner",
    "schema_version": "v1",
    "check_results": [
        {
            "cmd": "python3 scripts/validate_multimodal_plugin_enforcement.py --json-only",
            "stdout": "{\"multimodal_runtime_evidence_status\":\"PASS_REQUIRED\"}",
        }
    ],
    "multimodal_summary": {
        "calls": 1,
        "resolved": 1,
        "unresolved": 0,
        "errors": 0,
        "retry_calls": 0,
        "mode": "required",
        "required_confidence": 0.92,
    },
    "multimodal_calls": 1,
    "multimodal_resolved": 1,
    "multimodal_unresolved": 0,
    "multimodal_errors": 0,
    "multimodal_retry_calls": 0,
    "multimodal_preflight_status": "PASS_REQUIRED",
    "runtime_gate_mode": "required",
    "runtime_gate_required_confidence": 0.92,
    "multimodal_evidence_refs": [
        "runtime/reports/input-gate/probe-mm-input-gate.json"
    ],
    "send_time_gate_status": "PASS_REQUIRED",
    "governed_outlet_enforced": True,
    "outlet_bypass_detected": False,
    "outlet_channel_id": "final_emit_governed",
    "final_emit_channel_id": "final_emit_governed",
    "final_emit_policy_mode": "tool_choice_required",
    "final_emit_schema_id": "protocol.final_emit.v1",
    "final_emit_schema_status": "PASS_REQUIRED",
    "final_emit_contract_status": "PASS_REQUIRED",
    "blocker_receipt_path": "",
    "outlet_preflight_receipt": "runtime/receipts/outlet-preflight-explicit.json",
}

explicit_receipt_doc = {
    "identity_id": "probe-mm",
    "report_path": str(explicit_report_path),
    "all_ok": True,
    "writeback_status": "WRITTEN",
    "permission_state": "PASS_REQUIRED",
    "protocol_mode": "strict",
    "input_hash": "probe-mm-promotion-input-explicit-receipt",
    "reviewer_role": "protocol_auditor",
    "reviewer_signature_ref": "runtime/reports/promotion/explicit-receipt-review.sig",
    "evidence_bundle_refs": ["runtime/reports/promotion/explicit-receipt-evidence.json"],
}

pointer_report_doc["decision_hash"] = compute_promotion_decision_hash(pointer_report_doc)
explicit_report_doc["decision_hash"] = compute_promotion_decision_hash(explicit_report_doc)
explicit_receipt_doc["decision_hash"] = compute_promotion_decision_hash(explicit_receipt_doc)

pointer_report_path.write_text(
    json.dumps(
        pointer_report_doc,
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

explicit_report_path.write_text(
    json.dumps(
        explicit_report_doc,
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

explicit_receipt_path.write_text(
    json.dumps(
        explicit_receipt_doc,
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

(probe_mm_pack / "RULEBOOK.jsonl").write_text(
    "\n".join(
        [
            json.dumps(
                {
                    "entry_id": "probe-mm-ewb-pointer-rule",
                    "evidence_run_id": "identity-upgrade-exec-probe-mm-old",
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "entry_id": "probe-mm-ewb-explicit-rule",
                    "evidence_run_id": "identity-upgrade-exec-probe-mm-explicit",
                },
                ensure_ascii=False,
            ),
        ]
    )
    + "\n",
    encoding="utf-8",
)

(probe_mm_pack / "TASK_HISTORY.md").write_text(
    "\n".join(
        [
            "- identity-upgrade-exec-probe-mm-old",
            "- identity-upgrade-exec-probe-mm-explicit",
        ]
    )
    + "\n",
    encoding="utf-8",
)

(probe_mm_pack / "runtime" / "state").mkdir(parents=True, exist_ok=True)
(probe_mm_pack / "runtime" / "state" / "active_execution_report.json").write_text(
    json.dumps(
        {
            "report_path": str(pointer_report_path),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

(probe_mm_pack / "runtime" / "receipts").mkdir(parents=True, exist_ok=True)
(probe_mm_pack / "runtime" / "reports" / "input-gate").mkdir(parents=True, exist_ok=True)
(probe_mm_pack / "runtime" / "reports" / "input-gate" / "probe-mm-input-gate.json").write_text(
    json.dumps({"status": "PASS_REQUIRED"}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

(fixture_root / "catalog.yaml").write_text(
    yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)

fixture_manifest_path.parent.mkdir(parents=True, exist_ok=True)
fixture_manifest_path.write_text(
    json.dumps(
        {
            "catalog_path": str((fixture_root / "catalog.yaml").resolve()),
            "pointer_report_path": str(pointer_report_path.resolve()),
            "explicit_report_path": str(explicit_report_path.resolve()),
            "explicit_receipt_path": str(explicit_receipt_path.resolve()),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY

CATALOG_PATH="${FIXTURE_ROOT}/catalog.yaml"
EXPLICIT_REPORT_PATH="$(python3 - <<'PY' "${FIXTURE_MANIFEST_PATH}"
from __future__ import annotations

import json
import sys
from pathlib import Path

doc = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(str(doc.get('explicit_report_path', '')).strip())
PY
)"
EXPLICIT_RECEIPT_PATH="$(python3 - <<'PY' "${FIXTURE_MANIFEST_PATH}"
from __future__ import annotations

import json
import sys
from pathlib import Path

doc = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(str(doc.get('explicit_receipt_path', '')).strip())
PY
)"

run_probe() {
  local name="$1"
  shift
  local cmd=("$@")

  local stdout_path="${RESULT_ROOT}/${name}.stdout.json"
  local stderr_path="${RESULT_ROOT}/${name}.stderr.log"
  local meta_path="${RESULT_ROOT}/${name}.meta.json"
  local timestamp_utc
  timestamp_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local cmd_string
  cmd_string="$(printf '%q ' "${cmd[@]}")"
  cmd_string="${cmd_string% }"

  set +e
  "${cmd[@]}" >"${stdout_path}" 2>"${stderr_path}"
  local rc=$?
  set -e

  if [ ! -s "${stderr_path}" ]; then
    rm -f "${stderr_path}"
  fi

  python3 - <<'PY' "${name}" "${rc}" "${stdout_path}"
from __future__ import annotations

import json
import sys
from pathlib import Path

name = sys.argv[1]
rc = int(sys.argv[2])
stdout_path = Path(sys.argv[3])

doc = json.loads(stdout_path.read_text(encoding="utf-8"))

if name == "reasoning_floor_l0_fail":
    if rc == 0:
        raise SystemExit("reasoning_floor_l0_fail: expected non-zero rc")
    if str(doc.get("reasoning_loop_failclose_status", "")).strip().upper() != "FAIL_REQUIRED":
        raise SystemExit("reasoning_floor_l0_fail: status mismatch")
    if str(doc.get("error_code", "")).strip() != "IP-RL-CONF-001":
        raise SystemExit("reasoning_floor_l0_fail: error_code mismatch")
elif name == "multimodal_update_defer_allowed":
    if rc != 0:
        raise SystemExit("multimodal_update_defer_allowed: expected rc=0")
    if str(doc.get("multimodal_plugin_enforcement_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("multimodal_update_defer_allowed: plugin status mismatch")
    if str(doc.get("multimodal_runtime_evidence_status", "")).strip().upper() != "SKIPPED_NOT_REQUIRED":
        raise SystemExit("multimodal_update_defer_allowed: runtime evidence status mismatch")
    if str(doc.get("runtime_report_selection_mode", "")).strip() != "active_execution_pointer":
        raise SystemExit("multimodal_update_defer_allowed: selection mode mismatch")
    if str(doc.get("runtime_report_selected_authority_class", "")).strip() != "active_execution_pointer_pack_local_report":
        raise SystemExit("multimodal_update_defer_allowed: authority class mismatch")
    if str(doc.get("runtime_report_pointer_resolution_mode", "")).strip() != "pointer_candidate_root_report":
        raise SystemExit("multimodal_update_defer_allowed: pointer resolution mismatch")
elif name == "multimodal_readiness_skip_blocked":
    if rc == 0:
        raise SystemExit("multimodal_readiness_skip_blocked: expected non-zero rc")
    if str(doc.get("multimodal_plugin_enforcement_status", "")).strip().upper() != "FAIL_REQUIRED":
        raise SystemExit("multimodal_readiness_skip_blocked: plugin status mismatch")
    error_code = str(doc.get("error_code", "")).strip()
    allowed_error_codes = {"IP-MM-RUN-003", "IP-MM-RUN-007", "IP-GATE-ENTRY-002"}
    if error_code not in allowed_error_codes:
        raise SystemExit(
            "multimodal_readiness_skip_blocked: unexpected error_code "
            + (error_code or "<empty>")
        )
    if str(doc.get("runtime_report_selection_mode", "")).strip() != "active_execution_pointer":
        raise SystemExit("multimodal_readiness_skip_blocked: selection mode mismatch")
elif name == "multimodal_explicit_override_pass":
    if rc != 0:
        raise SystemExit("multimodal_explicit_override_pass: expected rc=0")
    if str(doc.get("multimodal_plugin_enforcement_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("multimodal_explicit_override_pass: plugin status mismatch")
    if str(doc.get("multimodal_runtime_evidence_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("multimodal_explicit_override_pass: runtime evidence status mismatch")
    if str(doc.get("runtime_report_selection_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("multimodal_explicit_override_pass: selection mode mismatch")
    if str(doc.get("runtime_report_selected_authority_class", "")).strip() != "explicit_report_override":
        raise SystemExit("multimodal_explicit_override_pass: authority class mismatch")
    if str(doc.get("runtime_report_pointer_resolution_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("multimodal_explicit_override_pass: pointer resolution mismatch")
elif name == "outlet_pointer_selection_pass":
    if rc != 0:
        raise SystemExit("outlet_pointer_selection_pass: expected rc=0")
    if str(doc.get("outlet_matrix_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("outlet_pointer_selection_pass: outlet status mismatch")
    if str(doc.get("report_selection_mode", "")).strip() != "active_execution_pointer":
        raise SystemExit("outlet_pointer_selection_pass: selection mode mismatch")
    if str(doc.get("report_selected_authority_class", "")).strip() != "active_execution_pointer_pack_local_report":
        raise SystemExit("outlet_pointer_selection_pass: authority class mismatch")
    if str(doc.get("report_pointer_resolution_mode", "")).strip() != "pointer_candidate_root_report":
        raise SystemExit("outlet_pointer_selection_pass: pointer resolution mismatch")
elif name == "outlet_explicit_override_pass":
    if rc != 0:
        raise SystemExit("outlet_explicit_override_pass: expected rc=0")
    if str(doc.get("outlet_matrix_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("outlet_explicit_override_pass: outlet status mismatch")
    if str(doc.get("report_selection_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("outlet_explicit_override_pass: selection mode mismatch")
    if str(doc.get("report_selected_authority_class", "")).strip() != "explicit_report_override":
        raise SystemExit("outlet_explicit_override_pass: authority class mismatch")
    if str(doc.get("report_pointer_resolution_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("outlet_explicit_override_pass: pointer resolution mismatch")
elif name == "promotion_pointer_selection_pass":
    if rc != 0:
        raise SystemExit("promotion_pointer_selection_pass: expected rc=0")
    if str(doc.get("promotion_pipeline_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("promotion_pointer_selection_pass: promotion status mismatch")
    if str(doc.get("promotion_evidence_selection_mode", "")).strip() != "active_execution_pointer":
        raise SystemExit("promotion_pointer_selection_pass: selection mode mismatch")
    if str(doc.get("promotion_evidence_selected_authority_class", "")).strip() != "active_execution_pointer_pack_local_report":
        raise SystemExit("promotion_pointer_selection_pass: authority class mismatch")
    if str(doc.get("promotion_evidence_pointer_resolution_mode", "")).strip() != "pointer_candidate_root_report":
        raise SystemExit("promotion_pointer_selection_pass: pointer resolution mismatch")
    if str(doc.get("promotion_evidence_kind", "")).strip() != "report":
        raise SystemExit("promotion_pointer_selection_pass: evidence kind mismatch")
elif name == "promotion_explicit_report_override_pass":
    if rc != 0:
        raise SystemExit("promotion_explicit_report_override_pass: expected rc=0")
    if str(doc.get("promotion_pipeline_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("promotion_explicit_report_override_pass: promotion status mismatch")
    if str(doc.get("promotion_evidence_selection_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("promotion_explicit_report_override_pass: selection mode mismatch")
    if str(doc.get("promotion_evidence_selected_authority_class", "")).strip() != "explicit_report_override":
        raise SystemExit("promotion_explicit_report_override_pass: authority class mismatch")
    if str(doc.get("promotion_evidence_pointer_resolution_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("promotion_explicit_report_override_pass: pointer resolution mismatch")
    if str(doc.get("promotion_evidence_kind", "")).strip() != "report":
        raise SystemExit("promotion_explicit_report_override_pass: evidence kind mismatch")
elif name == "promotion_explicit_receipt_override_pass":
    if rc != 0:
        raise SystemExit("promotion_explicit_receipt_override_pass: expected rc=0")
    if str(doc.get("promotion_pipeline_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("promotion_explicit_receipt_override_pass: promotion status mismatch")
    if str(doc.get("promotion_evidence_selection_mode", "")).strip() != "explicit_receipt_override":
        raise SystemExit("promotion_explicit_receipt_override_pass: selection mode mismatch")
    if str(doc.get("promotion_evidence_selected_authority_class", "")).strip() != "explicit_receipt_override":
        raise SystemExit("promotion_explicit_receipt_override_pass: authority class mismatch")
    if str(doc.get("promotion_evidence_pointer_resolution_mode", "")).strip() != "explicit_receipt_override":
        raise SystemExit("promotion_explicit_receipt_override_pass: pointer resolution mismatch")
    if str(doc.get("promotion_evidence_kind", "")).strip() != "receipt":
        raise SystemExit("promotion_explicit_receipt_override_pass: evidence kind mismatch")
elif name == "phase_pointer_selection_pass":
    if rc != 0:
        raise SystemExit("phase_pointer_selection_pass: expected rc=0")
    if str(doc.get("phase_bootstrap_before_strict_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("phase_pointer_selection_pass: status mismatch")
    if str(doc.get("report_selection_mode", "")).strip() != "active_execution_pointer":
        raise SystemExit("phase_pointer_selection_pass: selection mode mismatch")
    if str(doc.get("report_selected_authority_class", "")).strip() != "active_execution_pointer_pack_local_report":
        raise SystemExit("phase_pointer_selection_pass: authority class mismatch")
    if str(doc.get("report_pointer_resolution_mode", "")).strip() != "pointer_candidate_root_report":
        raise SystemExit("phase_pointer_selection_pass: pointer resolution mismatch")
elif name == "phase_explicit_override_pass":
    if rc != 0:
        raise SystemExit("phase_explicit_override_pass: expected rc=0")
    if str(doc.get("phase_bootstrap_before_strict_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("phase_explicit_override_pass: status mismatch")
    if str(doc.get("report_selection_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("phase_explicit_override_pass: selection mode mismatch")
    if str(doc.get("report_selected_authority_class", "")).strip() != "explicit_report_override":
        raise SystemExit("phase_explicit_override_pass: authority class mismatch")
    if str(doc.get("report_pointer_resolution_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("phase_explicit_override_pass: pointer resolution mismatch")
elif name == "fallback_pointer_selection_pass":
    if rc != 0:
        raise SystemExit("fallback_pointer_selection_pass: expected rc=0")
    if str(doc.get("fallback_taxonomy_normalization_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("fallback_pointer_selection_pass: status mismatch")
    if str(doc.get("report_selection_mode", "")).strip() != "active_execution_pointer":
        raise SystemExit("fallback_pointer_selection_pass: selection mode mismatch")
    if str(doc.get("report_selected_authority_class", "")).strip() != "active_execution_pointer_pack_local_report":
        raise SystemExit("fallback_pointer_selection_pass: authority class mismatch")
    if str(doc.get("report_pointer_resolution_mode", "")).strip() != "pointer_candidate_root_report":
        raise SystemExit("fallback_pointer_selection_pass: pointer resolution mismatch")
elif name == "fallback_explicit_override_pass":
    if rc != 0:
        raise SystemExit("fallback_explicit_override_pass: expected rc=0")
    if str(doc.get("fallback_taxonomy_normalization_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("fallback_explicit_override_pass: status mismatch")
    if str(doc.get("report_selection_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("fallback_explicit_override_pass: selection mode mismatch")
    if str(doc.get("report_selected_authority_class", "")).strip() != "explicit_report_override":
        raise SystemExit("fallback_explicit_override_pass: authority class mismatch")
    if str(doc.get("report_pointer_resolution_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("fallback_explicit_override_pass: pointer resolution mismatch")
elif name == "xwf_pointer_selection_pass":
    if rc != 0:
        raise SystemExit("xwf_pointer_selection_pass: expected rc=0")
    if str(doc.get("cross_workflow_schema_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("xwf_pointer_selection_pass: status mismatch")
    if str(doc.get("evidence_selection_mode", "")).strip() != "active_execution_pointer":
        raise SystemExit("xwf_pointer_selection_pass: selection mode mismatch")
    if str(doc.get("evidence_selected_authority_class", "")).strip() != "active_execution_pointer_pack_local_report":
        raise SystemExit("xwf_pointer_selection_pass: authority class mismatch")
    if str(doc.get("evidence_pointer_resolution_mode", "")).strip() != "pointer_candidate_root_report":
        raise SystemExit("xwf_pointer_selection_pass: pointer resolution mismatch")
    if str(doc.get("evidence_kind", "")).strip() != "report":
        raise SystemExit("xwf_pointer_selection_pass: evidence kind mismatch")
elif name == "xwf_explicit_override_pass":
    if rc != 0:
        raise SystemExit("xwf_explicit_override_pass: expected rc=0")
    if str(doc.get("cross_workflow_schema_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("xwf_explicit_override_pass: status mismatch")
    if str(doc.get("evidence_selection_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("xwf_explicit_override_pass: selection mode mismatch")
    if str(doc.get("evidence_selected_authority_class", "")).strip() != "explicit_report_override":
        raise SystemExit("xwf_explicit_override_pass: authority class mismatch")
    if str(doc.get("evidence_pointer_resolution_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("xwf_explicit_override_pass: pointer resolution mismatch")
    if str(doc.get("evidence_kind", "")).strip() != "report":
        raise SystemExit("xwf_explicit_override_pass: evidence kind mismatch")
elif name == "experience_writeback_pointer_selection_pass":
    if rc != 0:
        raise SystemExit("experience_writeback_pointer_selection_pass: expected rc=0")
    if str(doc.get("experience_writeback_validation_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("experience_writeback_pointer_selection_pass: status mismatch")
    if str(doc.get("report_selection_mode", "")).strip() != "active_execution_pointer":
        raise SystemExit("experience_writeback_pointer_selection_pass: selection mode mismatch")
    if str(doc.get("report_selected_authority_class", "")).strip() != "active_execution_pointer_pack_local_report":
        raise SystemExit("experience_writeback_pointer_selection_pass: authority class mismatch")
    if str(doc.get("report_pointer_resolution_mode", "")).strip() != "pointer_candidate_root_report":
        raise SystemExit("experience_writeback_pointer_selection_pass: pointer resolution mismatch")
    if str(doc.get("writeback_status", "")).strip() != "WRITTEN":
        raise SystemExit("experience_writeback_pointer_selection_pass: writeback status mismatch")
    if int(doc.get("rulebook_match_count", 0) or 0) < 1:
        raise SystemExit("experience_writeback_pointer_selection_pass: rulebook match count mismatch")
    if bool(doc.get("task_history_contains_run_id")) is not True:
        raise SystemExit("experience_writeback_pointer_selection_pass: task history linkage mismatch")
elif name == "experience_writeback_explicit_override_pass":
    if rc != 0:
        raise SystemExit("experience_writeback_explicit_override_pass: expected rc=0")
    if str(doc.get("experience_writeback_validation_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("experience_writeback_explicit_override_pass: status mismatch")
    if str(doc.get("report_selection_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("experience_writeback_explicit_override_pass: selection mode mismatch")
    if str(doc.get("report_selected_authority_class", "")).strip() != "explicit_report_override":
        raise SystemExit("experience_writeback_explicit_override_pass: authority class mismatch")
    if str(doc.get("report_pointer_resolution_mode", "")).strip() != "explicit_report_override":
        raise SystemExit("experience_writeback_explicit_override_pass: pointer resolution mismatch")
    if str(doc.get("writeback_status", "")).strip() != "WRITTEN":
        raise SystemExit("experience_writeback_explicit_override_pass: writeback status mismatch")
    if int(doc.get("rulebook_match_count", 0) or 0) < 1:
        raise SystemExit("experience_writeback_explicit_override_pass: rulebook match count mismatch")
    if bool(doc.get("task_history_contains_run_id")) is not True:
        raise SystemExit("experience_writeback_explicit_override_pass: task history linkage mismatch")
else:
    raise SystemExit(f"unknown probe name: {name}")
PY

  local sha256
  sha256="$(python3 - <<'PY' "${stdout_path}"
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
)"

  python3 - <<'PY' "${meta_path}" "${name}" "${stdout_path}" "${sha256}" "${cmd_string}" "${rc}" "${timestamp_utc}"
from __future__ import annotations

import json
import sys
from pathlib import Path

meta_path = Path(sys.argv[1])
name = sys.argv[2]
stdout_path = Path(sys.argv[3])
sha256 = sys.argv[4]
cmd = sys.argv[5]
rc = int(sys.argv[6])
timestamp_utc = sys.argv[7]

payload = {
    "name": name,
    "file": str(stdout_path.resolve()),
    "sha256": sha256,
    "command": cmd,
    "rc": rc,
    "timestamp_utc": timestamp_utc,
}
meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

  echo "[MONOTONIC][PROBE] ${name} rc=${rc} file=${stdout_path}"
}

cd "${REPO_ROOT}"

run_probe reasoning_floor_l0_fail \
  python3 scripts/validate_reasoning_loop_failclose.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-floor \
  --operation validate \
  --json-only

run_probe multimodal_update_defer_allowed \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation update \
  --run-id identity-upgrade-exec-probe-mm-new \
  --target-name multimodal_plugin_enforcement \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

run_probe multimodal_readiness_skip_blocked \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation readiness \
  --run-id identity-upgrade-exec-probe-mm-new \
  --target-name multimodal_plugin_enforcement \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

run_probe multimodal_explicit_override_pass \
  python3 scripts/validate_multimodal_plugin_enforcement.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation readiness \
  --run-id identity-upgrade-exec-probe-mm-explicit \
  --report-selected-path "${EXPLICIT_REPORT_PATH}" \
  --json-only

run_probe outlet_pointer_selection_pass \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --run-id identity-upgrade-exec-probe-mm-old \
  --target-name outlet_matrix \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

run_probe outlet_explicit_override_pass \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --run-id identity-upgrade-exec-probe-mm-explicit \
  --report-selected-path "${EXPLICIT_REPORT_PATH}" \
  --target-name outlet_matrix \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

run_probe promotion_pointer_selection_pass \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --target-name promotion_pipeline \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

run_probe promotion_explicit_report_override_pass \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --report-selected-path "${EXPLICIT_REPORT_PATH}" \
  --target-name promotion_pipeline \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

run_probe promotion_explicit_receipt_override_pass \
  python3 scripts/validate_promotion_pipeline.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --receipt "${EXPLICIT_RECEIPT_PATH}" \
  --json-only

run_probe phase_pointer_selection_pass \
  python3 scripts/validate_phase_bootstrap_before_strict.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --json-only

run_probe phase_explicit_override_pass \
  python3 scripts/validate_phase_bootstrap_before_strict.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --report "${EXPLICIT_REPORT_PATH}" \
  --json-only

run_probe fallback_pointer_selection_pass \
  python3 scripts/validate_fallback_taxonomy_normalization.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --fallback-reason protocol_trigger_not_met \
  --json-only

run_probe fallback_explicit_override_pass \
  python3 scripts/validate_fallback_taxonomy_normalization.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --report "${EXPLICIT_REPORT_PATH}" \
  --fallback-reason protocol_trigger_not_met \
  --json-only

run_probe xwf_pointer_selection_pass \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --run-id identity-upgrade-exec-probe-mm-old \
  --target-name cross_workflow_schema \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

run_probe xwf_explicit_override_pass \
  python3 scripts/required_gate_bundle_runner.py \
  --catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --operation validate \
  --run-id identity-upgrade-exec-probe-mm-explicit \
  --report-selected-path "${EXPLICIT_REPORT_PATH}" \
  --target-name cross_workflow_schema \
  --actor-id assistant:codex \
  --resolved-work-layer protocol \
  --resolved-source-layer project \
  --lock-state LOCK_MATCH \
  --send-time-gate-status PASS_REQUIRED \
  --outlet-bypass-detected false \
  --final-emit-contract-status PASS_REQUIRED \
  --final-emit-policy-mode tool_choice_required \
  --final-emit-schema-status PASS_REQUIRED \
  --json-only

run_probe experience_writeback_pointer_selection_pass \
  python3 scripts/validate_identity_experience_writeback.py \
  --repo-catalog "${CATALOG_PATH}" \
  --local-catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --json-only

run_probe experience_writeback_explicit_override_pass \
  python3 scripts/validate_identity_experience_writeback.py \
  --repo-catalog "${CATALOG_PATH}" \
  --local-catalog "${CATALOG_PATH}" \
  --identity-id probe-mm \
  --execution-report "${EXPLICIT_REPORT_PATH}" \
  --json-only

python3 - <<'PY' "${RESULT_ROOT}" "${MANIFEST_PATH}"
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

result_root = Path(sys.argv[1]).resolve()
manifest_path = Path(sys.argv[2]).resolve()

entries = []
for path in sorted(result_root.glob("*.meta.json")):
    entries.append(json.loads(path.read_text(encoding="utf-8")))

manifest = {
    "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "entries": entries,
}
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False))
PY

echo "[MONOTONIC][PASS] manifest=${MANIFEST_PATH}"
