"""Test gate runner (integration with ast-grep, skipped if not installed)."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path so we can import _lib
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from _lib.gate_runner import (
    get_enabled_gates,
    load_config,
    run_ast_grep,
    run_gates,
)

PROJECT_ROOT = Path(__file__).parent.parent  # core-ai-harness/
FIXTURES = PROJECT_ROOT / "tests" / "fixtures"

AST_GREP_AVAILABLE = shutil.which("ast-grep") is not None or shutil.which("sg") is not None


class TestGateRunner(unittest.TestCase):
    def test_load_config_default(self):
        """Test loading the default config.toml."""
        config = load_config()
        self.assertIn("gates", config)
        self.assertIn("ast-grep", config["gates"])

    def test_get_enabled_gates_default_profile(self):
        """Test enabled gates in default profile."""
        config = load_config()
        enabled = get_enabled_gates(config, "default")

        self.assertIn("ast-grep", enabled)
        # FBR-only gates should NOT be enabled in default profile
        self.assertNotIn("lint", enabled)
        self.assertNotIn("error-prone", enabled)
        self.assertNotIn("build", enabled)

    def test_get_enabled_gates_fbr_profile(self):
        """Test enabled gates in fbr profile."""
        config = load_config()
        enabled = get_enabled_gates(config, "fbr")

        # ast-grep is in both profiles
        self.assertIn("ast-grep", enabled)

    @unittest.skipUnless(AST_GREP_AVAILABLE, "ast-grep not installed")
    def test_run_ast_grep_finds_bad_loop(self):
        """Test that ast-grep finds the traditional for-loop violation."""
        findings, status = run_ast_grep(
            files=["tests/fixtures/BadLoop.java"],
            project_root=PROJECT_ROOT,
            config={},
        )

        self.assertEqual(status, "ok")
        self.assertGreaterEqual(len(findings), 1)
        self.assertTrue(any(f.rule_id == "no-traditional-for-loop" for f in findings))

    @unittest.skipUnless(AST_GREP_AVAILABLE, "ast-grep not installed")
    def test_run_ast_grep_clean_file(self):
        """Test that ast-grep finds no violations in clean file."""
        findings, status = run_ast_grep(
            files=["tests/fixtures/GoodLoop.java"],
            project_root=PROJECT_ROOT,
            config={},
        )

        self.assertEqual(status, "ok")
        self.assertEqual(findings, [])

    @unittest.skipUnless(AST_GREP_AVAILABLE, "ast-grep not installed")
    def test_run_gates_files_scope(self):
        """Test run_gates with files scope finds all violations."""
        bad_files = [
            "tests/fixtures/BadLoop.java",
            "tests/fixtures/BadMutation.java",
            "tests/fixtures/BadAccumulator.java",
        ]
        findings, statuses = run_gates(
            scope="files",
            files=bad_files,
            project_root=PROJECT_ROOT,
            profile="default",
        )

        self.assertEqual(statuses.get("ast-grep"), "ok")
        rule_ids = {f.rule_id for f in findings}
        self.assertIn("no-traditional-for-loop", rule_ids)
        self.assertIn("no-parameter-mutation", rule_ids)
        self.assertIn("no-mutable-accumulator", rule_ids)

    @unittest.skipUnless(AST_GREP_AVAILABLE, "ast-grep not installed")
    def test_run_gates_clean_files_no_findings(self):
        """Test that clean files produce no findings."""
        good_files = [
            "tests/fixtures/GoodLoop.java",
            "tests/fixtures/GoodMutation.java",
            "tests/fixtures/GoodAccumulator.java",
        ]
        findings, _ = run_gates(
            scope="files",
            files=good_files,
            project_root=PROJECT_ROOT,
            profile="default",
        )

        self.assertEqual(findings, [])

    @unittest.skipUnless(AST_GREP_AVAILABLE, "ast-grep not installed")
    def test_run_gates_empty_files(self):
        """Test run_gates with empty file list."""
        findings, statuses = run_gates(
            scope="files",
            files=[],
            project_root=PROJECT_ROOT,
            profile="default",
        )

        self.assertEqual(findings, [])
        self.assertEqual(statuses, {})

    @unittest.skipUnless(AST_GREP_AVAILABLE, "ast-grep not installed")
    def test_shape_rules_disabled_in_default_profile(self):
        """Test that shape rules only fire in the fbr profile."""
        files = [
            "tests/fixtures/MyController.java",
            "tests/fixtures/BadTypo.java",
        ]

        default_findings, _ = run_gates(
            scope="files", files=files, project_root=PROJECT_ROOT, profile="default"
        )
        shape_ids = {f.rule_id for f in default_findings if f.rule_id.startswith("shape-")}
        self.assertEqual(shape_ids, set(), f"default profile should not fire shape rules, got {shape_ids}")

    @unittest.skipUnless(AST_GREP_AVAILABLE, "ast-grep not installed")
    def test_shape_rules_enabled_in_fbr_profile(self):
        """Test that shape rules fire in the fbr profile."""
        files = [
            "tests/fixtures/MyController.java",
            "tests/fixtures/BadTypo.java",
        ]

        fbr_findings, _ = run_gates(
            scope="files", files=files, project_root=PROJECT_ROOT, profile="fbr"
        )
        shape_ids = {f.rule_id for f in fbr_findings if f.rule_id.startswith("shape-")}
        self.assertIn("shape-controller-outside-controller-package", shape_ids)
        self.assertIn("shape-forbid-kakfa-package-typo", shape_ids)

    @unittest.skipUnless(AST_GREP_AVAILABLE, "ast-grep not installed")
    def test_fbr_gates_skipped_without_jar(self):
        """Test lint/error-prone/build gates report skipped without deployed JARs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "build.gradle").touch()
            (project_root / "settings.gradle").touch()
            src = project_root / "src"
            (src / "main").mkdir(parents=True)
            (src / "main" / "Bad.java").write_text(
                "public class Bad { void f() { throw new RuntimeException(); } }"
            )

            findings, statuses = run_gates(
                scope="files",
                files=["src/main/Bad.java"],
                project_root=project_root,
                profile="fbr",
            )

            # lint/error-prone/build default enabled=false in config; only ast-grep+security run
            self.assertNotIn("lint", statuses)


if __name__ == "__main__":
    unittest.main()



if __name__ == "__main__":
    unittest.main()
