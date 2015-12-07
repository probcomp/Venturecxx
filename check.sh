#!/bin/sh

set -Ceu

: ${PYTHON:=python}
: ${NOSETESTS:=`which nosetests`}

if [ ! -x "${NOSETESTS}" ]; then
    printf >&2 'unable to find nosetests\n'
    exit 1
fi

root=`cd -- "$(dirname -- "$0")" && pwd`

(
    set -Ceu
    cd -- "${root}"
    "$PYTHON" setup.py build
    if [ $# -eq 0 ]; then
        # By default, when running all tests, skip tests that have
        # been marked for continuous integration by using __ci_ in
        # their names.  (git grep __ci_ to find these.)
        ./pythenv.sh "$PYTHON" "$NOSETESTS" -c crashes.cfg test
    else
        # If args are specified, run all tests, including continuous
        # integration tests, for the selected components.
        ./pythenv.sh "$PYTHON" "$NOSETESTS" "$@"
    fi
)
