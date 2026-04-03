#!/usr/bin/env python3
"""Validate ISSUE-040C lane_reopen_gate_contract_v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lane_reopen_gate_contract_common import (
    EXPECTED_CONTRACT,
    REQUIRED_FIELDS,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    default_doc_paths,
    extract_contract_payload,
    validate_expected_contract,
    validate_semantic_phrases,
)


def build_report(governance_doc: Path, review_doc: Path) -> dict[str, object]:
    errors: list[str] = []
    documents: dict[str, object] = {}
    payloads: dict[str, dict[str, object]] = {}

    for label, path in (("governance_doc", governance_doc), ("review_doc", review_doc)):
        document_record: dict[str, object] = {"path": str(path), "exists": path.exists()}
        documents[label] = document_record
        if not path.exists():
            errors.append(f"{label} is missing: {path}")
            continue
        markdown = path.read_text(encoding="utf-8")
        document_record["semantic_phrases_status"] = STATUS_PASS_REQUIRED
        semantic_errors = validate_semantic_phrases(markdown)
        if semantic_errors:
            document_record["semantic_phrases_status"] = STATUS_FAIL_REQUIRED
            errors.extend([f"{label}: {error}" for error in semantic_errors])
        try:
            payload = extract_contract_payload(markdown)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue
        payloads[label] = payload
        contract_errors = validate_expected_contract(payload)
        document_record["required_fields"] = [field for field in REQUIRED_FIELDS if field in payload]
        document_record["contract_status"] = (
            STATUS_PASS_REQUIRED if not contract_errors else STATUS_FAIL_REQUIRED
        )
        if contract_errors:
            errors.extend([f"{label}: {error}" for error in contract_errors])

    if len(payloads) == 2 and payloads["governance_doc"] != payloads["review_doc"]:
        errors.append("governance_doc and review_doc contract payloads are not identical")

    status = STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED
    return {
        "lane_reopen_gate_contract_status": status,
        "lane_id": EXPECTED_CONTRACT["lane_id"],
        "governing_law": EXPECTED_CONTRACT["governing_law"],
        "required_fields": list(REQUIRED_FIELDS),
        "documents": documents,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_governance_doc, default_review_doc = default_doc_paths()
    parser.add_argument("--governance-doc", default=str(default_governance_doc))
    parser.add_argument("--review-doc", default=str(default_review_doc))
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    report = build_report(Path(args.governance_doc), Path(args.review_doc))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["lane_reopen_gate_contract_status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    sys.exit(main())
