#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from types import SimpleNamespace
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    evaluate_root_doc_anchor_checks,
    root_doc_anchor_checks_from_doc,
    validate_expected_root_doc_anchor_checks,
)
from root_corpus_governance_common import find_missing_markers, load_root_corpus_registry, root_corpus_entries_from_registry
from root_design_question_closure_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    load_root_design_question_closure,
    question_closure_rows_from_doc,
)
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_family
from root_stream_design_admissibility_common import load_root_stream_design_admissibility, required_question_rows_from_doc

STATUS_KEY = "protocol_root_design_question_closure_status"
ERR_REGISTRY = "IP-RDQC-001"
ERR_STRUCTURE = "IP-RDQC-002"
ERR_CLOSURE = "IP-RDQC-003"

EXPECTED_QUESTION_CLOSURE_ROWS = {
    "ontology": {
        "order": 1,
        "philosophy_marker": "1. **Ontology question**: What exactly is the new object, and is its ontology unambiguous?",
        "admissibility_question_id": "ontology",
        "admissibility_normative_focus": "object_identity_and_non_collapse",
        "target_component_id": "root_machine_world_ontology",
        "target_current_file": "identity/protocol/mappings/root-machine-world-ontology.current.yaml",
        "target_validator_script": "scripts/validate_protocol_root_machine_world_ontology.py",
        "target_status_key": "protocol_root_machine_world_ontology_status",
        "target_contract_file": "identity/protocol/MACHINE_WORLD_ONTOLOGY_CONTRACT.md",
        "target_required_markers": (
            "## Machine-world ontology law",
            "## Required ontology objects",
        ),
    },
    "truth_lifecycle": {
        "order": 2,
        "philosophy_marker": "2. **Truth-lifecycle question**: Where is the canonical truth; how is it discovered by instances, admitted, bound to the current run / current thread, and consumed by the next hop; and do state, receipt, validator, and bundle all close around that lifecycle?",
        "admissibility_question_id": "truth_lifecycle",
        "admissibility_normative_focus": "canonical_truth_discoverability_admissibility_binding_consumption",
        "target_component_id": "root_truth_lifecycle",
        "target_current_file": "identity/protocol/mappings/root-truth-lifecycle.current.yaml",
        "target_validator_script": "scripts/validate_protocol_root_truth_lifecycle.py",
        "target_status_key": "protocol_root_truth_lifecycle_status",
        "target_contract_file": "identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md",
        "target_required_markers": (
            "## Truth-lifecycle law",
            "## Five lifecycle stages",
        ),
    },
    "normative": {
        "order": 3,
        "philosophy_marker": "3. **Normative question**: Which actions are permitted, which boundaries must fail-close, and which success-path conditions are required?",
        "admissibility_question_id": "normative",
        "admissibility_normative_focus": "allowed_actions_fail_close_success_path_and_forbidden_shortcuts",
        "target_component_id": "root_stream_design_admissibility",
        "target_current_file": "identity/protocol/mappings/root-stream-design-admissibility.current.yaml",
        "target_validator_script": "scripts/validate_protocol_root_stream_design_admissibility.py",
        "target_status_key": "protocol_root_stream_design_admissibility_status",
        "target_contract_file": "identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md",
        "target_required_markers": (
            "### 3. Normative question",
            "### 3. Normative-closure proof",
        ),
    },
    "responsibility_split": {
        "order": 4,
        "philosophy_marker": "4. **Responsibility-split question**: Is this a shared-law problem or an instance-adaptation problem?",
        "admissibility_question_id": "responsibility_split",
        "admissibility_normative_focus": "protocol_instance_operator_boundary",
        "target_component_id": "root_protocol_instance_responsibility",
        "target_current_file": "identity/protocol/mappings/root-protocol-instance-responsibility.current.yaml",
        "target_validator_script": "scripts/validate_protocol_root_protocol_instance_responsibility.py",
        "target_status_key": "protocol_root_protocol_instance_responsibility_status",
        "target_contract_file": "identity/protocol/PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md",
        "target_required_markers": (
            "## Responsibility law",
            "The protocol defines the law of the world; the instance converges its runtime back to that law.",
        ),
    },
    "answer_surface": {
        "order": 5,
        "philosophy_marker": "5. **Answer-surface question**: What is the stable answer surface ultimately delivered to the operator?",
        "admissibility_question_id": "answer_surface",
        "admissibility_normative_focus": "stable_operator_delivery_surface",
        "target_component_id": "root_operator_answer_surface",
        "target_current_file": "identity/protocol/mappings/root-operator-answer-surface.current.yaml",
        "target_validator_script": "scripts/validate_protocol_root_operator_answer_surface.py",
        "target_status_key": "protocol_root_operator_answer_surface_status",
        "target_contract_file": "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md",
        "target_required_markers": (
            "## Operator answer-surface law",
            "## Compression boundary",
        ),
    },
}
EXPECTED_MAPPING_CHILDREN = (
    "root-design-question-closure.current.yaml",
    "root-design-question-closure.v1.yaml",
)
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Design-question closure row-family completeness must stay explicit",
        "Required question-closure rows and emitted question-status rows must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize design-question closure legality while required question identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root design-question closure completeness discipline",
        "Design-question closure law is not a soft cross-reference bundle.",
        "1. required question-closure rows and emitted question-status rows must remain explicit as separate machine-readable row families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root design-question closure completeness boundary",
        "1. Design-question closure law must remain machine-readable as separate required-question-closure and emitted-question-status row families.",
        "4. Protocol legality must not finalize design-question closure legality while missing or unexpected question identities remain known only inside validator logic.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime design-question closure consumption boundary",
        "1. Runtime consumes design-question closure law as separate required-question-closure and emitted-question-status row families rather than as undifferentiated design prose.",
        "4. Runtime must not finalize design-question closure legality while missing or unexpected question identities remain known only inside validator machinery.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _contiguous_orders(values: list[int]) -> bool:
    return values == list(range(1, len(values) + 1))


def _status_rows(question_status_rows: list[dict[str, Any]]) -> tuple[SimpleNamespace, ...]:
    return tuple(
        SimpleNamespace(question_id=str(row.get("question_id") or "").strip())
        for row in question_status_rows
        if str(row.get("question_id") or "").strip()
    )


def _run_component_validator(repo_root, validator_script: str, status_key: str) -> tuple[int, dict[str, Any], str]:
    cmd = ["python3", validator_script, "--repo-root", str(repo_root), "--json-only"]
    proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    stdout = (proc.stdout or "").strip()
    if not stdout:
        return proc.returncode, {}, "validator_output_missing"
    try:
        payload = json.loads(stdout)
    except Exception:
        return proc.returncode, {}, "validator_output_invalid_json"
    if status_key not in payload:
        return proc.returncode, payload, "validator_status_key_missing"
    return proc.returncode, payload, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-root design-question closure against downstream root-law surfaces.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    closure_doc, closure_entry_path, closure_active_path, closure_alias_error = load_root_design_question_closure(repo_root)
    admissibility_doc, admissibility_entry_path, admissibility_active_path, admissibility_alias_error = load_root_stream_design_admissibility(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    closure_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    question_status_rows: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    for prefix, doc, alias_error, empty_reason in (
        ("root_design_question_closure", closure_doc, closure_alias_error, "root_design_question_closure_empty_or_invalid"),
        ("root_stream_design_admissibility", admissibility_doc, admissibility_alias_error, "root_stream_design_admissibility_empty_or_invalid"),
        ("root_corpus_registry", registry_doc, registry_alias_error, "root_corpus_registry_empty_or_invalid"),
    ):
        if alias_error:
            stale_reasons.append(f"{prefix}_alias_error:{alias_error}")
            error_code = ERR_REGISTRY
        elif not doc:
            stale_reasons.append(empty_reason)
            error_code = ERR_REGISTRY

    closure_rows = question_closure_rows_from_doc(closure_doc) if closure_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(closure_doc) if closure_doc else ()
    admissibility_question_rows = required_question_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "closure_family": "protocol_root_design_question_closure",
            "closure_version": "v1",
            "root_dir": "identity/protocol",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "admissibility_current_file": "identity/protocol/mappings/root-stream-design-admissibility.current.yaml",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "validator_script": "scripts/validate_protocol_root_design_question_closure.py",
            "probe_script": "scripts/ci/run_protocol_root_design_question_closure_probes_ci.sh",
            "common_script": "scripts/root_design_question_closure_common.py",
        }
        for field, expected in expected_scalar_fields.items():
            if str(closure_doc.get(field) or "").strip() != expected:
                stale_reasons.append(f"root_design_question_closure_field_invalid:{field}")
                error_code = ERR_REGISTRY
        for field in ("philosophy_anchor_file", "admissibility_current_file", "registry_current_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(closure_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_design_question_closure_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not closure_rows:
            stale_reasons.append("root_design_question_closure_rows_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_design_question_closure",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    if not stale_reasons:
        row_map = {row.question_id: row for row in closure_rows}
        orders = [row.order for row in closure_rows]
        if len(row_map) != len(closure_rows):
            structure_violations.append({"field": "required_question_closure_rows", "reason": "duplicate_question_id"})
        if len(set(orders)) != len(orders) or not _contiguous_orders(sorted(orders)):
            structure_violations.append({"field": "required_question_closure_rows", "reason": "question_order_non_contiguous"})

        missing = sorted(set(EXPECTED_QUESTION_CLOSURE_ROWS) - set(row_map))
        extra = sorted(set(row_map) - set(EXPECTED_QUESTION_CLOSURE_ROWS))
        if missing:
            structure_violations.append({"field": "required_question_closure_rows", "reason": "missing_expected_rows", "row_ids": missing})
        if extra:
            structure_violations.append({"field": "required_question_closure_rows", "reason": "unexpected_rows", "row_ids": extra})

        for question_id, expected in EXPECTED_QUESTION_CLOSURE_ROWS.items():
            row = row_map.get(question_id)
            if row is None:
                continue
            for field in (
                "order",
                "philosophy_marker",
                "admissibility_question_id",
                "admissibility_normative_focus",
                "target_component_id",
                "target_current_file",
                "target_validator_script",
                "target_status_key",
                "target_contract_file",
            ):
                if getattr(row, field) != expected[field]:
                    structure_violations.append(
                        {
                            "field": "required_question_closure_rows",
                            "reason": f"{field}_mismatch",
                            "row_id": question_id,
                            "expected": expected[field],
                            "actual": getattr(row, field),
                        }
                    )
            if tuple(row.target_required_markers) != expected["target_required_markers"]:
                structure_violations.append(
                    {
                        "field": "required_question_closure_rows",
                        "reason": "target_required_markers_mismatch",
                        "row_id": question_id,
                    }
                )
        if structure_violations:
            error_code = ERR_STRUCTURE

    if not stale_reasons:
        admissibility_map = {row.question_id: row for row in admissibility_question_rows}
        registry_map = {row.rel_path: row for row in registry_entries}
        mappings_entry = registry_map.get("identity/protocol/mappings")
        if mappings_entry is None:
            closure_violations.append({"field": "root_corpus_registry", "reason": "mappings_directory_not_registered"})
        else:
            for child in EXPECTED_MAPPING_CHILDREN:
                if child not in mappings_entry.required_children:
                    closure_violations.append(
                        {"field": "root_corpus_registry", "reason": "mappings_required_child_missing", "child": child}
                    )

        philosophy_path = (repo_root / str(closure_doc.get("philosophy_anchor_file") or "")).resolve()
        philosophy_text = philosophy_path.read_text(encoding="utf-8") if philosophy_path.exists() else ""

        for row in sorted(closure_rows, key=lambda item: item.order):
            admissibility_row = admissibility_map.get(row.admissibility_question_id)
            if admissibility_row is None:
                closure_violations.append(
                    {"field": "root_stream_design_admissibility", "reason": "admissibility_question_missing", "question_id": row.question_id}
                )
            else:
                if admissibility_row.question_id != row.question_id:
                    closure_violations.append(
                        {
                            "field": "root_stream_design_admissibility",
                            "reason": "admissibility_question_id_mismatch",
                            "question_id": row.question_id,
                            "actual": admissibility_row.question_id,
                        }
                    )
                if admissibility_row.normative_focus != row.admissibility_normative_focus:
                    closure_violations.append(
                        {
                            "field": "root_stream_design_admissibility",
                            "reason": "admissibility_normative_focus_mismatch",
                            "question_id": row.question_id,
                            "expected": row.admissibility_normative_focus,
                            "actual": admissibility_row.normative_focus,
                        }
                    )

            if row.target_contract_file not in registry_map:
                closure_violations.append(
                    {"field": "root_corpus_registry", "reason": "target_contract_not_registered", "question_id": row.question_id, "rel_path": row.target_contract_file}
                )
            else:
                registry_entry = registry_map[row.target_contract_file]
                if registry_entry.entry_kind != "file":
                    closure_violations.append(
                        {
                            "field": "root_corpus_registry",
                            "reason": "target_contract_entry_kind_mismatch",
                            "question_id": row.question_id,
                            "rel_path": row.target_contract_file,
                            "actual": registry_entry.entry_kind,
                        }
                    )
                if not registry_entry.law_bearing:
                    closure_violations.append(
                        {
                            "field": "root_corpus_registry",
                            "reason": "target_contract_not_law_bearing",
                            "question_id": row.question_id,
                            "rel_path": row.target_contract_file,
                        }
                    )

            for marker in find_missing_markers(philosophy_text, (row.philosophy_marker,)):
                closure_violations.append(
                    {"field": "philosophy_anchor", "reason": "required_marker_missing", "question_id": row.question_id, "marker": marker}
                )

            target_contract_path = (repo_root / row.target_contract_file).resolve()
            if not target_contract_path.exists():
                closure_violations.append(
                    {"field": "target_contract", "reason": "target_contract_missing", "question_id": row.question_id, "rel_path": row.target_contract_file}
                )
            else:
                target_text = target_contract_path.read_text(encoding="utf-8")
                for marker in find_missing_markers(target_text, tuple(row.target_required_markers)):
                    closure_violations.append(
                        {"field": "target_contract", "reason": "target_marker_missing", "question_id": row.question_id, "marker": marker}
                    )

            validator_path = (repo_root / row.target_validator_script).resolve()
            if not validator_path.exists():
                closure_violations.append(
                    {"field": "target_validator", "reason": "validator_missing", "question_id": row.question_id, "rel_path": row.target_validator_script}
                )
                continue
            current_file_path = (repo_root / row.target_current_file).resolve()
            if not current_file_path.exists():
                closure_violations.append(
                    {"field": "target_current_file", "reason": "current_file_missing", "question_id": row.question_id, "rel_path": row.target_current_file}
                )
                continue

            rc, payload, run_error = _run_component_validator(repo_root, row.target_validator_script, row.target_status_key)
            component_status = str(payload.get(row.target_status_key) or "")
            question_status_rows.append(
                {
                    "order": row.order,
                    "question_id": row.question_id,
                    "target_component_id": row.target_component_id,
                    "target_status_key": row.target_status_key,
                    "validator_script": row.target_validator_script,
                    "validator_rc": rc,
                    "component_status": component_status,
                    "validator_error": run_error,
                }
            )
            if run_error:
                closure_violations.append(
                    {"field": "target_validator", "reason": run_error, "question_id": row.question_id, "validator_rc": rc}
                )
            elif rc != 0 or component_status != STATUS_PASS_REQUIRED:
                closure_violations.append(
                    {
                        "field": "target_validator",
                        "reason": "component_not_pass_required",
                        "question_id": row.question_id,
                        "validator_rc": rc,
                        "component_status": component_status,
                    }
                )

        root_doc_anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                root_doc_anchor_checks,
                field_name="root_doc_anchor_checks",
            )
        )

        if (closure_violations or root_doc_anchor_violations) and not error_code:
            error_code = ERR_CLOSURE

    status = STATUS_PASS_REQUIRED
    if stale_reasons or structure_violations or closure_violations or root_doc_anchor_violations:
        status = STATUS_FAIL_REQUIRED

    row_family_projection_rows = [
        project_row_family(
            family_id="required_question_closure_rows",
            member_id_key="question_id",
            actual_rows=closure_rows,
            expected_rows=EXPECTED_QUESTION_CLOSURE_ROWS,
            id_attr="question_id",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        project_row_family(
            family_id="question_status_rows",
            member_id_key="question_id",
            actual_rows=_status_rows(question_status_rows),
            expected_rows=EXPECTED_QUESTION_CLOSURE_ROWS,
            id_attr="question_id",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
    ]

    payload = {
        STATUS_KEY: status,
        "closure_family": str(closure_doc.get("closure_family") or ""),
        "closure_version": str(closure_doc.get("closure_version") or ""),
        "mapping_entry_file": str(closure_entry_path.relative_to(repo_root)),
        "mapping_active_file": str(closure_active_path.relative_to(repo_root)),
        "question_closure_count": len(closure_rows),
        **project_root_contract_support_projection(
            prefix="design_question_closure",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "question_ids": [row.question_id for row in sorted(closure_rows, key=lambda item: item.order)],
        "question_status_rows": question_status_rows,
        "structure_violations": structure_violations,
        "closure_violations": closure_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
        "error_code": error_code,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
