#!/bin/bash
gcc -shared -fPIC -O3 -o pypy_lib.so util.c toms322.c
