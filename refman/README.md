Venture Reference Manual Sources
================================

Significant chunks of the actual reference documentation are extracted
from in-source descriptions of various entities using the `vendoc`
program.

To build
--------

- _Reinstall Venture_
- `rm -f *.gen && make html` in this directory

The `rm` is currently needed, because the Makefile doesn't know where
in the Venture source the documentation strings are extracted from.

To upload to the CSAIL web space
--------------------------------

- `scp -r _build/html/* login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/edge/reference/`

N.B. Can also use rsync
