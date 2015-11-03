#!/bin/bash

# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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
my_abs_path=$(readlink -f "$0")
my_dirname=$(dirname $my_abs_path)
cd "$my_dirname"

set -xe
venture lite --abstract-syntax -e '[infer (bind (collect (normal 0 1)) printf)]'
nosetests -c unattended.cfg
