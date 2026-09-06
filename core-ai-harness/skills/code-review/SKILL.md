---
name: code-review
description: "Perform comprehensive code review using gates and AI analysis"
---

# Code Review

Performs comprehensive code review combining gate checks with AI-powered analysis.

## Usage

```
/code-review [branch] [file1.java] [file2.java] ...
```

If no files specified, reviews all files changed in the current branch.

## What it does

1. **Gate Checks**: Runs all configured gates (AST-Grep, security, etc.)
2. **Architecture Review**: Checks for layer violations and dependency issues
3. **Security Analysis**: Identifies potential security vulnerabilities
4. **Performance Review**: Detects performance anti-patterns
5. **Code Quality**: Reviews naming, complexity, and maintainability

## Review Categories

### 🔴 Critical (must fix)
- Security vulnerabilities
- Data loss risks
- Breaking changes
- Critical FP violations

### 🟡 Warning (should fix)
- Architecture violations
- Performance concerns
- Code quality issues
- Maintainability problems

### 🔵 Info (consider fixing)
- Style improvements
- Refactoring suggestions
- Documentation gaps

## Output Format

```markdown
# Code Review Report

## Summary
- Files reviewed: 5
- Issues found: 12 (3 critical, 5 warnings, 4 info)

## Critical Issues
### src/main/java/com/example/Service.java
- **Line 23**: SQL injection vulnerability (security)
  - String concatenation used in SQL query
  - Fix: Use parameterized queries

## Warnings
### src/main/java/com/example/Controller.java
- **Line 45**: Layer violation (architecture)
  - Controller directly accesses Repository
  - Fix: Route through Service layer

## Info
### src/main/java/com/example/Utils.java
- **Line 12**: Consider using Optional instead of null (code-quality)
  - Method returns null for missing values
  - Fix: Return Optional<User>
```

## Integration

This skill combines gate-scanner findings with deeper AI analysis to provide comprehensive code review.
