#!/bin/sh

# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

# patch setup.py to use boost_*-mt libraries 
# (single-threaded versions are uninstalled by default on macports)
cat setup.py | /usr/bin/sed -e "s#'\(boost_[a-z]*\)'#'\1-mt'#g" > setup_osx_macports.py
# run patched setup.py
LDSHARED="gcc-mp-4.8 -Wl,-F. -bundle -undefined dynamic_lookup -L/opt/local/lib/" \
CFLAGS="" \
CC="ccache gcc-mp-4.8" \
CXX="g++-mp-4.8" \
	python setup_osx_macports.py install
