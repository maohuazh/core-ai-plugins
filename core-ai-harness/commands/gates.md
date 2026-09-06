---
description: "Run all enabled gates on the codebase"
---

# Gates Command

Run all enabled gates on your codebase to check for violations.

## Usage

```
/gates [options]

Options:
  --scope <scope>    Scope of files to check: changed, all, staged (default: changed)
  --profile <name>   Profile to use: default, fbr (default: default)
  --json             Output results in JSON format
  --quiet            Only show summary, no detailed findings
```

## Examples

Check all changed files:
```
/gates
```

Check all Java files in the project:
```
/gates --scope all
```

Check staged files only:
```
/gates --scope staged
```

Use FBR profile:
```
/gates --profile fbr
```

Get JSON output for integration:
```
/gates --json > results.json
```

## What it does

1. Detects project type (Java/Gradle, Java/Maven, Node, Python)
2. Loads enabled gates from config
3. Runs each gate on the specified files
4. Collects findings and displays results
5. Exits with code 1 if any ERROR findings, 0 otherwise

## Exit Codes

- 0: Success (no errors found)
- 1: Errors found
- 2: Gate execution failed

## Integration

This command is a wrapper around `hooks/_lib/gate_runner.py`.
