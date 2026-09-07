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

    # Build git diff command with -U0 to get zero context (only changed lines)
    cmd = ["git", "diff", "-U0", "--no-color"]

    if mode == "staged":
        cmd.append("--staged")
    elif mode == "commit":
        if not commit_hash:
            raise ValueError("commit_hash required when mode='commit'")
        cmd.append(commit_hash)

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

    # Parse diff output to extract file paths and line numbers
    return _parse_diff_output(result.stdout)


def _parse_diff_output(diff_text: str) -> list[FileDiff]:
    """
    Parse git diff -U0 output to extract file paths and line numbers.

    Format:
    diff --git a/file b/file
    --- a/file
    +++ b/file
    @@ -old_start,old_count +new_start,new_count @@
    -old line 1
    -old line 2
    +new line 1
    +new line 2
    """
    file_diffs = []
    current_file = None
    current_added = []
    current_removed = []
    current_line_num = 0

    for line in diff_text.splitlines():
        # Detect new file: +++ b/path/to/file
        if line.startswith("+++ b/"):
            # Save previous file if exists
            if current_file is not None:
                file_diffs.append(
                    FileDiff(
                        file=current_file,
                        added_lines=current_added,
                        removed_lines=current_removed,
                    )
                )
            current_file = line[6:]  # Remove "+++ b/"
            current_added = []
            current_removed = []
            current_line_num = 0
            continue

        # Detect hunk header: @@ -old_start,old_count +new_start,new_count @@
        if line.startswith("@@ ") and current_file is not None:
            # Parse: @@ -1,5 +2,3 @@
            parts = line.split()
            if len(parts) >= 3:
                # Extract new file line range: +new_start,new_count
                new_range = parts[2]
                if new_range.startswith("+"):
                    new_range = new_range[1:]
                    if "," in new_range:
                        new_start, new_count = new_range.split(",")
                        try:
                            current_line_num = int(new_start)
                        except ValueError:
                            current_line_num = 1
                    else:
                        try:
                            current_line_num = int(new_range)
                        except ValueError:
                            current_line_num = 1
            continue

        # Track line numbers in hunk
        if current_file is not None:
            if line.startswith("+") and not line.startswith("+++"):
                # Added line
                current_added.append(current_line_num)
                current_line_num += 1
            elif line.startswith("-") and not line.startswith("---"):
                # Removed line (don't increment current_line_num)
                current_removed.append(current_line_num)
            elif line.startswith(" "):
                # Context line (with -U0 there shouldn't be any, but handle it)
                current_line_num += 1

    # Save last file
    if current_file is not None:
        file_diffs.append(
            FileDiff(
                file=current_file,
                added_lines=current_added,
                removed_lines=current_removed,
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
