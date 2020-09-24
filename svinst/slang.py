import sys
from pathlib import Path
import subprocess

def main():
    slang_path = Path(__file__).resolve().parent / 'bin' / 'slang'
    subprocess.run([str(slang_path)] + sys.argv[1:])

if __name__ == '__main__':
    main()