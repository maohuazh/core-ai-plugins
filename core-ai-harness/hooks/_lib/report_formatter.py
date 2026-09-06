"""
Report formatter.

Formats Finding objects into terminal-colored output, Markdown, or JSON.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from . import Finding

OutputFormat = Literal["terminal", "markdown", "json"]


def format_findings(
    findings: list[Finding],
    output_format: OutputFormat = "terminal",
    title: str = "Gate Scan Results",
) -> str:
    """
    Format a list of findings into the specified output format.

    Args:
        findings: List of Finding objects.
        output_format: "terminal" (colored), "markdown", or "json".
        title: Title for the report (used in terminal/markdown).

    Returns:
        Formatted string.
    """
    if output_format == "json":
        return _format_json(findings)
    elif output_format == "markdown":
        return _format_markdown(findings, title)
    else:
        return _format_terminal(findings, title)


def _format_json(findings: list[Finding]) -> str:
    """Format findings as JSON array."""
    data = [f.to_dict() for f in findings]
    return json.dumps(data, indent=2, ensure_ascii=False)


def _format_markdown(findings: list[Finding], title: str) -> str:
    """Format findings as Markdown table."""
    if not findings:
        return f"## {title}\n\n✅ No issues found."

    lines = [
        f"## {title}",
        "",
        f"**Total:** {len(findings)} issues",
        "",
    ]

    # Group by severity
    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    hints = [f for f in findings if f.severity == "HINT"]

    if errors:
        lines.append(f"- 🔴 **ERROR:** {len(errors)}")
    if warnings:
        lines.append(f"- 🟡 **WARNING:** {len(warnings)}")
    if hints:
        lines.append(f"- 🔵 **HINT:** {len(hints)}")

    lines.append("")
    lines.append("| Severity | File | Line | Rule | Message |")
    lines.append("|----------|------|------|------|---------|")

    for f in findings:
        severity_icon = {"ERROR": "🔴", "WARNING": "🟡", "HINT": "🔵"}.get(f.severity, "•")
        message = f.message.replace("|", "\\|").replace("\n", " ")
        if len(message) > 80:
            message = message[:77] + "..."
        lines.append(f"| {severity_icon} {f.severity} | `{f.file}` | {f.line} | `{f.rule_id}` | {message} |")

    return "\n".join(lines)


def _format_terminal(findings: list[Finding], title: str) -> str:
    """Format findings with terminal colors."""
    if not findings:
        return f"{title}: ✅ No issues found."

    lines = [f"\n{'=' * 60}", f"{title}", f"{'=' * 60}"]

    # Summary
    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    hints = [f for f in findings if f.severity == "HINT"]

    summary_parts = []
    if errors:
        summary_parts.append(f"\033[31m{len(errors)} ERROR\033[0m")
    if warnings:
        summary_parts.append(f"\033[33m{len(warnings)} WARNING\033[0m")
    if hints:
        summary_parts.append(f"\033[34m{len(hints)} HINT\033[0m")

    lines.append(f"Found {len(findings)} issues: {', '.join(summary_parts)}")
    lines.append("")

    # Group by file
    by_file: dict[str, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    for file_path, file_findings in by_file.items():
        lines.append(f"\033[1m{file_path}\033[0m")

        # Sort by line number
        file_findings.sort(key=lambda f: f.line)

        for f in file_findings:
            severity_color = {"ERROR": "31", "WARNING": "33", "HINT": "34"}.get(f.severity, "0")
            fixable_marker = " [fixable]" if f.fixable else ""
            col_str = f":{f.col}" if f.col else ""

            lines.append(
                f"  \033[{severity_color}m{f.severity}\033[0m "
                f"line {f.line}{col_str} "
                f"\033[2m{f.rule_id}\033[0m{fixable_marker}"
            )

            if f.message:
                # Indent message
                msg_lines = f.message.split("\n")
                for msg_line in msg_lines[:3]:  # Limit to 3 lines
                    lines.append(f"    {msg_line}")

    lines.append("")
    return "\n".join(lines)


def print_findings(
    findings: list[Finding],
    output_format: OutputFormat = "terminal",
    title: str = "Gate Scan Results",
) -> None:
    """Print formatted findings to stdout."""
    print(format_findings(findings, output_format, title))


def count_by_severity(findings: list[Finding]) -> dict[str, int]:
    """Count findings by severity level."""
    return {
        "ERROR": len([f for f in findings if f.severity == "ERROR"]),
        "WARNING": len([f for f in findings if f.severity == "WARNING"]),
        "HINT": len([f for f in findings if f.severity == "HINT"]),
    }


def has_errors(findings: list[Finding]) -> bool:
    """Check if any findings have ERROR severity."""
    return any(f.severity == "ERROR" for f in findings)


def has_warnings(findings: list[Finding]) -> bool:
    """Check if any findings have WARNING severity."""
    return any(f.severity == "WARNING" for f in findings)
