# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

from psp import DeterministicPSP, ESRRefOutputPSP
from sp import SP, VentureSPRecord
from env import VentureEnvironment
from request import Request,ESR
from address import emptyAddress

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
    id = str(args.operandValues)
    exp = ["memoizedSP"] + [["quote",val] for val in args.operandValues]
    env = VentureEnvironment(None,["memoizedSP"],[self.sharedOperatorNode])
    return Request([ESR(id,exp,emptyAddress,env)])
