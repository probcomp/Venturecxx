#!/bin/bash

# Reset the working directory to the script's path
my_abs_path=$(readlink -f "$0")
my_dirname=$(dirname $my_abs_path)
cd "$my_dirname"

set -xe
venture lite -e '[infer (printf (normal 0 1))]'
./sanity_tests.sh
