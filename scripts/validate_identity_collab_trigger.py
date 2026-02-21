#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REQUIRED_BLOCKERS = {
    "login_required",
    "captcha_required",
    "session_expired",
    "manual_verification_required",
}

REQUIRED_TAXONOMY_FIELDS = {
    "blocker_type",
    "source",
    "detected_at",
    "requires_human_collab",
    "next_action",
}

REQUIRED_RECEIPT_FIELDS = {
    "event_id",
    "blocker_type",
    "notified_at",
    "channel",
    "dedupe_key",
    "status",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def _resolve_current_task(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")

    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p

    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy

    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _parse_iso_dt(value: str) -> datetime:
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iter_logs(pattern: str, explicit_file: str) -> list[Path]:
    if explicit_file:
        p = Path(explicit_file)
        return [p] if p.exists() else []
    return sorted(Path(".").glob(pattern))


def _validate_log(
    p: Path,
    *,
    identity_id: str,
    task_id: str,
    max_log_age_days: int,
    notify_channel: str,
    require_receipt: bool,
) -> tuple[int, list[str]]:
    rc = 0
    logs: list[str] = []
    try:
        rec = _load_json(p)
    except Exception as e:
        return 1, [f"[FAIL] invalid collaboration log {p}: {e}"]

    if str(rec.get("identity_id") or "") != identity_id:
        logs.append(f"[FAIL] {p} identity_id mismatch: expected={identity_id}, got={rec.get('identity_id')}")
        rc = 1

    if str(rec.get("task_id") or "") != task_id:
        logs.append(f"[FAIL] {p} task_id mismatch: expected={task_id}, got={rec.get('task_id')}")
        rc = 1

    blocker = str(rec.get("blocker_type") or "")
    if blocker not in REQUIRED_BLOCKERS:
        logs.append(f"[FAIL] {p} blocker_type must be one of {sorted(REQUIRED_BLOCKERS)}")
        rc = 1

    if rec.get("requires_human_collab") is not True:
        logs.append(f"[FAIL] {p} requires_human_collab must be true")
        rc = 1

    detected_at = str(rec.get("detected_at") or "")
    notified_at = str(rec.get("notified_at") or "")
    try:
        dt_detect = _parse_iso_dt(detected_at)
        dt_notify = _parse_iso_dt(notified_at)
        delay = (dt_notify - dt_detect).total_seconds()
        if delay < 0:
            logs.append(f"[FAIL] {p} notified_at earlier than detected_at")
            rc = 1
        age_days = (datetime.now(timezone.utc) - dt_notify).total_seconds() / 86400.0
        if max_log_age_days > 0 and age_days > max_log_age_days:
            logs.append(f"[FAIL] {p} notification log too old: age_days={age_days:.1f}, max={max_log_age_days}")
            rc = 1
    except Exception as e:
        logs.append(f"[FAIL] {p} invalid detected/notified timestamp: {e}")
        rc = 1

    if str(rec.get("notify_channel") or "") != notify_channel:
        logs.append(
            f"[FAIL] {p} notify_channel mismatch: expected={notify_channel}, got={rec.get('notify_channel')}"
        )
        rc = 1

    dedupe_key = str(rec.get("dedupe_key") or "").strip()
    if not dedupe_key:
        logs.append(f"[FAIL] {p} dedupe_key missing")
        rc = 1

    if rec.get("state_change_bypass_dedupe") is not True:
        logs.append(f"[FAIL] {p} state_change_bypass_dedupe must be true")
        rc = 1

    if require_receipt:
        receipt = rec.get("chat_receipt") or {}
        if not isinstance(receipt, dict):
            logs.append(f"[FAIL] {p} chat_receipt must be object")
            rc = 1
        else:
            if receipt.get("emitted") is not True:
                logs.append(f"[FAIL] {p} chat_receipt.emitted must be true")
                rc = 1
            missing = [k for k in REQUIRED_RECEIPT_FIELDS if k not in receipt]
            if missing:
                logs.append(f"[FAIL] {p} chat_receipt missing fields: {missing}")
                rc = 1

    if rc == 0:
        logs.append(f"[OK] {p} collaboration log passed")
    return rc, logs


def _run_self_test(sample_root: Path) -> int:
    pos = sorted((sample_root / "positive").glob("*.json"))
    neg = sorted((sample_root / "negative").glob("*.json"))
    if not pos or not neg:
        print(f"[FAIL] self-test requires positive and negative samples under {sample_root}")
        return 1

    rc = 0
    for p in pos:
        irc, logs = _validate_log(
            p,
            identity_id="store-manager",
            task_id="store_manager_20260218_role_os_bootstrap",
            max_log_age_days=0,
            notify_channel="ops-notification-router",
            require_receipt=True,
        )
        for ln in logs:
            print(ln)
        if irc != 0:
            print(f"[FAIL] positive sample should pass: {p}")
            rc = 1

    for p in neg:
        irc, logs = _validate_log(
            p,
            identity_id="store-manager",
            task_id="store_manager_20260218_role_os_bootstrap",
            max_log_age_days=0,
            notify_channel="ops-notification-router",
            require_receipt=True,
        )
        for ln in logs:
            print(ln)
        if irc == 0:
            print(f"[FAIL] negative sample should fail: {p}")
            rc = 1

    if rc == 0:
        print("[OK] collaboration trigger self-test passed")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity collaboration trigger contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--file", default="", help="validate explicit collaboration log file")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    task = _load_json(task_path)

    gates = task.get("gates") or {}
    if gates.get("collaboration_trigger_gate") != "required":
        print("[FAIL] gates.collaboration_trigger_gate must be required")
        return 1
    print("[OK] gates.collaboration_trigger_gate=required")

    taxonomy = task.get("blocker_taxonomy_contract") or {}
    if not isinstance(taxonomy, dict) or not taxonomy:
        print("[FAIL] blocker_taxonomy_contract missing")
        return 1

    if taxonomy.get("required") is not True:
        print("[FAIL] blocker_taxonomy_contract.required must be true")
        return 1

    blockers = set(taxonomy.get("required_blocker_types") or [])
    if not REQUIRED_BLOCKERS.issubset(blockers):
        print(f"[FAIL] blocker_taxonomy_contract.required_blocker_types missing: {sorted(REQUIRED_BLOCKERS - blockers)}")
        return 1
    print("[OK] blocker taxonomy covers required classes")

    tax_fields = set(taxonomy.get("blocker_classification_required_fields") or [])
    if not REQUIRED_TAXONOMY_FIELDS.issubset(tax_fields):
        print(
            "[FAIL] blocker_taxonomy_contract.blocker_classification_required_fields missing: "
            f"{sorted(REQUIRED_TAXONOMY_FIELDS - tax_fields)}"
        )
        return 1
    print("[OK] blocker taxonomy required classification fields complete")

    contract = task.get("collaboration_trigger_contract") or {}
    if not isinstance(contract, dict) or not contract:
        print("[FAIL] collaboration_trigger_contract missing")
        return 1

    mandatory_fields = [
        "hard_rule",
        "trigger_conditions",
        "notify_policy",
        "notify_timing",
        "notify_channel",
        "dedupe_window_hours",
        "state_change_bypass_dedupe",
        "must_emit_receipt_in_chat",
    ]
    miss = [k for k in mandatory_fields if k not in contract]
    if miss:
        print(f"[FAIL] collaboration_trigger_contract missing fields: {miss}")
        return 1

    trig = set(contract.get("trigger_conditions") or [])
    if not REQUIRED_BLOCKERS.issubset(trig):
        print(f"[FAIL] collaboration_trigger_contract.trigger_conditions missing: {sorted(REQUIRED_BLOCKERS - trig)}")
        return 1

    policy = str(contract.get("notify_policy") or "").strip()
    if not policy:
        print("[FAIL] collaboration_trigger_contract.notify_policy must be non-empty")
        return 1
    timing = str(contract.get("notify_timing") or "").strip().lower()
    if timing != "immediate":
        print(f"[FAIL] collaboration_trigger_contract.notify_timing must be immediate, got={timing}")
        return 1
    print(f"[OK] collaboration notify policy={policy}, timing=immediate")

    channel = str(contract.get("notify_channel") or "").strip()
    if channel != "ops-notification-router":
        print(f"[FAIL] collaboration_trigger_contract.notify_channel must be ops-notification-router, got={channel}")
        return 1

    try:
        dedupe_hours = int(contract.get("dedupe_window_hours"))
    except Exception:
        print("[FAIL] collaboration_trigger_contract.dedupe_window_hours must be integer")
        return 1
    if dedupe_hours <= 0:
        print("[FAIL] collaboration_trigger_contract.dedupe_window_hours must be > 0")
        return 1

    if contract.get("state_change_bypass_dedupe") is not True:
        print("[FAIL] collaboration_trigger_contract.state_change_bypass_dedupe must be true")
        return 1

    if contract.get("must_emit_receipt_in_chat") is not True:
        print("[FAIL] collaboration_trigger_contract.must_emit_receipt_in_chat must be true")
        return 1

    receipt_fields = set(contract.get("receipt_required_fields") or [])
    if not REQUIRED_RECEIPT_FIELDS.issubset(receipt_fields):
        print(
            "[FAIL] collaboration_trigger_contract.receipt_required_fields missing: "
            f"{sorted(REQUIRED_RECEIPT_FIELDS - receipt_fields)}"
        )
        return 1

    pattern = str(contract.get("evidence_log_path_pattern") or "")
    if not pattern and not args.file:
        print("[FAIL] collaboration_trigger_contract.evidence_log_path_pattern missing")
        return 1

    files = _iter_logs(pattern, args.file)
    minimum = int(contract.get("minimum_evidence_logs_required") or 1)
    if len(files) < minimum:
        print(f"[FAIL] collaboration evidence logs insufficient: found={len(files)}, required={minimum}")
        return 1

    task_id = str(task.get("task_id") or "")
    max_age_days = int(contract.get("max_log_age_days") or 7)

    rc = 0
    for p in files:
        irc, logs = _validate_log(
            p,
            identity_id=args.identity_id,
            task_id=task_id,
            max_log_age_days=max_age_days,
            notify_channel=channel,
            require_receipt=bool(contract.get("must_emit_receipt_in_chat", True)),
        )
        for ln in logs:
            print(ln)
        rc = max(rc, irc)

    if args.self_test:
        sample_root = Path("identity/runtime/examples/collaboration-trigger")
        rc = max(rc, _run_self_test(sample_root))

    if rc == 0:
        print("validate_identity_collab_trigger PASSED")
    else:
        print("validate_identity_collab_trigger FAILED")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
