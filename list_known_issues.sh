#!/bin/sh

echo in list_known_issues FIXME improve greps, as include in particular seems dangerous

grep -r FIXME . | grep -v site-packages | grep -v Eigen | grep -v include | grep -v \.fish | grep -v build | grep -v git
