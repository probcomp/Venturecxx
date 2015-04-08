from nose import SkipTest
from testconfig import config

from venture.test.config import get_ripl, on_inf_prim, gen_on_inf_prim
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSPRecord
from venture.lite.value import AnyType, VentureValue
import venture.value.dicts as v

from test_sps import relevantSPs

@on_inf_prim("none")
def testExpressionFor():
  checkTypedProperty(propExpressionWorks, AnyType())

def propExpressionWorks(value):
  expr = value.expressionFor()
  result = carefully(eval_in_ripl, expr)
  assert value.equal(result)

@on_inf_prim("none")
def testRiplRoundTripThroughStack():
  checkTypedProperty(propRiplRoundTripThroughStack, AnyType())

def propRiplRoundTripThroughStack(value):
  expr = v.quote(value.asStackDict())
  result = carefully(eval_in_ripl, expr)
  assert value.equal(result)

def eval_in_ripl(expr):
  ripl = get_ripl()
  ripl.predict(expr, label="thing")
  return VentureValue.fromStackDict(ripl.report("thing", type=True))

@gen_on_inf_prim("none")
def testRiplSimulate():
  for (name,sp) in relevantSPs():
    if name in ["scope_include", # Because scope_include is
                                 # misannotated as to the true
                                 # permissible types of scopes and
                                 # blocks
                "tag",
                "get_current_environment", # Because BogusArgs gives a bogus environment
                "extend_environment", # Because BogusArgs gives a bogus environment
              ]:
      continue
    if config["get_ripl"] != "lite" and name in [
        ## Expected failures
        "dict", # Because keys and values must be the same length
        "matrix", # Because rows must be the same length
        "lookup", # Because the key must be an integer for sequence lookups
        "get_empty_environment", # Environments can't be rendered to stack dicts
    ]:
      continue
    if not sp.outputPSP.isRandom():
      yield checkRiplAgreesWithDeterministicSimulate, name, sp

def checkRiplAgreesWithDeterministicSimulate(name, sp):
  if config["get_ripl"] != "lite" and name in [
    ## Incompatibilities with Puma
    "to_list", # Not implemented
    "min", # Not implemented
    "mod", # Not implemented
    "atan2", # Not implemented
    "real", # Not implemented
    "atom_eq", # Not implemented
    "arange", # Not implemented
    "linspace", # Not implemented
    "diag_matrix", # Not implemented
    "ravel", # Not implemented
    "matrix_mul", # Not implemented
    "repeat", # Not implemented
    "vector_dot", # Not implemented
    "zip", # Not implemented
    "is_procedure", # Not implemented
    "print", # Not implemented
  ]:
    raise SkipTest("%s in Puma not implemented compatibly with Lite" % name)
  checkTypedProperty(propRiplAgreesWithDeterministicSimulate, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propRiplAgreesWithDeterministicSimulate(args_lists, name, sp):
  """Check that the given SP produces the same answer directly and
through a ripl (applied fully uncurried)."""
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if isinstance(answer, VentureSPRecord):
    if isinstance(answer.sp.requestPSP, NullRequestPSP):
      if not answer.sp.outputPSP.isRandom():
        args2 = BogusArgs(args_lists[1], answer.spAux)
        ans2 = carefully(answer.sp.outputPSP.simulate, args2)
        inner = [v.symbol(name)] + [val.expressionFor() for val in args_lists[0]]
        expr = [inner] + [val.expressionFor() for val in args_lists[1]]
        assert ans2.equal(carefully(eval_in_ripl, expr))
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    expr = [v.symbol(name)] + [val.expressionFor() for val in args_lists[0]]
    assert answer.equal(carefully(eval_in_ripl, expr))

def eval_foreign_sp(name, sp, expr):
  ripl = get_ripl()
  ripl.bind_foreign_sp(name, sp)
  ripl.predict(expr, label="thing")
  return VentureValue.fromStackDict(ripl.report("thing", type=True))

@gen_on_inf_prim("none")
def testForeignInterfaceSimulate():
  for (name,sp) in relevantSPs():
    if name in ["scope_include", # Because scope_include is
                                 # misannotated as to the true
                                 # permissible types of scopes and
                                 # blocks
                "tag",
                "get_current_environment", # Because BogusArgs gives a bogus environment
                "extend_environment", # Because BogusArgs gives a bogus environment
              ]:
      continue
    if config["get_ripl"] != "lite" and name in [
        ## Expected failures
        "dict", # Because keys and values must be the same length
        "matrix", # Because rows must be the same length
        "get_empty_environment", # Environments can't be rendered to stack dicts
    ]:
      continue
    if not sp.outputPSP.isRandom():
      yield checkForeignInterfaceAgreesWithDeterministicSimulate, name, sp

def checkForeignInterfaceAgreesWithDeterministicSimulate(name, sp):
  checkTypedProperty(propForeignInterfaceAgreesWithDeterministicSimulate, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propForeignInterfaceAgreesWithDeterministicSimulate(args_lists, name, sp):
  """Check that the given SP produces the same answer directly and
through the foreign function interface (applied fully uncurried)."""
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if isinstance(answer, VentureSPRecord):
    if isinstance(answer.sp.requestPSP, NullRequestPSP):
      if not answer.sp.outputPSP.isRandom():
        args2 = BogusArgs(args_lists[1], answer.spAux)
        ans2 = carefully(answer.sp.outputPSP.simulate, args2)
        inner = [v.symbol("test_sp")] + [val.expressionFor() for val in args_lists[0]]
        expr = [inner] + [val.expressionFor() for val in args_lists[1]]
        assert ans2.equal(carefully(eval_foreign_sp, "test_sp", sp, expr))
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    expr = [v.symbol("test_sp")] + [val.expressionFor() for val in args_lists[0]]
    assert answer.equal(carefully(eval_foreign_sp, "test_sp", sp, expr))
