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
from exception import VentureError

class CSPRequestPSP(DeterministicPSP):
  def __init__(self,ids,exp,addr,env):
    self.ids = ids
    self.exp = exp
    self.addr = addr
    self.env = env

  def simulate(self,args):
    if len(self.ids) != len(args.operandNodes):
      raise VentureError("Wrong number of arguments: compound takes exactly %d arguments, got %d." % (len(self.ids), len(args.operandNodes)))
    extendedEnv = VentureEnvironment(self.env,self.ids,args.operandNodes)
    return Request([ESR(args.node,self.exp,self.addr,extendedEnv)])

  def gradientOfSimulate(self, args, _value, _direction):
    # TODO Collect derivatives with respect to constants in the body
    # of the lambda and pass them through the constructor to whoever
    # came up with those constants.
    return [0 for _ in args.operandNodes]

  def canAbsorb(self, _trace, _appNode, _parentNode): return True

class MakeCSPOutputPSP(DeterministicPSP):
  def simulate(self,args):
    (ids, exp) = args.operandValues()
    # point to the desugared source code location of lambda body
    addr = args.operandNodes[1].address.last.append(1)
    return VentureSPRecord(SP(CSPRequestPSP(ids,exp,addr,args.env),ESRRefOutputPSP()))

  def gradientOfSimulate(self, args, _value, _direction):
    # A lambda is a constant.  I may need to do some plumbing here,
    # depending on how I want to handle closed-over values.
    return [0 for _ in args.operandNodes]

  def description(self,name):
    return "%s\n  Used internally in the implementation of compound procedures." % name
