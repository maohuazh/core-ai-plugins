---
name: project-onboard
description: "Initialize core-ai-harness for a new project"
---

# Project Onboard

Sets up core-ai-harness in a new project, configuring gates and hooks based on project type.

## Usage

```
/project-onboard
```

## What it does

1. **Detect Project Type**
   - Scans for build files (pom.xml, build.gradle, package.json, etc.)
   - Identifies language and framework

2. **Copy Rules**
   - Copies rules/*.md to .claude/rules/
   - Makes rules available to Claude automatically

3. **Configure Gates**
   - Creates .claude/gates.toml with project-specific settings
   - Enables appropriate gates for the project type
   - Sets up FBR profile if detected

4. **Verify Setup**
   - Runs test scan on sample files
   - Confirms hooks are working
   - Reports any issues

## Project Types Supported

### Java Projects
- ✅ Gradle (single and multi-module)
- ✅ Maven
- ✅ Spring Boot
- ✅ FBR framework (auto-detected)

### Node/TypeScript Projects
- ✅ Basic gate support
- ⚠️ Limited FP rules (Java-focused)

### Python Projects
- ✅ Basic gate support
- ⚠️ Limited FP rules (Java-focused)

## Configuration

After onboarding, you can customize settings in `.claude/gates.toml`:

```toml
[profile]
active = "default"  # or "fbr" for FBR projects

[gates]
ast-grep.enabled = true
security.enabled = true

[gates.fbr]
lint.enabled = false  # FBR-specific gates
error-prone.enabled = false
build.enabled = false
```

## Next Steps

After onboarding:
1. Review the generated `.claude/gates.toml`
2. Run `/gate-scanner` to test the setup
3. Consider running `/gate-fixer` on existing code
4. Add project-specific rules to `.claude/rules/`

## Troubleshooting

If gates don't run after onboarding:
- Ensure you're in the project root directory
- Check that `.claude/gates.toml` exists
- Verify rules were copied to `.claude/rules/`
- Run `claude --plugin-dir ./core-ai-harness` to reload the plugin
