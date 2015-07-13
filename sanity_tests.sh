#!/bin/bash

# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

# Reset the working directory to the script's path
cd $(dirname "$0")

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
