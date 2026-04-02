from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

HISTORY_MODE_CLONE_ONLY = "clone_only"
HISTORY_MODE_CLONE_WITH_WORKTREE_OVERLAY = "clone_with_worktree_overlay"
SUPPORTED_HISTORY_MODES = (
    HISTORY_MODE_CLONE_ONLY,
    HISTORY_MODE_CLONE_WITH_WORKTREE_OVERLAY,
)
DEFAULT_BASELINE_COMMIT_MESSAGE = "probe: current worktree baseline"
DEFAULT_BASELINE_COMMIT_USER_NAME = "protocol-ci"
DEFAULT_BASELINE_COMMIT_USER_EMAIL = "protocol-ci@example.invalid"

SKIP_ENTRY_NAMES = {
    ".git",
    "__pycache__",
    ".DS_Store",
    ".tmp",
}


@dataclass(frozen=True)
class RepoMaterializationStats:
    source_repo_root: str
    target_repo_root: str
    history_mode: str
    source_dirty_entry_count: int
    worktree_overlay_applied: bool
    copied_file_count: int
    copied_symlink_count: int
    created_dir_count: int
    removed_entry_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run_git(source_repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ("git", "-C", str(source_repo), *args),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git command failed rc={proc.returncode}: git -C {source_repo} {' '.join(args)}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc.stdout


def _dirty_entry_count(source_repo: Path) -> int:
    output = _run_git(source_repo, "status", "--short")
    return len([line for line in output.splitlines() if line.strip()])


def _remove_path(path: Path) -> int:
    if not path.exists() and not path.is_symlink():
        return 0
    if path.is_symlink() or path.is_file():
        path.unlink()
        return 1
    shutil.rmtree(path)
    return 1


def _ensure_directory(path: Path) -> int:
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        _remove_path(path)
    if path.exists():
        return 0
    path.mkdir(parents=True, exist_ok=True)
    return 1


def _copy_symlink(source: Path, target: Path) -> int:
    link_target = os.readlink(source)
    if target.is_symlink() and os.readlink(target) == link_target:
        return 0
    if target.exists() or target.is_symlink():
        _remove_path(target)
    target.symlink_to(link_target, target_is_directory=source.resolve().is_dir())
    return 1


def _mirror_tree(source_root: Path, target_root: Path) -> dict[str, int]:
    counters = {
        "copied_file_count": 0,
        "copied_symlink_count": 0,
        "created_dir_count": 0,
        "removed_entry_count": 0,
    }

    def sync_dir(source_dir: Path, target_dir: Path) -> None:
        counters["created_dir_count"] += _ensure_directory(target_dir)
        source_names = {entry.name for entry in source_dir.iterdir() if entry.name not in SKIP_ENTRY_NAMES}
        for target_entry in list(target_dir.iterdir()):
            if target_entry.name in SKIP_ENTRY_NAMES:
                continue
            if target_entry.name not in source_names:
                counters["removed_entry_count"] += _remove_path(target_entry)

        for source_entry in sorted(source_dir.iterdir(), key=lambda item: item.name):
            if source_entry.name in SKIP_ENTRY_NAMES:
                continue
            target_entry = target_dir / source_entry.name
            if source_entry.is_symlink():
                counters["copied_symlink_count"] += _copy_symlink(source_entry, target_entry)
                continue
            if source_entry.is_dir():
                if target_entry.is_symlink() or (target_entry.exists() and not target_entry.is_dir()):
                    counters["removed_entry_count"] += _remove_path(target_entry)
                sync_dir(source_entry, target_entry)
                continue
            if target_entry.is_symlink() or (target_entry.exists() and not target_entry.is_file()):
                counters["removed_entry_count"] += _remove_path(target_entry)
            shutil.copy2(source_entry, target_entry)
            counters["copied_file_count"] += 1

    sync_dir(source_root, target_root)
    return counters


def materialize_repo_snapshot(
    *,
    source_repo_root: Path,
    target_repo_root: Path,
    history_mode: str,
) -> RepoMaterializationStats:
    mode = str(history_mode or "").strip()
    if mode not in SUPPORTED_HISTORY_MODES:
        raise ValueError(f"unsupported history_mode: {history_mode}")
    source_repo_root = source_repo_root.expanduser().resolve()
    target_repo_root = target_repo_root.expanduser().resolve()
    if not (source_repo_root / ".git").exists():
        raise ValueError(f"source repo missing .git: {source_repo_root}")
    if target_repo_root.exists():
        raise ValueError(f"target repo already exists: {target_repo_root}")
    target_repo_root.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ("git", "clone", "--quiet", "--local", str(source_repo_root), str(target_repo_root)),
        check=True,
    )
    counters = {
        "copied_file_count": 0,
        "copied_symlink_count": 0,
        "created_dir_count": 0,
        "removed_entry_count": 0,
    }
    worktree_overlay_applied = mode == HISTORY_MODE_CLONE_WITH_WORKTREE_OVERLAY
    if worktree_overlay_applied:
        counters = _mirror_tree(source_repo_root, target_repo_root)

    return RepoMaterializationStats(
        source_repo_root=str(source_repo_root),
        target_repo_root=str(target_repo_root),
        history_mode=mode,
        source_dirty_entry_count=_dirty_entry_count(source_repo_root),
        worktree_overlay_applied=worktree_overlay_applied,
        copied_file_count=int(counters["copied_file_count"]),
        copied_symlink_count=int(counters["copied_symlink_count"]),
        created_dir_count=int(counters["created_dir_count"]),
        removed_entry_count=int(counters["removed_entry_count"]),
    )


def create_baseline_commit(
    *,
    target_repo_root: Path,
    message: str = DEFAULT_BASELINE_COMMIT_MESSAGE,
    user_name: str = DEFAULT_BASELINE_COMMIT_USER_NAME,
    user_email: str = DEFAULT_BASELINE_COMMIT_USER_EMAIL,
) -> str:
    target_repo_root = target_repo_root.expanduser().resolve()
    if not (target_repo_root / ".git").exists():
        raise ValueError(f"target repo missing .git: {target_repo_root}")
    _run_git(target_repo_root, "config", "user.name", user_name)
    _run_git(target_repo_root, "config", "user.email", user_email)
    status = _run_git(target_repo_root, "status", "--short")
    if not any(line.strip() for line in status.splitlines()):
        return ""
    _run_git(target_repo_root, "add", "-A")
    proc = subprocess.run(
        ("git", "-C", str(target_repo_root), "commit", "-m", message),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git baseline commit failed rc={proc.returncode}: git -C {target_repo_root} commit -m {message!r}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return _run_git(target_repo_root, "rev-parse", "HEAD").strip()
