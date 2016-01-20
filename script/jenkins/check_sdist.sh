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

# UNUSED, PRESUMED STALE script for testing that Venture installs in a
# clean virtual env.  We moved to Docker for isolation of installation
# builds.

# Compute the version that will be built (tail skips warnings setup.py emits).
version=`python setup.py --version | tail -1`
version=${version%+*} # Strip the +foo suffix

# Save the version in the sdist, b/c git describe will not be available.
echo $version > VERSION

# Build the distribution.
python setup.py sdist

# Build a fresh virtualenv for it
venv_dir=`mktemp -dt "jenkins-sdist-install.XXXXXXXXXX"`
virtualenv $venv_dir
. $venv_dir/bin/activate

# Check it
./script/jenkins/check_built_sdist.sh dist/ $version

# Clean up
/bin/rm -fr $venv_dir
