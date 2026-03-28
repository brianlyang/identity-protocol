#!/usr/bin/env python3
from __future__ import annotations


RELEASE_CLOSURE_PHILOSOPHY_ORDER_MARKERS: tuple[str, ...] = (
    "source-order",
    "reading-order",
    "adjudication-order",
)

RELEASE_CLOSURE_CLOSURE_CLASS_MARKERS: tuple[str, ...] = (
    "root-closed",
    "machine-closed",
    "runtime-closed",
)

RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_MARKERS: tuple[str, ...] = (
    "repair lane",
    "terminal-truth observation lane",
    "creator/update admission lane",
    "repair success != clean terminal truth",
)


def collect_release_closure_philosophy_order_stale_reasons(text: str) -> list[str]:
    missing = [
        marker for marker in RELEASE_CLOSURE_PHILOSOPHY_ORDER_MARKERS if marker not in text
    ]
    return ["philosophy_root_order_markers_missing"] if missing else []


def collect_release_closure_closure_class_stale_reasons(text: str, *, label: str) -> list[str]:
    missing = [marker for marker in RELEASE_CLOSURE_CLOSURE_CLASS_MARKERS if marker not in text]
    return [f"{label}_missing_root_machine_runtime_closure_markers"] if missing else []


def collect_release_closure_terminal_truth_split_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    stale_reasons: list[str] = []
    for marker in RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_MARKERS:
        if marker not in text:
            stale_reasons.append(f"{label}_missing_terminal_truth_split_marker:{marker}")
    return stale_reasons

