#!/bin/bash

cat <<EOF
----------------------------------------------------------------------
Test:
  $0
Expectation:
  An error should produce a nice user-level error description (in this
  case, double-definition of a variable), without excess noise that
  a user would not be able to interpret anyway.
----------------------------------------------------------------------

EOF
echo -e "assume x (normal 0 1)\nassume x (gamma 1 1)" | venture lite
