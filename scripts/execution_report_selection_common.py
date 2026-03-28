#!/usr/bin/env python3
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from primary_execution_report_common import (
    IDENTITY_UPGRADE_EXEC_PREFIX,
    collect_primary_execution_reports_from_roots,
    dedupe_resolved_paths,
    is_derivative_execution_report as _is_derivative_execution_report,
    is_primary_execution_report,
    report_mtime as _report_mtime,
)
from runtime_temp_path_common import runtime_temp_root
from tool_vendor_governance_common import candidate_upgrade_report_roots, load_json


@dataclass(frozen=True)
class ExecutionReportCandidateEval:
    path: Path
    report_data: dict[str, Any]
    identity_id_match: bool
    catalog_path_match: bool
    pack_path_match: bool
    prompt_path_match: bool
    prompt_sha_match: bool
    report_newer_than_key_inputs: bool
    strict_identity_tuple_match: bool
    score: int
    report_mtime: float
    stale_reasons: list[str]


def derive_run_id_from_session_id(session_id: str) -> str:
    token = str(session_id or "").strip()
    if not token:
        return ""
    if token.startswith("run:") and len(token) > 4:
        return token.split(":", 1)[1].strip()
    return token


def stable_runtime_slug(value: str, *, default: str = "runtime") -> str:
    raw = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in str(value or "").strip())
    raw = raw.strip("-._")
    return raw or default


def _dedupe_paths(rows: list[Path]) -> list[Path]:
    return dedupe_resolved_paths(rows)


def _report_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _is_derivative_execution_report(path: Path) -> bool:
    return _is_derivative_execution_report(path)


def fallback_report_roots() -> list[Path]:
    roots: list[Path] = []
    runtime_tmp_root = runtime_temp_root()
    roots.append((runtime_tmp_root / "identity-upgrade-reports").resolve())
    roots.append((runtime_tmp_root / "identity-runtime").resolve())
    runtime_output_root = os.environ.get("IDENTITY_RUNTIME_OUTPUT_ROOT", "").strip()
    if runtime_output_root:
        roots.append(Path(runtime_output_root).expanduser().resolve())
    identity_home = os.environ.get("IDENTITY_HOME", "").strip()
    if identity_home:
        roots.append(Path(identity_home).expanduser().resolve())
    return _dedupe_paths(roots)


def candidate_report_roots(
    pack_path: Path,
    *,
    include_runtime_dir: bool = True,
    include_fallback_roots: bool = False,
) -> list[Path]:
    resolved_pack = Path(pack_path).expanduser().resolve()
    roots: list[Path] = [(resolved_pack / "runtime" / "reports").resolve()]
    if include_runtime_dir:
        roots.append((resolved_pack / "runtime").resolve())
    roots.extend(candidate_upgrade_report_roots(resolved_pack))
    if include_fallback_roots:
        roots.extend(fallback_report_roots())
    return _dedupe_paths(roots)


def collect_reports(
    pack_path: Path,
    identity_id: str,
    *,
    include_fallback_roots: bool = False,
    include_generic_upgrade_json: bool = False,
) -> list[Path]:
    return collect_primary_execution_reports_from_roots(
        candidate_report_roots(
            pack_path,
            include_runtime_dir=True,
            include_fallback_roots=include_fallback_roots,
        ),
        identity_id,
        include_generic_upgrade_json=include_generic_upgrade_json,
    )


def report_run_id(path: Path, report_doc: dict[str, Any] | None = None) -> str:
    data: dict[str, Any]
    if isinstance(report_doc, dict):
        data = report_doc
    else:
        try:
            data = load_json(path)
        except Exception:
            data = {}
    run_id = str(data.get("run_id", "")).strip()
    if run_id:
        return run_id
    if is_primary_execution_report(path) and path.name.startswith(IDENTITY_UPGRADE_EXEC_PREFIX):
        return path.stem
    return ""


def derive_runtime_run_token(
    *,
    explicit_run_id: str,
    execution_report: str,
    session_id: str,
    identity_id: str,
    default_prefix: str = "runtime",
) -> str:
    explicit = str(explicit_run_id or "").strip()
    if explicit:
        return explicit
    report = str(execution_report or "").strip()
    if report:
        report_stem = stable_runtime_slug(Path(report).expanduser().stem, default="")
        if report_stem:
            return report_stem
    session_slug = stable_runtime_slug(session_id, default="")
    if session_slug:
        return session_slug
    return f"{default_prefix}-{stable_runtime_slug(identity_id, default='identity')}"


def select_report(*, explicit_report: str, run_id: str, reports: list[Path]) -> tuple[Path | None, str]:
    if explicit_report.strip():
        p = Path(explicit_report).expanduser().resolve()
        if p.exists() and p.is_file():
            return p, "explicit_report"
        return None, "explicit_report_missing"

    if run_id.strip():
        exact_hits = [
            p
            for p in reports
            if report_run_id(p) == run_id or p.stem == run_id
        ]
        if exact_hits:
            return sorted(exact_hits, key=_report_mtime)[-1], "run_id_bound"
        run_hits = [p for p in reports if run_id in p.name]
        if run_hits:
            return sorted(run_hits, key=_report_mtime)[-1], "run_id_bound"
        return None, "run_id_not_found"

    if not reports:
        return None, "no_reports"
    return reports[-1], "mtime_fallback"


def resolve_report_selection(
    *,
    pack_path: Path | None,
    identity_id: str,
    explicit_report: str = "",
    preferred_run_id: str = "",
    include_fallback_roots: bool = False,
    include_generic_upgrade_json: bool = False,
) -> dict[str, Any]:
    if explicit_report.strip():
        selected, strategy = select_report(explicit_report=explicit_report, run_id="", reports=[])
        return {
            "selected_report": selected,
            "selection_strategy": strategy,
            "run_id": "",
            "candidate_count": 1 if selected is not None else 0,
            "candidate_paths": [str(selected)] if selected is not None else [],
        }

    if pack_path is None:
        return {
            "selected_report": None,
            "selection_strategy": "pack_path_unavailable",
            "run_id": str(preferred_run_id or "").strip(),
            "candidate_count": 0,
            "candidate_paths": [],
        }

    reports = collect_reports(
        pack_path,
        identity_id,
        include_fallback_roots=include_fallback_roots,
        include_generic_upgrade_json=include_generic_upgrade_json,
    )
    selected, strategy = select_report(
        explicit_report="",
        run_id=str(preferred_run_id or "").strip(),
        reports=reports,
    )
    return {
        "selected_report": selected,
        "selection_strategy": strategy,
        "run_id": str(preferred_run_id or "").strip(),
        "candidate_count": len(reports),
        "candidate_paths": [str(p) for p in reports[-10:]],
    }


def evaluate_report_candidate(
    path: Path,
    *,
    identity_id: str,
    catalog_path: Path,
    resolved_pack_path: Path,
    prompt_path: Path | None = None,
    prompt_sha: str = "",
    key_input_latest_mtime: float | None = None,
) -> ExecutionReportCandidateEval:
    try:
        data = load_json(path)
    except Exception:
        data = {}

    report_identity = str(data.get("identity_id", "")).strip()
    report_catalog = str(data.get("catalog_path", "")).strip()
    report_pack = str(data.get("resolved_pack_path", "") or data.get("pack_path", "") or "").strip()
    report_prompt = str(data.get("identity_prompt_path", "")).strip()
    report_prompt_sha = str(data.get("identity_prompt_sha256", "")).strip()

    identity_id_match = bool(report_identity) and report_identity == str(identity_id or "").strip()
    catalog_path_match = bool(report_catalog) and Path(report_catalog).expanduser().resolve() == catalog_path
    pack_candidate: Path | None = None
    if report_pack:
        pack_candidate = Path(report_pack).expanduser().resolve()
    elif report_prompt:
        pack_candidate = Path(report_prompt).expanduser().resolve().parent
    pack_path_match = pack_candidate is not None and pack_candidate == resolved_pack_path

    prompt_path_required = isinstance(prompt_path, Path)
    prompt_sha_required = bool(str(prompt_sha or "").strip())
    freshness_required = key_input_latest_mtime is not None

    prompt_path_match = (
        True
        if not prompt_path_required
        else bool(report_prompt) and Path(report_prompt).expanduser().resolve() == prompt_path
    )
    prompt_sha_match = (
        True
        if not prompt_sha_required
        else bool(report_prompt_sha) and report_prompt_sha == str(prompt_sha or "").strip()
    )
    report_newer_than_key_inputs = (
        True
        if not freshness_required
        else _report_mtime(path) >= float(key_input_latest_mtime or 0.0)
    )
    strict_identity_tuple_match = identity_id_match and pack_path_match

    stale_reasons: list[str] = []
    if not identity_id_match:
        stale_reasons.append("identity_id_mismatch_or_missing")
    if not catalog_path_match:
        stale_reasons.append("catalog_path_mismatch_or_missing")
    if not pack_path_match:
        stale_reasons.append("pack_path_mismatch_or_missing")
    if prompt_path_required and not prompt_path_match:
        stale_reasons.append("prompt_path_mismatch_or_missing")
    if prompt_sha_required and not prompt_sha_match:
        stale_reasons.append("prompt_sha_mismatch_or_missing")
    if freshness_required and not report_newer_than_key_inputs:
        stale_reasons.append("report_older_than_key_inputs")

    score = 0
    score += 32 if identity_id_match else 0
    score += 16 if pack_path_match else 0
    score += 8 if prompt_sha_required and prompt_sha_match else 0
    score += 4 if prompt_path_required and prompt_path_match else 0
    score += 2 if catalog_path_match else 0
    score += 1 if freshness_required and report_newer_than_key_inputs else 0

    return ExecutionReportCandidateEval(
        path=path,
        report_data=data,
        identity_id_match=identity_id_match,
        catalog_path_match=catalog_path_match,
        pack_path_match=pack_path_match,
        prompt_path_match=prompt_path_match,
        prompt_sha_match=prompt_sha_match,
        report_newer_than_key_inputs=report_newer_than_key_inputs,
        strict_identity_tuple_match=strict_identity_tuple_match,
        score=score,
        report_mtime=_report_mtime(path),
        stale_reasons=stale_reasons,
    )


def select_best_evaluated_candidate(
    candidates: list[ExecutionReportCandidateEval],
) -> ExecutionReportCandidateEval:
    if not candidates:
        raise RuntimeError("no_execution_report_candidates")
    return sorted(candidates, key=lambda row: (row.score, row.report_mtime), reverse=True)[0]
