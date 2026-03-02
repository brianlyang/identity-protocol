#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actor_session_common import load_actor_binding, resolve_actor_id
from protocol_feedback_contract_common import (
    canonical_dirs,
    ensure_index_linkage,
    is_strict_operation,
    rel_to_feedback_root,
    resolve_feedback_root,
    utc_now_z,
    write_json,
)
from response_stamp_common import DEFAULT_WORK_LAYER, resolve_layer_intent
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

ERR_LANE_GATESET_MISMATCH = "IP-LAYER-GATE-001"
ERR_INSTANCE_BLOCKED_BY_PROTOCOL_PUBLISH = "IP-LAYER-GATE-002"
ERR_PROTOCOL_PUBLISH_MISSING = "IP-LAYER-GATE-003"
ERR_PROTOCOL_FEEDBACK_CLOSURE_MISSING = "IP-LAYER-GATE-004"
ERR_DUAL_STRICT = "IP-LAYER-GATE-005"
ERR_PROTOCOL_CONTEXT_FALLBACK = "IP-LAYER-GATE-006"
ERR_PROTOCOL_CONTEXT_CONFIRMATION_MISSING = "IP-LAYER-GATE-007"

DEFAULT_PROTOCOL_PUBLISH_CHECKS = [
    "scripts/validate_changelog_updated.py",
    "scripts/validate_protocol_handoff_coupling.py",
    "scripts/validate_release_metadata_sync.py",
    "scripts/validate_release_freeze_boundary.py",
]

SIGNIFICANT_PREFIXES = (
    "identity/",
    "scripts/",
    "skills/",
    ".github/workflows/",
    "docs/references/",
)
SIGNIFICANT_FILES = {
    "README.md",
    "CHANGELOG.md",
}
EXEMPT_PREFIXES = (
    "docs/governance/",
)

PROTOCOL_ROOT = Path(__file__).resolve().parent.parent
LOCK_PROTOCOL_PREFIX = "SESSION_LANE_LOCK_PROTOCOL_"
LOCK_EXIT_PREFIX = "SESSION_LANE_LOCK_EXIT_"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "work_layer_gate_set_split_contract_v1",
        "work_layer_gate_set_split_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _run_git(args: list[str]) -> str:
    cp = subprocess.run(["git", *args], cwd=str(PROTOCOL_ROOT), capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return (cp.stdout or "").strip()


def _resolve_range(base: str, head: str) -> tuple[str, str]:
    resolved_head = str(head or "").strip() or _run_git(["rev-parse", "HEAD"])
    resolved_base = str(base or "").strip() or _run_git(["rev-parse", "HEAD~1"])
    return resolved_base, resolved_head


def _changed_files(base: str, head: str) -> list[str]:
    out = _run_git(["diff", "--name-only", f"{base}..{head}"])
    return [x.strip() for x in out.splitlines() if x.strip()]


def _is_protocol_publish_relevant(path: str) -> bool:
    if path in SIGNIFICANT_FILES:
        return path != "CHANGELOG.md"
    if any(path.startswith(p) for p in EXEMPT_PREFIXES):
        return False
    return any(path.startswith(p) for p in SIGNIFICANT_PREFIXES)


def _normalize_applied_gate_set(token: str) -> str:
    t = str(token or "").strip().lower()
    if t in {"instance", "instance_required_checks"}:
        return "instance_required_checks"
    if t in {"protocol", "protocol_required_checks"}:
        return "protocol_required_checks"
    if t in {"dual", "dual_unroutable"}:
        return "dual_unroutable"
    return ""


def _safe_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _latest_lane_lock_receipt(
    *,
    outbox_dir: Path,
    prefix: str,
    identity_id: str,
) -> Path | None:
    if not outbox_dir.exists():
        return None
    rows = sorted(outbox_dir.glob(f"{prefix}*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in rows:
        doc = _safe_json(p)
        rid = str(doc.get("identity_id", "")).strip()
        if rid and rid != identity_id:
            continue
        return p.resolve()
    return None


def _resolve_session_lane_lock(
    *,
    catalog_path: Path,
    identity_id: str,
    actor_id: str,
    feedback_root: Path,
) -> tuple[str, str, str]:
    binding = load_actor_binding(catalog_path, actor_id, identity_id=identity_id)
    for key in ("session_lane_lock", "lane_lock", "work_layer_lock"):
        token = str(binding.get(key, "")).strip().lower()
        if token in {"protocol", "instance", "dual"}:
            return token, "actor_binding", str(binding.get("actor_session_path", "")).strip()

    outbox_dir = (feedback_root / "outbox-to-protocol").resolve()
    lock_protocol = _latest_lane_lock_receipt(outbox_dir=outbox_dir, prefix=LOCK_PROTOCOL_PREFIX, identity_id=identity_id)
    lock_exit = _latest_lane_lock_receipt(outbox_dir=outbox_dir, prefix=LOCK_EXIT_PREFIX, identity_id=identity_id)
    if lock_protocol is None:
        return "", "", ""

    protocol_mtime = lock_protocol.stat().st_mtime
    exit_mtime = lock_exit.stat().st_mtime if lock_exit is not None else -1.0
    if exit_mtime > protocol_mtime:
        return "", "", ""
    return "protocol", "receipt", str(lock_protocol)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_pending_receipt(
    *,
    identity_id: str,
    feedback_root: Path,
    applied_gate_set: str,
    source_layer: str,
    lane_transition_reason: str,
    base: str,
    head: str,
    protocol_relevant_files: list[str],
) -> tuple[str, list[str]]:
    d = canonical_dirs(feedback_root)
    outbox = d["outbox_dir"]
    index_path = d["index_path"]
    outbox.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    ts = utc_now_z().replace("-", "").replace(":", "")
    receipt_path = (outbox / f"LAYER_GATE_PROTOCOL_PENDING_{ts}.json").resolve()
    payload = {
        "event": "instance_lane_protocol_publish_pending",
        "identity_id": identity_id,
        "work_layer": "instance",
        "source_layer": source_layer,
        "applied_gate_set": applied_gate_set,
        "protocol_feedback_triggered": True,
        "lane_transition_reason": lane_transition_reason,
        "next_action": "protocol_feedback_required",
        "git_range": {"base": base, "head": head},
        "protocol_relevant_files": protocol_relevant_files,
        "generated_at": utc_now_z(),
    }
    write_json(receipt_path, payload)
    receipt_ref = rel_to_feedback_root(receipt_path, feedback_root)
    ensure_index_linkage(index_path, [receipt_ref], section_title="Lane gate routing pending protocol feedback")
    return str(receipt_path), [receipt_ref]


def _write_lane_lock_protocol_receipt(
    *,
    identity_id: str,
    actor_id: str,
    feedback_root: Path,
    source_layer: str,
    lane_transition_reason: str,
    protocol_context_reasons: list[str],
) -> tuple[str, list[str]]:
    d = canonical_dirs(feedback_root)
    outbox = d["outbox_dir"]
    index_path = d["index_path"]
    outbox.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    ts = utc_now_z().replace("-", "").replace(":", "")
    receipt_path = (outbox / f"{LOCK_PROTOCOL_PREFIX}{ts}.json").resolve()
    payload = {
        "event": "session_lane_lock_protocol_acquired",
        "identity_id": identity_id,
        "actor_id": actor_id,
        "session_lane_lock": "protocol",
        "source_layer": source_layer,
        "lane_transition_reason": lane_transition_reason,
        "protocol_context_reasons": protocol_context_reasons,
        "generated_at": _now_iso(),
    }
    write_json(receipt_path, payload)
    receipt_ref = rel_to_feedback_root(receipt_path, feedback_root)
    ensure_index_linkage(index_path, [receipt_ref], section_title="Lane lock receipts")
    return str(receipt_path), [receipt_ref]


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate work-layer gate-set routing contract (FIX-033).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--feedback-root", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-lane-lock-receipt", default="")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    ap.add_argument("--applied-gate-set", default="")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    strict = is_strict_operation(args.operation)
    required_contract = bool(args.force_check or contract_required(contract) or strict)

    intent = resolve_layer_intent(
        explicit_work_layer=str(args.expected_work_layer or "").strip(),
        explicit_source_layer=str(args.source_layer or "").strip(),
        intent_text=str(args.layer_intent_text or "").strip(),
        default_work_layer=DEFAULT_WORK_LAYER,
        default_source_layer="global",
    )

    work_layer = str(intent.get("resolved_work_layer", DEFAULT_WORK_LAYER)).strip().lower() or DEFAULT_WORK_LAYER
    source_layer = str(intent.get("resolved_source_layer", "global")).strip().lower() or "global"
    intent_source = str(intent.get("intent_source", "")).strip() or "default_fallback"
    fallback_reason = str(intent.get("fallback_reason", "")).strip()
    protocol_triggered = bool(intent.get("protocol_triggered", False))
    protocol_trigger_reasons = list(intent.get("protocol_trigger_reasons") or [])
    intent_confidence = float(intent.get("intent_confidence", 0.0) or 0.0)

    applied_gate_set = (
        "instance_required_checks"
        if work_layer == "instance"
        else "protocol_required_checks"
        if work_layer == "protocol"
        else "dual_unroutable"
    )
    requested_applied_gate_set = _normalize_applied_gate_set(args.applied_gate_set)

    lane_transition_reason = (
        "explicit_work_layer_override"
        if intent_source == "explicit_arg"
        else fallback_reason
        if fallback_reason
        else "protocol_trigger_detected"
        if protocol_triggered
        else "instance_default_fallback"
    )

    base, head = "", ""
    changed_files: list[str] = []
    protocol_relevant_files: list[str] = []
    git_error = ""
    try:
        base, head = _resolve_range(str(args.base or "").strip(), str(args.head or "").strip())
        changed_files = _changed_files(base, head)
        protocol_relevant_files = [x for x in changed_files if _is_protocol_publish_relevant(x)]
    except Exception as exc:
        git_error = str(exc)

    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    d = canonical_dirs(feedback_root)
    missing_protocol_feedback_dirs: list[str] = []
    for p in (d["outbox_dir"], d["index_path"].parent, d["upgrade_dir"]):
        if not p.exists():
            missing_protocol_feedback_dirs.append(str(p))

    protocol_feedback_triggered = bool(work_layer == "protocol")
    protocol_feedback_paths: list[str] = []
    pending_receipt_path = ""
    lane_lock_receipt_path = ""

    stale_reasons: list[str] = []
    error_code = ""

    actor_id = resolve_actor_id(args.actor_id)
    session_lane_lock, session_lane_lock_source, session_lane_lock_receipt = _resolve_session_lane_lock(
        catalog_path=catalog_path,
        identity_id=args.identity_id,
        actor_id=actor_id,
        feedback_root=feedback_root,
    )
    if str(args.session_lane_lock_receipt or "").strip():
        receipt_path = Path(str(args.session_lane_lock_receipt).strip()).expanduser().resolve()
        if receipt_path.exists():
            doc = _safe_json(receipt_path)
            if str(doc.get("session_lane_lock", "")).strip().lower() == "protocol":
                session_lane_lock = "protocol"
                session_lane_lock_source = "explicit_receipt"
                session_lane_lock_receipt = str(receipt_path)
    protocol_context_reasons: list[str] = []
    explicit_work_layer = str(args.expected_work_layer or "").strip().lower()
    explicit_protocol = explicit_work_layer == "protocol"
    if explicit_protocol:
        protocol_context_reasons.append("explicit_work_layer_protocol")
    if session_lane_lock == "protocol":
        protocol_context_reasons.append("session_lane_lock_protocol")
    if protocol_triggered and intent_confidence >= 0.75:
        protocol_context_reasons.append("protocol_classifier_high_confidence")
    protocol_context_detected = bool(protocol_context_reasons)

    lane_resolution_decision = (
        "PROTOCOL_SELECTED"
        if work_layer == "protocol"
        else "DUAL_UNROUTABLE"
        if work_layer == "dual"
        else "INSTANCE_DEFAULT"
    )
    lane_resolution_blocked = False
    lane_resolution_error_code = ""

    if not required_contract:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "required_contract": False,
            "strict_operation": strict,
            "work_layer_gate_set_routing_status": STATUS_SKIPPED_NOT_REQUIRED,
            "work_layer": work_layer,
            "source_layer": source_layer,
            "applied_gate_set": applied_gate_set,
            "protocol_context_detected": protocol_context_detected,
            "session_lane_lock": session_lane_lock,
            "session_lane_lock_source": session_lane_lock_source,
            "session_lane_lock_receipt": session_lane_lock_receipt,
            "lane_resolution_decision": lane_resolution_decision,
            "lane_resolution_blocked": lane_resolution_blocked,
            "lane_resolution_error_code": lane_resolution_error_code,
            "protocol_feedback_triggered": protocol_feedback_triggered,
            "protocol_feedback_paths": protocol_feedback_paths,
            "lane_transition_reason": lane_transition_reason,
            "stale_reasons": ["contract_not_required"],
        }
        _emit(payload, json_only=args.json_only)
        return 0

    if strict and work_layer == "dual":
        stale_reasons.append("strict_operation_dual_lane_not_allowed")
        error_code = ERR_DUAL_STRICT

    if protocol_context_detected and work_layer != "protocol" and not error_code:
        lane_resolution_decision = "INSTANCE_FALLBACK_BLOCKED"
        lane_resolution_blocked = True
        if intent_source == "default_fallback":
            stale_reasons.append("protocol_context_detected_with_default_fallback")
            error_code = ERR_PROTOCOL_CONTEXT_FALLBACK
        else:
            stale_reasons.append("protocol_context_requires_explicit_confirmation")
            error_code = ERR_PROTOCOL_CONTEXT_CONFIRMATION_MISSING

    if requested_applied_gate_set and requested_applied_gate_set != applied_gate_set and not error_code:
        stale_reasons.append("applied_gate_set_mismatch")
        error_code = (
            ERR_INSTANCE_BLOCKED_BY_PROTOCOL_PUBLISH
            if work_layer == "instance" and requested_applied_gate_set == "protocol_required_checks"
            else ERR_LANE_GATESET_MISMATCH
        )

    if git_error and strict and not error_code:
        stale_reasons.append("git_range_resolution_failed")
        error_code = ERR_PROTOCOL_PUBLISH_MISSING

    if work_layer == "instance" and protocol_relevant_files and not git_error:
        try:
            pending_receipt_path, protocol_feedback_paths = _make_pending_receipt(
                identity_id=args.identity_id,
                feedback_root=feedback_root,
                applied_gate_set=applied_gate_set,
                source_layer=source_layer,
                lane_transition_reason=lane_transition_reason,
                base=base,
                head=head,
                protocol_relevant_files=protocol_relevant_files,
            )
            protocol_feedback_triggered = True
            missing_protocol_feedback_dirs = []
            for p in (d["outbox_dir"], d["index_path"].parent, d["upgrade_dir"]):
                if not p.exists():
                    missing_protocol_feedback_dirs.append(str(p))
        except Exception as exc:
            if strict and not error_code:
                stale_reasons.append("instance_lane_pending_receipt_write_failed")
                stale_reasons.append(str(exc))
                error_code = ERR_INSTANCE_BLOCKED_BY_PROTOCOL_PUBLISH

    if work_layer == "protocol":
        protocol_feedback_triggered = True
        protocol_feedback_paths = [
            "outbox-to-protocol/",
            "evidence-index/INDEX.md",
            "upgrade-proposals/",
        ]
        lane_resolution_decision = "PROTOCOL_SELECTED"
        if strict and not session_lane_lock:
            try:
                lane_lock_receipt_path, lane_lock_refs = _write_lane_lock_protocol_receipt(
                    identity_id=args.identity_id,
                    actor_id=actor_id,
                    feedback_root=feedback_root,
                    source_layer=source_layer,
                    lane_transition_reason=lane_transition_reason,
                    protocol_context_reasons=protocol_context_reasons or ["protocol_lane_selected"],
                )
                protocol_feedback_paths.extend(lane_lock_refs)
                session_lane_lock = "protocol"
                session_lane_lock_source = "receipt"
                session_lane_lock_receipt = lane_lock_receipt_path
            except Exception as exc:
                if not error_code:
                    lane_resolution_decision = "PROTOCOL_LOCK_RECEIPT_MISSING"
                    stale_reasons.append("protocol_lane_lock_receipt_write_failed")
                    stale_reasons.append(str(exc))
                    error_code = ERR_PROTOCOL_CONTEXT_CONFIRMATION_MISSING
        if missing_protocol_feedback_dirs and strict and not error_code:
            stale_reasons.append("protocol_feedback_canonical_roots_missing")
            error_code = ERR_PROTOCOL_FEEDBACK_CLOSURE_MISSING

    if error_code:
        lane_resolution_error_code = error_code

    if error_code and strict:
        status = STATUS_FAIL_REQUIRED
        rc = 1
    elif error_code:
        status = STATUS_WARN_NON_BLOCKING
        rc = 0
    else:
        status = STATUS_PASS_REQUIRED
        rc = 0

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "strict_operation": strict,
        "work_layer_gate_set_routing_status": status,
        "error_code": error_code,
        "work_layer": work_layer,
        "source_layer": source_layer,
        "intent_source": intent_source,
        "intent_confidence": intent_confidence,
        "protocol_triggered": protocol_triggered,
        "protocol_trigger_reasons": protocol_trigger_reasons,
        "protocol_context_detected": protocol_context_detected,
        "protocol_context_reasons": protocol_context_reasons,
        "session_lane_lock": session_lane_lock,
        "session_lane_lock_source": session_lane_lock_source,
        "session_lane_lock_receipt": session_lane_lock_receipt,
        "lane_resolution_decision": lane_resolution_decision,
        "lane_resolution_blocked": lane_resolution_blocked,
        "lane_resolution_error_code": lane_resolution_error_code,
        "lane_transition_reason": lane_transition_reason,
        "applied_gate_set": applied_gate_set,
        "requested_applied_gate_set": requested_applied_gate_set,
        "protocol_publish_checks": list(DEFAULT_PROTOCOL_PUBLISH_CHECKS),
        "protocol_relevant_diff_detected": bool(protocol_relevant_files),
        "protocol_relevant_files": protocol_relevant_files,
        "git_range_base": base,
        "git_range_head": head,
        "git_error": git_error,
        "protocol_feedback_triggered": protocol_feedback_triggered,
        "protocol_feedback_paths": protocol_feedback_paths,
        "pending_receipt_path": pending_receipt_path,
        "lane_lock_receipt_path": lane_lock_receipt_path,
        "missing_protocol_feedback_dirs": missing_protocol_feedback_dirs,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
