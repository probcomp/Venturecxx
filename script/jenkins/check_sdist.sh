#!/bin/sh

set -ex

# Build the grammar files if needed, for clean output when detecting
# the version.
python setup.py --version

# Compute the version that will be built.
version=`python setup.py --version`
version=${version%+*} # Strip the +foo suffix

# Build the distribution.
python setup.py sdist

# Install it in a fresh virtualenv
venv_dir=`mktemp -dt "jenkins-sdist-install.XXXXXXXXXX"`
virtualenv $venv_dir
. $venv_dir/bin/activate
pip install --find-links dist/ "Venture-CXX==$version"

# Smoke test the result without testing-only dependencies (copied from
# verifyinstall.sh)
# TODO This should be a separate script, and should exercise all the
# major functions.
venture lite --abstract-syntax -e '[infer (bind (collect (normal 0 1)) printf)]'

# Install the test dependencies.
pip install --find-links dist/ "Venture-CXX[tests]==$version"

# Test more thoroughly (copied from verifyinstall.sh).
# TODO Should this be the crash test suite?
nosetests -c unattended.cfg

# Clean up
/bin/rm -fr $venv_dir
