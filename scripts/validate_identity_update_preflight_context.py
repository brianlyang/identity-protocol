#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ERR_ENV_CATALOG_DRIFT = "IP-ENV-003"
ERR_ACTOR_BINDING = "IP-ASB-201"

SCRIPT_DIR = Path(__file__).resolve().parent
PROTOCOL_ROOT = SCRIPT_DIR.parent


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROTOCOL_ROOT),
    )
    return p.returncode, p.stdout or "", p.stderr or ""


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _extract_error_code(raw: str) -> str:
    text = str(raw or "")
    for token in text.replace("\n", " ").split(" "):
        t = token.strip("[],:;()")
        if t.startswith("IP-") and "-" in t[3:]:
            return t
    return ""


def _build_runtime_guard_cmd(args: argparse.Namespace) -> list[str]:
    cmd = [
        "python3",
        "scripts/validate_identity_runtime_mode_guard.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--expect-mode",
        args.expect_mode,
        "--operation",
        args.operation,
        "--json",
    ]
    if str(args.scope or "").strip():
        cmd.extend(["--scope", str(args.scope).strip()])
    if str(args.env_catalog_mismatch_override_receipt or "").strip():
        cmd.extend(
            [
                "--env-catalog-mismatch-override-receipt",
                str(args.env_catalog_mismatch_override_receipt).strip(),
            ]
        )
    return cmd


def _build_actor_binding_cmd(args: argparse.Namespace) -> list[str]:
    cmd = [
        "python3",
        "scripts/validate_actor_session_binding.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--actor-id",
        args.actor_id,
        "--operation",
        args.operation,
        "--json-only",
    ]
    if str(args.session_id or "").strip():
        cmd.extend(["--session-id", str(args.session_id).strip()])
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Aggregate update preflight context checks and fail-close on "
            "runtime mode drift / actor-session binding mismatch."
        )
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", required=True)
    ap.add_argument("--session-id", default="")
    ap.add_argument("--scope", default="")
    ap.add_argument("--expect-mode", choices=["auto", "project", "global"], default="auto")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="update",
    )
    ap.add_argument("--env-catalog-mismatch-override-receipt", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    runtime_cmd = _build_runtime_guard_cmd(args)
    rc_runtime, out_runtime, err_runtime = _run_capture(runtime_cmd)
    runtime_payload = _parse_json_payload(out_runtime) or {}
    runtime_error_code = str(runtime_payload.get("error_code", "")).strip() or _extract_error_code(
        f"{out_runtime}\n{err_runtime}"
    )
    runtime_status = "PASS_REQUIRED" if rc_runtime == 0 else "FAIL_REQUIRED"

    actor_cmd = _build_actor_binding_cmd(args)
    rc_actor, out_actor, err_actor = _run_capture(actor_cmd)
    actor_payload = _parse_json_payload(out_actor) or {}
    actor_status = str(actor_payload.get("actor_binding_status", "")).strip().upper()
    if not actor_status:
        actor_status = "PASS_REQUIRED" if rc_actor == 0 else "FAIL_REQUIRED"
    actor_error_code = str(actor_payload.get("error_code", "")).strip() or _extract_error_code(f"{out_actor}\n{err_actor}")

    overall_status = "PASS_REQUIRED"
    error_code = ""
    stale_reasons: list[str] = []
    next_action = "proceed_update_mutation"

    if runtime_status != "PASS_REQUIRED":
        overall_status = "FAIL_REQUIRED"
        error_code = runtime_error_code or ERR_ENV_CATALOG_DRIFT
        stale_reasons.extend(["runtime_mode_guard_failed"])
        if error_code == ERR_ENV_CATALOG_DRIFT:
            next_action = "source ./scripts/use_project_identity_runtime.sh"
        else:
            next_action = "verify --catalog and IDENTITY_CATALOG binding before update"

    actor_fail = actor_status not in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}
    if actor_fail:
        overall_status = "FAIL_REQUIRED"
        if not error_code:
            error_code = actor_error_code or ERR_ACTOR_BINDING
        stale_reasons.extend([x for x in (actor_payload.get("stale_reasons") or []) if str(x).strip()])
        if str(error_code or "").strip() == ERR_ACTOR_BINDING:
            session_hint = str(args.session_id or "").strip() or "run:<stable-session-id>"
            next_action = (
                "python3 scripts/identity_creator.py activate "
                f"--identity-id {args.identity_id} --actor-id {args.actor_id} --session-id {session_hint}"
            )
        elif not next_action:
            next_action = "refresh actor/session binding before update"

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "operation": args.operation,
        "actor_id": args.actor_id,
        "session_id": str(args.session_id or "").strip(),
        "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        "repo_catalog_path": str(Path(args.repo_catalog).expanduser().resolve()),
        "status": overall_status,
        "error_code": error_code,
        "next_action": next_action,
        "stale_reasons": sorted(set([str(x).strip() for x in stale_reasons if str(x).strip()])),
        "runtime_mode_guard_status": runtime_status,
        "runtime_mode_guard_error_code": runtime_error_code,
        "runtime_mode_guard_payload": runtime_payload,
        "actor_session_binding_status": actor_status,
        "actor_session_binding_error_code": actor_error_code,
        "actor_session_binding_payload": actor_payload,
        "validator_commands": {
            "runtime_mode_guard": runtime_cmd,
            "actor_session_binding": actor_cmd,
        },
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if overall_status != "PASS_REQUIRED":
            print(f"[FAIL] {error_code or 'IP-UPDATE-PREFLIGHT-001'} update preflight context validation failed")
            print(f"       next_action: {next_action}")
        else:
            print("[OK] update preflight context passed")

    return 0 if overall_status == "PASS_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
