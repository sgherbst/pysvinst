from pathlib import Path

def is_single_file(files):
    return isinstance(files, (str, Path))
