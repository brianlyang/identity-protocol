#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from capability_fit_roundtable_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    clean_string,
    derive_roundtable_evidence_payload,
)
from strict_live_evidence_resolution_common import resolve_active_execution_context


def _doc_references_path(node: Any, target_path: Path) -> bool:
    target = target_path.expanduser().resolve().as_posix()
    if isinstance(node, dict):
        return any(_doc_references_path(value, target_path) for value in node.values())
    if isinstance(node, list):
        return any(_doc_references_path(item, target_path) for item in node)
    token = clean_string(node)
    if not token:
        return False
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        try:
            return candidate.resolve().as_posix() == target
        except Exception:
            return False
    return token == target


def _path_linked_to_active_run(target_ref: str, *, active_context: dict[str, Any]) -> bool:
    token = clean_string(target_ref)
    if not token:
        return False
    target_path = Path(token).expanduser().resolve()
    active_report_path = clean_string(active_context.get("report_path"))
    if active_report_path:
        try:
            if target_path == Path(active_report_path).expanduser().resolve():
                return True
        except Exception:
            pass
    active_report_doc = active_context.get("report_doc") if isinstance(active_context.get("report_doc"), dict) else {}
    return _doc_references_path(active_report_doc, target_path)


def derive_route_live_bridge_projection(
    *,
    pack_root: Path,
    task_doc: dict[str, Any],
    identity_id: str,
    operation: str = "",
) -> dict[str, Any]:
    roundtable_payload = derive_roundtable_evidence_payload(
        pack_root=pack_root,
        task_doc=task_doc,
        identity_id=identity_id,
        operation=operation,
    )
    active_context = resolve_active_execution_context(pack_root)
    current_run_id = clean_string(active_context.get("run_id"))
    selected_candidate_id = clean_string(roundtable_payload.get("selected_candidate_id"))
    selection_basis = clean_string(roundtable_payload.get("selection_basis"))
    selected_candidate_receipt_ref = clean_string(roundtable_payload.get("selected_candidate_receipt_ref"))
    roundtable_receipt_ref = clean_string(roundtable_payload.get("roundtable_receipt_ref"))
    roundtable_required = bool(roundtable_payload.get("roundtable_required"))
    capability_fit_roundtable_status = clean_string(roundtable_payload.get("capability_fit_roundtable_status")).upper()

    stale_reasons: list[str] = []
    if capability_fit_roundtable_status == STATUS_FAIL_REQUIRED:
        stale_reasons.extend(
            f"roundtable:{clean_string(reason)}"
            for reason in (roundtable_payload.get("stale_reasons") or [])
            if clean_string(reason)
        )
    elif capability_fit_roundtable_status == STATUS_SKIPPED_NOT_REQUIRED:
        stale_reasons.append("roundtable_contract_not_required")

    if not current_run_id:
        stale_reasons.append("current_run_id_missing")
    if not selected_candidate_id:
        stale_reasons.append("selected_candidate_id_missing")
    if not selection_basis:
        stale_reasons.append("selection_basis_missing")
    if not selected_candidate_receipt_ref:
        stale_reasons.append("selected_candidate_receipt_ref_missing")
    elif not _path_linked_to_active_run(selected_candidate_receipt_ref, active_context=active_context):
        stale_reasons.append("selected_candidate_receipt_not_linked_to_active_run")

    if roundtable_required:
        if not roundtable_receipt_ref:
            stale_reasons.append("roundtable_receipt_ref_missing")
        elif not _path_linked_to_active_run(roundtable_receipt_ref, active_context=active_context):
            stale_reasons.append("roundtable_receipt_not_linked_to_active_run")

    route_live_binding_status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    return {
        "selected_candidate_id": selected_candidate_id,
        "selection_basis": selection_basis,
        "selected_candidate_receipt_ref": selected_candidate_receipt_ref,
        "roundtable_receipt_ref": roundtable_receipt_ref,
        "route_live_binding_status": route_live_binding_status,
        "route_live_binding_reasons": sorted(set(stale_reasons)),
        "roundtable_required": roundtable_required,
        "capability_fit_roundtable_status": capability_fit_roundtable_status or STATUS_SKIPPED_NOT_REQUIRED,
        "route_current_run_id": current_run_id,
        "route_current_run_pointer": clean_string(active_context.get("pointer_path")),
        "route_current_run_report_path": clean_string(active_context.get("report_path")),
    }
