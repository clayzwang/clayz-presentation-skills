"""Verify the runtime-only release is complete without an external knowledge asset."""
import tempfile
import unittest
import sys
from pathlib import Path
from scripts import build_runtime_packs as builder
from scripts.verify_release_bundles import verify
sys.path.insert(0,str(builder.ROOT/'scripts'))


class SeparateKnowledgeRelease(unittest.TestCase):
    def test_runtime_checksums_exclude_learning_only_when_explicitly_selected(self):
        version=(builder.ROOT/'VERSION').read_text().strip()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            archives=[builder.build_light(root,version,target) for target in builder.LIGHT_TARGETS]
            builder.write_checksums(archives,root)
            self.assertEqual([],verify(root,(),include_learning=False))
            self.assertTrue(any('art-learning.zip' in error for error in verify(root,())))
