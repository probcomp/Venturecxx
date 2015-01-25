#!/bin/bash

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

if [ -z $1 ]; then
    backend="puma"
else
    backend=$1
fi

# Actually run the tests
echo "Sanity-checking the $backend backend.  This may take several minutes"
nosetests -c crashes.cfg --tc=get_ripl:$backend
abort_on_error "$backend backend self-checking"
echo "Sanity-checked $backend backend.  You may wish to try the other one by supplying an appropriate argument to this script."
