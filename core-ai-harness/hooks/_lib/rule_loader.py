"""
Rule loader.

Loads rules from rules/*.md files and merges with project-level overrides.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from . import RULES_DIR, debug_log


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

    return rules


def _parse_frontmatter(content: str) -> dict | None:
    """
    Parse YAML-like frontmatter from markdown file.

    Expected format:
    ---
    name: rule-name
    description: Rule description
    category: fp
    ---

    # Rule Content
    ...
    """
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        return None

    metadata = {}
    in_frontmatter = False

    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            continue

        if in_frontmatter:
            if line.strip() == "---":
                # End of frontmatter
                break

            # Parse key: value
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                metadata[key] = value

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
    Merge base config with project-level overrides.

    Overrides can:
    - Enable/disable specific gates
    - Change severity levels
    - Add custom rules

    Args:
        base_config: Base config from gates/config.toml.
        overrides: Project overrides from .claude/gates.toml.

    Returns:
        Merged config dict.
    """
    merged = base_config.copy()

    # Merge gates section
    if "gates" in overrides:
        if "gates" not in merged:
            merged["gates"] = {}

        for gate_name, gate_overrides in overrides["gates"].items():
            if gate_name not in merged["gates"]:
                merged["gates"][gate_name] = {}

            merged["gates"][gate_name].update(gate_overrides)

    # Merge profile section
    if "profile" in overrides:
        merged["profile"] = overrides["profile"]

    return merged


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
