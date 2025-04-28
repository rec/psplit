#!/usr/bin/env python3

import fileinput
import math
import sys

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence
from typing_extensions import Never, TypeAlias

HELP = "✂️ `psplit`: Split git patch files ✂️"

EPILOG = """
`psplit` is a utility to split large git patch files. It is a single file
with no dependencies except Python 3.9 or greater.

`psplit` splits its inputs by file, then each file is split into one or more
patches. Each output patch file gets a unique name derived from the
underlying file name.

To avoid clutter, use the `--directory`/`-d` flag, which creates a
subdirectory if needed and puts the new patches in it.

If you set `--parts/-p`, `psplit` will split each file into that many parts:
each file gets the same number of parts.

If you set `--hunks/-u`, `psplit` will split each file into parts containing
that many hunks: larger files will get more parts.

(A hunk is a small, self-contained delta for a single text file.  A patch
contains zero or more files, each file containing one or more hunks.)

If neither flag is set, `psplit` will use the square root of the number of
hunks in the file, the geometric median between all the hunks in one part
and one hunk per part.
"""

NON_FILE_CHARS = "/:~"

Hunk: TypeAlias = list[str]


def main(argv=None):
    args = _parse_args(argv)
    _check(args)
    _setup_directory(args.directory, args.clean)

    lines = fileinput.input(args.files)
    for file_hunks in FileHunks.read(lines, args.parts, args.hunks):
        file_hunks.write(args.directory, args.join_character)


def _check(args: Namespace) -> None:
    if args.parts and args.hunks:
        sys.exit("Only one of --parts and --hunks may be set")

    if sys.stdin.isatty() and not args.files:
        sys.exit("No input")

    if args.join_character in NON_FILE_CHARS:
        sys.exit(f"--join-character had a character from {NON_FILE_CHARS=}")


class FileHunk:
    def __init__(self, head: Hunk, *hunks: Hunk) -> None:
        assert all(hunks), hunks
        assert all(isinstance(i, list) for i in hunks), hunks
        assert len(head) in (4, 5), head
        diff, command, *_ = head
        diff, git, a, b = diff.split()
        assert diff == "diff" and git == "--git", head

        command = command.split()[0]
        assert command in ("new", "deleted", "index", "similarity"), (command, hunks)

        none, _a, self.filename = a.partition("a/")
        none_b, _b, filename_b = b.partition("b/")
        assert _a and _b and not none and not none_b and self.filename and filename_b, (
            head, hunks
        )
        assert (not hunks) == (command == "similarity"), (command, hunks)

        self.is_splittable = command == "index"
        self.head, self.hunks = head, hunks

    def split(self, parts: int, hunks: int) -> "FileHunks":
        cut = hunks or parts or round(math.sqrt(len(self.hunks))) or 1

        div, mod = divmod(len(self.hunks), cut)
        div += bool(mod)
        count, step = (div, cut) if hunks else (cut, div)

        pieces = [self.hunks[step * i : step * (i + 1)] for i in range(count)]
        return FileHunks([self.head, *p] for p in pieces)

    def write(self, file: Path) -> None:
        with file.open("w") as fp:
            fp.writelines(self.head)
            for d in self.hunks:
                fp.writelines(d)


class FileHunks(list[FileHunk]):
    def __init__(self, hunks: Iterable[Sequence[Hunk]]) -> None:
        return super().__init__(FileHunk(*c) for c in hunks)

    @staticmethod
    def hunk(lines: Iterable[str]) -> "FileHunks":
        def hunk(it: Iterable[str], prefix: str) -> list[list[str]]:
            """Split a iteration of lines every time a line starts with `prefix`.

            The result is a list of Hunks, where in each Hunk except perhaps the first
            one, the first line starts with `prefix`.
            """
            result: list[list[str]] = []
            for line in it:
                if not result or result[-1] and line.startswith(prefix):
                    result.append([])
                result[-1].append(line)
            return result

        return FileHunks(hunk(fl, "@@") for fl in hunk(lines, "diff"))

    @staticmethod
    def read(lines: Iterable[str], parts: int, hunks: int) -> list["FileHunks"]:
        return [c.split(parts, hunks) for c in FileHunks.hunk(lines)]

    def write(self, directory: Path, join_character: str) -> None:
        filename = self[0].filename
        for c in NON_FILE_CHARS:
            filename = filename.replace(c, join_character)

        for i, fd in enumerate(self):
            index = f"-{i + 1}" if len(self) > 1 else ""
            file = directory / f"{filename}{index}.patch"
            print("Writing", file, file=sys.stderr)
            fd.write(file)


def _parse_args(argv) -> Namespace:
    parser = _ArgumentParser()

    help = "Files to split (or split stdin if no files)"
    parser.add_argument("files", nargs="*", help=help)

    help = "Output to this directory (create if needed)"
    parser.add_argument("--directory", "-d", type=Path, default=Path(), help=help)

    help = "Split into parts containing this many hunks"
    parser.add_argument("--hunks", "-u", default=0, type=int, help=help)

    help = f"The character replacing '{NON_FILE_CHARS}' in patch filenames"
    parser.add_argument("--join-character", "-j", type=str, default="-", help=help)

    help = "Split into this many parts"
    parser.add_argument("--parts", "-p", default=0, type=int, help=help)

    return parser.parse_args(argv)


def _setup_directory(directory: Path, clean: bool) -> None:
    if not directory.exists():
        print(f"Creating {directory}/")
        directory.mkdir(parents=True, exist_ok=True)

    elif clean:
        for i in directory.iterdir():
            if i.suffix == ".patch":
                i.unlink()


class _ArgumentParser(ArgumentParser):
    def __init__(
        self,
        prog: Optional[str] = None,
        usage: Optional[str] = None,
        description: Optional[str] = HELP,
        epilog: Optional[str] = EPILOG,
        is_fixer: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(prog, usage, description, None, **kwargs)
        self._epilog = epilog

    def exit(self, status: int = 0, message: Optional[str] = None) -> Never:
        argv = sys.argv[1:]
        if self._epilog and not status and ("-h" in argv or "--help" in argv):
            print(self._epilog)
        super().exit(status, message)


if __name__ == "__main__":
    main()
