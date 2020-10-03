import subprocess
import sys
import yaml
from pathlib import Path

from .util import is_single_file

def call_sv_parser(files, includes=None, defines=None, ignore_include=False,
                   full_tree=False, separate=False):
    # set defaults
    if includes is None:
        includes = []
    if defines is None:
        defines = {}

    # wrap files if needed
    if is_single_file(files):
        files = [files]

    # prepare arguments
    args = [Path(__file__).resolve().parent / 'bin' / 'svinst']
    args += files
    for k, v in defines.items():
        if v is not None:
            args += ['-d', f'{k}={v}']
        else:
            args += ['-d', f'{k}']
    for elem in includes:
        args += ['-i', f'{elem}']
    if ignore_include:
        args += ['--ignore-include']
    if full_tree:
        args += ['--full-tree']
    if separate:
        args += ['--separate']

    # convert arguments to strings
    args = [str(elem) for elem in args]

    # call command
    result = subprocess.run(args, capture_output=True, encoding='utf-8')
    if result.returncode != 0:
        print(f'{result.stderr}', file=sys.stderr)
        raise Exception(f'svinst returned code {result.returncode}.')

    # parse output as YAML
    return yaml.safe_load(result.stdout)
