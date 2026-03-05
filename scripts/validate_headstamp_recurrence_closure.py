#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import load_actor_binding

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

ERR_STATIC_WIRING = "IP-ASB-STAMP-SCAN-001"
ERR_MISSING_HEADER_NEGATIVE = "IP-ASB-STAMP-SCAN-002"
ERR_INLINE_NEGATIVE = "IP-ASB-STAMP-SCAN-003"
ERR_COMPOSE_POSITIVE = "IP-ASB-STAMP-SCAN-004"
ERR_OUTLET_NEGATIVE = "IP-ASB-STAMP-SCAN-005"
ERR_COVERAGE_EQUIV = "IP-ASB-STAMP-SCAN-006"
ERR_ACTOR_MISMATCH_NEGATIVE = "IP-ASB-STAMP-SCAN-007"

ERR_ACTOR_REQUIRED = "IP-ASB-ACTOR-001"
ERR_MIXED_EVIDENCE_UNPARTITIONED = "IP-ASB-ACTOR-002"

ERR_SEND_TIME_GATE = "IP-ASB-STAMP-SESSION-001"
ERR_SYNTHETIC_EVIDENCE = "IP-ASB-STAMP-SESSION-002"
ERR_NON_GOVERNED_OUTLET = "IP-ASB-STAMP-SESSION-004"
ERR_ACTOR_BOUND_MISMATCH = "IP-ASB-STAMP-SESSION-005"

STRICT_ACTOR_REQUIRED_OPS = {
    "activate",
    "update",
    "mutation",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "scan",
    "three-plane",
}

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

MANDATORY_ENTRYPOINTS = [
    "scripts/identity_creator.py",
    "scripts/release_readiness_check.py",
    "scripts/full_identity_protocol_scan.py",
    "scripts/report_three_plane_status.py",
    "scripts/execute_identity_upgrade.py",
    "scripts/e2e_smoke_test.sh",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), {})
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _parse_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        doc = json.loads(text)
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _run_json(cmd: list[str]) -> tuple[int, dict[str, Any], str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    payload = _parse_payload(proc.stdout)
    if not payload and proc.stderr:
        payload = {"stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-5:])}
    return proc.returncode, payload, proc.stdout, proc.stderr


def _static_wiring_scan() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    coverage_rows: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for rel in MANDATORY_ENTRYPOINTS:
        p = (REPO_ROOT / rel).resolve()
        if not p.exists():
            row = {
                "path": rel,
                "entrypoint_exists": False,
                "has_compose_wrapper": False,
                "has_direct_send_time": False,
                "coverage_mode": "missing_entrypoint",
                "coverage_normalized": False,
            }
            coverage_rows.append(row)
            missing.append({"path": rel, "missing": "entrypoint_file"})
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        has_compose = "scripts/compose_and_validate_governed_reply.py" in text
        has_send_time = "scripts/validate_send_time_reply_gate.py" in text
        if has_compose and has_send_time:
            mode = "compose_plus_direct"
        elif has_compose:
            mode = "compose_wrapper_only"
        elif has_send_time:
            mode = "direct_send_time_only"
        else:
            mode = "none"
        normalized = bool(has_compose or has_send_time)
        coverage_rows.append(
            {
                "path": rel,
                "entrypoint_exists": True,
                "has_compose_wrapper": has_compose,
                "has_direct_send_time": has_send_time,
                "coverage_mode": mode,
                "coverage_normalized": normalized,
            }
        )
        if not normalized:
            missing.append({"path": rel, "missing": "compose_or_send_time_reference"})
    return coverage_rows, missing


def _send_time_cmd(
    *,
    identity_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    actor_id: str,
    outlet_channel_id: str,
    blocker_receipt: Path,
    reply_file: Path | None = None,
    reply_text: str = "",
) -> list[str]:
    cmd = [
        sys.executable,
        str((SCRIPT_DIR / "validate_send_time_reply_gate.py").resolve()),
        "--identity-id",
        identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--force-check",
        "--enforce-send-time-gate",
        "--reply-outlet-guard-applied",
        "--outlet-channel-id",
        outlet_channel_id,
        "--operation",
        "send-time",
        "--blocker-receipt-out",
        str(blocker_receipt),
        "--actor-id",
        actor_id,
        "--json-only",
    ]
    if reply_file is not None:
        cmd += ["--reply-file", str(reply_file)]
    if reply_text:
        cmd += ["--reply-text", reply_text]
    return cmd


def _catalog_identity_ids(catalog_path: Path) -> list[str]:
    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return []
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    out: list[str] = []
    for row in rows:
        iid = str(row.get("id", "")).strip()
        if iid:
            out.append(iid)
    return out


def _actor_mismatch_probe(
    *,
    identity_id: str,
    actor_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    reply_file: Path,
    blocker_receipt: Path,
) -> tuple[bool, dict[str, Any], list[str]]:
    stale_reasons: list[str] = []
    actor_binding = load_actor_binding(catalog_path, actor_id)
    actor_bound_identity = str(actor_binding.get("identity_id", "")).strip()
    if not actor_bound_identity:
        stale_reasons.append("actor_mismatch_probe_skipped_no_binding")
        return (
            True,
            {
                "rc": 0,
                "status": "SKIPPED_NO_ACTOR_BINDING",
                "probe_actor_id": actor_id,
                "actor_bound_identity_id": "",
                "mismatch_identity_id": "",
            },
            stale_reasons,
        )

    mismatch_identity = ""
    for iid in _catalog_identity_ids(catalog_path):
        if iid != actor_bound_identity:
            mismatch_identity = iid
            break
    if not mismatch_identity:
        stale_reasons.append("actor_mismatch_probe_skipped_single_identity_catalog")
        return (
            True,
            {
                "rc": 0,
                "status": "SKIPPED_SINGLE_IDENTITY_CATALOG",
                "probe_actor_id": actor_id,
                "actor_bound_identity_id": actor_bound_identity,
                "mismatch_identity_id": "",
            },
            stale_reasons,
        )

    cmd = [
        sys.executable,
        str((SCRIPT_DIR / "compose_and_validate_governed_reply.py").resolve()),
        "--identity-id",
        mismatch_identity,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--body-text",
        "headstamp actor mismatch probe",
        "--out-reply-file",
        str(reply_file),
        "--blocker-receipt-out",
        str(blocker_receipt),
        "--outlet-channel-id",
        "governed_adapter_v1",
        "--actor-id",
        actor_id,
        "--json-only",
    ]
    rc, payload, _, _ = _run_json(cmd)
    case = {
        "rc": rc,
        "error_code": str(payload.get("error_code", "")),
        "send_time_gate_status": str(payload.get("send_time_gate_status", "")),
        "resolved_actor_id": str(payload.get("resolved_actor_id", "")),
        "actor_bound_identity_id": str(payload.get("actor_bound_identity_id", "")),
        "probe_actor_id": actor_id,
        "mismatch_identity_id": mismatch_identity,
        "target_identity_id": identity_id,
    }
    ok = rc != 0 and case["error_code"] == ERR_ACTOR_BOUND_MISMATCH
    if not ok:
        stale_reasons.append("actor_mismatch_negative_not_fail_closed")
    return ok, case, stale_reasons


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Hard-close headstamp recurrence for v1.5.x by combining static outlet wiring checks "
            "with dynamic send-time fail-closed replay cases."
        )
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "mutation", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    operation = str(args.operation or "").strip().lower()
    actor_id = str(args.actor_id or "").strip()
    actor_required = operation in STRICT_ACTOR_REQUIRED_OPS

    if not catalog_path.exists():
        _emit(
            {
                "identity_id": args.identity_id,
                "catalog_path": str(catalog_path),
                "repo_catalog_path": str(repo_catalog_path),
                "headstamp_recurrence_closure_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_STATIC_WIRING,
                "stale_reasons": [f"catalog_not_found:{catalog_path}"],
            },
            json_only=args.json_only,
        )
        return 1
    if not repo_catalog_path.exists():
        _emit(
            {
                "identity_id": args.identity_id,
                "catalog_path": str(catalog_path),
                "repo_catalog_path": str(repo_catalog_path),
                "headstamp_recurrence_closure_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_STATIC_WIRING,
                "stale_reasons": [f"repo_catalog_not_found:{repo_catalog_path}"],
            },
            json_only=args.json_only,
        )
        return 1

    if _is_fixture_identity(catalog_path, args.identity_id):
        _emit(
            {
                "identity_id": args.identity_id,
                "catalog_path": str(catalog_path),
                "repo_catalog_path": str(repo_catalog_path),
                "operation": args.operation,
                "required_contract": False,
                "headstamp_recurrence_closure_status": STATUS_SKIPPED_NOT_REQUIRED,
                "error_code": "",
                "stale_reasons": ["fixture_profile_scope"],
            },
            json_only=args.json_only,
        )
        return 0

    if actor_required and not actor_id:
        _emit(
            {
                "identity_id": args.identity_id,
                "catalog_path": str(catalog_path),
                "repo_catalog_path": str(repo_catalog_path),
                "operation": operation,
                "required_contract": True,
                "actor_id": actor_id,
                "actor_explicit_required": True,
                "actor_explicit": False,
                "headstamp_recurrence_closure_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_ACTOR_REQUIRED,
                "stale_reasons": ["strict_actor_id_required", "actor_semantic_role_missing_or_ambiguous"],
                "next_action": "rerun_with_explicit_actor_id",
            },
            json_only=args.json_only,
        )
        return 1

    coverage_rows, missing_wiring = _static_wiring_scan()
    stale_reasons: list[str] = []
    dynamic_cases: dict[str, dict[str, Any]] = {}
    error_code = ""

    if missing_wiring:
        stale_reasons.append("mandatory_entrypoint_wiring_missing")
        error_code = ERR_STATIC_WIRING

    tmp_prefix = f"/tmp/headstamp-closure-{args.identity_id}"
    missing_file = Path(f"{tmp_prefix}-missing.txt").resolve()
    pass_file = Path(f"{tmp_prefix}-pass.txt").resolve()
    missing_receipt = Path(f"{tmp_prefix}-missing-receipt.json").resolve()
    inline_receipt = Path(f"{tmp_prefix}-inline-receipt.json").resolve()
    nongov_receipt = Path(f"{tmp_prefix}-nongov-receipt.json").resolve()
    compose_receipt = Path(f"{tmp_prefix}-compose-receipt.json").resolve()
    coverage_receipt = Path(f"{tmp_prefix}-coverage-receipt.json").resolve()
    mismatch_reply = Path(f"{tmp_prefix}-mismatch-probe.txt").resolve()
    mismatch_receipt = Path(f"{tmp_prefix}-mismatch-probe-receipt.json").resolve()

    missing_file.write_text(
        "[Audit Receipt] identity-protocol v1.5.1 release on main\nDate: 2026-03-05\nFinal verdict: GO\n",
        encoding="utf-8",
    )

    negative_missing_cmd = _send_time_cmd(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
        actor_id=actor_id,
        outlet_channel_id="governed_adapter_v1",
        blocker_receipt=missing_receipt,
        reply_file=missing_file,
    )
    rc_missing, payload_missing, _, _ = _run_json(negative_missing_cmd)
    dynamic_cases["negative_missing_header"] = {
        "rc": rc_missing,
        "error_code": str(payload_missing.get("error_code", "")),
        "send_time_gate_status": str(payload_missing.get("send_time_gate_status", "")),
        "reply_first_line_status": str(payload_missing.get("reply_first_line_status", "")),
        "blocker_receipt_path": str(payload_missing.get("blocker_receipt_path", "")),
    }
    missing_ok = (
        rc_missing != 0
        and str(payload_missing.get("error_code", "")) == ERR_SEND_TIME_GATE
        and str(payload_missing.get("send_time_gate_status", "")) == STATUS_FAIL_REQUIRED
    )
    if not missing_ok and not error_code:
        error_code = ERR_MISSING_HEADER_NEGATIVE
    if not missing_ok:
        stale_reasons.append("missing_header_negative_not_fail_closed")

    negative_inline_cmd = _send_time_cmd(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
        actor_id=actor_id,
        outlet_channel_id="governed_adapter_v1",
        blocker_receipt=inline_receipt,
        reply_text="manual inline reply without governed file evidence",
    )
    rc_inline, payload_inline, _, _ = _run_json(negative_inline_cmd)
    dynamic_cases["negative_inline_synthetic"] = {
        "rc": rc_inline,
        "error_code": str(payload_inline.get("error_code", "")),
        "send_time_gate_status": str(payload_inline.get("send_time_gate_status", "")),
        "reply_evidence_mode": str(payload_inline.get("reply_evidence_mode", "")),
    }
    inline_ok = (
        rc_inline != 0
        and str(payload_inline.get("error_code", "")) == ERR_SYNTHETIC_EVIDENCE
        and str(payload_inline.get("send_time_gate_status", "")) == STATUS_FAIL_REQUIRED
    )
    if not inline_ok and not error_code:
        error_code = ERR_INLINE_NEGATIVE
    if not inline_ok:
        stale_reasons.append("inline_synthetic_not_fail_closed")

    negative_nongov_cmd = _send_time_cmd(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
        actor_id=actor_id,
        outlet_channel_id="direct_text_channel",
        blocker_receipt=nongov_receipt,
        reply_file=missing_file,
    )
    rc_nongov, payload_nongov, _, _ = _run_json(negative_nongov_cmd)
    dynamic_cases["negative_non_governed_outlet"] = {
        "rc": rc_nongov,
        "error_code": str(payload_nongov.get("error_code", "")),
        "send_time_gate_status": str(payload_nongov.get("send_time_gate_status", "")),
        "governed_outlet_enforced": bool(payload_nongov.get("governed_outlet_enforced", False)),
        "outlet_channel_id": str(payload_nongov.get("outlet_channel_id", "")),
    }
    nongov_ok = (
        rc_nongov != 0
        and str(payload_nongov.get("error_code", "")) == ERR_NON_GOVERNED_OUTLET
        and str(payload_nongov.get("send_time_gate_status", "")) == STATUS_FAIL_REQUIRED
    )
    if not nongov_ok and not error_code:
        error_code = ERR_OUTLET_NEGATIVE
    if not nongov_ok:
        stale_reasons.append("non_governed_outlet_not_fail_closed")

    compose_cmd = [
        sys.executable,
        str((SCRIPT_DIR / "compose_and_validate_governed_reply.py").resolve()),
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--body-text",
        "[Audit Receipt] identity-protocol v1.5.1 release on main\nDate: 2026-03-05\nFinal verdict: GO",
        "--out-reply-file",
        str(pass_file),
        "--blocker-receipt-out",
        str(compose_receipt),
        "--outlet-channel-id",
        "governed_adapter_v1",
        "--actor-id",
        actor_id,
        "--json-only",
    ]
    rc_compose, payload_compose, _, _ = _run_json(compose_cmd)
    first_line = ""
    if pass_file.exists():
        text = pass_file.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if line.strip():
                first_line = line.strip()
                break
    dynamic_cases["positive_governed_compose"] = {
        "rc": rc_compose,
        "error_code": str(payload_compose.get("error_code", "")),
        "send_time_gate_status": str(payload_compose.get("send_time_gate_status", "")),
        "reply_first_line_status": str(payload_compose.get("reply_first_line_status", "")),
        "reply_outlet_guard_applied": bool(payload_compose.get("reply_outlet_guard_applied", False)),
        "first_line_prefix_ok": bool(first_line.startswith("Identity-Context:")),
        "out_reply_file": str(payload_compose.get("out_reply_file", "")),
    }
    compose_ok = (
        rc_compose == 0
        and str(payload_compose.get("send_time_gate_status", "")) == STATUS_PASS_REQUIRED
        and str(payload_compose.get("reply_first_line_status", "")) == STATUS_PASS_REQUIRED
        and bool(first_line.startswith("Identity-Context:"))
    )
    if not compose_ok and not error_code:
        error_code = ERR_COMPOSE_POSITIVE
    if not compose_ok:
        stale_reasons.append("governed_compose_positive_not_pass")

    coverage_equiv_ok = False
    coverage_case: dict[str, Any] = {}
    if compose_ok and pass_file.exists():
        coverage_cmd = _send_time_cmd(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            actor_id=actor_id,
            outlet_channel_id="governed_adapter_v1",
            blocker_receipt=coverage_receipt,
            reply_file=pass_file,
        )
        rc_cov, payload_cov, _, _ = _run_json(coverage_cmd)
        coverage_case = {
            "rc": rc_cov,
            "error_code": str(payload_cov.get("error_code", "")),
            "send_time_gate_status": str(payload_cov.get("send_time_gate_status", "")),
            "reply_first_line_status": str(payload_cov.get("reply_first_line_status", "")),
            "reply_evidence_mode": str(payload_cov.get("reply_evidence_mode", "")),
        }
        coverage_equiv_ok = (
            rc_cov == 0
            and coverage_case["send_time_gate_status"] == STATUS_PASS_REQUIRED
            and coverage_case["reply_first_line_status"] == STATUS_PASS_REQUIRED
        )
    else:
        coverage_case = {"rc": 2, "error": "compose_positive_not_available"}
        coverage_equiv_ok = False
    dynamic_cases["coverage_equivalence_direct_vs_wrapper"] = coverage_case
    if not coverage_equiv_ok:
        stale_reasons.append("coverage_equivalence_not_closed")
        if not error_code:
            error_code = ERR_COVERAGE_EQUIV

    mismatch_ok, mismatch_case, mismatch_stale = _actor_mismatch_probe(
        identity_id=args.identity_id,
        actor_id=actor_id,
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
        reply_file=mismatch_reply,
        blocker_receipt=mismatch_receipt,
    )
    dynamic_cases["negative_actor_bound_mismatch"] = mismatch_case
    stale_reasons.extend(mismatch_stale)
    if not mismatch_ok:
        if not error_code:
            error_code = ERR_ACTOR_MISMATCH_NEGATIVE

    static_ok = not missing_wiring
    dynamic_ok = missing_ok and inline_ok and nongov_ok and compose_ok and coverage_equiv_ok and mismatch_ok
    ok = static_ok and dynamic_ok

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "repo_catalog_path": str(repo_catalog_path),
        "operation": args.operation,
        "required_contract": True,
        "actor_id": actor_id,
        "actor_explicit": bool(actor_id),
        "actor_explicit_required": actor_required,
        "actor_semantic_role": "assistant_runtime",
        "emitter_actor_id": actor_id,
        "executor_actor_id": actor_id,
        "runtime_identity_id": args.identity_id,
        "headstamp_recurrence_closure_status": STATUS_PASS_REQUIRED if ok else STATUS_FAIL_REQUIRED,
        "error_code": "" if ok else (error_code or ERR_MIXED_EVIDENCE_UNPARTITIONED),
        "static_wiring_status": STATUS_PASS_REQUIRED if static_ok else STATUS_FAIL_REQUIRED,
        "dynamic_replay_status": STATUS_PASS_REQUIRED if dynamic_ok else STATUS_FAIL_REQUIRED,
        "coverage_normalization_status": STATUS_PASS_REQUIRED if coverage_equiv_ok else STATUS_FAIL_REQUIRED,
        "actor_explicitness_status": STATUS_PASS_REQUIRED if bool(actor_id) else STATUS_FAIL_REQUIRED,
        "mandatory_entrypoints": MANDATORY_ENTRYPOINTS,
        "entrypoint_coverage": coverage_rows,
        "missing_wiring_items": missing_wiring,
        "dynamic_cases": dynamic_cases,
        "stale_reasons": sorted(set(stale_reasons)),
    }
    _emit(payload, json_only=args.json_only)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
