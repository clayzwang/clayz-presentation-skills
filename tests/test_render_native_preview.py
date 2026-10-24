import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import render_native_preview as preview


class NativePreviewProcessEvidenceTest(unittest.TestCase):
    def _font_environment(self, directory, *args):
        (directory / 'font-environment.json').write_text('{}\n')
        return {'TASK_TEST_ONLY': 'not-recorded-environment'}, {}

    def test_nonzero_render_keeps_exit_and_logs_before_stopping(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); native = root / 'native.pptx'; native.write_bytes(b'fixture')
            target = root / 'render'
            actual = subprocess.CompletedProcess(['libreoffice'], 1, '', 'conversion failed\n')
            with patch.object(preview, 'audit_shape_bounds', return_value={'passed': True, 'issues': []}), patch.object(preview, 'font_environment', self._font_environment), patch.object(preview.subprocess, 'run', return_value=actual) as run:
                with self.assertRaisesRegex(RuntimeError, 'conversion failed'):
                    preview.render(native, target, ['A'], font_file='bound', font_family='STKaiti')
            self.assertEqual(run.call_count, 1)
            rows = json.loads((target / 'subprocess-observations.json').read_text())
            self.assertEqual(len(rows), 1)
            self.assertEqual((rows[0]['stage'], rows[0]['returncode'], rows[0]['stdout'], rows[0]['stderr']), ('libreoffice', 1, '', 'conversion failed\n'))
            self.assertEqual((target / 'libreoffice.log').read_text(), 'conversion failed\n')
            self.assertNotIn('not-recorded-environment', json.dumps(rows))
            self.assertFalse((target / 'manifest.json').exists())

    def test_launch_failure_is_recorded_without_inventing_exit_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); native = root / 'native.pptx'; native.write_bytes(b'fixture')
            target = root / 'render'
            with patch.object(preview, 'audit_shape_bounds', return_value={'passed': True, 'issues': []}), patch.object(preview, 'font_environment', self._font_environment), patch.object(preview.subprocess, 'run', side_effect=FileNotFoundError('missing renderer')) as run:
                with self.assertRaises(FileNotFoundError):
                    preview.render(native, target, ['A'], font_file='bound', font_family='STKaiti')
            self.assertEqual(run.call_count, 1)
            row = json.loads((target / 'subprocess-observations.json').read_text())[0]
            self.assertIsNone(row['returncode']); self.assertIsNone(row['stdout']); self.assertIsNone(row['stderr'])
            self.assertEqual(row['launch_error']['type'], 'FileNotFoundError')
            self.assertIn('missing renderer', (target / 'libreoffice.log').read_text())
            self.assertFalse((target / 'manifest.json').exists())

    def test_success_keeps_original_route_and_binds_process_observations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); native = root / 'native.pptx'; native.write_bytes(b'fixture')
            target = root / 'render'; calls = []
            def execute(command, **kwargs):
                calls.append(command)
                self.assertTrue(kwargs['capture_output']); self.assertTrue(kwargs['text'])
                self.assertEqual(kwargs['env'], {'TASK_TEST_ONLY': 'not-recorded-environment'})
                if command[0] == 'libreoffice':
                    (target / 'native.pdf').write_bytes(b'pdf-fixture')
                elif command[0] == 'pdftoppm':
                    (target / 'slide-1.png').write_bytes(b'png-fixture')
                return subprocess.CompletedProcess(command, 0, command[0] + ' stdout', '')
            with patch.object(preview, 'audit_shape_bounds', return_value={'passed': True, 'issues': []}), patch.object(preview, 'font_environment', self._font_environment), patch.object(preview.subprocess, 'run', side_effect=execute):
                manifest = preview.render(native, target, ['A'], font_file='bound', font_family='STKaiti')
            self.assertEqual([c[0] for c in calls], ['libreoffice', 'pdffonts', 'pdftoppm'])
            self.assertEqual(calls[0], ['libreoffice', '-env:UserInstallation=file://' + str(target / 'lo-profile'), '--headless', '--convert-to', 'pdf', '--outdir', str(target), str(native)])
            self.assertEqual(calls[1], ['pdffonts', str(target / 'native.pdf')])
            self.assertEqual(calls[2], ['pdftoppm', '-png', '-scale-to', '1600', str(target / 'native.pdf'), str(target / 'slide')])
            rows = json.loads((target / 'subprocess-observations.json').read_text())
            self.assertEqual([r['returncode'] for r in rows], [0, 0, 0])
            self.assertEqual(manifest['process_observations'], preview.ref(target / 'subprocess-observations.json'))
            self.assertEqual(manifest['slides'][0]['slide_id'], 'A')
            self.assertEqual((target / 'libreoffice.log').read_text(), 'libreoffice stdout')
            self.assertEqual((target / 'pdffonts.txt').read_text(), 'pdffonts stdout')


if __name__ == '__main__':
    unittest.main()
