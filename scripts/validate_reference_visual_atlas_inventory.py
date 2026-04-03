#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from registry_alias_control_plane_common import STREAM_DOC_REGISTRY_CURRENT, resolve_current_yaml_alias
from repo_root_resolution_common import resolve_repo_root
from reference_visual_atlas_governance_common import (
    REFERENCE_VISUAL_ATLAS_INVENTORY_DOC,
    REFERENCE_VISUAL_ATLAS_ONBOARDING_CONTRACT,
    REFERENCE_VISUAL_ATLAS_PROBE_SCRIPT,
    REFERENCE_VISUAL_ATLAS_GENERATOR_SCRIPT,
    REFERENCE_VISUAL_ATLAS_REGISTRY_CURRENT,
    REFERENCE_VISUAL_ATLAS_RENDERER_SCRIPT,
    REFERENCE_VISUAL_ATLAS_TEMPLATE_ROOT,
    discover_visual_atlas_governance_scripts,
    load_reference_visual_atlas_registry,
    reference_visual_atlas_families_from_registry,
    render_reference_visual_atlas_inventory_markdown,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_CODE = "IP-REF-ATLAS-INV-001"
INVENTORY_DOC = REFERENCE_VISUAL_ATLAS_INVENTORY_DOC
EXPECTED_TOP_LEVEL = {
    "onboarding_contract": REFERENCE_VISUAL_ATLAS_ONBOARDING_CONTRACT,
    "generator_script": REFERENCE_VISUAL_ATLAS_GENERATOR_SCRIPT,
    "probe_script": REFERENCE_VISUAL_ATLAS_PROBE_SCRIPT,
    "renderer_script": REFERENCE_VISUAL_ATLAS_RENDERER_SCRIPT,
    "template_root": REFERENCE_VISUAL_ATLAS_TEMPLATE_ROOT,
    "inventory_doc": INVENTORY_DOC,
}
EXPECTED_INDEX_MARKERS = (
    "`identity/protocol/mappings/reference-visual-atlas-registry.current.yaml`",
    "`python3 scripts/render_reference_visual_atlas_inventory.py --write`",
    "`python3 scripts/generate_reference_visual_atlas_scaffold.py --help`",
    "`bash scripts/ci/run_reference_visual_atlas_scaffold_probes_ci.sh`",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _norm_path(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_stream_doc_registry(repo_root: Path) -> tuple[dict[str, Any], str]:
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, STREAM_DOC_REGISTRY_CURRENT)
    if alias_error:
        return {}, alias_error
    if not active_path.exists():
        return {}, "active_stream_doc_registry_missing"
    return _load_yaml(active_path), ""


def _mandatory_static_docs(registry_doc: dict[str, Any]) -> set[str]:
    rows = registry_doc.get("mandatory_static_docs")
    if not isinstance(rows, list):
        return set()
    return {_norm_path(row) for row in rows if _norm_path(row)}


def _static_alias_row(registry_doc: dict[str, Any], doc_rel: str) -> list[str]:
    rows = registry_doc.get("static_doc_required_alias_refs")
    if not isinstance(rows, list):
        return []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _norm_path(row.get("doc")) != doc_rel:
            continue
        values = row.get("alias_refs")
        if not isinstance(values, list):
            return []
        return [_norm_path(item) for item in values if _norm_path(item)]
    return []


def validate_reference_visual_atlas_inventory(repo_root_override: str = "") -> dict[str, Any]:
    repo_root = resolve_repo_root(repo_root_override, start=__file__)
    registry_doc, registry_entry, registry_active, registry_alias_error = load_reference_visual_atlas_registry(repo_root)
    registry_active_file = registry_active.relative_to(repo_root).as_posix() if registry_active.exists() else ""
    inventory_doc = (repo_root / INVENTORY_DOC).resolve()
    stream_doc_registry, stream_doc_registry_error = _load_stream_doc_registry(repo_root)
    mandatory_docs = _mandatory_static_docs(stream_doc_registry)

    violations: list[str] = []
    if registry_alias_error:
        violations.append(f"atlas_registry_alias_error:{registry_alias_error}:{registry_active_file}")
    elif not registry_active.exists():
        violations.append(f"atlas_registry_missing:{registry_active}")
    elif not registry_doc:
        violations.append(f"atlas_registry_parse_failed:{registry_active}")

    for key, expected in EXPECTED_TOP_LEVEL.items():
        actual = _norm_path(registry_doc.get(key))
        if actual != expected:
            violations.append(f"registry_field_mismatch:{key}:{actual or '<missing>'}:{expected}")

    rendered_inventory_text = render_reference_visual_atlas_inventory_markdown(registry_doc) if registry_doc else ""
    if not inventory_doc.exists():
        violations.append(f"inventory_doc_missing:{INVENTORY_DOC}")
        inventory_text = ""
    else:
        inventory_text = inventory_doc.read_text(encoding="utf-8")
        for marker in EXPECTED_INDEX_MARKERS:
            if marker not in inventory_text:
                violations.append(f"inventory_doc_marker_missing:{marker}")
        if rendered_inventory_text and inventory_text != rendered_inventory_text:
            violations.append("inventory_render_sync_drift")

    if stream_doc_registry_error:
        violations.append(f"stream_doc_registry_error:{stream_doc_registry_error}")

    if INVENTORY_DOC not in mandatory_docs:
        violations.append(f"mandatory_static_doc_missing:{INVENTORY_DOC}")
    if REFERENCE_VISUAL_ATLAS_REGISTRY_CURRENT not in mandatory_docs:
        violations.append(f"mandatory_static_doc_missing:{REFERENCE_VISUAL_ATLAS_REGISTRY_CURRENT}")

    alias_row = _static_alias_row(stream_doc_registry, INVENTORY_DOC)
    expected_index_aliases = {
        STREAM_DOC_REGISTRY_CURRENT,
        "identity/protocol/mappings/contract-binding.current.yaml",
        "identity/protocol/mappings/semantic-term-registry.current.yaml",
        REFERENCE_VISUAL_ATLAS_REGISTRY_CURRENT,
    }
    if not alias_row:
        violations.append(f"inventory_alias_row_missing:{INVENTORY_DOC}")
    else:
        missing_aliases = sorted(expected_index_aliases - set(alias_row))
        for alias_ref in missing_aliases:
            violations.append(f"inventory_alias_ref_missing:{alias_ref}")

    atlas_rows = reference_visual_atlas_families_from_registry(registry_doc)
    if not atlas_rows:
        violations.append("atlas_families_missing")

    discovered_validators = {
        path.relative_to(repo_root).as_posix(): path for path in discover_visual_atlas_governance_scripts(repo_root)
    }
    seen_family_ids: set[str] = set()
    registered_validator_paths: set[str] = set()

    for row in atlas_rows:
        family_id = row.family_id
        if not family_id:
            violations.append("atlas_family_missing_id")
            continue
        if family_id in seen_family_ids:
            violations.append(f"atlas_family_duplicate:{family_id}")
        seen_family_ids.add(family_id)

        canonical_doc = row.canonical_doc
        asset_root = row.canonical_asset_root
        validator_script = row.validator_script
        status_key = row.status_key
        scope_mode = row.scope_mode
        onboarding_contract = row.onboarding_contract
        owner_docs = list(row.owner_docs)

        if scope_mode != "protocol_repo_internal_only":
            violations.append(f"scope_mode_invalid:{family_id}:{scope_mode or '<missing>'}")
        if onboarding_contract != EXPECTED_TOP_LEVEL["onboarding_contract"]:
            violations.append(f"row_onboarding_contract_invalid:{family_id}:{onboarding_contract or '<missing>'}")
        if not owner_docs:
            violations.append(f"owner_docs_missing:{family_id}")
            owner_docs = []
        if not status_key:
            violations.append(f"status_key_missing:{family_id}")

        for label, rel_path in (
            ("canonical_doc_missing", canonical_doc),
            ("canonical_asset_root_missing", asset_root),
            ("validator_script_missing", validator_script),
        ):
            if not rel_path:
                violations.append(f"{label}:{family_id}")
                continue
            candidate = (repo_root / rel_path).resolve()
            if not candidate.exists():
                violations.append(f"{label}:{family_id}:{rel_path}")

        if canonical_doc and canonical_doc not in mandatory_docs:
            violations.append(f"family_doc_not_in_mandatory_static_docs:{family_id}:{canonical_doc}")

        if canonical_doc and inventory_text and canonical_doc not in inventory_text:
            violations.append(f"inventory_doc_missing_canonical_doc:{family_id}:{canonical_doc}")
        if asset_root and inventory_text and f"`{asset_root}/`" not in inventory_text and f"`{asset_root}`" not in inventory_text:
            violations.append(f"inventory_doc_missing_asset_root:{family_id}:{asset_root}")
        if validator_script and inventory_text and validator_script not in inventory_text:
            violations.append(f"inventory_doc_missing_validator:{family_id}:{validator_script}")
        if status_key and inventory_text and f"`{status_key}`" not in inventory_text:
            violations.append(f"inventory_doc_missing_status_key:{family_id}:{status_key}")
        if family_id and inventory_text and f"`{family_id}`" not in inventory_text:
            violations.append(f"inventory_doc_missing_family_id:{family_id}")

        for owner_doc in owner_docs:
            owner_rel = _norm_path(owner_doc)
            if not owner_rel:
                violations.append(f"owner_doc_blank:{family_id}")
                continue
            owner_path = (repo_root / owner_rel).resolve()
            if not owner_path.exists():
                violations.append(f"owner_doc_missing:{family_id}:{owner_rel}")
            if inventory_text and owner_rel not in inventory_text:
                violations.append(f"inventory_doc_missing_owner_doc:{family_id}:{owner_rel}")

        if validator_script:
            registered_validator_paths.add(validator_script)
            validator_path = discovered_validators.get(validator_script)
            if not validator_path:
                violations.append(f"validator_not_discovered:{family_id}:{validator_script}")
            else:
                validator_text = validator_path.read_text(encoding="utf-8")
                if canonical_doc and canonical_doc not in validator_text:
                    violations.append(f"validator_missing_canonical_doc_marker:{family_id}:{validator_script}")
                if asset_root and asset_root not in validator_text:
                    violations.append(f"validator_missing_asset_root_marker:{family_id}:{validator_script}")

    missing_from_registry = sorted(set(discovered_validators) - registered_validator_paths)
    for validator_script in missing_from_registry:
        violations.append(f"validator_missing_registry_row:{validator_script}")

    return {
        "reference_visual_atlas_inventory_status": STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED,
        "error_code": "" if not violations else ERR_CODE,
        "repo_root": str(repo_root),
        "atlas_registry_entry": str(registry_entry),
        "atlas_registry_active": str(registry_active),
        "atlas_registry_active_file": registry_active_file,
        "atlas_registry_alias_error": registry_alias_error,
        "inventory_doc": INVENTORY_DOC,
        "inventory_render_sync_status": "PASS_REQUIRED" if not rendered_inventory_text or inventory_text == rendered_inventory_text else "FAIL_REQUIRED",
        "inventory_renderer_script": REFERENCE_VISUAL_ATLAS_RENDERER_SCRIPT,
        "registered_family_ids": sorted(seen_family_ids),
        "atlas_family_count": len(seen_family_ids),
        "discovered_validator_scripts": sorted(discovered_validators),
        "mandatory_static_docs_checked": sorted(
            doc
            for doc in mandatory_docs
            if doc in {INVENTORY_DOC, REFERENCE_VISUAL_ATLAS_REGISTRY_CURRENT}
            or doc.startswith("docs/references/identity-protocol-")
        ),
        "violation_count": len(violations),
        "violations": violations,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate canonical reference visual atlas inventory registry + index synchronization."
    )
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload = validate_reference_visual_atlas_inventory(repo_root_override=args.repo_root)
    status = payload.get("reference_visual_atlas_inventory_status")
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if status == STATUS_PASS_REQUIRED else 1
    if status != STATUS_PASS_REQUIRED:
        print(f"[FAIL] {ERR_CODE} reference visual atlas inventory drift detected")
        for violation in payload.get("violations", []):
            print(f" - {violation}")
        return 1
    print("[PASS] reference visual atlas inventory OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
