#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from control_plane_lane_registry_common import (
    ACTIVE_CONTRACT_ID,
    ACTIVE_LANE_ID,
    ALLOWED_EXECUTION_MODES,
    CONTROL_PLANE_MVP_FIXED_WRITE_SET,
    DEFAULT_CURRENT_REGISTRY_REL,
    DEFAULT_VERSIONED_REGISTRY_REL,
    ISSUE_043_INPUT_SURFACES,
    ISSUE_043_UPSTREAM_LAW_REF,
    RECEIPT_SCHEMA_VERSION,
    REGISTRY_SCHEMA_VERSION,
    REQUIRED_ROLE_BINDINGS,
    emit,
    get_lane,
    load_registry_bundle,
    normalize_registry_doc,
    route_next_role,
)


REQUIRED_DOC_TOKENS = (
    "autonomous_reinforcement",
    "split_roles",
    "bootstrap_stream",
    "accepted_upstream_law_ref",
    "allowed_entry_surfaces",
    "handoff_required",
    "post_commit_acceptance_mode",
    "forbidden_rewrite_markers",
    "receipt_schema_version",
    "warn_preservation_policy",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the identity control-plane bootstrap MVP.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    return parser


def _record(checks: list[dict[str, str]], failures: list[str], name: str, ok: bool, detail: str) -> None:
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok:
        failures.append(name)


def main() -> int:
    args = build_parser().parse_args()
    try:
        bundle = load_registry_bundle(repo_root=args.repo_root, current_registry="")
        registry_doc = normalize_registry_doc(bundle.registry_doc, repo_root=bundle.repo_root)
        checks: list[dict[str, str]] = []
        failures: list[str] = []

        target_surfaces = [bundle.repo_root / relative for relative in CONTROL_PLANE_MVP_FIXED_WRITE_SET]
        _record(
            checks,
            failures,
            "surface_existence",
            all(path.exists() for path in target_surfaces),
            "all 11 fixed-write-set surfaces exist",
        )
        _record(
            checks,
            failures,
            "current_pointer",
            str(bundle.current_doc.get("active_file")) == DEFAULT_VERSIONED_REGISTRY_REL,
            f"active_file={bundle.current_doc.get('active_file')}",
        )
        _record(
            checks,
            failures,
            "top_level_contract",
            registry_doc["schema_version"] == REGISTRY_SCHEMA_VERSION
            and registry_doc["contract_id"] == ACTIVE_CONTRACT_ID
            and registry_doc["classification"] == "net_new_control_plane_bootstrap"
            and registry_doc["receipt_schema_version"] == RECEIPT_SCHEMA_VERSION
            and registry_doc["active_lane_id"] == ACTIVE_LANE_ID,
            "schema/contract/classification/active lane are aligned",
        )
        _record(
            checks,
            failures,
            "role_bindings",
            registry_doc["role_bindings"] == REQUIRED_ROLE_BINDINGS,
            "top-level role bindings match required identities",
        )
        active_lane = get_lane(registry_doc, ACTIVE_LANE_ID)
        _record(
            checks,
            failures,
            "active_lane_fixed_write_set",
            active_lane["exact_fixed_write_set"] == CONTROL_PLANE_MVP_FIXED_WRITE_SET,
            "active lane fixed write set matches locked 11-file set",
        )
        _record(
            checks,
            failures,
            "active_lane_commands",
            active_lane["validator_command"] == "TMPDIR=$PWD/.tmp python3 scripts/validate_identity_control_plane_bootstrap_mvp.py --json-only"
            and active_lane["probe_command"] == "TMPDIR=$PWD/.tmp bash scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh",
            "active lane validator/probe commands are locked",
        )
        _record(
            checks,
            failures,
            "execution_mode_coverage",
            {lane["execution_mode"] for lane in registry_doc["lanes"]} == ALLOWED_EXECUTION_MODES,
            "registry covers split_roles, autonomous_reinforcement, and bootstrap_stream",
        )
        autonomous_lane = get_lane(registry_doc, "autonomous_reinforcement_pattern_reference")
        _record(
            checks,
            failures,
            "autonomous_lane_contract",
            autonomous_lane["handoff_required"] is False
            and autonomous_lane["allowed_entry_surfaces"] == ["root", "middle", "consumer"]
            and autonomous_lane["forbidden_rewrite_markers"] == ["owner_truth_overwrite", "root_semantic_redefinition", "whole_lane_reopen"]
            and autonomous_lane["accepted_upstream_law_ref"] == ISSUE_043_UPSTREAM_LAW_REF,
            "autonomous reinforcement lane carries the immutable ISSUE-043 pattern contract",
        )
        split_lane = get_lane(registry_doc, "split_roles_reference")
        _record(
            checks,
            failures,
            "split_roles_contract",
            split_lane["handoff_required"] is True and split_lane["execution_mode"] == "split_roles",
            "split_roles fixture remains relay-based",
        )
        _record(
            checks,
            failures,
            "read_only_issue_043_surfaces",
            active_lane["read_only_input_surfaces"] == ISSUE_043_INPUT_SURFACES
            and all((bundle.repo_root / path).exists() for path in ISSUE_043_INPUT_SURFACES)
            and set(active_lane["exact_fixed_write_set"]).isdisjoint(ISSUE_043_INPUT_SURFACES),
            "ISSUE-043 surfaces are read-only consumed inputs and not writable targets",
        )
        doc_text = (bundle.repo_root / "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md").read_text(encoding="utf-8")
        _record(
            checks,
            failures,
            "mvp_doc_tokens",
            all(token in doc_text for token in REQUIRED_DOC_TOKENS),
            "MVP doc contains the locked schema and execution-mode tokens",
        )
        _record(
            checks,
            failures,
            "receipt_schema_consistency",
            all(lane["receipt_schema_version"] == RECEIPT_SCHEMA_VERSION for lane in registry_doc["lanes"]),
            "all lanes share one receipt schema version",
        )
        active_next_role = route_next_role(active_lane)
        autonomous_next_role = route_next_role(autonomous_lane)
        split_next_role = route_next_role(split_lane)
        _record(
            checks,
            failures,
            "next_role_resolution",
            active_next_role["identity_id"] == REQUIRED_ROLE_BINDINGS["architect"]
            and autonomous_next_role["identity_id"] == REQUIRED_ROLE_BINDINGS["executor"]
            and split_next_role["identity_id"] == REQUIRED_ROLE_BINDINGS["executor"],
            "next-role routing resolves to concrete identities",
        )
        payload = {
            "status": "FAIL_REQUIRED" if failures else "PASS_REQUIRED",
            "checks": checks,
            "failures": failures,
            "registry_current": DEFAULT_CURRENT_REGISTRY_REL,
            "registry_versioned": DEFAULT_VERSIONED_REGISTRY_REL,
        }
        emit(payload, json_only=args.json_only)
        return 1 if failures else 0
    except Exception as exc:  # pragma: no cover - CLI failure path
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
