import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import storage_budget as budget
from publish_en_posts import publish_image

class BudgetTests(unittest.TestCase):
    def test_threshold_boundaries(self):
        with contextlib.redirect_stdout(io.StringIO()):
            for size, expected in [(74, True), (75, True), (89, True), (90, False)]:
                self.assertEqual(budget.check_budget(size, 75, 90, 'test'), expected)
            with self.assertRaises(ValueError):
                budget.check_budget(0, 90, 75, 'test')

    def test_measures_generated_files_and_blocks(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            out = Path(tmp)
            (out / 'index.html').write_bytes(b'a' * 6)
            (out / 'sitemap.xml').write_bytes(b'b' * 4)
            with patch.object(budget, 'SITE_WARN', 8), patch.object(budget, 'SITE_LIMIT', 10):
                self.assertFalse(budget.check_site(out))

    def test_index_gross_growth_counts_duplicates_once(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL)
            git('init'); git('config', 'user.name', 'Test'); git('config', 'user.email', 'test@example.org')
            (root / 'old').write_bytes(b'a' * 30)
            git('add', '.'); git('commit', '-m', 'initial')
            (root / 'old').unlink()
            (root / 'new').write_bytes(b'b' * 15)
            (root / 'copy').write_bytes(b'b' * 15)
            git('add', '-A')
            with patch.object(budget, 'GROWTH_WARN', 10), patch.object(budget, 'GROWTH_LIMIT', 15):
                self.assertFalse(budget.report(root, staged=True))
            self.assertEqual(git('rev-list', '--count', 'HEAD').strip(), b'1')

    def test_copy_identical_bytes_does_not_touch_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); src = root / 'src.webp'; dst = root / 'dst.webp'
            src.write_bytes(b'same'); dst.write_bytes(b'same')
            import os
            os.utime(dst, (1, 1))
            self.assertFalse(publish_image(src, dst))
            self.assertEqual(dst.stat().st_mtime, 1)

if __name__ == '__main__':
    unittest.main()
