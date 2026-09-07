# Core AI Harness

A Claude Code plugin that enforces coding standards through automated gates (AST pattern matching, security checks) and provides AI-powered code review capabilities.

## Overview

Core AI Harness integrates three layers:

1. **Rules** - Natural language coding standards that Claude reads automatically
2. **Gates** - Automated checks (AST-Grep, security patterns) that run on every edit
3. **Skills** - AI-powered commands for code review, fixing violations, and project onboarding

## Features

### Automated Gate Checking

- **PostToolUse Hook**: Automatically checks Java files after every edit
- **Incremental Scanning**: Only scans changed files for fast feedback
- **Block on Errors**: Prevents violations from being committed by blocking the edit
- **Fix Suggestions**: Provides context and suggestions for fixing violations

### Supported Gates

1. **AST-Grep** - Functional programming pattern checks
   - No traditional for-loops (use Stream API)
   - No parameter mutation
   - No mutable accumulators
   - More FP rules...

2. **Security Patterns** - Regex-based security checks
   - Hardcoded secrets detection
   - SQL injection patterns
   - Other security anti-patterns

3. **Architecture Checks** - Layer violation detection
   - Controller → Service → Repository dependency rules
   - Package structure enforcement

### Skills

- `/gate-scanner` - Scan files for violations
- `/gate-fixer` - Get step-by-step guidance to fix violations
- `/code-review` - Comprehensive code review with multiple categories
- `/project-onboard` - Initialize core-ai-harness in a new project

### Commands

- `/gates` - Run all enabled gates on the codebase
- `/gate-check <file>` - Check specific files
- `/gate-install` - Install and configure for a project

## Installation

### Quick Install

In Claude Code, run:

```
/gate-install
```

This will:
1. Copy rules to `.claude/rules/`
2. Create `.claude/gates.toml` configuration
3. Verify the setup

### Manual Installation

1. Copy rules:
```bash
cp -r rules/ /path/to/your/project/.claude/rules/
```

2. Create configuration in your project:
```bash
cat > /path/to/your/project/.claude/gates.toml << 'EOF'
[profile]
active = "default"

[gates]
ast-grep.enabled = true
security.enabled = true
EOF
```

3. Load the plugin:
```bash
claude --plugin-dir /path/to/core-ai-harness
```

## Configuration

Configuration is stored in `.claude/gates.toml` in your project.

### Profile Selection

```toml
[profile]
active = "default"  # or "fbr" for FBR-specific rules
```

### Gate Configuration

```toml
[gates]
ast-grep.enabled = true
security.enabled = true

[gates.fbr]
lint.enabled = false      # FBR-specific gates
error-prone.enabled = false
build.enabled = false
```

### Severity Overrides

```toml
[overrides]
ast-grep.severity.no-while-loop = "warning"
security.patterns.severity.hardcoded-secret = "error"
```

## Usage

### Automatic Checking

The plugin automatically checks Java files after every edit. If violations are found:
- The edit is blocked
- Claude receives the findings in context
- Claude can automatically fix the issues

### Manual Checking

Run gates manually:

```bash
# Check all changed files
/gates

# Check specific files
/gate-check src/main/java/MyClass.java

# Check all files
/gates --scope all
```

### Code Review

Get comprehensive code review:

```bash
/code-review
```

### Auto-Fix

Get guided fixes for violations:

```bash
/gate-fixer
```

## Project Types

### Java Projects

Full support for:
- Gradle (single and multi-module)
- Maven
- Spring Boot
- FBR framework

### Other Languages

Basic support for:
- Node/TypeScript (limited gates)
- Python (limited gates)

## Development

### Plugin Structure

```
core-ai-harness/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── rules/                   # Natural language rules
├── gates/                   # Gate implementations
│   ├── ast-grep/
│   ├── security/
│   └── config.toml
├── hooks/                   # Hook scripts
│   ├── hooks.json
│   ├── _lib/               # Shared library
│   ├── post_edit_gate.py
│   └── session_start.py
├── skills/                  # Skill definitions
├── commands/                # Slash commands
└── tests/                   # Test fixtures
```

### Running Tests

```bash
cd tests
python3 test_finding.py
python3 test_project_detector.py
python3 test_rule_loader.py
```

### Debugging

Enable debug logging:

```bash
export DEBUG=1
claude
```

## Requirements

- Claude Code CLI
- Python 3.11+ (for hooks)
- ast-grep (for AST pattern matching)

### Installing ast-grep

```bash
# macOS
brew install ast-grep

# Other platforms
# See: https://ast-grep.github.io/guide/quick-start.html
```

## Architecture

### Gate Flow

```
File Edit
    ↓
PostToolUse Hook
    ↓
gate_runner.py
    ↓
ast-grep / security checks
    ↓
Findings → Hook Response
    ↓
Block or Allow
```

### Data Flow

```
hooks.json (hook definitions)
    ↓
post_edit_gate.py (hook script)
    ↓
_lib/gate_runner.py (execution engine)
    ↓
ast-grep CLI (pattern matching, invoked as subprocess)
    ↓
JSON findings → Finding objects
    ↓
Report to Claude
```

## License

MIT

## Contributing

Contributions welcome! Please:
1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Run all tests before submitting
