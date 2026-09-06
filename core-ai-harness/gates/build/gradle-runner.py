#!/usr/bin/env python3
"""
Gradle build adapter for agent and local execution.
Executes Gradle quietly, retains the lossless raw log in /tmp/fbr-gradle,
and projects a compact, high-signal diagnostic summary into context.
"""

import argparse
import datetime
import os
import pathlib
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple

LOG_DIR = pathlib.Path("/tmp/fbr-gradle")
MAX_COMPILER_ERRORS = 20
MAX_TEST_FAILURES = 10
MAX_STACK_FRAMES = 8
MAX_TOTAL_CHARS = 12000


def ensure_log_dir() -> pathlib.Path:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        return LOG_DIR
    except Exception:
        fallback = pathlib.Path(".gradle/agent-logs")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def parse_compiler_errors(raw_log: str) -> List[str]:
    errors = []
    lines = raw_log.splitlines()
    i = 0
    # Match standard javac error patterns: /path/File.java:12: error: message
    javac_pattern = re.compile(r'^([a-zA-Z0-9_\-./\\]+\.java):(\d+):(?:\s*(\d+):)?\s*error:\s*(.+)$')
    # Match Scala/Kotlin error patterns: [error] /path/File.scala:12:15: message or e: file:line:col
    alt_pattern = re.compile(r'^(?:\[error\]\s+|e:\s+)?([a-zA-Z0-9_\-./\\]+\.(?:java|kt|scala)):(\d+):(?:\s*(\d+):)?\s*(.+)$')

    while i < len(lines):
        line = lines[i]
        m = javac_pattern.match(line) or (alt_pattern.match(line) if "error" in line.lower() else None)
        if m:
            file_path, line_no, col_no, msg = m.groups()
            rel_path = file_path
            try:
                rel_path = os.path.relpath(file_path, os.getcwd())
            except Exception:
                pass
            loc = f"{rel_path}:{line_no}" + (f":{col_no}" if col_no else "")
            entry = [f"{loc} - {msg.strip()}"]
            # Look ahead for snippet and pointer
            j = i + 1
            while j < len(lines) and j <= i + 3:
                next_line = lines[j]
                if javac_pattern.match(next_line) or (alt_pattern.match(next_line) and "error" in next_line.lower()):
                    break
                if next_line.startswith("> Task :") or next_line.startswith("BUILD FAILED"):
                    break
                if next_line.strip().startswith("^") or (j == i + 1 and not next_line.startswith("[")):
                    entry.append("  " + next_line)
                j += 1
            errors.append("\n".join(entry))
            i = j - 1
        i += 1
    return errors


def parse_checkstyle_pmd_errors(raw_log: str, root_dir: pathlib.Path, start_time: float) -> List[str]:
    violations = []
    seen = set()

    # Determine which tools were involved in this run
    log_lower = raw_log.lower()
    has_checkstyle = "checkstyle" in log_lower
    has_pmd = "pmd" in log_lower
    has_spotbugs = "spotbugs" in log_lower

    # 1. Structured XML report parsing (Checkstyle)
    if has_checkstyle:
        for xml_path in root_dir.glob("**/reports/checkstyle/*.xml"):
            try:
                if xml_path.stat().st_mtime >= (start_time - 1.0):
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
                    for file_node in root.findall("file"):
                        fname = file_node.get("name", "")
                        try:
                            rel = os.path.relpath(fname, os.getcwd())
                        except Exception:
                            rel = fname
                        for err in file_node.findall("error"):
                            line = err.get("line", "")
                            col = err.get("column", "")
                            msg = err.get("message", "")
                            src = err.get("source", "")
                            rule = src.split(".")[-1].removesuffix("Check") if src else "Checkstyle"
                            loc = f"{rel}:{line}" + (f":{col}" if col else "")
                            item = f"{loc} - [Checkstyle:{rule}] {msg}"
                            if item not in seen:
                                seen.add(item)
                                violations.append(item)
            except Exception:
                continue

    # 2. Structured XML report parsing (PMD)
    if has_pmd:
        for xml_path in root_dir.glob("**/reports/pmd/*.xml"):
            try:
                if xml_path.stat().st_mtime >= (start_time - 1.0):
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
                    for node in root.iter():
                        if node.tag.endswith("file") and "name" in node.attrib:
                            fname = node.attrib["name"]
                            try:
                                rel = os.path.relpath(fname, os.getcwd())
                            except Exception:
                                rel = fname
                            for v in node:
                                if v.tag.endswith("violation"):
                                    line = v.get("beginline", "")
                                    col = v.get("begincolumn", "")
                                    rule = v.get("rule", "PMD")
                                    msg = (v.text or "").strip()
                                    loc = f"{rel}:{line}" + (f":{col}" if col else "")
                                    item = f"{loc} - [PMD:{rule}] {msg}"
                                    if item not in seen:
                                        seen.add(item)
                                        violations.append(item)
            except Exception:
                continue

    # If XML reports already found, return them
    if violations:
        return violations

    # 3. Fallback: Console parsing
    # Checkstyle format: [ERROR] /path/to/File.java:line:col: message [RuleName]
    cs_pattern = re.compile(r'\[ERROR\]\s+([a-zA-Z0-9_\-./\\]+\.java):(\d+):(?:\s*(\d+):)?\s*(.+?)(?:\s*\[([a-zA-Z0-9_]+)\])?$')
    # PMD format: /path/to/File.java:line:\tRuleName:\tMessage
    pmd_pattern = re.compile(r'^([a-zA-Z0-9_\-./\\]+\.java):(\d+):\s*([a-zA-Z0-9_]+):\s*(.+)$')
    # SpotBugs format: [M B DLS] Dead store to ... in ...
    spotbugs_pattern = re.compile(r'^[HMLEB]\s+([A-Z0-9_]+)\s+([A-Z0-9_]+):\s+(.+)$')

    for line in raw_log.splitlines():
        m_cs = cs_pattern.search(line)
        if m_cs:
            file_path, line_no, col_no, msg, rule = m_cs.groups()
            try:
                file_path = os.path.relpath(file_path, os.getcwd())
            except Exception:
                pass
            loc = f"{file_path}:{line_no}" + (f":{col_no}" if col_no else "")
            rule_tag = f"[Checkstyle:{rule}] " if rule else "[Checkstyle] "
            item = f"{loc} - {rule_tag}{msg.strip()}"
            if item not in seen:
                seen.add(item)
                violations.append(item)
            continue

        m_pmd = pmd_pattern.match(line.strip())
        if m_pmd:
            file_path, line_no, rule, msg = m_pmd.groups()
            try:
                file_path = os.path.relpath(file_path, os.getcwd())
            except Exception:
                pass
            item = f"{file_path}:{line_no} - [PMD:{rule}] {msg.strip()}"
            if item not in seen:
                seen.add(item)
                violations.append(item)
            continue

        m_sb = spotbugs_pattern.match(line.strip())
        if m_sb:
            cat, code, msg = m_sb.groups()
            item = f"SpotBugs [{cat}/{code}] {msg.strip()}"
            if item not in seen:
                seen.add(item)
                violations.append(item)

    return violations


def parse_junit_xml_results(search_dir: pathlib.Path, start_time: float) -> List[Dict[str, str]]:
    failed_tests = []
    # Find all test XML files under build directories
    test_result_files = []
    for xml_path in search_dir.glob("**/test-results/**/*.xml"):
        try:
            if xml_path.stat().st_mtime >= (start_time - 5.0):
                test_result_files.append(xml_path)
        except Exception:
            continue

    for xml_file in test_result_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            # Standard JUnit XML: <testsuite> -> <testcase> -> <failure> or <error>
            for testcase in root.iter("testcase"):
                classname = testcase.get("classname", "")
                name = testcase.get("name", "")
                failure = testcase.find("failure")
                if failure is None:
                    failure = testcase.find("error")
                if failure is not None:
                    msg = failure.get("message", "")
                    failure_type = failure.get("type", "")
                    body = (failure.text or "").strip()
                    stack_lines = [l.strip() for l in body.splitlines() if l.strip()]
                    trimmed_stack = stack_lines[:MAX_STACK_FRAMES]

                    failed_tests.append({
                        "class": classname,
                        "method": name,
                        "type": failure_type,
                        "message": msg or (trimmed_stack[0] if trimmed_stack else "Assertion/Test failure"),
                        "stack": trimmed_stack
                    })
        except Exception:
            continue
    return failed_tests


def parse_log_test_failures(raw_log: str) -> List[str]:
    # Fallback if JUnit XML was not generated / found
    failures = []
    lines = raw_log.splitlines()
    for i, line in enumerate(lines):
        clean_line = line.strip()
        if clean_line.startswith("> Task :") or clean_line.startswith("FAILURE:") or clean_line.startswith("*"):
            continue
        if " FAILED" in clean_line and ">" in clean_line:
            snippet = [clean_line]
            for j in range(i + 1, min(i + 6, len(lines))):
                next_l = lines[j].strip()
                if next_l.startswith("> Task :") or " FAILED" in next_l or next_l.startswith("BUILD ") or next_l.startswith("*"):
                    break
                snippet.append("  " + next_l)
            failures.append("\n".join(snippet))
    return failures


def parse_gradle_failure_summary(raw_log: str) -> str:
    lines = raw_log.splitlines()
    summary_lines = []
    capture = False

    for line in lines:
        if line.startswith("* What went wrong:"):
            capture = True
            summary_lines.append(line)
            continue
        if capture:
            if line.startswith("* Try:") or line.startswith("* Exception is:") or line.startswith("BUILD FAILED"):
                break
            summary_lines.append(line)

    if not summary_lines:
        # Fallback: scan for specific failure messages or error lines
        for line in lines:
            if any(marker in line for marker in [
                "Unknown command-line option",
                "Cannot locate tasks",
                "Execution failed for task",
                "Caused by:",
                "Task not found",
                "Project not found",
                "FAILURE: Build failed"
            ]):
                summary_lines.append(line.strip())

    return "\n".join(summary_lines).strip()


def run_gradle(args: List[str], raw_mode: bool = False, max_errors: int = MAX_COMPILER_ERRORS, max_tests: int = MAX_TEST_FAILURES) -> int:
    root_dir = pathlib.Path.cwd()
    gradlew = root_dir / "gradlew"
    if not gradlew.exists():
        sys.stderr.write("Error: ./gradlew not found in current directory.\n")
        return 1

    # Base Gradle command arguments
    # Avoid adding duplicates if already supplied
    cmd = [str(gradlew)]
    extra_flags = ["--console=plain", "--warning-mode=none"]
    for flag in extra_flags:
        if flag not in args:
            cmd.append(flag)

    cmd.extend(args)

    if raw_mode:
        res = subprocess.run(cmd)
        return res.returncode

    log_dir = ensure_log_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    target_slug = "_".join(a.replace(":", "_").replace("/", "_") for a in args if not a.startswith("-"))[:30] or "task"
    log_file = log_dir / f"build-{timestamp}-{target_slug}.log"

    start_time = time.time()
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    stdout_output, _ = process.communicate()
    elapsed = time.time() - start_time
    exit_code = process.returncode

    # Always write complete raw output to log file
    try:
        log_file.write_text(stdout_output, encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write log file {log_file}: {e}\n")

    if exit_code == 0:
        print(f"BUILD SUCCESSFUL [{', '.join(args)} in {elapsed:.1f}s]")
        print(f"Log: {log_file}")
        return 0

    # Build Failed -> Format high-signal diagnostic summary
    output_sections = []
    output_sections.append(f"BUILD FAILED [{', '.join(args)} in {elapsed:.1f}s]")

    # 1. Compiler diagnostics
    compiler_errors = parse_compiler_errors(stdout_output)
    if compiler_errors:
        total = len(compiler_errors)
        shown = compiler_errors[:max_errors]
        section = [f"=== Compiler Errors ({total}) ==="]
        section.extend(shown)
        if total > max_errors:
            section.append(f"... [{total - max_errors} additional compiler errors omitted]")
        output_sections.append("\n".join(section))

    # 2. Checkstyle / PMD / Lint diagnostics
    lint_errors = parse_checkstyle_pmd_errors(stdout_output, root_dir, start_time)
    if lint_errors:
        total = len(lint_errors)
        shown = lint_errors[:max_errors]
        section = [f"=== Checkstyle / Linter Violations ({total}) ==="]
        section.extend(shown)
        if total > max_errors:
            section.append(f"... [{total - max_errors} additional violations omitted]")
        output_sections.append("\n".join(section))

    # 3. Test failures
    junit_failures = parse_junit_xml_results(root_dir, start_time)
    if junit_failures:
        total = len(junit_failures)
        shown = junit_failures[:max_tests]
        section = [f"=== Failed Tests ({total}) ==="]
        for f in shown:
            item = [
                f"FAIL: {f['class']} > {f['method']}",
                f"  Reason: {f['message']}"
            ]
            if f["stack"]:
                item.append("  Stacktrace:")
                for frame in f["stack"]:
                    item.append(f"    at {frame}")
            section.append("\n".join(item))
        if total > max_tests:
            section.append(f"... [{total - max_tests} additional failed tests omitted]")
        output_sections.append("\n".join(section))
    else:
        log_test_failures = parse_log_test_failures(stdout_output)
        if log_test_failures:
            total = len(log_test_failures)
            shown = log_test_failures[:max_tests]
            section = [f"=== Failed Tests ({total}) ==="]
            section.extend(shown)
            if total > max_tests:
                section.append(f"... [{total - max_tests} additional failed tests omitted]")
            output_sections.append("\n".join(section))

    # 4. Gradle root cause summary
    gradle_summary = parse_gradle_failure_summary(stdout_output)
    if gradle_summary:
        output_sections.append(f"=== Gradle Failure ===\n{gradle_summary}")

    output_sections.append(f"Full log: {log_file}")

    result_text = "\n\n".join(output_sections)
    if len(result_text) > MAX_TOTAL_CHARS:
        result_text = result_text[:MAX_TOTAL_CHARS] + f"\n\n... [Output truncated to {MAX_TOTAL_CHARS} chars. Full log: {log_file}]"

    print(result_text)
    return exit_code


def main():
    parser = argparse.ArgumentParser(
        description="Lossless Gradle runner with concise diagnostic projection for agents and humans.",
        add_help=False
    )
    parser.add_argument("--raw", action="store_true", help="Pass through raw Gradle output directly.")
    parser.add_argument("--max-errors", type=int, default=MAX_COMPILER_ERRORS, help="Max compiler errors to display.")
    parser.add_argument("--max-tests", type=int, default=MAX_TEST_FAILURES, help="Max test failures to display.")

    known_args, gradle_args = parser.parse_known_args()

    if not gradle_args and not known_args.raw:
        # Default task if none supplied
        gradle_args = ["build"]

    exit_code = run_gradle(
        args=gradle_args,
        raw_mode=known_args.raw,
        max_errors=known_args.max_errors,
        max_tests=known_args.max_tests
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
