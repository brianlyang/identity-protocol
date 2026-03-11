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
from pathlib import Path
from typing import List, Set, Tuple

import yaml


INDEX_PATH = "docs/governance/AUDIT_SNAPSHOT_INDEX.md"
STREAM_DOC_REGISTRY_PATH = "identity/protocol/mappings/stream-doc-registry.current.yaml"
PLUGIN_DOC_CONTROL_PATH = "identity/protocol/plugins/PLUGIN_DOC_CONTROL.current.yaml"
REQUIRED_CURRENT_DOC_PATTERNS = [
    r"^docs/governance/identity-token-efficiency-and-skill-parity-governance-v\d+\.\d+\.\d+\.md$",
    r"^docs/governance/identity-token-governance-audit-checklist-v\d+\.\d+\.\d+\.md$",
]
V160_HISTORICAL_DOC = "docs/governance/identity-actor-session-binding-governance-v1.6.0.md"
V160_REQUIRED_MARKERS = (
    "historical baseline + traceability ledger",
    "Current-state contract resolution must follow active stream registry first",
    "historical replay context only and must not be treated as current wiring contract input",
    "stream-doc-registry.current.yaml",
)
V160_FORBIDDEN_MARKERS = (
    "This document is the only normative execution entrypoint for actor-session-binding governance in v1.6.",
    "This file is topic-canonical for v1.6 planning/execution.",
)
V150_GOV_HISTORICAL_DOC = "docs/governance/identity-actor-session-binding-governance-v1.5.0.md"
V150_GOV_REQUIRED_MARKERS = (
    "historical baseline for v1.5 actor-session-binding closure",
    "stream-doc-registry.current.yaml",
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
    "historical replay context only and must not be treated as current wiring contract input",
)
V16_REVIEW_HISTORICAL_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.md"
V16_REVIEW_REQUIRED_MARKERS = (
    "historical/replay trace; it is **not** the standalone source for current-state protocol judgments",
    "stream-doc-registry.current.yaml",
    "historical replay context only and must not be treated as current wiring contract input",
)

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


def _norm_path(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _requires_static_alias_ref_row(doc: str) -> bool:
    normalized = _norm_path(doc)
    if not normalized.endswith(".md"):
        return False
    return (
        normalized.startswith("docs/governance/")
        or normalized.startswith("docs/review/")
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


def _load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, ""
    current_doc = _load_yaml(configured_path)
    if not current_doc:
        return configured_path, "current_file_parse_failed"
    active_file = _norm_path(str(current_doc.get("active_file", "")))
    if not active_file:
        return configured_path, "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, "active_file_not_found"
    return active_path, ""


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


def _load_playbook_requirements(repo_root: Path) -> tuple[Path | None, List[str], List[str]]:
    errors: List[str] = []
    doc_control_path, alias_error = _resolve_current_yaml_alias(repo_root, PLUGIN_DOC_CONTROL_PATH)
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


def _load_stream_doc_registry(repo_root: Path) -> tuple[List[str], List[str], dict[str, List[str]], List[str]]:
    """
    Returns:
      stream_docs (governance/review docs per active stream),
      mandatory_static_docs (non-stream docs that must be present),
      doc_alias_requirements (doc -> required alias refs),
      validation_errors (fail-close reasons)
    """
    registry_entry_path = (repo_root / STREAM_DOC_REGISTRY_PATH).resolve()
    registry_path, alias_error = _resolve_current_yaml_alias(repo_root, STREAM_DOC_REGISTRY_PATH)
    if alias_error:
        return [], [], {}, [f"[INVALID_STREAM_DOC_REGISTRY] alias resolution failed: {STREAM_DOC_REGISTRY_PATH}:{alias_error}"]
    if not registry_path.exists():
        return [], [], {}, [f"[MISSING_STREAM_DOC_REGISTRY] required file not found: {registry_entry_path}"]

    data = _load_yaml(registry_path)
    errors: List[str] = []
    rows = data.get("stream_docs")
    if not isinstance(rows, list) or not rows:
        errors.append(
            f"[INVALID_STREAM_DOC_REGISTRY] stream_docs must be a non-empty list: {STREAM_DOC_REGISTRY_PATH}"
        )
        return [], [], {}, errors

    stream_docs: List[str] = []
    stream_versions_seen: set[str] = set()
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"[INVALID_STREAM_DOC_REGISTRY] row[{idx}] must be mapping")
            continue
        stream_version = str(row.get("stream_version", "")).strip() or f"row-{idx}"
        if stream_version in stream_versions_seen:
            errors.append(f"[INVALID_STREAM_DOC_REGISTRY] duplicate stream_version: {stream_version}")
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

    mandatory_static_docs = _as_str_list(data.get("mandatory_static_docs"))
    if not mandatory_static_docs:
        errors.append(f"[INVALID_STREAM_DOC_REGISTRY] mandatory_static_docs must be non-empty list")

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

    return _dedup(stream_docs), _dedup(mandatory_static_docs), doc_alias_requirements, errors


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

    # ignore placeholders or non-command snippets
    if not tokens or "..." in cmd or "<" in cmd:
        # keep <id>/<report.json> commands (they are still useful) but skip
        # if parsing would be too ambiguous.
        pass

    script_path = None
    is_python = False
    for i, t in enumerate(tokens):
        if t.startswith("scripts/") and (t.endswith(".py") or t.endswith(".sh")):
            script_path = t
            # heuristic: python command usually has interpreter before script
            is_python = t.endswith(".py") and any(
                interp in tokens[: i + 1]
                for interp in ("python", "python3", sys.executable)
            )
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


def load_help_flags(script_path: Path, subcommands: List[str]) -> Set[str]:
    cmd = [sys.executable, str(script_path), *subcommands, "--help"]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    # Some scripts may return non-zero for --help in edge cases; still parse output.
    output = f"{proc.stdout}\n{proc.stderr}"
    return set(re.findall(r"(--[a-zA-Z0-9][a-zA-Z0-9\\-]*)", output))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate governance-doc command snippets against script contracts."
    )
    parser.add_argument(
        "--docs",
        nargs="*",
        default=None,
        help="markdown docs to scan (default: dynamic list from AUDIT_SNAPSHOT_INDEX.md + required current docs)",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    docs = args.docs if args.docs else _docs_from_index(repo_root)
    bootstrap_failures: List[str] = []
    stream_doc_alias_requirements: dict[str, List[str]] = {}
    playbook_path: Path | None = None
    playbook_required_tokens: List[str] = []
    stream_docs, mandatory_static_docs, stream_doc_alias_requirements, registry_errors = _load_stream_doc_registry(repo_root)
    bootstrap_failures.extend(registry_errors)
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
        if _norm_path(doc) == V16_REVIEW_HISTORICAL_DOC:
            for marker in V16_REVIEW_REQUIRED_MARKERS:
                if marker not in content:
                    failures.append(
                        f"[V16_REVIEW_HISTORICAL_BOUNDARY_MISSING] {doc}: missing `{marker}`"
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
                script_path = repo_root / script_rel
                if not script_path.exists():
                    failures.append(
                        f"[MISSING_SCRIPT] {doc}: `{cmd_snippet}` -> `{script_rel}` not found"
                    )
                    continue
                if is_python:
                    help_flags = load_help_flags(script_path, subcommands)
                    for flag in flags:
                        # allow aliases in prose-style snippets using "..." or placeholders
                        if flag not in help_flags and "..." not in cmd_snippet:
                            failures.append(
                                f"[FLAG_MISMATCH] {doc}: `{cmd_snippet}` -> `{flag}` not in {script_rel} --help"
                            )

    if playbook_path is not None and playbook_required_tokens:
        playbook_text = playbook_path.read_text(encoding="utf-8")
        for token in sorted(set(playbook_required_tokens)):
            if token and token not in playbook_text:
                failures.append(
                    f"[PLAYBOOK_TOKEN_MISSING] {playbook_path}: missing `{token}`"
                )

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
