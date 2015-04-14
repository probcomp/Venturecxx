#!/usr/bin/env python -i

# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

import sys
from venture.shortcuts import make_ripl_rest_client

port = 8082
if len(sys.argv) > 1:
    port = int(sys.argv[1])

url = "http://127.0.0.1:{0}".format(port)
print "Connecting to RIPL Server at {0}".format(url)
ripl = make_ripl_rest_client(url)
print "Venture RIPL handle in `ripl' variable"
