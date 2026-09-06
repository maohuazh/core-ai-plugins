"""Test project detector."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from _lib.project_detector import detect_project, is_java_project, is_gradle_project


def test_detect_gradle_project():
    """Test detection of Gradle project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create Gradle files
        (project_root / "build.gradle.kts").touch()
        (project_root / "settings.gradle.kts").write_text(
            'include(":module-a", ":module-b")'
        )

        info = detect_project(project_root)

        assert info.type == "java"
        assert info.build_tool == "gradle"
        assert str(info.root) == str(project_root.resolve())
        assert ":module-a" in info.modules
        assert ":module-b" in info.modules
        assert is_java_project(info)
        assert is_gradle_project(info)


def test_detect_maven_project():
    """Test detection of Maven project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create Maven file
        (project_root / "pom.xml").touch()

        info = detect_project(project_root)

        assert info.type == "java"
        assert info.build_tool == "maven"
        assert str(info.root) == str(project_root.resolve())
        assert is_java_project(info)


def test_detect_node_project():
    """Test detection of Node.js project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create package.json
        (project_root / "package.json").write_text('{"name": "test"}')

        info = detect_project(project_root)

        assert info.type == "node"
        assert info.build_tool == "npm"
        assert str(info.root) == str(project_root.resolve())


def test_detect_unknown_project():
    """Test detection of unknown project type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        info = detect_project(project_root)

        assert info.type == "unknown"
        assert info.build_tool is None


if __name__ == "__main__":
    test_detect_gradle_project()
    test_detect_maven_project()
    test_detect_node_project()
    test_detect_unknown_project()
    print("All project detector tests passed!")
