from venture.lite.builtin import builtInSPsList
from venture.test import randomized as r
from venture.lite.psp import NullRequestPSP
from venture.lite.exception import VentureValueError
from venture.lite.sp import SPType
from nose import SkipTest
from nose.tools import eq_

def testTypes():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield propTypeCorrect, name, sp

def testRandomMark():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield propRandomAnnotated, name, sp

def appropriate_arguments(sp, type_, budget=20):
  for _ in range(budget):
    args = r.random_args_for_sp(sp, type_)
    if args is None: continue
    try:
      answer = sp.outputPSP.simulate(args)
      yield args, answer
    except ValueError: continue
    except VentureValueError: continue

def propTypeCorrect(name, sp):
  type_ = sp.venture_type()
  app_ct = 0
  for (_, answer) in appropriate_arguments(sp, type_):
    app_ct += 1
    helpPropTypeCorrect(answer, type_.return_type)
  if app_ct == 0:
    raise SkipTest("Could not find appropriate args for %s" % name)

def helpPropTypeCorrect(answer, type_):
  assert answer in type_
  if isinstance(type_, SPType):
    for (_, ans2) in appropriate_arguments(answer, type_, budget=1):
      helpPropTypeCorrect(ans2, type_.return_type)

def propRandomAnnotated(name, sp):
  app_ct = 0
  for (args, answer) in appropriate_arguments(sp, sp.venture_type()):
    app_ct += 1
    if not sp.outputPSP.isRandom():
      for _ in range(5):
        eq_(answer,sp.outputPSP.simulate(args))
    else:
      raise SkipTest("%s claims to be random" % name)
  if app_ct == 0:
    raise SkipTest("Could not find appropriate args for %s" % name)

######################################################################

from venture.lite.value import VentureType

class ArgumentsNotAppropriate(Exception):
  """Thrown by a property that is to be randomly checked when the
suggested inputs are not appropriate (even though they were type-correct)."""

def synthesize_for(type_):
  if isinstance(type_, VentureType):
    dist = type_.distribution(r.DefaultRandomVentureValue)
    if dist is not None:
      return dist.generate()
    else:
      raise ArgumentsNotAppropriate("Cannot generate arguments for %s" % type_)
  else:
    return [synthesize_for(t) for t in type_]

def checkTypedProperty(prop, type_, *args, **kwargs):
  app_ct = 0
  for _ in range(20):
    try:
      synth_args = synthesize_for(type_)
      prop(synth_args, *args, **kwargs)
      app_ct += 1
    except ArgumentsNotAppropriate: continue
    except Exception:
      # Reraise the exception with a reasonable backtrace, per
      # http://nedbatchelder.com/blog/200711/rethrowing_exceptions_in_python.html
      import sys
      info = sys.exc_info()
      print args
      raise info[1], None, info[2]
  if app_ct == 0:
    raise SkipTest("Could not find appropriate args for %s" % prop)

def carefully(f, *args, **kwargs):
  try:
    return f(*args, **kwargs)
  except ValueError, e: raise ArgumentsNotAppropriate(e)
  except VentureValueError, e: raise ArgumentsNotAppropriate(e)

def testTypes2():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield propTypeCorrect2, name, sp

def propTypeCorrect2(_name, sp):
  checkTypedProperty(helpPropTypeCorrect2, sp.venture_type().args_types, sp)

def helpPropTypeCorrect2(args_list, sp):
  args = r.BogusArgs(args_list, sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  assert answer in sp.venture_type().return_type
