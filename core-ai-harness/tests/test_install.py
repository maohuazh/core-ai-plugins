"""Tests for gates/install.py (the /gate-install implementation)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))

from install import (  # noqa: E402
    KIT_DIST,
    KIT_JARS,
    PLUGIN_ROOT,
    copy_rules,
    deploy_kit,
    detect_profile,
    render_gates_toml,
    write_gates_toml,
)

PROJECT_ROOT = Path(__file__).parent.parent


class TestDetectProfile(unittest.TestCase):
    def test_detect_fbr_on_core_framework_import(self):
        """core.framework imports -> fbr profile."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "backend" / "order-service" / "src" / "main" / "java"
            src.mkdir(parents=True)
            (src / "OrderController.java").write_text(
                "package app.order.web.controller;\n"
                "import core.framework.web.Controller;\n"
                "class OrderController {}\n",
                encoding="utf-8",
            )
            self.assertEqual(detect_profile(root), "fbr")

    def test_detect_default_without_core_framework(self):
        """No core.framework imports -> default profile."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src"
            src.mkdir(parents=True)
            (src / "App.java").write_text(
                "package com.example;\nimport java.util.List;\nclass App {}\n",
                encoding="utf-8",
            )
            self.assertEqual(detect_profile(root), "default")

    def test_detect_ignores_build_directory(self):
        """Files under build/ do not trigger fbr detection."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "build" / "classes"
            src.mkdir(parents=True)
            (src / "Generated.java").write_text(
                "import core.framework.web.Controller;\n", encoding="utf-8"
            )
            self.assertEqual(detect_profile(root), "default")


class TestCopyRules(unittest.TestCase):
    def test_copies_plugin_rules_into_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copied, skipped = copy_rules(root)
            self.assertGreater(copied, 0)
            target = root / ".claude" / "rules"
            self.assertTrue(target.is_dir())
            self.assertEqual(len(list(target.glob("*.md"))), copied + skipped)

    def test_second_run_skips_identical_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_rules(root)
            copied, skipped = copy_rules(root)
            self.assertEqual(copied, 0)
            self.assertGreater(skipped, 0)


class TestRenderGatesToml(unittest.TestCase):
    def test_default_profile_content(self):
        content = render_gates_toml("default", with_kit=False)
        self.assertIn('active = "default"', content)
        self.assertNotIn("[gates.lint]", content)

    def test_fbr_profile_content(self):
        content = render_gates_toml("fbr", with_kit=False)
        self.assertIn('active = "fbr"', content)

    def test_kit_enables_lint_and_error_prone(self):
        content = render_gates_toml("fbr", with_kit=True)
        self.assertIn("[gates.lint]", content)
        self.assertIn("enabled = true", content)
        self.assertIn("[gates.error-prone]", content)


class TestWriteGatesToml(unittest.TestCase):
    def test_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = write_gates_toml(root, "fbr", with_kit=False, force=False)
            self.assertEqual(state, "created")
            content = (root / ".claude" / "gates.toml").read_text(encoding="utf-8")
            self.assertIn('active = "fbr"', content)

    def test_keeps_existing_file_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / ".claude" / "gates.toml"
            path.parent.mkdir(parents=True)
            path.write_text("custom = true\n", encoding="utf-8")
            state = write_gates_toml(root, "fbr", with_kit=False, force=False)
            self.assertEqual(state, "kept")
            self.assertEqual(path.read_text(encoding="utf-8"), "custom = true\n")

    def test_force_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / ".claude" / "gates.toml"
            path.parent.mkdir(parents=True)
            path.write_text("custom = true\n", encoding="utf-8")
            state = write_gates_toml(root, "default", with_kit=False, force=True)
            self.assertEqual(state, "overwritten")
            self.assertIn('active = "default"', path.read_text(encoding="utf-8"))


class TestDeployKit(unittest.TestCase):
    def test_deploys_both_jars(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kit = root / "kit"
            dist = kit / KIT_DIST
            dist.mkdir(parents=True)
            (dist / "java-lint.jar").write_bytes(b"lint-bytes")
            (dist / "error-prone.jar").write_bytes(b"ep-bytes")
            gates_dir = root / "gates"

            report = deploy_kit(kit, gates_dir=gates_dir)

            self.assertEqual(len(report), 2)
            for gate, jar in KIT_JARS.items():
                dst = gates_dir / gate / ".dist" / jar
                self.assertTrue(dst.exists(), f"{jar} not deployed")
                self.assertEqual(dst.read_bytes(),
                                 (dist / jar).read_bytes())

    def test_missing_jar_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kit = root / "kit"
            dist = kit / KIT_DIST
            dist.mkdir(parents=True)
            (dist / "java-lint.jar").write_bytes(b"lint-bytes")
            gates_dir = root / "gates"
            with self.assertRaises(FileNotFoundError):
                deploy_kit(kit, gates_dir=gates_dir)


class TestMain(unittest.TestCase):
    def _run_main(self, argv, gates_dir=None, plugin_rules=None):
        """Run main() with GATES_DIR isolated to a temp dir (never the real plugin)."""
        import unittest.mock
        from install import main
        with tempfile.TemporaryDirectory() as tmp:
            if gates_dir is None:
                gates_dir = Path(tmp) / "plugin-gates"
            with unittest.mock.patch("install.GATES_DIR", gates_dir):
                with unittest.mock.patch("install.RULES_DIR", plugin_rules or (PLUGIN_ROOT / "rules")):
                    return main(argv)

    def test_main_install_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = self._run_main(["--project-root", str(root)])
            self.assertEqual(code, 0)
            self.assertTrue((root / ".claude" / "rules").is_dir())
            self.assertTrue((root / ".claude" / "gates.toml").exists())

    def test_main_deploys_kit_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kit = root / "kit"
            dist = kit / KIT_DIST
            dist.mkdir(parents=True)
            (dist / "java-lint.jar").write_bytes(b"lint-bytes")
            (dist / "error-prone.jar").write_bytes(b"ep-bytes")
            gates_dir = root / "plugin-gates"

            code = self._run_main(["--project-root", str(root), "--kit", str(kit)],
                                  gates_dir=gates_dir)
            self.assertEqual(code, 0)
            for gate, jar in KIT_JARS.items():
                self.assertTrue((gates_dir / gate / ".dist" / jar).exists())

    def test_main_kit_missing_jar_returns_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kit = root / "kit"
            dist = kit / KIT_DIST
            dist.mkdir(parents=True)
            (dist / "java-lint.jar").write_bytes(b"lint-bytes")
            code = self._run_main(["--project-root", str(root), "--kit", str(kit)])
            self.assertEqual(code, 1)

    def test_main_missing_project_root_returns_1(self):
        code = self._run_main(["--project-root", "/nonexistent/project/path"])
        self.assertEqual(code, 1)

    def test_main_json_output_valid(self):
        import json as json_mod
        import io
        import unittest.mock
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                code = self._run_main(["--project-root", str(root), "--json"])
            self.assertEqual(code, 0)
            payload = json_mod.loads(out.getvalue())
            self.assertEqual(payload["ok"], True)
            self.assertEqual(payload["profile"], "default")


if __name__ == "__main__":
    unittest.main()
