"""Test project detector."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from _lib.project_detector import (
    detect_project,
    is_java_project,
    is_gradle_project,
    is_maven_project,
)


class TestProjectDetector(unittest.TestCase):
    def test_detect_gradle_project(self):
        """Test detection of Gradle project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            (project_root / "build.gradle.kts").touch()
            (project_root / "settings.gradle.kts").write_text(
                'include(":module-a", ":module-b")'
            )

            info = detect_project(project_root)

            self.assertEqual(info.type, "java")
            self.assertEqual(info.build_tool, "gradle")
            self.assertEqual(str(info.root), str(project_root.resolve()))
            self.assertIn(":module-a", info.modules)
            self.assertIn(":module-b", info.modules)
            self.assertTrue(is_java_project(info))
            self.assertTrue(is_gradle_project(info))

    def test_detect_gradle_build_gradle(self):
        """Test detection of Gradle project with build.gradle (groovy)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            (project_root / "build.gradle").touch()
            (project_root / "settings.gradle").write_text("include ':app'\n")

            info = detect_project(project_root)

            self.assertEqual(info.type, "java")
            self.assertEqual(info.build_tool, "gradle")
            self.assertIn(":app", info.modules)

    def test_detect_maven_project(self):
        """Test detection of Maven project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            (project_root / "pom.xml").touch()

            info = detect_project(project_root)

            self.assertEqual(info.type, "java")
            self.assertEqual(info.build_tool, "maven")
            self.assertEqual(str(info.root), str(project_root.resolve()))
            self.assertTrue(is_java_project(info))
            self.assertTrue(is_maven_project(info))

    def test_detect_node_project(self):
        """Test detection of Node.js project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            (project_root / "package.json").write_text('{"name": "test"}')

            info = detect_project(project_root)

            self.assertEqual(info.type, "node")
            self.assertEqual(info.build_tool, "npm")
            self.assertEqual(str(info.root), str(project_root.resolve()))

    def test_detect_node_pnpm(self):
        """Test detection of pnpm project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            (project_root / "package.json").write_text('{"name": "test"}')
            (project_root / "pnpm-lock.yaml").touch()

            info = detect_project(project_root)

            self.assertEqual(info.type, "node")
            self.assertEqual(info.build_tool, "pnpm")

    def test_detect_python_project(self):
        """Test detection of Python project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            (project_root / "pyproject.toml").touch()

            info = detect_project(project_root)

            self.assertEqual(info.type, "python")

    def test_detect_unknown_project(self):
        """Test detection of unknown project type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            info = detect_project(project_root)

            self.assertEqual(info.type, "unknown")
            self.assertIsNone(info.build_tool)

    def test_detect_empty_gradle_modules(self):
        """Test that empty/malformed settings file yields no modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            (project_root / "build.gradle").touch()
            (project_root / "settings.gradle").write_text("// no includes\n")

            info = detect_project(project_root)

            self.assertEqual(info.type, "java")
            self.assertEqual(info.modules, [])

    def test_project_info_to_dict(self):
        """Test ProjectInfo serialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "pom.xml").touch()

            info = detect_project(project_root)
            d = info.to_dict()

            self.assertEqual(d["type"], "java")
            self.assertEqual(d["build_tool"], "maven")
            self.assertIsNone(d["modules"])
            self.assertEqual(d["root"], str(project_root.resolve()))


if __name__ == "__main__":
    unittest.main()
