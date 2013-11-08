#!/bin/sh
CFLAGS="" CC="ccache gcc" python setup.py build
sudo python setup.py install
