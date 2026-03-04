#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_PASS_NON_BLOCKING = "PASS_NON_BLOCKING"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"

ERR_FEEDBACK_BATCH_MISSING = "IP-VPACK-001"
ERR_EVIDENCE_INDEX_UNLINKED = "IP-VPACK-002"
ERR_PACK_OUTPUT_INCOMPLETE = "IP-VPACK-003"
ERR_SANITIZATION_CHECK_FAILED = "IP-VPACK-004"

REQUIRED_PACK_FILES = (
    "PROMPT_MAIN.txt",
    "RUN_ORDER.txt",
    "REVIEW_REQUEST.txt",
    "INPUT_FILES/EVIDENCE_REF.json",
    "INPUT_FILES/CONSTRAINTS.json",
    "MANIFEST.json",
)

SENSITIVE_HINTS = (
    "api_key=",
    "access_token=",
    "refresh_token=",
    "secret=",
    "sk-",
    "AKIA",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "vibe_coding_feeding_pack_contract_v1",
        "vibe_coding_feeding_pack_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c

    umbrella = task.get("platform_optimization_discovery_and_feeding_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("vibe_coding_feeding_pack_contract_v1")
        if isinstance(nested, dict):
            return nested
    return {}


def _feedback_artifacts_present(pack_path: Path) -> bool:
    root = (pack_path / "runtime" / "protocol-feedback" / "outbox-to-protocol").resolve()
    return root.exists() and any(p.is_file() for p in root.rglob("FEEDBACK_BATCH_*"))


def _resolve_latest_feedback_batch(pack_path: Path, pattern: str) -> Path | None:
    raw = str(pattern or "").strip() or "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md"
    p = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ["*", "?", "["])
    hits: list[Path] = []
    if p.is_absolute():
        if has_magic:
            hits = [Path(x).expanduser().resolve() for x in glob.glob(str(p))]
        elif p.exists():
            hits = [p.resolve()]
    else:
        preferred = sorted(pack_path.glob(raw))
        if preferred:
            hits = [x.resolve() for x in preferred]
        else:
            hits = [x.resolve() for x in Path(".").glob(raw)]
    hits = [x for x in hits if x.exists() and x.is_file()]
    if not hits:
        return None
    hits.sort(key=lambda x: x.stat().st_mtime)
    return hits[-1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _contains_sensitive(content: str) -> bool:
    low = content.lower()
    return any(token.lower() in low for token in SENSITIVE_HINTS)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build deterministic vibe-coding feeding pack from protocol-feedback evidence.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--feedback-batch", default="")
    ap.add_argument("--out-root", default="/tmp/vibe-coding-feeding-packs")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
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
    required = contract_required(contract) if contract else False
    auto_required_signal = False
    if not required and _feedback_artifacts_present(pack_path):
        auto_required_signal = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "vibe_coding_feeding_pack_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "pack_root": "",
        "pack_id": "",
        "pack_files": [],
        "feedback_batch_path": "",
        "feedback_batch_sha256": "",
        "evidence_index_path": "",
        "evidence_index_linked": False,
        "deterministic_manifest_sha256": "",
        "sanitization_check_passed": True,
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    pattern = str(contract.get("feedback_batch_path_pattern", "")).strip()
    batch_path: Path | None = None
    if args.feedback_batch.strip():
        p = Path(args.feedback_batch).expanduser().resolve()
        if p.exists() and p.is_file():
            batch_path = p
    else:
        batch_path = _resolve_latest_feedback_batch(pack_path, pattern)

    if batch_path is None:
        payload["vibe_coding_feeding_pack_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_FEEDBACK_BATCH_MISSING
        payload["stale_reasons"] = ["feedback_batch_not_found"]
        _emit(payload, json_only=args.json_only)
        return 0

    batch_sha = _sha256(batch_path)
    pack_id = hashlib.sha256(f"{args.identity_id}|{batch_path}|{batch_sha}|v1".encode("utf-8")).hexdigest()[:12]
    out_root = Path(args.out_root).expanduser().resolve()
    pack_root = (out_root / f"{args.identity_id}-{pack_id}").resolve()

    evidence_index_path = (pack_path / "runtime" / "protocol-feedback" / "evidence-index" / "INDEX.md").resolve()
    evidence_index_linked = False
    if evidence_index_path.exists():
        text = evidence_index_path.read_text(encoding="utf-8", errors="ignore")
        evidence_index_linked = batch_path.name in text

    prompt_main = (
        "# Vibe Coding Feeding Pack (Protocol-Layer Sanitized)\n\n"
        "You are executing a protocol-governed enhancement task.\n"
        "Use only machine-readable artifacts provided in INPUT_FILES/.\n"
        "Do not introduce tenant/business constants.\n"
        "Preserve contract-first and policy-first semantics.\n\n"
        f"Identity: {args.identity_id}\n"
        f"Feedback batch ref: {batch_path.name}\n"
        f"Evidence SHA256: {batch_sha}\n"
    )
    run_order = (
        "1) Read INPUT_FILES/EVIDENCE_REF.json\n"
        "2) Read INPUT_FILES/CONSTRAINTS.json\n"
        "3) Execute protocol-safe implementation plan\n"
        "4) Prepare REVIEW_REQUEST.txt response with machine-readable evidence refs\n"
    )
    review_request = (
        "# Review Request (Protocol Layer)\n\n"
        "Please verify:\n"
        "- contract-first semantics preserved\n"
        "- no business-data contamination\n"
        "- evidence refs are machine-readable\n"
        "- rollback/fallback strategy is explicit\n"
    )

    evidence_ref = {
        "identity_id": args.identity_id,
        "feedback_batch_path": str(batch_path),
        "feedback_batch_sha256": batch_sha,
        "evidence_index_path": str(evidence_index_path),
        "evidence_index_linked": evidence_index_linked,
        "operation": args.operation,
    }
    constraints = {
        "contract_mode": "contract-first/policy-first",
        "protocol_layer_only": True,
        "forbid_business_data": True,
        "required_outputs": ["PROMPT_MAIN.txt", "INPUT_FILES/", "RUN_ORDER.txt", "REVIEW_REQUEST.txt"],
    }

    _write(pack_root / "PROMPT_MAIN.txt", prompt_main)
    _write(pack_root / "RUN_ORDER.txt", run_order)
    _write(pack_root / "REVIEW_REQUEST.txt", review_request)
    _write(pack_root / "INPUT_FILES" / "EVIDENCE_REF.json", json.dumps(evidence_ref, ensure_ascii=False, indent=2) + "\n")
    _write(pack_root / "INPUT_FILES" / "CONSTRAINTS.json", json.dumps(constraints, ensure_ascii=False, indent=2) + "\n")

    # deterministic manifest
    file_hashes: dict[str, str] = {}
    for rel in REQUIRED_PACK_FILES[:-1]:  # exclude MANIFEST itself initially
        f = (pack_root / rel).resolve()
        if f.exists() and f.is_file():
            file_hashes[rel] = _sha256(f)
    manifest_obj = {
        "pack_id": pack_id,
        "identity_id": args.identity_id,
        "feedback_batch_path": str(batch_path),
        "feedback_batch_sha256": batch_sha,
        "file_hashes": dict(sorted(file_hashes.items(), key=lambda kv: kv[0])),
    }
    manifest_text = json.dumps(manifest_obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    _write(pack_root / "MANIFEST.json", manifest_text)
    manifest_sha = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()

    generated_files = [str((pack_root / rel).resolve()) for rel in REQUIRED_PACK_FILES if (pack_root / rel).exists()]

    missing_outputs = [rel for rel in REQUIRED_PACK_FILES if not (pack_root / rel).exists()]
    sanitization_failed = False
    for rel in ("PROMPT_MAIN.txt", "RUN_ORDER.txt", "REVIEW_REQUEST.txt"):
        p = (pack_root / rel).resolve()
        if p.exists() and _contains_sensitive(p.read_text(encoding="utf-8", errors="ignore")):
            sanitization_failed = True
            break

    payload.update(
        {
            "vibe_coding_feeding_pack_status": STATUS_PASS_NON_BLOCKING,
            "pack_root": str(pack_root),
            "pack_id": pack_id,
            "pack_files": generated_files,
            "feedback_batch_path": str(batch_path),
            "feedback_batch_sha256": batch_sha,
            "evidence_index_path": str(evidence_index_path),
            "evidence_index_linked": evidence_index_linked,
            "deterministic_manifest_sha256": manifest_sha,
            "sanitization_check_passed": not sanitization_failed,
            "stale_reasons": [],
        }
    )

    if missing_outputs:
        payload["vibe_coding_feeding_pack_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_PACK_OUTPUT_INCOMPLETE
        payload["stale_reasons"].append(f"missing_outputs:{','.join(missing_outputs)}")

    if not evidence_index_linked:
        payload["vibe_coding_feeding_pack_status"] = STATUS_WARN_NON_BLOCKING
        if not payload["error_code"]:
            payload["error_code"] = ERR_EVIDENCE_INDEX_UNLINKED
        payload["stale_reasons"].append("evidence_index_not_linked_to_feedback_batch")

    if sanitization_failed:
        payload["vibe_coding_feeding_pack_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_SANITIZATION_CHECK_FAILED
        payload["stale_reasons"].append("sensitive_token_detected_in_pack_template")

    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
