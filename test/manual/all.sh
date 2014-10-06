#!/bin/bash

# Reset the working directory to the directory of the script's path
my_abs_path=$(readlink -f "$0")
root_dirname=$(dirname $my_abs_path)
cd $root_dirname

echo "Running all the test scripts in $root_dirname:"
ls *.sh | grep -v all.sh
ls *.sh | grep -v all.sh | xargs -l bash
