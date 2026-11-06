import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1] / '.github/workflows/scripts'
sys.path.insert(0, str(SCRIPTS))
# Matrix and summary checks are offline; do not fetch an upstream version label.
with patch.dict(sys.modules, {'config': types.SimpleNamespace(KERNEL_VERSION='test')}):
    import matrix_generator
import build_summary
from patch_compat import adapt_namespace_context
with patch('urllib.request.urlopen', side_effect=OSError('offline test')):
    from config import BuildConfig
    from kernel_builder import KernelBuilder


class FullMatrixTests(unittest.TestCase):
    def test_real_packaging_outputs_can_be_collected(self):
        previous_cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                config = BuildConfig('android13', '5.10', '198', '2024-01')
                builder = KernelBuilder(config, tmp)
                builder.anykernel_dir.mkdir()
                (builder.anykernel_dir / 'anykernel.sh').write_text('# test template\n')
                (builder.work_dir / 'Image').write_bytes(b'test kernel image')
                artifacts = builder.create_anykernel_zips()
                self.assertEqual(1, len(artifacts))
                self.assertEqual(builder.work_dir, Path(artifacts[0]).parent)
                self.assertTrue(Path(artifacts[0]).is_file())
                result = root / 'result.json'
                result.write_text(json.dumps({'total': 1, 'success': 1,
                    'results': [{'artifacts': artifacts, 'config': config.to_dict()}]}))
                build_summary.collect(result, root / 'uploaded')
                with zipfile.ZipFile(root / 'uploaded' / Path(artifacts[0]).name) as archive:
                    self.assertEqual(b'test kernel image', archive.read('Image'))
        finally:
            os.chdir(previous_cwd)

    def test_namespace_context_adaptation_preserves_functional_changes(self):
        source = '#include "internal.h"\n\n/* mounts */\n'
        diff = ('diff --git a/fs/namespace.c b/fs/namespace.c\n'
                '--- a/fs/namespace.c\n+++ b/fs/namespace.c\n'
                '@@ -1,4 +1,7 @@\n'
                ' #include "internal.h"\n #include <trace/hooks/blk.h>\n \n'
                '+#ifdef CONFIG_KSU_SUSFS\n+#include <linux/susfs_def.h>\n+#endif\n'
                ' /* mounts */\n')
        adapted = adapt_namespace_context(diff, source)
        self.assertEqual([s for s in diff.splitlines() if s.startswith(('+', '-'))],
                         [s for s in adapted.splitlines() if s.startswith(('+', '-'))])
        self.assertEqual(diff, adapt_namespace_context(diff, '#include <trace/hooks/blk.h>'))
        self.assertEqual(adapted, adapt_namespace_context(adapted, source))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'fs').mkdir()
            (root / 'fs/namespace.c').write_text(source)
            before = subprocess.run(['patch', '--batch', '--dry-run', '-F0', '-p1'],
                                    cwd=root, input=diff, text=True, capture_output=True)
            self.assertNotEqual(0, before.returncode)
            subprocess.run(['patch', '--batch', '-F0', '-p1'], cwd=root,
                           input=adapted, text=True, capture_output=True, check=True)
            self.assertIn('#include <linux/susfs_def.h>', (root / 'fs/namespace.c').read_text())

    def test_matrix_coverage_and_pins(self):
        matrix = matrix_generator.generate_build_matrix()
        self.assertEqual(20, len(matrix))
        ids = {(c['android'], c['kernel'], c['sub_level']) for c in matrix}
        self.assertEqual(len(matrix), len(ids))
        self.assertIn(('android13', '5.10', '198'), ids)
        for cfg in matrix:
            self.assertRegex(cfg['susfs_commit'], r'^[0-9a-f]{40}$')
        self.assertEqual(['78', '90', '99', '124', '145'],
                         [c['sub_level'] for c in matrix if c['kernel'] == '6.1'])

    def test_summary_includes_failures_cancelled_and_missing(self):
        matrix = matrix_generator.generate_build_matrix()[:4]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for cfg, status in zip(matrix, ['success', 'failure', 'cancelled']):
                name = f"{cfg['android']}-{cfg['kernel']}-{cfg['sub_level']}"
                (root / f'{name}.status').write_text(f'{name}:outcome={status}\n')
            with contextlib.redirect_stdout(io.StringIO()):
                counts = build_summary.summarize(root, root / 'summary.md', matrix, {})
            self.assertEqual(dict(success=1, failure=1, cancelled=1, missing=1), counts)
            self.assertIn('Total: 4', (root / 'summary.md').read_text())

    def test_collect_rejects_missing_outputs_and_empty_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'android13-5.10.198-2024-01-AnyKernel3.zip'
            result = root / 'result.json'
            data = {'total': 1, 'success': 1, 'results': [{'artifacts': [str(archive)],
                    'config': {'android_version': 'android13', 'kernel_version': '5.10', 'sub_level': '198'}}]}
            result.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                build_summary.collect(result, root / 'output')
            with zipfile.ZipFile(archive, 'w') as zf:
                zf.writestr('anykernel.sh', 'test')
            with self.assertRaises(ValueError):
                build_summary.collect(result, root / 'output')
            with zipfile.ZipFile(archive, 'w') as zf:
                zf.writestr('Image', b'test kernel')
            build_summary.collect(result, root / 'output')
            self.assertTrue((root / 'output' / archive.name).exists())
            self.assertTrue((root / 'output' / 'build-info-android13-5.10-198.json').exists())


if __name__ == '__main__':
    unittest.main()
