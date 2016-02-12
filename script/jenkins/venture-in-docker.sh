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
requirements_file=${2:-}
image_tag=${BUILD_NUMBER:-0}

# Compute the version that will be built (tail skips warnings setup.py emits).
version=`python setup.py --version | tail -1`
dist_file_base="venture-$version"
dist_file="$dist_file_base.tar.gz"
dist_path="dist/$dist_file"

image_name="venture-$docker_dir:$image_tag"

# Save the version in the sdist, b/c git describe will not be available.
echo $version > VERSION

# Build the distribution.
python setup.py sdist

# Prepare a Docker image definition

# - Clear out any stale venture distributions
rm -rf "script/jenkins/$docker_dir/dist/"

# - Make sure there is a venture distribution directory
mkdir -p "script/jenkins/$docker_dir/dist/"

# - Put the distribution there
cp "$dist_path" "script/jenkins/$docker_dir/dist/"

# - If given, put the requirements file there
if [ ! -z $requirements_file ]; then
    cp "$requirements_file" "script/jenkins/$docker_dir/dist/requirements.txt"
fi

# - Write a script that will run tests from inside the container and
#   put it in the distribution directory
cat <<EOF > "script/jenkins/$docker_dir/dist/tests_run.sh"
#!/bin/sh
tar -xzf $dist_path && \
cd $dist_file_base && \
test -f test/properties/test_sps.py && \
./script/jenkins/check_built_sdist.sh ../dist/ \
    ${version%+*} # Version without the +foo suffix
EOF
chmod +x "script/jenkins/$docker_dir/dist/tests_run.sh"

cat <<EOF > "script/jenkins/$docker_dir/dist/run.sh"
#!/bin/sh
./dist/tests_run.sh
echo $? > exit_status
EOF
chmod +x "script/jenkins/$docker_dir/dist/run.sh"

# Actually build a docker image containing the results of installing
# and testing Venture.  (Not a container because containers are
# transient and I want to be able to inspect these if the tests fail)
docker build -t "$image_name" script/jenkins/$docker_dir

# Tell the user what image stuff happened in
echo "Tests run in $image_name"

# Extract the exit code of the test run.
exit `docker run -t "$image_name" cat exit_status`
