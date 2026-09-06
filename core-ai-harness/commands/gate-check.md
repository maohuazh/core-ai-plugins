---
description: "Check specific files with gates"
---

# Gate Check Command

Run gates on specific files to check for violations.

## Usage

```
/gate-check <file1> [file2] [file3] ...
```

## Examples

Check a single file:
```
/gate-check src/main/java/com/example/UserService.java
```

Check multiple files:
```
/gate-check file1.java file2.java file3.java
```

Check all Java files in a directory:
```
/gate-check src/main/java/**/*.java
```

## What it does

1. Validates that specified files exist and are Java files
2. Runs all enabled gates on the specified files
3. Displays findings grouped by severity
4. Exits with code 1 if any ERROR findings, 0 otherwise

## Output Format

```
Gate Check Results: src/main/java/com/example/UserService.java

ERRORS:
  Line 45: no-traditional-for-loop
    Traditional for-loop detected. Use Stream API instead.

WARNINGS:
  Line 78: no-mutable-accumulator
    Mutable accumulator pattern. Consider using Stream.reduce() or collect().

Summary: 1 error, 1 warning
```

## Integration

This command uses the same gate runner as the PostToolUse hook.
