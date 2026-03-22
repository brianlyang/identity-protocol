#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from identity_codex_launcher_evidence_common import (
    artifact_path,
    launcher_convergence_closure_checker_command,
    launcher_convergence_entry_command,
    launcher_convergence_manifest_notes,
    materialize_launcher_convergence_bundle,
    write_json,
)
from identity_codex_launcher_common import (
    IDENTITY_CODEX_LAUNCHER_CONVERGENCE_ENTRY_ID,
    IDENTITY_CODEX_LAUNCHER_CONVERGENCE_MUTATION_SCOPE,
    IDENTITY_CODEX_LAUNCHER_CONVERGENCE_RECEIPT_FAMILY,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    default_codex_home,
    resolve_catalog_path,
)

ERR_AUTHORITY = "IP-ILAUNCH-CONV-001"
ERR_PRECHECK = "IP-ILAUNCH-CONV-002"
ERR_APPLY = "IP-ILAUNCH-CONV-003"
ERR_POSTCHECK = "IP-ILAUNCH-CONV-004"
WORKSPACE_LOCAL_AUTHORITY_MODE = "workspace_local_runtime_catalog"
EVIDENCE_STREAM = "v1614-identity-codex-launcher"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    if json_only:
        print(text)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _run_json(cmd: list[str], *, env: dict[str, str]) -> tuple[int, dict[str, Any], str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
    stdout = str(proc.stdout or "").strip()
    stderr = str(proc.stderr or "").strip()
    payload: dict[str, Any] = {}
    if stdout:
        try:
            decoded = json.loads(stdout)
            if isinstance(decoded, dict):
                payload = decoded
        except Exception:
            payload = {
                "transport_error": "stdout_not_json",
                "stdout": stdout,
                "stderr": stderr,
            }
    if not payload:
        payload = {
            "transport_error": "stdout_missing",
            "stdout": stdout,
            "stderr": stderr,
        }
    return proc.returncode, payload, stdout, stderr


def _identity_ids_from_rows(rows: Any) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    if not isinstance(rows, list):
        return ordered
    for row in rows:
        if not isinstance(row, dict):
            continue
        identity_id = str(row.get("identity_id", "")).strip()
        if not identity_id or identity_id in seen:
            continue
        seen.add(identity_id)
        ordered.append(identity_id)
    return ordered


def _resolve_workspace_runtime_context(*, catalog_path: Path, repo_catalog: Path) -> Path:
    if catalog_path.resolve() == repo_catalog.resolve():
        raise RuntimeError(
            "repository fixture catalog is forbidden for launcher convergence; use a workspace-local runtime catalog"
        )
    if catalog_path.name != "catalog.local.yaml":
        raise RuntimeError(
            f"workspace-local runtime catalog required; expected catalog.local.yaml, got {catalog_path.name}"
        )
    identity_home = catalog_path.parent
    if identity_home.name != ".identity":
        raise RuntimeError(
            f"workspace-local runtime catalog required under .identity/, got parent {identity_home.name}"
        )
    workspace_root = identity_home.parent.resolve()
    if not workspace_root.exists() or not workspace_root.is_dir():
        raise RuntimeError(f"workspace root unavailable for runtime catalog: {workspace_root}")
    return workspace_root


def _artifact_dir(*, workspace_root: Path, now: datetime) -> Path:
    return (
        workspace_root
        / "activity"
        / "evidence"
        / EVIDENCE_STREAM
        / now.strftime("%Y-%m-%d")
    ).resolve()


def _artifact_path(root: Path, stem: str, run_token: str) -> Path:
    return artifact_path(root, stem, run_token)


def _launcher_env(*, repo_root: Path, catalog_path: Path, codex_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    identity_home = (codex_home / ".identity").resolve()
    env["CODEX_HOME"] = str(codex_home)
    env["IDENTITY_HOME"] = str(identity_home)
    env["IDENTITY_CATALOG"] = str(catalog_path)
    env["IDENTITY_PROTOCOL_HOME"] = str(repo_root)
    return env


def _check_launcher_closure(*, repo_root: Path, catalog_path: Path, env: dict[str, str]) -> tuple[int, dict[str, Any]]:
    cmd = _launcher_closure_command(repo_root=repo_root, catalog_path=catalog_path)
    rc, payload, _, _ = _run_json(cmd, env=env)
    return rc, payload


def _launcher_closure_command(*, repo_root: Path, catalog_path: Path) -> list[str]:
    return launcher_convergence_closure_checker_command(repo_root=repo_root, catalog_path=catalog_path)


def _validate_single_identity(
    *, repo_root: Path, catalog_path: Path, identity_id: str, codex_home: Path, env: dict[str, str]
) -> tuple[int, dict[str, Any]]:
    cmd = [
        "python3",
        str((repo_root / "scripts" / "validate_identity_codex_launcher.py").resolve()),
        "--catalog",
        str(catalog_path),
        "--identity-id",
        identity_id,
        "--bin-dir",
        str((codex_home / "bin").resolve()),
        "--require-installed",
        "--json-only",
    ]
    rc, payload, _, _ = _run_json(cmd, env=env)
    return rc, payload


def _apply_repair_for_identity(
    *, repo_root: Path, catalog_path: Path, identity_id: str, codex_home: Path, env: dict[str, str]
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "identity_id": identity_id,
        "mutation_scope": IDENTITY_CODEX_LAUNCHER_CONVERGENCE_MUTATION_SCOPE,
        "backfill_status": "",
        "backfill_changed": False,
        "backfill_evidence_ref": "",
        "install_status": "",
        "install_contract_changed": False,
        "install_manifest_changed": False,
        "install_readme_changed": False,
        "install_generic_changed": False,
        "install_shortcut_changed": False,
        "install_runtime_paths_env": "",
        "validator_status": "",
        "validator_stale_reasons": [],
        "final_status": STATUS_FAIL_REQUIRED,
    }

    backfill_cmd = [
        "python3",
        str((repo_root / "scripts" / "repair_contract_backfill.py").resolve()),
        "--catalog",
        str(catalog_path),
        "--identity-id",
        identity_id,
        "--apply",
        "--json-only",
    ]
    rc_backfill, backfill_payload, _, _ = _run_json(backfill_cmd, env=env)
    result["backfill_status"] = str(backfill_payload.get("contract_backfill_status", "")).strip().upper()
    result["backfill_changed"] = bool(backfill_payload.get("changed", False))
    result["backfill_evidence_ref"] = str(backfill_payload.get("evidence_ref", "")).strip()
    if rc_backfill != 0 or result["backfill_status"] != STATUS_PASS_REQUIRED:
        result["final_status"] = STATUS_FAIL_REQUIRED
        return result

    install_cmd = [
        "python3",
        str((repo_root / "scripts" / "install_identity_codex_launcher.py").resolve()),
        "--catalog",
        str(catalog_path),
        "--identity-id",
        identity_id,
        "--bin-dir",
        str((codex_home / "bin").resolve()),
        "--identity-home",
        str((codex_home / ".identity").resolve()),
        "--protocol-home",
        str(repo_root),
        "--json-only",
    ]
    rc_install, install_payload, _, _ = _run_json(install_cmd, env=env)
    result["install_status"] = str(install_payload.get("status", "")).strip().upper()
    result["install_contract_changed"] = bool(install_payload.get("contract_changed", False))
    result["install_manifest_changed"] = bool(install_payload.get("manifest_changed", False))
    result["install_readme_changed"] = bool(install_payload.get("readme_changed", False))
    result["install_generic_changed"] = bool(install_payload.get("generic_changed", False))
    result["install_shortcut_changed"] = bool(install_payload.get("shortcut_changed", False))
    result["install_runtime_paths_env"] = str(install_payload.get("runtime_paths_env", "")).strip()
    if rc_install != 0 or result["install_status"] != STATUS_PASS_REQUIRED:
        result["final_status"] = STATUS_FAIL_REQUIRED
        return result

    rc_validate, validate_payload = _validate_single_identity(
        repo_root=repo_root,
        catalog_path=catalog_path,
        identity_id=identity_id,
        codex_home=codex_home,
        env=env,
    )
    result["validator_status"] = str(validate_payload.get("identity_codex_launcher_status", "")).strip().upper()
    stale_reasons = validate_payload.get("stale_reasons")
    result["validator_stale_reasons"] = (
        [str(item).strip() for item in stale_reasons if str(item).strip()]
        if isinstance(stale_reasons, list)
        else []
    )
    result["final_status"] = (
        STATUS_PASS_REQUIRED if rc_validate == 0 and result["validator_status"] == STATUS_PASS_REQUIRED else STATUS_FAIL_REQUIRED
    )
    return result


def _entry_command(
    *,
    repo_root: Path,
    catalog_path: Path,
    mode: str,
    codex_home: Path,
    artifact_root: Path,
    run_token: str,
    receipt_out: Path,
) -> list[str]:
    return launcher_convergence_entry_command(
        repo_root=repo_root,
        catalog_path=catalog_path,
        mode=mode,
        codex_home=codex_home,
        artifact_root=artifact_root,
        run_token=run_token,
        receipt_path=receipt_out,
    )


def _finalize_bundle(
    *,
    workspace_root: Path,
    artifact_root: Path,
    receipt_out: Path,
    run_token: str,
    payload: dict[str, Any],
    generated_at: str,
    mode: str,
    catalog_path: Path,
    precheck_out: Path,
    precheck_rc: int,
    precheck_timestamp: str,
    precheck_cmd: list[str],
    entry_cmd: list[str],
    entry_rc: int,
    postcheck_out: Path | None = None,
    postcheck_rc: int | None = None,
    postcheck_timestamp: str = "",
    postcheck_cmd: list[str] | None = None,
) -> None:
    evidence_records = [
        {
            "kind": "launcher_convergence_receipt",
            "path": str(receipt_out),
            "command": entry_cmd,
            "rc": int(entry_rc),
            "timestamp": generated_at,
            "use_prepared_receipt_payload": True,
        },
        {
            "kind": "launcher_convergence_precheck",
            "path": str(precheck_out),
            "command": precheck_cmd,
            "rc": int(precheck_rc),
            "timestamp": precheck_timestamp,
        },
    ]
    if postcheck_out is not None and postcheck_cmd is not None and postcheck_rc is not None:
        evidence_records.append(
            {
                "kind": "launcher_convergence_postcheck",
                "path": str(postcheck_out),
                "command": postcheck_cmd,
                "rc": int(postcheck_rc),
                "timestamp": str(postcheck_timestamp or generated_at).strip(),
            }
        )
    next_payload, manifest_out, _manifest_payload = materialize_launcher_convergence_bundle(
        workspace_root=workspace_root,
        artifact_root=artifact_root,
        receipt_path=receipt_out,
        run_token=run_token,
        generated_at=generated_at,
        mode=mode,
        catalog_path=catalog_path,
        entry_id=IDENTITY_CODEX_LAUNCHER_CONVERGENCE_ENTRY_ID,
        receipt_family=IDENTITY_CODEX_LAUNCHER_CONVERGENCE_RECEIPT_FAMILY,
        receipt_payload=payload,
        evidence_record_inputs=evidence_records,
        notes=launcher_convergence_manifest_notes(),
    )
    payload.clear()
    payload.update(next_payload)
    payload["manifest_ref"] = str(manifest_out)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run the canonical workspace-level identity Codex launcher convergence entry."
    )
    ap.add_argument("--catalog", default="", help="workspace-local runtime catalog (defaults to local runtime resolution)")
    ap.add_argument("--mode", choices=["dry-run", "apply"], default="dry-run")
    ap.add_argument("--codex-home", default="", help="optional CODEX_HOME override for launcher install/recheck")
    ap.add_argument(
        "--artifact-root",
        default="",
        help="optional artifact root override; defaults to activity/evidence/v1614-identity-codex-launcher/<date>",
    )
    ap.add_argument("--run-token", default="", help="optional artifact token suffix")
    ap.add_argument("--out", default="", help="optional explicit receipt output path")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    repo_catalog = (repo_root / "identity" / "catalog" / "identities.yaml").resolve()
    now = datetime.now(timezone.utc)
    run_token = str(args.run_token or "").strip() or f"launcher-convergence-{int(now.timestamp())}"
    catalog_path = resolve_catalog_path(str(args.catalog or ""))

    base_payload: dict[str, Any] = {
        "entry_id": IDENTITY_CODEX_LAUNCHER_CONVERGENCE_ENTRY_ID,
        "receipt_family": IDENTITY_CODEX_LAUNCHER_CONVERGENCE_RECEIPT_FAMILY,
        "mode": str(args.mode),
        "workspace_catalog_authority_mode": WORKSPACE_LOCAL_AUTHORITY_MODE,
        "catalog_path": str(catalog_path),
        "repo_root": str(repo_root),
        "repo_catalog": str(repo_catalog),
        "run_token": run_token,
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "mutation_scope": IDENTITY_CODEX_LAUNCHER_CONVERGENCE_MUTATION_SCOPE,
        "mutation_applied": False,
        "repair_status": "",
        "checked_identity_ids": [],
        "planned_repair_identity_ids": [],
        "repaired_identity_ids": [],
        "remaining_violation_ids": [],
        "repair_results": [],
        "precheck_evidence_ref": "",
        "postcheck_evidence_ref": "",
        "evidence_ref": "",
        "manifest_ref": "",
        "stale_reasons": [],
    }

    try:
        workspace_root = _resolve_workspace_runtime_context(catalog_path=catalog_path, repo_catalog=repo_catalog)
    except RuntimeError as exc:
        payload = dict(base_payload)
        payload.update(
            {
                "workspace_root": "",
                "status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_AUTHORITY,
                "repair_status": "authority_rejected",
                "stale_reasons": [str(exc)],
            }
        )
        _emit(payload, json_only=args.json_only)
        return 1

    codex_home = Path(str(args.codex_home or "")).expanduser().resolve() if str(args.codex_home or "").strip() else default_codex_home()
    artifact_root = (
        Path(str(args.artifact_root or "")).expanduser().resolve()
        if str(args.artifact_root or "").strip()
        else _artifact_dir(workspace_root=workspace_root, now=now)
    )
    receipt_out = Path(args.out).expanduser().resolve() if str(args.out or "").strip() else _artifact_path(
        artifact_root,
        "launcher_convergence_receipt",
        run_token,
    )
    precheck_out = _artifact_path(artifact_root, "launcher_convergence_precheck", run_token)
    postcheck_out = _artifact_path(artifact_root, "launcher_convergence_postcheck", run_token)
    env = _launcher_env(repo_root=repo_root, catalog_path=catalog_path, codex_home=codex_home)
    precheck_cmd = _launcher_closure_command(repo_root=repo_root, catalog_path=catalog_path)
    entry_cmd = _entry_command(
        repo_root=repo_root,
        catalog_path=catalog_path,
        mode=str(args.mode),
        codex_home=codex_home,
        artifact_root=artifact_root,
        run_token=run_token,
        receipt_out=receipt_out,
    )

    precheck_rc, precheck_payload = _check_launcher_closure(repo_root=repo_root, catalog_path=catalog_path, env=env)
    write_json(precheck_out, precheck_payload)
    precheck_timestamp = datetime.fromtimestamp(precheck_out.stat().st_mtime, tz=timezone.utc).isoformat().replace(
        "+00:00",
        "Z",
    )

    checked_rows = precheck_payload.get("checked_rows") if isinstance(precheck_payload, dict) else []
    violation_rows = precheck_payload.get("violations") if isinstance(precheck_payload, dict) else []
    checked_identity_ids = _identity_ids_from_rows(checked_rows)
    violation_ids = _identity_ids_from_rows(violation_rows)

    payload = dict(base_payload)
    payload.update(
        {
            "workspace_root": str(workspace_root),
            "codex_home": str(codex_home),
            "artifact_root": str(artifact_root),
            "precheck_evidence_ref": str(precheck_out),
            "checked_identity_ids": checked_identity_ids,
            "checked_identity_count": len(checked_identity_ids),
            "planned_repair_identity_ids": violation_ids,
            "planned_repair_count": len(violation_ids),
            "precheck_status": str(precheck_payload.get("identity_codex_launcher_migration_closure_status", "")).strip().upper(),
            "precheck_violation_count": len(violation_ids),
        }
    )

    if not isinstance(precheck_payload, dict) or not payload["precheck_status"]:
        payload.update(
            {
                "status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_PRECHECK,
                "repair_status": "precheck_transport_failed",
                "stale_reasons": ["launcher_migration_precheck_transport_failed"],
            }
        )
        _finalize_bundle(
            workspace_root=workspace_root,
            artifact_root=artifact_root,
            receipt_out=receipt_out,
            run_token=run_token,
            payload=payload,
            generated_at=base_payload["generated_at"],
            mode=str(args.mode),
            catalog_path=catalog_path,
            precheck_out=precheck_out,
            precheck_rc=precheck_rc,
            precheck_timestamp=precheck_timestamp,
            precheck_cmd=precheck_cmd,
            entry_cmd=entry_cmd,
            entry_rc=1,
        )
        _emit(payload, json_only=args.json_only)
        return 1

    if args.mode == "dry-run":
        payload.update(
            {
                "status": STATUS_PASS_REQUIRED if not violation_ids else STATUS_FAIL_REQUIRED,
                "error_code": "" if not violation_ids else ERR_POSTCHECK,
                "repair_status": "dry_run_preview" if violation_ids else "already_converged",
                "remaining_violation_ids": violation_ids,
                "remaining_violation_count": len(violation_ids),
                "postcheck_status": "NOT_RUN_DRY_RUN",
                "stale_reasons": [] if not violation_ids else ["launcher_migration_closure_pending_apply"],
            }
        )
        _finalize_bundle(
            workspace_root=workspace_root,
            artifact_root=artifact_root,
            receipt_out=receipt_out,
            run_token=run_token,
            payload=payload,
            generated_at=base_payload["generated_at"],
            mode=str(args.mode),
            catalog_path=catalog_path,
            precheck_out=precheck_out,
            precheck_rc=precheck_rc,
            precheck_timestamp=precheck_timestamp,
            precheck_cmd=precheck_cmd,
            entry_cmd=entry_cmd,
            entry_rc=0 if payload["status"] == STATUS_PASS_REQUIRED else 1,
        )
        _emit(payload, json_only=args.json_only)
        return 0 if payload["status"] == STATUS_PASS_REQUIRED else 1

    if not violation_ids:
        write_json(postcheck_out, precheck_payload)
        postcheck_timestamp = datetime.fromtimestamp(postcheck_out.stat().st_mtime, tz=timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        )
        payload.update(
            {
                "status": STATUS_PASS_REQUIRED,
                "error_code": "",
                "repair_status": "already_converged",
                "remaining_violation_ids": [],
                "remaining_violation_count": 0,
                "postcheck_status": payload["precheck_status"],
                "postcheck_evidence_ref": str(postcheck_out),
                "stale_reasons": [],
            }
        )
        _finalize_bundle(
            workspace_root=workspace_root,
            artifact_root=artifact_root,
            receipt_out=receipt_out,
            run_token=run_token,
            payload=payload,
            generated_at=base_payload["generated_at"],
            mode=str(args.mode),
            catalog_path=catalog_path,
            precheck_out=precheck_out,
            precheck_rc=precheck_rc,
            precheck_timestamp=precheck_timestamp,
            precheck_cmd=precheck_cmd,
            entry_cmd=entry_cmd,
            entry_rc=0,
            postcheck_out=postcheck_out,
            postcheck_rc=precheck_rc,
            postcheck_timestamp=postcheck_timestamp,
            postcheck_cmd=precheck_cmd,
        )
        _emit(payload, json_only=args.json_only)
        return 0

    repair_results: list[dict[str, Any]] = []
    repaired_identity_ids: list[str] = []
    for identity_id in violation_ids:
        row = _apply_repair_for_identity(
            repo_root=repo_root,
            catalog_path=catalog_path,
            identity_id=identity_id,
            codex_home=codex_home,
            env=env,
        )
        repair_results.append(row)
        if str(row.get("final_status", "")).strip().upper() == STATUS_PASS_REQUIRED:
            repaired_identity_ids.append(identity_id)

    postcheck_rc, postcheck_payload = _check_launcher_closure(repo_root=repo_root, catalog_path=catalog_path, env=env)
    write_json(postcheck_out, postcheck_payload)
    postcheck_timestamp = datetime.fromtimestamp(postcheck_out.stat().st_mtime, tz=timezone.utc).isoformat().replace(
        "+00:00",
        "Z",
    )
    remaining_violation_ids = _identity_ids_from_rows(postcheck_payload.get("violations") if isinstance(postcheck_payload, dict) else [])
    postcheck_status = str(postcheck_payload.get("identity_codex_launcher_migration_closure_status", "")).strip().upper()
    apply_failed = any(str(row.get("final_status", "")).strip().upper() != STATUS_PASS_REQUIRED for row in repair_results)

    payload.update(
        {
            "mutation_applied": True,
            "repair_results": repair_results,
            "repaired_identity_ids": repaired_identity_ids,
            "repaired_identity_count": len(repaired_identity_ids),
            "postcheck_status": postcheck_status,
            "postcheck_evidence_ref": str(postcheck_out),
            "remaining_violation_ids": remaining_violation_ids,
            "remaining_violation_count": len(remaining_violation_ids),
        }
    )

    if postcheck_rc == 0 and postcheck_status == STATUS_PASS_REQUIRED and not remaining_violation_ids and not apply_failed:
        payload.update(
            {
                "status": STATUS_PASS_REQUIRED,
                "error_code": "",
                "repair_status": "apply_repaired",
                "stale_reasons": [],
            }
        )
        _finalize_bundle(
            workspace_root=workspace_root,
            artifact_root=artifact_root,
            receipt_out=receipt_out,
            run_token=run_token,
            payload=payload,
            generated_at=base_payload["generated_at"],
            mode=str(args.mode),
            catalog_path=catalog_path,
            precheck_out=precheck_out,
            precheck_rc=precheck_rc,
            precheck_timestamp=precheck_timestamp,
            precheck_cmd=precheck_cmd,
            entry_cmd=entry_cmd,
            entry_rc=0,
            postcheck_out=postcheck_out,
            postcheck_rc=postcheck_rc,
            postcheck_timestamp=postcheck_timestamp,
            postcheck_cmd=precheck_cmd,
        )
        _emit(payload, json_only=args.json_only)
        return 0

    payload.update(
        {
            "status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_POSTCHECK if remaining_violation_ids or postcheck_status != STATUS_PASS_REQUIRED else ERR_APPLY,
            "repair_status": "apply_partial" if repaired_identity_ids else "apply_failed",
            "stale_reasons": (
                ["launcher_migration_closure_unresolved_after_apply"] if remaining_violation_ids or postcheck_status != STATUS_PASS_REQUIRED else ["launcher_migration_apply_step_failed"]
            ),
        }
    )
    _finalize_bundle(
        workspace_root=workspace_root,
        artifact_root=artifact_root,
        receipt_out=receipt_out,
        run_token=run_token,
        payload=payload,
        generated_at=base_payload["generated_at"],
        mode=str(args.mode),
        catalog_path=catalog_path,
        precheck_out=precheck_out,
        precheck_rc=precheck_rc,
        precheck_timestamp=precheck_timestamp,
        precheck_cmd=precheck_cmd,
        entry_cmd=entry_cmd,
        entry_rc=1,
        postcheck_out=postcheck_out,
        postcheck_rc=postcheck_rc,
        postcheck_timestamp=postcheck_timestamp,
        postcheck_cmd=precheck_cmd,
    )
    _emit(payload, json_only=args.json_only)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
