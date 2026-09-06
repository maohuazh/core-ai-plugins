"""Test rule loader."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from _lib.rule_loader import (
    _parse_frontmatter,
    get_rules_summary,
    load_rules_metadata,
    merge_config_with_overrides,
)


def test_parse_frontmatter():
    """Test frontmatter parsing."""
    content = """---
name: fp-paradigm
description: Functional programming paradigm rules
category: fp
---

# FP Paradigm

Content here...
"""

    metadata = _parse_frontmatter(content)

    assert metadata is not None
    assert metadata["name"] == "fp-paradigm"
    assert metadata["description"] == "Functional programming paradigm rules"
    assert metadata["category"] == "fp"


def test_parse_frontmatter_with_quotes():
    """Test frontmatter parsing with quoted values."""
    content = """---
name: "test-rule"
description: 'Test description'
---
"""

    metadata = _parse_frontmatter(content)

    assert metadata["name"] == "test-rule"
    assert metadata["description"] == "Test description"


def test_parse_no_frontmatter():
    """Test parsing content without frontmatter."""
    content = "# Just a heading\n\nNo frontmatter here."

    metadata = _parse_frontmatter(content)

    assert metadata is None


def test_load_rules_metadata():
    """Test loading rules metadata from directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_dir = Path(tmpdir)

        # Create test rule file
        rule_file = rules_dir / "test-rule.md"
        rule_file.write_text("""---
name: test-rule
description: Test rule description
category: test
---

# Test Rule
""")

        rules = load_rules_metadata(rules_dir)

        assert len(rules) == 1
        assert rules[0]["name"] == "test-rule"
        assert rules[0]["description"] == "Test rule description"
        assert rules[0]["category"] == "test"
        assert rules[0]["file"] == "test-rule.md"


def test_merge_config_with_overrides():
    """Test merging base config with overrides."""
    base_config = {
        "gates": {
            "ast-grep": {
                "enabled": True,
                "timeout": 30,
            }
        }
    }

    overrides = {
        "gates": {
            "ast-grep": {
                "enabled": False,
                "custom_option": "value",
            }
        }
    }

    merged = merge_config_with_overrides(base_config, overrides)

    assert merged["gates"]["ast-grep"]["enabled"] is False
    assert merged["gates"]["ast-grep"]["timeout"] == 30
    assert merged["gates"]["ast-grep"]["custom_option"] == "value"


def test_get_rules_summary():
    """Test rules summary generation."""
    rules = [
        {
            "name": "rule-1",
            "description": "First rule",
            "category": "fp",
        },
        {
            "name": "rule-2",
            "description": "Second rule",
            "category": "security",
        },
    ]

    summary = get_rules_summary(rules)

    assert "Available rules:" in summary
    assert "rule-1" in summary
    assert "rule-2" in summary
    assert "First rule" in summary
    assert "Second rule" in summary


def test_get_rules_summary_empty():
    """Test rules summary with no rules."""
    summary = get_rules_summary([])

    assert summary == "No rules loaded."


if __name__ == "__main__":
    test_parse_frontmatter()
    test_parse_frontmatter_with_quotes()
    test_parse_no_frontmatter()
    test_load_rules_metadata()
    test_merge_config_with_overrides()
    test_get_rules_summary()
    test_get_rules_summary_empty()
    print("All rule loader tests passed!")
