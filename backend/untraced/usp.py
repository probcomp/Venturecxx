# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

from venture.lite.address import emptyAddress
from venture.lite.env import VentureEnvironment
from venture.lite.psp import DeterministicPSP, RandomPSP, NullRequestPSP
from venture.lite.sp import SP, VentureSPRecord
from venture.lite.sp import SPType
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.value import VentureValue
import venture.lite.types as t

from venture.untraced.evaluator import apply
from venture.untraced.node import Node

class MakeUSPOutputPSP(DeterministicPSP):
  def simulate(self, args):
    simulatorNode = args.operandNodes[0]
    assessorNode = args.operandNodes[1] # TODO make this optional
    return VentureSPRecord(SP(NullRequestPSP(), UntracedSPOutputPSP(simulatorNode, assessorNode)))

class UntracedSPOutputPSP(RandomPSP):
  def __init__(self, simulatorNode, assessorNode):
    self.simulatorNode = simulatorNode
    self.assessorNode = assessorNode

  def simulate(self, args):
    nodes = [self.simulatorNode] + args.operandNodes
    env = VentureEnvironment()
    return apply(emptyAddress, nodes, env)

  def logDensity(self, value, args):
    valueNode = Node(emptyAddress, value)
    nodes = [self.assessorNode, valueNode] + args.operandNodes
    env = VentureEnvironment()
    result = apply(emptyAddress, nodes, env)
    if isinstance(result, VentureValue):
      result = result.getNumber()
    return result

registerBuiltinSP("make_untraced_sp",
                  typed_nr(MakeUSPOutputPSP(),
                           [SPType([t.AnyType("a")], t.AnyType("b"), variadic=True),
                            SPType([t.AnyType("a")], t.AnyType("b"), variadic=True)],
                           SPType([t.AnyType("a")], t.AnyType("b"), variadic=True)))
