#!/bin/sh

cd backend/cxx
python -c "import wstests; wstests.runTests(10)"
cd ../..
echo FIXME test reporting causes some runtime errors to be missed, so watch output carefully
python -m unittest discover python/test/ "*.py"
