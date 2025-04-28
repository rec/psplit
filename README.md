# ✂️ `psplit`: Split git patch files ✂️

## Usage

```
psplit [-h. --help]
       [-c, --clean]
       [-d, --directory DIRECTORY]
       [-h, --hunks HUNKS]
       [-j, --join-character JOIN_CHARACTER]
       [-p, --parts PARTS]
       [files ...]
```

### Positional arguments
```
  files                 Files to split (or split stdin if no files)
```

### Optional arguments

```
  -h, --help            show this help message and exit
  --clean               Clean --directory of patch files
  --directory DIRECTORY, -d DIRECTORY
                        Output to this directory (create if needed)
  --hunks HUNKS, -u HUNKS
                        Split into parts containing this many hunks
  --join-character JOIN_CHARACTER, -j JOIN_CHARACTER
                        The character to replace / in filenames
  --parts PARTS, -p PARTS
                        Split into this many parts
```

## How it works

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

## Example

```
$ g diff HEAD~ | psplit -d patches
Creating patches/
Writing patches/tools-linter-adapters-_linter.py.patch
Writing patches/tools-linter-adapters-_linter-__init__.py.patch
Writing patches/tools-linter-adapters-_linter-argument_parser.py.patch
Writing patches/tools-linter-adapters-_linter-block.py.patch
Writing patches/tools-linter-adapters-_linter-blocks.py.patch
Writing patches/tools-linter-adapters-_linter-bracket_pairs.py.patch
Writing patches/tools-linter-adapters-_linter-file_linter.py.patch
Writing patches/tools-linter-adapters-_linter-file_summary.py.patch
Writing patches/tools-linter-adapters-_linter-messages.py.patch
Writing patches/tools-linter-adapters-_linter-python_file.py.patch
Writing patches/tools-linter-adapters-_linter-sets.py.patch
Writing patches/tools-linter-adapters-docstring_linter.py-1.patch
Writing patches/tools-linter-adapters-docstring_linter.py-2.patch
Writing patches/tools-linter-adapters-docstring_linter.py-3.patch
Writing patches/tools-linter-adapters-set_linter.py-1.patch
Writing patches/tools-linter-adapters-set_linter.py-2.patch
Writing patches/tools-test-test_docstring_linter.py.patch
```

## How to install

Either use `pip`: `python -m pip install psplit`. Or simply download the file
`psplit.py` and put it into your path.


## Other alternatives

https://manpages.ubuntu.com/manpages/xenial/man1/splitpatch.1.html didn't work
well for large files and isn't available on Mac OS

https://pypi.org/project/splitpatch/ is complicated and very new
