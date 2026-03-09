#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

DEFAULT_NO_TARGET_COMPLETION_MODE = "terminal_attempt_only"
NO_TARGET_COMPLETION_MODE_ANY = {"any_attempt", "historical_any", "any"}
NO_TARGET_COMPLETION_MODE_TERMINAL = {
    "terminal_attempt_only",
    "terminal_attempt",
    "terminal",
    "final_attempt",
}
DEFAULT_ESCALATION_SIGNAL_FIELDS = [
    "route_switch_triggered",
    "human_collaboration_triggered",
    "escalation_triggered",
    "route_switch_ref",
    "human_collaboration_ref",
    "escalation_ref",
    "next_action",
]
DEFAULT_ESCALATION_SIGNAL_VALUES = {
    "true",
    "1",
    "yes",
    "triggered",
    "escalate",
    "handoff",
    "route_switch",
    "human_collaboration",
}
DEFAULT_ESCALATION_NONEMPTY_FIELDS = {"next_action"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _fail(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def _resolve_current_task(catalog_path: Path, override: str, identity_id: str) -> tuple[Path, str, Path]:
    if override:
        p = Path(override)
        if not p.exists():
            raise FileNotFoundError(f"override current task not found: {p}")
        return p, identity_id or "(override)", p.parent

    catalog = _load_yaml(catalog_path)
    target_id = identity_id or str(catalog.get("default_identity", "")).strip()
    identities = catalog.get("identities") or []
    active = next((x for x in identities if str(x.get("id", "")).strip() == target_id), None)
    if not active:
        raise FileNotFoundError(f"identity not found in catalog: {target_id}")

    pack_path = str(active.get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p, target_id, Path(pack_path)

    legacy = Path("identity") / target_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy, target_id, legacy.parent

    raise FileNotFoundError("CURRENT_TASK.json not found from catalog identity")


def _resolve_run_report(identity_id: str, pack_dir: Path, override: str) -> Path:
    if override:
        return Path(override)

    preferred = pack_dir / "runtime" / "examples" / f"{identity_id}-learning-sample.json"
    if preferred.exists():
        return preferred
    fallback_repo = (Path("identity") / "runtime" / "examples" / f"{identity_id}-learning-sample.json").resolve()
    if fallback_repo.exists():
        return fallback_repo
    # Do not fall back across identities; missing identity-scoped evidence must fail-fast.
    return preferred


def _resolve_rulebook_path(rulebook_raw: str, *, pack_dir: Path) -> Path:
    candidate = Path(rulebook_raw).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    repo_relative = candidate.resolve()
    pack_relative = (pack_dir / candidate).resolve()
    if repo_relative.exists():
        return repo_relative
    return pack_relative


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _result_token(attempt: dict[str, Any]) -> str:
    for key in ("result_code", "result", "status"):
        token = str(attempt.get(key, "")).strip().lower()
        if token:
            return token
    return ""


def _completion_token(run: dict[str, Any]) -> str:
    for key in ("overall_status", "final_status", "status", "result", "outcome"):
        token = str(run.get(key, "")).strip().lower()
        if token:
            return token
    return ""


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def _normalize_no_target_completion_mode(raw: str) -> str:
    value = str(raw or "").strip().lower()
    if value in NO_TARGET_COMPLETION_MODE_ANY:
        return "any_attempt"
    if value in NO_TARGET_COMPLETION_MODE_TERMINAL or not value:
        return "terminal_attempt_only"
    return ""


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(x).strip() for x in value if str(x).strip()]


def _has_escalation_signal(
    *,
    run: dict[str, Any],
    attempts: list[dict[str, Any]],
    fields: list[str],
    values: set[str],
    accept_nonempty_ref: bool,
    accept_nonempty_fields: set[str],
) -> bool:
    sources: list[dict[str, Any]] = [run] + [row for row in attempts if isinstance(row, dict)]
    normalized_nonempty_fields = {str(x).strip().lower() for x in accept_nonempty_fields if str(x).strip()}
    for source in sources:
        for field in fields:
            key = str(field or "").strip()
            if not key:
                continue
            raw = source.get(key)
            if isinstance(raw, bool) and raw:
                return True
            norm_key = key.lower()
            if _nonempty(raw):
                if norm_key in normalized_nonempty_fields:
                    return True
                if accept_nonempty_ref and (norm_key.endswith("_ref") or norm_key.endswith("_refs")):
                    return True
            text = str(raw or "").strip().lower()
            if text in values:
                return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity learning loop evidence (reasoning + rulebook linkage)")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", default="", help="validate for explicit identity id")
    ap.add_argument("--current-task", default="")
    ap.add_argument("--run-report", default="")
    ap.add_argument("--rulebook", default="")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        return _fail(f"missing catalog: {catalog_path}")

    try:
        task_path, identity_id, pack_dir = _resolve_current_task(catalog_path, args.current_task, args.identity_id)
    except Exception as e:
        return _fail(str(e))

    run_report_path = _resolve_run_report(identity_id, pack_dir, args.run_report)

    if not task_path.exists():
        return _fail(f"missing current task file: {task_path}")
    task = _load_json(task_path)

    lvc = task.get("learning_verification_contract") or {}
    rlc = task.get("reasoning_loop_contract") or {}
    rb_contract = task.get("rulebook_contract") or {}

    if not lvc:
        return _fail("learning_verification_contract missing in CURRENT_TASK")

    if not run_report_path.exists():
        return _fail(f"missing run report: {run_report_path}")
    run = _load_json(run_report_path)

    print(f"[INFO] identity={identity_id} current_task={task_path}")
    print(f"[INFO] run_report={run_report_path}")

    rc = 0

    run_id = str(run.get("run_id") or "").strip()
    if lvc.get("run_id_required", False) and not run_id:
        print("[FAIL] run_id is required by learning_verification_contract")
        rc = 1
    else:
        print(f"[OK]   run_id={run_id}")

    attempts = run.get("reasoning_attempts") or []
    if lvc.get("reasoning_trace_required", False):
        if not isinstance(attempts, list) or not attempts:
            print("[FAIL] reasoning_trace_required=true but reasoning_attempts is empty")
            rc = 1
        else:
            print(f"[OK]   reasoning_attempts count={len(attempts)}")

    required_attempt_fields = set(rlc.get("mandatory_fields_per_attempt") or [])
    no_target_tokens = {
        str(x).strip().lower()
        for x in (rlc.get("no_target_result_tokens") or ["no_target_reached", "not_reached", "target_not_reached"])
        if str(x).strip()
    }
    completion_tokens = {
        str(x).strip().lower()
        for x in (rlc.get("completion_states_done") or ["done", "pass", "passed", "success", "completed", "closed"])
        if str(x).strip()
    }
    failure_requires_next_action = _boolish(rlc.get("failure_requires_next_action", True))
    max_attempts_before_escalation = int(rlc.get("max_attempts_before_escalation", 3))
    no_target_completion_mode = _normalize_no_target_completion_mode(
        str(
            rlc.get(
                "no_target_completion_mode",
                rlc.get("no_target_completion_scope", DEFAULT_NO_TARGET_COMPLETION_MODE),
            )
        )
    )
    if not no_target_completion_mode:
        print("[FAIL] invalid no_target_completion_mode in reasoning_loop_contract")
        return 1
    done_requires_terminal_target_reached = _boolish(rlc.get("done_requires_terminal_target_reached", True))
    escalation_signal_fields = _as_str_list(rlc.get("escalation_signal_fields")) or list(DEFAULT_ESCALATION_SIGNAL_FIELDS)
    escalation_signal_values = {
        token.strip().lower() for token in _as_str_list(rlc.get("escalation_signal_values"))
    } or DEFAULT_ESCALATION_SIGNAL_VALUES
    escalation_signal_accept_nonempty_ref = _boolish(rlc.get("escalation_signal_accept_nonempty_ref", True))
    escalation_signal_nonempty_fields = {
        token.strip().lower()
        for token in _as_str_list(rlc.get("escalation_signal_nonempty_fields"))
        if token.strip()
    } or set(DEFAULT_ESCALATION_NONEMPTY_FIELDS)
    no_target_reached_detected = False
    failed_attempt_count = 0
    failed_without_next_action_count = 0
    terminal_attempt_target_reached = False
    terminal_attempt_no_target_reached = False

    for i, att in enumerate(attempts, start=1):
        if not isinstance(att, dict):
            print(f"[FAIL] attempt[{i}] must be object")
            rc = 1
            continue
        missing = [k for k in required_attempt_fields if k not in att]
        if missing:
            print(f"[FAIL] attempt[{i}] missing fields: {missing}")
            rc = 1
        else:
            print(f"[OK]   attempt[{i}] fields complete")

        result_token = _result_token(att)
        no_target = _boolish(att.get("no_target_reached")) or (result_token in no_target_tokens)
        no_target_reached_detected = no_target_reached_detected or no_target
        target_reached = _boolish(att.get("target_reached")) or (result_token in {"pass", "passed", "success", "resolved", "target_reached"})
        attempt_failed = no_target or (result_token in {"fail", "failed", "error", "blocked"}) or (not target_reached and bool(result_token))
        if attempt_failed:
            failed_attempt_count += 1
            if failure_requires_next_action and not str(att.get("next_action", "")).strip():
                print(f"[FAIL] attempt[{i}] failed but next_action is missing")
                failed_without_next_action_count += 1
                rc = 1
        terminal_attempt_target_reached = target_reached
        terminal_attempt_no_target_reached = no_target

    completion_token = _completion_token(run)
    completion_is_done = completion_token in completion_tokens
    no_target_done_violation = False
    if completion_is_done:
        if no_target_completion_mode == "any_attempt":
            no_target_done_violation = no_target_reached_detected
        else:
            no_target_done_violation = terminal_attempt_no_target_reached
        if done_requires_terminal_target_reached and not terminal_attempt_target_reached:
            no_target_done_violation = True

    if no_target_done_violation:
        print(
            "[FAIL] done-transition violation "
            f"(mode={no_target_completion_mode}, terminal_target_reached={terminal_attempt_target_reached}, "
            f"terminal_no_target={terminal_attempt_no_target_reached})"
        )
        rc = 1
    else:
        print("[OK]   no-target completion semantic respected")

    if failed_attempt_count > max_attempts_before_escalation:
        has_escalation = _has_escalation_signal(
            run=run,
            attempts=[x for x in attempts if isinstance(x, dict)],
            fields=escalation_signal_fields,
            values=escalation_signal_values,
            accept_nonempty_ref=escalation_signal_accept_nonempty_ref,
            accept_nonempty_fields=escalation_signal_nonempty_fields,
        )
        if not has_escalation:
            print(
                "[FAIL] failed attempts exceed max_attempts_before_escalation "
                f"({failed_attempt_count}>{max_attempts_before_escalation}) without escalation signal"
            )
            rc = 1
        else:
            print("[OK]   escalation signal present for over-threshold failures")

    if args.rulebook:
        rulebook_path = Path(args.rulebook)
    else:
        rb_val = str(rb_contract.get("rulebook_path") or "").strip()
        if rb_val:
            rulebook_path = _resolve_rulebook_path(rb_val, pack_dir=pack_dir)
        else:
            rulebook_path = pack_dir / "RULEBOOK.jsonl"
    if lvc.get("rulebook_update_required", False):
        if not rulebook_path.exists():
            print(f"[FAIL] rulebook not found: {rulebook_path}")
            rc = 1
        else:
            link_field = str(lvc.get("rulebook_link_field") or "evidence_run_id")
            matched = 0
            lines = [ln.strip() for ln in rulebook_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            for ln in lines:
                try:
                    row = json.loads(ln)
                except Exception:
                    continue
                if str(row.get(link_field) or "").strip() == run_id:
                    matched += 1
            if matched <= 0:
                print(f"[FAIL] no rulebook records linked by {link_field}={run_id}")
                rc = 1
            else:
                print(f"[OK]   linked rulebook records found: {matched}")

    if rc == 0:
        print("Identity learning-loop validation PASSED")
    else:
        print("Identity learning-loop validation FAILED")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
