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

"""A vaguely QuickCheck-inspired randomized testing framework for
properties about Venture.

The main entry point is checkTypedProperty (unlike in QuickCheck, the
type to be tested must be passed in explicitly).

Currently limited to synthesizing only VentureValues (as used by the
Lite backend), not objects of other types.

There are currently no facilities for automatically searching for
smaller counter-examples, as there are in QuickCheck.  This would be a
good next point for improvement.

There are also no good facilities for automatically checking whether a
property fails stochastically or deterministically, or combinators for
deciding whether "sporadic fail" should be treated as "fail" or
"pass"."""

import numpy.random as npr
from nose import SkipTest

from venture.test import random_values as r
from venture.lite.exception import VentureValueError
from venture.lite.sp import SPType
from venture.lite.types import VentureType
from venture.lite import env as env

def checkTypedProperty(prop, type_, *args, **kwargs):
  """Checks a property, given a description of the arguments to pass it.

  Will repeatedly call the property with:
  1. A random object matching the given type in the first position
  2. All the additional given positional and keyword arguments in
     subsequent positions.

  If the property completes successfully it is taken to have passed.
  If the property raises ArgumentsNotAppropriate, that test is ignored.
  - This amounts to refining the distribution on possible inputs by
    rejection sampling.
  If too many tests are thrown out, the test is taken as a skip
    (because the distribution on random inputs is not precise enough).
  If the property raises SkipTest, the test is aborted as a skip.
  If the property raises any other exception, it is taken to have
    failed, and the offending generated argument is communicated as a
    counter-example.

  """

  # Try at most 20 times, but record a pass if even one passes (as
  # long as none fail).
  pass_ct = 0
  try_budget = 20
  while try_budget > 0:
    attempt = findAppropriateArguments(prop, type_, try_budget, *args, **kwargs)
    if attempt is None: break
    pass_ct += 1
    try_budget -= attempt[2]
  if pass_ct == 0:
    raise SkipTest("Could not find appropriate args for %s" % prop)

class ArgumentsNotAppropriate(Exception):
  """Thrown by a property that is to be randomly checked when the
suggested inputs are not appropriate (even though they were type-correct)."""

def synthesize_for(type_):
  """Synthesizes a bunch of VentureValues according to the given type.
If the type is a VentureType, makes one of those.  If the type is a
list, makes that many things of those types, recursively."""
  if isinstance(type_, VentureType):
    dist = type_.distribution(r.DefaultRandomVentureValue)
    if dist is not None:
      return dist.generate()
    else:
      raise ArgumentsNotAppropriate("Cannot generate arguments for %s" % type_)
  else:
    return [synthesize_for(t) for t in type_]

def findAppropriateArguments(f, type_, max_tries, *args, **kwargs):
  """Finds a set arguments from type_ that f deems appropriate.

  Returns the arguments, the return value, and the number of attempts.

  Gives up if none are discovered in max_tries tries (set this if you
  are worried that the type might be too loose).

  """
  tried = 0
  for _ in range(max_tries):
    tried += 1
    try:
      synth_args = synthesize_for(type_)
    except ArgumentsNotAppropriate: continue
    try:
      ans = f(synth_args, *args, **kwargs)
      return [synth_args, ans, tried]
    except ArgumentsNotAppropriate: continue
    except SkipTest: raise
    except Exception:
      # Reraise the exception with an indication of the argument that caused it.
      # Also arrange for a reasonable backtrace, per
      # http://nedbatchelder.com/blog/200711/rethrowing_exceptions_in_python.html
      import sys
      info = sys.exc_info()
      raise info[0]("%s led to %s" % (synth_args, info[1])), None, info[2]
  return None

def carefully(f, *args, **kwargs):
  """Calls f with the given arguments, converting ValueError and
VentureValueError into ArgumentsNotAppropriate."""
  try:
    return f(*args, **kwargs)
  except ValueError, e: raise ArgumentsNotAppropriate(e)
  except VentureValueError, e: raise ArgumentsNotAppropriate(e)

def sp_args_type(sp_type):
  """Returns a list representing the types of arguments that may be
passed to the given SP."""
  if not sp_type.variadic:
    return sp_type.args_types
  else:
    length = npr.randint(0, 10)
    return [sp_type.args_types[0] for _ in range(length)]

def fully_uncurried_sp_type(sp_type):
  """Returns a list of argument list types representing arguments that
may be passed to the given SP, in order, to get a return type that is
not an SP.

  """
  if not isinstance(sp_type, SPType):
    return []
  else:
    return [sp_args_type(sp_type)] + fully_uncurried_sp_type(sp_type.return_type)

def final_return_type(sp_type):
  """Returns the type that a given SP returns when applied fully uncurried."""
  if not isinstance(sp_type, SPType):
    return sp_type
  else:
    return final_return_type(sp_type.return_type)

class BogusArgs(object):
  """Calling an SP requires an Args object, which is supposed to point
  to Nodes in a Trace and all sorts of things.  Mock that for testing
  purposes, since most SPs do not read the hairy stuff."""

  def __init__(self, args, aux):
    # TODO Do I want to try to synthesize an actual real random valid Args object?
    self.args = args
    self.node = None
    self.operandNodes = [None for _ in args]
    self.isOutput = True
    self.esrValues = []
    self.esrNodes = []
    self.env = env.VentureEnvironment()
    self.spaux = aux

  def operandValues(self): return self.args
