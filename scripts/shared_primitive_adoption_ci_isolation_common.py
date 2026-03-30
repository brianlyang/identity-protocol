#!/usr/bin/env python3
"""Common contract rows for shared primitive adoption CI isolation."""

from __future__ import annotations

from dataclasses import dataclass

LANE_ID = "shared_primitive_adoption_ci_isolation_residual"
GOVERNING_LAW = "shared_primitive_adoption_ci_must_be_isolated_from_preexisting_dirty_state_and_nonlane_context"

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MISSING = "ERR_MISSING"
ERR_SCOPE = "ERR_SCOPE"
ERR_DIRTY_STATE = "ERR_DIRTY_STATE"
ERR_NONLANE = "ERR_NONLANE"

FIXED_WRITE_SET = (
    "scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh",
    "docs/governance/identity-shared-primitive-adoption-ci-isolation-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-shared-primitive-adoption-ci-isolation.md",
    "scripts/shared_primitive_adoption_ci_isolation_common.py",
    "scripts/validate_shared_primitive_adoption_ci_isolation.py",
)

FORBIDDEN_SCOPE_TOKENS = (
    "scripts/validate_protocol_root_*.py",
    "scripts/ci/run_protocol_root_*_probes_ci.sh",
    "protocol_root_probe_shadow_common.sh",
)

FORBIDDEN_DIRTY_STATE_TOKENS = (
    "git status",
    "git diff --name-only",
    "git ls-files --others",
)

REQUIRED_GOVERNANCE_TOKENS = (
    LANE_ID,
    GOVERNING_LAW,
    "pre-existing dirty/untracked state",
    "nonlane context",
    "ambient root-family wildcard expansion is not admitted",
)

REQUIRED_REVIEW_TOKENS = (
    LANE_ID,
    GOVERNING_LAW,
    "python3 scripts/validate_shared_primitive_adoption_ci_isolation.py --json-only",
    "bash scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh",
    "one isolated commit for this residual lane only",
)

REQUIRED_CI_TOKENS = (
    "FIXED_WRITE_SET_REL=(",
    "validate_shared_primitive_adoption_ci_isolation.py",
    "ambient_scope_dependency",
    "dirty_state_dependency",
)


@dataclass(frozen=True)
class ContractRow:
    contract_id: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            "contract_id": self.contract_id,
            "status": self.status,
            "detail": self.detail,
        }


def build_contract_row(contract_id: str, ok: bool, detail: str) -> dict[str, str]:
    return ContractRow(
        contract_id=contract_id,
        status=STATUS_PASS_REQUIRED if ok else STATUS_FAIL_REQUIRED,
        detail=detail,
    ).as_dict()
