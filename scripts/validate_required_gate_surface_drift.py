#!/usr/bin/env python3
from __future__ import annotations

import ast
import argparse
import json
import re
import shlex
from pathlib import Path
from typing import Any

import yaml
from protocol_infra_contract import (
    CANONICAL_FINAL_EMIT_SCRIPT,
    CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

STRICT_SURFACES: tuple[str, ...] = (
    "scripts/identity_creator.py",
    "scripts/release_readiness_check.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
    "scripts/e2e_smoke_test.sh",
    ".github/workflows/_identity-required-gates.yml",
)
GATEWAY_WRAPPER_BUS_REQUIRED_SURFACES: tuple[str, ...] = (
    "scripts/identity_creator.py",
    "scripts/release_readiness_check.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
)
INFRA_CONTRACT_REQUIRED_SURFACES: tuple[str, ...] = GATEWAY_WRAPPER_BUS_REQUIRED_SURFACES
INFRA_CONTRACT_REQUIRED_IMPORT = "protocol_infra_contract"
INFRA_CONTRACT_FORBIDDEN_LITERAL_TARGETS: tuple[str, ...] = (
    "FINAL_EMIT_SCRIPT",
    "REQUIRED_GATE_BUNDLE_SCRIPT",
    "BUNDLE_RUNNER_SCRIPT",
    "EXPECTED_ENTRY_SCRIPT",
    "EXPECTED_EGRESS_SCRIPT",
)
GATEWAY_WRAPPER_BUS_REQUIRED_IMPORT = "gateway_wrapper_enforcement"
GATEWAY_WRAPPER_BUS_REQUIRED_CALL = "run_gateway_wrapped_command"
GATEWAY_WRAPPER_BUS_FORBIDDEN_LEGACY_HELPERS: tuple[str, ...] = (
    "run_final_emit_via_instance_wrappers",
    "run_required_gate_bundle_via_ingress_wrapper",
)
WORKFLOW_REQUIRED_GATE_SURFACE = ".github/workflows/_identity-required-gates.yml"
SUPER_LINTER_WORKFLOW_SURFACE = ".github/workflows/super-linter.yml"
REQUIRED_GATE_CI_DELEGATE_SCRIPT = "scripts/ci/run_required_runtime_gates_ci.sh"
FULL_SCAN_TARGET_CI_DELEGATE_SCRIPT = "scripts/ci/run_full_scan_target_regression_ci.sh"
MONOTONIC_FLOOR_PROBE_CI_DELEGATE_SCRIPT = "scripts/ci/run_monotonic_floor_probes_ci.sh"
GATEWAY_TRUST_BOUNDARY_PROBE_CI_DELEGATE_SCRIPT = "scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh"
HOST_VISIBLE_SURFACE_PROBE_CI_DELEGATE_SCRIPT = "scripts/ci/run_host_visible_surface_live_probes_ci.sh"
UNIQUE_ENTRY_TUPLE_PROBE_CI_DELEGATE_SCRIPT = "scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh"
DOWNSINK_PATH_IMMUTABILITY_PROBE_CI_DELEGATE_SCRIPT = "scripts/ci/run_downsink_path_immutability_probes_ci.sh"
INSTALLER_VERSION_BASELINE_PROBE_CI_DELEGATE_SCRIPT = "scripts/ci/run_installer_version_baseline_probes_ci.sh"
SKILL_SUPPLY_CHAIN_PROBE_CI_DELEGATE_SCRIPT = "scripts/ci/run_skill_supply_chain_probes_ci.sh"
SEMANTIC_CLARITY_PROBE_CI_DELEGATE_SCRIPT = "scripts/ci/run_semantic_clarity_probes_ci.sh"
WORKFLOW_REQUIRED_EXECUTION_SCRIPTS: tuple[str, ...] = (
    REQUIRED_GATE_CI_DELEGATE_SCRIPT,
    MONOTONIC_FLOOR_PROBE_CI_DELEGATE_SCRIPT,
    GATEWAY_TRUST_BOUNDARY_PROBE_CI_DELEGATE_SCRIPT,
    HOST_VISIBLE_SURFACE_PROBE_CI_DELEGATE_SCRIPT,
    UNIQUE_ENTRY_TUPLE_PROBE_CI_DELEGATE_SCRIPT,
    DOWNSINK_PATH_IMMUTABILITY_PROBE_CI_DELEGATE_SCRIPT,
    INSTALLER_VERSION_BASELINE_PROBE_CI_DELEGATE_SCRIPT,
    SKILL_SUPPLY_CHAIN_PROBE_CI_DELEGATE_SCRIPT,
    SEMANTIC_CLARITY_PROBE_CI_DELEGATE_SCRIPT,
    FULL_SCAN_TARGET_CI_DELEGATE_SCRIPT,
)
CI_DELEGATED_LINEAGE_SURFACES: tuple[str, ...] = (
    REQUIRED_GATE_CI_DELEGATE_SCRIPT,
)
FULL_SCAN_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_full_scan_target_regression.py",
)
FULL_SCAN_DELEGATED_REQUIRED_TOKENS: tuple[str, ...] = (
    "--target-source-layer",
    "--expected-work-layer",
    "--expected-source-layer",
    "--actor-id",
    "--session-id",
    "--enforce-m2m-pass",
)
MONOTONIC_PROBE_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_reasoning_loop_failclose.py",
    CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
)
MONOTONIC_PROBE_REQUIRED_TARGET = "multimodal_plugin_enforcement"
GATEWAY_TRUST_BOUNDARY_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
    CANONICAL_FINAL_EMIT_SCRIPT,
    "scripts/compose_and_validate_governed_reply.py",
    "scripts/probe_gateway_timeout_guard.py",
)
HOST_VISIBLE_SURFACE_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/repair_contract_backfill.py",
    "scripts/validate_host_transport_wiring_attestation.py",
)
UNIQUE_ENTRY_TUPLE_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_protocol_unique_entry_gate.py",
    "scripts/repair_contract_backfill.py",
    "scripts/check_unique_entry_contract_migration_closure.py",
)
DOWNSINK_PATH_IMMUTABILITY_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/repair_contract_backfill.py",
    "scripts/validate_protocol_downsink_path_immutability.py",
    "scripts/validate_protocol_downsink_path_write_guard.py",
    "scripts/validate_protocol_downsink_path_literal_lock.py",
)
INSTALLER_VERSION_BASELINE_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/identity_installer.py",
    "scripts/check_version_baseline_migration_closure.py",
)
SKILL_SUPPLY_CHAIN_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_skill_installation_supply_chain.py",
    "scripts/validate_skill_frontmatter.py",
    "scripts/validate_skill_sync_drift_guard.py",
)
SEMANTIC_CLARITY_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_semantic_term_registry.py",
    "scripts/validate_cli_catalog_default_semantics.py",
    "scripts/validate_stream_scope_semantic_integrity.py",
)
RUNTIME_FILE_GOVERNANCE_GOV_DOC = "docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md"
RUNTIME_FILE_GOVERNANCE_REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md"
RUNTIME_FILE_GOVERNANCE_GOV_REQUIRED_TOKENS: tuple[str, ...] = (
    "One-to-one anti-forget correspondence matrix (mandatory)",
    "scripts/validate_required_contract_coverage.py",
    "scripts/validate_required_gate_surface_drift.py",
    "scripts/ci/run_skill_supply_chain_probes_ci.sh",
    "scripts/ci/run_downsink_path_immutability_probes_ci.sh",
)
RUNTIME_FILE_GOVERNANCE_REVIEW_REQUIRED_TOKENS: tuple[str, ...] = (
    "v1.6.10 one-to-one correspondence replay checklist",
    "required_gate_surface_drift_status",
    "required_contract_coverage_status",
    "scripts/validate_required_gate_surface_drift.py",
    "scripts/validate_required_contract_coverage.py",
)
HOST_VISIBLE_SEMANTIC_FREEZE_GOV_DOC = "docs/governance/identity-host-unique-channel-governance-v1.6.6.md"
HOST_VISIBLE_SEMANTIC_FREEZE_REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.6.md"
HOST_VISIBLE_SEMANTIC_FREEZE_GOV_REQUIRED_TOKENS: tuple[str, ...] = (
    "Semantic freeze (v1.6.6 authoritative wording):",
    "pre_send_gate_pass_rate >= 0.95",
    "post_gate_coverage_rate = 1.00",
    "chat_egress_uniqueness_rate = 1.00",
    "next_hop_headstamp_rate = 1.00",
    "runtime_live_receipt_sources = [runtime_dialogue]",
    "fixture_allowed_operations = [ci]",
    "entry_receipt_selector_precedence = same_tuple > same_catalog > bundle_status_pass > newest",
    "`5` serial self-test rounds",
    "`5` serial deep-scan rounds",
    "scripts/ci/run_host_visible_surface_live_probes_ci.sh",
    "scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh",
    "scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh",
)
HOST_VISIBLE_SEMANTIC_FREEZE_REVIEW_REQUIRED_TOKENS: tuple[str, ...] = (
    "26.37 Pre-95/Post-100 semantic freeze + serial-5 replay uplift",
    "26.38 v1.6.6 P0 closure supplement (live source + selector + continuity)",
    "post_gate_coverage_rate",
    "chat_egress_uniqueness_rate",
    "next_hop_headstamp_rate",
    "runtime_live_receipt_sources = [runtime_dialogue]",
    "entry_receipt_selector_precedence = same_tuple > same_catalog > bundle_status_pass > newest",
)
SUPER_LINTER_REQUIRED_TOKENS: tuple[str, ...] = (
    "name: super-linter",
    "merge_group:",
    "checks_requested",
    "super-linter/super-linter/slim@",
    "VALIDATE_ALL_CODEBASE: false",
    "VALIDATE_GITHUB_ACTIONS: true",
    "VALIDATE_JSON: true",
    "VALIDATE_MARKDOWN: true",
    "VALIDATE_YAML: true",
)
REQUIRED_GATES_SUPER_LINTER_TOKENS: tuple[str, ...] = (
    "Super-linter (governance required lane)",
    "super-linter/super-linter/slim@v8.2.1",
    "VALIDATE_ALL_CODEBASE: false",
    "VALIDATE_GITHUB_ACTIONS: true",
    "VALIDATE_JSON: true",
    "VALIDATE_MARKDOWN: true",
    "VALIDATE_YAML: true",
)
DIALOGUE_FEEDBACK_BUNDLE_SCRIPT = "scripts/run_identity_dialogue_feedback_bundle.py"
DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_SURFACES: tuple[str, ...] = (
    "scripts/identity_creator.py",
)
DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_VALIDATORS: tuple[str, ...] = (
    "scripts/validate_identity_experience_feedback_governance.py",
    "scripts/validate_identity_capability_arbitration.py",
    "scripts/validate_identity_dialogue_content.py",
    "scripts/validate_identity_dialogue_cross_validation.py",
    "scripts/validate_identity_dialogue_result_support.py",
    "scripts/validate_identity_ci_enforcement.py",
)
DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_ARGS: tuple[str, ...] = (
    "--catalog",
    "--identity-id",
)
FINAL_EGRESS_REQUIRED_SURFACES: tuple[str, ...] = (
    "scripts/identity_creator.py",
    "scripts/release_readiness_check.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
    "scripts/e2e_smoke_test.sh",
)

BUNDLE_RUNNER_SCRIPT = CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT
RECURRENCE_ESCALATOR_SCRIPT = "scripts/validate_required_gate_recurrence_escalator.py"
TUPLE_PARITY_SCRIPT = "scripts/validate_required_gate_tuple_parity.py"
FINAL_EGRESS_WRAPPER_SCRIPT = CANONICAL_FINAL_EMIT_SCRIPT
FORBIDDEN_DIRECT_EGRESS_SCRIPTS: tuple[str, ...] = (
    "scripts/compose_and_validate_governed_reply.py",
)
MANDATORY_LINEAGE_SCRIPTS: tuple[str, ...] = (
    BUNDLE_RUNNER_SCRIPT,
    RECURRENCE_ESCALATOR_SCRIPT,
    TUPLE_PARITY_SCRIPT,
)

BUNDLE_REQUIREMENT_KEYS: tuple[str, ...] = (
    "asb16-rq-017",
    "asb16-rq-030",
    "asb16-rq-021",
    "asb16-rq-022",
    "asb16-rq-018",
    "asb16-rq-019",
    "asb16-rq-020",
    "asb16-rq-033",
    "asb16-rq-034",
    "asb16-rq-035",
    "asb16-rq-039",
    "asb16-rq-040",
    "asb16-rq-041",
)

ACTOR_ID_REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/render_identity_response_stamp.py",
    FINAL_EGRESS_WRAPPER_SCRIPT,
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_send_time_reply_gate.py",
    "scripts/validate_execution_reply_identity_coherence.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
)
SESSION_ID_REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_required_contract_coverage.py",
    "scripts/render_identity_response_stamp.py",
    "scripts/validate_identity_response_stamp.py",
    FINAL_EGRESS_WRAPPER_SCRIPT,
    "scripts/validate_headstamp_recurrence_closure.py",
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_send_time_reply_gate.py",
    "scripts/validate_execution_reply_identity_coherence.py",
    "scripts/validate_actor_session_binding.py",
    "scripts/validate_actor_session_multibinding_concurrency.py",
    "scripts/validate_prompt_kernel_executable_coupling.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
)
BUNDLE_REQUIRED_ARGS: tuple[str, ...] = (
    "--run-id",
    "--send-time-gate-status",
    "--outlet-bypass-detected",
    "--final-emit-contract-status",
    "--final-emit-policy-mode",
    "--final-emit-schema-status",
    "--actor-id",
    "--resolved-work-layer",
    "--resolved-source-layer",
    "--lock-state",
)
BUNDLE_ARGS_FORBID_UNKNOWN: tuple[str, ...] = (
    "--send-time-gate-status",
    "--final-emit-contract-status",
    "--final-emit-schema-status",
)
BUNDLE_SKILL_PATH_ACTIVE_REPO_ROOT_REQUIRED_TOKENS: tuple[str, ...] = (
    "skill_path_active_repo_root",
    "if spec.target_name == \"skill_path_integrity\":",
    "--active-repo-root",
)
CANONICAL_GATE_PROFILE_FILE = "identity/protocol/mappings/layer-targeted-gate-profile.current.yaml"

VERSIONED_SCRIPT_ALIAS_RE = re.compile(r"^(?P<prefix>validate|normalize|emit)_v\d+_(?P<tail>.+)\.py$")
WRAPPER_MAIN_IMPORT_RE = re.compile(r"^\s*from\s+([A-Za-z0-9_.]+)\s+import\s+main\s*$", re.MULTILINE)
SCRIPT_LITERAL_RE = re.compile(r'["\'](scripts/[A-Za-z0-9_.-]+\.py)["\']')
SESSION_SET_RE = re.compile(r"session_id_required_scripts\s*=\s*\{(?P<body>.*?)\}", re.DOTALL)
INLINE_SCRIPT_SET_RE = re.compile(r"cmd\[1\]\s+in\s+\{(?P<body>.*?)\}", re.DOTALL)


def _resolve_default_contract_mapping(repo_root: Path) -> Path:
    mapping_dir = repo_root / "identity" / "protocol" / "mappings"
    current_file = mapping_dir / "contract-binding.current.yaml"
    if current_file.exists():
        return current_file
    candidates = sorted(mapping_dir.glob("contract-binding.v*.yaml"))
    if candidates:
        return candidates[-1]
    return mapping_dir / "contract-binding.yaml"


def _resolve_contract_mapping_alias(repo_root: Path, mapping_path: Path) -> tuple[Path, str]:
    if not mapping_path.name.endswith(".current.yaml"):
        return mapping_path, ""
    if not mapping_path.exists() or not mapping_path.is_file():
        return mapping_path, "current_file_missing"
    doc = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        return mapping_path, "current_file_parse_failed"
    active_file = str(doc.get("active_file", "")).strip()
    if not active_file:
        return mapping_path, "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, "active_file_not_found"
    return active_path, ""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def _gateway_wrapper_bus_ast_violations(surface_path: Path, text: str) -> list[str]:
    # AST-level check avoids comment/string token spoofing for required bus checks.
    if surface_path.suffix.lower() != ".py":
        violations: list[str] = []
        if GATEWAY_WRAPPER_BUS_REQUIRED_IMPORT not in text:
            violations.append("gateway_wrapper_enforcement_import_missing")
        if GATEWAY_WRAPPER_BUS_REQUIRED_CALL not in text:
            violations.append("run_gateway_wrapped_command_call_missing")
        for helper in GATEWAY_WRAPPER_BUS_FORBIDDEN_LEGACY_HELPERS:
            if helper in text:
                violations.append(f"legacy_gateway_helper_detected:{helper}")
        return sorted(set(violations))

    try:
        tree = ast.parse(text, filename=str(surface_path))
    except SyntaxError:
        return ["gateway_wrapper_enforcement_ast_parse_failed"]

    imported_bus_names: set[str] = set()
    imported_module_aliases: set[str] = set()
    imported_legacy_names: set[str] = set()
    legacy_called_helpers: set[str] = set()
    has_bus_call = False

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "gateway_wrapper_enforcement":
            for alias in node.names:
                raw_name = str(alias.name or "").strip()
                as_name = str(alias.asname or alias.name or "").strip()
                if not raw_name or not as_name:
                    continue
                if raw_name == GATEWAY_WRAPPER_BUS_REQUIRED_CALL:
                    imported_bus_names.add(as_name)
                if raw_name in GATEWAY_WRAPPER_BUS_FORBIDDEN_LEGACY_HELPERS:
                    imported_legacy_names.add(as_name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                raw_name = str(alias.name or "").strip()
                if raw_name == GATEWAY_WRAPPER_BUS_REQUIRED_IMPORT:
                    imported_module_aliases.add(str(alias.asname or raw_name).strip())

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            fn = str(func.id or "").strip()
            if fn in imported_bus_names:
                has_bus_call = True
            if fn in imported_legacy_names:
                legacy_called_helpers.add(fn)
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            module_ref = str(func.value.id or "").strip()
            attr = str(func.attr or "").strip()
            if module_ref in imported_module_aliases and attr == GATEWAY_WRAPPER_BUS_REQUIRED_CALL:
                has_bus_call = True
            if module_ref in imported_module_aliases and attr in GATEWAY_WRAPPER_BUS_FORBIDDEN_LEGACY_HELPERS:
                legacy_called_helpers.add(attr)

    violations: list[str] = []
    if not imported_bus_names and not imported_module_aliases:
        violations.append("gateway_wrapper_enforcement_import_missing")
    if not has_bus_call:
        violations.append("run_gateway_wrapped_command_call_missing")

    for helper in GATEWAY_WRAPPER_BUS_FORBIDDEN_LEGACY_HELPERS:
        if helper in legacy_called_helpers or helper in imported_legacy_names:
            violations.append(f"legacy_gateway_helper_detected:{helper}")
    return sorted(set(violations))


def _infra_contract_ast_violations(surface_path: Path, text: str) -> list[str]:
    # Enforce canonical infrastructure import to avoid script-local hardcoded routing literals.
    if surface_path.suffix.lower() != ".py":
        if INFRA_CONTRACT_REQUIRED_IMPORT not in text:
            return ["protocol_infra_contract_import_missing"]
        return []

    try:
        tree = ast.parse(text, filename=str(surface_path))
    except SyntaxError:
        return ["protocol_infra_contract_ast_parse_failed"]

    imported_infra = False
    literal_assignment_hits: list[str] = []
    canonical_literals = {
        CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
        CANONICAL_FINAL_EMIT_SCRIPT,
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == INFRA_CONTRACT_REQUIRED_IMPORT:
            imported_infra = True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if str(alias.name or "").strip() == INFRA_CONTRACT_REQUIRED_IMPORT:
                    imported_infra = True
        elif isinstance(node, ast.Assign):
            value = node.value
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            literal_value = str(value.value or "").strip()
            if literal_value not in canonical_literals:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = str(target.id or "").strip()
                    if target_name in INFRA_CONTRACT_FORBIDDEN_LITERAL_TARGETS:
                        literal_assignment_hits.append(
                            f"canonical_script_literal_assignment_detected:{target_name}"
                        )

    violations: list[str] = []
    if not imported_infra:
        violations.append("protocol_infra_contract_import_missing")
    if literal_assignment_hits:
        violations.extend(sorted(set(literal_assignment_hits)))
    return sorted(set(violations))


def _extract_shell_invocations(text: str, executable: str) -> set[str]:
    targets: set[str] = set()
    pattern = re.compile(rf"(?:^|\s){re.escape(executable)}\s+([^\s\"']+)")
    for raw_line in text.splitlines():
        # Strip inline comments so comment-only token spoofing cannot satisfy checks.
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        for match in pattern.finditer(line):
            target = match.group(1).strip()
            if target:
                targets.add(target)
    return targets


def _iter_shell_commands(text: str) -> list[str]:
    commands: list[str] = []
    buffer = ""
    for raw_line in text.splitlines():
        stripped = raw_line.split("#", 1)[0].rstrip()
        if not stripped:
            continue
        if stripped.endswith("\\"):
            buffer += stripped[:-1].rstrip() + " "
            continue
        buffer += stripped
        cmd = buffer.strip()
        if cmd:
            commands.append(cmd)
        buffer = ""
    if buffer.strip():
        commands.append(buffer.strip())
    return commands


def _extract_shell_invocation_args(text: str, *, executable: str, script: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for command in _iter_shell_commands(text):
        try:
            parts = shlex.split(command, posix=True)
        except Exception:
            continue
        if len(parts) < 2:
            continue
        if Path(parts[0]).name != executable:
            continue
        if parts[1] != script:
            continue
        rows.append(parts[2:])
    return rows


def _arg_token_present(args: list[str], token: str) -> bool:
    needle = str(token or "").strip()
    if not needle:
        return False
    for arg in args:
        if arg == needle or arg.startswith(f"{needle}="):
            return True
    return False


def _extract_workflow_run_invocations(path: Path, executable: str) -> set[str]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    if not isinstance(doc, dict):
        return set()
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict):
        return set()

    targets: set[str] = set()
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            run_block = step.get("run")
            if isinstance(run_block, str):
                targets.update(_extract_shell_invocations(run_block, executable))
    return targets


def _parse_validator_entry(raw_entry: str) -> str:
    token = str(raw_entry or "").strip()
    if not token:
        return ""
    if "::" in token:
        token = token.split("::", 1)[0].strip()
    return token


def _derive_alias_candidates(repo_root: Path, script_path: str) -> set[str]:
    aliases: set[str] = set()
    base_name = Path(script_path).name

    m = VERSIONED_SCRIPT_ALIAS_RE.match(base_name)
    if m:
        alias_name = f"{m.group('prefix')}_{m.group('tail')}.py"
        alias_script = f"scripts/{alias_name}"
        if alias_script != script_path:
            aliases.add(alias_script)

    script_file = repo_root / script_path
    if script_file.exists():
        text = _read_text(script_file)
        for module_name in WRAPPER_MAIN_IMPORT_RE.findall(text):
            leaf = str(module_name or "").strip().split(".")[-1].strip()
            if not leaf:
                continue
            alias_script = f"scripts/{leaf}.py"
            if alias_script != script_path:
                aliases.add(alias_script)

    return aliases


def _load_forbidden_direct_validators(*, repo_root: Path, mapping_path: Path) -> tuple[list[str], list[str]]:
    if not mapping_path.exists():
        return [], [f"contract_mapping_missing:{mapping_path}"]
    try:
        data = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return [], [f"contract_mapping_invalid:{mapping_path}:{exc}"]
    if not isinstance(data, dict):
        return [], [f"contract_mapping_invalid_root:{mapping_path}"]

    errors: list[str] = []
    discovered: set[str] = set()
    for requirement_key in BUNDLE_REQUIREMENT_KEYS:
        row = data.get(requirement_key)
        if not isinstance(row, dict):
            errors.append(f"mapping_row_missing:{requirement_key}")
            continue
        validator_ids = row.get("validator_ids") or []
        if not isinstance(validator_ids, list) or not validator_ids:
            errors.append(f"validator_ids_missing:{requirement_key}")
            continue
        for raw in validator_ids:
            script = _parse_validator_entry(str(raw))
            if not script:
                continue
            discovered.add(script)
            discovered.update(_derive_alias_candidates(repo_root, script))

    forbidden = sorted(
        script
        for script in discovered
        if script
        and script not in MANDATORY_LINEAGE_SCRIPTS
    )
    return forbidden, errors


def _python_command_blocks_for_script(text: str, script_path: str) -> list[str]:
    pattern = re.compile(
        r'\[\s*"python3"\s*,\s*"'
        + re.escape(script_path)
        + r'"(?P<body>.*?)\]',
        re.DOTALL,
    )
    return [m.group(0) for m in pattern.finditer(text)]


def _line_command_blocks_for_script(text: str, script_path: str) -> list[str]:
    rows: list[str] = []
    lines = text.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if script_path not in line or "python3" not in line:
            idx += 1
            continue
        start = idx + 1
        block_lines = [line.strip()]
        while line.rstrip().endswith("\\") and idx + 1 < len(lines):
            idx += 1
            line = lines[idx]
            block_lines.append(line.strip())
        rows.append(f"line:{start}:" + "\n".join(block_lines))
        idx += 1
    return rows


def _missing_actor_id_for_surface(*, surface_path: Path, text: str) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    suffix = surface_path.suffix.lower()
    for script_path in ACTOR_ID_REQUIRED_SCRIPTS:
        if suffix == ".py":
            blocks = _python_command_blocks_for_script(text, script_path)
        else:
            blocks = _line_command_blocks_for_script(text, script_path)
        if not blocks:
            continue
        bad_blocks = [b for b in blocks if "--actor-id" not in b]
        if bad_blocks:
            missing[script_path] = bad_blocks
    return missing


def _missing_session_id_for_surface(*, surface_path: Path, text: str) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    suffix = surface_path.suffix.lower()
    dynamic_session_scripts = _detect_dynamic_session_passthrough_scripts(text) if suffix == ".py" else set()
    for script_path in SESSION_ID_REQUIRED_SCRIPTS:
        if suffix == ".py":
            blocks = _python_command_blocks_for_script(text, script_path)
        else:
            blocks = _line_command_blocks_for_script(text, script_path)
        if not blocks:
            continue
        bad_blocks = [b for b in blocks if "--session-id" not in b and script_path not in dynamic_session_scripts]
        if bad_blocks:
            missing[script_path] = bad_blocks
    return missing


def _parse_script_literals(raw: str) -> set[str]:
    return {m.group(1).strip() for m in SCRIPT_LITERAL_RE.finditer(str(raw or "")) if m.group(1).strip()}


def _detect_dynamic_session_passthrough_scripts(text: str) -> set[str]:
    """
    Detect scripts that receive --session-id via dynamic injection loops
    (instead of being explicitly present in command list literals).
    This avoids false positives in surfaces that centralize session wiring.
    """
    dynamic: set[str] = set()
    body_text = str(text or "")
    if not body_text:
        return dynamic

    has_explicit_injection_loop = (
        "--session-id" in body_text
        and "cmd.extend([\"--session-id\"" in body_text
        and "cmd[1]" in body_text
    )
    if not has_explicit_injection_loop:
        return dynamic

    for m in SESSION_SET_RE.finditer(body_text):
        window_end = min(len(body_text), m.end() + 320)
        window = body_text[m.start() : window_end]
        if "cmd[1] in session_id_required_scripts" not in body_text:
            continue
        if "--session-id" not in window and "--session-id" not in body_text[m.end() : window_end]:
            continue
        dynamic.update(_parse_script_literals(m.group("body")))

    for m in INLINE_SCRIPT_SET_RE.finditer(body_text):
        window_start = max(0, m.start() - 240)
        window_end = min(len(body_text), m.end() + 320)
        window = body_text[window_start:window_end]
        if "session_id" not in window:
            continue
        if "--session-id" not in window:
            continue
        if "cmd.extend([\"--session-id\"" not in window and "cmd.extend(['--session-id'" not in window:
            continue
        dynamic.update(_parse_script_literals(m.group("body")))

    return dynamic


def _missing_bundle_args_for_surface(*, surface_path: Path, text: str) -> list[dict[str, Any]]:
    suffix = surface_path.suffix.lower()
    if suffix == ".py":
        blocks = _python_command_blocks_for_script(text, BUNDLE_RUNNER_SCRIPT)
    else:
        blocks = _line_command_blocks_for_script(text, BUNDLE_RUNNER_SCRIPT)
    if not blocks:
        return []

    rows: list[dict[str, Any]] = []
    for idx, block in enumerate(blocks, start=1):
        missing = [flag for flag in BUNDLE_REQUIRED_ARGS if flag not in block]
        if missing:
            rows.append(
                {
                    "command_index": idx,
                    "missing_args": missing,
                    "command_excerpt": block,
                }
            )
    return rows


def _block_contains_unknown_value(*, block: str, flag: str) -> bool:
    pattern_inline = re.compile(
        re.escape(flag) + r'\s+(?:"UNKNOWN"|UNKNOWN)(?:\s|$)',
        re.IGNORECASE,
    )
    pattern_python_list = re.compile(
        re.escape(flag) + r'"\s*,\s*"UNKNOWN"',
        re.IGNORECASE,
    )
    return bool(pattern_inline.search(block)) or bool(pattern_python_list.search(block))


def _block_contains_noncanonical_gate_profile_file(*, block: str) -> bool:
    candidates: list[str] = []
    inline_pattern = re.compile(
        r"--gate-profile-file\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s\\]+))",
        re.IGNORECASE,
    )
    list_pattern = re.compile(
        r"--gate-profile-file\"\s*,\s*\"([^\"]+)\"|--gate-profile-file'\s*,\s*'([^']+)'",
        re.IGNORECASE,
    )
    for match in inline_pattern.finditer(block):
        value = next((grp for grp in match.groups() if grp), "")
        value = str(value or "").strip()
        if value:
            candidates.append(value)
    for match in list_pattern.finditer(block):
        value = next((grp for grp in match.groups() if grp), "")
        value = str(value or "").strip()
        if value:
            candidates.append(value)
    for value in candidates:
        if value != CANONICAL_GATE_PROFILE_FILE:
            return True
    return False


def _invalid_bundle_arg_values_for_surface(*, surface_path: Path, text: str) -> list[dict[str, Any]]:
    suffix = surface_path.suffix.lower()
    if suffix == ".py":
        blocks = _python_command_blocks_for_script(text, BUNDLE_RUNNER_SCRIPT)
    else:
        blocks = _line_command_blocks_for_script(text, BUNDLE_RUNNER_SCRIPT)
    if not blocks:
        return []

    rows: list[dict[str, Any]] = []
    for idx, block in enumerate(blocks, start=1):
        bad_flags = [flag for flag in BUNDLE_ARGS_FORBID_UNKNOWN if _block_contains_unknown_value(block=block, flag=flag)]
        noncanonical_gate_profile = _block_contains_noncanonical_gate_profile_file(block=block)
        if bad_flags or noncanonical_gate_profile:
            row: dict[str, Any] = {
                "command_index": idx,
                "forbidden_unknown_args": bad_flags,
                "command_excerpt": block,
            }
            if noncanonical_gate_profile:
                row["forbidden_noncanonical_args"] = {
                    "--gate-profile-file": f"must_equal:{CANONICAL_GATE_PROFILE_FILE}"
                }
            rows.append(row)
    return rows


def _missing_bundle_skill_path_active_repo_root_tokens(text: str) -> list[str]:
    body = str(text or "")
    if not body:
        return list(BUNDLE_SKILL_PATH_ACTIVE_REPO_ROOT_REQUIRED_TOKENS)
    return [token for token in BUNDLE_SKILL_PATH_ACTIVE_REPO_ROOT_REQUIRED_TOKENS if token not in body]


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect strict-surface direct validator drift against bundle-runner lineage.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--contract-mapping", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    mapping_entry_path = (
        Path(args.contract_mapping).expanduser().resolve()
        if str(args.contract_mapping or "").strip()
        else _resolve_default_contract_mapping(repo_root)
    )
    mapping_path, mapping_alias_error = _resolve_contract_mapping_alias(repo_root, mapping_entry_path)
    forbidden_direct_validators, mapping_errors = _load_forbidden_direct_validators(
        repo_root=repo_root,
        mapping_path=mapping_path,
    )
    if mapping_alias_error:
        mapping_errors.append(f"contract_mapping_alias_resolution_failed:{mapping_alias_error}")

    missing_surface_files: list[str] = []
    missing_lineage_refs: dict[str, list[str]] = {}
    missing_execution_tokens: dict[str, list[str]] = {}
    forbidden_hits: dict[str, list[str]] = {}
    missing_final_egress_wrapper: list[str] = []
    forbidden_direct_egress_hits: dict[str, list[str]] = {}
    gateway_wrapper_bus_missing: list[str] = []
    gateway_wrapper_bus_violations: dict[str, list[str]] = {}
    infra_contract_missing: list[str] = []
    infra_contract_violations: dict[str, list[str]] = {}
    actor_id_passthrough_missing: dict[str, dict[str, list[str]]] = {}
    session_id_passthrough_missing: dict[str, dict[str, list[str]]] = {}
    bundle_arg_contract_missing: dict[str, list[dict[str, Any]]] = {}
    bundle_arg_value_invalid: dict[str, list[dict[str, Any]]] = {}
    bundle_runner_skill_path_active_repo_root_missing: list[str] = []
    dialogue_bundle_missing: dict[str, list[str]] = {}

    for rel in STRICT_SURFACES:
        path = repo_root / rel
        if not path.exists():
            missing_surface_files.append(rel)
            continue
        text = _read_text(path)
        if rel == WORKFLOW_REQUIRED_GATE_SURFACE:
            # Workflow surface uses delegated scripts; enforce command-level delegation,
            # and check lineage scripts on delegated shells instead of workflow comments/text.
            missing = []
        else:
            missing = [needle for needle in MANDATORY_LINEAGE_SCRIPTS if needle not in text]
        if rel in DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_SURFACES:
            if DIALOGUE_FEEDBACK_BUNDLE_SCRIPT not in text:
                existing = list(missing_execution_tokens.get(rel, []))
                missing_execution_tokens[rel] = sorted(set(existing + [DIALOGUE_FEEDBACK_BUNDLE_SCRIPT]))
        if missing:
            missing_lineage_refs[rel] = missing
        if rel == WORKFLOW_REQUIRED_GATE_SURFACE:
            invoked_scripts = _extract_workflow_run_invocations(path, executable="bash")
            invoked_scripts.update(_extract_workflow_run_invocations(path, executable="sh"))
            missing_exec = [script for script in WORKFLOW_REQUIRED_EXECUTION_SCRIPTS if script not in invoked_scripts]
            if missing_exec:
                missing_execution_tokens[rel] = missing_exec
        hits = [needle for needle in forbidden_direct_validators if needle in text]
        if hits:
            forbidden_hits[rel] = hits
        if rel in FINAL_EGRESS_REQUIRED_SURFACES and FINAL_EGRESS_WRAPPER_SCRIPT not in text:
            missing_final_egress_wrapper.append(rel)
        if rel in GATEWAY_WRAPPER_BUS_REQUIRED_SURFACES:
            bus_violations = _gateway_wrapper_bus_ast_violations(path, text)
            if bus_violations:
                gateway_wrapper_bus_missing.append(rel)
                gateway_wrapper_bus_violations[rel] = sorted(set(bus_violations))
        if rel in INFRA_CONTRACT_REQUIRED_SURFACES:
            infra_violations = _infra_contract_ast_violations(path, text)
            if infra_violations:
                infra_contract_missing.append(rel)
                infra_contract_violations[rel] = sorted(set(infra_violations))
        direct_egress_hits = [needle for needle in FORBIDDEN_DIRECT_EGRESS_SCRIPTS if needle in text]
        if direct_egress_hits:
            forbidden_direct_egress_hits[rel] = direct_egress_hits
        missing_actor = _missing_actor_id_for_surface(surface_path=path, text=text)
        if missing_actor:
            actor_id_passthrough_missing[rel] = missing_actor
        missing_session = _missing_session_id_for_surface(surface_path=path, text=text)
        if missing_session:
            session_id_passthrough_missing[rel] = missing_session
        missing_bundle_args = _missing_bundle_args_for_surface(surface_path=path, text=text)
        if missing_bundle_args:
            bundle_arg_contract_missing[rel] = missing_bundle_args
        invalid_bundle_values = _invalid_bundle_arg_values_for_surface(surface_path=path, text=text)
        if invalid_bundle_values:
            bundle_arg_value_invalid[rel] = invalid_bundle_values

    for rel in CI_DELEGATED_LINEAGE_SURFACES:
        path = repo_root / rel
        if not path.exists():
            missing_surface_files.append(rel)
            continue
        text = _read_text(path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing = [needle for needle in MANDATORY_LINEAGE_SCRIPTS if needle not in invoked_python_scripts]
        if missing:
            missing_lineage_refs[rel] = missing

    full_scan_delegate_path = repo_root / FULL_SCAN_TARGET_CI_DELEGATE_SCRIPT
    if not full_scan_delegate_path.exists():
        missing_surface_files.append(FULL_SCAN_TARGET_CI_DELEGATE_SCRIPT)
    else:
        rel = FULL_SCAN_TARGET_CI_DELEGATE_SCRIPT
        text = _read_text(full_scan_delegate_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing_python = [
            script
            for script in FULL_SCAN_DELEGATED_REQUIRED_PYTHON_SCRIPTS
            if script not in invoked_python_scripts
        ]
        if missing_python:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + missing_python))
        full_scan_invocation_args: list[list[str]] = []
        for script in FULL_SCAN_DELEGATED_REQUIRED_PYTHON_SCRIPTS:
            full_scan_invocation_args.extend(
                _extract_shell_invocation_args(text, executable="python3", script=script)
            )
        missing_tokens = [
            token
            for token in FULL_SCAN_DELEGATED_REQUIRED_TOKENS
            if not any(_arg_token_present(args, token) for args in full_scan_invocation_args)
        ]
    if missing_tokens:
        existing_tokens = list(missing_execution_tokens.get(rel, []))
        missing_execution_tokens[rel] = sorted(set(existing_tokens + missing_tokens))

    monotonic_probe_delegate_path = repo_root / MONOTONIC_FLOOR_PROBE_CI_DELEGATE_SCRIPT
    if not monotonic_probe_delegate_path.exists():
        missing_surface_files.append(MONOTONIC_FLOOR_PROBE_CI_DELEGATE_SCRIPT)
    else:
        rel = MONOTONIC_FLOOR_PROBE_CI_DELEGATE_SCRIPT
        text = _read_text(monotonic_probe_delegate_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing_python = [
            script
            for script in MONOTONIC_PROBE_DELEGATED_REQUIRED_PYTHON_SCRIPTS
            if script not in invoked_python_scripts
        ]
        if missing_python:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + missing_python))

        has_reasoning_probe = all(
            token in text
            for token in (
                "run_probe reasoning_floor_l0_fail",
                "scripts/validate_reasoning_loop_failclose.py",
                "--identity-id probe-floor",
                "--operation validate",
                "--json-only",
            )
        )
        if not has_reasoning_probe:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(
                set(existing_tokens + ["reasoning_floor_probe_invocation_missing"])
            )

        has_runner_update_probe = all(
            token in text
            for token in (
                "run_probe multimodal_update_defer_allowed",
                BUNDLE_RUNNER_SCRIPT,
                "--identity-id probe-mm",
                "--operation update",
                "--target-name " + MONOTONIC_PROBE_REQUIRED_TARGET,
                "--run-id identity-upgrade-exec-probe-mm-new",
                "--json-only",
            )
        )
        has_runner_readiness_probe = all(
            token in text
            for token in (
                "run_probe multimodal_readiness_skip_blocked",
                BUNDLE_RUNNER_SCRIPT,
                "--identity-id probe-mm",
                "--operation readiness",
                "--target-name " + MONOTONIC_PROBE_REQUIRED_TARGET,
                "--run-id identity-upgrade-exec-probe-mm-new",
                "--json-only",
            )
        )
        monotonic_missing_tokens: list[str] = []
        if not has_runner_update_probe:
            monotonic_missing_tokens.append("multimodal_update_probe_invocation_missing")
        if not has_runner_readiness_probe:
            monotonic_missing_tokens.append("multimodal_readiness_probe_invocation_missing")
        if monotonic_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + monotonic_missing_tokens))

    gateway_probe_delegate_path = repo_root / GATEWAY_TRUST_BOUNDARY_PROBE_CI_DELEGATE_SCRIPT
    if not gateway_probe_delegate_path.exists():
        missing_surface_files.append(GATEWAY_TRUST_BOUNDARY_PROBE_CI_DELEGATE_SCRIPT)
    else:
        rel = GATEWAY_TRUST_BOUNDARY_PROBE_CI_DELEGATE_SCRIPT
        text = _read_text(gateway_probe_delegate_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing_python = [
            script
            for script in GATEWAY_TRUST_BOUNDARY_DELEGATED_REQUIRED_PYTHON_SCRIPTS
            if script not in invoked_python_scripts
        ]
        if missing_python:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + missing_python))

        has_runner_forge_probe = all(
            token in text
            for token in (
                "run_probe runner_local_key_forge_blocked",
                BUNDLE_RUNNER_SCRIPT,
                "--wrapper-proof-json",
                "--wrapper-proof-signature",
            )
        )
        has_egress_forge_probe = all(
            token in text
            for token in (
                "run_probe final_emit_local_key_forge_blocked",
                FINAL_EGRESS_WRAPPER_SCRIPT,
                "--egress-grant-json",
                "--egress-grant-signature",
            )
        )
        has_egress_wrapper_direct_probe = all(
            token in text
            for token in (
                "run_probe egress_wrapper_direct_call_blocked",
                "python3 \"${EGRESS_WRAPPER_PATH}\"",
                "--candidate-output \"direct egress wrapper bypass probe\"",
                "--ingress-receipt",
            )
        )
        has_session_chain_headstamp_probe = all(
            token in text
            for token in (
                "run_probe session_chain_headstamp_first_line_required",
                "python3 \"${SESSION_CHAIN_WRAPPER_PATH}\"",
                "--message \"session chain headstamp required probe\"",
                "--json-only",
            )
        )
        has_session_chain_protocol_probe = all(
            token in text
            for token in (
                "run_probe session_chain_protocol_lane_explicit_context_pass",
                "python3 \"${SESSION_CHAIN_WRAPPER_PATH}\"",
                "--repo-catalog identity/catalog/identities.yaml",
                "--work-layer protocol",
                "session chain protocol explicit context probe",
            )
        )
        has_strict_default_first_line_probe = all(
            token in text
            for token in (
                "run_probe strict_first_line_missing_evidence_blocked",
                "python3 scripts/validate_reply_identity_context_first_line.py",
                "--operation validate",
                "--force-check",
            )
        )
        has_direct_text_emit_probe = all(
            token in text
            for token in (
                "run_probe direct_text_emit",
                "python3 scripts/final_emit_governed.py",
                "--body-text \"direct text emit bypass probe\"",
            )
        )
        has_channel_bypass_emit_probe = all(
            token in text
            for token in (
                "run_probe channel_bypass_emit",
                "python3 \"${EGRESS_WRAPPER_PATH}\"",
                "--candidate-output \"channel bypass emit probe\"",
                "--ingress-receipt",
            )
        )
        has_context_timeout_probe = all(
            token in text
            for token in (
                "run_probe resolve_context_timeout_guard",
                "python3 scripts/probe_gateway_timeout_guard.py",
                "--timeout-seconds 1",
                "--sleep-seconds 2",
                "--json-only",
            )
        )
        has_fixture_identity_runtime_egress_probe = all(
            token in text
            for token in (
                "run_probe fixture_identity_runtime_egress_blocked",
                "python3 scripts/final_emit_governed.py",
                "--identity-id \"probe-fixture\"",
                "fixture identity runtime egress blocked probe",
            )
        )
        has_session_chain_non_json_probe = all(
            token in text
            for token in (
                "run_probe session_chain_non_json_payload_blocked",
                "session_chain_payload_missing_or_non_json",
                "protocol_session_chain_wrapper_non_json.py",
                "invoke_gateway_wrapper_final_emit_probe.py",
            )
        )
        has_protocol_explicit_context_probe = all(
            token in text
            for token in (
                "run_probe protocol_work_layer_explicit_context_required",
                "python3 scripts/final_emit_governed.py",
                "--work-layer protocol",
                "--body-text \"protocol explicit context guard probe\"",
            )
        )
        has_quoted_foreign_context_probe = all(
            token in text
            for token in (
                "run_probe quoted_foreign_identity_context_must_not_switch_identity",
                "python3 scripts/compose_and_validate_governed_reply.py",
                "quoted foreign identity context guard probe",
                "quoted_identity_context_foreign_ids",
            )
        )
        has_session_bound_foreign_probe = all(
            token in text
            for token in (
                "run_probe session_bound_other_identity_without_switch_receipt_must_fail",
                "--session-id \"${SESSION_ID_FOREIGN}\"",
                "session bound foreign identity mismatch probe",
                "session_scoped_actor_binding_missing",
            )
        )
        has_session_chain_tuple_assertions = all(
            token in text
            for token in (
                "headstamp_first_line_status",
                "entry_receipt_tuple_status",
                "final_emit_contract_status",
                "required_tuple",
            )
        )
        gateway_missing_tokens: list[str] = []
        if not has_runner_forge_probe:
            gateway_missing_tokens.append("gateway_runner_forge_probe_invocation_missing")
        if not has_egress_forge_probe:
            gateway_missing_tokens.append("gateway_egress_forge_probe_invocation_missing")
        if not has_egress_wrapper_direct_probe:
            gateway_missing_tokens.append("gateway_egress_wrapper_direct_probe_invocation_missing")
        if not has_session_chain_headstamp_probe:
            gateway_missing_tokens.append("gateway_session_chain_headstamp_probe_invocation_missing")
        if not has_session_chain_protocol_probe:
            gateway_missing_tokens.append("gateway_session_chain_protocol_probe_invocation_missing")
        if not has_strict_default_first_line_probe:
            gateway_missing_tokens.append("gateway_strict_default_first_line_probe_invocation_missing")
        if not has_direct_text_emit_probe:
            gateway_missing_tokens.append("gateway_direct_text_emit_probe_invocation_missing")
        if not has_channel_bypass_emit_probe:
            gateway_missing_tokens.append("gateway_channel_bypass_emit_probe_invocation_missing")
        if not has_context_timeout_probe:
            gateway_missing_tokens.append("gateway_context_timeout_probe_invocation_missing")
        if not has_fixture_identity_runtime_egress_probe:
            gateway_missing_tokens.append("gateway_fixture_identity_runtime_egress_probe_invocation_missing")
        if not has_session_chain_non_json_probe:
            gateway_missing_tokens.append("gateway_session_chain_non_json_probe_invocation_missing")
        if not has_protocol_explicit_context_probe:
            gateway_missing_tokens.append("gateway_protocol_explicit_context_probe_invocation_missing")
        if not has_quoted_foreign_context_probe:
            gateway_missing_tokens.append("gateway_quoted_foreign_context_probe_invocation_missing")
        if not has_session_bound_foreign_probe:
            gateway_missing_tokens.append("gateway_session_bound_foreign_probe_invocation_missing")
        if not has_session_chain_tuple_assertions:
            gateway_missing_tokens.append("gateway_session_chain_tuple_assertions_missing")
        if gateway_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + gateway_missing_tokens))

    host_visible_probe_delegate_path = repo_root / HOST_VISIBLE_SURFACE_PROBE_CI_DELEGATE_SCRIPT
    if not host_visible_probe_delegate_path.exists():
        missing_surface_files.append(HOST_VISIBLE_SURFACE_PROBE_CI_DELEGATE_SCRIPT)
    else:
        rel = HOST_VISIBLE_SURFACE_PROBE_CI_DELEGATE_SCRIPT
        text = _read_text(host_visible_probe_delegate_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing_python = [
            script
            for script in HOST_VISIBLE_SURFACE_DELEGATED_REQUIRED_PYTHON_SCRIPTS
            if script not in invoked_python_scripts
        ]
        if missing_python:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + missing_python))

        has_static_probe = all(
            token in text
            for token in (
                "run_probe host_visible_contract_static",
                "scripts/validate_host_transport_wiring_attestation.py",
                "--json-only",
            )
        )
        has_live_probe = all(
            token in text
            for token in (
                "run_probe host_visible_live_receipts_pass",
                "scripts/validate_host_transport_wiring_attestation.py",
                "--require-live-receipts",
                "--require-run-id",
            )
        )
        has_negative_probe = all(
            token in text
            for token in (
                "run_probe host_visible_commentary_bypass_blocked",
                "host_visible_surface_live_channel_status_not_pass:commentary:headstamp_first_line_status",
            )
        )
        has_run_binding_negative_probe = all(
            token in text
            for token in (
                "run_probe host_visible_live_run_binding_required_blocked",
                "host_visible_surface_live_run_id_required_missing",
                "--require-live-receipts",
            )
        )
        has_binding_negative_probe = all(
            token in text
            for token in (
                "run_probe host_visible_commentary_session_binding_blocked",
                "host_visible_surface_live_channel_session_id_mismatch:commentary:",
                "--require-session-id",
                "--require-run-id",
            )
        )
        has_send_time_positive_probe = all(
            token in text
            for token in (
                "run_probe send_time_governed_pass_headstamp_required",
                "send_time_governed_pass_headstamp_required: send_time_gate_status must be PASS_REQUIRED",
                "send_time_governed_pass_headstamp_required: reply_first_line_status must be PASS_REQUIRED",
                "send_time_governed_pass_headstamp_required: chat_egress_uniqueness_status must be PASS_REQUIRED",
            )
        )
        has_post_check_blocker_probe = all(
            token in text
            for token in (
                "run_probe send_time_next_hop_blocked_by_post_check",
                "chat_egress_uniqueness_contract_id mismatch",
                "chat_egress_uniqueness_status must be FAIL_REQUIRED",
                "IP-HDSTAMP-003",
                "post_check_blocker_active_next_hop_blocked",
            )
        )
        has_post_check_state_missing_probe = all(
            token in text
            for token in (
                "run_probe send_time_next_hop_blocked_on_missing_post_check_state",
                "chat_egress_uniqueness_contract_id mismatch",
                "chat_egress_uniqueness_status must be FAIL_REQUIRED",
                "IP-HDSTAMP-003",
                "post_check_state_unavailable_fail_close",
            )
        )
        host_visible_missing_tokens: list[str] = []
        if not has_static_probe:
            host_visible_missing_tokens.append("host_visible_surface_static_probe_invocation_missing")
        if not has_live_probe:
            host_visible_missing_tokens.append("host_visible_surface_live_probe_invocation_missing")
        if not has_negative_probe:
            host_visible_missing_tokens.append("host_visible_surface_commentary_negative_probe_invocation_missing")
        if not has_run_binding_negative_probe:
            host_visible_missing_tokens.append("host_visible_surface_run_binding_negative_probe_invocation_missing")
        if not has_binding_negative_probe:
            host_visible_missing_tokens.append("host_visible_surface_commentary_session_binding_negative_probe_invocation_missing")
        if not has_send_time_positive_probe:
            host_visible_missing_tokens.append("host_visible_surface_send_time_positive_headstamp_probe_invocation_missing")
        if not has_post_check_blocker_probe:
            host_visible_missing_tokens.append("host_visible_surface_post_check_blocker_chat_egress_probe_invocation_missing")
        if not has_post_check_state_missing_probe:
            host_visible_missing_tokens.append("host_visible_surface_post_check_state_missing_chat_egress_probe_invocation_missing")
        if host_visible_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + host_visible_missing_tokens))

    unique_entry_probe_delegate_path = repo_root / UNIQUE_ENTRY_TUPLE_PROBE_CI_DELEGATE_SCRIPT
    if not unique_entry_probe_delegate_path.exists():
        missing_surface_files.append(UNIQUE_ENTRY_TUPLE_PROBE_CI_DELEGATE_SCRIPT)
    else:
        rel = UNIQUE_ENTRY_TUPLE_PROBE_CI_DELEGATE_SCRIPT
        text = _read_text(unique_entry_probe_delegate_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing_python = [
            script
            for script in UNIQUE_ENTRY_TUPLE_DELEGATED_REQUIRED_PYTHON_SCRIPTS
            if script not in invoked_python_scripts
        ]
        if missing_python:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + missing_python))

        has_strict_default_receipt_probe = all(
            token in text
            for token in (
                "run_probe strict_receipt_default_blocked",
                "protocol_unique_entry_receipt_required",
                "strict_operation_contract",
                "entry_receipt_missing",
            )
        )
        has_migration_closure_probe = all(
            token in text
            for token in (
                "run_probe tuple_binding_active_runtime_contract_closure",
                "scripts/check_unique_entry_contract_migration_closure.py",
                "--catalog",
                "--json-only",
            )
        )
        unique_entry_missing_tokens: list[str] = []
        if not has_strict_default_receipt_probe:
            unique_entry_missing_tokens.append("unique_entry_strict_default_receipt_probe_invocation_missing")
        if not has_migration_closure_probe:
            unique_entry_missing_tokens.append("unique_entry_migration_closure_probe_invocation_missing")
        if unique_entry_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + unique_entry_missing_tokens))

    downsink_probe_delegate_path = repo_root / DOWNSINK_PATH_IMMUTABILITY_PROBE_CI_DELEGATE_SCRIPT
    if not downsink_probe_delegate_path.exists():
        missing_surface_files.append(DOWNSINK_PATH_IMMUTABILITY_PROBE_CI_DELEGATE_SCRIPT)
    else:
        rel = DOWNSINK_PATH_IMMUTABILITY_PROBE_CI_DELEGATE_SCRIPT
        text = _read_text(downsink_probe_delegate_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing_python = [
            script
            for script in DOWNSINK_PATH_IMMUTABILITY_DELEGATED_REQUIRED_PYTHON_SCRIPTS
            if script not in invoked_python_scripts
        ]
        if missing_python:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + missing_python))

        has_noncanonical_probe = all(
            token in text
            for token in (
                "run_probe probe_path_registry_mutation_noncanonical",
                "scripts/validate_protocol_downsink_path_immutability.py",
            )
        )
        has_parent_escape_probe = all(
            token in text
            for token in (
                "run_probe probe_parent_escape",
                "../runtime/gate/protocol_ingress_wrapper.py",
            )
        )
        has_symlink_escape_probe = all(
            token in text
            for token in (
                "run_probe probe_symlink_escape",
                "outbox-to-protocol",
                "symlink_to(",
            )
        )
        has_feedback_nonregistry_probe = all(
            token in text
            for token in (
                "run_probe probe_feedback_nonregistry_write",
                "--probe-write-path \"runtime/protocol-feedback/noncanonical/FEEDBACK_BATCH_probe.md\"",
            )
        )
        has_feedback_filename_probe = all(
            token in text
            for token in (
                "run_probe probe_feedback_noncanonical_filename_write",
                "--probe-write-path \"runtime/protocol-feedback/outbox-to-protocol/freeform_note_probe.md\"",
            )
        )
        has_feedback_inquiry_trigger_positive_probe = all(
            token in text
            for token in (
                "run_probe probe_feedback_inquiry_requiredization_trigger_allowed",
                "--probe-write-path \"runtime/protocol-feedback/outbox-to-protocol/INQUIRY_REQUIREDIZATION_TRIGGER_20260316T000000Z.json\"",
            )
        )
        has_feedback_sanitization_positive_probe = all(
            token in text
            for token in (
                "run_probe probe_feedback_sanitization_paraphrase_allowed",
                "--probe-write-path \"runtime/protocol-feedback/outbox-to-protocol/SANITIZATION_PARAPHRASE_20260316T000000Z.json\"",
            )
        )
        has_feedback_lane_lock_protocol_positive_probe = all(
            token in text
            for token in (
                "run_probe probe_feedback_session_lane_lock_protocol_allowed",
                "--probe-write-path \"runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_PROTOCOL_20260316T000000Z.json\"",
            )
        )
        has_feedback_lane_lock_exit_positive_probe = all(
            token in text
            for token in (
                "run_probe probe_feedback_session_lane_lock_exit_allowed",
                "--probe-write-path \"runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_EXIT_20260316T000000Z.json\"",
            )
        )
        has_broadcast_nonregistry_probe = all(
            token in text
            for token in (
                "run_probe probe_broadcast_nonregistry_receipt",
                "--probe-write-path \"runtime/reports/noncanonical/broadcast-receipt-probe.json\"",
            )
        )
        has_literal_lock_probe = all(
            token in text
            for token in (
                "run_probe probe_unregistered_literal_fail",
                "scripts/validate_protocol_downsink_path_literal_lock.py",
                "--probe-path-literal \"runtime/protocol-feedback/outbox-legacy/FEEDBACK_BATCH_probe.md\"",
            )
        )
        downsink_missing_tokens: list[str] = []
        if not has_noncanonical_probe:
            downsink_missing_tokens.append("downsink_noncanonical_probe_invocation_missing")
        if not has_parent_escape_probe:
            downsink_missing_tokens.append("downsink_parent_escape_probe_invocation_missing")
        if not has_symlink_escape_probe:
            downsink_missing_tokens.append("downsink_symlink_escape_probe_invocation_missing")
        if not has_feedback_nonregistry_probe:
            downsink_missing_tokens.append("downsink_feedback_nonregistry_probe_invocation_missing")
        if not has_feedback_filename_probe:
            downsink_missing_tokens.append("downsink_feedback_filename_probe_invocation_missing")
        if not has_feedback_inquiry_trigger_positive_probe:
            downsink_missing_tokens.append("downsink_feedback_inquiry_trigger_positive_probe_missing")
        if not has_feedback_sanitization_positive_probe:
            downsink_missing_tokens.append("downsink_feedback_sanitization_positive_probe_missing")
        if not has_feedback_lane_lock_protocol_positive_probe:
            downsink_missing_tokens.append("downsink_feedback_lane_lock_protocol_positive_probe_missing")
        if not has_feedback_lane_lock_exit_positive_probe:
            downsink_missing_tokens.append("downsink_feedback_lane_lock_exit_positive_probe_missing")
        if not has_broadcast_nonregistry_probe:
            downsink_missing_tokens.append("downsink_broadcast_nonregistry_probe_invocation_missing")
        if not has_literal_lock_probe:
            downsink_missing_tokens.append("downsink_literal_lock_probe_invocation_missing")
        if downsink_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + downsink_missing_tokens))

    installer_baseline_probe_delegate_path = repo_root / INSTALLER_VERSION_BASELINE_PROBE_CI_DELEGATE_SCRIPT
    if not installer_baseline_probe_delegate_path.exists():
        missing_surface_files.append(INSTALLER_VERSION_BASELINE_PROBE_CI_DELEGATE_SCRIPT)
    else:
        rel = INSTALLER_VERSION_BASELINE_PROBE_CI_DELEGATE_SCRIPT
        text = _read_text(installer_baseline_probe_delegate_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing_python = [
            script
            for script in INSTALLER_VERSION_BASELINE_DELEGATED_REQUIRED_PYTHON_SCRIPTS
            if script not in invoked_python_scripts and script not in text
        ]
        if missing_python:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + missing_python))

        has_install_probe = all(
            token in text
            for token in (
                "run_probe install_legacy_pack_version_drift_blocked",
                "scripts/identity_installer.py",
                "version_baseline_apply_status",
                "version_baseline_verify_status",
            )
        )
        has_migration_closure_probe = all(
            token in text
            for token in (
                "run_probe install_then_migration_closure_pass",
                "scripts/check_version_baseline_migration_closure.py",
                "--catalog",
                "--json-only",
            )
        )
        installer_missing_tokens: list[str] = []
        if not has_install_probe:
            installer_missing_tokens.append("installer_version_baseline_install_probe_invocation_missing")
        if not has_migration_closure_probe:
            installer_missing_tokens.append("installer_version_baseline_migration_closure_probe_invocation_missing")
        if installer_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + installer_missing_tokens))

    skill_supply_chain_probe_delegate_path = repo_root / SKILL_SUPPLY_CHAIN_PROBE_CI_DELEGATE_SCRIPT
    if not skill_supply_chain_probe_delegate_path.exists():
        missing_surface_files.append(SKILL_SUPPLY_CHAIN_PROBE_CI_DELEGATE_SCRIPT)
    else:
        rel = SKILL_SUPPLY_CHAIN_PROBE_CI_DELEGATE_SCRIPT
        text = _read_text(skill_supply_chain_probe_delegate_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing_python = [
            script
            for script in SKILL_SUPPLY_CHAIN_DELEGATED_REQUIRED_PYTHON_SCRIPTS
            if script not in invoked_python_scripts and script not in text
        ]
        if missing_python:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + missing_python))

        has_frontmatter_missing_probe = all(
            token in text
            for token in (
                "validate_skill_frontmatter.py",
                "IP-SFRONT-001",
                "probe frontmatter_missing_blocked",
            )
        )
        has_drift_probe = all(
            token in text
            for token in (
                "validate_skill_sync_drift_guard.py",
                "IP-SDRIFT-001",
                "probe drift_detected_blocked",
            )
        )
        has_supply_chain_probe = all(
            token in text
            for token in (
                "validate_skill_installation_supply_chain.py",
                "IP-SSUP-001",
                "probe supply_chain_dependency_blocked",
            )
        )
        skill_probe_missing_tokens: list[str] = []
        if not has_frontmatter_missing_probe:
            skill_probe_missing_tokens.append("skill_frontmatter_negative_probe_invocation_missing")
        if not has_drift_probe:
            skill_probe_missing_tokens.append("skill_sync_drift_negative_probe_invocation_missing")
        if not has_supply_chain_probe:
            skill_probe_missing_tokens.append("skill_supply_chain_negative_probe_invocation_missing")
        if skill_probe_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + skill_probe_missing_tokens))

    semantic_clarity_probe_delegate_path = repo_root / SEMANTIC_CLARITY_PROBE_CI_DELEGATE_SCRIPT
    if not semantic_clarity_probe_delegate_path.exists():
        missing_surface_files.append(SEMANTIC_CLARITY_PROBE_CI_DELEGATE_SCRIPT)
    else:
        rel = SEMANTIC_CLARITY_PROBE_CI_DELEGATE_SCRIPT
        text = _read_text(semantic_clarity_probe_delegate_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        missing_python = [
            script
            for script in SEMANTIC_CLARITY_DELEGATED_REQUIRED_PYTHON_SCRIPTS
            if script not in invoked_python_scripts and script not in text
        ]
        if missing_python:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + missing_python))

        has_semantic_term_negative_probe = all(
            token in text
            for token in (
                "validate_semantic_term_registry.py",
                "IP-SEMREG-001",
                "negative semantic term forbidden phrase blocked",
            )
        )
        has_cli_catalog_negative_probe = all(
            token in text
            for token in (
                "validate_cli_catalog_default_semantics.py",
                "IP-CLICAT-001",
                "negative cli catalog fallback blocked",
            )
        )
        has_stream_scope_negative_probe = all(
            token in text
            for token in (
                "validate_stream_scope_semantic_integrity.py",
                "IP-SSCOPE-001",
                "negative stream scope alias fail-close blocked",
            )
        )
        semantic_probe_missing_tokens: list[str] = []
        if not has_semantic_term_negative_probe:
            semantic_probe_missing_tokens.append("semantic_term_registry_negative_probe_invocation_missing")
        if not has_cli_catalog_negative_probe:
            semantic_probe_missing_tokens.append("cli_catalog_default_semantics_negative_probe_invocation_missing")
        if not has_stream_scope_negative_probe:
            semantic_probe_missing_tokens.append("stream_scope_semantic_integrity_negative_probe_invocation_missing")
        if semantic_probe_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + semantic_probe_missing_tokens))

    runtime_file_governance_docs = (
        (RUNTIME_FILE_GOVERNANCE_GOV_DOC, RUNTIME_FILE_GOVERNANCE_GOV_REQUIRED_TOKENS),
        (RUNTIME_FILE_GOVERNANCE_REVIEW_DOC, RUNTIME_FILE_GOVERNANCE_REVIEW_REQUIRED_TOKENS),
        (HOST_VISIBLE_SEMANTIC_FREEZE_GOV_DOC, HOST_VISIBLE_SEMANTIC_FREEZE_GOV_REQUIRED_TOKENS),
        (HOST_VISIBLE_SEMANTIC_FREEZE_REVIEW_DOC, HOST_VISIBLE_SEMANTIC_FREEZE_REVIEW_REQUIRED_TOKENS),
    )
    for rel, required_tokens in runtime_file_governance_docs:
        path = repo_root / rel
        if not path.exists():
            missing_surface_files.append(rel)
            continue
        text = _read_text(path)
        missing_tokens = [token for token in required_tokens if token not in text]
        if missing_tokens:
            existing = list(missing_lineage_refs.get(rel, []))
            missing_lineage_refs[rel] = sorted(set(existing + [f"runtime_file_governance_token_missing:{tok}" for tok in missing_tokens]))

    dialogue_bundle_path = repo_root / DIALOGUE_FEEDBACK_BUNDLE_SCRIPT
    if not dialogue_bundle_path.exists():
        missing_surface_files.append(DIALOGUE_FEEDBACK_BUNDLE_SCRIPT)
    else:
        rel = DIALOGUE_FEEDBACK_BUNDLE_SCRIPT
        text = _read_text(dialogue_bundle_path)
        invoked_python_scripts = _extract_shell_invocations(text, executable="python3")
        literal_python_scripts = _parse_script_literals(text)
        discovered_scripts = set(invoked_python_scripts) | set(literal_python_scripts)
        missing_validators = [
            script
            for script in DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_VALIDATORS
            if script not in discovered_scripts
        ]
        if missing_validators:
            dialogue_bundle_missing[rel] = missing_validators
        bundle_invocation_args: list[list[str]] = []
        for script in DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_VALIDATORS:
            bundle_invocation_args.extend(
                _extract_shell_invocation_args(text, executable="python3", script=script)
            )
        missing_bundle_tokens = [
            token
            for token in DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_ARGS
            if not any(_arg_token_present(args, token) for args in bundle_invocation_args)
            and token not in text
        ]
        if missing_bundle_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + missing_bundle_tokens))

    super_linter_workflow_path = repo_root / SUPER_LINTER_WORKFLOW_SURFACE
    if not super_linter_workflow_path.exists():
        missing_surface_files.append(SUPER_LINTER_WORKFLOW_SURFACE)
    else:
        text = _read_text(super_linter_workflow_path)
        missing_tokens = [token for token in SUPER_LINTER_REQUIRED_TOKENS if token not in text]
        if missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(SUPER_LINTER_WORKFLOW_SURFACE, []))
            missing_execution_tokens[SUPER_LINTER_WORKFLOW_SURFACE] = sorted(set(existing_tokens + missing_tokens))

    required_gates_workflow_path = repo_root / WORKFLOW_REQUIRED_GATE_SURFACE
    if required_gates_workflow_path.exists():
        text = _read_text(required_gates_workflow_path)
        missing_tokens = [token for token in REQUIRED_GATES_SUPER_LINTER_TOKENS if token not in text]
        if missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(WORKFLOW_REQUIRED_GATE_SURFACE, []))
            missing_execution_tokens[WORKFLOW_REQUIRED_GATE_SURFACE] = sorted(set(existing_tokens + missing_tokens))

    bundle_runner_path = repo_root / BUNDLE_RUNNER_SCRIPT
    if bundle_runner_path.exists():
        bundle_runner_text = _read_text(bundle_runner_path)
        bundle_runner_skill_path_active_repo_root_missing = _missing_bundle_skill_path_active_repo_root_tokens(
            bundle_runner_text
        )
        if bundle_runner_skill_path_active_repo_root_missing:
            existing_tokens = list(missing_execution_tokens.get(BUNDLE_RUNNER_SCRIPT, []))
            missing_execution_tokens[BUNDLE_RUNNER_SCRIPT] = sorted(
                set(
                    existing_tokens
                    + [
                        f"bundle_skill_path_active_repo_root_wiring_missing:{token}"
                        for token in bundle_runner_skill_path_active_repo_root_missing
                    ]
                )
            )

    if mapping_errors or missing_surface_files:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-001"
    elif gateway_wrapper_bus_missing or infra_contract_missing:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-009"
    elif missing_lineage_refs or missing_execution_tokens or forbidden_hits or dialogue_bundle_missing:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-002"
    elif missing_final_egress_wrapper or forbidden_direct_egress_hits:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-006"
    elif actor_id_passthrough_missing:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-003"
    elif session_id_passthrough_missing:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-005"
    elif bundle_arg_contract_missing:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-004"
    elif bundle_arg_value_invalid:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-007"
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""

    payload: dict[str, Any] = {
        "required_gate_surface_drift_status": status,
        "error_code": error_code,
        "bundle_runner_script": BUNDLE_RUNNER_SCRIPT,
        "recurrence_escalator_script": RECURRENCE_ESCALATOR_SCRIPT,
        "tuple_parity_script": TUPLE_PARITY_SCRIPT,
        "mandatory_lineage_scripts": list(MANDATORY_LINEAGE_SCRIPTS),
        "contract_mapping_entry": str(mapping_entry_path),
        "contract_mapping": str(mapping_path),
        "mapping_errors": mapping_errors,
        "strict_surfaces": list(STRICT_SURFACES),
        "full_scan_delegate_required_python_scripts": list(FULL_SCAN_DELEGATED_REQUIRED_PYTHON_SCRIPTS),
        "full_scan_delegate_required_tokens": list(FULL_SCAN_DELEGATED_REQUIRED_TOKENS),
        "monotonic_floor_probe_ci_delegate_script": MONOTONIC_FLOOR_PROBE_CI_DELEGATE_SCRIPT,
        "monotonic_probe_delegate_required_python_scripts": list(MONOTONIC_PROBE_DELEGATED_REQUIRED_PYTHON_SCRIPTS),
        "monotonic_probe_required_target": MONOTONIC_PROBE_REQUIRED_TARGET,
        "gateway_trust_boundary_probe_ci_delegate_script": GATEWAY_TRUST_BOUNDARY_PROBE_CI_DELEGATE_SCRIPT,
        "gateway_trust_boundary_delegate_required_python_scripts": list(
            GATEWAY_TRUST_BOUNDARY_DELEGATED_REQUIRED_PYTHON_SCRIPTS
        ),
        "host_visible_surface_probe_ci_delegate_script": HOST_VISIBLE_SURFACE_PROBE_CI_DELEGATE_SCRIPT,
        "host_visible_surface_delegate_required_python_scripts": list(
            HOST_VISIBLE_SURFACE_DELEGATED_REQUIRED_PYTHON_SCRIPTS
        ),
        "unique_entry_tuple_probe_ci_delegate_script": UNIQUE_ENTRY_TUPLE_PROBE_CI_DELEGATE_SCRIPT,
        "unique_entry_tuple_delegate_required_python_scripts": list(
            UNIQUE_ENTRY_TUPLE_DELEGATED_REQUIRED_PYTHON_SCRIPTS
        ),
        "downsink_path_immutability_probe_ci_delegate_script": DOWNSINK_PATH_IMMUTABILITY_PROBE_CI_DELEGATE_SCRIPT,
        "downsink_path_immutability_delegate_required_python_scripts": list(
            DOWNSINK_PATH_IMMUTABILITY_DELEGATED_REQUIRED_PYTHON_SCRIPTS
        ),
        "installer_version_baseline_probe_ci_delegate_script": INSTALLER_VERSION_BASELINE_PROBE_CI_DELEGATE_SCRIPT,
        "installer_version_baseline_delegate_required_python_scripts": list(
            INSTALLER_VERSION_BASELINE_DELEGATED_REQUIRED_PYTHON_SCRIPTS
        ),
        "skill_supply_chain_probe_ci_delegate_script": SKILL_SUPPLY_CHAIN_PROBE_CI_DELEGATE_SCRIPT,
        "skill_supply_chain_delegate_required_python_scripts": list(
            SKILL_SUPPLY_CHAIN_DELEGATED_REQUIRED_PYTHON_SCRIPTS
        ),
        "semantic_clarity_probe_ci_delegate_script": SEMANTIC_CLARITY_PROBE_CI_DELEGATE_SCRIPT,
        "semantic_clarity_delegate_required_python_scripts": list(
            SEMANTIC_CLARITY_DELEGATED_REQUIRED_PYTHON_SCRIPTS
        ),
        "runtime_file_governance_governance_doc": RUNTIME_FILE_GOVERNANCE_GOV_DOC,
        "runtime_file_governance_review_doc": RUNTIME_FILE_GOVERNANCE_REVIEW_DOC,
        "runtime_file_governance_governance_doc_required_tokens": list(
            RUNTIME_FILE_GOVERNANCE_GOV_REQUIRED_TOKENS
        ),
        "runtime_file_governance_review_doc_required_tokens": list(
            RUNTIME_FILE_GOVERNANCE_REVIEW_REQUIRED_TOKENS
        ),
        "host_visible_semantic_freeze_governance_doc": HOST_VISIBLE_SEMANTIC_FREEZE_GOV_DOC,
        "host_visible_semantic_freeze_review_doc": HOST_VISIBLE_SEMANTIC_FREEZE_REVIEW_DOC,
        "host_visible_semantic_freeze_governance_doc_required_tokens": list(
            HOST_VISIBLE_SEMANTIC_FREEZE_GOV_REQUIRED_TOKENS
        ),
        "host_visible_semantic_freeze_review_doc_required_tokens": list(
            HOST_VISIBLE_SEMANTIC_FREEZE_REVIEW_REQUIRED_TOKENS
        ),
        "dialogue_feedback_bundle_script": DIALOGUE_FEEDBACK_BUNDLE_SCRIPT,
        "dialogue_feedback_bundle_required_surfaces": list(DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_SURFACES),
        "dialogue_feedback_bundle_required_validators": list(DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_VALIDATORS),
        "dialogue_feedback_bundle_required_args": list(DIALOGUE_FEEDBACK_BUNDLE_REQUIRED_ARGS),
        "super_linter_workflow_surface": SUPER_LINTER_WORKFLOW_SURFACE,
        "super_linter_required_tokens": list(SUPER_LINTER_REQUIRED_TOKENS),
        "required_gates_super_linter_tokens": list(REQUIRED_GATES_SUPER_LINTER_TOKENS),
        "forbidden_direct_validators": forbidden_direct_validators,
        "missing_surface_files": missing_surface_files,
        "missing_lineage_refs": missing_lineage_refs,
        "missing_execution_tokens": missing_execution_tokens,
        "dialogue_bundle_missing": dialogue_bundle_missing,
        "forbidden_hits": forbidden_hits,
        "final_egress_wrapper_script": FINAL_EGRESS_WRAPPER_SCRIPT,
        "final_egress_required_surfaces": list(FINAL_EGRESS_REQUIRED_SURFACES),
        "missing_final_egress_wrapper": missing_final_egress_wrapper,
        "forbidden_direct_egress_scripts": list(FORBIDDEN_DIRECT_EGRESS_SCRIPTS),
        "forbidden_direct_egress_hits": forbidden_direct_egress_hits,
        "gateway_wrapper_bus_required_surfaces": list(GATEWAY_WRAPPER_BUS_REQUIRED_SURFACES),
        "gateway_wrapper_bus_forbidden_legacy_helpers": list(GATEWAY_WRAPPER_BUS_FORBIDDEN_LEGACY_HELPERS),
        "gateway_wrapper_bus_missing": gateway_wrapper_bus_missing,
        "gateway_wrapper_bus_violations": gateway_wrapper_bus_violations,
        "infra_contract_required_surfaces": list(INFRA_CONTRACT_REQUIRED_SURFACES),
        "infra_contract_required_import": INFRA_CONTRACT_REQUIRED_IMPORT,
        "infra_contract_forbidden_literal_targets": list(INFRA_CONTRACT_FORBIDDEN_LITERAL_TARGETS),
        "infra_contract_missing": infra_contract_missing,
        "infra_contract_violations": infra_contract_violations,
        "actor_id_required_scripts": list(ACTOR_ID_REQUIRED_SCRIPTS),
        "actor_id_passthrough_missing": actor_id_passthrough_missing,
        "session_id_required_scripts": list(SESSION_ID_REQUIRED_SCRIPTS),
        "session_id_passthrough_missing": session_id_passthrough_missing,
        "bundle_runner_required_args": list(BUNDLE_REQUIRED_ARGS),
        "bundle_arg_contract_missing": bundle_arg_contract_missing,
        "bundle_args_forbid_unknown": list(BUNDLE_ARGS_FORBID_UNKNOWN),
        "bundle_skill_path_active_repo_root_required_tokens": list(
            BUNDLE_SKILL_PATH_ACTIVE_REPO_ROOT_REQUIRED_TOKENS
        ),
        "bundle_runner_skill_path_active_repo_root_missing": bundle_runner_skill_path_active_repo_root_missing,
        "bundle_args_forbid_noncanonical": {
            "--gate-profile-file": CANONICAL_GATE_PROFILE_FILE
        },
        "bundle_arg_value_invalid": bundle_arg_value_invalid,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[DRIFT] status={status} missing_surface_files={len(missing_surface_files)} "
            f"missing_lineage_surfaces={len(missing_lineage_refs)} forbidden_hit_surfaces={len(forbidden_hits)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 1 if status == STATUS_FAIL_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
