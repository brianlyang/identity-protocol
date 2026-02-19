#!/usr/bin/env python3
"""Create an identity pack and optionally register it in identity catalog."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import yaml


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(path: Path, data) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--pack-root", default="identity/packs")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--register", action="store_true", help="Register identity in catalog")
    ap.add_argument("--set-default", action="store_true", help="Set as default identity")
    args = ap.parse_args()

    identity_id = args.id.strip()
    if not identity_id:
        print("[FAIL] --id cannot be empty")
        return 1

    pack_dir = Path(args.pack_root) / identity_id
    if pack_dir.exists() and any(pack_dir.iterdir()):
        print(f"[FAIL] pack directory already exists and is non-empty: {pack_dir}")
        return 1

    write(
        pack_dir / "META.yaml",
        (
            f'id: "{identity_id}"\n'
            f'title: "{args.title}"\n'
            f'description: "{args.description}"\n'
            'status: "active"\n'
            'methodology_version: "v1.1"\n'
        ),
    )

    write(
        pack_dir / "IDENTITY_PROMPT.md",
        "# Identity Prompt\n\nDefine role cognition, principles, and decision rules.\n",
    )

    write(
        pack_dir / "CURRENT_TASK.json",
        """{
  "objective": {"title": "", "priority": "HIGH", "status": "pending"},
  "state_machine": {"current_state": "intake", "allowed_states": ["intake"]},
  "gates": {},
  "source_of_truth": {},
  "escalation_policy": {},
  "required_artifacts": [],
  "post_execution_mandatory": []
}
""",
    )

    write(pack_dir / "TASK_HISTORY.md", "# Task History\n\n## Entries\n")

    write(
        pack_dir / "agents/identity.yaml",
        (
            "interface:\n"
            f'  display_name: "{args.title}"\n'
            f'  short_description: "{args.description}"\n'
            f'  default_prompt: "Operate as {identity_id} and satisfy runtime gates."\n\n'
            "policy:\n"
            "  allow_implicit_activation: true\n"
            "  activation_priority: 50\n"
            "  conflict_resolution: \"priority_then_objective\"\n\n"
            "dependencies:\n"
            "  tools: []\n\n"
            "observability:\n"
            "  event_topics: []\n"
            "  required_artifacts: []\n"
        ),
    )

    print(f"[OK] created identity pack: {pack_dir}")

    if args.register:
        catalog_path = Path(args.catalog)
        if not catalog_path.exists():
            print(f"[FAIL] catalog file not found: {catalog_path}")
            return 1
        catalog = load_yaml(catalog_path) or {}
        identities = catalog.get("identities", [])
        if any((x or {}).get("id") == identity_id for x in identities):
            print(f"[FAIL] id already exists in catalog: {identity_id}")
            return 1

        identities.append(
            {
                "id": identity_id,
                "title": args.title,
                "description": args.description,
                "status": "active",
                "methodology_version": "v1.1",
                "pack_path": str(pack_dir),
                "tags": ["identity"],
            }
        )
        catalog["identities"] = identities
        if args.set_default:
            catalog["default_identity"] = identity_id
        dump_yaml(catalog_path, catalog)
        print(f"[OK] registered identity in catalog: {catalog_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
