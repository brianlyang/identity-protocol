#!/usr/bin/env python3
"""Create an identity pack and optionally register it in identity catalog."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import yaml


MANDATORY_PROTOCOL_SOURCES = [
    {
        "type": "github_repo_file",
        "repo": "brianlyang/identity-protocol",
        "path": "identity/protocol/IDENTITY_PROTOCOL.md",
    },
    {
        "type": "github_repo_file",
        "repo": "brianlyang/identity-protocol",
        "path": "docs/research/IDENTITY_PROTOCOL_BENCHMARK_SKILLS_2026-02-19.md",
    },
    {
        "type": "official_doc",
        "url": "https://developers.openai.com/codex/skills/",
    },
    {
        "type": "official_doc",
        "url": "https://agentskills.io/specification",
    },
    {
        "type": "official_doc",
        "url": "https://modelcontextprotocol.io/specification/latest",
    },
]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(path: Path, data) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _default_current_task(identity_id: str, title: str, description: str) -> dict:
    return {
        "task_id": f"{identity_id}_bootstrap",
        "agent_identity": {
            "name": identity_id,
            "role": title,
            "methodology_version": "v1.2.3",
            "prompt_version": "v1.2.3",
            "json_version": "v1.2.3",
            "identity_prompt_path": f"identity/packs/{identity_id}/IDENTITY_PROMPT.md",
            "canon_path": "identity/protocol/IDENTITY_PROTOCOL.md",
        },
        "objective": {
            "title": description,
            "priority": "HIGH",
            "status": "pending",
        },
        "state_machine": {
            "current_state": "intake",
            "allowed_states": ["intake", "analyze", "execute", "verify", "done", "blocked"],
            "transition_rules": [
                "intake -> analyze",
                "analyze -> execute",
                "execute -> verify",
                "verify -> done",
                "verify -> analyze",
                "analyze -> blocked",
            ],
        },
        "gates": {
            "document_gate": "required",
            "media_gate": "required",
            "category_compliance_gate": "required",
            "reject_memory_gate": "required",
            "protocol_baseline_review_gate": "required",
            "payload_evidence_gate": "required",
            "multimodal_consistency_gate": "required",
            "reasoning_loop_gate": "required",
            "routing_gate": "required",
            "rulebook_gate": "required",
        },
        "protocol_review_contract": {
            "required_before": ["identity_capability_upgrade", "identity_architecture_decision"],
            "must_review_sources": MANDATORY_PROTOCOL_SOURCES,
            "required_evidence_fields": [
                "review_id",
                "reviewed_at",
                "reviewer_identity",
                "purpose",
                "sources_reviewed",
                "findings",
                "decision",
            ],
            "evidence_report_path_pattern": "identity/runtime/examples/protocol-baseline-review-*.json",
            "max_review_age_days": 7,
        },
        "evaluation_contract": {
            "required_evidence_triplet": ["api_evidence", "event_evidence", "ui_evidence"],
            "consistency_required": True,
            "consistency_fail_action": "block_done_and_trigger_recheck",
            "run_report_path_pattern": "resource/reports/*run*.json",
        },
        "reasoning_loop_contract": {
            "max_attempts_before_escalation": 3,
            "mandatory_fields_per_attempt": ["attempt", "hypothesis", "patch", "expected_effect", "result"],
            "failure_requires_next_action": True,
        },
        "routing_contract": {
            "auto_route_enabled": True,
            "fallback_switch_after_failures": 2,
            "problem_type_routes": {
                "unknown": ["identity-creator"],
            },
        },
        "rulebook_contract": {
            "append_only": True,
            "required_rule_types": ["negative", "positive"],
            "required_fields": [
                "rule_id",
                "type",
                "trigger",
                "action",
                "evidence_run_id",
                "scope",
                "confidence",
                "updated_at",
            ],
            "rulebook_path": f"identity/packs/{identity_id}/RULEBOOK.jsonl",
        },
        "source_of_truth": {
            "local_docs_roots": [],
            "local_project_evidence_roots": ["resource/reports", "resource/preflight", "resource/reject-archive"],
        },
        "escalation_policy": {
            "email_for_offline_only": True,
            "offline_blockers": [],
            "do_not_email_for": ["routine_status_update", "normal_progress_report", "non_blocking_warning"],
        },
        "required_artifacts": [
            "resource/reports/*.json",
            "resource/reports/*.md",
        ],
        "post_execution_mandatory": [
            f"append task outcome into identity/packs/{identity_id}/TASK_HISTORY.md",
            "update objective.status",
            "update state_machine.current_state",
        ],
        "version_control": {
            "sync_status": "initialized",
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        },
    }


def _default_protocol_review_sample(identity_id: str) -> dict:
    return {
        "review_id": f"protocol-baseline-review-{identity_id}-sample",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "reviewer_identity": identity_id,
        "purpose": "sample protocol baseline review evidence generated by identity-creator scaffold",
        "sources_reviewed": MANDATORY_PROTOCOL_SOURCES,
        "findings": [
            "Identity-upgrade conclusions must be source-backed.",
            "Protocol baseline review gate must pass before architecture decisions.",
        ],
        "decision": {
            "result": "approved",
            "notes": "sample artifact; replace with real review for production upgrades",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--pack-root", default="identity/packs")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--register", action="store_true", help="Register identity in catalog")
    ap.add_argument("--set-default", action="store_true", help="Set as default identity")
    args = ap.parse_args()

    identity_id = args.id.strip()
    if not identity_id:
        print("[FAIL] --id cannot be empty")
        return 1

    pack_dir = Path(args.pack_root) / identity_id
    if pack_dir.exists() and any(pack_dir.iterdir()):
        print(f"[FAIL] pack directory already exists and is non-empty: {pack_dir}")
        return 1

    write(
        pack_dir / "META.yaml",
        (
            f'id: "{identity_id}"\n'
            f'title: "{args.title}"\n'
            f'description: "{args.description}"\n'
            'status: "active"\n'
            'methodology_version: "v1.2.3"\n'
        ),
    )

    write(
        pack_dir / "IDENTITY_PROMPT.md",
        "# Identity Prompt\n\nDefine role cognition, principles, and decision rules.\n",
    )

    write_json(pack_dir / "CURRENT_TASK.json", _default_current_task(identity_id, args.title, args.description))

    write(pack_dir / "TASK_HISTORY.md", "# Task History\n\n## Entries\n")

    write(
        pack_dir / "RULEBOOK.jsonl",
        json.dumps(
            {
                "rule_id": f"{identity_id}-bootstrap-positive-rule",
                "type": "positive",
                "trigger": "identity_pack_initialized",
                "action": "enforce_protocol_baseline_review_before_identity_upgrades",
                "evidence_run_id": "bootstrap",
                "scope": "identity_runtime",
                "confidence": "high",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
        )
        + "\n",
    )

    write(
        pack_dir / "agents/identity.yaml",
        (
            "interface:\n"
            f'  display_name: "{args.title}"\n'
            f'  short_description: "{args.description}"\n'
            f'  default_prompt: "Operate as {identity_id} and satisfy runtime gates."\n\n'
            "policy:\n"
            "  allow_implicit_activation: true\n"
            "  activation_priority: 50\n"
            "  conflict_resolution: \"priority_then_objective\"\n\n"
            "dependencies:\n"
            "  tools: []\n\n"
            "observability:\n"
            "  event_topics: []\n"
            "  required_artifacts:\n"
            "    - \"resource/reports/*.json\"\n"
        ),
    )

    protocol_review_sample_path = Path("identity/runtime/examples") / f"protocol-baseline-review-{identity_id}-sample.json"
    write_json(protocol_review_sample_path, _default_protocol_review_sample(identity_id))

    print(f"[OK] created identity pack: {pack_dir}")
    print(f"[OK] created protocol review sample: {protocol_review_sample_path}")

    if args.register:
        catalog_path = Path(args.catalog)
        if not catalog_path.exists():
            print(f"[FAIL] catalog file not found: {catalog_path}")
            return 1
        catalog = load_yaml(catalog_path) or {}
        identities = catalog.get("identities", [])
        if any((x or {}).get("id") == identity_id for x in identities):
            print(f"[FAIL] id already exists in catalog: {identity_id}")
            return 1

        identities.append(
            {
                "id": identity_id,
                "title": args.title,
                "description": args.description,
                "status": "active",
                "methodology_version": "v1.2.3",
                "pack_path": str(pack_dir),
                "tags": ["identity"],
            }
        )
        catalog["identities"] = identities
        if args.set_default:
            catalog["default_identity"] = identity_id
        dump_yaml(catalog_path, catalog)
        print(f"[OK] registered identity in catalog: {catalog_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
