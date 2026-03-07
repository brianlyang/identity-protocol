#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

STRICT_SURFACES: tuple[str, ...] = (
    "scripts/identity_creator.py",
    "scripts/release_readiness_check.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
    "scripts/e2e_smoke_test.sh",
    ".github/workflows/_identity-required-gates.yml",
)

FORBIDDEN_DIRECT_VALIDATORS: tuple[str, ...] = (
    "scripts/validate_v16_cross_verification_tracks.py",
    "scripts/validate_v16_intake_evidence_quorum.py",
    "scripts/validate_route_version_pinning.py",
    "scripts/validate_fallback_taxonomy_normalization.py",
    "scripts/validate_dedup_monotonicity.py",
    "scripts/validate_v16_cross_workflow_schema.py",
    "scripts/validate_v16_skill_path_integrity.py",
    "scripts/validate_execution_target_tuple_isolation.py",
)

BUNDLE_RUNNER_SCRIPT = "scripts/required_gate_bundle_runner.py"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect strict-surface direct validator drift against bundle-runner lineage.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()

    missing_surface_files: list[str] = []
    missing_bundle_runner_ref: list[str] = []
    forbidden_hits: dict[str, list[str]] = {}

    for rel in STRICT_SURFACES:
        path = repo_root / rel
        if not path.exists():
            missing_surface_files.append(rel)
            continue
        text = _read_text(path)
        if BUNDLE_RUNNER_SCRIPT not in text:
            missing_bundle_runner_ref.append(rel)
        hits = [needle for needle in FORBIDDEN_DIRECT_VALIDATORS if needle in text]
        if hits:
            forbidden_hits[rel] = hits

    if missing_surface_files:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-001"
    elif missing_bundle_runner_ref or forbidden_hits:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-002"
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""

    payload: dict[str, Any] = {
        "required_gate_surface_drift_status": status,
        "error_code": error_code,
        "bundle_runner_script": BUNDLE_RUNNER_SCRIPT,
        "strict_surfaces": list(STRICT_SURFACES),
        "forbidden_direct_validators": list(FORBIDDEN_DIRECT_VALIDATORS),
        "missing_surface_files": missing_surface_files,
        "missing_bundle_runner_ref": missing_bundle_runner_ref,
        "forbidden_hits": forbidden_hits,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[DRIFT] status={status} missing_surface_files={len(missing_surface_files)} "
            f"missing_bundle_runner_ref={len(missing_bundle_runner_ref)} forbidden_hit_surfaces={len(forbidden_hits)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 1 if status == STATUS_FAIL_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
