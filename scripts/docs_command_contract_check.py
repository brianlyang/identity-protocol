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


INDEX_PATH = "docs/governance/AUDIT_SNAPSHOT_INDEX.md"
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
    docs = re.findall(r"`(docs/governance/[^`]+?\.md)`", text)
    # keep order + dedup
    seen = set()
    out: List[str] = []
    for d in docs:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


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
        # enforce current-version docs by pattern (version-agnostic).
        required_docs, missing_required = _enforce_required_current_docs(docs)
        bootstrap_failures.extend(missing_required)
        for req in required_docs:
            if req not in docs:
                docs.append(req)
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
