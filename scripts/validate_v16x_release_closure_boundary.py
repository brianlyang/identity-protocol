#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
)
from release_readiness_runtime_closure_convergence_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
    RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
    RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RELEASE_CLOSURE = "IP-RCLOS-001"

PHILOSOPHY_DOC = "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md"
PROTOCOL_DOC = "identity/protocol/IDENTITY_PROTOCOL.md"
RUNTIME_DOC = "identity/protocol/IDENTITY_RUNTIME.md"
ISSUE_REGISTER_DOC = "docs/workbook/protocol-issue-register-v1.6.md"
GOVERNANCE_DOC = "docs/governance/identity-v1.6x-release-closure-governance.md"
REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md"

ISSUE_ROW_RE = re.compile(r"^\|\s*(ISSUE-(\d+))\b")
STREAM_VERSION_RE = re.compile(r"\bv1\.6\.(\d+)\b")
REQUIRED_TERMINAL_TRUTH_SPLIT_MARKERS = (
    "repair lane",
    "terminal-truth observation lane",
    "creator/update admission lane",
    "repair success != clean terminal truth",
)
REQUIRED_OUTER_SURFACE_E2E_BOUNDARY_MARKERS = (
    "scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh",
    "terminal_truth_boundary_projection",
    "summary_terminal_truth_boundary",
)
REQUIRED_RELEASE_READINESS_CONTINUATION_MARKERS = (
    "summary_lifecycle_status=IN_PROGRESS",
    "summary_checkpoint_kind=checkpoint",
    "stable prewrite snapshot",
    "scripts/run_release_readiness_continuation.py",
    "scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh",
    "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh",
    "scripts/ci/run_release_readiness_continuation_probes_ci.sh",
    "scripts/ci/run_release_plane_context_resolution_probes_ci.sh",
    *RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
    "caller cwd",
)
REQUIRED_REPO_GLOBAL_CLOSURE_OWNER_LANE_MARKERS = RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES
REQUIRED_REPO_GLOBAL_CLOSURE_PROOF_STRENGTH_MARKERS = (
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
)
REQUIRED_ACTIVE_REPORT_POINTER_LOCALITY_MARKERS = (
    "scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh",
    "active_execution_report pointer",
    "cross-pack absolute pointer drift",
    "pack-local candidate roots",
    "latest_identity_upgrade_report()",
    "selected_report_authority_class",
    "selection_mode",
    "active_execution_pointer_pack_local_report",
    "candidate_root_latest_pack_local_report",
)
REQUIRED_STRICT_LIVE_ACTIVE_POINTER_LOCALITY_MARKERS = (
    "scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh",
    "strict-live current-run pointer",
    "resolve_active_execution_context()",
    "pointer_candidate_root_report",
    "pointer_report_name_rehomed_candidate_root",
    "external_pointer_report_rejected",
)
REQUIRED_STRICT_LIVE_CONTRACT_RESOLUTION_MARKERS = (
    "scripts/ci/run_strict_live_contract_resolution_probes_ci.sh",
    "strict-live contract resolution",
    "strict_live_current_run_required_but_unproven",
    "sample-green fail-close",
    "pack-relative contract paths",
)
REQUIRED_WEAK_LIVE_POINTER_ABSORPTION_MARKERS = (
    "scripts/ci/run_identity_weak_live_linkage_pointer_locality_probes_ci.sh",
    "validate_identity_weak_live_linkage.py",
    "current_run_pointer_resolution_mode",
    "external_pointer_report_rejected",
)
REQUIRED_EXECUTION_REPORT_SELECTION_CONVERGENCE_MARKERS = (
    "scripts/ci/run_execution_report_selection_convergence_probes_ci.sh",
    "execution_report_selection_common.py",
    "primary execution report selection",
    "derivative report artifacts",
    "validate_execution_report_freshness.py",
    "validate_identity_protocol_baseline_freshness.py",
    "validate_run_id_report_selection.py",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_issue_register(text: str) -> tuple[str, list[str]]:
    max_issue_num = 0
    closed_versions: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("| ISSUE-"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 4:
            continue
        issue_cell = parts[1]
        status_cell = parts[2]
        stream_cell = parts[3].strip().strip("`")
        match = ISSUE_ROW_RE.match(f"| {issue_cell}")
        if match:
            max_issue_num = max(max_issue_num, int(match.group(2)))
        if status_cell == "CLOSED":
            version_match = STREAM_VERSION_RE.search(stream_cell)
            if version_match:
                closed_versions.add(f"v1.6.{int(version_match.group(1))}")
    if max_issue_num <= 0:
        raise ValueError("issue_register_missing_issue_rows")
    highest_issue = f"ISSUE-{max_issue_num:03d}"
    ordered_versions = sorted(closed_versions, key=lambda token: int(token.split(".")[-1]))
    return highest_issue, ordered_versions


def _contains_issue_horizon(text: str, highest_issue: str) -> bool:
    pattern = rf"`ISSUE-001`\s+through\s+`{re.escape(highest_issue)}`"
    return re.search(pattern, text) is not None


def _collect_issue_horizon_targets(text: str) -> list[str]:
    pattern = re.compile(r"`ISSUE-001`\s+through\s+`(ISSUE-\d+)`")
    return [str(match.group(1)).strip() for match in pattern.finditer(text)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v1.6.x release-closure boundary docs against the current workbook horizon.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    philosophy_path = (repo_root / PHILOSOPHY_DOC).resolve()
    protocol_path = (repo_root / PROTOCOL_DOC).resolve()
    runtime_path = (repo_root / RUNTIME_DOC).resolve()
    issue_register_path = (repo_root / ISSUE_REGISTER_DOC).resolve()
    governance_path = (repo_root / GOVERNANCE_DOC).resolve()
    review_path = (repo_root / REVIEW_DOC).resolve()

    payload: dict[str, Any] = {
        "v16x_release_closure_boundary_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "philosophy_doc": str(philosophy_path),
        "protocol_doc": str(protocol_path),
        "runtime_doc": str(runtime_path),
        "issue_register_doc": str(issue_register_path),
        "governance_doc": str(governance_path),
        "review_doc": str(review_path),
        "current_issue_horizon": "",
        "highest_closed_v16_stream_version": "",
        "stale_reasons": [],
    }

    try:
        for path in (
            philosophy_path,
            protocol_path,
            runtime_path,
            issue_register_path,
            governance_path,
            review_path,
        ):
            if not path.exists():
                raise FileNotFoundError(f"missing_required_doc:{path}")

        philosophy_text = _read(philosophy_path)
        protocol_text = _read(protocol_path)
        runtime_text = _read(runtime_path)
        issue_register_text = _read(issue_register_path)
        governance_text = _read(governance_path)
        review_text = _read(review_path)
        highest_issue, closed_versions = _parse_issue_register(issue_register_text)
    except Exception as exc:
        payload["error_code"] = ERR_RELEASE_CLOSURE
        payload["stale_reasons"] = [str(exc)]
        _emit(payload, json_only=args.json_only)
        return 1

    highest_version = closed_versions[-1] if closed_versions else ""
    payload["current_issue_horizon"] = highest_issue
    payload["highest_closed_v16_stream_version"] = highest_version

    stale_reasons: list[str] = []

    if "source-order" not in philosophy_text or "reading-order" not in philosophy_text or "adjudication-order" not in philosophy_text:
        stale_reasons.append("philosophy_root_order_markers_missing")

    for label, text in (
        ("governance_doc", governance_text),
        ("review_doc", review_text),
    ):
        if PHILOSOPHY_DOC not in text:
            stale_reasons.append(f"{label}_missing_philosophy_anchor")
        if PROTOCOL_DOC not in text:
            stale_reasons.append(f"{label}_missing_protocol_anchor")
        if RUNTIME_DOC not in text:
            stale_reasons.append(f"{label}_missing_runtime_anchor")
        if "root-closed" not in text or "machine-closed" not in text or "runtime-closed" not in text:
            stale_reasons.append(f"{label}_missing_root_machine_runtime_closure_markers")
        for marker in REQUIRED_TERMINAL_TRUTH_SPLIT_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_terminal_truth_split_marker:{marker}")
        for marker in REQUIRED_OUTER_SURFACE_E2E_BOUNDARY_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_outer_surface_e2e_marker:{marker}")
        for marker in REQUIRED_RELEASE_READINESS_CONTINUATION_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_release_readiness_continuation_marker:{marker}")
        for marker in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS:
            if marker not in text:
                stale_reasons.append(
                    f"{label}_missing_active_runtime_closure_projection_marker:{marker}"
                )
        for marker in REQUIRED_REPO_GLOBAL_CLOSURE_OWNER_LANE_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_repo_global_closure_owner_lane_marker:{marker}")
        for marker in REQUIRED_REPO_GLOBAL_CLOSURE_PROOF_STRENGTH_MARKERS:
            if marker not in text:
                stale_reasons.append(
                    f"{label}_missing_repo_global_closure_proof_strength_marker:{marker}"
                )
        for marker in REQUIRED_ACTIVE_REPORT_POINTER_LOCALITY_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_active_report_pointer_locality_marker:{marker}")
        for marker in REQUIRED_STRICT_LIVE_ACTIVE_POINTER_LOCALITY_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_strict_live_active_pointer_locality_marker:{marker}")
        for marker in REQUIRED_STRICT_LIVE_CONTRACT_RESOLUTION_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_strict_live_contract_resolution_marker:{marker}")
        for marker in REQUIRED_WEAK_LIVE_POINTER_ABSORPTION_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_weak_live_pointer_absorption_marker:{marker}")
        for marker in REQUIRED_EXECUTION_REPORT_SELECTION_CONVERGENCE_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_execution_report_selection_convergence_marker:{marker}")
        for marker in RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_transport_fleet_closure_convergence_marker:{marker}")
        for marker in RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_active_runtime_pack_closure_convergence_marker:{marker}")
        for marker in RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS:
            if marker not in text:
                stale_reasons.append(
                    f"{label}_missing_workspace_runtime_closure_command_convergence_marker:{marker}"
                )
        if not _contains_issue_horizon(text, highest_issue):
            stale_reasons.append(f"{label}_issue_horizon_mismatch")
        for target_issue in _collect_issue_horizon_targets(text):
            if target_issue != highest_issue:
                stale_reasons.append(f"{label}_stale_issue_horizon:{target_issue}")
        if highest_version and highest_version not in text:
            stale_reasons.append(f"{label}_missing_highest_v16_stream_version")

    payload["v16x_release_closure_boundary_status"] = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload["error_code"] = "" if not stale_reasons else ERR_RELEASE_CLOSURE
    payload["stale_reasons"] = stale_reasons
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
