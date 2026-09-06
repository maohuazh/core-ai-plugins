---
name: gate-scanner
description: "Run gate checks on Java files to detect FP violations and other code quality issues"
---

# Gate Scanner

Scans Java files using configured gates (AST-Grep, security patterns) to find violations of coding standards.

## Usage

```
/gate-scanner [file1.java] [file2.java] ...
```

If no files specified, scans all changed Java files in the working directory.

## What it does

1. Detects project type (Java/Gradle, Java/Maven, Node, Python)
2. Loads appropriate gate configuration
3. Runs enabled gates on the specified files
4. Reports findings grouped by severity (ERROR, WARNING, HINT)
5. Returns exit code 1 if any ERRORs found, 0 otherwise

## Example

```bash
# Scan specific files
/gate-scanner src/main/java/com/example/Service.java

# Scan multiple files
/gate-scanner src/main/java/com/example/Service.java src/main/java/com/example/Controller.java

# Scan all changed files (default)
/gate-scanner
```

## Output Format

```
Found 3 issues: 2 ERROR, 1 WARNING

src/main/java/com/example/Service.java
  🔴 ERROR line 15 no-traditional-for-loop
    Traditional for-loop detected. Use Stream API instead.
  🔴 ERROR line 23 no-parameter-mutation
    Parameter mutation detected. Parameters should be final.
  🟡 WARNING line 34 no-mutable-accumulator
    Mutable accumulator pattern. Consider using Stream.reduce() or collect().
```

## Integration

This skill is used by the PostToolUse hook to automatically check files after editing.
