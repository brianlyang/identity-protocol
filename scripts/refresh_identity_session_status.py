#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actor_session_common import actor_session_path, load_actor_binding, resolve_actor_id
from resolve_identity_context import resolve_identity

LEASE_ACTIVE = "ACTIVE"
LEASE_STALE = "STALE"
LEASE_MISSING = "MISSING"

POINTER_PASS = "PASS"
POINTER_WARN = "WARN"
POINTER_FAIL = "FAIL"


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _parse_iso8601(value: str) -> datetime | None:
    token = str(value or "").strip()
    if not token:
        return None
    normalized = token.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _lease_status(actor_binding: dict[str, Any]) -> tuple[str, list[str]]:
    if not actor_binding:
        return LEASE_MISSING, ["actor_binding_missing"]

    risks: list[str] = []
    explicit = str(actor_binding.get("lease_status", "")).strip().upper()
    if explicit in {LEASE_ACTIVE, LEASE_STALE, LEASE_MISSING}:
        if explicit != LEASE_ACTIVE:
            risks.append(f"lease_status_{explicit.lower()}")
        return explicit, risks

    expires_at = _parse_iso8601(str(actor_binding.get("lease_expires_at", "")).strip())
    if expires_at is not None:
        now = datetime.now(timezone.utc)
        if expires_at < now:
            risks.append("lease_expired")
            return LEASE_STALE, risks
        return LEASE_ACTIVE, risks

    # Compatibility fallback: run/session id present implies active lease surrogate.
    if any(str(actor_binding.get(k, "")).strip() for k in ("lease_id", "run_id", "state_hash", "updated_at")):
        return LEASE_ACTIVE, risks

    risks.append("lease_metadata_missing")
    return LEASE_MISSING, risks


def _pointer_consistency(
    *,
    identity_id: str,
    actor_id: str,
    catalog_path: Path,
    actor_binding: dict[str, Any],
    actor_session_file: Path,
) -> tuple[str, list[str], dict[str, Any]]:
    risks: list[str] = []
    status = POINTER_PASS

    actor_binding_identity = str(actor_binding.get("identity_id", "")).strip() if actor_binding else ""
    actor_binding_catalog = str(actor_binding.get("catalog_path", "")).strip() if actor_binding else ""
    actor_binding_actor = str(actor_binding.get("actor_id", "")).strip() if actor_binding else ""

    if not actor_binding:
        status = POINTER_FAIL
        risks.append("actor_binding_missing")
    else:
        if actor_binding_actor and actor_binding_actor != actor_id:
            status = POINTER_FAIL
            risks.append("actor_binding_actor_id_mismatch")
        if actor_binding_catalog and actor_binding_catalog != str(catalog_path):
            status = POINTER_FAIL
            risks.append("actor_binding_catalog_path_mismatch")
        if not actor_binding_identity:
            status = POINTER_FAIL
            risks.append("actor_binding_identity_missing")
        elif actor_binding_identity != identity_id:
            if status != POINTER_FAIL:
                status = POINTER_WARN
            risks.append("actor_bound_to_different_identity")

    # compatibility mirror consistency (warning-level drift)
    legacy_pointer_path = (catalog_path.parent / "session" / "active_identity.json").resolve()
    legacy_pointer = _load_json(legacy_pointer_path) if legacy_pointer_path.exists() else {}
    legacy_identity = str(legacy_pointer.get("identity_id", "")).strip() if legacy_pointer else ""
    legacy_catalog = str(legacy_pointer.get("catalog_path", "")).strip() if legacy_pointer else ""

    if not legacy_pointer:
        if status == POINTER_PASS:
            status = POINTER_WARN
        risks.append("legacy_pointer_missing")
    else:
        expected_identity = actor_binding_identity or identity_id
        if legacy_identity and expected_identity and legacy_identity != expected_identity:
            if status == POINTER_PASS:
                status = POINTER_WARN
            risks.append("legacy_pointer_identity_mismatch")
        if legacy_catalog and legacy_catalog != str(catalog_path):
            if status == POINTER_PASS:
                status = POINTER_WARN
            risks.append("legacy_pointer_catalog_mismatch")

    detail = {
        "actor_session_path": str(actor_session_file),
        "actor_binding_identity_id": actor_binding_identity,
        "legacy_pointer_path": str(legacy_pointer_path),
        "legacy_pointer_identity_id": legacy_identity,
    }
    return status, risks, detail


def _baseline_visibility(
    *,
    identity_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    execution_report: str,
    baseline_policy: str,
) -> tuple[dict[str, Any], list[str]]:
    cmd = [
        "python3",
        "scripts/validate_identity_protocol_baseline_freshness.py",
        "--identity-id",
        identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--baseline-policy",
        baseline_policy,
        "--json-only",
    ]
    if execution_report.strip():
        cmd.extend(["--execution-report", execution_report.strip()])

    rc, out, err = _run_capture(cmd)
    payload = _parse_json_payload(out) or {}
    stale_reasons: list[str] = []

    baseline_status = str(payload.get("baseline_status", "")).strip().upper()
    if baseline_status not in {"PASS", "WARN", "FAIL"}:
        baseline_status = "WARN"
        stale_reasons.append("baseline_status_missing_or_invalid")

    baseline_error_code = str(payload.get("baseline_error_code", "")).strip()
    if rc != 0 and baseline_status == "PASS":
        baseline_status = "WARN"
        stale_reasons.append("baseline_validator_nonzero_without_status")
    if rc != 0 and err:
        stale_reasons.append(f"baseline_validator_stderr:{err.splitlines()[-1]}")

    data = {
        "report_protocol_commit_sha": str(payload.get("report_protocol_commit_sha", "")).strip(),
        "protocol_head_sha_at_run_start": str(payload.get("protocol_head_sha_at_run_start", "")).strip(),
        "baseline_reference_mode": str(payload.get("baseline_reference_mode", "")).strip(),
        "current_protocol_head_sha": str(payload.get("current_protocol_head_sha", "")).strip(),
        "head_drift_detected": bool(payload.get("head_drift_detected", False)),
        "baseline_status": baseline_status,
        "baseline_error_code": baseline_error_code,
        "lag_commits": payload.get("lag_commits"),
        "report_selected_path": str(payload.get("report_selected_path", "")).strip(),
    }
    return data, stale_reasons


def _next_action(pointer_consistency: str, lease_status: str, baseline_status: str, risk_flags: list[str]) -> str:
    if pointer_consistency == POINTER_FAIL:
        return "repair_actor_binding_and_sync_session_pointer"
    if lease_status in {LEASE_MISSING, LEASE_STALE}:
        return "refresh_or_reactivate_actor_binding"
    if baseline_status in {"WARN", "FAIL"}:
        return "run_identity_update_to_refresh_protocol_baseline"
    if risk_flags:
        return "review_session_refresh_risk_flags"
    return "none"


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh identity actor/session status with baseline visibility fields.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--execution-report", default="")
    ap.add_argument("--baseline-policy", choices=["strict", "warn"], default="warn")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        resolved = resolve_identity(
            args.identity_id,
            repo_catalog_path,
            catalog_path,
            allow_conflict=True,
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity context: {exc}")
        return 1

    actor_id = resolve_actor_id(args.actor_id)
    actor_session_file = actor_session_path(catalog_path, actor_id)
    actor_binding = load_actor_binding(catalog_path, actor_id, identity_id=args.identity_id)

    resolved_pack = Path(str(resolved.get("resolved_pack_path") or resolved.get("pack_path") or "")).expanduser().resolve()
    resolved_scope = str(resolved.get("resolved_scope", "")).strip().upper() or "UNKNOWN"

    lease_status, lease_risks = _lease_status(actor_binding)
    pointer_consistency, pointer_risks, pointer_detail = _pointer_consistency(
        identity_id=args.identity_id,
        actor_id=actor_id,
        catalog_path=catalog_path,
        actor_binding=actor_binding,
        actor_session_file=actor_session_file,
    )

    baseline, baseline_risks = _baseline_visibility(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        repo_catalog_path=repo_catalog_path,
        execution_report=args.execution_report,
        baseline_policy=args.baseline_policy,
    )

    risk_flags = sorted(
        set(
            lease_risks
            + pointer_risks
            + baseline_risks
            + (["protocol_baseline_non_pass"] if baseline.get("baseline_status") in {"WARN", "FAIL"} else [])
            + (["pointer_consistency_warn"] if pointer_consistency == POINTER_WARN else [])
            + (["pointer_consistency_fail"] if pointer_consistency == POINTER_FAIL else [])
        )
    )

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "actor_id": actor_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(resolved_pack),
        "resolved_scope": resolved_scope,
        "lease_status": lease_status,
        "pointer_consistency": pointer_consistency,
        "risk_flags": risk_flags,
        "next_action": _next_action(pointer_consistency, lease_status, str(baseline.get("baseline_status", "")), risk_flags),
        "report_protocol_commit_sha": baseline.get("report_protocol_commit_sha", ""),
        "protocol_head_sha_at_run_start": baseline.get("protocol_head_sha_at_run_start", ""),
        "baseline_reference_mode": baseline.get("baseline_reference_mode", ""),
        "current_protocol_head_sha": baseline.get("current_protocol_head_sha", ""),
        "head_drift_detected": baseline.get("head_drift_detected", False),
        "baseline_status": baseline.get("baseline_status", "WARN"),
        "baseline_error_code": baseline.get("baseline_error_code", ""),
        "lag_commits": baseline.get("lag_commits"),
        "report_selected_path": baseline.get("report_selected_path", ""),
        "actor_session_path": str(actor_session_file),
        "pointer_detail": pointer_detail,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            "[OK] refresh identity session status: "
            f"identity={args.identity_id} actor={actor_id} pointer={pointer_consistency} lease={lease_status} baseline={payload['baseline_status']}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
