#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_identity(catalog_path: Path, identity_id: str) -> dict[str, Any]:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    return target


def _all_identity_tokens(catalog_path: Path) -> list[str]:
    catalog = _load_yaml(catalog_path)
    rows = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    out: list[str] = []
    for r in rows:
        iid = str(r.get("id", "")).strip()
        if not iid:
            continue
        out.append(iid.replace("-", "_"))
    return out


def _has_token(text: str, token: str) -> bool:
    # token match must align on underscore boundaries, not substring noise.
    return re.search(rf"(^|_){re.escape(token)}(_|$)", text) is not None


def _resolve_task_path(identity: dict[str, Any], identity_id: str) -> Path:
    pack_path = str((identity or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p
    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity={identity_id}")


def _resolve_pack_root(identity: dict[str, Any]) -> Path | None:
    pack_path = str((identity or {}).get("pack_path", "")).strip()
    if not pack_path:
        return None
    return Path(pack_path).expanduser().resolve()


def _resolve_runtime_pattern(pattern: str, pack_root: Path | None, identity_id: str) -> str:
    if not pattern:
        return pattern
    local_prefix = f"identity/runtime/local/{identity_id}/"
    if pattern.startswith(local_prefix) and pack_root is not None:
        return str((pack_root / "runtime" / pattern[len(local_prefix) :]).as_posix())
    if pattern.startswith("identity/runtime/") and pack_root is not None:
        return str((pack_root / "runtime" / pattern[len("identity/runtime/") :]).as_posix())
    return pattern


def _resolve_latest_evidence(pattern: str, identity_id: str, explicit: str, pack_root: Path | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    pattern = _resolve_runtime_pattern(pattern, pack_root, identity_id).replace("<identity-id>", identity_id)
    if Path(pattern).is_absolute():
        files = sorted((Path(p) for p in glob.glob(pattern)), key=lambda p: p.stat().st_mtime)
    else:
        files = sorted(Path(".").glob(pattern), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    scoped = [p for p in files if identity_id in p.name]
    return (sorted(scoped, key=lambda p: p.stat().st_mtime)[-1] if scoped else files[-1])


def _parse_utc(ts: str) -> datetime | None:
    value = str(ts or "").strip()
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity role-binding contract and activation switch guards")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--evidence", default="", help="optional explicit role-binding evidence json path")
    args = ap.parse_args()

    identity_id = args.identity_id.strip()
    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 1

    try:
        identity = _resolve_identity(catalog_path, identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    try:
        task_path = _resolve_task_path(identity, identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    task = _load_json(task_path)
    gates = task.get("gates") or {}
    if gates.get("role_binding_gate") != "required":
        print("[FAIL] gates.role_binding_gate must be required")
        return 1
    print("[OK] gates.role_binding_gate=required")

    contract = task.get("identity_role_binding_contract") or {}
    if not isinstance(contract, dict) or not contract:
        print("[FAIL] missing identity_role_binding_contract")
        return 1

    required_fields = [
        "required",
        "role_type",
        "catalog_registration_required",
        "runtime_bootstrap_pass_required",
        "runtime_bootstrap_live_revalidate",
        "activation_policy",
        "switch_guard_required",
        "evidence_max_age_days",
        "active_binding_status_required",
        "binding_evidence_path_pattern",
        "enforcement_validator",
    ]
    missing = [k for k in required_fields if k not in contract]
    if missing:
        print(f"[FAIL] identity_role_binding_contract missing fields: {missing}")
        return 1
    if contract.get("required") is not True:
        print("[FAIL] identity_role_binding_contract.required must be true")
        return 1
    if str(contract.get("enforcement_validator", "")).strip() != "scripts/validate_identity_role_binding.py":
        print("[FAIL] identity_role_binding_contract.enforcement_validator mismatch")
        return 1
    if int(contract.get("evidence_max_age_days", 0)) <= 0:
        print("[FAIL] identity_role_binding_contract.evidence_max_age_days must be > 0")
        return 1
    role_type = str(contract.get("role_type", "")).strip()
    if not role_type.endswith("_runtime_operator"):
        print("[FAIL] identity_role_binding_contract.role_type must end with _runtime_operator")
        return 1
    self_token = identity_id.replace("-", "_")
    all_tokens = _all_identity_tokens(catalog_path)
    foreign_hits = [t for t in all_tokens if t != self_token and _has_token(role_type, t)]
    if foreign_hits:
        print(
            "[FAIL] identity_role_binding_contract.role_type contains foreign identity token(s): "
            f"identity={identity_id}, role_type={role_type}, foreign_tokens={foreign_hits}"
        )
        return 1

    if bool(contract.get("catalog_registration_required", False)):
        # resolve_identity already proved registration exists
        print("[OK] catalog registration present")

    evidence = _resolve_latest_evidence(
        str(contract.get("binding_evidence_path_pattern", "")),
        identity_id,
        args.evidence,
        _resolve_pack_root(identity),
    )
    if not evidence:
        print("[FAIL] role-binding evidence not found")
        return 1

    data = _load_json(evidence)
    print(f"[OK] role-binding evidence: {evidence}")
    req_evidence_fields = [
        "binding_id",
        "generated_at",
        "identity_id",
        "role_type",
        "binding_status",
        "runtime_bootstrap",
        "switch_guard",
    ]
    missing_ev = [k for k in req_evidence_fields if k not in data]
    if missing_ev:
        print(f"[FAIL] role-binding evidence missing fields: {missing_ev}")
        return 1
    if str(data.get("identity_id", "")).strip() != identity_id:
        print("[FAIL] role-binding evidence identity_id mismatch")
        return 1
    if str(data.get("role_type", "")).strip() != role_type:
        print("[FAIL] role-binding evidence role_type mismatch with contract")
        return 1
    binding_status = str(data.get("binding_status", "")).strip()
    if binding_status not in {"BOUND_READY", "BOUND_ACTIVE"}:
        print("[FAIL] role-binding evidence binding_status must be BOUND_READY or BOUND_ACTIVE")
        return 1
    generated = _parse_utc(str(data.get("generated_at", "")).strip())
    if not generated:
        print("[FAIL] role-binding evidence generated_at must be valid ISO-8601 timestamp")
        return 1
    age_days = (datetime.now(timezone.utc) - generated).total_seconds() / 86400.0
    if age_days > float(contract.get("evidence_max_age_days", 7)):
        print(
            "[FAIL] role-binding evidence is stale: "
            f"age_days={age_days:.2f} > max_age_days={contract.get('evidence_max_age_days')}"
        )
        return 1

    if bool(contract.get("runtime_bootstrap_pass_required", False)):
        bootstrap = data.get("runtime_bootstrap") or {}
        if not isinstance(bootstrap, dict):
            print("[FAIL] role-binding evidence runtime_bootstrap must be object")
            return 1
        if bootstrap.get("status") != "PASS":
            print("[FAIL] runtime_bootstrap.status must be PASS")
            return 1
        validator = str(bootstrap.get("validator", "")).strip()
        if validator != "scripts/validate_identity_runtime_contract.py":
            print("[FAIL] runtime_bootstrap.validator must be scripts/validate_identity_runtime_contract.py")
            return 1
        if bool(contract.get("runtime_bootstrap_live_revalidate", False)):
            rc, out, err = _run(
                [
                    "python3",
                    "scripts/validate_identity_runtime_contract.py",
                    "--catalog",
                    str(catalog_path),
                    "--identity-id",
                    identity_id,
                ]
            )
            if rc != 0:
                print("[FAIL] runtime bootstrap live revalidation failed")
                if out:
                    print(out)
                if err:
                    print(err)
                return 1
            print("[OK] runtime bootstrap live revalidation passed")
        print("[OK] runtime bootstrap pass evidence validated")

    if bool(contract.get("switch_guard_required", False)):
        switch = data.get("switch_guard") or {}
        if not isinstance(switch, dict):
            print("[FAIL] role-binding evidence switch_guard must be object")
            return 1
        if switch.get("status") != "PASS":
            print("[FAIL] switch_guard.status must be PASS")
            return 1

        # promotion protection: active/default identities must be bound-ready or higher.
        identity_status = str((identity or {}).get("status", "")).strip().lower()
        catalog = _load_yaml(catalog_path)
        default_identity = str(catalog.get("default_identity", "")).strip()
        promotion_target = identity_status == "active" or default_identity == identity_id
        required_active_status = str(contract.get("active_binding_status_required", "")).strip() or "BOUND_ACTIVE"
        if promotion_target and binding_status != required_active_status:
            print(
                "[FAIL] active/default identity must have binding status "
                f"{required_active_status}, got={binding_status}"
            )
            return 1
        print("[OK] switch guard validated")

    print("Identity role-binding validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
