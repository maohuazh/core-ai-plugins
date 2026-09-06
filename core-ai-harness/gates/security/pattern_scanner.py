#!/usr/bin/env python3
"""
Security pattern scanner - regex-based security checks.

Detects common security anti-patterns in source files:
1. hardcoded-secret  - hardcoded passwords/keys/tokens (ERROR)
2. sql-injection     - string-concatenated SQL queries (ERROR)
3. empty-catch       - empty catch blocks that swallow exceptions (WARNING)

Output: normalized Finding JSON (same schema as gate_runner findings).
Can be invoked standalone or via gate_runner.

Usage:
    python3 pattern_scanner.py --files f1.java,f2.java [--json] [--project-root DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITY = {"hardcoded-secret": "ERROR", "sql-injection": "ERROR", "empty-catch": "WARNING"}

# Sensitive key names (case-insensitive word boundaries)
SECRET_KEY_RE = re.compile(
    r"\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?key|"
    r"private[_-]?key|auth[_-]?token|access[_-]?token|credential|"
    r"connection[_-]?string)\b",
    re.IGNORECASE,
)
# ... = "literal string value" (6+ chars)
SECRET_ASSIGN_RE = re.compile(
    r"""(?:=|:)\s*["'][A-Za-z0-9+/=._\-]{6,}["']"""
)

# SQL concatenation: a quoted segment containing SQL keywords followed by + variable
SQL_STRING_RE = re.compile(
    r"""["'](?=[^"']*\b(?:select|insert|update|delete|from|where)\b[^"']*)[^"']*["']\s*\+"""
)
# also catch "..." + variable used with sql/query words on the same line
SQL_INJECTION_LINE_RE = re.compile(
    r"""(?is)\b(?:select|insert|update|delete)\b[^\n;]{0,120}["']\s*\+\s*\w+"""
)

# Empty catch block: catch (...) { }
EMPTY_CATCH_RE = re.compile(
    r"""catch\s*\([^)]*\)\s*\{\s*\}"""
)


def scan_file(file_path: Path) -> list[dict]:
    """Scan a single file and return findings as dicts."""
    findings = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    lines = content.splitlines()

    # --- hardcoded secrets ---
    for line_no, line in enumerate(lines, start=1):
        if SECRET_KEY_RE.search(line) and SECRET_ASSIGN_RE.search(line):
            findings.append(_finding("hardcoded-secret", file_path, line_no, line))

    # --- SQL injection ---
    for line_no, line in enumerate(lines, start=1):
        if SQL_INJECTION_LINE_RE.search(line) or SQL_STRING_RE.search(line):
            findings.append(_finding("sql-injection", file_path, line_no, line))

    # --- empty catch ---
    for match in EMPTY_CATCH_RE.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        findings.append(_finding("empty-catch", file_path, line_no, ""))

    return findings


def _finding(rule_id: str, file_path: Path, line: int, text: str) -> dict:
    """Build a finding dict in the standard schema."""
    messages = {
        "hardcoded-secret": "Hardcoded secret detected. Use environment variables or a secret manager.",
        "sql-injection": "Potential SQL injection: query built by string concatenation. Use parameterized queries.",
        "empty-catch": "Empty catch block swallows the exception. Log or rethrow with context.",
    }
    col = None
    if text:
        match = re.search(r"[^ \t]", text)
        if match:
            col = match.start() + 1
    return {
        "rule_id": rule_id,
        "gate": "security",
        "file": str(file_path),
        "line": line,
        "col": col,
        "severity": SEVERITY.get(rule_id, "WARNING"),
        "message": messages.get(rule_id, ""),
        "fixable": False,
    }


def scan_files(file_paths: list[str], project_root: Path) -> list[dict]:
    """Scan multiple files, returning findings with paths relative to project_root."""
    all_findings = []
    for fp in file_paths:
        path = Path(fp)
        if not path.is_absolute():
            path = project_root / path
        for finding in scan_file(path):
            # Make file path relative to project root
            try:
                finding["file"] = str(path.relative_to(project_root))
            except ValueError:
                pass
            all_findings.append(finding)
    return all_findings


def main():
    parser = argparse.ArgumentParser(description="Security pattern scanner")
    parser.add_argument("--files", type=str, help="Comma-separated files to scan")
    parser.add_argument("--project-root", type=str, default=".", help="Project root")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    if not args.files:
        # Scan all Java files under project root
        files = [str(p) for p in project_root.rglob("*.java") if "build" not in p.parts]
    else:
        files = [f.strip() for f in args.files.split(",") if f.strip()]

    findings = scan_files(files, project_root)

    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        for f in findings:
            print(f"{f['file']}:{f['line']} {f['severity']} {f['rule_id']} {f['message']}")

    # Exit 1 if any ERROR
    if any(f["severity"] == "ERROR" for f in findings):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
