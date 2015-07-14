# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

from psp import DeterministicPSP, TypedPSP
from request import Request,ESR
from sp import SPType
import types as t

# TODO This is used very little because the stack expands if to biplex.  Flush?
class BranchRequestPSP(DeterministicPSP):
  def simulate(self,args): 
#    print "branchRequest::simulate()"
    vals = args.operandValues()
    assert not vals[0] is None
    if vals[0]:
      expIndex = 1
    else:
      expIndex = 2
    exp = vals[expIndex]
    # point to the source code location of the expression
    addr = args.operandNodes[expIndex].address.last.append(1)
    return Request([ESR(args.node,exp,addr,args.env)])

  def description(self,name):
    return "%s evaluates either exp1 or exp2 in the current environment and returns the result.  Is itself deterministic, but the chosen expression may involve a stochastic computation." % name

def branch_request_psp():
  return TypedPSP(BranchRequestPSP(), SPType([t.BoolType(), t.ExpressionType(), t.ExpressionType()], t.RequestType("<object>")))
