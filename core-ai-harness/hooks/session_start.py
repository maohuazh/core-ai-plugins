#!/usr/bin/env python3
"""
SessionStart hook - provides project context to Claude at session start.

Reads project configuration and provides a summary of:
- Project type and build tool
- Active profile (default vs fbr)
- Enabled gates and rules
- Quick start instructions

This helps Claude understand the project context and coding standards
before starting work.
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path so we can import _lib
sys.path.insert(0, str(Path(__file__).parent))

from _lib import PLUGIN_ROOT
from _lib.gate_runner import load_config, get_enabled_gates
from _lib.project_detector import detect_project
from _lib.rule_loader import get_rules_summary, load_rules_metadata


def main():
    """Entry point for SessionStart hook."""
    # Get current working directory (where Claude was started)
    cwd = Path.cwd()

    # Detect project type
    project_info = detect_project(cwd)

    # Load configuration
    config = load_config()

    # Get active profile (default to "default" if not specified)
    profile = config.get("profile", "default")

    # Get enabled gates for this profile
    enabled_gates = get_enabled_gates(config, profile)

    # Build context message
    context_parts = [
        "## Project Context",
        "",
        f"**Project Type:** {project_info.type}",
        f"**Build Tool:** {project_info.build_tool}",
        f"**Active Profile:** {profile}",
        "",
        "### Enabled Gates",
    ]

    if enabled_gates:
        for gate in enabled_gates:
            context_parts.append(f"- ✅ {gate}")
    else:
        context_parts.append("- ⚠️ No gates enabled for this profile")

    # Add rules summary
    rules = load_rules_metadata()
    context_parts.extend([
        "",
        "### Coding Standards",
        "",
        get_rules_summary(rules),
        "",
        "### Quick Start",
        "",
        "- Run `/gates` to manually check your code",
        "- Run `/gates-fix` to automatically fix gate violations",
        "- PostToolUse hook automatically checks Java files after editing",
    ])

    # Print context (will be injected into Claude's context)
    print("\n".join(context_parts))

    # Exit successfully (0 = no block)
    sys.exit(0)


if __name__ == "__main__":
    main()
