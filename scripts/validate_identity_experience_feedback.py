#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strict_live_evidence_resolution_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    apply_strict_live_required_gate,
    canonicalize_strict_live_contract_paths,
    derive_strict_live_evidence_projection,
    derive_strict_live_operational_projection,
    emit_payload,
    resolve_preferred_strict_live_report,
    resolve_strict_live_contract_path,
    resolve_strict_live_glob_paths,
    resolve_strict_live_pack_task,
)

REQ_KEYS = [
    "required",
    "positive_rulebook_path",
    "negative_rulebook_path",
    "required_fields",
    "cross_layer_feedback_targets",
    "promote_requires_replay_pass",
    "sample_report_path_pattern",
]
STATUS_FIELD = "experience_feedback_status"
ERR_TASK = "IP-EXPFB-001"
ERR_REPORT = "IP-EXPFB-002"


def _protocol_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(catalog_path: Path, identity_id: str) -> Path:
    _, task_path = resolve_strict_live_pack_task(catalog_path, identity_id)
    return task_path


def _validate_rulebook(path: Path, req_fields: list[str], label: str) -> int:
    if not path.exists():
        print(f"[FAIL] {label} not found: {path}")
        return 1
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        print(f"[FAIL] {label} empty: {path}")
        return 1
    rc = 0
    for i, ln in enumerate(lines, start=1):
        try:
            row = json.loads(ln)
        except Exception as e:
            print(f"[FAIL] {label} line {i} invalid json: {e}")
            rc = 1
            continue
        missing = [k for k in req_fields if k not in row]
        if missing:
            print(f"[FAIL] {label} line {i} missing fields: {missing}")
            rc = 1
    if rc == 0:
        print(f"[OK] {label} validated: {path}")
    return rc


def _resolve_contract_path(raw: str, *, pack_root: Path, protocol_root: Path) -> Path:
    del protocol_root
    return resolve_strict_live_contract_path(
        raw,
        pack_root=pack_root,
        identity_id=pack_root.name,
    )


def _glob_paths(pattern: str, *, pack_root: Path, protocol_root: Path) -> list[Path]:
    del protocol_root
    return resolve_strict_live_glob_paths(
        pattern,
        pack_root=pack_root,
        identity_id=pack_root.name,
    )


def _build_payload(
    *,
    identity_id: str,
    task_path: Path | None,
    pack_root: Path | None,
    contract_doc: dict[str, Any] | None,
    report_path: Path | None,
    report_doc: dict[str, Any] | None,
    selection_meta: dict[str, Any] | None,
    status: str,
    stale_reasons: list[str],
    error_code: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "identity_id": identity_id,
        "task_path": str(task_path) if task_path is not None else "",
        STATUS_FIELD: status,
        "error_code": error_code,
    }
    if pack_root is not None:
        if isinstance(selection_meta, dict):
            payload.update(
                {
                    "report_selection_mode": str(selection_meta.get("report_selection_mode", "")).strip() or "missing",
                    "live_candidate_paths": list(selection_meta.get("live_candidate_paths") or []),
                    "live_candidate_selected_path": str(selection_meta.get("live_candidate_selected_path", "")).strip(),
                }
            )
        evidence_projection = derive_strict_live_evidence_projection(
            pack_root=pack_root,
            contract_doc=contract_doc if isinstance(contract_doc, dict) else {},
            selected_report_path=report_path,
            report_doc=report_doc if isinstance(report_doc, dict) else {},
        )
        payload.update(evidence_projection)
        payload.update(
            derive_strict_live_operational_projection(
                semantic_status=status,
                evidence_projection=payload,
            )
        )
    else:
        payload.update(
            {
                "selected_report_path": str(report_path) if report_path is not None else "",
                "current_run_pointer": "",
                "current_run_report_path": "",
                "current_run_id": "",
                "report_selection_mode": "missing",
                "live_candidate_paths": [],
                "live_candidate_selected_path": "",
                "evidence_origin": "missing",
                "report_freshness_status": STATUS_FAIL_REQUIRED,
                "run_id_binding_status": STATUS_FAIL_REQUIRED,
                "strict_live_proof_status": STATUS_FAIL_REQUIRED,
                "selected_report_run_ids": [],
                "selected_report_age_seconds": None,
            }
        )
        payload.update(
            derive_strict_live_operational_projection(
                semantic_status=status,
                evidence_projection=payload,
            )
        )
    payload["stale_reasons"] = sorted(
        set([str(item).strip() for item in stale_reasons if str(item).strip()] + list(payload.pop("stale_reasons", [])))
    )
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate experience feedback contract")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=None,
            pack_root=None,
            contract_doc=None,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=[str(e)],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate experience feedback for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")
    pack_root = task_path.parent.resolve()
    protocol_root = _protocol_root().resolve()

    task = _load_json(task_path)
    c = task.get("experience_feedback_contract") or {}
    if isinstance(c, dict):
        c = canonicalize_strict_live_contract_paths(
            c,
            pack_root=pack_root,
            identity_id=args.identity_id,
        )
    if not isinstance(c, dict) or not c:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc={},
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["missing_experience_feedback_contract"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] missing experience_feedback_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=[f"experience_feedback_contract_missing_fields:{','.join(missing)}"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] experience_feedback_contract missing fields: {missing}")
        return 1

    if c.get("required") is not True:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["experience_feedback_contract_not_required"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] experience_feedback_contract.required must be true")
        return 1

    req_fields = c.get("required_fields") or []
    rc = 0
    positive_path = _resolve_contract_path(
        str(c.get("positive_rulebook_path", "")),
        pack_root=pack_root,
        protocol_root=protocol_root,
    )
    negative_path = _resolve_contract_path(
        str(c.get("negative_rulebook_path", "")),
        pack_root=pack_root,
        protocol_root=protocol_root,
    )
    rc |= _validate_rulebook(positive_path, req_fields, "positive_rulebook")
    rc |= _validate_rulebook(negative_path, req_fields, "negative_rulebook")

    targets = set(c.get("cross_layer_feedback_targets") or [])
    need = {"routing_contract", "capability_orchestration_contract", "gates"}
    if not need.issubset(targets):
        print(f"[FAIL] cross_layer_feedback_targets missing: {sorted(need-targets)}")
        rc = 1

    replay_gate = c.get("promote_requires_replay_pass")
    if replay_gate is None:
        replay_gate = c.get("promotion_requires_replay_pass")
    if replay_gate is not True:
        print("[FAIL] replay-pass promotion gate must be true (promote_requires_replay_pass or promotion_requires_replay_pass)")
        rc = 1

    report_path = (
        Path(args.report).expanduser().resolve()
        if args.report
        else (pack_root / "runtime" / "examples" / f"{args.identity_id}-experience-feedback-sample.json").resolve()
    )
    if not report_path.exists():
        files = _glob_paths(
            str(c.get("sample_report_path_pattern", "")),
            pack_root=pack_root,
            protocol_root=protocol_root,
        )
        if files:
            report_path = files[-1]
    selection_meta = resolve_preferred_strict_live_report(
        pack_root=pack_root,
        contract_doc=c,
        fallback_report_path=report_path,
        explicit_report_path=Path(args.report).expanduser().resolve() if args.report else None,
    )
    selected_report_path = selection_meta.get("selected_report_path")
    if isinstance(selected_report_path, Path):
        report_path = selected_report_path
    if not report_path.exists():
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=report_path,
            report_doc=None,
            selection_meta=selection_meta,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["experience_feedback_report_missing"],
            error_code=ERR_REPORT,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] missing experience feedback sample report: {report_path}")
        return 1

    report = _load_json(report_path)
    all_updates = (report.get("positive_updates") or []) + (report.get("negative_updates") or [])
    if not all_updates:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=report_path,
            report_doc=report,
            selection_meta=selection_meta,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["experience_feedback_updates_missing"],
            error_code=ERR_REPORT,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] sample report requires positive_updates or negative_updates")
        return 1

    for i, u in enumerate(all_updates):
        if not isinstance(u, dict):
            print(f"[FAIL] update[{i}] must be object")
            rc = 1
            continue
        missing_u = [k for k in req_fields if k not in u]
        if missing_u:
            print(f"[FAIL] update[{i}] missing fields: {missing_u}")
            rc = 1
        if u.get("replay_status") != "PASS":
            print(f"[FAIL] update[{i}].replay_status must be PASS")
            rc = 1

    if rc:
        return 1

    if args.self_test:
        pos = sorted((protocol_root / "identity/runtime/examples/experience/positive").glob("*.json"))
        neg = sorted((protocol_root / "identity/runtime/examples/experience/negative").glob("*.json"))
        if len(pos) < 2 or len(neg) < 1:
            print("[FAIL] experience self-test requires >=2 positive and >=1 negative samples")
            return 1
        # positives should pass required fields + replay PASS
        for p in pos:
            r = _load_json(p)
            updates = (r.get("positive_updates") or []) + (r.get("negative_updates") or [])
            if not updates:
                print(f"[FAIL] positive sample missing updates: {p}")
                return 1
            for i, u in enumerate(updates):
                miss = [k for k in req_fields if k not in u]
                if miss:
                    print(f"[FAIL] positive sample missing fields {miss}: {p}#{i}")
                    return 1
                if u.get("replay_status") != "PASS":
                    print(f"[FAIL] positive sample replay_status must be PASS: {p}#{i}")
                    return 1
        # negatives should contain at least one non-PASS replay
        for p in neg:
            r = _load_json(p)
            updates = (r.get("positive_updates") or []) + (r.get("negative_updates") or [])
            if not updates:
                print(f"[FAIL] negative sample missing updates: {p}")
                return 1
            if not any(u.get("replay_status") != "PASS" for u in updates if isinstance(u, dict)):
                print(f"[FAIL] negative sample did not include replay_status!=PASS: {p}")
                return 1
        print("[OK] experience self-test passed")

    status = STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    payload = _build_payload(
        identity_id=args.identity_id,
        task_path=task_path,
        pack_root=pack_root,
        contract_doc=c,
        report_path=report_path,
        report_doc=report,
        selection_meta=selection_meta,
        status=status,
        stale_reasons=[] if rc == 0 else ["experience_feedback_contract_validation_failed"],
        error_code="" if rc == 0 else ERR_TASK,
    )
    payload = apply_strict_live_required_gate(
        payload,
        contract_doc=c,
        status_field=STATUS_FIELD,
        strict_live_error_code=ERR_REPORT,
    )
    if rc:
        if args.json_only:
            emit_payload(payload, json_only=True)
        return 1

    if str(payload.get(STATUS_FIELD, "")).strip().upper() != STATUS_PASS_REQUIRED:
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] strict-live current-run evidence required but unproven for experience feedback")
        return 1

    if args.json_only:
        emit_payload(payload, json_only=True)
        return 0

    print(
        "[INFO] strict-live projection: "
        f"evidence_origin={payload['evidence_origin']} "
        f"report_freshness_status={payload['report_freshness_status']} "
        f"run_id_binding_status={payload['run_id_binding_status']} "
        f"strict_live_proof_status={payload['strict_live_proof_status']}"
    )
    print("Experience feedback contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
