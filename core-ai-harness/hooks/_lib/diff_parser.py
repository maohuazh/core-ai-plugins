"""
Git diff parser.

Parses git diff output to extract changed files and their line ranges.
Used for incremental scanning (only scan changed files).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


DiffMode = Literal["unstaged", "staged", "commit"]


@dataclass
class FileDiff:
    """Diff information for a single file."""

    file: str  # Relative path to project root
    added_lines: list[int]  # Line numbers that were added
    removed_lines: list[int]  # Line numbers that were removed (for context)

    @property
    def total_additions(self) -> int:
        return len(self.added_lines)

    @property
    def total_deletions(self) -> int:
        return len(self.removed_lines)


def get_changed_files(
    project_root: str | Path | None = None,
    mode: DiffMode = "unstaged",
    commit_hash: str | None = None,
) -> list[FileDiff]:
    """
    Get list of changed files with their diff information.

    Args:
        project_root: Path to git repository root. Defaults to CWD.
        mode: "unstaged" (working tree), "staged" (index), or "commit" (specific commit).
        commit_hash: Required if mode="commit". The commit hash to diff against.

    Returns:
        List of FileDiff objects.
    """
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root).resolve()

    # Build git diff command
    cmd = ["git", "diff"]

    if mode == "staged":
        cmd.append("--staged")
    elif mode == "commit":
        if not commit_hash:
            raise ValueError("commit_hash required when mode='commit'")
        cmd.append(commit_hash)

    cmd.extend(["--numstat", "--no-color"])

    # Run git diff
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []

    if result.returncode != 0:
        return []

    # Parse numstat output: "added\tdeleted\tfilename"
    file_diffs = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) != 3:
            continue

        added_str, deleted_str, file_path = parts

        # Binary files show "-" instead of numbers
        if added_str == "-" or deleted_str == "-":
            continue

        try:
            added_count = int(added_str)
            deleted_count = int(deleted_str)
        except ValueError:
            continue

        # For simplicity, we don't extract exact line numbers here.
        # The gate_runner will pass the file list to ast-grep, which scans the whole file.
        # Exact line numbers would require parsing the full diff output.
        file_diffs.append(
            FileDiff(
                file=file_path,
                added_lines=list(range(1, added_count + 1)),  # Approximate
                removed_lines=list(range(1, deleted_count + 1)),  # Approximate
            )
        )

    return file_diffs


def get_changed_file_paths(
    project_root: str | Path | None = None,
    mode: DiffMode = "unstaged",
    commit_hash: str | None = None,
) -> list[str]:
    """
    Get list of changed file paths (simpler version without line details).

    Args:
        project_root: Path to git repository root.
        mode: "unstaged", "staged", or "commit".
        commit_hash: Required if mode="commit".

    Returns:
        List of relative file paths.
    """
    file_diffs = get_changed_files(project_root, mode, commit_hash)
    return [fd.file for fd in file_diffs]


def filter_java_files(file_paths: list[str]) -> list[str]:
    """Filter list to only Java source files."""
    return [f for f in file_paths if f.endswith(".java")]


def get_staged_java_files(project_root: str | Path | None = None) -> list[str]:
    """Get staged Java files (ready to be committed)."""
    return filter_java_files(get_changed_file_paths(project_root, mode="staged"))


def get_unstaged_java_files(project_root: str | Path | None = None) -> list[str]:
    """Get unstaged Java files (modified but not staged)."""
    return filter_java_files(get_changed_file_paths(project_root, mode="unstaged"))
