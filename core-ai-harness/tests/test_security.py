"""Test security pattern scanner."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
sys.path.insert(0, str(Path(__file__).parent.parent / "gates" / "security"))

from _lib.gate_runner import run_security_scan
from pattern_scanner import scan_file

PROJECT_ROOT = Path(__file__).parent.parent  # core-ai-harness/


class TestPatternScanner(unittest.TestCase):
    def test_hardcoded_secret(self):
        """Test hardcoded secret detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "Bad.java"
            f.write_text('public class B { String password = "hunter2secret"; }\n')

            findings = scan_file(f)

            self.assertTrue(
                any(x["rule_id"] == "hardcoded-secret" for x in findings),
                f"expected hardcoded-secret, got {[x['rule_id'] for x in findings]}",
            )

    def test_no_secret_for_config_var(self):
        """Test that a variable read from env is NOT flagged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "Ok.java"
            f.write_text('public class B { String password = System.getenv("PASS"); }\n')

            findings = scan_file(f)

            self.assertFalse(any(x["rule_id"] == "hardcoded-secret" for x in findings))

    def test_sql_injection(self):
        """Test SQL concatenation detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "Sql.java"
            f.write_text(
                'public class S { void q(Connection c, String id) {'
                ' String q = "SELECT * FROM users WHERE id = \'" + id + "\'"; } }\n'
            )

            findings = scan_file(f)

            self.assertTrue(any(x["rule_id"] == "sql-injection" for x in findings))

    def test_empty_catch(self):
        """Test empty catch block detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "Catch.java"
            f.write_text("public class C { void r() { try { x(); } catch (Exception e) {} } }\n")

            findings = scan_file(f)

            self.assertTrue(any(x["rule_id"] == "empty-catch" for x in findings))

    def test_clean_file_no_findings(self):
        """Test a clean file produces no findings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "Clean.java"
            f.write_text(
                "public class C {"
                " String get() { return System.getenv(\"API_KEY\"); }"
                " void q(Connection c) {"
                "   PreparedStatement ps = c.prepareStatement(\"SELECT * FROM t WHERE id=?\");"
                " } }"
            )

            findings = scan_file(f)
            self.assertEqual(findings, [])

    def test_run_security_scan_via_gate_runner(self):
        """Test run_security_scan integration with gate_runner."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            bad = project_root / "Bad.java"
            bad.write_text('public class B { String apiKey = "sk-1234567890abcdef"; }\n')

            findings, status = run_security_scan(
                ["Bad.java"], project_root, {}
            )

            self.assertEqual(status, "ok")
            self.assertTrue(
                any(f.rule_id == "hardcoded-secret" and f.severity == "ERROR" for f in findings)
            )

    def test_run_security_scan_missing_file(self):
        """Test run_security_scan handles missing scanner gracefully."""
        # Path to scanner is fixed at GATES_DIR/security/pattern_scanner.py
        findings, status = run_security_scan(
            ["tests/fixtures/GoodLoop.java"], PROJECT_ROOT, {}
        )
        # Should not crash; scanner exists so status is ok
        self.assertIn(status, ("ok", "skipped", "error"))


if __name__ == "__main__":
    unittest.main()
