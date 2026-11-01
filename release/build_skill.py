#!/usr/bin/env python3
"""Build the selected five-stage workflow as one portable, neutral PPT Skill."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.compose_personal_light import compose_personal_light

version = (ROOT / "VERSION").read_text().strip()
profile = {
    "contract": "io.clayz.presentation.personal-extension-profile/1.0",
    "profile_id": "ppt.instruction-package",
    "profile_version": "1.0.0",
    "compatibility": {"minimum_core_version": version, "maximum_core_version_exclusive": "0.22.0"},
    "overrides": [{"path": "locale.default", "policy": "replace", "value": "zh-CN"}],
    "mounts": [{"mount_id": "task-learning", "logical_root": "library://ppt-learning/",
                "bindings": {"local": {"adapter": "filesystem", "root": "knowledge"},
                             "chatgpt-personal": {"adapter": "host-library", "root": "PPT"}}}],
    "providers": [],
}
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "profile.json"
    path.write_text(json.dumps(profile))
    output = ROOT / "dist" / f"ppt-{version}-standalone-skill.zip"
    compose_personal_light(path, [], output, plugin_name="ppt")
(ROOT / "dist" / "SKILL-SHA256SUMS.txt").write_text(
    hashlib.sha256(output.read_bytes()).hexdigest() + "  " + output.name + "\n")
print(output)
