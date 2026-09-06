---
name: gate-report
description: "Generate a comprehensive gate compliance report for a project or set of files"
---

# Gate Report

Generates a comprehensive compliance report based on gate scan results.

## Usage

```
/gate-report [--scope changed|all|files] [--output terminal|markdown|json] [--file <path>]
```

If no options given, reports on all changed Java files in terminal format.

## Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--scope` | `changed`, `all`, `files` | `changed` | Scope of files to report on |
| `--output` | `terminal`, `markdown`, `json` | `terminal` | Output format |
| `--file` | path | — | Single file (with `--scope files`) |
| `--profile` | `default`, `fbr` | `default` | Config profile |

## Report Structure

```markdown
# Gate Compliance Report

## Summary
- Scanned: 12 files
- ERROR: 3 (2 fixed since last scan)
- WARNING: 5
- HINT: 4
- Gates run: ast-grep ✅, security ⏭ (not installed)

## Violations by Rule
| Rule | Severity | Count | Files |
|------|----------|-------|-------|
| no-traditional-for-loop | ERROR | 2 | Service.java, Controller.java |

## Violations by File
### src/main/java/com/example/Service.java
- 🔴 line 15: no-traditional-for-loop — Use Stream API
- 🟡 line 23: no-mutable-accumulator — Use collect()

## Recommendations
1. Fix the 3 ERROR violations before commit (use /gate-fixer)
2. WARNING violations should be reviewed (use /code-review)
```

## Integration

- Used by `/gates` to format results
- Used by the SessionStart hook summary
- Output can be exported as JSON for CI integration
