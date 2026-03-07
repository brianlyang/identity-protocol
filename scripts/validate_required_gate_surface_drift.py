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

BUNDLE_RUNNER_SCRIPT = "scripts/required_gate_bundle_runner.py"
RECURRENCE_ESCALATOR_SCRIPT = "scripts/validate_required_gate_recurrence_escalator.py"
TUPLE_PARITY_SCRIPT = "scripts/validate_required_gate_tuple_parity.py"
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
)

VERSIONED_SCRIPT_ALIAS_RE = re.compile(r"^(?P<prefix>validate|normalize|emit)_v\d+_(?P<tail>.+)\.py$")
WRAPPER_MAIN_IMPORT_RE = re.compile(r"^\s*from\s+([A-Za-z0-9_.]+)\s+import\s+main\s*$", re.MULTILINE)


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
    forbidden_hits: dict[str, list[str]] = {}

    for rel in STRICT_SURFACES:
        path = repo_root / rel
        if not path.exists():
            missing_surface_files.append(rel)
            continue
        text = _read_text(path)
        missing = [needle for needle in MANDATORY_LINEAGE_SCRIPTS if needle not in text]
        if missing:
            missing_lineage_refs[rel] = missing
        hits = [needle for needle in forbidden_direct_validators if needle in text]
        if hits:
            forbidden_hits[rel] = hits

    if mapping_errors or missing_surface_files:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-001"
    elif missing_lineage_refs or forbidden_hits:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-002"
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
        "forbidden_hits": forbidden_hits,
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
