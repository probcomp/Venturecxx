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

from venture.lite.psp import DeterministicPSP
from venture.lite.psp import TypedPSP
from venture.lite.request import ESR
from venture.lite.request import Request
from venture.lite.sp import SPType
from venture.lite.sp_help import esr_output
from venture.lite.sp_help import type_test
from venture.lite.sp_help import typed_func
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
import venture.lite.env as env
import venture.lite.types as t

registerBuiltinSP("get_current_environment", typed_func(lambda args: args.env, [], env.EnvironmentType(),
                                                        descr="get_current_environment returns the lexical environment of its invocation site"))
registerBuiltinSP("get_empty_environment", typed_func(lambda args: env.VentureEnvironment(), [], env.EnvironmentType(),
                                                      descr="get_empty_environment returns the empty environment"))
registerBuiltinSP("is_environment", type_test(env.EnvironmentType()))

class ExtendEnvOutputPSP(DeterministicPSP):
  def simulate(self,args):
    (en, sym, _) = args.operandValues()
    node = args.operandNodes[2]
    return env.VentureEnvironment(en,[sym],[node])
  def description(self,name):
    return "%s returns an extension of the given environment where the given symbol is bound to the given object" % name

registerBuiltinSP("extend_environment", typed_nr(ExtendEnvOutputPSP(),
                                                 [env.EnvironmentType(), t.SymbolType(), t.AnyType()],
                                                 env.EnvironmentType()))

class EvalRequestPSP(DeterministicPSP):
  def simulate(self,args):
    (exp, en) = args.operandValues()
    # point to the desugared source code location of lambda body
    addr = args.operandNodes[0].address.last.append(1)
    return Request([ESR(args.node,exp,addr,en)])
  def description(self,name):
    return "%s evaluates the given expression in the given environment and returns the result.  Is itself deterministic, but the given expression may involve a stochasitc computation." % name

registerBuiltinSP("eval",esr_output(TypedPSP(EvalRequestPSP(),
                                             SPType([t.ExpressionType(), env.EnvironmentType()],
                                                    t.RequestType("<object>")))))
