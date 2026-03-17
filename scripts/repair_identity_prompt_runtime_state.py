#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import latest_identity_upgrade_report, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json_safe(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair prompt runtime-state artifact and prompt hash fields in latest report.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 2

    try:
        pack_path, _task_path = resolve_pack_and_task(catalog, args.identity_id)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prompt_path = (pack_path / "IDENTITY_PROMPT.md").resolve()
    runtime_state_path = (pack_path / "runtime" / "state" / "prompt_contract.json").resolve()
    explicit_report = str(args.report or "").strip()
    report_path: Path | None
    if explicit_report:
        candidate = Path(explicit_report).expanduser().resolve()
        report_path = candidate if candidate.exists() else None
    else:
        report_path = latest_identity_upgrade_report(args.identity_id, pack_path)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog),
        "resolved_pack_path": str(pack_path),
        "prompt_runtime_state_repair_status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "prompt_path": str(prompt_path),
        "runtime_state_artifact_path": str(runtime_state_path),
        "runtime_state_artifact_hash_before": "",
        "runtime_state_artifact_hash_after": "",
        "prompt_hash": "",
        "report_selected_path": str(report_path) if report_path is not None else "",
        "report_hash_before": "",
        "report_hash_after": "",
        "runtime_state_updated": False,
        "report_updated": False,
        "stale_reasons": [],
    }

    if not prompt_path.exists():
        payload["prompt_runtime_state_repair_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = "IP-PROMPT-REPAIR-001"
        payload["stale_reasons"] = ["identity_prompt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    prompt_hash = _sha256(prompt_path)
    prompt_bytes = int(prompt_path.stat().st_size)
    payload["prompt_hash"] = prompt_hash

    runtime_state_before = _load_json_safe(runtime_state_path)
    if runtime_state_path.exists():
        payload["runtime_state_artifact_hash_before"] = _sha256(runtime_state_path)
    runtime_state_after = {
        "schema": "prompt_runtime_state_v1",
        "identity_prompt_path": str(prompt_path),
        "prompt_policy_hash": prompt_hash,
        "last_upgrade_run_id": "",
        "last_upgrade_mode": "repair",
        "last_upgrade_at": now,
        "last_trigger_reasons": ["prompt_runtime_state_hash_repair"],
    }

    report_doc: dict[str, Any] = {}
    if report_path is not None and report_path.exists():
        report_doc = _load_json_safe(report_path)
        runtime_state_after["last_upgrade_run_id"] = str(report_doc.get("run_id", "")).strip()
        runtime_state_after["last_upgrade_mode"] = str(report_doc.get("mode", "")).strip() or "repair"
        payload["report_hash_before"] = _sha256(report_path)
    if not runtime_state_after["last_upgrade_run_id"]:
        runtime_state_after["last_upgrade_run_id"] = f"prompt-runtime-repair-{int(datetime.now(timezone.utc).timestamp())}"

    runtime_state_changed = runtime_state_before != runtime_state_after
    if args.apply and runtime_state_changed:
        _write_json(runtime_state_path, runtime_state_after)
        payload["runtime_state_updated"] = True
    if runtime_state_path.exists():
        payload["runtime_state_artifact_hash_after"] = _sha256(runtime_state_path)

    if report_path is None or not report_path.exists():
        payload["stale_reasons"].append("upgrade_report_missing_skip_report_patch")
        payload["report_hash_after"] = ""
        if runtime_state_changed and not args.apply:
            payload["stale_reasons"].append("runtime_state_patch_pending_apply")
        _emit(payload, json_only=args.json_only)
        return 0

    report_after = dict(report_doc)
    report_after["identity_prompt_path"] = str(prompt_path)
    report_after["identity_prompt_sha256"] = prompt_hash
    report_after["identity_prompt_bytes"] = prompt_bytes
    report_after["identity_prompt_activated_at"] = str(
        report_after.get("identity_prompt_activated_at", "") or now
    ).strip() or now
    report_after["identity_prompt_hash_after"] = prompt_hash
    report_after["prompt_policy_hash"] = prompt_hash
    report_after["identity_prompt_status"] = "ACTIVATED"
    if not str(report_after.get("identity_prompt_hash_before", "")).strip():
        report_after["identity_prompt_hash_before"] = prompt_hash
    report_after["runtime_state_artifact_path"] = str(runtime_state_path)
    report_after["runtime_state_artifact_hash"] = payload["runtime_state_artifact_hash_after"]
    report_after["prompt_runtime_state_binding_status"] = STATUS_PASS_REQUIRED
    prompt_text = prompt_path.read_text(encoding="utf-8", errors="ignore")
    if "<!-- IDENTITY_PROMPT_RUNTIME_CONTRACT:BEGIN -->" in prompt_text:
        report_after["prompt_runtime_state_externalization_status"] = STATUS_FAIL_REQUIRED
        report_after["prompt_runtime_state_externalization_error_code"] = "IP-PROMPT-STATE-001"
    else:
        report_after["prompt_runtime_state_externalization_status"] = STATUS_PASS_REQUIRED
        report_after["prompt_runtime_state_externalization_error_code"] = ""

    report_changed = report_after != report_doc
    if args.apply and report_changed:
        _write_json(report_path, report_after)
        payload["report_updated"] = True
    payload["report_hash_after"] = _sha256(report_path)

    if (runtime_state_changed or report_changed) and not args.apply:
        payload["prompt_runtime_state_repair_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = "IP-PROMPT-REPAIR-DRYRUN"
        payload["stale_reasons"].append("apply_required_for_prompt_runtime_state_repair")
        _emit(payload, json_only=args.json_only)
        return 1

    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
