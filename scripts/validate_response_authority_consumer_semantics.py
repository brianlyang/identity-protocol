#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RESPONSE_AUTHORITY_CONSUMER = "IP-HDSTAMP-CONSUMER-001"
AUTHORITY_CONSUMER_EXEMPT = True  # Validator module; not a direct authority-consuming surface.

DEFAULT_TARGET_FILES = (
    "scripts/final_emit_governed.py",
    "scripts/render_identity_response_stamp.py",
    "scripts/compose_and_validate_governed_reply.py",
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_layer_intent_resolution.py",
    "scripts/validate_identity_response_stamp.py",
    "scripts/validate_identity_response_stamp_blocker_receipt.py",
    "scripts/validate_execution_reply_identity_coherence.py",
    "scripts/validate_instance_protocol_split_receipt.py",
)

FORBID_HOST_FALLBACK_RESOLVER = {
    "scripts/final_emit_governed.py",
    "scripts/render_identity_response_stamp.py",
    "scripts/compose_and_validate_governed_reply.py",
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_identity_response_stamp.py",
    "scripts/validate_execution_reply_identity_coherence.py",
}

FORBID_COMPAT_POINTER_LITERAL = {
    "scripts/render_identity_response_stamp.py",
    "scripts/compose_and_validate_governed_reply.py",
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_layer_intent_resolution.py",
    "scripts/validate_execution_reply_identity_coherence.py",
    "scripts/validate_instance_protocol_split_receipt.py",
}

AUTHORITY_CONSUMER_DISCOVERY_TOKENS = (
    "resolve_stamp_context(",
    "validate_runtime_egress_identity_authority(",
)
AUTHORITY_CONSUMER_EXEMPT_MARKER = "AUTHORITY_CONSUMER_EXEMPT = True"


def _resolve_repo_root(path: str) -> Path:
    base = Path(path).expanduser().resolve()
    return base


def _relative_token(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except Exception:
        return str(path.resolve())


def _call_block(lines: list[str], start_idx: int, *, span: int = 10) -> str:
    return "\n".join(lines[start_idx : start_idx + span])


def _declares_authority_consumer_exempt(text: str) -> bool:
    return AUTHORITY_CONSUMER_EXEMPT_MARKER in text


def _discover_authority_consumer_registry_gaps(repo_root: Path) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    discovered: list[str] = []
    exempted: list[str] = []
    violations: list[dict[str, Any]] = []
    scripts_root = repo_root / "scripts"
    for path in sorted(scripts_root.glob("*.py")):
        rel = _relative_token(path, repo_root)
        text = path.read_text(encoding="utf-8")
        if not any(token in text for token in AUTHORITY_CONSUMER_DISCOVERY_TOKENS):
            continue
        discovered.append(rel)
        if rel in DEFAULT_TARGET_FILES:
            continue
        if _declares_authority_consumer_exempt(text):
            exempted.append(rel)
            continue
        first_hit = next(
            (
                line.strip()
                for line in text.splitlines()
                if any(token in line for token in AUTHORITY_CONSUMER_DISCOVERY_TOKENS)
            ),
            "",
        )
        violations.append(
            {
                "file": rel,
                "line": 1,
                "violation_type": "authority_consumer_registry_coverage_missing",
                "snippet": first_hit,
            }
        )
    return discovered, exempted, violations


def _scan_file(path: Path, *, repo_root: Path, enforce_all_rules: bool = False) -> list[dict[str, Any]]:
    rel = _relative_token(path, repo_root)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    violations: list[dict[str, Any]] = []

    for idx, line in enumerate(lines):
        if "resolve_stamp_context(" in line:
            block = _call_block(lines, idx)
            if "session_id=" not in block:
                violations.append(
                    {
                        "file": rel,
                        "line": idx + 1,
                        "violation_type": "stamp_context_session_passthrough_missing",
                        "snippet": line.strip(),
                    }
                )

        if "validate_runtime_egress_identity_authority(" in line:
            block = _call_block(lines, idx)
            if "actor_id=args.actor_id" in block or 'actor_id=str(args.actor_id' in block:
                violations.append(
                    {
                        "file": rel,
                        "line": idx + 1,
                        "violation_type": "authority_validator_raw_actor_passthrough",
                        "snippet": line.strip(),
                    }
                )

    if enforce_all_rules or rel in FORBID_HOST_FALLBACK_RESOLVER:
        for idx, line in enumerate(lines):
            if "resolve_actor_id(" in line:
                violations.append(
                    {
                        "file": rel,
                        "line": idx + 1,
                        "violation_type": "host_fallback_actor_resolver_forbidden",
                        "snippet": line.strip(),
                    }
                )

    if enforce_all_rules or rel in FORBID_COMPAT_POINTER_LITERAL:
        for idx, line in enumerate(lines):
            if "active_identity.json" in line:
                violations.append(
                    {
                        "file": rel,
                        "line": idx + 1,
                        "violation_type": "compatibility_pointer_literal_forbidden",
                        "snippet": line.strip(),
                    }
                )

    return violations


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fail-close when response/headstamp authority consumers drift from strict actor/session semantics."
    )
    ap.add_argument("--repo-root", default="", help="repository root to scan; defaults to script parent repo")
    ap.add_argument(
        "--scan-file",
        action="append",
        default=[],
        help="optional relative/absolute file path to scan; when omitted, scans the default authority-consumer set",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = (
        _resolve_repo_root(args.repo_root)
        if str(args.repo_root or "").strip()
        else Path(__file__).resolve().parent.parent
    )
    requested_files = [str(x).strip() for x in (args.scan_file or []) if str(x).strip()]
    if requested_files:
        scan_paths = [
            (Path(item).expanduser().resolve() if Path(item).is_absolute() else (repo_root / item).resolve())
            for item in requested_files
        ]
    else:
        scan_paths = [(repo_root / rel).resolve() for rel in DEFAULT_TARGET_FILES]

    violations: list[dict[str, Any]] = []
    scanned_files: list[str] = []
    missing_files: list[str] = []
    for path in scan_paths:
        rel = _relative_token(path, repo_root)
        if not path.exists():
            missing_files.append(rel)
            continue
        scanned_files.append(rel)
        violations.extend(_scan_file(path, repo_root=repo_root, enforce_all_rules=bool(requested_files)))

    discovered_authority_consumers, exempt_authority_consumers, registry_gap_violations = (
        _discover_authority_consumer_registry_gaps(repo_root)
    )
    violations.extend(registry_gap_violations)

    stale_reasons: list[str] = []
    if missing_files:
        stale_reasons.append("target_file_missing")
    stale_reasons.extend(sorted({str(item.get("violation_type", "")).strip() for item in violations if item.get("violation_type")}))

    payload = {
        "response_authority_consumer_semantics_status": STATUS_PASS_REQUIRED if not violations and not missing_files else STATUS_FAIL_REQUIRED,
        "error_code": "" if not violations and not missing_files else ERR_RESPONSE_AUTHORITY_CONSUMER,
        "repo_root": str(repo_root),
        "scanned_file_count": len(scanned_files),
        "scanned_files": scanned_files,
        "discovered_authority_consumer_files": discovered_authority_consumers,
        "exempt_authority_consumer_files": exempt_authority_consumers,
        "missing_files": missing_files,
        "violation_count": len(violations),
        "violations": violations,
        "stale_reasons": stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["response_authority_consumer_semantics_status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
