#!/bin/sh

set -eu

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
rm -rf script/jenkins/debian-test-docker/dist/

# - Make sure there is a venture distribution directory
mkdir -p script/jenkins/debian-test-docker/dist/

# - Put the distribution there
cp "$dist_path" script/jenkins/debian-test-docker/dist/

# - Actually build the container
docker build -t "venture-debian-test" script/jenkins/debian-test-docker

# Run the acceptance testing in the container
docker run -t "venture-debian-test" /bin/sh -c "\
    tar -xzf $dist_path && \
    cd $dist_file_base && \
    test -f test/properties/test_sps.py && \
    ./script/jenkins/check_built_sdist.sh ../dist/ \
        ${version%+*}" # Version without the +foo suffix

# Extract the id of the last container created on the machine, which I
# hope is the above
docker_id=`docker ps -a | head -2 | tail -1 | cut -f 1 -d ' '`
exit `docker wait "$docker_id"`
