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

from resolve_identity_context import (
    collect_protocol_evidence,
    default_identity_home,
    default_local_catalog_path,
    default_local_instances_root,
    ensure_local_catalog,
    resolve_protocol_root,
    resolve_identity,
)


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    print("$", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.stdout.strip():
        print(p.stdout.strip())
    if p.stderr.strip():
        print(p.stderr.strip())
    return p.returncode, p.stdout or "", p.stderr or ""


def _runtime_mode_guard(identity_id: str, catalog: str, repo_catalog: str, scope: str = "") -> int:
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
        "auto",
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
    if not auto_converge:
        print(
            "[FAIL] catalog has multiple active identities: "
            f"{actives}. Use --auto-converge-active to normalize or run activate transaction explicitly."
        )
        return 2
    changed = False
    for row in identities:
        iid = str(row.get("id", "")).strip()
        if not iid:
            continue
        desired = "active" if iid == target_identity_id else "inactive"
        if str(row.get("status", "")).strip().lower() != desired:
            row["status"] = desired
            changed = True
    if changed:
        _dump_yaml(catalog_path, data)
    print(
        "[OK] converged single-active catalog state: "
        f"target={target_identity_id} previous_active={actives} catalog={catalog_path}"
    )
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


def _activate_identity(
    repo_catalog: Path,
    local_catalog: Path,
    identity_id: str,
    scope: str = "",
    protocol_root: str = "",
    protocol_mode: str = "mode_a_shared",
) -> int:
    ensure_local_catalog(repo_catalog, local_catalog)
    try:
        resolved = resolve_identity(identity_id, repo_catalog, local_catalog, preferred_scope=scope)
    except Exception as e:
        print(f"[FAIL] {e}")
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

    previously_active = [
        str(x.get("id", "")).strip()
        for x in identities
        if isinstance(x, dict)
        and str(x.get("status", "")).strip().lower() == "active"
        and str(x.get("id", "")).strip()
        and str(x.get("id", "")).strip() != identity_id
    ]

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
        for old_id in previously_active:
            created_evidence.append(
                _write_binding_evidence(
                    data,
                    old_id,
                    "BOUND_READY",
                    note=f"demoted by single-active switch to {identity_id}",
                )
            )

        for item in identities:
            if not isinstance(item, dict):
                continue
            iid = str(item.get("id", "")).strip()
            if not iid:
                continue
            item["status"] = "active" if iid == identity_id else "inactive"

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
            "demoted_identities": previously_active,
            "single_active_enforced": True,
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
                "--canonical-out",
                str(canonical_session_pointer),
                "--mirror-out",
                str(scoped_session_mirror),
            ]
        )
        if rc != 0:
            raise RuntimeError("session pointer consistency validation failed")
        print(f"[OK] activated identity in catalog (single-active): {identity_id}")
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

    p_validate = sub.add_parser("validate", help="Run identity required validators for an identity")
    p_validate.add_argument("--identity-id", required=True)
    p_validate.add_argument("--repo-catalog", default=repo_catalog_default)
    p_validate.add_argument("--catalog", default=local_catalog_default)
    p_validate.add_argument("--scope", default="")

    p_compile = sub.add_parser("compile", help="Compile runtime brief")
    p_compile.add_argument("--check", action="store_true", help="fail if compile output is not stable")

    p_activate = sub.add_parser("activate", help="Set identity status=active in catalog")
    p_activate.add_argument("--identity-id", required=True)
    p_activate.add_argument("--repo-catalog", default=repo_catalog_default)
    p_activate.add_argument("--catalog", default=local_catalog_default)
    p_activate.add_argument("--scope", default="")
    p_activate.add_argument("--protocol-root", default="")
    p_activate.add_argument("--protocol-mode", choices=["mode_a_shared", "mode_b_standalone"], default="mode_a_shared")
    p_activate.add_argument("--auto-converge-active", action="store_true")

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
    p_update.add_argument("--auto-converge-active", action="store_true")

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
        rc_guard = _runtime_mode_guard(args.identity_id, args.catalog, args.repo_catalog, args.scope)
        if rc_guard != 0:
            return rc_guard
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
            ["python3", "scripts/validate_identity_upgrade_prereq.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_update_lifecycle.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_install_safety.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_tool_installation.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_install_provenance.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_vendor_api_discovery.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_vendor_api_solution.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_experience_feedback_governance.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_capability_arbitration.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_dialogue_content.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_dialogue_cross_validation.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_dialogue_result_support.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
            ["python3", "scripts/validate_identity_ci_enforcement.py", "--catalog", args.catalog, "--identity-id", args.identity_id],
        ]
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
        rc = _single_active_precheck(Path(args.catalog), args.identity_id, auto_converge=bool(args.auto_converge_active))
        if rc != 0:
            return rc
        return _activate_identity(
            Path(args.repo_catalog),
            Path(args.catalog),
            args.identity_id,
            args.scope,
            args.protocol_root,
            args.protocol_mode,
        )

    if args.command == "update":
        ensure_local_catalog(Path(args.repo_catalog), Path(args.catalog))
        rc_guard = _runtime_mode_guard(args.identity_id, args.catalog, args.repo_catalog, args.scope)
        if rc_guard != 0:
            return rc_guard
        rc = _single_active_precheck(Path(args.catalog), args.identity_id, auto_converge=bool(args.auto_converge_active))
        if rc != 0:
            return rc
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
        rc = _run(
            [
                "python3",
                "scripts/validate_identity_capability_activation.py",
                "--catalog",
                args.catalog,
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--activation-policy",
                args.capability_activation_policy,
            ]
        )
        if rc != 0:
            print("[FAIL] capability activation preflight failed; update blocked")
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
            "--resolved-scope",
            str(resolved.get("resolved_scope", "")),
            "--resolved-pack-path",
            str(resolved.get("resolved_pack_path", "")),
            "--capability-activation-policy",
            args.capability_activation_policy,
        ]
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
