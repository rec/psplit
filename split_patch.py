import argparse
import fileinput

from typing import Any, Iterable

import sys
from typing import Any, TypeAlias
from typing_extensions import Never


def run():
    parser = ArgumentParser()

    help = "A list of files to split (none means split stdin)"
    parser.add_argument("files", nargs="*", help=help)

    help = "Split, containing this many deltas"
    parser.add_argument("-c", "--chunk", default=0, type=int, help=help)

    help = "Split into this many parts"
    parser.add_argument("-p", "--parts", default=0, type=int, help=help)

    args = parser.parse_args()
    if args.chunks and args.parts:
        sys.exit("Only one of --chunks and --parts may be set")

    def split(it: Iterable[str], prefix: str) -> list[list[str]]:
        result: list[list[str]] = []
        for line in it:
            if line.startswith(prefix):
                if not result or result[-1]:
                    result.append([])
                result[-1].append(line)
        return result

    def join(patches: list[list[str]]) -> list[list[list[str]]]:
        lp = len(patches)
        cut = args.chunks or args.parts or round(lp ** 0.5)
        div, mod = divmod(lp, cut)
        div += bool(mod)
        count, step = (div, cut) if args.chunks else (cut, div)
        return [patches[step * i: step * (i + 1)] for i in range(count)]

    with fileinput.input(args.files) as f:
        for file_lines in split(itertools.chain.from_iterable(f), "diff"):
            head, *patches = split(file_lines, "@@")
            diff, git, a, b = head[0].split()
            none, a, filename = a.partition("a/")
            assert not none and diff == 'diff' and git = '--git', head

            filename = filename.replace("/", "-")  # TODO: more sanitizing
            for i, p in enumerate(patches):
                index = f"-{i}" if len(patches) > 1 else ""
                fname = f"{filename}{index}.patch"
                print(fname, file=sys.stderr)
                with open(fname, "w") as fp:
                    fp.writelines((*head, *p))


def _check_patches(all_patches):
    for file_patches in all_patches:
        for i, (head, *patch) in enumerate(file_patches):
            assert 3 <= len(head) <= 4  # Not sure 3 is possible, but...
            assert all(i[0].startswith("@@") for i in patch)


class ArgumentParser(argparse.ArgumentParser):
    def __init__(
        self,
        prog: str | None = None,
        usage: str | None = None,
        description: str | None = None,
        epilog: str | None = None,
        is_fixer: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(prog, usage, description, None, **kwargs)
        self._epilog = epilog

    def exit(self, status: int = 0, message: str | None = None) -> Never:
        argv = sys.argv[1:]
        if self._epilog and not status and "-h" in argv or "--help" in argv:
            print(self._epilog)
        super().exit(status, message)
