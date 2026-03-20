#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_ALIAS_POLICY = "IP-CURRENT-ALIAS-001"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
VERSION_RE = re.compile(r"\.v(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?\.(?:yaml|json)$")
REQUIRED_POLICY = {
    "pointer_contract": "frozen_versioned_active_carrier",
    "upgrade_switch_mode": "pointer_only",
    "replay_snapshot_immutable": True,
}


def _load_yaml(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return doc if isinstance(doc, dict) else {}


def _is_versioned_active_carrier(active_file: str) -> bool:
    match = VERSION_RE.search(str(active_file or "").strip())
    if not match:
        return False
    patch = match.group("patch")
    return patch not in (None, "", "0")


def main() -> int:
    violations: list[dict[str, Any]] = []
    current_files = sorted((REPO_ROOT / "identity" / "protocol").rglob("*.current.yaml"))
    inspected: list[str] = []
    for path in current_files:
        doc = _load_yaml(path)
        active_file = str(doc.get("active_file", "")).strip()
        if not _is_versioned_active_carrier(active_file):
            continue
        rel = str(path.relative_to(REPO_ROOT))
        inspected.append(rel)
        for key, expected in REQUIRED_POLICY.items():
            if doc.get(key) != expected:
                violations.append(
                    {
                        "file": rel,
                        "reason": "missing_versioned_carrier_policy",
                        "field": key,
                        "expected": expected,
                        "actual": doc.get(key),
                        "active_file": active_file,
                    }
                )

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "current_alias_versioned_carrier_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_ALIAS_POLICY,
        "required_policy": REQUIRED_POLICY,
        "inspected_versioned_carriers": inspected,
        "violations": violations,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
