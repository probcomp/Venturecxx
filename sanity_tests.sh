#!/bin/sh

# Reset the working directory to the script's path
my_abs_path=$(readlink -f "$0")
my_dirname=$(dirname $my_abs_path)
cd "$my_dirname"

# Actually run the tests
cd backend/cxx
python -c "import wstests; wstests.runTests(10)"
cd ../..
echo FIXME test reporting causes some runtime errors to be missed, so watch output carefully
python -m unittest discover python/test/ "*.py"
