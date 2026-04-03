#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from release_closure_doc_common import RELEASE_CLOSURE_DOC_REL_PATHS


@dataclass(frozen=True)
class ReleaseClosureRequiredDocSpec:
    doc_family: str
    relpaths: tuple[str, ...]


RELEASE_CLOSURE_SUMMARY_REQUIRED_DOC_RELPATHS: tuple[str, ...] = (
    RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.protocol_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.runtime_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.issue_register_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.workbook_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
)

RELEASE_CLOSURE_BOUNDARY_REQUIRED_DOC_RELPATHS: tuple[str, ...] = (
    RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.protocol_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.runtime_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.issue_register_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
)

RELEASE_CLOSURE_REQUIRED_DOC_SPECS: tuple[ReleaseClosureRequiredDocSpec, ...] = (
    ReleaseClosureRequiredDocSpec(
        doc_family="summary_required_docs",
        relpaths=RELEASE_CLOSURE_SUMMARY_REQUIRED_DOC_RELPATHS,
    ),
    ReleaseClosureRequiredDocSpec(
        doc_family="boundary_required_docs",
        relpaths=RELEASE_CLOSURE_BOUNDARY_REQUIRED_DOC_RELPATHS,
    ),
)


def _select_required_doc_spec(doc_family: str) -> ReleaseClosureRequiredDocSpec:
    for spec in RELEASE_CLOSURE_REQUIRED_DOC_SPECS:
        if spec.doc_family == doc_family:
            return spec
    raise RuntimeError(f"release_closure_required_doc_spec_unresolved:{doc_family}")


def collect_release_closure_required_doc_stale_reasons(
    repo_root: Path,
    *,
    required_relpaths: tuple[str, ...],
) -> list[str]:
    stale_reasons: list[str] = []
    for relpath in required_relpaths:
        if not (repo_root / relpath).exists():
            stale_reasons.append(f"missing_required_doc:{(repo_root / relpath).resolve()}")
    return stale_reasons


def collect_release_closure_summary_required_doc_bundle_stale_reasons(
    repo_root: Path,
) -> list[str]:
    return collect_release_closure_required_doc_stale_reasons(
        repo_root,
        required_relpaths=RELEASE_CLOSURE_SUMMARY_REQUIRED_DOC_RELPATHS,
    )


def collect_release_closure_boundary_required_doc_bundle_stale_reasons(
    repo_root: Path,
) -> list[str]:
    return collect_release_closure_required_doc_stale_reasons(
        repo_root,
        required_relpaths=RELEASE_CLOSURE_BOUNDARY_REQUIRED_DOC_RELPATHS,
    )


def _validate_release_closure_required_doc_specs() -> None:
    summary_spec = _select_required_doc_spec("summary_required_docs")
    boundary_spec = _select_required_doc_spec("boundary_required_docs")
    if not summary_spec.relpaths:
        raise RuntimeError("release_closure_required_doc_bundle_empty:summary")
    if not boundary_spec.relpaths:
        raise RuntimeError("release_closure_required_doc_bundle_empty:boundary")
    if len(set(summary_spec.relpaths)) != len(summary_spec.relpaths):
        raise RuntimeError("release_closure_required_doc_bundle_duplicate_relpath:summary")
    if len(set(boundary_spec.relpaths)) != len(boundary_spec.relpaths):
        raise RuntimeError("release_closure_required_doc_bundle_duplicate_relpath:boundary")


_validate_release_closure_required_doc_specs()
