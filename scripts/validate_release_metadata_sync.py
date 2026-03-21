#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_repo_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RELEASE_METADATA = "IP-RMETA-001"

PROTOCOL_PATH = "identity/protocol/IDENTITY_PROTOCOL.md"
README_PATH = "README.md"
VERSIONING_PATH = "VERSIONING.md"
REQUIREMENTS_PATH = "requirements-dev.txt"


def _read(repo_root: Path, rel_path: str) -> str:
    return (repo_root / rel_path).read_text(encoding="utf-8")


def _extract(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"cannot extract {label} using pattern: {pattern}")
    return str(match.group(1)).strip()


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2)
    print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release metadata version synchronization.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    payload: dict[str, Any] = {
        "release_metadata_sync_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "tracked_files": [PROTOCOL_PATH, README_PATH, VERSIONING_PATH, REQUIREMENTS_PATH],
        "versions": {},
        "release_metadata_mode": "active_draft_head_alignment",
        "stale_reasons": [],
    }

    try:
        protocol = _read(repo_root, PROTOCOL_PATH)
        readme = _read(repo_root, README_PATH)
        versioning = _read(repo_root, VERSIONING_PATH)
        requirements = _read(repo_root, REQUIREMENTS_PATH)
        protocol_v = _extract(
            r"^#\s+Identity Protocol\s+v(\d+\.\d+\.\d+)\s+\(draft\)",
            protocol,
            "protocol version",
        )
        readme_v = _extract(
            r"Protocol version:\s+`v(\d+\.\d+\.\d+)`\s+\(draft\)",
            readme,
            "README protocol version",
        )
        versioning_v = _extract(
            r"^##\s+Release metadata synchronization\s+\(v(\d+\.\d+\.\d+)\+\)",
            versioning,
            "VERSIONING release sync version",
        )
        requirements_v = _extract(
            r"release metadata synchronized in v(\d+\.\d+\.\d+)\s+draft",
            requirements,
            "requirements baseline version",
        )
    except Exception as exc:
        payload["error_code"] = ERR_RELEASE_METADATA
        payload["stale_reasons"] = [str(exc)]
        _emit(payload, json_only=args.json_only)
        return 1

    versions = {
        PROTOCOL_PATH: protocol_v,
        README_PATH: readme_v,
        VERSIONING_PATH: versioning_v,
        REQUIREMENTS_PATH: requirements_v,
    }
    payload["versions"] = versions
    baseline = protocol_v
    payload["baseline_version"] = baseline
    mismatch = {path: version for path, version in versions.items() if version != baseline}
    if mismatch:
        payload["error_code"] = ERR_RELEASE_METADATA
        payload["version_mismatches"] = mismatch
        payload["stale_reasons"] = [f"version_mismatch:{path}:v{version}" for path, version in mismatch.items()]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["release_metadata_sync_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
