#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}"
mkdir -p "$TMP_ROOT"
WORK_ROOT="$(mktemp -d "$TMP_ROOT/protocol-feedback-promotion-probes.XXXXXX")"
trap 'rm -rf "$WORK_ROOT"' EXIT

VALIDATOR="$REPO_ROOT/scripts/validate_protocol_feedback_promotion_decision.py"

ORDINARY_JSON="$WORK_ROOT/ordinary.json"
PENDING_JSON="$WORK_ROOT/pending.json"
ATOMIC_JSON="$WORK_ROOT/atomic.json"
BATCH_JSON="$WORK_ROOT/batch.json"
BLOCKED_JSON="$WORK_ROOT/blocked.json"
MISS_DECISION_JSON="$WORK_ROOT/miss-decision.json"
MISS_EMIT_JSON="$WORK_ROOT/miss-emit.json"
MISS_BLOCKER_JSON="$WORK_ROOT/miss-blocker.json"
MISS_INQUIRY_JSON="$WORK_ROOT/miss-inquiry.json"

python3 "$VALIDATOR" --fixture-case ordinary_protocol_discussion --json-only > "$ORDINARY_JSON"
python3 "$VALIDATOR" --fixture-case explicit_request_pending --json-only > "$PENDING_JSON"
python3 "$VALIDATOR" --fixture-case owner_gap_emitted_atomic --json-only > "$ATOMIC_JSON"
python3 "$VALIDATOR" --fixture-case root_cause_emitted_batch --json-only > "$BATCH_JSON"
python3 "$VALIDATOR" --fixture-case recurrent_drift_blocked --json-only > "$BLOCKED_JSON"

set +e
python3 "$VALIDATOR" --fixture-case trigger_missing_decision_receipt --json-only > "$MISS_DECISION_JSON"
MISS_DECISION_RC=$?
python3 "$VALIDATOR" --fixture-case emit_now_missing_emit_receipt --json-only > "$MISS_EMIT_JSON"
MISS_EMIT_RC=$?
python3 "$VALIDATOR" --fixture-case blocked_missing_blocker_receipt --json-only > "$MISS_BLOCKER_JSON"
MISS_BLOCKER_RC=$?
python3 "$VALIDATOR" --fixture-case pending_missing_inquiry_requiredization --json-only > "$MISS_INQUIRY_JSON"
MISS_INQUIRY_RC=$?
set -e

python3 - "$ORDINARY_JSON" "$PENDING_JSON" "$ATOMIC_JSON" "$BATCH_JSON" "$BLOCKED_JSON" "$MISS_DECISION_JSON" "$MISS_DECISION_RC" "$MISS_EMIT_JSON" "$MISS_EMIT_RC" "$MISS_BLOCKER_JSON" "$MISS_BLOCKER_RC" "$MISS_INQUIRY_JSON" "$MISS_INQUIRY_RC" <<'PY'
from pathlib import Path
import json
import sys

ordinary = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
pending = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
atomic = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
batch = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
blocked = json.loads(Path(sys.argv[5]).read_text(encoding="utf-8"))
miss_decision = json.loads(Path(sys.argv[6]).read_text(encoding="utf-8"))
miss_decision_rc = int(sys.argv[7])
miss_emit = json.loads(Path(sys.argv[8]).read_text(encoding="utf-8"))
miss_emit_rc = int(sys.argv[9])
miss_blocker = json.loads(Path(sys.argv[10]).read_text(encoding="utf-8"))
miss_blocker_rc = int(sys.argv[11])
miss_inquiry = json.loads(Path(sys.argv[12]).read_text(encoding="utf-8"))
miss_inquiry_rc = int(sys.argv[13])

def assert_pass(payload, expected_state, expected_trigger):
    if payload.get("status") != "PASS_REQUIRED":
        raise SystemExit(f"positive case did not PASS_REQUIRED: {payload.get('case_id')}")
    if payload.get("machine_state") != expected_state:
        raise SystemExit(
            f"positive case machine_state mismatch: {payload.get('case_id')} -> {payload.get('machine_state')}"
        )
    matched = payload.get("matched_trigger_classes", [])
    if expected_trigger is None:
        if matched:
            raise SystemExit(f"ordinary control unexpectedly matched trigger: {matched}")
    elif matched != [expected_trigger]:
        raise SystemExit(f"matched trigger mismatch for {payload.get('case_id')}: {matched}")

assert_pass(ordinary, "not_required", None)
assert_pass(pending, "pending", "user_explicit_protocol_review_request")
assert_pass(atomic, "emitted", "assistant_identified_protocol_owner_gap")
assert_pass(batch, "emitted", "protocol_root_cause_explanation_started")
assert_pass(blocked, "blocked", "recurrent_protocol_drift_detected")

if miss_decision_rc == 0:
    raise SystemExit("missing-decision negative unexpectedly succeeded")
if miss_decision.get("status") != "FAIL_REQUIRED":
    raise SystemExit("missing-decision negative did not FAIL_REQUIRED")
for token in ("matched_trigger_without_artifact", "promotion_expected_but_decision_receipt_absent"):
    if token not in miss_decision.get("stale_reasons", []):
        raise SystemExit(f"missing-decision negative missing stale reason: {token}")

if miss_emit_rc == 0:
    raise SystemExit("missing-emit negative unexpectedly succeeded")
if miss_emit.get("status") != "FAIL_REQUIRED":
    raise SystemExit("missing-emit negative did not FAIL_REQUIRED")
if "emit_now_without_emit_receipt" not in miss_emit.get("stale_reasons", []):
    raise SystemExit("missing-emit negative missing emit_now_without_emit_receipt")

if miss_blocker_rc == 0:
    raise SystemExit("missing-blocker negative unexpectedly succeeded")
if miss_blocker.get("status") != "FAIL_REQUIRED":
    raise SystemExit("missing-blocker negative did not FAIL_REQUIRED")
if "blocked_without_blocker_receipt" not in miss_blocker.get("stale_reasons", []):
    raise SystemExit("missing-blocker negative missing blocked_without_blocker_receipt")

if miss_inquiry_rc == 0:
    raise SystemExit("missing-inquiry negative unexpectedly succeeded")
if miss_inquiry.get("status") != "FAIL_REQUIRED":
    raise SystemExit("missing-inquiry negative did not FAIL_REQUIRED")
if "pending_without_inquiry_requiredization" not in miss_inquiry.get("stale_reasons", []):
    raise SystemExit("missing-inquiry negative missing pending_without_inquiry_requiredization")
PY

echo "PASS"
