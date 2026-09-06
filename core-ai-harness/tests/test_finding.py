"""Test Finding structure."""

import sys
import unittest
from pathlib import Path

# Add parent directory to path so we can import _lib
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from _lib import Finding


class TestFinding(unittest.TestCase):
    def test_finding_creation(self):
        """Test basic Finding creation."""
        f = Finding(
            rule_id="no-traditional-for-loop",
            gate="ast-grep",
            file="src/Main.java",
            line=10,
            col=5,
            severity="ERROR",
            message="Use Stream API instead of traditional for loop",
            fixable=False,
        )

        self.assertEqual(f.rule_id, "no-traditional-for-loop")
        self.assertEqual(f.gate, "ast-grep")
        self.assertEqual(f.file, "src/Main.java")
        self.assertEqual(f.line, 10)
        self.assertEqual(f.col, 5)
        self.assertEqual(f.severity, "ERROR")
        self.assertEqual(f.message, "Use Stream API instead of traditional for loop")
        self.assertFalse(f.fixable)

    def test_finding_to_dict(self):
        """Test Finding serialization to dict."""
        f = Finding(
            rule_id="test-rule",
            gate="test-gate",
            file="Test.java",
            line=20,
            severity="WARNING",
            message="Test message",
        )

        d = f.to_dict()

        self.assertEqual(d["rule_id"], "test-rule")
        self.assertEqual(d["gate"], "test-gate")
        self.assertEqual(d["file"], "Test.java")
        self.assertEqual(d["line"], 20)
        self.assertIsNone(d["col"])
        self.assertEqual(d["severity"], "WARNING")
        self.assertEqual(d["message"], "Test message")
        self.assertFalse(d["fixable"])

    def test_finding_from_dict(self):
        """Test Finding deserialization from dict."""
        data = {
            "rule_id": "test-rule",
            "gate": "test-gate",
            "file": "Test.java",
            "line": 30,
            "col": 15,
            "severity": "HINT",
            "message": "Hint message",
            "fixable": True,
        }

        f = Finding.from_dict(data)

        self.assertEqual(f.rule_id, "test-rule")
        self.assertEqual(f.gate, "test-gate")
        self.assertEqual(f.file, "Test.java")
        self.assertEqual(f.line, 30)
        self.assertEqual(f.col, 15)
        self.assertEqual(f.severity, "HINT")
        self.assertEqual(f.message, "Hint message")
        self.assertTrue(f.fixable)

    def test_finding_repr(self):
        """Test Finding string representation."""
        f = Finding(
            rule_id="test-rule",
            gate="test-gate",
            file="Test.java",
            line=40,
            severity="ERROR",
        )

        repr_str = repr(f)
        self.assertIn("test-rule", repr_str)
        self.assertIn("test-gate", repr_str)
        self.assertIn("Test.java", repr_str)
        self.assertIn("40", repr_str)
        self.assertIn("ERROR", repr_str)

    def test_finding_roundtrip(self):
        """Test Finding dict roundtrip preserves all fields."""
        original = Finding(
            rule_id="no-parameter-mutation",
            gate="ast-grep",
            file="src/Service.java",
            line=42,
            col=7,
            severity="ERROR",
            message="Parameters should not be reassigned",
            fixable=False,
        )
        restored = Finding.from_dict(original.to_dict())
        self.assertEqual(original.to_dict(), restored.to_dict())


if __name__ == "__main__":
    unittest.main()
