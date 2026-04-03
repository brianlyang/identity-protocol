#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from repo_root_resolution_common import resolve_repo_root
from reference_visual_atlas_governance_common import (
    REFERENCE_VISUAL_ATLAS_INVENTORY_DOC,
    load_reference_visual_atlas_registry,
    render_reference_visual_atlas_inventory_markdown,
)

STATUS_PASS_PREVIEW = "PASS_PREVIEW"
STATUS_PASS_WRITTEN = "PASS_WRITTEN"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_CODE = "IP-REF-ATLAS-INV-RENDER-001"


def build_render_payload(*, repo_root_override: str = "", inventory_doc_rel: str = REFERENCE_VISUAL_ATLAS_INVENTORY_DOC) -> dict:
    repo_root = resolve_repo_root(repo_root_override, start=__file__)
    inventory_doc_path = (repo_root / inventory_doc_rel).resolve()
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_reference_visual_atlas_registry(
        repo_root
    )

    stale_reasons: list[str] = []
    if registry_alias_error:
        stale_reasons.append(f"atlas_registry_alias_error:{registry_alias_error}")
    elif not registry_doc:
        stale_reasons.append(f"atlas_registry_parse_failed:{registry_active_path}")

    rendered_markdown = render_reference_visual_atlas_inventory_markdown(registry_doc) if registry_doc else ""
    current_markdown = ""
    if inventory_doc_path.exists() and inventory_doc_path.is_file():
        current_markdown = inventory_doc_path.read_text(encoding="utf-8")
    else:
        stale_reasons.append(f"inventory_doc_missing:{inventory_doc_rel}")

    return {
        "reference_visual_atlas_inventory_render_status": (
            STATUS_PASS_PREVIEW if not stale_reasons else STATUS_FAIL_REQUIRED
        ),
        "error_code": "" if not stale_reasons else ERR_CODE,
        "repo_root": str(repo_root),
        "atlas_registry_entry": str(registry_entry_path),
        "atlas_registry_active": str(registry_active_path),
        "atlas_registry_alias_error": registry_alias_error,
        "inventory_doc": str(inventory_doc_path),
        "inventory_doc_rel": inventory_doc_rel,
        "changed": current_markdown != rendered_markdown,
        "write_performed": False,
        "stale_reasons": stale_reasons,
        "rendered_markdown": rendered_markdown,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render registry-driven reference visual atlas inventory markdown.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--inventory-doc", default=REFERENCE_VISUAL_ATLAS_INVENTORY_DOC)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    payload = build_render_payload(repo_root_override=args.repo_root, inventory_doc_rel=args.inventory_doc)
    status = payload.get("reference_visual_atlas_inventory_render_status")
    rendered_markdown = str(payload.get("rendered_markdown", ""))
    inventory_doc = str(payload.get("inventory_doc", ""))

    if args.write and status != STATUS_FAIL_REQUIRED:
        from pathlib import Path

        inventory_doc_path = Path(inventory_doc)
        inventory_doc_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_doc_path.write_text(rendered_markdown, encoding="utf-8")
        payload["reference_visual_atlas_inventory_render_status"] = STATUS_PASS_WRITTEN
        payload["write_performed"] = True
        status = STATUS_PASS_WRITTEN

    if args.json_only:
        payload = dict(payload)
        payload.pop("rendered_markdown", None)
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if status != STATUS_FAIL_REQUIRED else 1

    if status == STATUS_FAIL_REQUIRED:
        print(f"[FAIL] {ERR_CODE} unable to render reference visual atlas inventory")
        for reason in payload.get("stale_reasons", []):
            print(f" - {reason}")
        return 1

    action = "wrote" if args.write else "previewed"
    print(f"[PASS] {action} reference visual atlas inventory: {inventory_doc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
