#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from identity_context_continuity_common import (
    CONTEXT_CONTINUITY_CONTRACT_KEY,
    CONTINUITY_GUARD_RECEIPT_KIND,
    CONTEXT_CONTINUITY_VALIDATOR_ID,
    CONTINUITY_RECEIPT_KINDS,
    CONTINUITY_RECEIPT_VALIDATOR_ID,
    REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY,
    REENTRY_BRIEF_VALIDATOR_ID,
    REENTRY_CONSUMPTION_VALIDATOR_ID,
    REPORT_ROOT_REL,
    REENTRY_BRIEF_REL,
    STATE_ROOT_REL,
    clean_string,
)

CONTEXT_CONTINUITY_SCRIPT_IDS: tuple[str, ...] = (
    "run_identity_context_continuity_guard",
    "emit_identity_context_checkpoint",
    "materialize_identity_reentry_brief",
    "emit_identity_reentry_consumption_receipt",
)
CONTINUITY_REQUIRED_VALIDATOR_IDS: tuple[str, ...] = (
    CONTEXT_CONTINUITY_VALIDATOR_ID,
    REENTRY_BRIEF_VALIDATOR_ID,
    REENTRY_CONSUMPTION_VALIDATOR_ID,
    CONTINUITY_RECEIPT_VALIDATOR_ID,
)
CONTINUITY_GUARD_SCRIPT_REL = Path("scripts/run_identity_context_continuity_guard.sh")
CONTINUITY_CHECKPOINT_SCRIPT_REL = Path("scripts/emit_identity_context_checkpoint.py")
CONTINUITY_REENTRY_BRIEF_SCRIPT_REL = Path("scripts/materialize_identity_reentry_brief.py")
CONTINUITY_REENTRY_CONSUMPTION_SCRIPT_REL = Path("scripts/emit_identity_reentry_consumption_receipt.py")
CONTINUITY_GUARD_STATE_REL = STATE_ROOT_REL / "guard-state.json"
CONTINUITY_GUARD_RECEIPT_GLOB = (REPORT_ROOT_REL / "guard-*.json").as_posix()
CONTINUITY_CHECKPOINT_RECEIPT_REL = REPORT_ROOT_REL / "checkpoint-receipt.json"
CONTINUITY_MIGRATION_RECEIPT_REL = REPORT_ROOT_REL / "migration-receipt.json"
CONTINUITY_REENTRY_BRIEF_RECEIPT_REL = REPORT_ROOT_REL / "reentry-brief-receipt.json"
CONTINUITY_REENTRY_CONSUMPTION_RECEIPT_REL = REPORT_ROOT_REL / "reentry-consumption-receipt.json"
CONTINUITY_README_SECTION_MARKER = "## Continuity / re-entry helpers"
CONTINUITY_GOVERNANCE_DOC = "docs/governance/identity-context-continuity-governance-v1.6.16.md"
CONTINUITY_REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md"
DEFAULT_SCOPE = "startup_resume_recover"
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"


@dataclass(frozen=True)
class ContinuityPackContext:
    identity_id: str
    script_path: Path
    pack_root: Path
    scripts_dir: Path
    runtime_dir: Path
    report_root: Path
    state_root: Path
    task_path: Path
    task_doc: dict[str, Any]
    catalog_path: Path
    protocol_home: Path
    workspace_root: Path
    source_layer: str
    resolved_scope: str


@dataclass(frozen=True)
class GuardTickDecision:
    artifact_kind: str
    trigger_class: str
    generation_reason: str
    hit_interval: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_timestamp() -> str:
    return _utc_now().strftime("%Y%m%dT%H%M%SZ")


def utc_iso() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json_root_not_object:{path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any], *, apply: bool = True) -> bool:
    text = _json_text(payload)
    before = path.read_text(encoding="utf-8") if path.exists() else None
    changed = before != text
    if apply and changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return changed


def _write_text(path: Path, text: str, *, apply: bool = True, executable: bool = False) -> bool:
    normalized = text if text.endswith("\n") else text + "\n"
    before = path.read_text(encoding="utf-8") if path.exists() else None
    changed = before != normalized
    if apply and changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(normalized, encoding="utf-8")
        if executable:
            path.chmod(0o755)
    elif apply and executable and path.exists():
        path.chmod(0o755)
    return changed


def _find_pack_root(start: Path) -> Path:
    probe = start.expanduser().resolve()
    for candidate in [probe] + list(probe.parents):
        if (candidate / "CURRENT_TASK.json").is_file() and (candidate / "runtime").is_dir():
            return candidate.resolve()
    raise RuntimeError(f"identity_pack_root_not_found:{start}")


def _find_protocol_home(pack_root: Path) -> Path:
    env_protocol_home = clean_string(os.environ.get("IDENTITY_PROTOCOL_HOME"))
    if env_protocol_home:
        return Path(env_protocol_home).expanduser().resolve()

    cwd = Path.cwd().resolve()
    direct = (cwd / "identity-protocol-local").resolve()
    if direct.is_dir():
        return direct

    for probe in [pack_root.parent.parent.resolve(), *pack_root.parent.parent.resolve().parents]:
        candidate = (probe / "identity-protocol-local").resolve()
        if candidate.is_dir():
            return candidate
    raise RuntimeError(f"identity_protocol_home_not_found:{pack_root}")


def _default_catalog_path(pack_root: Path) -> Path:
    env_catalog = clean_string(os.environ.get("IDENTITY_CATALOG"))
    if env_catalog:
        return Path(env_catalog).expanduser().resolve()
    return (pack_root.parent / "catalog.local.yaml").resolve()


def _source_layer_from_catalog(catalog_path: Path) -> str:
    token = catalog_path.resolve().as_posix()
    if "/.codex/" in token:
        return "global"
    if token.endswith("/.identity/catalog.local.yaml") or "/.identity/catalog.local.yaml" in token:
        return "project"
    return "unknown"


def resolve_continuity_pack_context(*, script_file: str | Path, explicit_catalog: str = "") -> ContinuityPackContext:
    script_path = Path(script_file).expanduser().resolve()
    pack_root = _find_pack_root(script_path)
    task_path = (pack_root / "CURRENT_TASK.json").resolve()
    task_doc = _load_json(task_path)
    protocol_home = _find_protocol_home(pack_root)
    catalog_path = Path(clean_string(explicit_catalog)).expanduser().resolve() if clean_string(explicit_catalog) else _default_catalog_path(pack_root)
    return ContinuityPackContext(
        identity_id=pack_root.name,
        script_path=script_path,
        pack_root=pack_root,
        scripts_dir=(pack_root / "scripts").resolve(),
        runtime_dir=(pack_root / "runtime").resolve(),
        report_root=(pack_root / REPORT_ROOT_REL).resolve(),
        state_root=(pack_root / STATE_ROOT_REL).resolve(),
        task_path=task_path,
        task_doc=task_doc,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
        workspace_root=protocol_home.parent.resolve(),
        source_layer=_source_layer_from_catalog(catalog_path),
        resolved_scope="USER",
    )


def _relative_pack_ref(pack_root: Path, target: Path | str) -> str:
    candidate = Path(target).expanduser().resolve() if not isinstance(target, Path) else target.expanduser().resolve()
    try:
        return candidate.relative_to(pack_root.resolve()).as_posix()
    except Exception:
        return candidate.as_posix()


def _authority_refs(pack_root: Path) -> list[dict[str, str]]:
    return [
        {"ref": "CURRENT_TASK.json"},
        {"ref": "IDENTITY_PROMPT.md"},
        {"ref": CONTINUITY_GOVERNANCE_DOC},
        {"ref": CONTINUITY_REVIEW_DOC},
    ]


def _objective_title(task_doc: dict[str, Any]) -> str:
    objective = task_doc.get("objective")
    if isinstance(objective, dict):
        title = clean_string(objective.get("title"))
        if title:
            return title
    return clean_string(task_doc.get("task_id")) or "identity continuity checkpoint"


def _objective_status(task_doc: dict[str, Any]) -> str:
    objective = task_doc.get("objective")
    if isinstance(objective, dict):
        status = clean_string(objective.get("status"))
        if status:
            return status
    return "active"


def _current_state(task_doc: dict[str, Any]) -> str:
    state_machine = task_doc.get("state_machine")
    if isinstance(state_machine, dict):
        token = clean_string(state_machine.get("current_state"))
        if token:
            return token
    return "unknown"


def _task_focus_summary(task_doc: dict[str, Any], *, reason: str) -> dict[str, Any]:
    return {
        "objective_title": _objective_title(task_doc),
        "objective_status": _objective_status(task_doc),
        "state_machine_state": _current_state(task_doc),
        "continuity_reason": clean_string(reason) or "checkpoint_emit",
    }


def _completed_rows(*, event: str) -> list[str]:
    return [f"Governed continuity event emitted: {clean_string(event) or 'continuity_emit'}." ]


def _blockers_payload(task_doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "none_declared_at_emit_time" if _objective_status(task_doc).lower() != "blocked" else "task_marked_blocked",
        "current_state": _current_state(task_doc),
    }


def _next_actions_rows(*, follow_on: str) -> list[str]:
    return [clean_string(follow_on) or "Continue governed execution from the emitted continuity surface."]


def _freshness_payload() -> dict[str, Any]:
    return {
        "status": "fresh",
        "policy": "default_turns_15_30_60",
        "emitted_at": utc_iso(),
    }


def _load_optional_json(path: Path) -> dict[str, Any]:
    try:
        return _load_json(path)
    except Exception:
        return {}


def discover_latest_continuity_artifact(pack_root: Path) -> tuple[Path | None, dict[str, Any], str]:
    report_root = (pack_root / REPORT_ROOT_REL).resolve()
    hits = sorted(
        (path.resolve() for path in report_root.glob("continuity-*.json") if path.is_file()),
        key=lambda item: item.stat().st_mtime,
    )
    if hits:
        latest = hits[-1]
        doc = _load_optional_json(latest)
        return latest, doc, clean_string(doc.get("continuity_id"))
    brief_path = (pack_root / REENTRY_BRIEF_REL).resolve()
    if brief_path.is_file():
        doc = _load_optional_json(brief_path)
        return brief_path, doc, clean_string(doc.get("continuity_id"))
    return None, {}, ""


def _continuity_filename(artifact_kind: str) -> str:
    token = {
        "rolling_checkpoint": "rolling",
        "stage_checkpoint": "stage",
        "migration_checkpoint": "migration",
    }.get(clean_string(artifact_kind), "rolling")
    return f"continuity-{token}-{utc_timestamp()}.json"


def _continuity_id(identity_id: str, artifact_kind: str) -> str:
    kind = clean_string(artifact_kind).replace("_", "-") or "continuity"
    return f"{clean_string(identity_id)}-{kind}-{utc_timestamp()}"


def continuity_manifest_entries() -> dict[str, dict[str, Any]]:
    return {
        "run_identity_context_continuity_guard": {
            "script_id": "run_identity_context_continuity_guard",
            "entry_relpath": CONTINUITY_GUARD_SCRIPT_REL.as_posix(),
            "script_kind": "guard",
            "default_receipt_pattern": CONTINUITY_GUARD_RECEIPT_GLOB,
        },
        "emit_identity_context_checkpoint": {
            "script_id": "emit_identity_context_checkpoint",
            "entry_relpath": CONTINUITY_CHECKPOINT_SCRIPT_REL.as_posix(),
            "script_kind": "emitter",
            "default_receipt_pattern": (REPORT_ROOT_REL / "*receipt*.json").as_posix(),
        },
        "materialize_identity_reentry_brief": {
            "script_id": "materialize_identity_reentry_brief",
            "entry_relpath": CONTINUITY_REENTRY_BRIEF_SCRIPT_REL.as_posix(),
            "script_kind": "emitter",
            "default_receipt_pattern": (REPORT_ROOT_REL / "reentry-brief-receipt*.json").as_posix(),
        },
        "emit_identity_reentry_consumption_receipt": {
            "script_id": "emit_identity_reentry_consumption_receipt",
            "entry_relpath": CONTINUITY_REENTRY_CONSUMPTION_SCRIPT_REL.as_posix(),
            "script_kind": "emitter",
            "default_receipt_pattern": (REPORT_ROOT_REL / "reentry-consumption-receipt*.json").as_posix(),
        },
    }


def merge_continuity_manifest_entries(manifest_doc: dict[str, Any], *, identity_id: str) -> tuple[dict[str, Any], list[str]]:
    updated = dict(manifest_doc or {})
    if clean_string(updated.get("manifest_version")) != "v1":
        updated["manifest_version"] = "v1"
    if clean_string(updated.get("identity_id")) != clean_string(identity_id):
        updated["identity_id"] = clean_string(identity_id)
    scripts_node = updated.get("scripts")
    if isinstance(scripts_node, list):
        normalized: dict[str, dict[str, Any]] = {}
        for row in scripts_node:
            if not isinstance(row, dict):
                continue
            script_id = clean_string(row.get("script_id"))
            if script_id:
                normalized[script_id] = dict(row)
        scripts = normalized
    elif isinstance(scripts_node, dict):
        scripts = {clean_string(key): dict(value) for key, value in scripts_node.items() if isinstance(value, dict) and clean_string(key)}
    else:
        scripts = {}
    changed_ids: list[str] = []
    for script_id, row in continuity_manifest_entries().items():
        existing = dict(scripts.get(script_id) or {})
        merged = dict(existing)
        merged.update({k: v for k, v in row.items() if not clean_string(existing.get(k))})
        for key, value in row.items():
            if merged.get(key) != value:
                merged[key] = value
        if merged != existing:
            changed_ids.append(script_id)
        scripts[script_id] = merged
    updated["scripts"] = scripts
    return updated, changed_ids


def augment_instance_scripts_readme(text: str, *, identity_id: str) -> tuple[str, bool]:
    current = str(text or "")
    if CONTINUITY_README_SECTION_MARKER in current:
        return current if current.endswith("\n") else current + "\n", False
    appendix = textwrap.dedent(
        f"""

        {CONTINUITY_README_SECTION_MARKER}

        These pack-local helpers are the canonical `v1.6.16` continuity / re-entry producer surface for
        `{clean_string(identity_id)}`.

        Materialized scripts:

        - `run_identity_context_continuity_guard.sh`
          - proactive guard entry invoked by lifecycle/tick surfaces
          - updates `runtime/state/context-continuity/guard-state.json`
          - writes guard receipts under `runtime/reports/context-continuity/guard-*.json`
        - `emit_identity_context_checkpoint.py`
          - deterministic checkpoint writer for `rolling_checkpoint`, `stage_checkpoint`, and `migration_checkpoint`
        - `materialize_identity_reentry_brief.py`
          - deterministic writer for `runtime/state/context-continuity/active-reentry-brief.json`
        - `emit_identity_reentry_consumption_receipt.py`
          - deterministic writer for `runtime/reports/context-continuity/reentry-consumption-receipt.json`

        Fixed runtime sinks:

        - `runtime/reports/context-continuity/continuity-rolling-*.json`
        - `runtime/reports/context-continuity/continuity-stage-*.json`
        - `runtime/reports/context-continuity/continuity-migration-*.json`
        - `runtime/state/context-continuity/active-reentry-brief.json`
        - `runtime/reports/context-continuity/checkpoint-receipt.json`
        - `runtime/reports/context-continuity/migration-receipt.json`
        - `runtime/reports/context-continuity/reentry-brief-receipt.json`
        - `runtime/reports/context-continuity/reentry-consumption-receipt.json`

        Examples:

        ```bash
        .identity/{clean_string(identity_id)}/scripts/run_identity_context_continuity_guard.sh tick --turn-count 15
        .identity/{clean_string(identity_id)}/scripts/run_identity_context_continuity_guard.sh pre-migrate
        .identity/{clean_string(identity_id)}/scripts/run_identity_context_continuity_guard.sh post-recover
        ```
        """
    ).rstrip() + "\n"
    merged = current.rstrip() + appendix
    return merged, True


def _script_bootstrap_block() -> str:
    return textwrap.dedent(
        """
        THIS_FILE = Path(__file__).resolve()


        def _find_pack_root(start: Path) -> Path:
            for probe in [start] + list(start.parents):
                if (probe / "CURRENT_TASK.json").is_file() and (probe / "runtime").is_dir():
                    return probe.resolve()
            raise RuntimeError(f"identity_pack_root_not_found:{start}")


        def _find_protocol_home(pack_root: Path) -> Path:
            env_home = str(os.environ.get("IDENTITY_PROTOCOL_HOME", "")).strip()
            if env_home:
                return Path(env_home).expanduser().resolve()
            cwd = Path.cwd().resolve()
            direct = (cwd / "identity-protocol-local").resolve()
            if direct.is_dir():
                return direct
            for probe in [pack_root.parent.parent.resolve(), *pack_root.parent.parent.resolve().parents]:
                candidate = (probe / "identity-protocol-local").resolve()
                if candidate.is_dir():
                    return candidate
            raise RuntimeError(f"identity_protocol_home_not_found:{pack_root}")


        PACK_ROOT = _find_pack_root(THIS_FILE.parent)
        PROTOCOL_HOME = _find_protocol_home(PACK_ROOT)
        SCRIPTS_HOME = (PROTOCOL_HOME / "scripts").resolve()
        if str(SCRIPTS_HOME) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_HOME))
        """
    ).strip()


def continuity_checkpoint_wrapper_text() -> str:
    return (
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        f"{_script_bootstrap_block()}\n\n"
        "from identity_context_continuity_materialization_common import main_emit_checkpoint_from_pack_script  # noqa: E402\n\n"
        "\nif __name__ == \"__main__\":\n"
        "    raise SystemExit(main_emit_checkpoint_from_pack_script(__file__))\n"
    )


def continuity_reentry_brief_wrapper_text() -> str:
    return (
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        f"{_script_bootstrap_block()}\n\n"
        "from identity_context_continuity_materialization_common import main_materialize_reentry_brief_from_pack_script  # noqa: E402\n\n"
        "\nif __name__ == \"__main__\":\n"
        "    raise SystemExit(main_materialize_reentry_brief_from_pack_script(__file__))\n"
    )


def continuity_reentry_consumption_wrapper_text() -> str:
    return (
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        f"{_script_bootstrap_block()}\n\n"
        "from identity_context_continuity_materialization_common import main_emit_reentry_consumption_from_pack_script  # noqa: E402\n\n"
        "\nif __name__ == \"__main__\":\n"
        "    raise SystemExit(main_emit_reentry_consumption_from_pack_script(__file__))\n"
    )


def continuity_guard_wrapper_text() -> str:
    return textwrap.dedent(
        """
        #!/usr/bin/env bash
        set -euo pipefail

        SCRIPT_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
        PACK_ROOT="$(cd "$(dirname "${SCRIPT_FILE}")/.." && pwd)"

        if [[ -n "${IDENTITY_PROTOCOL_HOME:-}" ]]; then
          PROTOCOL_HOME="$(cd "${IDENTITY_PROTOCOL_HOME}" && pwd)"
        elif [[ -d "$(pwd)/identity-protocol-local" ]]; then
          PROTOCOL_HOME="$(cd "$(pwd)/identity-protocol-local" && pwd)"
        else
          SEARCH_ROOT="$(cd "${PACK_ROOT}/.." && pwd)"
          PROTOCOL_HOME=""
          while [[ "${SEARCH_ROOT}" != "/" ]]; do
            if [[ -d "${SEARCH_ROOT}/identity-protocol-local" ]]; then
              PROTOCOL_HOME="$(cd "${SEARCH_ROOT}/identity-protocol-local" && pwd)"
              break
            fi
            SEARCH_ROOT="$(cd "${SEARCH_ROOT}/.." && pwd)"
          done
          if [[ -z "${PROTOCOL_HOME}" ]]; then
            echo "[FAIL] identity_protocol_home_not_found:${PACK_ROOT}" >&2
            exit 1
          fi
        fi

        exec python3 "${PROTOCOL_HOME}/scripts/run_identity_context_continuity_guard_runtime.py" \
          --guard-script "${SCRIPT_FILE}" \
          "$@"
        """
    ).strip() + "\n"


def continuity_materialized_file_map() -> dict[str, tuple[str, bool]]:
    return {
        CONTINUITY_GUARD_SCRIPT_REL.as_posix(): (continuity_guard_wrapper_text(), True),
        CONTINUITY_CHECKPOINT_SCRIPT_REL.as_posix(): (continuity_checkpoint_wrapper_text(), True),
        CONTINUITY_REENTRY_BRIEF_SCRIPT_REL.as_posix(): (continuity_reentry_brief_wrapper_text(), True),
        CONTINUITY_REENTRY_CONSUMPTION_SCRIPT_REL.as_posix(): (continuity_reentry_consumption_wrapper_text(), True),
    }


def _ensure_required_validators(task: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    validators = task.get("required_validators")
    if not isinstance(validators, list):
        validators = []
        task["required_validators"] = validators
    normalized = [clean_string(item) for item in validators if clean_string(item)]
    for validator in CONTINUITY_REQUIRED_VALIDATOR_IDS:
        if validator not in normalized:
            normalized.append(validator)
            changed.append(validator)
    task["required_validators"] = normalized
    return changed


def _force_required_continuity_contracts(task: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    for key in (CONTEXT_CONTINUITY_CONTRACT_KEY, REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY):
        node = task.get(key)
        if not isinstance(node, dict):
            continue
        if node.get("required") is not True:
            node["required"] = True
            changed.append(key)
    return changed


def _base_guard_state(identity_id: str) -> dict[str, Any]:
    return {
        "identity_id": clean_string(identity_id),
        "guard_contract_version": "v1.6.16",
        "trigger_profile": "default_turns_15_30_60",
        "turn_count": 0,
        "migration_checkpoint_due": False,
        "last_action": "bootstrap_seed",
        "last_updated_at": utc_iso(),
        "last_guard_receipt_ref": "",
        "last_checkpoint_ref": "",
        "last_checkpoint_continuity_id": "",
        "active_reentry_brief_ref": REENTRY_BRIEF_REL.as_posix(),
        "active_reentry_brief_continuity_id": "",
        "last_reentry_consumption_receipt_ref": "",
    }


def _receipt_scope(scope: str = "") -> str:
    return clean_string(scope) or DEFAULT_SCOPE


def emit_checkpoint_artifact(
    ctx: ContinuityPackContext,
    *,
    artifact_kind: str,
    generation_reason: str = "",
    trigger_class: str = "",
    supersedes_ref: str = "",
    apply: bool = True,
) -> dict[str, Any]:
    kind = clean_string(artifact_kind)
    if kind not in {"rolling_checkpoint", "stage_checkpoint", "migration_checkpoint"}:
        raise RuntimeError(f"unsupported_artifact_kind:{artifact_kind}")
    latest_path, latest_doc, latest_continuity_id = discover_latest_continuity_artifact(ctx.pack_root)
    continuity_id = _continuity_id(ctx.identity_id, kind)
    if not supersedes_ref:
        supersedes_ref = latest_continuity_id
    artifact_path = (ctx.report_root / _continuity_filename(kind)).resolve()
    receipt_path = (
        (ctx.pack_root / CONTINUITY_MIGRATION_RECEIPT_REL).resolve()
        if kind == "migration_checkpoint"
        else (ctx.pack_root / CONTINUITY_CHECKPOINT_RECEIPT_REL).resolve()
    )
    emitted_reason = clean_string(generation_reason) or (
        "migration_handoff_emit" if kind == "migration_checkpoint" else "checkpoint_emit"
    )
    emitted_trigger = clean_string(trigger_class) or (
        "resume_migration" if kind == "migration_checkpoint" else "turn_cadence"
    )
    artifact_doc = {
        "continuity_id": continuity_id,
        "artifact_kind": kind,
        "generation_reason": emitted_reason,
        "trigger_class": emitted_trigger,
        "source_identity_id": ctx.identity_id,
        "source_layer": ctx.source_layer,
        "work_layer": "instance",
        "authority_refs": _authority_refs(ctx.pack_root),
        "task_focus_summary": _task_focus_summary(ctx.task_doc, reason=emitted_reason),
        "completed_since_previous": _completed_rows(event=kind),
        "open_blockers": _blockers_payload(ctx.task_doc),
        "next_actions": _next_actions_rows(
            follow_on=(
                "Refresh the governed reentry brief before the next restart or migration."
                if kind != "migration_checkpoint"
                else "Consume the governed reentry brief after the target session recovers."
            )
        ),
        "receipt_refs": [{"ref": _relative_pack_ref(ctx.pack_root, receipt_path)}],
        "supersedes_ref": clean_string(supersedes_ref),
        "freshness": _freshness_payload(),
    }
    receipt_kind = (
        CONTINUITY_RECEIPT_KINDS["migration_handoff"] if kind == "migration_checkpoint" else CONTINUITY_RECEIPT_KINDS["checkpoint"]
    )
    receipt_doc = {
        "receipt_kind": receipt_kind,
        "artifact_ref": _relative_pack_ref(ctx.pack_root, artifact_path),
        "artifact_kind": kind,
        "route_or_entry_scope": _receipt_scope("guard_tick" if kind != "migration_checkpoint" else DEFAULT_SCOPE),
    }
    artifact_changed = _write_json(artifact_path, artifact_doc, apply=apply)
    receipt_changed = _write_json(receipt_path, receipt_doc, apply=apply)
    return {
        "status": STATUS_PASS_REQUIRED,
        "artifact_path": str(artifact_path),
        "artifact_ref": _relative_pack_ref(ctx.pack_root, artifact_path),
        "receipt_path": str(receipt_path),
        "receipt_ref": _relative_pack_ref(ctx.pack_root, receipt_path),
        "artifact_kind": kind,
        "continuity_id": continuity_id,
        "supersedes_ref": clean_string(supersedes_ref),
        "artifact_changed": artifact_changed,
        "receipt_changed": receipt_changed,
        "latest_artifact_hint": _relative_pack_ref(ctx.pack_root, latest_path) if latest_path is not None else "",
        "latest_continuity_id_hint": latest_continuity_id,
        "latest_artifact_kind_hint": clean_string(latest_doc.get("artifact_kind")),
    }


def materialize_reentry_brief(
    ctx: ContinuityPackContext,
    *,
    continuity_lineage_ref: str = "",
    generation_reason: str = "",
    trigger_class: str = "",
    apply: bool = True,
) -> dict[str, Any]:
    latest_path, latest_doc, latest_continuity_id = discover_latest_continuity_artifact(ctx.pack_root)
    lineage_ref = clean_string(continuity_lineage_ref) or latest_continuity_id
    if not lineage_ref:
        raise RuntimeError("continuity_lineage_ref_missing")
    continuity_id = _continuity_id(ctx.identity_id, "reentry_brief")
    brief_path = (ctx.pack_root / REENTRY_BRIEF_REL).resolve()
    receipt_path = (ctx.pack_root / CONTINUITY_REENTRY_BRIEF_RECEIPT_REL).resolve()
    emitted_reason = clean_string(generation_reason) or "startup_reentry"
    emitted_trigger = clean_string(trigger_class) or "launcher_restart_or_recover"
    brief_doc = {
        "continuity_id": continuity_id,
        "artifact_kind": "reentry_brief",
        "generation_reason": emitted_reason,
        "trigger_class": emitted_trigger,
        "source_identity_id": ctx.identity_id,
        "source_layer": ctx.source_layer,
        "work_layer": "instance",
        "authority_refs": _authority_refs(ctx.pack_root),
        "task_focus_summary": _task_focus_summary(ctx.task_doc, reason=emitted_reason),
        "completed_since_previous": _completed_rows(event="reentry_brief"),
        "open_blockers": _blockers_payload(ctx.task_doc),
        "next_actions": _next_actions_rows(
            follow_on="Consume the governed reentry brief via startup/resume/recover and emit the consumption receipt."
        ),
        "receipt_refs": [
            {"ref": _relative_pack_ref(ctx.pack_root, receipt_path)},
            {"ref": CONTINUITY_REENTRY_CONSUMPTION_RECEIPT_REL.as_posix()},
        ],
        "supersedes_ref": lineage_ref,
        "freshness": _freshness_payload(),
        "stable_prefix": {
            "identity_ref": "IDENTITY_PROMPT.md",
            "task_ref": "CURRENT_TASK.json",
            "lane_ref": DEFAULT_SCOPE,
            "authority_ref_set": [CONTINUITY_GOVERNANCE_DOC, CONTINUITY_REVIEW_DOC],
            "contract_ref_set": [
                clean_string((ctx.task_doc.get(CONTEXT_CONTINUITY_CONTRACT_KEY) or {}).get("contract_id")),
                clean_string((ctx.task_doc.get(REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY) or {}).get("contract_id")),
            ],
        },
        "dynamic_tail": {
            "lineage_ref": lineage_ref,
            "completed_items": _completed_rows(event="reentry_brief_materialized"),
            "blockers": ["Successful continuity recovery is proven only after the governed reentry consumption receipt is emitted."],
            "next_actions": _next_actions_rows(
                follow_on="Open the target session through the launcher owner stream and submit this governed reentry task block."
            ),
            "receipt_refs": [
                {"ref": _relative_pack_ref(ctx.pack_root, receipt_path)},
                {"ref": CONTINUITY_REENTRY_CONSUMPTION_RECEIPT_REL.as_posix()},
            ],
        },
    }
    receipt_doc = {
        "receipt_kind": CONTINUITY_RECEIPT_KINDS["reentry_brief"],
        "reentry_brief_ref": _relative_pack_ref(ctx.pack_root, brief_path),
        "continuity_lineage_ref": lineage_ref,
        "route_or_entry_scope": _receipt_scope(),
    }
    brief_changed = _write_json(brief_path, brief_doc, apply=apply)
    receipt_changed = _write_json(receipt_path, receipt_doc, apply=apply)
    return {
        "status": STATUS_PASS_REQUIRED,
        "brief_path": str(brief_path),
        "brief_ref": _relative_pack_ref(ctx.pack_root, brief_path),
        "receipt_path": str(receipt_path),
        "receipt_ref": _relative_pack_ref(ctx.pack_root, receipt_path),
        "continuity_id": continuity_id,
        "continuity_lineage_ref": lineage_ref,
        "brief_changed": brief_changed,
        "receipt_changed": receipt_changed,
        "latest_artifact_hint": _relative_pack_ref(ctx.pack_root, latest_path) if latest_path is not None else "",
        "latest_artifact_kind_hint": clean_string(latest_doc.get("artifact_kind")),
    }


def emit_reentry_consumption_receipt(
    ctx: ContinuityPackContext,
    *,
    brief_path: str = "",
    scope: str = DEFAULT_SCOPE,
    apply: bool = True,
) -> dict[str, Any]:
    resolved_brief = Path(clean_string(brief_path)).expanduser().resolve() if clean_string(brief_path) else (ctx.pack_root / REENTRY_BRIEF_REL).resolve()
    if not resolved_brief.is_file():
        raise RuntimeError(f"reentry_brief_not_found:{resolved_brief}")
    brief_doc = _load_json(resolved_brief)
    brief_continuity_id = clean_string(brief_doc.get("continuity_id"))
    if not brief_continuity_id:
        raise RuntimeError("reentry_brief_continuity_id_missing")
    receipt_path = (ctx.pack_root / CONTINUITY_REENTRY_CONSUMPTION_RECEIPT_REL).resolve()
    receipt_doc = {
        "receipt_kind": CONTINUITY_RECEIPT_KINDS["reentry_consumption"],
        "identity_reentry_brief_status": STATUS_PASS_REQUIRED,
        "startup_consumption_status": STATUS_PASS_REQUIRED,
        "reentry_brief_ref": _relative_pack_ref(ctx.pack_root, resolved_brief),
        "continuity_lineage_ref": brief_continuity_id,
        "authority_resolution_status": STATUS_PASS_REQUIRED,
        "tuple_bootstrap_preserved": True,
        "launcher_bind_status": STATUS_PASS_REQUIRED,
        "consumption_outcome": "governed_reentry_brief_consumed",
        "route_or_entry_scope": _receipt_scope(scope),
    }
    receipt_changed = _write_json(receipt_path, receipt_doc, apply=apply)
    guard_state_path = _guard_state_path(ctx.pack_root)
    guard_state = _load_guard_state(ctx.pack_root, identity_id=ctx.identity_id)
    guard_state["active_reentry_brief_ref"] = _relative_pack_ref(ctx.pack_root, resolved_brief)
    guard_state["active_reentry_brief_continuity_id"] = brief_continuity_id
    guard_state["last_reentry_consumption_receipt_ref"] = _relative_pack_ref(ctx.pack_root, receipt_path)
    guard_state["last_action"] = "post-recover"
    guard_state["migration_checkpoint_due"] = False
    guard_state["last_updated_at"] = utc_iso()
    guard_state_changed = _write_json(guard_state_path, guard_state, apply=apply)
    return {
        "status": STATUS_PASS_REQUIRED,
        "receipt_path": str(receipt_path),
        "receipt_ref": _relative_pack_ref(ctx.pack_root, receipt_path),
        "reentry_brief_ref": _relative_pack_ref(ctx.pack_root, resolved_brief),
        "continuity_lineage_ref": brief_continuity_id,
        "receipt_changed": receipt_changed,
        "guard_state_ref": _relative_pack_ref(ctx.pack_root, guard_state_path),
        "guard_state_changed": guard_state_changed,
    }


def inspect_continuity_materialization(*, pack_dir: Path) -> dict[str, Any]:
    manifest_path = (pack_dir / "scripts" / "INSTANCE_SCRIPT_MANIFEST.json").resolve()
    manifest_doc = _load_optional_json(manifest_path) if manifest_path.is_file() else {}
    manifest_scripts = manifest_doc.get("scripts") if isinstance(manifest_doc, dict) else {}
    if isinstance(manifest_scripts, list):
        manifest_index = {
            clean_string(row.get("script_id")): row
            for row in manifest_scripts
            if isinstance(row, dict) and clean_string(row.get("script_id"))
        }
    elif isinstance(manifest_scripts, dict):
        manifest_index = {
            clean_string(key): value
            for key, value in manifest_scripts.items()
            if isinstance(value, dict) and clean_string(key)
        }
    else:
        manifest_index = {}
    expected_scripts = continuity_manifest_entries()
    script_rows: list[dict[str, Any]] = []
    missing_script_ids: list[str] = []
    for script_id, entry in expected_scripts.items():
        entry_relpath = clean_string(entry.get("entry_relpath"))
        script_path = (pack_dir / entry_relpath).resolve()
        in_manifest = script_id in manifest_index
        present = script_path.is_file()
        row_status = STATUS_PASS_REQUIRED if present and in_manifest else STATUS_FAIL_REQUIRED
        if row_status != STATUS_PASS_REQUIRED:
            missing_script_ids.append(script_id)
        script_rows.append(
            {
                "script_id": script_id,
                "path": str(script_path),
                "in_manifest": in_manifest,
                "present": present,
                "status": row_status,
            }
        )
    guard_state_path = (pack_dir / CONTINUITY_GUARD_STATE_REL).resolve()
    guard_state_present = guard_state_path.is_file()
    bootstrap_checkpoint_present = any((pack_dir / REPORT_ROOT_REL).glob("continuity-*.json"))
    bootstrap_brief_present = (pack_dir / REENTRY_BRIEF_REL).is_file()
    bootstrap_brief_receipt_present = (pack_dir / CONTINUITY_REENTRY_BRIEF_RECEIPT_REL).is_file()
    bootstrap_checkpoint_receipt_present = (pack_dir / CONTINUITY_CHECKPOINT_RECEIPT_REL).is_file()
    overall_status = STATUS_PASS_REQUIRED if not missing_script_ids and guard_state_present and bootstrap_checkpoint_present and bootstrap_brief_present and bootstrap_brief_receipt_present and bootstrap_checkpoint_receipt_present else STATUS_FAIL_REQUIRED
    return {
        "status": overall_status,
        "manifest_path": str(manifest_path),
        "script_rows": script_rows,
        "missing_script_ids": missing_script_ids,
        "guard_state_path": str(guard_state_path),
        "guard_state_present": guard_state_present,
        "bootstrap_checkpoint_present": bootstrap_checkpoint_present,
        "bootstrap_brief_present": bootstrap_brief_present,
        "bootstrap_checkpoint_receipt_present": bootstrap_checkpoint_receipt_present,
        "bootstrap_brief_receipt_present": bootstrap_brief_receipt_present,
    }


def materialize_identity_context_continuity_assets(
    *,
    task: dict[str, Any],
    identity_id: str,
    pack_dir: Path,
    apply: bool,
    force_required_contracts: bool = True,
) -> dict[str, Any]:
    pack_dir = pack_dir.expanduser().resolve()
    report_root = (pack_dir / REPORT_ROOT_REL).resolve()
    state_root = (pack_dir / STATE_ROOT_REL).resolve()
    script_map = continuity_materialized_file_map()
    continuity_contracts_forced_required = _force_required_continuity_contracts(task) if force_required_contracts else []
    continuity_required_validators_added = _ensure_required_validators(task)
    script_changes: list[str] = []
    for relpath, (text, executable) in script_map.items():
        if _write_text(pack_dir / relpath, text, apply=apply, executable=executable):
            script_changes.append(relpath)
    manifest_path = (pack_dir / "scripts" / "INSTANCE_SCRIPT_MANIFEST.json").resolve()
    manifest_doc = _load_optional_json(manifest_path) if manifest_path.is_file() else {"manifest_version": "v1", "identity_id": identity_id, "scripts": {}}
    merged_manifest, changed_manifest_entries = merge_continuity_manifest_entries(manifest_doc, identity_id=identity_id)
    manifest_changed = _write_json(manifest_path, merged_manifest, apply=apply)
    readme_path = (pack_dir / "scripts" / "README.md").resolve()
    readme_before = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
    readme_after, readme_augmented = augment_instance_scripts_readme(readme_before, identity_id=identity_id)
    readme_changed = _write_text(readme_path, readme_after, apply=apply)
    guard_state_changed = _write_json(pack_dir / CONTINUITY_GUARD_STATE_REL, _base_guard_state(identity_id), apply=apply)
    if apply:
        report_root.mkdir(parents=True, exist_ok=True)
        state_root.mkdir(parents=True, exist_ok=True)
    bootstrap_summary: dict[str, Any] = {}
    latest_artifact, _latest_doc, _latest_continuity_id = discover_latest_continuity_artifact(pack_dir)
    ctx = resolve_continuity_pack_context(script_file=pack_dir / "scripts" / "README.md")
    if latest_artifact is None:
        bootstrap_summary["checkpoint"] = emit_checkpoint_artifact(
            ctx,
            artifact_kind="stage_checkpoint",
            generation_reason="bootstrap_materialization",
            trigger_class="major_gate_flip",
            apply=apply,
        )
    else:
        bootstrap_summary["checkpoint"] = {
            "status": STATUS_PASS_REQUIRED,
            "artifact_path": str(latest_artifact),
            "artifact_changed": False,
            "receipt_changed": False,
        }
    brief_path = (pack_dir / REENTRY_BRIEF_REL).resolve()
    if not brief_path.is_file():
        lineage = clean_string((bootstrap_summary.get("checkpoint") or {}).get("continuity_id"))
        bootstrap_summary["reentry_brief"] = materialize_reentry_brief(
            ctx,
            continuity_lineage_ref=lineage,
            generation_reason="bootstrap_reentry_seed",
            trigger_class="major_gate_flip",
            apply=apply,
        )
    else:
        bootstrap_summary["reentry_brief"] = {
            "status": STATUS_PASS_REQUIRED,
            "brief_path": str(brief_path),
            "brief_changed": False,
            "receipt_changed": False,
        }
    inspection = inspect_continuity_materialization(pack_dir=pack_dir)
    changed = bool(
        continuity_contracts_forced_required
        or continuity_required_validators_added
        or script_changes
        or changed_manifest_entries
        or manifest_changed
        or readme_changed
        or guard_state_changed
        or bool((bootstrap_summary.get("checkpoint") or {}).get("artifact_changed"))
        or bool((bootstrap_summary.get("checkpoint") or {}).get("receipt_changed"))
        or bool((bootstrap_summary.get("reentry_brief") or {}).get("brief_changed"))
        or bool((bootstrap_summary.get("reentry_brief") or {}).get("receipt_changed"))
    )
    return {
        "status": inspection.get("status", STATUS_FAIL_REQUIRED),
        "changed": changed,
        "contracts_forced_required": continuity_contracts_forced_required,
        "required_validators_added": continuity_required_validators_added,
        "script_files_changed": script_changes,
        "manifest_changed": manifest_changed,
        "manifest_entries_changed": changed_manifest_entries,
        "readme_changed": readme_changed or readme_augmented,
        "guard_state_changed": guard_state_changed,
        "bootstrap": bootstrap_summary,
        "inspection": inspection,
    }


def _emit_payload(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main_emit_checkpoint_from_pack_script(script_file: str | Path) -> int:
    ap = argparse.ArgumentParser(description="Emit a governed continuity checkpoint for the current identity pack.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--artifact-kind", default="rolling_checkpoint")
    ap.add_argument("--supersedes-ref", default="")
    ap.add_argument("--generation-reason", default="")
    ap.add_argument("--trigger-class", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()
    try:
        ctx = resolve_continuity_pack_context(script_file=script_file, explicit_catalog=args.catalog)
        payload = emit_checkpoint_artifact(
            ctx,
            artifact_kind=args.artifact_kind,
            supersedes_ref=args.supersedes_ref,
            generation_reason=args.generation_reason,
            trigger_class=args.trigger_class,
            apply=True,
        )
    except Exception as exc:
        payload = {"status": STATUS_FAIL_REQUIRED, "error": str(exc)}
        _emit_payload(payload, json_only=args.json_only)
        return 1
    _emit_payload(payload, json_only=args.json_only)
    return 0


def main_materialize_reentry_brief_from_pack_script(script_file: str | Path) -> int:
    ap = argparse.ArgumentParser(description="Materialize the governed reentry brief for the current identity pack.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--continuity-lineage-ref", default="")
    ap.add_argument("--generation-reason", default="")
    ap.add_argument("--trigger-class", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()
    try:
        ctx = resolve_continuity_pack_context(script_file=script_file, explicit_catalog=args.catalog)
        payload = materialize_reentry_brief(
            ctx,
            continuity_lineage_ref=args.continuity_lineage_ref,
            generation_reason=args.generation_reason,
            trigger_class=args.trigger_class,
            apply=True,
        )
    except Exception as exc:
        payload = {"status": STATUS_FAIL_REQUIRED, "error": str(exc)}
        _emit_payload(payload, json_only=args.json_only)
        return 1
    _emit_payload(payload, json_only=args.json_only)
    return 0


def main_emit_reentry_consumption_from_pack_script(script_file: str | Path) -> int:
    ap = argparse.ArgumentParser(description="Emit the governed reentry consumption receipt for the current identity pack.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--scope", default=DEFAULT_SCOPE)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()
    try:
        ctx = resolve_continuity_pack_context(script_file=script_file, explicit_catalog=args.catalog)
        payload = emit_reentry_consumption_receipt(
            ctx,
            brief_path=args.brief,
            scope=args.scope,
            apply=True,
        )
    except Exception as exc:
        payload = {"status": STATUS_FAIL_REQUIRED, "error": str(exc)}
        _emit_payload(payload, json_only=args.json_only)
        return 1
    _emit_payload(payload, json_only=args.json_only)
    return 0


def _guard_state_path(pack_root: Path) -> Path:
    return (pack_root / CONTINUITY_GUARD_STATE_REL).resolve()


def _load_guard_state(pack_root: Path, *, identity_id: str) -> dict[str, Any]:
    state_path = _guard_state_path(pack_root)
    if state_path.is_file():
        return _load_json(state_path)
    state = _base_guard_state(identity_id)
    _write_json(state_path, state, apply=True)
    return state


def _tick_decision(turn_count: int) -> GuardTickDecision | None:
    if turn_count > 0 and turn_count % 30 == 0:
        return GuardTickDecision(
            artifact_kind="stage_checkpoint",
            trigger_class="compaction_boundary",
            generation_reason="guard_tick_stage_interval",
            hit_interval=30,
        )
    if turn_count > 0 and turn_count % 15 == 0:
        return GuardTickDecision(
            artifact_kind="rolling_checkpoint",
            trigger_class="turn_cadence",
            generation_reason="guard_tick_rolling_interval",
            hit_interval=15,
        )
    return None


def _run_json(cmd: list[str], *, cwd: Path) -> tuple[int, dict[str, Any], str, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    payload: dict[str, Any] = {}
    if stdout:
        try:
            raw = json.loads(stdout)
            if isinstance(raw, dict):
                payload = raw
        except Exception:
            payload = {}
    return proc.returncode, payload, stdout, stderr


def _guard_receipt(ctx: ContinuityPackContext, *, action: str, turn_count: int, event_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_family": CONTINUITY_GUARD_RECEIPT_KIND,
        "identity_id": ctx.identity_id,
        "catalog_path": str(ctx.catalog_path),
        "guard_action": clean_string(action),
        "turn_count": int(turn_count),
        "trigger_profile": "default_turns_15_30_60",
        "generated_at": utc_iso(),
        "event_payload": event_payload,
        "guard_state_ref": CONTINUITY_GUARD_STATE_REL.as_posix(),
    }


def main_guard_runtime() -> int:
    ap = argparse.ArgumentParser(description="Shared runtime driver for the pack-local context continuity guard shell entry.")
    ap.add_argument("--guard-script", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("action", choices=("tick", "pre-clear", "pre-migrate", "post-recover"))
    ap.add_argument("--turn-count", type=int, default=-1)
    ap.add_argument("--turn-increment", type=int, default=1)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        ctx = resolve_continuity_pack_context(script_file=args.guard_script, explicit_catalog=args.catalog)
        state = _load_guard_state(ctx.pack_root, identity_id=ctx.identity_id)
        current_turn_count = int(state.get("turn_count") or 0)
        if args.action == "tick":
            turn_count = args.turn_count if args.turn_count >= 0 else current_turn_count + max(1, int(args.turn_increment or 1))
            decision = _tick_decision(turn_count)
            event_payload: dict[str, Any] = {
                "action": "tick",
                "turn_count": turn_count,
                "migration_checkpoint_due": bool(turn_count > 0 and turn_count % 60 == 0),
            }
            if decision is not None:
                checkpoint_script = (ctx.pack_root / CONTINUITY_CHECKPOINT_SCRIPT_REL).resolve()
                cmd = [
                    sys.executable,
                    str(checkpoint_script),
                    "--catalog",
                    str(ctx.catalog_path),
                    "--artifact-kind",
                    decision.artifact_kind,
                    "--generation-reason",
                    decision.generation_reason,
                    "--trigger-class",
                    decision.trigger_class,
                    "--json-only",
                ]
                rc, checkpoint_payload, stdout, stderr = _run_json(cmd, cwd=ctx.workspace_root)
                event_payload["checkpoint_writer"] = {
                    "returncode": rc,
                    "payload": checkpoint_payload,
                    "stdout": stdout,
                    "stderr": stderr,
                }
                if rc != 0 or clean_string(checkpoint_payload.get("status")) != STATUS_PASS_REQUIRED:
                    raise RuntimeError(
                        clean_string((checkpoint_payload or {}).get("error"))
                        or f"checkpoint_writer_failed:{decision.artifact_kind}"
                    )
                state["last_checkpoint_ref"] = clean_string(checkpoint_payload.get("artifact_ref"))
                state["last_checkpoint_continuity_id"] = clean_string(checkpoint_payload.get("continuity_id"))
            state["turn_count"] = turn_count
            state["migration_checkpoint_due"] = bool(turn_count > 0 and turn_count % 60 == 0)
        elif args.action in {"pre-clear", "pre-migrate"}:
            turn_count = current_turn_count
            checkpoint_script = (ctx.pack_root / CONTINUITY_CHECKPOINT_SCRIPT_REL).resolve()
            trigger_class = "clear_or_context_reset" if args.action == "pre-clear" else "resume_migration"
            checkpoint_cmd = [
                sys.executable,
                str(checkpoint_script),
                "--catalog",
                str(ctx.catalog_path),
                "--artifact-kind",
                "migration_checkpoint",
                "--generation-reason",
                args.action.replace("-", "_") + "_guard_handoff",
                "--trigger-class",
                trigger_class,
                "--json-only",
            ]
            rc1, checkpoint_payload, stdout1, stderr1 = _run_json(checkpoint_cmd, cwd=ctx.workspace_root)
            if rc1 != 0 or clean_string(checkpoint_payload.get("status")) != STATUS_PASS_REQUIRED:
                raise RuntimeError(clean_string(checkpoint_payload.get("error")) or f"migration_checkpoint_failed:{args.action}")
            brief_script = (ctx.pack_root / CONTINUITY_REENTRY_BRIEF_SCRIPT_REL).resolve()
            brief_cmd = [
                sys.executable,
                str(brief_script),
                "--catalog",
                str(ctx.catalog_path),
                "--continuity-lineage-ref",
                clean_string(checkpoint_payload.get("continuity_id")),
                "--generation-reason",
                args.action.replace("-", "_") + "_reentry_refresh",
                "--trigger-class",
                trigger_class,
                "--json-only",
            ]
            rc2, brief_payload, stdout2, stderr2 = _run_json(brief_cmd, cwd=ctx.workspace_root)
            if rc2 != 0 or clean_string(brief_payload.get("status")) != STATUS_PASS_REQUIRED:
                raise RuntimeError(clean_string(brief_payload.get("error")) or f"reentry_brief_refresh_failed:{args.action}")
            event_payload = {
                "action": args.action,
                "checkpoint_writer": {"returncode": rc1, "payload": checkpoint_payload, "stdout": stdout1, "stderr": stderr1},
                "brief_writer": {"returncode": rc2, "payload": brief_payload, "stdout": stdout2, "stderr": stderr2},
            }
            state["last_checkpoint_ref"] = clean_string(checkpoint_payload.get("artifact_ref"))
            state["last_checkpoint_continuity_id"] = clean_string(checkpoint_payload.get("continuity_id"))
            state["active_reentry_brief_ref"] = clean_string(brief_payload.get("brief_ref"))
            state["active_reentry_brief_continuity_id"] = clean_string(brief_payload.get("continuity_id"))
            state["migration_checkpoint_due"] = False
        else:
            turn_count = current_turn_count
            consumption_script = (ctx.pack_root / CONTINUITY_REENTRY_CONSUMPTION_SCRIPT_REL).resolve()
            consume_cmd = [
                sys.executable,
                str(consumption_script),
                "--catalog",
                str(ctx.catalog_path),
                "--scope",
                DEFAULT_SCOPE,
                "--json-only",
            ]
            rc3, consumption_payload, stdout3, stderr3 = _run_json(consume_cmd, cwd=ctx.workspace_root)
            if rc3 != 0 or clean_string(consumption_payload.get("status")) != STATUS_PASS_REQUIRED:
                raise RuntimeError(clean_string(consumption_payload.get("error")) or "reentry_consumption_emit_failed")
            event_payload = {
                "action": "post-recover",
                "reentry_consumption_writer": {"returncode": rc3, "payload": consumption_payload, "stdout": stdout3, "stderr": stderr3},
            }
            state["last_reentry_consumption_receipt_ref"] = clean_string(consumption_payload.get("receipt_ref"))
            state["migration_checkpoint_due"] = False
        receipt_doc = _guard_receipt(ctx, action=args.action, turn_count=turn_count, event_payload=event_payload)
        receipt_path = (ctx.report_root / f"guard-{args.action}-{utc_timestamp()}.json").resolve()
        _write_json(receipt_path, receipt_doc, apply=True)
        state["last_action"] = args.action
        state["last_updated_at"] = utc_iso()
        state["last_guard_receipt_ref"] = _relative_pack_ref(ctx.pack_root, receipt_path)
        _write_json(_guard_state_path(ctx.pack_root), state, apply=True)
        payload = {
            "status": STATUS_PASS_REQUIRED,
            "identity_id": ctx.identity_id,
            "catalog_path": str(ctx.catalog_path),
            "action": args.action,
            "turn_count": turn_count,
            "guard_state_path": str(_guard_state_path(ctx.pack_root)),
            "guard_receipt_path": str(receipt_path),
            "guard_receipt_ref": _relative_pack_ref(ctx.pack_root, receipt_path),
            "event_payload": event_payload,
        }
    except Exception as exc:
        payload = {
            "status": STATUS_FAIL_REQUIRED,
            "action": clean_string(getattr(args, "action", "")),
            "error": str(exc),
        }
        _emit_payload(payload, json_only=args.json_only)
        return 1

    _emit_payload(payload, json_only=args.json_only)
    return 0
