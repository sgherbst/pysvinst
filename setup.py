from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
import subprocess
import shutil

from pathlib import Path

name = 'svinst'
version = '0.1.0'

DESCRIPTION = '''\
Python library for parsing module definitions and instantiations from SystemVerilog files\
'''

class SvInstBuild(build_ext):
    def run(self):
        # get path to the directory where binaries should be installed
        ext = self.extensions[0]
        extdir = Path(self.get_ext_fullpath(ext.name)).resolve().parent
        extdir = extdir / 'svinst'
        extdir.mkdir(parents=True, exist_ok=True)

        # install the binary to the python package directory
        if shutil.which('cargo') is not None:
            subprocess.run(['cargo', 'install', 'svinst', '--root', str(extdir)])
        else:
            raise Exception('Rust is needed to build this package.  Please install it from https://www.rust-lang.org/tools/install')

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
    install_requires=[
        'PyYAML'
    ],
    # configure building of svinst binary
    ext_modules=[Extension('svinst', [])],
    cmdclass=dict(build_ext=SvInstBuild)
)
