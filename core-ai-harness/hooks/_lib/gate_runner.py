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

# Sentinel value to distinguish "not checked" from "confirmed not found"
_AST_GREP_NOT_CHECKED = object()

# 模块级缓存：ast-grep 命令路径
_ast_grep_cmd_cache: str | object = _AST_GREP_NOT_CHECKED

if TYPE_CHECKING:
    from . import Finding

from . import GATES_DIR, Finding, debug_log
from .diff_parser import get_changed_file_paths
from .project_detector import ProjectInfo, detect_project
from .report_formatter import format_findings


# ============================================================================
# Config loading
# ============================================================================


def load_config(config_path: Path | None = None, project_root: Path | None = None) -> dict:
    """
    Load gate configuration from config.toml, merged with project-level overrides.

    Project-level overrides are loaded from .claude/gates.toml in the
    project_root directory (or CWD if not specified) and merged using deep merge.

    Args:
        config_path: Path to config.toml. Defaults to gates/config.toml.
        project_root: Project root directory. Defaults to CWD.

    Returns:
        Config dict.
    """
    if config_path is None:
        config_path = GATES_DIR / "config.toml"

    if project_root is None:
        project_root = Path.cwd()

    base_config = {}
    if config_path.exists():
        try:
            with open(config_path, "rb") as f:
                base_config = tomllib.load(f)
        except Exception as e:
            debug_log(f"Failed to load config: {e}")
            return {}

    # Merge with project-level overrides from .claude/gates.toml
    try:
        from .rule_loader import load_project_overrides, merge_config_with_overrides
        project_overrides = load_project_overrides(project_root)
        if project_overrides:
            debug_log(f"Merged project overrides: {list(project_overrides.keys())}")
            return merge_config_with_overrides(base_config, project_overrides)
    except Exception as e:
        debug_log(f"Failed to load/merge project overrides: {e}")

    return base_config


def get_active_profile(config: dict) -> str:
    """
    Get the active profile from config.

    Supports both nested TOML table format:
        [profile]
        active = "fbr"
    and flat string format:
        profile = "fbr"

    Returns:
        Profile name, defaulting to "default".
    """
    profile_cfg = config.get("profile", "default")
    if isinstance(profile_cfg, dict):
        return profile_cfg.get("active", "default")
    if isinstance(profile_cfg, str) and profile_cfg:
        return profile_cfg
    return "default"


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
        # If profiles field is missing/empty, default to ["default"]
        profiles = gate_config.get("profiles", ["default"])

        # Only enable if:
        # 1. The current profile is explicitly in the profiles list, OR
        # 2. The profiles list is empty (backward compatibility)
        if profile in profiles or not profiles:
            if gate_config.get("enabled", True):
                enabled.append(gate_name)

    return enabled


def filter_excluded_files(
    files: list[str], config: dict
) -> list[str]:
    """
    Filter out files matching the [exclude].paths globs from config.

    Args:
        files: List of file paths (relative to project root).
        config: Config dict from load_config().

    Returns:
        Filtered list.
    """
    exclude_patterns = config.get("exclude", {}).get("paths", [])
    if not exclude_patterns:
        return files

    import fnmatch

    filtered = []
    for f in files:
        norm = f.replace("\\", "/")
        excluded = any(fnmatch.fnmatch(norm, pat) for pat in exclude_patterns)
        if not excluded:
            filtered.append(f)

    return filtered


def apply_severity_overrides(
    findings: list[Finding], config: dict
) -> list[Finding]:
    """
    Apply [severity] overrides from config to findings.

    Config format (both forms supported):
        [severity]
        # Form 1: TOML dotted key (parsed as nested structure)
        severity.ast-grep.no-while-loop = "WARNING"

        # Form 2: Quoted key (parsed as flat key)
        "ast-grep.no-while-loop" = "WARNING"

    Args:
        findings: List of Finding objects.
        config: Config dict from load_config().

    Returns:
        List of findings with severity overridden (OFF findings removed).
    """
    severity_cfg = config.get("severity", {})
    if not severity_cfg:
        return findings

    # Build lookup: (gate, rule_id) -> severity
    overrides = {}
    for key, value in severity_cfg.items():
        # Handle nested structure from TOML dotted keys
        # e.g., severity.ast-grep.no-while-loop becomes nested dict
        if isinstance(value, dict):
            # Nested: key is "severity", value is {"ast-grep": {"no-while-loop": "WARNING"}}
            for gate, rules in value.items():
                if isinstance(rules, dict):
                    for rule_id, sev in rules.items():
                        overrides[(gate, rule_id)] = str(sev).upper()
        else:
            # Flat: key is "severity.ast-grep.no-while-loop" or "ast-grep.no-while-loop"
            key_str = key.removeprefix("severity.")
            gate, _, rule_id = key_str.partition(".")
            if gate and rule_id:
                overrides[(gate, rule_id)] = str(value).upper()

    if not overrides:
        return findings

    result = []
    for f in findings:
        new_sev = overrides.get((f.gate, f.rule_id))
        if new_sev == "OFF":
            continue  # Rule disabled
        if new_sev in ("ERROR", "WARNING", "HINT"):
            # Create a new Finding object with overridden severity
            new_finding = Finding(
                rule_id=f.rule_id,
                gate=f.gate,
                file=f.file,
                line=f.line,
                col=f.col,
                severity=new_sev,
                message=f.message,
                fixable=f.fixable,
            )
            result.append(new_finding)
        else:
            result.append(f)

    return result


# ============================================================================
# Gate runners
# ============================================================================


def run_ast_grep(
    files: list[str],
    project_root: Path,
    config: dict,
    profile: str = "default",
) -> tuple[list[Finding], str]:
    """
    Run ast-grep on the given files.

    Args:
        files: List of file paths to scan.
        project_root: Project root directory.
        config: Gate config dict.
        profile: Config profile ("default" or "fbr"). Chooses the sgconfig:
            - default: fp + security rules (sgconfig.yml)
            - fbr: fp + security + shape rules (sgconfig-fbr.yml)

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

    # Choose sgconfig based on profile
    sgconfig_name = "sgconfig.yml" if profile != "fbr" else "sgconfig-fbr.yml"
    sgconfig_path = GATES_DIR / "ast-grep" / sgconfig_name
    rules_dir = GATES_DIR / "ast-grep" / "rules"

    if not sgconfig_path.exists():
        debug_log(f"{sgconfig_name} not found: {sgconfig_path}")
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


def run_security_scan(
    files: list[str],
    project_root: Path,
    config: dict,
) -> tuple[list[Finding], str]:
    """
    Run the security pattern scanner on the given files.

    Args:
        files: List of file paths to scan.
        project_root: Project root directory.
        config: Gate config dict (unused, kept for interface consistency).

    Returns:
        (findings, status) where status is "ok" or "error".
    """
    findings = []

    if not files:
        return findings, "ok"

    scanner = GATES_DIR / "security" / "pattern_scanner.py"
    if not scanner.exists():
        debug_log(f"pattern_scanner.py not found: {scanner}")
        return findings, "skipped"

    cmd = [
        sys.executable,
        str(scanner),
        "--files",
        ",".join(files),
        "--project-root",
        str(project_root),
        "--json",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        debug_log("security scan timed out")
        return findings, "error"
    except Exception as e:
        debug_log(f"security scan failed: {e}")
        return findings, "error"

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        debug_log(f"Failed to parse security scan output: {result.stdout[:200]}")
        return findings, "error"

    for item in data:
        try:
            finding = Finding.from_dict(item)
            finding.gate = "security"
            findings.append(finding)
        except Exception as e:
            debug_log(f"Failed to parse security finding: {e}")
            continue

    return findings, "ok"


def run_external_gate(
    gate_name: str,
    script_relpath: str,
    files: list[str],
    project_root: Path,
    extra_args: list[str] | None = None,
) -> tuple[list[Finding], str]:
    """
    Run an external FBR gate script (lint / error-prone / build).

    These gates are FBR-profile only and require binaries (JARs) that are
    deployed out-of-band by gate-install. If the script or its prerequisite
    JAR is missing, the gate is reported "skipped" (never an error).

    Args:
        gate_name: Gate name ("lint", "error-prone", "build") for status reporting.
        script_relpath: Path to the runner script, relative to GATES_DIR.
        files: Files to pass to the script (may be empty for build gate).
        project_root: Project root.
        extra_args: Extra CLI args before the file list.

    Returns:
        (findings, status) - status is "ok", "skipped", or "error".
        Findings parsed from the script's stdout in file:line: message form;
        unparseable output is not dropped - it is appended as a synthetic
        finding only when it clearly references a file.
    """
    findings = []

    script = GATES_DIR / script_relpath
    if not script.exists():
        debug_log(f"{gate_name} gate script not found: {script}")
        return findings, "skipped"

    # Check the gate is actually installed (JAR present for lint/error-prone;
    # gradlew wrapper for build)
    if gate_name in ("lint", "error-prone"):
        dist_dir = GATES_DIR / gate_name / ".dist"
        jar_files = list(dist_dir.glob("*.jar")) if dist_dir.exists() else []
        if not jar_files:
            debug_log(f"{gate_name} gate: no JAR deployed in {dist_dir}")
            return findings, "skipped"
    elif gate_name == "build":
        if not (project_root / "gradlew").exists():
            debug_log("build gate: no ./gradlew in project root")
            return findings, "skipped"

    cmd = [str(script)]
    if extra_args:
        cmd.extend(extra_args)
    cmd.extend(str(project_root / f) for f in files)

    debug_log(f"Running {gate_name} gate: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        debug_log(f"{gate_name} gate timed out")
        return findings, "error"
    except Exception as e:
        debug_log(f"{gate_name} gate failed: {e}")
        return findings, "error"

    # Exit 2 = prerequisites missing (script's own check)
    if result.returncode == 2:
        return findings, "skipped"

    # Parse output: try file:line: message form
    parsed = _parse_external_findings(result.stdout, project_root, gate_name)
    findings.extend(parsed)

    if result.returncode not in (0, 1):
        return findings, "error"

    return findings, "ok"


def _parse_external_findings(
    output: str, project_root: Path, gate_name: str
) -> list[Finding]:
    """
    Best-effort parse of external gate stdout into Findings.

    Recognized formats (per line):
        /abs/path.java:12: message
        /abs/path.java:12:5: message
        path.java: error: message
    Unrecognized lines are ignored (kept in logs via debug).
    """
    import re

    findings = []
    pattern = re.compile(r"^(.+?):(\d+)(?::(\d+))?:\s*(.*)$")

    for line in output.splitlines():
        line = line.rstrip()
        if not line.strip():
            continue

        m = pattern.match(line)
        if not m:
            continue

        file_str, line_str, col_str, message = m.groups()
        path = Path(file_str)
        if path.suffix != ".java":
            continue

        # Relative to project root if possible
        try:
            file_rel = str(path.relative_to(project_root))
        except ValueError:
            file_rel = str(path)

        findings.append(
            Finding(
                rule_id=f"{gate_name}:lint",
                gate=gate_name,
                file=file_rel,
                line=int(line_str),
                col=int(col_str) if col_str else None,
                severity="ERROR",
                message=message.strip(),
                fixable=False,
            )
        )

    return findings


def _find_ast_grep() -> str | None:
    """Find ast-grep executable with module-level caching.

    Uses a sentinel value to distinguish 'not yet checked' from 'confirmed not found',
    so that negative results are properly cached and we don't repeatedly spawn subprocesses.
    """
    global _ast_grep_cmd_cache

    # Check cache first - only return if we've actually checked before
    if _ast_grep_cmd_cache is not _AST_GREP_NOT_CHECKED:
        return _ast_grep_cmd_cache if isinstance(_ast_grep_cmd_cache, str) else None

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
                _ast_grep_cmd_cache = cmd
                return cmd
        except Exception:
            continue

    # Cache the negative result to avoid repeated subprocess calls
    _ast_grep_cmd_cache = None
    return None


# ============================================================================
# Main runner
# ============================================================================


def run_gates(
    scope: Literal["files", "changed", "all"],
    files: list[str] | None = None,
    project_root: Path | None = None,
    profile: str | None = None,
) -> tuple[list[Finding], dict[str, str]]:
    """
    Run all enabled gates.

    Args:
        scope: "files" (specific list), "changed" (git diff), or "all" (all Java files).
        files: List of files (required if scope="files").
        project_root: Project root directory. Defaults to CWD.
        profile: Config profile ("default" or "fbr"). Defaults to config's active profile.

    Returns:
        (findings, gate_statuses) where gate_statuses maps gate name to "ok"/"skipped"/"error".
    """
    if project_root is None:
        project_root = Path.cwd()

    config = load_config(project_root=project_root)

    # Resolve profile: explicit arg wins, else config's active profile
    if profile is None:
        profile = get_active_profile(config)

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

    # Apply [exclude].paths from config
    files_to_scan = filter_excluded_files(files_to_scan, config)

    debug_log(f"Files to scan (after excludes): {len(files_to_scan)}")

    all_findings = []
    gate_statuses = {}

    # Run ast-grep
    if "ast-grep" in enabled_gates:
        findings, status = run_ast_grep(files_to_scan, project_root, config, profile=profile)
        all_findings.extend(findings)
        gate_statuses["ast-grep"] = status

    # Run security scanner
    if "security" in enabled_gates:
        findings, status = run_security_scan(files_to_scan, project_root, config)
        all_findings.extend(findings)
        gate_statuses["security"] = status

    # Run FBR-specific gates (lint / error-prone): fbr profile + Gradle project only
    is_gradle = detect_project(project_root).build_tool == "gradle"
    if profile == "fbr" and is_gradle:
        if "lint" in enabled_gates:
            findings, status = run_external_gate(
                "lint", "lint/java-lint.sh", files_to_scan, project_root
            )
            all_findings.extend(findings)
            gate_statuses["lint"] = status

        if "error-prone" in enabled_gates:
            findings, status = run_external_gate(
                "error-prone", "error-prone/error-prone-scan.sh",
                files_to_scan, project_root,
            )
            all_findings.extend(findings)
            gate_statuses["error-prone"] = status

        if "build" in enabled_gates:
            findings, status = run_external_gate(
                "build", "build/gradle-run.sh", [], project_root,
                extra_args=["build"],
            )
            all_findings.extend(findings)
            gate_statuses["build"] = status

    # Apply [severity] overrides from config
    all_findings = apply_severity_overrides(all_findings, config)

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
