#!/bin/bash

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
