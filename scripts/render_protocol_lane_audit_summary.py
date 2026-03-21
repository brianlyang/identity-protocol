#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root, resolve_workspace_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

DOCS_CHECKED_RE = re.compile(r"docs checked:\s*(\d+)", flags=re.IGNORECASE)
DOCS_SNIPPETS_RE = re.compile(r"command snippets checked:\s*(\d+)", flags=re.IGNORECASE)
LAUNCHER_DRY_RUN_RE = re.compile(r"launcher_dry_run_status=(\S+)")


@dataclass(frozen=True)
class LaneProfile:
    lane_id: str
    docs_checker_cmd: tuple[str, ...]
    workbook_cmd: tuple[str, ...]
    stream_scope_cmd: tuple[str, ...]
    launcher_probe_cmd: tuple[str, ...]


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _run_json(cmd: tuple[str, ...], *, cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        if proc.returncode != 0:
            raise RuntimeError(
                f"command failed rc={proc.returncode}: {' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}"
            ) from exc
        raise RuntimeError(f"expected valid JSON from {' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected object JSON from {' '.join(cmd)}")
    return payload


def _run_text(cmd: tuple[str, ...], *, cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed rc={proc.returncode}: {' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc.stdout


def _git_text(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ("git", "-C", str(repo_root), *args),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git command failed rc={proc.returncode}: git -C {repo_root} {' '.join(args)}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc.stdout.strip()


def _resolve_range(
    *,
    repo_root: Path,
    explicit_base: str,
    explicit_head: str,
    explicit_commit: str,
) -> tuple[str, str, str]:
    base = str(explicit_base or "").strip()
    head = str(explicit_head or "").strip()
    commit = str(explicit_commit or "").strip()
    if commit and (base or head):
        raise RuntimeError("--commit is mutually exclusive with --base/--head")
    if bool(base) != bool(head):
        raise RuntimeError("--base and --head must be provided together")
    if commit:
        resolved_head = _git_text(repo_root, "rev-parse", commit)
        resolved_base = _git_text(repo_root, "rev-parse", f"{commit}^")
        return resolved_base, resolved_head, "commit_pinned"
    if base and head:
        return _git_text(repo_root, "rev-parse", base), _git_text(repo_root, "rev-parse", head), "explicit_range"
    return _git_text(repo_root, "rev-parse", "HEAD~1"), _git_text(repo_root, "rev-parse", "HEAD"), "default_head_parent"


def _changed_files(repo_root: Path, *, base: str, head: str) -> list[str]:
    output = _git_text(repo_root, "diff", "--name-only", base, head)
    return [line.strip() for line in output.splitlines() if line.strip()]


def _docs_checker_payload(output: str) -> dict[str, Any]:
    docs_match = DOCS_CHECKED_RE.search(output)
    snippets_match = DOCS_SNIPPETS_RE.search(output)
    status = STATUS_PASS_REQUIRED if "[PASS]" in output else STATUS_FAIL_REQUIRED
    return {
        "status": status,
        "docs_checked": int(docs_match.group(1)) if docs_match else None,
        "command_snippets_checked": int(snippets_match.group(1)) if snippets_match else None,
        "raw_output": output.strip(),
    }


def _launcher_probe_payload(output: str) -> dict[str, Any]:
    dry_run_match = LAUNCHER_DRY_RUN_RE.search(output)
    probe_status = STATUS_PASS_REQUIRED if "[PASS] identity codex launcher probes passed" in output else STATUS_FAIL_REQUIRED
    return {
        "probe_status": probe_status,
        "launcher_dry_run_status": dry_run_match.group(1) if dry_run_match else "",
        "raw_output": output.strip(),
    }


def _profile(repo_root: Path) -> LaneProfile:
    return LaneProfile(
        lane_id="identity_codex_launcher_v1_6_14",
        docs_checker_cmd=("python3", str((repo_root / "scripts" / "docs_command_contract_check.py").resolve())),
        workbook_cmd=(
            "python3",
            str((repo_root / "scripts" / "validate_issue_register_consistency.py").resolve()),
            "--json-only",
        ),
        stream_scope_cmd=(
            "python3",
            str((repo_root / "scripts" / "validate_stream_scope_semantic_integrity.py").resolve()),
            "--base",
            "{base}",
            "--head",
            "{head}",
            "--json-only",
        ),
        launcher_probe_cmd=("bash", str((repo_root / "scripts" / "ci" / "run_identity_codex_launcher_probes_ci.sh").resolve())),
    )


def _stream_touch_summary(stream_scope: dict[str, Any]) -> tuple[str, str]:
    status = str(stream_scope.get("stream_scope_semantic_integrity_status", "")).strip()
    touched = stream_scope.get("touched_stream_versions") or []
    stale = stream_scope.get("stale_reasons") or []
    if status == STATUS_PASS_REQUIRED and touched:
        return "APPLICABLE_PASS_REQUIRED", "stream_docs_touched_and_scope_matrix_verified"
    if status == STATUS_SKIPPED_NOT_REQUIRED and "no_stream_docs_touched_in_range" in stale:
        return "NOT_APPLICABLE_NO_STREAM_DOCS_TOUCHED", "workbook_or_runtime_only_change_range"
    if status == STATUS_SKIPPED_NOT_REQUIRED:
        return "NOT_APPLICABLE", "stream_scope_validator_skipped"
    if status == STATUS_FAIL_REQUIRED:
        return "APPLICABLE_FAIL_REQUIRED", "stream_scope_semantic_integrity_red"
    return "UNKNOWN", "unclassified_stream_scope_state"


def _lane_change_scope(changed_files: list[str], *, stream_scope: dict[str, Any]) -> str:
    categories: list[str] = []
    if any(
        path.startswith("docs/workbook/")
        or path == "docs/governance/identity-workbook-governance-v1.6.md"
        or path.startswith("identity/protocol/mappings/workbook-registry")
        for path in changed_files
    ):
        categories.append("workbook_control_plane")
    if stream_scope.get("touched_stream_versions"):
        categories.append("stream_docs")
    if any(
        "identity_codex_launcher" in path or path == "scripts/configure_identity_runtime_paths.py"
        for path in changed_files
    ):
        categories.append("launcher_runtime")
    if any(
        path == "scripts/render_protocol_lane_audit_summary.py"
        or path == "scripts/ci/run_protocol_lane_audit_summary_probes_ci.sh"
        for path in changed_files
    ):
        categories.append("audit_summary_control_plane")
    if not categories:
        categories.append("runtime_or_scripts_only")
    categories = sorted(set(categories))
    return categories[0] if len(categories) == 1 else "mixed:" + ",".join(categories)


def _lane_summary(
    *,
    workbook: dict[str, Any],
    stream_scope: dict[str, Any],
    launcher_probe: dict[str, Any],
    changed_files: list[str],
) -> dict[str, Any]:
    freshness_contract = workbook.get("freshness_contract") or {}
    projection_gate_active = bool(freshness_contract.get("projection_docs_checker_parity_gate_active"))
    stream_touch_evidence_status, stream_touch_reason = _stream_touch_summary(stream_scope)
    canonical_violation_partition = ((workbook.get("violation_partitions") or {}).get("canonical_docs_checker") or [])
    workbook_status = str(workbook.get("issue_register_consistency_status", "")).strip()
    launcher_status = str(launcher_probe.get("probe_status", "")).strip()
    return {
        "launcher_lane_status": launcher_status,
        "workbook_canonical_freshness_status": workbook_status,
        "projection_docs_checker_gate_status": "PARITY_REQUIRED" if projection_gate_active else "NOT_GATING_BOUNDARY_ONLY",
        "protocol_gate_depends_on_projection_docs_checker_counts": projection_gate_active,
        "canonical_docs_checker_violation_count": len(canonical_violation_partition),
        "lane_change_scope": _lane_change_scope(changed_files, stream_scope=stream_scope),
        "stream_touch_evidence_status": stream_touch_evidence_status,
        "stream_touch_applicability_reason": stream_touch_reason,
    }


def _overall_status(*, workbook: dict[str, Any], launcher_probe: dict[str, Any]) -> str:
    if str(workbook.get("issue_register_consistency_status", "")).strip() != STATUS_PASS_REQUIRED:
        return STATUS_FAIL_REQUIRED
    if str(launcher_probe.get("probe_status", "")).strip() != STATUS_PASS_REQUIRED:
        return STATUS_FAIL_REQUIRED
    return STATUS_PASS_REQUIRED


def main() -> int:
    ap = argparse.ArgumentParser(description="Render machine-auditable lane summary without cross-lane overclaim.")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--workspace-root", default="")
    ap.add_argument("--lane", default="identity_codex_launcher_v1_6_14")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    ap.add_argument("--commit", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    workspace_root = resolve_workspace_root(args.workspace_root, start=__file__)
    base, head, range_mode = _resolve_range(
        repo_root=repo_root,
        explicit_base=args.base,
        explicit_head=args.head,
        explicit_commit=args.commit,
    )
    changed_files = _changed_files(repo_root, base=base, head=head)
    profile = _profile(repo_root)
    if args.lane != profile.lane_id:
        payload = {
            "status": STATUS_FAIL_REQUIRED,
            "error": f"unsupported lane: {args.lane}",
            "supported_lanes": [profile.lane_id],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    docs_output = _run_text(profile.docs_checker_cmd, cwd=workspace_root)
    workbook = _run_json(profile.workbook_cmd, cwd=workspace_root)
    stream_scope_cmd = tuple(base if token == "{base}" else head if token == "{head}" else token for token in profile.stream_scope_cmd)
    stream_scope = _run_json(stream_scope_cmd, cwd=workspace_root)
    launcher_output = _run_text(profile.launcher_probe_cmd, cwd=workspace_root)

    docs_checker = _docs_checker_payload(docs_output)
    launcher_probe = _launcher_probe_payload(launcher_output)
    lane_summary = _lane_summary(
        workbook=workbook,
        stream_scope=stream_scope,
        launcher_probe=launcher_probe,
        changed_files=changed_files,
    )
    payload = {
        "status": _overall_status(workbook=workbook, launcher_probe=launcher_probe),
        "lane_id": profile.lane_id,
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "range_mode": range_mode,
        "base": base,
        "head": head,
        "changed_files": changed_files,
        "docs_checker": docs_checker,
        "workbook_consistency": workbook,
        "stream_scope": stream_scope,
        "launcher_probe": launcher_probe,
        "lane_summary": lane_summary,
        "summary_lines": [
            f"launcher lane status={lane_summary['launcher_lane_status']}",
            f"canonical workbook freshness status={lane_summary['workbook_canonical_freshness_status']}",
            f"projection docs-checker gate={lane_summary['projection_docs_checker_gate_status']}",
            f"stream-touch evidence={lane_summary['stream_touch_evidence_status']} ({lane_summary['stream_touch_applicability_reason']})",
        ],
    }
    _emit(payload, json_only=args.json_only)
    return 0 if payload["status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
