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
from request import Request, ESR
from value import VentureArray
from address import emptyAddress

class ApplyRequestPSP(DeterministicPSP):
    def simulate(self, args):
        operator = args.operandValues[0]
        operands = args.operandValues[1]
        exp = [operator] + operands
        env = VentureEnvironment()
        return Request([ESR(args.node, exp, emptyAddress, env)])

    def description(self, name):
        return "(%s func vals) returns the result of applying a variadic function to an array of operands" % name

class ArrayMapRequestPSP(DeterministicPSP):
    def simulate(self, args):
        operator = args.operandValues[0]
        operands = args.operandValues[1]
        exps = [[operator, operand] for operand in operands]
        env = VentureEnvironment()
        return Request([ESR((args.node, i), exp, emptyAddress, env) for i, exp in enumerate(exps)])

    def description(self, name):
        return "(%s func vals) returns the results of applying a function to each value in an array" % name

class IndexedArrayMapRequestPSP(DeterministicPSP):
    def simulate(self, args):
        operator = args.operandValues[0]
        operands = args.operandValues[1]
        exps = [[operator, index, operand] for (index, operand) in enumerate(operands)]
        env = VentureEnvironment()
        return Request([ESR((args.node, i), exp, emptyAddress, env) for i, exp in enumerate(exps)])

    def description(self, name):
        return "(%s func vals) returns the results of applying a function to each value in an array, together with its index" % name

class ESRArrayOutputPSP(DeterministicPSP):
    def simulate(self, args):
        return VentureArray(args.esrValues)
