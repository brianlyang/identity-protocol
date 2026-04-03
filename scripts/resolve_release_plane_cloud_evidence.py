#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime_temp_path_common import runtime_temp_file

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

DEFAULT_TIMEOUT_SECONDS = 20
MAX_GITHUB_API_PAGES = 10
MAX_GH_RUN_LIST_LIMIT = 100
MATERIALIZED_INPUT_SOURCE_KINDS = {"explicit_checks_json", "jobs_json_fixture", "gh_run_list_json"}
LIVE_FETCH_SOURCE_KINDS = {"gh_run_list_commit_aggregate", "github_actions_jobs_api"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _adapter_source_metadata(source_kind: str) -> dict[str, Any]:
    normalized = str(source_kind or "").strip()
    metadata: dict[str, Any] = {
        "adapter_acquisition_mode": "",
        "adapter_fetch_transport": "",
        "adapter_local_dev_canonical": False,
        "adapter_best_effort_fetch": False,
        "semantic_consumption_mode": "",
    }
    if not normalized:
        return metadata
    metadata["semantic_consumption_mode"] = "protocol_canonical_aggregation"
    if normalized in MATERIALIZED_INPUT_SOURCE_KINDS:
        metadata["adapter_acquisition_mode"] = "materialized_input"
        metadata["adapter_fetch_transport"] = "local_file"
        metadata["adapter_local_dev_canonical"] = True
        return metadata
    if normalized == "gh_run_list_commit_aggregate":
        metadata["adapter_acquisition_mode"] = "live_fetch"
        metadata["adapter_fetch_transport"] = "shell_gh"
        metadata["adapter_best_effort_fetch"] = True
        return metadata
    if normalized == "github_actions_jobs_api":
        metadata["adapter_acquisition_mode"] = "live_fetch"
        metadata["adapter_fetch_transport"] = "github_api"
        return metadata
    if normalized in LIVE_FETCH_SOURCE_KINDS:
        metadata["adapter_acquisition_mode"] = "live_fetch"
    return metadata


def _load_json_file(path: str) -> dict[str, Any] | list[Any]:
    data = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    if isinstance(data, (dict, list)):
        return data
    raise ValueError(f"json root must be object or array: {path}")


def _normalize_status(raw_status: str, raw_conclusion: str) -> str:
    conclusion = str(raw_conclusion or "").strip().lower()
    if conclusion:
        return conclusion
    status = str(raw_status or "").strip().lower()
    if status == "completed":
        return "unknown"
    return status or "unknown"


def _normalize_required_checks(rows: list[Any], *, source_kind: str) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        name = str(
            row.get("name")
            or row.get("display_title")
            or row.get("context")
            or row.get("job_name")
            or f"{source_kind}-{idx + 1}"
        ).strip()
        status = _normalize_status(str(row.get("status", "")), str(row.get("conclusion", "") or row.get("result", "")))
        check: dict[str, Any] = {
            "name": name,
            "status": status,
            "source_kind": source_kind,
        }
        if "id" in row:
            check["id"] = row.get("id")
        if row.get("html_url"):
            check["html_url"] = row.get("html_url")
        raw_status = str(row.get("status", "")).strip()
        raw_conclusion = str(row.get("conclusion", "") or row.get("result", "")).strip()
        if raw_status:
            check["raw_status"] = raw_status
        if raw_conclusion:
            check["raw_conclusion"] = raw_conclusion
        checks.append(check)
    return checks


def _normalize_payload(doc: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if isinstance(doc, list):
        return _normalize_required_checks(doc, source_kind="list_payload")
    if isinstance(doc.get("required_checks_set"), list):
        return _normalize_required_checks(list(doc.get("required_checks_set") or []), source_kind="canonical_checks_json")
    if isinstance(doc.get("jobs"), list):
        return _normalize_required_checks(list(doc.get("jobs") or []), source_kind="github_actions_job")
    if isinstance(doc.get("check_runs"), list):
        return _normalize_required_checks(list(doc.get("check_runs") or []), source_kind="github_check_run")
    return []


def _default_github_api_url(server_url: str) -> str:
    normalized = str(server_url or "").strip().rstrip("/")
    if not normalized or normalized == "https://github.com":
        return "https://api.github.com"
    return f"{normalized}/api/v3"


def _default_run_url(server_url: str, repository: str, run_id: str) -> str:
    server = str(server_url or "").strip().rstrip("/")
    repo = str(repository or "").strip().strip("/")
    token = str(run_id or "").strip()
    if not server or not repo or not token:
        return ""
    return f"{server}/{repo}/actions/runs/{token}"


_GITHUB_REMOTE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^https://(?P<host>[^/]+)/(?P<repo>[^/]+/[^/]+?)(?:\.git)?/?$"),
    re.compile(r"^git@(?P<host>[^:]+):(?P<repo>[^/]+/[^/]+?)(?:\.git)?/?$"),
    re.compile(r"^ssh://git@(?P<host>[^/]+)/(?P<repo>[^/]+/[^/]+?)(?:\.git)?/?$"),
)


def _normalize_repository_token(token: str) -> str:
    raw = str(token or "").strip().strip("/")
    if raw.endswith(".git"):
        raw = raw[:-4]
    return raw.strip("/")


def _infer_github_repo_context(
    *,
    explicit_repository: str = "",
    explicit_server_url: str = "",
    env: dict[str, str] | None = None,
) -> tuple[str, str]:
    env_map = env if isinstance(env, dict) else os.environ
    repository = _normalize_repository_token(explicit_repository) or _normalize_repository_token(
        str(env_map.get("GITHUB_REPOSITORY", "")).strip()
    )
    server_url = str(explicit_server_url or "").strip().rstrip("/") or str(
        env_map.get("GITHUB_SERVER_URL", "")
    ).strip().rstrip("/")

    if repository and server_url:
        return repository, server_url

    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        proc = None

    remote_url = str((proc.stdout if proc is not None else "") or "").strip()
    for pattern in _GITHUB_REMOTE_PATTERNS:
        match = pattern.match(remote_url)
        if not match:
            continue
        repository = repository or _normalize_repository_token(match.group("repo"))
        host = str(match.group("host") or "").strip()
        if host and not server_url:
            server_url = f"https://{host}".rstrip("/")
        break

    return repository, server_url


def _normalize_gh_run_rows(raw_doc: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_doc, list):
        return []
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_doc):
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row["_input_order"] = idx
        rows.append(row)
    return rows


def _gh_run_sort_key(row: dict[str, Any]) -> tuple[int, str, int]:
    database_id = 0
    try:
        database_id = int(row.get("databaseId") or 0)
    except Exception:
        database_id = 0
    created_at = str(row.get("createdAt") or row.get("updatedAt") or "").strip()
    input_order = 0
    try:
        input_order = int(row.get("_input_order") or 0)
    except Exception:
        input_order = 0
    return (database_id, created_at, -input_order)


def _workflow_run_check_name(row: dict[str, Any]) -> str:
    return str(
        row.get("workflowName")
        or row.get("name")
        or row.get("displayTitle")
        or f"workflow-run-{row.get('databaseId', 'unknown')}"
    ).strip()


def build_release_checks_from_gh_run_rows(
    *,
    run_rows: list[dict[str, Any]],
    target_branch: str,
    release_head_sha: str,
) -> dict[str, Any]:
    branch = str(target_branch or "").strip()
    head_sha = str(release_head_sha or "").strip()
    filtered = [
        dict(row)
        for row in run_rows
        if isinstance(row, dict)
        and (not branch or str(row.get("headBranch", "")).strip() == branch)
        and (not head_sha or str(row.get("headSha", "")).strip() == head_sha)
    ]
    filtered.sort(key=_gh_run_sort_key, reverse=True)

    if not filtered:
        return {
            "carrier_run": {},
            "required_checks_set": [],
            "matched_run_count": 0,
            "matched_workflow_count": 0,
        }

    carrier_run = dict(filtered[0])
    checks_by_name: dict[str, dict[str, Any]] = {}
    for row in filtered:
        name = _workflow_run_check_name(row)
        if name in checks_by_name:
            continue
        status = _normalize_status(str(row.get("status", "")), str(row.get("conclusion", "")))
        check: dict[str, Any] = {
            "name": name,
            "status": status,
            "source_kind": "gh_workflow_run",
        }
        if row.get("databaseId") is not None:
            check["id"] = row.get("databaseId")
        if row.get("url"):
            check["html_url"] = row.get("url")
        raw_status = str(row.get("status", "")).strip()
        raw_conclusion = str(row.get("conclusion", "")).strip()
        if raw_status:
            check["raw_status"] = raw_status
        if raw_conclusion:
            check["raw_conclusion"] = raw_conclusion
        checks_by_name[name] = check

    return {
        "carrier_run": carrier_run,
        "required_checks_set": list(checks_by_name.values()),
        "matched_run_count": len(filtered),
        "matched_workflow_count": len(checks_by_name),
    }


def _fetch_gh_run_list(
    *,
    github_repository: str,
    target_branch: str,
    release_head_sha: str,
    env: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    repository = _normalize_repository_token(github_repository)
    branch = str(target_branch or "").strip()
    head_sha = str(release_head_sha or "").strip()
    if not branch or not head_sha:
        return [], "release_plane_gh_run_list_missing_branch_or_sha"

    cmd = [
        "gh",
        "run",
        "list",
        "--branch",
        branch,
        "--commit",
        head_sha,
        "--limit",
        str(MAX_GH_RUN_LIST_LIMIT),
        "--json",
        "databaseId,headSha,url,headBranch,status,conclusion,workflowName,createdAt,updatedAt",
    ]
    if repository:
        cmd.extend(["--repo", repository])
    merged_env = dict(os.environ)
    if isinstance(env, dict):
        merged_env.update({str(k): str(v) for k, v in env.items()})
    shell_path = str(merged_env.get("SHELL", "")).strip() or "/bin/sh"
    proc = subprocess.run(
        [shell_path, "-lc", shlex.join(cmd)],
        capture_output=True,
        text=True,
        check=False,
        env=merged_env,
    )
    if proc.returncode != 0:
        err = str(proc.stderr or proc.stdout or "").strip().splitlines()
        detail = err[-1] if err else "unknown_error"
        return [], f"release_plane_gh_run_list_failed:{detail}"
    try:
        rows = _normalize_gh_run_rows(json.loads(proc.stdout or "[]"))
    except Exception as exc:
        return [], f"release_plane_gh_run_list_unparseable:{exc}"
    return rows, ""


def resolve_release_plane_context(
    *,
    explicit_target_branch: str = "",
    explicit_release_head_sha: str = "",
    explicit_required_gates_run_id: str = "",
    explicit_run_url: str = "",
    explicit_workflow_file_sha: str = "",
    explicit_run_head_sha: str = "",
    explicit_run_workflow_file_sha: str = "",
    explicit_checks_json: str = "",
    explicit_jobs_json: str = "",
    default_target_branch: str = "",
    default_release_head_sha: str = "",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    env_map = env if isinstance(env, dict) else os.environ
    github_run_id = str(env_map.get("GITHUB_RUN_ID", "")).strip()
    github_repository = str(env_map.get("GITHUB_REPOSITORY", "")).strip()
    github_server_url = str(env_map.get("GITHUB_SERVER_URL", "")).strip() or "https://github.com"
    github_run_url = _default_run_url(github_server_url, github_repository, github_run_id)

    source_rows = [
        ("explicit_target_branch", explicit_target_branch),
        ("explicit_release_head_sha", explicit_release_head_sha),
        ("explicit_required_gates_run_id", explicit_required_gates_run_id),
        ("explicit_run_url", explicit_run_url),
        ("explicit_workflow_file_sha", explicit_workflow_file_sha),
        ("explicit_run_head_sha", explicit_run_head_sha),
        ("explicit_run_workflow_file_sha", explicit_run_workflow_file_sha),
        ("explicit_checks_json", explicit_checks_json),
        ("explicit_jobs_json", explicit_jobs_json),
        ("ambient_github_run_url", github_run_url),
    ]
    context_sources = [label for label, value in source_rows if str(value or "").strip()]
    context_requested = bool(context_sources)

    if not context_requested:
        return {
            "release_plane_context_requested": False,
            "release_plane_context_sources": [],
            "target_branch": "",
            "release_head_sha": "",
            "required_gates_run_id": "",
            "run_url": "",
            "workflow_file_sha": "",
            "run_head_sha": "",
            "run_workflow_file_sha": "",
            "checks_json": str(explicit_checks_json or "").strip(),
            "jobs_json": str(explicit_jobs_json or "").strip(),
        }

    target_branch = (
        str(explicit_target_branch or "").strip()
        or str(env_map.get("GITHUB_REF_NAME", "")).strip()
        or str(default_target_branch or "").strip()
    )
    release_head_sha = str(explicit_release_head_sha or "").strip() or str(default_release_head_sha or "").strip()
    required_gates_run_id = str(explicit_required_gates_run_id or "").strip() or github_run_id
    run_url = str(explicit_run_url or "").strip() or github_run_url
    workflow_file_sha = str(explicit_workflow_file_sha or "").strip() or release_head_sha
    run_head_sha = str(explicit_run_head_sha or "").strip() or release_head_sha
    run_workflow_file_sha = str(explicit_run_workflow_file_sha or "").strip() or workflow_file_sha

    return {
        "release_plane_context_requested": True,
        "release_plane_context_sources": context_sources,
        "target_branch": target_branch,
        "release_head_sha": release_head_sha,
        "required_gates_run_id": required_gates_run_id,
        "run_url": run_url,
        "workflow_file_sha": workflow_file_sha,
        "run_head_sha": run_head_sha,
        "run_workflow_file_sha": run_workflow_file_sha,
        "checks_json": str(explicit_checks_json or "").strip(),
        "jobs_json": str(explicit_jobs_json or "").strip(),
    }


def _default_release_cloud_evidence_adapter_payload(
    *,
    identity_id: str,
    operation: str,
    github_token_env: str = "GITHUB_TOKEN",
) -> dict[str, Any]:
    return {
        "release_cloud_evidence_adapter_status": STATUS_SKIPPED_NOT_REQUIRED,
        "identity_id": identity_id,
        "operation": operation,
        "target_branch": "",
        "release_head_sha": "",
        "required_gates_run_id": "",
        "run_url": "",
        "checks_json_path": "",
        "gh_runs_json_path": "",
        "adapter_source_kind": "",
        "adapter_acquisition_mode": "",
        "adapter_fetch_transport": "",
        "adapter_local_dev_canonical": False,
        "adapter_best_effort_fetch": False,
        "semantic_consumption_mode": "",
        "github_repository": "",
        "github_server_url": "",
        "github_api_url": "",
        "github_token_env": github_token_env,
        "required_checks_count": 0,
        "stale_reasons": [],
        "adapter_http_status": "",
        "github_rate_limit_remaining": "",
        "github_rate_limit_reset_epoch": "",
    }


def resolve_release_plane_runtime_inputs(
    *,
    identity_id: str,
    operation: str,
    explicit_target_branch: str = "",
    explicit_release_head_sha: str = "",
    explicit_required_gates_run_id: str = "",
    explicit_run_url: str = "",
    explicit_workflow_file_sha: str = "",
    explicit_run_head_sha: str = "",
    explicit_run_workflow_file_sha: str = "",
    explicit_checks_json: str = "",
    explicit_jobs_json: str = "",
    explicit_gh_runs_json: str = "",
    default_target_branch: str = "",
    default_release_head_sha: str = "",
    github_repository: str = "",
    github_server_url: str = "",
    github_api_url: str = "",
    github_token_env: str = "GITHUB_TOKEN",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    release_context = resolve_release_plane_context(
        explicit_target_branch=str(explicit_target_branch or "").strip(),
        explicit_release_head_sha=str(explicit_release_head_sha or "").strip(),
        explicit_required_gates_run_id=str(explicit_required_gates_run_id or "").strip(),
        explicit_run_url=str(explicit_run_url or "").strip(),
        explicit_workflow_file_sha=str(explicit_workflow_file_sha or "").strip(),
        explicit_run_head_sha=str(explicit_run_head_sha or "").strip(),
        explicit_run_workflow_file_sha=str(explicit_run_workflow_file_sha or "").strip(),
        explicit_checks_json=str(explicit_checks_json or "").strip(),
        explicit_jobs_json=str(explicit_jobs_json or "").strip(),
        default_target_branch=str(default_target_branch or "").strip(),
        default_release_head_sha=str(default_release_head_sha or "").strip(),
        env=env,
    )
    gh_runs_json = str(explicit_gh_runs_json or "").strip()
    payload: dict[str, Any] = {
        "release_plane_context_requested": bool(release_context.get("release_plane_context_requested", False)),
        "release_plane_context_sources": list(release_context.get("release_plane_context_sources") or []),
        "target_branch": str(release_context.get("target_branch", "") or "").strip(),
        "release_head_sha": str(release_context.get("release_head_sha", "") or "").strip(),
        "required_gates_run_id": str(release_context.get("required_gates_run_id", "") or "").strip(),
        "run_url": str(release_context.get("run_url", "") or "").strip(),
        "workflow_file_sha": str(release_context.get("workflow_file_sha", "") or "").strip(),
        "run_head_sha": str(release_context.get("run_head_sha", "") or "").strip(),
        "run_workflow_file_sha": str(release_context.get("run_workflow_file_sha", "") or "").strip(),
        "checks_json": str(release_context.get("checks_json", "") or "").strip(),
        "jobs_json": str(release_context.get("jobs_json", "") or "").strip(),
        "gh_runs_json": gh_runs_json,
    }
    if not payload["release_plane_context_requested"]:
        payload["release_adapter_payload"] = _default_release_cloud_evidence_adapter_payload(
            identity_id=identity_id,
            operation=operation,
            github_token_env=github_token_env,
        )
        return payload

    adapter_payload = resolve_release_cloud_evidence(
        identity_id=identity_id,
        operation=operation,
        target_branch=payload["target_branch"],
        release_head_sha=payload["release_head_sha"],
        required_gates_run_id=payload["required_gates_run_id"],
        run_url=payload["run_url"],
        checks_json=payload["checks_json"],
        jobs_json=payload["jobs_json"],
        gh_runs_json=payload["gh_runs_json"],
        github_repository=github_repository,
        github_server_url=github_server_url,
        github_api_url=github_api_url,
        github_token_env=github_token_env,
        env=env,
    )
    payload["release_adapter_payload"] = adapter_payload
    payload["required_gates_run_id"] = str(
        adapter_payload.get("required_gates_run_id", "") or payload["required_gates_run_id"]
    ).strip()
    payload["run_url"] = str(adapter_payload.get("run_url", "") or payload["run_url"]).strip()
    payload["checks_json"] = str(adapter_payload.get("checks_json_path", "") or payload["checks_json"]).strip()
    return payload


def _classify_github_http_status(status_code: int, headers: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    raw_headers = headers or {}
    remaining = str(raw_headers.get("X-RateLimit-Remaining", "") or "").strip()
    reset_epoch = str(raw_headers.get("X-RateLimit-Reset", "") or "").strip()
    detail: dict[str, Any] = {
        "adapter_http_status": int(status_code),
        "github_rate_limit_remaining": remaining,
        "github_rate_limit_reset_epoch": reset_epoch,
    }
    if status_code == 401:
        return "release_plane_github_jobs_auth_unauthorized", detail
    if status_code in {403, 429} and remaining == "0":
        return "release_plane_github_jobs_rate_limited", detail
    if status_code == 403:
        return "release_plane_github_jobs_forbidden", detail
    if status_code == 404:
        return "release_plane_github_jobs_not_found", detail
    if 500 <= int(status_code) <= 599:
        return f"release_plane_github_jobs_server_error:{status_code}", detail
    return f"release_plane_github_jobs_http_error:{status_code}", detail


def _write_canonical_checks_json(
    *,
    identity_id: str,
    operation: str,
    run_token: str,
    checks: list[dict[str, Any]],
    required_gates_run_id: str,
    run_url: str,
    source_kind: str,
    github_repository: str,
) -> str:
    out_path = runtime_temp_file(
        channel="release-cloud-evidence",
        operation=operation or "general",
        identity_id=identity_id or "shared",
        run_token=run_token,
        stem=f"release-cloud-evidence-checks-{identity_id or 'shared'}-{run_token}",
        ext="json",
    )
    payload = {
        "required_checks_set": checks,
        "required_gates_run_id": required_gates_run_id,
        "run_url": run_url,
        "source_kind": source_kind,
        "github_repository": github_repository,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out_path)


def _fetch_github_jobs_payload(*, github_api_url: str, github_repository: str, run_id: str, token: str) -> dict[str, Any]:
    api_base = str(github_api_url or "").strip().rstrip("/")
    repo = str(github_repository or "").strip().strip("/")
    token_value = str(token or "").strip()
    if not api_base or not repo or not run_id or not token_value:
        raise ValueError("github_api_url, github_repository, run_id, and token are required")

    jobs: list[Any] = []
    next_url = f"{api_base}/repos/{repo}/actions/runs/{urllib.parse.quote(str(run_id), safe='')}/jobs?per_page=100"
    page_count = 0
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token_value}",
        "User-Agent": "identity-protocol-local/release-cloud-evidence",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    while next_url and page_count < MAX_GITHUB_API_PAGES:
        req = urllib.request.Request(next_url, headers=headers)
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            page_jobs = payload.get("jobs", [])
            if isinstance(page_jobs, list):
                jobs.extend(page_jobs)
            link = str(resp.headers.get("Link", "") or "")
            next_url = ""
            for part in link.split(","):
                chunk = part.strip()
                if 'rel="next"' not in chunk:
                    continue
                if "<" not in chunk or ">" not in chunk:
                    continue
                next_url = chunk.split("<", 1)[1].split(">", 1)[0].strip()
                break
        page_count += 1
    return {"jobs": jobs}


def resolve_release_cloud_evidence(
    *,
    identity_id: str,
    operation: str,
    target_branch: str = "",
    release_head_sha: str = "",
    required_gates_run_id: str,
    run_url: str,
    checks_json: str,
    jobs_json: str = "",
    gh_runs_json: str = "",
    github_repository: str = "",
    github_server_url: str = "",
    github_api_url: str = "",
    github_token_env: str = "GITHUB_TOKEN",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    env_map = dict(os.environ)
    if isinstance(env, dict):
        env_map.update({str(k): str(v) for k, v in env.items()})
    resolved_repository, inferred_server_url = _infer_github_repo_context(
        explicit_repository=github_repository,
        explicit_server_url=github_server_url,
        env=env_map,
    )
    resolved_run_id = str(required_gates_run_id or "").strip() or str(env_map.get("GITHUB_RUN_ID", "")).strip()
    resolved_server_url = inferred_server_url or str(env_map.get("GITHUB_SERVER_URL", "")).strip().rstrip("/") or "https://github.com"
    resolved_api_url = str(github_api_url or "").strip() or str(env_map.get("GITHUB_API_URL", "")).strip() or _default_github_api_url(resolved_server_url)
    resolved_run_url = str(run_url or "").strip() or _default_run_url(resolved_server_url, resolved_repository, resolved_run_id)
    explicit_checks_json = str(checks_json or "").strip()
    explicit_jobs_json = str(jobs_json or "").strip() or str(env_map.get("GITHUB_RUN_JOBS_JSON", "")).strip()
    explicit_gh_runs_json = str(gh_runs_json or "").strip() or str(env_map.get("GITHUB_RUN_LIST_JSON", "")).strip()
    github_token = str(env_map.get(github_token_env, "")).strip()
    target_branch_token = str(target_branch or "").strip()
    release_head_sha_token = str(release_head_sha or "").strip()

    payload: dict[str, Any] = {
        "release_cloud_evidence_adapter_status": STATUS_SKIPPED_NOT_REQUIRED,
        "identity_id": identity_id,
        "operation": operation,
        "target_branch": target_branch_token,
        "release_head_sha": release_head_sha_token,
        "required_gates_run_id": resolved_run_id,
        "run_url": resolved_run_url,
        "checks_json_path": explicit_checks_json,
        "gh_runs_json_path": explicit_gh_runs_json,
        "adapter_source_kind": "",
        "adapter_acquisition_mode": "",
        "adapter_fetch_transport": "",
        "adapter_local_dev_canonical": False,
        "adapter_best_effort_fetch": False,
        "semantic_consumption_mode": "",
        "github_repository": resolved_repository,
        "github_server_url": resolved_server_url,
        "github_api_url": resolved_api_url,
        "github_token_env": github_token_env,
        "required_checks_count": 0,
        "stale_reasons": [],
        "adapter_http_status": "",
        "github_rate_limit_remaining": "",
        "github_rate_limit_reset_epoch": "",
    }

    if explicit_checks_json:
        checks_path = Path(explicit_checks_json).expanduser().resolve()
        if not checks_path.exists():
            payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
            payload["stale_reasons"] = ["release_plane_checks_json_not_found"]
            return payload
        try:
            checks_doc = _load_json_file(str(checks_path))
        except Exception as exc:
            payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
            payload["stale_reasons"] = [f"release_plane_checks_json_unreadable:{exc}"]
            return payload
        checks = _normalize_payload(checks_doc)
        payload["release_cloud_evidence_adapter_status"] = STATUS_PASS_REQUIRED
        payload["adapter_source_kind"] = "explicit_checks_json"
        payload.update(_adapter_source_metadata("explicit_checks_json"))
        payload["required_checks_count"] = len(checks)
        return payload

    if explicit_jobs_json:
        jobs_path = Path(explicit_jobs_json).expanduser().resolve()
        if not jobs_path.exists():
            payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
            payload["stale_reasons"] = ["release_plane_jobs_json_not_found"]
            return payload
        try:
            jobs_doc = _load_json_file(str(jobs_path))
        except Exception as exc:
            payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
            payload["stale_reasons"] = [f"release_plane_jobs_json_unreadable:{exc}"]
            return payload
        checks = _normalize_payload(jobs_doc)
        payload["checks_json_path"] = _write_canonical_checks_json(
            identity_id=identity_id,
            operation=operation,
            run_token=resolved_run_id or "local",
            checks=checks,
            required_gates_run_id=resolved_run_id,
            run_url=resolved_run_url,
            source_kind="jobs_json_fixture",
            github_repository=resolved_repository,
        )
        payload["release_cloud_evidence_adapter_status"] = STATUS_PASS_REQUIRED
        payload["adapter_source_kind"] = "jobs_json_fixture"
        payload.update(_adapter_source_metadata("jobs_json_fixture"))
        payload["required_checks_count"] = len(checks)
        return payload

    if explicit_gh_runs_json:
        gh_runs_path = Path(explicit_gh_runs_json).expanduser().resolve()
        if not gh_runs_path.exists():
            payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
            payload["stale_reasons"] = ["release_plane_gh_runs_json_not_found"]
            return payload
        try:
            gh_runs_doc = _load_json_file(str(gh_runs_path))
        except Exception as exc:
            payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
            payload["stale_reasons"] = [f"release_plane_gh_runs_json_unreadable:{exc}"]
            return payload
        gh_release_checks = build_release_checks_from_gh_run_rows(
            run_rows=_normalize_gh_run_rows(gh_runs_doc),
            target_branch=target_branch_token,
            release_head_sha=release_head_sha_token,
        )
        carrier_run = dict(gh_release_checks.get("carrier_run") or {})
        gh_required_checks = list(gh_release_checks.get("required_checks_set") or [])
        if not carrier_run or not gh_required_checks:
            payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
            payload["stale_reasons"] = ["release_plane_gh_runs_json_no_matching_runs"]
            return payload
        resolved_run_id = str(resolved_run_id or carrier_run.get("databaseId") or "").strip()
        resolved_run_url = str(resolved_run_url or carrier_run.get("url") or "").strip()
        payload["required_gates_run_id"] = resolved_run_id
        payload["run_url"] = resolved_run_url
        payload["checks_json_path"] = _write_canonical_checks_json(
            identity_id=identity_id,
            operation=operation,
            run_token=resolved_run_id or release_head_sha_token or "gh-runs-json",
            checks=gh_required_checks,
            required_gates_run_id=resolved_run_id,
            run_url=resolved_run_url,
            source_kind="gh_run_list_json",
            github_repository=resolved_repository,
        )
        payload["release_cloud_evidence_adapter_status"] = STATUS_PASS_REQUIRED
        payload["adapter_source_kind"] = "gh_run_list_json"
        payload.update(_adapter_source_metadata("gh_run_list_json"))
        payload["required_checks_count"] = len(gh_required_checks)
        payload["gh_matched_run_count"] = int(gh_release_checks.get("matched_run_count", 0) or 0)
        payload["gh_matched_workflow_count"] = int(gh_release_checks.get("matched_workflow_count", 0) or 0)
        return payload

    gh_run_rows, gh_run_list_error = _fetch_gh_run_list(
        github_repository=resolved_repository,
        target_branch=target_branch_token,
        release_head_sha=release_head_sha_token,
        env=env_map,
    )
    gh_release_checks = build_release_checks_from_gh_run_rows(
        run_rows=gh_run_rows,
        target_branch=target_branch_token,
        release_head_sha=release_head_sha_token,
    )
    carrier_run = dict(gh_release_checks.get("carrier_run") or {})
    gh_required_checks = list(gh_release_checks.get("required_checks_set") or [])
    if carrier_run and gh_required_checks:
        resolved_run_id = str(resolved_run_id or carrier_run.get("databaseId") or "").strip()
        resolved_run_url = str(resolved_run_url or carrier_run.get("url") or "").strip()
        payload["required_gates_run_id"] = resolved_run_id
        payload["run_url"] = resolved_run_url
        payload["checks_json_path"] = _write_canonical_checks_json(
            identity_id=identity_id,
            operation=operation,
            run_token=resolved_run_id or release_head_sha_token or "gh-run-list",
            checks=gh_required_checks,
            required_gates_run_id=resolved_run_id,
            run_url=resolved_run_url,
            source_kind="gh_run_list_commit_aggregate",
            github_repository=resolved_repository,
        )
        payload["release_cloud_evidence_adapter_status"] = STATUS_PASS_REQUIRED
        payload["adapter_source_kind"] = "gh_run_list_commit_aggregate"
        payload.update(_adapter_source_metadata("gh_run_list_commit_aggregate"))
        payload["required_checks_count"] = len(gh_required_checks)
        payload["gh_matched_run_count"] = int(gh_release_checks.get("matched_run_count", 0) or 0)
        payload["gh_matched_workflow_count"] = int(gh_release_checks.get("matched_workflow_count", 0) or 0)
        return payload

    stale_reasons: list[str] = []
    if not resolved_run_id:
        stale_reasons.append("release_plane_required_gates_run_id_unresolved")
    if not resolved_run_url:
        stale_reasons.append("release_plane_run_url_unresolved")
    if not resolved_repository:
        stale_reasons.append("release_plane_github_repository_unresolved")
    if not github_token:
        stale_reasons.append(f"release_plane_github_token_missing:{github_token_env}")
    if gh_run_list_error:
        stale_reasons.append(gh_run_list_error)
    elif target_branch_token and release_head_sha_token and not gh_required_checks:
        stale_reasons.append("release_plane_gh_run_candidate_unresolved")
    if stale_reasons:
        payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED if (resolved_run_id or resolved_run_url) else STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = stale_reasons
        return payload

    try:
        jobs_doc = _fetch_github_jobs_payload(
            github_api_url=resolved_api_url,
            github_repository=resolved_repository,
            run_id=resolved_run_id,
            token=github_token,
        )
    except urllib.error.HTTPError as exc:
        payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
        reason, detail = _classify_github_http_status(int(exc.code), dict(exc.headers or {}))
        payload["stale_reasons"] = [reason]
        payload.update(detail)
        return payload
    except urllib.error.URLError as exc:
        payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = [f"release_plane_github_jobs_url_error:{exc.reason}"]
        return payload
    except Exception as exc:
        payload["release_cloud_evidence_adapter_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = [f"release_plane_github_jobs_fetch_failed:{exc}"]
        return payload

    checks = _normalize_payload(jobs_doc)
    payload["checks_json_path"] = _write_canonical_checks_json(
        identity_id=identity_id,
        operation=operation,
        run_token=resolved_run_id,
        checks=checks,
        required_gates_run_id=resolved_run_id,
        run_url=resolved_run_url,
        source_kind="github_actions_jobs_api",
        github_repository=resolved_repository,
    )
    payload["release_cloud_evidence_adapter_status"] = STATUS_PASS_REQUIRED
    payload["adapter_source_kind"] = "github_actions_jobs_api"
    payload.update(_adapter_source_metadata("github_actions_jobs_api"))
    payload["required_checks_count"] = len(checks)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve canonical release-plane cloud evidence payload.")
    ap.add_argument("--identity-id", default="shared")
    ap.add_argument("--operation", default="general")
    ap.add_argument("--target-branch", default="")
    ap.add_argument("--release-head-sha", default="")
    ap.add_argument("--required-gates-run-id", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--checks-json", default="")
    ap.add_argument("--jobs-json", default="")
    ap.add_argument("--gh-runs-json", default="")
    ap.add_argument("--github-repository", default="")
    ap.add_argument("--github-server-url", default="")
    ap.add_argument("--github-api-url", default="")
    ap.add_argument("--github-token-env", default="GITHUB_TOKEN")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload = resolve_release_cloud_evidence(
        identity_id=str(args.identity_id or "").strip(),
        operation=str(args.operation or "").strip(),
        target_branch=str(args.target_branch or "").strip(),
        release_head_sha=str(args.release_head_sha or "").strip(),
        required_gates_run_id=str(args.required_gates_run_id or "").strip(),
        run_url=str(args.run_url or "").strip(),
        checks_json=str(args.checks_json or "").strip(),
        jobs_json=str(args.jobs_json or "").strip(),
        gh_runs_json=str(args.gh_runs_json or "").strip(),
        github_repository=str(args.github_repository or "").strip(),
        github_server_url=str(args.github_server_url or "").strip(),
        github_api_url=str(args.github_api_url or "").strip(),
        github_token_env=str(args.github_token_env or "").strip() or "GITHUB_TOKEN",
    )
    _emit(payload, json_only=args.json_only)
    return 0 if payload.get("release_cloud_evidence_adapter_status") != STATUS_FAIL_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
