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
decising whether "sporadic fail" should be treated as "fail" or
"pass"."""

import numpy.random as npr
from nose import SkipTest

from venture.test import random_values as r
from venture.lite.exception import VentureValueError
from venture.lite.sp import SPType
from venture.lite.value import VentureType
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
  app_ct = 0
  for _ in range(20):
    try:
      synth_args = synthesize_for(type_)
    except ArgumentsNotAppropriate: continue
    try:
      prop(synth_args, *args, **kwargs)
      app_ct += 1
    except ArgumentsNotAppropriate: continue
    except SkipTest: raise
    except Exception:
      # Reraise the exception with an indication of the argument that caused it.
      # Also arrange for a reasonable backtrace, per
      # http://nedbatchelder.com/blog/200711/rethrowing_exceptions_in_python.html
      import sys
      info = sys.exc_info()
      raise info[0]("%s led to %s" % (synth_args, info[1])), None, info[2]
  if app_ct == 0:
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
    self.operandValues = args
    self.operandNodes = [None for _ in args]
    self.isOutput = True
    self.esrValues = []
    self.env = env.VentureEnvironment()
    self.spaux = aux
