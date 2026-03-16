#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_DRIFT_DETECTED = "IP-SDRIFT-001"
ERR_SKILL_MISSING = "IP-SDRIFT-002"
ERR_SKILL_PATH_DEPENDENCY = "IP-SDRIFT-003"

STRICT_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "scan",
    "three-plane",
    "inspection",
    "mutation",
}

CONTRACT_KEYS = (
    "skill_sync_drift_guard_contract_v1",
    "skill_sync_drift_guard_contract",
    "rq_041_skill_sync_drift_guard_contract_v1",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog_doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    rows = catalog_doc.get("identities")
    if not isinstance(rows, list):
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("id", "")).strip() != identity_id:
            continue
        profile = str(row.get("profile", "")).strip().lower()
        runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
        return profile == "fixture" or runtime_mode == "demo_only"
    return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_skill_path_integrity(*, catalog: Path, identity_id: str, operation: str) -> tuple[int, dict[str, Any], str]:
    cmd = [
        "python3",
        "scripts/validate_skill_path_integrity.py",
        "--catalog",
        str(catalog),
        "--identity-id",
        identity_id,
        "--operation",
        operation,
        "--json-only",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    raw = (proc.stdout or "").strip()
    payload: dict[str, Any] = {}
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                payload = data
        except Exception:
            payload = {}
    tail = ""
    if raw:
        tail = raw.splitlines()[-1]
    elif (proc.stderr or "").strip():
        tail = (proc.stderr or "").strip().splitlines()[-1]
    return proc.returncode, payload, tail


def _skill_candidates(skill_id: str, roots: list[Path]) -> list[Path]:
    names = [skill_id]
    if skill_id.startswith("identity-"):
        names.append(skill_id.replace("identity-", "skill-", 1))
    rows: list[Path] = []
    for root in roots:
        for name in names:
            rows.append((root / name / "SKILL.md").resolve())
            rows.append((root / ".system" / name / "SKILL.md").resolve())
    dedup: list[Path] = []
    seen: set[str] = set()
    for row in rows:
        key = row.as_posix()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return dedup


def _resolve_roots(skill_payload: dict[str, Any], contract: dict[str, Any]) -> list[Path]:
    rows: list[Path] = []
    for raw in skill_payload.get("allowed_skill_roots") or []:
        token = str(raw).strip()
        if token:
            rows.append(Path(token).expanduser().resolve())

    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
    default_roots = [
        codex_home / "skills",
        codex_home / ".identity" / "skills",
    ]
    for root in default_roots:
        rows.append(root.resolve())

    rendered_roots = contract.get("sync_roots")
    if isinstance(rendered_roots, list):
        active_repo_root = str(skill_payload.get("active_repo_root", "")).strip()
        active_runtime_root = str(skill_payload.get("active_runtime_root", "")).strip()
        for raw in rendered_roots:
            token = str(raw).strip()
            if not token:
                continue
            token = token.replace("{active_repo_root}", active_repo_root)
            token = token.replace("{active_runtime_root}", active_runtime_root)
            token = token.replace("{codex_home}", str(codex_home))
            rows.append(Path(token).expanduser().resolve())

    dedup: list[Path] = []
    seen: set[str] = set()
    for row in rows:
        key = row.as_posix()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return dedup


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate skill sync drift guard contract (RQ-041).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required = contract_required(contract)
    if args.force_required:
        required = True

    fixture_identity = _is_fixture_identity(catalog_path, args.identity_id)
    if fixture_identity:
        required = False

    rc_skill, skill_payload, skill_tail = _run_skill_path_integrity(
        catalog=catalog_path,
        identity_id=args.identity_id,
        operation=args.operation,
    )
    skill_status = str(skill_payload.get("path_integrity_status", "")).strip().upper()
    required_skills = list(skill_payload.get("required_skills") or []) if isinstance(skill_payload.get("required_skills"), list) else []

    allow_missing_skills = bool(contract.get("allow_missing_skills", False))
    drift_roots = _resolve_roots(skill_payload, contract)

    skill_sync_rows: list[dict[str, Any]] = []
    drift_skills: list[str] = []
    missing_skills: list[str] = []

    for skill_id in required_skills:
        candidates = _skill_candidates(str(skill_id), drift_roots)
        existing = [p for p in candidates if p.exists() and p.is_file()]
        hash_to_paths: dict[str, list[str]] = {}
        for path in existing:
            digest = _sha256(path)
            hash_to_paths.setdefault(digest, []).append(path.as_posix())

        if not existing:
            missing_skills.append(str(skill_id))

        if len(hash_to_paths.keys()) > 1:
            drift_skills.append(str(skill_id))

        skill_sync_rows.append(
            {
                "skill": str(skill_id),
                "candidate_count": len(candidates),
                "existing_count": len(existing),
                "hash_variants": len(hash_to_paths.keys()),
                "hash_to_paths": hash_to_paths,
            }
        )

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "fixture_identity": fixture_identity,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": True,
        "requiredization_current_round_linked": bool(required_skills),
        "skill_sync_drift_guard_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "allow_missing_skills": allow_missing_skills,
        "required_skill_count": len(required_skills),
        "required_skills": required_skills,
        "drift_roots": [x.as_posix() for x in drift_roots],
        "skill_sync_rows": skill_sync_rows,
        "drift_skills": drift_skills,
        "missing_skills": missing_skills,
        "skill_path_integrity": {
            "status": skill_status,
            "rc": rc_skill,
            "tail": skill_tail,
            "stale_reasons": list(skill_payload.get("stale_reasons") or []) if isinstance(skill_payload.get("stale_reasons"), list) else [],
        },
        "evidence_ref": str(task_path),
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["fixture_profile_scope"] if fixture_identity else ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if rc_skill != 0 or skill_status != STATUS_PASS_REQUIRED:
        payload["skill_sync_drift_guard_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SKILL_PATH_DEPENDENCY
        payload["stale_reasons"] = ["skill_path_integrity_not_pass_required"]
        _emit(payload, json_only=args.json_only)
        return 1

    if missing_skills and not allow_missing_skills:
        payload["skill_sync_drift_guard_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SKILL_MISSING
        payload["stale_reasons"] = ["required_skill_missing_in_sync_roots"]
        _emit(payload, json_only=args.json_only)
        return 1

    if drift_skills:
        payload["skill_sync_drift_guard_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_DRIFT_DETECTED
        payload["stale_reasons"] = ["skill_sync_drift_detected"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["skill_sync_drift_guard_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
