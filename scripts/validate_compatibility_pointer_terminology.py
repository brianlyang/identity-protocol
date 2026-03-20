#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_POINTER_TERMINOLOGY = "IP-COMPAT-PTR-001"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

FORBIDDEN_PUBLIC_FIELD_TOKENS = (
    '"canonical_session_pointer"',
    '"session_pointer_canonical_path"',
)
REQUIRED_NEW_FIELD_TOKENS = {
    "scripts/sync_session_identity.py": ("apply_compatibility_mirror_pointer_path(",),
    "scripts/repair_actor_session_authority_residue.py": ("apply_compatibility_mirror_pointer_path(",),
    "scripts/repair_actor_session_primary_conflicts.py": ('"compatibility_mirror_pointer_path"',),
    "scripts/identity_creator.py": ("SESSION_POINTER_COMPATIBILITY_PATH_FIELD",),
    "scripts/ci/run_semantic_clarity_probes_ci.sh": ('"compatibility_mirror_pointer_path"',),
}


def main() -> int:
    violations: list[dict[str, str]] = []
    for rel, required_tokens in REQUIRED_NEW_FIELD_TOKENS.items():
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        if not any(token in text for token in required_tokens):
            violations.append(
                {
                    "file": rel,
                    "reason": "required_compatibility_pointer_token_missing",
                    "token": " | ".join(required_tokens),
                }
            )
        for forbidden in FORBIDDEN_PUBLIC_FIELD_TOKENS:
            if forbidden in text:
                violations.append(
                    {
                        "file": rel,
                        "reason": "legacy_canonical_pointer_token_present",
                        "token": forbidden,
                    }
                )

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "compatibility_pointer_terminology_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_POINTER_TERMINOLOGY,
        "required_targets": sorted(REQUIRED_NEW_FIELD_TOKENS),
        "violations": violations,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
