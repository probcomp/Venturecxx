#!/bin/sh

# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

set -ex

# Compute the version that will be built (tail skips warnings setup.py emits).
version=`python setup.py --version | tail -1`
version=${version%+*} # Strip the +foo suffix

# Build the distribution.
python setup.py sdist

# Install it in a fresh virtualenv
venv_dir=`mktemp -dt "jenkins-sdist-install.XXXXXXXXXX"`
virtualenv $venv_dir
. $venv_dir/bin/activate
pip install --find-links dist/ "Venture-CXX==$version"

# Smoke test the result without testing-only dependencies
./tool/check_capabilities.sh
if [ -z $SKIP_PUMA_BACKEND ]; then
    ./tool/check_capabilities.sh puma
else
    ! venture puma --abstract-syntax -e '(normal 0 1)'
fi

# Install the test dependencies.
pip install --find-links dist/ "Venture-CXX[tests]==$version"

# Test more thoroughly.
# TODO This should be the crash test suite.  Right now the only
# difference is that it skips test_analytics.py:testCompareSnapshots,
# and doesn't try to generate the coverage report.
nosetests -c unattended.cfg

# Clean up
/bin/rm -fr $venv_dir
