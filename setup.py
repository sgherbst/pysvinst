from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
import os
import platform
import subprocess
import shutil

from pathlib import Path

name = 'svinst'
version = '0.1.7.dev13'

DESCRIPTION = '''\
Python library for parsing module definitions and instantiations from SystemVerilog files\
'''

class BinaryBuild(build_ext):
    def run(self):
        self.build_slang_binary()
        self.build_svinst_binary()

    @property
    def extdir(self):
        ext = self.extensions[0]
        retval = Path(self.get_ext_fullpath(ext.name)).resolve().parent
        retval = retval / 'svinst'
        return retval

    def build_svinst_binary(self):
        # get path to the directory where binaries should be installed
        self.extdir.mkdir(parents=True, exist_ok=True)

        # install the binary to the python package directory
        if shutil.which('cargo') is not None:
            subprocess.run(['cargo', 'install', 'svinst', '--root', str(self.extdir)])
        else:
            raise Exception(
                'Rust is needed to build this package.  '
                'Please install it from https://www.rust-lang.org/tools/install'
            )

    def build_slang_binary(self):
        # checkout slang
        if shutil.which('git') is None:
            raise Exception('git is needed to check out the slang source code.')
        subprocess.run([
            'git', 'clone',
            '-b', 'v0.4',
            '--single-branch',
            '--depth', '1',
            'https://github.com/MikePopoloski/slang.git'
        ])

        # go to the build directory
        cwd = Path(os.getcwd()).resolve()
        build = cwd / 'slang' / 'build'
        build.mkdir(parents=True, exist_ok=True)
        os.chdir(str(build))

        # run cmake
        if shutil.which('cmake') is None:
            raise Exception('cmake is needed to build the slang binary.')

        cmake_args = []
        cmake_args += ['cmake']
        if platform.system() != 'Darwin':
            cmake_args += ['-DSTATIC_BUILD=ON']
        cmake_args += ['-DCMAKE_BUILD_TYPE=Release']
        if platform.system() == 'Darwin':
            cmake_args += ['-DCMAKE_CXX_COMPILER=g++-9']
        cmake_args += ['..']
        subprocess.run(cmake_args)

        # run make
        if shutil.which('make') is None:
            raise Exception('git is needed to build the slang binary.')
        subprocess.run([
            'make', '-j8'
        ])

        # go back to the starting directory
        os.chdir(str(cwd))

        # copy the binary to the install location
        (self.extdir / 'bin').mkdir(parents=True, exist_ok=True)
        shutil.copy(str(build / 'bin' / 'slang'),
                    str(self.extdir / 'bin' / 'slang'))


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
    # create command-line script to run svinst and slang binaries
    entry_points={
        'console_scripts': [
            'svinst=svinst.svinst:main',
            'slang=svinst.slang:main'
        ]
    },
    install_requires=[
        'PyYAML'
    ],
    # configure building of svinst binary
    ext_modules=[
        Extension('svinst', []),
        Extension('slang', [])
    ],
    cmdclass=dict(build_ext=BinaryBuild)
)
