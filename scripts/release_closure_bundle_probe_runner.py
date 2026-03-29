#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from probe_shadow_fixture_common import stage_probe_shadow_fixture
from release_closure_bundle_probe_registry_common import (
    ReleaseClosureBundleProbeMutationSpec,
    release_closure_bundle_probe_profile,
)
from repo_root_resolution_common import resolve_repo_root


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_KEY = "release_closure_bundle_probe_runner_status"
ERR_CODE = "IP-RCBPR-001"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _load_json_blob(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _run_validator(
    *,
    source_repo_root: Path,
    validation_repo_root: Path,
    validator_script_rel: str,
) -> tuple[int, dict[str, Any], str]:
    command = [
        sys.executable,
        str((source_repo_root / validator_script_rel).resolve()),
        "--repo-root",
        str(validation_repo_root),
        "--json-only",
    ]
    proc = subprocess.run(
        command,
        cwd=source_repo_root,
        capture_output=True,
        text=True,
    )
    output = proc.stdout.strip() or proc.stderr.strip()
    return proc.returncode, _load_json_blob(output), output


def _mutate_text(*, text: str, needle: str, replacement: str, mode: str) -> tuple[str, int]:
    if mode == "first":
        count = text.count(needle)
        return text.replace(needle, replacement, 1), min(count, 1)
    if mode == "all":
        count = text.count(needle)
        return text.replace(needle, replacement), count
    raise ValueError(f"unsupported mutation mode: {mode}")


def _apply_literal_mutation(
    *,
    shadow_root: Path,
    spec: ReleaseClosureBundleProbeMutationSpec,
) -> None:
    target = (shadow_root / spec.target_relpath).resolve()
    text = target.read_text(encoding="utf-8")
    occurrence_count = text.count(spec.needle)
    if occurrence_count < int(spec.min_occurrences):
        raise RuntimeError(
            "probe setup failed: expected at least "
            f"{int(spec.min_occurrences)} occurrence(s) for literal {spec.needle!r}; "
            f"found {occurrence_count}"
        )
    mutated, replaced = _mutate_text(
        text=text,
        needle=spec.needle,
        replacement=spec.replacement,
        mode=spec.mode,
    )
    if replaced < int(spec.min_occurrences):
        raise RuntimeError(
            f"probe setup failed: mutation replaced {replaced} occurrence(s), "
            f"expected at least {int(spec.min_occurrences)}"
        )
    if spec.require_absent_after and spec.needle in mutated:
        residual = mutated.count(spec.needle)
        raise RuntimeError(
            "probe setup failed: literal residual remained after mutation; "
            f"needle={spec.needle!r} remaining_occurrences={residual}"
        )
    target.write_text(mutated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a shared release-closure bundle probe profile by staging a shadow fixture, "
            "applying profile-owned mutations, and asserting positive/negative validator behavior."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--probe-id", required=True)
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    profile = release_closure_bundle_probe_profile(str(args.probe_id))
    if profile is None:
        _emit(
            {
                STATUS_KEY: STATUS_FAIL_REQUIRED,
                "error_code": ERR_CODE,
                "probe_id": str(args.probe_id),
                "failure_reason": f"unknown_probe_id:{args.probe_id}",
            },
            json_only=args.json_only,
        )
        return 1

    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_FAIL_REQUIRED,
        "error_code": ERR_CODE,
        "probe_id": profile.probe_id,
        "validator_script_rel": profile.validator_script_rel,
        "status_key": profile.status_key,
        "shadow_copy_files": list(profile.shadow_copy_files),
        "mutation_count": len(profile.mutations),
        "expected_reasons": [],
        "missing_expected_reasons": [],
    }

    try:
        positive_rc, positive_payload, positive_output = _run_validator(
            source_repo_root=repo_root,
            validation_repo_root=repo_root,
            validator_script_rel=profile.validator_script_rel,
        )
        if positive_rc != 0:
            raise RuntimeError(
                "positive_validator_failed:"
                + (positive_output or profile.validator_script_rel)
            )
        if str(positive_payload.get(profile.status_key, "")).strip().upper() != STATUS_PASS_REQUIRED:
            raise RuntimeError("positive_validator_status_not_green")

        with tempfile.TemporaryDirectory(prefix=f"{profile.probe_id}-") as tmp_dir:
            shadow_root = (Path(tmp_dir) / "shadow-repo").resolve()
            stage_probe_shadow_fixture(
                repo_root=repo_root,
                shadow_root=shadow_root,
                copy_files=profile.shadow_copy_files,
                copy_globs=(),
            )
            for mutation in profile.mutations:
                _apply_literal_mutation(shadow_root=shadow_root, spec=mutation)

            negative_rc, negative_payload, negative_output = _run_validator(
                source_repo_root=repo_root,
                validation_repo_root=shadow_root,
                validator_script_rel=profile.validator_script_rel,
            )
            if negative_rc == 0:
                raise RuntimeError("negative_validator_unexpectedly_passed")
            if str(negative_payload.get(profile.status_key, "")).strip().upper() != STATUS_FAIL_REQUIRED:
                raise RuntimeError("negative_validator_status_not_fail_required")

            expected_reasons = tuple(
                sorted(dict.fromkeys(profile.expected_reason_collector(shadow_root)))
            )
            negative_reasons = set(negative_payload.get("stale_reasons") or [])
            missing_expected_reasons = [
                reason for reason in expected_reasons if reason not in negative_reasons
            ]
            if missing_expected_reasons:
                raise RuntimeError(
                    "negative_validator_missing_expected_reasons:"
                    + ",".join(missing_expected_reasons)
                )

            payload.update(
                {
                    STATUS_KEY: STATUS_PASS_REQUIRED,
                    "error_code": "",
                    "positive_validator_status": positive_payload.get(profile.status_key),
                    "negative_validator_status": negative_payload.get(profile.status_key),
                    "shadow_root": str(shadow_root),
                    "expected_reasons": list(expected_reasons),
                    "negative_reason_count": len(negative_reasons),
                    "missing_expected_reasons": [],
                }
            )
    except Exception as exc:
        payload["failure_reason"] = str(exc)
        _emit(payload, json_only=args.json_only)
        return 1

    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
