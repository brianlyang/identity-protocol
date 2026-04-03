#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/workbook-docs-checker-sync-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

python3 - <<'PY' "${REPO_ROOT}" "${TMP_DIR}"
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
workspace_root = repo_root.parent
tmp_dir = Path(sys.argv[2]).resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from sync_workbook_docs_checker_counts import (  # noqa: E402
    STATUS_PASS_REQUIRED,
    _run_docs_checker,
    _sync_doc,
)

STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_CHECKER_MISMATCH = "IP-IREG-006"
DOCS_COMMAND_LINE_RE = re.compile(
    r"(?P<prefix>- `scripts/docs_command_contract_check\.py` -> `PASS` \(`docs checked: )"
    r"(?P<docs>\d+)"
    r"(?P<middle>`, `command snippets checked: )"
    r"(?P<snippets>\d+)"
    r"(?P<suffix>`\))"
)

issue_register_src = (repo_root / "docs/workbook/protocol-issue-register-v1.6.md").resolve()
deep_audit_src = (repo_root / "docs/workbook/protocol-deep-audit-workbook-v1.6.md").resolve()
probe_doc_root = (repo_root / "docs/workbook/.probe-workbook-docs-checker-sync").resolve()
probe_doc_root.mkdir(parents=True, exist_ok=True)
issue_register_tmp = (probe_doc_root / issue_register_src.name).resolve()
deep_audit_tmp = (probe_doc_root / deep_audit_src.name).resolve()
shutil.copy2(issue_register_src, issue_register_tmp)
shutil.copy2(deep_audit_src, deep_audit_tmp)


def run_json(*args: str, expect_rc: int | None = 0) -> tuple[int, dict]:
    proc = subprocess.run(
        list(args),
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if not stdout:
        raise AssertionError(f"missing_json_stdout:args={args}:rc={proc.returncode}:stderr={stderr}")
    payload = json.loads(stdout)
    if expect_rc is not None and proc.returncode != expect_rc:
        raise AssertionError(
            f"unexpected_rc:args={args}:expected={expect_rc}:actual={proc.returncode}:payload={payload}:stderr={stderr}"
        )
    return proc.returncode, payload


def mutate_counts(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    match = DOCS_COMMAND_LINE_RE.search(text)
    if match is None:
        raise AssertionError(f"docs_checker_line_missing:{path}")
    replacement = (
        f"{match.group('prefix')}{match.group('docs')}"
        f"{match.group('middle')}{int(match.group('snippets')) + 77}"
        f"{match.group('suffix')}"
    )
    updated_text, count = DOCS_COMMAND_LINE_RE.subn(replacement, text, count=1)
    if count != 1:
        raise AssertionError(f"docs_checker_line_replace_failed:{path}:count={count}")
    path.write_text(updated_text, encoding="utf-8")


try:
    _, baseline = run_json(
        "python3",
        "scripts/sync_workbook_docs_checker_counts.py",
        "--repo-root",
        str(repo_root),
        "--json-only",
    )
    assert baseline["workbook_docs_checker_sync_status"] == STATUS_PASS_REQUIRED, baseline
    assert baseline["pending_changes"] is False, baseline
    assert baseline["write_applied"] is False, baseline

    mutate_counts(issue_register_tmp)
    mutate_counts(deep_audit_tmp)

    stale_rc, stale_validator = run_json(
        "python3",
        "scripts/validate_issue_register_consistency.py",
        "--repo-root",
        str(repo_root),
        "--workspace-root",
        str(workspace_root),
        "--issue-register-doc",
        str(issue_register_tmp),
        "--deep-audit-workbook-doc",
        str(deep_audit_tmp),
        "--json-only",
        expect_rc=1,
    )
    assert stale_rc == 1, stale_validator
    assert stale_validator["issue_register_consistency_status"] == STATUS_FAIL_REQUIRED, stale_validator
    assert stale_validator["error_code"] == ERR_CHECKER_MISMATCH, stale_validator
    assert stale_validator["docs_checker_sync_lane"]["script"] == "scripts/sync_workbook_docs_checker_counts.py", stale_validator

    docs_checked, snippets_checked, _raw_output = _run_docs_checker(repo_root)
    dry_run_results = [
        _sync_doc(issue_register_tmp, docs_checked=docs_checked, snippets_checked=snippets_checked, write=False),
        _sync_doc(deep_audit_tmp, docs_checked=docs_checked, snippets_checked=snippets_checked, write=False),
    ]
    assert all(bool(row["changed"]) for row in dry_run_results), dry_run_results
    assert all(not bool(row["write_applied"]) for row in dry_run_results), dry_run_results

    write_results = [
        _sync_doc(issue_register_tmp, docs_checked=docs_checked, snippets_checked=snippets_checked, write=True),
        _sync_doc(deep_audit_tmp, docs_checked=docs_checked, snippets_checked=snippets_checked, write=True),
    ]
    assert all(bool(row["write_applied"]) for row in write_results), write_results

    _, repaired_validator = run_json(
        "python3",
        "scripts/validate_issue_register_consistency.py",
        "--repo-root",
        str(repo_root),
        "--workspace-root",
        str(workspace_root),
        "--issue-register-doc",
        str(issue_register_tmp),
        "--deep-audit-workbook-doc",
        str(deep_audit_tmp),
        "--json-only",
    )
    assert repaired_validator["issue_register_consistency_status"] == STATUS_PASS_REQUIRED, repaired_validator

    print(
        json.dumps(
            {
                "workbook_docs_checker_sync_probe_status": STATUS_PASS_REQUIRED,
                "baseline_pending_changes": baseline["pending_changes"],
                "dry_run_changed_files": len([row for row in dry_run_results if row["changed"]]),
                "write_applied_files": len([row for row in write_results if row["write_applied"]]),
                "repaired_issue_register_consistency_status": repaired_validator["issue_register_consistency_status"],
            },
            ensure_ascii=False,
        )
    )
finally:
    shutil.rmtree(probe_doc_root, ignore_errors=True)
PY

echo "[PASS] workbook docs-checker sync probes passed"
