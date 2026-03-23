#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

from repo_root_resolution_common import resolve_repo_root
from registry_alias_control_plane_common import STREAM_DOC_REGISTRY_CURRENT, resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_LOOP_VISUAL_ATLAS = "IP-LOOP-ATLAS-001"

CANONICAL_ATLAS_DOC = "docs/references/identity-protocol-loop-visual-atlas-v1.6.md"
CANONICAL_ASSET_ROOT = "docs/references/assets/identity-protocol-loop-visual-atlas"
AUDIT_INDEX_DOC = "docs/governance/AUDIT_SNAPSHOT_INDEX.md"
STREAM_DOC_REGISTRY_REF = STREAM_DOC_REGISTRY_CURRENT
V162_GOV_DOC = "docs/governance/identity-multimodal-plugin-enforcement-governance-v1.6.2.md"
V1617_GOV_DOC = "docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md"
V1617_REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.17-routing-learning-strengthening.md"

CONTRACT_BINDING_CURRENT_REF = "identity/protocol/mappings/contract-binding.current.yaml"
SEMANTIC_TERM_REGISTRY_CURRENT_REF = "identity/protocol/mappings/semantic-term-registry.current.yaml"

ATLAS_ALIAS_REFS = (
    STREAM_DOC_REGISTRY_REF,
    CONTRACT_BINDING_CURRENT_REF,
    SEMANTIC_TERM_REGISTRY_CURRENT_REF,
)

REQUIRED_SVG_FILES = (
    "identity_protocol_four_loops_v1617.svg",
    "identity_protocol_loop3_route_discovery_control_plane_v1617.svg",
    "identity_protocol_loop4_feedback_strengthening_control_plane_v1617.svg",
    "identity_protocol_4to1_bounded_loopback_adjudication_v1617.svg",
)
SVG_FAMILY_RE = re.compile(
    r"^identity_protocol_(four_loops|loop3_route_discovery_control_plane|loop4_feedback_strengthening_control_plane|4to1_bounded_loopback_adjudication)_v[0-9A-Za-z.]+\.svg$"
)
ATLAS_DOC_RE = re.compile(r"^identity-protocol-loop-visual-atlas-v[0-9.]+\.md$")

ANTI_SCATTER_SCOPE_MODE = "protocol_repo_internal_only"

ATLAS_REQUIRED_MARKERS = (
    "Status: Active canonical visual reference for the frozen four-loop / 4→1 loopback explanation surface.",
    "Classification: protocol-owned explanatory atlas; not a normative contract source.",
    "Canonical atlas markdown path is fixed to:",
    "Canonical asset root for all protocol-owned loop visuals is fixed to:",
    "do not scatter them across `docs/governance/`, `docs/review/`, `activity/evidence/`, or ad-hoc workspace folders",
    "The anti-scatter guarantee frozen by this atlas is limited to the `identity-protocol-local` repository surface.",
    "Workspace-external staging/evidence copies, including `activity/evidence/` mirrors or sibling-workspace scratch outputs, are outside this validator scope and remain non-canonical by definition.",
    "No diagram in this atlas may introduce backward compatibility, backstop, downgrade, lagging-pack shortcut, or undeclared rescue semantics.",
)

INDEX_REQUIRED_MARKERS = (
    "`docs/references/identity-protocol-loop-visual-atlas-v1.6.md`",
    "asset root: `docs/references/assets/identity-protocol-loop-visual-atlas/`",
)

OWNER_DOC_MARKERS: dict[str, tuple[str, ...]] = {
    V162_GOV_DOC: (
        "docs/references/identity-protocol-loop-visual-atlas-v1.6.md",
        "docs/references/assets/identity-protocol-loop-visual-atlas/",
        "This stream remains the semantic owner for the first-loop / second-loop kernel-authoritative surfaces shown in that atlas",
    ),
    V1617_GOV_DOC: (
        "docs/references/identity-protocol-loop-visual-atlas-v1.6.md",
        "docs/references/assets/identity-protocol-loop-visual-atlas/",
        "Loop 3 center = `route_discovery_convergence_contract_v1`",
        "Loop 4 center = `feedback_operational_prompt_contract_v1`",
        "bounded bridge = `feedback_to_judgement_loopback_contract_v1`",
    ),
    V1617_REVIEW_DOC: (
        "docs/references/identity-protocol-loop-visual-atlas-v1.6.md",
        "docs/references/assets/identity-protocol-loop-visual-atlas/",
        "the shared four-track primitive remains distinct from the `4→1` bridge",
        "first-loop revalidation remains authoritative after loopback reentry.",
    ),
}


def _norm_path(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _load_stream_doc_registry(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / STREAM_DOC_REGISTRY_REF).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, STREAM_DOC_REGISTRY_REF)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_registry_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def _append_violation(violations: list[str], reason: str, detail: str) -> None:
    violations.append(f"{reason}:{detail}")


def _collect_stray_atlas_docs(repo_root: Path, canonical_doc: Path) -> list[str]:
    out: list[str] = []
    for candidate in repo_root.rglob("*.md"):
        if not ATLAS_DOC_RE.match(candidate.name):
            continue
        rel = candidate.relative_to(repo_root).as_posix()
        if rel != canonical_doc.relative_to(repo_root).as_posix():
            out.append(rel)
    return sorted(set(out))


def _collect_stray_svg_files(repo_root: Path, canonical_asset_root: Path) -> list[str]:
    out: list[str] = []
    for candidate in repo_root.rglob("*.svg"):
        if not SVG_FAMILY_RE.match(candidate.name):
            continue
        rel = candidate.relative_to(repo_root).as_posix()
        if canonical_asset_root not in candidate.parents:
            out.append(rel)
    return sorted(set(out))


def _static_alias_row_for(doc: str, registry_doc: dict[str, Any]) -> list[str]:
    rows = registry_doc.get("static_doc_required_alias_refs")
    if not isinstance(rows, list):
        return []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _norm_path(row.get("doc", "")) != doc:
            continue
        return [_norm_path(item) for item in (row.get("alias_refs") or []) if _norm_path(item)]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate canonical loop visual atlas SSOT/directory governance.")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    canonical_doc = (repo_root / CANONICAL_ATLAS_DOC).resolve()
    canonical_asset_root = (repo_root / CANONICAL_ASSET_ROOT).resolve()
    index_doc = (repo_root / AUDIT_INDEX_DOC).resolve()

    violations: list[str] = []

    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = _load_stream_doc_registry(repo_root)
    if registry_alias_error:
        _append_violation(violations, "stream_doc_registry_alias_error", registry_alias_error)

    if not canonical_doc.exists() or not canonical_doc.is_file():
        _append_violation(violations, "canonical_atlas_doc_missing", CANONICAL_ATLAS_DOC)
        atlas_text = ""
    else:
        atlas_text = canonical_doc.read_text(encoding="utf-8")
        for marker in ATLAS_REQUIRED_MARKERS:
            if marker not in atlas_text:
                _append_violation(violations, "atlas_doc_marker_missing", marker)
        for alias_ref in ATLAS_ALIAS_REFS:
            if alias_ref not in atlas_text:
                _append_violation(violations, "atlas_doc_alias_ref_missing", alias_ref)
        for svg_name in REQUIRED_SVG_FILES:
            if svg_name not in atlas_text:
                _append_violation(violations, "atlas_doc_svg_ref_missing", svg_name)

    if not canonical_asset_root.exists() or not canonical_asset_root.is_dir():
        _append_violation(violations, "canonical_asset_root_missing", CANONICAL_ASSET_ROOT)

    required_svg_paths: list[str] = []
    for svg_name in REQUIRED_SVG_FILES:
        svg_path = (canonical_asset_root / svg_name).resolve()
        required_svg_paths.append(svg_path.relative_to(repo_root).as_posix() if svg_path.exists() else f"{CANONICAL_ASSET_ROOT}/{svg_name}")
        if not svg_path.exists() or not svg_path.is_file():
            _append_violation(violations, "required_svg_missing", f"{CANONICAL_ASSET_ROOT}/{svg_name}")

    if not index_doc.exists() or not index_doc.is_file():
        _append_violation(violations, "audit_snapshot_index_missing", AUDIT_INDEX_DOC)
    else:
        index_text = index_doc.read_text(encoding="utf-8")
        for marker in INDEX_REQUIRED_MARKERS:
            if marker not in index_text:
                _append_violation(violations, "audit_index_marker_missing", marker)

    if registry_doc:
        mandatory_static_docs = {
            _norm_path(item)
            for item in (registry_doc.get("mandatory_static_docs") or [])
            if _norm_path(item)
        }
        if CANONICAL_ATLAS_DOC not in mandatory_static_docs:
            _append_violation(violations, "mandatory_static_doc_missing", CANONICAL_ATLAS_DOC)
        alias_refs = _static_alias_row_for(CANONICAL_ATLAS_DOC, registry_doc)
        if not alias_refs:
            _append_violation(violations, "static_alias_row_missing", CANONICAL_ATLAS_DOC)
        else:
            missing_alias_refs = sorted(set(ATLAS_ALIAS_REFS) - set(alias_refs))
            for alias_ref in missing_alias_refs:
                _append_violation(violations, "static_alias_ref_missing", alias_ref)
    else:
        _append_violation(violations, "stream_doc_registry_unavailable", str(registry_active_path))

    for owner_doc_rel, markers in OWNER_DOC_MARKERS.items():
        owner_doc = (repo_root / owner_doc_rel).resolve()
        if not owner_doc.exists() or not owner_doc.is_file():
            _append_violation(violations, "owner_doc_missing", owner_doc_rel)
            continue
        owner_text = owner_doc.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in owner_text:
                _append_violation(violations, "owner_doc_marker_missing", f"{owner_doc_rel}:{marker}")

    stray_atlas_docs = _collect_stray_atlas_docs(repo_root, canonical_doc)
    for rel in stray_atlas_docs:
        _append_violation(violations, "stray_atlas_doc", rel)

    stray_svg_files = _collect_stray_svg_files(repo_root, canonical_asset_root)
    for rel in stray_svg_files:
        _append_violation(violations, "stray_svg_file", rel)

    payload = {
        "loop_visual_atlas_governance_status": STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED,
        "error_code": "" if not violations else ERR_LOOP_VISUAL_ATLAS,
        "anti_scatter_scope_mode": ANTI_SCATTER_SCOPE_MODE,
        "repo_root": str(repo_root),
        "scan_root": str(repo_root),
        "workspace_external_surfaces_in_scope": False,
        "workspace_external_scope_examples": ["activity/evidence/", "sibling-workspace staging copies"],
        "stream_doc_registry_entry": str(registry_entry_path),
        "stream_doc_registry_active": str(registry_active_path),
        "stream_doc_registry_alias_error": registry_alias_error,
        "canonical_atlas_doc": CANONICAL_ATLAS_DOC,
        "canonical_asset_root": CANONICAL_ASSET_ROOT,
        "required_svg_files": list(REQUIRED_SVG_FILES),
        "required_svg_count": len(REQUIRED_SVG_FILES),
        "stray_atlas_docs": stray_atlas_docs,
        "stray_svg_files": stray_svg_files,
        "violation_count": len(violations),
        "violations": violations,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if not violations else 1

    if violations:
        print(f"[FAIL] {ERR_LOOP_VISUAL_ATLAS} loop visual atlas governance drift detected")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    print("[PASS] loop visual atlas governance validated")
    print(f"       atlas_doc={CANONICAL_ATLAS_DOC}")
    print(f"       asset_root={CANONICAL_ASSET_ROOT}")
    print(f"       anti_scatter_scope_mode={ANTI_SCATTER_SCOPE_MODE}")
    print(f"       required_svg_count={len(REQUIRED_SVG_FILES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
