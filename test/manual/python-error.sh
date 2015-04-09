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
  An error in a Python script using Venture should produce complete
  information about what went wrong:
  - Python stack traces all the way from user code through the Venture
    implementation (including any parallel workers)
  - The Venture stack trace
  - The actual error message
  preferably in that order (so that the most useful things are the
  most salient, at the end of the output) and without duplication.
Rationale:
  For now we assume Python users are "advanced" or "developers" and
  want to see all that stuff.  We may wish at some point to add a
  programmatic switch for controlling whether the stack through the
  Venture implementation is shown (though showing the stack through
  the user's Python program will remain valuable).
----------------------------------------------------------------------

EOF
python -c "import venture.shortcuts as v; r = v.Lite().make_church_prime_ripl(); r.assume('x', '(normal 0 1)'); r.assume('x', '(gamma 1 1)')"
