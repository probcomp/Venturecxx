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
from venture.lite.psp import TypedPSP
from venture.lite import env as env
from venture.lite.sp import SPAux # Pylint doesn't understand type comments pylint: disable=unused-import
import venture.lite.value as vv # Pylint doesn't understand type comments pylint: disable=unused-import

class MockArgs(IArgs):
  """IArgs instance for invoking methods on SPs that don't interact with the trace.

  (Which is most of them)."""

  def __init__(self, vals, aux, py_rng=None, np_rng=None, madeSPAux=None):
    # type: (List[vv.VentureValue], SPAux, random.Random, npr.RandomState, SPAux) -> None
    super(MockArgs, self).__init__()
    self.vals = vals
    self.aux = aux
    self._madeSPAux = madeSPAux
    self.operandNodes = [None for _ in vals]
    self.env = env.VentureEnvironment()
    self._np_rng = np_rng
    self._py_rng = py_rng

  def operandValues(self): return self.vals
  def spaux(self): return self.aux
  def madeSPAux(self): return self._madeSPAux
  def esrNodes(self): return []
  def esrValues(self): return []
  def requestValue(self): return None
  def py_prng(self):
    if self._py_rng is None:
      self._py_rng = random.Random()
      self._py_rng.seed(random.randrange(2**31-1))
    return self._py_rng
  def np_prng(self):
    if self._np_rng is None:
      self._np_rng = npr.RandomState()
      self._np_rng.seed(random.randrange(2**31-1))
    return self._np_rng

def simulate(sp, no_wrapper=False):
  """Extract the given SP's simulate method as a Python function.

  Assumes the SP doesn't need much trace context, and in particular
  does not need to make requests.

  The resulting function accepts the arguments as a list, and a
  keyword argument for the spaux to use.  If not given, ask the SP to
  synthesize an empty one.

  If no_wrapper is given and True, expect the output PSP to be wrapped
  by TypedPSP, and circumvent that wrapper (accepting Python values
  directly).
  """
  assert isinstance(sp.requestPSP, NullRequestPSP)
  def doit(vals, spaux=None):
    if spaux is None:
      spaux = sp.constructSPAux()
    args = MockArgs(vals, spaux)
    target = sp.outputPSP
    if no_wrapper:
      assert isinstance(target, TypedPSP)
      target = target.psp
    return target.simulate(args)
  return doit

def logDensity(sp, no_wrapper=False):
  """Extract the given SP's logDensity method as a Python function.

  Assumes the SP doesn't need much trace context, and in particular
  does not need to make requests.

  The resulting function accepts the arguments as a list, and a
  keyword argument for the spaux to use.  If not given, ask the SP to
  synthesize an empty one.

  If no_wrapper is given and True, expect the output PSP to be wrapped
  by TypedPSP, and circumvent that wrapper (accepting Python values
  directly).
  """
  assert isinstance(sp.requestPSP, NullRequestPSP)
  def doit(value, vals, spaux=None):
    if spaux is None:
      spaux = sp.constructSPAux()
    args = MockArgs(vals, spaux)
    target = sp.outputPSP
    if no_wrapper:
      assert isinstance(target, TypedPSP)
      target = target.psp
    return target.logDensity(value, args)
  return doit

def gradientOfLogDensity(sp, no_wrapper=False):
  """Extract the given SP's gradientOfLogDensity method as a Python function.

  Assumes the SP doesn't need much trace context, and in particular
  does not need to make requests.

  The resulting function accepts the arguments as a list, and a
  keyword argument for the spaux to use.  If not given, ask the SP to
  synthesize an empty one.

  If no_wrapper is given and True, expect the output PSP to be wrapped
  by TypedPSP, and circumvent that wrapper (accepting Python values
  directly).
  """
  assert isinstance(sp.requestPSP, NullRequestPSP)
  def doit(value, vals, spaux=None):
    if spaux is None:
      spaux = sp.constructSPAux()
    args = MockArgs(vals, spaux)
    target = sp.outputPSP
    if no_wrapper:
      assert isinstance(target, TypedPSP)
      target = target.psp
    return target.gradientOfLogDensity(value, args)
  return doit

class ReplacingArgs(IArgs):
  """An implementation of IArgs for replacing the argument values preseving the rest of the context.

  """
  def __init__(self, args, operandValues, operandNodes = None,
               spaux = None):
    super(ReplacingArgs, self).__init__()
    self.args = args
    self._operandValues = operandValues
    self.node = args.node
    if operandNodes is None:
      self.operandNodes = args.operandNodes
    else:
      self.operandNodes = operandNodes
    self._spaux = spaux
    self.env = args.env
    assert isinstance(args, IArgs)

  def operandValues(self): return self._operandValues
  def spaux(self):
    if self._spaux is None:
      return self.args.spaux()
    else:
      return self._spaux

  def requestValue(self): return self.args.requestValue()
  def esrNodes(self): return self.args.esrNodes()
  def esrValues(self): return self.args.esrValues()
  def madeSPAux(self): return self.args.madeSPAux()

  def py_prng(self): return self.args.py_prng()
  def np_prng(self): return self.args.np_prng()

  def __repr__(self):
    return "%s(%r)" % (self.__class__, self.__dict__)

class RemappingArgs(IArgs):
  """An implementation of IArgs for remapping the argument values by a given function.

  Accepts said function and another IArgs instance to delegate other methods to."""
  def __init__(self, f, args):
    super(RemappingArgs, self).__init__()
    self.f = f
    self.args = args
    self.node = args.node
    self.operandNodes = args.operandNodes
    self.env = args.env
    if hasattr(args, 'trace'):
      self.trace = args.trace
    assert isinstance(args, IArgs)

  def operandValues(self):
    return self.f(self.args.operandValues())

  def spaux(self): return self.args.spaux()

  def requestValue(self):
    return self.args.requestValue()

  def esrNodes(self):
    return self.args.esrNodes()

  def esrValues(self):
    return self.args.esrValues()

  def madeSPAux(self):
    return self.args.madeSPAux()

  def py_prng(self): return self.args.py_prng()
  def np_prng(self): return self.args.np_prng()

  def __repr__(self):
    return "%s(%r)" % (self.__class__, self.__dict__)
