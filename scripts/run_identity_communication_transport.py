#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from resolve_identity_context import resolve_repo_catalog_path
from tool_vendor_governance_common import resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        payload = json.loads(text[start : end + 1])
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _run_json(*, repo_root: Path, cmd: list[str]) -> tuple[int, dict[str, Any], str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_root), check=False)
    payload = _parse_json_payload(proc.stdout)
    return proc.returncode, payload, str(proc.stdout or ""), str(proc.stderr or "")


def _now_token() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    ap = argparse.ArgumentParser(description="Converge broadcast + protocol-feedback atomic lanes for identity communication transport.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--transaction-id", default="")
    ap.add_argument("--atomic-operation", default="validate")
    ap.add_argument("--skip-broadcast-sync", action="store_true")
    ap.add_argument("--skip-atomic-emit", action="store_true")
    ap.add_argument("--write-broadcast-receipt", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = resolve_repo_catalog_path(args.repo_catalog, start=Path(__file__).resolve())

    payload: dict[str, Any] = {
        "identity_communication_transport_run_status": STATUS_FAIL_REQUIRED,
        "error_code": "IP-COMM-005",
        "stale_reasons": [],
        "identity_id": str(args.identity_id or "").strip(),
        "catalog_path": str(catalog_path),
        "repo_catalog_path": str(repo_catalog_path),
        "run_id": str(args.run_id or "").strip(),
        "actor_id": str(args.actor_id or "").strip(),
        "session_id": str(args.session_id or "").strip(),
        "atomic_transaction_id": "",
        "broadcast_sync_executor_status": "",
        "atomic_emit_bootstrap_status": "",
        "transport_projection_status": "",
        "broadcast_sync_payload": {},
        "atomic_emit_payload": {},
        "transport_projection_payload": {},
    }

    if not catalog_path.exists():
        payload["stale_reasons"] = ["catalog_not_found"]
        _emit(payload, json_only=args.json_only)
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
    except Exception as exc:
        payload["stale_reasons"] = [f"identity_resolution_failed:{type(exc).__name__}"]
        _emit(payload, json_only=args.json_only)
        return 2

    run_id = str(args.run_id or "").strip() or f"comm-transport-{args.identity_id}-{_now_token()}"
    session_id = str(args.session_id or "").strip() or f"run:{run_id}"
    actor_id = str(args.actor_id or "").strip()
    tx = str(args.transaction_id or "").strip() or f"{run_id}-atomic-{int(time.time())}"
    payload["run_id"] = run_id
    payload["session_id"] = session_id
    payload["atomic_transaction_id"] = tx
    payload["pack_path"] = str(pack_path)
    payload["task_path"] = str(task_path)

    if not args.skip_broadcast_sync:
        rc, sync_payload, stdout, stderr = _run_json(
            repo_root=repo_root,
            cmd=[
                "python3",
                "scripts/run_identity_broadcast_delivery.py",
                "--catalog",
                str(catalog_path),
                "--identity-id",
                str(args.identity_id or "").strip(),
                "--run-id",
                run_id,
                "--actor-id",
                actor_id,
                "--session-id",
                session_id,
                "--sync",
                "--write-receipt",
                "--json-only",
            ],
        )
        sync_status = str(sync_payload.get("identity_broadcast_delivery_status", "")).strip().upper()
        payload["broadcast_sync_executor_status"] = sync_status or STATUS_FAIL_REQUIRED
        payload["broadcast_sync_payload"] = sync_payload or {
            "stdout": stdout,
            "stderr": stderr,
        }
        if rc != 0 or sync_status != STATUS_PASS_REQUIRED:
            payload["stale_reasons"] = (
                [str(item).strip() for item in (sync_payload.get("stale_reasons") or []) if str(item).strip()]
                or ["broadcast_delivery_sync_failed"]
            )
            _emit(payload, json_only=args.json_only)
            return 1
    else:
        payload["broadcast_sync_executor_status"] = "SKIPPED_BY_FLAG"

    if not args.skip_atomic_emit:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as tmp:
            json.dump(
                {
                    "bootstrap_kind": "identity_communication_transport",
                    "identity_id": str(args.identity_id or "").strip(),
                    "run_id": run_id,
                    "actor_id": actor_id,
                    "session_id": session_id,
                    "transport_scope": "identity_communication_transport",
                    "bootstrap_reason": "communication_transport_convergence",
                    "observed_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                },
                tmp,
                ensure_ascii=False,
                indent=2,
            )
            tmp.write("\n")
            tmp_path = Path(tmp.name).resolve()
        try:
            rc, atomic_payload, stdout, stderr = _run_json(
                repo_root=repo_root,
                cmd=[
                    "python3",
                    "scripts/emit_protocol_feedback_atomic.py",
                    "--catalog",
                    str(catalog_path),
                    "--identity-id",
                    str(args.identity_id or "").strip(),
                    "--operation",
                    str(args.atomic_operation or "validate").strip() or "validate",
                    "--transaction-id",
                    tx,
                    "--payload-json",
                    str(tmp_path),
                    "--json-only",
                ],
            )
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
        atomic_status = str(atomic_payload.get("atomic_emit_status", "")).strip().upper()
        payload["atomic_emit_bootstrap_status"] = atomic_status or STATUS_FAIL_REQUIRED
        payload["atomic_emit_payload"] = atomic_payload or {
            "stdout": stdout,
            "stderr": stderr,
        }
        if rc != 0 or atomic_status != STATUS_PASS_REQUIRED:
            payload["stale_reasons"] = (
                [str(item).strip() for item in (atomic_payload.get("stale_reasons") or []) if str(item).strip()]
                or ["protocol_feedback_atomic_emit_failed"]
            )
            _emit(payload, json_only=args.json_only)
            return 1
    else:
        payload["atomic_emit_bootstrap_status"] = "SKIPPED_BY_FLAG"

    rc, projection_payload, stdout, stderr = _run_json(
        repo_root=repo_root,
        cmd=[
            "python3",
            "scripts/validate_identity_communication_transport.py",
            "--catalog",
            str(catalog_path),
            "--repo-catalog",
            str(repo_catalog_path),
            "--identity-id",
            str(args.identity_id or "").strip(),
            "--json-only",
        ],
    )
    projection_status = str(projection_payload.get("identity_communication_transport_status", "")).strip().upper()
    payload["transport_projection_status"] = projection_status or STATUS_FAIL_REQUIRED
    payload["transport_projection_payload"] = projection_payload or {
        "stdout": stdout,
        "stderr": stderr,
    }
    if rc != 0 or projection_status != STATUS_PASS_REQUIRED:
        payload["stale_reasons"] = (
            [str(item).strip() for item in (projection_payload.get("stale_reasons") or []) if str(item).strip()]
            or ["identity_communication_transport_projection_failed"]
        )
        _emit(payload, json_only=args.json_only)
        return 1

    payload.update(projection_payload)
    payload["identity_communication_transport_run_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    payload["run_id"] = run_id
    payload["actor_id"] = actor_id
    payload["session_id"] = session_id
    payload["atomic_transaction_id"] = tx
    payload["pack_path"] = str(pack_path)
    payload["task_path"] = str(task_path)
    payload["catalog_path"] = str(catalog_path)
    payload["repo_catalog_path"] = str(repo_catalog_path)
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
