"""
Core AI Harness - shared library for hooks and skills.

This package provides the infrastructure for the core-ai-harness plugin:
- Path resolution (plugin root, gates dir, etc.)
- Standard Finding structure for gate results
- Common utilities for hooks
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal, Optional


# ============================================================================
# Path resolution (using __file__, NOT ${CLAUDE_PLUGIN_ROOT})
# ============================================================================

# Plugin root: core-ai-harness/
PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent

# Gates directory: core-ai-harness/gates/
GATES_DIR = PLUGIN_ROOT / "gates"

# Rules directory: core-ai-harness/rules/
RULES_DIR = PLUGIN_ROOT / "rules"

# Hooks directory: core-ai-harness/hooks/
HOOKS_DIR = PLUGIN_ROOT / "hooks"

# This library directory: core-ai-harness/hooks/_lib/
LIB_DIR = PLUGIN_ROOT / "hooks" / "_lib"


# ============================================================================
# Finding structure (D4: standard gate result)
# ============================================================================

Severity = Literal["ERROR", "WARNING", "HINT"]


class Finding:
    """
    Standard gate finding structure.

    All runners must normalize their output to this structure.
    """

    def __init__(
        self,
        rule_id: str,
        gate: str,
        file: str,
        line: int,
        col: Optional[int] = None,
        severity: Severity = "ERROR",
        message: str = "",
        fixable: bool = False,
    ):
        self.rule_id = rule_id
        self.gate = gate
        self.file = file
        self.line = line
        self.col = col
        self.severity = severity
        self.message = message
        self.fixable = fixable

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        result = {
            "rule_id": self.rule_id,
            "gate": self.gate,
            "file": self.file,
            "line": self.line,
            "col": self.col,
            "severity": self.severity,
            "message": self.message,
            "fixable": self.fixable,
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Finding:
        """Create Finding from dict."""
        return cls(
            rule_id=data["rule_id"],
            gate=data["gate"],
            file=data["file"],
            line=data["line"],
            col=data.get("col"),
            severity=data.get("severity", "ERROR"),
            message=data.get("message", ""),
            fixable=data.get("fixable", False),
        )

    def __repr__(self) -> str:
        return (
            f"Finding(rule_id={self.rule_id!r}, gate={self.gate!r}, "
            f"file={self.file!r}, line={self.line}, severity={self.severity!r})"
        )


# ============================================================================
# Environment detection
# ============================================================================


def is_java_file(file_path: str | Path) -> bool:
    """Check if file is a Java source file."""
    return Path(file_path).suffix == ".java"


def get_env_var(name: str, default: str = "") -> str:
    """Get environment variable with default."""
    return os.environ.get(name, default)


# ============================================================================
# Debug logging (stderr, only when debug mode is on)
# ============================================================================


def debug_log(msg: str) -> None:
    """Log debug message to stderr (only when DEBUG=1)."""
    if os.environ.get("DEBUG"):
        print(f"[core-ai-harness:debug] {msg}", file=sys.stderr)
