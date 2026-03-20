#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_ALIAS_RESIDUE = "IP-VALIAS-001"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
WRAPPER_TOKENS = (
    "validate_v16_cross_verification_tracks.py",
    "validate_v16_intake_evidence_core.py",
    "validate_v16_intake_evidence_quorum.py",
    "validate_v16_cross_workflow_schema.py",
    "validate_v16_dedup_monotonicity.py",
    "validate_v16_skill_path_integrity.py",
)
STRICT_TARGETS = (
    "scripts/create_identity_pack.py",
    "scripts/validate_required_contract_coverage.py",
    "scripts/validate_replay_archive_contract.py",
    "identity/store-manager/CURRENT_TASK.json",
    "identity/packs/system-requirements-analyst/CURRENT_TASK.json",
    "identity/protocol/mappings/control-plane-status.v1.6.json",
)
CONTRACT_BINDING_TARGET = "identity/protocol/mappings/contract-binding.v1.6.yaml"


def main() -> int:
    violations: list[dict[str, str]] = []

    for rel in STRICT_TARGETS:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for token in WRAPPER_TOKENS:
            if token in text:
                violations.append(
                    {
                        "file": rel,
                        "reason": "wrapper_validator_still_active",
                        "token": token,
                    }
                )

    contract_binding_text = (REPO_ROOT / CONTRACT_BINDING_TARGET).read_text(encoding="utf-8")
    for token in WRAPPER_TOKENS:
        marker = f"{token}::wrapper_compatibility_optional"
        if token in contract_binding_text and marker not in contract_binding_text:
            violations.append(
                {
                    "file": CONTRACT_BINDING_TARGET,
                    "reason": "wrapper_validator_not_demoted_to_optional_alias",
                    "token": token,
                }
            )

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "active_validator_alias_residue_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_ALIAS_RESIDUE,
        "strict_targets": list(STRICT_TARGETS),
        "contract_binding_target": CONTRACT_BINDING_TARGET,
        "violations": violations,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
