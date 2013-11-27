#!/bin/sh

# Reset the working directory to the script's path
my_abs_path=$(readlink -f "$0")
my_dirname=$(dirname $my_abs_path)
cd "$my_dirname"

function abort_on_error () {
    if [[ $? -ne "0" ]]; then
        echo FAILED: $1
        exit 1
    fi
}

# Actually run the tests
cd backend/cxx
python -c "import wstests; wstests.runAllTests(10)"
abort_on_error "engine self-checking"

cd ../..
echo FIXME test reporting causes some runtime errors to be missed, so watch output carefully
python -m unittest discover python/test/ "*.py"
abort_on_error "periphery self-checking"
