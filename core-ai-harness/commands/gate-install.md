---
description: "Install and configure core-ai-harness for a project"
---

# Gate Install Command

Install core-ai-harness in the current project.

## Usage

```
/gate-install
```

## What it does

1. **Check Prerequisites**
   - Verifies Python 3.11+ is available
   - Checks if ast-grep is installed
   - Detects project type

2. **Copy Rules**
   - Copies `rules/*.md` to `.claude/rules/`
   - Makes rules available to Claude automatically

3. **Create Configuration**
   - Creates `.claude/gates.toml` if it doesn't exist
   - Sets up default profile (or fbr profile if detected)

4. **Verify Installation**
   - Runs a test scan to confirm gates work
   - Reports any issues

## Manual Installation

If you prefer manual installation:

### 1. Copy Rules

```bash
mkdir -p .claude/rules
cp /path/to/core-ai-harness/rules/*.md .claude/rules/
```

### 2. Create Configuration

```bash
mkdir -p .claude
cat > .claude/gates.toml << 'EOF'
[profile]
active = "default"

[gates]
ast-grep.enabled = true
security.enabled = true
EOF
```

### 3. Load Plugin

```bash
claude --plugin-dir /path/to/core-ai-harness
```

## Project-Specific Configuration

After installation, customize `.claude/gates.toml`:

```toml
# Use FBR profile for FBR projects
[profile]
active = "fbr"

# Disable specific gates
[gates]
security.enabled = false

# Enable FBR-specific gates
[gates.fbr]
lint.enabled = true
error-prone.enabled = true
build.enabled = true
```

## Verification

After installation, verify it works:

```bash
# Check a file
/gate-check path/to/file.java

# Check all changed files
/gates --scope changed
```

## Troubleshooting

### ast-grep not found

Install ast-grep:
```bash
brew install ast-grep
```

### Rules not loading

Ensure rules are in `.claude/rules/`:
```bash
ls .claude/rules/
```

### Gates not running

Check configuration:
```bash
cat .claude/gates.toml
```

## Next Steps

After installation:
1. Review the rules in `.claude/rules/`
2. Customize `.claude/gates.toml` for your project
3. Run `/gates` to check your code
4. Consider adding project-specific rules
