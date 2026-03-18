#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPO_ROOT.parent if REPO_ROOT.name == "identity-protocol-local" else REPO_ROOT


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json root must be object: {path}")
    return data


def _check_source_contracts() -> list[str]:
    issues: list[str] = []
    identity_creator = (REPO_ROOT / "scripts" / "identity_creator.py").read_text(encoding="utf-8")
    sync_session = (REPO_ROOT / "scripts" / "sync_session_identity.py").read_text(encoding="utf-8")
    required_tokens = {
        "identity_creator_compiled_brief_default": "default=COMPILED_BRIEF_REFRESH_MODE_MANUAL_ONLY",
        "identity_creator_projection_default": "default=COMPATIBILITY_PROJECTION_WRITE_MODE_DISABLED",
        "identity_creator_compile_gate": "compiled_brief_refresh_mode_resolved == COMPILED_BRIEF_REFRESH_MODE_REFRESH_LEGACY",
        "identity_creator_sync_projection_mode": "--compatibility-projection-write-mode",
        "sync_projection_default": "default=COMPATIBILITY_PROJECTION_WRITE_MODE_DISABLED",
        "sync_projection_disabled_reason": "compatibility_projection_write_disabled_by_policy",
        "sync_projection_neutralize": "canonical compatibility pointer neutralized",
    }
    for label, token in required_tokens.items():
        haystack = identity_creator if label.startswith("identity_creator") else sync_session
        if token not in haystack:
            issues.append(f"missing_source_token:{label}")
    return issues


def _copy_runtime_snapshot(*, catalog_path: Path) -> tuple[Path, str, str, str]:
    root = Path(tempfile.mkdtemp(prefix="identity-switch-closure-", dir="/tmp")).resolve()
    actor_store_path = catalog_path.parent / "session" / "actors" / "assistant_codex.json"
    if not actor_store_path.exists():
        raise FileNotFoundError(f"actor store missing: {actor_store_path}")
    for rel in (
        ".identity/catalog.local.yaml",
        ".identity/session/active_identity.json",
        ".identity/session/mirror/current.json",
        ".identity/session/actors/assistant_codex.json",
    ):
        src = PROJECT_ROOT / rel
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    actor_store = _load_json(root / ".identity/session/actors/assistant_codex.json")
    compare_token = str(actor_store.get("compare_token", "")).strip()
    if not compare_token:
        raise ValueError("actor store compare_token missing")
    pointer = _load_json(root / ".identity/session/active_identity.json")
    current_identity = str(pointer.get("identity_id", "")).strip()
    return root, compare_token, "assistant:codex", current_identity


def _write_switch_receipt(
    *,
    temp_root: Path,
    actor_id: str,
    from_identity_id: str,
    to_identity_id: str,
    receipt_name: str,
) -> Path:
    receipt_path = (temp_root / ".identity/session/receipts" / f"{receipt_name}.json").resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            {
                "receipt_id": receipt_name,
                "actor_id": actor_id,
                "from_identity_id": from_identity_id,
                "to_identity_id": to_identity_id,
                "approved_by": "probe:test",
                "approved_at": "2026-03-18T00:00:00Z",
                "reason": "projection_boundary_probe",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return receipt_path


def _choose_alternate_identity(*, catalog_path: Path, current_identity: str) -> str:
    rows = [row for row in (_load_yaml(catalog_path).get("identities") or []) if isinstance(row, dict)]
    active_ids = [
        str(row.get("id", "")).strip()
        for row in rows
        if str(row.get("status", "")).strip().lower() == "active" and str(row.get("id", "")).strip()
    ]
    for identity_id in active_ids:
        if identity_id != current_identity:
            return identity_id
    raise ValueError(f"no alternate active identity found; active_ids={active_ids}")


def _run_sync_probe(
    *,
    temp_root: Path,
    identity_id: str,
    compare_token: str,
    actor_id: str,
    session_id: str,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "python3",
        str(REPO_ROOT / "scripts" / "sync_session_identity.py"),
        "--catalog",
        str((temp_root / ".identity/catalog.local.yaml").resolve()),
        "--identity-id",
        identity_id,
        "--out",
        str((temp_root / ".identity/session/active_identity.json").resolve()),
        "--mirror-out",
        str((temp_root / ".identity/session/mirror/current.json").resolve()),
        "--actor-id",
        actor_id,
        "--run-id",
        session_id.removeprefix("run:"),
        "--session-id",
        session_id,
        "--session-id-source",
        "explicit_session_id",
        "--compare-token",
        compare_token,
        "--mutation-lane",
        "activate",
        "--switch-reason",
        "projection_boundary_probe",
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity switch closure semantics for projection/prompt boundaries.")
    ap.add_argument(
        "--catalog",
        default=str((PROJECT_ROOT / ".identity/catalog.local.yaml").resolve()),
        help="runtime catalog to snapshot for the probe",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    current_pointer = _load_json(catalog_path.parent / "session" / "active_identity.json")
    current_identity = str(current_pointer.get("identity_id", "")).strip()
    source_issues = _check_source_contracts()
    target_identity = _choose_alternate_identity(catalog_path=catalog_path, current_identity=current_identity)

    disabled_root, compare_token, actor_id, disabled_current_identity = _copy_runtime_snapshot(
        catalog_path=catalog_path
    )
    disabled_receipt = _write_switch_receipt(
        temp_root=disabled_root,
        actor_id=actor_id,
        from_identity_id=disabled_current_identity,
        to_identity_id=target_identity,
        receipt_name="projection-boundary-disabled-receipt",
    )
    disabled_probe = _run_sync_probe(
        temp_root=disabled_root,
        identity_id=target_identity,
        compare_token=compare_token,
        actor_id=actor_id,
        session_id="run:projection-boundary-disabled-probe",
        extra_args=[
            "--switch-prestate-mode",
            "session_primary",
            "--switch-from-identity",
            disabled_current_identity,
            "--switch-intent-receipt",
            str(disabled_receipt),
        ],
    )
    disabled_pointer = _load_json(disabled_root / ".identity/session/active_identity.json")

    legacy_root, compare_token_legacy, actor_id_legacy, _ = _copy_runtime_snapshot(catalog_path=catalog_path)
    legacy_probe = _run_sync_probe(
        temp_root=legacy_root,
        identity_id=target_identity,
        compare_token=compare_token_legacy,
        actor_id=actor_id_legacy,
        session_id="run:projection-boundary-legacy-probe",
        extra_args=[
            "--compatibility-projection-write-mode",
            "legacy_actor_global_switch",
        ],
    )

    failures: list[str] = []
    if source_issues:
        failures.extend(source_issues)
    if disabled_probe.returncode != 0:
        failures.append("projection_disabled_probe_failed")
    if str(disabled_pointer.get("identity_id", "")).strip():
        failures.append("projection_disabled_pointer_identity_not_neutralized")
    if str(disabled_pointer.get("compatibility_projection_status", "")).strip() != "UNAVAILABLE":
        failures.append("projection_disabled_pointer_status_not_unavailable")
    if (
        str(disabled_pointer.get("compatibility_projection_write_reason", "")).strip()
        != "compatibility_projection_write_disabled_by_policy"
    ):
        failures.append("projection_disabled_pointer_write_reason_missing")
    if legacy_probe.returncode == 0:
        failures.append("legacy_actor_global_probe_without_receipt_unexpected_pass")
    legacy_text = "\n".join(
        part for part in [legacy_probe.stdout.strip(), legacy_probe.stderr.strip()] if part
    )
    if "IP-ASB-MB-008" not in legacy_text:
        failures.append("legacy_actor_global_probe_missing_receipt_error")

    payload = {
        "identity_switch_closure_status": "PASS_REQUIRED" if not failures else "FAIL_REQUIRED",
        "catalog_path": str(catalog_path),
        "compatibility_pointer_identity_id": current_identity,
        "compatibility_pointer_identity_authority": "diagnostic_only",
        "probe_target_identity_id": target_identity,
        "source_contract_issues": source_issues,
        "disabled_probe": {
            "returncode": int(disabled_probe.returncode),
            "stdout_tail": disabled_probe.stdout.strip().splitlines()[-6:],
            "stderr_tail": disabled_probe.stderr.strip().splitlines()[-6:],
            "pointer_identity_id": str(disabled_pointer.get("identity_id", "")).strip(),
            "pointer_status": str(disabled_pointer.get("status", "")).strip(),
            "compatibility_projection_status": str(
                disabled_pointer.get("compatibility_projection_status", "")
            ).strip(),
            "compatibility_projection_write_reason": str(
                disabled_pointer.get("compatibility_projection_write_reason", "")
            ).strip(),
        },
        "legacy_probe_without_receipt": {
            "returncode": int(legacy_probe.returncode),
            "stdout_tail": legacy_probe.stdout.strip().splitlines()[-6:],
            "stderr_tail": legacy_probe.stderr.strip().splitlines()[-6:],
        },
        "failures": failures,
    }
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
