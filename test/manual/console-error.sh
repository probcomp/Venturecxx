#!/bin/bash

# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

cat <<EOF
----------------------------------------------------------------------
Test:
  $0
Expectation:
  An error at the Venture console should produce a nice user-level
  error description (in this case, double-definition of a variable),
  without excess noise that a user would not be able to interpret
  anyway.
----------------------------------------------------------------------

EOF
echo -e "assume x (normal 0 1)\nassume x (gamma 1 1)" | venture lite
