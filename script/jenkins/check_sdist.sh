#!/bin/sh

set -ex

# Build the grammar files if needed, for clean output when detecting
# the version.
python setup.py --version

# Compute the name of the distribution file.
version=`python setup.py --version`
dist_name="Venture-CXX-$version.tar.gz"

# Build the distribution.
python setup.py sdist

# Install it in a fresh virtualenv
venv_dir=`mktemp -dt "jenkins-sdist-install.XXXXXXXXXX"`
virtualenv $venv_dir
. $venv_dir/bin/activate
pip install "dist/$dist_name"

# Test the result
./verifyinstall.sh

# Clean up
/bin/rm -fr $venv_dir
