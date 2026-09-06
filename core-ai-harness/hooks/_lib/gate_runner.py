"""
Gate runner - unified gate execution engine.

This is the single entry point for running gates. It:
- Reads config.toml to determine which gates are enabled
- Calls individual gate runners (ast-grep, etc.)
- Normalizes output to Finding structures
- Provides a CLI interface for hooks/skills/commands
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from . import Finding

from . import GATES_DIR, Finding, debug_log
from .diff_parser import get_changed_file_paths
from .project_detector import ProjectInfo, detect_project
from .report_formatter import format_findings


# ============================================================================
# Config loading
# ============================================================================


def load_config(config_path: Path | None = None) -> dict:
    """
    Load gate configuration from config.toml.

    Args:
        config_path: Path to config.toml. Defaults to gates/config.toml.

    Returns:
        Config dict.
    """
    if config_path is None:
        config_path = GATES_DIR / "config.toml"

    if not config_path.exists():
        debug_log(f"Config not found: {config_path}")
        return {}

    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        debug_log(f"Failed to load config: {e}")
        return {}


def get_enabled_gates(config: dict, profile: str = "default") -> list[str]:
    """
    Get list of enabled gates from config.

    Args:
        config: Config dict from load_config().
        profile: Profile name ("default" or "fbr").

    Returns:
        List of gate names.
    """
    gates = config.get("gates", {})
    enabled = []

    for gate_name, gate_config in gates.items():
        if not isinstance(gate_config, dict):
            continue

        # Check if gate is enabled in this profile
        profiles = gate_config.get("profiles", ["default"])
        if profile in profiles or "default" in profiles:
            if gate_config.get("enabled", True):
                enabled.append(gate_name)

    return enabled


# ============================================================================
# Gate runners
# ============================================================================


def run_ast_grep(
    files: list[str],
    project_root: Path,
    config: dict,
) -> tuple[list[Finding], str]:
    """
    Run ast-grep on the given files.

    Args:
        files: List of file paths to scan.
        project_root: Project root directory.
        config: Gate config dict.

    Returns:
        (findings, status) where status is "ok", "skipped", or "error".
    """
    findings = []

    if not files:
        return findings, "ok"

    # Check if ast-grep is available
    ast_grep_cmd = _find_ast_grep()
    if not ast_grep_cmd:
        debug_log("ast-grep not found")
        return findings, "skipped"

    # Build command
    sgconfig_path = GATES_DIR / "ast-grep" / "sgconfig.yml"
    rules_dir = GATES_DIR / "ast-grep" / "rules"

    if not sgconfig_path.exists():
        debug_log(f"sgconfig.yml not found: {sgconfig_path}")
        return findings, "skipped"

    # Use --json output for parsing
    cmd = [
        ast_grep_cmd,
        "scan",
        "--config",
        str(sgconfig_path),
        "--json",
    ]

    # Add files to scan (relative to project root)
    for f in files:
        cmd.append(str(project_root / f))

    debug_log(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        debug_log("ast-grep timed out")
        return findings, "error"
    except Exception as e:
        debug_log(f"ast-grep failed: {e}")
        return findings, "error"

    # Parse JSON output
    # ast-grep exit codes: 0 = no issues, 1 = issues found (not an error)
    if result.returncode not in (0, 1):
        debug_log(f"ast-grep exited with {result.returncode}: {result.stderr}")
        return findings, "error"

    try:
        # ast-grep --json outputs an array of matches
        # Format: {text, range, file, language, ruleId, severity, message, ...}
        matches = json.loads(result.stdout)
    except json.JSONDecodeError:
        debug_log(f"Failed to parse ast-grep output: {result.stdout[:200]}")
        return findings, "error"

    # Convert to Finding objects
    for match in matches:
        try:
            # ast-grep JSON format
            rule_id = match.get("ruleId", "unknown")
            file_path = match.get("file", "")
            line = match.get("range", {}).get("start", {}).get("line", 0) + 1
            col = match.get("range", {}).get("start", {}).get("column", 0) + 1

            # Convert to relative path
            try:
                file_path = str(Path(file_path).relative_to(project_root))
            except ValueError:
                pass

            # Severity is in the match (lowercase: "error", "warning")
            severity_raw = match.get("severity", "error")
            severity = severity_raw.upper() if severity_raw else "ERROR"

            message = match.get("message", "")
            if not message:
                message = f"Rule {rule_id} violated"

            # Take first line of message for brevity
            message = message.split("\n")[0] if message else ""

            finding = Finding(
                rule_id=rule_id,
                gate="ast-grep",
                file=file_path,
                line=line,
                col=col,
                severity=severity,
                message=message,
                fixable=False,  # ast-grep doesn't tell us this in JSON
            )
            findings.append(finding)
        except Exception as e:
            debug_log(f"Failed to parse match: {e}")
            continue

    return findings, "ok"


def _find_ast_grep() -> str | None:
    """Find ast-grep executable."""
    # Prefer 'ast-grep' over deprecated 'sg'
    for cmd in ["ast-grep", "sg"]:
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                debug_log(f"Found {cmd}: {result.stdout.strip()}")
                return cmd
        except Exception:
            continue

    return None


# ============================================================================
# Main runner
# ============================================================================


def run_gates(
    scope: Literal["files", "changed", "all"],
    files: list[str] | None = None,
    project_root: Path | None = None,
    profile: str = "default",
) -> tuple[list[Finding], dict[str, str]]:
    """
    Run all enabled gates.

    Args:
        scope: "files" (specific list), "changed" (git diff), or "all" (all Java files).
        files: List of files (required if scope="files").
        project_root: Project root directory. Defaults to CWD.
        profile: Config profile ("default" or "fbr").

    Returns:
        (findings, gate_statuses) where gate_statuses maps gate name to "ok"/"skipped"/"error".
    """
    if project_root is None:
        project_root = Path.cwd()

    config = load_config()
    enabled_gates = get_enabled_gates(config, profile)

    debug_log(f"Enabled gates: {enabled_gates}")
    debug_log(f"Scope: {scope}, Profile: {profile}")

    # Determine files to scan
    if scope == "files":
        if not files:
            return [], {}
        files_to_scan = files
    elif scope == "changed":
        files_to_scan = get_changed_file_paths(project_root, mode="unstaged")
        # Filter to Java files only
        files_to_scan = [f for f in files_to_scan if f.endswith(".java")]
    elif scope == "all":
        # Find all Java files in project
        files_to_scan = [
            str(p.relative_to(project_root))
            for p in project_root.rglob("*.java")
            if "build" not in p.parts and "target" not in p.parts
        ]
    else:
        return [], {}

    debug_log(f"Files to scan: {len(files_to_scan)}")

    all_findings = []
    gate_statuses = {}

    # Run ast-grep
    if "ast-grep" in enabled_gates:
        findings, status = run_ast_grep(files_to_scan, project_root, config)
        all_findings.extend(findings)
        gate_statuses["ast-grep"] = status

    return all_findings, gate_statuses


# ============================================================================
# CLI
# ============================================================================


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Core AI Harness - Gate Runner")
    parser.add_argument(
        "--scope",
        choices=["files", "changed", "all"],
        default="changed",
        help="Scope of files to scan",
    )
    parser.add_argument(
        "--files",
        type=str,
        help="Comma-separated list of files (for scope=files)",
    )
    parser.add_argument(
        "--profile",
        default="default",
        help="Config profile (default or fbr)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings as JSON",
    )
    parser.add_argument(
        "--project-root",
        type=str,
        help="Project root directory (default: CWD)",
    )

    args = parser.parse_args()

    # Parse files argument
    files = None
    if args.files:
        files = [f.strip() for f in args.files.split(",")]

    project_root = Path(args.project_root) if args.project_root else None

    # Run gates
    findings, gate_statuses = run_gates(
        scope=args.scope,
        files=files,
        project_root=project_root,
        profile=args.profile,
    )

    # Output results
    if args.json:
        output = {
            "findings": [f.to_dict() for f in findings],
            "gate_statuses": gate_statuses,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        from .report_formatter import print_findings

        print_findings(findings, output_format="terminal")

        # Print gate statuses
        print("\nGate statuses:")
        for gate, status in gate_statuses.items():
            print(f"  {gate}: {status}")

    # Exit code: 1 if any ERROR findings, 0 otherwise
    if any(f.severity == "ERROR" for f in findings):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
