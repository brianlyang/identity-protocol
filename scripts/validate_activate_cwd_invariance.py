#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_ACTIVATE_CWD_INVARIANCE = "IP-ACT-CWD-001"

DEFAULT_TARGET = "scripts/identity_creator.py"

REQUIRED_TOKENS = {
    "activate_catalog_canonicalization": 'local_catalog_activate = str(Path(args.catalog).expanduser().resolve())',
    "activate_repo_catalog_canonicalization": 'repo_catalog_activate = str(Path(args.repo_catalog).expanduser().resolve())',
    "activate_protocol_root_canonicalization": 'protocol_root_activate = str(resolve_protocol_root(args.protocol_root or str(PROTOCOL_ROOT)))',
    "activate_runtime_guard_uses_canonical_catalog": "local_catalog_activate,",
    "activate_runtime_guard_uses_canonical_repo_catalog": "repo_catalog_activate,",
    "activate_switch_receipt_canonicalization": 'switch_intent_receipt_activate = (',
    "activate_cross_actor_receipt_canonicalization": 'cross_actor_receipt_activate = (',
    "sync_subprocess_protocol_root_cwd": "cwd=str(protocol_root_resolved)",
}


def _resolve_repo_root(raw: str) -> Path:
    if str(raw or "").strip():
        return Path(raw).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fail-close when identity activation loses protocol-root/CWD invariance safeguards."
    )
    ap.add_argument("--repo-root", default="", help="repository root to scan; defaults to script parent repo")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = _resolve_repo_root(args.repo_root)
    target = (repo_root / DEFAULT_TARGET).resolve()
    violations: list[dict[str, str | int]] = []
    stale_reasons: list[str] = []

    if not target.exists():
        stale_reasons.append("identity_creator_missing")
        payload = {
            "activate_cwd_invariance_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_ACTIVATE_CWD_INVARIANCE,
            "repo_root": str(repo_root),
            "target_file": str(target),
            "violations": [],
            "stale_reasons": stale_reasons,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    text = target.read_text(encoding="utf-8")
    for violation_type, token in REQUIRED_TOKENS.items():
        if token in text:
            continue
        violations.append(
            {
                "file": DEFAULT_TARGET,
                "line": 1,
                "violation_type": violation_type,
                "snippet": token,
            }
        )
        stale_reasons.append(violation_type)

    payload = {
        "activate_cwd_invariance_status": STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED,
        "error_code": "" if not violations else ERR_ACTIVATE_CWD_INVARIANCE,
        "repo_root": str(repo_root),
        "target_file": DEFAULT_TARGET,
        "violations": violations,
        "stale_reasons": stale_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
