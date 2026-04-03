#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
from typing import Iterable

FAMILY_ID = "host_visible_native_attestation_projection"
CLASSIFICATION = "net_new_governed_family_bootstrap"
FAIL_CLOSE_TOKEN = "none_required_bootstrap_lane_stable"

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]

FIXED_WRITE_SET = (
    "identity-protocol-local/docs/governance/identity-host-visible-native-attestation-projection-governance-v1.6.x.md",
    "identity-protocol-local/docs/review/protocol-remediation-audit-ledger-v1.6.x-host-visible-native-attestation-projection.md",
    "identity-protocol-local/scripts/host_visible_native_attestation_projection_common.py",
    "identity-protocol-local/scripts/validate_host_visible_native_attestation_projection.py",
    "identity-protocol-local/scripts/ci/run_host_visible_native_attestation_projection_probes_ci.sh",
)

READ_ONLY_INPUT_SURFACES = (
    "identity-protocol-local/scripts/native_chat_headstamp_common.py",
    "identity-protocol-local/scripts/render_identity_response_stamp.py",
    "identity-protocol-local/scripts/full_identity_protocol_scan.py",
)

MACHINE_VISIBLE_FIELDS = (
    "current_chat_surface_native_machine_attested",
    "next_hop_admission_status",
    "host_visible_post_check_metrics_status",
)

EXCLUDED_SURFACES = (
    "ISSUE-040",
    "ISSUE-041",
    "ISSUE-042",
    "ISSUE-043",
    "ISSUE-044",
    "ISSUE-045",
    "ISSUE-046",
    "ISSUE-047",
    "ISSUE-048",
    "requested_session_binding_required",
    "broader headstamp",
    "handoff",
    "continuation semantics",
)

EVIDENCE_LOG = "identity-protocol-local/.tmp/full_identity_protocol_scan_base_repo_architect.log"
EVIDENCE_ANCHORS = (
    "current_chat_surface_native_machine_attested=false",
    "next_hop_admission_status=FAIL_REQUIRED",
    '"host_visible_post_check_metrics_status": "FAIL_REQUIRED"',
    "surface_class=host_native_chat_panel",
    "native_attestation_wiring_capability=unavailable",
)

EVIDENCE_LOG_ANCHOR_GROUPS = (
    (
        "current_chat_surface_native_machine_attested=false",
        '"current_chat_surface_native_machine_attested":false',
        '"current_chat_surface_native_machine_attested": false',
    ),
    (
        "next_hop_admission_status=FAIL_REQUIRED",
        '"next_hop_admission_status":"FAIL_REQUIRED"',
        '"next_hop_admission_status": "FAIL_REQUIRED"',
    ),
    (
        '"host_visible_post_check_metrics_status": "FAIL_REQUIRED"',
        "host_visible_post_check_metrics_status=FAIL_REQUIRED",
    ),
    (
        "surface_class=host_native_chat_panel",
        '"surface_class":"host_native_chat_panel"',
        '"surface_class": "host_native_chat_panel"',
    ),
    (
        "native_attestation_wiring_capability=unavailable",
        '"native_attestation_wiring_capability":"unavailable"',
        '"native_attestation_wiring_capability": "unavailable"',
    ),
)

READ_ONLY_MINIMUM_TOKENS = {
    "identity-protocol-local/scripts/native_chat_headstamp_common.py": (
        "current_chat_surface_native_machine_attested",
    ),
    "identity-protocol-local/scripts/render_identity_response_stamp.py": (
        "current_chat_surface_native_machine_attested",
        "next_hop_admission_status",
    ),
    "identity-protocol-local/scripts/full_identity_protocol_scan.py": (
        "next_hop_admission_status",
        "host_visible_post_check_metrics_status",
    ),
}


def repo_path(relative_path: str, env_var: str | None = None) -> Path:
    override = os.environ.get(env_var) if env_var else None
    if override:
        path = Path(override)
        return path if path.is_absolute() else WORKSPACE_ROOT / path
    return WORKSPACE_ROOT / relative_path


def read_text(relative_path: str, env_var: str | None = None) -> str:
    return repo_path(relative_path, env_var).read_text(encoding="utf-8")


def contains_all_tokens(text: str, tokens: Iterable[str]) -> list[str]:
    return [token for token in tokens if token not in text]


def governance_required_tokens() -> tuple[str, ...]:
    return (
        FAMILY_ID,
        CLASSIFICATION,
        FAIL_CLOSE_TOKEN,
        *MACHINE_VISIBLE_FIELDS,
        "requested_session_binding_required",
        "ISSUE-040 through ISSUE-048",
        *READ_ONLY_INPUT_SURFACES,
        EVIDENCE_LOG,
        *EVIDENCE_ANCHORS,
    )


def review_required_tokens() -> tuple[str, ...]:
    return (
        FAMILY_ID,
        CLASSIFICATION,
        "host_native_chat_panel",
        *MACHINE_VISIBLE_FIELDS,
        "requested_session_binding_required",
        "ISSUE-040 through ISSUE-048",
        EVIDENCE_LOG,
        *EVIDENCE_ANCHORS,
        *READ_ONLY_INPUT_SURFACES,
        FAIL_CLOSE_TOKEN,
    )
