#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import hashlib
import hmac
import json
import os
import shlex
import subprocess
import sys
import time
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
from tool_vendor_governance_common import resolve_pack_and_task
from protocol_infra_contract import (
    PRIVILEGE_ESCALATION_ERROR_CODE,
    PRIVILEGE_ESCALATION_REASON_PREFIX,
    PRIVILEGE_ESCALATION_REMEDIATION_HINT,
)

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    psutil = None

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

ERR_BODY_EMPTY = ERR_HDSTAMP_MISSING_OR_MALFORMED
ERR_COMPOSE_RUNTIME = ERR_HDSTAMP_RECEIPT_MISSING
ERR_COMPOSE_JSON_MISSING = ERR_HDSTAMP_RECEIPT_MISSING
ERR_EGRESS_CONTRACT_FAILED = ERR_HDSTAMP_RECEIPT_MISSING
ERR_REPLY_FILE_MISSING = ERR_HDSTAMP_RECEIPT_MISSING
ERR_CONTEXT_RESOLVE = ERR_HDSTAMP_ACTOR_LAYER_MISMATCH
ERR_IDENTITY_RESOLVE = ERR_HDSTAMP_ACTOR_LAYER_MISMATCH

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
HOST_GATEWAY_CONTRACT_KEYS = (
    "protocol_host_unique_channel_contract_v1",
    "protocol_gateway_wrapper_contract_v1",
    "protocol_gateway_contract_v1",
)
EGRESS_GRANT_NONCE_STATE_FILE = "egress_grant_nonce_state.json"


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


def _resolve_host_gateway_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in HOST_GATEWAY_CONTRACT_KEYS:
        raw = task.get(key)
        if isinstance(raw, dict):
            return raw
    for key, raw in task.items():
        if not isinstance(raw, dict):
            continue
        token = str(key or "").strip().lower()
        if "gateway" in token and "contract" in token:
            return raw
    return {}


def _resolve_pack_relative_path(pack_path: Path, raw_path: str) -> Path:
    token = str(raw_path or "").strip()
    if not token:
        return Path("")
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    if token.startswith("identity/runtime/"):
        return (pack_path / "runtime" / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (pack_path / token).resolve()
    return (pack_path / token).resolve()


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _is_privilege_escalation_error(exc: Exception) -> bool:
    if isinstance(exc, PermissionError):
        return True
    if isinstance(exc, OSError) and getattr(exc, "errno", None) in {
        errno.EACCES,
        errno.EPERM,
        errno.EROFS,
    }:
        return True
    return False


def _format_privilege_escalation_reason(*, path: Path, scope: str, exc: Exception) -> str:
    safe_scope = str(scope or "").strip() or "unknown_scope"
    safe_path = str(path.expanduser().resolve())
    safe_exc = type(exc).__name__
    return (
        f"{PRIVILEGE_ESCALATION_REASON_PREFIX}:{safe_scope}:path={safe_path}:error={safe_exc}:"
        f"hint={PRIVILEGE_ESCALATION_REMEDIATION_HINT}:error_code={PRIVILEGE_ESCALATION_ERROR_CODE}"
    )


def _read_process_commandline(pid: int) -> str:
    if pid <= 0:
        return ""
    if psutil is not None:
        try:
            proc = psutil.Process(pid)
            tokens = [str(tok or "").strip() for tok in (proc.cmdline() or [])]
            rendered = " ".join(token for token in tokens if token).strip()
            if rendered:
                return rendered
        except Exception:
            pass
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if proc_cmdline.exists():
        try:
            raw = proc_cmdline.read_bytes()
            tokens = [chunk.decode("utf-8", errors="ignore").strip() for chunk in raw.split(b"\x00")]
            return " ".join(token for token in tokens if token).strip()
        except Exception:
            pass
    try:
        proc = subprocess.run(
            ["ps", "-o", "command=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return str(proc.stdout or "").strip()


def _validate_wrapper_parent_attestation(
    *,
    expected_wrapper_path: str,
) -> tuple[bool, list[str], dict[str, Any]]:
    def _resolve_cli_path_token(token: str) -> str:
        raw = str(token or "").strip()
        if not raw:
            return ""
        if "/" not in raw and "\\" not in raw:
            return ""
        try:
            return str(Path(raw).expanduser().resolve())
        except Exception:
            return ""

    def _parent_command_matches_expected_wrapper(parent_cmdline: str, expected_path: Path) -> bool:
        line = str(parent_cmdline or "").strip()
        if not line:
            return False
        try:
            tokens = shlex.split(line)
        except Exception:
            tokens = line.split()
        if not tokens:
            return False

        expected = str(expected_path)

        direct_exec_path = _resolve_cli_path_token(tokens[0])
        if direct_exec_path and direct_exec_path == expected:
            return True

        exe_name = Path(tokens[0]).name.lower()
        if "python" not in exe_name:
            return False

        first_script_token = ""
        for tok in tokens[1:]:
            token = str(tok or "").strip()
            if not token:
                continue
            if token in {"-m", "-c"}:
                return False
            if token.startswith("-"):
                continue
            first_script_token = token
            break
        if not first_script_token:
            return False
        script_path = _resolve_cli_path_token(first_script_token)
        return bool(script_path and script_path == expected)

    errors: list[str] = []
    expected_path = Path(str(expected_wrapper_path or "").strip()).expanduser().resolve()
    parent_pid = int(os.getppid())
    parent_cmdline = _read_process_commandline(parent_pid)
    env_wrapper_path = str(os.environ.get("IDENTITY_PROTOCOL_EGRESS_WRAPPER_PATH", "")).strip()
    details: dict[str, Any] = {
        "egress_wrapper_parent_attestation_ppid": parent_pid,
        "egress_wrapper_parent_attestation_expected_path": str(expected_path)
        if str(expected_wrapper_path or "").strip()
        else "",
        "egress_wrapper_parent_attestation_command_sha256": (
            hashlib.sha256(parent_cmdline.encode("utf-8")).hexdigest() if parent_cmdline else ""
        ),
        "egress_wrapper_parent_attestation_env_path": env_wrapper_path,
    }
    if not str(expected_wrapper_path or "").strip():
        errors.append("egress_wrapper_parent_attestation_expected_path_missing")
    if not env_wrapper_path:
        errors.append("egress_wrapper_parent_attestation_env_path_missing")
    else:
        env_path = Path(env_wrapper_path).expanduser().resolve()
        if env_path != expected_path:
            errors.append("egress_wrapper_parent_attestation_env_path_mismatch")
    if not parent_cmdline:
        errors.append("egress_wrapper_parent_attestation_parent_command_missing")
    elif not _parent_command_matches_expected_wrapper(parent_cmdline, expected_path):
        errors.append("egress_wrapper_parent_attestation_parent_command_mismatch")
    return len(errors) == 0, errors, details


def _consume_egress_nonce(
    *,
    pack_path: Path,
    nonce: str,
    issued_at_epoch: int,
    max_age_seconds: int,
) -> tuple[bool, str]:
    state_path = (pack_path / "runtime" / "state" / EGRESS_GRANT_NONCE_STATE_FILE).resolve()
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            return False, _format_privilege_escalation_reason(
                path=state_path.parent,
                scope="egress_grant_nonce_state_dir_write",
                exc=exc,
            )
        return False, f"egress_grant_nonce_state_dir_write_failed:{exc}"
    state_doc: dict[str, Any] = {"used": {}}
    if state_path.exists():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                state_doc = loaded
        except Exception as exc:
            if _is_privilege_escalation_error(exc):
                return False, _format_privilege_escalation_reason(
                    path=state_path,
                    scope="egress_grant_nonce_state_read",
                    exc=exc,
                )
            state_doc = {"used": {}}
    used = state_doc.get("used")
    if not isinstance(used, dict):
        used = {}

    now_epoch = int(time.time())
    ttl = max(_safe_int(max_age_seconds, default=300), 1) * 4
    stale = [k for k, v in used.items() if now_epoch - _safe_int(v, default=0) > ttl]
    for k in stale:
        used.pop(k, None)

    nonce_key = str(nonce or "").strip()
    if nonce_key in used:
        return False, "egress_grant_nonce_replay_detected"

    used[nonce_key] = int(issued_at_epoch)
    state_doc["used"] = used
    try:
        state_path.write_text(json.dumps(state_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            return False, _format_privilege_escalation_reason(
                path=state_path,
                scope="egress_grant_nonce_state_write",
                exc=exc,
            )
        return False, f"egress_grant_nonce_state_write_failed:{exc}"
    return True, ""


def _validate_egress_grant(
    *,
    grant_json: str,
    grant_signature: str,
    dispatch_secret: str,
    identity_id: str,
    actor_id: str,
    session_id: str,
    run_id: str,
    outlet_channel_id: str,
    body: str,
    max_age_seconds: int,
    pack_path: Path,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not str(grant_json or "").strip():
        return False, ["egress_grant_missing"]
    if not str(grant_signature or "").strip():
        return False, ["egress_grant_signature_missing"]
    if not str(dispatch_secret or "").strip():
        return False, ["egress_grant_secret_missing"]
    try:
        grant = json.loads(str(grant_json).strip())
    except Exception:
        return False, ["egress_grant_invalid_json"]
    if not isinstance(grant, dict):
        return False, ["egress_grant_payload_not_object"]

    required_fields = (
        "schema_version",
        "identity_id",
        "actor_id",
        "session_id",
        "run_id",
        "outlet_channel_id",
        "body_sha256",
        "issued_at_epoch",
        "nonce",
    )
    missing = [field for field in required_fields if field not in grant]
    if missing:
        return False, ["egress_grant_fields_missing:" + ",".join(sorted(missing))]

    canonical = _canonical_json(grant)
    expected_signature = hmac.new(
        str(dispatch_secret).encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(str(grant_signature).strip(), expected_signature):
        errors.append("egress_grant_signature_invalid")

    if str(grant.get("schema_version", "")).strip() != "v1":
        errors.append("egress_grant_schema_version_invalid")
    if str(grant.get("identity_id", "")).strip() != str(identity_id or "").strip():
        errors.append("egress_grant_identity_mismatch")
    if str(grant.get("actor_id", "")).strip() != str(actor_id or "").strip():
        errors.append("egress_grant_actor_mismatch")
    if str(grant.get("session_id", "")).strip() != str(session_id or "").strip():
        errors.append("egress_grant_session_mismatch")
    if str(grant.get("run_id", "")).strip() != str(run_id or "").strip():
        errors.append("egress_grant_run_id_mismatch")
    if str(grant.get("outlet_channel_id", "")).strip() != str(outlet_channel_id or "").strip():
        errors.append("egress_grant_outlet_channel_mismatch")
    body_sha256 = hashlib.sha256(str(body or "").encode("utf-8")).hexdigest()
    if str(grant.get("body_sha256", "")).strip() != body_sha256:
        errors.append("egress_grant_body_sha256_mismatch")

    issued_at_epoch = _safe_int(grant.get("issued_at_epoch"), default=0)
    now_epoch = int(time.time())
    max_age = max(_safe_int(max_age_seconds, default=300), 1)
    if issued_at_epoch <= 0:
        errors.append("egress_grant_issued_at_invalid")
    else:
        if issued_at_epoch > now_epoch + 30:
            errors.append("egress_grant_issued_at_in_future")
        if now_epoch - issued_at_epoch > max_age:
            errors.append("egress_grant_expired")

    nonce = str(grant.get("nonce", "")).strip()
    if len(nonce) < 16:
        errors.append("egress_grant_nonce_too_short")
    if not errors:
        consumed, consume_error = _consume_egress_nonce(
            pack_path=pack_path,
            nonce=nonce,
            issued_at_epoch=issued_at_epoch,
            max_age_seconds=max_age,
        )
        if not consumed:
            errors.append(str(consume_error or "egress_grant_nonce_consume_failed"))
    return len(errors) == 0, errors


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
    ap.add_argument("--run-id", default="")
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
    ap.add_argument("--egress-grant-json", default="")
    ap.add_argument("--egress-grant-signature", default="")
    ap.add_argument("--json-only", action="store_true")
    ap.add_argument(
        "--strict-explicit-context",
        action="store_true",
        help="require explicit --identity-id/--catalog/--actor-id, disable auto context resolution",
    )
    args = ap.parse_args()

    requested_work_layer = str(args.work_layer or "").strip().lower()
    protocol_lane_explicit_context_required = requested_work_layer == "protocol"
    strict_explicit_context_required = bool(args.strict_explicit_context or protocol_lane_explicit_context_required)
    strict_explicit_context_mode = (
        "protocol_lane_enforced"
        if protocol_lane_explicit_context_required
        else ("explicit_flag" if args.strict_explicit_context else "auto")
    )

    try:
        if strict_explicit_context_required:
            missing: list[str] = []
            if not str(args.identity_id or "").strip():
                missing.append("identity-id")
            if not str(args.catalog or "").strip():
                missing.append("catalog")
            if protocol_lane_explicit_context_required and not str(args.repo_catalog or "").strip():
                missing.append("repo-catalog")
            if not str(args.actor_id or "").strip():
                missing.append("actor-id")
            if protocol_lane_explicit_context_required and not str(args.session_id or "").strip():
                missing.append("session-id")
            if missing:
                if protocol_lane_explicit_context_required:
                    raise ValueError(
                        "protocol_work_layer_requires_explicit_context_args:"
                        + ",".join(sorted(set(missing)))
                    )
                raise ValueError(f"missing required explicit context args: {','.join(sorted(set(missing)))}")

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
            "repo_catalog": str(args.repo_catalog or "").strip(),
            "actor_id": str(args.actor_id or "").strip(),
            "session_id": str(args.session_id or "").strip(),
            "requested_work_layer": requested_work_layer,
            "protocol_explicit_context_required": bool(protocol_lane_explicit_context_required),
            "strict_explicit_context_required": bool(strict_explicit_context_required),
            "strict_explicit_context_mode": strict_explicit_context_mode,
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

    run_id = str(args.run_id or "").strip()
    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, identity_id)
        task = _load_json(task_path)
    except Exception as exc:
        payload = {
            "final_emit_guard_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_IDENTITY_RESOLVE,
            "stale_reasons": [f"host_gateway_contract_resolve_failed:{exc}"],
            "identity_id": identity_id,
            "catalog_path": str(catalog_path),
        }
        _emit(payload, json_only=args.json_only)
        return 1

    host_gateway_contract = _resolve_host_gateway_contract(task if isinstance(task, dict) else {})
    host_release_mode = str(host_gateway_contract.get("host_release_mode", "")).strip().lower()
    egress_grant_required = False
    egress_grant_signer_mode = ""
    egress_grant_signer_secret_env = ""
    egress_grant_signing_key_path = ""
    egress_wrapper_parent_attestation_required = False
    egress_wrapper_parent_attestation_status = STATUS_SKIPPED_NOT_REQUIRED
    egress_wrapper_parent_attestation_ppid = int(os.getppid())
    egress_wrapper_parent_attestation_expected_path = ""
    egress_wrapper_parent_attestation_command_sha256 = ""
    if host_release_mode == "wrapper_only":
        egress_wrapper_parent_attestation_required = True
        egress_wrapper_path = _resolve_pack_relative_path(
            pack_path,
            str(host_gateway_contract.get("egress_wrapper_path", "")).strip(),
        )
        egress_wrapper_parent_attestation_expected_path = str(egress_wrapper_path) if egress_wrapper_path else ""
        (
            parent_ok,
            parent_errors,
            parent_details,
        ) = _validate_wrapper_parent_attestation(
            expected_wrapper_path=egress_wrapper_parent_attestation_expected_path,
        )
        egress_wrapper_parent_attestation_ppid = _safe_int(
            parent_details.get("egress_wrapper_parent_attestation_ppid"),
            default=egress_wrapper_parent_attestation_ppid,
        )
        egress_wrapper_parent_attestation_command_sha256 = str(
            parent_details.get("egress_wrapper_parent_attestation_command_sha256", "")
        ).strip()
        egress_wrapper_parent_attestation_status = (
            STATUS_PASS_REQUIRED if parent_ok else STATUS_FAIL_REQUIRED
        )
        if not parent_ok:
            payload = {
                "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_EGRESS_CONTRACT_FAILED,
                "stale_reasons": parent_errors,
                "identity_id": identity_id,
                "catalog_path": str(catalog_path),
                "egress_grant_required": True,
                "egress_wrapper_parent_attestation_required": True,
                "egress_wrapper_parent_attestation_status": egress_wrapper_parent_attestation_status,
                "egress_wrapper_parent_attestation_ppid": egress_wrapper_parent_attestation_ppid,
                "egress_wrapper_parent_attestation_expected_path": egress_wrapper_parent_attestation_expected_path,
                "egress_wrapper_parent_attestation_command_sha256": egress_wrapper_parent_attestation_command_sha256,
            }
            _emit(payload, json_only=args.json_only)
            return 1
        egress_grant_policy = host_gateway_contract.get("egress_grant_policy")
        egress_grant_required = True
        egress_grant_max_age_seconds = 300
        if isinstance(egress_grant_policy, dict):
            egress_grant_required = bool(egress_grant_policy.get("required", True))
            egress_grant_max_age_seconds = max(
                _safe_int(egress_grant_policy.get("max_age_seconds"), default=300),
                1,
            )
            egress_grant_signer_mode = str(egress_grant_policy.get("signer_mode", "")).strip().lower()
            egress_grant_signer_secret_env = str(egress_grant_policy.get("signer_secret_env", "")).strip()
            egress_grant_signing_key_path = str(egress_grant_policy.get("signing_key_path", "")).strip()
        if not egress_grant_signer_mode:
            egress_grant_signer_mode = "runtime_file_secret" if egress_grant_signing_key_path else ""
        dispatch_secret = ""
        if egress_grant_signer_mode == "runtime_env_secret":
            bootstrap_from_key = bool(
                (egress_grant_policy or {}).get("bootstrap_env_secret_from_signing_key_path", True)
            )
            if not egress_grant_signer_secret_env:
                payload = {
                    "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                    "error_code": ERR_EGRESS_CONTRACT_FAILED,
                    "stale_reasons": ["egress_grant_signer_secret_env_missing"],
                    "identity_id": identity_id,
                    "catalog_path": str(catalog_path),
                    "egress_grant_required": bool(egress_grant_required),
                }
                _emit(payload, json_only=args.json_only)
                return 1
            dispatch_secret = str(os.environ.get(egress_grant_signer_secret_env, "")).strip()
            if not dispatch_secret and bootstrap_from_key and egress_grant_signing_key_path:
                signing_key_path = _resolve_pack_relative_path(pack_path, egress_grant_signing_key_path)
                if signing_key_path.exists():
                    dispatch_secret = signing_key_path.read_text(encoding="utf-8", errors="ignore").strip()
                    if dispatch_secret:
                        os.environ[egress_grant_signer_secret_env] = dispatch_secret
            if not dispatch_secret:
                payload = {
                    "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                    "error_code": ERR_EGRESS_CONTRACT_FAILED,
                    "stale_reasons": ["egress_grant_signer_secret_env_unset"],
                    "identity_id": identity_id,
                    "catalog_path": str(catalog_path),
                    "egress_grant_required": bool(egress_grant_required),
                }
                _emit(payload, json_only=args.json_only)
                return 1
        elif egress_grant_signer_mode in {"runtime_file_secret", ""}:
            if not egress_grant_signing_key_path:
                payload = {
                    "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                    "error_code": ERR_EGRESS_CONTRACT_FAILED,
                    "stale_reasons": ["egress_grant_signing_key_path_missing"],
                    "identity_id": identity_id,
                    "catalog_path": str(catalog_path),
                    "egress_grant_required": bool(egress_grant_required),
                }
                _emit(payload, json_only=args.json_only)
                return 1
            signing_key_path = _resolve_pack_relative_path(pack_path, egress_grant_signing_key_path)
            if not signing_key_path.exists():
                payload = {
                    "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                    "error_code": ERR_EGRESS_CONTRACT_FAILED,
                    "stale_reasons": ["egress_grant_signing_key_missing"],
                    "identity_id": identity_id,
                    "catalog_path": str(catalog_path),
                    "egress_grant_required": bool(egress_grant_required),
                }
                _emit(payload, json_only=args.json_only)
                return 1
            dispatch_secret = signing_key_path.read_text(encoding="utf-8", errors="ignore").strip()
            if not dispatch_secret:
                payload = {
                    "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                    "error_code": ERR_EGRESS_CONTRACT_FAILED,
                    "stale_reasons": ["egress_grant_signing_key_empty"],
                    "identity_id": identity_id,
                    "catalog_path": str(catalog_path),
                    "egress_grant_required": bool(egress_grant_required),
                }
                _emit(payload, json_only=args.json_only)
                return 1
        else:
            payload = {
                "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_EGRESS_CONTRACT_FAILED,
                "stale_reasons": ["egress_grant_signer_mode_unsupported"],
                "identity_id": identity_id,
                "catalog_path": str(catalog_path),
                "egress_grant_required": bool(egress_grant_required),
            }
            _emit(payload, json_only=args.json_only)
            return 1
        if egress_grant_required:
            if not run_id:
                payload = {
                    "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                    "error_code": ERR_EGRESS_CONTRACT_FAILED,
                    "stale_reasons": ["egress_grant_run_id_missing"],
                    "identity_id": identity_id,
                    "catalog_path": str(catalog_path),
                    "egress_grant_required": True,
                }
                _emit(payload, json_only=args.json_only)
                return 1
            grant_ok, grant_errors = _validate_egress_grant(
                grant_json=str(args.egress_grant_json or "").strip(),
                grant_signature=str(args.egress_grant_signature or "").strip(),
                dispatch_secret=dispatch_secret,
                identity_id=identity_id,
                actor_id=actor_id,
                session_id=str(args.session_id or "").strip(),
                run_id=run_id,
                outlet_channel_id=outlet_channel_id,
                body=body,
                max_age_seconds=egress_grant_max_age_seconds,
                pack_path=pack_path,
            )
            if not grant_ok:
                payload = {
                    "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                    "error_code": ERR_EGRESS_CONTRACT_FAILED,
                    "stale_reasons": grant_errors,
                    "identity_id": identity_id,
                    "catalog_path": str(catalog_path),
                    "egress_grant_required": True,
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
        "run_id": run_id,
        "catalog_resolution_mode": catalog_resolution_mode,
        "repo_catalog_resolution_mode": repo_catalog_resolution_mode,
        "identity_resolution_mode": identity_resolution_mode,
        "actor_resolution_mode": actor_resolution_mode,
        "requested_work_layer": requested_work_layer,
        "protocol_explicit_context_required": bool(protocol_lane_explicit_context_required),
        "strict_explicit_context_required": bool(strict_explicit_context_required),
        "strict_explicit_context_mode": strict_explicit_context_mode,
        "strict_explicit_context_status": (
            STATUS_PASS_REQUIRED if strict_explicit_context_required else STATUS_SKIPPED_NOT_REQUIRED
        ),
        "body_mode": body_mode,
        "send_time_gate_status": send_time_status,
        "send_time_error_code": str(compose_payload.get("send_time_error_code", "")).strip(),
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
        "egress_grant_required": bool(egress_grant_required),
        "egress_grant_signer_mode": egress_grant_signer_mode,
        "egress_grant_signer_secret_env": egress_grant_signer_secret_env,
        "egress_wrapper_parent_attestation_required": bool(egress_wrapper_parent_attestation_required),
        "egress_wrapper_parent_attestation_status": egress_wrapper_parent_attestation_status,
        "egress_wrapper_parent_attestation_ppid": egress_wrapper_parent_attestation_ppid,
        "egress_wrapper_parent_attestation_expected_path": egress_wrapper_parent_attestation_expected_path,
        "egress_wrapper_parent_attestation_command_sha256": egress_wrapper_parent_attestation_command_sha256,
        "quoted_identity_context_detected": bool(compose_payload.get("quoted_identity_context_detected", False)),
        "quoted_identity_context_line_count": int(compose_payload.get("quoted_identity_context_line_count", 0) or 0),
        "quoted_identity_context_ids": list(compose_payload.get("quoted_identity_context_ids") or []),
        "quoted_identity_context_foreign_detected": bool(
            compose_payload.get("quoted_identity_context_foreign_detected", False)
        ),
        "quoted_identity_context_foreign_ids": list(
            compose_payload.get("quoted_identity_context_foreign_ids") or []
        ),
        "quoted_identity_context_guard_status": str(
            compose_payload.get("quoted_identity_context_guard_status", "")
        ).strip(),
        "quoted_identity_context_binding_effect": str(
            compose_payload.get("quoted_identity_context_binding_effect", "")
        ).strip(),
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
