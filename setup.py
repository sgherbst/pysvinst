from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
import subprocess

from pathlib import Path
import shutil

name = 'svinst'
version = '0.0.1'

DESCRIPTION = '''\
Python library for parsing module definitions and instantiations from SystemVerilog files\
'''

SVINST_PATH = "svinst-rust"
SVINST_REPO = "https://github.com/sgherbst/svinst"
SVINST_NAME = "svinst"
SVINST_BRANCH = "master"

def check_call(lis, *args, **kwargs):
    # minimal wrapper around subprocess check_call function that
    # ensures all arguments are strings.  this makes it easier to
    # pass numbers, paths, etc. as arguments
    lis = [str(elem) for elem in lis]
    subprocess.check_call(lis, *args, **kwargs)

class SvInstBuild(build_ext):
    def run(self):
        # get path to the directory where binaries should be installed
        ext = self.extensions[0]
        extdir = Path(self.get_ext_fullpath(ext.name)).resolve().parent
        extdir = extdir / SVINST_NAME
        extdir.mkdir(parents=True, exist_ok=True)

        if not Path(SVINST_PATH).is_dir():
            check_call(['git', 'clone', '--depth=1', '--branch',
                        SVINST_BRANCH, SVINST_REPO, SVINST_PATH])
        build_dir = Path(SVINST_PATH)

        # build the binary
        check_call(['cargo', 'build', '--release'], cwd=build_dir)

        # copy libraries over

        bin_file = list(build_dir.glob('target/*/svinst'))
        if len(bin_file) == 0:
            raise Exception('Could not find binary file for svinst.')
        elif len(bin_file) > 1:
            raise Exception('Multiple matches for svinst binary: ' + str(bin_file))
        else:
            shutil.copy(bin_file[0], extdir)

with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()

setup(
    name=name,
    version=version,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords = ['verilog', 'system-verilog', 'system verilog', 'parse', 'parser', 'parsing', 'module', 'modules',
                'definition', 'definitions', 'instantation', 'instantiations'],
    packages=find_packages(exclude=['tests']),
    license='MIT',
    url=f'https://github.com/sgherbst/{name}',
    author='Steven Herbst',
    author_email='sgherbst@gmail.com',
    python_requires='>=3.7',
    download_url = f'https://github.com/sgherbst/{name}/archive/v{version}.tar.gz',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'License :: OSI Approved :: MIT License',
        f'Programming Language :: Python :: 3.7'
    ],
    include_package_data=True,
    zip_safe=False,
    # create command-line script to run svinst binary
    entry_points={
        'console_scripts': [
            'svinst=svinst.svinst:main'
        ]
    },
    # configure building of svinst binary
    ext_modules=[Extension('svinst', [])],
    cmdclass=dict(build_ext=SvInstBuild)
)
