#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from actor_session_common import list_actor_bindings, load_actor_binding, load_actor_binding_store, resolve_actor_id
from resolve_identity_context import (
    collect_protocol_evidence,
    default_identity_home,
    default_local_catalog_path,
    default_local_instances_root,
    ensure_local_catalog,
    resolve_protocol_root,
    resolve_identity,
)

ERR_EXEC_ORDER_HEADER_FIRST = "IP-EXEC-ORDER-001"
ERR_EXEC_ORDER_SCAFFOLD_CONSENT = "IP-EXEC-ORDER-002"
ERR_EXEC_ORDER_MUTATION_PLAN = "IP-EXEC-ORDER-003"
SCAFFOLD_CONSENT_TOKEN = "I_ACK_IDENTITY_SCAFFOLD_SCOPE_STACK_RUNTIME"
SCRIPT_DIR = Path(__file__).resolve().parent
PROTOCOL_ROOT = SCRIPT_DIR.parent


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(PROTOCOL_ROOT))


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    print("$", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROTOCOL_ROOT))
    if p.stdout.strip():
        print(p.stdout.strip())
    if p.stderr.strip():
        print(p.stderr.strip())
    return p.returncode, p.stdout or "", p.stderr or ""


def _parse_json_payload(raw: str) -> dict | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _infer_source_domain_from_catalog(catalog: str) -> str:
    try:
        p = Path(catalog).expanduser().resolve()
    except Exception:
        return "auto"
    txt = str(p)
    if "/.agents/" in txt:
        return "project"
    if "/.codex/" in txt:
        return "global"
    return "auto"


def _emit_two_phase_trace(
    *,
    identity_id: str,
    phase_a_refresh_applied: bool,
    phase_b_strict_revalidate_status: str,
    phase_transition_reason: str,
    phase_transition_error_code: str,
) -> None:
    payload = {
        "identity_id": identity_id,
        "phase_a_refresh_applied": bool(phase_a_refresh_applied),
        "phase_b_strict_revalidate_status": str(phase_b_strict_revalidate_status or ""),
        "phase_transition_reason": str(phase_transition_reason or ""),
        "phase_transition_error_code": str(phase_transition_error_code or ""),
    }
    print(json.dumps(payload, ensure_ascii=False))


def _runtime_mode_guard(
    identity_id: str,
    catalog: str,
    repo_catalog: str,
    scope: str = "",
    expect_mode: str = "auto",
) -> int:
    cmd = [
        "python3",
        "scripts/validate_identity_runtime_mode_guard.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        repo_catalog,
        "--expect-mode",
        str(expect_mode or "auto"),
    ]
    if scope.strip():
        cmd.extend(["--scope", scope.strip()])
    rc = _run(cmd)
    if rc != 0:
        print("[FAIL] runtime mode/catalog binding guard failed; aborting identity operation.")
    return rc


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _dump_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _resolve_task_path(catalog_data: dict, identity_id: str) -> Path:
    identities = catalog_data.get("identities") or []
    target = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p
    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _resolve_pack_path(catalog_data: dict, identity_id: str) -> Path:
    identities = catalog_data.get("identities") or []
    target = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if not pack_path:
        raise FileNotFoundError(f"pack_path missing for identity: {identity_id}")
    return Path(pack_path).expanduser().resolve()


def _resolve_evidence_output_path(pattern: str, identity_id: str, ts: datetime, pack_path: Path) -> Path:
    candidate = pattern.replace("<identity-id>", identity_id).replace("*", str(int(ts.timestamp())))
    local_prefix = f"identity/runtime/local/{identity_id}/"
    if candidate.startswith(local_prefix):
        return (pack_path / "runtime" / candidate[len(local_prefix) :]).resolve()
    if candidate.startswith("identity/runtime/"):
        return (pack_path / "runtime" / candidate[len("identity/runtime/") :]).resolve()
    return Path(candidate).expanduser().resolve()


def _sync_meta_statuses(catalog_data: dict) -> dict[Path, str | None]:
    """
    Mirror catalog identity status into each pack META.yaml.
    Returns backups for rollback: {meta_path: original_text_or_none}
    """
    backups: dict[Path, str | None] = {}
    identities = [x for x in (catalog_data.get("identities") or []) if isinstance(x, dict)]
    for row in identities:
        identity_id = str(row.get("id", "")).strip()
        if not identity_id:
            continue
        pack_path = str(row.get("pack_path", "")).strip()
        if not pack_path:
            continue
        meta_path = Path(pack_path) / "META.yaml"
        if not meta_path.exists():
            continue
        status = str(row.get("status", "")).strip().lower()
        if status not in {"active", "inactive"}:
            continue
        original = meta_path.read_text(encoding="utf-8")
        backups[meta_path] = original
        meta = _load_yaml(meta_path)
        meta["status"] = status
        _dump_yaml(meta_path, meta)
    return backups


def _restore_meta_backups(backups: dict[Path, str | None]) -> None:
    for path, original in backups.items():
        try:
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_text(original, encoding="utf-8")
        except Exception:
            pass


def _single_active_precheck(catalog_path: Path, target_identity_id: str, auto_converge: bool = False) -> int:
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 1
    data = _load_yaml(catalog_path)
    identities = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    actives = [str(x.get("id", "")).strip() for x in identities if str(x.get("status", "")).strip().lower() == "active"]
    actives = [x for x in actives if x]
    if len(actives) <= 1:
        return 0
    if auto_converge:
        print(
            "[WARN] --auto-converge-active is deprecated under multi-active model; "
            f"preserving existing active identities: {actives}"
        )
    else:
        print(f"[INFO] multi-active catalog detected (allowed): active_identities={actives}")
    return 0


def _write_binding_evidence(catalog_data: dict, identity_id: str, binding_status: str, note: str) -> Path:
    task = _load_json(_resolve_task_path(catalog_data, identity_id))
    pack_path = _resolve_pack_path(catalog_data, identity_id)
    contract = task.get("identity_role_binding_contract") or {}
    role_type = str(contract.get("role_type", "")).strip() or "identity_runtime_operator"
    ts = datetime.now(timezone.utc)
    report = {
        "binding_id": f"identity-role-binding-{identity_id}-{int(ts.timestamp())}",
        "generated_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "identity_id": identity_id,
        "role_type": role_type,
        "binding_status": binding_status,
        "runtime_bootstrap": {
            "status": "PASS",
            "validator": "scripts/validate_identity_runtime_contract.py",
            "evidence": str(_resolve_task_path(catalog_data, identity_id)),
        },
        "switch_guard": {
            "status": "PASS",
            "activation_policy": str(contract.get("activation_policy", "inactive_by_default")),
            "notes": note,
        },
    }
    pattern = str(contract.get("binding_evidence_path_pattern", "")).strip()
    if pattern:
        out = _resolve_evidence_output_path(pattern, identity_id, ts, pack_path)
    else:
        out = (pack_path / "runtime" / "examples" / f"identity-role-binding-{identity_id}-{int(ts.timestamp())}.json").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def _load_cross_actor_receipt(path_raw: str) -> tuple[dict, list[str], str]:
    if not str(path_raw or "").strip():
        return {}, ["cross_actor_override_receipt_missing"], ""
    p = Path(path_raw).expanduser().resolve()
    if not p.exists():
        return {}, ["cross_actor_override_receipt_not_found"], str(p)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}, ["cross_actor_override_receipt_invalid_json"], str(p)
    if not isinstance(data, dict):
        return {}, ["cross_actor_override_receipt_payload_not_object"], str(p)
    required = ("receipt_id", "actor_id", "run_id", "approved_by", "approved_at", "reason")
    missing = [f"cross_actor_override_receipt_missing_field:{k}" for k in required if not str(data.get(k, "")).strip()]
    return data, missing, str(p)


def _load_switch_intent_receipt(
    path_raw: str,
    *,
    actor_id: str,
    from_identity_id: str,
    to_identity_id: str,
) -> tuple[dict, list[str], str]:
    if not str(path_raw or "").strip():
        return {}, ["switch_intent_receipt_missing"], ""
    p = Path(path_raw).expanduser().resolve()
    if not p.exists():
        return {}, ["switch_intent_receipt_not_found"], str(p)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}, ["switch_intent_receipt_invalid_json"], str(p)
    if not isinstance(data, dict):
        return {}, ["switch_intent_receipt_payload_not_object"], str(p)

    required = ("receipt_id", "actor_id", "from_identity_id", "to_identity_id", "approved_by", "approved_at", "reason")
    missing = [f"switch_intent_receipt_missing_field:{k}" for k in required if not str(data.get(k, "")).strip()]
    if missing:
        return data, missing, str(p)

    errors: list[str] = []
    actor_receipt = str(data.get("actor_id", "")).strip()
    from_receipt = str(data.get("from_identity_id", "")).strip()
    to_receipt = str(data.get("to_identity_id", "")).strip()
    if actor_receipt != actor_id:
        errors.append("switch_intent_receipt_actor_mismatch")
    if from_receipt != from_identity_id:
        errors.append("switch_intent_receipt_from_identity_mismatch")
    if to_receipt != to_identity_id:
        errors.append("switch_intent_receipt_to_identity_mismatch")
    return data, errors, str(p)


def _cross_actor_conflicts(catalog_path: Path, active_identities: list[str], actor_id: str) -> list[dict]:
    out: list[dict] = []
    active_set = {x for x in active_identities if x}
    if not active_set:
        return out
    for binding in list_actor_bindings(catalog_path):
        bound_identity = str(binding.get("identity_id", "")).strip()
        bound_actor = str(binding.get("actor_id", "")).strip()
        if not bound_identity or not bound_actor:
            continue
        if bound_identity not in active_set:
            continue
        if bound_actor == actor_id:
            continue
        out.append(
            {
                "actor_id": bound_actor,
                "identity_id": bound_identity,
                "actor_session_path": str(binding.get("actor_session_path", "")),
            }
        )
    return out


def _activate_identity(
    repo_catalog: Path,
    local_catalog: Path,
    identity_id: str,
    scope: str = "",
    protocol_root: str = "",
    protocol_mode: str = "mode_a_shared",
    actor_id: str = "",
    run_id: str = "",
    switch_reason: str = "",
    allow_identity_switch: bool = False,
    switch_intent_receipt: str = "",
    allow_cross_actor_switch: bool = False,
    cross_actor_receipt: str = "",
) -> int:
    ensure_local_catalog(repo_catalog, local_catalog)
    try:
        resolved = resolve_identity(identity_id, repo_catalog, local_catalog, preferred_scope=scope)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1
    actor_id_resolved = resolve_actor_id(actor_id)
    run_id_resolved = str(run_id or "").strip() or f"activate-{identity_id}-{int(datetime.now(timezone.utc).timestamp())}"
    switch_reason_resolved = str(switch_reason or "").strip() or "explicit_activate"
    actor_binding = load_actor_binding(local_catalog, actor_id_resolved)
    current_actor_identity = str(actor_binding.get("identity_id", "")).strip()
    switch_intent_payload: dict = {}
    switch_intent_receipt_path = ""
    switch_intent_receipt_errors: list[str] = []
    identity_switch_detected = bool(current_actor_identity and current_actor_identity != identity_id)
    if identity_switch_detected:
        if not allow_identity_switch:
            print(
                "[FAIL] activation would switch actor-bound identity without explicit switch intent "
                f"(error_code=IP-ACT-SWITCH-001, actor_id={actor_id_resolved}, current_identity={current_actor_identity}, "
                f"target_identity={identity_id})."
            )
            print("[HINT] re-run with --allow-identity-switch --switch-intent-receipt <path.json>")
            return 1
        switch_intent_payload, switch_intent_receipt_errors, switch_intent_receipt_path = _load_switch_intent_receipt(
            switch_intent_receipt,
            actor_id=actor_id_resolved,
            from_identity_id=current_actor_identity,
            to_identity_id=identity_id,
        )
        if switch_intent_receipt_errors:
            print(
                "[FAIL] invalid switch-intent receipt for identity switch "
                f"(error_code=IP-ACT-SWITCH-002, receipt={switch_intent_receipt_path or switch_intent_receipt}, "
                f"errors={switch_intent_receipt_errors})"
            )
            return 1

    rc = _run(["python3", "scripts/validate_identity_role_binding.py", "--catalog", str(local_catalog), "--identity-id", identity_id])
    if rc != 0:
        print("[FAIL] role-binding validation failed; activation blocked")
        return rc

    if not local_catalog.exists():
        print(f"[FAIL] local catalog not found: {local_catalog}")
        return 1
    original_catalog_text = local_catalog.read_text(encoding="utf-8")
    data = _load_yaml(local_catalog)
    identities = data.get("identities") or []
    target = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    if not target:
        print(f"[FAIL] identity not found in catalog: {identity_id}")
        return 1

    preexisting_active = [
        str(x.get("id", "")).strip()
        for x in identities
        if isinstance(x, dict)
        and str(x.get("status", "")).strip().lower() == "active"
        and str(x.get("id", "")).strip()
        and str(x.get("id", "")).strip() != identity_id
    ]
    # Multi-active runtime model: activation should not demote other active identities.
    # Keep cross-actor receipt fields for backward-compatible audit payload shape.
    cross_actor_conflicts: list[dict] = []
    cross_actor_receipt_payload: dict = {}
    cross_actor_receipt_path = ""
    cross_actor_receipt_errors: list[str] = []

    created_evidence: list[Path] = []
    meta_backups: dict[Path, str | None] = {}
    switch_report: Path | None = None
    canonical_session_pointer = (local_catalog.parent / "session" / "active_identity.json").resolve()
    scoped_session_mirror = (local_catalog.parent / "session" / "mirror" / "current.json").resolve()
    try:
        # promote target to active binding first (activation validator requires this for active identities)
        created_evidence.append(
            _write_binding_evidence(
                data,
                identity_id,
                "BOUND_ACTIVE",
                note="activation transaction promoted identity to active",
            )
        )
        for item in identities:
            if not isinstance(item, dict):
                continue
            iid = str(item.get("id", "")).strip()
            if not iid:
                continue
            if iid == identity_id:
                item["status"] = "active"

        meta_backups = _sync_meta_statuses(data)
        _dump_yaml(local_catalog, data)
        rc = _run(["python3", "scripts/validate_identity_role_binding.py", "--catalog", str(local_catalog), "--identity-id", identity_id])
        if rc != 0:
            raise RuntimeError("post-activation role-binding validation failed")
        rc = _run(["python3", "scripts/validate_identity_state_consistency.py", "--catalog", str(local_catalog)])
        if rc != 0:
            raise RuntimeError("post-activation state consistency validation failed")

        switch_dir = Path("/tmp/identity-activation-reports")
        switch_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc)
        switch_report = switch_dir / f"identity-activation-switch-{identity_id}-{int(ts.timestamp())}.json"
        switch_payload = {
            "switch_id": switch_report.stem,
            "generated_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "target_identity_id": identity_id,
            "preexisting_active_identities": preexisting_active,
            "demoted_identities": [],
            "single_active_enforced": False,
            "activation_model": "actor_scoped_catalog_with_multi_active",
            "actor_id": actor_id_resolved,
            "run_id": run_id_resolved,
            "entrypoint_pid": str(os.getpid()),
            "switch_reason": switch_reason_resolved,
            "identity_switch_detected": identity_switch_detected,
            "identity_switch_from": current_actor_identity,
            "identity_switch_to": identity_id,
            "switch_intent_override": {
                "applied": bool(identity_switch_detected),
                "receipt_path": switch_intent_receipt_path,
                "receipt_fields": switch_intent_payload if switch_intent_payload else {},
            },
            "cross_actor_demotion_detected": bool(cross_actor_conflicts),
            "cross_actor_conflicts": cross_actor_conflicts,
            "cross_actor_override": {
                "applied": bool(cross_actor_conflicts and allow_cross_actor_switch),
                "receipt_path": cross_actor_receipt_path,
                "receipt_fields": cross_actor_receipt_payload if cross_actor_receipt_payload else {},
            },
            "binding_evidence_paths": [str(p) for p in created_evidence],
            "catalog_layer": "local",
            "catalog_path": str(local_catalog),
            "resolved_scope": str(resolved.get("resolved_scope", "")),
            "resolved_pack_path": str(resolved.get("resolved_pack_path", "")),
            "session_pointer_canonical_path": str(canonical_session_pointer),
            "session_pointer_mirror_path": str(scoped_session_mirror),
        }
        protocol = collect_protocol_evidence(protocol_root, protocol_mode)
        switch_payload.update(
            {
                "protocol_mode": protocol["protocol_mode"],
                "protocol_root": protocol["protocol_root"],
                "protocol_commit_sha": protocol["protocol_commit_sha"],
                "protocol_ref": protocol["protocol_ref"],
                "identity_home": str(default_identity_home()),
            }
        )
        switch_report.write_text(json.dumps(switch_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        actor_store = load_actor_binding_store(local_catalog, actor_id_resolved)
        compare_token = str(actor_store.get("compare_token", "")).strip() or str(actor_store.get("binding_version", 0))
        session_id = f"run:{run_id_resolved}"
        sync = subprocess.run(
            [
                "python3",
                "scripts/sync_session_identity.py",
                "--catalog",
                str(local_catalog),
                "--identity-id",
                identity_id,
                "--out",
                str(canonical_session_pointer),
                "--mirror-out",
                str(scoped_session_mirror),
                "--actor-id",
                actor_id_resolved,
                "--run-id",
                run_id_resolved,
                "--session-id",
                session_id,
                "--compare-token",
                compare_token,
                "--mutation-lane",
                "activate",
                "--switch-reason",
                switch_reason_resolved,
                "--entrypoint-pid",
                str(os.getpid()),
                "--cross-actor-override-receipt",
                cross_actor_receipt_path,
            ],
            capture_output=True,
            text=True,
        )
        if sync.returncode != 0:
            if sync.stdout.strip():
                print(sync.stdout.strip())
            if sync.stderr.strip():
                print(sync.stderr.strip())
            raise RuntimeError("session pointer canonical sync failed")
        if sync.stdout.strip():
            print(sync.stdout.strip())
        rc = _run(
            [
                "python3",
                "scripts/validate_identity_session_pointer_consistency.py",
                "--catalog",
                str(local_catalog),
                "--identity-id",
                identity_id,
                "--actor-id",
                actor_id_resolved,
                "--canonical-out",
                str(canonical_session_pointer),
                "--mirror-out",
                str(scoped_session_mirror),
            ]
        )
        if rc != 0:
            raise RuntimeError("session pointer consistency validation failed")
        rc = _run(
            [
                "python3",
                "scripts/validate_actor_session_multibinding_concurrency.py",
                "--catalog",
                str(local_catalog),
                "--identity-id",
                identity_id,
                "--actor-id",
                actor_id_resolved,
                "--operation",
                "activate",
                "--json-only",
            ]
        )
        if rc != 0:
            raise RuntimeError("actor session multibinding concurrency validation failed")
        print(f"[OK] activated identity in catalog (actor-scoped multi-active): {identity_id}")
        print(f"[OK] switch report: {switch_report}")
        return 0
    except Exception as e:
        local_catalog.write_text(original_catalog_text, encoding="utf-8")
        _restore_meta_backups(meta_backups)
        for p in created_evidence:
            if p.exists():
                p.unlink()
        if switch_report and switch_report.exists():
            switch_report.unlink()
        print(f"[FAIL] activation transaction rolled back: {e}")
        return 1


def _heal_identity(
    repo_catalog: Path,
    local_catalog: Path,
    identity_id: str,
    scope: str,
    source_pack: str,
    canonical_root: str,
    apply_fix: bool,
    destructive_replace: bool,
    out_dir: str,
) -> int:
    ensure_local_catalog(repo_catalog, local_catalog)
    report_time = datetime.now(timezone.utc)
    report_id = f"identity-heal-{identity_id}-{int(report_time.timestamp())}"
    report: dict = {
        "report_id": report_id,
        "generated_at": report_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "identity_id": identity_id,
        "scope": scope,
        "catalog": str(local_catalog),
        "repo_catalog": str(repo_catalog),
        "apply_fix": apply_fix,
        "steps": [],
    }

    def _step(name: str, cmd: list[str]) -> int:
        rc, out, err = _run_capture(cmd)
        report["steps"].append(
            {
                "name": name,
                "command": cmd,
                "rc": rc,
                "stdout": out,
                "stderr": err,
            }
        )
        return rc

    base_opts = ["--identity-id", identity_id, "--catalog", str(local_catalog), "--repo-catalog", str(repo_catalog)]
    if scope:
        base_opts += ["--scope", scope]
    if canonical_root:
        base_opts += ["--canonical-root", canonical_root]

    rc = _step("scan", ["python3", "scripts/identity_installer.py", "scan", *base_opts])
    if rc != 0:
        report["result"] = "FAIL_SCAN"
        _write_heal_report(report, out_dir)
        return rc

    if not apply_fix:
        report["result"] = "DRY_RUN_ONLY"
        report["note"] = "rerun with --apply to execute adopt/lock/repair-paths/validate"
        _write_heal_report(report, out_dir)
        print("[OK] heal dry-run completed (scan only).")
        return 0

    try:
        resolved = resolve_identity(identity_id, repo_catalog, local_catalog, preferred_scope=scope)
        chosen_pack = source_pack.strip() or str(resolved.get("resolved_pack_path", "")).strip()
    except Exception:
        chosen_pack = source_pack.strip()
    if not chosen_pack:
        report["result"] = "FAIL_SOURCE_PACK_REQUIRED"
        report["note"] = "unable to auto-resolve source pack; pass --source-pack explicitly"
        _write_heal_report(report, out_dir)
        print("[FAIL] heal apply requires --source-pack when auto-resolution is ambiguous.")
        return 2

    adopt_cmd = ["python3", "scripts/identity_installer.py", "adopt", *base_opts, "--source-pack", chosen_pack]
    canonical_target = Path(canonical_root).expanduser().resolve() / identity_id if canonical_root else None
    source_path = Path(chosen_pack).expanduser().resolve()
    if canonical_target is None:
        try:
            current_ctx = resolve_identity(identity_id, repo_catalog, local_catalog, preferred_scope=scope)
            resolved_pack = str(current_ctx.get("resolved_pack_path", "")).strip()
            if resolved_pack:
                canonical_target = Path(resolved_pack).expanduser().resolve()
        except Exception:
            canonical_target = None
    if canonical_target and canonical_target.exists() and canonical_target == source_path:
        report["steps"].append(
            {
                "name": "adopt",
                "command": adopt_cmd,
                "rc": 0,
                "stdout": "[SKIP] canonical target already matches source pack",
                "stderr": "",
            }
        )
        rc = 0
    else:
        if destructive_replace:
            adopt_cmd.append("--destructive-replace")
        rc = _step("adopt", adopt_cmd)
    if rc != 0:
        report["result"] = "FAIL_ADOPT"
        _write_heal_report(report, out_dir)
        return rc

    rc = _step("lock", ["python3", "scripts/identity_installer.py", "lock", *base_opts])
    if rc != 0:
        report["result"] = "FAIL_LOCK"
        _write_heal_report(report, out_dir)
        return rc

    rc = _step("repair_paths", ["python3", "scripts/identity_installer.py", "repair-paths", *base_opts])
    if rc != 0:
        report["result"] = "FAIL_REPAIR_PATHS"
        _write_heal_report(report, out_dir)
        return rc

    # Normalize duplicate runtime directories to prevent scope validator hard-fail.
    try:
        resolved_after = resolve_identity(identity_id, repo_catalog, local_catalog, preferred_scope=scope)
        canonical_pack = str(resolved_after.get("resolved_pack_path") or resolved_after.get("pack_path") or "").strip()
        if canonical_pack:
            moved, skipped = _cleanup_duplicate_instance_dirs(identity_id, canonical_pack)
            report["steps"].append(
                {
                    "name": "cleanup_duplicate_instance_dirs",
                    "command": ["internal", "_cleanup_duplicate_instance_dirs"],
                    "rc": 0 if not skipped else 1,
                    "stdout": json.dumps({"moved": moved, "skipped": skipped}, ensure_ascii=False),
                    "stderr": "",
                }
            )
    except Exception as e:
        report["steps"].append(
            {
                "name": "cleanup_duplicate_instance_dirs",
                "command": ["internal", "_cleanup_duplicate_instance_dirs"],
                "rc": 1,
                "stdout": "",
                "stderr": str(e),
            }
        )

    validate_cmd = [
        "python3",
        "scripts/identity_creator.py",
        "validate",
        "--identity-id",
        identity_id,
        "--repo-catalog",
        str(repo_catalog),
        "--catalog",
        str(local_catalog),
    ]
    if scope:
        validate_cmd += ["--scope", scope]
    rc = _step("validate", validate_cmd)
    if rc != 0:
        last = report["steps"][-1]
        merged = f"{last.get('stdout','')}\n{last.get('stderr','')}"
        needs_rulebook_scope_backfill = "rulebook line" in merged and "missing fields: ['scope']" in merged
        if needs_rulebook_scope_backfill:
            rb_cmd = [
                "python3",
                "scripts/repair_rulebook_schema_backfill.py",
                "--identity-id",
                identity_id,
                "--catalog",
                str(local_catalog),
                "--apply",
            ]
            rc_rb = _step("auto_repair_rulebook_schema_backfill", rb_cmd)
            if rc_rb == 0:
                rc = _step("revalidate_after_rulebook_backfill", validate_cmd)
                last = report["steps"][-1]
                merged = f"{last.get('stdout','')}\n{last.get('stderr','')}"

        needs_protocol = "no protocol review evidence file matched" in merged
        needs_binding = "role-binding evidence not found" in merged
        needs_replay = "replay evidence file not found" in merged
        if needs_protocol or needs_binding:
            repair_cmd = [
                "python3",
                "scripts/repair_identity_baseline_evidence.py",
                "--identity-id",
                identity_id,
                "--catalog",
                str(local_catalog),
                "--apply",
            ]
            if needs_protocol and not needs_binding:
                repair_cmd.append("--repair-protocol")
            if needs_binding and not needs_protocol:
                repair_cmd.append("--repair-role-binding")
            rc_repair = _step("auto_repair_baseline_evidence", repair_cmd)
            if rc_repair == 0:
                rc = _step("revalidate_after_auto_repair", validate_cmd)
        if rc != 0 and needs_replay:
            replay_cmd = [
                "python3",
                "scripts/repair_identity_replay_evidence.py",
                "--identity-id",
                identity_id,
                "--catalog",
                str(local_catalog),
                "--apply",
            ]
            rc_replay = _step("auto_repair_replay_evidence", replay_cmd)
            if rc_replay == 0:
                rc = _step("revalidate_after_replay_repair", validate_cmd)
        if rc != 0 and "install report not found by pattern" in (report["steps"][-1].get("stdout", "") + report["steps"][-1].get("stderr", "")):
            install_cmd = [
                "python3",
                "scripts/repair_identity_install_evidence.py",
                "--identity-id",
                identity_id,
                "--catalog",
                str(local_catalog),
                "--apply",
            ]
            rc_install = _step("auto_repair_install_evidence", install_cmd)
            if rc_install == 0:
                rc = _step("revalidate_after_install_repair", validate_cmd)
        if rc != 0 and "feedback logs count" in (report["steps"][-1].get("stdout", "") + report["steps"][-1].get("stderr", "")):
            fb_cmd = [
                "python3",
                "scripts/repair_identity_feedback_evidence.py",
                "--identity-id",
                identity_id,
                "--catalog",
                str(local_catalog),
                "--apply",
            ]
            rc_fb = _step("auto_repair_feedback_evidence", fb_cmd)
            if rc_fb == 0:
                rc = _step("revalidate_after_feedback_repair", validate_cmd)
        if rc != 0 and "missing capability arbitration sample report" in (report["steps"][-1].get("stdout", "") + report["steps"][-1].get("stderr", "")):
            arb_cmd = [
                "python3",
                "scripts/repair_identity_arbitration_evidence.py",
                "--identity-id",
                identity_id,
                "--catalog",
                str(local_catalog),
                "--apply",
            ]
            rc_arb = _step("auto_repair_arbitration_evidence", arb_cmd)
            if rc_arb == 0:
                rc = _step("revalidate_after_arbitration_repair", validate_cmd)

    report["result"] = "PASS" if rc == 0 else "FAIL_VALIDATE"
    _write_heal_report(report, out_dir)
    return rc


def _write_heal_report(report: dict, out_dir: str) -> None:
    p = Path(out_dir).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    out = p / f"{report['report_id']}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[INFO] heal report: {out}")


def _cleanup_duplicate_instance_dirs(identity_id: str, canonical_pack_path: str) -> tuple[list[str], list[str]]:
    """
    Quarantine duplicate runtime instance directories under ~/.codex/identity.
    Returns (moved_paths, skipped_paths).
    """
    moved: list[str] = []
    skipped: list[str] = []
    canonical = Path(canonical_pack_path).expanduser().resolve()
    home = (Path.home() / ".codex" / "identity").resolve()
    candidates = [
        home / identity_id,
        home / "instances" / identity_id,
        home / "identity" / identity_id,
        home / "identities" / identity_id,
        home / "instances-canonical" / identity_id,
    ]
    seen: set[str] = set()
    existing: list[Path] = []
    for c in candidates:
        try:
            p = c.expanduser().resolve()
        except Exception:
            p = c.expanduser()
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        if p.exists() and p.is_dir():
            existing.append(p)

    if len(existing) <= 1:
        return moved, skipped

    quarantine_root = home / "_quarantine" / identity_id
    quarantine_root.mkdir(parents=True, exist_ok=True)
    ts = int(datetime.now(timezone.utc).timestamp())
    for p in existing:
        if p == canonical:
            continue
        try:
            dest = quarantine_root / f"{p.name}-{ts}"
            p.rename(dest)
            moved.append(str(dest))
        except Exception:
            skipped.append(str(p))
    return moved, skipped


def _classify_scope_from_pack_path(pack_path: str) -> str:
    p = Path(pack_path).expanduser()
    if not p.is_absolute():
        return "SYSTEM" if str(p).startswith("identity/") else "REPO"
    rp = str(p.resolve())
    home = str(Path.home().resolve())
    cwd = str(Path.cwd().resolve())
    if rp.startswith("/etc/"):
        return "ADMIN"
    if rp == cwd or rp.startswith(cwd + "/"):
        return "REPO"
    if rp == home or rp.startswith(home + "/"):
        return "USER"
    return "USER"


def _enforce_scope_pack_alignment(
    identity_id: str,
    required_scope: str,
    resolved_pack_path: str,
    resolved_scope: str = "",
) -> int:
    scope = (required_scope or "").strip().upper()
    if not scope:
        return 0
    if scope not in {"REPO", "USER", "ADMIN", "SYSTEM"}:
        print(f"[FAIL] invalid --scope value: {required_scope}")
        return 1
    if not resolved_pack_path:
        print(f"[FAIL] resolved_pack_path missing for identity={identity_id}")
        return 1
    resolved_scope_norm = (resolved_scope or "").strip().upper()
    if resolved_scope_norm in {"", "UNKNOWN"}:
        actual = _classify_scope_from_pack_path(resolved_pack_path)
    else:
        actual = resolved_scope_norm
    if actual != scope:
        print(
            "[FAIL] scope/pack_path mismatch: "
            f"identity={identity_id} required_scope={scope} actual_scope={actual} pack_path={resolved_pack_path}"
        )
        print("[HINT] run identity_installer adopt + lock for this identity before update.")
        return 1
    print(f"[OK] scope/pack_path aligned: identity={identity_id} scope={scope} pack_path={resolved_pack_path}")
    return 0


def _enforce_protocol_root_separation(
    identity_id: str,
    resolved_pack_path: str,
    protocol_root: str,
    allow_protocol_root_pack: bool,
) -> int:
    if allow_protocol_root_pack:
        print("[WARN] allow-protocol-root-pack is enabled; protocol-root separation bypassed")
        return 0
    try:
        pack = Path(resolved_pack_path).expanduser().resolve()
        root = resolve_protocol_root(protocol_root).resolve()
        pack.relative_to(root)
        print(
            "[FAIL] resolved pack_path is inside protocol root (runtime/protocol boundary violation): "
            f"identity={identity_id} pack_path={pack} protocol_root={root}"
        )
        print("[HINT] migrate identity pack with identity_installer adopt + lock before update.")
        return 1
    except ValueError:
        return 0
    except Exception as exc:
        print(f"[FAIL] protocol-root separation check failed: {exc}")
        return 1


def main() -> int:
    identity_home = default_identity_home()
    repo_catalog_default = "identity/catalog/identities.yaml"
    local_catalog_default = str(default_local_catalog_path(identity_home))
    ap = argparse.ArgumentParser(
        description="Unified identity-creator CLI wrapper (init/register/validate/compile/activate/update)"
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create an identity pack scaffold")
    p_init.add_argument("--id", required=True)
    p_init.add_argument("--title", required=True)
    p_init.add_argument("--description", required=True)
    p_init.add_argument("--profile", choices=["full-contract", "minimal"], default="full-contract")
    p_init.add_argument("--register", action="store_true")
    p_init.add_argument("--activate", action="store_true")
    p_init.add_argument("--set-default", action="store_true")
    p_init.add_argument("--catalog", default=local_catalog_default)
    p_init.add_argument("--repo-catalog", default=repo_catalog_default)
    p_init.add_argument("--pack-root", default=str(default_local_instances_root(identity_home)))
    p_init.add_argument("--repo-fixture", action="store_true")
    p_init.add_argument("--repo-fixture-confirm", default="")
    p_init.add_argument("--repo-fixture-purpose", default="")
    p_init.add_argument("--skip-sample-bootstrap", action="store_true")
    p_init.add_argument(
        "--scaffold-consent-token",
        default="",
        help=f"required scaffold consent token for init mutation preflight ({SCAFFOLD_CONSENT_TOKEN})",
    )
    p_init.add_argument("--why-now", default="", help="pre-mutation disclosure rationale for init")
    p_init.add_argument("--planned-file", action="append", default=[], help="explicit planned mutation file for init")
    p_init.add_argument("--pre-mutation-gate-receipt", default="", help="optional pre-mutation gate receipt path for init")

    p_validate = sub.add_parser("validate", help="Run identity required validators for an identity")
    p_validate.add_argument("--identity-id", required=True)
    p_validate.add_argument("--repo-catalog", default=repo_catalog_default)
    p_validate.add_argument("--catalog", default=local_catalog_default)
    p_validate.add_argument("--scope", default="")
    p_validate.add_argument(
        "--baseline-policy",
        choices=["strict", "warn"],
        default="strict",
        help="protocol baseline freshness enforcement policy for validate chain",
    )
    p_validate.add_argument("--layer-intent-text", default="", help="optional natural-language layer intent for stamp render/validators")
    p_validate.add_argument("--expected-work-layer", default="", help="optional expected work_layer override for strict reply gates")
    p_validate.add_argument("--expected-source-layer", default="", help="optional expected source_layer override for strict reply gates")

    p_compile = sub.add_parser("compile", help="Compile runtime brief")
    p_compile.add_argument("--check", action="store_true", help="fail if compile output is not stable")

    p_activate = sub.add_parser("activate", help="Set identity status=active in catalog")
    p_activate.add_argument("--identity-id", required=True)
    p_activate.add_argument("--repo-catalog", default=repo_catalog_default)
    p_activate.add_argument("--catalog", default=local_catalog_default)
    p_activate.add_argument("--scope", default="")
    p_activate.add_argument("--protocol-root", default="")
    p_activate.add_argument("--protocol-mode", choices=["mode_a_shared", "mode_b_standalone"], default="mode_a_shared")
    p_activate.add_argument("--actor-id", default="", help="actor id for actor-scoped session binding")
    p_activate.add_argument("--run-id", default="", help="activation run id for audit traceability")
    p_activate.add_argument("--switch-reason", default="explicit_activate", help="reason for activation switch")
    p_activate.add_argument(
        "--allow-identity-switch",
        action="store_true",
        help=(
            "explicitly allow switching actor-bound identity; required when current actor binding points to a different identity"
        ),
    )
    p_activate.add_argument(
        "--switch-intent-receipt",
        default="",
        help=(
            "JSON receipt path required with --allow-identity-switch; must bind actor_id/from_identity_id/to_identity_id"
        ),
    )
    p_activate.add_argument(
        "--allow-cross-actor-switch",
        action="store_true",
        help="allow cross-actor demotion only with audited --cross-actor-receipt",
    )
    p_activate.add_argument(
        "--cross-actor-receipt",
        default="",
        help="JSON receipt path required when --allow-cross-actor-switch is used with cross-actor conflicts",
    )
    p_activate.add_argument("--auto-converge-active", action="store_true")
    p_activate.add_argument(
        "--allow-fixture-runtime",
        action="store_true",
        help="explicitly allow fixture identity activation with audited override receipt",
    )
    p_activate.add_argument(
        "--fixture-audit-receipt",
        default="",
        help="JSON receipt path required when --allow-fixture-runtime is used for fixture mutation",
    )

    p_update = sub.add_parser("update", help="Run identity upgrade executor")
    p_update.add_argument("--identity-id", required=True)
    p_update.add_argument("--mode", choices=["review-required", "safe-auto"], default="review-required")
    p_update.add_argument(
        "--out-dir",
        default="identity/runtime/reports",
        help="upgrade report output directory; default is remapped to runtime_output_root/reports",
    )
    p_update.add_argument("--repo-catalog", default=repo_catalog_default)
    p_update.add_argument("--catalog", default=local_catalog_default)
    p_update.add_argument("--scope", default=os.environ.get("IDENTITY_SCOPE", "USER"))
    p_update.add_argument(
        "--baseline-policy",
        choices=["strict", "warn"],
        default="strict",
        help="protocol baseline freshness enforcement policy for update preflight",
    )
    p_update.add_argument("--protocol-root", default="")
    p_update.add_argument("--protocol-mode", choices=["mode_a_shared", "mode_b_standalone"], default="mode_a_shared")
    p_update.add_argument(
        "--capability-activation-policy",
        choices=["strict-union", "route-any-ready"],
        default="strict-union",
        help=(
            "capability preflight policy: strict-union requires all declared route capabilities; "
            "route-any-ready allows progress when at least one route is ready."
        ),
    )
    p_update.add_argument(
        "--allow-protocol-root-pack",
        action="store_true",
        help="allow update on identities whose pack_path is inside protocol root (fixture/debug only)",
    )
    p_update.add_argument(
        "--allow-fixture-runtime",
        action="store_true",
        help="explicitly allow fixture identity update with audited override receipt",
    )
    p_update.add_argument(
        "--fixture-audit-receipt",
        default="",
        help="JSON receipt path required when --allow-fixture-runtime is used for fixture mutation",
    )
    p_update.add_argument("--auto-converge-active", action="store_true")
    p_update.add_argument("--layer-intent-text", default="", help="optional natural-language layer intent passthrough")
    p_update.add_argument("--expected-work-layer", default="", help="optional expected work_layer passthrough")
    p_update.add_argument("--expected-source-layer", default="", help="optional expected source_layer passthrough")
    p_update.add_argument("--why-now", default="", help="pre-mutation disclosure rationale for update")
    p_update.add_argument("--planned-file", action="append", default=[], help="explicit planned mutation file for update")
    p_update.add_argument("--pre-mutation-gate-receipt", default="", help="optional pre-mutation gate receipt path for update")
    p_update.add_argument(
        "--release-session-lane-lock",
        action="store_true",
        help=(
            "emit canonical SESSION_LANE_LOCK_EXIT receipt before update. "
            "Use when protocol lane lock must be explicitly exited before returning to instance lane."
        ),
    )
    p_update.add_argument(
        "--session-lane-lock-exit-reason",
        default="manual_session_lane_lock_exit",
        help="exit reason payload for SESSION_LANE_LOCK_EXIT receipt",
    )

    p_heal = sub.add_parser("heal", help="Run runtime identity self-healing flow (scan/adopt/lock/repair/validate)")
    p_heal.add_argument("--identity-id", required=True)
    p_heal.add_argument("--repo-catalog", default=repo_catalog_default)
    p_heal.add_argument("--catalog", default=local_catalog_default)
    p_heal.add_argument("--scope", default="USER")
    p_heal.add_argument("--source-pack", default="")
    p_heal.add_argument("--canonical-root", default="")
    p_heal.add_argument("--apply", action="store_true", help="execute fixes; otherwise scan-only dry run")
    p_heal.add_argument("--destructive-replace", action="store_true")
    p_heal.add_argument("--out-dir", default="/tmp/identity-heal-reports")


    args = ap.parse_args()

    if args.command == "init":
        gate_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        init_run_id = f"identity-init-{args.id}-{int(datetime.now(timezone.utc).timestamp())}"
        source_domain = _infer_source_domain_from_catalog(args.catalog)
        actor = f"user:{os.environ.get('USER', 'unknown')}"
        header_line = (
            f"Identity-Context: actor_id={actor}; identity_id={args.id}; scope=USER; lock=LOCK_MATCH; source={source_domain} "
            f"| Layer-Context: work_layer=instance; source_layer={source_domain}"
        )
        print(header_line)
        header_first_gate_status = "PASS_REQUIRED" if header_line.startswith("Identity-Context:") else "FAIL_REQUIRED"
        scaffold_consent_gate_status = (
            "PASS_REQUIRED"
            if str(args.scaffold_consent_token or "").strip() == SCAFFOLD_CONSENT_TOKEN
            else "FAIL_REQUIRED"
        )
        pack_root_path = Path(args.pack_root).expanduser().resolve()
        default_planned_files = [
            str((pack_root_path / args.id / "CURRENT_TASK.json").resolve()),
            str((pack_root_path / args.id / "IDENTITY_PROMPT.md").resolve()),
            str((pack_root_path / args.id / "TASK_HISTORY.md").resolve()),
            str((pack_root_path / args.id / "RULEBOOK.jsonl").resolve()),
        ]
        if args.register or args.activate or args.set_default:
            default_planned_files.append(str(Path(args.catalog).expanduser().resolve()))
        provided_planned_files = [str(x or "").strip() for x in list(args.planned_file or []) if str(x or "").strip()]
        planned_files = provided_planned_files or default_planned_files
        why_now = str(args.why_now or "").strip() or f"initialize_identity_pack:{args.id}"
        mutation_plan_disclosed = bool(planned_files and why_now)
        pre_mutation_error_code = ""
        if header_first_gate_status != "PASS_REQUIRED":
            pre_mutation_error_code = ERR_EXEC_ORDER_HEADER_FIRST
        elif scaffold_consent_gate_status != "PASS_REQUIRED":
            pre_mutation_error_code = ERR_EXEC_ORDER_SCAFFOLD_CONSENT
        elif not mutation_plan_disclosed:
            pre_mutation_error_code = ERR_EXEC_ORDER_MUTATION_PLAN
        receipt_path = (
            Path(args.pre_mutation_gate_receipt).expanduser().resolve()
            if str(args.pre_mutation_gate_receipt or "").strip()
            else Path(f"/tmp/identity-pre-mutation-gate-init-{args.id}-{int(datetime.now(timezone.utc).timestamp())}.json")
        )
        _write_json(
            receipt_path,
            {
                "identity_id": args.id,
                "operation": "init",
                "run_id": init_run_id,
                "header_first_gate_status": header_first_gate_status,
                "scaffold_consent_gate_status": scaffold_consent_gate_status,
                "mutation_plan_disclosed": mutation_plan_disclosed,
                "planned_files": planned_files,
                "why_now": why_now,
                "pre_mutation_gate_ts": gate_ts,
                "pre_mutation_gate_error_code": pre_mutation_error_code,
                "required_scaffold_consent_token": SCAFFOLD_CONSENT_TOKEN,
                "status": "PASS_REQUIRED" if not pre_mutation_error_code else "FAIL_REQUIRED",
            },
        )
        print(f"[INFO] pre-mutation gate receipt: {receipt_path}")
        if pre_mutation_error_code:
            print(f"[FAIL] init pre-mutation gate failed: {pre_mutation_error_code}")
            if pre_mutation_error_code == ERR_EXEC_ORDER_SCAFFOLD_CONSENT:
                print(f"[HINT] pass --scaffold-consent-token {SCAFFOLD_CONSENT_TOKEN}")
            return 1
        cmd = [
            "python3",
            "scripts/create_identity_pack.py",
            "--id",
            args.id,
            "--title",
            args.title,
            "--description",
            args.description,
            "--profile",
            args.profile,
            "--catalog",
            args.catalog,
            "--pack-root",
            args.pack_root,
        ]
        if args.repo_fixture:
            cmd.append("--repo-fixture")
            if args.repo_fixture_confirm.strip():
                cmd.extend(["--repo-fixture-confirm", args.repo_fixture_confirm.strip()])
            if args.repo_fixture_purpose.strip():
                cmd.extend(["--repo-fixture-purpose", args.repo_fixture_purpose.strip()])
        if args.skip_sample_bootstrap:
            cmd.append("--skip-sample-bootstrap")
        if args.register:
            cmd.append("--register")
        if args.activate:
            cmd.append("--activate")
        if args.set_default:
            cmd.append("--set-default")
        return _run(cmd)

    if args.command == "validate":
        ensure_local_catalog(Path(args.repo_catalog), Path(args.catalog))
        rc_guard = _runtime_mode_guard(
            args.identity_id,
            args.catalog,
            args.repo_catalog,
            args.scope,
            expect_mode="any",
        )
        if rc_guard != 0:
            return rc_guard
        identity_home_expected = str(Path(args.catalog).expanduser().resolve().parent)
        stamp_artifact = f"/tmp/identity-response-stamp-{args.identity_id}.json"
        stamp_blocker_receipt = f"/tmp/identity-stamp-blocker-receipt-{args.identity_id}.json"
        reply_first_line_blocker_receipt = (
            f"/tmp/identity-reply-first-line-blocker-receipt-{args.identity_id}.json"
        )
        send_time_reply_file = f"/tmp/identity-send-time-reply-{args.identity_id}.txt"
        send_time_reply_gate_blocker_receipt = (
            f"/tmp/identity-send-time-reply-gate-blocker-receipt-{args.identity_id}.json"
        )
        execution_reply_coherence_blocker_receipt = (
            f"/tmp/identity-execution-reply-coherence-blocker-receipt-{args.identity_id}.json"
        )
        try:
            _ = resolve_identity(
                args.identity_id,
                Path(args.repo_catalog),
                Path(args.catalog),
                preferred_scope=args.scope,
            )
        except Exception as e:
            print(f"[FAIL] {e}")
            return 1
        checks = [
            ["python3", "scripts/validate_identity_scope_resolution.py", "--catalog", args.catalog, "--repo-catalog", args.repo_catalog, "--identity-id", args.identity_id, "--scope", args.scope],
            ["python3", "scripts/validate_identity_scope_isolation.py", "--catalog", args.catalog, "--repo-catalog", args.repo_catalog, "--identity-id", args.identity_id, "--scope", args.scope],
            ["python3", "scripts/validate_identity_scope_persistence.py", "--catalog", args.catalog, "--repo-catalog", args.repo_catalog, "--identity-id", args.identity_id, "--scope", args.scope],
            ["python3", "scripts/validate_identity_state_consistency.py", "--catalog", args.catalog],
            ["python3", "scripts/validate_identity_instance_isolation.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_runtime_contract.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_role_binding.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            [
                "python3",
                "scripts/validate_identity_home_catalog_alignment.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--identity-home",
                identity_home_expected,
            ],
            [
                "python3",
                "scripts/validate_fixture_runtime_boundary.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_actor_session_binding.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_no_implicit_switch.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_cross_actor_isolation.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_actor_session_multibinding_concurrency.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_identity_session_refresh_status.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--baseline-policy",
                args.baseline_policy,
            ],
            [
                "python3",
                "scripts/render_identity_response_stamp.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--view",
                "external",
                "--disclosure-level",
                "standard",
                "--out",
                stamp_artifact,
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_identity_response_stamp.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--stamp-json",
                stamp_artifact,
                "--force-check",
                "--enforce-user-visible-gate",
                "--operation",
                "validate",
                "--blocker-receipt-out",
                stamp_blocker_receipt,
            ],
            [
                "python3",
                "scripts/validate_identity_response_stamp_blocker_receipt.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--force-check",
                "--receipt",
                stamp_blocker_receipt,
            ],
            [
                "python3",
                "scripts/validate_reply_identity_context_first_line.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--stamp-json",
                stamp_artifact,
                "--force-check",
                "--enforce-first-line-gate",
                "--operation",
                "validate",
                "--blocker-receipt-out",
                reply_first_line_blocker_receipt,
            ],
            [
                "python3",
                "scripts/validate_layer_intent_resolution.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--stamp-json",
                stamp_artifact,
                "--force-check",
                "--enforce-layer-intent-gate",
                "--operation",
                "validate",
                "--json-only",
            ],
            [
                "python3",
                "scripts/compose_and_validate_governed_reply.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--body-text",
                "VALIDATE_SEND_TIME_REPLY_BODY",
                "--out-reply-file",
                send_time_reply_file,
                "--blocker-receipt-out",
                send_time_reply_gate_blocker_receipt,
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_send_time_reply_gate.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--reply-file",
                send_time_reply_file,
                "--force-check",
                "--enforce-send-time-gate",
                "--reply-outlet-guard-applied",
                "--reply-transport-ref",
                send_time_reply_file,
                "--operation",
                "validate",
                "--blocker-receipt-out",
                send_time_reply_gate_blocker_receipt,
            ],
            [
                "python3",
                "scripts/validate_identity_response_stamp_blocker_receipt.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--force-check",
                "--receipt",
                send_time_reply_gate_blocker_receipt,
            ],
            [
                "python3",
                "scripts/validate_identity_response_stamp_blocker_receipt.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--force-check",
                "--receipt",
                reply_first_line_blocker_receipt,
            ],
            [
                "python3",
                "scripts/validate_execution_reply_identity_coherence.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--stamp-json",
                stamp_artifact,
                "--force-check",
                "--enforce-coherence-gate",
                "--operation",
                "validate",
                "--blocker-receipt-out",
                execution_reply_coherence_blocker_receipt,
            ],
            [
                "python3",
                "scripts/validate_identity_response_stamp_blocker_receipt.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--force-check",
                "--receipt",
                execution_reply_coherence_blocker_receipt,
            ],
            ["python3", "scripts/validate_identity_upgrade_prereq.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_update_lifecycle.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_install_safety.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_tool_installation.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_install_provenance.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_vendor_api_discovery.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_vendor_api_solution.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            [
                "python3",
                "scripts/validate_required_contract_coverage.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_semantic_routing_guard.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_protocol_vendor_semantic_isolation.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_external_source_trust_chain.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_protocol_data_sanitization_boundary.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/trigger_platform_optimization_discovery.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_discovery_requiredization.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--json-only",
            ],
            [
                "python3",
                "scripts/build_vibe_coding_feeding_pack.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--out-root",
                "/tmp/vibe-coding-feeding-packs",
            ],
            [
                "python3",
                "scripts/validate_identity_capability_fit_optimization.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_capability_composition_before_discovery.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_capability_fit_review_freshness.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_capability_fit_roundtable_evidence.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/trigger_capability_fit_review.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/build_capability_fit_matrix.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--out-root",
                "/tmp/capability-fit-matrices",
            ],
            [
                "python3",
                "scripts/validate_vendor_namespace_separation.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_instance_protocol_split_receipt.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_work_layer_gate_set_routing.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--force-check",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_writeback_continuity.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_post_execution_mandatory.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_protocol_feedback_reply_channel.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--force-check",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_protocol_feedback_bootstrap_ready.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--force-check",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_protocol_entry_candidate_bridge.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--force-check",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_protocol_inquiry_followup_chain.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--force-check",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_protocol_feedback_sidecar_contract.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
                "--enforce-blocking",
            ],
            [
                "python3",
                "scripts/validate_instance_base_repo_write_boundary.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_protocol_feedback_ssot_archival.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "validate",
            ],
            [
                "python3",
                "scripts/validate_identity_protocol_baseline_freshness.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--baseline-policy",
                args.baseline_policy,
            ],
            [
                "python3",
                "scripts/validate_identity_protocol_version_alignment.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--scope",
                args.scope,
                "--operation",
                "validate",
                "--alignment-policy",
                args.baseline_policy,
                "--json-only",
            ],
            ["python3", "scripts/validate_identity_experience_feedback_governance.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_capability_arbitration.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_dialogue_content.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_dialogue_cross_validation.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_dialogue_result_support.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_ci_enforcement.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
        ]
        layer_intent_text = str(args.layer_intent_text or "").strip()
        expected_work_layer = str(args.expected_work_layer or "").strip().lower()
        expected_source_layer = str(args.expected_source_layer or "").strip().lower()
        if layer_intent_text:
            for cmd in checks:
                if len(cmd) < 2:
                    continue
                if cmd[1] in {
                    "scripts/render_identity_response_stamp.py",
                    "scripts/compose_and_validate_governed_reply.py",
                    "scripts/validate_layer_intent_resolution.py",
                    "scripts/validate_reply_identity_context_first_line.py",
                    "scripts/validate_send_time_reply_gate.py",
                    "scripts/validate_execution_reply_identity_coherence.py",
                    "scripts/validate_work_layer_gate_set_routing.py",
                    "scripts/validate_protocol_feedback_bootstrap_ready.py",
                    "scripts/validate_protocol_entry_candidate_bridge.py",
                    "scripts/validate_protocol_inquiry_followup_chain.py",
                }:
                    cmd.extend(["--layer-intent-text", layer_intent_text])
        if expected_work_layer:
            for cmd in checks:
                if len(cmd) < 2:
                    continue
                if cmd[1] in {
                    "scripts/validate_layer_intent_resolution.py",
                    "scripts/validate_reply_identity_context_first_line.py",
                    "scripts/validate_send_time_reply_gate.py",
                    "scripts/validate_execution_reply_identity_coherence.py",
                    "scripts/validate_work_layer_gate_set_routing.py",
                    "scripts/validate_protocol_feedback_bootstrap_ready.py",
                    "scripts/validate_protocol_entry_candidate_bridge.py",
                    "scripts/validate_protocol_inquiry_followup_chain.py",
                }:
                    cmd.extend(["--expected-work-layer", expected_work_layer])
                if cmd[1] == "scripts/compose_and_validate_governed_reply.py":
                    cmd.extend(["--work-layer", expected_work_layer])
        if expected_source_layer:
            for cmd in checks:
                if len(cmd) < 2:
                    continue
                if cmd[1] == "scripts/compose_and_validate_governed_reply.py":
                    cmd.extend(["--source-layer", expected_source_layer])
                if cmd[1] in {
                    "scripts/validate_layer_intent_resolution.py",
                    "scripts/validate_reply_identity_context_first_line.py",
                    "scripts/validate_send_time_reply_gate.py",
                    "scripts/validate_execution_reply_identity_coherence.py",
                }:
                    cmd.extend(["--expected-source-layer", expected_source_layer])
                if cmd[1] in {
                    "scripts/validate_protocol_feedback_bootstrap_ready.py",
                    "scripts/validate_protocol_entry_candidate_bridge.py",
                    "scripts/validate_protocol_inquiry_followup_chain.py",
                }:
                    cmd.extend(["--source-layer", expected_source_layer])
                if cmd[1] in {
                    "scripts/validate_work_layer_gate_set_routing.py",
                }:
                    cmd.extend(["--source-layer", expected_source_layer])
        for cmd in checks:
            rc = _run(cmd)
            if rc != 0:
                return rc
        return 0

    if args.command == "compile":
        rc = _run(["python3", "scripts/compile_identity_runtime.py"])
        if rc != 0:
            return rc
        if args.check:
            return _run(["git", "diff", "--exit-code", "--", "identity/runtime/IDENTITY_COMPILED.md"])
        return 0

    if args.command == "activate":
        rc_guard = _runtime_mode_guard(args.identity_id, args.catalog, args.repo_catalog, args.scope)
        if rc_guard != 0:
            return rc_guard
        identity_home_expected = str(Path(args.catalog).expanduser().resolve().parent)
        rc_home_align = _run(
            [
                "python3",
                "scripts/validate_identity_home_catalog_alignment.py",
                "--identity-id",
                args.identity_id,
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-home",
                identity_home_expected,
            ]
        )
        if rc_home_align != 0:
            print("[FAIL] identity home/catalog alignment validation failed; activate blocked")
            return rc_home_align
        fixture_boundary_cmd = [
            "python3",
            "scripts/validate_fixture_runtime_boundary.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--operation",
            "activate",
        ]
        if args.allow_fixture_runtime:
            fixture_boundary_cmd.append("--allow-fixture-runtime")
        if args.fixture_audit_receipt.strip():
            fixture_boundary_cmd.extend(["--fixture-audit-receipt", args.fixture_audit_receipt.strip()])
        rc_boundary = _run(fixture_boundary_cmd)
        if rc_boundary != 0:
            print("[FAIL] fixture/runtime boundary validation failed; activate blocked")
            return rc_boundary
        return _activate_identity(
            Path(args.repo_catalog),
            Path(args.catalog),
            args.identity_id,
            args.scope,
            args.protocol_root,
            args.protocol_mode,
            args.actor_id,
            args.run_id,
            args.switch_reason,
            bool(args.allow_identity_switch),
            args.switch_intent_receipt,
            bool(args.allow_cross_actor_switch),
            args.cross_actor_receipt,
        )

    if args.command == "update":
        ensure_local_catalog(Path(args.repo_catalog), Path(args.catalog))
        rc_guard = _runtime_mode_guard(args.identity_id, args.catalog, args.repo_catalog, args.scope)
        if rc_guard != 0:
            return rc_guard
        identity_home_expected = str(Path(args.catalog).expanduser().resolve().parent)
        rc_home_align = _run(
            [
                "python3",
                "scripts/validate_identity_home_catalog_alignment.py",
                "--identity-id",
                args.identity_id,
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-home",
                identity_home_expected,
            ]
        )
        if rc_home_align != 0:
            print("[FAIL] identity home/catalog alignment validation failed; update blocked")
            return rc_home_align
        fixture_boundary_cmd = [
            "python3",
            "scripts/validate_fixture_runtime_boundary.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--operation",
            "update",
        ]
        if args.allow_fixture_runtime:
            fixture_boundary_cmd.append("--allow-fixture-runtime")
        if args.fixture_audit_receipt.strip():
            fixture_boundary_cmd.extend(["--fixture-audit-receipt", args.fixture_audit_receipt.strip()])
        rc_fixture = _run(fixture_boundary_cmd)
        if rc_fixture != 0:
            print("[FAIL] fixture/runtime boundary validation failed; update blocked")
            return rc_fixture
        try:
            resolved = resolve_identity(
                args.identity_id,
                Path(args.repo_catalog),
                Path(args.catalog),
                preferred_scope=args.scope,
            )
        except Exception as e:
            print(f"[FAIL] {e}")
            return 1
        rc_scope = _enforce_scope_pack_alignment(
            args.identity_id,
            args.scope,
            str(resolved.get("resolved_pack_path", "")).strip(),
            str(resolved.get("resolved_scope", "")).strip(),
        )
        if rc_scope != 0:
            return rc_scope
        rc_boundary = _enforce_protocol_root_separation(
            args.identity_id,
            str(resolved.get("resolved_pack_path", "")).strip(),
            args.protocol_root,
            bool(args.allow_protocol_root_pack),
        )
        if rc_boundary != 0:
            return rc_boundary
        creator_run_id = f"identity-upgrade-exec-{args.identity_id}-{int(datetime.now(timezone.utc).timestamp())}"
        pre_mutation_gate_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        pre_mutation_reply_file = f"/tmp/identity-pre-mutation-reply-{args.identity_id}-{creator_run_id}.txt"
        pre_mutation_send_time_blocker = (
            f"/tmp/identity-pre-mutation-send-time-blocker-{args.identity_id}-{creator_run_id}.json"
        )
        pre_mutation_compose_cmd = [
            "python3",
            "scripts/compose_and_validate_governed_reply.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--body-text",
            "PRE_MUTATION_HEADER_FIRST_GATE",
            "--out-reply-file",
            pre_mutation_reply_file,
            "--blocker-receipt-out",
            pre_mutation_send_time_blocker,
            "--json-only",
        ]
        if args.layer_intent_text.strip():
            pre_mutation_compose_cmd.extend(["--layer-intent-text", args.layer_intent_text.strip()])
        if args.expected_work_layer.strip():
            pre_mutation_compose_cmd.extend(["--work-layer", args.expected_work_layer.strip()])
        if args.expected_source_layer.strip():
            pre_mutation_compose_cmd.extend(["--source-layer", args.expected_source_layer.strip()])
        rc_pre_mutation_header, out_pre_mutation_header, _ = _run_capture(pre_mutation_compose_cmd)
        pre_mutation_header_payload = _parse_json_payload(out_pre_mutation_header) or {}
        header_first_gate_status = (
            "PASS_REQUIRED"
            if rc_pre_mutation_header == 0
            and str(pre_mutation_header_payload.get("send_time_gate_status", "")).strip().upper() == "PASS_REQUIRED"
            else "FAIL_REQUIRED"
        )
        scaffold_consent_gate_status = "PASS_NOT_APPLICABLE"
        resolved_pack_path = Path(str(resolved.get("resolved_pack_path", "")).strip()).expanduser().resolve()
        out_dir_path = Path(args.out_dir).expanduser().resolve()
        default_planned_files = [
            str((out_dir_path / f"{creator_run_id}-patch-plan.json").resolve()),
            str((out_dir_path / f"{creator_run_id}.json").resolve()),
            str((resolved_pack_path / "RULEBOOK.jsonl").resolve()),
            str((resolved_pack_path / "TASK_HISTORY.md").resolve()),
            str((resolved_pack_path / "runtime" / "state" / "prompt_contract.json").resolve()),
        ]
        provided_planned_files = [str(x or "").strip() for x in list(args.planned_file or []) if str(x or "").strip()]
        planned_files = provided_planned_files or default_planned_files
        why_now = str(args.why_now or "").strip() or "identity_update_cycle_pre_mutation_gate"
        mutation_plan_disclosed = bool(planned_files and why_now)
        pre_mutation_gate_error_code = ""
        if header_first_gate_status != "PASS_REQUIRED":
            pre_mutation_gate_error_code = ERR_EXEC_ORDER_HEADER_FIRST
        elif not mutation_plan_disclosed:
            pre_mutation_gate_error_code = ERR_EXEC_ORDER_MUTATION_PLAN
        pre_mutation_gate_receipt = (
            Path(args.pre_mutation_gate_receipt).expanduser().resolve()
            if str(args.pre_mutation_gate_receipt or "").strip()
            else Path(f"/tmp/identity-pre-mutation-gate-update-{args.identity_id}-{creator_run_id}.json")
        )
        _write_json(
            pre_mutation_gate_receipt,
            {
                "identity_id": args.identity_id,
                "operation": "update",
                "run_id": creator_run_id,
                "header_first_gate_status": header_first_gate_status,
                "scaffold_consent_gate_status": scaffold_consent_gate_status,
                "mutation_plan_disclosed": mutation_plan_disclosed,
                "planned_files": planned_files,
                "why_now": why_now,
                "pre_mutation_gate_ts": pre_mutation_gate_ts,
                "pre_mutation_gate_error_code": pre_mutation_gate_error_code,
                "header_gate_blocker_receipt_path": str(
                    pre_mutation_header_payload.get("blocker_receipt_path", "") or pre_mutation_send_time_blocker
                ),
                "status": "PASS_REQUIRED" if not pre_mutation_gate_error_code else "FAIL_REQUIRED",
            },
        )
        print(f"[INFO] pre-mutation gate receipt: {pre_mutation_gate_receipt}")
        if pre_mutation_gate_error_code:
            print(f"[FAIL] update pre-mutation gate failed: {pre_mutation_gate_error_code}")
            return 1
        rc = _run(
            [
                "python3",
                "scripts/validate_identity_instance_isolation.py",
                "--catalog",
                args.catalog,
                "--identity-id",
                args.identity_id,
            ]
        )
        if rc != 0:
            print("[FAIL] instance isolation validation failed; update blocked")
            return rc
        if args.release_session_lane_lock:
            exit_cmd = [
                "python3",
                "scripts/write_session_lane_lock_exit.py",
                "--identity-id",
                args.identity_id,
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--operation",
                "update",
                "--exit-reason",
                str(args.session_lane_lock_exit_reason or "").strip() or "manual_session_lane_lock_exit",
                "--json-only",
            ]
            if args.expected_source_layer.strip():
                exit_cmd.extend(["--source-layer", args.expected_source_layer.strip()])
            rc = _run(exit_cmd)
            if rc != 0:
                print("[FAIL] session lane lock exit emission failed; update blocked")
                return rc
        phase_a_refresh_applied = False
        phase_b_strict_revalidate_status = "NOT_APPLICABLE"
        phase_transition_reason = ""
        phase_transition_error_code = ""

        refresh_validate_cmd = [
            "python3",
            "scripts/validate_identity_session_refresh_status.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "update",
            "--baseline-policy",
            args.baseline_policy,
            "--json-only",
        ]
        rc_refresh, out_refresh, _ = _run_capture(refresh_validate_cmd)
        refresh_payload = _parse_json_payload(out_refresh) or {}
        if rc_refresh != 0:
            stale_reasons = refresh_payload.get("stale_reasons", [])
            if not isinstance(stale_reasons, list):
                stale_reasons = []
            refresh_error = str(refresh_payload.get("error_code", "")).strip()
            baseline_status = str(refresh_payload.get("baseline_status", "")).strip().upper()
            lease_status = str(refresh_payload.get("lease_status", "")).strip().upper()
            pointer_consistency = str(refresh_payload.get("pointer_consistency", "")).strip().upper()
            stale_baseline_codes = {"IP-PBL-001", "IP-PBL-002", "IP-PBL-003", "IP-PBL-004"}
            baseline_error_code = str(refresh_payload.get("baseline_error_code", "")).strip()
            stale_only = (
                str(args.baseline_policy).strip().lower() == "strict"
                and refresh_error == "IP-ASB-RFS-004"
                and baseline_status == "FAIL"
                and baseline_error_code in stale_baseline_codes
                and lease_status in {"", "ACTIVE"}
                and pointer_consistency in {"", "PASS", "WARN"}
                and len(stale_reasons) > 0
                and all(
                    str(x).startswith("baseline_")
                    or str(x).startswith("report_protocol")
                    or str(x) in {"protocol_baseline_non_pass", "live_head_drift_non_blocking"}
                    for x in stale_reasons
                )
            )
            if stale_only:
                phase_a_refresh_applied = True
                phase_transition_reason = "stale_baseline_only_detected"
                refresh_cmd = [
                    "python3",
                    "scripts/refresh_identity_session_status.py",
                    "--catalog",
                    args.catalog,
                    "--repo-catalog",
                    args.repo_catalog,
                    "--identity-id",
                    args.identity_id,
                    "--baseline-policy",
                    "warn",
                    "--json-only",
                ]
                rc_phase_a, _, _ = _run_capture(refresh_cmd)
                if rc_phase_a != 0:
                    phase_b_strict_revalidate_status = "FAIL_REQUIRED"
                    phase_transition_error_code = "IP-UPG-BASE-001"
                    _emit_two_phase_trace(
                        identity_id=args.identity_id,
                        phase_a_refresh_applied=phase_a_refresh_applied,
                        phase_b_strict_revalidate_status=phase_b_strict_revalidate_status,
                        phase_transition_reason=phase_transition_reason,
                        phase_transition_error_code=phase_transition_error_code,
                    )
                    print("[FAIL] strict two-phase refresh unavailable; baseline refresh phase-A failed")
                    return 1
                rc_phase_b, out_phase_b, _ = _run_capture(refresh_validate_cmd)
                phase_b_payload = _parse_json_payload(out_phase_b) or {}
                phase_b_status = str(phase_b_payload.get("session_refresh_status", "")).strip().upper()
                phase_b_strict_revalidate_status = phase_b_status or ("PASS_REQUIRED" if rc_phase_b == 0 else "FAIL_REQUIRED")
                if rc_phase_b != 0:
                    phase_transition_error_code = "IP-UPG-BASE-001"
                    _emit_two_phase_trace(
                        identity_id=args.identity_id,
                        phase_a_refresh_applied=phase_a_refresh_applied,
                        phase_b_strict_revalidate_status=phase_b_strict_revalidate_status,
                        phase_transition_reason=phase_transition_reason,
                        phase_transition_error_code=phase_transition_error_code,
                    )
                    print("[FAIL] strict two-phase refresh phase-B revalidate failed; update blocked")
                    return rc_phase_b
            else:
                phase_b_strict_revalidate_status = "FAIL_REQUIRED"
                if (
                    str(args.baseline_policy).strip().lower() == "strict"
                    and refresh_error == "IP-ASB-RFS-004"
                    and baseline_status == "FAIL"
                ):
                    phase_transition_reason = "baseline_mode_violation"
                    phase_transition_error_code = baseline_error_code or refresh_error
                    _emit_two_phase_trace(
                        identity_id=args.identity_id,
                        phase_a_refresh_applied=phase_a_refresh_applied,
                        phase_b_strict_revalidate_status=phase_b_strict_revalidate_status,
                        phase_transition_reason=phase_transition_reason,
                        phase_transition_error_code=phase_transition_error_code,
                    )
                print("[FAIL] session refresh status validation failed; update blocked")
                return rc_refresh
        else:
            phase_b_strict_revalidate_status = "PASS_REQUIRED"
        protocol_alignment_cmd = [
            "python3",
            "scripts/validate_identity_protocol_version_alignment.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--scope",
            args.scope,
            "--operation",
            "update",
            "--alignment-policy",
            args.baseline_policy,
            "--json-only",
        ]
        rc_pva, out_pva, _ = _run_capture(protocol_alignment_cmd)
        pva_payload = _parse_json_payload(out_pva) or {}
        pva_error_code = str(pva_payload.get("error_code", "")).strip()
        tuple_checks = pva_payload.get("tuple_checks", {})
        if not isinstance(tuple_checks, dict):
            tuple_checks = {}
        pva_freshness_ok = bool(tuple_checks.get("execution_report_freshness", False))
        pva_baseline_ok = bool(tuple_checks.get("protocol_baseline_freshness", False))
        pva_prompt_ok = bool(tuple_checks.get("prompt_activation", False))
        pva_binding_ok = bool(tuple_checks.get("binding_tuple", False))
        legacy_tuple_refresh_allowed = (
            str(args.baseline_policy or "").strip().lower() == "strict"
            and pva_error_code in {"IP-PVA-003", "IP-PVA-004"}
            and pva_freshness_ok
            and pva_baseline_ok
            and (not pva_prompt_ok or not pva_binding_ok)
        )
        if rc_pva != 0 and not legacy_tuple_refresh_allowed:
            print("[FAIL] protocol version alignment validation failed; update blocked")
            return rc_pva
        if rc_pva != 0 and legacy_tuple_refresh_allowed:
            if not phase_transition_reason:
                phase_transition_reason = "legacy_alignment_tuple_refresh"
            if not phase_transition_error_code:
                phase_transition_error_code = pva_error_code
            print(
                "[WARN] protocol version alignment preflight reported legacy prompt/binding tuple drift; "
                "continuing update to refresh execution tuple in-run"
            )
        effective_capability_activation_policy = str(args.capability_activation_policy or "strict-union").strip().lower()
        capability_preflight_cmd = [
            "python3",
            "scripts/validate_identity_capability_activation.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--activation-policy",
            effective_capability_activation_policy,
        ]
        rc_cap, out_cap, _ = _run_capture(capability_preflight_cmd)
        cap_payload = _parse_json_payload(out_cap) or {}
        cap_status = str(cap_payload.get("capability_activation_status", "")).strip().upper()
        cap_error_code = str(cap_payload.get("capability_activation_error_code", "")).strip()
        strict_cap_env_blocked = (
            effective_capability_activation_policy == "strict-union"
            and cap_error_code == "IP-CAP-003"
            and (rc_cap != 0 or cap_status == "BLOCKED")
        )
        if strict_cap_env_blocked:
            print(
                "[WARN] capability activation strict-union blocked by env/auth boundary (IP-CAP-003); "
                "retrying with route-any-ready fallback"
            )
            fallback_cmd = capability_preflight_cmd.copy()
            policy_idx = fallback_cmd.index("--activation-policy")
            fallback_cmd[policy_idx + 1] = "route-any-ready"
            rc_cap, out_cap_fb, _ = _run_capture(fallback_cmd)
            if rc_cap == 0:
                effective_capability_activation_policy = "route-any-ready"
                if not phase_transition_reason:
                    phase_transition_reason = "capability_env_auth_fallback"
                if not phase_transition_error_code:
                    phase_transition_error_code = "IP-CAP-003"
        if rc_cap != 0:
            print("[FAIL] capability activation preflight failed; update blocked")
            return rc_cap
        rc = _run(
            [
                "python3",
                "scripts/validate_discovery_requiredization.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--operation",
                "update",
                "--apply-requiredization",
                "--json-only",
            ]
        )
        if rc != 0:
            print("[FAIL] discovery requiredization validation failed; update blocked")
            return rc
        cmd = [
            "python3",
            "scripts/execute_identity_upgrade.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--mode",
            args.mode,
            "--out-dir",
            args.out_dir,
            "--protocol-root",
            args.protocol_root,
            "--protocol-mode",
            args.protocol_mode,
            "--repo-catalog",
            args.repo_catalog,
            "--run-id",
            creator_run_id,
            "--resolved-scope",
            str(resolved.get("resolved_scope", "")),
            "--resolved-pack-path",
            str(resolved.get("resolved_pack_path", "")),
            "--capability-activation-policy",
            effective_capability_activation_policy,
            "--header-first-gate-status",
            header_first_gate_status,
            "--scaffold-consent-gate-status",
            scaffold_consent_gate_status,
            "--mutation-plan-disclosed",
            "true" if mutation_plan_disclosed else "false",
            "--pre-mutation-gate-ts",
            pre_mutation_gate_ts,
            "--pre-mutation-gate-receipt",
            str(pre_mutation_gate_receipt),
            "--why-now",
            why_now,
        ]
        for planned in planned_files:
            cmd.extend(["--planned-file", str(planned)])
        if args.layer_intent_text.strip():
            cmd.extend(["--layer-intent-text", args.layer_intent_text.strip()])
        if args.expected_work_layer.strip():
            cmd.extend(["--expected-work-layer", args.expected_work_layer.strip()])
        if args.expected_source_layer.strip():
            cmd.extend(["--expected-source-layer", args.expected_source_layer.strip()])
        if phase_a_refresh_applied:
            cmd.append("--phase-a-refresh-applied")
        if phase_b_strict_revalidate_status:
            cmd.extend(["--phase-b-strict-revalidate-status", phase_b_strict_revalidate_status])
        if phase_transition_reason:
            cmd.extend(["--phase-transition-reason", phase_transition_reason])
        if phase_transition_error_code:
            cmd.extend(["--phase-transition-error-code", phase_transition_error_code])
        _emit_two_phase_trace(
            identity_id=args.identity_id,
            phase_a_refresh_applied=phase_a_refresh_applied,
            phase_b_strict_revalidate_status=phase_b_strict_revalidate_status,
            phase_transition_reason=phase_transition_reason,
            phase_transition_error_code=phase_transition_error_code,
        )
        if args.allow_protocol_root_pack:
            cmd.append("--allow-protocol-root-pack")
        return _run(cmd)

    if args.command == "heal":
        return _heal_identity(
            Path(args.repo_catalog),
            Path(args.catalog),
            args.identity_id,
            args.scope,
            args.source_pack,
            args.canonical_root,
            args.apply,
            args.destructive_replace,
            args.out_dir,
        )

    print(f"[FAIL] unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
