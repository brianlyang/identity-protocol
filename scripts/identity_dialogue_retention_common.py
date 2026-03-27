#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"

DIALOGUE_RETENTION_CONTRACT_KEY = "dialogue_retention_contract_v1"
DIALOGUE_RETENTION_CONTRACT_ID = "rq_051_identity_dialogue_retention_contract_v1"
DIALOGUE_RETENTION_VALIDATOR_ID = "scripts/validate_identity_dialogue_retention.py"
DIALOGUE_RETENTION_SYNC_RECEIPT_FAMILY = "identity_dialogue_retention_sync_receipt_v1"
DIALOGUE_RETENTION_REPORT_ROOT_REL = Path("runtime/reports/dialogue-retention")
DIALOGUE_RETENTION_STATE_ROOT_REL = Path("runtime/state/dialogue-retention")
DIALOGUE_RETENTION_STATE_REL = DIALOGUE_RETENTION_STATE_ROOT_REL / "current-thread.json"
DIALOGUE_RETENTION_THREAD_PREFIX = "dialogue-thread-"
DIALOGUE_RETENTION_THREAD_SUFFIX = ".jsonl"
DIALOGUE_RETENTION_SUPPLEMENT_PREFIX = "dialogue-final-reply-"
DIALOGUE_RETENTION_SUPPLEMENT_SUFFIX = ".json"
DIALOGUE_RETENTION_RECEIPT_PREFIX = "dialogue-retention-sync-"
DIALOGUE_RETENTION_RECEIPT_SUFFIX = ".json"
DELIVERY_HOOK_PROTOCOL_SCRIPT = "scripts/run_identity_delivery_runtime_hooks.py"
FINAL_EMIT_SCRIPT_REL = Path("scripts/emit_current_thread_final_reply.py")


@dataclass(frozen=True)
class DialogueRetentionPackContext:
    identity_id: str
    script_path: Path
    pack_root: Path
    report_root: Path
    state_root: Path
    task_path: Path
    task_doc: dict[str, Any]
    catalog_path: Path
    protocol_home: Path
    workspace_root: Path
    source_layer: str
    resolved_scope: str
    codex_home: Path


def clean_string(value: Any) -> str:
    return str(value or "").strip()


def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_timestamp() -> str:
    return _utc_now().strftime("%Y%m%dT%H%M%S%fZ")


def _artifact_component(value: Any) -> str:
    text = clean_string(value)
    if not text:
        return ""
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in text).strip("-._")
    return cleaned or ""


def _unique_runtime_artifact_token(*components: Any) -> str:
    normalized = [_artifact_component(item) for item in components if _artifact_component(item)]
    normalized.extend([utc_timestamp(), uuid.uuid4().hex[:8]])
    return "-".join(normalized)


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    payload = load_json(path)
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
    identity_home = pack_root.parent.resolve()
    for probe in [identity_home.parent.resolve(), *identity_home.parent.resolve().parents]:
        candidate = (probe / "identity-protocol-local").resolve()
        if candidate.is_dir():
            return candidate
    raise RuntimeError(f"identity_protocol_home_not_found:{pack_root}")


def _default_catalog_path(pack_root: Path) -> Path:
    env_catalog = clean_string(os.environ.get("IDENTITY_CATALOG"))
    if env_catalog:
        return Path(env_catalog).expanduser().resolve()
    return (pack_root.parent / "catalog.local.yaml").resolve()


def default_codex_home() -> Path:
    token = clean_string(os.environ.get("CODEX_HOME"))
    if token:
        return Path(token).expanduser().resolve()
    return Path("~/.codex").expanduser().resolve()


def _source_layer_from_catalog(catalog_path: Path) -> str:
    token = catalog_path.resolve().as_posix()
    if "/.codex/" in token:
        return "global"
    if token.endswith("/.identity/catalog.local.yaml") or "/.identity/catalog.local.yaml" in token:
        return "project"
    return "unknown"


def resolve_dialogue_retention_pack_context(*, script_file: str | Path, explicit_catalog: str = "") -> DialogueRetentionPackContext:
    script_path = Path(script_file).expanduser().resolve()
    pack_root = _find_pack_root(script_path)
    task_path = (pack_root / "CURRENT_TASK.json").resolve()
    task_doc = _load_json(task_path)
    protocol_home = _find_protocol_home(pack_root)
    catalog_path = Path(clean_string(explicit_catalog)).expanduser().resolve() if clean_string(explicit_catalog) else _default_catalog_path(pack_root)
    codex_home = default_codex_home()
    return DialogueRetentionPackContext(
        identity_id=pack_root.name,
        script_path=script_path,
        pack_root=pack_root,
        report_root=(pack_root / DIALOGUE_RETENTION_REPORT_ROOT_REL).resolve(),
        state_root=(pack_root / DIALOGUE_RETENTION_STATE_ROOT_REL).resolve(),
        task_path=task_path,
        task_doc=task_doc,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
        workspace_root=protocol_home.parent.resolve(),
        source_layer=_source_layer_from_catalog(catalog_path),
        resolved_scope="USER",
        codex_home=codex_home,
    )


def resolve_pack_task(*, catalog_path: Path | None, current_task: str, identity_id: str) -> tuple[Path, Path, dict[str, Any]]:
    if clean_string(current_task):
        task_path = Path(clean_string(current_task)).expanduser().resolve()
        pack_root = task_path.parent.resolve()
        task_doc = _load_json(task_path)
        return pack_root, task_path, task_doc
    if catalog_path is None or not catalog_path.exists():
        missing_catalog = catalog_path if catalog_path is not None else "<missing>"
        raise FileNotFoundError(f"catalog not found: {missing_catalog}")
    pack_root, task_path = resolve_pack_and_task(catalog_path, identity_id)
    task_doc = _load_json(task_path)
    return pack_root, task_path, task_doc


def _contract_aliases(primary_key: str) -> tuple[str, ...]:
    legacy = primary_key.removesuffix("_v1")
    if legacy == primary_key:
        return (primary_key,)
    return (primary_key, legacy)


def resolve_contract(task_doc: dict[str, Any], primary_key: str) -> tuple[dict[str, Any], str]:
    for key in _contract_aliases(primary_key):
        node = task_doc.get(key)
        if isinstance(node, dict):
            return node, key
    return {}, primary_key


def dialogue_retention_contract_required(task_doc: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
    contract_doc, contract_key = resolve_contract(task_doc, DIALOGUE_RETENTION_CONTRACT_KEY)
    return contract_required(contract_doc), contract_doc, contract_key


def dialogue_retention_contract_skeleton() -> dict[str, Any]:
    return {
        "required": False,
        "contract_id": DIALOGUE_RETENTION_CONTRACT_ID,
        "validator": DIALOGUE_RETENTION_VALIDATOR_ID,
        "fail_mode": "fail_required",
        "product_truth_source": {
            "family": "codex_session_sidecar_jsonl",
            "path_pattern": "${CODEX_HOME}/sessions/**/*.jsonl",
            "thread_binding_env": "CODEX_THREAD_ID",
            "history_index_path": "${CODEX_HOME}/history.jsonl",
        },
        "canonical_runtime_families": [
            DIALOGUE_RETENTION_REPORT_ROOT_REL.as_posix(),
            DIALOGUE_RETENTION_STATE_ROOT_REL.as_posix(),
        ],
        "canonical_thread_mirror_glob": (
            DIALOGUE_RETENTION_REPORT_ROOT_REL / f"{DIALOGUE_RETENTION_THREAD_PREFIX}*{DIALOGUE_RETENTION_THREAD_SUFFIX}"
        ).as_posix(),
        "canonical_delivery_supplement_glob": (
            DIALOGUE_RETENTION_REPORT_ROOT_REL / f"{DIALOGUE_RETENTION_SUPPLEMENT_PREFIX}*{DIALOGUE_RETENTION_SUPPLEMENT_SUFFIX}"
        ).as_posix(),
        "canonical_sync_receipt_glob": (
            DIALOGUE_RETENTION_REPORT_ROOT_REL / f"{DIALOGUE_RETENTION_RECEIPT_PREFIX}*{DIALOGUE_RETENTION_RECEIPT_SUFFIX}"
        ).as_posix(),
        "canonical_state_path": DIALOGUE_RETENTION_STATE_REL.as_posix(),
        "delivery_hook": {
            "shared_protocol_script": DELIVERY_HOOK_PROTOCOL_SCRIPT,
            "trigger_surface": FINAL_EMIT_SCRIPT_REL.as_posix(),
            "exact_mirror_required": True,
            "supplement_current_final_reply_when_sidecar_lag_possible": True,
            "forbid_summary_rewrite_as_raw_truth": True,
        },
    }


def _base_dialogue_retention_state(identity_id: str) -> dict[str, Any]:
    return {
        "identity_id": clean_string(identity_id),
        "dialogue_retention_contract_version": "v1.6.18",
        "current_thread_id": "",
        "source_session_file": "",
        "current_thread_mirror_ref": "",
        "current_thread_mirror_sha256": "",
        "latest_source_sha256": "",
        "latest_source_size_bytes": 0,
        "latest_source_line_count": 0,
        "latest_source_last_modified_at": "",
        "latest_sync_receipt_ref": "",
        "latest_delivery_supplement_ref": "",
        "rolling_mode": "thread_mirror_in_place",
        "sync_count": 0,
        "last_synced_at": "",
    }


def _relative_pack_ref(pack_root: Path, target: Path | str) -> str:
    candidate = Path(target).expanduser().resolve() if not isinstance(target, Path) else target.expanduser().resolve()
    try:
        return candidate.relative_to(pack_root.resolve()).as_posix()
    except Exception:
        return candidate.as_posix()


def dialogue_retention_state_path(pack_root: Path) -> Path:
    return (pack_root.resolve() / DIALOGUE_RETENTION_STATE_REL).resolve()


def dialogue_retention_report_root(pack_root: Path) -> Path:
    return (pack_root.resolve() / DIALOGUE_RETENTION_REPORT_ROOT_REL).resolve()


def load_optional_state(pack_root: Path, *, identity_id: str) -> dict[str, Any]:
    state_path = dialogue_retention_state_path(pack_root)
    if state_path.is_file():
        try:
            doc = _load_json(state_path)
            if isinstance(doc, dict):
                return doc
        except Exception:
            pass
    return _base_dialogue_retention_state(identity_id)


def materialize_identity_dialogue_retention_assets(
    *,
    task: dict[str, Any],
    identity_id: str,
    pack_dir: Path,
    apply: bool,
) -> dict[str, Any]:
    pack_dir = pack_dir.expanduser().resolve()
    contract_node = task.get(DIALOGUE_RETENTION_CONTRACT_KEY)
    contract_before = json.loads(json.dumps(contract_node)) if isinstance(contract_node, dict) else None
    if not isinstance(contract_node, dict):
        task[DIALOGUE_RETENTION_CONTRACT_KEY] = dialogue_retention_contract_skeleton()
    else:
        merged = json.loads(json.dumps(dialogue_retention_contract_skeleton()))
        merged.update(contract_node)
        delivery_hook = dict(dialogue_retention_contract_skeleton().get("delivery_hook") or {})
        delivery_hook.update(dict(contract_node.get("delivery_hook") or {}))
        product_truth_source = dict(dialogue_retention_contract_skeleton().get("product_truth_source") or {})
        product_truth_source.update(dict(contract_node.get("product_truth_source") or {}))
        merged["delivery_hook"] = delivery_hook
        merged["product_truth_source"] = product_truth_source
        task[DIALOGUE_RETENTION_CONTRACT_KEY] = merged
    validators = task.get("required_validators")
    if not isinstance(validators, list):
        validators = []
        task["required_validators"] = validators
    normalized_validators = [clean_string(item) for item in validators if clean_string(item)]
    validator_added = False
    if DIALOGUE_RETENTION_VALIDATOR_ID not in normalized_validators:
        normalized_validators.append(DIALOGUE_RETENTION_VALIDATOR_ID)
        validator_added = True
    task["required_validators"] = normalized_validators
    report_root = dialogue_retention_report_root(pack_dir)
    state_root = (pack_dir / DIALOGUE_RETENTION_STATE_ROOT_REL).resolve()
    if apply:
        report_root.mkdir(parents=True, exist_ok=True)
        state_root.mkdir(parents=True, exist_ok=True)
    state_doc = load_optional_state(pack_dir, identity_id=identity_id)
    state_changed = _write_json(dialogue_retention_state_path(pack_dir), state_doc, apply=apply)
    inspection = inspect_dialogue_retention_materialization(pack_dir=pack_dir)
    contract_changed = contract_before != task.get(DIALOGUE_RETENTION_CONTRACT_KEY)
    return {
        "status": inspection.get("status", STATUS_FAIL_REQUIRED),
        "changed": bool(contract_changed or validator_added or state_changed),
        "contract_changed": contract_changed,
        "validator_added": validator_added,
        "state_changed": state_changed,
        "inspection": inspection,
    }


def inspect_dialogue_retention_materialization(*, pack_dir: Path) -> dict[str, Any]:
    pack_dir = pack_dir.expanduser().resolve()
    report_root = dialogue_retention_report_root(pack_dir)
    state_path = dialogue_retention_state_path(pack_dir)
    emitter = (pack_dir / FINAL_EMIT_SCRIPT_REL).resolve()
    hook_status, hook_reasons = detect_delivery_hook_installation(pack_dir)
    report_root_present = report_root.is_dir()
    state_present = state_path.is_file()
    overall_status = (
        STATUS_PASS_REQUIRED
        if report_root_present and state_present and hook_status == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED
    )
    return {
        "status": overall_status,
        "report_root": str(report_root),
        "report_root_present": report_root_present,
        "state_path": str(state_path),
        "state_present": state_present,
        "emitter_path": str(emitter),
        "delivery_hook_status": hook_status,
        "delivery_hook_reasons": hook_reasons,
    }


def detect_delivery_hook_installation(pack_root: Path) -> tuple[str, list[str]]:
    emitter_path = (pack_root / FINAL_EMIT_SCRIPT_REL).resolve()
    if not emitter_path.is_file():
        return STATUS_SKIPPED_NOT_REQUIRED, ["final_emitter_missing"]
    text = emitter_path.read_text(encoding="utf-8")
    reasons: list[str] = []
    if "run_identity_delivery_runtime_hooks.py" not in text:
        reasons.append("delivery_hook_invocation_missing")
    if "delivery_hook_result" not in text:
        reasons.append("delivery_hook_payload_missing")
    if reasons:
        return STATUS_FAIL_REQUIRED, reasons
    return STATUS_PASS_REQUIRED, []


def resolve_dialogue_retention_reference(token: str, *, pack_root: Path) -> Path | None:
    text = clean_string(token)
    if not text:
        return None
    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
        return resolved if resolved.exists() else None
    for base in (pack_root,):
        resolved = (base / candidate).resolve()
        if resolved.exists():
            return resolved
    return None


def _receipt_matches_state_thread(receipt_doc: dict[str, Any], *, thread_id: str) -> bool:
    expected_thread = clean_string(thread_id)
    if expected_thread and clean_string(receipt_doc.get("thread_id")) != expected_thread:
        return False
    state_binding_update_applied = receipt_doc.get("state_binding_update_applied")
    if state_binding_update_applied is False:
        return False
    sync_binding_mode = clean_string(receipt_doc.get("sync_binding_mode"))
    if sync_binding_mode and sync_binding_mode != "active_current_thread":
        return False
    return True


def latest_dialogue_retention_receipt(
    pack_root: Path,
    *,
    thread_id: str = "",
    state_bound_only: bool = False,
) -> Path | None:
    report_root = dialogue_retention_report_root(pack_root)
    hits = sorted(
        (
            path.resolve()
            for path in report_root.glob(f"{DIALOGUE_RETENTION_RECEIPT_PREFIX}*{DIALOGUE_RETENTION_RECEIPT_SUFFIX}")
            if path.is_file()
        ),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    expected_thread = clean_string(thread_id)
    for candidate in hits:
        if not expected_thread and not state_bound_only:
            return candidate
        try:
            receipt_doc = _load_json(candidate)
        except Exception:
            continue
        if expected_thread and clean_string(receipt_doc.get("thread_id")) != expected_thread:
            continue
        if state_bound_only and not _receipt_matches_state_thread(receipt_doc, thread_id=expected_thread):
            continue
        return candidate
    return None


def state_bound_dialogue_retention_receipt(pack_root: Path, *, state_doc: dict[str, Any] | None = None) -> Path | None:
    live_state = state_doc if isinstance(state_doc, dict) else load_optional_state(pack_root, identity_id=pack_root.name)
    state_thread_id = clean_string(live_state.get("current_thread_id"))
    token = clean_string(live_state.get("latest_sync_receipt_ref"))
    if not token:
        return latest_dialogue_retention_receipt(pack_root, thread_id=state_thread_id, state_bound_only=True) if state_thread_id else None
    resolved = resolve_dialogue_retention_reference(token, pack_root=pack_root)
    if resolved is not None and resolved.is_file():
        try:
            receipt_doc = _load_json(resolved)
        except Exception:
            receipt_doc = {}
        if not state_thread_id or _receipt_matches_state_thread(receipt_doc, thread_id=state_thread_id):
            return resolved
    return latest_dialogue_retention_receipt(pack_root, thread_id=state_thread_id, state_bound_only=True) if state_thread_id else None


def resolve_dialogue_retention_validation_receipt(
    pack_root: Path,
    *,
    state_doc: dict[str, Any] | None = None,
) -> tuple[Path | None, str]:
    state_receipt = state_bound_dialogue_retention_receipt(pack_root, state_doc=state_doc)
    if state_receipt is not None:
        return state_receipt, "state_bound_receipt"
    latest = latest_dialogue_retention_receipt(pack_root)
    if latest is not None:
        return latest, "latest_matching_report"
    return None, "receipt_not_found"


def latest_dialogue_retention_supplement(pack_root: Path, *, thread_id: str = "") -> Path | None:
    report_root = dialogue_retention_report_root(pack_root)
    pattern = f"{DIALOGUE_RETENTION_SUPPLEMENT_PREFIX}{clean_string(thread_id)}-*{DIALOGUE_RETENTION_SUPPLEMENT_SUFFIX}" if clean_string(thread_id) else f"{DIALOGUE_RETENTION_SUPPLEMENT_PREFIX}*{DIALOGUE_RETENTION_SUPPLEMENT_SUFFIX}"
    hits = sorted((path.resolve() for path in report_root.glob(pattern) if path.is_file()), key=lambda item: item.stat().st_mtime)
    return hits[-1] if hits else None


def thread_mirror_path(pack_root: Path, thread_id: str) -> Path:
    return (dialogue_retention_report_root(pack_root) / f"{DIALOGUE_RETENTION_THREAD_PREFIX}{clean_string(thread_id)}{DIALOGUE_RETENTION_THREAD_SUFFIX}").resolve()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _stream_source_metrics(source: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    size_bytes = 0
    line_count = 0
    with source.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            if not chunk:
                break
            digest.update(chunk)
            size_bytes += len(chunk)
            line_count += chunk.count(b"\n")
    stat = source.stat()
    return {
        "sha256": digest.hexdigest(),
        "size_bytes": size_bytes,
        "line_count": line_count,
        "last_modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="dialogue-retention-", suffix=".tmp", dir=str(destination.parent), delete=False) as tmp:
        tmp_path = Path(tmp.name).resolve()
    try:
        with source.open("rb") as src, tmp_path.open("wb") as dst:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                if not chunk:
                    break
                dst.write(chunk)
        tmp_path.replace(destination)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def _reply_metrics(reply_path: Path) -> dict[str, Any]:
    text = reply_path.read_text(encoding="utf-8")
    encoded = text.encode("utf-8")
    return {
        "reply_sha256": hashlib.sha256(encoded).hexdigest(),
        "reply_size_bytes": len(encoded),
        "reply_text": text,
    }


def _write_delivery_supplement(
    *,
    ctx: DialogueRetentionPackContext,
    thread_id: str,
    reply_file: Path,
    source_session_file: Path,
    source_metrics: dict[str, Any],
    apply: bool,
) -> dict[str, Any]:
    supplement_path = (
        ctx.report_root
        / f"{DIALOGUE_RETENTION_SUPPLEMENT_PREFIX}{_unique_runtime_artifact_token(thread_id)}{DIALOGUE_RETENTION_SUPPLEMENT_SUFFIX}"
    ).resolve()
    reply_payload = _reply_metrics(reply_file)
    payload = {
        "artifact_family": "runtime_dialogue_retention_delivery_supplement",
        "identity_id": ctx.identity_id,
        "thread_id": clean_string(thread_id),
        "captured_at": utc_iso(),
        "reply_file": str(reply_file.resolve()),
        "source_session_file": str(source_session_file.resolve()),
        "source_session_sha256": clean_string(source_metrics.get("sha256")),
        "reply_sha256": clean_string(reply_payload.get("reply_sha256")),
        "reply_size_bytes": int(reply_payload.get("reply_size_bytes") or 0),
        "reply_text": reply_payload.get("reply_text", ""),
    }
    changed = _write_json(supplement_path, payload, apply=apply)
    return {
        "status": STATUS_PASS_REQUIRED,
        "supplement_path": str(supplement_path),
        "supplement_ref": _relative_pack_ref(ctx.pack_root, supplement_path),
        "supplement_changed": changed,
        "reply_sha256": clean_string(reply_payload.get("reply_sha256")),
        "reply_size_bytes": int(reply_payload.get("reply_size_bytes") or 0),
    }


def _resolve_thread_id(*, requested_thread_id: str, state_doc: dict[str, Any]) -> str:
    if clean_string(requested_thread_id):
        return clean_string(requested_thread_id)
    env_thread = clean_string(os.environ.get("CODEX_THREAD_ID"))
    if env_thread:
        return env_thread
    return clean_string(state_doc.get("current_thread_id"))


def _resolve_source_session_file(
    *,
    ctx: DialogueRetentionPackContext,
    thread_id: str,
    requested_source_session_file: str,
    state_doc: dict[str, Any],
) -> Path:
    explicit = clean_string(requested_source_session_file)
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise RuntimeError(f"source_session_file_not_found:{path}")
        return path
    state_source = clean_string(state_doc.get("source_session_file"))
    if state_source:
        candidate = Path(state_source).expanduser().resolve()
        if candidate.is_file() and clean_string(thread_id) and clean_string(thread_id) in candidate.name:
            return candidate
    sessions_root = (ctx.codex_home / "sessions").resolve()
    if not sessions_root.is_dir():
        raise RuntimeError(f"codex_sessions_root_not_found:{sessions_root}")
    hits = sorted(
        (
            path.resolve()
            for path in sessions_root.rglob(f"*{clean_string(thread_id)}*.jsonl")
            if path.is_file()
        ),
        key=lambda item: item.stat().st_mtime,
    )
    if not hits:
        raise RuntimeError(f"source_session_file_not_found_for_thread:{thread_id}")
    return hits[-1]


def _resolve_sync_binding_mode(*, requested_thread_id: str, resolved_thread_id: str, state_doc: dict[str, Any]) -> str:
    env_thread = clean_string(os.environ.get("CODEX_THREAD_ID"))
    state_thread = clean_string(state_doc.get("current_thread_id"))
    requested = clean_string(requested_thread_id)
    if env_thread:
        return "active_current_thread" if env_thread == clean_string(resolved_thread_id) else "historical_thread_refresh"
    if requested and state_thread and requested != state_thread:
        return "historical_thread_refresh"
    return "active_current_thread"


def sync_dialogue_retention(
    ctx: DialogueRetentionPackContext,
    *,
    thread_id: str = "",
    source_session_file: str = "",
    reply_file: str = "",
    apply: bool = True,
) -> dict[str, Any]:
    state_doc = load_optional_state(ctx.pack_root, identity_id=ctx.identity_id)
    resolved_thread_id = _resolve_thread_id(requested_thread_id=thread_id, state_doc=state_doc)
    if not clean_string(resolved_thread_id):
        raise RuntimeError("thread_id_missing")
    source_path = _resolve_source_session_file(
        ctx=ctx,
        thread_id=resolved_thread_id,
        requested_source_session_file=source_session_file,
        state_doc=state_doc,
    )
    if not source_path.is_file():
        raise RuntimeError(f"source_session_file_not_found:{source_path}")
    if apply:
        ctx.report_root.mkdir(parents=True, exist_ok=True)
        ctx.state_root.mkdir(parents=True, exist_ok=True)
    source_metrics = _stream_source_metrics(source_path)
    mirror_path = thread_mirror_path(ctx.pack_root, resolved_thread_id)
    mirror_ref = _relative_pack_ref(ctx.pack_root, mirror_path)
    previous_sha = clean_string(state_doc.get("latest_source_sha256"))
    mirror_changed = (not mirror_path.exists()) or previous_sha != clean_string(source_metrics.get("sha256"))
    sync_binding_mode = _resolve_sync_binding_mode(
        requested_thread_id=thread_id,
        resolved_thread_id=resolved_thread_id,
        state_doc=state_doc,
    )
    state_binding_update_applied = sync_binding_mode == "active_current_thread"
    preserved_current_thread_id = clean_string(state_doc.get("current_thread_id"))
    if apply and mirror_changed:
        _copy_file(source_path, mirror_path)
    supplement_result = {
        "status": STATUS_NOT_APPLICABLE,
        "supplement_path": "",
        "supplement_ref": "",
        "supplement_changed": False,
        "reply_sha256": "",
        "reply_size_bytes": 0,
    }
    resolved_reply_file = clean_string(reply_file)
    if resolved_reply_file:
        reply_path = Path(resolved_reply_file).expanduser().resolve()
        if not reply_path.is_file():
            raise RuntimeError(f"reply_file_not_found:{reply_path}")
        supplement_result = _write_delivery_supplement(
            ctx=ctx,
            thread_id=resolved_thread_id,
            reply_file=reply_path,
            source_session_file=source_path,
            source_metrics=source_metrics,
            apply=apply,
        )
    receipt_path = (
        ctx.report_root
        / f"{DIALOGUE_RETENTION_RECEIPT_PREFIX}{_unique_runtime_artifact_token(resolved_thread_id)}{DIALOGUE_RETENTION_RECEIPT_SUFFIX}"
    ).resolve()
    state_path = dialogue_retention_state_path(ctx.pack_root)
    receipt_doc = {
        "receipt_family": DIALOGUE_RETENTION_SYNC_RECEIPT_FAMILY,
        "identity_id": ctx.identity_id,
        "catalog_path": str(ctx.catalog_path),
        "thread_id": clean_string(resolved_thread_id),
        "product_sidecar_truth_status": STATUS_PASS_REQUIRED,
        "source_session_status": STATUS_PASS_REQUIRED,
        "source_session_file": str(source_path),
        "source_session_sha256": clean_string(source_metrics.get("sha256")),
        "source_session_size_bytes": int(source_metrics.get("size_bytes") or 0),
        "source_session_line_count": int(source_metrics.get("line_count") or 0),
        "source_session_last_modified_at": clean_string(source_metrics.get("last_modified_at")),
        "mirror_status": STATUS_PASS_REQUIRED,
        "mirror_path": str(mirror_path),
        "mirror_ref": mirror_ref,
        "mirror_exact_source_match": True,
        "mirror_changed": bool(mirror_changed),
        "sync_binding_mode": sync_binding_mode,
        "state_binding_update_applied": state_binding_update_applied,
        "preserved_current_thread_id": preserved_current_thread_id if not state_binding_update_applied else "",
        "delivery_supplement_status": supplement_result.get("status", STATUS_NOT_APPLICABLE),
        "delivery_supplement_ref": clean_string(supplement_result.get("supplement_ref")),
        "current_thread_state_ref": DIALOGUE_RETENTION_STATE_REL.as_posix(),
        "generated_at": utc_iso(),
        "stale_reasons": [],
    }
    receipt_changed = _write_json(receipt_path, receipt_doc, apply=apply)
    state_changed = False
    if state_binding_update_applied:
        updated_state = dict(state_doc)
        updated_state.update(
            {
                "identity_id": ctx.identity_id,
                "dialogue_retention_contract_version": "v1.6.18",
                "current_thread_id": clean_string(resolved_thread_id),
                "source_session_file": str(source_path),
                "current_thread_mirror_ref": mirror_ref,
                "current_thread_mirror_sha256": clean_string(source_metrics.get("sha256")),
                "latest_source_sha256": clean_string(source_metrics.get("sha256")),
                "latest_source_size_bytes": int(source_metrics.get("size_bytes") or 0),
                "latest_source_line_count": int(source_metrics.get("line_count") or 0),
                "latest_source_last_modified_at": clean_string(source_metrics.get("last_modified_at")),
                "latest_sync_receipt_ref": _relative_pack_ref(ctx.pack_root, receipt_path),
                "latest_delivery_supplement_ref": clean_string(supplement_result.get("supplement_ref")),
                "rolling_mode": "thread_mirror_in_place",
                "sync_count": int(state_doc.get("sync_count") or 0) + 1,
                "last_synced_at": utc_iso(),
            }
        )
        state_changed = _write_json(state_path, updated_state, apply=apply)
    return {
        "status": STATUS_PASS_REQUIRED,
        "identity_id": ctx.identity_id,
        "catalog_path": str(ctx.catalog_path),
        "thread_id": clean_string(resolved_thread_id),
        "source_session_file": str(source_path),
        "source_session_sha256": clean_string(source_metrics.get("sha256")),
        "source_session_size_bytes": int(source_metrics.get("size_bytes") or 0),
        "source_session_line_count": int(source_metrics.get("line_count") or 0),
        "mirror_path": str(mirror_path),
        "mirror_ref": mirror_ref,
        "mirror_changed": bool(mirror_changed),
        "sync_binding_mode": sync_binding_mode,
        "state_binding_update_applied": state_binding_update_applied,
        "preserved_current_thread_id": preserved_current_thread_id if not state_binding_update_applied else "",
        "delivery_supplement_status": supplement_result.get("status", STATUS_NOT_APPLICABLE),
        "delivery_supplement_ref": clean_string(supplement_result.get("supplement_ref")),
        "receipt_path": str(receipt_path),
        "receipt_ref": _relative_pack_ref(ctx.pack_root, receipt_path),
        "receipt_changed": receipt_changed,
        "state_path": str(state_path),
        "state_ref": DIALOGUE_RETENTION_STATE_REL.as_posix(),
        "state_changed": state_changed,
    }
