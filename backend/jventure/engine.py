# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
from libtrace import Trace
import pdb
from venture.exception import VentureException
from venture.cxx import engine

# Hack the Engine class from backend/cxx/engine.py to wrap Julia traces
# instead of CXX traces.

class Engine(engine.Engine):

  def __init__(self):
    print "Making JVenture engine"
    self.directiveCounter = 0
    self.directives = {}
    self.trace = Trace() # Same code, different Trace, due to different import

  def clear(self):
    del self.trace
    self.directiveCounter = 0
    self.directives = {}
    self.trace = Trace()

  def reset(self):
    worklist = sorted(self.directives.iteritems())
    self.clear()
    # TODO Do I need to frobnicate the random seed?  Julia traces do
    # not provide a method for doing that yet.
    [self.replay(dir) for (_,dir) in worklist]
