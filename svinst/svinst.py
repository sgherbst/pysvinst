import sys
from pathlib import Path
import subprocess

def main():
    svinst_path = Path(__file__).resolve().parent / 'svinst'
    subprocess.call([str(svinst_path)] + sys.argv[1:])

if __name__ == '__main__':
    main()