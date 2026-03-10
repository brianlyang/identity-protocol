#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

REQ_KEYS = [
    "required",
    "required_workflows",
    "required_job",
    "required_validator_set_label",
    "required_validators",
    "candidate_validators_v1_2",
    "required_checks",
    "freshness_gate",
]
DELEGATED_SHELL_SCRIPT_RE = re.compile(r"""(?:^|[\s;|&])(?:bash|sh)\s+["']?([A-Za-z0-9_./-]+\.sh)["']?""")


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _collect_delegated_script_paths(text: str) -> list[str]:
    rows: list[str] = []
    for m in DELEGATED_SHELL_SCRIPT_RE.finditer(str(text or "")):
        token = str(m.group(1) or "").strip()
        if not token:
            continue
        if not token.startswith("scripts/"):
            continue
        if token not in rows:
            rows.append(token)
    return rows


def _collect_workflow_reference_texts(
    *,
    repo_root: Path,
    workflow_text: str,
    reusable_text: str,
) -> tuple[list[str], list[str]]:
    """
    Collect searchable texts for validator reference checks:
    workflow file -> reusable workflow -> delegated shell scripts.
    """
    texts: list[str] = [str(workflow_text or "")]
    pending: list[str] = _collect_delegated_script_paths(workflow_text)
    if reusable_text:
        texts.append(reusable_text)
        pending.extend(_collect_delegated_script_paths(reusable_text))

    missing_scripts: list[str] = []
    visited: set[str] = set()
    while pending:
        rel = str(pending.pop(0) or "").strip()
        if not rel or rel in visited:
            continue
        visited.add(rel)
        script_path = (repo_root / rel).resolve()
        if not script_path.exists():
            missing_scripts.append(rel)
            continue
        body = script_path.read_text(encoding="utf-8")
        texts.append(body)
        for nested in _collect_delegated_script_paths(body):
            if nested not in visited:
                pending.append(nested)

    return texts, missing_scripts


def _resolve_current_task(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p
    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate CI enforcement contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate ci enforcement for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    task = _load_json(task_path)
    c = task.get("ci_enforcement_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing ci_enforcement_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        print(f"[FAIL] ci_enforcement_contract missing fields: {missing}")
        return 1

    if c.get("required") is not True:
        print("[FAIL] ci_enforcement_contract.required must be true")
        return 1

    rc = 0
    repo_root = Path(".").resolve()
    wf_dir = Path('.github/workflows')
    required_job = str(c.get("required_job"))
    validators = c.get("required_validators") or []
    candidate = c.get("candidate_validators_v1_2") or []
    if not isinstance(candidate, list):
        print("[FAIL] candidate_validators_v1_2 must be list")
        rc = 1
    if not str(c.get("required_validator_set_label", "")).strip():
        print("[FAIL] required_validator_set_label must be non-empty")
        rc = 1

    reusable_path = (wf_dir / "_identity-required-gates.yml").resolve()
    reusable_text = _read_text_if_exists(reusable_path)

    for wf in c.get("required_workflows") or []:
        wf_path = wf_dir / f"{wf}.yml"
        if not wf_path.exists():
            print(f"[FAIL] required workflow file missing: {wf_path}")
            rc = 1
            continue
        text = wf_path.read_text(encoding="utf-8")
        if f"{required_job}:" not in text:
            print(f"[FAIL] workflow {wf_path} missing job: {required_job}")
            rc = 1
        uses_reusable = "uses: ./.github/workflows/_identity-required-gates.yml" in text
        if uses_reusable and not reusable_text:
            print(f"[FAIL] workflow {wf_path} references reusable required-gates workflow but {reusable_path} is missing")
            rc = 1
        searchable_texts, missing_delegates = _collect_workflow_reference_texts(
            repo_root=repo_root,
            workflow_text=text,
            reusable_text=reusable_text if uses_reusable else "",
        )
        for rel in missing_delegates:
            print(f"[FAIL] workflow {wf_path} delegated script missing: {rel}")
            rc = 1
        for v in validators:
            if any(v in block for block in searchable_texts):
                continue
            print(f"[FAIL] workflow {wf_path} missing validator call reference: {v}")
            rc = 1

    fg = c.get("freshness_gate") or {}
    if int(fg.get("handoff_logs_max_age_days", 0)) <= 0:
        print("[FAIL] freshness_gate.handoff_logs_max_age_days must be >0")
        rc = 1
    if int(fg.get("route_metrics_max_age_days", 0)) <= 0:
        print("[FAIL] freshness_gate.route_metrics_max_age_days must be >0")
        rc = 1

    checks = c.get("required_checks") or []
    if not any("protocol-ci / required-gates" == x for x in checks):
        print("[FAIL] required_checks must include protocol-ci / required-gates")
        rc = 1
    if not any("identity-protocol-ci / required-gates" == x for x in checks):
        print("[FAIL] required_checks must include identity-protocol-ci / required-gates")
        rc = 1

    overlap = sorted(set(validators).intersection(set(candidate)))
    if overlap:
        print(f"[FAIL] required_validators overlaps candidate_validators_v1_2: {overlap}")
        rc = 1

    if rc:
        return 1

    print("CI enforcement contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
