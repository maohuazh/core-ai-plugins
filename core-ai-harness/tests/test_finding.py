"""Test Finding structure."""

import sys
from pathlib import Path

# Add parent directory to path so we can import _lib
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from _lib import Finding


def test_finding_creation():
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

    assert f.rule_id == "no-traditional-for-loop"
    assert f.gate == "ast-grep"
    assert f.file == "src/Main.java"
    assert f.line == 10
    assert f.col == 5
    assert f.severity == "ERROR"
    assert f.message == "Use Stream API instead of traditional for loop"
    assert f.fixable is False


def test_finding_to_dict():
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

    assert d["rule_id"] == "test-rule"
    assert d["gate"] == "test-gate"
    assert d["file"] == "Test.java"
    assert d["line"] == 20
    assert d["col"] is None
    assert d["severity"] == "WARNING"
    assert d["message"] == "Test message"
    assert d["fixable"] is False


def test_finding_from_dict():
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

    assert f.rule_id == "test-rule"
    assert f.gate == "test-gate"
    assert f.file == "Test.java"
    assert f.line == 30
    assert f.col == 15
    assert f.severity == "HINT"
    assert f.message == "Hint message"
    assert f.fixable is True


def test_finding_repr():
    """Test Finding string representation."""
    f = Finding(
        rule_id="test-rule",
        gate="test-gate",
        file="Test.java",
        line=40,
        severity="ERROR",
    )

    repr_str = repr(f)
    assert "test-rule" in repr_str
    assert "test-gate" in repr_str
    assert "Test.java" in repr_str
    assert "40" in repr_str
    assert "ERROR" in repr_str


if __name__ == "__main__":
    test_finding_creation()
    test_finding_to_dict()
    test_finding_from_dict()
    test_finding_repr()
    print("All Finding tests passed!")
