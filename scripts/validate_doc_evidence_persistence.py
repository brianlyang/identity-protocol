#!/usr/bin/env python3
"""
Validate evidence persistence policy for governance/review docs.

Round-29.5 contract (frozen):
1) Governance docs: no /tmp as long-term evidence path.
2) Review docs: /tmp allowed only with persistent mirror + tuple metadata.
3) Persistent evidence path allowlist:
   - activity/evidence/<stream>/<date>/...
   - .identity/<id>/runtime/reports/...
4) Mirrored evidence must expose tuple fields:
   sha256, command, rc, timestamp.

Execution model:
- Strict full-scan on v1.6.x stream docs (v1.6.1/v1.6.2/v1.6.3).
- Delta-scan on newly-added lines for all governance/review docs
  (prevents *new* /tmp debt without breaking historical backlog).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from contract_binding_mapping_common import is_stream_version


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_POLICY = "IP-DOC-EVID-001"
STREAM_DOC_REGISTRY_FILE = "identity/protocol/mappings/stream-doc-registry.current.yaml"

TMP_PREFIXES = ("/tmp/", "/private/tmp/")
ALLOWED_PERSISTENT_PREFIXES = (
    "activity/evidence/",
    ".identity/",
)
ALLOWED_IDENTITY_REPORT_RE = re.compile(r"^\.identity/[^/\s]+/runtime/reports/.+")
ALLOWED_ACTIVITY_RE = re.compile(r"^activity/evidence/[^/\s]+/\d{4}-\d{2}-\d{2}/.+")
PATH_TOKEN_RE = re.compile(
    r"(?P<path>(?:/tmp/|/private/tmp/|activity/evidence/|\.identity/)[^\s`\"'()<>\]]+)"
)
REQUIRED_TUPLE_FIELDS = ("sha256", "command", "rc", "timestamp")
EVIDENCE_ALLOWLIST_FILE = "identity/protocol/mappings/doc-evidence-allowlist.current.yaml"


def _norm_path(value: str) -> str:
    text = str(value or "").strip().replace("\\", "/")
    return text.rstrip(".,;:")


def _doc_scope(rel: str) -> str:
    if rel.startswith("docs/governance/"):
        return "governance"
    if rel.startswith("docs/review/"):
        return "review"
    return "unknown"


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    current_doc = _load_yaml(configured_path)
    if not current_doc:
        return configured_path, "", "current_file_parse_failed"
    active_file = _norm_path(current_doc.get("active_file", ""))
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _load_strict_doc_scopes(repo_root: Path) -> tuple[dict[str, str], list[str], Path, Path]:
    """
    Read active stream governance/review docs from registry as single source.
    Returns (doc->scope map, validation_errors).
    """
    registry_entry_path = (repo_root / STREAM_DOC_REGISTRY_FILE).resolve()
    registry_path, active_file, alias_error = _resolve_current_yaml_alias(repo_root, STREAM_DOC_REGISTRY_FILE)
    if alias_error:
        return (
            {},
            [f"stream_doc_registry_invalid:alias_resolution_failed:{STREAM_DOC_REGISTRY_FILE}:{alias_error}:{active_file}"],
            registry_entry_path,
            registry_path,
        )
    if not registry_path.exists():
        return {}, [f"stream_doc_registry_missing:{registry_path}"], registry_entry_path, registry_path
    data = _load_yaml(registry_path)
    rows = data.get("stream_docs")
    if not isinstance(rows, list) or not rows:
        return (
            {},
            [f"stream_doc_registry_invalid:stream_docs_non_empty_list_required:{registry_path}"],
            registry_entry_path,
            registry_path,
        )

    scopes: dict[str, str] = {}
    errors: list[str] = []
    stream_versions_seen: set[str] = set()
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"stream_doc_registry_invalid:row_{idx}_must_be_mapping")
            continue
        stream_version = str(row.get("stream_version", "")).strip() or f"row_{idx}"
        if stream_version in stream_versions_seen:
            errors.append(f"stream_doc_registry_invalid:duplicate_stream_version:{stream_version}")
        if stream_version.startswith("row_") or not is_stream_version(stream_version):
            errors.append(f"stream_doc_registry_invalid:invalid_stream_version_format:{stream_version}")
        stream_versions_seen.add(stream_version)
        governance_doc = _norm_path(row.get("governance_doc", ""))
        review_doc = _norm_path(row.get("review_doc", ""))
        if not governance_doc:
            errors.append(f"stream_doc_registry_invalid:{stream_version}:missing_governance_doc")
        elif governance_doc in scopes and scopes[governance_doc] != "governance":
            errors.append(f"stream_doc_registry_invalid:{stream_version}:governance_doc_scope_conflict:{governance_doc}")
        else:
            scopes[governance_doc] = "governance"
        if not review_doc:
            errors.append(f"stream_doc_registry_invalid:{stream_version}:missing_review_doc")
        elif review_doc in scopes and scopes[review_doc] != "review":
            errors.append(f"stream_doc_registry_invalid:{stream_version}:review_doc_scope_conflict:{review_doc}")
        else:
            scopes[review_doc] = "review"

    if not scopes:
        errors.append("stream_doc_registry_invalid:no_strict_docs_resolved")
    return scopes, errors, registry_entry_path, registry_path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _collect_paths(text: str) -> tuple[list[str], list[str], list[str]]:
    tmp_refs: list[str] = []
    persistent_refs: list[str] = []
    persistent_dir_refs: list[str] = []
    for m in PATH_TOKEN_RE.finditer(text or ""):
        raw = _norm_path(m.group("path"))
        if not raw:
            continue
        if raw in {"/tmp/", "/private/tmp/", "activity/evidence/", ".identity/"}:
            continue
        # ignore placeholders / globs
        if "..." in raw or "*" in raw or "<" in raw or ">":
            continue
        if raw.endswith("/"):
            if raw.startswith(ALLOWED_PERSISTENT_PREFIXES):
                persistent_dir_refs.append(raw)
            continue
        if raw.startswith(TMP_PREFIXES):
            tmp_refs.append(raw)
            continue
        if raw.startswith(ALLOWED_PERSISTENT_PREFIXES):
            if raw.startswith(".identity/") and "/runtime/reports/" not in raw:
                # .identity path may be config/reference; only runtime/reports is evidence mirror contract.
                continue
            persistent_refs.append(raw)
    return sorted(set(tmp_refs)), sorted(set(persistent_refs)), sorted(set(persistent_dir_refs))


def _allowed_persistent_path(path: str) -> bool:
    p = _norm_path(path)
    if p.startswith("activity/evidence/"):
        return bool(ALLOWED_ACTIVITY_RE.match(p))
    if p.startswith(".identity/"):
        return bool(ALLOWED_IDENTITY_REPORT_RE.match(p))
    return False


def _load_manifest_records(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    by_mirror: dict[str, dict[str, Any]] = {}
    by_tmp: dict[str, dict[str, Any]] = {}
    manifests: list[str] = []
    for manifest in sorted(repo_root.glob("activity/evidence/**/EVIDENCE_MANIFEST*.json")):
        rel_manifest = str(manifest.relative_to(repo_root)).replace("\\", "/")
        manifests.append(rel_manifest)
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            continue
        rows = data.get("evidence_records") or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            mirror = _norm_path(row.get("mirror_path", ""))
            tmp = _norm_path(row.get("tmp_path", ""))
            record = dict(row)
            record["_manifest_path"] = rel_manifest
            if mirror:
                by_mirror[mirror] = record
            if tmp:
                by_tmp[tmp] = record
    return by_mirror, by_tmp, manifests


def _run_git_diff(repo_root: Path, *, base: str, head: str) -> str:
    cmd = ["git", "diff", "--unified=0", "--no-color"]
    if base and head:
        cmd.append(f"{base}..{head}")
    cmd.extend(["--", "docs/governance", "docs/review"])
    proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    return proc.stdout


def _collect_delta_added_lines(repo_root: Path, *, base: str, head: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}

    def ingest(diff_text: str) -> None:
        current: str | None = None
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current = _norm_path(line[len("+++ b/") :])
                if current not in out:
                    out[current] = []
                continue
            if line.startswith("@@"):
                continue
            if line.startswith("+") and not line.startswith("+++"):
                if current:
                    out.setdefault(current, []).append(line[1:])

    if base and head:
        ingest(_run_git_diff(repo_root, base=base, head=head))
        return {k: v for k, v in out.items() if v}

    # local fallback: staged + unstaged
    ingest(_run_git_diff(repo_root, base="", head=""))
    proc = subprocess.run(
        ["git", "diff", "--cached", "--unified=0", "--no-color", "--", "docs/governance", "docs/review"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        ingest(proc.stdout)
    return {k: v for k, v in out.items() if v}


def _validate_tmp_for_review_doc(
    *,
    doc_rel: str,
    tmp_path: str,
    by_tmp: dict[str, dict[str, Any]],
    full_persistent_refs: set[str],
    violations: list[dict[str, Any]],
) -> None:
    rec = by_tmp.get(tmp_path)
    if not rec:
        violations.append(
            {
                "type": "review_tmp_without_mirror",
                "doc": doc_rel,
                "scope": "review",
                "tmp_path": tmp_path,
                "error_code": "IP-DOC-EVID-003",
            }
        )
        return
    mirror = _norm_path(rec.get("mirror_path", ""))
    if not mirror or not _allowed_persistent_path(mirror):
        violations.append(
            {
                "type": "review_tmp_mirror_path_invalid",
                "doc": doc_rel,
                "scope": "review",
                "tmp_path": tmp_path,
                "mirror_path": mirror,
                "manifest": rec.get("_manifest_path", ""),
                "error_code": "IP-DOC-EVID-004",
            }
        )
        return
    if mirror not in full_persistent_refs:
        violations.append(
            {
                "type": "review_tmp_mirror_not_referenced",
                "doc": doc_rel,
                "scope": "review",
                "tmp_path": tmp_path,
                "mirror_path": mirror,
                "manifest": rec.get("_manifest_path", ""),
                "error_code": "IP-DOC-EVID-010",
            }
        )


def _validate_activity_mirror_ref(
    *,
    repo_root: Path,
    ref: str,
    by_mirror: dict[str, dict[str, Any]],
    violations: list[dict[str, Any]],
) -> None:
    file_path = repo_root / ref
    if not file_path.exists():
        violations.append(
            {
                "type": "mirror_file_missing",
                "path": ref,
                "error_code": "IP-DOC-EVID-006",
            }
        )
        return
    if file_path.name.startswith("EVIDENCE_MANIFEST"):
        # manifest is the tuple index and does not need self-index tuple.
        return
    rec = by_mirror.get(ref)
    if not rec:
        violations.append(
            {
                "type": "mirror_metadata_missing",
                "path": ref,
                "error_code": "IP-DOC-EVID-007",
            }
        )
        return
    missing = [k for k in REQUIRED_TUPLE_FIELDS if rec.get(k) in ("", None)]
    if missing:
        violations.append(
            {
                "type": "mirror_tuple_incomplete",
                "path": ref,
                "manifest": rec.get("_manifest_path", ""),
                "missing_fields": missing,
                "error_code": "IP-DOC-EVID-008",
            }
        )
        return
    declared_sha = _norm_path(rec.get("sha256", ""))
    actual_sha = _sha256_file(file_path)
    if declared_sha != actual_sha:
        violations.append(
            {
                "type": "mirror_sha_mismatch",
                "path": ref,
                "manifest": rec.get("_manifest_path", ""),
                "declared_sha256": declared_sha,
                "actual_sha256": actual_sha,
                "error_code": "IP-DOC-EVID-009",
            }
        )


def _validate_strict_doc_evidence_allowlist(
    *,
    doc_rel: str,
    persistent_refs: list[str],
    allowlist_doc: dict[str, Any] | None,
    violations: list[dict[str, Any]],
) -> None:
    if allowlist_doc is None:
        violations.append(
            {
                "type": "strict_doc_allowlist_missing",
                "doc": doc_rel,
                "error_code": "IP-DOC-EVID-012",
            }
        )
        return
    patterns_raw = allowlist_doc.get("allowed_activity_patterns")
    if not isinstance(patterns_raw, list) or not patterns_raw:
        violations.append(
            {
                "type": "strict_doc_allowlist_pattern_missing",
                "doc": doc_rel,
                "error_code": "IP-DOC-EVID-012",
            }
        )
        return
    compiled_patterns: list[re.Pattern[str]] = []
    for raw in patterns_raw:
        token = str(raw or "").strip()
        if not token:
            continue
        try:
            compiled_patterns.append(re.compile(token))
        except re.error:
            violations.append(
                {
                    "type": "strict_doc_allowlist_pattern_invalid",
                    "doc": doc_rel,
                    "pattern": token,
                    "error_code": "IP-DOC-EVID-012",
                }
            )
    activity_refs = [ref for ref in persistent_refs if ref.startswith("activity/evidence/")]
    max_refs = allowlist_doc.get("max_activity_refs", 0)
    if isinstance(max_refs, int) and max_refs > 0 and len(activity_refs) > max_refs:
        violations.append(
            {
                "type": "strict_doc_activity_ref_count_exceeded",
                "doc": doc_rel,
                "observed_count": len(activity_refs),
                "max_allowed": max_refs,
                "error_code": "IP-DOC-EVID-013",
            }
        )
    for ref in activity_refs:
        matched = any(pat.match(ref) for pat in compiled_patterns)
        if matched:
            continue
        violations.append(
            {
                "type": "strict_doc_activity_ref_not_allowlisted",
                "doc": doc_rel,
                "path": ref,
                "error_code": "IP-DOC-EVID-012",
            }
        )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate governance/review evidence persistence policy.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--base", default="", help="git diff base sha (optional)")
    ap.add_argument("--head", default="", help="git diff head sha (optional)")
    ap.add_argument(
        "--enforce-delta",
        action="store_true",
        help="enable delta checks for newly-added lines in governance/review docs",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    violations: list[dict[str, Any]] = []

    by_mirror, by_tmp, manifest_files = _load_manifest_records(repo_root)
    (
        strict_doc_scopes,
        stream_registry_errors,
        stream_registry_entry_path,
        stream_registry_resolved_path,
    ) = _load_strict_doc_scopes(repo_root)
    evidence_allowlist_entry_path = (repo_root / EVIDENCE_ALLOWLIST_FILE).resolve()
    evidence_allowlist_path, evidence_allowlist_active_file, evidence_allowlist_alias_error = _resolve_current_yaml_alias(
        repo_root, EVIDENCE_ALLOWLIST_FILE
    )
    if evidence_allowlist_alias_error:
        violations.append(
            {
                "type": "evidence_allowlist_invalid",
                "error_code": ERR_POLICY,
                "reason": f"evidence_allowlist_alias_resolution_failed:{EVIDENCE_ALLOWLIST_FILE}:{evidence_allowlist_alias_error}:{evidence_allowlist_active_file}",
                "allowlist_file": EVIDENCE_ALLOWLIST_FILE,
            }
        )
    evidence_allowlist = _load_yaml(evidence_allowlist_path) if evidence_allowlist_path.exists() else {}
    strict_doc_allowlist = evidence_allowlist.get("strict_docs") if isinstance(evidence_allowlist, dict) else {}
    if not isinstance(strict_doc_allowlist, dict):
        strict_doc_allowlist = {}
    strict_scope_keys = set(strict_doc_scopes.keys())
    allowlist_scope_keys = {
        _norm_path(key)
        for key in strict_doc_allowlist.keys()
        if _doc_scope(_norm_path(str(key))) in {"governance", "review"}
    }
    all_persistent_refs: set[str] = set()

    for reason in stream_registry_errors:
        violations.append(
            {
                "type": "stream_doc_registry_invalid",
                "error_code": ERR_POLICY,
                "reason": reason,
                "registry_file": STREAM_DOC_REGISTRY_FILE,
                "registry_entry_path": str(stream_registry_entry_path),
                "registry_resolved_path": str(stream_registry_resolved_path),
            }
        )
    for orphan in sorted(allowlist_scope_keys - strict_scope_keys):
        violations.append(
            {
                "type": "strict_doc_allowlist_orphan_entry",
                "doc": orphan,
                "error_code": ERR_POLICY,
                "reason": "allowlist_entry_not_in_stream_registry",
                "registry_file": STREAM_DOC_REGISTRY_FILE,
                "allowlist_file": EVIDENCE_ALLOWLIST_FILE,
                "allowlist_entry_path": str(evidence_allowlist_entry_path),
                "allowlist_resolved_path": str(evidence_allowlist_path),
            }
        )

    # Strict stream full-scan (v1.6.x docs from stream-doc-registry)
    docs_checked: set[str] = set()
    for rel, scope in strict_doc_scopes.items():
        docs_checked.add(rel)
        p = repo_root / rel
        if not p.exists():
            violations.append(
                {
                    "type": "missing_doc",
                    "doc": rel,
                    "scope": scope,
                    "error_code": "IP-DOC-EVID-404",
                }
            )
            continue
        text = p.read_text(encoding="utf-8")
        tmp_refs, persistent_refs, _ = _collect_paths(text)
        all_persistent_refs.update(persistent_refs)
        _validate_strict_doc_evidence_allowlist(
            doc_rel=rel,
            persistent_refs=persistent_refs,
            allowlist_doc=(strict_doc_allowlist.get(rel) if isinstance(strict_doc_allowlist, dict) else None),
            violations=violations,
        )

        if scope == "governance":
            for ref in tmp_refs:
                violations.append(
                    {
                        "type": "governance_tmp_forbidden",
                        "doc": rel,
                        "scope": scope,
                        "tmp_path": ref,
                        "error_code": "IP-DOC-EVID-002",
                    }
                )
        else:
            full_persistent_set = set(persistent_refs)
            for tmp in tmp_refs:
                _validate_tmp_for_review_doc(
                    doc_rel=rel,
                    tmp_path=tmp,
                    by_tmp=by_tmp,
                    full_persistent_refs=full_persistent_set,
                    violations=violations,
                )

    # Delta-scan for newly added lines across governance/review docs.
    delta_added: dict[str, list[str]] = {}
    if args.enforce_delta:
        delta_added = _collect_delta_added_lines(repo_root, base=args.base.strip(), head=args.head.strip())
        for rel, added_lines in sorted(delta_added.items()):
            scope = _doc_scope(rel)
            if scope not in {"governance", "review"}:
                continue
            docs_checked.add(rel)
            added_text = "\n".join(added_lines)
            added_tmp_refs, added_persistent_refs, added_persistent_dir_refs = _collect_paths(added_text)

            doc_path = repo_root / rel
            full_persistent_refs: set[str] = set()
            if doc_path.exists():
                _, full_persistent, _ = _collect_paths(doc_path.read_text(encoding="utf-8"))
                full_persistent_refs = set(full_persistent)

            if scope == "governance":
                for tmp in added_tmp_refs:
                    violations.append(
                        {
                            "type": "governance_tmp_added_forbidden",
                            "doc": rel,
                            "scope": scope,
                            "tmp_path": tmp,
                            "error_code": "IP-DOC-EVID-011",
                        }
                    )
            else:
                for tmp in added_tmp_refs:
                    _validate_tmp_for_review_doc(
                        doc_rel=rel,
                        tmp_path=tmp,
                        by_tmp=by_tmp,
                        full_persistent_refs=full_persistent_refs,
                        violations=violations,
                    )

            # Newly-added persistent refs must follow allowlist shape.
            for ref in added_persistent_refs:
                if not _allowed_persistent_path(ref):
                    violations.append(
                        {
                            "type": "persistent_path_out_of_contract",
                            "doc": rel,
                            "path": ref,
                            "error_code": "IP-DOC-EVID-005",
                        }
                    )
            for ref in added_persistent_dir_refs:
                violations.append(
                    {
                        "type": "persistent_directory_ref_added_forbidden",
                        "doc": rel,
                        "path": ref,
                        "reason": "directory_refs_are_not_replayable;use_manifest_or_concrete_file_path",
                        "error_code": "IP-DOC-EVID-005",
                    }
                )

    # Validate all collected persistent refs used by strict/delta docs.
    for ref in sorted(all_persistent_refs):
        if not _allowed_persistent_path(ref):
            violations.append(
                {
                    "type": "persistent_path_out_of_contract",
                    "path": ref,
                    "error_code": "IP-DOC-EVID-005",
                }
            )
            continue
        if ref.startswith("activity/evidence/"):
            _validate_activity_mirror_ref(
                repo_root=repo_root,
                ref=ref,
                by_mirror=by_mirror,
                violations=violations,
            )

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "doc_evidence_persistence_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_POLICY,
        "stream_doc_registry_file": STREAM_DOC_REGISTRY_FILE,
        "stream_doc_registry_entry_path": str(stream_registry_entry_path),
        "stream_doc_registry_resolved_path": str(stream_registry_resolved_path),
        "stream_doc_registry_error_count": len(stream_registry_errors),
        "stream_doc_registry_errors": stream_registry_errors,
        "evidence_allowlist_file": EVIDENCE_ALLOWLIST_FILE,
        "evidence_allowlist_entry_path": str(evidence_allowlist_entry_path),
        "evidence_allowlist_path": str(evidence_allowlist_path),
        "evidence_allowlist_alias_error": evidence_allowlist_alias_error,
        "strict_docs_checked": list(strict_doc_scopes.keys()),
        "docs_checked_total": len(docs_checked),
        "docs_checked": sorted(docs_checked),
        "delta_enforced": bool(args.enforce_delta),
        "delta_docs_detected": len(delta_added),
        "delta_mode": "base_head" if args.base.strip() and args.head.strip() else "local_git_diff",
        "delta_base": args.base.strip(),
        "delta_head": args.head.strip(),
        "required_tuple_fields": list(REQUIRED_TUPLE_FIELDS),
        "allowed_persistent_prefixes": list(ALLOWED_PERSISTENT_PREFIXES),
        "manifest_files_scanned": manifest_files,
        "violation_count": len(violations),
        "violations": violations[:300],
        "stale_reasons": [] if not violations else ["doc_evidence_persistence_policy_violation"],
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
