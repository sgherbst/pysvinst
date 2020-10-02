#!/bin/bash

#
# adapted from https://github.com/pypa/python-manylinux-demo/blob/master/travis/build-wheels.sh
#

set -e -x

# Update yum
yum -y update

# List installed packages
yum list installed

# Install needed packages
yum -y install libyaml libyaml-devel

# Install Rust
curl https://sh.rustup.rs -sSf | sh -s -- -y
source $HOME/.cargo/env

# Update pip itself
"/opt/python/${PYVER}/bin/pip" install --upgrade --no-cache-dir pip

# Show tool versions
g++ -v
cmake --version

# Compile wheels
"/opt/python/${PYVER}/bin/pip" wheel /io/ -w wheelhouse/ -v

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/
done
