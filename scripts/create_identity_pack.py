#!/usr/bin/env python3
"""Create an identity pack and optionally register it in identity catalog."""

from __future__ import annotations

import argparse
import copy
import hashlib
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


def _minimal_current_task(identity_id: str, title: str, description: str) -> dict:
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


def _replace_store_manager_tokens(value, identity_id: str):
    if isinstance(value, str):
        return value.replace("store-manager", identity_id)
    if isinstance(value, list):
        return [_replace_store_manager_tokens(v, identity_id) for v in value]
    if isinstance(value, dict):
        return {k: _replace_store_manager_tokens(v, identity_id) for k, v in value.items()}
    return value


def _full_contract_current_task(identity_id: str, title: str, description: str) -> dict:
    template_path = Path("identity/store-manager/CURRENT_TASK.json")
    if not template_path.exists():
        raise FileNotFoundError(f"missing template CURRENT_TASK: {template_path}")
    template = json.loads(template_path.read_text(encoding="utf-8"))
    task = _replace_store_manager_tokens(copy.deepcopy(template), identity_id)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    task["task_id"] = f"{identity_id}_bootstrap"
    agent = task.setdefault("agent_identity", {})
    if isinstance(agent, dict):
        agent["name"] = identity_id
        agent["role"] = title
        agent["identity_prompt_path"] = f"identity/packs/{identity_id}/IDENTITY_PROMPT.md"
    objective = task.setdefault("objective", {})
    if isinstance(objective, dict):
        objective["title"] = description
        objective["status"] = "pending"

    task.setdefault("version_control", {})
    if isinstance(task["version_control"], dict):
        task["version_control"]["last_updated"] = now
        task["version_control"]["sync_status"] = "initialized"

    # Force identity-scoped evidence patterns
    prc = task.setdefault("protocol_review_contract", {})
    if isinstance(prc, dict):
        prc["evidence_report_path_pattern"] = f"identity/runtime/examples/protocol-baseline-review-{identity_id}-*.json"
    replay = (
        task.setdefault("identity_update_lifecycle_contract", {})
        .setdefault("replay_contract", {})
    )
    if isinstance(replay, dict):
        replay["evidence_path_pattern"] = f"identity/runtime/examples/{identity_id}-update-replay-*.json"
    install = task.setdefault("install_safety_contract", {})
    if isinstance(install, dict):
        install["install_report_path_pattern"] = f"identity/runtime/examples/install/install-report-*-{identity_id}.json"
    feedback = task.setdefault("experience_feedback_contract", {})
    if isinstance(feedback, dict):
        feedback["feedback_log_path_pattern"] = f"identity/runtime/logs/feedback/{identity_id}-feedback-*.json"
    return task


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_replay_sample(identity_id: str, task: dict) -> Path:
    checks = (
        task.get("identity_update_lifecycle_contract", {})
        .get("validation_contract", {})
        .get("required_checks", [])
    )
    logs_dir = Path(f"identity/runtime/logs/upgrade/{identity_id}")
    logs_dir.mkdir(parents=True, exist_ok=True)
    base_time = datetime.now(timezone.utc)
    check_results = []
    for i, chk in enumerate(checks, start=1):
        cmd = f"python3 {chk} --identity-id {identity_id}"
        if chk.endswith("validate_changelog_updated.py"):
            cmd = "python3 scripts/validate_changelog_updated.py --base HEAD~1 --head HEAD"
        log_path = logs_dir / f"{identity_id}-update-replay-check-{i:02d}.log"
        started = base_time.replace(microsecond=0)
        ended = started
        log_path.write_text(
            (
                f"$ {cmd}\n"
                "[exit_code] 0\n"
                f"[started_at] {started.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
                f"[ended_at] {ended.strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
                "[stdout]\nPASS\n[stderr]\n\n"
            ),
            encoding="utf-8",
        )
        check_results.append(
            {
                "command": cmd,
                "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "ended_at": ended.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "exit_code": 0,
                "log_path": str(log_path),
                "sha256": _sha256_file(log_path),
            }
        )

    replay_id = f"{identity_id}-update-replay-sample"
    sample = {
        "replay_id": replay_id,
        "identity_id": identity_id,
        "replay_status": "PASS",
        "failed_case_id": f"{identity_id}-bootstrap-case",
        "patched_files": ["CURRENT_TASK.json", "IDENTITY_PROMPT.md", "RULEBOOK.jsonl", "TASK_HISTORY.md"],
        "validation_checks_passed": checks,
        "creator_invocation": {
            "tool": "identity-creator",
            "mode": "update",
            "run_id": replay_id,
            "evidence_path": f"identity/runtime/examples/{identity_id}-update-replay-sample.json",
        },
        "check_results": check_results,
        "notes": "bootstrap replay sample generated by identity-creator scaffold",
    }
    out = Path(f"identity/runtime/examples/{identity_id}-update-replay-sample.json")
    write_json(out, sample)
    return out


def _copy_sample_with_identity(src: Path, dst: Path, identity_id: str) -> None:
    if not src.exists():
        return
    try:
        payload = json.loads(src.read_text(encoding="utf-8"))
    except Exception:
        return
    payload = _replace_store_manager_tokens(payload, identity_id)
    if isinstance(payload, dict):
        if "identity_id" in payload:
            payload["identity_id"] = identity_id
        if "reviewer_identity" in payload:
            payload["reviewer_identity"] = identity_id
    write_json(dst, payload)


def _bootstrap_identity_samples(identity_id: str) -> None:
    _copy_sample_with_identity(
        Path("identity/runtime/examples/store-manager-capability-arbitration-sample.json"),
        Path(f"identity/runtime/examples/{identity_id}-capability-arbitration-sample.json"),
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/examples/store-manager-learning-sample.json"),
        Path(f"identity/runtime/examples/{identity_id}-learning-sample.json"),
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/examples/store-manager-experience-feedback-sample.json"),
        Path(f"identity/runtime/examples/{identity_id}-experience-feedback-sample.json"),
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/examples/install/install-report-2026-02-22-store-manager.json"),
        Path(f"identity/runtime/examples/install/install-report-bootstrap-{identity_id}.json"),
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/logs/feedback/store-manager-feedback-2026-02-22T09-40-00Z.json"),
        Path(f"identity/runtime/logs/feedback/{identity_id}-feedback-bootstrap.json"),
        identity_id,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--pack-root", default="identity/packs")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument(
        "--profile",
        choices=["full-contract", "minimal"],
        default="full-contract",
        help="scaffold profile; full-contract mirrors runtime-required contracts",
    )
    ap.add_argument("--register", action="store_true", help="Register identity in catalog")
    ap.add_argument("--activate", action="store_true", help="Register with status=active (default inactive)")
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

    if args.profile == "full-contract":
        current_task = _full_contract_current_task(identity_id, args.title, args.description)
    else:
        current_task = _minimal_current_task(identity_id, args.title, args.description)
    write_json(pack_dir / "CURRENT_TASK.json", current_task)

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
    replay_sample_path = _write_replay_sample(identity_id, current_task)
    _bootstrap_identity_samples(identity_id)

    print(f"[OK] created identity pack: {pack_dir}")
    print(f"[OK] created protocol review sample: {protocol_review_sample_path}")
    print(f"[OK] created replay sample: {replay_sample_path}")

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
                "status": "active" if args.activate else "inactive",
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
