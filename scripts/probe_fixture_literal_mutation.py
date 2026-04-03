#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def _mutate_text(*, text: str, needle: str, replacement: str, mode: str) -> tuple[str, int]:
    if mode == "first":
        count = text.count(needle)
        return text.replace(needle, replacement, 1), min(count, 1)
    if mode == "all":
        count = text.count(needle)
        return text.replace(needle, replacement), count
    raise ValueError(f"unsupported mutation mode: {mode}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Mutate probe fixture literals with fail-close residual checks.")
    ap.add_argument("--path", required=True, help="target file path")
    ap.add_argument("--needle", required=True, help="literal text to mutate")
    ap.add_argument("--replacement", default="", help="replacement literal")
    ap.add_argument(
        "--mode",
        choices=("first", "all"),
        default="all",
        help="whether to mutate the first occurrence only or all occurrences (default: all)",
    )
    ap.add_argument(
        "--min-occurrences",
        type=int,
        default=1,
        help="minimum number of literal occurrences required before mutation (default: 1)",
    )
    ap.add_argument(
        "--require-absent-after",
        action="store_true",
        help="fail if the original literal still exists after mutation",
    )
    args = ap.parse_args()

    target = Path(args.path).expanduser().resolve()
    text = target.read_text(encoding="utf-8")
    occurrence_count = text.count(args.needle)
    if occurrence_count < int(args.min_occurrences):
        raise SystemExit(
            f"probe setup failed: expected at least {int(args.min_occurrences)} occurrence(s) for literal in {target}; "
            f"found {occurrence_count}"
        )
    mutated, replaced = _mutate_text(
        text=text,
        needle=args.needle,
        replacement=args.replacement,
        mode=str(args.mode),
    )
    if replaced < int(args.min_occurrences):
        raise SystemExit(
            f"probe setup failed: mutation replaced {replaced} occurrence(s), expected at least {int(args.min_occurrences)}"
        )
    if args.require_absent_after and args.needle in mutated:
        residual = mutated.count(args.needle)
        raise SystemExit(
            f"probe setup failed: literal residual remained after mutation in {target}; remaining_occurrences={residual}"
        )
    target.write_text(mutated, encoding="utf-8")
    print(
        f"[OK] probe fixture mutated: path={target} mode={args.mode} "
        f"replaced_occurrences={replaced} original_occurrences={occurrence_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
