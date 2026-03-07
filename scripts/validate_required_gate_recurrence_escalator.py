#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from runtime_temp_path_common import runtime_temp_file

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_ESCALATION = "IP-GATE-ENTRY-004"
ERR_INPUT = "IP-GATE-ENTRY-001"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso_ts(raw: str) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _error_family(error_code: str) -> str:
    code = str(error_code or "").strip().upper()
    if not code:
        return ""
    parts = code.split("-")
    if len(parts) >= 2 and parts[-1].isdigit():
        parts[-1] = "*"
        return "-".join(parts)
    return code


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("payload is not object")
    return data


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"events": [], "l2_occurrences": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            events = data.get("events") if isinstance(data.get("events"), list) else []
            l2 = data.get("l2_occurrences") if isinstance(data.get("l2_occurrences"), list) else []
            return {"events": events, "l2_occurrences": l2}
    except Exception:
        pass
    return {"events": [], "l2_occurrences": []}


def _save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _collect_new_events(*, receipt: dict[str, Any], identity_id: str, surface: str, ts_iso: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in list(receipt.get("results") or []):
        if not isinstance(row, dict):
            continue
        status = str(row.get("status", "")).strip().upper()
        if status != STATUS_FAIL_REQUIRED:
            continue
        error_code = str(row.get("error_code", "")).strip().upper()
        if not error_code:
            continue
        family = _error_family(error_code)
        if not family:
            continue
        out.append(
            {
                "ts": ts_iso,
                "identity_id": identity_id,
                "surface": surface,
                "target_name": str(row.get("target_name", "")).strip(),
                "error_code": error_code,
                "error_family": family,
                "run_id_binding": str(receipt.get("run_id_binding", "")).strip(),
            }
        )
    return out


def _dedupe_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = "|".join(
            [
                str(row.get("ts", "")),
                str(row.get("identity_id", "")),
                str(row.get("surface", "")),
                str(row.get("target_name", "")),
                str(row.get("error_code", "")),
                str(row.get("run_id_binding", "")),
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _window_metrics(events: list[dict[str, Any]], *, now_dt: datetime, window: timedelta) -> tuple[int, int]:
    start = now_dt - window
    subset = []
    for row in events:
        dt = _parse_iso_ts(row.get("ts", ""))
        if dt is None:
            continue
        if dt >= start:
            subset.append(row)
    surfaces = {str(row.get("surface", "")).strip() for row in subset if str(row.get("surface", "")).strip()}
    return len(subset), len(surfaces)


def main() -> int:
    parser = argparse.ArgumentParser(description="Quantized recurrence escalator for required-gate failures.")
    parser.add_argument("--identity-id", required=True)
    parser.add_argument("--surface", required=True)
    parser.add_argument("--operation", default="validate")
    parser.add_argument("--receipt", required=True, help="bundle runner receipt JSON path")
    parser.add_argument("--state-path", default="")
    parser.add_argument("--window-l1-hours", type=int, default=24)
    parser.add_argument("--window-l2-hours", type=int, default=72)
    parser.add_argument("--window-l3-hours", type=int, default=168)
    parser.add_argument("--threshold-l1", type=int, default=2)
    parser.add_argument("--threshold-l2", type=int, default=3)
    parser.add_argument("--threshold-l3", type=int, default=5)
    parser.add_argument("--enforce-blocking", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    receipt_path = Path(args.receipt).expanduser().resolve()
    if not receipt_path.exists():
        payload = {
            "required_gate_recurrence_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_INPUT,
            "error_family": "",
            "escalation_level": "L0",
            "receipt_path": str(receipt_path),
            "state_path": "",
            "stale_reasons": ["receipt_missing"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    try:
        receipt = _load_json(receipt_path)
    except Exception as exc:
        payload = {
            "required_gate_recurrence_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_INPUT,
            "error_family": "",
            "escalation_level": "L0",
            "receipt_path": str(receipt_path),
            "state_path": "",
            "stale_reasons": [f"receipt_invalid:{exc}"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    state_path = (
        Path(args.state_path).expanduser().resolve()
        if str(args.state_path or "").strip()
        else runtime_temp_file(
            channel="required-gate-recurrence",
            operation=str(args.operation),
            identity_id=str(args.identity_id),
            run_token="",
            stem=f"required-gate-recurrence-{args.identity_id}",
            ext="json",
        )
    )

    state = _load_state(state_path)
    now_dt = _now_utc()
    now_iso = _to_iso_z(now_dt)

    historical_events = [row for row in state.get("events", []) if isinstance(row, dict)]
    new_events = _collect_new_events(
        receipt=receipt,
        identity_id=str(args.identity_id),
        surface=str(args.surface),
        ts_iso=now_iso,
    )
    merged_events = _dedupe_events(historical_events + new_events)

    keep_start = now_dt - timedelta(hours=max(1, int(args.window_l3_hours)))
    kept_events: list[dict[str, Any]] = []
    for row in merged_events:
        dt = _parse_iso_ts(row.get("ts", ""))
        if dt is None:
            continue
        if dt >= keep_start:
            kept_events.append(row)

    families = sorted({str(row.get("error_family", "")).strip() for row in kept_events if str(row.get("error_family", "")).strip()})

    family_metrics: list[dict[str, Any]] = []
    l1_families: list[str] = []
    l2_families: list[str] = []
    l3_families: list[str] = []

    l2_occurrences = [row for row in state.get("l2_occurrences", []) if isinstance(row, dict)]
    updated_l2_occurrences: list[dict[str, Any]] = []

    for family in families:
        family_events = [row for row in kept_events if str(row.get("error_family", "")).strip() == family]
        c24, s24 = _window_metrics(family_events, now_dt=now_dt, window=timedelta(hours=int(args.window_l1_hours)))
        c72, s72 = _window_metrics(family_events, now_dt=now_dt, window=timedelta(hours=int(args.window_l2_hours)))
        c7d, s7d = _window_metrics(family_events, now_dt=now_dt, window=timedelta(hours=int(args.window_l3_hours)))

        l1_hit = c24 >= int(args.threshold_l1) and s24 >= 2
        l2_hit = c72 >= int(args.threshold_l2) and s72 >= 2

        prev_l2_in_window = False
        for item in l2_occurrences:
            if str(item.get("error_family", "")).strip() != family:
                continue
            dt = _parse_iso_ts(item.get("ts", ""))
            if dt is None:
                continue
            if dt >= keep_start:
                prev_l2_in_window = True
                updated_l2_occurrences.append(item)

        second_l2 = l2_hit and prev_l2_in_window
        l3_hit = (c7d >= int(args.threshold_l3) and s7d >= 2) or second_l2

        if l2_hit:
            updated_l2_occurrences.append({"ts": now_iso, "error_family": family, "surface": str(args.surface)})

        if l1_hit:
            l1_families.append(family)
        if l2_hit:
            l2_families.append(family)
        if l3_hit:
            l3_families.append(family)

        family_metrics.append(
            {
                "error_family": family,
                "count_24h": c24,
                "surface_count_24h": s24,
                "count_72h": c72,
                "surface_count_72h": s72,
                "count_l3_window": c7d,
                "surface_count_l3_window": s7d,
                "l1_hit": l1_hit,
                "l2_hit": l2_hit,
                "l3_hit": l3_hit,
                "second_l2": second_l2,
            }
        )

    updated_l2_occurrences = _dedupe_events(updated_l2_occurrences)
    state_out = {
        "events": kept_events,
        "l2_occurrences": [
            row
            for row in updated_l2_occurrences
            if (_parse_iso_ts(row.get("ts", "")) or now_dt) >= keep_start
        ],
    }
    _save_state(state_path, state_out)

    escalation_level = "L0"
    if l3_families:
        escalation_level = "L3"
    elif l2_families:
        escalation_level = "L2"
    elif l1_families:
        escalation_level = "L1"

    if escalation_level == "L0":
        status = STATUS_PASS_REQUIRED
        error_code = ""
    elif escalation_level == "L1":
        status = STATUS_WARN_NON_BLOCKING
        error_code = ""
    elif escalation_level == "L2":
        status = STATUS_FAIL_REQUIRED if args.enforce_blocking else STATUS_WARN_NON_BLOCKING
        error_code = ERR_ESCALATION
    else:  # L3
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_ESCALATION

    payload = {
        "required_gate_recurrence_status": status,
        "error_code": error_code,
        "escalation_level": escalation_level,
        "identity_id": str(args.identity_id),
        "surface": str(args.surface),
        "operation": str(args.operation),
        "receipt_path": str(receipt_path),
        "state_path": str(state_path),
        "new_event_count": len(new_events),
        "tracked_event_count": len(kept_events),
        "l1_error_families": sorted(set(l1_families)),
        "l2_error_families": sorted(set(l2_families)),
        "l3_error_families": sorted(set(l3_families)),
        "family_metrics": family_metrics,
        "stale_reasons": [],
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[RECURRENCE] status={status} escalation_level={escalation_level} "
            f"new_events={len(new_events)} tracked_events={len(kept_events)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 1 if status == STATUS_FAIL_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
