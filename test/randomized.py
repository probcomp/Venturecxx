"""A vaguely QuickCheck-inspired randomized testing framework for properties about Venture."""

from nose import SkipTest

from venture.test import random_values as r
from venture.lite.exception import VentureValueError
from venture.lite.sp import SPType
from venture.lite.value import VentureType

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

def checkTypedProperty(prop, type_, *args, **kwargs):
  """Checks a property, given a description of the argument to pass it.

  Will repeatedly call the property with:
  1. An object matching the given type in the first position
  2. All the additional given positional and keyword in subsequent
     positions.

  If the property completes successfully it is taken to have passed.
  If the property raises ArgumentsNotAppropriate, that test is ignored.
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
      prop(synth_args, *args, **kwargs)
      app_ct += 1
    except ArgumentsNotAppropriate: continue
    except SkipTest: raise
    except Exception:
      # Reraise the exception with a reasonable backtrace, per
      # http://nedbatchelder.com/blog/200711/rethrowing_exceptions_in_python.html
      import sys
      info = sys.exc_info()
      raise Exception("%s led to %s" % (synth_args, info[1])), None, info[2]
  if app_ct == 0:
    raise SkipTest("Could not find appropriate args for %s" % prop)

def carefully(f, *args, **kwargs):
  """Calls f with the given arguments, converting ValueError and
VentureValueError into ArgumentsNotAppropriate."""
  try:
    return f(*args, **kwargs)
  except ValueError, e: raise ArgumentsNotAppropriate(e)
  except VentureValueError, e: raise ArgumentsNotAppropriate(e)

def fully_uncurried_sp_type(sp_type):
  """Returns a list of arguments lists to pass to the given SP, in
order, to get a return type that is not an SP."""
  if not isinstance(sp_type, SPType):
    return []
  else:
    return [sp_type.args_types] + fully_uncurried_sp_type(sp_type.return_type)


