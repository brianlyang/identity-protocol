#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import load_actor_binding, load_actor_binding_store, resolve_actor_id
from final_emit_contract_common import (
    FINAL_EMIT_CHANNEL_ID,
    FINAL_EMIT_POLICY_MODE,
    FINAL_EMIT_SCHEMA_ID,
)
from headstamp_error_family_common import (
    ERR_HDSTAMP_ACTOR_LAYER_MISMATCH,
    ERR_HDSTAMP_MISSING_OR_MALFORMED,
    ERR_HDSTAMP_RECEIPT_MISSING,
    inject_legacy_error_fields,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_BODY_EMPTY = ERR_HDSTAMP_MISSING_OR_MALFORMED
ERR_COMPOSE_RUNTIME = ERR_HDSTAMP_RECEIPT_MISSING
ERR_COMPOSE_JSON_MISSING = ERR_HDSTAMP_RECEIPT_MISSING
ERR_EGRESS_CONTRACT_FAILED = ERR_HDSTAMP_RECEIPT_MISSING
ERR_REPLY_FILE_MISSING = ERR_HDSTAMP_RECEIPT_MISSING
ERR_CONTEXT_RESOLVE = ERR_HDSTAMP_ACTOR_LAYER_MISMATCH
ERR_IDENTITY_RESOLVE = ERR_HDSTAMP_ACTOR_LAYER_MISMATCH

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    payload = inject_legacy_error_fields(payload)
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        doc = json.loads(text)
        return doc if isinstance(doc, dict) else None
    except Exception:
        return None


def _resolve_relative_path(raw: str) -> Path:
    p = Path(str(raw).strip()).expanduser()
    if not p.is_absolute():
        p = (REPO_ROOT / p).resolve()
    return p.resolve()


def _default_repo_catalog_path() -> Path:
    return (REPO_ROOT / "identity" / "catalog" / "identities.yaml").resolve()


def _default_global_catalog_path() -> Path:
    codex_home = str(os.environ.get("CODEX_HOME", "")).strip()
    if codex_home:
        return (Path(codex_home).expanduser() / ".identity" / "catalog.local.yaml").resolve()
    return (Path.home() / ".codex" / ".identity" / "catalog.local.yaml").resolve()


def _default_project_catalog_candidates() -> list[Path]:
    if REPO_ROOT.name == "identity-protocol-local":
        project_root = REPO_ROOT.parent
    else:
        project_root = REPO_ROOT
    candidates = [
        (project_root / ".identity" / "catalog.local.yaml").resolve(),
        (REPO_ROOT / ".identity" / "catalog.local.yaml").resolve(),
    ]
    # Preserve order while deduplicating.
    out: list[Path] = []
    for path in candidates:
        if path not in out:
            out.append(path)
    return out


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json root must be object: {path}")
    return data


def _resolve_catalog(args: argparse.Namespace) -> tuple[Path, str]:
    raw = str(args.catalog or "").strip()
    if raw:
        return _resolve_relative_path(raw), "explicit"

    for candidate in _default_project_catalog_candidates():
        if candidate.exists():
            return candidate, "project_auto"
    global_catalog = _default_global_catalog_path()
    if global_catalog.exists():
        return global_catalog, "global_auto"
    return _default_project_catalog_candidates()[0], "project_default_missing"


def _resolve_repo_catalog(args: argparse.Namespace) -> tuple[Path, str]:
    raw = str(args.repo_catalog or "").strip()
    if raw:
        return _resolve_relative_path(raw), "explicit"
    return _default_repo_catalog_path(), "repo_default"


def _resolve_actor_id(args: argparse.Namespace) -> tuple[str, str]:
    actor_raw = str(args.actor_id or "").strip()
    if actor_raw:
        return resolve_actor_id(actor_raw), "explicit"
    actor_env = str(os.environ.get("CODEX_ACTOR_ID", "")).strip()
    if actor_env:
        return resolve_actor_id(actor_env), "env"
    raise ValueError("actor-id required: pass --actor-id or set CODEX_ACTOR_ID")


def _resolve_identity_id(
    *,
    args: argparse.Namespace,
    catalog_path: Path,
    actor_id: str,
    session_id: str = "",
) -> tuple[str, str]:
    explicit = str(args.identity_id or "").strip()
    if explicit:
        return explicit, "explicit"
    if not catalog_path.exists():
        raise FileNotFoundError(f"catalog not found for auto identity resolution: {catalog_path}")

    session_id = str(session_id or "").strip()
    binding = load_actor_binding(catalog_path, actor_id, session_id=session_id)
    bound_identity_id = str(binding.get("identity_id", "")).strip()
    if bound_identity_id:
        return bound_identity_id, "actor_binding_session_scoped" if session_id else "actor_binding"
    if session_id:
        raise RuntimeError(f"session_id has no actor binding: actor={actor_id} session_id={session_id}")

    store = load_actor_binding_store(catalog_path, actor_id)
    bound_identity_ids = {
        str(x.get("identity_id", "")).strip()
        for x in (store.get("bindings") or [])
        if isinstance(x, dict) and str(x.get("identity_id", "")).strip()
    }
    if len(bound_identity_ids) > 1:
        raise RuntimeError(
            "identity-id is ambiguous under actor multibinding; pass --identity-id or --session-id explicitly "
            f"(actor={actor_id}, bound_identities={sorted(bound_identity_ids)})"
        )

    session_active = (catalog_path.parent / "session" / "active_identity.json").resolve()
    if session_active.exists():
        try:
            active_payload = _load_json(session_active)
            active_identity_id = str(active_payload.get("identity_id", "")).strip()
            if active_identity_id:
                return active_identity_id, "session_active"
        except Exception:
            pass

    doc = _load_yaml(catalog_path)
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    active_rows = [x for x in rows if str(x.get("status", "")).strip().lower() == "active"]
    active_ids = [str(x.get("id", "")).strip() for x in active_rows if str(x.get("id", "")).strip()]
    if len(active_ids) == 1:
        return active_ids[0], "catalog_single_active"

    default_identity = str(doc.get("default_identity", "")).strip()
    if default_identity:
        return default_identity, "catalog_default_identity"

    all_ids = [str(x.get("id", "")).strip() for x in rows if str(x.get("id", "")).strip()]
    if len(all_ids) == 1:
        return all_ids[0], "catalog_single_row"

    raise RuntimeError(
        "identity-id is ambiguous under auto mode; pass --identity-id explicitly "
        f"(active_ids={active_ids}, all_ids={all_ids})"
    )


def _resolve_body(args: argparse.Namespace) -> tuple[str, str]:
    body_text = str(args.body_text or "")
    if str(args.body_file or "").strip():
        body_file = Path(str(args.body_file).strip()).expanduser().resolve()
        if not body_file.exists():
            raise FileNotFoundError(f"body file not found: {body_file}")
        body_text = body_file.read_text(encoding="utf-8", errors="ignore")
    elif args.stdin_body:
        body_text = sys.stdin.read()
    normalized = str(body_text or "").strip()
    if not normalized:
        raise ValueError("empty body")
    return normalized, "stdin" if args.stdin_body else ("body_file" if str(args.body_file or "").strip() else "body_text")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Final egress single-entry wrapper. "
            "Always routes through compose_and_validate_governed_reply and emits reply only when contracts pass."
        )
    )
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="")
    ap.add_argument(
        "--actor-id",
        default="",
        help="required actor context; no implicit default fallback is allowed",
    )
    ap.add_argument("--session-id", default="", help="optional actor session selector for multibinding disambiguation")
    ap.add_argument("--body-text", default="")
    ap.add_argument("--body-file", default="")
    ap.add_argument("--stdin-body", action="store_true")
    ap.add_argument("--work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--outlet-channel-id", default=FINAL_EMIT_CHANNEL_ID)
    ap.add_argument("--out-reply-file", default="")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument("--json-only", action="store_true")
    ap.add_argument(
        "--strict-explicit-context",
        action="store_true",
        help="require explicit --identity-id/--catalog/--actor-id, disable auto context resolution",
    )
    args = ap.parse_args()

    try:
        if args.strict_explicit_context:
            missing: list[str] = []
            if not str(args.identity_id or "").strip():
                missing.append("identity-id")
            if not str(args.catalog or "").strip():
                missing.append("catalog")
            if not str(args.actor_id or "").strip():
                missing.append("actor-id")
            if missing:
                raise ValueError(f"missing required explicit context args: {','.join(missing)}")

        catalog_path, catalog_resolution_mode = _resolve_catalog(args)
        repo_catalog_path, repo_catalog_resolution_mode = _resolve_repo_catalog(args)
        actor_id, actor_resolution_mode = _resolve_actor_id(args)
        identity_id, identity_resolution_mode = _resolve_identity_id(
            args=args,
            catalog_path=catalog_path,
            actor_id=actor_id,
            session_id=str(args.session_id or "").strip(),
        )
    except Exception as exc:
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_CONTEXT_RESOLVE,
            "stale_reasons": [f"context_resolution_failed:{exc}"],
            "identity_id": str(args.identity_id or "").strip(),
            "catalog": str(args.catalog or "").strip(),
            "actor_id": str(args.actor_id or "").strip(),
        }
        _emit(payload, json_only=args.json_only)
        return 1

    if not repo_catalog_path.exists():
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_CONTEXT_RESOLVE,
            "stale_reasons": [f"repo_catalog_missing:{repo_catalog_path}"],
            "repo_catalog_path": str(repo_catalog_path),
        }
        _emit(payload, json_only=args.json_only)
        return 1
    if not catalog_path.exists():
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_IDENTITY_RESOLVE,
            "stale_reasons": [f"catalog_missing:{catalog_path}"],
            "catalog_path": str(catalog_path),
        }
        _emit(payload, json_only=args.json_only)
        return 1

    outlet_channel_id = str(args.outlet_channel_id or "").strip() or FINAL_EMIT_CHANNEL_ID
    if outlet_channel_id != FINAL_EMIT_CHANNEL_ID:
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_EGRESS_CONTRACT_FAILED,
            "stale_reasons": [f"non_canonical_outlet_channel:{outlet_channel_id}"],
            "outlet_channel_id": outlet_channel_id,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        body, body_mode = _resolve_body(args)
    except Exception as exc:
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_BODY_EMPTY,
            "stale_reasons": [f"body_invalid:{exc}"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    compose_cmd = [
        sys.executable,
        str((SCRIPT_DIR / "compose_and_validate_governed_reply.py").resolve()),
        "--identity-id",
        identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--actor-id",
        actor_id,
        "--session-id",
        str(args.session_id or "").strip(),
        "--body-text",
        body,
        "--outlet-channel-id",
        outlet_channel_id,
        "--json-only",
    ]
    if str(args.work_layer or "").strip():
        compose_cmd += ["--work-layer", str(args.work_layer).strip()]
    if str(args.source_layer or "").strip():
        compose_cmd += ["--source-layer", str(args.source_layer).strip()]
    if str(args.layer_intent_text or "").strip():
        compose_cmd += ["--layer-intent-text", str(args.layer_intent_text).strip()]
    if str(args.out_reply_file or "").strip():
        compose_cmd += ["--out-reply-file", str(args.out_reply_file).strip()]
    if str(args.out_json or "").strip():
        compose_cmd += ["--out-json", str(args.out_json).strip()]
    if str(args.blocker_receipt_out or "").strip():
        compose_cmd += ["--blocker-receipt-out", str(args.blocker_receipt_out).strip()]

    proc = subprocess.run(compose_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    compose_payload = _parse_json_payload(proc.stdout or "")
    if proc.returncode != 0 and compose_payload is None:
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_COMPOSE_RUNTIME,
            "compose_rc": proc.returncode,
            "stderr_tail": (proc.stderr or "").strip().splitlines()[-1] if (proc.stderr or "").strip() else "",
        }
        _emit(payload, json_only=args.json_only)
        return 1
    if compose_payload is None:
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_COMPOSE_JSON_MISSING,
            "compose_rc": proc.returncode,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    send_time_status = str(compose_payload.get("send_time_gate_status", "")).strip().upper()
    final_emit_status = str(compose_payload.get("final_emit_contract_status", "")).strip().upper()
    emit_allowed = bool(compose_payload.get("reply_emit_allowed", False))
    out_reply_file = str(compose_payload.get("out_reply_file", "")).strip()
    pass_contract = (
        proc.returncode == 0
        and send_time_status == STATUS_PASS_REQUIRED
        and final_emit_status == STATUS_PASS_REQUIRED
        and emit_allowed
    )

    payload: dict[str, Any] = {
        "final_emit_guard_status": STATUS_PASS_REQUIRED if pass_contract else STATUS_FAIL_REQUIRED,
        "error_code": "" if pass_contract else ERR_EGRESS_CONTRACT_FAILED,
        "compose_rc": proc.returncode,
        "identity_id": identity_id,
        "catalog_path": str(catalog_path),
        "repo_catalog_path": str(repo_catalog_path),
        "resolved_actor_id": actor_id,
        "catalog_resolution_mode": catalog_resolution_mode,
        "repo_catalog_resolution_mode": repo_catalog_resolution_mode,
        "identity_resolution_mode": identity_resolution_mode,
        "actor_resolution_mode": actor_resolution_mode,
        "body_mode": body_mode,
        "send_time_gate_status": send_time_status,
        "final_emit_contract_status": final_emit_status,
        "reply_emit_allowed": emit_allowed,
        "out_reply_file": out_reply_file,
        "outlet_channel_id": str(compose_payload.get("outlet_channel_id", "")),
        "governed_outlet_enforced": bool(compose_payload.get("governed_outlet_enforced", False)),
        "outlet_preflight_receipt": str(compose_payload.get("outlet_preflight_receipt", "")),
        "outlet_bypass_detected": bool(compose_payload.get("outlet_bypass_detected", False)),
        "final_emit_channel_id": str(compose_payload.get("final_emit_channel_id", FINAL_EMIT_CHANNEL_ID)),
        "final_emit_policy_mode": str(compose_payload.get("final_emit_policy_mode", FINAL_EMIT_POLICY_MODE)),
        "final_emit_schema_id": str(compose_payload.get("final_emit_schema_id", FINAL_EMIT_SCHEMA_ID)),
        "final_emit_schema_status": str(compose_payload.get("final_emit_schema_status", "")).strip().upper(),
    }
    if not pass_contract:
        payload["stale_reasons"] = ["egress_contract_not_pass"]
        _emit(payload, json_only=args.json_only)
        return 1

    reply_path = Path(out_reply_file).expanduser().resolve()
    if not reply_path.exists():
        payload["final_emit_guard_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REPLY_FILE_MISSING
        payload["stale_reasons"] = ["reply_file_missing_after_compose_pass"]
        _emit(payload, json_only=args.json_only)
        return 1

    reply_text = reply_path.read_text(encoding="utf-8", errors="ignore")
    if args.json_only:
        payload["reply_preview"] = reply_text.splitlines()[:2]
        _emit(payload, json_only=True)
    else:
        print(reply_text.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
