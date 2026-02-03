import contextlib
import filecmp
import shutil
from io import StringIO
from pathlib import Path
from unittest import TestCase

import tdir

import psplit

PARENT = Path(__file__).parent.parent
PATCH_FILES = PARENT / 'patches'
assert PATCH_FILES.exists()
EXPECTED = PARENT / 'test_expected'
PATCHES = sorted(PATCH_FILES.glob('*.patch'))
CONTENTS = {p: p.read_text().splitlines(keepends=True) for p in PATCHES}
ADD, BIG, EDIT, MV, REMOVE = CONTENTS.values()
BIG_PATCH = PATCH_FILES / 'big.patch'


class SplitPatchTest(TestCase):
    def test_add(self):
        (hunks,) = psplit.FileHunks.read(ADD, 0, 0)
        (hunk,) = hunks
        self.assertEqual(len(hunk.hunks), 1)
        self.assertEqual(
            hunk.hunks[0], ['@@ -0,0 +1,3 @@\n', '+three\n', '+four\n', '+five\n']
        )
        self.assertFalse(hunk.is_splittable)

    def test_mv(self):
        (hunks,) = psplit.FileHunks.read(MV, 0, 0)
        (hunk,) = hunks
        self.assertEqual(len(hunk.hunks), 0)
        self.assertFalse(hunk.is_splittable)

    def test_remove(self):
        (hunks,) = psplit.FileHunks.read(REMOVE, 0, 0)
        (hunk,) = hunks
        self.assertEqual(len(hunk.hunks), 1)
        self.assertFalse(hunk.is_splittable)

    def test_edit(self):
        (hunks,) = psplit.FileHunks.read(EDIT, 0, 0)
        (hunk,) = hunks
        self.assertEqual(len(hunk.hunks), 1)
        self.assertTrue(hunk.is_splittable)

    def test_big(self):
        hunks = psplit.FileHunks.read(BIG, 0, 0)
        self.assertEqual([len(d) for d in hunks], [3, 6])

    def test_big_1(self):
        hunks = psplit.FileHunks.read(BIG, 1, 0)
        self.assertEqual([len(d) for d in hunks], [1, 1])

    def test_big_2(self):
        hunks = psplit.FileHunks.read(BIG, 0, 1)
        self.assertEqual([len(d) for d in hunks], [12, 31])

    @tdir
    def test_integration(self):
        Path('patches').mkdir()
        with StringIO() as out:
            with contextlib.redirect_stderr(out):
                psplit.main(['-d', 'patches', str(BIG_PATCH)])
            actual = out.getvalue().splitlines()
            expected = [
                'Writing patches/torch-_inductor-ir.py-1.patch',
                'Writing patches/torch-_inductor-ir.py-2.patch',
                'Writing patches/torch-_inductor-ir.py-3.patch',
                'Writing patches/torch-_inductor-br.py-1.patch',
                'Writing patches/torch-_inductor-br.py-2.patch',
                'Writing patches/torch-_inductor-br.py-3.patch',
                'Writing patches/torch-_inductor-br.py-4.patch',
                'Writing patches/torch-_inductor-br.py-5.patch',
                'Writing patches/torch-_inductor-br.py-6.patch',
            ]
            self.assertEqual(actual, expected)

        if EXPECTED.exists():
            c = filecmp.dircmp(EXPECTED, 'patches')
            if c.left_only or c.right_only or c.diff_files:
                c.report()
                self.assertEqual(
                    (c.left_only, c.right_only, c.diff_files), ([], [], [])
                )
        else:
            shutil.copytree('patches', str(EXPECTED))
