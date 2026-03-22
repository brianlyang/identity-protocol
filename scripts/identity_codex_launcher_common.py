#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import Any

from actor_session_common import resolve_required_protocol_actor_id
from instance_script_orchestration_common import resolve_pack_task
from resolve_identity_context import default_local_catalog_path, resolve_identity, resolve_protocol_root
from runtime_temp_path_common import runtime_temp_file

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY = "identity_codex_launcher_contract_v1"
IDENTITY_CODEX_LAUNCHER_CONTRACT_ID = "identity_codex_launcher_contract_v1"
IDENTITY_CODEX_LAUNCHER_RENDERER_ID = "scripts/render_identity_codex_launcher.py"
IDENTITY_CODEX_LAUNCHER_INSTALLER_ID = "scripts/install_identity_codex_launcher.py"
IDENTITY_CODEX_LAUNCHER_VALIDATOR_ID = "scripts/validate_identity_codex_launcher.py"
IDENTITY_CODEX_LAUNCHER_CONVERGENCE_ENTRY_ID = "scripts/run_identity_codex_launcher_workspace_convergence.py"
IDENTITY_CODEX_LAUNCHER_CONVERGENCE_RECEIPT_FAMILY = (
    "identity_codex_launcher_workspace_convergence_receipt_v1"
)
IDENTITY_CODEX_LAUNCHER_CONVERGENCE_MUTATION_SCOPE = "transitive_backfill_plus_launcher_install"

IDENTITY_CODEX_LAUNCHERS_DIR_REL = Path("scripts/launchers")
IDENTITY_CODEX_LAUNCHER_MANIFEST_REL = IDENTITY_CODEX_LAUNCHERS_DIR_REL / "identity-codex-launcher.manifest.json"
IDENTITY_CODEX_LAUNCHER_README_REL = IDENTITY_CODEX_LAUNCHERS_DIR_REL / "README.md"

GENERIC_LAUNCHER_NAME = "identity-codex"
IDENTITY_SHORTCUT_PREFIX = "id-"
GENERIC_LAUNCHER_BIN_REL = Path("bin") / GENERIC_LAUNCHER_NAME

FORBIDDEN_RUNTIME_OVERRIDE_KEYS: tuple[str, ...] = (
    "model_instructions_file",
    "project_doc_fallback_filenames",
)
RUNTIME_PATHS_CONFIG_REL = Path("config") / "runtime-paths.env"
PROJECT_DOC_FALLBACK_PREFIX = ".IDENTITY."


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text_if_changed(path: Path, text: str, *, executable: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    changed = not path.exists() or path.read_text(encoding="utf-8") != text
    if changed:
        path.write_text(text, encoding="utf-8")
    if executable:
        current_mode = path.stat().st_mode if path.exists() else 0o644
        desired_mode = current_mode | 0o755
        if current_mode != desired_mode:
            os.chmod(path, desired_mode)
            changed = True
    return changed


def _repo_catalog_path(protocol_home: Path) -> Path:
    return (protocol_home / "identity" / "catalog" / "identities.yaml").resolve()


def _run_json(cmd: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed rc={proc.returncode}: {' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"expected JSON output from {' '.join(cmd)}; got: {proc.stdout}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected object JSON from {' '.join(cmd)}")
    return payload


def default_codex_home() -> Path:
    raw = str(os.environ.get("CODEX_HOME", "")).strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def default_identity_home() -> Path:
    raw = str(os.environ.get("IDENTITY_HOME", "")).strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (default_codex_home() / ".identity").resolve()


def default_bin_dir() -> Path:
    return (default_codex_home() / "bin").resolve()


def runtime_paths_config_path(identity_home: Path | None = None) -> Path:
    root = identity_home if identity_home is not None else default_identity_home()
    return (root / RUNTIME_PATHS_CONFIG_REL).resolve()


def runtime_identity_home_for_catalog(catalog_path: Path) -> Path:
    return catalog_path.parent.resolve()


def read_runtime_paths_config(identity_home: Path | None = None) -> dict[str, str]:
    config_path = runtime_paths_config_path(identity_home)
    if not config_path.exists():
        return {}
    payload: dict[str, str] = {}
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = str(raw_line or "").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = str(key or "").strip()
        value = str(value or "").strip()
        if not key:
            continue
        payload[key] = value
    return payload


def write_runtime_paths_config(
    *,
    identity_home: Path,
    protocol_home: Path,
    runtime_identity_home: Path | None = None,
    runtime_catalog: Path | None = None,
) -> Path:
    config_home = identity_home.resolve()
    target_identity_home = (runtime_identity_home or config_home).resolve()
    target_catalog = (runtime_catalog or (target_identity_home / "catalog.local.yaml")).resolve()
    config_path = runtime_paths_config_path(config_home)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        "# identity runtime shared path config\n"
        "# priority: environment variable > this file > built-in fallback\n"
        f"IDENTITY_HOME={target_identity_home}\n"
        f"IDENTITY_CATALOG={target_catalog}\n"
        f"IDENTITY_PROTOCOL_HOME={protocol_home.resolve()}\n"
    )
    config_path.write_text(payload, encoding="utf-8")
    return config_path


def resolve_catalog_path(raw_catalog: str) -> Path:
    token = str(raw_catalog or "").strip()
    if token:
        return Path(token).expanduser().resolve()
    env_catalog = str(os.environ.get("IDENTITY_CATALOG", "")).strip()
    if env_catalog:
        return Path(env_catalog).expanduser().resolve()
    return default_local_catalog_path(start=Path.cwd())


def resolve_launcher_pack_task(
    *,
    identity_id: str,
    catalog_path: Path | None = None,
    current_task: str = "",
) -> tuple[Path, Path, dict[str, Any]]:
    return resolve_pack_task(
        catalog_path=catalog_path,
        current_task=current_task,
        identity_id=identity_id,
    )


def launcher_manifest_path(pack_root: Path) -> Path:
    return (pack_root / IDENTITY_CODEX_LAUNCHER_MANIFEST_REL).resolve()


def launcher_readme_path(pack_root: Path) -> Path:
    return (pack_root / IDENTITY_CODEX_LAUNCHER_README_REL).resolve()


def shortcut_launcher_name(identity_id: str) -> str:
    return f"{IDENTITY_SHORTCUT_PREFIX}{str(identity_id or '').strip()}"


def launcher_contract_skeleton(identity_id: str) -> dict[str, Any]:
    identity_token = str(identity_id or "").strip()
    return {
        "required": True,
        "contract_id": IDENTITY_CODEX_LAUNCHER_CONTRACT_ID,
        "validator": IDENTITY_CODEX_LAUNCHER_VALIDATOR_ID,
        "renderer": IDENTITY_CODEX_LAUNCHER_RENDERER_ID,
        "installer": IDENTITY_CODEX_LAUNCHER_INSTALLER_ID,
        "pack_manifest_relpath": IDENTITY_CODEX_LAUNCHER_MANIFEST_REL.as_posix(),
        "pack_readme_relpath": IDENTITY_CODEX_LAUNCHER_README_REL.as_posix(),
        "generic_command": GENERIC_LAUNCHER_NAME,
        "shortcut_command": shortcut_launcher_name(identity_token),
        "installed_bin_dir": "${CODEX_HOME}/bin",
        "generic_launcher_filename": GENERIC_LAUNCHER_NAME,
        "shortcut_launcher_filename": shortcut_launcher_name(identity_token),
        "forbidden_runtime_overrides": list(FORBIDDEN_RUNTIME_OVERRIDE_KEYS),
        "bootstrap_owner_streams": ["v1.6.12", "v1.6.13", "v1.6.14"],
        "process_entry_injection": {
            "model_instructions_file_owner": True,
            "project_doc_fallback_owner": True,
            "shared_global_config_mutation_forbidden": True,
        },
    }


def _deep_merge_defaults(base: Any, cur: Any) -> Any:
    if isinstance(base, dict):
        result: dict[str, Any] = {}
        cur_dict = cur if isinstance(cur, dict) else {}
        for key, value in base.items():
            if key in cur_dict:
                result[key] = _deep_merge_defaults(value, cur_dict[key])
            else:
                result[key] = value
        for key, value in cur_dict.items():
            if key not in result:
                result[key] = value
        return result
    if isinstance(base, list):
        if isinstance(cur, list) and cur:
            return cur
        return list(base)
    if cur in (None, "", []):
        return base
    return cur


def ensure_launcher_contract(task_doc: dict[str, Any], identity_id: str) -> bool:
    base = launcher_contract_skeleton(identity_id)
    current = task_doc.get(IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY)
    merged = _deep_merge_defaults(base, current if isinstance(current, dict) else {})
    changed = merged != current
    task_doc[IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY] = merged
    return changed


def launcher_required(task_doc: dict[str, Any], pack_root: Path) -> bool:
    if isinstance(task_doc.get(IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY), dict):
        return True
    return launcher_manifest_path(pack_root).exists() or launcher_readme_path(pack_root).exists()


def launcher_manifest_doc(identity_id: str) -> dict[str, Any]:
    identity_token = str(identity_id or "").strip()
    return {
        "manifest_version": "v1",
        "identity_id": identity_token,
        "contract_id": IDENTITY_CODEX_LAUNCHER_CONTRACT_ID,
        "validator": IDENTITY_CODEX_LAUNCHER_VALIDATOR_ID,
        "renderer": IDENTITY_CODEX_LAUNCHER_RENDERER_ID,
        "installer": IDENTITY_CODEX_LAUNCHER_INSTALLER_ID,
        "generic_command": GENERIC_LAUNCHER_NAME,
        "shortcut_command": shortcut_launcher_name(identity_token),
        "pack_manifest_relpath": IDENTITY_CODEX_LAUNCHER_MANIFEST_REL.as_posix(),
        "pack_readme_relpath": IDENTITY_CODEX_LAUNCHER_README_REL.as_posix(),
        "installed_bin_dir": "${CODEX_HOME}/bin",
        "generic_launcher_filename": GENERIC_LAUNCHER_NAME,
        "shortcut_launcher_filename": shortcut_launcher_name(identity_token),
        "forbidden_runtime_overrides": list(FORBIDDEN_RUNTIME_OVERRIDE_KEYS),
        "process_entry_artifacts": {
            "bootstrap_file_kind": "model_instructions_file",
            "fallback_file_kind": "project_doc_fallback_filenames",
            "fallback_file_prefix": PROJECT_DOC_FALLBACK_PREFIX,
        },
    }


def launcher_readme_text(identity_id: str) -> str:
    identity_token = str(identity_id or "").strip() or "<identity-id>"
    shortcut = shortcut_launcher_name(identity_token)
    return f"""# Identity Codex Launchers

This directory is the canonical pack-local launcher metadata surface for
`{identity_token}` under `v1.6.14`.

Canonical commands:

- Generic launcher:
  - `identity-codex --identity-id {identity_token} -- <codex args>`
- Convenience launcher:
  - `{shortcut} <codex args>`

Canonical installed home:

- `${{CODEX_HOME}}/bin/identity-codex`
- `${{CODEX_HOME}}/bin/{shortcut}`

Boundary:

- Pack-local launcher metadata lives only under `scripts/launchers/`.
- Installed executable shims live only under `${{CODEX_HOME}}/bin/`.
- `runtime/` and `scripts/identity/` are non-canonical launcher homes.
- Launcher-owned startup injection owns `model_instructions_file` and
  `project_doc_fallback_filenames` for the launched process and fail-closes on
  manual override attempts.
"""


def ensure_launcher_assets(pack_root: Path, identity_id: str) -> dict[str, Any]:
    manifest_path = launcher_manifest_path(pack_root)
    readme_path = launcher_readme_path(pack_root)
    manifest_doc = launcher_manifest_doc(identity_id)
    manifest_text = json.dumps(manifest_doc, ensure_ascii=False, indent=2) + "\n"
    manifest_changed = _write_text_if_changed(manifest_path, manifest_text)
    readme_changed = _write_text_if_changed(readme_path, launcher_readme_text(identity_id))
    return {
        "manifest_path": str(manifest_path),
        "readme_path": str(readme_path),
        "manifest_changed": manifest_changed,
        "readme_changed": readme_changed,
    }


def render_generic_launcher_sh() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

resolve_default_codex_home() {
  if [[ -n "${CODEX_HOME:-}" ]]; then
    printf '%s\\n' "${CODEX_HOME}"
    return 0
  fi
  printf '%s\\n' "${HOME}/.codex"
}

load_runtime_paths_file() {
  local config_path="$1"
  [[ -f "${config_path}" ]] || return 0
  while IFS='=' read -r key value; do
    [[ -n "${key}" ]] || continue
    [[ "${key}" =~ ^# ]] && continue
    case "${key}" in
      IDENTITY_HOME|IDENTITY_CATALOG|IDENTITY_PROTOCOL_HOME)
        if [[ -z "${!key:-}" ]]; then
          value="${value%$'\\r'}"
          value="${value#\\\"}"
          value="${value%\\\"}"
          value="${value#\\'}"
          value="${value%\\'}"
          export "${key}=${value}"
        fi
        ;;
    esac
  done < "${config_path}"
}

CODEX_HOME="$(resolve_default_codex_home)"
export CODEX_HOME
if [[ -z "${IDENTITY_HOME:-}" ]]; then
  export IDENTITY_HOME="${CODEX_HOME}/.identity"
fi
load_runtime_paths_file "${IDENTITY_HOME}/config/runtime-paths.env"

if [[ -z "${IDENTITY_PROTOCOL_HOME:-}" ]]; then
  echo "[FAIL] IP-ILAUNCH-001 protocol home unresolved; export IDENTITY_PROTOCOL_HOME or refresh runtime-paths.env via install_identity_codex_launcher.py." >&2
  exit 1
fi

exec python3 "${IDENTITY_PROTOCOL_HOME}/scripts/render_identity_codex_launcher.py" exec "$@"
"""


def render_shortcut_launcher_sh(identity_id: str) -> str:
    shortcut = shortcut_launcher_name(identity_id)
    return f"""#!/usr/bin/env bash
set -euo pipefail

LAUNCHER_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# identity-codex shortcut shim
# contract_id={IDENTITY_CODEX_LAUNCHER_CONTRACT_ID}
# identity_id={identity_id}
# shortcut_name={shortcut}

exec "${{LAUNCHER_DIR}}/{GENERIC_LAUNCHER_NAME}" --identity-id {shlex.quote(identity_id)} -- "$@"
"""


def install_launcher_shims(*, identity_id: str, bin_dir: Path) -> dict[str, Any]:
    bin_root = bin_dir.expanduser().resolve()
    bin_root.mkdir(parents=True, exist_ok=True)
    generic_path = (bin_root / GENERIC_LAUNCHER_NAME).resolve()
    shortcut_path = (bin_root / shortcut_launcher_name(identity_id)).resolve()
    generic_changed = _write_text_if_changed(generic_path, render_generic_launcher_sh(), executable=True)
    shortcut_changed = _write_text_if_changed(shortcut_path, render_shortcut_launcher_sh(identity_id), executable=True)
    return {
        "bin_dir": str(bin_root),
        "generic_launcher_path": str(generic_path),
        "shortcut_launcher_path": str(shortcut_path),
        "generic_changed": generic_changed,
        "shortcut_changed": shortcut_changed,
    }


def _normalize_run_session_id(raw: str, *, source: str) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    if not value.startswith("run:"):
        raise RuntimeError(
            f"invalid identity session_id from {source}: {value!r}; "
            "identity session ids must use run:<...>; codex resume thread UUIDs are host-thread ids only"
        )
    return value


def _resolve_explicit_or_env_session_id(explicit_session_id: str) -> tuple[str, str]:
    explicit = _normalize_run_session_id(explicit_session_id, source="explicit_session_id")
    if explicit:
        return explicit, "explicit_session_id"
    codex_session = _normalize_run_session_id(str(os.environ.get("CODEX_SESSION_ID", "")).strip(), source="CODEX_SESSION_ID")
    identity_session = _normalize_run_session_id(
        str(os.environ.get("IDENTITY_SESSION_ID", "")).strip(),
        source="IDENTITY_SESSION_ID",
    )
    if codex_session and identity_session and codex_session != identity_session:
        raise RuntimeError(
            "current-turn session tuple mismatch: CODEX_SESSION_ID != IDENTITY_SESSION_ID; "
            "compatibility pointer fallback is forbidden"
        )
    session_id = codex_session or identity_session
    if session_id:
        return session_id, "current_turn_session_tuple"
    return "", "session_context_missing"


def resolve_bound_session_id_for_identity(*, protocol_home: Path, catalog_path: Path, actor_id: str, identity_id: str) -> tuple[str, str]:
    script_dir = (protocol_home / "scripts").resolve()
    if str(script_dir) not in os.sys.path:
        os.sys.path.insert(0, str(script_dir))
    from actor_session_common import resolve_bound_session_id_for_identity as _resolve_bound_session_id  # type: ignore

    session_id, source = _resolve_bound_session_id(
        catalog_path,
        actor_id,
        identity_id,
        explicit_session_id="",
    )
    return str(session_id or "").strip(), str(source or "binding_missing").strip()


def resolve_launcher_identity_context(
    *,
    identity_id: str,
    actor_id: str,
    catalog_path: Path,
    protocol_home: Path,
) -> dict[str, Any]:
    resolved = resolve_identity(
        identity_id,
        _repo_catalog_path(protocol_home),
        catalog_path,
        preferred_scope="USER",
    )
    resolved_catalog_path = Path(str(resolved.get("catalog_path", "")).strip()).expanduser().resolve()
    if resolved_catalog_path != catalog_path:
        raise RuntimeError(
            f"runtime drift detected: resolved catalog_path={resolved_catalog_path} expected={catalog_path}; "
            "fix the local runtime selection before launching"
        )
    return resolved


def resolve_launcher_runtime_authority(
    *,
    identity_id: str,
    actor_id: str,
    session_id: str,
    catalog_path: Path,
    protocol_home: Path,
) -> dict[str, Any]:
    return _run_json(
        [
            "python3",
            str((protocol_home / "scripts" / "resolve_runtime_authoritative_identity.py").resolve()),
            "--catalog",
            str(catalog_path),
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        cwd=Path.cwd(),
    )


def resolve_launcher_tuple(
    *,
    identity_id: str,
    actor_id: str,
    explicit_session_id: str,
    catalog_path: Path,
    protocol_home: Path,
) -> tuple[str, str]:
    explicit = str(explicit_session_id or "").strip()
    if explicit:
        current_session_id, current_session_source = _resolve_explicit_or_env_session_id(explicit)
        if current_session_id:
            return current_session_id, current_session_source
    session_id, session_source = resolve_bound_session_id_for_identity(
        protocol_home=protocol_home,
        catalog_path=catalog_path,
        actor_id=actor_id,
        identity_id=identity_id,
    )
    if not session_id:
        raise RuntimeError(
            "current-turn session tuple unresolved: no authoritative bound session_id found for the current identity"
        )
    return session_id, session_source


def _prompt_version(pack_path: Path) -> str:
    task_path = (pack_path / "CURRENT_TASK.json").resolve()
    if not task_path.exists():
        return ""
    try:
        payload = _load_json(task_path)
    except Exception:
        return ""
    agent_identity = payload.get("agent_identity")
    if isinstance(agent_identity, dict):
        return str(agent_identity.get("prompt_version", "")).strip()
    return ""


def _machine_template(protocol_home: Path) -> dict[str, Any]:
    template_path = (
        protocol_home
        / "identity"
        / "protocol"
        / "plugins"
        / "templates"
        / "native-chat-headstamp.machine_verification_profiles_v1.json"
    )
    return _load_json(template_path)


def _render_success_identity_line(
    *,
    actor_id: str,
    identity_id: str,
    scope: str,
    source_layer: str,
    work_layer: str,
) -> str:
    return (
        f"Identity-Context: actor_id={actor_id}; identity_id={identity_id}; "
        f"scope={scope}; lock=LOCK_MATCH; source={source_layer} | "
        f"Layer-Context: work_layer={work_layer}; source_layer={source_layer}"
    )


def _render_failure_identity_line(
    *,
    actor_id: str,
    requested_identity_id: str,
    conflict: str,
    scope: str,
    source_layer: str,
    work_layer: str,
) -> str:
    return (
        f"Identity-Context: withheld; actor_id={actor_id}; requested_identity_id={requested_identity_id or 'unknown'}; "
        f"conflict={conflict}; scope={scope or 'unknown'}; source={source_layer or 'unknown'} | "
        f"Layer-Context: work_layer={work_layer}; source_layer={source_layer or 'unknown'}"
    )


def _format_machine_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value).strip()


def _render_machine_line(payload: dict[str, Any], *, field_order: list[str], include_extra_fields: bool) -> str:
    ordered_parts: list[str] = []
    seen: set[str] = set()
    for key in field_order:
        rendered = _format_machine_value(payload.get(key))
        if rendered == "":
            continue
        ordered_parts.append(f"{key}={rendered}")
        seen.add(key)
    if include_extra_fields:
        for key in sorted(payload.keys()):
            if key in seen:
                continue
            rendered = _format_machine_value(payload.get(key))
            if rendered == "":
                continue
            ordered_parts.append(f"{key}={rendered}")
    return "Machine-Verification: " + "; ".join(ordered_parts)


def _authority_source(resolution_mode: str) -> str:
    token = str(resolution_mode or "").strip()
    if token == "actor_binding_session_scoped":
        return "actor_session_store"
    return token or "actor_session_store"


def _failure_conflict(authority: dict[str, Any]) -> str:
    resolution_mode = str(authority.get("resolution_mode", "")).strip()
    if resolution_mode == "session_context_missing":
        return "UNRESOLVED_CURRENT_TURN_MACHINE_TUPLE"
    error_code = str(authority.get("error_code", "")).strip()
    if error_code:
        return error_code.replace("-", "_")
    stale_reasons = authority.get("stale_reasons") or []
    if isinstance(stale_reasons, list) and stale_reasons:
        return str(stale_reasons[0]).strip().replace(":", "_").replace("-", "_").upper()
    return "UNRESOLVED_CURRENT_TURN_MACHINE_TUPLE"


def _success_machine_payload(
    *,
    authority: dict[str, Any],
    resolved: dict[str, Any],
    prompt_version: str,
) -> dict[str, Any]:
    return {
        "authority_source": _authority_source(str(authority.get("resolution_mode", "")).strip()),
        "identity_id": str(authority.get("authoritative_identity_id", "")).strip(),
        "status": str(resolved.get("status", "")).strip() or "active",
        "prompt_version": prompt_version,
        "source_layer": str(resolved.get("source_layer", "")).strip() or "unknown",
    }


def _failure_machine_payload() -> dict[str, Any]:
    return {
        "verification_source": "current_turn_machine_tuple",
        "verification_status": STATUS_FAIL_REQUIRED,
        "current_chat_surface_native_machine_attested": False,
        "next_hop_admission_status": STATUS_FAIL_REQUIRED,
    }


def resolve_headstamp_payload(
    *,
    identity_id: str,
    actor_id: str,
    session_id: str,
    catalog_path: Path,
    protocol_home: Path,
    work_layer: str = "instance",
    machine_profile: str = "mini",
) -> dict[str, Any]:
    resolved = resolve_launcher_identity_context(
        identity_id=identity_id,
        actor_id=actor_id,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
    )
    authority = resolve_launcher_runtime_authority(
        identity_id=identity_id,
        actor_id=actor_id,
        session_id=session_id,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
    )
    success = str(authority.get("runtime_authoritative_identity_status", "")).strip() == STATUS_PASS_REQUIRED
    scope = str(resolved.get("resolved_scope", "")).strip() or "USER"
    source_layer = str(resolved.get("source_layer", "")).strip() or "project"
    pack_path = Path(str(resolved.get("pack_path", "")).strip()).expanduser().resolve()
    prompt_version = _prompt_version(pack_path)
    machine_template = _machine_template(protocol_home)
    success_profile = (machine_template.get("profiles") or {}).get(machine_profile) or {}
    failure_profile = (machine_template.get("failure_profiles") or {}).get(machine_profile) or {}

    if success:
        line_1 = _render_success_identity_line(
            actor_id=actor_id,
            identity_id=str(authority.get("authoritative_identity_id", "")).strip() or identity_id,
            scope=scope,
            source_layer=source_layer,
            work_layer=work_layer,
        )
        line_2 = _render_machine_line(
            _success_machine_payload(
                authority=authority,
                resolved=resolved,
                prompt_version=prompt_version,
            ),
            field_order=list(success_profile.get("field_order") or []),
            include_extra_fields=bool(success_profile.get("include_extra_fields")),
        )
    else:
        line_1 = _render_failure_identity_line(
            actor_id=actor_id,
            requested_identity_id=identity_id,
            conflict=_failure_conflict(authority),
            scope=scope,
            source_layer=source_layer,
            work_layer=work_layer,
        )
        line_2 = _render_machine_line(
            _failure_machine_payload(),
            field_order=list(failure_profile.get("field_order") or []),
            include_extra_fields=bool(failure_profile.get("include_extra_fields")),
        )

    return {
        "status": STATUS_PASS_REQUIRED if success else STATUS_FAIL_REQUIRED,
        "identity_id": identity_id,
        "actor_id": actor_id,
        "session_id": session_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_path),
        "source_layer": source_layer,
        "resolved_scope": scope,
        "work_layer": work_layer,
        "machine_profile": machine_profile,
        "line_1": line_1,
        "line_2": line_2,
        "authority": authority,
        "resolved_identity": resolved,
    }


def _candidate_config_paths(explicit_config: str) -> list[Path]:
    if str(explicit_config or "").strip():
        return [Path(explicit_config).expanduser().resolve()]
    cwd = Path.cwd().resolve()
    out: list[Path] = []
    for candidate in (
        cwd / ".codex" / "config.toml",
        default_codex_home() / "config.toml",
    ):
        resolved = candidate.expanduser().resolve()
        if resolved not in out:
            out.append(resolved)
    return out


def _resolve_base_instructions_text(*, explicit_config: str = "", explicit_base_path: str = "") -> tuple[str, str, str]:
    if str(explicit_base_path or "").strip():
        path = Path(explicit_base_path).expanduser().resolve()
        if not path.exists():
            raise RuntimeError(f"base model instructions file not found: {path}")
        return path.read_text(encoding="utf-8"), str(path), ""

    for config_path in _candidate_config_paths(explicit_config):
        if not config_path.exists():
            continue
        try:
            config_payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        configured = str(config_payload.get("model_instructions_file", "")).strip()
        if not configured:
            continue
        base_path = (config_path.parent / configured).resolve()
        if not base_path.exists():
            continue
        return base_path.read_text(encoding="utf-8"), str(base_path), str(config_path)
    return "", "", ""


def compose_bootstrap_instructions(*, payload: dict[str, Any], base_instructions: str) -> str:
    base_text = str(base_instructions or "").rstrip()
    intro = (
        "# Native Chat Entry Bootstrap\n\n"
        "This Codex process already has a verified current-turn identity tuple.\n"
        "Every assistant-authored user-visible native-chat reply MUST begin with the exact two lines below, and nothing may precede them.\n"
        "Re-emit these exact two lines on every reply in this process unless fresh machine verification explicitly fails.\n"
        "If verification fails or conflicts, do not reuse stale success lines; fail-close to the withheld/conflict envelope instead.\n\n"
        f"{payload['line_1']}\n"
        f"{payload['line_2']}\n"
    )
    if not base_text:
        return intro + "\n"
    return intro + "\n---\n\n" + base_text + "\n"


def compose_project_fallback_doc(*, payload: dict[str, Any]) -> str:
    return (
        "# Native Chat Project Fallback\n\n"
        "This file is generated per Codex process and selected through a process-local "
        "`project_doc_fallback_filenames` override.\n"
        "It exists so every new turn can re-read the same machine-attested headstamp contract "
        "without relying on a shared workspace-global projection file.\n\n"
        "Every assistant-authored user-visible native-chat reply MUST begin with the exact two "
        "lines below, and nothing may precede them.\n"
        "If fresh machine verification fails, do not reuse stale success lines; fail-close to "
        "the withheld/conflict envelope instead.\n\n"
        f"{payload['line_1']}\n{payload['line_2']}\n"
    )


def _safe_session_token(session_id: str) -> str:
    token = str(session_id or "session-missing")
    token = token.replace(":", "__").replace("/", "__")
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in token) or "session-missing"


def write_process_local_bootstrap_artifacts(
    *,
    identity_id: str,
    actor_id: str,
    session_id: str,
    catalog_path: Path,
    protocol_home: Path,
    work_layer: str = "instance",
    machine_profile: str = "mini",
    explicit_config: str = "",
    explicit_base_instructions_file: str = "",
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    payload = resolve_headstamp_payload(
        identity_id=identity_id,
        actor_id=actor_id,
        session_id=session_id,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
        work_layer=work_layer,
        machine_profile=machine_profile,
    )
    base_text, base_path, config_path = _resolve_base_instructions_text(
        explicit_config=explicit_config,
        explicit_base_path=explicit_base_instructions_file,
    )
    bootstrap_file = runtime_temp_file(
        channel="identity-codex-launcher",
        operation="bootstrap",
        identity_id=identity_id,
        run_token=_safe_session_token(session_id),
        stem=f"identity-codex-bootstrap-{identity_id}",
        ext="md",
    )
    bootstrap_file.write_text(
        compose_bootstrap_instructions(payload=payload, base_instructions=base_text),
        encoding="utf-8",
    )
    project_root = workspace_root.resolve() if workspace_root is not None else Path.cwd().resolve()
    fallback_basename = f"{PROJECT_DOC_FALLBACK_PREFIX}{_safe_session_token(session_id)}.md"
    fallback_file = (project_root / fallback_basename).resolve()
    fallback_file.write_text(compose_project_fallback_doc(payload=payload), encoding="utf-8")
    return {
        **payload,
        "bootstrap_file": str(bootstrap_file),
        "project_doc_fallback_file": str(fallback_file),
        "project_doc_fallback_basename": fallback_basename,
        "base_instructions_path": base_path,
        "config_path": config_path,
    }


def has_forbidden_runtime_override(codex_args: list[str]) -> bool:
    idx = 0
    while idx < len(codex_args):
        arg = str(codex_args[idx])
        if arg == "-c":
            next_arg = str(codex_args[idx + 1]) if idx + 1 < len(codex_args) else ""
            if any(token in next_arg for token in FORBIDDEN_RUNTIME_OVERRIDE_KEYS):
                return True
            idx += 2
            continue
        if arg.startswith("-c=") and any(token in arg for token in FORBIDDEN_RUNTIME_OVERRIDE_KEYS):
            return True
        idx += 1
    return False


def build_codex_exec_command(*, bootstrap_payload: dict[str, Any], codex_args: list[str]) -> list[str]:
    fallback_names = ["AGENTS.md", str(bootstrap_payload["project_doc_fallback_basename"])]
    return [
        "codex",
        "-c",
        f'model_instructions_file="{bootstrap_payload["bootstrap_file"]}"',
        "-c",
        f"project_doc_fallback_filenames={json.dumps(fallback_names, ensure_ascii=False)}",
        "-c",
        'trace_exporter="none"',
        *list(codex_args),
    ]


def exec_identity_codex(
    *,
    identity_id: str,
    codex_args: list[str],
    actor_id: str = "",
    explicit_session_id: str = "",
    raw_catalog: str = "",
    work_layer: str = "instance",
    machine_profile: str = "mini",
    explicit_config: str = "",
    explicit_base_instructions_file: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    if has_forbidden_runtime_override(codex_args):
        raise RuntimeError(
            "identity-codex owns model_instructions_file and project_doc_fallback_filenames injection; "
            "remove the manual override and relaunch"
        )
    protocol_home = resolve_protocol_root(os.environ.get("IDENTITY_PROTOCOL_HOME", ""))
    catalog_path = resolve_catalog_path(raw_catalog)
    actor_token = resolve_required_protocol_actor_id(str(actor_id or ""))
    session_id, session_source = resolve_launcher_tuple(
        identity_id=identity_id,
        actor_id=actor_token,
        explicit_session_id=explicit_session_id,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
    )
    bootstrap_payload = write_process_local_bootstrap_artifacts(
        identity_id=identity_id,
        actor_id=actor_token,
        session_id=session_id,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
        work_layer=work_layer,
        machine_profile=machine_profile,
        explicit_config=explicit_config,
        explicit_base_instructions_file=explicit_base_instructions_file,
        workspace_root=Path.cwd(),
    )
    cmd = build_codex_exec_command(bootstrap_payload=bootstrap_payload, codex_args=codex_args)
    env = os.environ.copy()
    env["CODEX_ACTOR_ID"] = actor_token
    env["CODEX_SESSION_ID"] = session_id
    env["IDENTITY_SESSION_ID"] = session_id
    env["IDENTITY_BOOTSTRAP_IDENTITY_ID"] = identity_id
    env["IDENTITY_BOOTSTRAP_IDENTITY_SOURCE"] = "explicit_identity_id"
    env["IDENTITY_BOOTSTRAP_TUPLE_SOURCE"] = session_source
    env["IDENTITY_CATALOG"] = str(catalog_path)
    env["IDENTITY_HOME"] = str(catalog_path.parent)
    env["IDENTITY_PROTOCOL_HOME"] = str(protocol_home)
    env["OTEL_SDK_DISABLED"] = env.get("OTEL_SDK_DISABLED", "true") or "true"

    result = {
        "status": STATUS_PASS_REQUIRED,
        "identity_id": identity_id,
        "actor_id": actor_token,
        "session_id": session_id,
        "session_source": session_source,
        "catalog_path": str(catalog_path),
        "protocol_home": str(protocol_home),
        "bootstrap_file": str(bootstrap_payload["bootstrap_file"]),
        "project_doc_fallback_file": str(bootstrap_payload["project_doc_fallback_file"]),
        "project_doc_fallback_basename": str(bootstrap_payload["project_doc_fallback_basename"]),
        "line_1": str(bootstrap_payload["line_1"]),
        "line_2": str(bootstrap_payload["line_2"]),
        "command": cmd,
        "command_string": " ".join(shlex.quote(part) for part in cmd),
    }
    if dry_run:
        return result
    os.execvpe(cmd[0], cmd, env)
    raise RuntimeError("os.execvpe returned unexpectedly")


def validate_launcher_manifest_doc(*, manifest_doc: dict[str, Any], identity_id: str) -> list[str]:
    issues: list[str] = []
    expected = launcher_manifest_doc(identity_id)
    for key, value in expected.items():
        current = manifest_doc.get(key)
        if current != value:
            issues.append(f"manifest_field_mismatch:{key}")
    return issues


def active_identity_install_required(status: str, *, force_installed: bool = False) -> bool:
    if force_installed:
        return True
    token = str(status or "").strip().lower()
    return token == "active"
