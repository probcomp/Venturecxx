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

import random

from venture.exception import VentureException
from venture.lite.env import EnvironmentType
from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureValueError
from venture.lite.parallel_map import parallel_map
from venture.lite.psp import DeterministicPSP
from venture.lite.psp import NullRequestPSP
from venture.lite.psp import TypedPSP
from venture.lite.request import ESR
from venture.lite.request import Request
from venture.lite.sp import SP
from venture.lite.sp import SPType
from venture.lite.sp_help import esr_output
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.sp_use import ReplacingArgs
from venture.lite.value import SPRef
from venture.lite.value import VentureArray
import venture.lite.address as addr
import venture.lite.exp as e
import venture.lite.types as t

class ApplyRequestPSP(DeterministicPSP):
    def simulate(self, args):
        (operator, operands) = args.operandValues()
        exp = [operator] + operands
        env = VentureEnvironment()
        return Request([ESR(args.node, exp, addr.req_frame(0), env)])

    def description(self, name):
        return "%s(func, vals) returns the result of applying a variadic" \
            " function to an array of operands" % name

registerBuiltinSP(
    "apply",
    esr_output(TypedPSP(
        ApplyRequestPSP(),
        SPType([SPType([t.AnyType("a")], t.AnyType("b"), variadic=True),
                t.HomogeneousArrayType(t.AnyType("a"))],
               t.RequestType("b")))))

class ParallelArrayMapOutputPSP(DeterministicPSP):
    def simulate(self, args):
        from venture.lite.sp_use import RemappingArgs
        import venture.untraced.evaluator as untraced_evaluator
        base_address = args.node.address
        assert isinstance(args, RemappingArgs)
        if not isinstance(args.args, untraced_evaluator.OutputArgs):
            raise VentureException('evaluation', 'Cannot trace parallel_mapv!',
                address=base_address)
        assert isinstance(args.args, untraced_evaluator.OutputArgs)
        operator = args.operandValues()[0]
        operands = args.operandValues()[1]
        if len(args.operandValues()) == 3:
            parallelism = args.operandValues()[2]
        else:
            parallelism = None
        env = VentureEnvironment()
        rng = args.py_prng()
        def per_operand((i, seed, operand)):
            address = addr.request(base_address, addr.req_frame(i))
            rng_i = random.Random(seed)
            exp = [operator, e.quote(operand)]
            return untraced_evaluator.eval(address, exp, env, rng_i)
        inputs = [
            (i, rng.randint(1, 2**31 - 1), operand)
            for i, operand in enumerate(operands)
        ]
        return parallel_map(per_operand, inputs, parallelism=parallelism)

registerBuiltinSP("parallel_mapv",
    typed_nr(ParallelArrayMapOutputPSP(),
        [SPType([t.AnyType('a')], t.AnyType('b')),
            t.HomogeneousArrayType(t.AnyType('a')),
            t.IntegerType('parallelism')],
        t.HomogeneousArrayType(t.AnyType('b')),
        min_req_args=2))

class ArrayMapRequestPSP(DeterministicPSP):
    def simulate(self, args):
        (operator, operands) = args.operandValues()
        exps = [[operator, e.quote(operand)] for operand in operands]
        env = VentureEnvironment()
        return Request([ESR((args.node, i), exp, addr.req_frame(i), env)
                        for i, exp in enumerate(exps)])

    def description(self, name):
        return "%s(func, vals) returns the results of applying a function" \
            " to each value in an array" % name

class ESRArrayOutputPSP(DeterministicPSP):
    def simulate(self, args):
        return VentureArray(args.esrValues())

registerBuiltinSP(
    "mapv",
    SP(TypedPSP(ArrayMapRequestPSP(),
                SPType([SPType([t.AnyType("a")], t.AnyType("b")),
                        t.HomogeneousArrayType(t.AnyType("a"))],
                       t.RequestType("<array b>"))),
       ESRArrayOutputPSP()))

class ArrayMap2RequestPSP(DeterministicPSP):
    def simulate(self, args):
        (operator, operands1, operands2) = args.operandValues()
        exps = [[operator, e.quote(operand1), e.quote(operand2)]
                for operand1, operand2 in zip(operands1, operands2)]
        env = VentureEnvironment()
        return Request([ESR((args.node, i), exp, addr.req_frame(i), env)
                        for i, exp in enumerate(exps)])

    def description(self, name):
        return "%s(func, vals1, vals2) returns the results of applying" \
            " a binary function to each pair of values in the given two arrays" % name

registerBuiltinSP(
    "mapv2",
    SP(TypedPSP(ArrayMap2RequestPSP(),
                SPType([SPType([t.AnyType("a"), t.AnyType("b")], t.AnyType("c")),
                        t.HomogeneousArrayType(t.AnyType("a")),
                        t.HomogeneousArrayType(t.AnyType("b"))],
                       t.RequestType("<array c>"))),
       ESRArrayOutputPSP()))

class IndexedArrayMapRequestPSP(DeterministicPSP):
    def simulate(self, args):
        (operator, operands) = args.operandValues()
        exps = [[operator, index, e.quote(operand)]
                for (index, operand) in enumerate(operands)]
        env = VentureEnvironment()
        return Request([ESR((args.node, i), exp, addr.req_frame(i), env)
                        for i, exp in enumerate(exps)])

    def description(self, name):
        return "%s(func, vals) returns the results of applying a function" \
            " to each value in an array, together with its index" % name

registerBuiltinSP(
    "imapv",
    SP(TypedPSP(
        IndexedArrayMapRequestPSP(),
        SPType([SPType([t.AnyType("index"), t.AnyType("a")], t.AnyType("b")),
                t.HomogeneousArrayType(t.AnyType("a"))],
               t.RequestType("<array b>"))),
       ESRArrayOutputPSP()))

class FixRequestPSP(DeterministicPSP):
    def simulate(self, args):
        (ids, exps) = args.operandValues()
        # point to the desugared source code location of expression list
        loc = addr.append(addr.top_frame(args.operandNodes[1].address), 1)
        # extend current environment with empty bindings for ids
        # (will be initialized in the output PSP)
        env = VentureEnvironment(args.env, ids, [None for _ in ids])
        request = Request([ESR((args.node, i), exp, addr.append(loc, i), env)
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

registerBuiltinSP(
    "fix",
    SP(TypedPSP(FixRequestPSP(),
                SPType([t.HomogeneousArrayType(t.SymbolType()),
                        t.HomogeneousArrayType(t.ExpressionType())],
                       t.RequestType())),
       TypedPSP(FixOutputPSP(),
                SPType([t.HomogeneousArrayType(t.SymbolType()),
                        t.HomogeneousArrayType(t.ExpressionType())],
                       EnvironmentType()))))

class AssessOutputPSP(DeterministicPSP):
    def simulate(self, args):
        vals = args.operandValues()
        value = vals[0]
        if isinstance(value, SPRef):
            # XXX trace.madeSPRecordAt(value.makerNode)
            value = value.makerNode.madeSPRecord

        operator = vals[1]
        if isinstance(operator, SPRef):
            # XXX trace.madeSPRecordAt(operator.makerNode)
            operator = operator.makerNode.madeSPRecord
        if not isinstance(operator.sp.requestPSP, NullRequestPSP):
            raise VentureValueError("Cannot assess a requesting SP.")
        if not operator.sp.outputPSP.isRandom():
            raise VentureValueError("Cannot assess a deterministic SP.")

        assessedArgs = ReplacingArgs(
            args, vals[2:], operandNodes=args.operandNodes[2:],
            spaux=operator.spAux)
        return operator.sp.outputPSP.logDensity(value, assessedArgs)

    def description(self, name):
        return "  %s(val, func, arg1, arg2, ...) returns the log probability" \
            " (density) of simulating val from func(arg1, arg2, ...)" % name

registerBuiltinSP(
    "assess", typed_nr(
        AssessOutputPSP(),
        [t.AnyType("<val>"),
         SPType([t.AnyType("<args>")], t.AnyType("<val>"), variadic=True),
         t.AnyType("<args>")],
        t.NumberType(),
        variadic=True))
