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

# Dockerfile for testing Venture's Debian dependency list in an
# isolated environment.

FROM        ubuntu:14.04

MAINTAINER  MIT Probabilistic Computing Project

# Install dependencies
RUN         apt-get update
RUN         apt-get install -y libboost-all-dev libgsl0-dev python-pip ccache libfreetype6-dev
RUN         pip install -U distribute
RUN         apt-get install -y python-flask python-requests python-numpy python-matplotlib python-scipy python-zmq ipython ipython-notebook

RUN         mkdir -p ~/.config/matplotlib
RUN         echo 'backend: Agg' > ~/.config/matplotlib/matplotlibrc
RUN         mkdir -p ~/.matplotlib
RUN         echo 'backend: Agg' > ~/.matplotlib/matplotlibrc
RUN         echo 'backend: Agg' > ~/.matplotlibrc

# The caller is expected to place a built Venture source distribution
# into the working directory.

ADD         . /root/Venturecxx
WORKDIR     /root/Venturecxx/
