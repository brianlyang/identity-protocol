#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


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
    required_gates_run_id: str,
    run_url: str,
    checks_json: str,
    jobs_json: str = "",
    github_repository: str = "",
    github_server_url: str = "",
    github_api_url: str = "",
    github_token_env: str = "GITHUB_TOKEN",
) -> dict[str, Any]:
    resolved_run_id = str(required_gates_run_id or "").strip() or str(os.environ.get("GITHUB_RUN_ID", "")).strip()
    resolved_repository = str(github_repository or "").strip() or str(os.environ.get("GITHUB_REPOSITORY", "")).strip()
    resolved_server_url = str(github_server_url or "").strip() or str(os.environ.get("GITHUB_SERVER_URL", "")).strip() or "https://github.com"
    resolved_api_url = str(github_api_url or "").strip() or str(os.environ.get("GITHUB_API_URL", "")).strip() or _default_github_api_url(resolved_server_url)
    resolved_run_url = str(run_url or "").strip() or _default_run_url(resolved_server_url, resolved_repository, resolved_run_id)
    explicit_checks_json = str(checks_json or "").strip()
    explicit_jobs_json = str(jobs_json or "").strip() or str(os.environ.get("GITHUB_RUN_JOBS_JSON", "")).strip()
    github_token = str(os.environ.get(github_token_env, "")).strip()

    payload: dict[str, Any] = {
        "release_cloud_evidence_adapter_status": STATUS_SKIPPED_NOT_REQUIRED,
        "identity_id": identity_id,
        "operation": operation,
        "required_gates_run_id": resolved_run_id,
        "run_url": resolved_run_url,
        "checks_json_path": explicit_checks_json,
        "adapter_source_kind": "",
        "github_repository": resolved_repository,
        "github_server_url": resolved_server_url,
        "github_api_url": resolved_api_url,
        "github_token_env": github_token_env,
        "required_checks_count": 0,
        "stale_reasons": [],
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
        payload["required_checks_count"] = len(checks)
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
        payload["stale_reasons"] = [f"release_plane_github_jobs_http_error:{exc.code}"]
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
    payload["required_checks_count"] = len(checks)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve canonical release-plane cloud evidence payload.")
    ap.add_argument("--identity-id", default="shared")
    ap.add_argument("--operation", default="general")
    ap.add_argument("--required-gates-run-id", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--checks-json", default="")
    ap.add_argument("--jobs-json", default="")
    ap.add_argument("--github-repository", default="")
    ap.add_argument("--github-server-url", default="")
    ap.add_argument("--github-api-url", default="")
    ap.add_argument("--github-token-env", default="GITHUB_TOKEN")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload = resolve_release_cloud_evidence(
        identity_id=str(args.identity_id or "").strip(),
        operation=str(args.operation or "").strip(),
        required_gates_run_id=str(args.required_gates_run_id or "").strip(),
        run_url=str(args.run_url or "").strip(),
        checks_json=str(args.checks_json or "").strip(),
        jobs_json=str(args.jobs_json or "").strip(),
        github_repository=str(args.github_repository or "").strip(),
        github_server_url=str(args.github_server_url or "").strip(),
        github_api_url=str(args.github_api_url or "").strip(),
        github_token_env=str(args.github_token_env or "").strip() or "GITHUB_TOKEN",
    )
    _emit(payload, json_only=args.json_only)
    return 0 if payload.get("release_cloud_evidence_adapter_status") != STATUS_FAIL_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
