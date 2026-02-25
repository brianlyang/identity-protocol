#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import yaml

from resolve_identity_context import resolve_identity


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(catalog_path: Path, identity_id: str) -> tuple[Path, Path]:
    catalog = _load_yaml(catalog_path)
    rows = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity not found in catalog: {identity_id}")
    pack = Path(str(row.get("pack_path", "")).strip()).expanduser().resolve()
    if not pack.exists():
        raise FileNotFoundError(f"pack_path not found: {pack}")
    task = pack / "CURRENT_TASK.json"
    if not task.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found: {task}")
    return pack, task


def _skill_candidates(skill: str, cwd: Path) -> list[Path]:
    names = [skill]
    # weak aliasing for system skill naming conventions.
    if skill.startswith("identity-"):
        names.append(skill.replace("identity-", "skill-", 1))
    roots = [
        cwd / "skills",
        cwd / ".codex" / "skills",
        cwd / ".." / "skills",
        cwd / ".." / ".codex" / "skills",
        cwd / "identity-protocol-local" / "skills",
        Path.home() / ".codex" / "skills",
        Path.home() / ".codex" / "skills" / ".system",
    ]
    out: list[Path] = []
    for root in roots:
        for n in names:
            if root.name == ".system":
                out.append((root / n / "SKILL.md").resolve())
            else:
                out.append((root / n / "SKILL.md").resolve())
                out.append((root / ".system" / n / "SKILL.md").resolve())
    # de-dup preserve order
    seen: set[str] = set()
    dedup: list[Path] = []
    for p in out:
        s = str(p)
        if s in seen:
            continue
        seen.add(s)
        dedup.append(p)
    return dedup


def _find_skill(skill: str, cwd: Path) -> str:
    for p in _skill_candidates(skill, cwd):
        if p.exists():
            return str(p)
    return ""


def _load_mcp_servers(cwd: Path) -> dict[str, str]:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
    cfg_paths = [
        cwd / ".codex" / "config.toml",
        cwd / ".." / ".codex" / "config.toml",
        codex_home / "config.toml",
    ]
    servers: dict[str, str] = {}
    for cfg in cfg_paths:
        if not cfg.exists():
            continue
        try:
            data = tomllib.loads(cfg.read_text(encoding="utf-8"))
        except Exception:
            continue
        raw = data.get("mcp_servers") or {}
        if not isinstance(raw, dict):
            continue
        for name in raw.keys():
            servers[str(name)] = str(cfg)
    return servers


def _collect_contract(pack: Path, task_path: Path) -> dict[str, Any]:
    task = _load_json(task_path)
    c = (task.get("capability_orchestration_contract") or {}) if isinstance(task, dict) else {}
    routes = c.get("task_type_routes") or {}
    required_skills: set[str] = set()
    required_mcp: set[str] = set()
    tool_routes: list[dict[str, Any]] = []
    for route_name, route in routes.items():
        if not isinstance(route, dict):
            continue
        for s in route.get("primary_skills") or []:
            if str(s).strip():
                required_skills.add(str(s).strip())
        for s in route.get("fallback_skills") or []:
            if str(s).strip():
                required_skills.add(str(s).strip())
        for m in route.get("required_mcp") or []:
            if str(m).strip():
                required_mcp.add(str(m).strip())
        tool_routes.append(
            {
                "route": str(route_name),
                "pipeline": route.get("pipeline") or [],
                "max_tool_calls": route.get("max_tool_calls"),
                "max_runtime_minutes": route.get("max_runtime_minutes"),
            }
        )
    return {
        "required": bool(c.get("required", False)),
        "required_skills": sorted(required_skills),
        "required_mcp": sorted(required_mcp),
        "preflight_requirements": [str(x) for x in (c.get("preflight_requirements") or []) if str(x).strip()],
        "tool_routes": tool_routes,
        "pack_path": str(pack),
        "task_path": str(task_path),
    }


def _check_gh_cli() -> bool:
    return subprocess.call(["bash", "-lc", "command -v gh >/dev/null 2>&1"]) == 0


def _check_gh_auth_status() -> tuple[bool, str]:
    """
    Returns:
      (auth_ready, detail_reason)
    """
    if not _check_gh_cli():
        return False, "gh_cli_missing"
    cmds = [
        ["gh", "auth", "status", "-h", "github.com"],
        ["gh", "auth", "status"],
    ]
    for cmd in cmds:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        msg = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip().lower()
        if "failed to log in" in msg:
            return False, "gh_auth_invalid"
        if "invalid" in msg:
            return False, "gh_auth_invalid"
        if "not logged into any hosts" in msg or "run: gh auth login" in msg:
            return False, "gh_auth_missing"
        if proc.returncode == 0:
            return True, "gh_auth_ready"
    return False, "gh_auth_not_ready"


def _derive_activation_mode(catalog: Path) -> str:
    p = str(catalog)
    if "/.agents/identity/" in p:
        return "project"
    if "/.codex/identity/" in p:
        return "global"
    return "unknown"


def _build_runtime_payload(
    *,
    identity_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
) -> dict[str, Any]:
    pack, task_path = _resolve_current_task(catalog_path, identity_id)
    contract = _collect_contract(pack, task_path)
    cwd = Path.cwd().resolve()
    skill_rows: list[dict[str, Any]] = []
    active_skills: list[str] = []
    missing_skills: list[str] = []
    for skill in contract["required_skills"]:
        found = _find_skill(skill, cwd)
        row = {"skill": skill, "available": bool(found), "path": found}
        skill_rows.append(row)
        if found:
            active_skills.append(skill)
        else:
            missing_skills.append(skill)

    mcp_servers = _load_mcp_servers(cwd)
    gh_cli_present = _check_gh_cli()
    gh_auth_ready, gh_auth_reason = _check_gh_auth_status()
    mcp_rows: list[dict[str, Any]] = []
    mcp_tools_used: list[str] = []
    missing_mcp: list[str] = []
    missing_mcp_auth: list[str] = []
    for name in contract["required_mcp"]:
        ok = False
        reason = ""
        source = ""
        if name == "github":
            source = mcp_servers.get(name, "gh_cli" if gh_cli_present else "")
            if gh_auth_ready:
                ok = True
                reason = "github_auth_ready"
            else:
                ok = False
                reason = f"github_auth_not_ready:{gh_auth_reason}"
                missing_mcp_auth.append(name)
        elif name in mcp_servers:
            ok = True
            source = mcp_servers[name]
            reason = "configured_in_codex_config"
        else:
            reason = "not_configured"
        row = {"mcp": name, "available": ok, "source": source, "reason": reason}
        mcp_rows.append(row)
        if ok:
            mcp_tools_used.append(name)
        else:
            missing_mcp.append(name)

    status = "ACTIVATED"
    error_code = ""
    notes: list[str] = []
    if missing_skills:
        status = "BLOCKED"
        error_code = "IP-CAP-001"
        notes.append(f"missing_skills={missing_skills}")
    if missing_mcp:
        status = "BLOCKED"
        error_code = "IP-CAP-002"
        notes.append(f"missing_mcp={missing_mcp}")
    if missing_mcp_auth:
        status = "BLOCKED"
        error_code = "IP-CAP-003"
        notes.append(f"mcp_auth_not_ready={missing_mcp_auth}")
    if not contract["required"]:
        status = "NOT_REQUIRED"
        error_code = ""
    ctx = resolve_identity(
        identity_id,
        repo_catalog_path.expanduser().resolve(),
        catalog_path.expanduser().resolve(),
        allow_conflict=True,
    )
    return {
        "identity_id": identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack),
        "task_path": str(task_path),
        "resolved_scope": str(ctx.get("resolved_scope", "")),
        "resolved_pack_path": str(ctx.get("resolved_pack_path", "")),
        "activation_mode": _derive_activation_mode(catalog_path),
        "preflight_requirements_checked": contract["preflight_requirements"],
        "required_skills": contract["required_skills"],
        "required_mcp": contract["required_mcp"],
        "github_cli_present": gh_cli_present,
        "github_auth_ready": gh_auth_ready,
        "github_auth_status_detail": gh_auth_reason,
        "skills_checked": skill_rows,
        "active_skills": active_skills,
        "mcp_servers_checked": mcp_rows,
        "mcp_servers": sorted(mcp_servers.keys()),
        "skills_used": active_skills,
        "mcp_tools_used": mcp_tools_used,
        "tool_calls_used": ["validate_identity_capability_activation"],
        "tool_routes": contract["tool_routes"],
        "capability_contract_required": bool(contract.get("required", False)),
        "capability_activation_status": status,
        "capability_activation_error_code": error_code,
        "capability_activation_notes": notes,
    }


def _validate_report(path: Path, require_activated: bool) -> tuple[bool, str]:
    data = _load_json(path)
    required = [
        "skills_used",
        "mcp_tools_used",
        "tool_calls_used",
        "active_skills",
        "mcp_servers_checked",
        "tool_routes",
        "capability_activation_status",
        "capability_activation_error_code",
        "capability_contract_required",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"report_missing_fields:{missing}"
    status = str(data.get("capability_activation_status", "")).strip().upper()
    if require_activated and status != "ACTIVATED":
        return False, f"capability_activation_status_not_activated:{status}"
    if not isinstance(data.get("skills_used"), list):
        return False, "skills_used_must_be_list"
    if not isinstance(data.get("mcp_tools_used"), list):
        return False, "mcp_tools_used_must_be_list"
    if not isinstance(data.get("tool_calls_used"), list):
        return False, "tool_calls_used_must_be_list"
    if not isinstance(data.get("active_skills"), list):
        return False, "active_skills_must_be_list"
    if not isinstance(data.get("mcp_servers_checked"), list):
        return False, "mcp_servers_checked_must_be_list"
    if not isinstance(data.get("tool_routes"), list):
        return False, "tool_routes_must_be_list"
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity capability activation (skill/mcp/tool attachment preflight).")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--report", default="")
    ap.add_argument("--require-activated", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if args.report.strip():
        report_path = Path(args.report).expanduser().resolve()
        if not report_path.exists():
            print(f"[FAIL] report not found: {report_path}")
            return 1
        ok, reason = _validate_report(report_path, require_activated=bool(args.require_activated))
        if not ok:
            print(f"[FAIL] {reason}")
            return 1
        print(f"[OK] capability activation report validated: {report_path}")
        return 0

    if not args.catalog.strip():
        print("[FAIL] --catalog is required when validating live capability activation (non-report mode)")
        return 1
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()

    try:
        payload = _build_runtime_payload(identity_id=args.identity_id, catalog_path=catalog_path, repo_catalog_path=repo_catalog_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    if args.out.strip():
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = str(payload.get("capability_activation_status", "BLOCKED"))
    if args.require_activated and status != "ACTIVATED":
        print(f"[FAIL] capability activation not ready: status={status} error={payload.get('capability_activation_error_code')}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if status in {"BLOCKED", "ERROR"}:
        print(f"[WARN] capability activation not fully ready: status={status} error={payload.get('capability_activation_error_code')}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"[OK] capability activation validated: identity={args.identity_id} status={status}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
