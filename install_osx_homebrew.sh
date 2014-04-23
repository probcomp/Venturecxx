#!/bin/sh
LDSHARED="gcc-4.8 -Wl,-F. -bundle -undefined dynamic_lookup -L/opt/local/lib/" CFLAGS="" CC="ccache gcc" python setup.py install
