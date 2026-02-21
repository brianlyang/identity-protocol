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


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a fresh production handoff log template")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--to-agent", default="sub-agent")
    args = ap.parse_args()

    current_task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    current_task = _load_json(current_task_path)
    task_id = str(current_task.get("task_id") or "")

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    stamp = now.strftime("%Y%m%d-%H%M%S")

    out = Path(args.out) if args.out else Path(
        f"identity/runtime/logs/handoff/handoff-{args.identity_id}-{stamp}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    artifact_path = f"identity/runtime/logs/handoff/artifacts/{args.identity_id}-{stamp}.md"

    payload = {
        "generated_at": ts,
        "identity_id": args.identity_id,
        "handoff_id": f"handoff-{args.identity_id}-{stamp}",
        "task_id": task_id,
        "from_agent": f"{args.identity_id}-master",
        "to_agent": args.to_agent,
        "input_scope": "TODO: describe delegated scope",
        "actions_taken": [
            "TODO: action-1",
            "TODO: action-2"
        ],
        "artifacts": [
            {
                "path": artifact_path,
                "kind": "TODO: artifact_kind"
            }
        ],
        "route_decision": {
            "route_hit": True,
            "misroute": False,
            "fallback": False
        },
        "result": "PASS",
        "next_action": {
            "owner": args.to_agent,
            "action": "TODO: next action",
            "input": "TODO: structured input"
        },
        "rulebook_update": {
            "applied": False,
            "evidence_run_id": ""
        },
        "attempted_mutations": []
    }

    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    artifact = Path(artifact_path)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    if not artifact.exists():
        artifact.write_text(
            "# Handoff Artifact\n\n- Fill with concrete evidence for this handoff run.\n",
            encoding="utf-8",
        )

    print(f"[OK] created handoff template: {out}")
    print(f"[OK] ensured artifact file: {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
