#!/usr/bin/env python3
"""
Validate Release-plane cloud closure evidence (6-condition contract).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: str | None) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"json file not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def _all_success(checks: List[Dict[str, Any]]) -> bool:
    if not checks:
        return False
    return all(str(c.get("status", "")).lower() == "success" for c in checks)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Release-plane cloud closure contract (6 conditions)."
    )
    parser.add_argument("--target-branch", required=True)
    parser.add_argument("--release-head-sha", required=True)
    parser.add_argument("--required-gates-run-id", required=True)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--workflow-file-sha", required=True)
    parser.add_argument("--run-head-sha", required=True)
    parser.add_argument("--run-workflow-file-sha", required=True)
    parser.add_argument(
        "--checks-json",
        help="json file with `required_checks_set`: [{name,status}, ...]",
    )
    parser.add_argument(
        "--evidence-json",
        help="optional json that can provide any of the fields above; CLI args remain authoritative",
    )
    args = parser.parse_args()

    try:
        evidence = _load_json(args.evidence_json)
        checks_doc = _load_json(args.checks_json)
    except Exception as exc:
        payload = {
            "release_plane_status": "BLOCKED",
            "error_code": "IP-REL-001",
            "error_reason": str(exc),
            "target_branch": args.target_branch,
            "release_head_sha": args.release_head_sha,
            "required_gates_run_id": args.required_gates_run_id,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    required_checks_set = checks_doc.get("required_checks_set", [])
    if not required_checks_set and isinstance(evidence.get("required_checks_set"), list):
        required_checks_set = evidence["required_checks_set"]

    conditions = {
        "target_branch_explicit": bool(args.target_branch.strip()),
        "release_head_sha_explicit": bool(args.release_head_sha.strip()),
        "required_gates_run_id_accessible": bool(args.required_gates_run_id.strip())
        and bool(args.run_url.strip()),
        "run_head_matches_release_head": args.run_head_sha == args.release_head_sha,
        "required_checks_all_success": _all_success(required_checks_set),
        "workflow_file_sha_matches": args.run_workflow_file_sha == args.workflow_file_sha,
    }

    release_plane_status = "CLOSED" if all(conditions.values()) else "BLOCKED"
    payload = {
        "target_branch": args.target_branch,
        "release_head_sha": args.release_head_sha,
        "required_gates_run_id": args.required_gates_run_id,
        "run_url": args.run_url,
        "workflow_file_sha": args.workflow_file_sha,
        "run_head_sha": args.run_head_sha,
        "run_workflow_file_sha": args.run_workflow_file_sha,
        "required_checks_set": required_checks_set,
        "conditions": conditions,
        "release_plane_status": release_plane_status,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if release_plane_status != "CLOSED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
