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
STREAM_DOC_REGISTRY_PATH = "identity/protocol/mappings/stream-doc-registry.v1.6.yaml"
REQUIRED_CURRENT_DOC_PATTERNS = [
    r"^docs/governance/identity-token-efficiency-and-skill-parity-governance-v\d+\.\d+\.\d+\.md$",
    r"^docs/governance/identity-token-governance-audit-checklist-v\d+\.\d+\.\d+\.md$",
]

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


def _dedup(seq: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _load_stream_doc_registry(repo_root: Path) -> tuple[List[str], List[str], List[str]]:
    """
    Returns:
      stream_docs (governance/review docs per active stream),
      mandatory_static_docs (non-stream docs that must be present),
      validation_errors (fail-close reasons)
    """
    registry_path = repo_root / STREAM_DOC_REGISTRY_PATH
    if not registry_path.exists():
        return [], [], [f"[MISSING_STREAM_DOC_REGISTRY] required file not found: {STREAM_DOC_REGISTRY_PATH}"]

    data = _load_yaml(registry_path)
    errors: List[str] = []
    rows = data.get("stream_docs")
    if not isinstance(rows, list) or not rows:
        errors.append(
            f"[INVALID_STREAM_DOC_REGISTRY] stream_docs must be a non-empty list: {STREAM_DOC_REGISTRY_PATH}"
        )
        return [], [], errors

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

    return _dedup(stream_docs), _dedup(mandatory_static_docs), errors


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
    if args.docs is None:
        stream_docs, mandatory_static_docs, registry_errors = _load_stream_doc_registry(repo_root)
        bootstrap_failures.extend(registry_errors)
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
