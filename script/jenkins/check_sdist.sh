#!/bin/sh

set -ex

version=`python setup.py --version`
dist_name="Venture-CXX-$version.tar.gz"
python setup.py sdist

venv_dir=`mktemp -dt "jenkins-sdist-install.XXXXXXXXXX"`
virtualenv $venv_dir
. $venv_dir/bin/activate
pip install "dist/$dist_name"
verifyinstall.sh
/bin/rm -fr $venv_dir
