from pathlib import Path
from unittest import TestCase

import split_patch as sp

PATCH_FILES = Path(__file__).parent / 'patches'
assert PATCH_FILES.exists()
PATCHES = sorted(PATCH_FILES.glob("*.patch"))
CONTENTS = {p: p.read_text().splitlines(keepends=True) for p in PATCHES}


class SplitPatchTest(TestCase):
    def test_chunking(self):
        for p, lines in CONTENTS.items():
            with self.subTest(path=p):
                chunks = sp._chunk(lines)
                if p.stem == "big":
                    first, second = chunks
                    self.assertEqual(len(first), 13)
                    self.assertEqual(len(second), 32)
                elif p.stem == 'mv':
                    chunk, = chunks
                    self.assertEqual(len(chunk), 1)
                else:
                    chunk, = chunks
                    self.assertEqual(len(chunk), 2)
