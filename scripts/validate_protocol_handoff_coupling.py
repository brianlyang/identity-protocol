#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import yaml

DEFAULT_MAP_PATH = Path("docs/governance/templates/protocol-core-change-map.yaml")
DEFAULT_INDEX_PATH = Path("docs/governance/AUDIT_SNAPSHOT_INDEX.md")
DEFAULT_CANONICAL_DOC_PATTERN = r"docs/governance/identity-protocol-strengthening-handoff-v\d+\.\d+\.\d+\.md"

CORE_FILES = (
    ".github/workflows/_identity-required-gates.yml",
    "scripts/e2e_smoke_test.sh",
    "scripts/release_readiness_check.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
    "scripts/identity_creator.py",
    "scripts/execute_identity_upgrade.py",
    "scripts/create_identity_pack.py",
    "scripts/identity_installer.py",
)

CORE_PREFIXES = (
    "scripts/validate_identity_",
    "scripts/validate_protocol_",
)


def _run_git(args: list[str]) -> str:
    cp = subprocess.run(["git", *args], capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return cp.stdout.strip()


def _resolve_range(base: str | None, head: str | None) -> tuple[str, str]:
    resolved_head = (head or "").strip() or _run_git(["rev-parse", "HEAD"])
    resolved_base = (base or "").strip() or _run_git(["rev-parse", "HEAD~1"])
    return resolved_base, resolved_head


def _changed_files(base: str, head: str) -> list[str]:
    out = _run_git(["diff", "--name-only", f"{base}..{head}"])
    return [x.strip() for x in out.splitlines() if x.strip()]


def _load_map(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"mapping file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("mapping root must be object")
    return data


def _resolve_map(path: Path) -> dict:
    data = _load_map(path)
    handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
    core = data.get("core_change_map") if isinstance(data.get("core_change_map"), dict) else {}

    index_path = Path(str(handoff.get("index_path", str(DEFAULT_INDEX_PATH))).strip() or str(DEFAULT_INDEX_PATH))
    canonical_pattern_raw = str(handoff.get("canonical_doc_pattern", DEFAULT_CANONICAL_DOC_PATTERN)).strip() or DEFAULT_CANONICAL_DOC_PATTERN

    core_files = core.get("files")
    if not isinstance(core_files, list) or not core_files:
        core_files = list(CORE_FILES)
    core_files = [str(x).strip() for x in core_files if str(x).strip()]

    core_prefixes = core.get("prefixes")
    if not isinstance(core_prefixes, list) or not core_prefixes:
        core_prefixes = list(CORE_PREFIXES)
    core_prefixes = [str(x).strip() for x in core_prefixes if str(x).strip()]

    if not core_files and not core_prefixes:
        raise ValueError("core_change_map must define at least one file/prefix matcher")

    try:
        pattern = re.compile(canonical_pattern_raw)
    except re.error as exc:
        raise ValueError(f"invalid canonical_doc_pattern regex: {exc}") from exc

    return {
        "index_path": index_path,
        "canonical_pattern": pattern,
        "core_files": core_files,
        "core_prefixes": core_prefixes,
    }


def _canonical_handoff_path(index_path: Path, canonical_pattern: re.Pattern[str]) -> str:
    if not index_path.exists():
        return ""
    text = index_path.read_text(encoding="utf-8")
    matches = canonical_pattern.findall(text)
    if not matches:
        return ""
    return sorted(set(matches))[-1]


def _is_core_file(path: str, core_files: list[str], core_prefixes: list[str]) -> bool:
    if path in core_files:
        return True
    return any(path.startswith(p) for p in core_prefixes)


def main() -> int:
    ap = argparse.ArgumentParser(description="Enforce protocol core-change -> canonical handoff doc coupling.")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    ap.add_argument("--mapping", default=str(DEFAULT_MAP_PATH), help="path to protocol core-change mapping yaml")
    args = ap.parse_args()

    try:
        mapping = _resolve_map(Path(args.mapping).expanduser().resolve())
        base, head = _resolve_range(args.base, args.head)
        changed = _changed_files(base, head)
    except Exception as exc:
        print(f"[FAIL] IP-SSOT-006 unable to inspect coupling context: {exc}")
        return 1

    if not changed:
        print(f"[OK] no changed files in range {base}..{head}")
        return 0

    core_changed = [
        p for p in changed if _is_core_file(p, mapping["core_files"], mapping["core_prefixes"])
    ]
    if not core_changed:
        print("[OK] no protocol-core changes detected; handoff coupling not required")
        return 0

    canonical = _canonical_handoff_path(mapping["index_path"], mapping["canonical_pattern"])
    if not canonical:
        print("[FAIL] IP-SSOT-006 canonical handoff path unresolved from index mapping")
        return 1

    if canonical not in changed:
        print("[FAIL] IP-SSOT-006 protocol-core changes require canonical handoff doc update in same range")
        print(f"       missing_changed_file={canonical}")
        print("       core_changed_files:")
        for p in core_changed[:50]:
            print(f"         - {p}")
        return 1

    print("[OK] protocol handoff coupling validated")
    print(f"     range={base}..{head}")
    print(f"     mapping={Path(args.mapping).expanduser().resolve()}")
    print(f"     canonical_handoff_changed={canonical}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
