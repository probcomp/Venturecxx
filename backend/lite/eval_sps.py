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

from psp import DeterministicPSP
from env import VentureEnvironment
from request import Request,ESR

class EvalRequestPSP(DeterministicPSP):
  def simulate(self,args):
    (exp, env) = args.operandValues()
    # point to the desugared source code location of lambda body
    addr = args.operandNodes[0].address.last.append(1)    
    return Request([ESR(args.node,exp,addr,env)])
  def description(self,name):
    return "%s evaluates the given expression in the given environment and returns the result.  Is itself deterministic, but the given expression may involve a stochasitc computation." % name

class ExtendEnvOutputPSP(DeterministicPSP):
  def simulate(self,args): 
    (env, sym, _) = args.operandValues()
    node = args.operandNodes[2]
    return VentureEnvironment(env,[sym],[node])
  def description(self,name):
    return "%s returns an extension of the given environment where the given symbol is bound to the given object" % name
