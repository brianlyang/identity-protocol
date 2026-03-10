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

STRICT_SURFACES: tuple[str, ...] = (
    "scripts/identity_creator.py",
    "scripts/release_readiness_check.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
    "scripts/e2e_smoke_test.sh",
    ".github/workflows/_identity-required-gates.yml",
)
WORKFLOW_REQUIRED_GATE_SURFACE = ".github/workflows/_identity-required-gates.yml"
REQUIRED_GATE_CI_DELEGATE_SCRIPT = "scripts/ci/run_required_runtime_gates_ci.sh"
FULL_SCAN_TARGET_CI_DELEGATE_SCRIPT = "scripts/ci/run_full_scan_target_regression_ci.sh"
WORKFLOW_REQUIRED_EXECUTION_TOKENS: tuple[str, ...] = (
    f"bash {REQUIRED_GATE_CI_DELEGATE_SCRIPT}",
    f"bash {FULL_SCAN_TARGET_CI_DELEGATE_SCRIPT}",
)
CI_DELEGATED_LINEAGE_SURFACES: tuple[str, ...] = (
    REQUIRED_GATE_CI_DELEGATE_SCRIPT,
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

VERSIONED_SCRIPT_ALIAS_RE = re.compile(r"^(?P<prefix>validate|normalize|emit)_v\d+_(?P<tail>.+)\.py$")
WRAPPER_MAIN_IMPORT_RE = re.compile(r"^\s*from\s+([A-Za-z0-9_.]+)\s+import\s+main\s*$", re.MULTILINE)
SCRIPT_LITERAL_RE = re.compile(r'["\'](scripts/[A-Za-z0-9_.-]+\.py)["\']')
SESSION_SET_RE = re.compile(r"session_id_required_scripts\s*=\s*\{(?P<body>.*?)\}", re.DOTALL)
INLINE_SCRIPT_SET_RE = re.compile(r"cmd\[1\]\s+in\s+\{(?P<body>.*?)\}", re.DOTALL)


def _resolve_default_contract_mapping(repo_root: Path) -> Path:
    mapping_dir = repo_root / "identity" / "protocol" / "mappings"
    candidates = sorted(mapping_dir.glob("contract-binding.v*.yaml"))
    if candidates:
        return candidates[-1]
    return mapping_dir / "contract-binding.yaml"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


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
        if bad_flags:
            rows.append(
                {
                    "command_index": idx,
                    "forbidden_unknown_args": bad_flags,
                    "command_excerpt": block,
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect strict-surface direct validator drift against bundle-runner lineage.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--contract-mapping", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    mapping_path = (
        Path(args.contract_mapping).expanduser().resolve()
        if str(args.contract_mapping or "").strip()
        else _resolve_default_contract_mapping(repo_root)
    )
    forbidden_direct_validators, mapping_errors = _load_forbidden_direct_validators(
        repo_root=repo_root,
        mapping_path=mapping_path,
    )

    missing_surface_files: list[str] = []
    missing_lineage_refs: dict[str, list[str]] = {}
    missing_execution_tokens: dict[str, list[str]] = {}
    forbidden_hits: dict[str, list[str]] = {}
    missing_final_egress_wrapper: list[str] = []
    forbidden_direct_egress_hits: dict[str, list[str]] = {}
    actor_id_passthrough_missing: dict[str, dict[str, list[str]]] = {}
    session_id_passthrough_missing: dict[str, dict[str, list[str]]] = {}
    bundle_arg_contract_missing: dict[str, list[dict[str, Any]]] = {}
    bundle_arg_value_invalid: dict[str, list[dict[str, Any]]] = {}

    for rel in STRICT_SURFACES:
        path = repo_root / rel
        if not path.exists():
            missing_surface_files.append(rel)
            continue
        text = _read_text(path)
        missing = [needle for needle in MANDATORY_LINEAGE_SCRIPTS if needle not in text]
        if missing:
            missing_lineage_refs[rel] = missing
        if rel == WORKFLOW_REQUIRED_GATE_SURFACE:
            missing_exec = [token for token in WORKFLOW_REQUIRED_EXECUTION_TOKENS if token not in text]
            if missing_exec:
                missing_execution_tokens[rel] = missing_exec
        hits = [needle for needle in forbidden_direct_validators if needle in text]
        if hits:
            forbidden_hits[rel] = hits
        if rel in FINAL_EGRESS_REQUIRED_SURFACES and FINAL_EGRESS_WRAPPER_SCRIPT not in text:
            missing_final_egress_wrapper.append(rel)
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
        missing = [needle for needle in MANDATORY_LINEAGE_SCRIPTS if needle not in text]
        if missing:
            missing_lineage_refs[rel] = missing

    if mapping_errors or missing_surface_files:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-001"
    elif missing_lineage_refs or missing_execution_tokens or forbidden_hits:
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
        "contract_mapping": str(mapping_path),
        "mapping_errors": mapping_errors,
        "strict_surfaces": list(STRICT_SURFACES),
        "forbidden_direct_validators": forbidden_direct_validators,
        "missing_surface_files": missing_surface_files,
        "missing_lineage_refs": missing_lineage_refs,
        "missing_execution_tokens": missing_execution_tokens,
        "forbidden_hits": forbidden_hits,
        "final_egress_wrapper_script": FINAL_EGRESS_WRAPPER_SCRIPT,
        "final_egress_required_surfaces": list(FINAL_EGRESS_REQUIRED_SURFACES),
        "missing_final_egress_wrapper": missing_final_egress_wrapper,
        "forbidden_direct_egress_scripts": list(FORBIDDEN_DIRECT_EGRESS_SCRIPTS),
        "forbidden_direct_egress_hits": forbidden_direct_egress_hits,
        "actor_id_required_scripts": list(ACTOR_ID_REQUIRED_SCRIPTS),
        "actor_id_passthrough_missing": actor_id_passthrough_missing,
        "session_id_required_scripts": list(SESSION_ID_REQUIRED_SCRIPTS),
        "session_id_passthrough_missing": session_id_passthrough_missing,
        "bundle_runner_required_args": list(BUNDLE_REQUIRED_ARGS),
        "bundle_arg_contract_missing": bundle_arg_contract_missing,
        "bundle_args_forbid_unknown": list(BUNDLE_ARGS_FORBID_UNKNOWN),
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
