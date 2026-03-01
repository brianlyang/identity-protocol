#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ERR_RE = re.compile(r"\b(IP-[A-Z0-9-]+)\b")
REPORT_RE = re.compile(r"^report=(.+)$", re.MULTILINE)
OUTDATED_BASELINE_CODES = {"IP-PBL-001", "IP-PBL-002", "IP-PBL-003", "IP-PBL-004"}


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
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


def _extract_error_code(stdout: str, stderr: str) -> str:
    text = f"{stdout}\n{stderr}".strip()
    m = ERR_RE.search(text)
    return m.group(1) if m else ""


def _git_head(repo_root: Path) -> str:
    rc, out, _ = _run(["git", "-C", str(repo_root), "rev-parse", "HEAD"])
    return out.strip() if rc == 0 else ""


def _load_catalog(path: Path) -> list[dict[str, Any]]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"catalog root must be object: {path}")
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    return rows


def _extract_report_path(stdout: str) -> str:
    m = REPORT_RE.search(stdout or "")
    if not m:
        return ""
    return str(m.group(1)).strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _baseline_next_action(status: str, error_code: str, stale_reasons: list[str]) -> str:
    status_norm = str(status or "").strip().upper()
    code = str(error_code or "").strip().upper()
    reasons = {str(x).strip() for x in (stale_reasons or []) if str(x).strip()}
    if status_norm == "PASS":
        return "identity_aligned_to_current_protocol"
    if code == "IP-PBL-001" or "protocol_commit_sha_mismatch" in reasons:
        return "run_identity_creator_update"
    if code == "IP-PBL-002" or "execution_report_not_found" in reasons:
        return "bootstrap_or_update_required"
    if code in {"IP-PBL-003", "IP-PBL-004"}:
        return "resolve_protocol_baseline_source_then_update"
    return "review_protocol_baseline_then_update"


def _is_outdated_baseline(status: str, error_code: str, stale_reasons: list[str], baseline_rc: int) -> bool:
    status_norm = str(status or "").strip().upper()
    code = str(error_code or "").strip().upper()
    reasons = {str(x).strip() for x in (stale_reasons or []) if str(x).strip()}
    if status_norm != "PASS":
        return True
    if code in OUTDATED_BASELINE_CODES:
        return True
    if baseline_rc != 0:
        return True
    if "protocol_commit_sha_mismatch" in reasons:
        return True
    if "execution_report_not_found" in reasons:
        return True
    if "protocol_commit_sha_invalid" in reasons:
        return True
    if "protocol_root_unavailable" in reasons:
        return True
    return False


def _is_review_required_outcome(update_rc: int, next_action: str, error_code: str) -> bool:
    action = str(next_action or "").strip()
    code = str(error_code or "").strip()
    if update_rc != 2:
        return False
    if code:
        return False
    return action in {
        "review_required_create_pr_from_patch_plan",
        "safe_auto_blocked_require_review",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run protocol upgrade wave for runtime identities based on baseline freshness.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-ids", default="", help="optional space/comma-separated identity ids")
    ap.add_argument("--mode", choices=["review-required", "safe-auto"], default="review-required")
    ap.add_argument(
        "--capability-activation-policy",
        choices=["strict-union", "route-any-ready"],
        default="strict-union",
    )
    ap.add_argument("--dry-run", action="store_true", default=True, help="preview only (default true)")
    ap.add_argument("--apply", action="store_true", help="execute updates for outdated identities")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    dry_run = False if args.apply else True
    target_ids = {x.strip() for x in args.identity_ids.replace(",", " ").split() if x.strip()}
    rows = _load_catalog(catalog_path)
    runtime_rows = [r for r in rows if str(r.get("profile", "")).strip().lower() == "runtime"]
    if target_ids:
        runtime_rows = [r for r in runtime_rows if str(r.get("id", "")).strip() in target_ids]

    now = datetime.now(timezone.utc)
    wave_id = f"protocol-upgrade-wave-{int(now.timestamp())}"
    repo_root = Path(__file__).resolve().parent.parent
    protocol_head_sha = _git_head(repo_root)

    items: list[dict[str, Any]] = []
    outdated_ids: list[str] = []
    updated_count = 0
    review_required_count = 0
    blocked_count = 0
    skipped_count = 0

    for row in runtime_rows:
        iid = str(row.get("id", "")).strip()
        if not iid:
            continue
        base_cmd = [
            "python3",
            "scripts/validate_identity_protocol_baseline_freshness.py",
            "--identity-id",
            iid,
            "--catalog",
            str(catalog_path),
            "--repo-catalog",
            str(repo_catalog_path),
            "--baseline-policy",
            "warn",
            "--json-only",
        ]
        rc_base, out_base, err_base = _run(base_cmd)
        base_payload = _parse_json_payload(out_base) or {}
        baseline_status = str(base_payload.get("baseline_status", "FAIL")).strip().upper() or "FAIL"
        baseline_error_code = str(base_payload.get("baseline_error_code", "")).strip() or _extract_error_code(out_base, err_base)
        stale_reasons = base_payload.get("stale_reasons", [])
        if not isinstance(stale_reasons, list):
            stale_reasons = [str(stale_reasons)]

        outdated = _is_outdated_baseline(baseline_status, baseline_error_code, stale_reasons, rc_base)
        if outdated:
            outdated_ids.append(iid)

        next_action = _baseline_next_action(baseline_status, baseline_error_code, stale_reasons)
        item: dict[str, Any] = {
            "identity_id": iid,
            "baseline_status": baseline_status,
            "baseline_error_code": baseline_error_code,
            "baseline_rc": rc_base,
            "outdated": outdated,
            "report_path": str(base_payload.get("report_selected_path", "")).strip(),
            "update_rc": None,
            "update_status": "",
            "next_action": next_action,
            "error_code": "",
            "stale_reasons": stale_reasons,
        }

        if dry_run:
            skipped_count += 1
            item["update_status"] = "SKIPPED_DRY_RUN"
            item["error_code"] = baseline_error_code
            items.append(item)
            continue

        if not outdated:
            skipped_count += 1
            item["update_status"] = "SKIPPED_NOT_OUTDATED"
            item["next_action"] = "skip_not_outdated"
            item["error_code"] = baseline_error_code
            items.append(item)
            continue

        update_cmd = [
            "python3",
            "scripts/identity_creator.py",
            "update",
            "--identity-id",
            iid,
            "--mode",
            args.mode,
            "--catalog",
            str(catalog_path),
            "--repo-catalog",
            str(repo_catalog_path),
            "--capability-activation-policy",
            args.capability_activation_policy,
            "--baseline-policy",
            "warn",
        ]
        rc_upd, out_upd, err_upd = _run(update_cmd)
        item["update_rc"] = rc_upd
        update_report = _extract_report_path(out_upd)
        if update_report:
            item["report_path"] = update_report
        report_json: dict[str, Any] = {}
        if item["report_path"]:
            rp = Path(item["report_path"]).expanduser().resolve()
            if rp.exists():
                try:
                    report_json = _load_json(rp)
                except Exception:
                    report_json = {}
        item["next_action"] = str(report_json.get("next_action", "")).strip() or (
            "review_required_create_pr_from_patch_plan" if rc_upd == 0 else "inspect_update_failure"
        )
        item["error_code"] = (
            str(report_json.get("permission_error_code", "")).strip()
            or str(report_json.get("capability_activation_error_code", "")).strip()
            or _extract_error_code(out_upd, err_upd)
        )
        if rc_upd == 0:
            updated_count += 1
            item["update_status"] = "UPDATED"
        elif _is_review_required_outcome(rc_upd, item["next_action"], item["error_code"]):
            review_required_count += 1
            item["update_status"] = "REVIEW_REQUIRED"
        else:
            blocked_count += 1
            item["update_status"] = "BLOCKED"
        items.append(item)

    payload = {
        "wave_id": wave_id,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "catalog_path": str(catalog_path),
        "repo_catalog_path": str(repo_catalog_path),
        "protocol_head_sha": protocol_head_sha,
        "dry_run": dry_run,
        "mode": args.mode,
        "capability_activation_policy": args.capability_activation_policy,
        "total_identities": len(items),
        "outdated_identities": sorted(outdated_ids),
        "updated_count": updated_count,
        "review_required_count": review_required_count,
        "blocked_count": blocked_count,
        "skipped_count": skipped_count,
        "items": items,
    }

    if args.out:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] wrote: {out_path}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not dry_run and blocked_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
