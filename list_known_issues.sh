#!/bin/sh

# FIXME improve greps; include in particular seems dangerous; also why isn't this FIXME being found?

grep -r FIXME . | grep -v site-packages | grep -v Eigen | grep -v include | grep -v \.fish | grep -v build | grep -v git
