---
description: "Install and configure core-ai-harness for a project"
---

# Gate Install Command

Install core-ai-harness in the current project.

## Usage

```
/gate-install [--profile default|fbr] [--kit <fbr-agent-gates-dir>] [--force]
```

| Option | Description |
|--------|-------------|
| `--profile <name>` | Profile to write into `.claude/gates.toml` (`default` or `fbr`). Default: auto-detect — projects importing `core.framework.*` are treated as FBR. |
| `--kit <dir>` | FBR agent kit directory (`fbr-agent-gates`) whose `tools/.dist/*.jar` get deployed into the plugin's `gates/lint/.dist/` and `gates/error-prone/.dist/`. |
| `--force` | Overwrite an existing `.claude/gates.toml`. By default an existing file is left untouched. |

Run from the target project root. The command delegates to
`gates/install.py`:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-.}/gates/install.py" --project-root "$(pwd)" [options]
```

## Examples

Install with the default (generic) profile:
```
/gate-install
```

Install an FBR project and deploy its lint/error-prone JARs:
```
/gate-install --profile fbr --kit ~/Downloads/fbr-agent-gates
```

Force-regenerate the project config:
```
/gate-install --force
```

## What it does

1. **Copy Rules** - Copies `rules/*.md` to `.claude/rules/`
2. **Create Configuration** - Creates `.claude/gates.toml` if it doesn't exist
   (profile auto-detected: `fbr` when the project imports `core.framework.*`)
3. **Deploy Kit** (with `--kit`) - Copies `java-lint.jar` and
   `error-prone.jar` from `<kit>/tools/.dist/` into the plugin's
   `gates/lint/.dist/` and `gates/error-prone/.dist/`, and enables those two
   gates in the generated `.claude/gates.toml`
4. **Verify** - Reports toolchain (python/ast-grep), installed rules, and
   deployed JARs

> The JARs are NOT shipped in the repo (~25MB each, FBR-specific). They are
> deployed into the plugin's own `gates/<gate>/.dist/` directory — that is
> where `gate_runner` looks for them, and they are shared by every project
> that uses the plugin. Re-run `--kit` after reinstalling the plugin or on a
> fresh machine.

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
# Use FBR profile for core-ng / FBR projects
[profile]
active = "fbr"

# Disable specific gates
[gates.security]
enabled = false

# Enable FBR-specific gates (JARs must be deployed via --kit)
[gates.lint]
enabled = true

[gates.error-prone]
enabled = true

[gates.build]
enabled = true
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

### lint / error-prone reported as "skipped"

The JARs are missing. Deploy them from the FBR agent kit:
```
/gate-install --kit /path/to/fbr-agent-gates
```

## Next Steps

After installation:
1. Review the rules in `.claude/rules/`
2. Customize `.claude/gates.toml` for your project
3. Run `/gates` to check your code
4. Consider adding project-specific rules
