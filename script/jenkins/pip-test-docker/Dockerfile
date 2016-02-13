# Copyright (c) 2014, MIT Probabilistic Computing Project.
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

# Dockerfile for testing Venture's dependency list in an isolated
# environment.

# Emulating the pip-major installation strategy (getting Python
# software from pip, and just Debian-only dependencies thereof from
# Debian).

FROM        ubuntu:14.04

MAINTAINER  MIT Probabilistic Computing Project

# Setup
RUN         apt-get update # again
RUN         apt-get install -y emacs python-pip
RUN         pip install -U distribute

# Puma's dependencies
RUN         apt-get install -y libboost-all-dev libgsl0-dev ccache

# Building matplotlib from source depends on these
RUN         apt-get install -y pkg-config libfreetype6-dev

# Building scipy from source depends on these
RUN         apt-get install -y gfortran libblas-dev liblapack-dev

# Teach matplotlib to work headless by default
RUN         mkdir -p ~/.config/matplotlib
RUN         echo 'backend: Agg' > ~/.config/matplotlib/matplotlibrc
RUN         mkdir -p ~/.matplotlib
RUN         echo 'backend: Agg' > ~/.matplotlib/matplotlibrc
RUN         echo 'backend: Agg' > ~/.matplotlibrc

# The caller is expected to place a built Venture source distribution
# into the dist/ directory, and a run.sh script that will test it.

ADD         . /root/Venturecxx
WORKDIR     /root/Venturecxx/
RUN         ./dist/run.sh
