#!/bin/sh

# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

set -Ceu

: ${PYTHON:=python}
root=`cd -- "$(dirname -- "$0")" && pwd`
platform=`"${PYTHON}" -c 'import distutils.util as u; print u.get_platform()'`
version=`"${PYTHON}" -c 'import sys; print sys.version[0:3]'`


# The lib directory varies depending on
#
# (a) whether there are extension modules (here, no); and
# (b) whether some Debian maintainer decided to patch the local Python
# to behave as though there were.
#
# But there's no obvious way to just ask distutils what the name will
# be.  There's no harm in naming a pathname that doesn't exist, other
# than a handful of microseconds of runtime, so we'll add both.
libdir="${root}/build/lib"
plat_libdir="${libdir}.${platform}-${version}"
export PYTHONPATH="${libdir}:${plat_libdir}${PYTHONPATH:+:${PYTHONPATH}}"

bindir="${root}/build/scripts-${version}"
export PATH="${bindir}${PATH:+:${PATH}}"

exec "$@"
