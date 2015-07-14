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

from psp import DeterministicPSP, NullRequestPSP
from env import VentureEnvironment
from request import Request, ESR
from value import VentureArray, SPRef
from address import emptyAddress
from exception import VentureValueError

class ApplyRequestPSP(DeterministicPSP):
    def simulate(self, args):
        (operator, operands) = args.operandValues()
        exp = [operator] + operands
        env = VentureEnvironment()
        return Request([ESR(args.node, exp, emptyAddress, env)])

    def description(self, name):
        return "(%s func vals) returns the result of applying a variadic function to an array of operands" % name

class ArrayMapRequestPSP(DeterministicPSP):
    def simulate(self, args):
        (operator, operands) = args.operandValues()
        exps = [[operator, operand] for operand in operands]
        env = VentureEnvironment()
        return Request([ESR((args.node, i), exp, emptyAddress, env) for i, exp in enumerate(exps)])

    def description(self, name):
        return "(%s func vals) returns the results of applying a function to each value in an array" % name

class IndexedArrayMapRequestPSP(DeterministicPSP):
    def simulate(self, args):
        (operator, operands) = args.operandValues()
        exps = [[operator, index, operand] for (index, operand) in enumerate(operands)]
        env = VentureEnvironment()
        return Request([ESR((args.node, i), exp, emptyAddress, env) for i, exp in enumerate(exps)])

    def description(self, name):
        return "(%s func vals) returns the results of applying a function to each value in an array, together with its index" % name

class ESRArrayOutputPSP(DeterministicPSP):
    def simulate(self, args):
        return VentureArray(args.esrValues())

class FixRequestPSP(DeterministicPSP):
    def simulate(self, args):
        (ids, exps) = args.operandValues()
        # point to the desugared source code location of expression list
        addr = args.operandNodes[1].address.last.append(1)
        # extend current environment with empty bindings for ids
        # (will be initialized in the output PSP)
        env = VentureEnvironment(args.env, ids, [None for _ in ids])
        request = Request([ESR((args.node, i), exp, addr.append(i), env)
                           for i, exp in enumerate(exps)])
        return request

class FixOutputPSP(DeterministicPSP):
    def simulate(self, args):
        ids = args.operandValues()[0]
        # get the extended environment shared by the ESRs
        env = None
        for esr in args.requestValue().esrs:
            if env is None: env = esr.env
            else: assert env is esr.env
        if env is None: env = args.env
        # bind ids to the requested values
        for id, esrParent in zip(ids, args.esrNodes()):
            env.fillBinding(id, esrParent)
        return env

    def description(self, name):
        return "%s\n  Used internally in the implementation of letrec." % name

class AssessOutputPSP(DeterministicPSP):
    def simulate(self, args):
        value = args.operandValues[0]
        if isinstance(value, SPRef):
            value = value.makerNode.madeSPRecord # XXX trace.madeSPRecordAt(value.makerNode)

        operator = args.operandValues[1]
        if isinstance(operator, SPRef):
            operator = operator.makerNode.madeSPRecord # XXX trace.madeSPRecordAt(operator.makerNode)
        if not isinstance(operator.sp.requestPSP, NullRequestPSP):
            raise VentureValueError("Cannot assess a requesting SP.")
        if not operator.sp.outputPSP.isRandom():
            raise VentureValueError("Cannot assess a deterministic SP.")

        import copy
        assessedArgs = copy.copy(args)
        assessedArgs.operandValues = args.operandValues[2:]
        assessedArgs.operandNodes = args.operandNodes[2:]
        assessedArgs.spaux = operator.spAux # XXX trace.madeSPAuxAt(operator.makerNode)
        # XXX madeSPAux?

        return operator.sp.outputPSP.logDensity(value, assessedArgs)

    def description(self, name):
        return "  (%s val func arg1 arg2 ...) returns the log probability (density) of simulating val from (func arg1 arg2 ...)" % name
