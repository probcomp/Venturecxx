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

from venture.lite.env import VentureEnvironment
from venture.lite.psp import DeterministicPSP, ESRRefOutputPSP
from venture.lite.request import Request,ESR
from venture.lite.sp import SP, VentureSPRecord
from venture.lite.sp import SPType
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
import venture.lite.address as addr
import venture.lite.types as t

class MakeMSPOutputPSP(DeterministicPSP):
  def simulate(self,args):
    sharedOperatorNode = args.operandNodes[0]
    return VentureSPRecord(SP(MSPRequestPSP(sharedOperatorNode),ESRRefOutputPSP()))

  def description(self,name):
    return "%s returns the stochastically memoized version of the input SP." % name

class MSPRequestPSP(DeterministicPSP):
  def __init__(self,sharedOperatorNode):
    self.sharedOperatorNode = sharedOperatorNode

  def simulate(self,args):
    vals = args.operandValues()
    id = str(vals)
    exp = ["memoizedSP"] + [["quote",val] for val in vals]
    env = VentureEnvironment(None,["memoizedSP"],[self.sharedOperatorNode])
    return Request([ESR(id,exp,addr.req_frame(id),env)])

registerBuiltinSP("mem",typed_nr(MakeMSPOutputPSP(),
                                 [SPType([t.AnyType("a")], t.AnyType("b"), variadic=True)],
                                 SPType([t.AnyType("a")], t.AnyType("b"), variadic=True)))
