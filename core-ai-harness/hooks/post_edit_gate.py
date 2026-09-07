#!/usr/bin/env python3
"""
PostToolUse hook - checks gate violations after file edits.

Runs when Claude uses Edit or Write tools on files.
For Java files, runs ast-grep to check for FP paradigm violations.
Returns structured findings for Claude to fix.

Key behaviors:
- Only checks Java files (.java extension)
- Returns JSON with decision and reason for Claude to see
- Never blocks on non-Java files
- Handles missing dependencies gracefully (skipped status)
- Always exits 0 to avoid hook error messages
"""

import sys
import json
import os
from pathlib import Path

# Add parent directory to Python path so we can import _lib
sys.path.insert(0, str(Path(__file__).parent))

from _lib import PLUGIN_ROOT, is_java_file
from _lib.gate_runner import run_gates, load_config
from _lib.project_detector import detect_project
from _lib import debug_log

# Module-level cache to avoid redundant file system scans and config parsing
_project_cache = {}
_config_cache = {}


def get_cached_project_info(project_root: Path):
    """Get cached project info to avoid repeated file system scans."""
    cache_key = str(project_root)
    if cache_key not in _project_cache:
        _project_cache[cache_key] = detect_project(project_root)
    return _project_cache[cache_key]


def get_cached_config(project_root: Path | None = None):
    """Get cached config to avoid repeated TOML parsing.

    Args:
        project_root: Project root path. If None, uses CWD.
    """
    if project_root is None:
        project_root = Path.cwd()
    cache_key = str(project_root)
    if cache_key not in _config_cache:
        _config_cache[cache_key] = load_config()
    return _config_cache[cache_key]


SESSION_STATE_DIR = Path("/tmp/core-ai-harness")


def update_session_state(session_id: str, pending_errors: int) -> None:
    """
    Persist the unresolved-error count for the current session.

    This state is read by the Stop hook (stop_report.py) to decide whether
    to remind Claude about unresolved gate violations at the end of a turn.
    """
    try:
        SESSION_STATE_DIR.mkdir(exist_ok=True)
        state_file = SESSION_STATE_DIR / f"{session_id}.json"
        state_file.write_text(
            json.dumps({"pending_errors": pending_errors}),
            encoding="utf-8",
        )
    except Exception as e:
        debug_log(f"Failed to update session state: {e}")


def main():
    """Entry point for PostToolUse hook."""
    # Read hook input from stdin (provided by Claude Code)
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # If we can't parse input, exit gracefully
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")

    # Get the file path that was edited
    tool_input = hook_input.get("tool_input", {})
    file_path_str = tool_input.get("file_path", "")

    if not file_path_str:
        # No file path, nothing to check
        sys.exit(0)

    file_path = Path(file_path_str)

    # Only check Java files
    if not is_java_file(file_path):
        # Not a Java file, skip check
        sys.exit(0)

    # Check if file exists (Write/Edit should have created it)
    if not file_path.exists():
        # File doesn't exist, skip check
        sys.exit(0)

    # Get current working directory
    cwd = Path.cwd()

    # Get cached config and project info to avoid redundant I/O
    config = get_cached_config(cwd)
    project_info = get_cached_project_info(cwd)
    debug_log(f"Project: {project_info.type}/{project_info.build_tool}")

    # Run gates on the edited file
    # profile=None → uses config's active profile (see run_gates)
    findings, statuses = run_gates(
        scope="files",
        files=[str(file_path)],
        project_root=cwd,
        profile=None,
    )

    # Log any skipped gates (dependencies missing) for debugging
    # Skipped gates don't block the overall check; we continue with findings
    # from the gates that did run successfully.
    skipped_gates = [g for g, status in statuses.items() if status == "skipped"]
    if skipped_gates:
        debug_log(f"Skipped gates (dependencies missing): {skipped_gates}")

    # Filter for ERROR severity only (WARNING/HINT don't block)
    errors = [f for f in findings if f.severity == "ERROR"]

    # Record session state for the Stop hook (0 when clean so a later fix
    # clears the reminder)
    update_session_state(session_id, len(errors))

    if not errors:
        # No errors found, allow the edit
        sys.exit(0)

    # Format findings for Claude to see
    findings_json = [f.to_dict() for f in errors]

    # Build a reason message for Claude
    reason_parts = [
        f"Gate check found {len(errors)} violation(s):",
        "",
    ]

    for f in errors[:10]:  # Limit to first 10 to avoid overwhelming
        reason_parts.append(f"- Line {f.line}: {f.rule_id}")
        if f.message:
            reason_parts.append(f"  {f.message}")

    if len(errors) > 10:
        reason_parts.append(f"\n... and {len(errors) - 10} more violations")

    reason_parts.append("\nPlease fix these violations before proceeding.")
    reason_parts.append("Use `/gate-fixer` to auto-fix common issues.")

    # Output JSON for Claude to see
    output = {
        "decision": "block",
        "reason": "\n".join(reason_parts),
        "findings": findings_json,
    }

    print(json.dumps(output))

    # Exit 0 (hook succeeded, even though we blocked the tool)
    # Exit 2 would be a hard block, but we want Claude to see the reason
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Catch-all: never let the hook fail with an error
        # This prevents "hook error" messages from appearing
        # Log to stderr for debugging
        print(f"PostToolUse hook error: {e}", file=sys.stderr)
        sys.exit(0)
