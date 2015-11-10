#!/bin/sh

set -Ceu

run ()
{
  echo '#' "$@"
  time "$@"
}

outside ()
{
  run "$@"
}

inside ()
{
  run sudo env -i PATH=/sbin:/bin:/usr/sbin:/usr/bin chroot "$root" "$@"
}

root=`pwd`/root

clean ()
{
  sudo umount "$root"/proc || :
  sudo umount "$root"/sys || :
}

trap clean EXIT HUP INT TERM

# Compute the version that will be built (tail skips warnings setup.py emits).
version=`python setup.py --version | tail -1`

# Save the version in the sdist, b/c git describe will not be available.
echo $version > VERSION

# Build the distribution.
python setup.py sdist

# Prepare a chroot
if [ ! -d ./template ]; then
  outside sudo rm -rf ./template.tmp
  outside sudo debootstrap --components=main,universe trusty ./template.tmp
  outside sudo mv -f ./template.tmp ./template
fi
outside sudo rm -rf ./root
outside sudo mkdir -m 0755 ./root
outside sudo sh -c '(cd ./template && tar cf - .) | (cd $root && tar xpf -)'
outside sudo mount -t proc chroot-proc "$root"/proc
outside sudo mount -t sysfs chroot-sysfs "$root"/sys
inside apt-get --yes update
inside apt-get --yes install \
  libboost-python-dev \
  libboost-system-dev \
  libboost-thread-dev \
  libgsl0-dev \
  ccache \
  python-dev \
  python-matplotlib \
  python-numpy \
  python-pandas \
  python-scipy \
  python-virtualenv \
  python-zmq \
  # end of apt packages
inside virtualenv --system-site-packages /tmp/venv

# Copy the sdist file and its test script into the chroot
outside cp script/jenkins/check_built_sdist.sh "$root"/tmp
outside cp dist/venture-"$version" "$root"/tmp/

# Install and test it
inside sh -c '. /tmp/venv/bin/activate && cd /tmp/ && \
  ./check_built_sdist.sh . ${version%+*}' # Version without the +foo suffix
