#!/usr/bin/env python3
"""Validate identity protocol artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import validate as jsonschema_validate

REQ_TASK_KEYS = {
    "objective", "state_machine", "gates", "source_of_truth",
    "escalation_policy", "required_artifacts", "post_execution_mandatory"
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def fail(msg: str) -> None:
    raise SystemExit(f"[FAIL] {msg}")


def main() -> int:
    catalog_path = Path("identity/catalog/identities.yaml")
    schema_path = Path("identity/catalog/schema/identities.schema.json")

    if not catalog_path.exists():
        fail(f"missing {catalog_path}")
    if not schema_path.exists():
        fail(f"missing {schema_path}")

    catalog = load_yaml(catalog_path)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema_validate(catalog, schema)

    default_id = catalog.get("default_identity")
    identities = catalog.get("identities") or []
    active = next((x for x in identities if x.get("id") == default_id), None)
    if not active:
        fail(f"default_identity not found in identities: {default_id}")

    pack_path = Path(active.get("pack_path", ""))
    required_pack_files = ["IDENTITY_PROMPT.md", "CURRENT_TASK.json", "TASK_HISTORY.md"]

    if not (pack_path and pack_path.exists()):
        legacy = Path("identity") / str(default_id)
        if not legacy.exists():
            fail(f"pack_path missing/invalid and legacy pack not found: {pack_path}")
        pack_path = legacy

    for f in required_pack_files:
        p = pack_path / f
        if not p.exists():
            fail(f"missing pack file: {p}")

    task = json.loads((pack_path / "CURRENT_TASK.json").read_text(encoding="utf-8"))
    missing = [k for k in sorted(REQ_TASK_KEYS) if k not in task]
    if missing:
        fail(f"CURRENT_TASK missing keys: {missing}")

    print("[OK] identity protocol validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
