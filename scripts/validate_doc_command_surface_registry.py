#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from doc_command_surface_common import (
    DEFAULT_SELF_PREFIXES,
    MODE_COMPATIBILITY_BRIDGE_TRACE,
    MODE_HISTORICAL_REPLAY_TRACE,
    MODE_LIVE_CONTRACT,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    doc_command_surface_rows_from_doc,
    load_doc_command_surface,
    repo_self_prefixes_from_doc,
    resolve_doc_command_surface_mode,
    surface_mode_profiles_from_doc,
)
from repo_root_resolution_common import resolve_repo_root

STATUS_KEY = "doc_command_surface_registry_status"
ERR_REGISTRY = "IP-DCSR-001"
ERR_STRUCTURE = "IP-DCSR-002"

EXPECTED_MODES = (
    MODE_LIVE_CONTRACT,
    MODE_HISTORICAL_REPLAY_TRACE,
    MODE_COMPATIBILITY_BRIDGE_TRACE,
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate protocol doc-command surface registry and mode discipline."
    )
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    surface_doc, entry_path, active_path, alias_error = load_doc_command_surface(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    mode_rows = surface_mode_profiles_from_doc(surface_doc) if surface_doc else ()
    doc_rows = doc_command_surface_rows_from_doc(surface_doc) if surface_doc else ()
    self_prefixes = repo_self_prefixes_from_doc(surface_doc) if surface_doc else DEFAULT_SELF_PREFIXES
    mode_map = {row.mode: row for row in mode_rows}
    error_code = ""

    if alias_error:
        stale_reasons.append(f"doc_command_surface_alias_error:{alias_error}")
        error_code = ERR_REGISTRY
    elif not surface_doc:
        stale_reasons.append("doc_command_surface_registry_empty_or_invalid")
        error_code = ERR_REGISTRY

    if not stale_reasons:
        if str(surface_doc.get("command_surface_family") or "").strip() != "protocol_doc_command_surface":
            stale_reasons.append("doc_command_surface_family_invalid")
            error_code = ERR_REGISTRY
        if str(surface_doc.get("command_surface_version") or "").strip() != "v1":
            stale_reasons.append("doc_command_surface_version_invalid")
            error_code = ERR_REGISTRY
        if str(surface_doc.get("stream_doc_registry_current_file") or "").strip() != "identity/protocol/mappings/stream-doc-registry.current.yaml":
            stale_reasons.append("doc_command_surface_stream_doc_registry_pointer_invalid")
            error_code = ERR_REGISTRY
        if str(surface_doc.get("validator_script") or "").strip() != "scripts/validate_doc_command_surface_registry.py":
            stale_reasons.append("doc_command_surface_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(surface_doc.get("probe_script") or "").strip() != "scripts/ci/run_doc_command_surface_probes_ci.sh":
            stale_reasons.append("doc_command_surface_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(surface_doc.get("common_script") or "").strip() != "scripts/doc_command_surface_common.py":
            stale_reasons.append("doc_command_surface_common_script_invalid")
            error_code = ERR_REGISTRY
        if str(surface_doc.get("status_key") or "").strip() != STATUS_KEY:
            stale_reasons.append("doc_command_surface_status_key_invalid")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script", "stream_doc_registry_current_file"):
            rel_path = str(surface_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"doc_command_surface_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not mode_rows:
            stale_reasons.append("doc_command_surface_modes_missing")
            error_code = ERR_REGISTRY
        if not doc_rows:
            stale_reasons.append("doc_command_surface_rows_missing")
            error_code = ERR_REGISTRY
        if "identity-protocol-local" not in self_prefixes:
            stale_reasons.append("doc_command_surface_self_prefix_missing_identity_protocol_local")
            error_code = ERR_STRUCTURE

    if not stale_reasons:
        if sorted(mode_map) != sorted(EXPECTED_MODES):
            structure_violations.append(
                {"field": "surface_modes", "reason": "mode_set_mismatch", "expected_modes": list(EXPECTED_MODES)}
            )
        live_mode = mode_map.get(MODE_LIVE_CONTRACT)
        if live_mode and not (
            live_mode.enforce_script_existence
            and live_mode.enforce_current_flag_contract
            and live_mode.enforce_workspace_semantic_probe
        ):
            structure_violations.append(
                {"field": "surface_modes", "reason": "live_contract_policy_mismatch"}
            )
        historical_mode = mode_map.get(MODE_HISTORICAL_REPLAY_TRACE)
        if historical_mode and historical_mode.enforce_current_flag_contract:
            structure_violations.append(
                {"field": "surface_modes", "reason": "historical_replay_trace_must_not_enforce_flag_contract"}
            )
        compatibility_mode = mode_map.get(MODE_COMPATIBILITY_BRIDGE_TRACE)
        if compatibility_mode and compatibility_mode.enforce_script_existence:
            structure_violations.append(
                {"field": "surface_modes", "reason": "compatibility_bridge_trace_must_not_require_script_existence"}
            )

        doc_seen: set[str] = set()
        for row in doc_rows:
            if row.doc in doc_seen:
                structure_violations.append(
                    {"field": "doc_command_surface_rows", "reason": "duplicate_doc", "doc": row.doc}
                )
            doc_seen.add(row.doc)
            if row.default_mode not in mode_map:
                structure_violations.append(
                    {"field": "doc_command_surface_rows", "reason": "unknown_default_mode", "doc": row.doc}
                )
            if not (repo_root / row.doc).exists():
                structure_violations.append(
                    {"field": "doc_command_surface_rows", "reason": "doc_missing", "doc": row.doc}
                )
            rule_keys: set[tuple[str, str]] = set()
            for rule in row.script_rules:
                if rule.mode not in mode_map:
                    structure_violations.append(
                        {
                            "field": "doc_command_surface_rows",
                            "reason": "unknown_rule_mode",
                            "doc": row.doc,
                            "mode": rule.mode,
                        }
                    )
                if bool(rule.script_rel) == bool(rule.script_prefix):
                    structure_violations.append(
                        {
                            "field": "doc_command_surface_rows",
                            "reason": "rule_selector_must_choose_exactly_one_of_script_rel_or_script_prefix",
                            "doc": row.doc,
                        }
                    )
                selector_type = "script_rel" if rule.script_rel else "script_prefix"
                selector_value = rule.script_rel or rule.script_prefix
                if selector_value and not selector_value.startswith(("scripts/", "identity-protocol-local/scripts/")):
                    structure_violations.append(
                        {
                            "field": "doc_command_surface_rows",
                            "reason": "rule_selector_must_target_scripts_namespace",
                            "doc": row.doc,
                            "selector": selector_value,
                        }
                    )
                dedupe_key = (selector_type, selector_value)
                if dedupe_key in rule_keys:
                    structure_violations.append(
                        {
                            "field": "doc_command_surface_rows",
                            "reason": "duplicate_rule_selector",
                            "doc": row.doc,
                            "selector": selector_value,
                        }
                    )
                rule_keys.add(dedupe_key)

        doc_row_map = {row.doc: row for row in doc_rows}
        v15_governance = doc_row_map.get("docs/governance/identity-actor-session-binding-governance-v1.5.0.md")
        if v15_governance and v15_governance.default_mode != MODE_HISTORICAL_REPLAY_TRACE:
            structure_violations.append(
                {
                    "field": "doc_command_surface_rows",
                    "reason": "historical_governance_doc_must_default_to_historical_replay_trace",
                    "doc": v15_governance.doc,
                }
            )
        v15_review = doc_row_map.get("docs/review/protocol-remediation-audit-ledger-v1.5.md")
        if v15_review and v15_review.default_mode != MODE_HISTORICAL_REPLAY_TRACE:
            structure_violations.append(
                {
                    "field": "doc_command_surface_rows",
                    "reason": "historical_review_doc_must_default_to_historical_replay_trace",
                    "doc": v15_review.doc,
                }
            )

        compatibility_doc = "docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md"
        resolved_mode, _rationale = resolve_doc_command_surface_mode(
            surface_rows=doc_rows,
            doc_rel=compatibility_doc,
            script_rel="scripts/codex_native_chat/native_chat_bootstrap_bridge.py",
            repo_name=repo_root.name,
            self_prefixes=self_prefixes,
        )
        if resolved_mode != MODE_COMPATIBILITY_BRIDGE_TRACE:
            structure_violations.append(
                {
                    "field": "doc_command_surface_rows",
                    "reason": "native_chat_bridge_must_resolve_to_compatibility_bridge_trace",
                    "doc": compatibility_doc,
                }
            )

        historical_doc = "docs/governance/github-native-control-plane-specialization-v1.6.3.md"
        resolved_mode, _rationale = resolve_doc_command_surface_mode(
            surface_rows=doc_rows,
            doc_rel=historical_doc,
            script_rel="scripts/full_identity_protocol_scan.py",
            repo_name=repo_root.name,
            self_prefixes=self_prefixes,
        )
        if resolved_mode != MODE_HISTORICAL_REPLAY_TRACE:
            structure_violations.append(
                {
                    "field": "doc_command_surface_rows",
                    "reason": "v163_full_scan_must_resolve_to_historical_replay_trace",
                    "doc": historical_doc,
                }
            )

    if structure_violations and not error_code:
        error_code = ERR_STRUCTURE
    stale_reasons.extend(
        f"structure_violation:{item['field']}:{item['reason']}" for item in structure_violations
    )

    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED,
        "error_code": error_code,
        "repo_root": str(repo_root),
        "entry_path": str(entry_path),
        "active_path": str(active_path),
        "mode_count": len(mode_rows),
        "doc_row_count": len(doc_rows),
        "self_prefixes": list(self_prefixes),
        "surface_modes": [
            {
                "mode": row.mode,
                "enforce_script_existence": row.enforce_script_existence,
                "enforce_current_flag_contract": row.enforce_current_flag_contract,
                "enforce_workspace_semantic_probe": row.enforce_workspace_semantic_probe,
            }
            for row in mode_rows
        ],
        "doc_command_surface_rows": [
            {
                "doc": row.doc,
                "default_mode": row.default_mode,
                "script_rule_count": len(row.script_rules),
            }
            for row in doc_rows
        ],
        "structure_violations": structure_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
