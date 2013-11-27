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
cd backend/cxx
python -c "import wstests; wstests.runAllTests(1)" > /dev/null
abort_on_error "engine self-checking"

cd ../..
python -m unittest discover python/test/ "*.py"
abort_on_error "periphery self-checking"

set -o pipefail # Preserve exit status of venture, per http://stackoverflow.com/questions/6871859/piping-command-output-to-tee-but-also-save-exit-code-of-command
echo "assume x (uniform_continuous 0.0 0.9)" | venture | grep '>>> 0.'
abort_on_error "executing the venture command"

timeout 1.5s python examples/lda.py
if [[ $? -ne "124" ]]; then
    echo FAILED: running python examples/lda.py
    exit 1
fi

timeout 1.5s python examples/crosscat.py
if [[ $? -ne "124" ]]; then
    echo FAILED: running python examples/crosscat.py
    exit 1
fi
