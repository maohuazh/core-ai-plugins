"""Test rule loader."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from _lib.rule_loader import (
    _parse_frontmatter,
    get_rules_summary,
    load_project_overrides,
    load_rules_metadata,
    merge_config_with_overrides,
)


class TestRuleLoader(unittest.TestCase):
    def test_parse_frontmatter(self):
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

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["name"], "fp-paradigm")
        self.assertEqual(metadata["description"], "Functional programming paradigm rules")
        self.assertEqual(metadata["category"], "fp")

    def test_parse_frontmatter_with_quotes(self):
        """Test frontmatter parsing with quoted values."""
        content = """---
name: "test-rule"
description: 'Test description'
---
"""

        metadata = _parse_frontmatter(content)

        self.assertEqual(metadata["name"], "test-rule")
        self.assertEqual(metadata["description"], "Test description")

    def test_parse_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "# Just a heading\n\nNo frontmatter here."

        metadata = _parse_frontmatter(content)

        self.assertIsNone(metadata)

    def test_load_rules_metadata(self):
        """Test loading rules metadata from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)

            rule_file = rules_dir / "test-rule.md"
            rule_file.write_text("""---
name: test-rule
description: Test rule description
category: test
---

# Test Rule
""")

            rules = load_rules_metadata(rules_dir)

            self.assertEqual(len(rules), 1)
            self.assertEqual(rules[0]["name"], "test-rule")
            self.assertEqual(rules[0]["description"], "Test rule description")
            self.assertEqual(rules[0]["category"], "test")
            self.assertEqual(rules[0]["file"], "test-rule.md")

    def test_load_rules_metadata_skips_readme(self):
        """Test that README.md is skipped in metadata loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)

            (rules_dir / "README.md").write_text("# README")
            (rules_dir / "fp.md").write_text("---\nname: fp\n---\n")

            rules = load_rules_metadata(rules_dir)

            self.assertEqual(len(rules), 1)
            self.assertEqual(rules[0]["name"], "fp")

    def test_load_rules_metadata_empty_dir(self):
        """Test loading from empty/nonexistent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir) / "does-not-exist"

            rules = load_rules_metadata(rules_dir)

            self.assertEqual(rules, [])

    def test_merge_config_with_overrides(self):
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

        self.assertFalse(merged["gates"]["ast-grep"]["enabled"])
        self.assertEqual(merged["gates"]["ast-grep"]["timeout"], 30)
        self.assertEqual(merged["gates"]["ast-grep"]["custom_option"], "value")

    def test_merge_config_overrides_new_gate(self):
        """Test that overrides can add a new gate not in base config."""
        base_config = {"gates": {}}
        overrides = {"gates": {"custom-gate": {"enabled": True}}}

        merged = merge_config_with_overrides(base_config, overrides)

        self.assertTrue(merged["gates"]["custom-gate"]["enabled"])

    def test_merge_config_profile(self):
        """Test profile merge."""
        base_config = {"profile": {"active": "default"}}
        overrides = {"profile": {"active": "fbr"}}

        merged = merge_config_with_overrides(base_config, overrides)

        self.assertEqual(merged["profile"]["active"], "fbr")

    def test_load_project_overrides_missing(self):
        """Test loading overrides when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            overrides = load_project_overrides(project_root)

            self.assertEqual(overrides, {})

    def test_get_rules_summary(self):
        """Test rules summary generation."""
        rules = [
            {"name": "rule-1", "description": "First rule", "category": "fp"},
            {"name": "rule-2", "description": "Second rule", "category": "security"},
        ]

        summary = get_rules_summary(rules)

        self.assertIn("Available rules:", summary)
        self.assertIn("rule-1", summary)
        self.assertIn("rule-2", summary)
        self.assertIn("First rule", summary)
        self.assertIn("Second rule", summary)

    def test_get_rules_summary_empty(self):
        """Test rules summary with no rules."""
        summary = get_rules_summary([])

        self.assertEqual(summary, "No rules loaded.")

    def test_get_rules_summary_truncation(self):
        """Test rules summary respects max_length."""
        rules = [
            {"name": "rule-1", "description": "x" * 100, "category": "fp"},
            {"name": "rule-2", "description": "y" * 100, "category": "fp"},
        ]

        summary = get_rules_summary(rules, max_length=50)

        self.assertLessEqual(len(summary), 50 + 50)  # allow truncation marker overhead
        self.assertIn("truncated", summary)


if __name__ == "__main__":
    unittest.main()
