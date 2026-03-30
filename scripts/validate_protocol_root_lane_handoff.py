#!/usr/bin/env python3
"""Validate reconciled root_lane_handoff compatibility artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from root_lane_handoff_common import (
    EXPECTED_ARTIFACT_CLASSIFICATION,
    EXPECTED_CANONICAL_GOVERNANCE_DOC,
    EXPECTED_CANONICAL_REVIEW_DOC,
    EXPECTED_CLASSIFICATION_OPTIONS,
    EXPECTED_CURRENT_PAYLOAD,
    FORBIDDEN_CONTRACT_PHRASES,
    REQUIRED_CONTRACT_PAYLOAD,
    REQUIRED_CONTRACT_PHRASES,
    REQUIRED_MAPPING_PAYLOAD,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    default_paths,
    extract_contract_payload,
    load_json_like_yaml,
    repo_root,
    validate_contract_phrases,
    validate_dict,
)


def build_report(contract_doc: Path, current_mapping: Path, versioned_mapping: Path) -> dict[str, object]:
    errors: list[str] = []
    documents: dict[str, object] = {}

    for label, path in (
        ("contract_doc", contract_doc),
        ("current_mapping", current_mapping),
        ("versioned_mapping", versioned_mapping),
    ):
        documents[label] = {"path": str(path), "exists": path.exists()}
        if not path.exists():
            errors.append(f"{label} is missing: {path}")

    if not errors:
        markdown = contract_doc.read_text(encoding="utf-8")
        documents["contract_doc"]["semantic_status"] = STATUS_PASS_REQUIRED
        phrase_errors = validate_contract_phrases(markdown)
        if phrase_errors:
            documents["contract_doc"]["semantic_status"] = STATUS_FAIL_REQUIRED
            errors.extend([f"contract_doc: {error}" for error in phrase_errors])

        try:
            contract_payload = extract_contract_payload(markdown)
        except ValueError as exc:
            documents["contract_doc"]["payload_status"] = STATUS_FAIL_REQUIRED
            errors.append(f"contract_doc: {exc}")
        else:
            documents["contract_doc"]["payload_status"] = STATUS_PASS_REQUIRED
            payload_errors = validate_dict(REQUIRED_CONTRACT_PAYLOAD, contract_payload, "contract_doc")
            if payload_errors:
                documents["contract_doc"]["payload_status"] = STATUS_FAIL_REQUIRED
                errors.extend(payload_errors)

        current_payload = load_json_like_yaml(current_mapping)
        versioned_payload = load_json_like_yaml(versioned_mapping)
        documents["current_mapping"]["payload_status"] = STATUS_PASS_REQUIRED
        documents["versioned_mapping"]["payload_status"] = STATUS_PASS_REQUIRED

        current_errors = validate_dict(EXPECTED_CURRENT_PAYLOAD, current_payload, "current_mapping")
        if current_errors:
            documents["current_mapping"]["payload_status"] = STATUS_FAIL_REQUIRED
            errors.extend(current_errors)

        mapping_errors = validate_dict(REQUIRED_MAPPING_PAYLOAD, versioned_payload, "versioned_mapping")
        if mapping_errors:
            documents["versioned_mapping"]["payload_status"] = STATUS_FAIL_REQUIRED
            errors.extend(mapping_errors)

        if tuple(versioned_payload.get("required_contract_phrases", [])) != REQUIRED_CONTRACT_PHRASES:
            documents["versioned_mapping"]["payload_status"] = STATUS_FAIL_REQUIRED
            errors.append("versioned_mapping: required_contract_phrases diverge from the canonical compatibility contract surface")

        if tuple(versioned_payload.get("forbidden_contract_phrases", [])) != FORBIDDEN_CONTRACT_PHRASES:
            documents["versioned_mapping"]["payload_status"] = STATUS_FAIL_REQUIRED
            errors.append("versioned_mapping: forbidden_contract_phrases diverge from the fail-close compatibility boundary")

        if tuple(versioned_payload.get("classification_options", [])) != EXPECTED_CLASSIFICATION_OPTIONS:
            documents["versioned_mapping"]["payload_status"] = STATUS_FAIL_REQUIRED
            errors.append("versioned_mapping: classification_options must remain the frozen canonical/derived/compatibility/residual set")

        if versioned_payload.get("artifact_classification") != EXPECTED_ARTIFACT_CLASSIFICATION:
            documents["versioned_mapping"]["payload_status"] = STATUS_FAIL_REQUIRED
            errors.append(
                "versioned_mapping: artifact_classification must remain compatibility to avoid competing canonical handoff semantics"
            )

        canonical_repo_root = repo_root()
        for path_label, rel_path in (
            ("canonical_governance_doc", EXPECTED_CANONICAL_GOVERNANCE_DOC),
            ("canonical_review_doc", EXPECTED_CANONICAL_REVIEW_DOC),
        ):
            exists = (canonical_repo_root / rel_path).exists()
            documents[path_label] = {"path": rel_path, "exists": exists}
            if not exists:
                errors.append(f"missing canonical reference path: {rel_path}")

    status = STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED
    return {
        "protocol_root_lane_handoff_status": status,
        "artifact_classification": EXPECTED_ARTIFACT_CLASSIFICATION,
        "governing_law": REQUIRED_MAPPING_PAYLOAD["governing_law"],
        "documents": documents,
        "errors": errors,
    }



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_contract_doc, default_current_mapping, default_versioned_mapping = default_paths()
    parser.add_argument("--contract-doc", default=str(default_contract_doc))
    parser.add_argument("--current-mapping", default=str(default_current_mapping))
    parser.add_argument("--versioned-mapping", default=str(default_versioned_mapping))
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    report = build_report(
        Path(args.contract_doc),
        Path(args.current_mapping),
        Path(args.versioned_mapping),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["protocol_root_lane_handoff_status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
