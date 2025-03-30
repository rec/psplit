#!/bin/env python3

import argparse
import fileinput
import itertools
import sys

from pathlib import Path
from typing import Any, Iterable, Optional
from typing_extensions import Never


def run():
    parser = ArgumentParser()

    help = "A list of files to split (none means split stdin)"
    parser.add_argument("files", nargs="*", help=help)

    help = "Split, containing this many deltas"
    parser.add_argument("-c", "--chunks", default=0, type=int, help=help)

    help = "Split into this many parts"
    parser.add_argument("-p", "--parts", default=0, type=int, help=help)

    help = "Output to this directory (create if necessary)"
    parser.add_argument("-d", "--directory", type=str, default="", help=help)

    args = parser.parse_args()
    if args.chunks and args.parts:
        sys.exit("Only one of --chunks and --parts may be set")

    def split(it: Iterable[str], prefix: str) -> list[list[str]]:
        result: list[list[str]] = []
        for line in it:
            if not result or (line.startswith(prefix) and result[-1]):
                result.append([])
            result[-1].append(line)
        return result

    def join(patches: list[list[str]]) -> list[list[list[str]]]:
        lp = len(patches)
        cut = args.chunks or args.parts or round(lp ** 0.5)
        div, mod = divmod(lp, cut)
        div += bool(mod)
        count, step = (div, cut) if args.chunks else (cut, div)
        print(f"{lp=}, {cut=}, {div=}, {mod=}, {count=}, {step=}")
        return [patches[step * i: step * (i + 1)] for i in range(count)]

    if not args.files and sys.stdin.isatty():
        sys.exit("No input")

    directory = Path(args.directory)
    if not directory.exists():
        print(f"Creating {directory}/")
        directory.mkdir(parents=True, exist_ok=True)

    all_lines = list(fileinput.input(args.files))
    for file_lines in split(all_lines, "diff"):
        files = join(split(file_lines, "@@"))
        diff, git, a, b = files[0][0][0].split()
        none, a, filename = a.partition("a/")
        assert not none and diff == 'diff' and git == '--git', head

        filename = filename.replace("/", "-")  # TODO: more sanitizing
        for i, p in enumerate(files):
            index = f"-{i + 1}" if len(files) > 1 else ""
            file = directory / f"{filename}{index}.patch"
            print(file, file=sys.stderr)
            file.write_text(''.join(j for i in p for j in i))


def _check_patches(all_patches):
    for file_patches in all_patches:
        for i, (head, *patch) in enumerate(file_patches):
            assert 3 <= len(head) <= 4  # Not sure 3 is possible, but...
            assert all(i[0].startswith("@@") for i in patch)


class ArgumentParser(argparse.ArgumentParser):
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


if __name__ == '__main__':
    run()
