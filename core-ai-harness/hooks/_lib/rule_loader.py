"""
Rule loader.

Loads rules from rules/*.md files and merges with project-level overrides.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from . import RULES_DIR, debug_log

# Module-level cache for rules metadata
_rules_cache = {}


def load_rules_metadata(rules_dir: Path | None = None) -> list[dict]:
    """
    Load metadata from rules/*.md files.

    Each rule file should have frontmatter with:
    - name: Short name
    - description: One-line description
    - category: e.g., "fp", "architecture", "security", "code-style"

    Args:
        rules_dir: Path to rules directory. Defaults to plugin rules/.

    Returns:
        List of rule metadata dicts.
    """
    if rules_dir is None:
        rules_dir = RULES_DIR

    # Check cache using directory mtime
    try:
        dir_mtime = rules_dir.stat().st_mtime
        cache_key = str(rules_dir)

        if cache_key in _rules_cache:
            cached_mtime, cached_rules = _rules_cache[cache_key]
            if cached_mtime == dir_mtime:
                debug_log(f"Using cached rules metadata for {rules_dir}")
                return cached_rules
    except OSError:
        # If we can't stat the directory, skip cache
        pass

    if not rules_dir.exists():
        debug_log(f"Rules directory not found: {rules_dir}")
        return []

    rules = []

    for md_file in rules_dir.glob("*.md"):
        if md_file.name == "README.md":
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
            metadata = _parse_frontmatter(content)

            if metadata:
                metadata["file"] = md_file.name
                metadata["path"] = str(md_file)
                rules.append(metadata)
        except Exception as e:
            debug_log(f"Failed to load {md_file}: {e}")

    # Update cache
    try:
        _rules_cache[str(rules_dir)] = (dir_mtime, rules)
    except OSError:
        pass

    return rules


def _parse_frontmatter(content: str) -> dict | None:
    """
    Parse YAML-like frontmatter from markdown file.

    Supports:
    - Simple key: value pairs
    - Quoted strings: name: "value" or name: 'value'
    - Lists: tags: [fp, java]
    - Multi-line strings: description: |\\n  Line 1\\n  Line 2

    Expected format:
    ---
    name: rule-name
    description: Rule description
    category: fp
    tags: [fp, java]
    ---

    # Rule Content
    ...
    """
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        return None

    metadata = {}
    in_frontmatter = False
    current_key = None
    multiline_buffer = []
    multiline_indent = 0

    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            continue

        if in_frontmatter:
            if line.strip() == "---":
                # End of frontmatter - flush any pending multiline value
                if current_key and multiline_buffer:
                    metadata[current_key] = "\n".join(multiline_buffer)
                break

            # Check if this is a new key: value line
            if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
                # Flush previous multiline value
                if current_key and multiline_buffer:
                    metadata[current_key] = "\n".join(multiline_buffer)
                    multiline_buffer = []

                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                current_key = key

                # Check for multiline indicator
                if value in ("|", ">"):
                    # Multi-line string - collect indented lines
                    multiline_buffer = []
                    continue

                # Check for list syntax: [item1, item2]
                if value.startswith("[") and value.endswith("]"):
                    # Parse list
                    list_content = value[1:-1]
                    items = [item.strip() for item in list_content.split(",") if item.strip()]
                    metadata[key] = items
                    current_key = None  # Reset - no multiline following
                else:
                    # Simple value
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    metadata[key] = value
                    current_key = None
            elif current_key and line.startswith("  "):
                # This is a continuation line for multiline value
                # Remove leading spaces (preserve relative indentation)
                stripped = line.lstrip()
                multiline_buffer.append(stripped)

    return metadata if metadata else None


def load_project_overrides(project_root: Path) -> dict:
    """
    Load project-level gate overrides from .claude/gates.toml.

    Args:
        project_root: Project root directory.

    Returns:
        Overrides dict.
    """
    override_path = project_root / ".claude" / "gates.toml"

    if not override_path.exists():
        return {}

    try:
        with open(override_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        debug_log(f"Failed to load project overrides: {e}")
        return {}


def merge_config_with_overrides(
    base_config: dict, overrides: dict
) -> dict:
    """
    Merge base config with project-level overrides using deep merge.

    Overrides can:
    - Enable/disable specific gates
    - Change severity levels
    - Add custom rules
    - Override exclude paths
    - Override profile settings

    Args:
        base_config: Base config from gates/config.toml.
        overrides: Project overrides from .claude/gates.toml.

    Returns:
        Merged config dict.
    """
    return _deep_merge(base_config, overrides)


def _deep_merge(base: dict, override: dict) -> dict:
    """
    Recursively merge override dict into base dict.
    Override values take precedence.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_rules_summary(rules: list[dict], max_length: int = 1000) -> str:
    """
    Generate a summary of rules for SessionStart injection.

    Args:
        rules: List of rule metadata dicts.
        max_length: Maximum length of summary string.

    Returns:
        Summary string.
    """
    if not rules:
        return "No rules loaded."

    lines = ["Available rules:"]

    for rule in rules:
        name = rule.get("name", rule.get("file", "unknown"))
        description = rule.get("description", "No description")
        category = rule.get("category", "general")

        line = f"- [{category}] {name}: {description}"
        lines.append(line)

    summary = "\n".join(lines)

    # Truncate if too long
    if len(summary) > max_length:
        summary = summary[:max_length] + "\n... (truncated)"

    return summary
