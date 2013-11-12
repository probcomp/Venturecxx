#!/bin/sh

# Reset the working directory to the script's path
my_abs_path=$(readlink -f "$0")
my_dirname=$(dirname $my_abs_path)
cd "$my_dirname"

# Actually run the tests
cd python/test
python -c "import sivm_correctness_tests; sivm_correctness_tests.runTests(10, '$1')"
cd ../..
echo FIXME test reporting causes some runtime errors to be missed, so watch output carefully
python -m unittest discover python/test/ "*.py"
