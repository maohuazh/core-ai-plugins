"""Test diff parser."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from _lib.diff_parser import (
    FileDiff,
    filter_java_files,
    get_changed_files,
    get_changed_file_paths,
    get_staged_java_files,
    get_unstaged_java_files,
)


def git(repo: Path, *args: str) -> str:
    """Run git command in repo and return stdout."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    return result.stdout


class TestDiffParser(unittest.TestCase):
    def setUp(self):
        """Create a temp git repo with an initial commit."""
        self.repo = Path(tempfile.mkdtemp())
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")

        # Initial file
        (self.repo / "Main.java").write_text("class Main {}\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "init")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.repo)

    def test_no_changes(self):
        """Test with no changes."""
        files = get_changed_file_paths(self.repo)
        self.assertEqual(files, [])

    def test_unstaged_changes(self):
        """Test detection of unstaged modified file."""
        (self.repo / "Main.java").write_text("class Main { int x; }\n")

        diffs = get_changed_files(self.repo, mode="unstaged")
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0].file, "Main.java")

    def test_new_java_file_unstaged(self):
        """Test detection of new untracked Java file."""
        (self.repo / "NewFile.java").write_text("class NewFile {}\n")

        files = get_changed_file_paths(self.repo)
        # git diff (unstaged) does not include untracked files by default
        self.assertNotIn("NewFile.java", files)

    def test_staged_changes(self):
        """Test detection of staged file."""
        (self.repo / "Main.java").write_text("class Main { int y; }\n")
        git(self.repo, "add", "Main.java")

        files = get_changed_file_paths(self.repo, mode="staged")
        self.assertIn("Main.java", files)

    def test_filter_java_files(self):
        """Test Java file filtering."""
        paths = ["a.java", "b.py", "c/Controller.java", "README.md", "d.Java"]
        java = filter_java_files(paths)

        self.assertEqual(java, ["a.java", "c/Controller.java"])

    def test_get_unstaged_java_files(self):
        """Test getting unstaged Java files only."""
        (self.repo / "Main.java").write_text("class Main { int z; }\n")
        (self.repo / "notes.md").write_text("hello\n")

        java_files = get_unstaged_java_files(self.repo)
        self.assertIn("Main.java", java_files)
        self.assertNotIn("notes.md", java_files)

    def test_get_staged_java_files(self):
        """Test getting staged Java files only."""
        (self.repo / "Main.java").write_text("class Main { int w; }\n")
        (self.repo / "Other.java").write_text("class Other {}\n")
        git(self.repo, "add", "Main.java")

        staged = get_staged_java_files(self.repo)
        self.assertIn("Main.java", staged)
        self.assertNotIn("Other.java", staged)

    def test_commit_mode(self):
        """Test diff against a specific commit."""
        (self.repo / "Main.java").write_text("class Main { int v; }\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "second")

        # Diff from HEAD~1 to HEAD
        files = get_changed_file_paths(self.repo, mode="commit", commit_hash="HEAD~1")
        self.assertIn("Main.java", files)

    def test_filediff_structure(self):
        """Test FileDiff fields."""
        fd = FileDiff(file="a.java", added_lines=[1, 2], removed_lines=[3])
        self.assertEqual(fd.total_additions, 2)
        self.assertEqual(fd.total_deletions, 1)
        self.assertEqual(fd.file, "a.java")

    def test_real_line_numbers(self):
        """Test that diff parser returns actual line numbers, not synthetic ranges."""
        # Create a file with multiple lines
        (self.repo / "Test.java").write_text(
            "class Test {\n"  # line 1
            "  void method1() {}\n"  # line 2
            "  void method2() {}\n"  # line 3
            "  void method3() {}\n"  # line 4
            "}\n"  # line 5
        )
        git(self.repo, "add", "Test.java")
        git(self.repo, "commit", "-q", "-m", "add Test.java")

        # Modify only line 4
        (self.repo / "Test.java").write_text(
            "class Test {\n"  # line 1
            "  void method1() {}\n"  # line 2
            "  void method2() {}\n"  # line 3
            "  void method3() { int x = 42; }\n"  # line 4 (modified)
            "}\n"  # line 5
        )

        diffs = get_changed_files(self.repo, mode="unstaged")
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0].file, "Test.java")

        # The added line should be line 4, not a synthetic range
        self.assertIn(4, diffs[0].added_lines)
        # The removed line should also be line 4 (old content)
        self.assertIn(4, diffs[0].removed_lines)

        # Should NOT have synthetic line numbers like 1, 2, 3
        self.assertNotIn(1, diffs[0].added_lines)
        self.assertNotIn(2, diffs[0].added_lines)


if __name__ == "__main__":
    unittest.main()
