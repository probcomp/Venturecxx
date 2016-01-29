#!/bin/sh

# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

set -eu

docker_dir=$1

# Compute the version that will be built (tail skips warnings setup.py emits).
version=`python setup.py --version | tail -1`
dist_file_base="venture-$version"
dist_file="$dist_file_base.tar.gz"
dist_path="dist/$dist_file"

# Save the version in the sdist, b/c git describe will not be available.
echo $version > VERSION

# Build the distribution.
python setup.py sdist

# Prepare a Docker container

# - Clear out any stale venture distributions
rm -rf "script/jenkins/$docker_dir/dist/"

# - Make sure there is a venture distribution directory
mkdir -p "script/jenkins/$docker_dir/dist/"

# - Put the distribution there
cp "$dist_path" "script/jenkins/$docker_dir/dist/"

# - Actually build the container
docker build -t "venture-$docker_dir" script/jenkins/$docker_dir

# Run the acceptance testing in the container
docker run -t "venture-$docker_dir" /bin/sh -c "\
    tar -xzf $dist_path && \
    cd $dist_file_base && \
    test -f test/properties/test_sps.py && \
    ./script/jenkins/check_built_sdist.sh ../dist/ \
        ${version%+*}" # Version without the +foo suffix

# Extract the id of the last container with the appropriate name
# created on the machine, which I hope is the above
docker_id=`docker ps -a | grep venture-$docker_dir | head -1 | cut -f 1 -d ' '`
exit `docker wait "$docker_id"`
