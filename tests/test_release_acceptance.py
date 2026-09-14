from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_chatgpt_release_acceptance import validate  # noqa: E402


class ReleaseAcceptanceTests(unittest.TestCase):
    def test_exact_candidate_receipt_binds_version_commit_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            manifest = Path(raw) / "component-versions.json"
            manifest.write_text(json.dumps({"release_version": "0.9.0"}), encoding="utf-8")
            digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
            commit = "a" * 40
            receipt = {
                "contract": "io.clayz.presentation.chatgpt-release-acceptance/1.0",
                "status": "accepted", "version": "0.9.0", "candidate_commit": commit,
                "personal_candidate_sha256": "b" * 64,
                "component_manifest_sha256": digest,
                "chatgpt_skill_id": "skill-synthetic",
                "acceptance_url": "https://chatgpt.com/c/synthetic",
                "accepted_by": "owner", "accepted_at": "2026-09-02T00:00:00+08:00",
                "startup_gate_status": "candidate-validated",
                "private_learning_status": "READY-FOR-LOGIC",
                "learning_audit_sha256": "c" * 64,
                "user_acceptance": True,
            }
            self.assertEqual(validate(receipt, version="0.9.0", commit=commit, component_manifest=manifest), [])
            receipt["candidate_commit"] = "d" * 40
            errors = validate(receipt, version="0.9.0", commit=commit, component_manifest=manifest)
            self.assertTrue(any("candidate_commit" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
