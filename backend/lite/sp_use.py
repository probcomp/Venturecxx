# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

"""Helpers for using SP objects."""

import random
import numpy.random as npr

from venture.lite.psp import IArgs
from venture.lite.psp import NullRequestPSP
from venture.lite import env as env

class MockArgs(IArgs):
  """IArgs instance for invoking methods on SPs that don't interact with the trace.

  (Which is most of them)."""

  def __init__(self, args, aux, py_rng=None, np_rng=None):
    super(MockArgs, self).__init__()
    # TODO Do I want to try to synthesize an actual real random valid Args object?
    if py_rng is None:
      py_rng = random.Random()
    if np_rng is None:
      np_rng = npr.RandomState()
    self.args = args
    self.aux = aux
    self.operandNodes = [None for _ in args]
    self.env = env.VentureEnvironment()
    self._np_rng = np_rng
    self._py_rng = py_rng

  def operandValues(self): return self.args
  def spaux(self): return self.aux
  def madeSPAux(self): raise NotImplementedError
  def esrNodes(self): return []
  def esrValues(self): return []
  def py_prng(self): return self._py_rng
  def np_prng(self): return self._np_rng

def simulate(sp):
  """Extract the given SP's simulate method as a Python function.

  Assumes the SP doesn't need much trace context, and in particular
  does not need to make requests.

  The resulting function accepts the arguments as a list, and a
  keyword argument for the spaux to use.  If not given, ask the SP to
  synthesize an empty one.
  """
  assert isinstance(sp.requestPSP, NullRequestPSP)
  def doit(args, spaux=None):
    if spaux is None:
      spaux = sp.constructSPAux()
    args = MockArgs(args, spaux)
    return sp.outputPSP.simulate(args)
  return doit
