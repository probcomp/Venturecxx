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

# Actually run the tests
echo "This may take several minutes"
nosetests -c crashes.cfg --tc=get_ripl:$1
abort_on_error "engine self-checking"
