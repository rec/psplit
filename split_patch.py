#!/bin/env python3

import argparse
import fileinput
import itertools
import sys

from argparse import ArgumentParser, Namespace
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional
from typing_extensions import Never, TypeAlias

HELP = """
split_patch.py - split a git diff into multiple parts

TODO:

* tests!

(Supposedly done)
* git rm
* git mv, matching
* git mv, non-matching

"""

Chunk: TypeAlias = list[str]
FileChunks = list[Chunk]


def run(argv=None):
    args = _parse_args(argv)
    _check(args)
    _setup_directory(args.directory, args.clear)

    lines = fileinput.input(args.files)
    for file_chunk in _read(lines, args.parts, args.chunks):
        _write(file_chunk, args.join_character)

    if args.remove:
        for f in args.files:
            f.unlink()


def _check(args: Namespace) -> None:
    if args.chunks and args.parts:
        sys.exit("Only one of --chunks and --parts may be set")

    if args.remove and not args.files:
        sys.exit("--remove requires some file arguments")

    if sys.stdin.isatty() and not args.files:
        sys.exit("No input")


def _chunk(lines: Iterable[str]) -> list[FileChunks]:
    def chunk(it: Iterable[str], prefix: str) -> FileChunks:
        """Split a iteration of lines every time a line starts with `prefix`.

        The result is a list of Chunks, where in each Chunk except perhaps the first
        one, the first line starts with `prefix`.
        """
        result: FileChunks = []
        for line in it:
            if not result or result[-1] and line.startswith(prefix):
                result.append([])
            result[-1].append(line)
        return result

    return [chunk(fl, "@@") for fl in chunk(lines, "diff")]


def _is_splittable(chunks: FileChunks) -> bool:
    name = chunks[0][0][1].partition(" ")[0]
    assert name in ("new", "deleted", "index", "similarity"), (name, chunks[0][0])
    return name == "index"


def _parse_args(argv) -> Namespace:
    parser = _ArgumentParser()

    help = "A list of files to split (none means split stdin)"
    parser.add_argument("files", nargs="*", help=help)

    help = "Split, containing this many deltas"
    parser.add_argument("--chunks", "-c", default=0, type=int, help=help)

    help = "Clean --directory of patch files"
    parser.add_argument("--clean", action="store_true", help=help)

    help = "Output to this directory (create if necessary)"
    parser.add_argument("--directory", "-d", type=Path, default=Path(), help=help)

    help = "The character to replace / in filenames"
    parser.add_argument("--join-character", "-j", type=str, default="-", help=help)

    help = "Split into this many parts"
    parser.add_argument("--parts", "-p", default=0, type=int, help=help)

    help = "Remove original patch files at the end"
    parser.add_argument("--remove", action="store_true", help=help)

    return parser.parse_args(argv)


def _read(lines: Iterable[str], parts: int, chunks: int) -> Iterator[list[FileChunks]]:
    yield from (_split(s, parts, chunks) for s in _chunk(lines))


def _setup_directory(directory: Path, clear: bool) -> None:
    if not directory.exists():
        print(f"Creating {directory}/")
        directory.mkdir(parents=True, exist_ok=True)

    elif clear:
        for i in directory.iterdir():
            if i.suffix == ".patch":
                i.unlink()


def _split(patches: FileChunks, parts: int, chunks: int) -> list[FileChunks]:
    if not _is_splittable(patches):
        return [patches]

    head, patches = patches[:1], patches[1:]
    cut = chunks or parts or round(len(patches) ** 0.5)

    div, mod = divmod(len(patches), cut)
    div += bool(mod)
    count, step = (div, cut) if chunks else (cut, div)

    return [head + patches[step * i: step * (i + 1)] for i in range(count)]


def _write(files: list[FileChunks], join_character: str) -> None:
    diff, git, a, b = files[0][0][0].split()
    none, a, filename = a.partition("a/")
    assert not none and diff == "diff" and git == "--git", head

    for c in "/:~":
        filename = filename.replace(C, join_character)

    for i, p in enumerate(files):
        index = f"-{i + 1}" if len(files) > 1 else ""
        file = directory / f"{filename}{index}.patch"
        print("Writing", file, file=sys.stderr)
        file.write_text("".join(j for i in p for j in i))


class _ArgumentParser(ArgumentParser):
    def __init__(
        self,
        prog: Optional[str] = None,
        usage: Optional[str] = None,
        description: Optional[str] = None,
        epilog: Optional[str] = None,
        is_fixer: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(prog, usage, description, None, **kwargs)
        self._epilog = epilog

    def exit(self, status: int = 0, message: Optional[str] = None) -> Never:
        argv = sys.argv[1:]
        if self._epilog and not status and "-h" in argv or "--help" in argv:
            print(self._epilog)
        super().exit(status, message)


if __name__ == "__main__":
    run()
