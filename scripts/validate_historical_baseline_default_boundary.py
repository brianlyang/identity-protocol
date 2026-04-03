#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_DEFAULT_BOUNDARY = "IP-HIST-DEFAULT-001"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

HISTORICAL_DOC_LITERALS = (
    "docs/governance/identity-actor-session-binding-governance-v1.6.0.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.md",
)
ALLOWED_LITERAL_HOLDERS = {
    "scripts/docs_command_contract_check.py",
    "scripts/validate_historical_baseline_default_boundary.py",
}
REQUIRED_DYNAMIC_RESOLUTION = {
    "scripts/create_identity_pack.py",
    "scripts/validate_docs_bridge_consistency.py",
    "scripts/validate_unlock_formula.py",
}
REQUIRED_DYNAMIC_TOKENS = (
    "resolve_validator_doc_defaults",
    "contract-binding.current.yaml",
)


def _read_text(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    violations: list[dict[str, str]] = []
    for path in sorted((REPO_ROOT / "scripts").glob("*.py")):
        rel = f"scripts/{path.name}"
        text = path.read_text(encoding="utf-8")
        for literal in HISTORICAL_DOC_LITERALS:
            if literal not in text:
                continue
            if rel in ALLOWED_LITERAL_HOLDERS:
                continue
            violations.append(
                {
                    "file": rel,
                    "reason": "historical_doc_literal_in_live_default_surface",
                    "literal": literal,
                }
            )

    missing_dynamic_resolution: list[str] = []
    for rel in sorted(REQUIRED_DYNAMIC_RESOLUTION):
        text = _read_text(rel)
        if not any(token in text for token in REQUIRED_DYNAMIC_TOKENS):
            missing_dynamic_resolution.append(rel)

    status = STATUS_PASS_REQUIRED if not violations and not missing_dynamic_resolution else STATUS_FAIL_REQUIRED
    payload = {
        "historical_baseline_default_boundary_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_DEFAULT_BOUNDARY,
        "historical_doc_literals": list(HISTORICAL_DOC_LITERALS),
        "allowed_literal_holders": sorted(ALLOWED_LITERAL_HOLDERS),
        "required_dynamic_resolution": sorted(REQUIRED_DYNAMIC_RESOLUTION),
        "violations": violations,
        "missing_dynamic_resolution": missing_dynamic_resolution,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
