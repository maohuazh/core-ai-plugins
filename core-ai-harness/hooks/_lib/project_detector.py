"""
Project type detector.

Detects the project type (Java/Gradle, Java/Maven, Node/TS, etc.) by scanning
the project root for characteristic files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProjectInfo:
    """Detected project information."""

    type: str  # "java" | "node" | "python" | "unknown"
    build_tool: Optional[str] = None  # "gradle" | "maven" | "npm" | "yarn" | "pnpm"
    modules: list[str] | None = None  # List of module paths (multi-module projects)
    root: Optional[Path] = None  # Project root path

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "build_tool": self.build_tool,
            "modules": self.modules,
            "root": str(self.root) if self.root else None,
        }


def detect_project(project_root: str | Path | None = None) -> ProjectInfo:
    """
    Detect project type by scanning the root directory.

    Args:
        project_root: Path to project root. Defaults to CWD.

    Returns:
        ProjectInfo with detected type, build tool, and modules.
    """
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root).resolve()

    # Java / Gradle
    build_gradle_kts = project_root / "build.gradle.kts"
    build_gradle = project_root / "build.gradle"
    settings_gradle_kts = project_root / "settings.gradle.kts"
    settings_gradle = project_root / "settings.gradle"

    if (build_gradle_kts.exists() or build_gradle.exists()) and (
        settings_gradle_kts.exists() or settings_gradle.exists()
    ):
        modules = _detect_gradle_modules(project_root, settings_gradle_kts if settings_gradle_kts.exists() else settings_gradle)
        return ProjectInfo(
            type="java",
            build_tool="gradle",
            modules=modules,
            root=project_root,
        )

    # Single-module Gradle (no settings.gradle)
    if build_gradle_kts.exists() or build_gradle.exists():
        return ProjectInfo(
            type="java",
            build_tool="gradle",
            modules=None,
            root=project_root,
        )

    # Java / Maven
    pom_xml = project_root / "pom.xml"
    if pom_xml.exists():
        return ProjectInfo(
            type="java",
            build_tool="maven",
            modules=None,
            root=project_root,
        )

    # Node / TypeScript
    package_json = project_root / "package.json"
    if package_json.exists():
        lock_file, package_manager = _detect_node_package_manager(project_root)
        return ProjectInfo(
            type="node",
            build_tool=package_manager,
            modules=None,
            root=project_root,
        )

    # Python
    pyproject_toml = project_root / "pyproject.toml"
    setup_py = project_root / "setup.py"
    if pyproject_toml.exists() or setup_py.exists():
        return ProjectInfo(
            type="python",
            build_tool=None,
            modules=None,
            root=project_root,
        )

    # Unknown
    return ProjectInfo(
        type="unknown",
        build_tool=None,
        modules=None,
        root=project_root,
    )


def _detect_gradle_modules(
    project_root: Path, settings_file: Path
) -> list[str]:
    """
    Detect Gradle modules by parsing settings.gradle / settings.gradle.kts.

    Looks for 'include' directives like:
        include ':module-a', ':module-b'
        include(":module-a")
    """
    import re
    modules = []
    try:
        content = settings_file.read_text(encoding="utf-8")
        # Find all module references: colon-prefixed identifiers in quotes
        # e.g., ':module-a', ":module-b"
        matches = re.findall(r"""['"](:[\w\-:]+)['"]""", content)
        modules.extend(matches)
    except Exception:
        # If parsing fails, return empty list
        pass

    return modules


def _detect_node_package_manager(
    project_root: Path,
) -> tuple[str | None, str]:
    """
    Detect Node.js package manager by checking lock files.

    Returns:
        (lock_file_name, package_manager_name)
    """
    if (project_root / "pnpm-lock.yaml").exists():
        return "pnpm-lock.yaml", "pnpm"
    if (project_root / "yarn.lock").exists():
        return "yarn.lock", "yarn"
    if (project_root / "package-lock.json").exists():
        return "package-lock.json", "npm"

    # Default to npm if no lock file found
    return None, "npm"


def is_java_project(project_info: ProjectInfo) -> bool:
    """Check if project is a Java project (Gradle or Maven)."""
    return project_info.type == "java"


def is_gradle_project(project_info: ProjectInfo) -> bool:
    """Check if project uses Gradle."""
    return project_info.build_tool == "gradle"


def is_maven_project(project_info: ProjectInfo) -> bool:
    """Check if project uses Maven."""
    return project_info.build_tool == "maven"
