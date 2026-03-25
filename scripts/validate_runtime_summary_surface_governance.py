#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from governed_runtime_summary_surface_common import (
    SURFACE_PROFILES,
    build_governed_runtime_summary_surface_payload,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ScriptBindingSpec:
    name: str
    script_rel: str
    surface_id: str
    required_tokens: tuple[str, ...]


@dataclass(frozen=True)
class DocAnchorSpec:
    rel_path: str
    required_markers: tuple[str, ...]


SCRIPT_BINDINGS: tuple[ScriptBindingSpec, ...] = (
    ScriptBindingSpec(
        name="release_readiness_summary",
        script_rel="scripts/release_readiness_check.py",
        surface_id="release_readiness_summary",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"release_readiness_summary"',
        ),
    ),
    ScriptBindingSpec(
        name="semantic_tuple_three_plane",
        script_rel="scripts/report_three_plane_status.py",
        surface_id="semantic_tuple_three_plane",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"semantic_tuple_three_plane"',
        ),
    ),
    ScriptBindingSpec(
        name="protocol_lane_audit_summary",
        script_rel="scripts/render_protocol_lane_audit_summary.py",
        surface_id="protocol_lane_audit_summary",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"protocol_lane_audit_summary"',
        ),
    ),
    ScriptBindingSpec(
        name="full_identity_protocol_scan_summary",
        script_rel="scripts/full_identity_protocol_scan.py",
        surface_id="full_identity_protocol_scan_summary",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"full_identity_protocol_scan_summary"',
        ),
    ),
    ScriptBindingSpec(
        name="control_plane_status_artifact",
        script_rel="scripts/render_control_plane_status.py",
        surface_id="control_plane_status_artifact",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"control_plane_status_artifact"',
        ),
    ),
    ScriptBindingSpec(
        name="control_plane_budget_artifact",
        script_rel="scripts/render_control_plane_budget.py",
        surface_id="control_plane_budget_artifact",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"control_plane_budget_artifact"',
        ),
    ),
)

DOC_ANCHORS: tuple[DocAnchorSpec, ...] = (
    DocAnchorSpec(
        rel_path="docs/governance/identity-v1.6x-release-closure-governance.md",
        required_markers=(
            "three-plane verdict remains a governed outer runtime-state surface",
            "`scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.",
            "All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md",
        required_markers=(
            "three-plane verdict remains a governed outer runtime-state surface",
            "`scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.",
            "All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/release/identity-v1.6x-release-closure-summary.md",
        required_markers=(
            "three-plane verdict remains a governed outer runtime-state surface",
            "`scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/governance/identity-codex-launcher-governance-v1.6.14.md",
        required_markers=(
            "`scripts/render_protocol_lane_audit_summary.py` remains a single-lane formal control-plane summary surface on an outer runtime-state layer.",
            "It must not replace root-law owners, stream-owner governance/review surfaces, direct validator receipts, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md",
        required_markers=(
            "`scripts/render_protocol_lane_audit_summary.py` remains a single-lane formal control-plane summary surface on an outer runtime-state layer.",
            "It must not replace root-law owners, stream-owner governance/review surfaces, direct validator receipts, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/governance/github-native-control-plane-specialization-v1.6.3.md",
        required_markers=(
            "`scripts/render_control_plane_status.py` remains a machine control-plane status summary surface on an outer control-plane layer.",
            "It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6.3.md",
        required_markers=(
            "`scripts/render_control_plane_status.py` remains a machine control-plane status summary surface on an outer control-plane layer.",
            "It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/governance/github-native-control-plane-specialization-v1.6.3.md",
        required_markers=(
            "`scripts/render_control_plane_budget.py` remains a machine control-plane budget summary surface on an outer control-plane layer.",
            "It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6.3.md",
        required_markers=(
            "`scripts/render_control_plane_budget.py` remains a machine control-plane budget summary surface on an outer control-plane layer.",
            "It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _validate_script_bindings(repo_root: Path) -> tuple[str, list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for spec in SCRIPT_BINDINGS:
        path = (repo_root / spec.script_rel).resolve()
        text = _read_text(path)
        enforced = True
        if spec.surface_id == "release_readiness_summary":
            enforced = "--summary-out" in text or "summary_out" in text
        missing_tokens = [token for token in spec.required_tokens if token not in text] if enforced else []
        row = {
            "name": spec.name,
            "script_rel": spec.script_rel,
            "surface_id": spec.surface_id,
            "exists": path.exists(),
            "enforced": enforced,
            "missing_tokens": missing_tokens,
        }
        rows.append(row)
        if not path.exists():
            errors.append(f"missing_script:{spec.script_rel}")
        elif enforced and missing_tokens:
            errors.append(f"script_tokens_missing:{spec.script_rel}:{','.join(missing_tokens)}")
    return (STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED, rows, errors)


def _validate_doc_anchors(repo_root: Path) -> tuple[str, list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for spec in DOC_ANCHORS:
        path = (repo_root / spec.rel_path).resolve()
        text = _read_text(path)
        missing_markers = [marker for marker in spec.required_markers if marker not in text]
        row = {
            "rel_path": spec.rel_path,
            "exists": path.exists(),
            "missing_markers": missing_markers,
        }
        rows.append(row)
        if not path.exists():
            errors.append(f"missing_doc:{spec.rel_path}")
        elif missing_markers:
            errors.append(f"doc_markers_missing:{spec.rel_path}:{len(missing_markers)}")
    return (STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED, rows, errors)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate governance markers for governed outer runtime summary surfaces.")
    ap.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(str(args.repo_root or "").strip()).expanduser().resolve()
    script_status, script_rows, script_errors = _validate_script_bindings(repo_root)
    doc_status, doc_rows, doc_errors = _validate_doc_anchors(repo_root)
    errors = [*script_errors, *doc_errors]
    payload = {
        "runtime_summary_surface_governance_status": STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED,
        "repo_root": str(repo_root),
        "script_source_status": script_status,
        "doc_anchor_status": doc_status,
        "script_bindings_checked": script_rows,
        "doc_anchors_checked": doc_rows,
        "surface_profiles": {
            surface_id: build_governed_runtime_summary_surface_payload(surface_id)
            for surface_id in sorted(SURFACE_PROFILES)
        },
        "error_count": len(errors),
        "errors": errors,
    }
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if not errors:
            print("[PASS] runtime summary surface governance validated.")
        else:
            print(f"[FAIL] runtime summary surface governance drift: {len(errors)}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
