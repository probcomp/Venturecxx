from venture.lite.builtin import builtInSPsList
from venture.test import randomized as r
from venture.lite.psp import NullRequestPSP
from venture.lite.exception import VentureValueError
from venture.lite.sp import SPType
from nose import SkipTest
from nose.tools import eq_
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

def testTypes2():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield propTypeCorrect2, name, sp

def fully_uncurried_sp_type(sp_type):
  """Returns a list of arguments lists to pass to the given SP, in
order, to get a return type that is not an SP."""
  if not isinstance(sp_type, SPType):
    return []
  else:
    return [sp_type.args_types] + fully_uncurried_sp_type(sp_type.return_type)

def propTypeCorrect2(_name, sp):
  type_ = sp.venture_type()
  checkTypedProperty(helpPropTypeCorrect2, fully_uncurried_sp_type(type_), sp, type_)

def helpPropTypeCorrect2(args_lists, sp, type_):
  if len(args_lists) == 0:
    pass # OK
  else:
    args = r.BogusArgs(args_lists[0], sp.constructSPAux())
    answer = carefully(sp.outputPSP.simulate, args)
    assert answer in type_.return_type
    helpPropTypeCorrect2(args_lists[1:], answer, type_.return_type)

def testRandomMark2():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield propRandomAnnotated2, name, sp

def propRandomAnnotated2(name, sp):
  checkTypedProperty(helpPropRandomAnnotated2, sp.venture_type().args_types, name, sp)

def helpPropRandomAnnotated2(args_list, name, sp):
  args = r.BogusArgs(args_list, sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if not sp.outputPSP.isRandom():
    for _ in range(5):
      eq_(answer, carefully(sp.outputPSP.simulate, args))
  else:
    raise SkipTest("%s claims to be random" % name)
