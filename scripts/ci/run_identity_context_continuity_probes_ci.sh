#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${ROOT}/scripts/shell_strict_entry_common.sh"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-context-continuity-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

eval "$(
  ROOT="${ROOT}" TMP_ROOT="${TMP_ROOT}" python3 - <<'PY'
import json
import os
import shlex
import shutil
import sys
from pathlib import Path

root = Path(os.environ["ROOT"]).resolve()
tmp_root = Path(os.environ["TMP_ROOT"]).resolve()
sys.path.insert(0, str(root / "scripts"))

from identity_context_continuity_common import (  # noqa: E402
    CONTEXT_CONTINUITY_CONTRACT_ID,
    CONTEXT_CONTINUITY_CONTRACT_KEY,
    CONTEXT_CONTINUITY_VALIDATOR_ID,
    CONTINUITY_RECEIPT_CONTRACT_ID,
    CONTINUITY_RECEIPT_KINDS,
    REENTRY_BRIEF_CONSUMPTION_CONTRACT_ID,
    REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY,
    REENTRY_BRIEF_REL,
    REENTRY_BRIEF_VALIDATOR_ID,
    REENTRY_CONSUMPTION_VALIDATOR_ID,
)

IDENTITY_ID = "continuity-probe-identity"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def continuity_contract(*, required: bool) -> dict:
    return {
        "required": bool(required),
        "contract_id": CONTEXT_CONTINUITY_CONTRACT_ID,
        "validator": CONTEXT_CONTINUITY_VALIDATOR_ID,
        "fail_mode": "fail_required",
        "canonical_runtime_families": [
            "runtime/reports/context-continuity",
            "runtime/state/context-continuity",
        ],
    }


def reentry_contract(*, required: bool) -> dict:
    return {
        "required": bool(required),
        "contract_id": REENTRY_BRIEF_CONSUMPTION_CONTRACT_ID,
        "validators": [
            REENTRY_BRIEF_VALIDATOR_ID,
            REENTRY_CONSUMPTION_VALIDATOR_ID,
        ],
        "fail_mode": "fail_required",
        "bind_object": {
            "artifact_kind": "reentry_brief",
            "artifact_ref": REENTRY_BRIEF_REL.as_posix(),
        },
        "receipt_family_contract_id": CONTINUITY_RECEIPT_CONTRACT_ID,
    }


def base_task(*, continuity_required: bool, reentry_required: bool) -> dict:
    return {
        "identity_id": IDENTITY_ID,
        CONTEXT_CONTINUITY_CONTRACT_KEY: continuity_contract(required=continuity_required),
        REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY: reentry_contract(required=reentry_required),
    }


def checkpoint_doc(
    *,
    continuity_id: str,
    artifact_kind: str,
    supersedes_ref: str = "",
    freshness_status: str = "fresh",
    authority_override: bool = False,
) -> dict:
    doc = {
        "continuity_id": continuity_id,
        "artifact_kind": artifact_kind,
        "generation_reason": "checkpoint_emit",
        "trigger_class": "turn_cadence",
        "source_identity_id": IDENTITY_ID,
        "source_layer": "project",
        "work_layer": "instance",
        "authority_refs": [
            {"ref": "CURRENT_TASK.json"},
            {"ref": "IDENTITY_PROMPT.md"},
        ],
        "task_focus_summary": {
            "summary": "Preserve bounded task continuity across fresh-session recovery.",
        },
        "completed_since_previous": [
            "Validated continuity artifact envelope.",
        ],
        "open_blockers": [
            "Await live adoption proof.",
        ],
        "next_actions": [
            "Emit governed runtime evidence.",
        ],
        "receipt_refs": [
            {"ref": "runtime/reports/context-continuity/placeholder-receipt.json"},
        ],
        "supersedes_ref": supersedes_ref,
        "freshness": {
            "status": freshness_status,
            "policy": "default_turns_15_30_60",
        },
    }
    if authority_override:
        doc["authority_override"] = True
    return doc


def reentry_brief_doc(
    *,
    continuity_id: str,
    supersedes_ref: str,
    freshness_status: str = "fresh",
    authority_override: bool = False,
) -> dict:
    doc = checkpoint_doc(
        continuity_id=continuity_id,
        artifact_kind="reentry_brief",
        supersedes_ref=supersedes_ref,
        freshness_status=freshness_status,
        authority_override=authority_override,
    )
    doc["generation_reason"] = "startup_reentry"
    doc["trigger_class"] = "launcher_restart_or_recover"
    doc["stable_prefix"] = {
        "identity_ref": "IDENTITY_PROMPT.md",
        "task_ref": "CURRENT_TASK.json",
        "lane_ref": "startup_resume_recover",
        "authority_ref_set": [
            "docs/governance/identity-context-continuity-governance-v1.6.16.md",
        ],
        "contract_ref_set": [
            CONTEXT_CONTINUITY_CONTRACT_ID,
            REENTRY_BRIEF_CONSUMPTION_CONTRACT_ID,
        ],
    }
    doc["dynamic_tail"] = {
        "lineage_ref": supersedes_ref,
        "completed_items": [
            "Checkpoint lineage refreshed.",
        ],
        "blockers": [
            "Need startup consumption proof.",
        ],
        "next_actions": [
            "Consume governed reentry brief on startup.",
        ],
        "receipt_refs": [
            {"ref": "runtime/reports/context-continuity/reentry-consumption-receipt.json"},
        ],
    }
    return doc


def relative(pack_root: Path, target: Path) -> str:
    return target.resolve().relative_to(pack_root.resolve()).as_posix()


def checkpoint_receipt_doc(*, pack_root: Path, artifact_path: Path, artifact_kind: str, role: str) -> dict:
    return {
        "receipt_kind": CONTINUITY_RECEIPT_KINDS[role],
        "artifact_ref": relative(pack_root, artifact_path),
        "artifact_kind": artifact_kind,
        "route_or_entry_scope": "startup_resume_recover",
    }


def reentry_brief_receipt_doc(*, pack_root: Path, brief_path: Path, continuity_lineage_ref: str) -> dict:
    return {
        "receipt_kind": CONTINUITY_RECEIPT_KINDS["reentry_brief"],
        "reentry_brief_ref": relative(pack_root, brief_path),
        "continuity_lineage_ref": continuity_lineage_ref,
        "route_or_entry_scope": "startup_resume_recover",
    }


def reentry_consumption_receipt_doc(*, pack_root: Path, brief_path: Path, continuity_lineage_ref: str) -> dict:
    return {
        "receipt_kind": CONTINUITY_RECEIPT_KINDS["reentry_consumption"],
        "identity_reentry_brief_status": "PASS_REQUIRED",
        "startup_consumption_status": "PASS_REQUIRED",
        "reentry_brief_ref": relative(pack_root, brief_path),
        "continuity_lineage_ref": continuity_lineage_ref,
        "authority_resolution_status": "PASS_REQUIRED",
        "tuple_bootstrap_preserved": True,
        "launcher_bind_status": "PASS_REQUIRED",
        "consumption_outcome": "governed_reentry_brief_consumed",
        "route_or_entry_scope": "startup_resume_recover",
    }


def seed_pack(pack_root: Path, *, continuity_required: bool, reentry_required: bool) -> None:
    (pack_root / "runtime" / "reports" / "context-continuity").mkdir(parents=True, exist_ok=True)
    (pack_root / "runtime" / "state" / "context-continuity").mkdir(parents=True, exist_ok=True)
    write_json(
        pack_root / "CURRENT_TASK.json",
        base_task(
            continuity_required=continuity_required,
            reentry_required=reentry_required,
        ),
    )


def clone_pack(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


dormant_pack = tmp_root / "dormant-pack"
seed_pack(dormant_pack, continuity_required=False, reentry_required=False)

artifact_pass_pack = tmp_root / "artifact-pass-pack"
seed_pack(artifact_pass_pack, continuity_required=True, reentry_required=False)
artifact_pass_path = artifact_pass_pack / "runtime" / "reports" / "context-continuity" / "continuity-rolling-pass.json"
write_json(
    artifact_pass_path,
    checkpoint_doc(
        continuity_id="cont-rolling-pass",
        artifact_kind="rolling_checkpoint",
    ),
)

artifact_override_pack = tmp_root / "artifact-override-pack"
clone_pack(artifact_pass_pack, artifact_override_pack)
artifact_override_path = artifact_override_pack / artifact_pass_path.relative_to(artifact_pass_pack)
override_doc = checkpoint_doc(
    continuity_id="cont-rolling-override",
    artifact_kind="rolling_checkpoint",
    authority_override=True,
)
write_json(artifact_override_path, override_doc)

artifact_stale_pack = tmp_root / "artifact-stale-pack"
clone_pack(artifact_pass_pack, artifact_stale_pack)
artifact_stale_path = artifact_stale_pack / artifact_pass_path.relative_to(artifact_pass_pack)
stale_doc = checkpoint_doc(
    continuity_id="cont-rolling-stale",
    artifact_kind="rolling_checkpoint",
    freshness_status="stale",
)
write_json(artifact_stale_path, stale_doc)

artifact_self_cycle_pack = tmp_root / "artifact-self-cycle-pack"
clone_pack(artifact_pass_pack, artifact_self_cycle_pack)
artifact_self_cycle_path = artifact_self_cycle_pack / artifact_pass_path.relative_to(artifact_pass_pack)
self_cycle_doc = checkpoint_doc(
    continuity_id="cont-rolling-self-cycle",
    artifact_kind="rolling_checkpoint",
    supersedes_ref="cont-rolling-self-cycle",
)
write_json(artifact_self_cycle_path, self_cycle_doc)

reentry_pass_pack = tmp_root / "reentry-pass-pack"
seed_pack(reentry_pass_pack, continuity_required=True, reentry_required=True)
reentry_checkpoint_path = reentry_pass_pack / "runtime" / "reports" / "context-continuity" / "continuity-stage-pass.json"
write_json(
    reentry_checkpoint_path,
    checkpoint_doc(
        continuity_id="cont-stage-pass",
        artifact_kind="stage_checkpoint",
        supersedes_ref="cont-rolling-pass",
    ),
)
reentry_brief_path = reentry_pass_pack / REENTRY_BRIEF_REL
write_json(
    reentry_brief_path,
    reentry_brief_doc(
        continuity_id="cont-reentry-pass",
        supersedes_ref="cont-stage-pass",
    ),
)
reentry_consumption_receipt_path = reentry_pass_pack / "runtime" / "reports" / "context-continuity" / "reentry-consumption-pass.json"
write_json(
    reentry_consumption_receipt_path,
    reentry_consumption_receipt_doc(
        pack_root=reentry_pass_pack,
        brief_path=reentry_brief_path,
        continuity_lineage_ref="cont-reentry-pass",
    ),
)

reentry_ready_no_proof_pack = tmp_root / "reentry-ready-no-proof-pack"
clone_pack(reentry_pass_pack, reentry_ready_no_proof_pack)
(reentry_ready_no_proof_pack / reentry_consumption_receipt_path.relative_to(reentry_pass_pack)).unlink()

reentry_brief_fail_pack = tmp_root / "reentry-brief-fail-pack"
clone_pack(reentry_pass_pack, reentry_brief_fail_pack)
reentry_brief_fail_path = reentry_brief_fail_pack / REENTRY_BRIEF_REL
write_json(
    reentry_brief_fail_path,
    reentry_brief_doc(
        continuity_id="cont-reentry-stale",
        supersedes_ref="cont-stage-pass",
        freshness_status="stale",
        authority_override=True,
    ),
)

reentry_missing_field_pack = tmp_root / "reentry-missing-field-pack"
clone_pack(reentry_pass_pack, reentry_missing_field_pack)
reentry_missing_field_receipt_path = reentry_missing_field_pack / reentry_consumption_receipt_path.relative_to(reentry_pass_pack)
missing_field_doc = reentry_consumption_receipt_doc(
    pack_root=reentry_missing_field_pack,
    brief_path=reentry_missing_field_pack / REENTRY_BRIEF_REL,
    continuity_lineage_ref="cont-reentry-pass",
)
missing_field_doc.pop("launcher_bind_status", None)
write_json(reentry_missing_field_receipt_path, missing_field_doc)

reentry_tuple_fail_pack = tmp_root / "reentry-tuple-fail-pack"
clone_pack(reentry_pass_pack, reentry_tuple_fail_pack)
reentry_tuple_fail_receipt_path = reentry_tuple_fail_pack / reentry_consumption_receipt_path.relative_to(reentry_pass_pack)
tuple_fail_doc = reentry_consumption_receipt_doc(
    pack_root=reentry_tuple_fail_pack,
    brief_path=reentry_tuple_fail_pack / REENTRY_BRIEF_REL,
    continuity_lineage_ref="cont-reentry-pass",
)
tuple_fail_doc["tuple_bootstrap_preserved"] = False
write_json(reentry_tuple_fail_receipt_path, tuple_fail_doc)

reentry_outcome_fail_pack = tmp_root / "reentry-outcome-fail-pack"
clone_pack(reentry_pass_pack, reentry_outcome_fail_pack)
reentry_outcome_fail_receipt_path = reentry_outcome_fail_pack / reentry_consumption_receipt_path.relative_to(reentry_pass_pack)
outcome_fail_doc = reentry_consumption_receipt_doc(
    pack_root=reentry_outcome_fail_pack,
    brief_path=reentry_outcome_fail_pack / REENTRY_BRIEF_REL,
    continuity_lineage_ref="cont-reentry-pass",
)
outcome_fail_doc["consumption_outcome"] = "raw_transcript_restored"
write_json(reentry_outcome_fail_receipt_path, outcome_fail_doc)

reentry_brief_location_pack = tmp_root / "reentry-brief-location-pack"
clone_pack(reentry_pass_pack, reentry_brief_location_pack)
reentry_brief_bad_location_path = (
    reentry_brief_location_pack
    / "runtime"
    / "reports"
    / "context-continuity"
    / "active-reentry-brief.json"
)
write_json(
    reentry_brief_bad_location_path,
    reentry_brief_doc(
        continuity_id="cont-reentry-bad-location",
        supersedes_ref="cont-stage-pass",
    ),
)

reentry_receipt_location_pack = tmp_root / "reentry-receipt-location-pack"
clone_pack(reentry_pass_pack, reentry_receipt_location_pack)
reentry_receipt_bad_location_path = (
    reentry_receipt_location_pack
    / "runtime"
    / "state"
    / "context-continuity"
    / "reentry-consumption-bad-location.json"
)
write_json(
    reentry_receipt_bad_location_path,
    reentry_consumption_receipt_doc(
        pack_root=reentry_receipt_location_pack,
        brief_path=reentry_receipt_location_pack / REENTRY_BRIEF_REL,
        continuity_lineage_ref="cont-reentry-pass",
    ),
)

receipt_pass_pack = tmp_root / "receipt-family-pass-pack"
seed_pack(receipt_pass_pack, continuity_required=True, reentry_required=True)
receipt_checkpoint_path = receipt_pass_pack / "runtime" / "reports" / "context-continuity" / "continuity-rolling-family.json"
receipt_migration_path = receipt_pass_pack / "runtime" / "reports" / "context-continuity" / "continuity-migration-family.json"
receipt_brief_path = receipt_pass_pack / REENTRY_BRIEF_REL
write_json(
    receipt_checkpoint_path,
    checkpoint_doc(
        continuity_id="cont-family-rolling",
        artifact_kind="rolling_checkpoint",
    ),
)
write_json(
    receipt_migration_path,
    checkpoint_doc(
        continuity_id="cont-family-migration",
        artifact_kind="migration_checkpoint",
        supersedes_ref="cont-family-rolling",
    ),
)
write_json(
    receipt_brief_path,
    reentry_brief_doc(
        continuity_id="cont-family-reentry",
        supersedes_ref="cont-family-migration",
    ),
)
checkpoint_receipt_path = receipt_pass_pack / "runtime" / "reports" / "context-continuity" / "checkpoint-receipt.json"
migration_receipt_path = receipt_pass_pack / "runtime" / "reports" / "context-continuity" / "migration-receipt.json"
brief_receipt_path = receipt_pass_pack / "runtime" / "reports" / "context-continuity" / "reentry-brief-receipt.json"
consumption_receipt_path = receipt_pass_pack / "runtime" / "reports" / "context-continuity" / "reentry-consumption-receipt.json"
write_json(
    checkpoint_receipt_path,
    checkpoint_receipt_doc(
        pack_root=receipt_pass_pack,
        artifact_path=receipt_checkpoint_path,
        artifact_kind="rolling_checkpoint",
        role="checkpoint",
    ),
)
write_json(
    migration_receipt_path,
    checkpoint_receipt_doc(
        pack_root=receipt_pass_pack,
        artifact_path=receipt_migration_path,
        artifact_kind="migration_checkpoint",
        role="migration_handoff",
    ),
)
write_json(
    brief_receipt_path,
    reentry_brief_receipt_doc(
        pack_root=receipt_pass_pack,
        brief_path=receipt_brief_path,
        continuity_lineage_ref="cont-family-migration",
    ),
)
write_json(
    consumption_receipt_path,
    reentry_consumption_receipt_doc(
        pack_root=receipt_pass_pack,
        brief_path=receipt_brief_path,
        continuity_lineage_ref="cont-family-reentry",
    ),
)

receipt_missing_member_pack = tmp_root / "receipt-family-missing-member-pack"
clone_pack(receipt_pass_pack, receipt_missing_member_pack)
(receipt_missing_member_pack / checkpoint_receipt_path.relative_to(receipt_pass_pack)).unlink()

receipt_unknown_kind_pack = tmp_root / "receipt-family-unknown-kind-pack"
clone_pack(receipt_pass_pack, receipt_unknown_kind_pack)
write_json(
    receipt_unknown_kind_pack / "runtime" / "reports" / "context-continuity" / "unknown-continuity-receipt.json",
    {
        "receipt_kind": "instance_continuity_shadow_receipt",
        "artifact_ref": "runtime/reports/context-continuity/continuity-rolling-family.json",
        "artifact_kind": "rolling_checkpoint",
    },
)

receipt_broken_join_pack = tmp_root / "receipt-family-broken-join-pack"
clone_pack(receipt_pass_pack, receipt_broken_join_pack)
broken_join_receipt_path = receipt_broken_join_pack / consumption_receipt_path.relative_to(receipt_pass_pack)
broken_join_doc = reentry_consumption_receipt_doc(
    pack_root=receipt_broken_join_pack,
    brief_path=receipt_broken_join_pack / REENTRY_BRIEF_REL,
    continuity_lineage_ref="cont-family-non-joinable",
)
write_json(broken_join_receipt_path, broken_join_doc)

exports = {
    "IDENTITY_ID": IDENTITY_ID,
    "DORMANT_TASK": dormant_pack / "CURRENT_TASK.json",
    "ARTIFACT_PASS_TASK": artifact_pass_pack / "CURRENT_TASK.json",
    "ARTIFACT_PASS_PATH": artifact_pass_path,
    "ARTIFACT_OVERRIDE_TASK": artifact_override_pack / "CURRENT_TASK.json",
    "ARTIFACT_OVERRIDE_PATH": artifact_override_path,
    "ARTIFACT_STALE_TASK": artifact_stale_pack / "CURRENT_TASK.json",
    "ARTIFACT_STALE_PATH": artifact_stale_path,
    "ARTIFACT_SELF_CYCLE_TASK": artifact_self_cycle_pack / "CURRENT_TASK.json",
    "ARTIFACT_SELF_CYCLE_PATH": artifact_self_cycle_path,
    "REENTRY_PASS_TASK": reentry_pass_pack / "CURRENT_TASK.json",
    "REENTRY_PASS_BRIEF": reentry_brief_path,
    "REENTRY_PASS_RECEIPT": reentry_consumption_receipt_path,
    "REENTRY_READY_NO_PROOF_TASK": reentry_ready_no_proof_pack / "CURRENT_TASK.json",
    "REENTRY_READY_NO_PROOF_BRIEF": reentry_ready_no_proof_pack / REENTRY_BRIEF_REL,
    "REENTRY_BRIEF_FAIL_TASK": reentry_brief_fail_pack / "CURRENT_TASK.json",
    "REENTRY_BRIEF_FAIL_PATH": reentry_brief_fail_path,
    "REENTRY_MISSING_FIELD_TASK": reentry_missing_field_pack / "CURRENT_TASK.json",
    "REENTRY_MISSING_FIELD_BRIEF": reentry_missing_field_pack / REENTRY_BRIEF_REL,
    "REENTRY_MISSING_FIELD_RECEIPT": reentry_missing_field_receipt_path,
    "REENTRY_TUPLE_FAIL_TASK": reentry_tuple_fail_pack / "CURRENT_TASK.json",
    "REENTRY_TUPLE_FAIL_BRIEF": reentry_tuple_fail_pack / REENTRY_BRIEF_REL,
    "REENTRY_TUPLE_FAIL_RECEIPT": reentry_tuple_fail_receipt_path,
    "REENTRY_OUTCOME_FAIL_TASK": reentry_outcome_fail_pack / "CURRENT_TASK.json",
    "REENTRY_OUTCOME_FAIL_BRIEF": reentry_outcome_fail_pack / REENTRY_BRIEF_REL,
    "REENTRY_OUTCOME_FAIL_RECEIPT": reentry_outcome_fail_receipt_path,
    "REENTRY_BRIEF_LOCATION_TASK": reentry_brief_location_pack / "CURRENT_TASK.json",
    "REENTRY_BRIEF_BAD_LOCATION_PATH": reentry_brief_bad_location_path,
    "REENTRY_RECEIPT_LOCATION_TASK": reentry_receipt_location_pack / "CURRENT_TASK.json",
    "REENTRY_RECEIPT_LOCATION_BRIEF": reentry_receipt_location_pack / REENTRY_BRIEF_REL,
    "REENTRY_RECEIPT_BAD_LOCATION_PATH": reentry_receipt_bad_location_path,
    "RECEIPT_PASS_TASK": receipt_pass_pack / "CURRENT_TASK.json",
    "RECEIPT_MISSING_MEMBER_TASK": receipt_missing_member_pack / "CURRENT_TASK.json",
    "RECEIPT_UNKNOWN_KIND_TASK": receipt_unknown_kind_pack / "CURRENT_TASK.json",
    "RECEIPT_BROKEN_JOIN_TASK": receipt_broken_join_pack / "CURRENT_TASK.json",
}

for key, value in exports.items():
    print(f"{key}={shlex.quote(str(value))}")
PY
)"

DORMANT_CONTINUITY_JSON="${TMP_ROOT}/dormant-continuity.json"
DORMANT_REENTRY_BRIEF_JSON="${TMP_ROOT}/dormant-reentry-brief.json"
DORMANT_REENTRY_CONSUMPTION_JSON="${TMP_ROOT}/dormant-reentry-consumption.json"
DORMANT_RECEIPTS_JSON="${TMP_ROOT}/dormant-receipts.json"
ARTIFACT_PASS_JSON="${TMP_ROOT}/artifact-pass.json"
ARTIFACT_OVERRIDE_JSON="${TMP_ROOT}/artifact-override.json"
ARTIFACT_STALE_JSON="${TMP_ROOT}/artifact-stale.json"
ARTIFACT_SELF_CYCLE_JSON="${TMP_ROOT}/artifact-self-cycle.json"
REENTRY_BRIEF_PASS_JSON="${TMP_ROOT}/reentry-brief-pass.json"
REENTRY_CONSUMPTION_PASS_JSON="${TMP_ROOT}/reentry-consumption-pass.json"
REENTRY_READY_NO_PROOF_ANSWER_JSON="${TMP_ROOT}/reentry-ready-no-proof-answer.json"
REENTRY_BRIEF_FAIL_JSON="${TMP_ROOT}/reentry-brief-fail.json"
REENTRY_MISSING_FIELD_JSON="${TMP_ROOT}/reentry-missing-field.json"
REENTRY_TUPLE_FAIL_JSON="${TMP_ROOT}/reentry-tuple-fail.json"
REENTRY_OUTCOME_FAIL_JSON="${TMP_ROOT}/reentry-outcome-fail.json"
REENTRY_BRIEF_LOCATION_JSON="${TMP_ROOT}/reentry-brief-location.json"
REENTRY_RECEIPT_LOCATION_JSON="${TMP_ROOT}/reentry-receipt-location.json"
RECEIPT_PASS_JSON="${TMP_ROOT}/receipt-family-pass.json"
RECEIPT_MISSING_MEMBER_JSON="${TMP_ROOT}/receipt-family-missing-member.json"
RECEIPT_UNKNOWN_KIND_JSON="${TMP_ROOT}/receipt-family-unknown-kind.json"
RECEIPT_BROKEN_JOIN_JSON="${TMP_ROOT}/receipt-family-broken-join.json"
DORMANT_BUNDLE_JSON="${TMP_ROOT}/dormant-bundle.json"
REENTRY_BUNDLE_PASS_JSON="${TMP_ROOT}/reentry-bundle-pass.json"
REENTRY_BUNDLE_FAIL_JSON="${TMP_ROOT}/reentry-bundle-fail.json"
DORMANT_REENTRY_ANSWER_JSON="${TMP_ROOT}/dormant-reentry-answer.json"
REENTRY_ANSWER_PASS_JSON="${TMP_ROOT}/reentry-answer-pass.json"
REENTRY_ANSWER_FAIL_JSON="${TMP_ROOT}/reentry-answer-fail.json"

run_cmd() {
  echo "[RUN] $*" >&2
  "$@"
}

run_cmd python3 "${ROOT}/scripts/validate_identity_context_continuity.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${DORMANT_TASK}" \
  --json-only > "${DORMANT_CONTINUITY_JSON}"

run_cmd python3 "${ROOT}/scripts/validate_identity_reentry_brief.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${DORMANT_TASK}" \
  --json-only > "${DORMANT_REENTRY_BRIEF_JSON}"

run_cmd python3 "${ROOT}/scripts/validate_identity_reentry_consumption.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${DORMANT_TASK}" \
  --json-only > "${DORMANT_REENTRY_CONSUMPTION_JSON}"

run_cmd python3 "${ROOT}/scripts/validate_identity_context_continuity_receipts.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${DORMANT_TASK}" \
  --json-only > "${DORMANT_RECEIPTS_JSON}"

run_cmd python3 "${ROOT}/scripts/render_identity_context_continuity_bundle.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${DORMANT_TASK}" \
  --json-only > "${DORMANT_BUNDLE_JSON}"

run_cmd python3 "${ROOT}/scripts/render_identity_context_reentry_answers.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${DORMANT_TASK}" \
  --json-only > "${DORMANT_REENTRY_ANSWER_JSON}"

run_cmd python3 "${ROOT}/scripts/validate_identity_context_continuity.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${ARTIFACT_PASS_TASK}" \
  --artifact "${ARTIFACT_PASS_PATH}" \
  --artifact-kind rolling_checkpoint \
  --json-only > "${ARTIFACT_PASS_JSON}"

if python3 "${ROOT}/scripts/validate_identity_context_continuity.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${ARTIFACT_OVERRIDE_TASK}" \
  --artifact "${ARTIFACT_OVERRIDE_PATH}" \
  --artifact-kind rolling_checkpoint \
  --json-only > "${ARTIFACT_OVERRIDE_JSON}"; then
  echo "[FAIL] continuity authority-override negative probe unexpectedly passed"
  exit 1
fi

if python3 "${ROOT}/scripts/validate_identity_context_continuity.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${ARTIFACT_STALE_TASK}" \
  --artifact "${ARTIFACT_STALE_PATH}" \
  --artifact-kind rolling_checkpoint \
  --json-only > "${ARTIFACT_STALE_JSON}"; then
  echo "[FAIL] continuity stale negative probe unexpectedly passed"
  exit 1
fi

if python3 "${ROOT}/scripts/validate_identity_context_continuity.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${ARTIFACT_SELF_CYCLE_TASK}" \
  --artifact "${ARTIFACT_SELF_CYCLE_PATH}" \
  --artifact-kind rolling_checkpoint \
  --json-only > "${ARTIFACT_SELF_CYCLE_JSON}"; then
  echo "[FAIL] continuity self-cycle negative probe unexpectedly passed"
  exit 1
fi

run_cmd python3 "${ROOT}/scripts/validate_identity_reentry_brief.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_PASS_TASK}" \
  --brief "${REENTRY_PASS_BRIEF}" \
  --json-only > "${REENTRY_BRIEF_PASS_JSON}"

run_cmd python3 "${ROOT}/scripts/validate_identity_reentry_consumption.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_PASS_TASK}" \
  --brief "${REENTRY_PASS_BRIEF}" \
  --receipt "${REENTRY_PASS_RECEIPT}" \
  --json-only > "${REENTRY_CONSUMPTION_PASS_JSON}"

run_cmd python3 "${ROOT}/scripts/render_identity_context_continuity_bundle.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_PASS_TASK}" \
  --brief "${REENTRY_PASS_BRIEF}" \
  --receipt "${REENTRY_PASS_RECEIPT}" \
  --json-only > "${REENTRY_BUNDLE_PASS_JSON}"

run_cmd python3 "${ROOT}/scripts/render_identity_context_reentry_answers.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_PASS_TASK}" \
  --brief "${REENTRY_PASS_BRIEF}" \
  --receipt "${REENTRY_PASS_RECEIPT}" \
  --json-only > "${REENTRY_ANSWER_PASS_JSON}"

run_cmd python3 "${ROOT}/scripts/render_identity_context_reentry_answers.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_READY_NO_PROOF_TASK}" \
  --brief "${REENTRY_READY_NO_PROOF_BRIEF}" \
  --json-only > "${REENTRY_READY_NO_PROOF_ANSWER_JSON}"

if python3 "${ROOT}/scripts/validate_identity_reentry_brief.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_BRIEF_FAIL_TASK}" \
  --brief "${REENTRY_BRIEF_FAIL_PATH}" \
  --json-only > "${REENTRY_BRIEF_FAIL_JSON}"; then
  echo "[FAIL] reentry brief negative probe unexpectedly passed"
  exit 1
fi

if python3 "${ROOT}/scripts/render_identity_context_continuity_bundle.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_BRIEF_FAIL_TASK}" \
  --brief "${REENTRY_BRIEF_FAIL_PATH}" \
  --json-only > "${REENTRY_BUNDLE_FAIL_JSON}"; then
  echo "[FAIL] continuity bundle negative probe unexpectedly passed"
  exit 1
fi

run_cmd python3 "${ROOT}/scripts/render_identity_context_reentry_answers.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_BRIEF_FAIL_TASK}" \
  --brief "${REENTRY_BRIEF_FAIL_PATH}" \
  --json-only > "${REENTRY_ANSWER_FAIL_JSON}"

if python3 "${ROOT}/scripts/validate_identity_reentry_consumption.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_MISSING_FIELD_TASK}" \
  --brief "${REENTRY_MISSING_FIELD_BRIEF}" \
  --receipt "${REENTRY_MISSING_FIELD_RECEIPT}" \
  --json-only > "${REENTRY_MISSING_FIELD_JSON}"; then
  echo "[FAIL] reentry consumption missing-field negative probe unexpectedly passed"
  exit 1
fi

if python3 "${ROOT}/scripts/validate_identity_reentry_consumption.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_TUPLE_FAIL_TASK}" \
  --brief "${REENTRY_TUPLE_FAIL_BRIEF}" \
  --receipt "${REENTRY_TUPLE_FAIL_RECEIPT}" \
  --json-only > "${REENTRY_TUPLE_FAIL_JSON}"; then
  echo "[FAIL] reentry consumption tuple-preservation negative probe unexpectedly passed"
  exit 1
fi

if python3 "${ROOT}/scripts/validate_identity_reentry_consumption.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_OUTCOME_FAIL_TASK}" \
  --brief "${REENTRY_OUTCOME_FAIL_BRIEF}" \
  --receipt "${REENTRY_OUTCOME_FAIL_RECEIPT}" \
  --json-only > "${REENTRY_OUTCOME_FAIL_JSON}"; then
  echo "[FAIL] reentry consumption outcome negative probe unexpectedly passed"
  exit 1
fi

if python3 "${ROOT}/scripts/validate_identity_reentry_brief.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_BRIEF_LOCATION_TASK}" \
  --brief "${REENTRY_BRIEF_BAD_LOCATION_PATH}" \
  --json-only > "${REENTRY_BRIEF_LOCATION_JSON}"; then
  echo "[FAIL] reentry brief location negative probe unexpectedly passed"
  exit 1
fi

if python3 "${ROOT}/scripts/validate_identity_reentry_consumption.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${REENTRY_RECEIPT_LOCATION_TASK}" \
  --brief "${REENTRY_RECEIPT_LOCATION_BRIEF}" \
  --receipt "${REENTRY_RECEIPT_BAD_LOCATION_PATH}" \
  --json-only > "${REENTRY_RECEIPT_LOCATION_JSON}"; then
  echo "[FAIL] reentry consumption receipt-location negative probe unexpectedly passed"
  exit 1
fi

run_cmd python3 "${ROOT}/scripts/validate_identity_context_continuity_receipts.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${RECEIPT_PASS_TASK}" \
  --require-observed \
  --json-only > "${RECEIPT_PASS_JSON}"

if python3 "${ROOT}/scripts/validate_identity_context_continuity_receipts.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${RECEIPT_MISSING_MEMBER_TASK}" \
  --require-observed \
  --json-only > "${RECEIPT_MISSING_MEMBER_JSON}"; then
  echo "[FAIL] continuity receipt-family missing-member probe unexpectedly passed"
  exit 1
fi

if python3 "${ROOT}/scripts/validate_identity_context_continuity_receipts.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${RECEIPT_UNKNOWN_KIND_TASK}" \
  --require-observed \
  --json-only > "${RECEIPT_UNKNOWN_KIND_JSON}"; then
  echo "[FAIL] continuity receipt-family unknown-kind probe unexpectedly passed"
  exit 1
fi

if python3 "${ROOT}/scripts/validate_identity_context_continuity_receipts.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${RECEIPT_BROKEN_JOIN_TASK}" \
  --require-observed \
  --json-only > "${RECEIPT_BROKEN_JOIN_JSON}"; then
  echo "[FAIL] continuity receipt-family broken-join probe unexpectedly passed"
  exit 1
fi

python3 - "${TMP_ROOT}" \
  "${DORMANT_CONTINUITY_JSON}" \
  "${DORMANT_REENTRY_BRIEF_JSON}" \
  "${DORMANT_REENTRY_CONSUMPTION_JSON}" \
  "${DORMANT_RECEIPTS_JSON}" \
  "${ARTIFACT_PASS_JSON}" \
  "${ARTIFACT_OVERRIDE_JSON}" \
  "${ARTIFACT_STALE_JSON}" \
  "${ARTIFACT_SELF_CYCLE_JSON}" \
  "${REENTRY_BRIEF_PASS_JSON}" \
  "${REENTRY_CONSUMPTION_PASS_JSON}" \
  "${REENTRY_READY_NO_PROOF_ANSWER_JSON}" \
  "${REENTRY_BRIEF_FAIL_JSON}" \
  "${REENTRY_MISSING_FIELD_JSON}" \
  "${REENTRY_TUPLE_FAIL_JSON}" \
  "${REENTRY_OUTCOME_FAIL_JSON}" \
  "${REENTRY_BRIEF_LOCATION_JSON}" \
  "${REENTRY_RECEIPT_LOCATION_JSON}" \
  "${RECEIPT_PASS_JSON}" \
  "${RECEIPT_MISSING_MEMBER_JSON}" \
  "${RECEIPT_UNKNOWN_KIND_JSON}" \
  "${RECEIPT_BROKEN_JOIN_JSON}" \
  "${DORMANT_BUNDLE_JSON}" \
  "${REENTRY_BUNDLE_PASS_JSON}" \
  "${REENTRY_BUNDLE_FAIL_JSON}" \
  "${DORMANT_REENTRY_ANSWER_JSON}" \
  "${REENTRY_ANSWER_PASS_JSON}" \
  "${REENTRY_ANSWER_FAIL_JSON}" <<'PY'
import json
import sys
from pathlib import Path

(
    tmp_root,
    dormant_continuity_path,
    dormant_reentry_brief_path,
    dormant_reentry_consumption_path,
    dormant_receipts_path,
    artifact_pass_path,
    artifact_override_path,
    artifact_stale_path,
    artifact_self_cycle_path,
    reentry_brief_pass_path,
    reentry_consumption_pass_path,
    reentry_ready_no_proof_answer_path,
    reentry_brief_fail_path,
    reentry_missing_field_path,
    reentry_tuple_fail_path,
    reentry_outcome_fail_path,
    reentry_brief_location_path,
    reentry_receipt_location_path,
    receipt_pass_path,
    receipt_missing_member_path,
    receipt_unknown_kind_path,
    receipt_broken_join_path,
    dormant_bundle_path,
    reentry_bundle_pass_path,
    reentry_bundle_fail_path,
    dormant_reentry_answer_path,
    reentry_answer_pass_path,
    reentry_answer_fail_path,
) = sys.argv[1:]

def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

dormant_continuity = load(dormant_continuity_path)
dormant_reentry_brief = load(dormant_reentry_brief_path)
dormant_reentry_consumption = load(dormant_reentry_consumption_path)
dormant_receipts = load(dormant_receipts_path)
artifact_pass = load(artifact_pass_path)
artifact_override = load(artifact_override_path)
artifact_stale = load(artifact_stale_path)
artifact_self_cycle = load(artifact_self_cycle_path)
reentry_brief_pass = load(reentry_brief_pass_path)
reentry_consumption_pass = load(reentry_consumption_pass_path)
reentry_ready_no_proof_answer = load(reentry_ready_no_proof_answer_path)
reentry_brief_fail = load(reentry_brief_fail_path)
reentry_missing_field = load(reentry_missing_field_path)
reentry_tuple_fail = load(reentry_tuple_fail_path)
reentry_outcome_fail = load(reentry_outcome_fail_path)
reentry_brief_location = load(reentry_brief_location_path)
reentry_receipt_location = load(reentry_receipt_location_path)
receipt_pass = load(receipt_pass_path)
receipt_missing_member = load(receipt_missing_member_path)
receipt_unknown_kind = load(receipt_unknown_kind_path)
receipt_broken_join = load(receipt_broken_join_path)
dormant_bundle = load(dormant_bundle_path)
reentry_bundle_pass = load(reentry_bundle_pass_path)
reentry_bundle_fail = load(reentry_bundle_fail_path)
dormant_reentry_answer = load(dormant_reentry_answer_path)
reentry_answer_pass = load(reentry_answer_pass_path)
reentry_answer_fail = load(reentry_answer_fail_path)

assert dormant_continuity["identity_context_continuity_status"] == "SKIPPED_NOT_REQUIRED", dormant_continuity
assert dormant_reentry_brief["identity_reentry_brief_status"] == "SKIPPED_NOT_REQUIRED", dormant_reentry_brief
assert dormant_reentry_consumption["identity_reentry_consumption_status"] == "SKIPPED_NOT_REQUIRED", dormant_reentry_consumption
assert dormant_receipts["identity_context_continuity_receipt_family_status"] == "SKIPPED_NOT_REQUIRED", dormant_receipts
assert dormant_bundle["identity_context_continuity_bundle_status"] == "SKIPPED_NOT_REQUIRED", dormant_bundle
assert dormant_bundle["operator_surface_contract"]["new_user_facing_continuity_command_family_forbidden"] is True, dormant_bundle
assert dormant_reentry_answer["identity_context_reentry_answer_bundle_status"] == "PASS_REQUIRED", dormant_reentry_answer
assert dormant_reentry_answer["overall_reentry_readiness_status"] == "SKIPPED_NOT_REQUIRED", dormant_reentry_answer
assert dormant_reentry_answer["recommended_reentry_answer_mode"] == "fresh_start_only_no_governed_reentry_contract", dormant_reentry_answer
assert dormant_reentry_answer["intent_answers"]["reload_after_clear"]["status"] == "SKIPPED_NOT_REQUIRED", dormant_reentry_answer
assert dormant_reentry_answer["operator_surface_contract"]["thread_uuid_injection_by_continuity_surface_forbidden"] is True, dormant_reentry_answer

assert artifact_pass["identity_context_continuity_status"] == "PASS_REQUIRED", artifact_pass
assert artifact_override["identity_context_continuity_status"] == "FAIL_REQUIRED", artifact_override
assert "authority_override_attempt" in artifact_override.get("stale_reasons", []), artifact_override
assert artifact_stale["identity_context_continuity_status"] == "FAIL_REQUIRED", artifact_stale
assert "freshness_indicates_stale" in artifact_stale.get("stale_reasons", []), artifact_stale
assert artifact_self_cycle["identity_context_continuity_status"] == "FAIL_REQUIRED", artifact_self_cycle
assert "supersedes_ref_self_cycle" in artifact_self_cycle.get("stale_reasons", []), artifact_self_cycle

assert reentry_brief_pass["identity_reentry_brief_status"] == "PASS_REQUIRED", reentry_brief_pass
assert reentry_consumption_pass["identity_reentry_consumption_status"] == "PASS_REQUIRED", reentry_consumption_pass
assert reentry_bundle_pass["identity_context_continuity_bundle_status"] == "PASS_REQUIRED", reentry_bundle_pass
assert reentry_bundle_pass["startup_reentry_readiness_status"] == "PASS_REQUIRED", reentry_bundle_pass
assert reentry_bundle_pass["live_reentry_consumption_proof_status"] == "PASS_REQUIRED", reentry_bundle_pass
assert reentry_bundle_pass["recommended_launcher_bind_mode"] == "consume_governed_reentry_brief", reentry_bundle_pass
assert reentry_answer_pass["identity_context_reentry_answer_bundle_status"] == "PASS_REQUIRED", reentry_answer_pass
assert reentry_answer_pass["overall_reentry_readiness_status"] == "PASS_REQUIRED", reentry_answer_pass
assert reentry_answer_pass["live_reentry_consumption_proof_status"] == "PASS_REQUIRED", reentry_answer_pass
assert reentry_answer_pass["recommended_reentry_answer_mode"] == "governed_reentry_ready_with_live_proof", reentry_answer_pass
assert reentry_answer_pass["intent_answers"]["migrate_new_window"]["status"] == "PASS_REQUIRED", reentry_answer_pass
assert reentry_answer_pass["intent_answers"]["reload_after_clear"]["status"] == "PASS_REQUIRED", reentry_answer_pass
assert reentry_answer_pass["intent_answers"]["reload_after_clear"]["copyable_reentry_task_block"], reentry_answer_pass
assert "governed_identity_context_reentry" in reentry_answer_pass["intent_answers"]["reload_after_clear"]["copyable_reentry_task_block"], reentry_answer_pass
assert reentry_ready_no_proof_answer["identity_context_reentry_answer_bundle_status"] == "PASS_REQUIRED", reentry_ready_no_proof_answer
assert reentry_ready_no_proof_answer["overall_reentry_readiness_status"] == "PASS_REQUIRED", reentry_ready_no_proof_answer
assert reentry_ready_no_proof_answer["live_reentry_consumption_proof_status"] == "FAIL_REQUIRED", reentry_ready_no_proof_answer
assert reentry_ready_no_proof_answer["recommended_reentry_answer_mode"] == "governed_reentry_ready_pending_first_live_proof", reentry_ready_no_proof_answer
assert reentry_ready_no_proof_answer["intent_answers"]["reload_after_clear"]["status"] == "PASS_REQUIRED", reentry_ready_no_proof_answer
assert reentry_ready_no_proof_answer["intent_answers"]["reload_after_clear"]["post_reentry_evidence_required"] is True, reentry_ready_no_proof_answer
assert reentry_brief_fail["identity_reentry_brief_status"] == "FAIL_REQUIRED", reentry_brief_fail
assert reentry_bundle_fail["identity_context_continuity_bundle_status"] == "FAIL_REQUIRED", reentry_bundle_fail
assert reentry_bundle_fail["startup_reentry_readiness_status"] == "FAIL_REQUIRED", reentry_bundle_fail
assert reentry_bundle_fail["recommended_launcher_bind_mode"] == "fresh_start_without_governed_reentry_claim", reentry_bundle_fail
assert reentry_answer_fail["identity_context_reentry_answer_bundle_status"] == "PASS_REQUIRED", reentry_answer_fail
assert reentry_answer_fail["overall_reentry_readiness_status"] == "FAIL_REQUIRED", reentry_answer_fail
assert reentry_answer_fail["recommended_reentry_answer_mode"] == "governed_reentry_blocked_until_readiness_repaired", reentry_answer_fail
assert reentry_answer_fail["intent_answers"]["reload_after_clear"]["status"] == "FAIL_REQUIRED", reentry_answer_fail
assert any(
    token in reentry_brief_fail.get("stale_reasons", [])
    for token in ("freshness_indicates_stale", "authority_override_attempt")
), reentry_brief_fail
assert reentry_missing_field["identity_reentry_consumption_status"] == "FAIL_REQUIRED", reentry_missing_field
assert "missing_required_receipt_field:launcher_bind_status" in reentry_missing_field.get("stale_reasons", []), reentry_missing_field
assert reentry_tuple_fail["identity_reentry_consumption_status"] == "FAIL_REQUIRED", reentry_tuple_fail
assert "tuple_bootstrap_not_preserved" in reentry_tuple_fail.get("stale_reasons", []), reentry_tuple_fail
assert reentry_outcome_fail["identity_reentry_consumption_status"] == "FAIL_REQUIRED", reentry_outcome_fail
assert "consumption_outcome_non_governed" in reentry_outcome_fail.get("stale_reasons", []), reentry_outcome_fail
assert reentry_brief_location["identity_reentry_brief_status"] == "FAIL_REQUIRED", reentry_brief_location
assert "reentry_brief_not_under_state_runtime_family" in reentry_brief_location.get("stale_reasons", []), reentry_brief_location
assert reentry_receipt_location["identity_reentry_consumption_status"] == "FAIL_REQUIRED", reentry_receipt_location
assert "report_under_state_surface" in reentry_receipt_location.get("stale_reasons", []), reentry_receipt_location

assert receipt_pass["identity_context_continuity_receipt_family_status"] == "PASS_REQUIRED", receipt_pass
assert receipt_pass["receipt_join_status"] == "PASS_REQUIRED", receipt_pass
assert receipt_missing_member["identity_context_continuity_receipt_family_status"] == "FAIL_REQUIRED", receipt_missing_member
assert receipt_missing_member["error_code"] == "IP-ICREC-001", receipt_missing_member
assert receipt_unknown_kind["identity_context_continuity_receipt_family_status"] == "FAIL_REQUIRED", receipt_unknown_kind
assert receipt_unknown_kind["error_code"] == "IP-ICREC-004", receipt_unknown_kind
assert receipt_broken_join["identity_context_continuity_receipt_family_status"] == "FAIL_REQUIRED", receipt_broken_join
assert receipt_broken_join["error_code"] == "IP-ICREC-003", receipt_broken_join

print(
    json.dumps(
        {
            "identity_context_continuity_probe_status": "PASS_REQUIRED",
            "dormant_contract_status": "SKIPPED_NOT_REQUIRED",
            "rq_044_positive_status": artifact_pass["identity_context_continuity_status"],
            "rq_044_negative_failures": [
                "authority_override_attempt",
                "freshness_indicates_stale",
                "supersedes_ref_self_cycle",
            ],
            "rq_045_positive_status": reentry_consumption_pass["identity_reentry_consumption_status"],
            "rq_045_negative_failures": [
                "brief_stale_or_override",
                "missing_required_receipt_field:launcher_bind_status",
                "tuple_bootstrap_not_preserved",
                "consumption_outcome_non_governed",
                "reentry_brief_not_under_state_runtime_family",
                "report_under_state_surface",
            ],
            "rq_046_positive_status": receipt_pass["identity_context_continuity_receipt_family_status"],
            "rq_046_negative_failures": [
                "missing_receipt_role",
                "unknown_continuity_receipt_kind",
                "reentry_consumption_lineage_not_joinable",
            ],
            "continuity_bundle_surface_status": reentry_bundle_pass["identity_context_continuity_bundle_status"],
            "reentry_answer_surface_status": reentry_answer_pass["identity_context_reentry_answer_bundle_status"],
            "tmp_root": tmp_root,
        },
        ensure_ascii=False,
    )
)
PY
