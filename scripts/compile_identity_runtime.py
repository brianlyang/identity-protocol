#!/usr/bin/env python3
"""Compile a concise identity runtime brief from catalog + active pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", default="identity/catalog/identities.yaml")
    p.add_argument("--output", default="identity/runtime/IDENTITY_COMPILED.md")
    args = p.parse_args()

    catalog_path = Path(args.catalog)
    catalog = load_yaml(catalog_path)

    default_id = catalog.get("default_identity")
    identities = catalog.get("identities") or []
    if not default_id or not isinstance(identities, list):
        raise SystemExit("Invalid catalog: default_identity/identities missing")

    active = next((x for x in identities if x.get("id") == default_id), None)
    if not active:
        raise SystemExit(f"default_identity not found in identities: {default_id}")

    pack_path = Path(active.get("pack_path", ""))
    current_task_path = pack_path / "CURRENT_TASK.json"
    if not current_task_path.exists():
        legacy = Path("identity") / active["id"] / "CURRENT_TASK.json"
        current_task_path = legacy if legacy.exists() else current_task_path

    if not current_task_path.exists():
        raise SystemExit(f"CURRENT_TASK.json not found: {current_task_path}")

    current_task = json.loads(current_task_path.read_text(encoding="utf-8"))
    objective = (current_task.get("objective") or {}).get("title", "")
    state = (current_task.get("state_machine") or {}).get("current_state", "unknown")

    hard_guardrails = (((active.get("governance") or {}).get("hard_guardrails") or [])
        if isinstance(active.get("governance"), dict)
        else [])

    lines = [
        "# Identity Runtime Brief",
        "",
        f"Active identity: {active.get('id', 'unknown')}",
        "",
        "This file is generated/maintained by identity runtime tooling.",
        "",
        "Hard guardrails:",
    ]
    lines.extend([f"- {g}" for g in hard_guardrails] or ["- (none)"])
    lines += [
        "",
        "Current objective:",
        f"- {objective or '(not set)'}",
        "",
        "Current state:",
        f"- {state}",
        "",
        "See source:",
        f"- {catalog_path.as_posix()}",
        f"- {current_task_path.as_posix()}",
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
