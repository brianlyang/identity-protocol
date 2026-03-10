#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_LITERAL_PATH = "IP-MM-LINT-001"

CANONICAL_PLUGIN_ROOT = "identity/protocol/plugins/"
SCAN_ROOTS = (
    "scripts",
    ".github/workflows",
    "identity/protocol",
)
SCAN_SUFFIXES = (
    ".py",
    ".sh",
    ".yml",
    ".yaml",
    ".json",
    ".md",
)
TOKENS = (
    "plugin.contract.yaml",
    "plugin.input.schema.json",
    "plugin.output.schema.json",
    "plugin.error-codes.yaml",
    "PLUGIN_REGISTRY.current.yaml",
    "PROVIDER_PROFILES.current.yaml",
    "FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml",
)


def _is_allowed_context(*, rel: str, line: str, token: str) -> bool:
    normalized = line.replace(" ", "")
    # Canonical dynamic resolution in protocol validator is allowed.
    if rel == "scripts/validate_multimodal_plugin_enforcement.py":
        if f'plugin_root/"{token}"' in normalized or f"plugin_root/'{token}'" in normalized:
            return True
        if f'plugin_dir/"{token}"' in normalized or f"plugin_dir/'{token}'" in normalized:
            return True
        if f'"**/{token}"' in line or f"'**/{token}'" in line:
            return True
    return False


def _extract_literal_path_candidates(*, line: str, token: str) -> list[str]:
    text = str(line or "")
    out: list[str] = []
    # quoted strings
    for m in re.finditer(r'["\']([^"\']+)["\']', text):
        raw = str(m.group(1) or "")
        if token in raw:
            out.append(raw)
    # markdown/code-ish bare paths (fallback for docs lines without quotes)
    bare_pat = re.compile(
        re.escape(CANONICAL_PLUGIN_ROOT) + r"[^\s`'\"<>]*" + re.escape(token)
    )
    for m in bare_pat.finditer(text):
        out.append(str(m.group(0) or ""))
    return out


def _is_canonical_literal_path(*, candidate: str, token: str) -> bool:
    text = str(candidate or "").replace("\\", "/").strip()
    if not text or token not in text:
        return False
    if not text.startswith(CANONICAL_PLUGIN_ROOT):
        return False
    # Must end at the governed token file name.
    if not text.endswith(token):
        return False
    # Path traversal/dot-segment is forbidden even if prefix looks canonical.
    parts = list(PurePosixPath(text).parts)
    if ".." in parts or "." in parts:
        return False
    return True


def _contains_canonical_root_literal(*, line: str, token: str) -> bool:
    for candidate in _extract_literal_path_candidates(line=line, token=token):
        if _is_canonical_literal_path(candidate=candidate, token=token):
            return True
    return False


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _iter_scan_files(repo_root: Path) -> list[Path]:
    out: list[Path] = []
    for root in SCAN_ROOTS:
        base = (repo_root / root).resolve()
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if not p.suffix:
                continue
            if p.suffix.lower() not in SCAN_SUFFIXES:
                continue
            # Canonical plugin tree is the allowed literal source, don't lint it against itself.
            if CANONICAL_PLUGIN_ROOT in str(p.relative_to(repo_root)).replace("\\", "/"):
                continue
            out.append(p)
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail-close when plugin contract/profile literal paths are non-canonical.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    violations: list[dict[str, Any]] = []

    for path in _iter_scan_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        if rel == "scripts/validate_plugin_contract_literal_paths.py":
            continue
        for idx, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            for token in TOKENS:
                if token not in line:
                    continue
                # allow only structurally canonical literals; variable-name presence alone is insufficient.
                if _contains_canonical_root_literal(line=line, token=token):
                    continue
                if _is_allowed_context(rel=rel, line=raw_line, token=token):
                    continue
                violations.append(
                    {
                        "path": rel,
                        "line": idx,
                        "token": token,
                        "snippet": raw_line[:240],
                    }
                )

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "plugin_literal_path_lint_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_LITERAL_PATH,
        "canonical_plugin_root": CANONICAL_PLUGIN_ROOT,
        "scan_roots": list(SCAN_ROOTS),
        "tokens_checked": list(TOKENS),
        "violation_count": len(violations),
        "violations": violations[:200],
        "stale_reasons": [] if not violations else ["non_canonical_plugin_literal_path_detected"],
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
