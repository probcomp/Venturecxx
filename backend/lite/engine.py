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
from trace import Trace
from venture.cxx import engine

# Hack the Engine class from backend/cxx/engine.py to wrap Lite traces
# instead of CXX traces.

class Engine(engine.Engine):

  def __init__(self): # pylint: disable=super-init-not-called
    # Intentionally overriding the superclass init to avoid loading libtrace.so
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
    # Do not frobnicate the random seed, because the Lite trace uses
    # Python's rng rather than seeding its own from the system clock.
    for (_,directive) in worklist:
      self.replay(directive)
