# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

from nose import SkipTest
from nose.tools import eq_
from testconfig import config

from venture.test.config import get_ripl, on_inf_prim, gen_on_inf_prim
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSPRecord
from venture.lite.value import VentureValue
from venture.lite.types import AnyType
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
    if name in [# Because tag is misannotated as to the true
                # permissible types of scopes and blocks
                "tag", "tag_exclude",
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
    "apply", # Not implemented, and can't seem to import it as a foreign from Python
    "arange", # Not the same return type (elements boxed in Puma?)
    "vector_dot", # Numerical inconsistency between Eigen and Numpy
    "matrix_times_vector", # Numerical inconsistency between Eigen and Numpy
    "int_div", # Disagreement between Python and C++
    "int_mod", # Disagreement between Python and C++
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
        assert eq_(ans2, carefully(eval_in_ripl, expr))
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    expr = [v.symbol(name)] + [val.expressionFor() for val in args_lists[0]]
    eq_(answer, carefully(eval_in_ripl, expr))

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
