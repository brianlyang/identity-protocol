#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from governed_answer_bridge_admission_common import (
    build_governed_answer_bridge_admission_contract,
)
from governed_runtime_summary_surface_common import build_governed_runtime_summary_surface_payload
from identity_context_continuity_common import (
    REENTRY_ANSWER_BUNDLE_CONTRACT_ID,
    REENTRY_ANSWER_INTENTS,
    REENTRY_ANSWER_QUESTION_FAMILY,
    REENTRY_REQUIRED_OUTCOME,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    build_reentry_task_block,
    clean_string,
)
from render_identity_context_continuity_bundle import render_continuity_bundle_payload


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _intent_names(raw_intent: str) -> tuple[str, ...]:
    token = clean_string(raw_intent)
    if not token:
        return REENTRY_ANSWER_INTENTS
    if token not in REENTRY_ANSWER_INTENTS:
        raise ValueError(
            f"unsupported intent {token!r}; expected one of: {', '.join(REENTRY_ANSWER_INTENTS)}"
        )
    return (token,)


def _bridge_admission_contract() -> dict[str, Any]:
    return build_governed_answer_bridge_admission_contract(
        consumer_stream="v1.6.14",
        owner_stream="v1.6.16",
        question_family=REENTRY_ANSWER_QUESTION_FAMILY,
    )


def _answer_mode(
    *,
    startup_status: str,
    live_proof_status: str,
    continuity_required: bool,
    reentry_required: bool,
) -> str:
    if startup_status == STATUS_PASS_REQUIRED:
        if live_proof_status == STATUS_PASS_REQUIRED:
            return "governed_reentry_ready_with_live_proof"
        return "governed_reentry_ready_pending_first_live_proof"
    if (
        startup_status == STATUS_SKIPPED_NOT_REQUIRED
        and not continuity_required
        and not reentry_required
    ):
        return "fresh_start_only_no_governed_reentry_contract"
    return "governed_reentry_blocked_until_readiness_repaired"


def _intent_status(
    *,
    startup_status: str,
    continuity_required: bool,
    reentry_required: bool,
) -> str:
    if startup_status == STATUS_PASS_REQUIRED:
        return STATUS_PASS_REQUIRED
    if (
        startup_status == STATUS_SKIPPED_NOT_REQUIRED
        and not continuity_required
        and not reentry_required
    ):
        return STATUS_SKIPPED_NOT_REQUIRED
    return STATUS_FAIL_REQUIRED


def _intent_reason(
    *,
    status: str,
    answer_mode: str,
) -> str:
    if status == STATUS_PASS_REQUIRED:
        return answer_mode
    if status == STATUS_SKIPPED_NOT_REQUIRED:
        return "governed_reentry_contract_not_required"
    return "startup_reentry_readiness_not_pass"


def _intent_operator_steps(
    *,
    intent: str,
    status: str,
) -> list[dict[str, Any]]:
    if status == STATUS_PASS_REQUIRED:
        return [
            {
                "step": 1,
                "action": "resolve_launcher_entry",
                "owner_stream": "v1.6.14",
                "note": "continuity surface does not assemble start/resume commands",
            },
            {
                "step": 2,
                "action": "open_new_window" if intent == "migrate_new_window" else "clear_current_session",
                "owner_stream": "operator_or_host",
            },
            {
                "step": 3,
                "action": "submit_governed_reentry_task_block",
                "owner_stream": "v1.6.16",
            },
            {
                "step": 4,
                "action": "verify_runtime_receipt",
                "required_receipt_kind": REENTRY_REQUIRED_OUTCOME,
            },
        ]
    if status == STATUS_SKIPPED_NOT_REQUIRED:
        return [
            {
                "step": 1,
                "action": "fresh_start_only",
                "owner_stream": "v1.6.14",
            }
        ]
    return [
        {
            "step": 1,
            "action": "block_reentry_claim",
            "owner_stream": "v1.6.16",
        },
        {
            "step": 2,
            "action": "repair_startup_reentry_readiness_before_clear_or_migration",
            "owner_stream": "v1.6.16",
        },
    ]


def _merged_stale_reasons(bundle_payload: dict[str, Any]) -> list[str]:
    rows = bundle_payload.get("validator_stale_reasons")
    if not isinstance(rows, dict):
        return []
    merged: list[str] = []
    for key in ("reentry_brief", "reentry_consumption", "continuity_artifact", "receipt_family"):
        value = rows.get(key)
        if isinstance(value, list):
            for token in value:
                text = clean_string(token)
                if text and text not in merged:
                    merged.append(text)
    return merged


def render_reentry_answers_payload(
    *,
    identity_id: str,
    catalog: str = "",
    current_task: str = "",
    brief: str = "",
    receipt: str = "",
    intent: str = "",
) -> dict[str, Any]:
    continuity_bundle = render_continuity_bundle_payload(
        identity_id=identity_id,
        catalog=catalog,
        current_task=current_task,
        brief=brief,
        receipt=receipt,
    )
    if not isinstance(continuity_bundle, dict):
        return {
            "status": STATUS_FAIL_REQUIRED,
            "identity_context_reentry_answer_bundle_status": STATUS_FAIL_REQUIRED,
            "answer_bundle_contract_id": REENTRY_ANSWER_BUNDLE_CONTRACT_ID,
            "question_family": REENTRY_ANSWER_QUESTION_FAMILY,
            "identity_id": identity_id,
            "error": "continuity_bundle_root_not_object",
        }

    continuity_bundle_status = clean_string(
        continuity_bundle.get("identity_context_continuity_bundle_status")
    ) or clean_string(continuity_bundle.get("status"))
    if clean_string(continuity_bundle.get("error")) and not clean_string(
        continuity_bundle.get("resolved_pack_path")
    ):
        return {
            "status": STATUS_FAIL_REQUIRED,
            "identity_context_reentry_answer_bundle_status": STATUS_FAIL_REQUIRED,
            "answer_bundle_contract_id": REENTRY_ANSWER_BUNDLE_CONTRACT_ID,
            "question_family": REENTRY_ANSWER_QUESTION_FAMILY,
            "continuity_owner_stream": "v1.6.16",
            "bridge_admission_contract": _bridge_admission_contract(),
            "identity_id": identity_id,
            "continuity_bundle_status": continuity_bundle_status or STATUS_FAIL_REQUIRED,
            "error": clean_string(continuity_bundle.get("error")),
            "continuity_support": continuity_bundle,
        }
    startup_status = clean_string(continuity_bundle.get("startup_reentry_readiness_status"))
    live_proof_status = clean_string(continuity_bundle.get("live_reentry_consumption_proof_status"))
    continuity_required = bool(continuity_bundle.get("continuity_contract_required"))
    reentry_required = bool(continuity_bundle.get("reentry_contract_required"))
    answer_mode = _answer_mode(
        startup_status=startup_status,
        live_proof_status=live_proof_status,
        continuity_required=continuity_required,
        reentry_required=reentry_required,
    )
    current_reentry_brief_ref = clean_string(continuity_bundle.get("current_reentry_brief_ref"))
    continuity_lineage_ref = clean_string(continuity_bundle.get("continuity_lineage_ref"))
    task_path = Path(
        clean_string(continuity_bundle.get("task_path")) or clean_string(current_task) or "."
    ).expanduser().resolve()
    selected_intents = _intent_names(intent)
    shared_stale_reasons = _merged_stale_reasons(continuity_bundle)

    intent_answers: dict[str, Any] = {}
    for name in selected_intents:
        status = _intent_status(
            startup_status=startup_status,
            continuity_required=continuity_required,
            reentry_required=reentry_required,
        )
        task_block = (
            build_reentry_task_block(
                identity_id=identity_id,
                intent=name,
                task_path=task_path,
                reentry_brief_ref=current_reentry_brief_ref,
                continuity_lineage_ref=continuity_lineage_ref,
                startup_reentry_readiness_status=startup_status,
                live_reentry_consumption_proof_status=live_proof_status,
            )
            if status == STATUS_PASS_REQUIRED
            else {}
        )
        intent_answers[name] = {
            "intent": name,
            "status": status,
            "safe_to_trigger_now": status == STATUS_PASS_REQUIRED,
            "recommended_reentry_answer_mode": answer_mode,
            "reason": _intent_reason(status=status, answer_mode=answer_mode),
            "post_reentry_evidence_required": status == STATUS_PASS_REQUIRED,
            "required_receipt_kind": REENTRY_REQUIRED_OUTCOME,
            "reentry_brief_ref": current_reentry_brief_ref,
            "continuity_lineage_ref": continuity_lineage_ref,
            "operator_steps": _intent_operator_steps(intent=name, status=status),
            "stale_reasons": shared_stale_reasons,
            "reentry_task_block": task_block,
            "copyable_reentry_task_block": (
                json.dumps(task_block, ensure_ascii=False, indent=2) if task_block else ""
            ),
        }

    return {
        "status": STATUS_PASS_REQUIRED,
        "identity_context_reentry_answer_bundle_status": STATUS_PASS_REQUIRED,
        "answer_bundle_contract_id": REENTRY_ANSWER_BUNDLE_CONTRACT_ID,
        "question_family": REENTRY_ANSWER_QUESTION_FAMILY,
        "bridge_admission_contract": _bridge_admission_contract(),
        "identity_id": identity_id,
        "requested_intent": clean_string(intent),
        "catalog_path": clean_string(continuity_bundle.get("catalog_path")),
        "pack_path": clean_string(continuity_bundle.get("resolved_pack_path")),
        "task_path": str(task_path),
        "continuity_bundle_status": continuity_bundle_status,
        "overall_reentry_readiness_status": startup_status,
        "live_reentry_consumption_proof_status": live_proof_status,
        "continuity_contract_required": continuity_required,
        "reentry_contract_required": reentry_required,
        "recommended_reentry_answer_mode": answer_mode,
        "current_reentry_brief_ref": current_reentry_brief_ref,
        "continuity_lineage_ref": continuity_lineage_ref,
        "continuity_support_ref": "scripts/render_identity_context_continuity_bundle.py",
        "launcher_entry_owner_stream": "v1.6.14",
        "continuity_owner_stream": "v1.6.16",
        "surface_governance": build_governed_runtime_summary_surface_payload(
            "identity_context_reentry_answer_surface"
        ),
        "operator_surface_contract": {
            "identity_instance_visible_answer_surface": True,
            "new_terminal_command_family_created": False,
            "launcher_command_lookup_delegated_to_v1_6_14": True,
            "bridge_admission_contract_emitted": True,
            "bridge_integrity_not_equal_owner_answer_status": True,
            "owner_answer_status_not_equal_operator_projection": True,
            "manual_reentry_task_assembly_forbidden": True,
            "thread_uuid_injection_by_continuity_surface_forbidden": True,
            "raw_transcript_authority_forbidden": True,
        },
        "instance_answer_guidance": {
            "instance_returns_concrete_reentry_task": True,
            "instance_must_state_reentry_readiness_explicitly": True,
            "instance_must_state_live_proof_status_explicitly": True,
            "instance_must_not_claim_memory_restore_without_governed_reentry_receipt": True,
        },
        "intent_answers": intent_answers,
        "continuity_support": continuity_bundle,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Render protocol-owned reentry recovery answers for identity-visible migration / clear-recovery questions."
    )
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--receipt", default="")
    ap.add_argument("--intent", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        payload = render_reentry_answers_payload(
            identity_id=args.identity_id,
            catalog=args.catalog,
            current_task=args.current_task,
            brief=args.brief,
            receipt=args.receipt,
            intent=args.intent,
        )
    except Exception as exc:
        payload = {
            "status": STATUS_FAIL_REQUIRED,
            "identity_context_reentry_answer_bundle_status": STATUS_FAIL_REQUIRED,
            "answer_bundle_contract_id": REENTRY_ANSWER_BUNDLE_CONTRACT_ID,
            "question_family": REENTRY_ANSWER_QUESTION_FAMILY,
            "continuity_owner_stream": "v1.6.16",
            "bridge_admission_contract": _bridge_admission_contract(),
            "identity_id": args.identity_id,
            "error": str(exc),
        }
        _emit(payload, json_only=args.json_only)
        return 1

    _emit(payload, json_only=args.json_only)
    return 0 if clean_string(payload.get("status")) == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
