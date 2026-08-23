#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Run repository validation without creating cache files."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run([sys.executable, *args], cwd=ROOT, env=environment, check=True)


def compile_sources() -> None:
    for path in sorted(ROOT.rglob("*.py")):
        if ".git" in path.parts:
            continue
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def main() -> int:
    compile_sources()
    run("scripts/validate_version.py", ".")
    run("scripts/validate_config.py", "config/default.json")
    run("scripts/validate_provenance.py", "provenance/manifest.yaml")
    run("scripts/validate_architecture_research_library.py", ".")
    run("scripts/validate_visual_regression_suite.py", "tests/fixtures/visual-regression-suite.json")
    run("scripts/validate_skill_tree.py", ".")
    run("scripts/validate_knowledge_scaffold.py", ".")
    run("scripts/validate_index_foundation.py")
    run("scripts/validate_layout_contracts.py")
    run("scripts/validate_pattern_library.py")
    run("scripts/validate_markdown_links.py", ".")
    run("scripts/validate_experience.py", ".")
    denylist = os.environ.get("CLAYZ_RELEASE_DENYLIST")
    command = ["scripts/check_release_hygiene.py", "."]
    if denylist:
        command.extend(["--denylist", denylist])
    run(*command)
    run("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py")
    print("all validations passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
