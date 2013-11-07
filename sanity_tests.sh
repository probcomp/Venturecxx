#!/bin/sh

cd backend/cxx
python -c "import wstests; wstests.runTests(10)"
cd ../..
python -m unittest discover python/test/ "*.py"
