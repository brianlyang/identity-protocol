#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
from pathlib import Path
from typing import Any

import yaml

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
DOWNSINK_PATH_IMMUTABILITY_PROBE_CI_DELEGATE_SCRIPT = "scripts/ci/run_downsink_path_immutability_probes_ci.sh"
WORKFLOW_REQUIRED_EXECUTION_SCRIPTS: tuple[str, ...] = (
    REQUIRED_GATE_CI_DELEGATE_SCRIPT,
    MONOTONIC_FLOOR_PROBE_CI_DELEGATE_SCRIPT,
    GATEWAY_TRUST_BOUNDARY_PROBE_CI_DELEGATE_SCRIPT,
    DOWNSINK_PATH_IMMUTABILITY_PROBE_CI_DELEGATE_SCRIPT,
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
    "scripts/required_gate_bundle_runner.py",
)
MONOTONIC_PROBE_REQUIRED_TARGET = "multimodal_plugin_enforcement"
GATEWAY_TRUST_BOUNDARY_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/required_gate_bundle_runner.py",
    "scripts/final_emit_governed.py",
)
DOWNSINK_PATH_IMMUTABILITY_DELEGATED_REQUIRED_PYTHON_SCRIPTS: tuple[str, ...] = (
    "scripts/repair_contract_backfill.py",
    "scripts/validate_protocol_downsink_path_immutability.py",
    "scripts/validate_protocol_downsink_path_write_guard.py",
    "scripts/validate_protocol_downsink_path_literal_lock.py",
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

BUNDLE_RUNNER_SCRIPT = "scripts/required_gate_bundle_runner.py"
RECURRENCE_ESCALATOR_SCRIPT = "scripts/validate_required_gate_recurrence_escalator.py"
TUPLE_PARITY_SCRIPT = "scripts/validate_required_gate_tuple_parity.py"
FINAL_EGRESS_WRAPPER_SCRIPT = "scripts/final_emit_governed.py"
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
    "scripts/final_emit_governed.py",
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
    actor_id_passthrough_missing: dict[str, dict[str, list[str]]] = {}
    session_id_passthrough_missing: dict[str, dict[str, list[str]]] = {}
    bundle_arg_contract_missing: dict[str, list[dict[str, Any]]] = {}
    bundle_arg_value_invalid: dict[str, list[dict[str, Any]]] = {}
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
            bus_violations: list[str] = []
            if GATEWAY_WRAPPER_BUS_REQUIRED_IMPORT not in text:
                bus_violations.append("gateway_wrapper_enforcement_import_missing")
            if GATEWAY_WRAPPER_BUS_REQUIRED_CALL not in text:
                bus_violations.append("run_gateway_wrapped_command_call_missing")
            legacy_hits = [
                helper
                for helper in GATEWAY_WRAPPER_BUS_FORBIDDEN_LEGACY_HELPERS
                if helper in text
            ]
            if legacy_hits:
                for helper in legacy_hits:
                    bus_violations.append(f"legacy_gateway_helper_detected:{helper}")
            if bus_violations:
                gateway_wrapper_bus_missing.append(rel)
                gateway_wrapper_bus_violations[rel] = sorted(set(bus_violations))
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
                "scripts/required_gate_bundle_runner.py",
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
                "scripts/required_gate_bundle_runner.py",
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
                "scripts/required_gate_bundle_runner.py",
                "--wrapper-proof-json",
                "--wrapper-proof-signature",
            )
        )
        has_egress_forge_probe = all(
            token in text
            for token in (
                "run_probe final_emit_local_key_forge_blocked",
                "scripts/final_emit_governed.py",
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
        gateway_missing_tokens: list[str] = []
        if not has_runner_forge_probe:
            gateway_missing_tokens.append("gateway_runner_forge_probe_invocation_missing")
        if not has_egress_forge_probe:
            gateway_missing_tokens.append("gateway_egress_forge_probe_invocation_missing")
        if not has_egress_wrapper_direct_probe:
            gateway_missing_tokens.append("gateway_egress_wrapper_direct_probe_invocation_missing")
        if gateway_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + gateway_missing_tokens))

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
        if not has_broadcast_nonregistry_probe:
            downsink_missing_tokens.append("downsink_broadcast_nonregistry_probe_invocation_missing")
        if not has_literal_lock_probe:
            downsink_missing_tokens.append("downsink_literal_lock_probe_invocation_missing")
        if downsink_missing_tokens:
            existing_tokens = list(missing_execution_tokens.get(rel, []))
            missing_execution_tokens[rel] = sorted(set(existing_tokens + downsink_missing_tokens))

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

    if mapping_errors or missing_surface_files:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-001"
    elif gateway_wrapper_bus_missing:
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
        "downsink_path_immutability_probe_ci_delegate_script": DOWNSINK_PATH_IMMUTABILITY_PROBE_CI_DELEGATE_SCRIPT,
        "downsink_path_immutability_delegate_required_python_scripts": list(
            DOWNSINK_PATH_IMMUTABILITY_DELEGATED_REQUIRED_PYTHON_SCRIPTS
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
        "actor_id_required_scripts": list(ACTOR_ID_REQUIRED_SCRIPTS),
        "actor_id_passthrough_missing": actor_id_passthrough_missing,
        "session_id_required_scripts": list(SESSION_ID_REQUIRED_SCRIPTS),
        "session_id_passthrough_missing": session_id_passthrough_missing,
        "bundle_runner_required_args": list(BUNDLE_REQUIRED_ARGS),
        "bundle_arg_contract_missing": bundle_arg_contract_missing,
        "bundle_args_forbid_unknown": list(BUNDLE_ARGS_FORBID_UNKNOWN),
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
