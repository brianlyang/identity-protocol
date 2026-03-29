#!/usr/bin/env python3
"""
Validate command snippets in governance docs against current script contracts.

Scope:
- ensures referenced scripts exist
- for python script commands, verifies referenced CLI flags appear in `--help` output

This is a lightweight guardrail to prevent "doc command drift".

IMPORTANT:
- This checker is Repo-plane governance only.
- Do NOT wire this script into instance runtime closure (validate/update/heal/e2e main chain).
- Instance-plane must remain fail-operational for recoverable issues.
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import List, Set, Tuple

import yaml

from contract_binding_mapping_common import is_stream_version
from doc_command_surface_common import (
    MODE_LIVE_CONTRACT,
    canonicalize_repo_self_prefix_path,
    doc_command_surface_rows_from_doc,
    load_doc_command_surface,
    repo_self_prefixes_from_doc,
    resolve_doc_command_surface_mode,
    resolve_doc_script_target,
    surface_mode_profiles_from_doc,
)
from registry_alias_control_plane_common import STREAM_DOC_REGISTRY_CURRENT, resolve_current_yaml_alias
from runtime_summary_surface_governance_common import (
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_VALIDATOR,
)
from reference_visual_atlas_governance_common import discover_visual_atlas_governance_scripts


INDEX_PATH = "docs/governance/AUDIT_SNAPSHOT_INDEX.md"
STREAM_DOC_REGISTRY_PATH = STREAM_DOC_REGISTRY_CURRENT
PLUGIN_DOC_CONTROL_PATH = "identity/protocol/plugins/PLUGIN_DOC_CONTROL.current.yaml"
REQUIRED_CURRENT_DOC_PATTERNS = [
    r"^docs/governance/identity-token-efficiency-and-skill-parity-governance-v\d+\.\d+\.\d+\.md$",
    r"^docs/governance/identity-token-governance-audit-checklist-v\d+\.\d+\.\d+\.md$",
]
LEGACY_DOC_VERSION_RE = re.compile(r"-v(?P<major>\d+)\.(?P<minor>\d+)(?:\.\d+)?\.md$")
V160_HISTORICAL_DOC = "docs/governance/identity-actor-session-binding-governance-v1.6.0.md"
V160_REQUIRED_MARKERS = (
    "historical baseline + traceability ledger",
    "Current-state contract resolution must follow active stream registry first",
    "historical replay context only and must not be treated as current wiring contract input",
    "stream-doc-registry.current.yaml",
    "contract-binding.current.yaml",
    "control-plane-invariants.current.yaml",
    "control-plane-budget.current.yaml",
    "control-plane-status.current.yaml",
    "github-control-plane-offload.current.yaml",
)
V160_FORBIDDEN_MARKERS = (
    "This document is the only normative execution entrypoint for actor-session-binding governance in v1.6.",
    "This file is topic-canonical for v1.6 planning/execution.",
)
V150_GOV_HISTORICAL_DOC = "docs/governance/identity-actor-session-binding-governance-v1.5.0.md"
V150_GOV_REQUIRED_MARKERS = (
    "historical baseline for v1.5 actor-session-binding closure",
    "stream-doc-registry.current.yaml",
    "contract-binding.current.yaml",
    "control-plane-invariants.current.yaml",
    "control-plane-budget.current.yaml",
    "control-plane-status.current.yaml",
    "github-control-plane-offload.current.yaml",
    "not the active normative execution entrypoint",
    "historical replay context only and must not be treated as current wiring contract input",
)
V150_GOV_FORBIDDEN_MARKERS = (
    "This document is the only normative execution entrypoint for actor-session-binding governance.",
    "This file is **topic-canonical** for actor-session-binding governance.",
)
V150_REVIEW_HISTORICAL_DOC = "docs/review/protocol-remediation-audit-ledger-v1.5.md"
V150_REVIEW_REQUIRED_MARKERS = (
    "historical v1.5 review ledger",
    "stream-doc-registry.current.yaml",
    "contract-binding.current.yaml",
    "control-plane-invariants.current.yaml",
    "control-plane-budget.current.yaml",
    "control-plane-status.current.yaml",
    "github-control-plane-offload.current.yaml",
    "historical replay context only and must not be treated as current wiring contract input",
)
V150_REVIEW_FORBIDDEN_MARKERS = (
    "This file is the only normative execution entrypoint for actor-session-binding governance.",
    "This file is **topic-canonical** for actor-session-binding governance.",
)
V16_REVIEW_HISTORICAL_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.md"
V16_REVIEW_REQUIRED_MARKERS = (
    "historical/replay trace; it is **not** the standalone source for current-state protocol judgments",
    "stream-doc-registry.current.yaml",
    "contract-binding.current.yaml",
    "control-plane-invariants.current.yaml",
    "control-plane-budget.current.yaml",
    "control-plane-status.current.yaml",
    "github-control-plane-offload.current.yaml",
    "historical replay context only and must not be treated as current wiring contract input",
)
V16_REVIEW_FORBIDDEN_MARKERS = (
    "it is **the** standalone source for current-state protocol judgments",
    "This document is the only normative execution entrypoint for actor-session-binding governance in v1.6.",
)
V166_TEMP_PATH_GUARDED_DOCS = {
    "docs/governance/identity-host-unique-channel-governance-v1.6.6.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.6.md",
}
V166_FORBIDDEN_EPHEMERAL_PATH_MARKERS = (
    "/tmp/",
    "/private/var/folders/",
)
DOC_PATH_VALUE_FLAGS = {
    "--catalog",
    "--local-catalog",
    "--repo-catalog",
}
DOC_SEMANTIC_SKIP_FLAGS = {
    "--out",
    "--reply-file",
    "--receipt",
    "--report",
    "--execution-report",
    "--out-dir",
}
DOC_SEMANTIC_SAFE_SCRIPTS = {
    "scripts/validate_fixture_runtime_boundary.py",
    "scripts/validate_protocol_entry_candidate_bridge.py",
    "scripts/render_identity_response_stamp.py",
    "scripts/validate_headstamp_recurrence_closure.py",
}
DOC_SEMANTIC_PATH_ERROR_MARKERS = (
    "repo catalog not found:",
    "catalog not found:",
    "missing catalog:",
)


def _resolve_repo_root(raw_repo_root: str) -> Path:
    token = str(raw_repo_root or "").strip()
    if token:
        return Path(token).expanduser().resolve()
    cwd = Path.cwd().resolve()
    if (cwd / INDEX_PATH).exists() and (cwd / "scripts").exists() and (cwd / "identity").exists():
        return cwd
    return Path(__file__).resolve().parent.parent


def _resolve_workspace_root(repo_root: Path) -> Path:
    return repo_root.parent if repo_root.name == "identity-protocol-local" else repo_root


def extract_backtick_commands(text: str) -> List[str]:
    return re.findall(r"`([^`]+)`", text)


def _snippet_to_commands(snippet: str) -> List[str]:
    # Split fenced-like inline blocks into executable command lines.
    # Supports simple "\" line continuation.
    if "\n" not in snippet:
        return [snippet.strip()]
    lines = [ln.rstrip() for ln in snippet.splitlines()]
    cmds: List[str] = []
    cur = ""
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#") or s in {"bash", "sh", "zsh"}:
            continue
        if cur:
            cur = f"{cur} {s}"
        else:
            cur = s
        if cur.endswith("\\"):
            cur = cur[:-1].rstrip()
            continue
        cmds.append(cur)
        cur = ""
    if cur:
        cmds.append(cur)
    return cmds


def _docs_from_index(repo_root: Path) -> List[str]:
    p = repo_root / INDEX_PATH
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8")
    docs = re.findall(r"`(docs/(?:governance|review)/[^`]+?\.md)`", text)
    # keep order + dedup
    seen = set()
    out: List[str] = []
    for d in docs:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def _canonical_script_rel(script_rel: str) -> str:
    repo_root = _resolve_repo_root("")
    return canonicalize_repo_self_prefix_path(
        script_rel,
        repo_name=repo_root.name,
        self_prefixes=("identity-protocol-local",),
    )


def _norm_path(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _requires_static_alias_ref_row(doc: str) -> bool:
    normalized = _norm_path(doc)
    if not normalized.endswith(".md"):
        return False
    return (
        normalized.startswith("docs/governance/")
        or normalized.startswith("docs/release/")
        or normalized.startswith("docs/workbook/")
        or normalized.startswith("docs/review/")
        or normalized.startswith("docs/references/")
        or normalized.startswith("identity/protocol/plugins/")
    )


def _as_str_list(value: object) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        token = _norm_path(str(item))
        if token:
            out.append(token)
    return out


def _is_legacy_v16_or_earlier_doc(rel: str) -> bool:
    normalized = _norm_path(rel)
    if not normalized.endswith(".md"):
        return False
    if not (
        normalized.startswith("docs/governance/")
        or normalized.startswith("docs/review/")
    ):
        return False
    m = LEGACY_DOC_VERSION_RE.search(normalized)
    if not m:
        return False
    major = int(m.group("major"))
    minor = int(m.group("minor"))
    return major < 1 or (major == 1 and minor <= 6)


def _is_release_doc(rel: str) -> bool:
    normalized = _norm_path(rel)
    return normalized.startswith("docs/release/") and normalized.endswith(".md")


def _load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_current_markdown_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "current_file_missing"
    if not configured_path.name.endswith(".current.md"):
        return configured_path, ""
    text = configured_path.read_text(encoding="utf-8")
    refs = re.findall(r"`([^`]+\.md)`", text)
    active_file = ""
    for candidate in refs:
        rel = _norm_path(candidate)
        if rel and not rel.endswith(".current.md"):
            active_file = rel
            break
    if not active_file:
        return configured_path, "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, "active_file_not_found"
    return active_path, ""


def _run_visual_atlas_governance_checks(repo_root: Path, failures: List[str]) -> None:
    validator_paths = discover_visual_atlas_governance_scripts(repo_root)
    if not validator_paths:
        failures.append("[MISSING_SCRIPT] no scripts/validate_*_visual_atlas_governance.py validators found")
        return

    for validator_path in validator_paths:
        proc = subprocess.run(
            [sys.executable, str(validator_path), "--json-only"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if proc.returncode != 0:
            failures.append(
                f"[VISUAL_ATLAS_GOVERNANCE_FAIL] {validator_path.relative_to(repo_root).as_posix()}: "
                + (proc.stdout.strip() or proc.stderr.strip() or "visual atlas governance validator failed")
            )


def _run_reference_visual_atlas_scaffold_probe(repo_root: Path, failures: List[str]) -> None:
    probe_script = repo_root / "scripts/ci/run_reference_visual_atlas_scaffold_probes_ci.sh"
    if not probe_script.exists() or not probe_script.is_file():
        failures.append(
            "[MISSING_SCRIPT] scripts/ci/run_reference_visual_atlas_scaffold_probes_ci.sh not found"
        )
        return
    proc = subprocess.run(
        ["bash", str(probe_script)],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    if proc.returncode != 0:
        failures.append(
            "[VISUAL_ATLAS_SCAFFOLD_PROBE_FAIL] "
            + (proc.stdout.strip() or proc.stderr.strip() or "reference visual atlas scaffold probe failed")
        )


def _run_reference_visual_atlas_inventory_check(repo_root: Path, failures: List[str]) -> None:
    validator = repo_root / "scripts/validate_reference_visual_atlas_inventory.py"
    if not validator.exists() or not validator.is_file():
        failures.append("[MISSING_SCRIPT] scripts/validate_reference_visual_atlas_inventory.py not found")
        return
    proc = subprocess.run(
        [sys.executable, str(validator), "--json-only"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    if proc.returncode != 0:
        failures.append(
            "[VISUAL_ATLAS_INVENTORY_FAIL] "
            + (proc.stdout.strip() or proc.stderr.strip() or "reference visual atlas inventory validator failed")
        )


def _load_playbook_requirements(repo_root: Path) -> tuple[Path | None, List[str], List[str]]:
    errors: List[str] = []
    doc_control_path, _doc_control_active_file, alias_error = resolve_current_yaml_alias(
        repo_root, PLUGIN_DOC_CONTROL_PATH
    )
    if alias_error:
        return None, [], [f"[INVALID_PLUGIN_DOC_CONTROL] alias resolution failed: {PLUGIN_DOC_CONTROL_PATH}:{alias_error}"]
    if not doc_control_path.exists():
        return None, [], [f"[MISSING_PLUGIN_DOC_CONTROL] required file not found: {PLUGIN_DOC_CONTROL_PATH}"]
    doc_control = _load_yaml(doc_control_path)
    if not doc_control:
        return None, [], [f"[INVALID_PLUGIN_DOC_CONTROL] parse failed: {doc_control_path}"]
    docs_cfg = doc_control.get("docs")
    if not isinstance(docs_cfg, dict):
        return None, [], [f"[INVALID_PLUGIN_DOC_CONTROL] docs section missing: {doc_control_path}"]
    playbook_rel = _norm_path(str(docs_cfg.get("canonical_playbook", "")))
    if not playbook_rel:
        errors.append(f"[INVALID_PLUGIN_DOC_CONTROL] docs.canonical_playbook missing: {doc_control_path}")
        return None, [], errors
    playbook_path, playbook_alias_error = _resolve_current_markdown_alias(repo_root, playbook_rel)
    if playbook_alias_error:
        errors.append(
            f"[INVALID_PLUGIN_DOC_CONTROL] canonical_playbook alias resolution failed: {playbook_rel}:{playbook_alias_error}"
        )
        return None, [], errors
    required_tokens = _as_str_list(docs_cfg.get("playbook_required_tokens"))
    if not required_tokens:
        errors.append(
            f"[INVALID_PLUGIN_DOC_CONTROL] docs.playbook_required_tokens must be non-empty: {doc_control_path}"
        )
    return playbook_path, required_tokens, errors


def _dedup(seq: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _load_stream_doc_registry(
    repo_root: Path,
) -> tuple[List[str], List[str], dict[str, List[str]], List[str], dict[str, object], List[str]]:
    """
    Returns:
      stream_docs (governance/review docs per active stream),
      mandatory_static_docs (non-stream docs that must be present),
      doc_alias_requirements (doc -> required alias refs),
      legacy_archival_docs (historical governance/review docs that are intentionally non-authoritative),
      release_doc_surface (canonical/archival release-doc classification),
      validation_errors (fail-close reasons)
    """
    registry_entry_path = (repo_root / STREAM_DOC_REGISTRY_PATH).resolve()
    registry_path, _stream_registry_active_file, alias_error = resolve_current_yaml_alias(
        repo_root, STREAM_DOC_REGISTRY_PATH
    )
    if alias_error:
        return [], [], {}, [], {}, [f"[INVALID_STREAM_DOC_REGISTRY] alias resolution failed: {STREAM_DOC_REGISTRY_PATH}:{alias_error}"]
    if not registry_path.exists():
        return [], [], {}, [], {}, [f"[MISSING_STREAM_DOC_REGISTRY] required file not found: {registry_entry_path}"]

    data = _load_yaml(registry_path)
    errors: List[str] = []
    rows = data.get("stream_docs")
    if not isinstance(rows, list) or not rows:
        errors.append(
            f"[INVALID_STREAM_DOC_REGISTRY] stream_docs must be a non-empty list: {STREAM_DOC_REGISTRY_PATH}"
        )
        return [], [], {}, [], {}, errors

    stream_docs: List[str] = []
    mandatory_static_docs = _as_str_list(data.get("mandatory_static_docs"))
    if not mandatory_static_docs:
        errors.append(f"[INVALID_STREAM_DOC_REGISTRY] mandatory_static_docs must be non-empty list")
    canonical_release_summary_doc = _norm_path(data.get("canonical_release_summary_doc", ""))
    if not canonical_release_summary_doc:
        errors.append("[INVALID_STREAM_DOC_REGISTRY] canonical_release_summary_doc must be non-empty")
    elif not _is_release_doc(canonical_release_summary_doc):
        errors.append(
            f"[INVALID_STREAM_DOC_REGISTRY] canonical_release_summary_doc must be docs/release/*.md: {canonical_release_summary_doc}"
        )
    elif canonical_release_summary_doc not in mandatory_static_docs:
        errors.append(
            f"[INVALID_STREAM_DOC_REGISTRY] canonical_release_summary_doc must be listed in mandatory_static_docs: {canonical_release_summary_doc}"
        )

    release_archival_docs = _as_str_list(data.get("release_archival_docs"))
    if not isinstance(data.get("release_archival_docs"), list) or not release_archival_docs:
        errors.append("[INVALID_STREAM_DOC_REGISTRY] release_archival_docs must be a non-empty list")
    stream_versions_seen: set[str] = set()
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"[INVALID_STREAM_DOC_REGISTRY] row[{idx}] must be mapping")
            continue
        stream_version = str(row.get("stream_version", "")).strip() or f"row-{idx}"
        if stream_version in stream_versions_seen:
            errors.append(f"[INVALID_STREAM_DOC_REGISTRY] duplicate stream_version: {stream_version}")
        if stream_version.startswith("row-") or not is_stream_version(stream_version):
            errors.append(f"[INVALID_STREAM_DOC_REGISTRY] invalid stream_version format: {stream_version}")
        stream_versions_seen.add(stream_version)
        governance_doc = _norm_path(row.get("governance_doc", ""))
        review_doc = _norm_path(row.get("review_doc", ""))
        if not governance_doc:
            errors.append(f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} missing governance_doc")
        else:
            stream_docs.append(governance_doc)
        if not review_doc:
            errors.append(f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} missing review_doc")
        else:
            stream_docs.append(review_doc)

    doc_alias_requirements: dict[str, List[str]] = {}
    alias_rows = data.get("stream_doc_required_alias_refs")
    if not isinstance(alias_rows, list) or not alias_rows:
        errors.append(
            "[INVALID_STREAM_DOC_REGISTRY] stream_doc_required_alias_refs must be a non-empty list"
        )
    else:
        alias_versions_seen: set[str] = set()
        for idx, row in enumerate(alias_rows, start=1):
            if not isinstance(row, dict):
                errors.append(f"[INVALID_STREAM_DOC_REGISTRY] stream_doc_required_alias_refs[{idx}] must be mapping")
                continue
            stream_version = str(row.get("stream_version", "")).strip() or f"row-{idx}"
            if stream_version in alias_versions_seen:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] duplicate stream_doc_required_alias_refs stream_version: {stream_version}"
                )
            if stream_version.startswith("row-") or not is_stream_version(stream_version):
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] invalid stream_doc_required_alias_refs stream_version format: {stream_version}"
                )
            alias_versions_seen.add(stream_version)

            governance_doc = _norm_path(row.get("governance_doc", ""))
            review_doc = _norm_path(row.get("review_doc", ""))
            governance_alias_refs = _as_str_list(row.get("governance_alias_refs"))
            review_alias_refs = _as_str_list(row.get("review_alias_refs"))

            if not governance_doc:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} missing governance_doc in stream_doc_required_alias_refs"
                )
            elif governance_doc not in stream_docs:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} governance_doc not listed in stream_docs: {governance_doc}"
                )
            elif not governance_alias_refs:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} governance_alias_refs must be non-empty"
                )
            else:
                for alias_ref in governance_alias_refs:
                    if ".current." not in alias_ref:
                        errors.append(
                            f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} governance_alias_ref must be current-pointer: {alias_ref}"
                        )
                        continue
                    alias_path = (repo_root / alias_ref).resolve()
                    if not alias_path.exists():
                        errors.append(
                            f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} governance_alias_ref not found: {alias_ref}"
                        )
                doc_alias_requirements[governance_doc] = governance_alias_refs

            if not review_doc:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} missing review_doc in stream_doc_required_alias_refs"
                )
            elif review_doc not in stream_docs:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} review_doc not listed in stream_docs: {review_doc}"
                )
            elif not review_alias_refs:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} review_alias_refs must be non-empty"
                )
            else:
                for alias_ref in review_alias_refs:
                    if ".current." not in alias_ref:
                        errors.append(
                            f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} review_alias_ref must be current-pointer: {alias_ref}"
                        )
                        continue
                    alias_path = (repo_root / alias_ref).resolve()
                    if not alias_path.exists():
                        errors.append(
                            f"[INVALID_STREAM_DOC_REGISTRY] {stream_version} review_alias_ref not found: {alias_ref}"
                        )
                doc_alias_requirements[review_doc] = review_alias_refs

    static_alias_rows = data.get("static_doc_required_alias_refs")
    static_docs_seen: set[str] = set()
    if not isinstance(static_alias_rows, list) or not static_alias_rows:
        errors.append(
            "[INVALID_STREAM_DOC_REGISTRY] static_doc_required_alias_refs must be a non-empty list"
        )
    else:
        for idx, row in enumerate(static_alias_rows, start=1):
            if not isinstance(row, dict):
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] static_doc_required_alias_refs[{idx}] must be mapping"
                )
                continue
            doc = _norm_path(row.get("doc", ""))
            alias_refs = _as_str_list(row.get("alias_refs"))
            if not doc:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] static_doc_required_alias_refs[{idx}] missing doc"
                )
                continue
            if doc in static_docs_seen:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] duplicate static_doc_required_alias_refs doc: {doc}"
                )
            static_docs_seen.add(doc)
            if doc not in mandatory_static_docs:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] static_doc_required_alias_refs doc not listed in mandatory_static_docs: {doc}"
                )
                continue
            if not alias_refs:
                errors.append(
                    f"[INVALID_STREAM_DOC_REGISTRY] static_doc_required_alias_refs alias_refs must be non-empty: {doc}"
                )
                continue
            for alias_ref in alias_refs:
                if ".current." not in alias_ref:
                    errors.append(
                        f"[INVALID_STREAM_DOC_REGISTRY] static_doc_required_alias_ref must be current-pointer: {doc}:{alias_ref}"
                    )
                    continue
                alias_path = (repo_root / alias_ref).resolve()
                if not alias_path.exists():
                    errors.append(
                        f"[INVALID_STREAM_DOC_REGISTRY] static_doc_required_alias_ref not found: {doc}:{alias_ref}"
                    )
            doc_alias_requirements[doc] = alias_refs

    required_row_docs = {
        doc for doc in mandatory_static_docs if _requires_static_alias_ref_row(doc)
    }
    missing_static_alias_rows = sorted(required_row_docs - static_docs_seen)
    for doc in missing_static_alias_rows:
        errors.append(
            f"[INVALID_STREAM_DOC_REGISTRY] mandatory static doc missing static_doc_required_alias_refs row: {doc}"
        )

    if canonical_release_summary_doc and canonical_release_summary_doc not in doc_alias_requirements:
        errors.append(
            f"[INVALID_STREAM_DOC_REGISTRY] canonical_release_summary_doc missing static_doc_required_alias_refs row: {canonical_release_summary_doc}"
        )

    release_seen: set[str] = set()
    for doc in release_archival_docs:
        if doc in release_seen:
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] duplicate release_archival_docs entry: {doc}"
            )
            continue
        release_seen.add(doc)
        if not _is_release_doc(doc):
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] release_archival_docs entry must be docs/release/*.md: {doc}"
            )
            continue
        if not (repo_root / doc).exists():
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] release_archival_docs entry not found: {doc}"
            )
            continue
        if doc == canonical_release_summary_doc:
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] release_archival_docs entry conflicts with canonical_release_summary_doc: {doc}"
            )
            continue
        if doc in stream_docs:
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] release_archival_docs entry conflicts with stream_docs authoritative row: {doc}"
            )
            continue
        if doc in mandatory_static_docs:
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] release_archival_docs entry conflicts with mandatory_static_docs authoritative row: {doc}"
            )

    legacy_archival_docs = _as_str_list(data.get("legacy_archival_docs"))
    legacy_seen: set[str] = set()
    for doc in legacy_archival_docs:
        if doc in legacy_seen:
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] duplicate legacy_archival_docs entry: {doc}"
            )
            continue
        legacy_seen.add(doc)
        if not _is_legacy_v16_or_earlier_doc(doc):
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] legacy_archival_docs entry must be v1.6-or-earlier governance/review doc: {doc}"
            )
            continue
        if not (repo_root / doc).exists():
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] legacy_archival_docs entry not found: {doc}"
            )
            continue
        if doc in stream_docs:
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] legacy_archival_docs entry conflicts with stream_docs authoritative row: {doc}"
            )
            continue
        if doc in mandatory_static_docs:
            errors.append(
                f"[INVALID_STREAM_DOC_REGISTRY] legacy_archival_docs entry conflicts with mandatory_static_docs authoritative row: {doc}"
            )

    release_doc_surface = {
        "canonical_release_summary_doc": canonical_release_summary_doc,
        "release_archival_docs": _dedup(release_archival_docs),
    }

    return (
        _dedup(stream_docs),
        _dedup(mandatory_static_docs),
        doc_alias_requirements,
        _dedup(legacy_archival_docs),
        release_doc_surface,
        errors,
    )


def _enforce_required_current_docs(index_docs: List[str]) -> tuple[List[str], List[str]]:
    """
    Enforce that index contains current-version governance+checklist docs
    without hardcoding a specific version string.
    Returns (matched_required_docs, missing_pattern_messages).
    """
    matched: List[str] = []
    missing: List[str] = []
    for pat in REQUIRED_CURRENT_DOC_PATTERNS:
        hit = next((d for d in index_docs if re.match(pat, d)), None)
        if hit:
            matched.append(hit)
        else:
            missing.append(f"[MISSING_REQUIRED_CURRENT_DOC] no index entry matches pattern: {pat}")
    return matched, missing


def parse_script_command(cmd: str) -> Tuple[str | None, List[str], bool, List[str]]:
    """
    Returns:
      script_path, flags, is_python, subcommands
    """
    try:
        tokens = shlex.split(cmd)
    except Exception:
        return None, [], False, []

    # Ellipsis placeholders are documentation shorthand, not executable commands.
    if not tokens or "..." in cmd:
        return None, [], False, []

    script_path = None
    is_python = False
    for i, t in enumerate(tokens):
        normalized = _norm_path(t)
        if (
            "/scripts/" in normalized or normalized.startswith("scripts/")
        ) and (normalized.endswith(".py") or normalized.endswith(".sh")):
            python_invoked = normalized.endswith(".py") and any(
                interp in tokens[: i + 1]
                for interp in ("python", "python3", sys.executable)
            )
            shell_invoked = normalized.endswith(".sh") and (
                i == 0 or any(interp in tokens[: i + 1] for interp in ("bash", "sh", "zsh"))
            )
            if normalized.endswith(".py") and not python_invoked:
                continue
            if normalized.endswith(".sh") and not shell_invoked:
                continue
            script_path = t
            is_python = python_invoked
            break

    flags = [t for t in tokens if t.startswith("--")]
    subcommands: List[str] = []
    if script_path:
        # detect subcommand chain between script path and first option
        idx = tokens.index(script_path)
        for t in tokens[idx + 1 :]:
            if t.startswith("-"):
                break
            if t in {"bash", "python", "python3", "sh"}:
                continue
            if "<" in t or ">" in t:
                continue
            # simple heuristic: accept bare words as subcommands
            if re.match(r"^[a-zA-Z0-9_\\-]+$", t):
                subcommands.append(t)
            else:
                break

    return script_path, flags, is_python, subcommands


@lru_cache(maxsize=None)
def _load_help_flags_cached(script_path_text: str, subcommands_key: tuple[str, ...], cwd_root_text: str) -> Set[str]:
    script_path = Path(script_path_text)
    cwd_root = Path(cwd_root_text)
    cmd = [sys.executable, str(script_path), *subcommands_key, "--help"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd_root,
            timeout=20,
        )
        # Some scripts may return non-zero for --help in edge cases; still parse output.
        output = f"{proc.stdout}\n{proc.stderr}"
    except subprocess.TimeoutExpired as exc:
        output = f"{exc.stdout or ''}\n{exc.stderr or ''}\n--help timeout"
    return set(re.findall(r"(--[a-zA-Z0-9][a-zA-Z0-9\\-]*)", output))


def load_help_flags(script_path: Path, subcommands: List[str], cwd_root: Path) -> Set[str]:
    return _load_help_flags_cached(str(script_path.resolve()), tuple(subcommands), str(cwd_root.resolve()))


def resolve_script_target(
    repo_root: Path,
    script_rel: str,
    repo_self_prefixes: tuple[str, ...] = ("identity-protocol-local",),
) -> tuple[Path, Path]:
    return resolve_doc_script_target(
        repo_root,
        script_rel,
        workspace_root=_resolve_workspace_root(repo_root),
        self_prefixes=repo_self_prefixes,
    )


def _rewrite_path_value_for_workspace(
    raw_value: str,
    *,
    repo_root: Path,
    workspace_root: Path,
    script_rel: str,
    repo_self_prefixes: tuple[str, ...],
) -> str:
    token = str(raw_value or "").strip()
    if not token or token.startswith("<") or "..." in token:
        return token
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        return str(candidate.resolve())
    normalized_script = canonicalize_repo_self_prefix_path(
        script_rel,
        repo_name=repo_root.name,
        self_prefixes=repo_self_prefixes,
    )
    base_root = repo_root if _norm_path(script_rel) == normalized_script else workspace_root
    absolute = (base_root / candidate).resolve()
    try:
        return absolute.relative_to(workspace_root).as_posix()
    except Exception:
        return str(absolute)


def _build_workspace_semantic_probe_tokens(
    tokens: List[str],
    *,
    script_rel: str,
    repo_root: Path,
    workspace_root: Path,
    repo_self_prefixes: tuple[str, ...],
) -> List[str]:
    rewritten = list(tokens)
    normalized_script = canonicalize_repo_self_prefix_path(
        script_rel,
        repo_name=repo_root.name,
        self_prefixes=repo_self_prefixes,
    )
    script_token = f"{repo_root.name}/{normalized_script}"
    try:
        script_idx = rewritten.index(script_rel)
    except ValueError:
        return rewritten
    rewritten[script_idx] = script_token
    idx = 0
    while idx < len(rewritten) - 1:
        flag = rewritten[idx]
        if flag not in DOC_PATH_VALUE_FLAGS:
            idx += 1
            continue
        rewritten[idx + 1] = _rewrite_path_value_for_workspace(
            rewritten[idx + 1],
            repo_root=repo_root,
            workspace_root=workspace_root,
            script_rel=script_rel,
            repo_self_prefixes=repo_self_prefixes,
        )
        idx += 2
    return rewritten


def _run_workspace_semantic_probe(
    *,
    repo_root: Path,
    script_rel: str,
    cmd_snippet: str,
    repo_self_prefixes: tuple[str, ...],
) -> tuple[bool, str]:
    normalized_script = canonicalize_repo_self_prefix_path(
        script_rel,
        repo_name=repo_root.name,
        self_prefixes=repo_self_prefixes,
    )
    if normalized_script not in DOC_SEMANTIC_SAFE_SCRIPTS:
        return True, ""
    if any(marker in cmd_snippet for marker in ("<", "...", ">", "|")):
        return True, ""
    try:
        tokens = shlex.split(cmd_snippet)
    except Exception as exc:
        return False, f"semantic_probe_parse_failed:{exc}"
    if any(flag in tokens for flag in DOC_SEMANTIC_SKIP_FLAGS):
        return True, ""
    workspace_root = _resolve_workspace_root(repo_root)
    probe_tokens = _build_workspace_semantic_probe_tokens(
        tokens,
        script_rel=script_rel,
        repo_root=repo_root,
        workspace_root=workspace_root,
        repo_self_prefixes=repo_self_prefixes,
    )
    try:
        proc = subprocess.run(probe_tokens, capture_output=True, text=True, cwd=workspace_root, timeout=20)
    except subprocess.TimeoutExpired:
        return True, ""
    combined = f"{proc.stdout}\n{proc.stderr}".lower()
    if any(marker in combined for marker in DOC_SEMANTIC_PATH_ERROR_MARKERS):
        return False, f"workspace_launch_context_path_error:rc={proc.returncode}"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate governance-doc command snippets against script contracts."
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument(
        "--docs",
        nargs="*",
        default=None,
        help="markdown docs to scan (default: dynamic list from AUDIT_SNAPSHOT_INDEX.md + required current docs)",
    )
    args = parser.parse_args()

    repo_root = _resolve_repo_root(args.repo_root)
    docs = args.docs if args.docs else _docs_from_index(repo_root)
    bootstrap_failures: List[str] = []
    stream_doc_alias_requirements: dict[str, List[str]] = {}
    legacy_archival_docs: List[str] = []
    release_doc_surface: dict[str, object] = {}
    required_current_docs: List[str] = []
    doc_command_surface_rows = ()
    doc_command_surface_mode_map = {}
    repo_self_prefixes: tuple[str, ...] = ("identity-protocol-local",)
    playbook_path: Path | None = None
    playbook_required_tokens: List[str] = []
    (
        stream_docs,
        mandatory_static_docs,
        stream_doc_alias_requirements,
        legacy_archival_docs,
        release_doc_surface,
        registry_errors,
    ) = _load_stream_doc_registry(repo_root)
    bootstrap_failures.extend(registry_errors)
    (
        doc_command_surface_doc,
        _doc_command_surface_entry_path,
        _doc_command_surface_active_path,
        doc_command_surface_alias_error,
    ) = load_doc_command_surface(repo_root)
    if doc_command_surface_alias_error:
        bootstrap_failures.append(
            f"[INVALID_DOC_COMMAND_SURFACE] alias resolution failed: identity/protocol/mappings/doc-command-surface.current.yaml:{doc_command_surface_alias_error}"
        )
    elif not doc_command_surface_doc:
        bootstrap_failures.append("[INVALID_DOC_COMMAND_SURFACE] doc-command surface registry empty or invalid")
    else:
        doc_command_surface_rows = doc_command_surface_rows_from_doc(doc_command_surface_doc)
        mode_profiles = surface_mode_profiles_from_doc(doc_command_surface_doc)
        doc_command_surface_mode_map = {row.mode: row for row in mode_profiles}
        repo_self_prefixes = repo_self_prefixes_from_doc(doc_command_surface_doc)
        if not doc_command_surface_rows:
            bootstrap_failures.append("[INVALID_DOC_COMMAND_SURFACE] doc_command_surface_rows missing")
        if MODE_LIVE_CONTRACT not in doc_command_surface_mode_map:
            bootstrap_failures.append("[INVALID_DOC_COMMAND_SURFACE] live_contract mode missing")
    playbook_path, playbook_required_tokens, playbook_errors = _load_playbook_requirements(repo_root)
    bootstrap_failures.extend(playbook_errors)
    if args.docs is None:
        governance_stream_docs = [doc for doc in stream_docs if doc.startswith("docs/governance/")]
        review_stream_docs = [doc for doc in stream_docs if doc.startswith("docs/review/")]
        for doc in governance_stream_docs:
            if doc not in docs:
                bootstrap_failures.append(
                    f"[MISSING_STREAM_GOV_DOC_IN_INDEX] missing index entry for stream governance doc: {doc}"
                )
        for doc in review_stream_docs:
            if doc not in docs:
                bootstrap_failures.append(
                    f"[MISSING_STREAM_REVIEW_DOC_IN_INDEX] missing index entry for stream review doc: {doc}"
                )

        # enforce current-version docs by pattern (version-agnostic).
        required_docs, missing_required = _enforce_required_current_docs(docs)
        required_current_docs = list(required_docs)
        bootstrap_failures.extend(missing_required)
        for req in required_docs:
            if req not in docs:
                docs.append(req)
        for req in stream_docs + mandatory_static_docs:
            if req in docs:
                continue
            if (repo_root / req).exists():
                docs.append(req)
            else:
                bootstrap_failures.append(f"[MISSING_MANDATORY_DOC] required doc not found: {req}")
        if len(docs) < 4:
            bootstrap_failures.append(
                f"[INSUFFICIENT_COVERAGE] dynamic docs coverage too small: {len(docs)} (<4). check {INDEX_PATH}"
            )
    else:
        required_current_docs = [d for d in docs if any(re.match(pat, d) for pat in REQUIRED_CURRENT_DOC_PATTERNS)]

    legacy_docs: List[str] = []
    for sub in ("docs/governance", "docs/review"):
        root = repo_root / sub
        if not root.exists():
            continue
        for p in sorted(root.glob("*.md")):
            rel = p.relative_to(repo_root).as_posix()
            if _is_legacy_v16_or_earlier_doc(rel):
                legacy_docs.append(rel)
    legacy_docs = _dedup(legacy_docs)

    release_docs: List[str] = []
    release_root = repo_root / "docs/release"
    if release_root.exists():
        for p in sorted(release_root.glob("*.md")):
            release_docs.append(p.relative_to(repo_root).as_posix())
    release_docs = _dedup(release_docs)

    authoritative_semantic_docs: set[str] = set(stream_docs)
    authoritative_semantic_docs.update(
        d
        for d in mandatory_static_docs
        if d.startswith("docs/governance/") or d.startswith("docs/review/")
    )
    authoritative_semantic_docs.update(required_current_docs)
    legacy_archival_docs_set = set(legacy_archival_docs)
    canonical_release_summary_doc = _norm_path(
        str(release_doc_surface.get("canonical_release_summary_doc", ""))
    )
    release_archival_docs_set = set(
        _as_str_list(release_doc_surface.get("release_archival_docs"))
    )
    authoritative_release_docs = {
        d for d in mandatory_static_docs if _is_release_doc(d)
    }
    if canonical_release_summary_doc:
        authoritative_release_docs.add(canonical_release_summary_doc)

    for doc in legacy_docs:
        if doc in authoritative_semantic_docs:
            continue
        if doc in legacy_archival_docs_set:
            continue
        bootstrap_failures.append(
            f"[MISSING_LEGACY_DOC_SEMANTIC_CLASS] missing legacy_archival_docs classification: {doc}"
        )
    for doc in sorted(legacy_archival_docs_set):
        if doc in authoritative_semantic_docs:
            bootstrap_failures.append(
                f"[AMBIGUOUS_LEGACY_DOC_SEMANTIC_CLASS] doc listed as both authoritative and archival: {doc}"
            )
    if canonical_release_summary_doc:
        for doc in sorted(authoritative_release_docs):
            if doc != canonical_release_summary_doc:
                bootstrap_failures.append(
                    f"[AMBIGUOUS_RELEASE_DOC_SURFACE] unexpected authoritative release doc outside canonical_release_summary_doc: {doc}"
                )
    for doc in release_docs:
        if doc in authoritative_release_docs:
            continue
        if doc in release_archival_docs_set:
            continue
        bootstrap_failures.append(
            f"[MISSING_RELEASE_DOC_SEMANTIC_CLASS] missing release_archival_docs classification: {doc}"
        )
    for doc in sorted(release_archival_docs_set):
        if doc in authoritative_release_docs:
            bootstrap_failures.append(
                f"[AMBIGUOUS_RELEASE_DOC_SEMANTIC_CLASS] doc listed as both canonical and archival: {doc}"
            )
    if bootstrap_failures:
        print(f"[INFO] docs checked: {len(docs)}")
        print(f"[FAIL] contract drift found: {len(bootstrap_failures)}")
        for item in bootstrap_failures:
            print(f" - {item}")
        return 1

    failures: List[str] = []
    checks = 0

    for doc in docs:
        doc_path = repo_root / doc
        if not doc_path.exists():
            failures.append(f"[MISSING_DOC] {doc}")
            continue
        content = doc_path.read_text(encoding="utf-8")
        if _norm_path(doc) == V160_HISTORICAL_DOC:
            for marker in V160_REQUIRED_MARKERS:
                if marker not in content:
                    failures.append(
                        f"[V160_HISTORICAL_BOUNDARY_MISSING] {doc}: missing `{marker}`"
                    )
            for marker in V160_FORBIDDEN_MARKERS:
                if marker in content:
                    failures.append(
                        f"[V160_HISTORICAL_BOUNDARY_CONFLICT] {doc}: contains forbidden legacy marker `{marker}`"
                    )
        if _norm_path(doc) == V150_GOV_HISTORICAL_DOC:
            for marker in V150_GOV_REQUIRED_MARKERS:
                if marker not in content:
                    failures.append(
                        f"[V150_HISTORICAL_BOUNDARY_MISSING] {doc}: missing `{marker}`"
                    )
            for marker in V150_GOV_FORBIDDEN_MARKERS:
                if marker in content:
                    failures.append(
                        f"[V150_HISTORICAL_BOUNDARY_CONFLICT] {doc}: contains forbidden legacy marker `{marker}`"
                    )
        if _norm_path(doc) == V150_REVIEW_HISTORICAL_DOC:
            for marker in V150_REVIEW_REQUIRED_MARKERS:
                if marker not in content:
                    failures.append(
                        f"[V150_REVIEW_HISTORICAL_BOUNDARY_MISSING] {doc}: missing `{marker}`"
                    )
            for marker in V150_REVIEW_FORBIDDEN_MARKERS:
                if marker in content:
                    failures.append(
                        f"[V150_REVIEW_HISTORICAL_BOUNDARY_CONFLICT] {doc}: contains forbidden legacy marker `{marker}`"
                    )
        if _norm_path(doc) == V16_REVIEW_HISTORICAL_DOC:
            for marker in V16_REVIEW_REQUIRED_MARKERS:
                if marker not in content:
                    failures.append(
                        f"[V16_REVIEW_HISTORICAL_BOUNDARY_MISSING] {doc}: missing `{marker}`"
                    )
            for marker in V16_REVIEW_FORBIDDEN_MARKERS:
                if marker in content:
                    failures.append(
                        f"[V16_REVIEW_HISTORICAL_BOUNDARY_CONFLICT] {doc}: contains forbidden legacy marker `{marker}`"
                    )
        if _norm_path(doc) in V166_TEMP_PATH_GUARDED_DOCS:
            for marker in V166_FORBIDDEN_EPHEMERAL_PATH_MARKERS:
                if marker in content:
                    failures.append(
                        f"[V166_EPHEMERAL_PATH_FORBIDDEN] {doc}: contains ephemeral path marker `{marker}`"
                    )
        required_alias_refs = stream_doc_alias_requirements.get(doc, [])
        for ref in required_alias_refs:
            if ref not in content:
                failures.append(
                    f"[MISSING_STREAM_DOC_ALIAS_REF] {doc}: missing `{ref}`"
                )
        for snippet in extract_backtick_commands(content):
            for cmd_snippet in _snippet_to_commands(snippet):
                if "scripts/" not in cmd_snippet:
                    continue
                script_rel, flags, is_python, subcommands = parse_script_command(cmd_snippet)
                if not script_rel:
                    continue
                checks += 1
                surface_mode, _surface_rationale = resolve_doc_command_surface_mode(
                    surface_rows=doc_command_surface_rows,
                    doc_rel=doc,
                    script_rel=script_rel,
                    repo_name=repo_root.name,
                    self_prefixes=repo_self_prefixes,
                )
                mode_profile = doc_command_surface_mode_map.get(surface_mode)
                if mode_profile is None:
                    failures.append(
                        f"[INVALID_DOC_COMMAND_SURFACE_MODE] {doc}: `{cmd_snippet}` -> unresolved mode `{surface_mode}`"
                    )
                    continue
                script_path, script_cwd = resolve_script_target(repo_root, script_rel, repo_self_prefixes)
                if not script_path.exists():
                    if mode_profile.enforce_script_existence:
                        failures.append(
                            f"[MISSING_SCRIPT] {doc}: `{cmd_snippet}` -> `{script_rel}` not found"
                        )
                    continue
                if is_python and mode_profile.enforce_current_flag_contract:
                    help_flags = load_help_flags(script_path, subcommands, script_cwd)
                    for flag in flags:
                        # allow aliases in prose-style snippets using "..." or placeholders
                        if flag not in help_flags and "..." not in cmd_snippet:
                            failures.append(
                                f"[FLAG_MISMATCH] {doc}: `{cmd_snippet}` -> `{flag}` not in {script_rel} --help"
                            )
                if is_python and mode_profile.enforce_workspace_semantic_probe:
                    semantic_ok, semantic_reason = _run_workspace_semantic_probe(
                        repo_root=repo_root,
                        script_rel=script_rel,
                        cmd_snippet=cmd_snippet,
                        repo_self_prefixes=repo_self_prefixes,
                    )
                    if not semantic_ok:
                        failures.append(
                            f"[WORKSPACE_LAUNCH_CONTEXT_FAIL] {doc}: `{cmd_snippet}` -> {semantic_reason}"
                        )

    if playbook_path is not None and playbook_required_tokens:
        playbook_text = playbook_path.read_text(encoding="utf-8")
        for token in sorted(set(playbook_required_tokens)):
            if token and token not in playbook_text:
                failures.append(
                    f"[PLAYBOOK_TOKEN_MISSING] {playbook_path}: missing `{token}`"
                )

    _run_visual_atlas_governance_checks(repo_root, failures)
    _run_reference_visual_atlas_scaffold_probe(repo_root, failures)
    _run_reference_visual_atlas_inventory_check(repo_root, failures)

    release_closure_boundary_script = repo_root / "scripts/validate_v16x_release_closure_boundary.py"
    if release_closure_boundary_script.exists():
        proc = subprocess.run(
            [sys.executable, str(release_closure_boundary_script), "--json-only"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if proc.returncode != 0:
            failures.append(
                "[RELEASE_CLOSURE_BOUNDARY_FAIL] "
                + (proc.stdout.strip() or proc.stderr.strip() or "validate_v16x_release_closure_boundary failed")
            )
    else:
        failures.append("[MISSING_SCRIPT] scripts/validate_v16x_release_closure_boundary.py not found")

    release_closure_summary_script = repo_root / "scripts/validate_v16x_release_closure_summary.py"
    if release_closure_summary_script.exists():
        proc = subprocess.run(
            [sys.executable, str(release_closure_summary_script), "--json-only"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if proc.returncode != 0:
            failures.append(
                "[RELEASE_CLOSURE_SUMMARY_FAIL] "
                + (proc.stdout.strip() or proc.stderr.strip() or "validate_v16x_release_closure_summary failed")
            )
    else:
        failures.append("[MISSING_SCRIPT] scripts/validate_v16x_release_closure_summary.py not found")

    release_doc_surface_script = repo_root / "scripts/validate_release_doc_surface_governance.py"
    if release_doc_surface_script.exists():
        proc = subprocess.run(
            [sys.executable, str(release_doc_surface_script), "--json-only"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if proc.returncode != 0:
            failures.append(
                "[RELEASE_DOC_SURFACE_GOVERNANCE_FAIL] "
                + (proc.stdout.strip() or proc.stderr.strip() or "validate_release_doc_surface_governance failed")
            )
    else:
        failures.append("[MISSING_SCRIPT] scripts/validate_release_doc_surface_governance.py not found")

    workspace_runtime_closure_command_surface_script = (
        repo_root / "scripts/validate_workspace_runtime_closure_command_surface.py"
    )
    if workspace_runtime_closure_command_surface_script.exists():
        proc = subprocess.run(
            [sys.executable, str(workspace_runtime_closure_command_surface_script), "--json-only"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if proc.returncode != 0:
            failures.append(
                "[WORKSPACE_RUNTIME_CLOSURE_COMMAND_SURFACE_FAIL] "
                + (
                    proc.stdout.strip()
                    or proc.stderr.strip()
                    or "validate_workspace_runtime_closure_command_surface failed"
                )
            )
    else:
        failures.append("[MISSING_SCRIPT] scripts/validate_workspace_runtime_closure_command_surface.py not found")

    audit_snapshot_index_script = repo_root / "scripts/validate_audit_snapshot_index.py"
    if audit_snapshot_index_script.exists():
        proc = subprocess.run(
            [sys.executable, str(audit_snapshot_index_script), "--repo-root", str(repo_root)],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if proc.returncode != 0:
            failures.append(
                "[AUDIT_SNAPSHOT_INDEX_FAIL] "
                + (proc.stdout.strip() or proc.stderr.strip() or "validate_audit_snapshot_index failed")
            )
    else:
        failures.append("[MISSING_SCRIPT] scripts/validate_audit_snapshot_index.py not found")

    runtime_summary_surface_script = repo_root / RUNTIME_SUMMARY_SURFACE_GOVERNANCE_VALIDATOR
    if runtime_summary_surface_script.exists():
        proc = subprocess.run(
            [sys.executable, str(runtime_summary_surface_script), "--repo-root", str(repo_root), "--json-only"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if proc.returncode != 0:
            failures.append(
                "[RUNTIME_SUMMARY_SURFACE_GOVERNANCE_FAIL] "
                + (
                    proc.stdout.strip()
                    or proc.stderr.strip()
                    or "validate_runtime_summary_surface_governance failed"
                )
            )
    else:
        failures.append(f"[MISSING_SCRIPT] {RUNTIME_SUMMARY_SURFACE_GOVERNANCE_VALIDATOR} not found")

    doc_command_surface_registry_script = repo_root / "scripts/validate_doc_command_surface_registry.py"
    if doc_command_surface_registry_script.exists():
        proc = subprocess.run(
            [sys.executable, str(doc_command_surface_registry_script), "--json-only"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if proc.returncode != 0:
            failures.append(
                "[DOC_COMMAND_SURFACE_REGISTRY_FAIL] "
                + (
                    proc.stdout.strip()
                    or proc.stderr.strip()
                    or "validate_doc_command_surface_registry failed"
                )
            )
    else:
        failures.append("[MISSING_SCRIPT] scripts/validate_doc_command_surface_registry.py not found")

    # Round-29.5: enforce doc evidence persistence policy
    evidence_policy_script = repo_root / "scripts/validate_doc_evidence_persistence.py"
    if evidence_policy_script.exists():
        proc = subprocess.run(
            [sys.executable, str(evidence_policy_script), "--json-only"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if proc.returncode != 0:
            failures.append(
                "[EVIDENCE_POLICY_FAIL] "
                + (proc.stdout.strip() or proc.stderr.strip() or "validate_doc_evidence_persistence failed")
            )
    else:
        failures.append("[MISSING_SCRIPT] scripts/validate_doc_evidence_persistence.py not found")

    print(f"[INFO] docs checked: {len(docs)}")
    print(f"[INFO] command snippets checked: {checks}")
    if failures:
        print(f"[FAIL] contract drift found: {len(failures)}")
        for item in failures:
            print(f" - {item}")
        return 1
    print("[PASS] docs command contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
