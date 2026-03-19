#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_STREAM = "IP-NCHAT-BOOT-001"

DEFAULT_STREAM_VERSION = "v1.6.12"
DEFAULT_STREAM_SLUG = "v1612-native-chat-bootstrap-entry"
DEFAULT_GOV_DOC = "docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md"
DEFAULT_REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.12-native-chat-bootstrap-entry.md"
DEFAULT_AUDIT_INDEX = "docs/governance/AUDIT_SNAPSHOT_INDEX.md"
DEFAULT_STREAM_DOC_REGISTRY = "identity/protocol/mappings/stream-doc-registry.current.yaml"
DEFAULT_DOC_EVIDENCE_ALLOWLIST = "identity/protocol/mappings/doc-evidence-allowlist.current.yaml"
DEFAULT_SUMMARY_NAME = "bootstrap_entry_summary.v1.6.12.json"
DEFAULT_MANIFEST_NAME = "EVIDENCE_MANIFEST.v1.6.12-native-chat-bootstrap-entry.json"

CHECK_SCOPE_FULL = "full"
CHECK_SCOPE_BUNDLE_ONLY = "bundle_only"
ALLOWED_CHECK_SCOPES = (CHECK_SCOPE_FULL, CHECK_SCOPE_BUNDLE_ONLY)

ALLOWED_LIVE_SMOKE_STATUSES = {
    STATUS_PASS_REQUIRED,
    "INCONCLUSIVE_HOST_RUNTIME_PANIC",
}
REQUIRED_POSITIVE_RECORD_KINDS = {
    "stream_summary",
    "fast_audit_summary",
    "protocol_authority_resolve",
    "wrapper_dry_run_resume",
    "wrapper_dry_run_exec",
}
REQUIRED_INCONCLUSIVE_RECORD_KINDS = {
    "live_smoke_timeout_audit",
    "live_smoke_stderr",
}
REQUIRED_RECORD_FIELDS = ("mirror_path", "sha256", "command", "rc", "timestamp")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return data


def _norm_path(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _relative(repo_root: Path, path: Path) -> str:
    return _norm_path(str(path.resolve().relative_to(repo_root.resolve())))


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / _norm_path(configured_rel)).resolve()
    if not configured_path.exists():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    current_doc = _load_yaml(configured_path)
    active_file = _norm_path(current_doc.get("active_file", ""))
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _discover_latest_bundle_root(repo_root: Path, stream_slug: str) -> Path:
    root = (repo_root / "activity" / "evidence" / stream_slug).resolve()
    if not root.exists():
        raise RuntimeError(f"bundle_root_missing:{root}")
    candidates = sorted(path for path in root.iterdir() if path.is_dir())
    if not candidates:
        raise RuntimeError(f"bundle_date_missing:{root}")
    return candidates[-1]


def _matches_any(patterns: list[str], rel_path: str) -> bool:
    for pattern in patterns:
        token = str(pattern or "").strip()
        if not token:
            continue
        if re.match(token, rel_path):
            return True
    return False


def _failure(payload: dict[str, Any], reason: str) -> None:
    failures = payload.setdefault("failures", [])
    if reason not in failures:
        failures.append(reason)


def _validate_registry(payload: dict[str, Any], *, repo_root: Path, stream_version: str, governance_doc: str, review_doc: str, registry_rel: str) -> None:
    resolved_path, active_file, alias_error = _resolve_current_yaml_alias(repo_root, registry_rel)
    payload["stream_doc_registry_entry"] = str((repo_root / registry_rel).resolve())
    payload["stream_doc_registry_resolved"] = str(resolved_path)
    payload["stream_doc_registry_active_file"] = active_file
    payload["stream_doc_registry_alias_error"] = alias_error
    if alias_error:
        _failure(payload, f"stream_doc_registry_alias_error:{alias_error}")
        return
    data = _load_yaml(resolved_path)
    rows = data.get("stream_docs") or []
    if not isinstance(rows, list):
        _failure(payload, "stream_doc_registry_stream_docs_invalid")
        return
    row = next(
        (
            item
            for item in rows
            if isinstance(item, dict) and str(item.get("stream_version", "")).strip() == stream_version
        ),
        None,
    )
    if row is None:
        _failure(payload, f"stream_doc_registry_missing_stream:{stream_version}")
        return
    if _norm_path(row.get("governance_doc", "")) != governance_doc:
        _failure(payload, "stream_doc_registry_governance_doc_mismatch")
    if _norm_path(row.get("review_doc", "")) != review_doc:
        _failure(payload, "stream_doc_registry_review_doc_mismatch")


def _validate_allowlist(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    governance_doc: str,
    review_doc: str,
    allowlist_rel: str,
    manifest_rel: str,
    summary_rel: str,
) -> None:
    resolved_path, active_file, alias_error = _resolve_current_yaml_alias(repo_root, allowlist_rel)
    payload["doc_evidence_allowlist_entry"] = str((repo_root / allowlist_rel).resolve())
    payload["doc_evidence_allowlist_resolved"] = str(resolved_path)
    payload["doc_evidence_allowlist_active_file"] = active_file
    payload["doc_evidence_allowlist_alias_error"] = alias_error
    if alias_error:
        _failure(payload, f"doc_evidence_allowlist_alias_error:{alias_error}")
        return
    data = _load_yaml(resolved_path)
    strict_docs = data.get("strict_docs") or {}
    if not isinstance(strict_docs, dict):
        _failure(payload, "doc_evidence_allowlist_strict_docs_invalid")
        return
    for doc_key in (governance_doc, review_doc):
        row = strict_docs.get(doc_key) or {}
        if not isinstance(row, dict):
            _failure(payload, f"doc_evidence_allowlist_missing_doc:{doc_key}")
            continue
        patterns = row.get("allowed_activity_patterns") or row.get("allowed_evidence") or []
        if not isinstance(patterns, list):
            _failure(payload, f"doc_evidence_allowlist_patterns_invalid:{doc_key}")
            continue
        if not _matches_any(patterns, manifest_rel):
            _failure(payload, f"doc_evidence_allowlist_manifest_missing:{doc_key}")
        if not _matches_any(patterns, summary_rel):
            _failure(payload, f"doc_evidence_allowlist_summary_missing:{doc_key}")


def _validate_audit_index(payload: dict[str, Any], *, repo_root: Path, audit_index_rel: str, governance_doc: str, review_doc: str) -> None:
    audit_index = (repo_root / audit_index_rel).resolve()
    payload["audit_snapshot_index"] = str(audit_index)
    if not audit_index.exists():
        _failure(payload, f"audit_snapshot_index_missing:{audit_index_rel}")
        return
    text = audit_index.read_text(encoding="utf-8")
    if governance_doc not in text:
        _failure(payload, "audit_snapshot_index_governance_doc_missing")
    if review_doc not in text:
        _failure(payload, "audit_snapshot_index_review_doc_missing")


def _validate_summary_and_manifest(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    stream_version: str,
    manifest_path: Path,
    summary_path: Path,
    governance_doc: str,
    review_doc: str,
) -> None:
    summary = _load_json(summary_path)
    manifest = _load_json(manifest_path)
    payload["summary_path"] = str(summary_path)
    payload["manifest_path"] = str(manifest_path)
    payload["summary_ref"] = _relative(repo_root, summary_path)
    payload["manifest_ref"] = _relative(repo_root, manifest_path)

    if str(summary.get("stream_version", "")).strip() != stream_version:
        _failure(payload, "summary_stream_version_mismatch")
    if str(manifest.get("stream_version", "")).strip() != stream_version:
        _failure(payload, "manifest_stream_version_mismatch")
    if str(summary.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        _failure(payload, "summary_status_not_pass_required")

    four_track = summary.get("four_track_alignment") or {}
    if not isinstance(four_track, dict):
        _failure(payload, "summary_four_track_alignment_invalid")
    else:
        if _norm_path(four_track.get("t1_roundtable", "")) == "":
            _failure(payload, "summary_t1_roundtable_missing")
        if _norm_path(four_track.get("t2_execution_runtime", "")) == "":
            _failure(payload, "summary_t2_execution_runtime_missing")
        t3 = four_track.get("t3_protocol_kernel") or []
        if not isinstance(t3, list) or len(t3) < 2:
            _failure(payload, "summary_t3_protocol_kernel_missing")
        if _norm_path(four_track.get("t4_replay_bundle", "")) != _relative(repo_root, manifest_path):
            _failure(payload, "summary_t4_replay_bundle_mismatch")

    fast_audit = summary.get("fast_audit") or {}
    if not isinstance(fast_audit, dict) or str(fast_audit.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        _failure(payload, "fast_audit_not_pass_required")

    wrapper_dry_runs = summary.get("wrapper_dry_runs") or []
    if not isinstance(wrapper_dry_runs, list) or len(wrapper_dry_runs) < 2:
        _failure(payload, "wrapper_dry_runs_missing")
    else:
        for row in wrapper_dry_runs:
            if not isinstance(row, dict) or str(row.get("status", "")).strip() != STATUS_PASS_REQUIRED:
                _failure(payload, "wrapper_dry_runs_not_pass_required")
                break

    authority = summary.get("protocol_authority_resolve") or {}
    if not isinstance(authority, dict) or str(authority.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        _failure(payload, "protocol_authority_resolve_not_pass_required")

    live_smoke = summary.get("live_smoke") or {}
    live_smoke_status = str(live_smoke.get("status", "")).strip()
    payload["live_smoke_status"] = live_smoke_status
    if live_smoke_status not in ALLOWED_LIVE_SMOKE_STATUSES:
        _failure(payload, "live_smoke_status_not_allowed_for_stream_opening")
    if live_smoke_status == "INCONCLUSIVE_HOST_RUNTIME_PANIC":
        payload["live_smoke_contract_classification"] = "HOST_RUNTIME_INCONCLUSIVE_NON_PROMOTIONAL"
        payload["promotion_status"] = "NON_PROMOTIONAL_LOCK"
    elif live_smoke_status == STATUS_PASS_REQUIRED:
        payload["live_smoke_contract_classification"] = "PROMOTION_SIGNAL_PASS"
        payload["promotion_status"] = "PROMOTION_REVIEW_ELIGIBLE"
    else:
        payload["live_smoke_contract_classification"] = "FAIL_REQUIRED"
        payload["promotion_status"] = STATUS_FAIL_REQUIRED

    if str(manifest.get("summary_ref", "")).strip() != _relative(repo_root, summary_path):
        _failure(payload, "manifest_summary_ref_mismatch")

    evidence_records = manifest.get("evidence_records") or []
    if not isinstance(evidence_records, list) or not evidence_records:
        _failure(payload, "manifest_evidence_records_missing")
        return

    kinds: list[str] = []
    for idx, row in enumerate(evidence_records, start=1):
        if not isinstance(row, dict):
            _failure(payload, f"manifest_record_invalid:{idx}")
            continue
        kind = str(row.get("kind", "")).strip()
        if kind:
            kinds.append(kind)
        missing_fields = [field for field in REQUIRED_RECORD_FIELDS if row.get(field, "") == ""]
        if missing_fields:
            _failure(payload, f"manifest_record_missing_fields:{idx}:{','.join(missing_fields)}")

    payload["manifest_record_kinds"] = sorted(set(kinds))
    for required_kind in REQUIRED_POSITIVE_RECORD_KINDS:
        if required_kind not in kinds:
            _failure(payload, f"manifest_missing_record_kind:{required_kind}")
    if kinds.count("fast_audit_identity") < 1:
        _failure(payload, "manifest_missing_fast_audit_identity_record")
    if live_smoke_status == "INCONCLUSIVE_HOST_RUNTIME_PANIC":
        for required_kind in REQUIRED_INCONCLUSIVE_RECORD_KINDS:
            if required_kind not in kinds:
                _failure(payload, f"manifest_missing_inconclusive_record_kind:{required_kind}")

    notes = manifest.get("notes") or []
    if not isinstance(notes, list) or len(notes) < 2:
        _failure(payload, "manifest_notes_missing")

    payload["governance_doc"] = governance_doc
    payload["review_doc"] = review_doc


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate the v1.6.12 native-chat bootstrap entry stream opening contract without reopening stream semantics."
    )
    ap.add_argument("--stream-version", default=DEFAULT_STREAM_VERSION)
    ap.add_argument("--stream-slug", default=DEFAULT_STREAM_SLUG)
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--summary", default="")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--governance-doc", default=DEFAULT_GOV_DOC)
    ap.add_argument("--review-doc", default=DEFAULT_REVIEW_DOC)
    ap.add_argument("--audit-index", default=DEFAULT_AUDIT_INDEX)
    ap.add_argument("--stream-doc-registry", default=DEFAULT_STREAM_DOC_REGISTRY)
    ap.add_argument("--doc-evidence-allowlist", default=DEFAULT_DOC_EVIDENCE_ALLOWLIST)
    ap.add_argument("--check-scope", choices=ALLOWED_CHECK_SCOPES, default=CHECK_SCOPE_FULL)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve() if str(args.repo_root).strip() else _repo_root()
    summary_path = Path(args.summary).expanduser().resolve() if str(args.summary).strip() else None
    manifest_path = Path(args.manifest).expanduser().resolve() if str(args.manifest).strip() else None
    if summary_path is None or manifest_path is None:
        bundle_root = _discover_latest_bundle_root(repo_root, args.stream_slug)
        summary_path = summary_path or (bundle_root / DEFAULT_SUMMARY_NAME).resolve()
        manifest_path = manifest_path or (bundle_root / DEFAULT_MANIFEST_NAME).resolve()

    payload: dict[str, Any] = {
        "status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "stream_version": str(args.stream_version).strip(),
        "stream_slug": str(args.stream_slug).strip(),
        "check_scope": str(args.check_scope).strip(),
        "stream_opening_status": STATUS_PASS_REQUIRED,
        "promotion_status": "UNKNOWN",
        "live_smoke_contract_classification": "UNKNOWN",
        "failures": [],
    }

    try:
        if args.check_scope == CHECK_SCOPE_FULL:
            manifest_rel = _relative(repo_root, manifest_path)
            summary_rel = _relative(repo_root, summary_path)
            _validate_registry(
                payload,
                repo_root=repo_root,
                stream_version=args.stream_version,
                governance_doc=_norm_path(args.governance_doc),
                review_doc=_norm_path(args.review_doc),
                registry_rel=_norm_path(args.stream_doc_registry),
            )
            _validate_allowlist(
                payload,
                repo_root=repo_root,
                governance_doc=_norm_path(args.governance_doc),
                review_doc=_norm_path(args.review_doc),
                allowlist_rel=_norm_path(args.doc_evidence_allowlist),
                manifest_rel=manifest_rel,
                summary_rel=summary_rel,
            )
            _validate_audit_index(
                payload,
                repo_root=repo_root,
                audit_index_rel=_norm_path(args.audit_index),
                governance_doc=_norm_path(args.governance_doc),
                review_doc=_norm_path(args.review_doc),
            )
        _validate_summary_and_manifest(
            payload,
            repo_root=repo_root,
            stream_version=args.stream_version,
            manifest_path=manifest_path,
            summary_path=summary_path,
            governance_doc=_norm_path(args.governance_doc),
            review_doc=_norm_path(args.review_doc),
        )
    except Exception as exc:
        _failure(payload, f"exception:{exc}")

    if payload["failures"]:
        payload["status"] = STATUS_FAIL_REQUIRED
        payload["stream_opening_status"] = STATUS_FAIL_REQUIRED
        payload["promotion_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_STREAM

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
