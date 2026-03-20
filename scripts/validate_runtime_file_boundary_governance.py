#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from repo_root_resolution_common import resolve_repo_root

from protocol_infra_contract import (
    HOST_GATEWAY_DEFAULT_EGRESS_WRAPPER,
    HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER,
    HOST_GATEWAY_DEFAULT_RUNTIME_CONTRACT,
    HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER,
    INSTANCE_AUTONOMOUS_RUNTIME_TERM,
    PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_PATHS,
    PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_TERM,
    PROTOCOL_GENERATED_GATEWAY_SHELL_PATHS,
    PROTOCOL_GENERATED_GATEWAY_SHELL_TERM,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_BOUNDARY = "IP-RFILE-BDRY-001"

DEFAULT_GOV_DOC = "docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md"
DEFAULT_REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md"
DEFAULT_PROTOCOL_OVERVIEW_DOC = "identity/protocol/IDENTITY_PROTOCOL.md"
DEFAULT_STREAM_REGISTRY = "identity/protocol/mappings/stream-doc-registry.current.yaml"
DEFAULT_SEMANTIC_REGISTRY = "identity/protocol/mappings/semantic-term-registry.current.yaml"
TRACKED_COMPILED_BRIEF_ARTIFACT_TERM = "tracked_compiled_brief_artifact"
TRACKED_COMPILED_BRIEF_FROZEN_PATH_TERM = "tracked_compiled_brief_frozen_path"
LEGACY_CANONICAL_COMPATIBILITY_PATH_TERM = "legacy_canonical_compatibility_path"
INSTANCE_OWNED_TECHNICAL_DEBT_TERM = "instance_owned_technical_debt"
INSTANCE_CLEAN_PROOF_TERM = "instance_clean_proof"
PROTOCOL_RESIDUAL_ISSUE_TERM = "protocol_residual_issue"


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    try:
        current_doc = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return configured_path, "", "current_file_parse_failed"
    if not isinstance(current_doc, dict):
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _missing_tokens(text: str, tokens: list[str]) -> list[str]:
    body = str(text or "")
    return [token for token in tokens if token not in body]


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate v1.6.10 runtime file governance boundary freeze.")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--governance-doc", default=DEFAULT_GOV_DOC)
    ap.add_argument("--review-doc", default=DEFAULT_REVIEW_DOC)
    ap.add_argument("--protocol-overview-doc", default=DEFAULT_PROTOCOL_OVERVIEW_DOC)
    ap.add_argument("--stream-registry", default=DEFAULT_STREAM_REGISTRY)
    ap.add_argument("--semantic-registry", default=DEFAULT_SEMANTIC_REGISTRY)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    governance_doc = (repo_root / str(args.governance_doc)).resolve()
    review_doc = (repo_root / str(args.review_doc)).resolve()
    protocol_overview_doc = (repo_root / str(args.protocol_overview_doc)).resolve()
    stream_registry_path, stream_registry_active_file, stream_registry_alias_error = _resolve_current_yaml_alias(
        repo_root, str(args.stream_registry)
    )
    semantic_registry_path, semantic_registry_active_file, semantic_registry_alias_error = _resolve_current_yaml_alias(
        repo_root, str(args.semantic_registry)
    )

    payload: dict[str, Any] = {
        "runtime_file_boundary_governance_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_BOUNDARY,
        "governance_doc": str(governance_doc),
        "review_doc": str(review_doc),
        "protocol_overview_doc": str(protocol_overview_doc),
        "stream_registry_path": str(stream_registry_path),
        "stream_registry_active_file": stream_registry_active_file,
        "stream_registry_alias_error": stream_registry_alias_error,
        "semantic_registry_path": str(semantic_registry_path),
        "semantic_registry_active_file": semantic_registry_active_file,
        "semantic_registry_alias_error": semantic_registry_alias_error,
        "canonical_shell_term": PROTOCOL_GENERATED_GATEWAY_SHELL_TERM,
        "canonical_mirror_term": PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_TERM,
        "canonical_autonomous_term": INSTANCE_AUTONOMOUS_RUNTIME_TERM,
        "compiled_brief_term": TRACKED_COMPILED_BRIEF_ARTIFACT_TERM,
        "compiled_brief_path_term": TRACKED_COMPILED_BRIEF_FROZEN_PATH_TERM,
        "legacy_compatibility_term": LEGACY_CANONICAL_COMPATIBILITY_PATH_TERM,
        "canonical_shell_paths": list(PROTOCOL_GENERATED_GATEWAY_SHELL_PATHS),
        "canonical_mirror_paths": list(PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_PATHS),
        "governance_doc_missing_tokens": [],
        "review_doc_missing_tokens": [],
        "protocol_overview_missing_tokens": [],
        "missing_terms": [],
        "stream_registry_violations": [],
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []
    if stream_registry_alias_error:
        stale_reasons.append(f"stream_registry_alias_error:{stream_registry_alias_error}")
    if semantic_registry_alias_error:
        stale_reasons.append(f"semantic_registry_alias_error:{semantic_registry_alias_error}")
    if stale_reasons:
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    missing_paths = [
        label
        for label, path in (
            ("governance_doc_missing", governance_doc),
            ("review_doc_missing", review_doc),
            ("protocol_overview_doc_missing", protocol_overview_doc),
        )
        if not path.exists() or not path.is_file()
    ]
    if not stream_registry_path.exists() or not stream_registry_path.is_file():
        missing_paths.append("stream_registry_missing")
    if not semantic_registry_path.exists() or not semantic_registry_path.is_file():
        missing_paths.append("semantic_registry_missing")
    if missing_paths:
        payload["stale_reasons"] = missing_paths
        _emit(payload, json_only=args.json_only)
        return 1

    governance_text = governance_doc.read_text(encoding="utf-8", errors="ignore")
    review_text = review_doc.read_text(encoding="utf-8", errors="ignore")
    protocol_overview_text = protocol_overview_doc.read_text(encoding="utf-8", errors="ignore")
    stream_doc = _load_yaml(stream_registry_path)
    semantic_doc = _load_yaml(semantic_registry_path)

    expected_shell_paths = [
        HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER,
        HOST_GATEWAY_DEFAULT_EGRESS_WRAPPER,
        HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER,
    ]
    if list(PROTOCOL_GENERATED_GATEWAY_SHELL_PATHS) != expected_shell_paths:
        stale_reasons.append("canonical_shell_paths_drift")
    if list(PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_PATHS) != [HOST_GATEWAY_DEFAULT_RUNTIME_CONTRACT]:
        stale_reasons.append("canonical_mirror_paths_drift")
    if set(PROTOCOL_GENERATED_GATEWAY_SHELL_PATHS) & set(PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_PATHS):
        stale_reasons.append("shell_mirror_overlap_detected")

    governance_required_tokens = [
        "Boundary freeze (authoritative)",
        PROTOCOL_GENERATED_GATEWAY_SHELL_TERM,
        PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_TERM,
        INSTANCE_AUTONOMOUS_RUNTIME_TERM,
        HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER,
        HOST_GATEWAY_DEFAULT_EGRESS_WRAPPER,
        HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER,
        HOST_GATEWAY_DEFAULT_RUNTIME_CONTRACT,
        "Runtime default is `instance_autonomous_runtime` unless explicitly declared as `protocol_controlled_mirror_artifact`.",
        "PROTOCOL_GENERATED_GATEWAY_SHELL_PATHS",
        "PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_PATHS",
        TRACKED_COMPILED_BRIEF_ARTIFACT_TERM,
        TRACKED_COMPILED_BRIEF_FROZEN_PATH_TERM,
        LEGACY_CANONICAL_COMPATIBILITY_PATH_TERM,
        "identity/runtime/IDENTITY_COMPILED.md",
        "governed generated artifact",
        "not ordinary runtime evidence/log artifact",
        "not instance-autonomous runtime state",
        "source-first",
        INSTANCE_OWNED_TECHNICAL_DEBT_TERM,
        INSTANCE_CLEAN_PROOF_TERM,
        PROTOCOL_RESIDUAL_ISSUE_TERM,
        "No instance-clean proof, no protocol escalation.",
        "does **not** backstop `instance_owned_technical_debt`",
    ]
    review_required_tokens = [
        PROTOCOL_GENERATED_GATEWAY_SHELL_TERM,
        PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_TERM,
        INSTANCE_AUTONOMOUS_RUNTIME_TERM,
        TRACKED_COMPILED_BRIEF_ARTIFACT_TERM,
        TRACKED_COMPILED_BRIEF_FROZEN_PATH_TERM,
        LEGACY_CANONICAL_COMPATIBILITY_PATH_TERM,
        "scripts/validate_runtime_file_boundary_governance.py",
        "scripts/ci/run_semantic_clarity_probes_ci.sh",
        HOST_GATEWAY_DEFAULT_RUNTIME_CONTRACT,
        "identity/runtime/IDENTITY_COMPILED.md",
        "governed generated artifact",
        "direct manual semantic editing",
        INSTANCE_OWNED_TECHNICAL_DEBT_TERM,
        INSTANCE_CLEAN_PROOF_TERM,
        PROTOCOL_RESIDUAL_ISSUE_TERM,
        "No instance-clean proof, no protocol escalation.",
        "does **not** backstop `instance_owned_technical_debt`",
    ]
    protocol_overview_required_tokens = [
        "Core ownership and escalation contract",
        INSTANCE_OWNED_TECHNICAL_DEBT_TERM,
        INSTANCE_CLEAN_PROOF_TERM,
        PROTOCOL_RESIDUAL_ISSUE_TERM,
        "No instance-clean proof, no protocol escalation.",
        "does **not** backstop instance-owned technical debt",
        "autonomous optimization unit",
        "Host/runtime entry gaps remain a separate boundary",
    ]
    payload["governance_doc_missing_tokens"] = _missing_tokens(governance_text, governance_required_tokens)
    payload["review_doc_missing_tokens"] = _missing_tokens(review_text, review_required_tokens)
    payload["protocol_overview_missing_tokens"] = _missing_tokens(
        protocol_overview_text, protocol_overview_required_tokens
    )
    if payload["governance_doc_missing_tokens"]:
        stale_reasons.append("governance_doc_missing_required_tokens")
    if payload["review_doc_missing_tokens"]:
        stale_reasons.append("review_doc_missing_required_tokens")
    if payload["protocol_overview_missing_tokens"]:
        stale_reasons.append("protocol_overview_missing_required_tokens")

    semantic_terms = semantic_doc.get("terms") if isinstance(semantic_doc, dict) else []
    canonical_terms = {
        str(row.get("canonical_term", "")).strip()
        for row in semantic_terms
        if isinstance(row, dict) and str(row.get("canonical_term", "")).strip()
    }
    missing_terms = [
        term
        for term in (
            PROTOCOL_GENERATED_GATEWAY_SHELL_TERM,
            PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_TERM,
            INSTANCE_AUTONOMOUS_RUNTIME_TERM,
            TRACKED_COMPILED_BRIEF_ARTIFACT_TERM,
            TRACKED_COMPILED_BRIEF_FROZEN_PATH_TERM,
            LEGACY_CANONICAL_COMPATIBILITY_PATH_TERM,
            INSTANCE_OWNED_TECHNICAL_DEBT_TERM,
            INSTANCE_CLEAN_PROOF_TERM,
            PROTOCOL_RESIDUAL_ISSUE_TERM,
        )
        if term not in canonical_terms
    ]
    payload["missing_terms"] = missing_terms
    if missing_terms:
        stale_reasons.append("semantic_registry_missing_boundary_terms")

    stream_docs = stream_doc.get("stream_docs") if isinstance(stream_doc, dict) else []
    legacy_archival_docs = set(stream_doc.get("legacy_archival_docs") or []) if isinstance(stream_doc, dict) else set()
    v1610_row = next(
        (
            row
            for row in stream_docs
            if isinstance(row, dict) and str(row.get("stream_version", "")).strip() == "v1.6.10"
        ),
        None,
    )
    stream_violations: list[str] = []
    gov_rel = governance_doc.relative_to(repo_root).as_posix()
    review_rel = review_doc.relative_to(repo_root).as_posix()
    if not isinstance(v1610_row, dict):
        stream_violations.append("v1.6.10_stream_row_missing")
    else:
        if str(v1610_row.get("governance_doc", "")).strip() != gov_rel:
            stream_violations.append("v1.6.10_governance_doc_mismatch")
        if str(v1610_row.get("review_doc", "")).strip() != review_rel:
            stream_violations.append("v1.6.10_review_doc_mismatch")
    if gov_rel in legacy_archival_docs:
        stream_violations.append("v1.6.10_governance_doc_still_legacy_archival")
    if review_rel in legacy_archival_docs:
        stream_violations.append("v1.6.10_review_doc_still_legacy_archival")
    payload["stream_registry_violations"] = stream_violations
    if stream_violations:
        stale_reasons.append("stream_registry_boundary_row_invalid")

    if stale_reasons:
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["runtime_file_boundary_governance_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
