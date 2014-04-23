#!/bin/sh

# patch setup.py to use boost_*-mt libraries 
# (single-threaded versions are uninstalled by default on macports)
cat setup.py | /usr/bin/sed -e "s#'\(boost_[a-z]*\)'#'\1-mt'#g" > setup_osx_macports.py
# run patched setup.py
LDSHARED="gcc-mp-4.8 -Wl,-F. -bundle -undefined dynamic_lookup -L/opt/local/lib/" \
CFLAGS="" \
CC="ccache gcc-mp-4.8" \
CXX="g++-mp-4.8" \
	python setup_osx_macports.py install
