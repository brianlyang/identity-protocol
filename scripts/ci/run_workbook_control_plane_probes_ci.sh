#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${ROOT}/scripts/runtime_temp_path_common.sh"

WORKSPACE_ROOT="$(cd "${ROOT}/.." && pwd)"
export IDENTITY_RUNTIME_TMP_ROOT="${IDENTITY_RUNTIME_TMP_ROOT:-${ROOT}/.tmp}"
TMP_ROOT="$(identity_runtime_mktemp_dir_sh "workbook-control-plane-probes" "run")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

python3 - "${ROOT}" "${WORKSPACE_ROOT}" "${TMP_ROOT}" <<'PY'
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str((Path(sys.argv[1]).resolve() / "scripts")))

from workbook_control_plane_common import PROJECTION_BOUNDARY_MARKER  # noqa: E402


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_WORKBOOK_BOUNDARY = "IP-IREG-008"
ERR_STREAM_DOC_REGISTRY = "IP-IREG-009"
WORKBOOK_REGISTRY_CURRENT = Path("identity/protocol/mappings/workbook-registry.current.yaml")
STREAM_DOC_REGISTRY_CURRENT = Path("identity/protocol/mappings/stream-doc-registry.current.yaml")
WORKBOOK_README = Path("docs/workbook/README.md")
PROJECTION_FORBIDDEN_SENTENCE = "Authoritative current status: illegal mirror override"
DOCS_CHECKED_LINE_RE = re.compile(r"docs checked:\s*\d+")
ISSUE_REGISTER_COUNT_LINE_RE = re.compile(r"issue_register_issue_count=\d+")


def load_yaml(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise SystemExit(f"yaml root must be mapping: {path}")
    return doc


def resolve_family_doc_path(family: dict, key: str) -> str:
    authority_surfaces = family.get("authority_surfaces")
    if isinstance(authority_surfaces, dict):
        nested = str(authority_surfaces.get(key, "")).strip()
        if nested:
            return nested
    return str(family.get(key, "")).strip()


def template_static_doc_paths(registry_doc: dict) -> list[Path]:
    template_contract = registry_doc.get("template_contract")
    if not isinstance(template_contract, dict):
        raise SystemExit("template_contract missing from workbook registry")
    paths: list[Path] = []
    for key in ("templates_readme", "issue_register_template", "deep_audit_template"):
        raw = str(template_contract.get(key, "")).strip()
        if not raw:
            raise SystemExit(f"template_contract missing {key}")
        path = Path(raw)
        if path not in paths:
            paths.append(path)
    return paths


def ensure_materialized_dir(probe_root: Path, source_root: Path, rel_dir: Path) -> None:
    if str(rel_dir) in {"", "."}:
        return
    parent = rel_dir.parent
    if str(parent) != ".":
        ensure_materialized_dir(probe_root, source_root, parent)
    target = probe_root / rel_dir
    source = source_root / rel_dir
    if target.exists():
        if target.is_symlink():
            target.unlink()
        elif target.is_dir():
            return
        else:
            raise SystemExit(f"cannot materialize directory over file: {target}")
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        child_target = target / child.name
        if child_target.exists():
            continue
        child_target.symlink_to(child, target_is_directory=child.is_dir())


def materialize_file(probe_root: Path, source_root: Path, rel_file: Path) -> None:
    ensure_materialized_dir(probe_root, source_root, rel_file.parent)
    target = probe_root / rel_file
    if target.exists():
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            raise SystemExit(f"cannot materialize file over directory: {target}")
    shutil.copy2(source_root / rel_file, target)


def materialize_workspace_file(probe_repo_root: Path, source_workspace_root: Path, rel_file: Path) -> Path:
    probe_workspace_root = probe_repo_root.parent
    materialize_file(probe_workspace_root, source_workspace_root, rel_file)
    return probe_workspace_root / rel_file


def build_probe_repo(
    probe_root: Path,
    source_root: Path,
    source_workspace_root: Path,
    *,
    materialized_paths: list[Path],
) -> Path:
    probe_workspace_root = probe_root.parent
    probe_workspace_root.mkdir(parents=True, exist_ok=True)
    for child in source_workspace_root.iterdir():
        if child.name in {source_root.name, ".git", ".tmp", "__pycache__"}:
            continue
        target = probe_workspace_root / child.name
        if target.exists():
            continue
        target.symlink_to(child, target_is_directory=child.is_dir())
    probe_root.mkdir(parents=True, exist_ok=True)
    for child in source_root.iterdir():
        if child.name in {".git", ".tmp", "__pycache__"}:
            continue
        target = probe_root / child.name
        if target.exists():
            continue
        target.symlink_to(child, target_is_directory=child.is_dir())
    for rel_path in materialized_paths:
        source = source_root / rel_path
        if source.is_dir():
            ensure_materialized_dir(probe_root, source_root, rel_path)
        elif source.is_file():
            materialize_file(probe_root, source_root, rel_path)
        else:
            raise SystemExit(f"materialized path missing from source repo: {source}")
    return probe_root


def run_validator(repo_root: Path, workspace_root: Path) -> tuple[int, dict]:
    cmd = [
        "python3",
        str(repo_root / "scripts/validate_issue_register_consistency.py"),
        "--repo-root",
        str(repo_root),
        "--workspace-root",
        str(workspace_root),
        "--json-only",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if not stdout:
        raise SystemExit(f"validator produced no stdout (rc={proc.returncode}): {stderr}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"validator did not emit JSON (rc={proc.returncode}): {exc}: stdout={stdout!r} stderr={stderr!r}"
        ) from exc
    return proc.returncode, payload


root = Path(sys.argv[1]).resolve()
workspace_root = Path(sys.argv[2]).resolve()
tmp_root = Path(sys.argv[3]).resolve()

workbook_current = load_yaml(root / WORKBOOK_REGISTRY_CURRENT)
workbook_versioned_rel = Path(str(workbook_current.get("active_file", "")).strip())
if not workbook_versioned_rel:
    raise SystemExit("workbook registry current pointer missing active_file")
workbook_versioned = load_yaml(root / workbook_versioned_rel)
family = workbook_versioned.get("active_workbook_family")
if not isinstance(family, dict):
    raise SystemExit("active_workbook_family missing")
workbook_family = str(family.get("workbook_family", "")).strip()
governance_doc_rel = Path(str(family.get("governance_doc", "")).strip())
issue_register_rel = Path(resolve_family_doc_path(family, "issue_register_doc"))
deep_audit_rel = Path(resolve_family_doc_path(family, "deep_audit_workbook_doc"))
if not workbook_family or not governance_doc_rel or not issue_register_rel or not deep_audit_rel:
    raise SystemExit("workbook registry missing family/governance/authority docs")
template_doc_rels = template_static_doc_paths(workbook_versioned)
projection_rows = family.get("projection_exports") or []
if not isinstance(projection_rows, list) or not projection_rows:
    raise SystemExit("active workbook family missing projection exports")
issue_projection_rel = None
for row in projection_rows:
    if not isinstance(row, dict):
        raise SystemExit("projection export row must be mapping")
    if str(row.get("projection_role", "")).strip() == "issue_register_projection":
        raw_path = str(row.get("path", "")).strip()
        if not raw_path:
            raise SystemExit("issue_register_projection missing path")
        issue_projection_rel = Path(raw_path)
        break
if issue_projection_rel is None:
    raise SystemExit("issue_register_projection row missing from workbook registry")

stream_current = load_yaml(root / STREAM_DOC_REGISTRY_CURRENT)
stream_versioned_rel = Path(str(stream_current.get("active_file", "")).strip())
if not stream_versioned_rel:
    raise SystemExit("stream doc registry current pointer missing active_file")

materialized_control_plane_paths = [
    WORKBOOK_REGISTRY_CURRENT,
    workbook_versioned_rel,
    STREAM_DOC_REGISTRY_CURRENT,
    stream_versioned_rel,
    governance_doc_rel,
    WORKBOOK_README,
    issue_register_rel,
    deep_audit_rel,
    *template_doc_rels,
]

positive_rc, positive = run_validator(root, workspace_root)
if positive_rc != 0 or positive.get("issue_register_consistency_status") != STATUS_PASS_REQUIRED:
    raise SystemExit(f"positive workbook validator failed: {positive}")

baseline_shadow = build_probe_repo(
    tmp_root / "baseline-shadow" / root.name,
    root,
    workspace_root,
    materialized_paths=materialized_control_plane_paths,
)
baseline_shadow_rc, baseline_shadow_payload = run_validator(baseline_shadow, baseline_shadow.parent)
if baseline_shadow_rc != 0 or baseline_shadow_payload.get("issue_register_consistency_status") != STATUS_PASS_REQUIRED:
    raise SystemExit(f"baseline shadow repo did not preserve positive status: {baseline_shadow_payload}")

extra_doc_repo = build_probe_repo(
    tmp_root / "minor-family-extra-doc" / root.name,
    root,
    workspace_root,
    materialized_paths=materialized_control_plane_paths,
)
extra_doc_path = extra_doc_repo / "docs/workbook/protocol-issue-register-shadow.md"
extra_doc_text = (root / issue_register_rel).read_text(encoding="utf-8")
extra_doc_path.write_text(extra_doc_text, encoding="utf-8")
extra_rc, extra_payload = run_validator(extra_doc_repo, extra_doc_repo.parent)
if extra_rc == 0:
    raise SystemExit("minor-family extra-doc negative probe unexpectedly passed")
extra_violations = [str(item) for item in (extra_payload.get("violations") or [])]
expected_extra_rel = "docs/workbook/protocol-issue-register-shadow.md"
if extra_payload.get("error_code") != ERR_WORKBOOK_BOUNDARY:
    raise SystemExit(f"minor-family extra-doc probe returned wrong error code: {extra_payload}")
if not any(item.startswith("minor_family_uniqueness_extra_doc:") and expected_extra_rel in item for item in extra_violations):
    raise SystemExit(f"minor-family extra-doc violation missing: {extra_payload}")

stream_doc_repo = build_probe_repo(
    tmp_root / "stream-doc-registry-missing-static-doc" / root.name,
    root,
    workspace_root,
    materialized_paths=materialized_control_plane_paths,
)
stream_registry_path = stream_doc_repo / stream_versioned_rel
stream_doc = load_yaml(stream_registry_path)
mandatory_static_docs = stream_doc.get("mandatory_static_docs") or []
if governance_doc_rel.as_posix() not in mandatory_static_docs:
    raise SystemExit("governance doc is not present in mandatory_static_docs for negative probe")
stream_doc["mandatory_static_docs"] = [
    item for item in mandatory_static_docs if str(item).strip() != governance_doc_rel.as_posix()
]
stream_registry_path.write_text(yaml.safe_dump(stream_doc, sort_keys=False, allow_unicode=False), encoding="utf-8")
stream_rc, stream_payload = run_validator(stream_doc_repo, stream_doc_repo.parent)
if stream_rc == 0:
    raise SystemExit("stream-doc-registry missing-static-doc negative probe unexpectedly passed")
stream_violations = [str(item) for item in (stream_payload.get("violations") or [])]
expected_stream_violation = f"stream_doc_registry_missing_static_doc:{governance_doc_rel.as_posix()}"
if stream_payload.get("error_code") != ERR_STREAM_DOC_REGISTRY:
    raise SystemExit(f"stream-doc-registry missing-static-doc probe returned wrong error code: {stream_payload}")
if expected_stream_violation not in stream_violations:
    raise SystemExit(f"stream-doc-registry missing-static-doc violation missing: {stream_payload}")

template_doc_rel = template_doc_rels[0]
template_stream_repo = build_probe_repo(
    tmp_root / "stream-doc-registry-missing-template-static-doc" / root.name,
    root,
    workspace_root,
    materialized_paths=materialized_control_plane_paths,
)
template_stream_registry_path = template_stream_repo / stream_versioned_rel
template_stream_doc = load_yaml(template_stream_registry_path)
template_mandatory_static_docs = template_stream_doc.get("mandatory_static_docs") or []
if template_doc_rel.as_posix() not in template_mandatory_static_docs:
    raise SystemExit("template doc is not present in mandatory_static_docs for negative probe")
template_stream_doc["mandatory_static_docs"] = [
    item for item in template_mandatory_static_docs if str(item).strip() != template_doc_rel.as_posix()
]
template_stream_registry_path.write_text(
    yaml.safe_dump(template_stream_doc, sort_keys=False, allow_unicode=False),
    encoding="utf-8",
)
template_stream_rc, template_stream_payload = run_validator(template_stream_repo, template_stream_repo.parent)
if template_stream_rc == 0:
    raise SystemExit("stream-doc-registry missing-template-static-doc negative probe unexpectedly passed")
template_stream_violations = [str(item) for item in (template_stream_payload.get("violations") or [])]
expected_template_stream_violation = f"stream_doc_registry_missing_static_doc:{template_doc_rel.as_posix()}"
if template_stream_payload.get("error_code") != ERR_STREAM_DOC_REGISTRY:
    raise SystemExit(
        f"stream-doc-registry missing-template-static-doc probe returned wrong error code: {template_stream_payload}"
    )
if expected_template_stream_violation not in template_stream_violations:
    raise SystemExit(
        f"stream-doc-registry missing-template-static-doc violation missing: {template_stream_payload}"
    )

stale_projection_repo = build_probe_repo(
    tmp_root / "projection-boundary-only-stale-counts" / root.name,
    root,
    workspace_root,
    materialized_paths=materialized_control_plane_paths,
)
stale_projection_path = materialize_workspace_file(stale_projection_repo, workspace_root, issue_projection_rel)
stale_projection_text = stale_projection_path.read_text(encoding="utf-8")
if not DOCS_CHECKED_LINE_RE.search(stale_projection_text) or not ISSUE_REGISTER_COUNT_LINE_RE.search(
    stale_projection_text
):
    raise SystemExit("projection stale-count probe could not find expected live counters")
stale_projection_text = DOCS_CHECKED_LINE_RE.sub("docs checked: 999", stale_projection_text, count=1)
stale_projection_text = ISSUE_REGISTER_COUNT_LINE_RE.sub(
    "issue_register_issue_count=999",
    stale_projection_text,
    count=1,
)
stale_projection_path.write_text(stale_projection_text, encoding="utf-8")
stale_projection_rc, stale_projection_payload = run_validator(stale_projection_repo, stale_projection_repo.parent)
if stale_projection_rc != 0 or stale_projection_payload.get("issue_register_consistency_status") != STATUS_PASS_REQUIRED:
    raise SystemExit(f"boundary-only stale projection probe unexpectedly failed: {stale_projection_payload}")

authority_projection_repo = build_probe_repo(
    tmp_root / "projection-authority-claim" / root.name,
    root,
    workspace_root,
    materialized_paths=materialized_control_plane_paths,
)
authority_projection_path = materialize_workspace_file(authority_projection_repo, workspace_root, issue_projection_rel)
authority_projection_text = authority_projection_path.read_text(encoding="utf-8")
if PROJECTION_BOUNDARY_MARKER not in authority_projection_text:
    raise SystemExit("projection authority-claim probe could not find boundary marker")
authority_projection_text = authority_projection_text.replace(
    PROJECTION_BOUNDARY_MARKER,
    PROJECTION_BOUNDARY_MARKER + "\n" + PROJECTION_FORBIDDEN_SENTENCE,
    1,
)
authority_projection_path.write_text(authority_projection_text, encoding="utf-8")
authority_projection_rc, authority_projection_payload = run_validator(
    authority_projection_repo,
    authority_projection_repo.parent,
)
if authority_projection_rc == 0:
    raise SystemExit("projection authority-claim negative probe unexpectedly passed")
authority_projection_violations = [str(item) for item in (authority_projection_payload.get("violations") or [])]
expected_authority_projection_violation = "projection_authority_claim:issue_register_projection"
if authority_projection_payload.get("error_code") != ERR_WORKBOOK_BOUNDARY:
    raise SystemExit(
        f"projection authority-claim negative probe returned wrong error code: {authority_projection_payload}"
    )
if expected_authority_projection_violation not in authority_projection_violations:
    raise SystemExit(
        f"projection authority-claim violation missing: {authority_projection_payload}"
    )

print(
    json.dumps(
        {
            "workbook_control_plane_probe_status": STATUS_PASS_REQUIRED,
            "workbook_family": workbook_family,
            "positive_status": positive.get("issue_register_consistency_status"),
            "baseline_shadow_status": baseline_shadow_payload.get("issue_register_consistency_status"),
            "negative_extra_doc_error_code": extra_payload.get("error_code"),
            "negative_extra_doc_violation": expected_extra_rel,
            "negative_stream_doc_error_code": stream_payload.get("error_code"),
            "negative_stream_doc_violation": expected_stream_violation,
            "negative_template_stream_doc_error_code": template_stream_payload.get("error_code"),
            "negative_template_stream_doc_violation": expected_template_stream_violation,
            "boundary_only_stale_projection_status": stale_projection_payload.get("issue_register_consistency_status"),
            "negative_projection_authority_error_code": authority_projection_payload.get("error_code"),
            "negative_projection_authority_violation": expected_authority_projection_violation,
            "tmp_root": str(tmp_root),
        },
        ensure_ascii=False,
    )
)
PY
