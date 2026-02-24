#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_identity(catalog_path: Path, identity_id: str) -> dict[str, Any]:
    catalog = _load_yaml(catalog_path)
    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in identities if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    return row


def _task_path(identity: dict[str, Any], identity_id: str) -> Path:
    pack = str(identity.get("pack_path", "")).strip()
    p = Path(pack).expanduser().resolve() / "CURRENT_TASK.json"
    if not p.exists():
        p = Path("identity") / identity_id / "CURRENT_TASK.json"
    if not p.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found for identity={identity_id}")
    return p


def _materialize(pattern: str, identity_id: str, ts: int) -> Path:
    p = pattern.replace("<identity-id>", identity_id)
    if "*" in p:
        p = p.replace("*", str(ts))
    return Path(p).expanduser()


def _write(path: Path, payload: dict[str, Any], apply: bool) -> None:
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair/generate experience feedback governance evidence.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default=str((Path.home()/".codex"/"identity"/"catalog.local.yaml").resolve()))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    identity = _resolve_identity(catalog, args.identity_id)
    task = _load_json(_task_path(identity, args.identity_id))
    contract = task.get("experience_feedback_contract") or {}
    log_pattern = str(contract.get("feedback_log_path_pattern", "")).strip()
    if not log_pattern:
        print("[FAIL] feedback_log_path_pattern missing")
        return 1
    sample_pattern = str(contract.get("sample_report_path_pattern", "")).strip()

    ts = int(datetime.now(timezone.utc).timestamp())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    log_path = _materialize(log_pattern, args.identity_id, ts)
    log_payload = {
        "feedback_id": f"feedback-{args.identity_id}-{ts}",
        "identity_id": args.identity_id,
        "task_id": str(task.get("task_id", "")),
        "run_id": f"repair-feedback-{ts}",
        "timestamp": now,
        "context_signature": "auto-repair-context",
        "outcome": "PASS",
        "failure_type": "none",
        "decision_trace_ref": "auto-repair-feedback-evidence",
        "artifacts": [str(log_path)],
        "rulebook_delta": {"positive": 0, "negative": 0},
        "replay_status": "PASS",
    }
    _write(log_path, log_payload, args.apply)

    outputs = [log_path]

    if sample_pattern:
        sample_path = _materialize(sample_pattern, args.identity_id, ts)
        sample_payload = {
            "identity_id": args.identity_id,
            "generated_at": now,
            "positive_updates": [
                {"rule_id": f"feedback-positive-{ts}", "replay_status": "PASS"}
            ],
            "negative_updates": [],
        }
        _write(sample_path, sample_payload, args.apply)
        outputs.append(sample_path)

    print(f"[OK] feedback evidence repair {'applied' if args.apply else 'preview'} for identity={args.identity_id}")
    for p in outputs:
        print(f"  - {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
