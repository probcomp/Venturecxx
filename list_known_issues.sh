#!/bin/sh

grep -r FIXME . | grep -v site-packages | grep -v Eigen | grep -v include | grep -v fish | grep -v build
