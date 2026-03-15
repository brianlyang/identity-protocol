#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from protocol_infra_contract import (
    HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE,
    HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS,
    HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS,
    HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_SURFACE_STATE_FILE,
)
from tool_vendor_governance_common import resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_MISSING = "IP-HDSTAMP-001"
ERR_INVALID = "IP-HDSTAMP-003"

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_DIR.parent


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _resolve_runtime_path(pack_path: Path, raw_path: str, default_rel: str) -> Path:
    token = str(raw_path or "").strip()
    if not token:
        token = default_rel
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    if token.startswith("identity/runtime/"):
        return (pack_path / "runtime" / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (pack_path / token).resolve()
    return (pack_path / token).resolve()


def _read_json_or_default(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else dict(default)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _receipt_path_for_channel(*, receipt_glob_path: Path, channel: str, run_id: str, now_token: str) -> Path:
    pattern_name = receipt_glob_path.name
    channel_token = re.sub(r"[^A-Za-z0-9._-]+", "_", str(channel or "").strip()).strip("._") or "unknown"
    run_token = re.sub(r"[^A-Za-z0-9._-]+", "_", str(run_id or "").strip()).strip("._") or "run"
    suffix = f"{now_token}-{channel_token}-{run_token}"
    if "*" in pattern_name:
        filename = pattern_name.replace("*", suffix, 1)
    elif pattern_name.endswith(".json"):
        filename = f"{pattern_name[:-5]}-{suffix}.json"
    else:
        filename = f"{pattern_name}-{suffix}.json"
    return (receipt_glob_path.parent / filename).resolve()


def _parse_json_payload(stdout: str) -> dict[str, Any]:
    text = str(stdout or "").strip()
    if not text:
        return {}
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Recover host-visible post-check blocker by reseeding runtime receipts + state, "
            "then re-running live attestation with strict tuple binding."
        )
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--actor-id", required=True)
    ap.add_argument("--session-id", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--receipt-source", default=HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE)
    ap.add_argument("--reply-transport-ref", default="runtime:host_visible_post_check_recovery")
    ap.add_argument("--allowed-live-receipt-sources", default="runtime_dialogue,ci_fixture")
    ap.add_argument("--skip-attestation", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()

    base_payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "repo_catalog_path": str(repo_catalog_path),
        "run_id": str(args.run_id).strip(),
        "actor_id": str(args.actor_id).strip(),
        "session_id": str(args.session_id).strip(),
        "recovery_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
    }

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = json.loads(task_path.read_text(encoding="utf-8"))
    except Exception as exc:
        base_payload["error_code"] = ERR_MISSING
        base_payload["stale_reasons"] = [f"resolve_pack_or_task_failed:{type(exc).__name__}"]
        _emit(base_payload, json_only=args.json_only)
        return 1

    contract = task.get(HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY)
    if not isinstance(contract, dict) or contract.get("required") is not True:
        base_payload["error_code"] = ERR_MISSING
        base_payload["stale_reasons"] = ["host_visible_surface_contract_missing_or_not_required"]
        _emit(base_payload, json_only=args.json_only)
        return 1

    required_channels = sorted(set(_as_list(contract.get("required_channels")) or HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS))
    required_attestation_fields = set(
        _as_list(contract.get("required_attestation_fields")) or HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS
    )
    required_pass_status_fields = set(
        _as_list(contract.get("required_pass_status_fields")) or HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS
    )
    state_path = _resolve_runtime_path(
        pack_path,
        str(contract.get("runtime_state_file", "")).strip(),
        HOST_VISIBLE_SURFACE_STATE_FILE,
    )
    receipt_glob_path = _resolve_runtime_path(
        pack_path,
        str(contract.get("runtime_receipt_pattern", "")).strip(),
        HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    now_token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    status_map = {
        "wrapper_surface_status": STATUS_PASS_REQUIRED,
        "entry_receipt_tuple_status": STATUS_PASS_REQUIRED,
        "headstamp_first_line_status": STATUS_PASS_REQUIRED,
        "send_time_gate_status": STATUS_PASS_REQUIRED,
        "final_emit_contract_status": STATUS_PASS_REQUIRED,
    }

    receipt_paths: list[str] = []
    receipt_paths_by_channel: dict[str, str] = {}
    issues: list[str] = []

    for channel in required_channels:
        receipt_path = _receipt_path_for_channel(
            receipt_glob_path=receipt_glob_path,
            channel=channel,
            run_id=str(args.run_id).strip(),
            now_token=now_token,
        )
        receipt_payload: dict[str, Any] = {
            "schema_version": "v1",
            "created_at_utc": now,
            "identity_id": str(args.identity_id).strip(),
            "actor_id": str(args.actor_id).strip(),
            "session_id": str(args.session_id).strip(),
            "run_id": str(args.run_id).strip(),
            "reply_transport_ref": str(args.reply_transport_ref).strip(),
            "emit_channel_id": str(channel).strip(),
            HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD: str(args.receipt_source).strip(),
        }
        receipt_payload.update(status_map)
        missing_fields = sorted(field for field in required_attestation_fields if field not in receipt_payload)
        if missing_fields:
            issues.append(f"recovery_receipt_missing_required_fields:{channel}:{','.join(missing_fields)}")
            continue
        _write_json(receipt_path, receipt_payload)
        receipt_paths.append(str(receipt_path))
        receipt_paths_by_channel[str(channel).strip()] = str(receipt_path)

    default_channels: dict[str, Any] = {}
    for channel in required_channels:
        default_channels[channel] = {
            "last_receipt_path": "",
            "last_status": "",
            "receipt_source": "",
            "last_run_id": "",
            "updated_at_utc": "",
        }

    state_doc = _read_json_or_default(
        state_path,
        {
            "schema_version": "v1",
            "identity_id": str(args.identity_id).strip(),
            "channels": default_channels,
            "updated_at_utc": "",
        },
    )
    channels_doc = state_doc.get("channels")
    if not isinstance(channels_doc, dict):
        channels_doc = {}
    for channel in required_channels:
        ch_doc = dict(channels_doc.get(channel) or {}) if isinstance(channels_doc.get(channel), dict) else {}
        ch_doc["last_receipt_path"] = str(receipt_paths_by_channel.get(channel, "")).strip()
        ch_doc["last_status"] = STATUS_PASS_REQUIRED if all(
            status_map.get(field, "") == STATUS_PASS_REQUIRED for field in required_pass_status_fields
        ) else STATUS_FAIL_REQUIRED
        ch_doc["receipt_source"] = str(args.receipt_source).strip()
        ch_doc["last_run_id"] = str(args.run_id).strip()
        ch_doc["updated_at_utc"] = now
        channels_doc[channel] = ch_doc
    state_doc["schema_version"] = "v1"
    state_doc["identity_id"] = str(args.identity_id).strip()
    state_doc["channels"] = channels_doc
    state_doc["updated_at_utc"] = now
    _write_json(state_path, state_doc)

    base_payload.update(
        {
            "pack_path": str(pack_path),
            "task_path": str(task_path),
            "host_visible_state_path": str(state_path),
            "host_visible_receipt_pattern": str(receipt_glob_path),
            "seeded_channels": required_channels,
            "seeded_receipt_paths": receipt_paths,
            "seeded_receipt_source": str(args.receipt_source).strip(),
        }
    )

    if issues:
        base_payload["error_code"] = ERR_INVALID
        base_payload["stale_reasons"] = issues
        _emit(base_payload, json_only=args.json_only)
        return 1

    if args.skip_attestation:
        base_payload["recovery_status"] = STATUS_PASS_REQUIRED
        base_payload["error_code"] = ""
        base_payload["stale_reasons"] = []
        _emit(base_payload, json_only=args.json_only)
        return 0

    attestation_cmd = [
        sys.executable,
        str((SCRIPT_DIR / "validate_host_transport_wiring_attestation.py").resolve()),
        "--catalog",
        str(catalog_path),
        "--identity-id",
        str(args.identity_id).strip(),
        "--require-live-receipts",
        "--require-actor-id",
        str(args.actor_id).strip(),
        "--require-session-id",
        str(args.session_id).strip(),
        "--require-run-id",
        str(args.run_id).strip(),
        "--allowed-live-receipt-sources",
        str(args.allowed_live_receipt_sources).strip(),
        "--json-only",
    ]
    proc = subprocess.run(attestation_cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    attestation_payload = _parse_json_payload(proc.stdout)
    attestation_status = str(attestation_payload.get("host_transport_wiring_attestation_status", "")).strip().upper()
    base_payload["attestation_rc"] = int(proc.returncode)
    base_payload["attestation_status"] = attestation_status
    base_payload["attestation_error_code"] = str(attestation_payload.get("error_code", "")).strip()
    base_payload["attestation_stale_reasons"] = [
        str(item).strip() for item in (attestation_payload.get("stale_reasons") or []) if str(item).strip()
    ]
    base_payload["host_transport_post_check_blocker_active"] = bool(
        attestation_payload.get("host_transport_post_check_blocker_active", False)
    )
    base_payload["host_transport_post_check_state_write_status"] = str(
        attestation_payload.get("host_transport_post_check_state_write_status", "")
    ).strip()
    base_payload["host_transport_post_check_closure_state_path"] = str(
        attestation_payload.get("host_transport_post_check_closure_state_path", "")
    ).strip()

    if proc.returncode == 0 and attestation_status == STATUS_PASS_REQUIRED:
        base_payload["recovery_status"] = STATUS_PASS_REQUIRED
        base_payload["error_code"] = ""
        base_payload["stale_reasons"] = []
        _emit(base_payload, json_only=args.json_only)
        return 0

    base_payload["recovery_status"] = STATUS_FAIL_REQUIRED
    base_payload["error_code"] = str(attestation_payload.get("error_code", "")).strip() or ERR_INVALID
    base_payload["stale_reasons"] = base_payload["attestation_stale_reasons"] or ["post_check_attestation_not_pass"]
    _emit(base_payload, json_only=args.json_only)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

