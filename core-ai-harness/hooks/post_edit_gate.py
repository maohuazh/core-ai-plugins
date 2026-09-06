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
from _lib.gate_runner import run_gates
from _lib.project_detector import detect_project


def main():
    """Entry point for PostToolUse hook."""
    # Read hook input from stdin (provided by Claude Code)
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # If we can't parse input, exit gracefully
        sys.exit(0)

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

    # Detect project type to determine which profile to use
    cwd = Path.cwd()
    project_info = detect_project(cwd)

    # Determine profile based on project type
    # FBR projects use specific rules; others use default
    # For now, default to "default" profile
    profile = "default"

    # Run gates on the edited file
    findings, statuses = run_gates(
        scope="files",
        files=[str(file_path)],
        project_root=cwd,
        profile=profile,
    )

    # Check if any gate was skipped due to missing dependencies
    skipped_gates = [g for g, status in statuses.items() if status == "skipped"]
    if skipped_gates:
        # Dependencies missing, exit gracefully
        # Don't block the user, just inform them
        sys.exit(0)

    # Filter for ERROR severity only (WARNING/HINT don't block)
    errors = [f for f in findings if f.severity == "ERROR"]

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
    reason_parts.append("Use `/gates-fix` to auto-fix common issues.")

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
